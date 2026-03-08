import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Menu } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import AuthModal from "@/components/auth/AuthModal";

const navLinks = [
  { to: "/", label: "Home" },
  { to: "/careers/pathfinder", label: "Pathfinder" },
  { to: "/careers/pathfinder/map", label: "Career Map" },
  { to: "/skillbridge", label: "SkillBridge" },
  { to: "/benefits", label: "Benefits" },
  { to: "/communities", label: "Communities" },
  { to: "/employment/ergs", label: "ERGs" },
  { to: "/employment/networking", label: "Networking" },
  { to: "/news", label: "News" },
  { to: "/dashboard", label: "Dashboard" },
];

export default function AppNav() {
  const location = useLocation();
  const { isAuthenticated, user, signOut } = useAuth();
  const [authOpen, setAuthOpen] = useState(false);

  const navContent = (
    <>
      {navLinks.map(({ to, label }) => (
        <Button
          key={to}
          variant="ghost"
          size="sm"
          asChild
          className={
            location.pathname === to
              ? "!bg-[var(--color-accent-dim)] !text-fob-accent"
              : "text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
          }
        >
          <Link to={to}>{label}</Link>
        </Button>
      ))}
    </>
  );

  return (
    <nav
      className="sticky top-0 z-50 h-14 w-full border-b backdrop-blur-[12px] px-4 flex items-center justify-between"
      style={{
        background: "var(--color-bg-secondary)",
        borderColor: "var(--color-border)",
      }}
    >
      <Link
        to="/"
        className="font-serif text-lg shrink-0"
        style={{ color: "var(--color-text-primary)" }}
      >
        THE <span style={{ color: "var(--color-accent)" }}>FOB</span>
      </Link>

      {/* Desktop nav — center */}
      <div className="hidden md:flex items-center gap-1 flex-1 justify-center">
        {navContent}
      </div>

      {/* Right: Sign In or Avatar + Dropdown */}
      <div className="flex items-center gap-2 shrink-0">
        {!isAuthenticated ? (
          <Button size="sm" variant="info" onClick={() => setAuthOpen(true)}>
            Sign In
          </Button>
        ) : (
          <>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button
                  className="rounded-full focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background"
                  aria-label="Account menu"
                >
                  <Avatar
                    className="h-8 w-8 text-fob-accent text-xs font-semibold"
                    style={{ backgroundColor: "var(--color-accent-dim)", color: "var(--color-accent)" }}
                  >
                    <AvatarFallback>
                      {user?.email?.[0]?.toUpperCase() ?? "U"}
                    </AvatarFallback>
                  </Avatar>
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem asChild>
                  <Link to="/dashboard">Dashboard</Link>
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => signOut()}>
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </>
        )}

        {/* Mobile menu */}
        <Sheet>
          <SheetTrigger asChild className="md:hidden">
            <Button variant="ghost" size="icon" aria-label="Open menu">
              <Menu className="h-5 w-5" />
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="w-[280px] flex flex-col gap-2 pt-8">
            {navLinks.map(({ to, label }) => (
              <Button
                key={to}
                variant="ghost"
                size="sm"
                asChild
                className="justify-start w-full"
              >
                <Link to={to}>{label}</Link>
              </Button>
            ))}
          </SheetContent>
        </Sheet>
      </div>

      <AuthModal
        open={authOpen}
        onOpenChange={setAuthOpen}
        defaultTab="signin"
        contextMessage="Sign in to save your progress"
      />
    </nav>
  );
}
