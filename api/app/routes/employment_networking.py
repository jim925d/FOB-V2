"""
Employment Networking API — events by zip and local search by zip.
The FOB Platform

Endpoints:
  GET /api/v1/employment-networking/events  - Planned events for an org near a zip (mock/placeholder)
  GET /api/v1/employment-networking/local-search - Veteran networking opportunities by zip/state (DB then live API)
"""

import logging
import re
from typing import Optional, List

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.database import VeteranNetworkingResult, VeteranEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/employment-networking", tags=["Employment Networking"])

VALID_ORG_IDS = {"acp", "four-block", "vets-in-tech", "breakline"}


class EventItem(BaseModel):
    id: str
    title: str
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    org_id: str


class LocalSearchRow(BaseModel):
    name: str
    type: str  # e.g. "Event", "Organization", "Chapter", "Resource"
    organization: Optional[str] = None  # parent org if part of larger org
    location: Optional[str] = None
    date_or_description: Optional[str] = None
    link: str


def _mock_events_for_org_and_zip(org_id: str, zip_code: str) -> List[dict]:
    """Return curated events per org. Replace with real Eventbrite/Meetup/org API later."""
    _EVENTS = {
        "acp": [
            {"id": "acp-1", "title": "ACP Mentor Orientation — Virtual", "date": "Monthly", "time": "12:00 PM ET", "location": "Virtual (Zoom)", "url": "https://www.acp-usa.org/mentoring-program/mentors", "org_id": "acp"},
            {"id": "acp-2", "title": "ACP Protégé Info Session", "date": "Ongoing enrollment", "time": None, "location": "Virtual", "url": "https://www.acp-usa.org/mentoring-program/veterans", "org_id": "acp"},
        ],
        "four-block": [
            {"id": "fb-1", "title": "Four Block Career Readiness Program", "date": "Spring & Fall semesters", "time": "Evenings", "location": "Multiple cities & virtual", "url": "https://fourblock.org/programs/", "org_id": "four-block"},
            {"id": "fb-2", "title": "Four Block Networking Night", "date": "Quarterly", "time": "6:00 PM local", "location": "Chapter cities", "url": "https://fourblock.org", "org_id": "four-block"},
        ],
        "vets-in-tech": [
            {"id": "vit-1", "title": "VetsinTech Web Dev Cohort", "date": "Rolling enrollment", "time": None, "location": "Virtual", "url": "https://vetsintech.co/vit-vets/", "org_id": "vets-in-tech"},
            {"id": "vit-2", "title": "VetsinTech Cybersecurity Training", "date": "Rolling enrollment", "time": None, "location": "Virtual", "url": "https://vetsintech.co/vit-vets/", "org_id": "vets-in-tech"},
            {"id": "vit-3", "title": "VetsinTech Local Chapter Meetup", "date": "Monthly", "time": "6:30 PM local", "location": "50+ cities nationwide", "url": "https://vetsintech.co/chapters/", "org_id": "vets-in-tech"},
        ],
        "breakline": [
            {"id": "bl-1", "title": "Breakline Career Program — Virtual Cohort", "date": "Monthly start dates", "time": "Flexible", "location": "Virtual", "url": "https://breakline.org/programs/", "org_id": "breakline"},
            {"id": "bl-2", "title": "Breakline Employer Showcase", "date": "Quarterly", "time": "1:00 PM ET", "location": "Virtual", "url": "https://breakline.org", "org_id": "breakline"},
        ],
    }
    return _EVENTS.get(org_id, [])


@router.get("/events", summary="Events for an org near a zip code")
async def get_events(
    zip_code: str = Query(..., min_length=5, max_length=10, description="ZIP code (5 or 9 digit)"),
    org_id: str = Query(..., description="Org id: acp | four-block | vets-in-tech | breakline"),
):
    """
    Returns planned events for the given national org that are near the given zip.
    Currently returns empty list; integrate Eventbrite/Meetup/org-specific APIs to populate.
    """
    zip_code = zip_code.strip()
    org_id = org_id.strip().lower()
    if org_id not in VALID_ORG_IDS:
        return {"events": [], "zip": zip_code, "org_id": org_id}
    events = _mock_events_for_org_and_zip(org_id, zip_code)
    return {"events": events, "zip": zip_code, "org_id": org_id}


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
    "VA": "Virginia", "WA": "Washington", "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}

# 3-digit ZIP prefix -> state mapping (covers all US zip ranges)
def _build_zip3_to_state() -> dict:
    """Build comprehensive ZIP-3 prefix to state mapping."""
    m: dict = {}
    _ranges = [
        ("AL", 350, 369), ("AK", 995, 999), ("AZ", 850, 865), ("AR", 716, 729),
        ("CA", 900, 961), ("CO", 800, 816), ("CT", 60, 69), ("DE", 197, 199),
        ("FL", 320, 349), ("GA", 300, 319), ("HI", 967, 968), ("ID", 832, 838),
        ("IL", 600, 629), ("IN", 460, 479), ("IA", 500, 528), ("KS", 660, 679),
        ("KY", 400, 427), ("LA", 700, 714), ("ME", 39, 49), ("MD", 206, 219),
        ("MA", 10, 27), ("MI", 480, 499), ("MN", 550, 567), ("MS", 386, 397),
        ("MO", 630, 658), ("MT", 590, 599), ("NE", 680, 693), ("NV", 889, 898),
        ("NH", 30, 38), ("NJ", 70, 89), ("NM", 870, 884), ("NY", 100, 149),
        ("NC", 270, 289), ("ND", 580, 588), ("OH", 430, 458), ("OK", 730, 749),
        ("OR", 970, 979), ("PA", 150, 196), ("RI", 28, 29), ("SC", 290, 299),
        ("SD", 570, 577), ("TN", 370, 385), ("TX", 750, 799), ("UT", 840, 847),
        ("VT", 50, 59), ("VA", 220, 246), ("WA", 980, 994), ("WV", 247, 268),
        ("WI", 530, 549), ("WY", 820, 831), ("DC", 200, 205),
    ]
    for state, lo, hi in _ranges:
        for p in range(lo, hi + 1):
            m[f"{p:03d}"] = state
    return m

ZIP3_TO_STATE = _build_zip3_to_state()


def _build_search_query(zip_code: Optional[str], radius_miles: Optional[int], state: Optional[str]) -> str:
    """Build search query from zip, radius, or state. Matches Google query that returns local results."""
    base = "veteran networking events"
    if state:
        state_name = US_STATES.get(state.upper(), state) if len(state) == 2 else state
        return f"{base} {state_name}"
    if zip_code and radius_miles and radius_miles in (10, 25, 50):
        return f"{base} within {radius_miles} miles of {zip_code}"
    if zip_code:
        return f"{base} by zip {zip_code}"
    return base


def _google_search_url(zip_code: Optional[str], radius_miles: Optional[int], state: Optional[str]) -> str:
    """Build a Google search URL for the same query (fallback when API has no results or no key)."""
    from urllib.parse import quote_plus
    q = _build_search_query(zip_code, radius_miles, state)
    return f"https://www.google.com/search?q={quote_plus(q)}"


def _extract_date_from_text(text: str) -> Optional[str]:
    """Extract a short date/time string for display on the same line as the event name."""
    if not text or len(text) < 4:
        return None
    # (Feb 25, 5:30 PM) or Feb 25, 5:30 PM or Feb 25 — allow optional leading paren
    m = re.search(
        r"(?:\(|\b)((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s*(?:\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))?)",
        text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    # Month DD at H:MM PM
    m = re.search(
        r"(?:\(|\b)((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}\s+at\s+\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))",
        text,
        re.IGNORECASE,
    )
    if m:
        return m.group(1).strip()
    # MM/DD or MM/DD/YY
    m = re.search(r"\b(\d{1,2}/\d{1,2}(?:/\d{2,4})?)\b", text)
    if m:
        return m.group(1)
    return None


def _name_with_date_on_same_line(title: str, snippet: str) -> str:
    """If snippet (or title) contains a date, return 'Title (Date)' so UI can show date on same line."""
    date_str = _extract_date_from_text(snippet) or _extract_date_from_text(title)
    if not date_str or date_str in title:
        return title
    return f"{title} ({date_str})"


def _item_to_row(item: dict) -> dict:
    """Convert a search result item (Google CSE or SerpAPI) to our table row format."""
    title = item.get("title") or ""
    link = item.get("link") or ""
    snippet = item.get("snippet") or ""
    type_ = "Resource"
    if "event" in title.lower() or "event" in snippet.lower() or "meeting" in title.lower():
        type_ = "Event"
    elif "chapter" in title.lower() or "chapter" in snippet.lower():
        type_ = "Chapter"
    elif "vfw" in title.lower() or "american legion" in title.lower() or "dav" in title.lower():
        type_ = "Organization"
    org_name: Optional[str] = None
    if "VFW" in title or "VFW" in snippet:
        org_name = "Veterans of Foreign Wars"
    elif "American Legion" in title or "American Legion" in snippet:
        org_name = "American Legion"
    elif "DAV" in title or "Disabled American Veterans" in snippet:
        org_name = "Disabled American Veterans"
    name = _name_with_date_on_same_line(title, snippet)
    date_str = _extract_date_from_text(snippet) or _extract_date_from_text(title)
    return {
        "name": name,
        "type": type_,
        "organization": org_name,
        "location": None,
        "date": date_str,
        "date_or_description": snippet[:200] if snippet else None,
        "link": link,
    }


async def _google_cse_search(query: str, api_key: str, cx: str) -> List[dict]:
    """Fetch results from Google Custom Search JSON API; request two pages (up to 20) to better match Google SERP."""
    import httpx
    url = "https://www.googleapis.com/customsearch/v1"
    all_items: List[dict] = []
    for start in (1, 11):
        params = {"key": api_key, "cx": cx, "q": query, "num": 10, "start": start}
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            logger.warning("Google CSE request failed", error=str(e), start=start)
            break
        items = data.get("items") or []
        if not items:
            break
        all_items.extend(items)
    return [_item_to_row(it) for it in all_items]


async def _serp_search(query: str, api_key: str) -> List[dict]:
    """Fetch results via SerpAPI (fallback); request more results to better match Google SERP."""
    import httpx
    url = "https://serpapi.com/search"
    params = {"q": query, "api_key": api_key, "engine": "google", "num": 25}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception as e:
        logger.warning("SerpAPI request failed", error=str(e))
        return []
    organic = data.get("organic_results") or []
    return [_item_to_row(it) for it in organic]


# ---------------------------------------------------------------------------
# Curated veteran networking events by state
# ---------------------------------------------------------------------------
_EVENTS_BY_STATE: dict = {
    "CO": [
        {"name": "Denver Veteran Career Fair", "type": "Event", "organization": "RecruitMilitary", "location": "Empower Field, Denver, CO", "date_or_description": "Quarterly hiring event connecting veterans with 50+ employers. Free registration, resume reviews on-site.", "link": "https://recruitmilitary.com/events"},
        {"name": "VFW Post 1 Monthly Networking", "type": "Event", "organization": "VFW Post 1 Denver", "location": "1545 S Broadway, Denver, CO", "date_or_description": "Monthly social and networking night for veterans. First Thursday of each month, 6 PM.", "link": "https://www.vfw.org/find-a-post"},
        {"name": "Colorado Springs Military Transition Summit", "type": "Event", "organization": "Hire Heroes USA", "location": "Colorado Springs, CO", "date_or_description": "Full-day career workshop for transitioning service members from Fort Carson, Peterson, and Schriever.", "link": "https://www.hireheroesusa.org"},
        {"name": "Team Rubicon Colorado Chapter Meetup", "type": "Event", "organization": "Team Rubicon", "location": "Denver metro area", "date_or_description": "Monthly volunteer meetup and disaster response training. Open to all veterans.", "link": "https://teamrubiconusa.org"},
        {"name": "Bunker Labs Denver: Veterans in Entrepreneurship", "type": "Event", "organization": "Bunker Labs", "location": "Denver, CO (virtual option)", "date_or_description": "Monthly meetup for veteran entrepreneurs. Pitch nights, mentorship, and startup networking.", "link": "https://bunkerlabs.org"},
        {"name": "American Legion Post 1 Westminster", "type": "Event", "organization": "American Legion", "location": "Westminster, CO", "date_or_description": "Weekly veteran gatherings. Career support, community service projects, and social events.", "link": "https://www.legion.org/posts"},
        {"name": "Aurora Vet Center Group Events", "type": "Event", "organization": "VA Vet Center", "location": "1536 S Potomac St, Aurora, CO", "date_or_description": "Peer support groups, readjustment counseling, and veteran networking for combat vets and families.", "link": "https://www.vetcenter.va.gov"},
    ],
    "TX": [
        {"name": "DAV/RecruitMilitary Dallas Veteran Job Fair", "type": "Event", "organization": "DAV & RecruitMilitary", "location": "AT&T Stadium, Arlington, TX", "date_or_description": "Major quarterly hiring event. 60+ employers, on-site resume help, career workshops.", "link": "https://recruitmilitary.com/events"},
        {"name": "San Antonio Military Transition Mixer", "type": "Event", "organization": "USAA & Hire Heroes", "location": "San Antonio, TX", "date_or_description": "Networking mixer for transitioning military from JBSA. Employer panels and mentorship matching.", "link": "https://www.hireheroesusa.org"},
        {"name": "VFW Post 76 San Antonio Networking Night", "type": "Event", "organization": "VFW", "location": "San Antonio, TX", "date_or_description": "Monthly veteran social and networking event. All branches welcome.", "link": "https://www.vfw.org/find-a-post"},
        {"name": "Houston Veteran Entrepreneur Meetup", "type": "Event", "organization": "Bunker Labs Houston", "location": "Houston, TX", "date_or_description": "Monthly meetup for veteran-owned businesses. Pitch practice, investor connections, peer mentorship.", "link": "https://bunkerlabs.org"},
        {"name": "Fort Hood/Cavazos Career Skills Program Fair", "type": "Event", "organization": "U.S. Army MWR", "location": "Fort Cavazos, TX", "date_or_description": "Bi-annual career fair for soldiers in transition. SkillBridge and apprenticeship opportunities.", "link": "https://www.armymwr.com"},
    ],
    "CA": [
        {"name": "Los Angeles Veteran Career Fair", "type": "Event", "organization": "RecruitMilitary", "location": "Dodger Stadium, Los Angeles, CA", "date_or_description": "Quarterly hiring event with 50+ employers seeking veteran talent.", "link": "https://recruitmilitary.com/events"},
        {"name": "VetsinTech SF Bay Area Chapter Meetup", "type": "Event", "organization": "VetsinTech", "location": "San Francisco, CA", "date_or_description": "Monthly networking for veterans in tech. Coding workshops, career panels, and employer showcases.", "link": "https://vetsintech.co/chapters/"},
        {"name": "Camp Pendleton Transition Career Fair", "type": "Event", "organization": "Marine Corps TAPS", "location": "Camp Pendleton, CA", "date_or_description": "Career fair for transitioning Marines. 40+ employers, SkillBridge info, and resume workshops.", "link": "https://www.usmc-mccs.org"},
        {"name": "San Diego Veteran Networking Breakfast", "type": "Event", "organization": "San Diego Military Advisory Council", "location": "San Diego, CA", "date_or_description": "Monthly breakfast networking event. Defense industry, tech, and government employers.", "link": "https://sdmac.org"},
        {"name": "Sacramento Region Veteran Job Fair", "type": "Event", "organization": "CalVet & EDD", "location": "Sacramento, CA", "date_or_description": "State-sponsored veteran hiring event. State and federal agencies, private employers, resume reviews.", "link": "https://www.calvet.ca.gov"},
    ],
    "VA": [
        {"name": "Northern Virginia Veteran Networking Event", "type": "Event", "organization": "Hire Heroes USA", "location": "Arlington, VA", "date_or_description": "Monthly networking for veterans targeting DC metro employers. Defense, tech, and consulting.", "link": "https://www.hireheroesusa.org"},
        {"name": "Fort Belvoir Transition Career Fair", "type": "Event", "organization": "Army Community Service", "location": "Fort Belvoir, VA", "date_or_description": "Quarterly career fair for transitioning soldiers and military spouses.", "link": "https://www.armymwr.com"},
        {"name": "Hampton Roads Veteran Job Fair", "type": "Event", "organization": "RecruitMilitary", "location": "Norfolk, VA", "date_or_description": "Major hiring event near Naval Station Norfolk. Shipbuilding, defense, and tech employers.", "link": "https://recruitmilitary.com/events"},
        {"name": "American Legion Post 24 Alexandria", "type": "Event", "organization": "American Legion", "location": "Alexandria, VA", "date_or_description": "Weekly veteran gatherings with career support, mentorship pairing, and community networking.", "link": "https://www.legion.org/posts"},
    ],
    "FL": [
        {"name": "Tampa Bay Veteran Career Fair", "type": "Event", "organization": "RecruitMilitary", "location": "Raymond James Stadium, Tampa, FL", "date_or_description": "Quarterly hiring event. Major employers including MacDill AFB contractors.", "link": "https://recruitmilitary.com/events"},
        {"name": "Jacksonville Military Transition Summit", "type": "Event", "organization": "Hire Heroes USA", "location": "Jacksonville, FL", "date_or_description": "Full-day career workshop for NAS Jax and Mayport transitioning service members.", "link": "https://www.hireheroesusa.org"},
        {"name": "VFW Post 39 St. Petersburg Networking", "type": "Event", "organization": "VFW", "location": "St. Petersburg, FL", "date_or_description": "Monthly veteran social and career networking. All branches and eras welcome.", "link": "https://www.vfw.org/find-a-post"},
        {"name": "Miami Bunker Labs Veteran Startup Night", "type": "Event", "organization": "Bunker Labs Miami", "location": "Miami, FL", "date_or_description": "Monthly meetup for veteran entrepreneurs. Pitch competitions and investor networking.", "link": "https://bunkerlabs.org"},
    ],
    "NC": [
        {"name": "Fort Liberty Transition Career Fair", "type": "Event", "organization": "Army MWR", "location": "Fort Liberty (Bragg), NC", "date_or_description": "Quarterly career fair for transitioning soldiers. 80+ employers, SkillBridge partners.", "link": "https://www.armymwr.com"},
        {"name": "Raleigh-Durham Veteran Networking Mixer", "type": "Event", "organization": "Four Block", "location": "Raleigh, NC", "date_or_description": "Quarterly networking event connecting veterans with Research Triangle employers.", "link": "https://fourblock.org"},
        {"name": "Camp Lejeune Marine Transition Fair", "type": "Event", "organization": "Marine Corps TAPS", "location": "Camp Lejeune, NC", "date_or_description": "Career fair for transitioning Marines and sailors. Defense and civilian employers.", "link": "https://www.usmc-mccs.org"},
    ],
    "GA": [
        {"name": "Atlanta Veteran Career Fair", "type": "Event", "organization": "RecruitMilitary", "location": "Mercedes-Benz Stadium, Atlanta, GA", "date_or_description": "Quarterly hiring event with Fortune 500 employers actively seeking veteran talent.", "link": "https://recruitmilitary.com/events"},
        {"name": "Fort Stewart/Hunter Transition Summit", "type": "Event", "organization": "Army Community Service", "location": "Fort Stewart, GA", "date_or_description": "Career workshops and employer meet-and-greets for 3rd Infantry Division soldiers.", "link": "https://www.armymwr.com"},
        {"name": "VetsinTech Atlanta Chapter Meetup", "type": "Event", "organization": "VetsinTech", "location": "Atlanta, GA", "date_or_description": "Monthly tech networking for veterans. Coding workshops and tech employer connections.", "link": "https://vetsintech.co/chapters/"},
    ],
    "WA": [
        {"name": "Seattle Veteran Career Fair", "type": "Event", "organization": "RecruitMilitary", "location": "T-Mobile Park, Seattle, WA", "date_or_description": "Quarterly hiring event. Amazon, Microsoft, Boeing, and 40+ employers.", "link": "https://recruitmilitary.com/events"},
        {"name": "JBLM Military Transition Career Fair", "type": "Event", "organization": "Army MWR", "location": "Joint Base Lewis-McChord, WA", "date_or_description": "Major transition fair for JBLM service members. 60+ employers, SkillBridge info.", "link": "https://www.armymwr.com"},
        {"name": "VetsinTech Seattle Chapter", "type": "Event", "organization": "VetsinTech", "location": "Seattle, WA", "date_or_description": "Monthly meetup for veterans in Pacific NW tech. Cloud, cybersecurity, and startup networking.", "link": "https://vetsintech.co/chapters/"},
    ],
    "NY": [
        {"name": "NYC Veteran Career Fair", "type": "Event", "organization": "RecruitMilitary", "location": "Citi Field, New York, NY", "date_or_description": "Major quarterly hiring event. Finance, tech, healthcare, and government employers.", "link": "https://recruitmilitary.com/events"},
        {"name": "Four Block NYC Career Readiness Program", "type": "Event", "organization": "Four Block", "location": "New York, NY", "date_or_description": "Semester-long career program with corporate mentors. Weekly sessions at NYC universities.", "link": "https://fourblock.org"},
        {"name": "ACP NYC Mentor Matching Reception", "type": "Event", "organization": "American Corporate Partners", "location": "New York, NY", "date_or_description": "Annual reception pairing veterans with Fortune 500 mentors. Networking and career coaching.", "link": "https://www.acp-usa.org"},
    ],
    "IL": [
        {"name": "Chicago Veteran Career Fair", "type": "Event", "organization": "RecruitMilitary", "location": "Soldier Field, Chicago, IL", "date_or_description": "Quarterly hiring event. Manufacturing, tech, finance, and healthcare employers.", "link": "https://recruitmilitary.com/events"},
        {"name": "Bunker Labs Chicago Veteran Startup Night", "type": "Event", "organization": "Bunker Labs", "location": "Chicago, IL", "date_or_description": "Monthly meetup for veteran entrepreneurs. Bunker Labs HQ city with strong startup community.", "link": "https://bunkerlabs.org"},
        {"name": "Great Lakes Naval Station Transition Fair", "type": "Event", "organization": "Navy Fleet & Family", "location": "Naval Station Great Lakes, IL", "date_or_description": "Career fair for transitioning sailors. Midwest employers and apprenticeship programs.", "link": "https://www.navymwr.org"},
    ],
}

# Nationwide fallback events (used for states without specific data)
_NATIONWIDE_EVENTS: List[dict] = [
    {"name": "Hire Heroes USA Virtual Career Workshop", "type": "Event", "organization": "Hire Heroes USA", "location": "Virtual (nationwide)", "date_or_description": "Weekly virtual workshops: resume building, interview prep, LinkedIn optimization. Free for all veterans.", "link": "https://www.hireheroesusa.org"},
    {"name": "RecruitMilitary Virtual Career Fair", "type": "Event", "organization": "RecruitMilitary", "location": "Virtual (nationwide)", "date_or_description": "Monthly online career fair connecting veterans with employers. Chat with recruiters from home.", "link": "https://recruitmilitary.com/events"},
    {"name": "American Legion Post Networking", "type": "Event", "organization": "American Legion", "location": "12,500+ posts nationwide", "date_or_description": "Local post events include career workshops, networking nights, and community service. Find your nearest post.", "link": "https://www.legion.org/posts"},
    {"name": "VFW Post Community Events", "type": "Event", "organization": "Veterans of Foreign Wars", "location": "6,000+ posts nationwide", "date_or_description": "VFW posts host career fairs, networking mixers, and transition support events. Find a post near you.", "link": "https://www.vfw.org/find-a-post"},
    {"name": "VetsinTech Virtual Training & Networking", "type": "Event", "organization": "VetsinTech", "location": "Virtual (nationwide)", "date_or_description": "Free virtual tech training in web dev, cybersecurity, cloud, and AI. Monthly networking events.", "link": "https://vetsintech.co"},
    {"name": "Breakline Virtual Career Cohort", "type": "Event", "organization": "Breakline", "location": "Virtual (nationwide)", "date_or_description": "Free virtual career development program. Monthly cohorts with employer connections in defense tech and beyond.", "link": "https://breakline.org"},
    {"name": "SCORE Veteran Business Mentoring", "type": "Event", "organization": "SCORE / SBA", "location": "300+ chapters nationwide", "date_or_description": "Free one-on-one mentoring for veteran entrepreneurs. Local workshops, webinars, and business plan reviews.", "link": "https://www.score.org/content/veteran-resources"},
]


def _get_curated_events(state: Optional[str]) -> List[dict]:
    """Return curated events for a state, with nationwide events appended."""
    state_events = _EVENTS_BY_STATE.get(state, []) if state else []
    # Always append a few nationwide/virtual events
    return state_events + _NATIONWIDE_EVENTS


async def _serp_search_veteran_networking(
    zip_code: Optional[str] = None,
    radius_miles: Optional[int] = None,
    state: Optional[str] = None,
) -> List[dict]:
    """Get veteran networking search results from Google (CSE or SerpAPI) or return curated events."""
    query = _build_search_query(zip_code, radius_miles, state)
    settings = get_settings()
    rows: List[dict] = []

    # 1) Prefer Google Custom Search (results directly from Google)
    if settings.google_cse_api_key and settings.google_cse_cx:
        rows = await _google_cse_search(query, settings.google_cse_api_key, settings.google_cse_cx)
        if rows:
            return rows
        logger.debug("Google CSE returned no items -- using curated events")
    # 2) Fallback to SerpAPI if configured
    elif settings.serp_api_key:
        rows = await _serp_search(query, settings.serp_api_key)
        if rows:
            return rows
    # 3) No API or no results: return curated events for the state (with date when extractable)
    resolved_state = state or _zip_to_state(zip_code)
    rows = _get_curated_events(resolved_state)
    for r in rows:
        r.setdefault("date", _extract_date_from_text(r.get("date_or_description") or ""))
    return rows


def _get_session_factory(request: Request):
    """Return async session factory if DB is available."""
    return getattr(request.app.state, "session_factory", None)


def _db_row_to_api_row(r: VeteranNetworkingResult) -> dict:
    """Convert VeteranNetworkingResult to local-search API row shape; date on same line as name when present."""
    name = _name_with_date_on_same_line(r.title or "", r.snippet or "")
    date_str = _extract_date_from_text(r.snippet or "") or _extract_date_from_text(r.title or "")
    return {
        "name": name,
        "type": r.result_type or "Resource",
        "organization": r.organization,
        "location": r.location_text,
        "date": date_str,
        "date_or_description": (r.snippet or "")[:200] if r.snippet else None,
        "link": r.link,
    }


def _veteran_event_to_api_row(e: VeteranEvent) -> dict:
    """Convert VeteranEvent to local-search API row shape; use event_date when set."""
    date_str = None
    if e.event_date:
        date_str = e.event_date.strftime("%Y-%m-%d") if hasattr(e.event_date, "strftime") else str(e.event_date)
        if e.event_time:
            date_str = f"{date_str} {e.event_time}"
    if not date_str:
        date_str = _extract_date_from_text(e.snippet or "") or _extract_date_from_text(e.title or "")
    return {
        "name": e.title or "",
        "type": e.result_type or "Event",
        "organization": e.organization,
        "location": e.location_text,
        "date": date_str,
        "date_or_description": (e.snippet or "")[:200] if e.snippet else None,
        "link": e.link,
    }


async def _local_search_from_db(session: AsyncSession, state: str) -> List[dict]:
    """Query veteran_events (Supabase) first, then veteran_networking_results; return API-shaped rows with dates."""
    if not state or state not in US_STATES:
        return []
    # Prefer veteran_events (Supabase) when table exists
    try:
        q = (
            select(VeteranEvent)
            .where(VeteranEvent.state_code == state)
            .order_by(VeteranEvent.scraped_at.desc())
            .limit(100)
        )
        result = await session.execute(q)
        rows = result.scalars().all()
        if rows:
            return [_veteran_event_to_api_row(r) for r in rows]
    except Exception as e:
        logger.debug("veteran_events query failed, falling back to veteran_networking_results", error=str(e))
    q = (
        select(VeteranNetworkingResult)
        .where(VeteranNetworkingResult.search_state == state)
        .order_by(VeteranNetworkingResult.scraped_at.desc())
        .limit(50)
    )
    result = await session.execute(q)
    rows = result.scalars().all()
    return [_db_row_to_api_row(r) for r in rows]


def _zip_to_state(zip_code: Optional[str]) -> Optional[str]:
    """Map ZIP to state using first 3 digits (approximate)."""
    if not zip_code or len(zip_code) < 3:
        return None
    prefix = zip_code.strip()[:3]
    return ZIP3_TO_STATE.get(prefix)


def _prioritize_by_zip(rows: List[dict], zip_code: Optional[str]) -> List[dict]:
    """Put results that mention the given ZIP (in name, location, or description) at the top."""
    if not zip_code or not rows:
        return rows
    zip_str = zip_code.strip()
    in_zip: List[dict] = []
    other: List[dict] = []
    for r in rows:
        name = (r.get("name") or "")
        loc = (r.get("location") or "")
        desc = (r.get("date_or_description") or "")
        combined = f"{name} {loc} {desc}"
        if zip_str in combined:
            in_zip.append(r)
        else:
            other.append(r)
    return in_zip + other


@router.get("/local-search", summary="Veteran networking opportunities by zip, radius, or state")
async def local_search(
    request: Request,
    zip_code: Optional[str] = Query(None, min_length=5, max_length=10, description="ZIP code (optional if state provided)"),
    radius_miles: Optional[int] = Query(None, description="Expand search: 10, 25, or 50 miles from ZIP"),
    state: Optional[str] = Query(None, min_length=2, max_length=2, description="2-letter state code (e.g. CA); search by state instead of ZIP"),
):
    """
    Returns veteran networking opportunities. Prefer scraped table by state; fallback to live Google/SerpAPI.
    Use zip_code (maps to state), zip_code + radius_miles (10|25|50), or state. Table fields: name, type, organization, location, link.
    """
    zip_code = (zip_code or "").strip() or None
    state = (state or "").strip().upper() or None
    if not zip_code and not state:
        return {"zip": None, "state": None, "radius_miles": None, "results": [], "message": "Provide zip_code or state."}
    if radius_miles is not None and radius_miles not in (10, 25, 50):
        radius_miles = None
    query_state = state or _zip_to_state(zip_code)
    # Prefer stored results (veteran_events from weekly scrape) so users see actual Google-captured events.
    # Fall back to live Google/SerpAPI or curated events when DB is empty.
    settings = get_settings()
    has_search_api = bool(settings.google_cse_api_key and settings.google_cse_cx) or bool(settings.serp_api_key)
    rows: List[dict] = []
    factory = _get_session_factory(request)
    if query_state and factory:
        try:
            async with factory() as session:
                rows = await _local_search_from_db(session, query_state)
        except Exception as e:
            logger.warning("DB lookup for local-search failed", error=str(e))
    if not rows and has_search_api:
        rows = await _serp_search_veteran_networking(zip_code=zip_code, radius_miles=radius_miles, state=state)
    if not rows:
        rows = await _serp_search_veteran_networking(zip_code=zip_code, radius_miles=radius_miles, state=state)
    # Prioritize results that mention the user's ZIP (actual events in that zip at top)
    rows = _prioritize_by_zip(rows, zip_code)
    return {"zip": zip_code, "state": state or query_state or None, "radius_miles": radius_miles, "results": rows}
