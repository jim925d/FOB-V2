import { Link } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import PageHero from "@/components/layout/PageHero";
import { useApi } from "@/hooks/useApi";
import { getPrograms, getProgramStats } from "@/lib/api";

function toList(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  return data.items ?? data.programs ?? data.results ?? [];
}

export default function SkillBridgeExplorerPage() {
  const { data: programsData, loading, error } = useApi(getPrograms, { limit: 50 });
  const { data: stats } = useApi(getProgramStats);
  const programs = toList(programsData);

  return (
    <>
      <PageHero
        eyebrow="SkillBridge"
        title="SkillBridge Explorer"
        subtitle="Explore DoD SkillBridge programs for internships and training during transition."
      />
      <div className="max-w-[900px] mx-auto px-7 py-8">
        {loading && (
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>Loading programs…</p>
        )}
        {error && (
          <Card className="mb-6" style={{ background: "var(--color-bg-secondary)", borderColor: "var(--color-border)" }}>
            <CardContent className="pt-5">
              <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>{error}</p>
              <p className="text-xs mt-2" style={{ color: "var(--color-text-dim)" }}>
                Set VITE_API_BASE in .env to your backend URL (e.g. http://localhost:8000) and ensure the API is running.
              </p>
            </CardContent>
          </Card>
        )}
        {!loading && !error && (
          <>
            {stats && (stats.total ?? stats.count != null) && (
              <p className="text-sm mb-4" style={{ color: "var(--color-text-muted)" }}>
                {stats.total ?? stats.count} program{stats.total !== 1 && stats.count !== 1 ? "s" : ""} available
              </p>
            )}
            {programs.length === 0 ? (
              <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
                No programs returned. Your API may use a different response shape (e.g. programs, items).
              </p>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {programs.slice(0, 24).map((p, i) => (
                  <Card
                    key={p.id ?? p.slug ?? i}
                    style={{ background: "var(--color-bg-secondary)", borderColor: "var(--color-border)" }}
                  >
                    <CardContent className="pt-4 pb-4">
                      <div className="font-medium" style={{ color: "var(--color-text-primary)" }}>
                        {p.name ?? p.title ?? p.program_name ?? "Unnamed program"}
                      </div>
                      {(p.description ?? p.summary) && (
                        <p className="text-sm mt-1 line-clamp-2" style={{ color: "var(--color-text-muted)" }}>
                          {p.description ?? p.summary}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
