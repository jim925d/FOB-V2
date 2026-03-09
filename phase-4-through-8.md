# Phase 4 — Career Pathfinder + Sankey (shadcn/ui)

## What you're building

The hero feature: input form → Sankey diagram → role cards. Uses shadcn Card, Button, Badge, Tabs, Separator throughout.

**Prerequisites:** Phases 0-3 complete. Reference: `reference/fob-sankey-career-map-demo.jsx` and `reference/fob-career-pathfinder-prototype.jsx`

**CRITICAL: Read both reference JSX files. Match the Sankey rendering approach (filled area bands, not stroked lines) and the career track data structure.**

---

## Page 1: Career Pathfinder Input — `src/pages/CareerPathfinderPage.jsx`

Uses `PageHero` + max-w-[680px] container. Six fields in two shadcn Card sections.

**Components used:** `Card, CardContent`, `Button`, `SectionLabel`, `SearchableSelect` (custom, built on shadcn Popover+Command), `PageHero`

**Section 1: "Where You Are"** (SectionLabel with accent bar)
```jsx
<Card className="mb-7">
  <CardContent className="pt-6 space-y-4">
    <SearchableSelect label="Current Role / MOS" options={roles} grouped required />
    <SearchableSelect label="Highest Education" options={eduOptions} required />
    <SearchableSelect label="Years in Current Role" options={yearsOptions} required />
  </CardContent>
</Card>
```

**Section 2: "Where You Want To Go"** (SectionLabel with copper bar)
```jsx
<Card className="mb-7">
  <CardContent className="pt-6 space-y-4">
    <SearchableSelect label="Target Role" options={targets} grouped required />
    <SearchableSelect label="Target Industry" options={industries} />
    <SearchableSelect label="Separation Timeline" options={timelineOptions} required />
  </CardContent>
</Card>
```

**Submit:** `<Button variant="info" size="lg" className="w-full max-w-[400px] mx-auto">Generate Career Map →</Button>`

**Data:** Roles from `useApi(getRoles)`, targets from `useApi(getTargets)`. Static options for education, years, industry, timeline.

**On submit:** `useLazyApi(generateRoadmap)` → navigate to `/careers/pathfinder/map` with roadmap data in router state.

---

## Page 2: Career Map — `src/pages/CareerMapPage.jsx`

**Components:** `PageHero` (compact), `Card`, `Button`, `Badge`, `Tabs, TabsList, TabsTrigger, TabsContent`, `Separator`

**Layout:**
```jsx
<PageHero compact eyebrow="Your Career Map" title={roadmap.title} subtitle={`${count} paths · ${salaryRange}`}>
  <div className="flex gap-3 flex-wrap">
    <Button variant="outline" size="sm" onClick={goBack}>← Edit Inputs</Button>
    <ProtectedAction message="Sign in to save" onAuthenticated={save}>
      {({ onClick }) => <Button variant="info" size="sm" onClick={onClick}>Save to Dashboard</Button>}
    </ProtectedAction>
  </div>
</PageHero>

{/* Summary cards */}
<div className="grid md:grid-cols-3 gap-4 mb-6">
  {[fastest, highest, recommended].map(s => (
    <Card className="cursor-pointer hover:border-[--color-border-accent] transition-colors">
      <CardContent className="pt-4">
        <span className="text-[10px] uppercase tracking-wider text-[--color-text-dim]">{s.icon} {s.label}</span>
        <p className="text-sm font-bold text-[--color-text-primary] mt-1">{s.title}</p>
        <p className="text-xs text-[--color-text-muted] mt-0.5">{s.detail}</p>
      </CardContent>
    </Card>
  ))}
</div>

{/* View toggle */}
<Tabs defaultValue="sankey">
  <TabsList className="mb-4" style={{ background: 'var(--color-bg-tertiary)' }}>
    <TabsTrigger value="sankey" className="data-[state=active]:bg-fob-info data-[state=active]:text-white">Career Map</TabsTrigger>
    <TabsTrigger value="cards" className="data-[state=active]:bg-fob-info data-[state=active]:text-white">Role Cards</TabsTrigger>
  </TabsList>
  <TabsContent value="sankey"><SankeyDiagram ... /><SankeyDetailPanel ... /></TabsContent>
  <TabsContent value="cards"><ProgressionCards ... /></TabsContent>
</Tabs>
```

---

## SankeyDiagram.jsx — `src/components/career/SankeyDiagram.jsx`

**MATCH THE REFERENCE JSX EXACTLY.** This component is pure SVG — shadcn doesn't apply here.

Key rules (unchanged):
1. Custom `buildLayout()` engine — no d3-sankey
2. **FILLED AREA BANDS** — closed `<path>` with `fill`, `stroke="none"`. Top edge + bottom edge + Z close
3. Thin 10px vertical node bars, labels outside
4. Per-link linear gradients in `<defs>`
5. **Upstream path tracing** on hover — recursive `walkUp` from hovered node back to origin + one step downstream
6. Click-to-lock
7. Opacity: default nodes 0.92 / links 0.18, highlighted 1.0 / 0.55, dimmed 0.08 / 0.03

---

## SankeyDetailPanel.jsx

Uses shadcn `Card`, `Badge`.

```jsx
<Card className="mt-4 min-h-[70px]">
  <CardContent className="pt-5">
    {!activeItem ? (
      <p className="text-center text-sm" style={{ color: 'var(--color-text-dim)' }}>Hover to explore · Click to lock</p>
    ) : (
      <>
        <div className="flex items-center gap-2 mb-2">
          <span className="font-serif text-lg" style={{ color: 'var(--color-text-primary)' }}>{detail.title}</span>
          <Badge variant={nodeType}>{typeLabel}</Badge>
        </div>
        {detail.desc && <p className="text-sm mb-3" style={{ color: 'var(--color-text-secondary)' }}>{detail.desc}</p>}
        <div className="flex flex-wrap gap-2">
          {detail.attrs.map(a => (
            <div className="rounded-lg px-3 py-1.5" style={{ background: 'var(--color-bg-tertiary)', border: '1px solid var(--color-border-light)' }}>
              <span className="text-[10px] uppercase" style={{ color: 'var(--color-text-dim)' }}>{a.label} </span>
              <span className="text-xs font-semibold" style={{ color: 'var(--color-text-primary)' }}>{a.value}</span>
            </div>
          ))}
        </div>
      </>
    )}
  </CardContent>
</Card>
```

---

## ProgressionCards.jsx — Role Cards View

Uses shadcn `Card`, `Badge`, `Separator`.

Each role card:
```jsx
<Card className="overflow-hidden hover:border-[color]/30 transition-colors">
  <div className="h-1" style={{ background: nodeColor }} />
  <CardContent className="pt-4 pb-3">
    <div className="flex justify-between items-start mb-2">
      <div>
        <h4 className="text-sm font-bold" style={{ color: 'var(--color-text-primary)' }}>{card.label}</h4>
        <Badge variant={card.type}>{typeLabel}</Badge>
      </div>
      <div className="text-right">
        <span className="text-xs" style={{ color: 'var(--color-text-dim)' }}>Salary</span>
        <p className="text-sm font-bold font-mono" style={{ color: nodeColor }}>{salary}</p>
      </div>
    </div>
    
    {/* Prerequisites — color-coded */}
    <div className="flex flex-wrap gap-1 mt-3">
      {prereqs.map(p => (
        <Badge variant={p.type} className="text-[10px]">
          {p.type === 'certification' ? '📜 ' : p.type === 'education' ? '🎓 ' : '🔗 '}{p.label}
        </Badge>
      ))}
      {directRolePrereqs.map(p => (
        <Badge variant={p.type} className="text-[10px]">← {p.label}</Badge>
      ))}
    </div>
    
    {/* Progresses to */}
    <div className="flex flex-wrap gap-1 mt-2">
      {nextRoles.map(r => (
        <Badge variant="target_role" className="text-[10px]">→ {r}</Badge>
      ))}
    </div>
  </CardContent>
</Card>
```

Prerequisites carry forward through the full upstream chain (recursive `collectAllPrereqs`).

---

## Verify

- Form renders with SearchableSelect dropdowns inside shadcn Cards
- Submit → navigates to map page
- Sankey renders filled bands (NOT stroked lines)
- Hover traces full upstream path
- Click-to-lock works
- Detail panel shows in shadcn Card with Badge
- Tab toggle between Sankey and Role Cards
- Role Cards show color-coded prereqs (📜 blue certs, 🎓 purple degrees, 🔗 copper skillbridge, ← orange roles)
- Prereqs carry forward (Security Engineer shows Security+ AND CySA+ from SOC Analyst)
- Save to Dashboard triggers ProtectedAction

**Phase 4 complete.** Commit: `feat: phase 4 — career pathfinder with sankey + shadcn role cards`

---
---

# Phase 5 — SkillBridge Explorer (shadcn/ui)

## What you're building

Interactive map + searchable program list. Uses shadcn Card, Button, Badge, Input, ScrollArea, Separator, Tooltip.

**Prerequisites:** Phases 0-4 complete.

---

## `src/pages/SkillBridgeExplorerPage.jsx`

```jsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Search, MapPin, Clock, Building2 } from "lucide-react";
```

**Layout:**
- `PageHero` with program count
- Search: shadcn `Input` with Search icon, full width, debounced 300ms
- Filter pills: `Button variant="outline" size="sm"` for each branch + "Remote Only" toggle. Active: `variant="info"`
- Split view: Map (left 60%) + `ScrollArea` list (right 40%) on desktop. Stacked on mobile.
- Program cards inside `Card`:

```jsx
<Card className="hover:border-fob-info/30 transition-colors cursor-pointer">
  <div className="h-0.5 bg-fob-info" />
  <CardHeader className="pb-2">
    <CardTitle className="text-sm font-bold">{program.company}</CardTitle>
    <p className="text-xs text-[--color-text-muted]">{program.title}</p>
  </CardHeader>
  <CardContent className="pb-3">
    <div className="flex flex-wrap gap-1.5 mb-2">
      <Badge variant="outline" className="text-[10px] gap-1"><MapPin size={10} />{location}</Badge>
      <Badge variant="outline" className="text-[10px] gap-1"><Clock size={10} />{duration}</Badge>
      {remote && <Badge variant="certification" className="text-[10px]">Remote</Badge>}
    </div>
    <ProtectedAction message="Sign in to save" onAuthenticated={saveProgram}>
      {({ onClick }) => <Button variant="outline" size="sm" onClick={onClick}>Save to Dashboard</Button>}
    </ProtectedAction>
  </CardContent>
</Card>
```

- Map: Mapbox GL if token available, otherwise show list-only mode with a message

**Phase 5 complete.** Commit: `feat: phase 5 — skillbridge explorer with shadcn cards`

---
---

# Phase 6 — Supporting Feature Pages (shadcn/ui)

## What you're building

Benefits, Communities, ERGs, News, Networking. All use shadcn components consistently.

---

## 6A: Benefits Navigator

Uses: `Card, CardContent, CardHeader`, `Badge`, `Progress`, `Accordion, AccordionItem, AccordionTrigger, AccordionContent`, `Button`, `Tabs, TabsList, TabsTrigger, TabsContent`

- Four benefit Cards in 2×2 grid (GI Bill copper, VET TEC purple, Voc Rehab info, VA Loans accent)
- `Progress` bars for each tracked benefit (value from Supabase)
- `Accordion` for detailed info per benefit (eligibility, steps, FAQ)
- ProtectedAction save on progress updates

## 6B: Communities

Uses: `Card`, `Badge`, `Input`, `Button`, `Avatar`

- Search Input + category filter Button pills
- Org Cards with Avatar (org initials), name, type Badge, member count, description
- ProtectedAction save per card

## 6C: ERG Directory

Uses: `Card`, `Badge`, `Input`, `Button`

- Search + industry filter pills
- Company Cards: name, ERG name(s), industry Badge
- ProtectedAction save

## 6D: VA News

Uses: `Card`, `Badge`, `Tabs, TabsList, TabsTrigger, TabsContent`, `Button`, `Separator`

- Category Tabs: All, Benefits, Policy, Health, Jobs, Education
- Article Cards: source Badge (colored), headline, timestamp, excerpt
- Click opens URL in new tab
- ProtectedAction save article

## 6E: Employment Networking

Uses: `Card`, `Button`, `Input`, `Tabs`, `Badge`, `Alert`

- Step 1: CSV upload (drag-drop zone + file Input)
- Step 2: Analysis results in Cards
- Step 3: Outreach roadmap
- ProtectedAction save roadmap

**Phase 6 complete.** Commit: `feat: phase 6 — benefits, communities, ergs, news, networking with shadcn`

---
---

# Phase 7 — Dashboard (shadcn/ui)

## What you're building

User dashboard using shadcn Card grid, Avatar, Badge, Progress, Button, Separator, ScrollArea, Alert.

---

## `src/pages/DashboardPage.jsx`

**Unauthenticated:**
```jsx
<div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
  <div className="space-y-4">
    {featurePreviewCards.map(f => (
      <Card><CardContent className="flex items-center gap-3 pt-4">
        <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: f.colorDim }}>
          <f.icon size={20} style={{ color: f.color }} />
        </div>
        <div>
          <p className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>{f.title}</p>
          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{f.desc}</p>
        </div>
      </CardContent></Card>
    ))}
  </div>
  <Card className="p-6">
    {/* Inline sign-in form — not in a Dialog, rendered directly */}
    <AuthForm />
  </Card>
</div>
```

**Authenticated:**
```jsx
{/* Header */}
<div className="flex items-center gap-4">
  <Avatar className="h-12 w-12"><AvatarFallback className="bg-fob-accent/15 text-fob-accent text-lg font-bold">{initial}</AvatarFallback></Avatar>
  <div>
    <h1 className="font-serif text-2xl" style={{ color: 'var(--color-text-primary)' }}>Welcome back, {name}</h1>
    <div className="flex gap-2 mt-1">
      <Badge variant="outline">{branch} · {mos}</Badge>
      <Badge variant="outline" className="text-fob-warn border-fob-warn/30 bg-fob-warn/10">ETS: {days} days</Badge>
    </div>
  </div>
</div>

{/* Two-column grid */}
<div className="grid lg:grid-cols-[1fr_340px] gap-6 mt-8">
  <div className="space-y-8">
    <SectionLabel>Saved Roadmaps</SectionLabel>
    {roadmaps.map(r => <Card>...</Card>)}
    <SectionLabel color="var(--color-info)">Saved Programs</SectionLabel>
    {programs.map(p => <Card>...</Card>)}
    ...
  </div>
  <div className="space-y-8">
    <SectionLabel color="var(--color-copper)">Benefits Progress</SectionLabel>
    {benefits.map(b => <Card><Progress value={b.pct} /></Card>)}
    <SectionLabel color="var(--color-warning)">Upcoming</SectionLabel>
    {events.map(e => <Card>...</Card>)}
    ...
  </div>
</div>
```

Each section: loading skeleton, empty state with link, populated state with delete buttons (optimistic removal + undo toast).

Parallel `Promise.allSettled` for all data fetching.

**Phase 7 complete.** Commit: `feat: phase 7 — dashboard with shadcn cards + progress bars`

---
---

# Phase 8 — Home Page + Polish (shadcn/ui)

## What you're building

Landing page and final polish. Reference: `reference/demo-home-shadcn.jsx` for visual direction.

---

## `src/pages/HomePage.jsx`

Uses: `Card, CardContent, CardHeader, CardTitle, CardDescription`, `Button`, `Badge`, `Separator`, `Tabs, TabsList, TabsTrigger, TabsContent`

**Sections:**
1. Hero: font-serif headline, subtitle, `Button variant="info" size="lg"` CTA, `Button variant="outline" size="lg"` secondary
2. Stats bar: 4 metrics in flex row, font-mono numbers, text-dim labels
3. Example career paths: 3 Cards showing MOS → Target with salary/timeline Badges
4. Feature grid: 6 Cards with lucide icons, colored top strips, stat Badges
5. News + Popular Paths: shadcn `Tabs` toggle between news articles and career paths
6. CTA banner: Card with icon, heading, CTA button
7. Footer

**Polish checklist (all pages):**
- [ ] All pages responsive at 375px, 768px, 1024px, 1440px
- [ ] Nav: mobile Sheet menu works
- [ ] All shadcn components use FOB dark theme (no light defaults visible)
- [ ] Active nav link highlighted
- [ ] CrisisBar on every page
- [ ] Footer on every page
- [ ] All ProtectedAction wraps work
- [ ] Toast on every mutation (save, delete, generate)
- [ ] Loading states on every data-dependent component
- [ ] Empty states on every list
- [ ] Error states with retry
- [ ] 404 page works
- [ ] Page titles via document.title per page
- [ ] No console errors
- [ ] Sankey: filled bands (not stroked lines)
- [ ] Sankey: upstream path tracing on hover
- [ ] Role cards: color-coded prereqs carry forward
- [ ] Career map title matches user's selected target role

**Phase 8 complete.** Commit: `feat: phase 8 — home page + production polish`

Deploy: `web/` → Vercel (Root Directory = `web`, add VITE_ env vars), `api/` → Render (unchanged)

---
---

# Backend Fix — Sankey Generation Bugs

Run this prompt against the `api/` folder after all frontend phases are complete.

---

## Bug 1: Target role doesn't match user's selection

The user's selected target role MUST be in column 4 with type `target_role`. Anything beyond it goes to column 5 as `stretch_role`.

In `api/app/services/sankey_builder.py`, add explicit column assignment:
- Column 0: Origin (always one node)
- Column 1: Credentials (certs + degrees)
- Column 2: Bridge programs (SkillBridge, advanced certs)
- Column 3: Entry roles
- Column 4: **USER'S TARGET** (type `target_role`)
- Column 5: Stretch goals beyond target (type `stretch_role`)

Add validation after generation:
```python
def validate_sankey(data, target_id):
    target = next((n for n in data["nodes"] if n["id"] == target_id), None)
    assert target and target["column"] == 4 and target["type"] == "target_role"
```

Ensure title uses user's target: `f"{origin} → {user_selected_target}"`

## Bug 2: First branch is always certs, never degrees

When user's education is below bachelor's, column 1 MUST include a degree path alongside certs.

Add `should_include_degree_path(education, target)` to `sankey_builder.py`:
- no_degree / high_school / some_college / associate → include BS path
- bachelors → include MS if target is management-oriented
- masters+ → no degree path

Inject degree node into column 1 with type `education`, link from origin with value 12-16 (thinner than cert paths at 20-30).

Update `ai_roadmap_generator.py` system prompt with explicit rules about degree inclusion and target anchoring.

**Test cases:**
1. 25B + "Cybersecurity Analyst" → target in col 4, Security Engineer in col 5
2. 11B + "Operations Manager" → target in col 4, NOT "IT Manager"
3. Any MOS + "High school" education → BS degree appears in column 1
4. Any MOS + "Bachelor's" + management target → MS appears in column 1

Commit: `fix: anchor target role in column 4 + include degree paths in column 1`
