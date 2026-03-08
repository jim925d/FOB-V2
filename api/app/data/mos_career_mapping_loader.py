"""
Load optional MOS → career options from an external mapping file.

Used when you build a keyword/skill-based mapping (e.g. MOS skills → career
role keywords) in another platform and import the result as JSON.
See app/data/mos_career_mapping_schema.md for format and usage.
"""

import json
import logging
from pathlib import Path
from typing import Optional

# #region agent log
# Write under skillbridge-api so log is created when API runs from that dir
_DEBUG_LOG_PATH = Path(__file__).resolve().parent.parent.parent / "debug-2af1a2.log"
def _debug_log(location: str, message: str, data: dict, hypothesis_id: str):
    try:
        import time
        line = json.dumps({"sessionId": "2af1a2", "timestamp": int(time.time() * 1000), "location": location, "message": message, "data": data, "hypothesisId": hypothesis_id}) + "\n"
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
# #endregion

logger = logging.getLogger(__name__)

# Default path: same directory as this module
_DEFAULT_MAPPING_PATH = Path(__file__).resolve().parent / "mos_career_mapping.json"


def _candidate_mapping_paths() -> list[Path]:
    """Return paths to check for the mapping file, in priority order."""
    candidates = []
    # Possible repo roots (API may be run from skillbridge-api or from FOB)
    roots = [
        Path(__file__).resolve().parent.parent.parent.parent,  # FOB if skillbridge-api is inside FOB
        Path.cwd(),
        Path.cwd().parent,
        Path(__file__).resolve().parent.parent.parent,  # skillbridge-api
    ]
    for root in roots:
        if not root:
            continue
        # Career Mapping folder (user-updated)
        p = root / "Career Mapping" / "mos_career_mapping.json"
        if p not in candidates:
            candidates.append(p)
        # MOS Mapping folder
        p2 = root / "Career Roadmap" / "MOS Mapping" / "mos_career_mapping.json"
        if p2 not in candidates:
            candidates.append(p2)
        # MOS Mapping pipeline output
        p3 = root / "Career Roadmap" / "MOS Mapping" / "output" / "mos_career_mapping.json"
        if p3 not in candidates:
            candidates.append(p3)
    candidates.append(_DEFAULT_MAPPING_PATH)
    return candidates

# In-memory cache: MOS code (upper) -> list of option dicts
_MOS_CAREER_MAPPING: dict[str, list[dict]] = {}
_LOADED = False


def get_mapping_path() -> Path:
    """Path to the mapping JSON file. Priority: env override > candidate paths (Career Mapping, MOS Mapping, etc.) > app/data."""
    from app.config import get_settings
    settings = get_settings()
    path_override = getattr(settings, "mos_career_mapping_path", None)
    if path_override:
        p = Path(path_override)
        if p.exists():
            return p
    for p in _candidate_mapping_paths():
        if p.exists():
            return p
    return _DEFAULT_MAPPING_PATH


def load_mos_career_mapping(path: Optional[Path] = None) -> dict[str, list[dict]]:
    """
    Load MOS -> career options from JSON file.
    Returns dict: mos_code (uppercase) -> list of option dicts.
    Empty dict if file missing or invalid.
    """
    global _LOADED
    if _LOADED:
        return _MOS_CAREER_MAPPING

    p = path or get_mapping_path()
    _LOADED = True
    # #region agent log
    _debug_log("load_mos_career_mapping", "resolve path", {"path": str(p), "exists": p.exists()}, "A")
    # #endregion
    if not p.exists():
        logger.warning(
            "MOS career mapping file not found at %s. Tried: %s. Set MOS_CAREER_MAPPING_PATH to the full path of mos_career_mapping.json to use your expanded mapping.",
            p,
            [str(x) for x in _candidate_mapping_paths()[:6]],
        )
        return _MOS_CAREER_MAPPING

    try:
        with open(p, encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load MOS career mapping from %s: %s", p, e)
        return _MOS_CAREER_MAPPING

    # Normalize: keys uppercase, value must be list of option dicts
    for mos, options in raw.items():
        if not isinstance(options, list):
            continue
        mos_upper = str(mos).strip().upper()
        if not mos_upper:
            continue
        valid = [
            o for o in options
            if isinstance(o, dict)
            and o.get("industry") and o.get("entry_role") and o.get("career_field")
        ]
        if valid:
            _MOS_CAREER_MAPPING[mos_upper] = valid

    # #region agent log
    _debug_log("load_mos_career_mapping", "after parse", {"path": str(p), "mos_count": len(_MOS_CAREER_MAPPING), "total_options": sum(len(v) for v in _MOS_CAREER_MAPPING.values())}, "C")
    # #endregion
    logger.info(
        "Loaded MOS career mapping from %s: %d MOS codes, %d total options",
        p,
        len(_MOS_CAREER_MAPPING),
        sum(len(v) for v in _MOS_CAREER_MAPPING.values()),
    )
    return _MOS_CAREER_MAPPING


def _normalize_industry_for_match(s: Optional[str]) -> str:
    """Normalize industry string for comparison (e.g. 'Logistics & Supply Chain' vs 'Logistics and Supply Chain')."""
    if not s or not str(s).strip():
        return ""
    t = str(s).strip().lower().replace(" & ", " ").replace(" and ", " ")
    return "_".join(t.split())


def get_options_for_mos(
    mos_code: str,
    industry_filter: Optional[str] = None,
) -> list[dict]:
    """
    Get career options for a MOS from the mapping file (if any).
    industry_filter: if set, only return options whose industry matches (case-insensitive, normalized).
    """
    mapping = load_mos_career_mapping()
    mos_upper = mos_code.strip().upper()
    options = mapping.get(mos_upper, [])
    # #region agent log
    _debug_log("get_options_for_mos", "before filter", {"mos_upper": mos_upper, "industry_filter": industry_filter, "options_before_filter": len(options)}, "B")
    # #endregion
    if not industry_filter or not industry_filter.strip():
        return list(options)

    want = _normalize_industry_for_match(industry_filter)
    out = [o for o in options if _normalize_industry_for_match(o.get("industry")) == want]
    # #region agent log
    _debug_log("get_options_for_mos", "after filter", {"industry_normalized": want, "options_after_filter": len(out)}, "D")
    # #endregion
    return out
