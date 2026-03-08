import { Card, CardContent } from "@/components/ui/card";
import PageHero from "@/components/layout/PageHero";
import { useApi } from "@/hooks/useApi";
import { getNews } from "@/lib/api";

function toList(data) {
  if (!data) return [];
  if (Array.isArray(data)) return data;
  return data.items ?? data.articles ?? data.results ?? data.entries ?? [];
}

export default function VANewsPage() {
  const { data: newsData, loading, error } = useApi(getNews);
  const items = toList(newsData);

  return (
    <>
      <PageHero
        eyebrow="News"
        title="VA &amp; Veteran News"
        subtitle="Curated feeds from military and veteran news sources."
      />
      <div className="max-w-[800px] mx-auto px-7 py-8">
        {loading && (
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>Loading news…</p>
        )}
        {error && (
          <Card className="mb-6" style={{ background: "var(--color-bg-secondary)", borderColor: "var(--color-border)" }}>
            <CardContent className="pt-5">
              <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>{error}</p>
              <p className="text-xs mt-2" style={{ color: "var(--color-text-dim)" }}>
                Set VITE_API_BASE in .env and ensure the news API is running.
              </p>
            </CardContent>
          </Card>
        )}
        {!loading && !error && (
          <>
            {items.length === 0 ? (
              <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
                No articles yet. The API may return a different shape (e.g. items, articles).
              </p>
            ) : (
              <ul className="space-y-3">
                {items.slice(0, 30).map((a, i) => (
                  <li key={a.id ?? a.url ?? i}>
                    <Card style={{ background: "var(--color-bg-secondary)", borderColor: "var(--color-border)" }}>
                      <CardContent className="pt-4 pb-4">
                        <a
                          href={a.url ?? a.link ?? "#"}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="font-medium hover:underline"
                          style={{ color: "var(--color-text-primary)" }}
                        >
                          {a.title ?? a.headline ?? "Untitled"}
                        </a>
                        {(a.source ?? a.site_name ?? a.published_at) && (
                          <p className="text-xs mt-1" style={{ color: "var(--color-text-muted)" }}>
                            {[a.source, a.site_name, a.published_at].filter(Boolean).join(" · ")}
                          </p>
                        )}
                      </CardContent>
                    </Card>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>
    </>
  );
}
