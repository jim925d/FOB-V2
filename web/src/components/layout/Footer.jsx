import { Link } from "react-router-dom";

const footerLinks = [
  { to: "/", label: "Home" },
  { to: "/careers/pathfinder", label: "Pathfinder" },
  { to: "/skillbridge", label: "SkillBridge" },
  { to: "/benefits", label: "Benefits" },
  { to: "/communities", label: "Communities" },
  { to: "/news", label: "News" },
  { to: "/dashboard", label: "Dashboard" },
];

export default function Footer() {
  return (
    <footer
      className="border-t py-6 px-4"
      style={{
        background: "var(--color-bg-secondary)",
        borderColor: "var(--color-border)",
      }}
    >
      <div className="max-w-[1200px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <Link
          to="/"
          className="font-serif text-lg text-[--color-text-primary]"
        >
          THE <span style={{ color: "var(--color-accent)" }}>FOB</span>
        </Link>
        <nav className="flex flex-wrap items-center justify-center gap-x-6 gap-y-1">
          {footerLinks.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className="text-xs text-[--color-text-muted] hover:text-[--color-text-primary] transition-colors"
            >
              {label}
            </Link>
          ))}
        </nav>
      </div>
      <p className="text-xs text-[--color-text-muted] text-center mt-4">
        © {new Date().getFullYear()} The FOB. All rights reserved.
      </p>
    </footer>
  );
}
