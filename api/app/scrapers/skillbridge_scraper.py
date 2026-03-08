"""
SkillBridge Scraper — Paginates through skillbridge.osd.mil/locations.htm
and extracts all program listings into structured data.

The DoD site uses a paginated HTML table. Each page shows ~20 results.
With 10,000+ programs, this means ~570+ pages.

We are respectful: random delays between requests, proper User-Agent,
and logging of all activity. The scraper identifies itself as a veteran
resource platform.
"""

import asyncio
import hashlib
import random
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

import httpx
from bs4 import BeautifulSoup
import structlog

from app.config import get_settings

logger = structlog.get_logger()


@dataclass
class ScrapedProgram:
    """Raw scraped data before DB insertion."""
    company: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    location_raw: str = ""
    nationwide: bool = False
    online: bool = False
    program_duration: str = ""
    duration_min_days: Optional[int] = None
    duration_max_days: Optional[int] = None
    opportunity_type: str = ""
    delivery_method: str = ""
    description: str = ""
    job_family: str = ""
    target_moc: str = ""
    employer_poc_name: str = ""
    employer_poc_email: str = ""
    employer_website: str = ""
    army: bool = False
    navy: bool = False
    air_force: bool = False
    marines: bool = False
    coast_guard: bool = False
    space_force: bool = False
    source_url: str = ""
    source_page: int = 0

    @property
    def fingerprint(self) -> str:
        """Unique hash for deduplication."""
        raw = f"{self.company}|{self.city}|{self.state}|{self.job_family}|{self.opportunity_type}"
        return hashlib.md5(raw.encode()).hexdigest()


def parse_duration(duration_str: str) -> Tuple[Optional[int], Optional[int]]:
    """Parse duration string like '1-180 Days' into min/max days."""
    if not duration_str:
        return None, None

    # Common patterns: "1-180 Days", "90 Days", "Up to 180 Days"
    duration_str = duration_str.strip().lower()

    # Range: "1-180 days"
    range_match = re.search(r'(\d+)\s*[-–to]+\s*(\d+)', duration_str)
    if range_match:
        return int(range_match.group(1)), int(range_match.group(2))

    # Single: "180 days"
    single_match = re.search(r'(\d+)', duration_str)
    if single_match:
        days = int(single_match.group(1))
        return days, days

    return None, None


def classify_industry(job_family: str, company: str, description: str) -> str:
    """
    Classify program into an industry category based on job family,
    company name, and description text.
    """
    text = f"{job_family} {company} {description}".lower()

    industry_keywords = {
        "Technology": [
            "software", "developer", "engineer", "it ", "information technology",
            "data", "cloud", "cyber", "network", "systems admin", "devops",
            "programming", "web ", "database", "microsoft", "google", "amazon",
            "apple", "intel", "cisco", "dell", "salesforce", "sap", "oracle",
            "computer", "digital", "tech", "ai ", "machine learning",
        ],
        "Healthcare": [
            "health", "medical", "nurse", "clinical", "hospital", "patient",
            "pharma", "biotech", "dental", "therapy", "mental health",
            "veteran affairs", "va ", "medtronic", "unitedhealth", "mayo",
        ],
        "Defense": [
            "defense", "military", "lockheed", "raytheon", "northrop",
            "general dynamics", "bae systems", "booz allen", "saic", "leidos",
            "l3harris", "intelligence", "clearance", "dod", "classified",
        ],
        "Aerospace": [
            "aerospace", "aviation", "aircraft", "boeing", "spacex", "nasa",
            "sikorsky", "ge aviation", "pratt", "pilot", "flight", "rocket",
        ],
        "Manufacturing": [
            "manufactur", "production", "assembly", "quality", "lean",
            "six sigma", "caterpillar", "john deere", "factory", "plant",
            "welding", "machining", "cnc",
        ],
        "Logistics": [
            "logistics", "supply chain", "warehouse", "distribution",
            "transportation", "shipping", "freight", "fedex", "ups",
            "amazon", "walmart", "trucking", "fleet",
        ],
        "Finance": [
            "finance", "banking", "accounting", "insurance", "investment",
            "jpmorgan", "usaa", "deloitte", "pwc", "kpmg", "ernst",
            "financial", "audit", "tax", "risk",
        ],
        "Energy": [
            "energy", "power", "electric", "solar", "wind", "oil", "gas",
            "nuclear", "utility", "pipeline", "duke energy", "dominion",
            "halliburton", "schlumberger",
        ],
        "Trades": [
            "hvac", "plumbing", "electrical", "mechanic", "technician",
            "construction", "carpentry", "welding", "diesel", "linework",
            "apprentice",
        ],
        "Automotive": [
            "automotive", "auto ", "vehicle", "toyota", "general motors",
            "ford", "tesla", "dealer",
        ],
        "Cybersecurity": [
            "cybersecurity", "cyber security", "soc analyst", "penetration",
            "threat", "incident response", "forensic", "palo alto",
            "crowdstrike", "firewall",
        ],
        "Retail": [
            "retail", "store", "sales", "customer service", "home depot",
            "lowes", "target",
        ],
        "Education": [
            "education", "training", "teaching", "instructor", "university",
            "college", "academic",
        ],
        "Government": [
            "government", "federal", "state agency", "public sector",
            "civil service", "gsa", "fema", "dhs", "cbp",
        ],
    }

    for industry, keywords in industry_keywords.items():
        for kw in keywords:
            if kw in text:
                return industry

    return "Other"


class SkillBridgeScraper:
    """
    Scrapes the DoD SkillBridge locations page.

    The site at skillbridge.osd.mil/locations.htm uses JavaScript
    to render a paginated table. We need to identify the underlying
    data source — likely an API call or embedded JSON.
    """

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.scrape_base_url
        self.programs: List[ScrapedProgram] = []
        self.seen_fingerprints = set()
        self.stats = {
            "pages_scraped": 0,
            "programs_found": 0,
            "duplicates_skipped": 0,
            "errors": 0,
        }

    async def _get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            headers={
                "User-Agent": self.settings.scrape_user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            },
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
        )

    async def _polite_delay(self):
        """Random delay between requests to be respectful."""
        delay = random.uniform(
            self.settings.scrape_delay_min,
            self.settings.scrape_delay_max,
        )
        await asyncio.sleep(delay)

    async def discover_data_source(self, client: httpx.AsyncClient) -> str:
        """
        Fetch the locations page and discover how data is loaded.
        The DoD site may use:
        1. Server-rendered HTML tables
        2. JavaScript-loaded data from an API
        3. Embedded JSON in script tags

        We check all three approaches.
        """
        logger.info("Discovering data source", url=self.base_url)

        resp = await client.get(self.base_url)
        resp.raise_for_status()
        html = resp.text

        soup = BeautifulSoup(html, "lxml")

        # Check for embedded JSON data in script tags
        for script in soup.find_all("script"):
            text = script.string or ""
            # Look for large JSON arrays that might contain program data
            if "locations" in text.lower() or "programs" in text.lower():
                json_match = re.search(r'(?:var\s+\w+\s*=\s*)(\[[\s\S]*?\]);', text)
                if json_match:
                    logger.info("Found embedded JSON data source")
                    return "embedded_json"

            # Look for API endpoint URLs
            api_match = re.search(r'(https?://[^"\']+(?:api|data|json)[^"\']*)', text)
            if api_match:
                logger.info("Found API endpoint", url=api_match.group(1))
                return f"api:{api_match.group(1)}"

        # Check for HTML table
        table = soup.find("table")
        if table:
            logger.info("Found HTML table data source")
            return "html_table"

        # Check for iframe or other embedded content
        iframe = soup.find("iframe")
        if iframe:
            src = iframe.get("src", "")
            logger.info("Found iframe source", src=src)
            return f"iframe:{src}"

        logger.warning("Could not determine data source, will attempt HTML parsing")
        return "unknown"

    def parse_html_table_page(self, html: str, page_num: int) -> List[ScrapedProgram]:
        """Parse a page of HTML table results."""
        soup = BeautifulSoup(html, "lxml")
        programs = []

        table = soup.find("table")
        if not table:
            # Try finding data in div-based layouts
            rows = soup.find_all("div", class_=re.compile(r"row|result|card|listing", re.I))
            if not rows:
                logger.warning("No table or results found on page", page=page_num)
                return programs

        # Extract table rows
        rows = table.find_all("tr") if table else []
        headers = []

        for i, row in enumerate(rows):
            cells = row.find_all(["td", "th"])
            cell_texts = [c.get_text(strip=True) for c in cells]

            # First row is usually headers
            if i == 0 and any("company" in t.lower() or "organization" in t.lower() for t in cell_texts):
                headers = [t.lower().strip() for t in cell_texts]
                continue

            if not headers or len(cell_texts) < 3:
                continue

            # Map cell values to a dict using headers
            row_data = {}
            for j, header in enumerate(headers):
                if j < len(cell_texts):
                    row_data[header] = cell_texts[j]

            program = self._row_to_program(row_data, page_num)
            if program:
                programs.append(program)

        return programs

    def _row_to_program(self, row: Dict[str, str], page_num: int) -> Optional[ScrapedProgram]:
        """Convert a parsed row dict into a ScrapedProgram."""
        # Try various header name patterns
        company = (
            row.get("company", "") or
            row.get("organization", "") or
            row.get("employer", "") or
            row.get("provider", "")
        ).strip()

        if not company:
            return None

        # Location parsing
        city = (row.get("city", "") or "").strip()
        state = (row.get("state", "") or "").strip()
        location = (row.get("location", "") or row.get("city, state", "") or "").strip()

        if not city and location:
            # Try to parse "City, ST" format
            parts = location.split(",")
            if len(parts) >= 2:
                city = parts[0].strip()
                state = parts[-1].strip()[:2].upper()

        # Nationwide / Online flags
        nationwide = any(
            kw in (location + city + state).lower()
            for kw in ["nationwide", "national", "all states", "various"]
        )
        online = any(
            kw in (location + city + state + row.get("delivery", "")).lower()
            for kw in ["online", "virtual", "remote"]
        )

        # Duration
        duration_str = (
            row.get("duration", "") or
            row.get("program duration", "") or
            row.get("length", "")
        ).strip()
        dur_min, dur_max = parse_duration(duration_str)

        # Job family / industry
        job_family = (
            row.get("job family", "") or
            row.get("career field", "") or
            row.get("industry", "") or
            row.get("occupation", "")
        ).strip()

        # Description
        description = (
            row.get("description", "") or
            row.get("program description", "") or
            row.get("details", "")
        ).strip()

        # Opportunity type
        opp_type = (
            row.get("opportunity type", "") or
            row.get("type", "") or
            row.get("program type", "")
        ).strip()

        # Delivery method
        delivery = (
            row.get("delivery method", "") or
            row.get("delivery", "") or
            row.get("format", "")
        ).strip()

        # Service branches
        branches_text = (
            row.get("service", "") or
            row.get("branch", "") or
            row.get("services", "")
        ).lower()

        # Classify industry
        industry = classify_industry(job_family, company, description)

        program = ScrapedProgram(
            company=company,
            city=city,
            state=state.upper()[:2] if state else "",
            location_raw=location or f"{city}, {state}",
            nationwide=nationwide,
            online=online,
            program_duration=duration_str,
            duration_min_days=dur_min,
            duration_max_days=dur_max,
            opportunity_type=opp_type,
            delivery_method=delivery,
            description=description,
            job_family=job_family,
            industry=industry,
            army="army" in branches_text or not branches_text,
            navy="navy" in branches_text or not branches_text,
            air_force="air" in branches_text or not branches_text,
            marines="marine" in branches_text or not branches_text,
            coast_guard="coast" in branches_text or not branches_text,
            space_force="space" in branches_text,
            source_url=f"{self.base_url}?page={page_num}",
            source_page=page_num,
        )

        return program

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
        Main scraping entry point. Discovers data source and
        iterates through all pages.
        """
        max_pages = max_pages or self.settings.scrape_max_pages
        logger.info("Starting SkillBridge scrape", max_pages=max_pages)

        async with await self._get_client() as client:
            # Discover how the data is served
            source_type = await self.discover_data_source(client)
            logger.info("Data source type", source_type=source_type)

            if source_type.startswith("api:"):
                await self._scrape_api(client, source_type.split(":", 1)[1], max_pages)
            elif source_type == "embedded_json":
                await self._scrape_embedded_json(client)
            else:
                await self._scrape_html_pages(client, max_pages)

        logger.info(
            "Scrape complete",
            pages=self.stats["pages_scraped"],
            programs=self.stats["programs_found"],
            duplicates=self.stats["duplicates_skipped"],
            errors=self.stats["errors"],
        )

        return self.programs

    async def _scrape_html_pages(self, client: httpx.AsyncClient, max_pages: int):
        """Paginate through HTML table pages."""
        page = 1
        consecutive_empty = 0

        while page <= max_pages and consecutive_empty < 3:
            try:
                # The DoD site may use query params or form post for pagination
                url = f"{self.base_url}?page={page}"
                logger.info("Scraping page", page=page, url=url)

                resp = await client.get(url)
                resp.raise_for_status()

                programs = self.parse_html_table_page(resp.text, page)
                self.stats["pages_scraped"] += 1

                if not programs:
                    consecutive_empty += 1
                    logger.info("Empty page", page=page, consecutive_empty=consecutive_empty)
                else:
                    consecutive_empty = 0
                    added = sum(1 for p in programs if self._add_program(p))
                    logger.info("Page results", page=page, found=len(programs), added=added)

                page += 1
                await self._polite_delay()

            except httpx.HTTPStatusError as e:
                logger.error("HTTP error", page=page, status=e.response.status_code)
                self.stats["errors"] += 1
                if e.response.status_code == 429:
                    # Rate limited — back off
                    logger.warning("Rate limited, backing off 60s")
                    await asyncio.sleep(60)
                elif e.response.status_code >= 500:
                    await asyncio.sleep(10)
                else:
                    break

            except Exception as e:
                logger.error("Scrape error", page=page, error=str(e))
                self.stats["errors"] += 1
                await asyncio.sleep(5)

    async def _scrape_api(self, client: httpx.AsyncClient, api_url: str, max_pages: int):
        """If we discover a JSON API, use it directly."""
        page = 1
        while page <= max_pages:
            try:
                params = {"page": page, "pageSize": 50}
                resp = await client.get(api_url, params=params)
                resp.raise_for_status()

                data = resp.json()
                # Adapt based on actual API response structure
                items = data if isinstance(data, list) else data.get("data", data.get("results", []))

                if not items:
                    break

                for item in items:
                    program = ScrapedProgram(
                        company=item.get("Organization", item.get("company", "")),
                        city=item.get("City", item.get("city", "")),
                        state=item.get("State", item.get("state", "")),
                        description=item.get("Description", item.get("description", "")),
                        job_family=item.get("Job Family", item.get("jobFamily", "")),
                        program_duration=item.get("Duration", item.get("duration", "")),
                        opportunity_type=item.get("Opportunity Type", ""),
                        delivery_method=item.get("Delivery Method", ""),
                        source_page=page,
                    )
                    program.industry = classify_industry(
                        program.job_family, program.company, program.description
                    )
                    dur_min, dur_max = parse_duration(program.program_duration)
                    program.duration_min_days = dur_min
                    program.duration_max_days = dur_max
                    self._add_program(program)

                self.stats["pages_scraped"] += 1
                page += 1
                await self._polite_delay()

            except Exception as e:
                logger.error("API scrape error", page=page, error=str(e))
                self.stats["errors"] += 1
                break

    async def _scrape_embedded_json(self, client: httpx.AsyncClient):
        """Extract data from embedded JSON in the page source."""
        resp = await client.get(self.base_url)
        resp.raise_for_status()

        # Find JSON arrays in script tags
        soup = BeautifulSoup(resp.text, "lxml")
        for script in soup.find_all("script"):
            text = script.string or ""
            json_matches = re.findall(r'(\[{.*?}\])', text, re.DOTALL)
            for match in json_matches:
                try:
                    import json
                    items = json.loads(match)
                    if isinstance(items, list) and len(items) > 10:
                        logger.info("Found embedded data", count=len(items))
                        for item in items:
                            if isinstance(item, dict) and any(
                                k in str(item.keys()).lower()
                                for k in ["company", "organization", "employer"]
                            ):
                                program = ScrapedProgram(
                                    company=str(item.get("Organization", item.get("company", ""))),
                                    city=str(item.get("City", item.get("city", ""))),
                                    state=str(item.get("State", item.get("state", ""))),
                                    description=str(item.get("Description", "")),
                                    job_family=str(item.get("Job Family", "")),
                                )
                                program.industry = classify_industry(
                                    program.job_family, program.company, program.description
                                )
                                self._add_program(program)
                        self.stats["pages_scraped"] = 1
                        return
                except (ValueError, TypeError):
                    continue
