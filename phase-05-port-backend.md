# Phase 5 — Port Backend

## Objective

Port the backend from `skillbridge-api` into the project as `api/` so the frontend (Pathfinder, SkillBridge, News, etc.) can connect to a single local or deployed API.

## What Was Done

1. **Copy backend** — Contents of `skillbridge-api` (from parent FOB folder or equivalent) were copied into `api/` at the repo root, excluding `__pycache__`, `.env`, `.git`, `.pytest_cache`, `venv`, and log files.

2. **API response shape for Pathfinder**
   - **Roles** — Backend now returns grouped format expected by the frontend:  
     `[{ "label": "Military", "options": [{ "value", "label" }] }, { "label": "Civilian", "options": [...] }]`  
     so the Current Role / MOS dropdown works without frontend changes.
   - **Targets** — Backend returns a flat list with `value`, `label`, `group`. The frontend uses `toGrouped(targetsRaw, "group")` so the Target Role dropdown works.

3. **Pathfinder payload adapter** — Backend `/api/v1/roadmap/generate` accepts the frontend’s payload:
   - `current_role_id`, `target_role_id`, `separation_timeline`, `education`, `years_in_role`, `target_industry`
   - These are mapped to the internal pathfinder format (`current_role`, `target_role`, `timeline`, etc.).  
   - `separation_timeline` values (`0-6`, `6-12`, `12-18`, `18+`) are mapped to backend `TimelineUrgency` values.

4. **Frontend connection**
   - Frontend uses `VITE_API_BASE` (e.g. `http://localhost:8000`) in `web/.env`.
   - All API calls go through `web/src/lib/api.js` to `${VITE_API_BASE}/api/v1/...`.

## Running Locally

### Backend (api/)

```bash
cd api
python -m venv .venv
.venv\Scripts\activate   # Windows
# or: source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env     # edit .env with DATABASE_URL etc. if using DB
uvicorn app.main:app --reload --port 8000
```

- Without a database the API still runs; Pathfinder roles/targets and roadmap generation use in-memory data.
- With a database you get SkillBridge programs, caching, and scheduled scrapes.

### Frontend (web/)

```bash
cd web
npm install
# Ensure .env has: VITE_API_BASE=http://localhost:8000
npm run dev
```

- Open the app (e.g. http://localhost:5173), go to Pathfinder, and confirm dropdowns load and “Generate Career Map” works.

## Folder Layout (After Phase 5)

```
<repo>/
├── api/                 # Ported backend (FastAPI)
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routes/      # career, roadmap, programs, news, etc.
│   │   ├── services/
│   │   ├── data/
│   │   └── ...
│   ├── requirements.txt
│   ├── .env.example
│   └── ...
├── web/                 # Frontend (Vite + React)
│   ├── src/
│   │   ├── lib/api.js   # Single API client
│   │   └── ...
│   └── .env             # VITE_API_BASE=http://localhost:8000
└── phase-05-port-backend.md
```

## Deploy

- **Frontend:** Deploy `web/` to Vercel (or similar). Set env var `VITE_API_BASE` to your backend URL (e.g. `https://your-api.onrender.com`).
- **Backend:** Deploy `api/` to Render (or similar). Set `CORS_ORIGINS` to include your frontend origin(s).

## Checklist

- [x] Backend copied into `api/`
- [x] Roles endpoint returns grouped format for Pathfinder
- [x] Targets endpoint returns flat list with `group` (frontend groups by `group`)
- [x] Roadmap generate accepts `current_role_id`, `target_role_id`, `separation_timeline`
- [x] Frontend uses `VITE_API_BASE`; Pathfinder and roadmap work when API is running
