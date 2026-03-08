# Step-by-step: Run API (Terminal 1) and Communities Scrape (Terminal 2)

## Database required

The communities scraper and API **require PostgreSQL**. If you see:

- `"Database not available — communities require a database connection"`

then the API could not connect to the DB at startup. Do this:

1. **Install PostgreSQL** (if needed): [PostgreSQL downloads](https://www.postgresql.org/download/windows/).
2. **Start the PostgreSQL service** (e.g. from Services, or `pg_ctl start`).
3. **Create the database** (if it doesn’t exist):
   ```powershell
   psql -U postgres -c "CREATE DATABASE skillbridge;"
   ```
   (Use the same user/password as in your connection string.)
4. **Set the connection string** in `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/skillbridge
   ```
   Default (no `.env` override) is `postgresql+asyncpg://postgres:postgres@localhost:5432/skillbridge`.
5. **Restart the API** (Terminal 1). You should see `Database connected` in the logs. Then run the refresh again in Terminal 2.

---

## Terminal 1 — Start the API server

Run these commands in **Terminal 1**. The server must stay running.

### 1. Go to the API project folder

```powershell
cd c:\Users\james\OneDrive\FOB\skillbridge-api
```

### 2. (Optional) Activate the virtual environment

If you use a venv:

```powershell
.\venv\Scripts\Activate
```

### 3. (Optional) Set environment variables

If you use a `.env` file, make sure it exists and has at least:

- `DATABASE_URL` — e.g. `postgresql+asyncpg://postgres:postgres@localhost:5432/skillbridge`

If you don’t have a database, the API will still start but will log that the database is unavailable; the communities endpoints will return 503 until the DB is connected.

### 4. Start the API

```powershell
uvicorn app.main:app --reload --port 8000
```

You should see something like:

- `INFO:     Uvicorn running on http://127.0.0.1:8000`
- `Database connected` (if DB is configured)
- `API startup complete`

Leave this terminal open. The API is now available at **http://localhost:8000**.

---

## Terminal 2 — Run the communities scrape (first time)

Open a **second terminal**. Run these commands **after** the API in Terminal 1 is running.

### 1. Go to the API project folder

```powershell
cd c:\Users\james\OneDrive\FOB\skillbridge-api
```

### 2. (Optional) Activate the virtual environment

```powershell
.\venv\Scripts\Activate
```

### 3. Trigger the communities scrape

In PowerShell, use `Invoke-WebRequest` (or `Invoke-RestMethod`). **Do not use `curl`** — in PowerShell it is an alias and does not accept `-X POST`.

**Option A — No secret (if `api_secret_key` is not set or empty in `.env`):**

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/communities/refresh" -Method POST
```

**Option B — With secret (if you set `API_SECRET_KEY` in `.env`):**

Replace `YOUR_SECRET` with the value of `api_secret_key` from your `.env`:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/communities/refresh?secret=YOUR_SECRET" -Method POST
```

To see the full response (including status code), use `Invoke-WebRequest` and then `.Content`:

```powershell
(Invoke-WebRequest -Uri "http://localhost:8000/api/v1/communities/refresh" -Method POST).Content
```

### 4. What to expect

- The request may take a while (the scraper paginates ProPublica and enriches each org).
- A successful response is JSON like:
  `{"total_new": ..., "total_updated": ..., "total_errors": 0, "total_processed": ...}`

After this, **GET** `http://localhost:8000/api/v1/communities` will return the scraped organizations (and the frontend Communities tab can use them).

---

## Quick checks

- **API health:** open in browser or run:  
  `curl http://localhost:8000/`
- **List communities (after scrape):**  
  `curl "http://localhost:8000/api/v1/communities?limit=5"`
- **Categories with counts:**  
  `curl "http://localhost:8000/api/v1/communities/categories"`
