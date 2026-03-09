# Phase 0 — Project Scaffolding (Vite + shadcn/ui)

## What you're building

A new Vite + React project for **The FOB** (Forward Operating Base), a veteran career transition platform. This phase creates the empty shell: build tooling, shadcn/ui component library, design tokens, routing, and placeholder pages.

**Read `docs/REBUILD-GUIDE.md` for full architecture context.**

---

## Step 1: Initialize Vite + React

```bash
npm create vite@latest web -- --template react
cd web
npm install
```

## Step 2: Install core dependencies

```bash
npm install react-router-dom react-hot-toast lucide-react
npm install -D tailwindcss @tailwindcss/postcss postcss autoprefixer
```

## Step 3: Initialize shadcn/ui

```bash
npx shadcn@latest init
```

When prompted:
- Style: **Default**
- Base color: **Neutral** (we'll override with FOB tokens)
- CSS variables: **Yes**
- Tailwind config: use the one we create
- Components directory: `src/components/ui`
- Utils: `src/lib/utils`

## Step 4: Install shadcn components

Install every component we'll use across the site:

```bash
npx shadcn@latest add button card badge tabs input separator dialog tooltip popover select accordion scroll-area avatar dropdown-menu sheet progress alert textarea label
```

## Step 5: Configure Vite

Create `web/vite.config.js`:

```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    open: true,
  },
});
```

## Step 6: FOB Design Token Overrides

shadcn uses CSS variables for theming. Override its defaults with the FOB dark theme in `src/index.css` (or wherever shadcn placed its CSS variables during init):

Find the `:root` and `.dark` blocks that shadcn generated and **replace them entirely** with:

```css
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  /* ── shadcn required variables (mapped to FOB tokens) ── */
  --background: 210 15% 7%;           /* #0F1214 */
  --foreground: 30 14% 93%;           /* #F0EDEA */
  
  --card: 210 12% 10%;                /* #171B1E */
  --card-foreground: 30 14% 93%;      /* #F0EDEA */
  
  --popover: 210 10% 12%;             /* #1E2326 */
  --popover-foreground: 30 14% 93%;
  
  --primary: 155 66% 53%;             /* #3ECF8E accent */
  --primary-foreground: 210 15% 7%;   /* dark bg for text on accent */
  
  --secondary: 210 10% 14%;           /* #252A2E */
  --secondary-foreground: 200 8% 80%; /* #C5CCD0 */
  
  --muted: 210 8% 16%;               /* #2A2F34 */
  --muted-foreground: 200 6% 57%;    /* #8A9399 */
  
  --accent: 210 10% 14%;
  --accent-foreground: 30 14% 93%;
  
  --destructive: 0 84% 60%;          /* #EF4444 */
  --destructive-foreground: 0 0% 100%;
  
  --border: 210 8% 16%;              /* #252A2E */
  --input: 210 10% 14%;              /* #1E2326 */
  --ring: 155 66% 53%;               /* #3ECF8E */
  
  --radius: 0.75rem;                  /* 12px */

  /* ── FOB Extended Tokens ── */
  --color-bg-primary: #0F1214;
  --color-bg-secondary: #171B1E;
  --color-bg-tertiary: #1E2326;
  --color-bg-hover: #252A2E;
  --color-bg-elevated: #2A2F34;

  --color-text-primary: #F0EDEA;
  --color-text-secondary: #C5CCD0;
  --color-text-muted: #8A9399;
  --color-text-dim: #566069;

  --color-accent: #3ECF8E;
  --color-accent-hover: #35B87D;
  --color-accent-dim: rgba(62, 207, 142, 0.15);
  --color-border-accent: rgba(62, 207, 142, 0.3);

  --color-copper: #C8956A;
  --color-copper-dim: rgba(200, 149, 106, 0.12);

  --color-info: #60A5FA;
  --color-info-dim: rgba(96, 165, 250, 0.15);
  --color-warning: #F5A623;
  --color-warning-dim: rgba(245, 166, 35, 0.15);
  --color-danger: #EF4444;
  --color-purple: #A855F7;
  --color-purple-dim: rgba(168, 85, 247, 0.15);
  --color-orange: #E08A52;

  --color-border: #252A2E;
  --color-border-light: #2F353A;

  --font-serif: 'DM Serif Display', Georgia, serif;
  --font-sans: 'DM Sans', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

/* Force dark mode globally — no .dark class needed */
body {
  background-color: var(--color-bg-primary);
  color: var(--color-text-secondary);
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
}

* {
  scrollbar-width: thin;
  scrollbar-color: var(--color-border) transparent;
}
```

## Step 7: Tailwind config

Update `tailwind.config.js` to extend with FOB fonts:

```javascript
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        serif: ['DM Serif Display', 'Georgia', 'serif'],
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        'fob-accent': '#3ECF8E',
        'fob-copper': '#C8956A',
        'fob-info': '#60A5FA',
        'fob-warn': '#F5A623',
        'fob-purple': '#A855F7',
        'fob-orange': '#E08A52',
      },
    },
  },
  plugins: [require('tailwindcss-animate')], // required by shadcn
};
```

## Step 8: App entry + Router

Create `web/src/main.jsx`:

```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-center"
        toastOptions={{
          duration: 4000,
          style: {
            background: 'var(--color-bg-elevated)',
            color: 'var(--color-text-primary)',
            border: '1px solid var(--color-border)',
            borderRadius: '12px',
            fontSize: '14px',
            fontFamily: 'var(--font-sans)',
          },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
);
```

Create `web/src/App.jsx`:

```jsx
import { Routes, Route } from 'react-router-dom';

import HomePage from '@/pages/HomePage';
import CareerPathfinderPage from '@/pages/CareerPathfinderPage';
import CareerMapPage from '@/pages/CareerMapPage';
import SkillBridgeExplorerPage from '@/pages/SkillBridgeExplorerPage';
import BenefitsPage from '@/pages/BenefitsPage';
import CommunitiesPage from '@/pages/CommunitiesPage';
import ERGDirectoryPage from '@/pages/ERGDirectoryPage';
import VANewsPage from '@/pages/VANewsPage';
import EmploymentNetworkingPage from '@/pages/EmploymentNetworkingPage';
import DashboardPage from '@/pages/DashboardPage';
import NotFoundPage from '@/pages/NotFoundPage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/careers/pathfinder" element={<CareerPathfinderPage />} />
      <Route path="/careers/pathfinder/map" element={<CareerMapPage />} />
      <Route path="/skillbridge" element={<SkillBridgeExplorerPage />} />
      <Route path="/benefits" element={<BenefitsPage />} />
      <Route path="/communities" element={<CommunitiesPage />} />
      <Route path="/employment/ergs" element={<ERGDirectoryPage />} />
      <Route path="/employment/networking" element={<EmploymentNetworkingPage />} />
      <Route path="/news" element={<VANewsPage />} />
      <Route path="/dashboard" element={<DashboardPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
```

## Step 9: Placeholder pages

Create `web/src/pages/` with a placeholder for each route. Every placeholder should use shadcn's Card:

```jsx
// src/pages/HomePage.jsx
import { Card, CardContent } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      <Card className="max-w-md w-full" style={{ background: 'var(--color-bg-secondary)', borderColor: 'var(--color-border)' }}>
        <CardContent className="pt-8 text-center">
          <h1 className="text-3xl font-serif mb-2" style={{ color: 'var(--color-text-primary)' }}>Home</h1>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Phase 0 — placeholder</p>
        </CardContent>
      </Card>
    </div>
  );
}
```

Create for: `HomePage`, `CareerPathfinderPage`, `CareerMapPage`, `SkillBridgeExplorerPage`, `BenefitsPage`, `CommunitiesPage`, `ERGDirectoryPage`, `VANewsPage`, `EmploymentNetworkingPage`, `DashboardPage`, `NotFoundPage`.

`NotFoundPage` should show "404 — Page not found" with a shadcn `<Button>` linking back to Home.

## Step 10: Environment + Vercel

Create `web/.env.example`:
```
VITE_API_BASE=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_MAPBOX_TOKEN=your-mapbox-token
```

Create `web/vercel.json`:
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }],
  "headers": [{
    "source": "/(.*)",
    "headers": [
      { "key": "X-Content-Type-Options", "value": "nosniff" },
      { "key": "X-Frame-Options", "value": "DENY" }
    ]
  }]
}
```

Update `index.html` — add Google Fonts preconnect:
```html
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>The FOB — Forward Operating Base</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
</head>
```

## Verify

- `npm run dev` starts on port 3000
- Home page renders with Card component on dark (#0F1214) background
- shadcn components render with FOB dark theme (not default light)
- Navigate to `/careers/pathfinder`, `/dashboard`, etc. — all show placeholders
- Navigate to `/nonexistent` — shows 404
- No console errors
- DM Serif Display font loads for headings

**Phase 0 complete.** Commit: `feat: phase 0 — vite + shadcn/ui scaffolding with FOB theme`
