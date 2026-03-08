import { Card, CardContent } from "@/components/ui/card";
import PageHero from "@/components/layout/PageHero";

const sections = [
  {
    title: "VA Education Benefits",
    items: [
      "Post-9/11 GI Bill (Chapter 33)",
      "Montgomery GI Bill (Chapter 30)",
      "VR&E (Chapter 31) — employment and training",
      "Dependents and survivors benefits",
    ],
  },
  {
    title: "VA Home Loans",
    items: [
      "VA-backed home loans (no down payment in many cases)",
      "Native American Direct Loan (NADL)",
      "Adapted housing grants for service-connected disabilities",
    ],
  },
  {
    title: "Health &amp; Support",
    items: [
      "VA health care enrollment",
      "Mental health and crisis support (988, press 1)",
      "eBenefits and VA.gov for claims and records",
    ],
  },
];

export default function BenefitsPage() {
  return (
    <>
      <PageHero
        eyebrow="Benefits"
        title="VA Benefits &amp; Resources"
        subtitle="Education benefits, home loans, health care, and support resources."
      />
      <div className="max-w-[720px] mx-auto px-7 py-8">
        <p className="text-sm mb-8" style={{ color: "var(--color-text-muted)" }}>
          Use this page as a starting point. For eligibility and applications, go to{" "}
          <a
            href="https://www.va.gov"
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
            style={{ color: "var(--color-accent)" }}
          >
            VA.gov
          </a>{" "}
          or your local VA office.
        </p>
        <div className="space-y-8">
          {sections.map((sec) => (
            <Card
              key={sec.title}
              style={{ background: "var(--color-bg-secondary)", borderColor: "var(--color-border)" }}
            >
              <CardContent className="pt-6 pb-6">
                <h2 className="text-lg font-semibold mb-3" style={{ color: "var(--color-text-primary)" }}>
                  {sec.title}
                </h2>
                <ul className="list-disc list-inside space-y-1 text-sm" style={{ color: "var(--color-text-muted)" }}>
                  {sec.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </>
  );
}
