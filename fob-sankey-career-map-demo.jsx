import { useState, useEffect, useRef, useMemo } from "react";

const T = {
  bg:"#0F1214",bgCard:"#171B1E",bgInput:"#1E2326",bgHover:"#252A2E",bgElev:"#2A2F34",
  text:"#F0EDEA",textSec:"#C5CCD0",textMut:"#8A9399",textDim:"#566069",
  accent:"#3ECF8E",accentH:"#35B87D",accentDim:"rgba(62,207,142,0.15)",
  copper:"#C8956A",info:"#60A5FA",warn:"#F5A623",danger:"#EF4444",
  purple:"#A855F7",orange:"#E08A52",
  border:"#252A2E",borderL:"#2F353A",
  serif:"'DM Serif Display',Georgia,serif",
  sans:"'DM Sans',system-ui,sans-serif",
  mono:"'JetBrains Mono',monospace",
};
const COL={origin:T.accent,certification:T.info,education:T.purple,skillbridge:T.copper,
  bootcamp:T.warn,entry_role:T.orange,mid_role:"#E0A552",target_role:T.accent,stretch_role:T.accentH};

// ═══════════════════════════════════════════════════════════════
// Data
// ═══════════════════════════════════════════════════════════════
const NODES=[
  {id:"origin",label:"25B IT Specialist",col:0,type:"origin",detail:{title:"Your Starting Point",desc:"Army 25B — IT Specialist, 4 yrs, CompTIA A+, Secret clearance.",attrs:[{k:"MOS",v:"25B"},{k:"Exp",v:"4 years"},{k:"Certs",v:"CompTIA A+"},{k:"Clearance",v:"Secret"}]}},
  {id:"sec-plus",label:"Security+",col:1,type:"certification",detail:{title:"CompTIA Security+",desc:"DoD 8570 baseline — unlocks all gov/contractor cyber roles.",attrs:[{k:"Study",v:"2–3 mo"},{k:"Cost",v:"$404"}]}},
  {id:"net-plus",label:"Network+",col:1,type:"certification",detail:{title:"CompTIA Network+",desc:"Networking fundamentals. Complements A+ for infrastructure.",attrs:[{k:"Study",v:"1–2 mo"},{k:"Cost",v:"$369"}]}},
  {id:"aws-clp",label:"AWS Cloud Practitioner",col:1,type:"certification",detail:{title:"AWS Cloud Practitioner",desc:"Cloud foundations — fastest entry to highest-paying track.",attrs:[{k:"Study",v:"1–2 mo"},{k:"Cost",v:"$100"}]}},
  {id:"ccna",label:"Cisco CCNA",col:1,type:"certification",detail:{title:"Cisco CCNA",desc:"Gold standard for networking. Premium over Network+.",attrs:[{k:"Study",v:"3–4 mo"},{k:"Cost",v:"$330"}]}},
  {id:"bs-it",label:"BS Info Technology",col:1,type:"education",detail:{title:"BS in IT",desc:"Opens management track. GI Bill covered.",attrs:[{k:"Duration",v:"2–3 yr"},{k:"Cost",v:"GI Bill"}]}},
  {id:"cysa",label:"CySA+",col:2,type:"certification",detail:{title:"CompTIA CySA+",desc:"Analyst-level cert for SOC and cyber analyst roles.",attrs:[{k:"Study",v:"2–4 mo"},{k:"Cost",v:"$404"}]}},
  {id:"sb-msft",label:"SkillBridge: Microsoft",col:2,type:"skillbridge",detail:{title:"Microsoft MSSA",desc:"180-day SkillBridge — cloud admin + cyber tracks. ~40% convert.",attrs:[{k:"Duration",v:"180 days"},{k:"Conversion",v:"~40%"}]}},
  {id:"aws-saa",label:"AWS Solutions Architect",col:2,type:"certification",detail:{title:"AWS SAA",desc:"Most in-demand cloud cert. +$30K salary bump.",attrs:[{k:"Study",v:"2–3 mo"},{k:"Cost",v:"$150"}]}},
  {id:"bs-cyber",label:"BS Cybersecurity",col:2,type:"education",detail:{title:"BS Cybersecurity",desc:"Specialized degree. WGU bundles certs in curriculum.",attrs:[{k:"Duration",v:"2–3 yr"},{k:"Cost",v:"GI Bill"}]}},
  {id:"helpdesk",label:"Help Desk Tier II",col:3,type:"entry_role",detail:{title:"Help Desk Tier II",desc:"Immediate hire with A+ and 25B experience.",attrs:[{k:"Salary",v:"$48K–$62K"},{k:"When",v:"Day 1"}]}},
  {id:"sysadmin",label:"Systems Administrator",col:3,type:"entry_role",detail:{title:"Systems Administrator",desc:"Manages servers and infrastructure. Core IT role.",attrs:[{k:"Salary",v:"$60K–$80K"},{k:"When",v:"Month 2–4"}]}},
  {id:"soc",label:"SOC Analyst",col:3,type:"entry_role",detail:{title:"SOC Analyst",desc:"Frontline cybersecurity monitoring and incident response.",attrs:[{k:"Salary",v:"$58K–$78K"},{k:"When",v:"Month 3–6"}]}},
  {id:"cloud-ops",label:"Cloud Support Engineer",col:3,type:"entry_role",detail:{title:"Cloud Support",desc:"Entry cloud role — troubleshooting cloud infrastructure.",attrs:[{k:"Salary",v:"$55K–$72K"},{k:"When",v:"Month 2–4"}]}},
  {id:"net-eng",label:"Network Engineer",col:4,type:"mid_role",detail:{title:"Network Engineer",desc:"Designs and maintains network infrastructure.",attrs:[{k:"Salary",v:"$75K–$100K"},{k:"When",v:"Year 1–2"}]}},
  {id:"cyber-analyst",label:"Cybersecurity Analyst",col:4,type:"mid_role",detail:{title:"Cybersecurity Analyst",desc:"Proactive threat analysis. Core cyber career ladder.",attrs:[{k:"Salary",v:"$80K–$115K"},{k:"When",v:"Year 1–2"}]}},
  {id:"cloud-eng",label:"Cloud Engineer",col:4,type:"mid_role",detail:{title:"Cloud Engineer",desc:"Builds cloud infrastructure. Highest-growth track.",attrs:[{k:"Salary",v:"$90K–$130K"},{k:"When",v:"Year 1–2"}]}},
  {id:"it-mgr",label:"IT Manager",col:5,type:"target_role",detail:{title:"IT Manager",desc:"Leads IT teams. Military leadership is key differentiator.",attrs:[{k:"Salary",v:"$95K–$135K"},{k:"When",v:"Year 3–5"}]}},
  {id:"sec-eng",label:"Security Engineer",col:5,type:"target_role",detail:{title:"Security Engineer",desc:"Top technical cyber role before CISO.",attrs:[{k:"Salary",v:"$115K–$165K"},{k:"When",v:"Year 3–5"}]}},
  {id:"sol-arch",label:"Solutions Architect",col:5,type:"stretch_role",detail:{title:"Solutions Architect",desc:"Top of the cloud career ladder.",attrs:[{k:"Salary",v:"$130K–$185K"},{k:"When",v:"Year 4–6"}]}},
];

const LINKS=[
  {s:"origin",t:"sec-plus",v:30,detail:{title:"Cybersecurity Track",desc:"Security+ is the gateway to all cyber roles."}},
  {s:"origin",t:"net-plus",v:18,detail:{title:"Infrastructure Track",desc:"Network+ validates 25B daily skills."}},
  {s:"origin",t:"aws-clp",v:16,detail:{title:"Cloud Track",desc:"Fastest path to highest-paying track."}},
  {s:"origin",t:"ccna",v:14,detail:{title:"Cisco Path",desc:"Gold standard for networking careers."}},
  {s:"origin",t:"bs-it",v:12,detail:{title:"Degree Path",desc:"GI Bill covers it. Credits transfer."}},
  {s:"origin",t:"helpdesk",v:10,detail:{title:"Direct Placement",desc:"Qualify for Tier II on day 1."}},
  {s:"sec-plus",t:"cysa",v:20,detail:{title:"Cert Ladder",desc:"CySA+ adds analyst-specific skills."}},
  {s:"sec-plus",t:"sb-msft",v:12,detail:{title:"SkillBridge",desc:"MSSA cyber track — 180 days paid."}},
  {s:"sec-plus",t:"bs-cyber",v:8,detail:{title:"Cyber Degree",desc:"WGU counts Security+ as credit."}},
  {s:"aws-clp",t:"aws-saa",v:14,detail:{title:"AWS Ladder",desc:"SAA is the most in-demand cloud cert."}},
  {s:"aws-clp",t:"sb-msft",v:6,detail:{title:"Cloud SkillBridge",desc:"MSSA cloud admin track."}},
  {s:"net-plus",t:"ccna",v:8,detail:{title:"Network Ladder",desc:"Net+ → CCNA natural progression."}},
  {s:"bs-it",t:"bs-cyber",v:6,detail:{title:"Degree Pivot",desc:"General IT → specialized cybersecurity."}},
  {s:"cysa",t:"soc",v:18,detail:{title:"CySA+ → SOC",desc:"Top SOC candidate with clearance."}},
  {s:"sb-msft",t:"sysadmin",v:10,detail:{title:"MSSA → SysAdmin",desc:"Graduates land sysadmin roles."}},
  {s:"sb-msft",t:"soc",v:6,detail:{title:"MSSA → SOC",desc:"Cyber track qualifies for SOC."}},
  {s:"aws-saa",t:"cloud-ops",v:12,detail:{title:"AWS → Cloud Ops",desc:"SAA + ops experience = strong candidate."}},
  {s:"ccna",t:"sysadmin",v:12,detail:{title:"CCNA → SysAdmin",desc:"Top candidates for sys/network admin."}},
  {s:"bs-cyber",t:"soc",v:6,detail:{title:"Degree → SOC",desc:"Qualifies at degree-required employers."}},
  {s:"helpdesk",t:"sysadmin",v:8,detail:{title:"Tier II → SysAdmin",desc:"6–12 mo helpdesk + certs qualifies."}},
  {s:"sysadmin",t:"net-eng",v:16,detail:{title:"SysAdmin → Net Eng",desc:"CCNA + experience opens network eng."}},
  {s:"soc",t:"cyber-analyst",v:24,detail:{title:"SOC → Cyber Analyst",desc:"1–2 yr SOC + CISSP → full analyst."}},
  {s:"cloud-ops",t:"cloud-eng",v:12,detail:{title:"Ops → Cloud Eng",desc:"SAA + 1yr → cloud engineering."}},
  {s:"net-eng",t:"it-mgr",v:12,detail:{title:"Net Eng → IT Mgr",desc:"Technical depth + military leadership."}},
  {s:"cyber-analyst",t:"sec-eng",v:18,detail:{title:"Analyst → Sec Eng",desc:"CISSP + 3yr → security engineering."}},
  {s:"cyber-analyst",t:"it-mgr",v:6,detail:{title:"Analyst → IT Mgr",desc:"BS degree pivots to management."}},
  {s:"cloud-eng",t:"sol-arch",v:12,detail:{title:"Cloud → Architect",desc:"SAP + 3yr → Solutions Architect."}},
  {s:"cloud-eng",t:"sec-eng",v:4,detail:{title:"Cloud → Security",desc:"Cloud security engineering niche."}},
];

// ═══════════════════════════════════════════════════════════════
// Layout — produces filled-band Sankey
// ═══════════════════════════════════════════════════════════════
function buildLayout(nodes, links, W, H) {
  const PAD = { t: 50, b: 30, l: 16, r: 16 };
  const NW = 10;
  const NP = 22;

  const cols = {};
  nodes.forEach(n => (cols[n.col] ??= []).push({ ...n, sL: [], tL: [] }));
  const nm = {};
  Object.values(cols).flat().forEach(n => (nm[n.id] = n));
  const nc = Math.max(...Object.keys(cols).map(Number)) + 1;
  const cW = (W - PAD.l - PAD.r - NW) / Math.max(nc - 1, 1);

  const built = links.map((l, i) => {
    const o = { ...l, i, src: nm[l.s], tgt: nm[l.t] };
    if (o.src) o.src.sL.push(o);
    if (o.tgt) o.tgt.tL.push(o);
    return o;
  }).filter(l => l.src && l.tgt);

  // Compute flows
  Object.values(nm).forEach(n => {
    n.flow = Math.max(
      n.sL.reduce((a, l) => a + l.v, 0),
      n.tL.reduce((a, l) => a + l.v, 0), 5);
  });

  // Position nodes
  Object.entries(cols).forEach(([c, ns]) => {
    const x = PAD.l + (+c) * cW;
    const totalFlow = ns.reduce((a, n) => a + n.flow, 0);
    const totalPad = Math.max(ns.length - 1, 0) * NP;
    const avail = H - PAD.t - PAD.b - totalPad;
    const scale = Math.min(avail / Math.max(totalFlow, 1), 7);
    let y = PAD.t + Math.max(0, (avail + totalPad - totalFlow * scale - totalPad) / 2);
    ns.forEach(n => {
      const h = Math.max(n.flow * scale, 16);
      n.x0 = x; n.x1 = x + NW; n.y0 = y; n.y1 = y + h;
      y += h + NP;
    });
  });

  // Compute link band positions (top edge y0, bottom edge y1 at source and target)
  // Sort links per node for consistent stacking
  Object.values(nm).forEach(n => {
    n.sL.sort((a, b) => a.tgt.y0 - b.tgt.y0);
    n.tL.sort((a, b) => a.src.y0 - b.src.y0);
  });

  built.forEach(l => {
    const s = l.src, t = l.tgt;
    const sOut = s.sL.reduce((a, x) => a + x.v, 0);
    const tIn = t.tL.reduce((a, x) => a + x.v, 0);
    const sBefore = s.sL.slice(0, s.sL.indexOf(l)).reduce((a, x) => a + x.v, 0);
    const tBefore = t.tL.slice(0, t.tL.indexOf(l)).reduce((a, x) => a + x.v, 0);
    const sH = s.y1 - s.y0;
    const tH = t.y1 - t.y0;

    // Band thickness at source and target
    l.sw = (l.v / Math.max(sOut, 1)) * sH;
    l.tw = (l.v / Math.max(tIn, 1)) * tH;

    // Top edge positions
    l.sy0 = s.y0 + (sBefore / Math.max(sOut, 1)) * sH;
    l.sy1 = l.sy0 + l.sw;
    l.ty0 = t.y0 + (tBefore / Math.max(tIn, 1)) * tH;
    l.ty1 = l.ty0 + l.tw;
  });

  return { nodes: Object.values(nm), links: built, cW, NW, nc, PAD };
}

// Generate filled band path (area between two curves)
function bandPath(l) {
  const sx = l.src.x1;
  const tx = l.tgt.x0;
  const mx = (sx + tx) / 2;
  // Top edge: source top → target top
  const top = `M${sx},${l.sy0} C${mx},${l.sy0} ${mx},${l.ty0} ${tx},${l.ty0}`;
  // Bottom edge: target bottom → source bottom (reversed)
  const bot = `L${tx},${l.ty1} C${mx},${l.ty1} ${mx},${l.sy1} ${sx},${l.sy1}`;
  return `${top} ${bot} Z`;
}

// ═══════════════════════════════════════════════════════════════
// Detail Panel
// ═══════════════════════════════════════════════════════════════
function Panel({ item }) {
  if (!item) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: 28, minHeight: 80 }}>
      <p style={{ fontFamily: T.sans, fontSize: 14, color: T.textDim, textAlign: "center", margin: 0 }}>
        Hover over any path or milestone to explore · Click to lock selection
      </p>
    </div>
  );
  const d = item.detail; if (!d) return null;
  const c = item._lk ? COL[item.src?.type] || T.accent : COL[item.type] || T.accent;
  return (
    <div style={{ padding: "20px 24px", animation: "sf .2s ease" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
        <h3 style={{ fontFamily: T.serif, fontSize: 20, color: T.text, margin: 0 }}>{d.title}</h3>
        <span style={{ fontSize: 10, fontFamily: T.sans, fontWeight: 600, background: c + "22", color: c,
          border: `1px solid ${c}44`, borderRadius: 20, padding: "2px 10px" }}>
          {item._lk ? "Path" : (item.type || "").replace(/_/g, " ")}
        </span>
      </div>
      {d.desc && <p style={{ fontFamily: T.sans, fontSize: 14, color: T.textSec, margin: "0 0 14px", lineHeight: 1.55 }}>{d.desc}</p>}
      {d.attrs && (
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {d.attrs.map((a, i) => (
            <div key={i} style={{ background: T.bgInput, border: `1px solid ${T.borderL}`, borderRadius: 9, padding: "7px 14px" }}>
              <div style={{ fontSize: 10, color: T.textDim, textTransform: "uppercase", letterSpacing: .5, marginBottom: 2, fontFamily: T.sans }}>{a.k}</div>
              <div style={{ fontSize: 13, color: T.text, fontWeight: 600, fontFamily: T.sans }}>{a.v}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// Main Component
// ═══════════════════════════════════════════════════════════════
export default function SankeyCareerMap() {
  const cRef = useRef(null);
  const [W, setW] = useState(1100);
  const H = 780;
  const [hov, setHov] = useState(null);
  const [lock, setLock] = useState(null);
  const active = lock || hov;

  useEffect(() => {
    const m = () => { if (cRef.current) setW(Math.max(cRef.current.clientWidth, 800)); };
    m(); window.addEventListener("resize", m); return () => window.removeEventListener("resize", m);
  }, []);

  const G = useMemo(() => buildLayout(NODES, LINKS, W, H), [W]);

  // Connected sets — trace FULL upstream path back to origin
  const { cN, cL } = useMemo(() => {
    if (!active) return { cN: null, cL: null };
    const nodeSet = new Set();
    const linkSet = new Set();

    if (active.type === "link") {
      // For a hovered link: trace upstream from source, and include target
      const link = active.data;
      linkSet.add(link.i);
      nodeSet.add(link.tgt.id);
      // Walk upstream from source
      const walkUp = (nodeId) => {
        if (nodeSet.has(nodeId)) return;
        nodeSet.add(nodeId);
        G.links.forEach(l => {
          if (l.tgt.id === nodeId) {
            linkSet.add(l.i);
            walkUp(l.src.id);
          }
        });
      };
      walkUp(link.src.id);
    } else {
      // For a hovered node: trace ALL upstream paths back to origin
      const walkUp = (nodeId) => {
        if (nodeSet.has(nodeId)) return;
        nodeSet.add(nodeId);
        G.links.forEach(l => {
          if (l.tgt.id === nodeId) {
            linkSet.add(l.i);
            walkUp(l.src.id);
          }
        });
      };
      walkUp(active.id);
      // Also trace one step downstream so user sees what comes next
      G.links.forEach(l => {
        if (l.src.id === active.id) {
          linkSet.add(l.i);
          nodeSet.add(l.tgt.id);
        }
      });
    }

    return { cN: nodeSet, cL: linkSet };
  }, [active, G]);

  const nO = n => !cN ? .92 : cN.has(n.id) ? 1 : .08;
  const lO = l => !cL ? .18 : cL.has(l.i) ? .55 : .03;

  const clk = (type, data) => {
    const id = type === "link" ? `l${data.i}` : data.id;
    if (lock?.id === id) setLock(null);
    else setLock({ type, id, data });
  };

  const colXs = {};
  for (let c = 0; c < G.nc; c++) colXs[c] = G.PAD.l + c * G.cW + G.NW / 2;
  const CL = ["Starting\nPoint", "Credentials", "Advanced /\nBridge", "Entry\nRoles", "Mid-Level\nRoles", "Target\nRoles"];

  return (
    <div style={{ background: T.bg, minHeight: "100vh", fontFamily: T.sans, color: T.textSec }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&family=JetBrains+Mono:wght@400;500&display=swap');
        @keyframes sf{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
        .sl{transition:opacity .3s ease;cursor:pointer}
        .sl:hover{opacity:.6!important}
        .sn{transition:opacity .3s ease;cursor:pointer}
        .st{pointer-events:none;transition:opacity .3s ease}
      `}</style>

      {/* Hero */}
      <div style={{ background: `linear-gradient(160deg,${T.bgCard},${T.bg})`, borderBottom: `1px solid ${T.border}`, padding: "40px 28px 28px" }}>
        <div style={{ maxWidth: 1400, margin: "0 auto" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
            <div style={{ width: 22, height: 2, background: T.accent, opacity: .6 }} />
            <span style={{ fontSize: 11, fontWeight: 500, letterSpacing: 1.2, color: T.accent, textTransform: "uppercase" }}>Career Map</span>
          </div>
          <h1 style={{ fontFamily: T.serif, fontSize: 34, color: T.text, margin: "0 0 6px", fontWeight: 400 }}>
            25B IT Specialist → <span style={{ color: T.accent }}>5 Career Tracks</span>
          </h1>
          <p style={{ fontSize: 14, color: T.textMut, margin: 0 }}>$48K–$185K salary range · Hover to explore paths</p>
          <div style={{ display: "flex", gap: 12, marginTop: 20, flexWrap: "wrap" }}>
            {[{ i: "⚡", l: "FASTEST", t: "Direct Placement", d: "Tier II — day 1", c: T.warn },
              { i: "💰", l: "HIGHEST CEILING", t: "Cloud → Architect", d: "$130K–$185K", c: T.accent },
              { i: "🛡️", l: "MOST IN-DEMAND", t: "Cyber Track", d: "Sec Engineer $165K", c: T.info },
              { i: "⭐", l: "RECOMMENDED", t: "SkillBridge + Certs", d: "Paid training + pipeline", c: T.copper },
            ].map((c, i) => (
              <div key={i} style={{ background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 12, padding: "12px 16px", flex: "1 1 170px", transition: "border-color .2s" }}
                onMouseEnter={e => e.currentTarget.style.borderColor = c.c + "66"}
                onMouseLeave={e => e.currentTarget.style.borderColor = T.border}>
                <div style={{ fontSize: 10, color: T.textDim, letterSpacing: .8, textTransform: "uppercase", marginBottom: 5 }}>{c.i} {c.l}</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: T.text, marginBottom: 1 }}>{c.t}</div>
                <div style={{ fontSize: 12, color: T.textMut }}>{c.d}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Diagram */}
      <div ref={cRef} style={{ maxWidth: 1400, margin: "0 auto", padding: "0 20px" }}>
        <div style={{ overflowX: "auto", marginTop: 20, borderRadius: 12, border: `1px solid ${T.border}`, background: T.bgCard }}>
          <svg width={W} height={H + 40} style={{ display: "block" }}
            onClick={e => { if (e.target.tagName === "svg") setLock(null); }}>
            <defs>
              {G.links.map(l => (
                <linearGradient key={`g${l.i}`} id={`sg${l.i}`} gradientUnits="userSpaceOnUse" x1={l.src.x1} x2={l.tgt.x0}>
                  <stop offset="0%" stopColor={COL[l.src.type] || T.accent} />
                  <stop offset="100%" stopColor={COL[l.tgt.type] || T.accent} />
                </linearGradient>
              ))}
            </defs>

            {/* Column labels */}
            {CL.map((lb, ci) => {
              const lines = lb.split("\n");
              return (
                <text key={`c${ci}`} x={colXs[ci]} y={16} textAnchor="middle"
                  fontFamily={T.sans} fontSize={10} fill={T.textDim} fontWeight={500}
                  style={{ letterSpacing: .6, textTransform: "uppercase" }}>
                  {lines.map((ln, li) => <tspan key={li} x={colXs[ci]} dy={li === 0 ? 0 : 12}>{ln}</tspan>)}
                </text>
              );
            })}

            {/* Links — FILLED BANDS (area paths, not strokes) */}
            <g>
              {G.links.map(l => (
                <path key={`lk${l.i}`} className="sl"
                  d={bandPath(l)}
                  fill={`url(#sg${l.i})`}
                  opacity={lO(l)}
                  stroke="none"
                  onMouseEnter={() => setHov({ type: "link", id: `l${l.i}`, data: { ...l, _lk: true } })}
                  onMouseLeave={() => setHov(null)}
                  onClick={() => clk("link", { ...l, _lk: true })}
                />
              ))}
            </g>

            {/* Nodes — vertical bars */}
            <g>
              {G.nodes.map(n => {
                const c = COL[n.type] || T.accent;
                const h = n.y1 - n.y0;
                const my = n.y0 + h / 2;
                const op = nO(n);
                const last = n.col === G.nc - 1;
                const lx = last ? n.x0 - 8 : n.x1 + 8;
                const anc = last ? "end" : "start";
                return (
                  <g key={n.id} className="sn" opacity={op}
                    onMouseEnter={() => setHov({ type: "node", id: n.id, data: n })}
                    onMouseLeave={() => setHov(null)}
                    onClick={() => clk("node", n)}>
                    <rect x={n.x0} y={n.y0} width={G.NW} height={h}
                      rx={2} ry={2} fill={c}
                      stroke={lock?.id === n.id ? T.text : "none"}
                      strokeWidth={lock?.id === n.id ? 2 : 0} />
                    <text className="st" x={lx} y={my}
                      textAnchor={anc} dominantBaseline="central"
                      fontFamily={T.sans} fontSize={11.5} fontWeight={600}
                      fill={T.text} fillOpacity={op < .5 ? .15 : .9}>
                      {n.label}
                    </text>
                    {n.type.includes("role") && n.detail?.attrs?.[0] && (
                      <text className="st" x={lx} y={my + 15}
                        textAnchor={anc} dominantBaseline="central"
                        fontFamily={T.mono} fontSize={9.5}
                        fill={c} fillOpacity={op < .5 ? .1 : .65}>
                        {n.detail.attrs[0].v}
                      </text>
                    )}
                  </g>
                );
              })}
            </g>
          </svg>
        </div>

        {/* Legend */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 16, marginTop: 14, justifyContent: "center" }}>
          {[{ t: "origin", l: "Starting Point" }, { t: "certification", l: "Certification" },
            { t: "education", l: "Degree" }, { t: "skillbridge", l: "SkillBridge" },
            { t: "entry_role", l: "Entry Role" }, { t: "mid_role", l: "Mid-Level" },
            { t: "target_role", l: "Target Role" }, { t: "stretch_role", l: "Stretch Goal" },
          ].map(x => (
            <div key={x.t} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{ width: 10, height: 10, borderRadius: 2, background: COL[x.t] }} />
              <span style={{ fontSize: 11, color: T.textMut }}>{x.l}</span>
            </div>
          ))}
        </div>

        {/* Detail Panel */}
        <div style={{ marginTop: 16, background: T.bgCard, border: `1px solid ${T.border}`, borderRadius: 12, marginBottom: 60 }}>
          <Panel item={active?.data} />
        </div>
      </div>
    </div>
  );
}
