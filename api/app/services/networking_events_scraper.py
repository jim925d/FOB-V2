"""
Veteran networking events — weekly scrape of Google results per state.
Stores results in veteran_networking_results for the local-search endpoint to read.
"""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.database import VeteranNetworkingResult, VeteranEvent

logger = logging.getLogger(__name__)

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    "DC": "District of Columbia",
}


async def _fetch_search_results(query: str) -> list:
    """Run one search via Google CSE or SerpAPI; return list of row dicts (name, link, type, etc.)."""
    from app.routes.employment_networking import _google_cse_search, _serp_search
    settings = get_settings()
    if settings.google_cse_api_key and settings.google_cse_cx:
        return await _google_cse_search(query, settings.google_cse_api_key, settings.google_cse_cx)
    if settings.serp_api_key:
        return await _serp_search(query, settings.serp_api_key)
    return []


def _row_to_model(state_code: str, row: dict) -> VeteranNetworkingResult:
    """Convert API row dict to VeteranNetworkingResult model."""
    return VeteranNetworkingResult(
        title=row.get("name") or "",
        link=row.get("link") or "",
        snippet=(row.get("date_or_description") or "")[:2000],
        result_type=row.get("type") or "Resource",
        organization=row.get("organization"),
        location_text=row.get("location"),
        search_state=state_code,
        search_zip=None,
        scraped_at=datetime.utcnow(),
    )


def _row_to_veteran_event(state_code: str, row: dict) -> VeteranEvent:
    """Convert API row dict to VeteranEvent (Supabase veteran_events table)."""
    return VeteranEvent(
        title=row.get("name") or "",
        link=row.get("link") or "",
        snippet=(row.get("date_or_description") or "")[:2000],
        result_type=row.get("type") or "Event",
        organization=row.get("organization"),
        location_text=row.get("location"),
        state_code=state_code,
        zip_code=None,
        event_date=None,  # optional: parse from snippet/title if needed
        event_time=None,
        scraped_at=datetime.utcnow(),
    )


async def run_weekly_scrape(session: AsyncSession) -> dict:
    """
    Scrape veteran networking events for each state. Writes to veteran_events (Supabase)
    and veteran_networking_results (legacy). Call with an async session; one search per state, rate-limited.
    Returns {"states": 51, "inserted": N, "error": optional}.
    """
    from app.routes.employment_networking import _build_search_query
    settings = get_settings()
    if not settings.google_cse_api_key and not settings.serp_api_key:
        logger.warning("No Google CSE or SerpAPI key — skipping veteran networking scrape")
        return {"states": 0, "inserted": 0, "error": "No API key configured"}
    # Clear veteran_events (Supabase) for this run
    try:
        await session.execute(delete(VeteranEvent))
        await session.commit()
    except Exception as e:
        logger.warning("veteran_events table may not exist yet (run FOB Supabase migration)", error=str(e))
        await session.rollback()
    # Clear legacy table if it exists (same DB may only have veteran_events)
    try:
        await session.execute(delete(VeteranNetworkingResult))
        await session.commit()
    except Exception as e:
        logger.debug("veteran_networking_results clear skipped", error=str(e))
        await session.rollback()
    total = 0
    for state_code, state_name in US_STATES.items():
        query = _build_search_query(zip_code=None, radius_miles=None, state=state_code)
        rows = await _fetch_search_results(query)
        for row in rows:
            if not row.get("link"):
                continue
            session.add(_row_to_veteran_event(state_code, row))
            try:
                session.add(_row_to_model(state_code, row))
            except Exception:
                pass
            total += 1
        await session.commit()
        await asyncio.sleep(2)  # rate limit
    logger.info("Veteran networking scrape complete", states=len(US_STATES), inserted=total)
    return {"states": len(US_STATES), "inserted": total}
