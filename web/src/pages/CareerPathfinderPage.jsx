import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SectionLabel } from "@/components/ui/section-label";
import { SearchableSelect } from "@/components/ui/searchable-select";
import PageHero from "@/components/layout/PageHero";
import { useApi, useLazyApi } from "@/hooks/useApi";
import { getRoles, getTargets, generateRoadmap } from "@/lib/api";

const eduOptions = [
  { value: "high_school", label: "High school / GED" },
  { value: "some_college", label: "Some college" },
  { value: "associate", label: "Associate degree" },
  { value: "bachelors", label: "Bachelor's degree" },
  { value: "masters", label: "Master's degree" },
  { value: "doctorate", label: "Doctorate" },
];

const yearsOptions = [
  { value: "0-2", label: "0–2 years" },
  { value: "3-5", label: "3–5 years" },
  { value: "6-10", label: "6–10 years" },
  { value: "10+", label: "10+ years" },
];

const industries = [
  { value: "tech", label: "Technology" },
  { value: "healthcare", label: "Healthcare" },
  { value: "government", label: "Government" },
  { value: "defense", label: "Defense / Contracting" },
  { value: "finance", label: "Finance" },
  { value: "other", label: "Other" },
];

const timelineOptions = [
  { value: "0-6", label: "0–6 months" },
  { value: "6-12", label: "6–12 months" },
  { value: "12-18", label: "12–18 months" },
  { value: "18+", label: "18+ months" },
];

// Fallback options when API is unavailable or returns empty (so dropdowns always have choices)
const FALLBACK_ROLES = [
  {
    label: "Army",
    options: [
      { value: "11B", label: "11B – Infantryman" },
      { value: "25B", label: "25B – Information Technology Specialist" },
      { value: "35F", label: "35F – Intelligence Analyst" },
      { value: "68W", label: "68W – Combat Medic" },
      { value: "88M", label: "88M – Motor Transport Operator" },
      { value: "92Y", label: "92Y – Unit Supply Specialist" },
    ],
  },
  {
    label: "Navy",
    options: [
      { value: "IT", label: "IT – Information Systems Technician" },
      { value: "CTN", label: "CTN – Cryptologic Technician (Networks)" },
      { value: "HM", label: "HM – Hospital Corpsman" },
      { value: "LS", label: "LS – Logistics Specialist" },
      { value: "YN", label: "YN – Yeoman" },
    ],
  },
  {
    label: "Air Force",
    options: [
      { value: "1N4", label: "1N4 – Network Intelligence Analyst" },
      { value: "3D0", label: "3D0 – Cyber Operations" },
      { value: "4A0", label: "4A0 – Health Services Management" },
      { value: "6C0", label: "6C0 – Contracting" },
    ],
  },
  {
    label: "Marine Corps",
    options: [
      { value: "0311", label: "0311 – Rifleman" },
      { value: "0621", label: "0621 – Field Radio Operator" },
      { value: "0651", label: "0651 – Cyber Network Operator" },
      { value: "3521", label: "3521 – Motor Vehicle Operator" },
    ],
  },
];

const FALLBACK_TARGETS = [
  {
    label: "Technology",
    options: [
      { value: "cyber-analyst", label: "Cybersecurity Analyst" },
      { value: "cloud-eng", label: "Cloud Engineer" },
      { value: "software-dev", label: "Software Developer" },
      { value: "data-analyst", label: "Data Analyst" },
      { value: "network-admin", label: "Network Administrator" },
    ],
  },
  {
    label: "Operations & Management",
    options: [
      { value: "ops-mgr", label: "Operations Manager" },
      { value: "project-mgr", label: "Project Manager" },
      { value: "logistics-mgr", label: "Logistics Manager" },
    ],
  },
  {
    label: "Healthcare & Support",
    options: [
      { value: "health-admin", label: "Healthcare Administrator" },
      { value: "hr-specialist", label: "HR Specialist" },
      { value: "contract-specialist", label: "Contract Specialist" },
    ],
  },
];

function normalizeOptions(list) {
  if (!list?.length) return [];
  return list.map((r) => ({
    value: r.id ?? r.value ?? r.mos_id ?? r.name,
    label: r.label ?? r.name ?? r.title ?? String(r.value ?? r.id),
  }));
}

function toGrouped(flat, groupKey = "branch") {
  const byGroup = {};
  flat.forEach((r) => {
    const g = r[groupKey] || "Other";
    if (!byGroup[g]) byGroup[g] = [];
    byGroup[g].push({ value: r.id ?? r.value, label: r.label ?? r.name ?? r.title ?? String(r.value ?? r.id) });
  });
  return Object.entries(byGroup).map(([label, options]) => ({ label, options }));
}

export default function CareerPathfinderPage() {
  const navigate = useNavigate();
  const { data: rolesRaw, loading: rolesLoading, error: rolesError } = useApi(getRoles);
  const { data: targetsRaw, loading: targetsLoading, error: targetsError } = useApi(getTargets);
  const { loading: roadmapLoading, error: roadmapError, execute: runRoadmap } = useLazyApi(generateRoadmap);

  const rolesFromApi = rolesRaw?.length
    ? (rolesRaw[0]?.options ? rolesRaw : toGrouped(normalizeOptions(rolesRaw)))
    : [];
  const targetsFromApi = targetsRaw?.length
    ? (targetsRaw[0]?.options ? targetsRaw : toGrouped(targetsRaw, "group"))
    : [];
  const roles = rolesFromApi.length > 0 ? rolesFromApi : FALLBACK_ROLES;
  const targets = targetsFromApi.length > 0 ? targetsFromApi : FALLBACK_TARGETS;
  const rolesGrouped = roles.length > 0 && roles[0]?.options != null;
  const targetsGrouped = targets.length > 0 && targets[0]?.options != null;

  const [currentRole, setCurrentRole] = useState(null);
  const [education, setEducation] = useState(null);
  const [yearsInRole, setYearsInRole] = useState(null);
  const [targetRole, setTargetRole] = useState(null);
  const [targetIndustry, setTargetIndustry] = useState(null);
  const [timeline, setTimeline] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!currentRole || !education || !yearsInRole || !targetRole || !timeline) return;
    try {
      const payload = {
        current_role_id: currentRole,
        education,
        years_in_role: yearsInRole,
        target_role_id: targetRole,
        target_industry: targetIndustry || undefined,
        separation_timeline: timeline,
      };
      const roadmap = await runRoadmap(payload);
      navigate("/careers/pathfinder/map", { state: { roadmap, inputs: payload } });
    } catch (_) {
      // error surfaced via roadmapError
    }
  };

  const canSubmit = currentRole && education && yearsInRole && targetRole && timeline && !roadmapLoading;

  return (
    <>
      <PageHero
        eyebrow="Career Pathfinder"
        title="Where you are → Where you want to go"
        subtitle="Get a personalized career map and role cards."
      />
      <div className="max-w-[680px] mx-auto px-7 pb-12">
        <form onSubmit={handleSubmit}>
          <SectionLabel color="var(--color-accent)">Where You Are</SectionLabel>
          <Card className="mb-7">
            <CardContent className="pt-6 space-y-4">
              <SearchableSelect
                label="Current Role / MOS"
                options={roles}
                grouped={rolesGrouped}
                value={currentRole}
                onChange={setCurrentRole}
                placeholder={rolesLoading ? "Loading…" : rolesError ? "Error loading roles" : "Select role"}
                required
              />
              <SearchableSelect
                label="Highest Education"
                options={eduOptions}
                value={education}
                onChange={setEducation}
                placeholder="Select education"
                required
              />
              <SearchableSelect
                label="Years in Current Role"
                options={yearsOptions}
                value={yearsInRole}
                onChange={setYearsInRole}
                placeholder="Select years"
                required
              />
            </CardContent>
          </Card>

          <SectionLabel color="var(--color-copper)">Where You Want To Go</SectionLabel>
          <Card className="mb-7">
            <CardContent className="pt-6 space-y-4">
              <SearchableSelect
                label="Target Role"
                options={targets}
                grouped={targetsGrouped}
                value={targetRole}
                onChange={setTargetRole}
                placeholder={targetsLoading ? "Loading…" : targetsError ? "Error loading targets" : "Select target role"}
                required
              />
              <SearchableSelect
                label="Target Industry"
                options={industries}
                value={targetIndustry}
                onChange={setTargetIndustry}
                placeholder="Optional"
              />
              <SearchableSelect
                label="Separation Timeline"
                options={timelineOptions}
                value={timeline}
                onChange={setTimeline}
                placeholder="Select timeline"
                required
              />
            </CardContent>
          </Card>

          {roadmapError && (
            <p className="text-sm text-destructive mb-4">{roadmapError}</p>
          )}
          <Button
            type="submit"
            variant="info"
            size="lg"
            className="w-full max-w-[400px] mx-auto block"
            disabled={!canSubmit}
          >
            {roadmapLoading ? "Generating…" : "Generate Career Map →"}
          </Button>
        </form>
      </div>
    </>
  );
}
