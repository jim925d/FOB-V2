import { Card, CardContent } from "@/components/ui/card";
import PageHero from "@/components/layout/PageHero";
import { useApi } from "@/hooks/useApi";
import { getERGs } from "@/lib/api";

function toList(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  return data.items ?? data.ergs ?? data.results ?? [];
}

export default function ERGDirectoryPage() {
  const { data: rawData, loading, error } = useApi(getERGs);
  const list = toList(rawData);

  return (
    <>
      <PageHero
        eyebrow="Employment"
        title="ERG Directory"
        subtitle="Companies with Employee Resource Groups for veterans."
      />
      <div className="max-w-[900px] mx-auto px-7 py-8">
        {loading && (
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>Loading ERGs…</p>
        )}
        {error && (
          <Card className="mb-6" style={{ background: "var(--color-bg-secondary)", borderColor: "var(--color-border)" }}>
            <CardContent className="pt-5">
              <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>{error}</p>
              <p className="text-xs mt-2" style={{ color: "var(--color-text-dim)" }}>
                Set VITE_API_BASE in .env and ensure the API is running.
              </p>
            </CardContent>
          </Card>
        )}
        {!loading && !error && (
          <>
            {list.length === 0 ? (
              <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
                No ERGs returned. Check API response shape (e.g. items, ergs).
              </p>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {list.slice(0, 24).map((e, i) => (
                  <Card
                    key={e.id ?? e.company_id ?? i}
                    style={{ background: "var(--color-bg-secondary)", borderColor: "var(--color-border)" }}
                  >
                    <CardContent className="pt-4 pb-4">
                      <div className="font-medium" style={{ color: "var(--color-text-primary)" }}>
                        {e.company_name ?? e.name ?? e.title ?? "Unnamed"}
                      </div>
                      {(e.erg_name ?? e.description) && (
                        <p className="text-sm mt-1 line-clamp-2" style={{ color: "var(--color-text-muted)" }}>
                          {e.erg_name ?? e.description}
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
