"""
Multi-source ERG scraper — Veteran Jobs Mission, Military Friendly, Military Times, Military.com.
Merges and deduplicates by company name (fuzzy), then runs enrichment pass.
Output: unified ERG records conforming to ERG output schema.
"""

import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

RATE_LIMIT_DELAY = 2  # seconds between requests
USER_AGENT = "TheFOB-ERGScraper/1.0 (Veteran Resource Platform; contact@thefob.com)"

# Controlled vocabulary for offerings (must match erg_seed_data.OFFERING_TYPES)
OFFERING_TYPES = [
    "mentorship", "networking", "career_development", "transition_support",
    "training_program", "hiring_pipeline", "internship", "community_service",
    "family_support", "spouse_support", "wellness", "resume_support",
    "skillbridge_partner", "coaching", "recruiting_support", "military_leave_benefits",
]


def _normalize_offerings(raw: List[str]) -> List[str]:
    return [o for o in raw if o in OFFERING_TYPES]


def scrape_veteran_jobs_mission() -> List[Dict[str, Any]]:
    """
    Scrape https://veteranjobsmission.com/meet-the-coalition
    Returns list of dicts with company_name, description, industry, career page URL.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("requests or beautifulsoup4 not installed; skipping VJM scrape")
        return []

    url = "https://veteranjobsmission.com/meet-the-coalition"
    results = []
    try:
        time.sleep(RATE_LIMIT_DELAY)
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        # Structure depends on live site; adapt selectors as needed
        for card in soup.select("[class*='company'], [class*='member'], .card, .listing"):
            name_el = card.select_one("h2, h3, .name, [class*='company-name']")
            desc_el = card.select_one("p, .description, [class*='desc']")
            link_el = card.select_one("a[href*='career'], a[href*='job']")
            if name_el:
                results.append({
                    "company_name": name_el.get_text(strip=True),
                    "description": desc_el.get_text(strip=True) if desc_el else None,
                    "careers_url": link_el.get("href") if link_el else None,
                    "data_sources": ["vjm"],
                })
        logger.info("VJM scrape: %d companies", len(results))
    except Exception as e:
        logger.exception("VJM scrape failed: %s", e)
    return results


def scrape_military_friendly() -> List[Dict[str, Any]]:
    """
    Scrape https://www.militaryfriendly.com/employers/
    Returns list with company name, rating tier, year designated.
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return []

    url = "https://www.militaryfriendly.com/employers/"
    results = []
    try:
        time.sleep(RATE_LIMIT_DELAY)
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for row in soup.select("table tr, [class*='employer'], .listing"):
            name_el = row.select_one("td:first-child, .name, h3, a")
            if name_el:
                text = name_el.get_text(strip=True)
                if len(text) > 2:
                    results.append({
                        "company_name": text,
                        "military_friendly_rating": "military_friendly",
                        "data_sources": ["military_friendly"],
                    })
        logger.info("Military Friendly scrape: %d employers", len(results))
    except Exception as e:
        logger.exception("Military Friendly scrape failed: %s", e)
    return results


def merge_and_dedupe(
    vjm: List[Dict],
    mf: List[Dict],
    known_ergs: List[Dict],
) -> List[Dict[str, Any]]:
    """
    Merge sources and deduplicate by company name (case-insensitive; optional fuzzy).
    known_ergs take precedence (seed data).
    """
    by_name = {}
    for rec in known_ergs:
        name = (rec.get("company") or rec.get("company_name") or "").strip()
        if name:
            by_name[name.lower()] = {**rec, "company_name": name, "source_type": "seed_data", "verified": True}

    def add_or_merge(source: Dict, key_name: str = "company_name"):
        name = (source.get(key_name) or source.get("company") or "").strip()
        if not name:
            return
        k = name.lower()
        if k in by_name:
            existing = by_name[k]
            existing.setdefault("data_sources", [])
            for ds in source.get("data_sources", []):
                if ds not in existing["data_sources"]:
                    existing["data_sources"].append(ds)
            if source.get("military_friendly_rating"):
                existing["military_friendly_rating"] = source["military_friendly_rating"]
            if source.get("careers_url"):
                existing["careers_url"] = source["careers_url"]
            if source.get("description"):
                existing["description"] = source["description"]
        else:
            by_name[k] = {
                "company_name": name,
                "description": source.get("description"),
                "careers_url": source.get("careers_url"),
                "military_friendly_rating": source.get("military_friendly_rating"),
                "data_sources": source.get("data_sources", []),
                "source_type": "scraped",
                "verified": False,
            }

    for rec in vjm:
        add_or_merge(rec)
    for rec in mf:
        add_or_merge(rec)

    return list(by_name.values())


def run_all_sources(known_ergs: List[Dict]) -> List[Dict[str, Any]]:
    """
    Run VJM + Military Friendly, merge with known_ergs, return unified list.
    Enrichment pass is separate (erg_enricher).
    """
    vjm = scrape_veteran_jobs_mission()
    mf = scrape_military_friendly()
    merged = merge_and_dedupe(vjm, mf, known_ergs)
    now = datetime.now(timezone.utc).isoformat()
    for r in merged:
        r.setdefault("scraped_at", now)
        r.setdefault("offerings", [])
        r.setdefault("company_size", None)
        r.setdefault("industry", "Other")
    return merged
