import { useState, useEffect, useRef, useMemo, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════
// Design Tokens (FOB)
// ═══════════════════════════════════════════════════════════════
const T = {
  bg:"#0F1214",bgCard:"#171B1E",bgInput:"#1E2326",bgHover:"#252A2E",bgElev:"#2A2F34",
  text:"#F0EDEA",textSec:"#C5CCD0",textMut:"#8A9399",textDim:"#566069",
  accent:"#3ECF8E",accentH:"#35B87D",accentDim:"rgba(62,207,142,0.15)",accentBdr:"rgba(62,207,142,0.3)",
  copper:"#C8956A",copperDim:"rgba(200,149,106,0.12)",
  info:"#60A5FA",infoDim:"rgba(96,165,250,0.15)",
  warn:"#F5A623",warnDim:"rgba(245,166,35,0.15)",
  purple:"#A855F7",purpleDim:"rgba(168,85,247,0.15)",
  orange:"#E08A52",orangeDim:"rgba(224,138,82,0.15)",
  danger:"#EF4444",
  border:"#252A2E",borderL:"#2F353A",
  serif:"'DM Serif Display',Georgia,serif",
  sans:"'DM Sans',system-ui,sans-serif",
  mono:"'JetBrains Mono',monospace",
};
const COL={origin:T.accent,certification:T.info,education:T.purple,skillbridge:T.copper,
  entry_role:T.orange,mid_role:"#E0A552",target_role:T.accent,stretch_role:T.accentH};
const COL_DIM={origin:T.accentDim,certification:T.infoDim,education:T.purpleDim,skillbridge:T.copperDim,
  entry_role:T.orangeDim,mid_role:T.warnDim,target_role:T.accentDim,stretch_role:T.accentDim};

// ═══════════════════════════════════════════════════════════════
// Demo Data Generator (simulates backend response)
// ═══════════════════════════════════════════════════════════════
function generateRoadmap(inputs) {
  const { role, education, years, targetRole, industry, timeline } = inputs;
  const roleLabel = role?.label || "Your Role";
  const targetLabel = targetRole?.label || "Target Role";
  const targetVal = targetRole?.value || "cyber-analyst";
  const eduVal = education?.value || "some_college";
  const needsDegree = ["no_degree","high_school","some_college","associate"].includes(eduVal);
  const hasBachelors = eduVal === "bachelors";

  const nodes = [
    { id:"origin", label:roleLabel, col:0, type:"origin",
      detail:{ title:"Your Starting Point", desc:`Current role: ${roleLabel}. ${education?.label || ""}. ${years?.label || ""} experience.`,
        attrs:[{k:"Role",v:roleLabel},{k:"Education",v:education?.label||"—"},{k:"Experience",v:years?.label||"—"},{k:"Timeline",v:timeline?.label||"—"}]}},
  ];
  const links = [];

  // ═══════════════════════════════════════════════════════════
  // Career track definitions keyed by target role
  // Each track defines: certs (col 1), bridge (col 2), entry (col 3), 
  // the USER'S TARGET in mid/col 4, and stretch goals in col 5
  // ═══════════════════════════════════════════════════════════
  const TRACKS = {
    "cyber-analyst": {
      degree: { id:"degree-bs-cyber", label:"BS Cybersecurity", desc:"GI Bill covered. WGU bundles certs.", schools:"WGU, UMGC" },
      msDegree: { id:"degree-ms-cyber", label:"MS Cybersecurity", desc:"Advanced degree for CISO track.", schools:"SANS, Georgia Tech" },
      certs: [
        { id:"cert-sec", label:"Security+", desc:"DoD 8570 baseline — unlocks all cyber roles.", attrs:[{k:"Study",v:"2–3 mo"},{k:"Cost",v:"$404"}] },
        { id:"cert-net", label:"Network+", desc:"Networking fundamentals for infrastructure.", attrs:[{k:"Study",v:"1–2 mo"},{k:"Cost",v:"$369"}] },
      ],
      bridge: [
        { id:"cert-cysa", label:"CySA+", type:"certification", desc:"Analyst-level cert for SOC roles.", attrs:[{k:"Study",v:"2–4 mo"},{k:"Cost",v:"$404"}] },
        { id:"sb-msft", label:"SkillBridge: Microsoft", type:"skillbridge", desc:"180-day MSSA program. ~40% conversion.", attrs:[{k:"Duration",v:"180 days"},{k:"Rate",v:"~40%"}] },
      ],
      entry: [
        { id:"role-helpdesk", label:"Help Desk Tier II", desc:"Immediate with A+ and experience.", salary:"$48K–$62K", when:"Day 1" },
        { id:"role-soc", label:"SOC Analyst", desc:"Frontline cybersecurity monitoring.", salary:"$58K–$78K", when:"Month 3–6" },
      ],
      target: { id:"role-target", label:"Cybersecurity Analyst", desc:"Proactive threat analysis and security posture management.", salary:"$80K–$115K", when:"Year 1–2" },
      stretch: [
        { id:"role-sec-eng", label:"Security Engineer", desc:"Designs security architecture. Top technical cyber role.", salary:"$115K–$165K", when:"Year 3–5" },
        { id:"role-ciso", label:"CISO", desc:"Chief Information Security Officer.", salary:"$160K–$250K", when:"Year 7–10" },
      ],
      certToEntry: [{s:"cert-sec",t:"role-soc",v:20},{s:"cert-net",t:"role-helpdesk",v:12}],
      bridgeToEntry: [{s:"cert-cysa",t:"role-soc",v:18},{s:"sb-msft",t:"role-soc",v:10},{s:"sb-msft",t:"role-helpdesk",v:6}],
      entryToTarget: [{s:"role-soc",t:"role-target",v:24},{s:"role-helpdesk",t:"role-soc",v:10}],
    },
    "cloud-eng": {
      degree: { id:"degree-bs-it", label:"BS Information Technology", desc:"GI Bill covered. Opens management track.", schools:"WGU, UMGC, Purdue Global" },
      msDegree: { id:"degree-ms-it", label:"MS Cloud Computing", desc:"Advanced cloud architecture and strategy.", schools:"Georgia Tech, WGU" },
      certs: [
        { id:"cert-aws-clp", label:"AWS Cloud Practitioner", desc:"Cloud foundations — fastest entry.", attrs:[{k:"Study",v:"1–2 mo"},{k:"Cost",v:"$100"}] },
        { id:"cert-az900", label:"Azure Fundamentals", desc:"Microsoft cloud entry cert.", attrs:[{k:"Study",v:"1 mo"},{k:"Cost",v:"$99"}] },
      ],
      bridge: [
        { id:"cert-aws-saa", label:"AWS Solutions Architect", type:"certification", desc:"Most in-demand cloud cert. +$30K salary bump.", attrs:[{k:"Study",v:"2–3 mo"},{k:"Cost",v:"$150"}] },
        { id:"sb-amzn", label:"SkillBridge: Amazon", type:"skillbridge", desc:"AWS re/Start program. Cloud + security focus.", attrs:[{k:"Duration",v:"180 days"},{k:"Location",v:"Arlington, VA"}] },
      ],
      entry: [
        { id:"role-cloud-support", label:"Cloud Support Engineer", desc:"Entry cloud — troubleshooting infrastructure.", salary:"$55K–$72K", when:"Month 2–4" },
        { id:"role-sysadmin", label:"Systems Administrator", desc:"Manages servers and infrastructure.", salary:"$60K–$80K", when:"Month 2–4" },
      ],
      target: { id:"role-target", label:"Cloud Engineer", desc:"Builds and automates cloud infrastructure. Highest-growth track.", salary:"$90K–$130K", when:"Year 1–2" },
      stretch: [
        { id:"role-sol-arch", label:"Solutions Architect", desc:"Top of cloud career ladder.", salary:"$130K–$185K", when:"Year 3–5" },
        { id:"role-cloud-mgr", label:"Cloud Engineering Manager", desc:"Leads cloud teams.", salary:"$140K–$190K", when:"Year 5–7" },
      ],
      certToEntry: [{s:"cert-aws-clp",t:"role-cloud-support",v:18},{s:"cert-az900",t:"role-sysadmin",v:14}],
      bridgeToEntry: [{s:"cert-aws-saa",t:"role-cloud-support",v:16},{s:"sb-amzn",t:"role-cloud-support",v:14},{s:"sb-amzn",t:"role-sysadmin",v:6}],
      entryToTarget: [{s:"role-cloud-support",t:"role-target",v:22},{s:"role-sysadmin",t:"role-target",v:10}],
    },
    "ops-mgr": {
      degree: { id:"degree-bs-bus", label:"BS Business Administration", desc:"GI Bill covered. Foundation for management.", schools:"WGU, SNHU, UMGC" },
      msDegree: { id:"degree-mba", label:"MBA", desc:"Master's for senior leadership track.", schools:"Syracuse, Georgetown, USC" },
      certs: [
        { id:"cert-pmp", label:"PMP", desc:"Project Management Professional — gold standard.", attrs:[{k:"Study",v:"3–4 mo"},{k:"Cost",v:"$555"}] },
        { id:"cert-six-sigma", label:"Six Sigma Green Belt", desc:"Process improvement methodology.", attrs:[{k:"Study",v:"2–3 mo"},{k:"Cost",v:"$300"}] },
      ],
      bridge: [
        { id:"cert-capm", label:"CAPM", type:"certification", desc:"Entry project management cert. Stepping stone to PMP.", attrs:[{k:"Study",v:"1–2 mo"},{k:"Cost",v:"$300"}] },
        { id:"sb-amzn-ops", label:"SkillBridge: Amazon Ops", type:"skillbridge", desc:"Operations management training at Amazon.", attrs:[{k:"Duration",v:"180 days"},{k:"Location",v:"Multiple"}] },
      ],
      entry: [
        { id:"role-proj-coord", label:"Project Coordinator", desc:"Supports project managers. Entry to PM track.", salary:"$50K–$65K", when:"Month 1–3" },
        { id:"role-ops-analyst", label:"Operations Analyst", desc:"Analyzes and improves business operations.", salary:"$55K–$72K", when:"Month 2–4" },
      ],
      target: { id:"role-target", label:"Operations Manager", desc:"Manages day-to-day operations, team leadership, process optimization.", salary:"$75K–$110K", when:"Year 1–3" },
      stretch: [
        { id:"role-dir-ops", label:"Director of Operations", desc:"Senior leadership overseeing multiple teams.", salary:"$110K–$155K", when:"Year 3–5" },
        { id:"role-vp-ops", label:"VP Operations", desc:"Executive operations leadership.", salary:"$140K–$200K", when:"Year 5–8" },
      ],
      certToEntry: [{s:"cert-pmp",t:"role-proj-coord",v:18},{s:"cert-pmp",t:"role-ops-analyst",v:14},{s:"cert-six-sigma",t:"role-ops-analyst",v:16}],
      bridgeToEntry: [{s:"cert-capm",t:"role-proj-coord",v:14},{s:"sb-amzn-ops",t:"role-ops-analyst",v:14},{s:"sb-amzn-ops",t:"role-proj-coord",v:8}],
      entryToTarget: [{s:"role-proj-coord",t:"role-target",v:20},{s:"role-ops-analyst",t:"role-target",v:22}],
    },
    "fin-analyst": {
      degree: { id:"degree-bs-fin", label:"BS Finance / Accounting", desc:"GI Bill covered. Required by most employers.", schools:"WGU, SNHU, UMGC" },
      msDegree: { id:"degree-ms-fin", label:"MS Finance", desc:"Advanced quantitative finance.", schools:"Georgetown, NYU" },
      certs: [
        { id:"cert-cfa1", label:"CFA Level I", desc:"Chartered Financial Analyst — prestigious investment cert.", attrs:[{k:"Study",v:"6 mo"},{k:"Cost",v:"$1,200"}] },
        { id:"cert-series7", label:"Series 7 + 66", desc:"Securities licensing for broker-dealers.", attrs:[{k:"Study",v:"2–3 mo"},{k:"Cost",v:"$350"}] },
      ],
      bridge: [
        { id:"cert-fmva", label:"FMVA Certification", type:"certification", desc:"Financial Modeling & Valuation Analyst.", attrs:[{k:"Study",v:"2–3 mo"},{k:"Cost",v:"$500"}] },
        { id:"sb-jpmc", label:"SkillBridge: JPMorgan", type:"skillbridge", desc:"Military Pathways program at JPMorgan Chase.", attrs:[{k:"Duration",v:"180 days"},{k:"Location",v:"NYC / Remote"}] },
      ],
      entry: [
        { id:"role-fin-assoc", label:"Financial Associate", desc:"Entry finance role. Analysis and reporting.", salary:"$55K–$70K", when:"Month 2–4" },
        { id:"role-acct", label:"Staff Accountant", desc:"Bookkeeping, reporting, audit support.", salary:"$50K–$65K", when:"Month 1–3" },
      ],
      target: { id:"role-target", label:"Financial Analyst", desc:"Analyzes financial data, builds models, advises business decisions.", salary:"$72K–$100K", when:"Year 1–2" },
      stretch: [
        { id:"role-sr-fin", label:"Senior Financial Analyst", desc:"Leads analysis and presents to leadership.", salary:"$95K–$130K", when:"Year 3–5" },
        { id:"role-fin-mgr", label:"Finance Manager", desc:"Manages finance team and budgets.", salary:"$110K–$150K", when:"Year 4–7" },
      ],
      certToEntry: [{s:"cert-cfa1",t:"role-fin-assoc",v:16},{s:"cert-series7",t:"role-fin-assoc",v:12},{s:"cert-series7",t:"role-acct",v:10}],
      bridgeToEntry: [{s:"cert-fmva",t:"role-fin-assoc",v:14},{s:"sb-jpmc",t:"role-fin-assoc",v:16},{s:"sb-jpmc",t:"role-acct",v:8}],
      entryToTarget: [{s:"role-fin-assoc",t:"role-target",v:24},{s:"role-acct",t:"role-target",v:14}],
    },
    "fed-pm": {
      degree: { id:"degree-bs-pub", label:"BS Public Administration", desc:"GI Bill covered. Tailored for gov careers.", schools:"UMGC, ASU, Georgetown" },
      msDegree: { id:"degree-mpa", label:"MPA / MPP", desc:"Master's for senior federal leadership.", schools:"Georgetown, Syracuse, GWU" },
      certs: [
        { id:"cert-pmp-fed", label:"PMP", desc:"Required for most federal PM positions.", attrs:[{k:"Study",v:"3–4 mo"},{k:"Cost",v:"$555"}] },
        { id:"cert-fac", label:"FAC-P/PM Level I", desc:"Federal Acquisition Certification for PM.", attrs:[{k:"Study",v:"1–2 mo"},{k:"Cost",v:"Free (gov)"}] },
      ],
      bridge: [
        { id:"cert-fac2", label:"FAC-P/PM Level II", type:"certification", desc:"Advanced federal PM certification.", attrs:[{k:"Study",v:"2–3 mo"},{k:"Cost",v:"Free (gov)"}] },
        { id:"sb-dod", label:"SkillBridge: DoD Civilian", type:"skillbridge", desc:"Transition to DoD civilian PM roles.", attrs:[{k:"Duration",v:"180 days"},{k:"Location",v:"Various"}] },
      ],
      entry: [
        { id:"role-pm-gs11", label:"Program Analyst (GS-11)", desc:"Entry federal program analysis.", salary:"$73K–$95K", when:"Month 1–3" },
        { id:"role-contract", label:"Contract Specialist", desc:"Federal acquisition and procurement.", salary:"$65K–$85K", when:"Month 2–4" },
      ],
      target: { id:"role-target", label:"Federal Program Manager", desc:"Manages federal programs, budgets, and cross-agency coordination.", salary:"$95K–$140K", when:"Year 1–3" },
      stretch: [
        { id:"role-gs15", label:"Senior PM (GS-15)", desc:"Senior federal program leadership.", salary:"$130K–$170K", when:"Year 4–7" },
        { id:"role-ses", label:"SES / Director", desc:"Senior Executive Service.", salary:"$170K–$210K", when:"Year 8+" },
      ],
      certToEntry: [{s:"cert-pmp-fed",t:"role-pm-gs11",v:20},{s:"cert-fac",t:"role-contract",v:16},{s:"cert-fac",t:"role-pm-gs11",v:10}],
      bridgeToEntry: [{s:"cert-fac2",t:"role-pm-gs11",v:14},{s:"sb-dod",t:"role-pm-gs11",v:16},{s:"sb-dod",t:"role-contract",v:8}],
      entryToTarget: [{s:"role-pm-gs11",t:"role-target",v:24},{s:"role-contract",t:"role-target",v:14}],
    },
    "sw-dev": {
      degree: { id:"degree-bs-cs", label:"BS Computer Science", desc:"GI Bill covered. Strongest foundation for dev careers.", schools:"WGU, UMGC, Oregon State" },
      msDegree: { id:"degree-ms-cs", label:"MS Computer Science", desc:"Advanced CS for senior engineering.", schools:"Georgia Tech OMSCS, Stanford" },
      certs: [
        { id:"cert-aws-dev", label:"AWS Developer Associate", desc:"Cloud development fundamentals.", attrs:[{k:"Study",v:"2–3 mo"},{k:"Cost",v:"$150"}] },
        { id:"cert-meta-fe", label:"Meta Front-End Certificate", desc:"React and front-end development.", attrs:[{k:"Study",v:"3–4 mo"},{k:"Cost",v:"$49/mo"}] },
      ],
      bridge: [
        { id:"boot-code", label:"Coding Bootcamp", type:"skillbridge", desc:"12–16 week intensive coding program. VET TEC eligible.", attrs:[{k:"Duration",v:"12–16 wk"},{k:"Cost",v:"VET TEC covers"}] },
        { id:"sb-google", label:"SkillBridge: Google", type:"skillbridge", desc:"Google tech residency program.", attrs:[{k:"Duration",v:"180 days"},{k:"Location",v:"Remote / MTV"}] },
      ],
      entry: [
        { id:"role-jr-dev", label:"Junior Developer", desc:"Entry software development. Build features and fix bugs.", salary:"$60K–$80K", when:"Month 3–6" },
        { id:"role-qa", label:"QA Engineer", desc:"Software testing and quality assurance.", salary:"$55K–$72K", when:"Month 2–4" },
      ],
      target: { id:"role-target", label:"Software Developer", desc:"Builds and maintains software applications. Core engineering role.", salary:"$85K–$130K", when:"Year 1–2" },
      stretch: [
        { id:"role-sr-dev", label:"Senior Developer", desc:"Leads technical design and mentors team.", salary:"$120K–$170K", when:"Year 3–5" },
        { id:"role-eng-mgr", label:"Engineering Manager", desc:"Manages engineering teams.", salary:"$150K–$200K", when:"Year 5–8" },
      ],
      certToEntry: [{s:"cert-aws-dev",t:"role-jr-dev",v:16},{s:"cert-meta-fe",t:"role-jr-dev",v:18},{s:"cert-meta-fe",t:"role-qa",v:10}],
      bridgeToEntry: [{s:"boot-code",t:"role-jr-dev",v:22},{s:"boot-code",t:"role-qa",v:8},{s:"sb-google",t:"role-jr-dev",v:16}],
      entryToTarget: [{s:"role-jr-dev",t:"role-target",v:26},{s:"role-qa",t:"role-target",v:12}],
    },
    "data-analyst": {
      degree: { id:"degree-bs-data", label:"BS Data Science / Statistics", desc:"GI Bill covered. Strong quantitative foundation.", schools:"WGU, SNHU, UMGC" },
      msDegree: { id:"degree-ms-data", label:"MS Data Science", desc:"Advanced analytics and ML.", schools:"Georgia Tech, Berkeley" },
      certs: [
        { id:"cert-google-da", label:"Google Data Analytics Cert", desc:"Entry-level data analytics certification.", attrs:[{k:"Study",v:"3–4 mo"},{k:"Cost",v:"$49/mo"}] },
        { id:"cert-sql", label:"SQL Certification", desc:"Database querying — foundation of all data work.", attrs:[{k:"Study",v:"1–2 mo"},{k:"Cost",v:"$150"}] },
      ],
      bridge: [
        { id:"cert-tableau", label:"Tableau Desktop Specialist", type:"certification", desc:"Data visualization certification.", attrs:[{k:"Study",v:"1–2 mo"},{k:"Cost",v:"$100"}] },
        { id:"sb-deloitte", label:"SkillBridge: Deloitte", type:"skillbridge", desc:"Analytics consulting program.", attrs:[{k:"Duration",v:"180 days"},{k:"Location",v:"Various"}] },
      ],
      entry: [
        { id:"role-bi-analyst", label:"BI Analyst", desc:"Business intelligence reporting and dashboards.", salary:"$55K–$72K", when:"Month 2–4" },
        { id:"role-data-coord", label:"Data Coordinator", desc:"Data entry, cleaning, and basic reporting.", salary:"$48K–$62K", when:"Month 1–3" },
      ],
      target: { id:"role-target", label:"Data Analyst", desc:"Analyzes datasets to drive business decisions. SQL, Python, Tableau.", salary:"$70K–$100K", when:"Year 1–2" },
      stretch: [
        { id:"role-sr-data", label:"Senior Data Analyst", desc:"Leads analytics projects and mentors team.", salary:"$95K–$130K", when:"Year 3–5" },
        { id:"role-data-sci", label:"Data Scientist", desc:"ML models and advanced statistical analysis.", salary:"$110K–$160K", when:"Year 3–6" },
      ],
      certToEntry: [{s:"cert-google-da",t:"role-bi-analyst",v:18},{s:"cert-sql",t:"role-bi-analyst",v:14},{s:"cert-sql",t:"role-data-coord",v:12}],
      bridgeToEntry: [{s:"cert-tableau",t:"role-bi-analyst",v:16},{s:"sb-deloitte",t:"role-bi-analyst",v:14},{s:"sb-deloitte",t:"role-data-coord",v:8}],
      entryToTarget: [{s:"role-bi-analyst",t:"role-target",v:24},{s:"role-data-coord",t:"role-target",v:14}],
    },
    "net-admin": {
      degree: { id:"degree-bs-net", label:"BS Network Engineering", desc:"GI Bill covered. Infrastructure focus.", schools:"WGU, UMGC" },
      msDegree: null,
      certs: [
        { id:"cert-ccna", label:"Cisco CCNA", desc:"Industry gold standard for networking.", attrs:[{k:"Study",v:"3–4 mo"},{k:"Cost",v:"$330"}] },
        { id:"cert-net-plus", label:"CompTIA Network+", desc:"Networking fundamentals.", attrs:[{k:"Study",v:"1–2 mo"},{k:"Cost",v:"$369"}] },
      ],
      bridge: [
        { id:"cert-ccnp", label:"CCNP Enterprise", type:"certification", desc:"Advanced Cisco networking cert.", attrs:[{k:"Study",v:"4–6 mo"},{k:"Cost",v:"$700"}] },
        { id:"sb-cisco", label:"SkillBridge: Cisco", type:"skillbridge", desc:"Networking training with Cisco.", attrs:[{k:"Duration",v:"180 days"},{k:"Location",v:"Various"}] },
      ],
      entry: [
        { id:"role-net-tech", label:"Network Technician", desc:"Installs and maintains network hardware.", salary:"$50K–$65K", when:"Month 1–3" },
        { id:"role-sysadmin-net", label:"Systems Administrator", desc:"Manages servers and network infrastructure.", salary:"$60K–$80K", when:"Month 2–4" },
      ],
      target: { id:"role-target", label:"Network Administrator", desc:"Manages enterprise network infrastructure, security, and performance.", salary:"$70K–$95K", when:"Year 1–2" },
      stretch: [
        { id:"role-net-eng", label:"Network Engineer", desc:"Designs network architecture.", salary:"$85K–$120K", when:"Year 2–4" },
        { id:"role-net-arch", label:"Network Architect", desc:"Enterprise-scale network design.", salary:"$110K–$150K", when:"Year 4–7" },
      ],
      certToEntry: [{s:"cert-ccna",t:"role-sysadmin-net",v:20},{s:"cert-ccna",t:"role-net-tech",v:14},{s:"cert-net-plus",t:"role-net-tech",v:16}],
      bridgeToEntry: [{s:"cert-ccnp",t:"role-sysadmin-net",v:14},{s:"sb-cisco",t:"role-sysadmin-net",v:16},{s:"sb-cisco",t:"role-net-tech",v:8}],
      entryToTarget: [{s:"role-net-tech",t:"role-target",v:18},{s:"role-sysadmin-net",t:"role-target",v:24}],
    },
    "health-admin": {
      degree: { id:"degree-bs-ha", label:"BS Healthcare Administration", desc:"GI Bill covered. Required for most admin roles.", schools:"SNHU, WGU, Purdue Global" },
      msDegree: { id:"degree-mha", label:"MHA / MPH", desc:"Master's for executive healthcare leadership.", schools:"USC, GWU, Johns Hopkins" },
      certs: [
        { id:"cert-hipaa", label:"HIPAA Certification", desc:"Healthcare compliance and privacy.", attrs:[{k:"Study",v:"1 mo"},{k:"Cost",v:"$200"}] },
        { id:"cert-lean-hc", label:"Lean Healthcare Cert", desc:"Process improvement for healthcare.", attrs:[{k:"Study",v:"2 mo"},{k:"Cost",v:"$350"}] },
      ],
      bridge: [
        { id:"cert-chfp", label:"CHFP", type:"certification", desc:"Certified Healthcare Financial Professional.", attrs:[{k:"Study",v:"2–3 mo"},{k:"Cost",v:"$500"}] },
        { id:"sb-va", label:"SkillBridge: VA Hospital", type:"skillbridge", desc:"Administrative training at VA medical centers.", attrs:[{k:"Duration",v:"180 days"},{k:"Location",v:"Various VA"}] },
      ],
      entry: [
        { id:"role-med-office", label:"Medical Office Manager", desc:"Manages clinic operations and staff.", salary:"$48K–$62K", when:"Month 1–3" },
        { id:"role-health-coord", label:"Health Services Coordinator", desc:"Coordinates patient services and programs.", salary:"$45K–$58K", when:"Month 1–3" },
      ],
      target: { id:"role-target", label:"Healthcare Administrator", desc:"Manages healthcare facility operations, budgets, compliance, and staff.", salary:"$70K–$100K", when:"Year 1–3" },
      stretch: [
        { id:"role-dir-ops-hc", label:"Director of Operations", desc:"Senior healthcare operations leadership.", salary:"$95K–$135K", when:"Year 3–6" },
        { id:"role-coo-hc", label:"COO / VP Operations", desc:"Executive healthcare leadership.", salary:"$130K–$180K", when:"Year 6–10" },
      ],
      certToEntry: [{s:"cert-hipaa",t:"role-med-office",v:16},{s:"cert-hipaa",t:"role-health-coord",v:14},{s:"cert-lean-hc",t:"role-med-office",v:12}],
      bridgeToEntry: [{s:"cert-chfp",t:"role-med-office",v:14},{s:"sb-va",t:"role-health-coord",v:16},{s:"sb-va",t:"role-med-office",v:10}],
      entryToTarget: [{s:"role-med-office",t:"role-target",v:22},{s:"role-health-coord",t:"role-target",v:18}],
    },
    "intel-analyst": {
      degree: { id:"degree-bs-ia", label:"BS Intelligence Studies", desc:"GI Bill covered. Tailored for intel careers.", schools:"AMU, Mercyhurst, UMGC" },
      msDegree: { id:"degree-ms-ia", label:"MS Strategic Intelligence", desc:"Advanced analysis and leadership.", schools:"Georgetown, NIC, Johns Hopkins" },
      certs: [
        { id:"cert-sec-intel", label:"Security+", desc:"DoD 8570 baseline for intel systems.", attrs:[{k:"Study",v:"2–3 mo"},{k:"Cost",v:"$404"}] },
        { id:"cert-geoint", label:"GEOINT Certificate", desc:"Geospatial intelligence analysis.", attrs:[{k:"Study",v:"2–3 mo"},{k:"Cost",v:"$500"}] },
      ],
      bridge: [
        { id:"cert-cissp-intel", label:"CISSP", type:"certification", desc:"Advanced security cert for intel roles.", attrs:[{k:"Study",v:"4–6 mo"},{k:"Cost",v:"$749"}] },
        { id:"sb-ic", label:"SkillBridge: Intel Community", type:"skillbridge", desc:"Transition into civilian intel agencies.", attrs:[{k:"Duration",v:"180 days"},{k:"Location",v:"DC Metro"}] },
      ],
      entry: [
        { id:"role-analyst-jr", label:"Junior Intelligence Analyst", desc:"Entry-level all-source analysis.", salary:"$60K–$80K", when:"Month 1–3" },
        { id:"role-osint", label:"OSINT Analyst", desc:"Open-source intelligence collection and analysis.", salary:"$58K–$75K", when:"Month 1–3" },
      ],
      target: { id:"role-target", label:"Intelligence Analyst", desc:"All-source analysis, threat assessment, and intelligence production.", salary:"$78K–$110K", when:"Year 1–2" },
      stretch: [
        { id:"role-sr-intel", label:"Senior Intelligence Analyst", desc:"Leads analysis teams and briefs leadership.", salary:"$100K–$140K", when:"Year 3–5" },
        { id:"role-intel-mgr", label:"Intelligence Manager", desc:"Manages intel programs and collection.", salary:"$120K–$165K", when:"Year 5–8" },
      ],
      certToEntry: [{s:"cert-sec-intel",t:"role-analyst-jr",v:20},{s:"cert-sec-intel",t:"role-osint",v:12},{s:"cert-geoint",t:"role-analyst-jr",v:14}],
      bridgeToEntry: [{s:"cert-cissp-intel",t:"role-analyst-jr",v:14},{s:"sb-ic",t:"role-analyst-jr",v:18},{s:"sb-ic",t:"role-osint",v:10}],
      entryToTarget: [{s:"role-analyst-jr",t:"role-target",v:24},{s:"role-osint",t:"role-target",v:16}],
    },
    "electrician": {
      degree: null,
      msDegree: null,
      certs: [
        { id:"cert-osha30", label:"OSHA 30", desc:"Occupational safety — required on most job sites.", attrs:[{k:"Study",v:"1 mo"},{k:"Cost",v:"$180"}] },
        { id:"cert-epa608", label:"EPA 608", desc:"Refrigerant handling certification.", attrs:[{k:"Study",v:"1 wk"},{k:"Cost",v:"$150"}] },
      ],
      bridge: [
        { id:"appr-ibew", label:"IBEW Apprenticeship", type:"skillbridge", desc:"Union electrical apprenticeship. 4-year paid program.", attrs:[{k:"Duration",v:"4 years"},{k:"Pay",v:"$18–$28/hr while training"}] },
        { id:"sb-trades", label:"SkillBridge: Troops to Trades", type:"skillbridge", desc:"Helmets to Hardhats transition program.", attrs:[{k:"Duration",v:"180 days"},{k:"Location",v:"Various"}] },
      ],
      entry: [
        { id:"role-elec-helper", label:"Electrician's Helper", desc:"Assists journeymen. Learn on the job.", salary:"$35K–$45K", when:"Month 1" },
        { id:"role-appr", label:"Electrical Apprentice", desc:"Formal apprenticeship — best path.", salary:"$38K–$55K", when:"Month 1–3" },
      ],
      target: { id:"role-target", label:"Electrician (Journeyman)", desc:"Licensed journeyman electrician. Commercial and residential.", salary:"$55K–$80K", when:"Year 2–4" },
      stretch: [
        { id:"role-master-elec", label:"Master Electrician", desc:"Highest electrical license. Can pull permits.", salary:"$75K–$100K", when:"Year 5–7" },
        { id:"role-elec-contr", label:"Electrical Contractor", desc:"Own your business. Unlimited earning potential.", salary:"$90K–$200K+", when:"Year 7+" },
      ],
      certToEntry: [{s:"cert-osha30",t:"role-elec-helper",v:18},{s:"cert-osha30",t:"role-appr",v:20},{s:"cert-epa608",t:"role-elec-helper",v:10}],
      bridgeToEntry: [{s:"appr-ibew",t:"role-appr",v:24},{s:"sb-trades",t:"role-appr",v:16},{s:"sb-trades",t:"role-elec-helper",v:8}],
      entryToTarget: [{s:"role-elec-helper",t:"role-target",v:16},{s:"role-appr",t:"role-target",v:28}],
    },
  };

  // Default to matching track, or closest match for unbuilt tracks
  const ALIASES = { "hvac": "electrician", "med-tech": "health-admin" };
  const trackKey = ALIASES[targetVal] || targetVal;
  const track = TRACKS[trackKey] || TRACKS["cyber-analyst"];

  // ═══════════════════════════════════════════════════════════
  // Build nodes from track definition
  // ═══════════════════════════════════════════════════════════

  // Column 1 — Credentials (certs + degree if needed)
  const colCerts = track.certs.map(c => ({
    id: c.id, label: c.label, col: 1, type: "certification",
    detail: { title: c.label, desc: c.desc, attrs: c.attrs || [] }
  }));

  if (needsDegree && track.degree) {
    colCerts.push({
      id: track.degree.id, label: track.degree.label, col: 1, type: "education",
      detail: { title: track.degree.label, desc: track.degree.desc, attrs: [{k:"Duration",v:"2–3 yr"},{k:"Cost",v:"GI Bill Ch. 33"},{k:"Schools",v:track.degree.schools}] }
    });
  }
  if (hasBachelors && track.msDegree) {
    colCerts.push({
      id: track.msDegree.id, label: track.msDegree.label, col: 1, type: "education",
      detail: { title: track.msDegree.label, desc: track.msDegree.desc, attrs: [{k:"Duration",v:"1.5–2 yr"},{k:"Cost",v:"GI Bill"},{k:"Schools",v:track.msDegree.schools}] }
    });
  }

  // Column 2 — Bridge (advanced certs, SkillBridge)
  const colBridge = track.bridge.map(b => ({
    id: b.id, label: b.label, col: 2, type: b.type || "certification",
    detail: { title: b.label, desc: b.desc, attrs: b.attrs || [] }
  }));

  // Column 3 — Entry roles
  const colEntry = track.entry.map(r => ({
    id: r.id, label: r.label, col: 3, type: "entry_role",
    detail: { title: r.label, desc: r.desc, attrs: [{k:"Salary",v:r.salary},{k:"Timeline",v:r.when}] }
  }));

  // Column 4 — THE USER'S TARGET (always here)
  const colMid = [{
    id: track.target.id, label: track.target.label, col: 4, type: "target_role",
    detail: { title: track.target.label, desc: track.target.desc, attrs: [{k:"Salary",v:track.target.salary},{k:"Timeline",v:track.target.when}] }
  }];

  // Column 5 — Stretch goals (beyond the target)
  const colTarget = track.stretch.map(r => ({
    id: r.id, label: r.label, col: 5, type: "stretch_role",
    detail: { title: r.label, desc: r.desc, attrs: [{k:"Salary",v:r.salary},{k:"Timeline",v:r.when}] }
  }));

  // ═══════════════════════════════════════════════════════════
  // Build links
  // ═══════════════════════════════════════════════════════════

  // Origin → Certs
  track.certs.forEach((c, i) => {
    links.push({ s:"origin", t:c.id, v: 28 - i * 8, detail:{ title:`${c.label} Track`, desc:c.desc } });
  });

  // Origin → Degree (if applicable)
  if (needsDegree && track.degree) {
    links.push({ s:"origin", t:track.degree.id, v:14, detail:{ title:"Degree Path", desc:"GI Bill covers it fully. Opens management and degree-required roles." } });
  }
  if (hasBachelors && track.msDegree) {
    links.push({ s:"origin", t:track.msDegree.id, v:10, detail:{ title:"Advanced Degree", desc:"MS/MBA for senior leadership track." } });
  }

  // Certs → Bridge
  if (track.certs[0] && track.bridge[0]) links.push({ s:track.certs[0].id, t:track.bridge[0].id, v:20, detail:{ title:"Cert Ladder", desc:`${track.bridge[0].label} builds on ${track.certs[0].label}.` } });
  if (track.certs[0] && track.bridge[1]) links.push({ s:track.certs[0].id, t:track.bridge[1].id, v:14, detail:{ title:"SkillBridge Path", desc:`${track.bridge[1].label} — paid training on active duty.` } });
  if (track.certs[1] && track.bridge[0]) links.push({ s:track.certs[1].id, t:track.bridge[0].id, v:10, detail:{ title:"Cert Progression", desc:`${track.certs[1].label} feeds into ${track.bridge[0].label}.` } });

  // Bridge/Cert → Entry (from track definition)
  track.certToEntry.forEach(l => links.push({ ...l, detail:{ title:`→ ${track.entry.find(e=>e.id===l.t)?.label||"Entry"}`, desc:"Certification qualifies for entry role." } }));
  track.bridgeToEntry.forEach(l => links.push({ ...l, detail:{ title:`→ ${track.entry.find(e=>e.id===l.t)?.label||"Entry"}`, desc:"Bridge program leads to entry role." } }));

  // Degree → Entry / Target
  if (needsDegree && track.degree) {
    if (track.entry[1]) links.push({ s:track.degree.id, t:track.entry[1].id, v:8, detail:{ title:"Degree → Entry", desc:"Meets HR degree filters." } });
    links.push({ s:track.degree.id, t:track.target.id, v:6, detail:{ title:"Degree → Target Direct", desc:"Some employers hire degree holders directly." } });
  }
  if (hasBachelors && track.msDegree) {
    links.push({ s:track.msDegree.id, t:track.target.id, v:8, detail:{ title:"MS → Target", desc:"Advanced degree accelerates path." } });
    if (track.stretch[0]) links.push({ s:track.msDegree.id, t:track.stretch[0].id, v:6, detail:{ title:"MS → Leadership", desc:"Advanced degree opens senior roles." } });
  }

  // Entry → Target (from track definition)
  track.entryToTarget.forEach(l => links.push({ ...l, detail:{ title:`→ ${track.target.label}`, desc:"Experience qualifies for target role." } }));

  // Target → Stretch
  if (track.stretch[0]) links.push({ s:track.target.id, t:track.stretch[0].id, v:18, detail:{ title:`→ ${track.stretch[0].label}`, desc:"Career growth beyond your target." } });
  if (track.stretch[1]) links.push({ s:track.target.id, t:track.stretch[1].id, v:8, detail:{ title:`→ ${track.stretch[1].label}`, desc:"Long-term leadership trajectory." } });

  nodes.push(...colCerts, ...colBridge, ...colEntry, ...colMid, ...colTarget);

  const columns = [
    {index:0,label:"Starting Point"},{index:1,label:"Credentials"},
    {index:2,label:"Advanced / Bridge"},{index:3,label:"Entry Roles"},
    {index:4,label:"Target Role"},{index:5,label:"Growth"},
  ];

  // Build card progression data with FULL prerequisite chain
  // Walk upstream through the graph to collect ALL prereqs, not just immediate
  const allRoles = [...colEntry, ...colMid, ...colTarget];
  
  // Helper: recursively collect all upstream non-role nodes (certs, degrees, skillbridge)
  function collectAllPrereqs(nodeId, visited = new Set()) {
    if (visited.has(nodeId)) return [];
    visited.add(nodeId);
    const prereqs = [];
    const incoming = links.filter(l => l.t === nodeId);
    for (const link of incoming) {
      const src = nodes.find(n => n.id === link.s);
      if (!src) continue;
      // If source is a credential/education/bridge node, add it as a prereq
      if (["certification", "education", "skillbridge"].includes(src.type)) {
        prereqs.push({ label: src.label, type: src.type, id: src.id });
        // Also collect what feeds into THAT node
        prereqs.push(...collectAllPrereqs(src.id, visited));
      }
      // If source is a role, collect its upstream certs/degrees too (carried forward)
      if (["entry_role", "mid_role"].includes(src.type)) {
        prereqs.push(...collectAllPrereqs(src.id, visited));
      }
    }
    return prereqs;
  }

  const cards = allRoles.map(r => {
    const outgoing = links.filter(l => l.s === r.id);
    const nextRoles = outgoing.map(l => {
      const tgt = nodes.find(n => n.id === l.t);
      return tgt ? tgt.label : l.t;
    });
    
    // Collect full upstream prereqs (deduplicated)
    const rawPrereqs = collectAllPrereqs(r.id);
    const seen = new Set();
    const prereqs = rawPrereqs.filter(p => {
      if (seen.has(p.id)) return false;
      seen.add(p.id);
      return true;
    });
    
    // Also add immediate role prerequisites (the roles that feed into this one)
    const directRolePrereqs = links.filter(l => l.t === r.id).map(l => {
      const src = nodes.find(n => n.id === l.s);
      return src && ["entry_role", "mid_role"].includes(src.type) 
        ? { label: src.label, type: src.type, id: src.id } 
        : null;
    }).filter(Boolean);
    
    return { ...r, prereqs, directRolePrereqs, nextRoles };
  });

  return { nodes, links, columns, cards, title: `${roleLabel} → ${targetLabel}` };
}

// ═══════════════════════════════════════════════════════════════
// Sankey Layout
// ═══════════════════════════════════════════════════════════════
function buildLayout(nodes, links, W, H) {
  const PAD={t:50,b:30,l:16,r:16}, NW=10, NP=22;
  const cols={};
  nodes.forEach(n=>(cols[n.col]??=[]).push({...n,sL:[],tL:[]}));
  const nm={};
  Object.values(cols).flat().forEach(n=>nm[n.id]=n);
  const nc=Math.max(...Object.keys(cols).map(Number))+1;
  const cW=(W-PAD.l-PAD.r-NW)/Math.max(nc-1,1);
  const built=links.map((l,i)=>{
    const o={...l,i,src:nm[l.s],tgt:nm[l.t]};
    if(o.src)o.src.sL.push(o);if(o.tgt)o.tgt.tL.push(o);return o;
  }).filter(l=>l.src&&l.tgt);
  Object.values(nm).forEach(n=>{n.flow=Math.max(n.sL.reduce((a,l)=>a+l.v,0),n.tL.reduce((a,l)=>a+l.v,0),5)});
  Object.entries(cols).forEach(([c,ns])=>{
    const x=PAD.l+(+c)*cW;const tf=ns.reduce((a,n)=>a+n.flow,0);
    const tp=Math.max(ns.length-1,0)*NP;const av=H-PAD.t-PAD.b-tp;
    const sc=Math.min(av/Math.max(tf,1),7);
    let y=PAD.t+Math.max(0,(av+tp-tf*sc-tp)/2);
    ns.forEach(n=>{const h=Math.max(n.flow*sc,16);n.x0=x;n.x1=x+NW;n.y0=y;n.y1=y+h;y+=h+NP;});
  });
  Object.values(nm).forEach(n=>{n.sL.sort((a,b)=>a.tgt.y0-b.tgt.y0);n.tL.sort((a,b)=>a.src.y0-b.src.y0);});
  built.forEach(l=>{
    const s=l.src,t=l.tgt;
    const sO=s.sL.reduce((a,x)=>a+x.v,0),tI=t.tL.reduce((a,x)=>a+x.v,0);
    const sB=s.sL.slice(0,s.sL.indexOf(l)).reduce((a,x)=>a+x.v,0);
    const tB=t.tL.slice(0,t.tL.indexOf(l)).reduce((a,x)=>a+x.v,0);
    const sH=s.y1-s.y0,tH=t.y1-t.y0;
    l.sw=(l.v/Math.max(sO,1))*sH;l.tw=(l.v/Math.max(tI,1))*tH;
    l.sy0=s.y0+(sB/Math.max(sO,1))*sH;l.sy1=l.sy0+l.sw;
    l.ty0=t.y0+(tB/Math.max(tI,1))*tH;l.ty1=l.ty0+l.tw;
  });
  return {nodes:Object.values(nm),links:built,cW,NW,nc,PAD};
}
function bandPath(l){const sx=l.src.x1,tx=l.tgt.x0,mx=(sx+tx)/2;
  return`M${sx},${l.sy0}C${mx},${l.sy0} ${mx},${l.ty0} ${tx},${l.ty0}L${tx},${l.ty1}C${mx},${l.ty1} ${mx},${l.sy1} ${sx},${l.sy1}Z`;}

// ═══════════════════════════════════════════════════════════════
// Dropdown Component
// ═══════════════════════════════════════════════════════════════
function Select({label,options,value,onChange,placeholder,required,grouped}) {
  const [open,setOpen]=useState(false);
  const [search,setSearch]=useState("");
  const ref=useRef(null);
  useEffect(()=>{const h=e=>{if(ref.current&&!ref.current.contains(e.target))setOpen(false)};
    document.addEventListener("mousedown",h);return()=>document.removeEventListener("mousedown",h)},[]);
  const filtered=options.filter(o=>!o.isGroup&&o.label.toLowerCase().includes(search.toLowerCase()));
  const display=grouped?options.filter(o=>o.isGroup||filtered.includes(o)):filtered;
  return(
    <div ref={ref} style={{marginBottom:16,position:"relative"}}>
      {label&&<label style={{display:"block",fontSize:12,fontWeight:600,color:T.textMut,marginBottom:6,fontFamily:T.sans,textTransform:"uppercase",letterSpacing:.5}}>
        {label}{required&&<span style={{color:T.danger,marginLeft:4}}>*</span>}
      </label>}
      <div onClick={()=>setOpen(!open)} style={{
        background:T.bgInput,border:`1px solid ${open?T.accentBdr:T.border}`,borderRadius:9,padding:"10px 14px",
        cursor:"pointer",display:"flex",justifyContent:"space-between",alignItems:"center",transition:"border-color .2s",
      }}>
        <span style={{fontSize:14,color:value?T.text:T.textDim,fontFamily:T.sans}}>{value?.label||placeholder||"Select..."}</span>
        <span style={{color:T.textDim,fontSize:10,transform:open?"rotate(180deg)":"",transition:"transform .2s"}}>▼</span>
      </div>
      {open&&(
        <div style={{position:"absolute",top:"100%",left:0,right:0,marginTop:4,background:T.bgCard,border:`1px solid ${T.border}`,
          borderRadius:12,boxShadow:"0 12px 40px rgba(0,0,0,.4)",zIndex:50,maxHeight:280,overflowY:"auto",overflowX:"hidden"}}>
          <div style={{padding:"8px 10px",borderBottom:`1px solid ${T.border}`}}>
            <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search..." autoFocus
              style={{width:"100%",background:T.bgInput,border:`1px solid ${T.border}`,borderRadius:6,padding:"8px 10px",
                fontSize:13,color:T.text,fontFamily:T.sans,outline:"none"}}/>
          </div>
          {display.map((o,i)=>o.isGroup?(
            <div key={`g${i}`} style={{padding:"10px 14px 4px",fontSize:10,fontWeight:600,color:T.textDim,textTransform:"uppercase",
              letterSpacing:.8,borderTop:i>0?`1px solid ${T.border}`:"none",fontFamily:T.sans}}>{o.label}</div>
          ):(
            <div key={o.value} onClick={()=>{onChange(o);setOpen(false);setSearch("")}}
              style={{padding:"9px 14px",fontSize:13,color:value?.value===o.value?T.accent:T.textSec,cursor:"pointer",
                fontFamily:T.sans,display:"flex",justifyContent:"space-between",alignItems:"center",
                background:value?.value===o.value?T.accentDim:"transparent",transition:"background .15s"}}
              onMouseEnter={e=>e.currentTarget.style.background=T.bgHover}
              onMouseLeave={e=>e.currentTarget.style.background=value?.value===o.value?T.accentDim:"transparent"}>
              <span>{o.label}</span>
              {value?.value===o.value&&<span style={{color:T.accent,fontSize:14}}>✓</span>}
            </div>
          ))}
          {display.filter(o=>!o.isGroup).length===0&&(
            <div style={{padding:16,textAlign:"center",fontSize:13,color:T.textDim}}>No results</div>
          )}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// Detail Panel
// ═══════════════════════════════════════════════════════════════
function Panel({item}) {
  if(!item) return(<div style={{display:"flex",alignItems:"center",justifyContent:"center",padding:28,minHeight:80}}>
    <p style={{fontFamily:T.sans,fontSize:14,color:T.textDim,textAlign:"center",margin:0}}>Hover over any path or milestone to explore · Click to lock</p></div>);
  const d=item.detail;if(!d) return null;
  const c=item._lk?COL[item.src?.type]||T.accent:COL[item.type]||T.accent;
  return(<div style={{padding:"20px 24px",animation:"sf .2s ease"}}>
    <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:8,flexWrap:"wrap"}}>
      <h3 style={{fontFamily:T.serif,fontSize:20,color:T.text,margin:0}}>{d.title}</h3>
      <span style={{fontSize:10,fontFamily:T.sans,fontWeight:600,background:c+"22",color:c,border:`1px solid ${c}44`,borderRadius:20,padding:"2px 10px"}}>{item._lk?"Path":(item.type||"").replace(/_/g," ")}</span>
    </div>
    {d.desc&&<p style={{fontFamily:T.sans,fontSize:14,color:T.textSec,margin:"0 0 14px",lineHeight:1.55}}>{d.desc}</p>}
    {d.attrs&&<div style={{display:"flex",flexWrap:"wrap",gap:8}}>{d.attrs.map((a,i)=>(
      <div key={i} style={{background:T.bgInput,border:`1px solid ${T.borderL}`,borderRadius:9,padding:"7px 14px"}}>
        <div style={{fontSize:10,color:T.textDim,textTransform:"uppercase",letterSpacing:.5,marginBottom:2,fontFamily:T.sans}}>{a.k}</div>
        <div style={{fontSize:13,color:T.text,fontWeight:600,fontFamily:T.sans}}>{a.v}</div>
      </div>))}</div>}
  </div>);
}

// ═══════════════════════════════════════════════════════════════
// Role Progression Cards
// ═══════════════════════════════════════════════════════════════
function ProgressionCards({cards}) {
  const groups = [
    {label:"Entry Roles", type:"entry_role", items: cards.filter(c=>c.type==="entry_role")},
    {label:"Mid-Level Roles", type:"mid_role", items: cards.filter(c=>c.type==="mid_role")},
    {label:"Target Roles", type:"target_role", items: cards.filter(c=>c.type==="target_role"||c.type==="stretch_role")},
  ].filter(g=>g.items.length>0);

  return(
    <div>
      {groups.map((g,gi)=>(
        <div key={gi} style={{marginBottom:32}}>
          <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:16}}>
            <div style={{width:4,height:20,borderRadius:2,background:COL[g.type]||T.accent}}/>
            <h3 style={{fontFamily:T.serif,fontSize:20,color:T.text,margin:0}}>{g.label}</h3>
          </div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(300px,1fr))",gap:16}}>
            {g.items.map(card=>{
              const c=COL[card.type]||T.accent;
              const d=card.detail;
              return(
                <div key={card.id} style={{background:T.bgCard,border:`1px solid ${T.border}`,borderRadius:12,overflow:"hidden",transition:"border-color .2s"}}
                  onMouseEnter={e=>e.currentTarget.style.borderColor=c+"55"}
                  onMouseLeave={e=>e.currentTarget.style.borderColor=T.border}>
                  {/* Color strip */}
                  <div style={{height:4,background:`linear-gradient(90deg,${c},${c}88)`}}/>
                  <div style={{padding:"20px 20px 16px"}}>
                    {/* Header */}
                    <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:10}}>
                      <div>
                        <h4 style={{fontFamily:T.sans,fontSize:16,fontWeight:700,color:T.text,margin:"0 0 4px"}}>{card.label}</h4>
                        <span style={{fontSize:10,fontFamily:T.sans,fontWeight:600,background:COL_DIM[card.type]||T.accentDim,color:c,borderRadius:20,padding:"2px 10px",textTransform:"uppercase",letterSpacing:.5}}>
                          {(card.type||"").replace(/_/g," ")}
                        </span>
                      </div>
                      {d?.attrs?.find(a=>a.k==="Salary")&&(
                        <div style={{textAlign:"right"}}>
                          <div style={{fontSize:10,color:T.textDim,textTransform:"uppercase",letterSpacing:.5,fontFamily:T.sans}}>Salary</div>
                          <div style={{fontSize:15,fontWeight:700,color:c,fontFamily:T.mono}}>{d.attrs.find(a=>a.k==="Salary").v}</div>
                        </div>
                      )}
                    </div>
                    {/* Description */}
                    {d?.desc&&<p style={{fontSize:13,color:T.textSec,lineHeight:1.5,margin:"0 0 14px",fontFamily:T.sans}}>{d.desc}</p>}
                    {/* Attributes */}
                    <div style={{display:"flex",flexWrap:"wrap",gap:6,marginBottom:14}}>
                      {(d?.attrs||[]).filter(a=>a.k!=="Salary").map((a,i)=>(
                        <div key={i} style={{background:T.bgInput,borderRadius:6,padding:"5px 10px",fontSize:11,fontFamily:T.sans}}>
                          <span style={{color:T.textDim}}>{a.k}: </span><span style={{color:T.text,fontWeight:600}}>{a.v}</span>
                        </div>
                      ))}
                    </div>
                    {/* Prerequisites — color-coded by type */}
                    {(card.prereqs?.length>0 || card.directRolePrereqs?.length>0)&&(
                      <div style={{marginBottom:10}}>
                        <div style={{fontSize:10,color:T.textDim,textTransform:"uppercase",letterSpacing:.5,marginBottom:6,fontFamily:T.sans}}>Prerequisites</div>
                        <div style={{display:"flex",flexWrap:"wrap",gap:4}}>
                          {/* Credential prereqs (certs, degrees, skillbridge) — color coded */}
                          {(card.prereqs||[]).map((p,i)=>{
                            const color = COL[p.type] || T.textSec;
                            const dimBg = COL_DIM[p.type] || T.bgElev;
                            const typeIcon = p.type === "certification" ? "📜 " : p.type === "education" ? "🎓 " : p.type === "skillbridge" ? "🔗 " : "";
                            return(
                              <span key={`cred-${i}`} style={{fontSize:11,background:dimBg,color:color,borderRadius:6,padding:"3px 8px",fontFamily:T.sans,fontWeight:500,border:`1px solid ${color}25`}}>
                                {typeIcon}{p.label}
                              </span>
                            );
                          })}
                          {/* Direct role prereqs (roles that feed into this one) */}
                          {(card.directRolePrereqs||[]).map((p,i)=>{
                            const color = COL[p.type] || T.orange;
                            const dimBg = COL_DIM[p.type] || T.orangeDim;
                            return(
                              <span key={`role-${i}`} style={{fontSize:11,background:dimBg,color:color,borderRadius:6,padding:"3px 8px",fontFamily:T.sans,fontWeight:500,border:`1px solid ${color}25`}}>
                                ← {p.label}
                              </span>
                            );
                          })}
                        </div>
                      </div>
                    )}
                    {/* Next roles */}
                    {card.nextRoles?.length>0&&(
                      <div>
                        <div style={{fontSize:10,color:T.textDim,textTransform:"uppercase",letterSpacing:.5,marginBottom:6,fontFamily:T.sans}}>Progresses to</div>
                        <div style={{display:"flex",flexWrap:"wrap",gap:4}}>
                          {card.nextRoles.map((r,i)=>(
                            <span key={i} style={{fontSize:11,background:T.accentDim,color:T.accent,borderRadius:6,padding:"3px 8px",fontFamily:T.sans,fontWeight:500}}>→ {r}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// Main Page Component
// ═══════════════════════════════════════════════════════════════
export default function CareerPathfinderPage() {
  // Form state
  const [role, setRole] = useState(null);
  const [education, setEducation] = useState(null);
  const [years, setYears] = useState(null);
  const [targetRole, setTargetRole] = useState(null);
  const [industry, setIndustry] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [generated, setGenerated] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [roadmap, setRoadmap] = useState(null);
  const [viewMode, setViewMode] = useState("sankey"); // "sankey" | "cards"

  // Sankey state
  const cRef = useRef(null);
  const [W, setW] = useState(1100);
  const H = 680;
  const [hov, setHov] = useState(null);
  const [lock, setLock] = useState(null);
  const active = lock || hov;

  useEffect(()=>{const m=()=>{if(cRef.current)setW(Math.max(cRef.current.clientWidth,800))};
    m();window.addEventListener("resize",m);return()=>window.removeEventListener("resize",m)},[]);

  const G = useMemo(()=>roadmap?buildLayout(roadmap.nodes,roadmap.links,W,H):null,[roadmap,W]);

  const {cN,cL}=useMemo(()=>{
    if(!active||!G)return{cN:null,cL:null};
    const ns=new Set(),ls=new Set();
    if(active.type==="link"){const lk=active.data;ls.add(lk.i);ns.add(lk.tgt.id);
      const wu=id=>{if(ns.has(id))return;ns.add(id);G.links.forEach(l=>{if(l.tgt.id===id){ls.add(l.i);wu(l.src.id)}})};wu(lk.src.id);
    }else{
      const wu=id=>{if(ns.has(id))return;ns.add(id);G.links.forEach(l=>{if(l.tgt.id===id){ls.add(l.i);wu(l.src.id)}})};wu(active.id);
      G.links.forEach(l=>{if(l.src.id===active.id){ls.add(l.i);ns.add(l.tgt.id)}});
    }
    return{cN:ns,cL:ls};
  },[active,G]);

  const nO=n=>!cN?.92:cN.has(n.id)?1:.08;
  const lO=l=>!cL?.18:cL.has(l.i)?.55:.03;

  const clk=(type,data)=>{const id=type==="link"?`l${data.i}`:data.id;if(lock?.id===id)setLock(null);else setLock({type,id,data})};

  const handleGenerate = () => {
    setGenerating(true);
    setTimeout(()=>{
      const data = generateRoadmap({role,education,years,targetRole,industry,timeline});
      setRoadmap(data);
      setGenerated(true);
      setGenerating(false);
      setLock(null);setHov(null);
    }, 1200);
  };

  const canGenerate = role && education && years && targetRole && timeline;

  // Dropdown options
  const roleOptions = [
    {isGroup:true,label:"Army"},{value:"11B",label:"11B — Infantry"},{value:"25B",label:"25B — IT Specialist"},
    {value:"68W",label:"68W — Combat Medic"},{value:"35F",label:"35F — Intelligence Analyst"},
    {value:"12B",label:"12B — Combat Engineer"},{value:"42A",label:"42A — Human Resources"},
    {isGroup:true,label:"Marines"},{value:"0311",label:"0311 — Rifleman"},{value:"0621",label:"0621 — Radio Operator"},
    {isGroup:true,label:"Navy"},{value:"IT",label:"IT — Info Technology"},{value:"HM",label:"HM — Hospital Corpsman"},
    {isGroup:true,label:"Air Force"},{value:"3D0X2",label:"3D0X2 — Cyber Systems"},{value:"1N0X1",label:"1N0X1 — All Source Intel"},
    {isGroup:true,label:"Civilian"},{value:"civ-pm",label:"Project Manager"},{value:"civ-it",label:"IT Support Specialist"},
    {value:"civ-analyst",label:"Business Analyst"},{value:"civ-admin",label:"Administrative Specialist"},
  ];
  const eduOptions = [
    {value:"no_degree",label:"No formal degree"},{value:"high_school",label:"High school / GED"},
    {value:"some_college",label:"Some college (no degree)"},{value:"associate",label:"Associate degree"},
    {value:"bachelors",label:"Bachelor's degree"},{value:"masters",label:"Master's degree"},
    {value:"doctorate",label:"Doctorate"},{value:"trade",label:"Trade school / Technical certificate"},
  ];
  const yearsOptions = [
    {value:"lt1",label:"Less than 1 year"},{value:"1_3",label:"1–3 years"},{value:"4_6",label:"4–6 years"},
    {value:"7_10",label:"7–10 years"},{value:"11_15",label:"11–15 years"},{value:"16_20",label:"16–20 years"},
    {value:"20plus",label:"20+ years"},
  ];
  const targetOptions = [
    {isGroup:true,label:"Technology"},{value:"cyber-analyst",label:"Cybersecurity Analyst"},{value:"sw-dev",label:"Software Developer"},
    {value:"cloud-eng",label:"Cloud Engineer"},{value:"data-analyst",label:"Data Analyst"},{value:"net-admin",label:"Network Administrator"},
    {isGroup:true,label:"Business / Finance"},{value:"fin-analyst",label:"Financial Analyst"},{value:"ops-mgr",label:"Operations Manager"},
    {isGroup:true,label:"Healthcare"},{value:"health-admin",label:"Healthcare Administrator"},{value:"med-tech",label:"Medical Equipment Technician"},
    {isGroup:true,label:"Government"},{value:"fed-pm",label:"Federal Program Manager"},{value:"intel-analyst",label:"Intelligence Analyst"},
    {isGroup:true,label:"Trades"},{value:"electrician",label:"Electrician"},{value:"hvac",label:"HVAC Technician"},
  ];
  const industryOptions = [
    {value:"technology",label:"Technology"},{value:"healthcare",label:"Healthcare"},
    {value:"finance",label:"Business / Finance"},{value:"government",label:"Government / Public Sector"},
    {value:"trades",label:"Trades / Construction"},{value:"logistics",label:"Logistics / Operations"},
  ];
  const timelineOptions = [
    {value:"12plus",label:"12+ months out (Planning ahead)"},{value:"6_12",label:"6–12 months (Actively preparing)"},
    {value:"3_6",label:"3–6 months (Transitioning soon)"},{value:"separated",label:"Already separated"},
    {value:"exploring",label:"Just exploring"},
  ];

  const colXs = G ? Object.fromEntries(Array.from({length:G.nc},(_,c)=>[c,G.PAD.l+c*G.cW+G.NW/2])) : {};
  const CL=["Starting\nPoint","Credentials","Advanced /\nBridge","Entry\nRoles","Mid-Level","Target\nRoles"];

  return (
    <div style={{background:T.bg,minHeight:"100vh",fontFamily:T.sans,color:T.textSec}}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&family=JetBrains+Mono:wght@400;500&display=swap');
        @keyframes sf{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
        @keyframes spin{to{transform:rotate(360deg)}}
        .sl{transition:opacity .3s ease;cursor:pointer}.sn{transition:opacity .3s ease;cursor:pointer}.st{pointer-events:none;transition:opacity .3s ease}
        *{scrollbar-width:thin;scrollbar-color:${T.border} transparent}
      `}</style>

      {/* ═══ HERO ═══ */}
      <div style={{background:`linear-gradient(160deg,${T.bgCard},${T.bg})`,borderBottom:`1px solid ${T.border}`,padding:"48px 28px 36px"}}>
        <div style={{maxWidth:1200,margin:"0 auto"}}>
          <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:12}}>
            <div style={{width:22,height:2,background:T.accent,opacity:.6}}/>
            <span style={{fontSize:11,fontWeight:500,letterSpacing:1.2,color:T.accent,textTransform:"uppercase"}}>Career Pathfinder</span>
          </div>
          <h1 style={{fontFamily:T.serif,fontSize:38,color:T.text,margin:"0 0 8px",fontWeight:400}}>
            Map your <em style={{fontStyle:"normal",color:T.accent}}>career path</em>
          </h1>
          <p style={{fontSize:15,color:T.textMut,margin:0,maxWidth:560}}>
            See every route from where you are to where you want to be — roles, certifications, timelines, and salaries.
          </p>
        </div>
      </div>

      <div style={{maxWidth:1200,margin:"0 auto",padding:"32px 28px 80px"}}>

        {/* ═══ INPUT FORM ═══ */}
        {!generated && (
          <div style={{maxWidth:680,margin:"0 auto",animation:"sf .4s ease"}}>
            {/* WHERE YOU ARE */}
            <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:14}}>
              <div style={{width:4,height:18,borderRadius:2,background:T.accent}}/>
              <span style={{fontSize:11,fontWeight:600,letterSpacing:1,color:T.textDim,textTransform:"uppercase"}}>Where you are</span>
            </div>
            <div style={{background:T.bgCard,border:`1px solid ${T.border}`,borderRadius:12,padding:"24px 24px 8px",marginBottom:28}}>
              <Select label="Current Role or MOS" options={roleOptions} value={role} onChange={setRole} placeholder="Select or search MOS / job title..." required grouped/>
              <Select label="Highest Education" options={eduOptions} value={education} onChange={setEducation} placeholder="Select education level..." required/>
              <Select label="Years in Current Role / MOS" options={yearsOptions} value={years} onChange={setYears} placeholder="Select range..." required/>
            </div>

            {/* WHERE YOU WANT TO GO */}
            <div style={{display:"flex",alignItems:"center",gap:8,marginBottom:14}}>
              <div style={{width:4,height:18,borderRadius:2,background:T.copper}}/>
              <span style={{fontSize:11,fontWeight:600,letterSpacing:1,color:T.textDim,textTransform:"uppercase"}}>Where you want to go</span>
            </div>
            <div style={{background:T.bgCard,border:`1px solid ${T.border}`,borderRadius:12,padding:"24px 24px 8px",marginBottom:28}}>
              <Select label="Target Role" options={targetOptions} value={targetRole} onChange={setTargetRole} placeholder="Select target career..." required grouped/>
              <Select label="Target Industry" options={industryOptions} value={industry} onChange={setIndustry} placeholder="Select industry..."/>
              <Select label="Separation Timeline" options={timelineOptions} value={timeline} onChange={setTimeline} placeholder="How far out are you?" required/>
            </div>

            {/* GENERATE */}
            <button onClick={handleGenerate} disabled={!canGenerate||generating}
              style={{width:"100%",maxWidth:400,margin:"0 auto",display:"flex",alignItems:"center",justifyContent:"center",gap:10,
                padding:"14px 28px",borderRadius:9,border:"none",cursor:canGenerate&&!generating?"pointer":"not-allowed",
                background:canGenerate?T.accent:T.bgHover,color:canGenerate?"#0F1214":T.textDim,
                fontSize:15,fontWeight:700,fontFamily:T.sans,transition:"all .2s",opacity:generating?.7:1}}>
              {generating&&<div style={{width:16,height:16,border:`2px solid ${T.bg}`,borderTopColor:"transparent",borderRadius:"50%",animation:"spin .6s linear infinite"}}/>}
              {generating?"Generating your career map...":"Generate Career Map →"}
            </button>
            <p style={{textAlign:"center",fontSize:12,color:T.textDim,marginTop:12,fontFamily:T.sans}}>
              We'll map every path from your background to your target career.
            </p>
          </div>
        )}

        {/* ═══ RESULTS ═══ */}
        {generated && roadmap && (
          <div style={{animation:"sf .4s ease"}}>
            {/* Results Header */}
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",flexWrap:"wrap",gap:16,marginBottom:24}}>
              <div>
                <h2 style={{fontFamily:T.serif,fontSize:26,color:T.text,margin:"0 0 4px"}}>{roadmap.title}</h2>
                <p style={{fontSize:13,color:T.textMut,margin:0}}>{roadmap.cards.length} roles mapped · {roadmap.links.length} connections</p>
              </div>
              <div style={{display:"flex",gap:10}}>
                <button onClick={()=>setGenerated(false)}
                  style={{padding:"8px 16px",borderRadius:9,border:`1px solid ${T.border}`,background:"transparent",color:T.textSec,fontSize:13,fontFamily:T.sans,cursor:"pointer"}}>
                  ← Edit Inputs
                </button>
                <button style={{padding:"8px 16px",borderRadius:9,border:"none",background:T.accent,color:T.bg,fontSize:13,fontWeight:600,fontFamily:T.sans,cursor:"pointer"}}>
                  Save to Dashboard
                </button>
              </div>
            </div>

            {/* View Toggle */}
            <div style={{display:"flex",gap:4,background:T.bgCard,border:`1px solid ${T.border}`,borderRadius:9,padding:4,marginBottom:20,width:"fit-content"}}>
              {[{k:"sankey",l:"Career Map"},{k:"cards",l:"Role Cards"}].map(v=>(
                <button key={v.k} onClick={()=>setViewMode(v.k)}
                  style={{padding:"8px 20px",borderRadius:7,border:"none",cursor:"pointer",fontSize:13,fontWeight:600,fontFamily:T.sans,
                    background:viewMode===v.k?T.accent:"transparent",color:viewMode===v.k?T.bg:T.textMut,transition:"all .2s"}}>
                  {v.l}
                </button>
              ))}
            </div>

            {/* ═══ SANKEY VIEW ═══ */}
            {viewMode==="sankey" && G && (
              <div ref={cRef}>
                <div style={{overflowX:"auto",borderRadius:12,border:`1px solid ${T.border}`,background:T.bgCard}}>
                  <svg width={W} height={H+40} style={{display:"block"}} onClick={e=>{if(e.target.tagName==="svg")setLock(null)}}>
                    <defs>{G.links.map(l=>(
                      <linearGradient key={`g${l.i}`} id={`sg${l.i}`} gradientUnits="userSpaceOnUse" x1={l.src.x1} x2={l.tgt.x0}>
                        <stop offset="0%" stopColor={COL[l.src.type]||T.accent}/><stop offset="100%" stopColor={COL[l.tgt.type]||T.accent}/>
                      </linearGradient>))}</defs>
                    {/* Columns */}
                    {CL.map((lb,ci)=>{const lines=lb.split("\n");return colXs[ci]!=null?(
                      <text key={`c${ci}`} x={colXs[ci]} y={16} textAnchor="middle" fontFamily={T.sans} fontSize={10} fill={T.textDim} fontWeight={500}
                        style={{letterSpacing:.6,textTransform:"uppercase"}}>{lines.map((ln,li)=><tspan key={li} x={colXs[ci]} dy={li===0?0:12}>{ln}</tspan>)}</text>
                    ):null})}
                    {Object.values(colXs).map((x,i)=><line key={`d${i}`} x1={x} y1={32} x2={x} y2={H+10} stroke={T.border} strokeWidth={1} strokeDasharray="3 5" opacity={.3}/>)}
                    {/* Links */}
                    <g>{G.links.map(l=><path key={`lk${l.i}`} className="sl" d={bandPath(l)} fill={`url(#sg${l.i})`} stroke="none" opacity={lO(l)}
                      onMouseEnter={()=>setHov({type:"link",id:`l${l.i}`,data:{...l,_lk:true}})} onMouseLeave={()=>setHov(null)}
                      onClick={()=>clk("link",{...l,_lk:true})}/>)}</g>
                    {/* Nodes */}
                    <g>{G.nodes.map(n=>{const c=COL[n.type]||T.accent;const h=n.y1-n.y0;const my=n.y0+h/2;const op=nO(n);
                      const last=n.col===G.nc-1;const lx=last?n.x0-8:n.x1+8;const anc=last?"end":"start";
                      return(<g key={n.id} className="sn" opacity={op} onMouseEnter={()=>setHov({type:"node",id:n.id,data:n})} onMouseLeave={()=>setHov(null)} onClick={()=>clk("node",n)}>
                        <rect x={n.x0} y={n.y0} width={G.NW} height={h} rx={2} ry={2} fill={c} stroke={lock?.id===n.id?T.text:"none"} strokeWidth={lock?.id===n.id?2:0}/>
                        <text className="st" x={lx} y={my} textAnchor={anc} dominantBaseline="central" fontFamily={T.sans} fontSize={11.5} fontWeight={600} fill={T.text} fillOpacity={op<.5?.15:.9}>{n.label}</text>
                        {n.type.includes("role")&&n.detail?.attrs?.[0]&&(
                          <text className="st" x={lx} y={my+15} textAnchor={anc} dominantBaseline="central" fontFamily={T.mono} fontSize={9.5} fill={c} fillOpacity={op<.5?.1:.65}>{n.detail.attrs[0].v}</text>)}
                      </g>)})}</g>
                  </svg>
                </div>
                {/* Legend */}
                <div style={{display:"flex",flexWrap:"wrap",gap:16,marginTop:14,justifyContent:"center"}}>
                  {[{t:"origin",l:"You"},{t:"certification",l:"Certification"},{t:"education",l:"Degree"},{t:"skillbridge",l:"SkillBridge"},
                    {t:"entry_role",l:"Entry Role"},{t:"mid_role",l:"Mid-Level"},{t:"target_role",l:"Target"},{t:"stretch_role",l:"Stretch"}].map(x=>(
                    <div key={x.t} style={{display:"flex",alignItems:"center",gap:6}}>
                      <div style={{width:10,height:10,borderRadius:2,background:COL[x.t]}}/>
                      <span style={{fontSize:11,color:T.textMut}}>{x.l}</span></div>))}
                </div>
                {/* Detail Panel */}
                <div style={{marginTop:16,background:T.bgCard,border:`1px solid ${T.border}`,borderRadius:12}}>
                  <Panel item={active?.data}/>
                </div>
              </div>
            )}

            {/* ═══ CARD VIEW ═══ */}
            {viewMode==="cards" && (
              <div style={{animation:"sf .3s ease"}}>
                <ProgressionCards cards={roadmap.cards}/>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
