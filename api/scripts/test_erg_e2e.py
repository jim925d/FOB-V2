#!/usr/bin/env python3
"""
Manual E2E test for ERG directory: load seed data, then hit list/stats/industries.
Requires DATABASE_URL (or default Postgres) and corporate_ergs table (run migrations first).

Usage (from repo root):
  cd skillbridge-api
  .\\venv\\Scripts\\Activate.ps1   # or: source venv/bin/activate
  python -m scripts.test_erg_e2e
"""

import asyncio
import os
import sys


async def main():
    from app.config import get_settings
    from app.models.database import get_async_engine, get_async_session_factory
    from app.services import erg_service

    settings = get_settings()
    url = os.environ.get("DATABASE_URL") or settings.database_url
    if "asyncpg" not in url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print("ERG E2E test")
    print("Database:", url.split("@")[-1] if "@" in url else url[:50] + "...")
    print()

    engine = get_async_engine(url)
    factory = get_async_session_factory(engine)

    async with factory() as session:
        # 1) Load seed
        print("1. Loading seed data...")
        try:
            inserted, updated = await erg_service.load_seed_data(session)
            print(f"   Seed: inserted={inserted}, updated={updated}")
        except Exception as e:
            print(f"   FAIL:", e)
            await engine.dispose()
            sys.exit(1)

        # 2) Stats
        print("2. Stats...")
        try:
            stats = await erg_service.get_stats(session)
            for k, v in stats.items():
                print(f"   {k}: {v}")
        except Exception as e:
            print(f"   FAIL:", e)

        # 3) List
        print("3. List ERGs (first 5)...")
        try:
            items, total = await erg_service.list_ergs(
                session, page=1, per_page=5, sort="company_name", order="asc"
            )
            print(f"   total={total}")
            for e in items:
                print(f"   - {e.company_name} | {e.erg_name or '(no name)'}")
        except Exception as e:
            print(f"   FAIL:", e)

        # 4) Industries
        print("4. Industries (top 5)...")
        try:
            ind = await erg_service.get_industries_with_counts(session)
            for row in ind[:5]:
                print(f"   - {row['industry']}: {row['count']}")
        except Exception as e:
            print(f"   FAIL:", e)

    await engine.dispose()
    print()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
