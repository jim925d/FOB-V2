#!/usr/bin/env python3
"""
ERG scraper CLI — Seed data and (future) multi-source scrape.

Usage:
    python -m scripts.run_erg_scrape --seed              # Load seed data only
    python -m scripts.run_erg_scrape --source all         # Run all scrapers (TODO)
    python -m scripts.run_erg_scrape --source vjm         # Veteran Jobs Mission only (TODO)
    python -m scripts.run_erg_scrape --source enrich      # Enrichment pass only (TODO)
    python -m scripts.run_erg_scrape --stats              # Show DB stats

Run from repo root: cd skillbridge-api && python -m scripts.run_erg_scrape --seed
"""

import asyncio
import argparse
import sys

from app.config import get_settings
from app.models.database import get_async_engine, get_async_session_factory
from app.services import erg_service


async def run_seed():
    settings = get_settings()
    engine = get_async_engine(settings.database_url)
    factory = get_async_session_factory(engine)
    async with factory() as session:
        inserted, updated = await erg_service.load_seed_data(session)
        print(f"Seed complete: inserted={inserted}, updated={updated}")
    await engine.dispose()


async def run_stats():
    settings = get_settings()
    engine = get_async_engine(settings.database_url)
    factory = get_async_session_factory(engine)
    async with factory() as session:
        stats = await erg_service.get_stats(session)
        print("ERG directory stats:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    await engine.dispose()


async def run_scrape(source: str):
    from app.scrapers.erg_seed_data import KNOWN_ERGS
    from app.scrapers.erg_scraper import (
        scrape_veteran_jobs_mission,
        scrape_military_friendly,
        merge_and_dedupe,
    )
    from app.services import erg_service

    settings = get_settings()
    engine = get_async_engine(settings.database_url)
    factory = get_async_session_factory(engine)

    if source == "enrich":
        print("Enrichment pass: run --seed first, then implement enrich_records + DB update in script.")
        await engine.dispose()
        return

    vjm = []
    mf = []
    if source in ("all", "vjm"):
        print("Scraping Veteran Jobs Mission...")
        vjm = scrape_veteran_jobs_mission()
    if source == "all":
        print("Scraping Military Friendly...")
        mf = scrape_military_friendly()

    # Normalize KNOWN_ERGS to have company_name
    known = [{"company_name": r.get("company", r.get("company_name")), **r} for r in KNOWN_ERGS]
    merged = merge_and_dedupe(vjm, mf, known)

    async with factory() as session:
        ins, upd = await erg_service.upsert_scraped_records(session, merged, source_type="scraped")
        print(f"Scrape upsert: inserted={ins}, updated={upd}")

    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="ERG directory scraper/seed")
    parser.add_argument("--seed", action="store_true", help="Load seed data (KNOWN_ERGS)")
    parser.add_argument("--source", type=str, help="Scrape source: all | vjm | enrich")
    parser.add_argument("--stats", action="store_true", help="Print directory stats and exit")
    args = parser.parse_args()

    if args.stats:
        asyncio.run(run_stats())
        return
    if args.seed:
        asyncio.run(run_seed())
        return
    if args.source:
        asyncio.run(run_scrape(args.source))
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
