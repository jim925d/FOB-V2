"""
Load labor occupations (target careers/industries) from scraped O*NET data.
Used by career pathfinder /targets and for roadmap target matching.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).resolve().parent / "labor_occupations.json"
_CACHE: Optional[dict] = None


def load_labor_occupations(path: Optional[Path] = None) -> dict:
    """
    Load labor_occupations.json. Returns dict with keys:
      source, url, occupations (list of {soc_code, title, description, industry, industry_key, value, label}), industries.
    Returns empty structure if file missing.
    """
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    p = path or _DATA_PATH
    if not p.exists():
        logger.debug("Labor occupations file not found at %s; run labor_occupations_scraper", p)
        _CACHE = {"source": "", "occupations": [], "industries": [], "url": ""}
        return _CACHE
    try:
        with open(p, encoding="utf-8") as f:
            _CACHE = json.load(f)
        return _CACHE
    except Exception as e:
        logger.warning("Failed to load labor occupations from %s: %s", p, e)
        _CACHE = {"source": "", "occupations": [], "industries": [], "url": ""}
        return _CACHE


def get_targets_for_pathfinder() -> list[dict]:
    """
    Return list of target career options for pathfinder dropdown, grouped by industry.
    Each item: { value, label, group } where group is industry name.
    Uses scraped O*NET data when available; otherwise returns empty (caller uses path-based fallback).
    """
    data = load_labor_occupations()
    occupations = data.get("occupations") or []
    if not occupations:
        return []
    out = []
    for o in occupations:
        out.append({
            "value": o.get("value") or o.get("soc_code", "").lower().replace("-", "_"),
            "label": o.get("label") or o.get("title", ""),
            "group": o.get("industry", "Other"),
            "soc_code": o.get("soc_code"),
            "industry_key": o.get("industry_key"),
        })
    return out


def find_occupation_by_title_or_soc(title: Optional[str] = None, soc_code: Optional[str] = None) -> Optional[dict]:
    """Find a labor occupation by title (fuzzy) or SOC code. For roadmap target matching."""
    data = load_labor_occupations()
    occupations = data.get("occupations") or []
    if not occupations:
        return None
    title_clean = (title or "").strip().lower()
    soc_clean = (soc_code or "").strip()
    for o in occupations:
        if soc_clean and o.get("soc_code", "").strip() == soc_clean:
            return o
        if title_clean and title_clean in (o.get("title") or "").lower():
            return o
        if title_clean and title_clean in (o.get("label") or "").lower():
            return o
    return None
