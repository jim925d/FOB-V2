"""
VA News API Router
The FOB Platform

Endpoints:
  GET  /v1/news             - List articles (filterable by category, paginated)
  GET  /v1/news/ticker      - Latest headlines for the news ticker bar
  POST /v1/news/refresh     - Trigger an on-demand RSS scrape
  GET  /v1/news/categories  - List available categories with counts
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import NewsArticle
from app.services.news_scraper import NewsScraper

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/news", tags=["VA News"])

VALID_CATEGORIES = [
    "benefits", "healthcare", "education", "employment", "policy", "doge",
]


async def _get_session(request: Request) -> AsyncSession:
    """Get a DB session from the app state."""
    try:
        factory = request.app.state.session_factory
        return factory()
    except AttributeError:
        raise HTTPException(
            status_code=503,
            detail="Database not available — news feed requires a database connection",
        )


@router.get("", summary="List news articles")
async def list_articles(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Max articles to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    List VA/veteran news articles, newest first.

    Optional `category` filter: benefits, healthcare, education,
    employment, policy, doge.
    """
    session = await _get_session(request)
    async with session:
        stmt = (
            select(NewsArticle)
            .order_by(desc(NewsArticle.published_at))
        )

        if category:
            cat = category.lower().strip()
            if cat not in VALID_CATEGORIES:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": f"Invalid category '{category}'",
                        "valid_categories": VALID_CATEGORIES,
                    },
                )
            stmt = stmt.where(NewsArticle.category == cat)

        stmt = stmt.offset(offset).limit(limit)
        result = await session.execute(stmt)
        articles = result.scalars().all()

        # Get total count for pagination
        count_stmt = select(func.count(NewsArticle.id))
        if category:
            count_stmt = count_stmt.where(
                NewsArticle.category == category.lower().strip()
            )
        total = (await session.execute(count_stmt)).scalar() or 0

        return {
            "total": total,
            "offset": offset,
            "limit": limit,
            "articles": [a.to_dict() for a in articles],
        }


@router.get("/ticker", summary="Headlines for the news ticker bar")
async def ticker_headlines(
    request: Request,
    limit: int = Query(8, ge=1, le=20, description="Number of headlines"),
):
    """
    Return the latest headlines for the sticky news ticker.

    Returns a lightweight list — title, category, source only.
    """
    session = await _get_session(request)
    async with session:
        stmt = (
            select(NewsArticle)
            .order_by(desc(NewsArticle.published_at))
            .limit(limit)
        )
        result = await session.execute(stmt)
        articles = result.scalars().all()

        return {
            "count": len(articles),
            "headlines": [
                {
                    "id": a.id,
                    "title": a.title,
                    "category": a.category,
                    "catLabel": a.category.replace("_", " ").title()
                        if a.category not in ("doge",) else a.category.upper(),
                    "source": a.source_name,
                    "url": a.url,
                    "date": a.published_at.strftime("%b %d, %Y") if a.published_at else None,
                }
                for a in articles
            ],
        }


@router.post("/refresh", summary="Trigger on-demand RSS scrape")
async def refresh_news(request: Request):
    """
    Trigger an immediate scrape of all RSS feeds.

    Returns summary of new articles found per feed.
    """
    session = await _get_session(request)
    async with session:
        scraper = NewsScraper(session)
        result = await scraper.scrape_all()
        logger.info(
            "Manual news refresh: %d new articles",
            result["total_new"],
        )
        return result


@router.get("/categories", summary="List categories with article counts")
async def list_categories(request: Request):
    """
    Return all news categories with their article counts.
    """
    session = await _get_session(request)
    async with session:
        stmt = (
            select(
                NewsArticle.category,
                func.count(NewsArticle.id).label("count"),
            )
            .group_by(NewsArticle.category)
            .order_by(desc("count"))
        )
        result = await session.execute(stmt)
        rows = result.all()

        total = sum(r.count for r in rows)

        categories = [
            {"key": "all", "label": "All Updates", "count": total},
        ]

        # Static label mapping
        LABELS = {
            "benefits": "Benefits",
            "healthcare": "Healthcare",
            "education": "Education & GI Bill",
            "employment": "Employment",
            "policy": "Policy & Legislation",
            "doge": "DOGE & Staffing",
        }

        for row in rows:
            categories.append({
                "key": row.category,
                "label": LABELS.get(row.category, row.category.title()),
                "count": row.count,
            })

        return {
            "total_articles": total,
            "categories": categories,
        }
