"""
The FOB — SkillBridge API

Main FastAPI application that serves scraped and geocoded
DoD SkillBridge program data for the veteran resource platform.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import structlog

from app.config import get_settings
from app.models.database import (
    get_async_engine, get_async_session_factory, init_db,
)
from app.routes.programs import router as programs_router
from app.routes.roadmap import router as roadmap_router
from app.routes.career import router as career_router
from app.routes.news import router as news_router
from app.routes.communities import router as communities_router
from app.routes.employment_networking import router as employment_networking_router
from app.routes.auth import router as auth_router
from app.routes.ergs import router as ergs_router
from app.routes.linkedin import router as linkedin_router

logger = structlog.get_logger()
settings = get_settings()


# ─── Scheduled Scrapers ───

async def scheduled_scrape():
    """Run the SkillBridge scrape pipeline on a schedule."""
    from app.services.pipeline import ScrapePipeline

    logger.info("Scheduled scrape starting")
    try:
        pipeline = ScrapePipeline()
        result = await pipeline.run()
        logger.info("Scheduled scrape complete", **result)
    except Exception as e:
        logger.error("Scheduled scrape failed", error=str(e))


async def scheduled_news_scrape():
    """Run the VA news RSS scrape on a schedule (hourly)."""
    from app.services.news_scraper import NewsScraper

    logger.info("Scheduled news scrape starting")
    try:
        engine = get_async_engine(settings.database_url)
        factory = get_async_session_factory(engine)
        async with factory() as session:
            scraper = NewsScraper(session)
            result = await scraper.scrape_all()
            logger.info("Scheduled news scrape complete", new=result["total_new"])
        await engine.dispose()
    except Exception as e:
        logger.error("Scheduled news scrape failed", error=str(e))


async def scheduled_networking_scrape():
    """Run weekly scrape of veteran networking events (per state) into veteran_networking_results."""
    if not getattr(settings, "google_cse_api_key", None) and not getattr(settings, "serp_api_key", None):
        return
    from app.services.networking_events_scraper import run_weekly_scrape

    logger.info("Scheduled veteran networking scrape starting")
    try:
        engine = get_async_engine(settings.database_url)
        factory = get_async_session_factory(engine)
        async with factory() as session:
            result = await run_weekly_scrape(session)
            logger.info("Scheduled veteran networking scrape complete", **result)
        await engine.dispose()
    except Exception as e:
        logger.error("Scheduled veteran networking scrape failed", error=str(e))


async def _initial_news_scrape(session_factory):
    """Run a one-time news scrape on startup after a short delay."""
    import asyncio
    from app.services.news_scraper import NewsScraper

    await asyncio.sleep(3)  # let the app fully start
    logger.info("Running initial news scrape")
    try:
        async with session_factory() as session:
            scraper = NewsScraper(session)
            result = await scraper.scrape_all()
            logger.info("Initial news scrape done", new=result["total_new"])
    except Exception as e:
        logger.error("Initial news scrape failed", error=str(e))


# ─── App Lifecycle ───

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting SkillBridge API", version=settings.api_version)

    # Initialize database (graceful if DB not available)
    engine = None
    scheduler = None
    try:
        await init_db(settings.database_url)
        engine = get_async_engine(settings.database_url)
        session_factory = get_async_session_factory(engine)
        app.state.engine = engine
        app.state.session_factory = session_factory
        logger.info("Database connected")

        # Start scheduler only if DB is available
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            scheduled_scrape,
            "interval",
            hours=settings.scrape_interval_hours,
            id="skillbridge_scrape",
            name="SkillBridge Weekly Scrape",
            misfire_grace_time=3600,
        )
        scheduler.add_job(
            scheduled_news_scrape,
            "interval",
            minutes=60,
            id="news_scrape",
            name="VA News RSS Scrape (hourly)",
            misfire_grace_time=300,
        )
        if settings.google_cse_api_key or settings.serp_api_key:
            scheduler.add_job(
                scheduled_networking_scrape,
                "interval",
                weeks=1,
                id="networking_scrape",
                name="Veteran Networking Events Scrape (weekly)",
                misfire_grace_time=3600,
            )
        scheduler.start()
        app.state.scheduler = scheduler

        # Run initial news scrape on startup
        import asyncio
        asyncio.create_task(_initial_news_scrape(session_factory))
    except Exception as e:
        logger.warning("Database unavailable — running without DB", error=str(e))

    logger.info("API startup complete")
    yield

    # Shutdown
    logger.info("Shutting down SkillBridge API")
    if scheduler:
        scheduler.shutdown(wait=False)
    if engine:
        await engine.dispose()
    logger.info("Shutdown complete")


# ─── Create App ───

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=(
        "Serves 10,000+ DoD SkillBridge programs with search, filtering, "
        "geocoded locations, and map clustering for The FOB veteran resource platform."
    ),
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(programs_router)
app.include_router(roadmap_router)
app.include_router(career_router)
app.include_router(news_router)
app.include_router(communities_router)
app.include_router(employment_networking_router)
app.include_router(auth_router)
app.include_router(ergs_router)
app.include_router(linkedin_router)


# ─── Admin Endpoints ───

@app.post("/api/v1/scrape/trigger")
async def trigger_scrape(secret: str = ""):
    """Manually trigger a scrape (requires API secret)."""
    if secret != settings.api_secret_key:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Invalid secret")

    from app.services.pipeline import ScrapePipeline
    import asyncio

    # Run in background
    pipeline = ScrapePipeline()
    asyncio.create_task(pipeline.run())

    return {"status": "scrape_triggered", "message": "Running in background"}


@app.post("/api/v1/scrape/trigger-networking")
async def trigger_networking_scrape(secret: str = ""):
    """Manually trigger the weekly veteran networking events scrape (requires API secret)."""
    if secret != settings.api_secret_key:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Invalid secret")
    if not settings.google_cse_api_key and not settings.serp_api_key:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="No Google CSE or SerpAPI key configured")

    import asyncio
    asyncio.create_task(scheduled_networking_scrape())
    return {"status": "networking_scrape_triggered", "message": "Running in background"}


@app.get("/")
async def root():
    return {
        "name": "The FOB — SkillBridge API",
        "version": settings.api_version,
        "docs": "/docs",
        "health": "/api/v1/health",
    }
