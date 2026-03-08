import { Card, CardContent } from "@/components/ui/card";
import PageHero from "@/components/layout/PageHero";
import { useAuth } from "@/contexts/AuthContext";
import { useApi } from "@/hooks/useApi";
import { getProfile } from "@/lib/database";

function ProfileBlock({ userId }) {
  const { data, loading, error } = useApi(getProfile, userId);
  return (
    <Card style={{ background: "var(--color-bg-secondary)", borderColor: "var(--color-border)" }}>
      <CardContent className="pt-5 pb-5">
        <h3 className="text-sm font-semibold mb-2" style={{ color: "var(--color-text-primary)" }}>
          Profile
        </h3>
        {loading && <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>Loading…</p>}
        {error && <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>{error}</p>}
        {data && (
          <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
            {data.display_name ?? data.full_name ?? "Profile loaded."}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <>
      <PageHero
        eyebrow="Dashboard"
        title="Your Dashboard"
        subtitle="Saved items, profile, and progress in one place."
      />
      <div className="max-w-[720px] mx-auto px-7 py-8">
        {user ? (
          <div className="space-y-6">
            <ProfileBlock userId={user.id} />
            <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
              More dashboard features (saved roadmaps, programs, benefits progress) will appear here as you use the app.
            </p>
          </div>
        ) : (
          <Card style={{ background: "var(--color-bg-secondary)", borderColor: "var(--color-border)" }}>
            <CardContent className="pt-6 pb-6">
              <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
                Sign in to see your profile and saved items. Use the Sign In button in the nav.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </>
  );
}
