"""
Scrape target career/industry list from US labor data (O*NET).
O*NET is the US Department of Labor's occupational database (Creative Commons).
Run once to fetch Occupation Data and save to labor_occupations.json for pathfinder.
"""

import json
import logging
import re
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

# O*NET 30.2 Occupation Data (tab-delimited)
ONET_OCCUPATION_DATA_URL = "https://www.onetcenter.org/dl_files/database/db_30_2_text/Occupation%20Data.txt"

# SOC 2018 major group (first 2 digits) -> industry label for pathfinder grouping
SOC_MAJOR_TO_INDUSTRY = {
    "11": "Management",
    "13": "Business and Financial Operations",
    "15": "Computer and Mathematical",
    "17": "Architecture and Engineering",
    "19": "Life, Physical, and Social Science",
    "21": "Community and Social Service",
    "23": "Legal",
    "25": "Education, Training, and Library",
    "27": "Arts, Design, Entertainment, Sports, and Media",
    "29": "Healthcare Practitioners and Technical",
    "31": "Healthcare Support",
    "33": "Protective Service",
    "35": "Food Preparation and Serving",
    "37": "Building and Grounds Cleaning and Maintenance",
    "39": "Personal Care and Service",
    "41": "Sales and Related",
    "43": "Office and Administrative Support",
    "45": "Farming, Fishing, and Forestry",
    "47": "Construction and Extraction",
    "49": "Installation, Maintenance, and Repair",
    "51": "Production",
    "53": "Transportation and Material Moving",
}

# Normalize to pathfinder-style industry keys (for matching progression paths)
INDUSTRY_TO_PATHFINDER_KEY = {
    "Management": "business_finance",
    "Business and Financial Operations": "business_finance",
    "Computer and Mathematical": "technology",
    "Architecture and Engineering": "technology",
    "Life, Physical, and Social Science": "technology",
    "Community and Social Service": "government_public",
    "Legal": "government_public",
    "Education, Training, and Library": "education_training",
    "Arts, Design, Entertainment, Sports, and Media": "arts_media",
    "Healthcare Practitioners and Technical": "healthcare",
    "Healthcare Support": "healthcare",
    "Protective Service": "government_public",
    "Food Preparation and Serving": "hospitality",
    "Building and Grounds Cleaning and Maintenance": "trades_construction",
    "Personal Care and Service": "healthcare",
    "Sales and Related": "business_finance",
    "Office and Administrative Support": "business_finance",
    "Farming, Fishing, and Forestry": "trades_construction",
    "Construction and Extraction": "trades_construction",
    "Installation, Maintenance, and Repair": "trades_construction",
    "Production": "manufacturing",
    "Transportation and Material Moving": "logistics_supply_chain",
}


def _soc_major(soc_code: str) -> str:
    """Extract 2-digit major group from O*NET-SOC code (e.g. 15-1212.00 -> 15)."""
    if not soc_code:
        return ""
    match = re.match(r"^(\d{2})", soc_code.strip())
    return match.group(1) if match else ""


def run(output_path: Path | None = None, timeout: float = 30.0) -> dict:
    """
    Download O*NET Occupation Data and save target careers with industry.
    Returns summary: { "occupations": int, "industries": int, "path": str }.
    """
    if output_path is None:
        output_path = Path(__file__).resolve().parent.parent / "data" / "labor_occupations.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Fetching O*NET Occupation Data from %s", ONET_OCCUPATION_DATA_URL)
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        resp = client.get(ONET_OCCUPATION_DATA_URL)
        resp.raise_for_status()
        text = resp.text

    # Tab-delimited: first line is header
    lines = text.strip().split("\n")
    if not lines:
        logger.warning("Empty O*NET occupation data")
        rows = []
    else:
        headers = [h.strip().strip('"').lstrip("\ufeff") for h in lines[0].split("\t")]
        key_code = "O*NET-SOC Code" if "O*NET-SOC Code" in headers else (headers[0] if headers else "")
        key_title = "Title" if "Title" in headers else (headers[1] if len(headers) > 1 else "")
        key_desc = "Description" if "Description" in headers else (headers[2] if len(headers) > 2 else "")
        rows = []
        for line in lines[1:]:
            parts = [p.strip().strip('"') for p in line.split("\t")]
            if len(parts) >= 2:
                row = dict(zip(headers[: len(parts)], parts))
                rows.append(row)

    occupations = []
    seen_titles = set()
    for row in rows:
        if not row:
            continue
        code = (row.get(key_code) or row.get("O*NET-SOC Code", "")).strip()
        title = (row.get(key_title) or row.get("Title", "")).strip()
        desc = (row.get(key_desc) or row.get("Description", "")).strip()
        if not code or not title:
            continue
        if title in seen_titles:
            continue
        seen_titles.add(title)
        major = _soc_major(code)
        industry = SOC_MAJOR_TO_INDUSTRY.get(major, "Other")
        pathfinder_key = INDUSTRY_TO_PATHFINDER_KEY.get(industry, "other")
        value = title.lower().replace(" ", "-").replace("/", "-")[:60]
        value = re.sub(r"[^a-z0-9\-]", "", value) or code.lower().replace("-", "_")
        occupations.append({
            "soc_code": code,
            "title": title,
            "description": desc[:500] if desc else "",
            "industry": industry,
            "industry_key": pathfinder_key,
            "value": value,
            "label": title,
        })

    industries_seen = {o["industry"] for o in occupations}
    out = {
        "source": "O*NET 30.2",
        "url": ONET_OCCUPATION_DATA_URL,
        "occupations": occupations,
        "industries": sorted(industries_seen),
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    logger.info("Saved %d occupations, %d industries to %s", len(occupations), len(industries_seen), output_path)
    return {
        "occupations": len(occupations),
        "industries": len(industries_seen),
        "path": str(output_path),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run()
    print("Result:", result)
