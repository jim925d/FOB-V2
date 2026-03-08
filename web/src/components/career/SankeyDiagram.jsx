/**
 * Sankey diagram for Career Map — matches fob-sankey-career-map-demo.jsx.
 * Accepts API sankey shape: nodes (id, label, column, type, detail), links (source, target, value, detail).
 */
import { useState, useRef, useEffect, useMemo } from "react";
import { Card, CardContent } from "@/components/ui/card";

const COL = {
  origin: "var(--color-accent)",
  certification: "var(--color-info)",
  education: "var(--color-info)",
  skillbridge: "var(--color-copper)",
  bootcamp: "var(--color-warning)",
  entry_role: "var(--color-orange)",
  mid_role: "var(--color-warning)",
  target_role: "var(--color-accent)",
  stretch_role: "var(--color-accent)",
};

function normalizeApiSankey(apiSankey) {
  if (!apiSankey?.nodes) return { nodes: [], links: [] };
  const nodes = (apiSankey.nodes || []).map((n) => ({
    id: n.id,
    label: n.label || n.id,
    col: n.column ?? n.col ?? 0,
    type: n.type || "certification",
    detail: {
      title: n.detail?.title || n.label,
      desc: n.detail?.description ?? n.detail?.desc,
      attrs: (n.detail?.attributes || n.detail?.attrs || []).map((a) => ({
        k: a.label ?? a.k,
        v: a.value ?? a.v,
      })),
    },
  }));
  const links = (apiSankey.links || []).map((l, i) => ({
    s: l.source ?? l.s,
    t: l.target ?? l.t,
    v: l.value ?? l.v ?? 10,
    i,
    detail: l.detail
      ? {
          title: l.detail.title,
          desc: l.detail.description ?? l.detail.desc,
          attrs: (l.detail.attributes || l.detail.attrs || []).map((a) => ({
            k: a.label ?? a.k,
            v: a.value ?? a.v,
          })),
        }
      : {},
  }));
  return { nodes, links };
}

function buildLayout(nodes, links, W, H) {
  const PAD = { t: 50, b: 30, l: 16, r: 16 };
  const NW = 10;
  const NP = 22;

  const cols = {};
  nodes.forEach((n) => (cols[n.col] ??= []).push({ ...n, sL: [], tL: [] }));
  const nm = {};
  Object.values(cols)
    .flat()
    .forEach((n) => (nm[n.id] = n));
  const nc = Math.max(...Object.keys(cols).map(Number), 0) + 1;
  const cW = (W - PAD.l - PAD.r - NW) / Math.max(nc - 1, 1);

  const built = links
    .map((l, i) => {
      const o = { ...l, i, src: nm[l.s], tgt: nm[l.t] };
      if (o.src) o.src.sL.push(o);
      if (o.tgt) o.tgt.tL.push(o);
      return o;
    })
    .filter((l) => l.src && l.tgt);

  Object.values(nm).forEach((n) => {
    n.flow = Math.max(
      n.sL.reduce((a, l) => a + l.v, 0),
      n.tL.reduce((a, l) => a + l.v, 0),
      5
    );
  });

  Object.entries(cols).forEach(([c, ns]) => {
    const x = PAD.l + +c * cW;
    const totalFlow = ns.reduce((a, n) => a + n.flow, 0);
    const totalPad = Math.max(ns.length - 1, 0) * NP;
    const avail = H - PAD.t - PAD.b - totalPad;
    const scale = Math.min(avail / Math.max(totalFlow, 1), 7);
    let y =
      PAD.t +
      Math.max(0, (avail + totalPad - totalFlow * scale - totalPad) / 2);
    ns.forEach((n) => {
      const h = Math.max(n.flow * scale, 16);
      n.x0 = x;
      n.x1 = x + NW;
      n.y0 = y;
      n.y1 = y + h;
      y += h + NP;
    });
  });

  Object.values(nm).forEach((n) => {
    n.sL.sort((a, b) => a.tgt.y0 - b.tgt.y0);
    n.tL.sort((a, b) => a.src.y0 - b.src.y0);
  });

  built.forEach((l) => {
    const s = l.src;
    const t = l.tgt;
    const sBefore = s.sL
      .slice(0, s.sL.indexOf(l))
      .reduce((a, x) => a + x.v, 0);
    const tBefore = t.tL
      .slice(0, t.tL.indexOf(l))
      .reduce((a, x) => a + x.v, 0);
    const sOut = s.sL.reduce((a, x) => a + x.v, 0);
    const tIn = t.tL.reduce((a, x) => a + x.v, 0);
    const sH = s.y1 - s.y0;
    const tH = t.y1 - t.y0;
    l.sw = (l.v / Math.max(sOut, 1)) * sH;
    l.tw = (l.v / Math.max(tIn, 1)) * tH;
    l.sy0 = s.y0 + (sBefore / Math.max(sOut, 1)) * sH;
    l.sy1 = l.sy0 + l.sw;
    l.ty0 = t.y0 + (tBefore / Math.max(tIn, 1)) * tH;
    l.ty1 = l.ty0 + l.tw;
  });

  return { nodes: Object.values(nm), links: built, cW, NW, nc, PAD };
}

function bandPath(l) {
  const sx = l.src.x1;
  const tx = l.tgt.x0;
  const mx = (sx + tx) / 2;
  const top = `M${sx},${l.sy0} C${mx},${l.sy0} ${mx},${l.ty0} ${tx},${l.ty0}`;
  const bot = `L${tx},${l.ty1} C${mx},${l.ty1} ${mx},${l.sy1} ${sx},${l.sy1}`;
  return `${top} ${bot} Z`;
}

function DetailPanel({ item }) {
  if (!item)
    return (
      <div
        className="flex items-center justify-center py-7 min-h-[80px]"
        style={{ color: "var(--color-text-dim)" }}
      >
        <p className="text-sm text-center m-0">
          Hover over any path or milestone to explore · Click to lock selection
        </p>
      </div>
    );
  const d = item.detail;
  if (!d) return null;
  const typeLabel = item._lk ? "Path" : (item.type || "").replace(/_/g, " ");
  const attrs = d.attrs || [];
  return (
    <div className="p-5">
      <div className="flex items-center gap-2 mb-2">
        <h3 className="font-serif text-xl m-0" style={{ color: "var(--color-text-primary)" }}>
          {d.title}
        </h3>
        <span
          className="text-[10px] font-semibold rounded-full px-2.5 py-0.5"
          style={{
            background: "var(--color-bg-tertiary)",
            border: "1px solid var(--color-border-light)",
            color: "var(--color-text-secondary)",
          }}
        >
          {typeLabel}
        </span>
      </div>
      {d.desc && (
        <p className="text-sm mb-3 leading-relaxed" style={{ color: "var(--color-text-secondary)" }}>
          {d.desc}
        </p>
      )}
      {attrs.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {attrs.map((a, i) => (
            <div
              key={i}
              className="rounded-lg px-3 py-1.5"
              style={{
                background: "var(--color-bg-tertiary)",
                border: "1px solid var(--color-border-light)",
              }}
            >
              <div className="text-[10px] uppercase tracking-wider" style={{ color: "var(--color-text-dim)" }}>
                {a.k}
              </div>
              <div className="text-xs font-semibold" style={{ color: "var(--color-text-primary)" }}>
                {a.v}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SankeyDiagram({ sankey: apiSankey, className = "" }) {
  const cRef = useRef(null);
  const [W, setW] = useState(1000);
  const H = 720;
  const [hov, setHov] = useState(null);
  const [lock, setLock] = useState(null);
  const active = lock || hov;

  const { nodes, links } = useMemo(
    () => normalizeApiSankey(apiSankey),
    [apiSankey]
  );

  useEffect(() => {
    const m = () => {
      if (cRef.current) setW(Math.max(cRef.current.clientWidth, 600));
    };
    m();
    window.addEventListener("resize", m);
    return () => window.removeEventListener("resize", m);
  }, []);

  const G = useMemo(
    () => (nodes.length ? buildLayout(nodes, links, W, H) : null),
    [nodes, links, W]
  );

  const { cN, cL } = useMemo(() => {
    if (!active || !G) return { cN: null, cL: null };
    const nodeSet = new Set();
    const linkSet = new Set();

    if (active.type === "link") {
      const link = active.data;
      linkSet.add(link.i);
      nodeSet.add(link.tgt.id);
      const walkUp = (nodeId) => {
        if (nodeSet.has(nodeId)) return;
        nodeSet.add(nodeId);
        G.links.forEach((l) => {
          if (l.tgt.id === nodeId) {
            linkSet.add(l.i);
            walkUp(l.src.id);
          }
        });
      };
      walkUp(link.src.id);
    } else {
      const walkUp = (nodeId) => {
        if (nodeSet.has(nodeId)) return;
        nodeSet.add(nodeId);
        G.links.forEach((l) => {
          if (l.tgt.id === nodeId) {
            linkSet.add(l.i);
            walkUp(l.src.id);
          }
        });
      };
      walkUp(active.id);
      G.links.forEach((l) => {
        if (l.src.id === active.id) {
          linkSet.add(l.i);
          nodeSet.add(l.tgt.id);
        }
      });
    }
    return { cN: nodeSet, cL: linkSet };
  }, [active, G]);

  const nO = (n) => (!cN ? 0.92 : cN.has(n.id) ? 1 : 0.08);
  const lO = (l) => (!cL ? 0.18 : cL.has(l.i) ? 0.55 : 0.03);

  const clk = (type, data) => {
    const id = type === "link" ? `l${data.i}` : data.id;
    if (lock?.id === id) setLock(null);
    else setLock({ type, id, data });
  };

  if (!nodes.length) {
    return (
      <Card className={className}>
        <CardContent className="py-8">
          <p className="text-sm text-center" style={{ color: "var(--color-text-muted)" }}>
            No roadmap nodes to display. The path may still be loading.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (!G) return null;

  const colXs = {};
  for (let c = 0; c < G.nc; c++)
    colXs[c] = G.PAD.l + c * G.cW + G.NW / 2;
  const colLabels = (apiSankey?.columns || []).map((col) => col?.label ?? "") ||
    ["Start", "Credentials", "Bridge", "Entry", "Mid", "Target"];

  return (
    <div ref={cRef} className={className}>
      <div
        className="overflow-x-auto mt-5 rounded-xl border"
        style={{
          borderColor: "var(--color-border)",
          background: "var(--color-bg-secondary)",
        }}
      >
        <svg
          width={W}
          height={H + 40}
          className="block"
          onClick={(e) => {
            if (e.target.tagName === "svg") setLock(null);
          }}
        >
          <defs>
            {G.links.map((l) => (
              <linearGradient
                key={`g${l.i}`}
                id={`sg${l.i}`}
                gradientUnits="userSpaceOnUse"
                x1={l.src.x1}
                x2={l.tgt.x0}
              >
                <stop offset="0%" stopColor={COL[l.src.type] || "var(--color-accent)"} />
                <stop offset="100%" stopColor={COL[l.tgt.type] || "var(--color-accent)"} />
              </linearGradient>
            ))}
          </defs>

          {colLabels.slice(0, G.nc).map((lb, ci) => (
            <text
              key={`c${ci}`}
              x={colXs[ci]}
              y={16}
              textAnchor="middle"
              fontSize={10}
              fill="var(--color-text-dim)"
              fontWeight={500}
              className="uppercase tracking-wide"
            >
              {(typeof lb === "string" ? lb : "").split("\n").map((ln, li) => (
                <tspan key={li} x={colXs[ci]} dy={li === 0 ? 0 : 12}>
                  {ln}
                </tspan>
              ))}
            </text>
          ))}

          <g>
            {G.links.map((l) => (
              <path
                key={`lk${l.i}`}
                d={bandPath(l)}
                fill={`url(#sg${l.i})`}
                opacity={lO(l)}
                stroke="none"
                className="cursor-pointer transition-opacity hover:opacity-80"
                onMouseEnter={() =>
                  setHov({
                    type: "link",
                    id: `l${l.i}`,
                    data: { ...l, _lk: true },
                  })
                }
                onMouseLeave={() => setHov(null)}
                onClick={() => clk("link", { ...l, _lk: true })}
              />
            ))}
          </g>

          <g>
            {G.nodes.map((n) => {
              const c = COL[n.type] || "var(--color-accent)";
              const h = n.y1 - n.y0;
              const my = n.y0 + h / 2;
              const op = nO(n);
              const last = n.col === G.nc - 1;
              const lx = last ? n.x0 - 8 : n.x1 + 8;
              const anc = last ? "end" : "start";
              return (
                <g
                  key={n.id}
                  className="cursor-pointer transition-opacity"
                  style={{ opacity: op }}
                  onMouseEnter={() => setHov({ type: "node", id: n.id, data: n })}
                  onMouseLeave={() => setHov(null)}
                  onClick={() => clk("node", n)}
                >
                  <rect
                    x={n.x0}
                    y={n.y0}
                    width={G.NW}
                    height={h}
                    rx={2}
                    ry={2}
                    fill={c}
                    stroke={lock?.id === n.id ? "var(--color-text-primary)" : "none"}
                    strokeWidth={lock?.id === n.id ? 2 : 0}
                  />
                  <text
                    x={lx}
                    y={my}
                    textAnchor={anc}
                    dominantBaseline="central"
                    fontSize={11.5}
                    fontWeight={600}
                    fill="var(--color-text-primary)"
                    style={{ opacity: op < 0.5 ? 0.15 : 0.9 }}
                  >
                    {n.label}
                  </text>
                  {n.type?.includes("role") && n.detail?.attrs?.[0] && (
                    <text
                      x={lx}
                      y={my + 15}
                      textAnchor={anc}
                      dominantBaseline="central"
                      fontSize={9.5}
                      fill={c}
                      style={{ opacity: op < 0.5 ? 0.1 : 0.65 }}
                    >
                      {n.detail.attrs[0].v}
                    </text>
                  )}
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      <div
        className="flex flex-wrap gap-4 mt-3 justify-center text-xs"
        style={{ color: "var(--color-text-muted)" }}
      >
        {["origin", "certification", "education", "skillbridge", "entry_role", "mid_role", "target_role", "stretch_role"].map(
          (t) => (
            <div key={t} className="flex items-center gap-1.5">
              <div
                className="w-2.5 h-2.5 rounded-sm"
                style={{ background: COL[t] || "var(--color-accent)" }}
              />
              <span>{t.replace(/_/g, " ")}</span>
            </div>
          )
        )}
      </div>

      <Card className="mt-4 border rounded-xl" style={{ borderColor: "var(--color-border)", background: "var(--color-bg-secondary)" }}>
        <CardContent className="p-0">
          <DetailPanel item={active?.data} />
        </CardContent>
      </Card>
    </div>
  );
}
