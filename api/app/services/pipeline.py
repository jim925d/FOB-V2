"""
Scrape Pipeline — orchestrates the full flow:
1. Scrape programs from DoD SkillBridge (API-first, HTML fallback)
2. Geocode locations (skip if API provided coords)
3. Upsert into PostgreSQL
4. Mark stale programs inactive
5. Log results

Designed to run as a scheduled job (weekly) or triggered manually.
"""

import hashlib
from datetime import datetime
from typing import Optional

import structlog
from sqlalchemy import select

from app.config import get_settings
from app.models.database import (
    Program, ScrapeLog,
    get_async_engine, get_async_session_factory,
)
from app.services.geocoding import GeocodingService

logger = structlog.get_logger()


class ScrapePipeline:
    """Full scrape → geocode → store pipeline."""

    def __init__(self, use_api: bool = True):
        self.settings = get_settings()
        self.engine = get_async_engine(self.settings.database_url)
        self.session_factory = get_async_session_factory(self.engine)
        self.use_api = use_api
        self.geocoder = GeocodingService()

    def _get_scraper(self):
        if self.use_api:
            from app.scrapers.skillbridge_api_scraper import SkillBridgeAPIScraper
            return SkillBridgeAPIScraper()
        else:
            from app.scrapers.skillbridge_scraper import SkillBridgeScraper
            return SkillBridgeScraper()

    async def run(self, max_pages: Optional[int] = None) -> dict:
        log_entry = ScrapeLog(started_at=datetime.utcnow(), status="running")

        async with self.session_factory() as session:
            session.add(log_entry)
            await session.commit()
            log_id = log_entry.id

        try:
            # Step 1: Scrape
            scraper = self._get_scraper()
            method = "API" if self.use_api else "HTML"
            logger.info("Pipeline: Starting scrape", method=method)

            try:
                programs = await scraper.scrape_all(max_pages=max_pages)
            except Exception as e:
                if self.use_api:
                    logger.warning("API scraper failed, falling back to HTML", error=str(e))
                    from app.scrapers.skillbridge_scraper import SkillBridgeScraper
                    scraper = SkillBridgeScraper()
                    programs = await scraper.scrape_all(max_pages=max_pages)
                    method = "HTML (fallback)"
                else:
                    raise

            logger.info("Pipeline: Scrape complete", method=method, count=len(programs))

            # Step 2: Geocode
            geocoded_count = await self._geocode_programs(programs)

            # Step 3: Store
            new_count, updated_count = await self._store_programs(programs)

            # Step 4: Mark stale
            stale_count = await self._mark_stale(programs)

            # Log
            async with self.session_factory() as session:
                entry = await session.get(ScrapeLog, log_id)
                if entry:
                    entry.finished_at = datetime.utcnow()
                    entry.status = "completed"
                    entry.pages_scraped = scraper.stats.get("pages_scraped", 0)
                    entry.programs_found = len(programs)
                    entry.programs_new = new_count
                    entry.programs_updated = updated_count
                    entry.programs_geocoded = geocoded_count
                    await session.commit()

            return {
                "status": "completed", "method": method,
                "programs_found": len(programs), "programs_new": new_count,
                "programs_updated": updated_count, "programs_geocoded": geocoded_count,
                "programs_stale": stale_count,
            }

        except Exception as e:
            logger.error("Pipeline failed", error=str(e))
            async with self.session_factory() as session:
                entry = await session.get(ScrapeLog, log_id)
                if entry:
                    entry.finished_at = datetime.utcnow()
                    entry.status = "failed"
                    entry.error_message = str(e)
                    await session.commit()
            raise
        finally:
            await self.engine.dispose()

    async def _geocode_programs(self, programs):
        already = sum(1 for p in programs if getattr(p, "latitude", None) and getattr(p, "longitude", None))
        needs = [p for p in programs if not (getattr(p, "latitude", None) and getattr(p, "longitude", None)) and (p.city or p.state or p.zip_code)]

        logger.info("Geocoding", already_have=already, need=len(needs))
        if not needs:
            return already

        unique = set((p.city, p.state, p.zip_code) for p in needs)
        results = await self.geocoder.batch_geocode(list(unique), concurrency=3)

        geocoded = 0
        for p in needs:
            key = self.geocoder._cache_key(p.city, p.state, p.zip_code)
            if key in results:
                geo = results[key]
                p.latitude = geo.latitude
                p.longitude = geo.longitude
                p.geocode_quality = geo.quality
                geocoded += 1

        return already + geocoded

    async def _store_programs(self, programs):
        new_count = updated_count = 0
        async with self.session_factory() as session:
            for prog in programs:
                existing = await session.execute(
                    select(Program).where(
                        Program.company == prog.company,
                        Program.city == prog.city,
                        Program.state == prog.state,
                        Program.job_family == prog.job_family,
                    )
                )
                ex = existing.scalar_one_or_none()

                if ex:
                    for f in ["description","program_duration","duration_min_days","duration_max_days",
                              "opportunity_type","delivery_method","target_moc","employer_poc_name",
                              "employer_poc_email","employer_website","army","navy","air_force",
                              "marines","coast_guard","space_force","industry","nationwide","online"]:
                        v = getattr(prog, f, None)
                        if v:
                            setattr(ex, f, v)
                    if getattr(prog, "latitude", None) and (not ex.latitude or ex.geocode_quality in ("state_centroid","zip_centroid")):
                        ex.latitude = prog.latitude
                        ex.longitude = prog.longitude
                        ex.geocode_quality = getattr(prog, "geocode_quality", "api_provided")
                    ex.updated_at = datetime.utcnow()
                    ex.is_active = True
                    updated_count += 1
                else:
                    db_prog = Program(
                        company=prog.company, city=prog.city, state=prog.state,
                        zip_code=prog.zip_code, location_raw=prog.location_raw,
                        nationwide=prog.nationwide, online=prog.online,
                        program_duration=prog.program_duration,
                        duration_min_days=prog.duration_min_days,
                        duration_max_days=prog.duration_max_days,
                        opportunity_type=prog.opportunity_type,
                        delivery_method=prog.delivery_method,
                        description=prog.description, job_family=prog.job_family,
                        target_moc=prog.target_moc,
                        employer_poc_name=prog.employer_poc_name,
                        employer_poc_email=prog.employer_poc_email,
                        employer_website=prog.employer_website,
                        army=prog.army, navy=prog.navy, air_force=prog.air_force,
                        marines=prog.marines, coast_guard=prog.coast_guard,
                        space_force=prog.space_force,
                        latitude=getattr(prog, "latitude", None),
                        longitude=getattr(prog, "longitude", None),
                        geocode_quality=getattr(prog, "geocode_quality", None),
                        industry=getattr(prog, "industry", None),
                        source_url=prog.source_url, source_page=prog.source_page,
                    )
                    session.add(db_prog)
                    new_count += 1
            await session.commit()
        return new_count, updated_count

    async def _mark_stale(self, fresh):
        fps = set(p.fingerprint for p in fresh)
        stale = 0
        async with self.session_factory() as session:
            result = await session.execute(select(Program).where(Program.is_active))
            for prog in result.scalars().all():
                raw = f"{prog.company}|{prog.city}|{prog.state}|{prog.job_family}|{prog.opportunity_type}"
                if hashlib.md5(raw.encode()).hexdigest() not in fps:
                    prog.is_active = False
                    prog.updated_at = datetime.utcnow()
                    stale += 1
            if stale:
                await session.commit()
        return stale
