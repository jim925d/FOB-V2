# SkillBridge API — The FOB Backend

Production-ready FastAPI backend that scrapes, geocodes, and serves all 10,000+ DoD SkillBridge programs.

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────┐
│  Weekly Cron     │────▶│  Scraper      │────▶│  PostgreSQL   │
│  (APScheduler)   │     │  + Geocoder   │     │  + Redis      │
└─────────────────┘     └──────────────┘     └──────┬───────┘
                                                     │
                                              ┌──────▼───────┐
                                              │  FastAPI      │
                                              │  /api/v1/     │
                                              │  programs     │
                                              └──────┬───────┘
                                                     │
                                              ┌──────▼───────┐
                                              │  The FOB      │
                                              │  Frontend     │
                                              └──────────────┘
```

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Edit .env with your database URL and API keys

# 3. Initialize database
python -m app.models.database

# 4. Run initial scrape
python -m scripts.initial_scrape

# 5. Start API server
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/programs` | List programs with filters |
| GET | `/api/v1/programs/{id}` | Get single program detail |
| GET | `/api/v1/programs/map` | Map-optimized (clustered) data |
| GET | `/api/v1/programs/stats` | Aggregate statistics |
| GET | `/api/v1/industries` | List all industries |
| GET | `/api/v1/states` | List all states with counts |
| POST | `/api/v1/scrape/trigger` | Trigger manual scrape (auth required) |
| GET | `/api/v1/health` | Health check |

## Query Parameters (GET /programs)

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Search company, role, description |
| `state` | string | Filter by state (e.g., "VA") |
| `industry` | string | Filter by industry category |
| `city` | string | Filter by city |
| `remote` | bool | Filter remote-eligible |
| `lat` | float | Center latitude for distance search |
| `lon` | float | Center longitude for distance search |
| `radius_miles` | int | Radius in miles (requires lat/lon) |
| `min_duration` | int | Minimum program duration (days) |
| `max_duration` | int | Maximum program duration (days) |
| `sort` | string | Sort field: `company`, `city`, `state`, `duration` |
| `order` | string | `asc` or `desc` |
| `page` | int | Page number (default: 1) |
| `per_page` | int | Results per page (default: 50, max: 200) |

## Deployment

Designed for Render or Fly.io with PostgreSQL and Redis addons.

```bash
# Render
render deploy

# Fly.io
fly launch
fly deploy
```

## Environment Variables

```
DATABASE_URL=postgresql://user:pass@host:5432/skillbridge
REDIS_URL=redis://localhost:6379
GEOCODING_API_KEY=your_opencage_or_google_key
SCRAPE_INTERVAL_HOURS=168  # weekly
API_SECRET_KEY=your_secret_for_admin_endpoints
```

### Local search (Employment Networking — results from Google)

To show **Google search results** in the “Local veteran networking by ZIP” table, set:

- **`GOOGLE_CSE_API_KEY`** — From [Google Cloud Console](https://console.cloud.google.com/): enable “Custom Search API”, then create an API key.
- **`GOOGLE_CSE_CX`** — From [Programmable Search Engine](https://programmablesearchengine.google.com/): create a search engine that searches “the entire web” (or add a single site like `*`), then copy the “Search engine ID” (cx).

Without these, the table shows a single row that opens the same query on Google in a new tab. Optional fallback: **`SERP_API_KEY`** (SerpAPI) if you prefer not to use Google CSE.
