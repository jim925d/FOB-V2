"""
Career Pathfinder dropdown data: roles (MOS + civilian), certifications, targets.
All MOSs from progression paths + static titles; industries from paths.
"""

import logging
from fastapi import APIRouter

from app.data.progression_paths import (
    CAREER_PROGRESSION_PATHS,
)
from app.data.mos_titles import get_mos_title
from app.data.labor_occupations_loader import get_targets_for_pathfinder

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/career", tags=["Career Pathfinder"])


def _all_mos_codes() -> set[str]:
    """All MOS/AFSC/Rating codes from progression paths."""
    codes = set()
    for path in CAREER_PROGRESSION_PATHS:
        codes.update(path.get("source_mos_codes") or [])
    return codes


@router.get("/roles", summary="List roles for pathfinder (military + civilian)")
async def get_roles():
    """
    Return all roles for the Career Pathfinder dropdown: military (MOS) and civilian.
    Military list is built from all MOS codes in our progression paths so every
    option can generate a roadmap (with fallback path if needed).
    """
    military = []
    for code in sorted(_all_mos_codes()):
        title = get_mos_title(code)
        military.append({
            "code": code,
            "title": title,
            "value": code,
            "label": f"{code} — {title}",
            "group": "MILITARY",
        })
    civilian = []
    seen_roles = set()
    for path in CAREER_PROGRESSION_PATHS:
        for m in path.get("milestones") or []:
            if m.get("phase") == "entry_role":
                title = m.get("title") or ""
                if title and title not in seen_roles:
                    seen_roles.add(title)
                    cid = title.lower().replace(" ", "-").replace("/", "-")[:50]
                    civilian.append({
                        "value": cid,
                        "label": title,
                        "group": "CIVILIAN",
                    })
    if not civilian:
        civilian = [
            {"value": "project-manager", "label": "Project Manager", "group": "CIVILIAN"},
            {"value": "it-support", "label": "IT Support Specialist", "group": "CIVILIAN"},
            {"value": "logistics-coordinator", "label": "Logistics Coordinator", "group": "CIVILIAN"},
        ]
    # Return grouped format for frontend SearchableSelect (label + options)
    return [
        {"label": "Military", "options": [{"value": r["value"], "label": r["label"]} for r in military]},
        {"label": "Civilian", "options": [{"value": r["value"], "label": r["label"]} for r in civilian]},
    ]


@router.get("/certifications", summary="List certifications for pathfinder")
async def get_certifications():
    """Return certifications grouped by domain (from paths + static list)."""
    by_group = {}
    seen = set()
    for path in CAREER_PROGRESSION_PATHS:
        for m in path.get("milestones") or []:
            for c in m.get("certifications") or []:
                name = c.get("name") or ""
                if name and name not in seen:
                    seen.add(name)
                    group = "IT / Cyber"  # default
                    if "PMP" in name or "CAPM" in name or "Scrum" in name or "Six Sigma" in name:
                        group = "Project Management"
                    elif "EMT" in name or "NREMT" in name or "CNA" in name or "Phlebotomy" in name:
                        group = "Healthcare"
                    elif "CDL" in name or "OSHA" in name or "EPA" in name or "Welding" in name:
                        group = "Trades"
                    elif "SHRM" in name or "PHR" in name:
                        group = "Leadership / HR"
                    elif "CPA" in name or "CFA" in name or "Series" in name:
                        group = "Finance"
                    by_group.setdefault(group, []).append({
                        "value": name.lower().replace(" ", "-").replace("+", "plus")[:40],
                        "label": name,
                        "group": group,
                    })
    flat = []
    for group in ["IT / Cyber", "Project Management", "Healthcare", "Trades", "Leadership / HR", "Finance", "Other"]:
        flat.extend(by_group.get(group, []))
    static = [
        {"value": "comptia-aplus", "label": "CompTIA A+", "group": "IT / Cyber"},
        {"value": "comptia-secplus", "label": "CompTIA Security+", "group": "IT / Cyber"},
        {"value": "comptia-netplus", "label": "CompTIA Network+", "group": "IT / Cyber"},
        {"value": "pmp", "label": "PMP", "group": "Project Management"},
        {"value": "capm", "label": "CAPM", "group": "Project Management"},
    ]
    for s in static:
        if s["label"] not in seen:
            flat.append(s)
    return flat


def _targets_from_paths():
    """Build target list from progression paths (fallback when no labor data)."""
    by_industry = {}
    for path in CAREER_PROGRESSION_PATHS:
        ind = path.get("target_industry") or "other"
        ind_label = ind.replace("_", " ").title()
        by_industry.setdefault(ind, {"label": ind_label, "roles": []})
        target_m = next(
            (m for m in path.get("milestones") or [] if m.get("phase") == "target_role"),
            None,
        )
        if target_m:
            title = target_m.get("title") or path.get("path_name", "").split("→")[-1].strip()
            vid = title.lower().replace(" ", "-").replace("/", "-")[:50]
            if not any(r.get("value") == vid for r in by_industry[ind]["roles"]):
                by_industry[ind]["roles"].append({
                    "value": vid,
                    "label": title,
                    "group": ind_label,
                })
    flat = []
    for ind_key in sorted(by_industry.keys()):
        meta = by_industry[ind_key]
        for r in meta["roles"]:
            r["group"] = meta["label"]
            flat.append(r)
    return flat


@router.get("/targets", summary="List target careers for pathfinder")
async def get_targets():
    """
    Return target careers/industries for pathfinder dropdown.
    Uses scraped O*NET labor occupations when labor_occupations.json exists (run labor_occupations_scraper);
    otherwise uses progression paths + static fallback.
    """
    labor = get_targets_for_pathfinder()
    if labor:
        return [
            {"value": o["value"], "label": o["label"], "group": o["group"], "industry_key": o.get("industry_key")}
            for o in labor
        ]
    flat = _targets_from_paths()
    if not flat:
        flat = [
            {"value": "cybersecurity-analyst", "label": "Cybersecurity Analyst", "group": "Technology"},
            {"value": "software-developer", "label": "Software Developer", "group": "Technology"},
            {"value": "supply-chain-manager", "label": "Supply Chain Manager", "group": "Logistics"},
            {"value": "healthcare-admin", "label": "Healthcare Administrator", "group": "Healthcare"},
            {"value": "data-analyst", "label": "Data Analyst", "group": "Technology"},
        ]
    return flat
