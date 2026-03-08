# Adding Back Full Content (Supabase + API)

**For connecting Supabase, Vercel, GitHub, and deploying to production**, see **[CONNECTING_SERVICES.md](../CONNECTING_SERVICES.md)** in the project root.

The app runs with **defaults** when env vars are missing or placeholder. To get **auth, user data, and API-driven content** back:

## 1. Create `.env` in the `web` folder

Copy the example and edit with your real values:

```bash
cd web
cp .env.example .env
```

(On Windows PowerShell: `Copy-Item .env.example .env`)

## 2. Fill in `.env`

| Variable | Purpose | Example / Where to get it |
|----------|---------|---------------------------|
| **VITE_SUPABASE_URL** | Supabase project URL | [Supabase Dashboard](https://app.supabase.com) → your project → Settings → API → Project URL |
| **VITE_SUPABASE_ANON_KEY** | Supabase anonymous (public) key | Same place → Project API keys → `anon` `public` |
| **VITE_API_BASE** | Backend API base URL | Your FastAPI/backend root, e.g. `http://localhost:8000` (no trailing slash) |
| **VITE_MAPBOX_TOKEN** | Mapbox for maps (optional) | [Mapbox](https://account.mapbox.com) → Access tokens |

- Use **real** Supabase values. If you leave `your-project` or `your-anon-key`, the app will keep using the no-op defaults.
- For **VITE_API_BASE**: if your backend runs at `http://localhost:8000`, set that. If you don’t have the backend running, Pathfinder, SkillBridge, News, etc. will show errors when those features call the API.

## 3. Restart the dev server

After saving `.env`:

```bash
# Stop the current server (Ctrl+C), then:
npm run dev
```

## What comes back when configured

| With Supabase only | With API only | With both |
|-------------------|----------------|-----------|
| Sign In / Sign Out, Google OAuth, magic link | Career Pathfinder (roles, roadmap), SkillBridge, Communities, ERGs, News, Networking | Full app: auth + all API content + dashboard profile |

- **Supabase** → Auth and user-related data (profiles, dashboard).
- **API (VITE_API_BASE)** → Career Pathfinder, SkillBridge programs, communities, ERGs, VA news, networking.

If you don’t have a backend yet, set at least **VITE_SUPABASE_URL** and **VITE_SUPABASE_ANON_KEY** to get sign-in and user content back; API-backed pages will need the backend running and **VITE_API_BASE** set.
