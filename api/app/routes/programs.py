"""
API routes for SkillBridge programs.

Provides:
- Full-text search + filtered listing
- Single program detail
- Map-optimized endpoint with server-side clustering
- Aggregate statistics
- Industry and state lists
"""

import math
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Program, ScrapeLog
from app.models.schemas import (
    ProgramSummary, ProgramDetail, PaginatedResponse,
    MapPoint, ClusterPoint, MapResponse,
    StatsResponse, IndustryCount, StateCount,
)

router = APIRouter(prefix="/api/v1", tags=["programs"])


# ─── Dependency ───

async def get_db(request: Request) -> AsyncSession:
    """Get async DB session from app state."""
    if not hasattr(request.app.state, "session_factory"):
        raise HTTPException(
            status_code=503,
            detail="Database not available",
        )
    async with request.app.state.session_factory() as session:
        yield session


# ─── List Programs ───

@router.get("/programs", response_model=PaginatedResponse)
async def list_programs(
    q: Optional[str] = Query(None, description="Search company, role, description"),
    state: Optional[str] = Query(None, description="Filter by state abbreviation"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    city: Optional[str] = Query(None, description="Filter by city"),
    remote: Optional[bool] = Query(None, description="Filter remote/online programs"),
    nationwide: Optional[bool] = Query(None, description="Filter nationwide programs"),
    lat: Optional[float] = Query(None, description="Latitude for distance search"),
    lon: Optional[float] = Query(None, description="Longitude for distance search"),
    radius_miles: Optional[int] = Query(None, description="Radius in miles"),
    min_duration: Optional[int] = Query(None, description="Min duration (days)"),
    max_duration: Optional[int] = Query(None, description="Max duration (days)"),
    branch: Optional[str] = Query(None, description="Military branch filter"),
    sort: str = Query("company", description="Sort field"),
    order: str = Query("asc", description="Sort order: asc/desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List programs with comprehensive filtering and pagination."""

    query = select(Program).where(Program.is_active)

    # Text search
    if q:
        search_term = f"%{q}%"
        query = query.where(
            or_(
                Program.company.ilike(search_term),
                Program.description.ilike(search_term),
                Program.job_family.ilike(search_term),
                Program.city.ilike(search_term),
                Program.opportunity_type.ilike(search_term),
            )
        )

    # Filters
    if state:
        query = query.where(Program.state == state.upper())
    if industry:
        query = query.where(Program.industry == industry)
    if city:
        query = query.where(Program.city.ilike(f"%{city}%"))
    if remote is not None:
        query = query.where(Program.online == remote)
    if nationwide is not None:
        query = query.where(Program.nationwide == nationwide)
    if min_duration is not None:
        query = query.where(Program.duration_min_days >= min_duration)
    if max_duration is not None:
        query = query.where(Program.duration_max_days <= max_duration)

    # Branch filter
    if branch:
        branch_col = {
            "army": Program.army, "navy": Program.navy,
            "air_force": Program.air_force, "marines": Program.marines,
            "coast_guard": Program.coast_guard, "space_force": Program.space_force,
        }.get(branch.lower())
        if branch_col is not None:
            query = query.where(branch_col)

    # Distance filter (Haversine approximation)
    if lat is not None and lon is not None and radius_miles:
        # Rough bounding box first (fast filter)
        lat_delta = radius_miles / 69.0
        lon_delta = radius_miles / (69.0 * math.cos(math.radians(lat)))
        query = query.where(
            and_(
                Program.latitude.between(lat - lat_delta, lat + lat_delta),
                Program.longitude.between(lon - lon_delta, lon + lon_delta),
                Program.latitude.isnot(None),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Sorting
    sort_col = {
        "company": Program.company,
        "city": Program.city,
        "state": Program.state,
        "industry": Program.industry,
        "duration": Program.duration_max_days,
        "updated": Program.updated_at,
    }.get(sort, Program.company)

    query = query.order_by(desc(sort_col) if order == "desc" else asc(sort_col))

    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    programs = result.scalars().all()

    return PaginatedResponse(
        items=[ProgramSummary.model_validate(p) for p in programs],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )





# ─── Map Endpoint with Clustering ───

@router.get("/programs/map", response_model=MapResponse)
async def get_map_data(
    state: Optional[str] = None,
    industry: Optional[str] = None,
    q: Optional[str] = None,
    cluster_radius: float = Query(2.0, description="Clustering radius in degrees"),
    db: AsyncSession = Depends(get_db),
):
    """
    Map-optimized endpoint returning clustered program data.
    Programs close together are grouped into clusters.
    """
    query = select(Program).where(
        Program.is_active,
        Program.latitude.isnot(None),
        Program.longitude.isnot(None),
    )

    if state:
        query = query.where(Program.state == state.upper())
    if industry:
        query = query.where(Program.industry == industry)
    if q:
        search_term = f"%{q}%"
        query = query.where(
            or_(
                Program.company.ilike(search_term),
                Program.job_family.ilike(search_term),
            )
        )

    result = await db.execute(query)
    programs = result.scalars().all()

    # Server-side clustering
    clusters, singles = _cluster_programs(programs, cluster_radius)

    # Calculate bounds
    all_points = [
        (p.latitude, p.longitude)
        for p in programs
        if p.latitude and p.longitude
    ]
    bounds = None
    if all_points:
        lats = [p[0] for p in all_points]
        lons = [p[1] for p in all_points]
        bounds = {
            "north": max(lats),
            "south": min(lats),
            "east": max(lons),
            "west": min(lons),
        }

    return MapResponse(
        clusters=clusters,
        singles=singles,
        total_programs=len(programs),
        total_positions=len(programs),
        bounds=bounds,
    )


def _cluster_programs(
    programs: list,
    radius_deg: float = 2.0,
) -> tuple[List[ClusterPoint], List[MapPoint]]:
    """
    Simple grid-based clustering for map display.
    Groups programs whose lat/lon fall in the same grid cell.
    """
    grid = {}

    for p in programs:
        if not p.latitude or not p.longitude:
            continue

        # Grid cell key
        cell_lat = round(p.latitude / radius_deg) * radius_deg
        cell_lon = round(p.longitude / radius_deg) * radius_deg
        key = (cell_lat, cell_lon)

        if key not in grid:
            grid[key] = []
        grid[key].append(p)

    clusters = []
    singles = []

    for (cell_lat, cell_lon), cell_programs in grid.items():
        if len(cell_programs) == 1:
            p = cell_programs[0]
            singles.append(MapPoint(
                id=p.id, company=p.company, city=p.city,
                state=p.state, lat=p.latitude, lon=p.longitude,
                industry=p.industry, nationwide=p.nationwide,
            ))
        else:
            # Calculate centroid
            avg_lat = sum(p.latitude for p in cell_programs) / len(cell_programs)
            avg_lon = sum(p.longitude for p in cell_programs) / len(cell_programs)

            # Top industry in cluster
            ind_counts = {}
            for p in cell_programs:
                ind = p.industry or "Other"
                ind_counts[ind] = ind_counts.get(ind, 0) + 1
            top_ind = max(ind_counts, key=ind_counts.get)

            # Label from most common state
            state_counts = {}
            for p in cell_programs:
                if p.state:
                    state_counts[p.state] = state_counts.get(p.state, 0) + 1
            label = max(state_counts, key=state_counts.get) if state_counts else None

            cluster_programs = [
                MapPoint(
                    id=p.id, company=p.company, city=p.city,
                    state=p.state, lat=p.latitude, lon=p.longitude,
                    industry=p.industry, nationwide=p.nationwide,
                )
                for p in cell_programs
            ]

            clusters.append(ClusterPoint(
                cluster_id=f"cl-{cell_lat:.1f}-{cell_lon:.1f}",
                lat=avg_lat,
                lon=avg_lon,
                count=len(cell_programs),
                programs=cluster_programs,
                top_industry=top_ind,
                label=f"{label} Area" if label else None,
            ))

    return clusters, singles


# ─── Statistics ───

@router.get("/programs/stats", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate statistics about all programs."""
    total = await db.execute(
        select(func.count(Program.id)).where(Program.is_active)
    )
    companies = await db.execute(
        select(func.count(func.distinct(Program.company))).where(Program.is_active)
    )
    states = await db.execute(
        select(func.count(func.distinct(Program.state))).where(
            Program.is_active, Program.state.isnot(None)
        )
    )
    nationwide = await db.execute(
        select(func.count(Program.id)).where(
            Program.is_active, Program.nationwide
        )
    )
    online = await db.execute(
        select(func.count(Program.id)).where(
            Program.is_active, Program.online
        )
    )

    # By industry
    ind_result = await db.execute(
        select(Program.industry, func.count(Program.id))
        .where(Program.is_active, Program.industry.isnot(None))
        .group_by(Program.industry)
        .order_by(desc(func.count(Program.id)))
    )
    by_industry = [
        IndustryCount(industry=row[0], count=row[1])
        for row in ind_result.all()
    ]

    # By state
    state_result = await db.execute(
        select(Program.state, func.count(Program.id))
        .where(Program.is_active, Program.state.isnot(None))
        .group_by(Program.state)
        .order_by(desc(func.count(Program.id)))
    )
    by_state = [
        StateCount(state=row[0], count=row[1])
        for row in state_result.all()
    ]

    # Last scrape
    last_scrape = await db.execute(
        select(ScrapeLog.finished_at)
        .where(ScrapeLog.status == "completed")
        .order_by(desc(ScrapeLog.finished_at))
        .limit(1)
    )
    last_scraped = last_scrape.scalar_one_or_none()

    return StatsResponse(
        total_programs=total.scalar() or 0,
        total_companies=companies.scalar() or 0,
        total_states=states.scalar() or 0,
        total_nationwide=nationwide.scalar() or 0,
        total_online=online.scalar() or 0,
        by_industry=by_industry,
        by_state=by_state,
        last_scraped=last_scraped,
    )


# ─── Single Program ───

@router.get("/programs/{program_id}", response_model=ProgramDetail)
async def get_program(program_id: int, db: AsyncSession = Depends(get_db)):
    """Get full program detail."""
    result = await db.execute(select(Program).where(Program.id == program_id))
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    return ProgramDetail.model_validate(program)


# ─── Lookup Endpoints ───

@router.get("/industries")
async def list_industries(db: AsyncSession = Depends(get_db)):
    """List all industries with program counts."""
    result = await db.execute(
        select(Program.industry, func.count(Program.id))
        .where(Program.is_active, Program.industry.isnot(None))
        .group_by(Program.industry)
        .order_by(desc(func.count(Program.id)))
    )
    return [{"industry": row[0], "count": row[1]} for row in result.all()]


@router.get("/states")
async def list_states(db: AsyncSession = Depends(get_db)):
    """List all states with program counts."""
    result = await db.execute(
        select(Program.state, func.count(Program.id))
        .where(Program.is_active, Program.state.isnot(None), Program.state != "")
        .group_by(Program.state)
        .order_by(Program.state)
    )
    return [{"state": row[0], "count": row[1]} for row in result.all()]


# ─── Health ───

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint."""
    try:
        result = await db.execute(select(func.count(Program.id)))
        count = result.scalar()
        return {
            "status": "healthy",
            "programs_in_db": count,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
