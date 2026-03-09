# Phase 1 — Layout + shadcn/ui Component Customization

## What you're building

The layout shell (nav, hero, footer, crisis bar) and customized shadcn/ui components styled to the FOB design system. After this phase, every future page uses these components.

**Prerequisites:** Phase 0 complete (Vite + shadcn running, dark theme, routes).

---

## Layout Components — `src/components/layout/`

### AppNav.jsx

Top navigation bar, persistent on every page. Uses shadcn `Button`, `Sheet` (mobile menu), `Avatar`, `DropdownMenu`.

**Structure:**
- Sticky top, full width, h-14, bg `--color-bg-secondary` with backdrop-filter blur(12px), bottom border `--color-border`
- Left: Logo — "THE FOB" in `font-serif` text-lg. "FOB" in `text-fob-accent`.
- Center: Nav links using shadcn `Button variant="ghost" size="sm"`. Active link: bg `--color-accent-dim`, text `--color-accent`. Others: text `--color-text-muted`, hover text `--color-text-primary`. Use `useLocation()` from react-router to determine active.
- Right: 
  - Not signed in: `<Button size="sm">Sign In</Button>` styled with `bg-fob-info text-white`
  - Signed in: shadcn `Avatar` (initials, accent-dim bg, accent text) + `DropdownMenu` with Dashboard link and Sign Out
- Mobile (<768px): Links collapse. Use shadcn `Sheet` (slides from right) triggered by hamburger icon. Sheet contains full nav links as vertical `Button variant="ghost"` list.
- Z-index 50

```jsx
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Menu } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
```

### PageHero.jsx

Reusable hero section. No shadcn needed — pure layout component.

**Props:** `eyebrow`, `title` (string, supports HTML via dangerouslySetInnerHTML), `subtitle`, `compact` (boolean), `children`

**Structure:**
- Background: gradient from `--color-bg-secondary` to `--color-bg-primary`
- Border bottom `--color-border`
- Padding: py-12 px-7 (default) or py-8 px-7 (compact)
- Max-width 1200px centered
- Eyebrow: flex row — 22px×2px accent bar + text-xs uppercase tracking-widest text-fob-accent
- Title: `font-serif` text-4xl (default) or text-2xl (compact), text-[--color-text-primary]. `<em>` tags → text-fob-accent, not italic
- Subtitle: text-sm text-[--color-text-muted] max-w-xl

### CrisisBar.jsx

- Full width, bg `rgba(239,68,68,0.08)`
- Centered text-xs text-destructive
- "Veterans Crisis Line: Dial 988 press 1 · Text 838255"
- Dismissible × button, stores state in sessionStorage

### Footer.jsx

- bg `--color-bg-secondary`, border-top `--color-border`
- Logo + nav links + copyright
- Links: text-xs text-[--color-text-muted] hover:text-[--color-text-primary]

---

## Custom shadcn Overrides — `src/components/ui/`

shadcn installs base components. Customize these files directly (shadcn is designed for this):

### Extend Button variants

Edit `src/components/ui/button.jsx` — add FOB-specific variants to the `buttonVariants` cva config:

```javascript
const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-[9px] text-sm font-semibold ring-offset-background transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-[--color-accent] text-[--color-bg-primary] hover:bg-[--color-accent-hover]",
        info: "bg-fob-info text-white hover:bg-fob-info/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-[--color-border] bg-transparent text-[--color-text-secondary] hover:bg-[--color-bg-hover]",
        ghost: "text-[--color-text-muted] hover:bg-[--color-bg-hover] hover:text-[--color-text-primary]",
        amber: "bg-fob-warn text-[--color-bg-primary] hover:bg-fob-warn/90",
        copper: "bg-fob-copper text-white hover:bg-fob-copper/90",
        link: "text-[--color-accent] underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-5 py-2",
        sm: "h-8 rounded-[7px] px-3 text-xs",
        lg: "h-12 rounded-[9px] px-8 text-base",
        icon: "h-9 w-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);
```

### Extend Badge variants

Edit `src/components/ui/badge.jsx` — add node-type badges:

```javascript
const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-primary text-primary-foreground",
        secondary: "border-transparent bg-secondary text-secondary-foreground",
        outline: "text-foreground",
        // FOB node type badges
        certification: "border-fob-info/30 bg-fob-info/15 text-fob-info",
        education: "border-fob-purple/30 bg-fob-purple/15 text-fob-purple",
        skillbridge: "border-fob-copper/30 bg-fob-copper/15 text-fob-copper",
        entry_role: "border-fob-orange/30 bg-fob-orange/15 text-fob-orange",
        mid_role: "border-fob-warn/30 bg-fob-warn/15 text-fob-warn",
        target_role: "border-fob-accent/30 bg-fob-accent/15 text-fob-accent",
        stretch_role: "border-fob-accent/30 bg-fob-accent/10 text-fob-accent/80",
        origin: "border-fob-accent/30 bg-fob-accent/15 text-fob-accent",
      },
    },
    defaultVariants: { variant: "default" },
  }
);
```

### Style Card overrides

Edit `src/components/ui/card.jsx` — update the Card component's default classes:

```javascript
const Card = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "rounded-xl border bg-[--color-bg-secondary] border-[--color-border] text-card-foreground shadow-sm transition-all duration-200",
      className
    )}
    {...props}
  />
));
```

### Additional custom components to create

These don't come from shadcn — build them fresh:

#### `src/components/ui/section-label.jsx`
```jsx
export function SectionLabel({ children, color = "var(--color-accent)" }) {
  return (
    <div className="flex items-center gap-2 mb-3.5">
      <div className="w-1 h-[18px] rounded-sm" style={{ background: color }} />
      <span className="text-[11px] font-semibold tracking-wider uppercase" style={{ color: 'var(--color-text-dim)' }}>
        {children}
      </span>
    </div>
  );
}
```

#### `src/components/ui/page-hero.jsx`
(The PageHero component described above)

#### `src/components/ui/searchable-select.jsx`

Build a custom SearchableSelect using shadcn `Popover` + `Command`:

```bash
npx shadcn@latest add popover command
```

Then build SearchableSelect using `Popover` as the dropdown container and `Command` (cmdk) for the searchable list. This gives you keyboard navigation, filtering, and accessibility for free.

**Props:** `options`, `value`, `onChange`, `placeholder`, `multi`, `grouped`, `allowCustom`, `label`, `error`, `required`

**Structure:**
- Trigger: styled like shadcn Input, with chevron icon
- Content: `Popover` containing `Command` with `CommandInput` (search), `CommandGroup` (for grouped options), `CommandItem` (each option)
- Multi-select: selected items as Badges below input with × to remove
- Custom entry: CommandItem "Add custom" at bottom

---

## Wire Layout into App.jsx

```jsx
import AppNav from '@/components/layout/AppNav';
import CrisisBar from '@/components/layout/CrisisBar';
import Footer from '@/components/layout/Footer';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <CrisisBar />
      <AppNav />
      <main className="flex-1 pt-14"> {/* pt-14 = nav height */}
        <Routes>
          {/* ...all routes... */}
        </Routes>
      </main>
      <Footer />
    </div>
  );
}
```

---

## Verify

- Nav renders on every page, active link highlighted in accent
- Mobile: Sheet menu opens/closes with hamburger
- All shadcn components render with dark FOB theme (not default light)
- `<Button variant="info">` renders blue, `<Button variant="ghost">` renders transparent
- `<Badge variant="certification">` renders blue, `<Badge variant="education">` renders purple
- `<Card>` renders with dark bg and border
- SearchableSelect: opens popover, type to filter, select option, keyboard nav works
- CrisisBar visible above nav
- Footer at bottom
- No default shadcn light theme colors visible anywhere

**Phase 1 complete.** Commit: `feat: phase 1 — layout shell + customized shadcn/ui components`
