# Veteran events scrape — capture Google results into the DB

The Employment & Networking page shows a **Local Search** section: users enter a ZIP (or state) and see veteran networking events. Those results come from the **`veteran_events`** table in Supabase when it's populated.

## How it works

1. **Weekly scrape** runs a Google search for **"veteran networking events"** once per US state (e.g. "veteran networking events California").
2. Results (title, link, snippet, etc.) are stored in **`veteran_events`** in your FOB Supabase project.
3. When a user searches by ZIP or state on the Employment & Networking page, the API reads from **`veteran_events`** first and returns those rows. If the table is empty, it falls back to live Google/SerpAPI or curated events.

So you need to **run the scrape at least once** (and optionally on a schedule) to fill the table.

## Prerequisites

1. **Supabase:** Run `skillbridge-explorer/supabase/migrations/001_fob_full_schema.sql` in your FOB project so the `veteran_events` table exists.
2. **API .env** (`skillbridge-api/.env`):
   - **`DATABASE_URL`** — FOB Postgres connection string (same as for ERGs).
   - **Search:** either **Google CSE** (Option A) or **SerpAPI** (Option B) below.

Google no longer offers **"Search the entire web"** for new Programmable Search Engines. Use either a CSE that searches specific sites (Option A) or SerpAPI for full Google search (Option B).

---

### Option A: Google CSE (search specific sites)

Add these **Sites to search** in [Programmable Search Engine](https://programmablesearchengine.google.com/) — one URL per line. Queries like "veteran networking events California" will then return events from these domains:

- `https://www.eventbrite.com`
- `https://www.meetup.com`
- `https://www.vfw.org`
- `https://www.legion.org`
- `https://recruitmilitary.com`
- `https://www.hireheroesusa.org`
- `https://bunkerlabs.org`
- `https://vetsintech.co`
- `https://fourblock.org`
- `https://www.acp-usa.org`
- `https://breakline.org`
- `https://www.va.gov`
- `https://www.dav.org`
- `https://www.score.org`
- `https://www.sba.gov`

**When creating the engine:**

| Field | What to enter |
|--------|----------------|
| **Search engine name** | Any name (e.g. `Veteran Networking Events`). |
| **Sites to search** | Paste the URLs above, one per line. You can add more veteran/event sites. |
| **SafeSearch** (Customize → Basics) | Off or Moderate. |
| **Image search** | Leave off. |

Copy the **Search engine ID** from **Customize** → **Basics** — that is **`GOOGLE_CSE_CX`**.

Then in [Google Cloud Console](https://console.cloud.google.com/): enable **Custom Search API**, create an **API key**, and set **`GOOGLE_CSE_API_KEY`** in `.env`.

---

### Option B: SerpAPI (full Google search)

If you want results from the whole web (not just the sites above), use [SerpAPI](https://serpapi.com/). Sign up, get an API key, and add to `.env`:

```env
SERP_API_KEY=your_serpapi_key_here
```

The scrape script uses SerpAPI when CSE keys are not set. SerpAPI has a free tier with limited searches; paid plans for more.

---

### Add to `.env`

**Option A (Google CSE):**
```env
GOOGLE_CSE_API_KEY=your_api_key_here
GOOGLE_CSE_CX=your_search_engine_id_here
```

**Option B (SerpAPI):**
```env
SERP_API_KEY=your_serpapi_key_here
```

## Run the scrape

From the **`skillbridge-api`** directory:

```bash
py -m scripts.run_veteran_events_scrape
```

- One search per state (51 total), with a short delay between requests to avoid rate limits.
- The script clears `veteran_events` and refills it for this run.
- When it finishes, the Employment & Networking Local Search will show these events (by state; ZIP maps to state).

## Schedule it (optional)

Run the same command weekly (e.g. cron or Task Scheduler):

- **Cron (Linux/macOS):** `0 3 * * 0 cd /path/to/skillbridge-api && py -m scripts.run_veteran_events_scrape`
- **Windows Task Scheduler:** Create a task that runs `py -m scripts.run_veteran_events_scrape` with working directory `skillbridge-api`.

## Troubleshooting

- **"No API key configured"** — Set either `GOOGLE_CSE_API_KEY` + `GOOGLE_CSE_CX` (Option A) or `SERP_API_KEY` (Option B) in `.env`.
- **"veteran_events table may not exist"** — Run the FOB migration SQL so `veteran_events` is created.
- **Empty results on the site** — Run the scrape at least once after the migration; the UI reads from the DB first.
- **CSE returns no/few results** — Make sure you added the sites listed in Option A (one URL per line). Add more veteran or local-event domains if needed.
