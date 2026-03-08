#!/usr/bin/env python3
"""
Veteran events scraper — Run weekly to capture Google results for "veteran networking events"
and store them in the Supabase veteran_events table.

Usage:
    py -m scripts.run_veteran_events_scrape

  - .env: DATABASE_URL; and either GOOGLE_CSE_API_KEY + GOOGLE_CSE_CX (Option A) or SERP_API_KEY (Option B). See docs/VETERAN-EVENTS-SCRAPE.md.
  - Run supabase/migrations/001_fob_full_schema.sql on your FOB project so veteran_events exists.

Run from skillbridge-api: py -m scripts.run_veteran_events_scrape
"""

import asyncio
import sys

from app.config import get_settings
from app.models.database import get_async_engine, get_async_session_factory
from app.services.networking_events_scraper import run_weekly_scrape


async def main():
    settings = get_settings()
    if not settings.google_cse_api_key and not settings.serp_api_key:
        print("Error: Set GOOGLE_CSE_API_KEY and GOOGLE_CSE_CX, or SERP_API_KEY, in .env (see docs/VETERAN-EVENTS-SCRAPE.md)")
        sys.exit(1)
    if not settings.database_url or "postgres" not in settings.database_url:
        print("Error: Set DATABASE_URL in .env (e.g. Supabase connection string)")
        sys.exit(1)

    print("Veteran events scrape — query: 'veteran networking events' per state")
    print("Using:", "Google CSE" if settings.google_cse_api_key else "SerpAPI")
    engine = get_async_engine(settings.database_url)
    factory = get_async_session_factory(engine)
    try:
        async with factory() as session:
            result = await run_weekly_scrape(session)
        print(f"Done: states={result.get('states', 0)}, inserted={result.get('inserted', 0)}")
        if result.get("error"):
            print("Warning:", result["error"])
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
