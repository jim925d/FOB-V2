# The FOB — Full Rebuild & Migration Document

**Purpose:** This document is the single source of truth for rebuilding The FOB from a patched, iteratively-built app into a clean, production-grade platform. Upload this to Cursor alongside the project files and execute phase-by-phase.

**Date:** 2026-03-06
**Author:** Jim + Claude (architecture partner)

---

## Table of Contents

1. Current State Audit
2. Stack Recommendations
3. New Project Structure
4. Information Architecture & UX Redesign
5. Design System Formalization
6. Database Schema (Consolidated)
7. API Contract (Consolidated)
8. Implementation Phases (Cursor-Ready)
9. Reference Files

---

## 1. Current State Audit

### What exists and works

- **SkillBridge Explorer** — Interactive map + search across 3,053 DoD programs. Fully functional.
- **Career Pathfinder** — MOS-to-civilian career matching with roadmap generation (72 MOS codes, TF-IDF + cosine similarity). Recently redesigned with Sankey diagram visualization + card progression view.
- **Benefits Navigator** — VA education benefits, VA loans, and related resources.
- **Communities Directory** — 45+ veteran organizations with search and filtering.
- **ERG Directory** — 225+ companies with Employee Resource Group data.
- **VA News** — Live RSS feed from 7 veteran-focused news sources (Military Times, Stars & Stripes, Task & Purpose, VA Vantage Point, Defense.gov, DAV, Military.com).
- **Employment Networking** — LinkedIn networking roadmap feature (CSV-based MVP).
- **Auth** — Supabase PKCE + magic link + Google OAuth.
- **Dashboard** — User-specific saved items (roadmaps, programs, benefits progress, events, reminders).

### What's broken or duct-taped

- **CRA + CRACO** — Create React App is deprecated. CRACO is a workaround on top of a workaround. Build times are slow, config is brittle.
- **Folder naming** — Root folders still named `skillbridge-explorer` and `skillbridge-api` from the original SkillBridge-only scope. The product is "The FOB" now.
- **Root-level clutter** — 10+ prototype folders (`Benefits Navigator/`, `Career Pathfinder/`, `Career Roadmap/`, etc.), prompt files, zip archives, and a duplicate backend folder (`skillbridge-api-backend/`).
- **Component organization** — `CareerRoadmap.jsx` sits at `src/` root instead of in `src/pages/` or `src/components/career/`. Some components have co-located CSS, others use global CSS, others use inline styles.
- **CSS layering** — Four CSS files (`index.css`, `design-tokens.css`, `globals.css`, `components.css`) with overlapping scope. Tailwind v4 is installed but not consistently used alongside custom CSS classes.
- **API client sprawl** — `src/lib/careerPathfinderApi.js` + `src/api/*` + direct fetch calls in components. No single API layer.
- **Database boundaries unclear** — Some user data goes to Supabase, some app data to Render Postgres. The split works but isn't documented in code.
- **No testing** — Zero test files. No CI/CD pipeline.
- **No TypeScript** — All JSX, no type safety.

---

## 2. Stack Recommendations

### Frontend: Vite + React (replaces CRA + CRACO)

**Why:** CRA is officially deprecated. Vite is the React team's recommended replacement. Benefits:
- 10-50x faster dev server startup (native ESM)
- Faster HMR (hot module replacement)
- Native `@/` path alias support (no CRACO needed)
- Native `.env` support (`VITE_` prefix instead of `REACT_APP_`)
- Built-in CSS modules, PostCSS, Tailwind support
- Active maintenance and ecosystem

**Migration cost:** Low. It's a build tool swap, not a framework change. Components, hooks, and routing stay identical. The main changes are:
- `process.env.REACT_APP_*` → `import.meta.env.VITE_*`
- `craco.config.js` → `vite.config.js`
- `jsconfig.json` → `vite.config.js` alias section
- Entry point: `index.html` moves to project root (Vite convention)

**Optional future upgrade:** Next.js or Remix if SSR/SEO becomes important. For now, Vite + React SPA keeps deployment simple (Vercel static) and avoids unnecessary complexity.

### Keep: Tailwind CSS v4

Already installed. Consolidate all custom CSS into Tailwind utilities + a single `components.css` for complex component styles. Remove `globals.css` and `index.css` — fold their rules into Tailwind's `@layer` system.

### Keep: FastAPI backend

The backend is well-structured. No reason to change.

### Keep: Supabase (auth + user data)

Works well. Keep the Supabase/Render split.

### Keep: Render (backend hosting + Postgres)

No change needed.

### Add: TypeScript (gradual adoption)

Don't rewrite everything at once. Set up `tsconfig.json` and start new files as `.tsx`. Rename existing files gradually. Vite supports mixed `.jsx` and `.tsx` natively.

### Add: Vitest (testing)

Comes with Vite. Add tests as you build each phase.

### Env Variable Rename

All environment variables change prefix:

| Old (CRA) | New (Vite) |
|-----------|------------|
| `REACT_APP_API_BASE` | `VITE_API_BASE` |
| `REACT_APP_SUPABASE_URL` | `VITE_SUPABASE_URL` |
| `REACT_APP_SUPABASE_ANON_KEY` | `VITE_SUPABASE_ANON_KEY` |
| `REACT_APP_MAPBOX_TOKEN` | `VITE_MAPBOX_TOKEN` |

---

## 3. New Project Structure

Rename the repo to `the-fob` (or `fob`). Clean flat structure, two deployable apps, shared docs.

```
the-fob/
├── web/                              ← Frontend (Vite + React), deploys to Vercel
│   ├── index.html                    ← Vite entry point (in root, not public/)
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── tsconfig.json
│   ├── package.json
│   ├── vercel.json
│   ├── .env.example
│   ├── public/
│   │   ├── favicon.ico
│   │   ├── manifest.json
│   │   └── assets/                   ← Static images, lottie files
│   └── src/
│       ├── main.jsx                  ← App entry (replaces index.js)
│       ├── App.jsx                   ← Router
│       ├── routes.jsx                ← Route definitions (extracted from App)
│       │
│       ├── styles/
│       │   ├── tokens.css            ← Design tokens (custom properties)
│       │   └── components.css        ← Complex component styles only
│       │
│       ├── lib/
│       │   ├── supabase.js           ← Supabase client (with lock pattern)
│       │   ├── api.js                ← Single API client for Render backend
│       │   └── database.js           ← Supabase data functions
│       │
│       ├── hooks/
│       │   ├── useAuth.js            ← Auth hook (wraps context)
│       │   ├── useApi.js             ← Generic fetch hook with loading/error
│       │   └── useSankey.js          ← Sankey layout + interaction hook
│       │
│       ├── contexts/
│       │   └── AuthContext.jsx
│       │
│       ├── components/
│       │   ├── layout/
│       │   │   ├── AppNav.jsx
│       │   │   ├── PageHero.jsx      ← Reusable hero section
│       │   │   ├── ContentWrap.jsx   ← Max-width container
│       │   │   ├── CrisisBar.jsx
│       │   │   └── Footer.jsx
│       │   │
│       │   ├── ui/
│       │   │   ├── SearchableSelect.jsx
│       │   │   ├── Card.jsx
│       │   │   ├── Button.jsx
│       │   │   ├── Badge.jsx
│       │   │   ├── LoadingSpinner.jsx
│       │   │   └── Toast.jsx         ← Wraps react-hot-toast config
│       │   │
│       │   ├── auth/
│       │   │   ├── AuthModal.jsx
│       │   │   ├── ProtectedAction.jsx
│       │   │   └── SignInForm.jsx
│       │   │
│       │   ├── career/
│       │   │   ├── SankeyDiagram.jsx
│       │   │   ├── SankeyDetailPanel.jsx
│       │   │   ├── PathSummaryCards.jsx
│       │   │   └── ProgressionCards.jsx
│       │   │
│       │   ├── dashboard/
│       │   │   ├── DashboardGrid.jsx
│       │   │   ├── SavedRoadmaps.jsx
│       │   │   ├── SavedPrograms.jsx
│       │   │   ├── BenefitsProgress.jsx
│       │   │   ├── QuickLinks.jsx
│       │   │   └── Reminders.jsx
│       │   │
│       │   └── shared/
│       │       ├── AddToDashboardButton.jsx
│       │       ├── VANewsBar.jsx
│       │       └── SectionLabel.jsx
│       │
│       └── pages/
│           ├── HomePage.jsx
│           ├── DashboardPage.jsx
│           ├── CareerPathfinderPage.jsx    ← Input form
│           ├── CareerMapPage.jsx           ← Sankey + cards output
│           ├── SkillBridgeExplorerPage.jsx
│           ├── BenefitsPage.jsx
│           ├── CommunitiesPage.jsx
│           ├── ERGDirectoryPage.jsx
│           ├── VANewsPage.jsx
│           ├── EmploymentNetworkingPage.jsx
│           └── NotFoundPage.jsx
│
├── api/                              ← Backend (FastAPI), deploys to Render
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── routes/
│   │   │   ├── career.py             ← /roles, /certifications, /targets
│   │   │   ├── roadmap.py            ← /roadmap/generate
│   │   │   ├── programs.py           ← SkillBridge programs
│   │   │   ├── communities.py
│   │   │   ├── ergs.py
│   │   │   ├── news.py
│   │   │   ├── networking.py
│   │   │   └── auth.py
│   │   ├── services/
│   │   │   ├── roadmap_generator.py
│   │   │   ├── ai_roadmap_generator.py
│   │   │   ├── sankey_builder.py
│   │   │   ├── skillbridge_enrichment.py
│   │   │   └── pipeline.py
│   │   ├── data/
│   │   │   ├── progression_paths.py
│   │   │   ├── mos_titles.py
│   │   │   ├── mos_career_mapping_loader.py
│   │   │   └── labor_occupations.json
│   │   ├── scrapers/
│   │   │   └── labor_occupations_scraper.py
│   │   └── models/
│   │       ├── roadmap.py
│   │       ├── database.py
│   │       ├── schemas.py
│   │       └── erg.py
│   ├── migrations/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── render.yaml
│   └── .env.example
│
├── supabase/
│   └── migrations/                   ← All Supabase SQL migrations (single location)
│
├── docs/
│   ├── FOB-SITE-REFERENCE.md         ← Design + UX + routes
│   ├── ARCHITECTURE.md               ← Deployment split
│   ├── API-CONTRACTS.md              ← All endpoint specs
│   └── REBUILD-GUIDE.md              ← This document
│
├── reference/
│   └── fob-sankey-career-map-demo.jsx ← Working Sankey prototype
│
├── README.md
├── .gitignore
└── CLAUDE.md                         ← Project context for AI assistants
```

### Key changes from current structure

1. **`skillbridge-explorer/` → `web/`** — name matches the product, not the original feature
2. **`skillbridge-api/` → `api/`** — same
3. **Root clutter deleted** — all prototype folders, prompt files, zips, duplicates gone
4. **Single `supabase/migrations/`** at repo root — not split between frontend and backend
5. **Pages in `pages/`** — no more `CareerRoadmap.jsx` at `src/` root
6. **Single API client** — `src/lib/api.js` replaces `careerPathfinderApi.js` + `src/api/*` + scattered fetch calls
7. **Extracted hooks** — `useAuth`, `useApi`, `useSankey` keep components lean
8. **UI component library** — `Button`, `Card`, `Badge`, `SearchableSelect` are reusable primitives used everywhere

---

## 4. Information Architecture & UX Redesign

### Navigation Structure

```
┌─────────────────────────────────────────────────┐
│  THE FOB                     [Nav Links] [Auth] │
│  CrisisBar (always visible)                      │
├─────────────────────────────────────────────────┤
│  Home                                            │
│  ├── Career Pathfinder  (/careers/pathfinder)   │
│  │   └── Career Map     (/careers/pathfinder/map)│
│  ├── SkillBridge Explorer  (/skillbridge)       │
│  ├── Employment Hub                              │
│  │   ├── ERG Directory  (/employment/ergs)      │
│  │   └── Networking     (/employment/networking)│
│  ├── Education & Benefits                        │
│  │   └── Benefits Navigator (/benefits)         │
│  ├── Communities  (/communities)                │
│  ├── VA News  (/news)                           │
│  └── Dashboard  (/dashboard)                    │
└─────────────────────────────────────────────────┘
```

### User Flow Redesign

**Primary Flow: Career Pathfinder (the hero feature)**

```
Home → Career Pathfinder Input Form → Career Map (Sankey + Cards)
                                        ├── Save to Dashboard
                                        ├── Explore SkillBridge programs
                                        ├── View relevant communities
                                        └── Check education benefits
```

The Career Pathfinder is the gateway. From the generated career map, the user can drill into any of the other features. This creates a hub-and-spoke model where the career map is the hub.

**Secondary Flows: Direct access to any feature**

Every feature is also accessible directly from the nav. Users don't have to go through the pathfinder first.

### Page Specifications

#### Home Page (`/`)
- Hero with CTA to Career Pathfinder
- Feature grid showing all six pillars (Pathfinder, SkillBridge, Employment, Benefits, Communities, News)
- Each pillar card links to its page
- Recent VA News headlines
- If authenticated: quick-access dashboard summary (saved items count, upcoming events)

#### Career Pathfinder Input (`/careers/pathfinder`)
- Six input fields: Current Role/MOS, Highest Education, Years in Role, Target Role, Target Industry, Separation Timeline
- All use SearchableSelect component
- "Generate Career Map →" button
- On success: navigate to `/careers/pathfinder/map` with data via router state

#### Career Map (`/careers/pathfinder/map`)
- Toggle between Sankey diagram view and Role Cards view
- Sankey: filled-band rendering with upstream path tracing on hover (see reference JSX)
- Cards: grouped by level (Entry → Mid → Target), each showing salary, requirements, prerequisites, progression
- Actions: Save to Dashboard, Edit Inputs, Share
- Summary cards: Fastest Path, Highest Ceiling, Recommended

#### SkillBridge Explorer (`/skillbridge`)
- Interactive map + list of 3,053 programs
- Filters: branch, industry, location, remote
- Program detail cards
- Save to Dashboard button per program

#### Benefits Navigator (`/benefits`)
- VA education benefits (GI Bill, VET TEC, Voc Rehab)
- VA loans overview
- School finder (future: GI Bill Comparison Tool API)
- Benefits progress tracker (Supabase-persisted)

#### Communities (`/communities`)
- 45+ organizations with search
- Category filters
- Organization detail cards
- Save to Dashboard

#### ERG Directory (`/employment/ergs`)
- 225+ companies with ERG data
- Search and filter by company, industry, ERG type
- Save to Dashboard

#### VA News (`/news`)
- RSS feed from 7 sources
- Category filters (6 categories)
- Article cards with source, date, summary
- Save articles to Dashboard

#### Employment Networking (`/employment/networking`)
- LinkedIn CSV upload
- Network analysis against target role/company
- Phased outreach strategy generation

#### Dashboard (`/dashboard`)
- Authenticated state: saved roadmaps, saved programs, benefits progress, events, reminders, quick links
- Unauthenticated state: feature preview + sign-in form
- Drag-to-reorder customization (future phase)

---

## 5. Design System Formalization

### Tokens (already defined, carry forward)

All colors, fonts, radii, and spacing use CSS custom properties from `tokens.css`. No ad-hoc hex values in components.

- Backgrounds: `--color-bg-primary` through `--color-bg-elevated` (5 levels)
- Text: `--color-text-primary` through `--color-text-dim` (4 levels)
- Accent: `--color-accent` (sage green #3ECF8E)
- Copper: `--color-copper` (#C8956A)
- Semantic: info (#60A5FA), warning (#F5A623), danger (#EF4444), purple (#A855F7)
- Fonts: DM Serif Display (headings), DM Sans (body), JetBrains Mono (data/code)
- Radii: card (12px), button (9px), badge (20px)

### CSS Strategy

1. **`tokens.css`** — CSS custom properties only. No selectors.
2. **Tailwind utility classes** — For all layout, spacing, typography, basic colors.
3. **`components.css`** — Complex component styles that can't be expressed in Tailwind utilities (animations, pseudo-elements, multi-state interactions). Use `@layer components`.
4. **No other CSS files.** Delete `globals.css` and `index.css`. Their rules move into Tailwind's base layer or `components.css`.

### Component Standards

- Every component uses design tokens via CSS custom properties or Tailwind classes
- No inline `style={{}}` objects (current prototype uses these for rapid iteration — the production build should use Tailwind classes)
- Consistent prop patterns: `variant` for visual variants, `size` for dimensions, `className` for overrides
- All interactive elements have hover/focus/active states
- All transitions: 200-300ms ease

---

## 6. Database Schema (Consolidated)

### Supabase Tables (auth + user data)

```sql
-- profiles (extends Supabase auth.users)
profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id),
  display_name text,
  avatar_url text,
  branch text,              -- military branch
  mos_code text,            -- current/last MOS
  ets_date date,            -- separation date
  dashboard_layout jsonb,   -- user's dashboard customization
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
)

-- saved_roadmaps
saved_roadmaps (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  title text NOT NULL,
  inputs jsonb NOT NULL,        -- the form inputs that generated this roadmap
  roadmap_data jsonb NOT NULL,  -- full sankey response
  created_at timestamptz DEFAULT now()
)

-- saved_programs (SkillBridge favorites)
saved_programs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  program_id text NOT NULL,     -- references Render Postgres program
  program_data jsonb,           -- snapshot of program details
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, program_id)
)

-- saved_ergs
saved_ergs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  erg_id text NOT NULL,
  erg_data jsonb,
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, erg_id)
)

-- saved_communities
saved_communities (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  community_id text NOT NULL,
  community_data jsonb,
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, community_id)
)

-- saved_articles (VA News)
saved_articles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  article_url text NOT NULL,
  article_data jsonb,
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, article_url)
)

-- benefits_progress
benefits_progress (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  benefit_type text NOT NULL,
  status text DEFAULT 'not_started',
  progress_data jsonb,
  updated_at timestamptz DEFAULT now(),
  UNIQUE(user_id, benefit_type)
)

-- user_events
user_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  title text NOT NULL,
  event_date date,
  description text,
  created_at timestamptz DEFAULT now()
)

-- recurring_reminders
recurring_reminders (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  title text NOT NULL,
  frequency text,
  next_date date,
  created_at timestamptz DEFAULT now()
)

-- dashboard_quick_links
dashboard_quick_links (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  label text NOT NULL,
  url text NOT NULL,
  created_at timestamptz DEFAULT now()
)

-- networking_roadmaps
networking_roadmaps (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES profiles(id) ON DELETE CASCADE,
  title text NOT NULL,
  roadmap_data jsonb NOT NULL,
  created_at timestamptz DEFAULT now()
)
```

All tables have RLS enabled. Policies: users can only read/write their own rows.

### Render Postgres Tables (app/scraped data)

These stay on Render Postgres — no changes needed:
- `programs` (SkillBridge 3,053 programs)
- `erg_companies` (225+ companies)
- `communities` (45+ orgs)
- `news_articles` (RSS scraped)
- `career_progression_paths` (curated paths)
- `roadmap_analytics` (anonymous usage data)

---

## 7. API Contract (Consolidated)

### Career Pathfinder

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/career/roles` | Searchable role options (military + civilian) |
| GET | `/api/v1/career/certifications` | Cert options grouped by domain |
| GET | `/api/v1/career/targets` | Target role options grouped by industry |
| POST | `/api/v1/roadmap/generate` | Generate career roadmap (Sankey response) |

### SkillBridge Programs

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/programs` | Search/filter programs |
| GET | `/api/v1/programs/:id` | Single program detail |
| GET | `/api/v1/programs/map` | Map-optimized endpoint |
| GET | `/api/v1/programs/stats` | Aggregate statistics |

### Communities

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/communities` | List/search communities |

### ERG Directory

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/ergs` | List/search ERG companies |

### VA News

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/news` | Recent articles with category filter |

### Employment Networking

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/networking/analyze` | Analyze LinkedIn CSV |
| POST | `/api/v1/networking/roadmap` | Generate outreach roadmap |

---

## 8. Implementation Phases

Each phase is a self-contained unit. Complete one before starting the next. Each includes Cursor-ready instructions.

### Phase 0: Project Scaffolding

**Goal:** New repo with Vite + React, Tailwind, design tokens, basic routing.

**Cursor prompt:**

> Create a new Vite + React project in the `web/` folder. Configure:
> - Vite with React plugin, path alias `@/` → `src/`
> - Tailwind CSS v4 with PostCSS
> - Copy `tokens.css` from the old project (design tokens only)
> - Create a minimal `components.css` with `@layer components`
> - Set up React Router v6 with the route structure from REBUILD-GUIDE.md section 4
> - Create placeholder pages (just the component shell + page title) for all routes
> - Set up `.env.example` with VITE_ prefixed variables
> - Configure `vercel.json` with SPA rewrites
> - Install: react-router-dom, react-hot-toast, @radix-ui/react-dialog, lucide-react

**Verify:** `npm run dev` starts, all routes render placeholder pages.

### Phase 1: Design System + Layout Components

**Goal:** Reusable layout shell (nav, hero, footer, crisis bar) + UI primitives.

**Cursor prompt:**

> Build the layout and UI component library. Reference `tokens.css` for all colors/fonts.
> 
> Layout components (`src/components/layout/`):
> - `AppNav.jsx` — top navigation bar with logo, nav links, auth button. Dark bg, sage green accent. Mobile hamburger menu.
> - `PageHero.jsx` — reusable hero section with props: eyebrow, title, subtitle. Uses DM Serif Display for title.
> - `ContentWrap.jsx` — max-width container (1200px default, configurable via prop).
> - `CrisisBar.jsx` — persistent crisis resources banner (Veterans Crisis Line).
> - `Footer.jsx` — simple footer with links and copyright.
>
> UI primitives (`src/components/ui/`):
> - `Button.jsx` — variants: accent, ghost, amber, danger. Sizes: sm, md, lg.
> - `Card.jsx` — bg-secondary, border, radius-card. Props: clickable, hoverable.
> - `Badge.jsx` — colored badges for node types. Props: type (certification, education, etc.), label.
> - `SearchableSelect.jsx` — full implementation from the Sankey prompt (searchable, multi-select, grouped, custom entries).
> - `LoadingSpinner.jsx` — simple spinner using accent color.
> - `SectionLabel.jsx` — uppercase label with left accent bar.
>
> Use Tailwind classes for layout/spacing. Use CSS custom properties for colors. No inline style objects.

### Phase 2: Auth + Supabase Integration

**Goal:** Auth flow working — sign in, sign up, magic link, Google OAuth, protected routes.

**Cursor prompt:**

> Implement Supabase auth. Port from old project but clean up.
>
> - `src/lib/supabase.js` — Supabase client with the lock pattern (navigatorLock workaround for PKCE)
> - `src/contexts/AuthContext.jsx` — provides user, session, loading state, sign in/out methods
> - `src/hooks/useAuth.js` — convenience hook wrapping the context
> - `src/components/auth/AuthModal.jsx` — Radix Dialog with sign-in/sign-up tabs, password strength indicator, magic link, Google OAuth. Uses the FOB dark theme.
> - `src/components/auth/ProtectedAction.jsx` — wraps any action that requires auth. Shows contextual message + AuthModal if not signed in.
>
> Environment variables: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

### Phase 3: API Client + Data Layer

**Goal:** Single API client for all backend calls + Supabase data functions.

**Cursor prompt:**

> Create a unified API layer.
>
> `src/lib/api.js` — single module that exports all backend API functions:
> - Base URL from `import.meta.env.VITE_API_BASE`
> - Generic `fetchApi(path, options)` with error handling, JSON parsing, timeout
> - Named exports: `getRoles()`, `getCertifications()`, `getTargets()`, `generateRoadmap(inputs)`, `getPrograms(filters)`, `getProgram(id)`, `getCommunities(filters)`, `getERGs(filters)`, `getNews(filters)`, `analyzeNetwork(csv)`, `generateNetworkingRoadmap(analysis)`
>
> `src/lib/database.js` — Supabase data functions:
> - All CRUD for: saved_roadmaps, saved_programs, saved_ergs, saved_communities, saved_articles, benefits_progress, user_events, recurring_reminders, dashboard_quick_links, networking_roadmaps
> - Each function takes user_id as first argument
> - Consistent error handling
>
> `src/hooks/useApi.js` — generic hook: `const { data, loading, error, refetch } = useApi(apiFunction, ...args)`

### Phase 4: Career Pathfinder (Core Feature)

**Goal:** Complete input form → Sankey diagram → card progression flow.

**Cursor prompt:**

> Build the Career Pathfinder — the hero feature.
>
> Reference the working Sankey prototype at `reference/fob-sankey-career-map-demo.jsx`. Match its rendering approach exactly for the diagram.
>
> `src/pages/CareerPathfinderPage.jsx` — input form with six SearchableSelect fields:
> - Current Role/MOS (grouped by branch, searchable)
> - Highest Education (static options)
> - Years in Role (static options)
> - Target Role (grouped by industry, searchable)
> - Target Industry (static options)
> - Separation Timeline (static options)
> - "Generate Career Map →" button, validates required fields, posts to API, navigates to map page
>
> `src/pages/CareerMapPage.jsx` — results page with toggle between views:
> - Sankey diagram view (Career Map tab)
> - Role cards view (Role Cards tab)
> - Hero: title from inputs, path count, salary range
> - Summary cards: Fastest, Highest Ceiling, Recommended
> - Actions: Edit Inputs (back to form), Save to Dashboard (ProtectedAction), Share
>
> `src/components/career/SankeyDiagram.jsx`:
> - Custom layout engine (no d3-sankey dependency)
> - FILLED AREA BANDS for links (closed path with fill, NOT stroked lines)
> - Thin vertical node bars (10px) with labels outside
> - Per-link linear gradients (source color → target color)
> - Upstream path tracing on hover (recursive walkUp algorithm)
> - Click-to-lock selections
> - Responsive: min 800px width with horizontal scroll on mobile
>
> `src/components/career/SankeyDetailPanel.jsx` — detail panel below diagram
> `src/components/career/PathSummaryCards.jsx` — three summary cards
> `src/components/career/ProgressionCards.jsx` — card view grouped by role level

### Phase 5: SkillBridge Explorer

**Goal:** Interactive map and program search.

**Cursor prompt:**

> Rebuild the SkillBridge Explorer page.
>
> `src/pages/SkillBridgeExplorerPage.jsx`:
> - Map view (Mapbox GL) showing program locations with clustering
> - List view with search, filters (branch, industry, location, remote)
> - Program cards with detail expansion
> - Save to Dashboard button (ProtectedAction)
> - Responsive: map above list on mobile, side-by-side on desktop

### Phase 6: Supporting Features

**Goal:** Benefits, Communities, ERGs, News, Networking.

**Cursor prompt:**

> Build the remaining feature pages. Each follows the same pattern: PageHero + ContentWrap + filter bar + card grid + Save to Dashboard.
>
> - `BenefitsPage.jsx` — GI Bill, VET TEC, Voc Rehab, VA Loans sections. Benefits progress tracker (Supabase).
> - `CommunitiesPage.jsx` — 45+ orgs, search + category filter, org cards.
> - `ERGDirectoryPage.jsx` — 225+ companies, search + industry filter, company cards.
> - `VANewsPage.jsx` — RSS feed, 6 category tabs, article cards with source/date.
> - `EmploymentNetworkingPage.jsx` — CSV upload, analysis results, outreach roadmap.
>
> All pages use the shared UI components (Card, Badge, SearchableSelect, SectionLabel).

### Phase 7: Dashboard

**Goal:** User dashboard with saved items across all features.

**Cursor prompt:**

> Build the Dashboard page.
>
> `src/pages/DashboardPage.jsx`:
> - **Unauthenticated state:** Feature preview (what you'll get) + sign-in form (AuthModal inline)
> - **Authenticated state:** Welcome header (avatar, name, branch/MOS, ETS countdown) + dashboard grid
>
> Dashboard grid sections:
> - Saved Roadmaps (from Career Pathfinder)
> - Saved SkillBridge Programs
> - Saved ERGs
> - Saved Communities
> - Saved Articles (VA News)
> - Benefits Progress
> - Events & Reminders
> - Quick Links
>
> Each section: loading state, empty state, populated state. Per-section error handling. Parallel data fetching (Promise.all).
>
> Future phase: drag-to-reorder customization using @dnd-kit, persisted to profiles.dashboard_layout.

### Phase 8: Home Page + Polish

**Goal:** Home page, final wiring, responsive testing.

**Cursor prompt:**

> Build the Home page and do final polish.
>
> `src/pages/HomePage.jsx`:
> - Hero section with CTA to Career Pathfinder
> - Six feature pillar cards in a responsive grid
> - VA News headline ticker
> - If authenticated: mini dashboard summary
> - Testimonials or platform stats (number of programs, MOS codes, etc.)
>
> Final checks:
> - All routes working
> - All pages responsive at 375px, 768px, 1024px, 1440px
> - Auth flows tested (sign up, sign in, magic link, Google OAuth, sign out)
> - Save actions tested across all features
> - Dashboard populated from saves
> - Toast notifications on all mutations
> - 404 page for unknown routes
> - CrisisBar visible on all pages
> - Page titles set for each route

---

## 9. Reference Files

Include these alongside this document when working in Cursor:

1. **This document** (`REBUILD-GUIDE.md`) — architecture, structure, phases
2. **`fob-sankey-career-map-demo.jsx`** — working Sankey prototype (rendering, layout, interaction)
3. **`FOB-SITE-REFERENCE.md`** — design tokens, CSS classes, current UX patterns (use as reference for visual language, not as the structural guide — this document supersedes it for structure)
4. **`FOB-MIGRATION-MAP.md`** — inventory of what exists in the current repo (use to know what to port vs rebuild)

---

## Quick Start

1. Create new repo: `the-fob`
2. Copy `api/` folder from `skillbridge-api/` (rename)
3. Upload this doc + reference files to Cursor
4. Execute Phase 0 (scaffolding)
5. Execute phases 1-8 in order
6. Each phase: paste the Cursor prompt, let it build, verify, commit
7. Deploy: `web/` → Vercel, `api/` → Render
8. Update env vars with `VITE_` prefix on Vercel
