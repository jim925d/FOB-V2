import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import PageHero from "@/components/layout/PageHero";

const quickLinks = [
  { to: "/careers/pathfinder", label: "Career Pathfinder", desc: "Map your path from current role to civilian career" },
  { to: "/careers/pathfinder/map", label: "Career Map", desc: "Visualize your roadmap" },
  { to: "/skillbridge", label: "SkillBridge Explorer", desc: "Explore DoD SkillBridge programs" },
  { to: "/benefits", label: "Benefits", desc: "VA education, loans, and resources" },
  { to: "/communities", label: "Communities", desc: "Veteran organizations and groups" },
  { to: "/employment/ergs", label: "ERG Directory", desc: "Employer resource groups" },
  { to: "/employment/networking", label: "Networking", desc: "LinkedIn and networking roadmaps" },
  { to: "/news", label: "VA News", desc: "Veteran and military news" },
  { to: "/dashboard", label: "Dashboard", desc: "Your saved items and profile" },
];

export default function HomePage() {
  return (
    <>
      <PageHero
        eyebrow="The FOB"
        title="Forward Operating Base"
        subtitle="Your hub for career transition, benefits, and veteran resources."
      />
      <div className="max-w-[900px] mx-auto px-7 py-10">
        <h2 className="text-lg font-semibold mb-4" style={{ color: "var(--color-text-primary)" }}>
          Explore
        </h2>
        <div className="grid gap-3 sm:grid-cols-2">
          {quickLinks.map(({ to, label, desc }) => (
            <Link key={to} to={to}>
              <Card
                className="h-full transition-colors hover:border-[var(--color-accent)]"
                style={{ background: "var(--color-bg-secondary)", borderColor: "var(--color-border)" }}
              >
                <CardContent className="pt-5 pb-5">
                  <div className="font-medium" style={{ color: "var(--color-text-primary)" }}>
                    {label}
                  </div>
                  <p className="text-sm mt-1" style={{ color: "var(--color-text-muted)" }}>
                    {desc}
                  </p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </>
  );
}
