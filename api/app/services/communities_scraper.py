"""
Veteran 501(c)(3) / Community Orgs Scraper — ProPublica Nonprofit Explorer API
The FOB Platform

Searches for veteran-affiliated 501(c)(3)s, enriches with org detail (990 PDF, mission),
maps NTEE to FOB categories, and upserts into CommunityOrg table.
"""

import asyncio
import logging
import re
from datetime import datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import CommunityOrg

logger = logging.getLogger(__name__)

PROPUBLICA_BASE = "https://projects.propublica.org/nonprofits/api/v2"
RATE_LIMIT_DELAY = 1.0  # seconds between requests

# NTEE major group: first character of ntee_code (e.g. A20 -> A = Arts)
# ProPublica filter uses 1-10; NTEE letters: A=Arts, B=Education, C=Environment, D=Health,
# E=Human Services, F=International, G=Public, H=Religion, I=Mutual, J+=Unknown
NTEE_LETTER_TO_MAJOR = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8, "I": 9,
}
# FOB categories: service, outdoor, wellness, professional, arts, social, education
NTEE_MAJOR_TO_FOB = {
    1: "arts",           # Arts, Culture & Humanities
    2: "education",      # Education
    3: "outdoor",        # Environment and Animals (often outdoor/recreation for vet orgs)
    4: "wellness",       # Health
    5: "service",        # Human Services -> service or social by keyword
    6: "service",        # International, Foreign Affairs
    7: "service",        # Public, Societal Benefit
    8: "social",         # Religion Related
    9: "social",         # Mutual/Membership Benefit
    10: "service",       # Unknown, Unclassified
}


def ntee_major_from_code(ntee_code: str | None) -> int:
    """Return NTEE major group 1-10 from code like 'A20' or 'B30'."""
    if not ntee_code or not isinstance(ntee_code, str):
        return 10
    first = ntee_code.strip().upper()[:1]
    return NTEE_LETTER_TO_MAJOR.get(first, 10)


def categorize_org(ntee_code: str | None, name: str, description: str | None) -> str:
    """Map NTEE + name/description to FOB category."""
    major = ntee_major_from_code(ntee_code)
    base_cat = NTEE_MAJOR_TO_FOB.get(major, "service")
    text = f" {(name or '')} {(description or '')} ".lower()
    # Nudge by keywords
    if re.search(r"\b(employment|career|job|business|entrepreneur)\b", text):
        return "professional"
    if re.search(r"\b(family|spouse|children|family)\b", text):
        return "social"
    if re.search(r"\b(outdoor|recreation|sport|fitness|running|hiking)\b", text):
        return "outdoor"
    if re.search(r"\b(mental\s+health|wellness|ptsd|therapy)\b", text):
        return "wellness"
    if re.search(r"\b(education|scholarship|college|university|student)\b", text):
        return "education"
    if re.search(r"\b(arts|culture|writing|music)\b", text):
        return "arts"
    return base_cat


def _safe_str(val, max_len: int = 500) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s[:max_len] if s else None


def _ein_str(ein) -> str:
    """Normalize EIN to string with leading zeros (e.g. 9 digits)."""
    if ein is None:
        return ""
    s = str(ein).strip()
    s = s.replace("-", "").zfill(9)
    return s[:9]


def _domain_from_url(url: str | None) -> str | None:
    """Extract hostname (domain) from URL for Clearbit logo, e.g. https://www.dav.org -> dav.org."""
    if not url or not url.strip():
        return None
    url = url.strip().lower()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = parsed.netloc or parsed.path
        if not host or host.startswith("."):
            return None
        # Strip www.
        if host.startswith("www."):
            host = host[4:]
        return host.split(":")[0] if host else None
    except Exception:
        return None


# Google Favicon API - works for most domains (Clearbit logo API was deprecated)
GOOGLE_FAVICON_BASE = "https://www.google.com/s2/favicons"


class CommunitiesScraper:
    """Scrape veteran 501(c)(3)s from ProPublica and upsert into CommunityOrg."""

    def __init__(self, session: AsyncSession, *, max_orgs: int | None = None):
        self.session = session
        self.max_orgs = max_orgs  # cap enrichment calls for testing (None = all)

    async def scrape_all(self) -> dict:
        """Run full scrape: search -> enrich -> categorize -> upsert. Returns summary."""
        total_new = 0
        total_updated = 0
        total_errors = 0
        seen_eins: set[str] = set()

        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "TheFOB-CommunitiesBot/1.0 (veteran resource platform)"},
        ) as client:
            # Step 1: Paginate search
            page = 0
            num_pages = 1
            all_orgs: list[dict] = []

            while page < num_pages:
                url = f"{PROPUBLICA_BASE}/search.json"
                params = {"q": "veteran", "c_code[id]": 3, "page": page}
                await asyncio.sleep(RATE_LIMIT_DELAY)
                try:
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                except Exception as e:
                    logger.error("ProPublica search failed page=%s: %s", page, e)
                    total_errors += 1
                    break
                num_pages = data.get("num_pages") or 1
                orgs = data.get("organizations") or []
                all_orgs.extend(orgs)
                logger.info("Search page %s: %s orgs (total pages %s)", page + 1, len(orgs), num_pages)
                page += 1

            # Step 2 & 3 & 4: Enrich each (by EIN), categorize, upsert
            for i, raw in enumerate(all_orgs):
                if self.max_orgs is not None and i >= self.max_orgs:
                    break
                ein = _ein_str(raw.get("ein"))
                if not ein or ein in seen_eins:
                    continue
                seen_eins.add(ein)
                await asyncio.sleep(RATE_LIMIT_DELAY)
                detail = await self._fetch_org_detail(client, ein)
                name = _safe_str(raw.get("name") or (detail and detail.get("organization", {}).get("name")), 500)
                if not name:
                    continue
                city = _safe_str(raw.get("city") or (detail and detail.get("organization", {}).get("city")), 200)
                state = _safe_str(raw.get("state") or (detail and detail.get("organization", {}).get("state")), 10)
                zip_code = _safe_str(
                    raw.get("zipcode") or raw.get("zip") or (detail and detail.get("organization", {}).get("zipcode")), 20
                )
                address = _safe_str(raw.get("address") or (detail and detail.get("organization", {}).get("address")), 500)
                ntee_code = _safe_str(raw.get("ntee_code") or (detail and detail.get("organization", {}).get("ntee_code")), 10)
                description = None
                website = None
                form_990_url = None
                form_990_fiscal_year = None
                revenue = None
                expenses = None
                if detail:
                    org_obj = detail.get("organization") or {}
                    description = _safe_str(org_obj.get("mission") or org_obj.get("description"), 10000)
                    website = _safe_str(org_obj.get("website"), 500)
                    filings = (detail.get("filings_with_data") or []) + (detail.get("filings_without_data") or [])
                    for f in sorted(filings, key=lambda x: (x.get("tax_prd") or 0), reverse=True):
                        if f.get("pdf_url"):
                            form_990_url = _safe_str(f["pdf_url"], 1000)
                            form_990_fiscal_year = _safe_str(str(f.get("tax_prd_yr") or ""), 20)
                            revenue = f.get("totrevenue") if isinstance(f.get("totrevenue"), (int, float)) else None
                            expenses = f.get("totfuncexpns") if isinstance(f.get("totfuncexpns"), (int, float)) else None
                            break
                category = categorize_org(ntee_code, name, description)
                alternate_name = _safe_str(raw.get("sub_name") or (detail and (detail.get("organization") or {}).get("sub_name")), 500)
                tagline = None  # ProPublica doesn't provide; leave for manual/social_links later
                social_links = None  # ProPublica doesn't provide; populate later

                # Logo: use Google Favicon API by domain (no API key, works for most sites).
                logo_url = None
                domain = _domain_from_url(website)
                if domain:
                    logo_url = f"{GOOGLE_FAVICON_BASE}?domain={domain}&sz=128"

                try:
                    updated = await self._upsert(
                        ein=ein,
                        name=name,
                        alternate_name=alternate_name,
                        city=city,
                        state=state,
                        zip_code=zip_code,
                        address=address,
                        category=category,
                        ntee_code=ntee_code,
                        description=description,
                        website=website,
                        tagline=tagline,
                        form_990_url=form_990_url,
                        form_990_fiscal_year=form_990_fiscal_year,
                        revenue=revenue,
                        expenses=expenses,
                        social_links=social_links,
                        logo_url=logo_url,
                    )
                    if updated:
                        total_updated += 1
                    else:
                        total_new += 1
                except Exception as e:
                    logger.warning("Upsert failed for EIN %s: %s", ein, e)
                    total_errors += 1

        await self.session.commit()
        return {
            "total_new": total_new,
            "total_updated": total_updated,
            "total_errors": total_errors,
            "total_processed": len(seen_eins),
        }

    async def _fetch_org_detail(self, client: httpx.AsyncClient, ein: str) -> dict | None:
        """GET organizations/:ein.json. ProPublica expects EIN as integer (no leading zeros)."""
        ein_num = ein.replace("-", "").lstrip("0") or "0"
        if ein_num.isdigit():
            ein_for_url = str(int(ein_num))
        else:
            ein_for_url = ein_num
        url = f"{PROPUBLICA_BASE}/organizations/{ein_for_url}.json"
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.debug("Org detail failed for EIN %s: %s", ein, e)
            return None

    async def _upsert(
        self,
        ein: str,
        name: str,
        alternate_name: str | None,
        city: str | None,
        state: str | None,
        zip_code: str | None,
        address: str | None,
        category: str,
        ntee_code: str | None,
        description: str | None,
        website: str | None,
        tagline: str | None,
        form_990_url: str | None,
        form_990_fiscal_year: str | None,
        revenue: float | None,
        expenses: float | None,
        social_links: dict | None,
        logo_url: str | None = None,
    ) -> bool:
        """Insert or update by EIN. Returns True if updated, False if inserted."""
        existing = await self.session.execute(
            select(CommunityOrg.id).where(CommunityOrg.ein == ein)
        )
        existing_id = existing.scalar_one_or_none()
        now = datetime.utcnow()
        if existing_id:
            org = await self.session.get(CommunityOrg, existing_id)
            if org:
                org.name = name
                org.alternate_name = alternate_name
                org.city = city
                org.state = state
                org.zip_code = zip_code
                org.address = address
                org.category = category
                org.ntee_code = ntee_code
                org.description = description
                org.website = website
                org.tagline = tagline
                org.form_990_url = form_990_url
                org.form_990_fiscal_year = form_990_fiscal_year
                org.revenue = revenue
                org.expenses = expenses
                org.social_links = social_links
                org.logo_url = logo_url
                org.updated_at = now
                return True
        org = CommunityOrg(
            ein=ein,
            name=name,
            alternate_name=alternate_name,
            city=city,
            state=state,
            zip_code=zip_code,
            address=address,
            category=category,
            ntee_code=ntee_code,
            description=description,
            website=website,
            tagline=tagline,
            form_990_url=form_990_url,
            form_990_fiscal_year=form_990_fiscal_year,
            revenue=revenue,
            expenses=expenses,
            social_links=social_links,
            logo_url=logo_url,
        )
        self.session.add(org)
        return False
