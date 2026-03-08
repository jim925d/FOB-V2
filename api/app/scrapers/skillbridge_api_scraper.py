"""
SkillBridge API Scraper — Uses the DoD SkillBridge JSON API
(sb-api.azurewebsites.us) to fetch all programs.

Strategy:
1. Hit /api/Location/Filters to get all states, partners, job families
2. Iterate by state via /api/Location/LookUp (max 150 per call)
3. Deduplicate, classify industry, build ScrapedProgram objects
4. For states with 150 results (likely truncated), sub-query by partner

Rate limiting: 300ms between requests. Identifies as veteran resource platform.
"""

import asyncio
from typing import List, Dict, Optional, Set

import httpx
import structlog

from app.config import get_settings
from app.scrapers.skillbridge_scraper import (
    ScrapedProgram, parse_duration,
)

logger = structlog.get_logger()

API_BASE = "https://sb-api.azurewebsites.us/api"
DEVICE_PARAMS = "device=platform:Linux,browser:Chrome&mobile=false"

# All US states + territories for iteration
US_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "GU", "VI",
]


class SkillBridgeAPIScraper:
    """
    Fetches programs from the DoD SkillBridge API.

    Preferred over HTML scraping — the API returns structured JSON
    with lat/lon already included for most programs.
    """

    def __init__(self):
        self.settings = get_settings()
        self.programs: List[ScrapedProgram] = []
        self.seen_fingerprints: Set[str] = set()
        self.filters_data: Dict = {}
        self.stats = {
            "api_calls": 0,
            "pages_scraped": 0,  # Compat with pipeline
            "programs_found": 0,
            "duplicates_skipped": 0,
            "states_queried": 0,
            "truncated_states": 0,
            "errors": 0,
        }

    async def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers={
                "User-Agent": self.settings.scrape_user_agent,
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.5",
            },
            timeout=30.0,
        )

    async def fetch_filters(self) -> Dict:
        """
        Fetch available filters: partners, states, job families, etc.
        GET /api/Location/Filters?{DEVICE_PARAMS}
        """
        async with await self._get_client() as client:
            url = f"{API_BASE}/Location/Filters?{DEVICE_PARAMS}"
            logger.info("Fetching filters", url=url)
            resp = await client.get(url)
            resp.raise_for_status()
            self.filters_data = resp.json()
            self.stats["api_calls"] += 1

            logger.info(
                "Filters fetched",
                partners=len(self.filters_data.get("Partners", [])),
                states=len(self.filters_data.get("States", [])),
                total_count=self.filters_data.get("Count", 0),
            )
            return self.filters_data

    async def fetch_programs_by_state(
        self, state: str, partner: str = ""
    ) -> List[Dict]:
        """
        Fetch programs for a given state (and optionally partner).
        POST /api/Location/LookUp?{DEVICE_PARAMS}

        Returns max 150 records per call.
        """
        async with await self._get_client() as client:
            url = f"{API_BASE}/Location/LookUp?{DEVICE_PARAMS}"
            payload = {
                "State": state,
                "Partner": partner,
                "Keyword": "",
                "MOC": "",
                "JobFamily": "",
                "DeliveryMethod": "",
            }

            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                self.stats["api_calls"] += 1

                data = resp.json()

                # The API returns a list of program objects
                programs = data if isinstance(data, list) else data.get("Result", [])

                logger.debug(
                    "State query result",
                    state=state,
                    partner=partner or "all",
                    count=len(programs),
                )
                return programs

            except httpx.HTTPStatusError as e:
                logger.error(
                    "API error", state=state, status=e.response.status_code
                )
                self.stats["errors"] += 1
                return []
            except Exception as e:
                logger.error("Fetch error", state=state, error=str(e))
                self.stats["errors"] += 1
                return []

    def _parse_api_program(self, raw: Dict, state_queried: str) -> Optional[ScrapedProgram]:
        """Convert an API response record into a ScrapedProgram."""
        try:
            company = (raw.get("Employer") or raw.get("Company") or "").strip()
            if not company:
                return None

            city = (raw.get("City") or "").strip()
            state = (raw.get("State") or state_queried or "").strip().upper()
            zip_code = (raw.get("Zip") or raw.get("ZipCode") or "").strip()

            # Location flags
            nationwide = bool(raw.get("Nationwide", False))
            online = bool(
                raw.get("Online", False)
                or raw.get("Virtual", False)
                or "virtual" in (raw.get("DeliveryMethod") or "").lower()
            )

            # Duration
            duration_str = raw.get("Duration") or raw.get("ProgramDuration") or ""
            dur_min, dur_max = parse_duration(duration_str)

            # Description and job info
            description = (raw.get("Summary") or raw.get("Description") or "").strip()
            job_family = (raw.get("JobFamily") or raw.get("Job") or "").strip()
            target_moc = (raw.get("MOC") or raw.get("TargetMOC") or "").strip()
            opportunity_type = (raw.get("OpportunityType") or "").strip()
            delivery_method = (raw.get("DeliveryMethod") or "").strip()

            # Contact
            poc_name = (raw.get("POCName") or raw.get("POC") or "").strip()
            poc_email = (raw.get("POCEmail") or raw.get("Email") or "").strip()
            website = (raw.get("URL") or raw.get("Website") or "").strip()

            # Service branches
            branches = raw.get("Branches") or raw.get("Branch") or ""
            branches_lower = branches.lower() if isinstance(branches, str) else ""
            army = "army" in branches_lower or raw.get("Army", False)
            navy = "navy" in branches_lower or raw.get("Navy", False)
            air_force = "air force" in branches_lower or raw.get("AirForce", False)
            marines = "marine" in branches_lower or raw.get("Marines", False)
            coast_guard = "coast guard" in branches_lower or raw.get("CoastGuard", False)
            space_force = "space force" in branches_lower or raw.get("SpaceForce", False)

            # Lat/Lon — the API often provides these
            lat = raw.get("Lat") or raw.get("Latitude")
            lon = raw.get("Long") or raw.get("Longitude") or raw.get("Lng")

            # Industry classification

            program = ScrapedProgram(
                company=company,
                city=city,
                state=state,
                zip_code=zip_code,
                location_raw=f"{city}, {state} {zip_code}".strip(", "),
                nationwide=nationwide,
                online=online,
                program_duration=duration_str,
                duration_min_days=dur_min,
                duration_max_days=dur_max,
                opportunity_type=opportunity_type,
                delivery_method=delivery_method,
                description=description,
                job_family=job_family,
                target_moc=target_moc,
                employer_poc_name=poc_name,
                employer_poc_email=poc_email,
                employer_website=website,
                army=army,
                navy=navy,
                air_force=air_force,
                marines=marines,
                coast_guard=coast_guard,
                space_force=space_force,
                source_url=f"{API_BASE}/Location/LookUp",
                source_page=0,
            )

            # Attach lat/lon if the API provided them
            if lat is not None and lon is not None:
                try:
                    program.latitude = float(lat)
                    program.longitude = float(lon)
                    program.geocode_quality = "api_provided"
                except (ValueError, TypeError):
                    pass

            return program

        except Exception as e:
            logger.error("Parse error", error=str(e), raw_keys=list(raw.keys()))
            self.stats["errors"] += 1
            return None

    def _add_program(self, program: ScrapedProgram) -> bool:
        """Add program if not a duplicate. Returns True if added."""
        fp = program.fingerprint
        if fp in self.seen_fingerprints:
            self.stats["duplicates_skipped"] += 1
            return False
        self.seen_fingerprints.add(fp)
        self.programs.append(program)
        self.stats["programs_found"] += 1
        return True

    async def scrape_all(self, max_pages: Optional[int] = None) -> List[ScrapedProgram]:
        """
        Fetch all programs by iterating through states.

        For states that return exactly 150 results (API limit),
        sub-query by partner to capture truncated data.
        """
        logger.info("Starting full SkillBridge API scrape")

        # Step 1: Get filters (for partner list if needed)
        try:
            await self.fetch_filters()
        except Exception as e:
            logger.warning("Could not fetch filters, proceeding with state iteration", error=str(e))

        partners = [
            p.get("Name", p) if isinstance(p, dict) else p
            for p in self.filters_data.get("Partners", [])
        ]

        # Step 2: Iterate all states
        delay_min = self.settings.scrape_delay_min
        delay_max = self.settings.scrape_delay_max

        for state in US_STATES:
            self.stats["states_queried"] += 1

            raw_programs = await self.fetch_programs_by_state(state)

            # Parse and deduplicate
            state_count = 0
            for raw in raw_programs:
                program = self._parse_api_program(raw, state)
                if program and self._add_program(program):
                    state_count += 1

            logger.info(
                "State complete",
                state=state,
                raw=len(raw_programs),
                new=state_count,
                total=len(self.programs),
            )

            # If we hit the 150 limit, this state is likely truncated
            if len(raw_programs) >= 150 and partners:
                self.stats["truncated_states"] += 1
                logger.info(
                    "State truncated, sub-querying by partner",
                    state=state,
                    partners_to_query=min(len(partners), 50),
                )

                for partner in partners[:200]:  # Safety limit
                    sub_programs = await self.fetch_programs_by_state(state, partner)
                    for raw in sub_programs:
                        program = self._parse_api_program(raw, state)
                        if program:
                            self._add_program(program)

                    # Rate limit
                    await asyncio.sleep(
                        delay_min + (delay_max - delay_min) * 0.3
                    )

            # Rate limit between states
            import random
            await asyncio.sleep(random.uniform(delay_min * 0.3, delay_max * 0.5))

            # Safety: respect max_pages as approximate call limit
            if max_pages and self.stats["api_calls"] >= max_pages:
                logger.warning("Hit max API call limit", calls=self.stats["api_calls"])
                break

        self.stats["pages_scraped"] = self.stats["api_calls"]

        logger.info(
            "SkillBridge API scrape complete",
            total_programs=len(self.programs),
            api_calls=self.stats["api_calls"],
            states=self.stats["states_queried"],
            truncated=self.stats["truncated_states"],
            duplicates=self.stats["duplicates_skipped"],
            errors=self.stats["errors"],
        )

        return self.programs
