"""
ERG directory business logic: search, filter, list, submit, seed.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import CorporateErg, ErgSubmission
from app.models.erg import ERGSubmitRequest
from app.scrapers.erg_seed_data import KNOWN_ERGS, OFFERING_TYPES

logger = logging.getLogger(__name__)


VALID_SORT = {"company_name", "created_at", "member_count"}
VALID_COMPANY_SIZES = {"small", "medium", "large", "enterprise"}
VALID_RATINGS = {"top_employer", "gold", "silver", "designated", "military_friendly"}


def _normalize_offerings(offerings: List[str]) -> List[str]:
    """Keep only controlled vocabulary."""
    if not offerings:
        return []
    return [o for o in offerings if o in OFFERING_TYPES]


async def list_ergs(
    session: AsyncSession,
    *,
    q: Optional[str] = None,
    industry: Optional[str] = None,
    company_size: Optional[str] = None,
    offering: Optional[str] = None,
    has_skillbridge: Optional[bool] = None,
    verified: Optional[bool] = None,
    rating: Optional[str] = None,
    sort: str = "company_name",
    order: str = "asc",
    page: int = 1,
    per_page: int = 20,
) -> Tuple[List[CorporateErg], int]:
    """List ERGs with filters and full-text search. Returns (items, total)."""
    base = select(CorporateErg)
    count_stmt = select(func.count(CorporateErg.id))

    if q and q.strip():
        qnorm = q.strip()
        search = f"%{qnorm}%"
        cond = or_(
            CorporateErg.company_name.ilike(search),
            CorporateErg.erg_name.ilike(search),
            CorporateErg.description.ilike(search),
            CorporateErg.industry.ilike(search),
        )
        base = base.where(cond)
        count_stmt = count_stmt.where(cond)

    if industry and industry.strip():
        base = base.where(CorporateErg.industry.ilike(industry.strip()))
        count_stmt = count_stmt.where(CorporateErg.industry.ilike(industry.strip()))

    if company_size and company_size.strip().lower() in VALID_COMPANY_SIZES:
        base = base.where(CorporateErg.company_size == company_size.strip().lower())
        count_stmt = count_stmt.where(CorporateErg.company_size == company_size.strip().lower())

    if offering and offering.strip() and offering.strip() in OFFERING_TYPES:
        base = base.where(CorporateErg.offerings.contains([offering.strip()]))
        count_stmt = count_stmt.where(CorporateErg.offerings.contains([offering.strip()]))

    if has_skillbridge is not None:
        base = base.where(CorporateErg.has_skillbridge == has_skillbridge)
        count_stmt = count_stmt.where(CorporateErg.has_skillbridge == has_skillbridge)

    if verified is not None:
        base = base.where(CorporateErg.verified == verified)
        count_stmt = count_stmt.where(CorporateErg.verified == verified)

    if rating and rating.strip().lower() in VALID_RATINGS:
        base = base.where(CorporateErg.military_friendly_rating == rating.strip().lower())
        count_stmt = count_stmt.where(CorporateErg.military_friendly_rating == rating.strip().lower())

    total = (await session.execute(count_stmt)).scalar() or 0

    sort_col = getattr(CorporateErg, sort, CorporateErg.company_name)
    if sort not in VALID_SORT:
        sort_col = CorporateErg.company_name
    base = base.order_by(sort_col.asc() if order == "asc" else sort_col.desc())

    offset = (page - 1) * per_page
    base = base.offset(offset).limit(per_page)
    result = await session.execute(base)
    items = list(result.scalars().all())
    return items, total


async def get_erg_by_id(session: AsyncSession, erg_id: UUID) -> Optional[CorporateErg]:
    """Get a single ERG by id."""
    stmt = select(CorporateErg).where(CorporateErg.id == erg_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_erg_by_company_name(session: AsyncSession, company_name: str) -> Optional[CorporateErg]:
    """Look up ERG by company name (case-insensitive)."""
    stmt = select(CorporateErg).where(func.lower(CorporateErg.company_name) == company_name.strip().lower())
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_stats(session: AsyncSession) -> dict:
    """Directory statistics."""
    total = (await session.execute(select(func.count(CorporateErg.id)))).scalar() or 0
    industries = (
        await session.execute(
            select(CorporateErg.industry, func.count(CorporateErg.id))
            .group_by(CorporateErg.industry)
        )
    )
    industry_count = len(industries.all())
    named = (
        await session.execute(
            select(func.count(CorporateErg.id)).where(CorporateErg.erg_name.isnot(None)).where(CorporateErg.erg_name != "")
        )
    ).scalar() or 0
    skillbridge = (
        await session.execute(select(func.count(CorporateErg.id)).where(CorporateErg.has_skillbridge))
    ).scalar() or 0
    verified_count = (
        await session.execute(select(func.count(CorporateErg.id)).where(CorporateErg.verified))
    ).scalar() or 0
    return {
        "total_ergs": total,
        "total_companies": total,
        "total_industries": industry_count,
        "total_named_ergs": named,
        "with_skillbridge": skillbridge,
        "verified_count": verified_count,
    }


async def get_ergs_by_company_names(
    session: AsyncSession,
    company_names: List[str],
) -> List[CorporateErg]:
    """Return ERGs for companies whose name is in the given list (case-insensitive match)."""
    if not company_names:
        return []
    names_lower = [n.strip().lower() for n in company_names if n and n.strip()]
    if not names_lower:
        return []
    # Match by lower(company_name) in list
    stmt = select(CorporateErg).where(
        func.lower(CorporateErg.company_name).in_(names_lower)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_industries_with_counts(session: AsyncSession) -> List[dict]:
    """List unique industries with counts."""
    stmt = (
        select(CorporateErg.industry, func.count(CorporateErg.id).label("count"))
        .group_by(CorporateErg.industry)
        .order_by(func.count(CorporateErg.id).desc())
    )
    result = await session.execute(stmt)
    return [{"industry": row.industry, "count": row.count} for row in result.all()]


async def submit_erg(
    session: AsyncSession,
    payload: ERGSubmitRequest,
    user_id: Optional[UUID] = None,
) -> ErgSubmission:
    """Create a pending ERG submission (community submission)."""
    if not payload.verification_agreement:
        raise ValueError("Verification agreement is required")

    offerings = _normalize_offerings(payload.offerings)

    sub = ErgSubmission(
        submitted_by=user_id,
        submitter_email=payload.submitter_email.strip(),
        submitter_name=payload.submitter_name.strip() if payload.submitter_name else None,
        submitter_role=payload.submitter_role.strip() if payload.submitter_role else None,
        company_name=payload.company_name.strip(),
        erg_name=payload.erg_name.strip() if payload.erg_name else None,
        industry=payload.industry.strip() if payload.industry else None,
        company_size=payload.company_size.strip().lower() if payload.company_size else None,
        description=payload.description.strip() if payload.description else None,
        offerings=offerings,
        founded_year=payload.founded_year,
        member_count=payload.member_count,
        careers_url=payload.careers_url.strip() if payload.careers_url else None,
        erg_url=payload.erg_url.strip() if payload.erg_url else None,
        company_website=payload.company_website.strip() if payload.company_website else None,
        contact_email=payload.contact_email.strip() if payload.contact_email else None,
        linkedin_url=payload.linkedin_url.strip() if payload.linkedin_url else None,
        headquarters_city=payload.headquarters_city.strip() if payload.headquarters_city else None,
        headquarters_state=payload.headquarters_state.strip() if payload.headquarters_state else None,
        has_skillbridge=payload.has_skillbridge,
        status="pending",
    )
    session.add(sub)
    await session.commit()
    await session.refresh(sub)
    logger.info("ERG submission created", company=sub.company_name, id=str(sub.id))
    return sub


async def upsert_scraped_records(
    session: AsyncSession,
    records: List[dict],
    source_type: str = "scraped",
) -> Tuple[int, int]:
    """Upsert scraped/merged ERG records. Returns (inserted, updated)."""
    inserted = 0
    updated = 0
    now = datetime.now(timezone.utc)

    for rec in records:
        company_name = (rec.get("company_name") or rec.get("company")).strip()
        if not company_name:
            continue
        stmt = select(CorporateErg).where(func.lower(CorporateErg.company_name) == company_name.lower())
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        offerings = _normalize_offerings(rec.get("offerings") or [])
        data_sources = list(rec.get("data_sources") or [])
        if source_type not in data_sources:
            data_sources.append(source_type)

        if existing:
            existing.erg_name = rec.get("erg_name") or existing.erg_name
            existing.industry = rec.get("industry") or existing.industry or "Other"
            existing.company_size = rec.get("company_size")
            existing.description = rec.get("description") or existing.description
            existing.offerings = offerings or existing.offerings
            existing.founded_year = rec.get("founded_year")
            existing.member_count = rec.get("member_count")
            existing.careers_url = rec.get("careers_url") or existing.careers_url
            existing.erg_url = rec.get("erg_url")
            existing.company_website = rec.get("company_website")
            existing.military_friendly_rating = rec.get("military_friendly_rating") or existing.military_friendly_rating
            existing.has_skillbridge = rec.get("has_skillbridge", existing.has_skillbridge)
            existing.data_sources = data_sources
            existing.source_type = source_type
            existing.scraped_at = now
            existing.updated_at = now
            updated += 1
        else:
            erg = CorporateErg(
                company_name=company_name,
                erg_name=rec.get("erg_name"),
                industry=rec.get("industry") or "Other",
                company_size=rec.get("company_size"),
                description=rec.get("description"),
                offerings=offerings,
                founded_year=rec.get("founded_year"),
                member_count=rec.get("member_count"),
                careers_url=rec.get("careers_url"),
                erg_url=rec.get("erg_url"),
                company_website=rec.get("company_website"),
                military_friendly_rating=rec.get("military_friendly_rating"),
                has_skillbridge=rec.get("has_skillbridge", False),
                verified=rec.get("verified", False),
                data_sources=data_sources,
                source_type=source_type,
                scraped_at=now,
            )
            session.add(erg)
            inserted += 1

    await session.commit()
    logger.info("Scraped ERG upsert complete", inserted=inserted, updated=updated)
    return inserted, updated


async def load_seed_data(session: AsyncSession) -> Tuple[int, int]:
    """Upsert KNOWN_ERGS into corporate_ergs. Returns (inserted, updated)."""
    from app.models.database import CorporateErg

    inserted = 0
    updated = 0
    now = datetime.now(timezone.utc)

    for rec in KNOWN_ERGS:
        company_name = rec["company"].strip()
        stmt = select(CorporateErg).where(func.lower(CorporateErg.company_name) == company_name.lower())
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()

        offerings = _normalize_offerings(rec.get("offerings") or [])
        data = {
            "erg_name": rec.get("erg_name"),
            "industry": rec.get("industry") or "Other",
            "company_size": rec.get("company_size"),
            "description": rec.get("description"),
            "offerings": offerings,
            "founded_year": rec.get("founded_year"),
            "member_count": rec.get("member_count"),
            "careers_url": rec.get("careers_url"),
            "erg_url": rec.get("erg_url"),
            "military_friendly_rating": rec.get("military_friendly_rating"),
            "has_skillbridge": "skillbridge_partner" in (rec.get("offerings") or []),
            "verified": True,
            "data_sources": ["seed_data"],
            "source_type": "seed_data",
            "scraped_at": now,
        }

        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            existing.updated_at = now
            updated += 1
        else:
            erg = CorporateErg(
                company_name=company_name,
                **data,
            )
            session.add(erg)
            inserted += 1

    await session.commit()
    logger.info("ERG seed load complete", inserted=inserted, updated=updated)
    return inserted, updated
