"""
Communities API Router — Veteran 501(c)(3) / community organizations
The FOB Platform

Endpoints:
  GET  /api/v1/communities          - List orgs (filter by category, state; paginated)
  GET  /api/v1/communities/categories - Categories with counts
  POST /api/v1/communities/refresh   - Trigger ProPublica scrape (optional secret)
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import CommunityOrg
from app.services.communities_scraper import CommunitiesScraper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/communities", tags=["Communities"])

VALID_CATEGORIES = [
    "service", "outdoor", "wellness", "professional", "arts", "social", "education",
]


async def _get_session(request: Request) -> AsyncSession:
    try:
        factory = request.app.state.session_factory
        return factory()
    except AttributeError:
        raise HTTPException(
            status_code=503,
            detail="Database not available — communities require a database connection",
        )


@router.get("", summary="List community organizations")
async def list_organizations(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by FOB category"),
    state: Optional[str] = Query(None, description="Filter by state (2-letter)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    List veteran-affiliated 501(c)(3) orgs with optional category and state filters.
    Returns organizations with website, form_990_url, social_links, etc.
    """
    session = await _get_session(request)
    async with session:
        stmt = select(CommunityOrg).order_by(CommunityOrg.name)
        if category:
            cat = category.lower().strip()
            if cat not in VALID_CATEGORIES:
                raise HTTPException(
                    status_code=400,
                    detail={"error": f"Invalid category '{category}'", "valid_categories": VALID_CATEGORIES},
                )
            stmt = stmt.where(CommunityOrg.category == cat)
        if state:
            stmt = stmt.where(CommunityOrg.state == state.upper().strip()[:2])
        count_stmt = select(func.count(CommunityOrg.id))
        if category:
            count_stmt = count_stmt.where(CommunityOrg.category == category.lower().strip())
        if state:
            count_stmt = count_stmt.where(CommunityOrg.state == state.upper().strip()[:2])
        total = (await session.execute(count_stmt)).scalar() or 0
        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        orgs = result.scalars().all()
        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "organizations": [o.to_dict() for o in orgs],
        }


@router.get("/categories", summary="List categories with counts")
async def list_categories(request: Request):
    """Return FOB categories with org counts for filter UI."""
    session = await _get_session(request)
    async with session:
        stmt = (
            select(CommunityOrg.category, func.count(CommunityOrg.id).label("count"))
            .group_by(CommunityOrg.category)
            .order_by(desc("count"))
        )
        result = await session.execute(stmt)
        rows = result.all()
        total = sum(r.count for r in rows)
        LABELS = {
            "service": "Service & Advocacy",
            "outdoor": "Outdoor & Adventure",
            "wellness": "Wellness & Sports",
            "professional": "Professional & Career",
            "arts": "Arts & Culture",
            "social": "Social & Family",
            "education": "Education",
        }
        categories = [{"key": "all", "label": "All", "count": total}]
        for row in rows:
            categories.append({
                "key": row.category,
                "label": LABELS.get(row.category, row.category.title()),
                "count": row.count,
            })
        return {"total_organizations": total, "categories": categories}


@router.post("/refresh", summary="Trigger communities scrape")
async def refresh_communities(request: Request, secret: Optional[str] = Query(None)):
    """
    Run ProPublica veteran 501(c)(3) scrape and upsert into DB.
    Optional: pass ?secret=... matching api_secret_key to authorize.
    """
    from app.config import get_settings
    settings = get_settings()
    if settings.api_secret_key and secret != settings.api_secret_key:
        raise HTTPException(status_code=403, detail="Invalid or missing secret")
    session = await _get_session(request)
    async with session:
        scraper = CommunitiesScraper(session)
        result = await scraper.scrape_all()
        logger.info("Communities refresh: %s", result)
        return result
