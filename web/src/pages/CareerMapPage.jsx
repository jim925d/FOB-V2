import { Link, useLocation } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import PageHero from "@/components/layout/PageHero";
import SankeyDiagram from "@/components/career/SankeyDiagram";

export default function CareerMapPage() {
  const { state } = useLocation();
  const roadmap = state?.roadmap;
  const hasRoadmap = !!roadmap;
  const sankey = roadmap?.sankey;
  const title = roadmap?.title || "Your Career Map";

  return (
    <>
      <PageHero
        eyebrow="Career Pathfinder"
        title={hasRoadmap ? title : "Career Map"}
        subtitle={
          hasRoadmap
            ? "Your personalized roadmap"
            : "Generate a roadmap from the Pathfinder to see it here."
        }
      >
        {hasRoadmap && (
          <div className="flex gap-3 flex-wrap mt-3">
            <Button variant="outline" size="sm" asChild>
              <Link to="/careers/pathfinder">← Back to Pathfinder</Link>
            </Button>
          </div>
        )}
      </PageHero>
      <div className="max-w-[1100px] mx-auto px-7 py-8">
        {hasRoadmap ? (
          <SankeyDiagram sankey={sankey} title={title} />
        ) : (
          <Card style={{ background: "var(--color-bg-secondary)", borderColor: "var(--color-border)" }}>
            <CardContent className="pt-6 pb-6">
              <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
                Use the Career Pathfinder to choose your current role, target role, and timeline—then generate your map.
              </p>
              <Link
                to="/careers/pathfinder"
                className="inline-block mt-4 text-sm font-medium"
                style={{ color: "var(--color-accent)" }}
              >
                Go to Pathfinder →
              </Link>
            </CardContent>
          </Card>
        )}
      </div>
    </>
  );
}
