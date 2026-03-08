#!/usr/bin/env python3
"""
Initial Scrape Script — Run once to populate the database.

Usage:
    python -m scripts.initial_scrape [--max-pages 10] [--dry-run]

This runs the full pipeline:
1. Scrapes skillbridge.osd.mil
2. Geocodes all locations
3. Stores in PostgreSQL
"""

import asyncio
import argparse
import sys
import time

import structlog

from app.config import get_settings
from app.models.database import init_db
from app.services.pipeline import ScrapePipeline

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
)
logger = structlog.get_logger()


async def main(max_pages: int = None, dry_run: bool = False):
    settings = get_settings()

    logger.info("=" * 60)
    logger.info("The FOB — SkillBridge Initial Scrape")
    logger.info("=" * 60)
    logger.info("Database", url=settings.database_url[:50] + "...")
    logger.info("Geocoding provider", provider=settings.geocoding_provider)
    logger.info("Max pages", max_pages=max_pages or "unlimited")
    logger.info("Dry run", dry_run=dry_run)
    logger.info("")

    # Initialize database tables
    logger.info("Initializing database...")
    await init_db(settings.database_url)
    logger.info("Database ready")

    if dry_run:
        logger.info("DRY RUN — testing scraper only (no DB writes)")
        from app.scrapers.skillbridge_scraper import SkillBridgeScraper
        scraper = SkillBridgeScraper()
        programs = await scraper.scrape_all(max_pages=max_pages or 3)
        logger.info(f"Found {len(programs)} programs in dry run")
        for p in programs[:10]:
            logger.info(f"  {p.company} | {p.city}, {p.state} | {p.industry}")
        if len(programs) > 10:
            logger.info(f"  ... and {len(programs) - 10} more")
        return

    # Run full pipeline
    start = time.time()
    pipeline = ScrapePipeline()
    result = await pipeline.run(max_pages=max_pages)
    elapsed = time.time() - start

    logger.info("")
    logger.info("=" * 60)
    logger.info("SCRAPE COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Status:           {result['status']}")
    logger.info(f"Pages scraped:    {result['pages_scraped']}")
    logger.info(f"Programs found:   {result['programs_found']}")
    logger.info(f"New programs:     {result['programs_new']}")
    logger.info(f"Updated programs: {result['programs_updated']}")
    logger.info(f"Geocoded:         {result['programs_geocoded']}")
    logger.info(f"Time elapsed:     {elapsed:.1f}s")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initial SkillBridge scrape")
    parser.add_argument("--max-pages", type=int, default=None, help="Max pages to scrape")
    parser.add_argument("--dry-run", action="store_true", help="Test scraper without DB writes")
    args = parser.parse_args()

    asyncio.run(main(max_pages=args.max_pages, dry_run=args.dry_run))
