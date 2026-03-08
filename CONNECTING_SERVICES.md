# Connecting FOB V2 to Supabase, Vercel, GitHub & API

This guide walks through connecting your app to **Supabase**, **Vercel**, **GitHub**, and your **backend API** (and related services).

---

## 1. Supabase

You already have Supabase in `web/.env`. For **production** (Vercel), use the same project.

### In Supabase Dashboard

1. Go to [app.supabase.com](https://app.supabase.com) → your project.
2. **Settings → API**: copy **Project URL** and **anon public** key (you already use these in `.env`).
3. **Authentication → URL Configuration**:
   - **Site URL**: set to your production URL, e.g. `https://your-app.vercel.app` (or your custom domain).
   - **Redirect URLs**: add:
     - `https://your-app.vercel.app/**`
     - `https://your-app.vercel.app`
     - (and your custom domain if you add one)

Without these, sign-in (especially OAuth/magic link) may fail in production.

### Env vars (local already set in `web/.env`)

| Variable | Where | Purpose |
|----------|--------|---------|
| `VITE_SUPABASE_URL` | `web/.env` + Vercel | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | `web/.env` + Vercel | Supabase anon (public) key |

For the **API** (JWT verification on protected routes), set in the **API** env (e.g. Render/Railway):

| Variable | Where | Purpose |
|----------|--------|---------|
| `SUPABASE_URL` | `api/.env` + API host | Same Supabase project URL |
| `SUPABASE_JWT_SECRET` | `api/.env` + API host | Supabase **JWT Secret** (Settings → API), not the anon key |

---

## 2. GitHub

Use GitHub as the source for Vercel (and optional CI).

### Option A: New repository

1. Create a new repo on [github.com](https://github.com) (e.g. `your-org/fob-v2`).
2. In your project folder (FOB V2):

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_ORG/fob-v2.git
   git push -u origin main
   ```

3. If you have a `.gitignore`, ensure it includes `.env`, `node_modules`, `api/.venv`, etc., so secrets are not pushed.

### Option B: Existing repository

Clone or open the repo and push your latest code.

### After the repo exists

- Vercel will connect to this repo for **automatic deploys** on push.
- Optionally add **GitHub Actions** later for tests/lint (e.g. run `npm run lint` and `npm run test:e2e` in `web/`).

---

## 3. Vercel (frontend)

Deploy the **web** app (Vite/React) to Vercel.

### Import project

1. Go to [vercel.com](https://vercel.com) and sign in (GitHub is easiest).
2. **Add New → Project** and **Import** your GitHub repository.
3. **Configure**:
   - **Root Directory**: set to `web` (so Vercel builds the Vite app).
   - **Framework Preset**: Vite (should auto-detect).
   - **Build Command**: `npm run build` (default).
   - **Output Directory**: `dist` (Vite default).
   - **Install Command**: `npm install`.

### Environment variables (required for production)

In the Vercel project: **Settings → Environment Variables**. Add these for **Production** (and optionally Preview):

| Name | Value | Notes |
|------|--------|------|
| `VITE_SUPABASE_URL` | Your Supabase project URL | Same as in `web/.env` |
| `VITE_SUPABASE_ANON_KEY` | Your Supabase anon key | Same as in `web/.env` |
| `VITE_API_BASE` | Your **deployed** API URL | e.g. `https://your-api.onrender.com` (no trailing slash). Use your real API host when deployed. |
| `VITE_MAPBOX_TOKEN` | Your Mapbox token | Same as in `web/.env` if you use maps |

Redeploy after adding or changing env vars (Vite bakes `VITE_*` in at build time).

### Optional: custom domain

In Vercel: **Settings → Domains** → add your domain and follow the DNS steps. Then add that domain to Supabase **Redirect URLs** and **Site URL** as above.

---

## 4. Backend API (FastAPI)

The `api/` app is a separate service. Deploy it to a host that runs Python (e.g. **Render**, **Railway**, **Fly.io**, or a VPS). Vercel can run serverless functions, but the current `api` is a full FastAPI app; Render/Railway are straightforward.

### Example: Render

1. Create a **Web Service**; connect the same GitHub repo.
2. **Root Directory**: `api` (or where your FastAPI app lives).
3. **Build**: e.g. `pip install -r requirements.txt` (if you have one) or equivalent.
4. **Start**: e.g. `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
5. Set **Environment** variables (see `api/.env.example`), including:
   - `DATABASE_URL`, `REDIS_URL` (if you use them)
   - `SUPABASE_URL`, `SUPABASE_JWT_SECRET` (for protected endpoints)
   - `CORS_ORIGINS`: include your Vercel URL, e.g. `["https://your-app.vercel.app"]`

### CORS

Your API’s `config.py` has `cors_origins`. For production, add your frontend origin(s), e.g.:

- `https://your-app.vercel.app`
- `https://your-custom-domain.com`

Set via env, e.g. `CORS_ORIGINS=["https://your-app.vercel.app"]`, if your app reads CORS from the environment.

### After API is deployed

Set **VITE_API_BASE** in Vercel to the API’s public URL (e.g. `https://your-api.onrender.com`) and redeploy the web app.

---

## 5. Other services (optional)

| Service | Purpose | Where to set |
|--------|---------|--------------|
| **Mapbox** | Maps (e.g. Career Map) | `VITE_MAPBOX_TOKEN` in `web/.env` and Vercel |
| **Anthropic (Claude)** | AI features in API | `ANTHROPIC_API_KEY` in API env (e.g. Render) |
| **Google CSE** | Employment/Networking search | `GOOGLE_CSE_API_KEY`, `GOOGLE_CSE_CX` in API env |
| **OpenCage / Geocoding** | Geocoding in API | `GEOCODING_API_KEY` in API env |
| **Vercel Analytics** | Analytics | Enable in Vercel project dashboard |

---

## Quick checklist

- [ ] **Supabase**: Site URL and Redirect URLs updated for production domain.
- [ ] **GitHub**: Repo created/updated and code pushed.
- [ ] **Vercel**: Project imported from GitHub, root = `web`, env vars set (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE`, `VITE_MAPBOX_TOKEN`).
- [ ] **API**: Deployed (e.g. Render); `CORS_ORIGINS` includes Vercel URL; `SUPABASE_URL` and `SUPABASE_JWT_SECRET` set.
- [ ] **Vercel**: `VITE_API_BASE` points to deployed API URL; redeploy after any env change.

Your local `web/.env` already has Supabase and Mapbox; use the same values (and a production API URL) in Vercel for a full production setup.
