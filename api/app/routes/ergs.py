"""
ERG Directory API — Corporate veteran ERGs.
Endpoints:
  GET  /api/v1/ergs                    — List/search with filters
  GET  /api/v1/ergs/{id}              — Single ERG
  GET  /api/v1/ergs/stats             — Directory stats
  GET  /api/v1/ergs/industries        — Industries with counts
  GET  /api/v1/ergs/company/{name}    — By company name
  POST /api/v1/ergs/submit             — Submit ERG (auth)
  POST /api/v1/ergs/scrape/trigger    — Trigger scrape (admin secret)
  POST /api/v1/ergs/seed               — Load seed data (admin secret)
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies.supabase_auth import get_user_id_from_request
from app.models.erg import ERGSubmitRequest
from app.services import erg_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ergs", tags=["ERGs"])


async def _get_session(request: Request) -> AsyncSession:
    try:
        factory = request.app.state.session_factory
        return factory()
    except AttributeError:
        raise HTTPException(
            status_code=503,
            detail="Database not available — ERG directory requires a database connection",
        )


def _require_secret(request: Request) -> None:
    auth = request.headers.get("Authorization") or request.query_params.get("secret") or ""
    token = auth.replace("Bearer ", "").strip() if auth else ""
    settings = get_settings()
    if settings.api_secret_key and token != settings.api_secret_key:
        raise HTTPException(status_code=403, detail="Invalid or missing secret")


def _user_id_from_request(request: Request) -> Optional[str]:
    """Bearer token is the user id (UUID) from auth/enter."""
    auth = request.headers.get("Authorization") or ""
    if not auth.startswith("Bearer "):
        return None
    return auth[7:].strip() or None


@router.get("", summary="List ERGs with search and filters")
async def list_ergs(
    request: Request,
    q: Optional[str] = Query(None, description="Full-text search"),
    industry: Optional[str] = Query(None),
    company_size: Optional[str] = Query(None),
    offering: Optional[str] = Query(None),
    has_skillbridge: Optional[bool] = Query(None),
    verified: Optional[bool] = Query(None),
    rating: Optional[str] = Query(None),
    sort: str = Query("company_name", description="company_name | created_at | member_count"),
    order: str = Query("asc", description="asc | desc"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    session = await _get_session(request)
    async with session:
        items, total = await erg_service.list_ergs(
            session,
            q=q,
            industry=industry,
            company_size=company_size,
            offering=offering,
            has_skillbridge=has_skillbridge,
            verified=verified,
            rating=rating,
            sort=sort,
            order=order,
            page=page,
            per_page=per_page,
        )
        return {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page if total else 0,
            "ergs": [e.to_dict() for e in items],
        }


@router.get("/by-companies", summary="Get ERGs for given company names (for roadmap/SkillBridge integration)")
async def get_by_companies(
    request: Request,
    names: str = Query(..., description="Comma-separated company names"),
):
    """Returns list of ERG records for companies in the given list. Use for roadmap/SkillBridge UI."""
    company_names = [n.strip() for n in names.split(",") if n.strip()]
    if not company_names:
        return {"ergs": []}
    session = await _get_session(request)
    async with session:
        ergs = await erg_service.get_ergs_by_company_names(session, company_names)
        return {"ergs": [e.to_dict() for e in ergs]}


@router.get("/stats", summary="Directory statistics")
async def erg_stats(request: Request):
    session = await _get_session(request)
    async with session:
        return await erg_service.get_stats(session)


@router.get("/industries", summary="Industries with counts")
async def erg_industries(request: Request):
    session = await _get_session(request)
    async with session:
        return {"industries": await erg_service.get_industries_with_counts(session)}


@router.get("/company/{company_name:path}", summary="Get ERG by company name")
async def get_by_company(company_name: str, request: Request):
    session = await _get_session(request)
    async with session:
        erg = await erg_service.get_erg_by_company_name(session, company_name)
        if not erg:
            raise HTTPException(status_code=404, detail="ERG not found for this company")
        return erg.to_dict()


@router.get("/{erg_id}", summary="Get single ERG by id")
async def get_erg(erg_id: UUID, request: Request):
    session = await _get_session(request)
    async with session:
        erg = await erg_service.get_erg_by_id(session, erg_id)
        if not erg:
            raise HTTPException(status_code=404, detail="ERG not found")
        return erg.to_dict()


@router.post("/submit", summary="Submit ERG (community submission)")
async def submit_erg(
    request: Request,
    body: ERGSubmitRequest,
    user_id: UUID = Depends(get_user_id_from_request),
):
    """Requires auth (Supabase JWT or legacy Bearer UUID). Creates a pending submission."""
    if not body.verification_agreement:
        raise HTTPException(status_code=422, detail="Verification agreement is required")

    session = await _get_session(request)
    async with session:
        sub = await erg_service.submit_erg(session, body, user_id=user_id)
        return {
            "message": "Thank you for submitting! Your submission will be reviewed within 3-5 business days.",
            "submission_id": str(sub.id),
            "company_name": sub.company_name,
            "status": sub.status,
        }


@router.post("/scrape/trigger", summary="Trigger ERG scrape (admin)")
async def trigger_scrape(request: Request):
    _require_secret(request)
    # TODO: when erg_scraper is implemented, run it in background
    return {"status": "scrape_triggered", "message": "ERG scrape not yet implemented; use /seed to load seed data."}


@router.post("/seed", summary="Load seed ERG data (admin)")
async def load_seed(request: Request):
    """Upsert known ERGs from seed data. Requires API secret."""
    _require_secret(request)
    session = await _get_session(request)
    async with session:
        inserted, updated = await erg_service.load_seed_data(session)
        return {"status": "ok", "inserted": inserted, "updated": updated}
