import { Card, CardContent } from "@/components/ui/card";
import PageHero from "@/components/layout/PageHero";

const hasApi = (import.meta.env.VITE_API_BASE ?? '').trim().length > 0;

export default function EmploymentNetworkingPage() {
  return (
    <>
      <PageHero
        eyebrow="Employment"
        title="Employment Networking"
        subtitle="LinkedIn and networking roadmaps to grow your professional network during transition."
      />
      <div className="max-w-[720px] mx-auto px-7 py-8">
        <Card style={{ background: "var(--color-bg-secondary)", borderColor: "var(--color-border)" }}>
          <CardContent className="pt-6 pb-6">
            <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
              The networking feature analyzes your goals and builds a step-by-step roadmap (who to connect with,
              how to message, and follow-up). It requires the backend API to be running.
            </p>
            {!hasApi && (
              <p className="text-sm mt-4" style={{ color: "var(--color-text-dim)" }}>
                Set <code className="text-xs bg-[var(--color-bg-tertiary)] px-1 rounded">VITE_API_BASE</code> in{" "}
                <code className="text-xs bg-[var(--color-bg-tertiary)] px-1 rounded">.env</code> (e.g.{" "}
                <code className="text-xs bg-[var(--color-bg-tertiary)] px-1 rounded">http://localhost:8000</code>)
                and start your backend to use the networking tools.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
