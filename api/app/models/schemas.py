"""Pydantic schemas for API serialization."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─── Response Models ───

class ProgramBase(BaseModel):
    id: int
    company: str
    city: Optional[str] = None
    state: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    industry: Optional[str] = None
    nationwide: bool = False
    online: bool = False

    class Config:
        from_attributes = True


class ProgramSummary(ProgramBase):
    """Used in list views."""
    opportunity_type: Optional[str] = None
    delivery_method: Optional[str] = None
    duration_min_days: Optional[int] = None
    duration_max_days: Optional[int] = None
    job_family: Optional[str] = None


class ProgramDetail(ProgramSummary):
    """Full program detail."""
    zip_code: Optional[str] = None
    location_raw: Optional[str] = None
    program_duration: Optional[str] = None
    description: Optional[str] = None
    target_moc: Optional[str] = None
    employer_poc_name: Optional[str] = None
    employer_poc_email: Optional[str] = None
    employer_website: Optional[str] = None
    army: bool = False
    navy: bool = False
    air_force: bool = False
    marines: bool = False
    coast_guard: bool = False
    space_force: bool = False
    geocode_quality: Optional[str] = None
    scraped_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MapPoint(BaseModel):
    """Minimal model for map rendering — keeps payload small."""
    id: int
    company: str
    city: Optional[str] = None
    state: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    industry: Optional[str] = None
    nationwide: bool = False

    class Config:
        from_attributes = True


class ClusterPoint(BaseModel):
    """Represents a cluster of programs on the map."""
    cluster_id: str
    lat: float
    lon: float
    count: int
    programs: List[MapPoint]
    top_industry: Optional[str] = None
    label: Optional[str] = None  # e.g., "DC Metro" or "Seattle Area"


# ─── Pagination ───

class PaginatedResponse(BaseModel):
    items: List[ProgramSummary]
    total: int
    page: int
    per_page: int
    pages: int


class MapResponse(BaseModel):
    """Response for the map endpoint with clusters and singles."""
    clusters: List[ClusterPoint]
    singles: List[MapPoint]
    total_programs: int
    total_positions: int  # number of visible programs
    bounds: Optional[dict] = None  # {north, south, east, west}


# ─── Stats ───

class IndustryCount(BaseModel):
    industry: str
    count: int


class StateCount(BaseModel):
    state: str
    count: int


class StatsResponse(BaseModel):
    total_programs: int
    total_companies: int
    total_states: int
    total_nationwide: int
    total_online: int
    by_industry: List[IndustryCount]
    by_state: List[StateCount]
    last_scraped: Optional[datetime] = None


# ─── Scrape ───

class ScrapeStatus(BaseModel):
    status: str
    pages_scraped: int
    programs_found: int
    programs_new: int
    programs_geocoded: int
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None


# ─── Query Params ───

class ProgramQuery(BaseModel):
    q: Optional[str] = None
    state: Optional[str] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    remote: Optional[bool] = None
    nationwide: Optional[bool] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    radius_miles: Optional[int] = None
    min_duration: Optional[int] = None
    max_duration: Optional[int] = None
    branch: Optional[str] = None  # army, navy, etc.
    sort: str = "company"
    order: str = "asc"
    page: int = 1
    per_page: int = Field(default=50, le=200)
