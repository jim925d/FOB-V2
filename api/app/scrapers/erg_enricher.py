"""
ERG enricher — For each company, try common military/diversity page URLs,
parse for ERG keywords, extract ERG name, description, offerings.
Marks records as scraped vs community_submitted vs seed_data.
"""

import logging
import re
import time
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

RATE_LIMIT_DELAY = 2
USER_AGENT = "TheFOB-ERGScraper/1.0 (Veteran Resource Platform)"

ERG_KEYWORDS = [
    "employee resource group",
    "ERG",
    "veteran resource group",
    "VRG",
    "business resource group",
    "BRG",
    "affinity group",
    "military employee network",
]

OFFERING_KEYWORDS = {
    "mentorship": ["mentor", "mentorship", "mentoring"],
    "networking": ["networking", "network", "mixer", "events"],
    "career_development": ["career development", "career path", "leadership development"],
    "transition_support": ["transition", "military to civilian", "transitioning"],
    "training_program": ["training", "certification", "MSSA", "boot camp"],
    "hiring_pipeline": ["hiring", "recruit", "veteran hiring"],
    "internship": ["internship", "intern "],
    "community_service": ["community service", "volunteer", "outreach"],
    "family_support": ["family", "military family"],
    "spouse_support": ["spouse", "military spouse"],
    "wellness": ["wellness", "mental health", "PTS", "PTSD"],
    "resume_support": ["resume", "resume translation"],
    "skillbridge_partner": ["SkillBridge", "skill bridge", "DoD SkillBridge"],
    "coaching": ["coaching", "coach"],
    "recruiting_support": ["recruiting", "recruit veterans"],
    "military_leave_benefits": ["military leave", "pay differential", "deployment"],
}


def _get_base_domain(url: Optional[str]) -> Optional[str]:
    if not url or not url.startswith("http"):
        return None
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return None


def _build_candidate_urls(company_website: Optional[str], company_name: str) -> List[str]:
    """Build URLs to try for military/diversity/ERG pages."""
    base = _get_base_domain(company_website)
    if not base:
        return []
    paths = ["/military", "/veterans", "/diversity", "/careers/military", "/about/military", "/careers/veterans"]
    return [urljoin(base, p) for p in paths]


def _extract_offerings_from_text(text: str) -> List[str]:
    """Match offering keywords in text; return list of offering type keys."""
    found = []
    text_lower = text.lower()
    for offering_key, keywords in OFFERING_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(offering_key)
    return list(dict.fromkeys(found))


def _has_erg_content(html: str) -> bool:
    return any(kw.lower() in html.lower() for kw in ERG_KEYWORDS)


def _extract_erg_name(html: str) -> Optional[str]:
    """Simple regex/heuristic for ERG name (e.g. 'Warriors at Amazon')."""
    # Look for common patterns: "X at Company", "Veterans Network", "VetNet"
    patterns = [
        r"(?:ERG|group|network)\s*[:\-]?\s*([A-Za-z0-9\s&]+?)(?:\s*[\.\-\|]|</)",
        r"([A-Za-z]+(?:\s+at\s+[A-Za-z]+)?(?:\s+ERG|Network|BRG|VRG)?)",
    ]
    for pat in patterns:
        m = re.search(pat, html, re.I)
        if m:
            name = m.group(1).strip()
            if 3 <= len(name) <= 80:
                return name
    return None


def enrich_company(
    company_name: str,
    company_website: Optional[str] = None,
    careers_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Try candidate URLs; parse for ERG keywords; return enrichment dict
    (erg_name, description snippet, offerings, contact_email if found).
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return {}

    base = _get_base_domain(company_website or careers_url)
    if not base:
        return {}

    urls = _build_candidate_urls(company_website or careers_url, company_name)
    for url in urls[:5]:
        try:
            time.sleep(RATE_LIMIT_DELAY)
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
            if r.status_code != 200:
                continue
            if not _has_erg_content(r.text):
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            body = soup.get_text(separator=" ", strip=True)
            offerings = _extract_offerings_from_text(body)
            erg_name = _extract_erg_name(r.text)
            return {
                "erg_name": erg_name,
                "offerings": offerings,
                "data_sources": list(set(["company_page"])),
            }
        except Exception as e:
            logger.debug("Enrich %s %s: %s", company_name, url, e)
            continue
    return {}


def enrich_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    For each record, run enrich_company and merge result into record.
    """
    out = []
    for rec in records:
        merged = dict(rec)
        if merged.get("source_type") == "seed_data":
            out.append(merged)
            continue
        en = enrich_company(
            merged.get("company_name", ""),
            merged.get("company_website"),
            merged.get("careers_url"),
        )
        if en:
            merged.setdefault("data_sources", [])
            for ds in en.get("data_sources", []):
                if ds not in merged["data_sources"]:
                    merged["data_sources"].append(ds)
            if en.get("erg_name"):
                merged["erg_name"] = en["erg_name"]
            if en.get("offerings"):
                merged["offerings"] = list(dict.fromkeys((merged.get("offerings") or []) + en["offerings"]))
        out.append(merged)
    return out
