"""
Build Sankey diagram payload from a roadmap response.

Explodes milestones into granular nodes (individual certs, education, SkillBridge,
roles) and creates cross-cutting links to produce a rich multi-path graph — matching
the branching career map style from the demo.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Columns — match demo labels
# ─────────────────────────────────────────────────────────────────────────────

COLUMNS = [
    {"index": 0, "label": "Starting\nPoint"},
    {"index": 1, "label": "Credentials"},
    {"index": 2, "label": "Advanced /\nBridge"},
    {"index": 3, "label": "Entry\nRoles"},
    {"index": 4, "label": "Mid-Level\nRoles"},
    {"index": 5, "label": "Target\nRoles"},
]

# Phase → column mapping (matches demo)
PHASE_COL = {
    "origin": 0,
    "preparation": 1,   # base certs go here; advanced certs/education/SB → col 2
    "entry_role": 3,
    "growth_role": 4,
    "target_role": 5,
    "stretch_role": 5,
}


def _classify_node_type(*, phase: str, has_education: bool = False,
                        has_skillbridge: bool = False, has_certs: bool = False,
                        has_bootcamp: bool = False, edu_type: str = "") -> str:
    """Classify node type by inspecting milestone content, not just phase."""
    if phase == "origin":
        return "origin"
    if phase == "entry_role":
        return "entry_role"
    if phase == "growth_role":
        return "mid_role"
    if phase == "target_role":
        return "target_role"
    if phase == "stretch_role":
        return "stretch_role"
    # preparation phase — look at content
    if edu_type == "skillbridge" or has_skillbridge:
        return "skillbridge"
    if has_bootcamp or edu_type == "bootcamp":
        return "bootcamp"
    if has_education or edu_type in ("bachelor", "master", "associate"):
        return "education"
    return "certification"


def _salary_sublabel(m: dict) -> str:
    low = m.get("salary_range_low")
    high = m.get("salary_range_high")
    if low and high:
        return f"${low / 1000:.0f}K–${high / 1000:.0f}K"
    return ""


def _detail_attrs(m: dict) -> list[dict]:
    attrs = []
    if m.get("salary_range_low") and m.get("salary_range_high"):
        attrs.append({"label": "Salary", "value": f"${m['salary_range_low']:,}–${m['salary_range_high']:,}"})
    for c in m.get("certifications", [])[:1]:
        attrs.append({"label": "Duration", "value": f"{c.get('estimated_weeks', 0)} weeks"})
        attrs.append({"label": "Cost", "value": f"${c.get('estimated_cost', 0):.0f}"})
    if m.get("employers"):
        attrs.append({"label": "Employers", "value": ", ".join(e.get("company_name", "") for e in m["employers"][:3])})
    return attrs


def _make_node(node_id: str, label: str, column: int, node_type: str,
               detail_title: str = "", detail_desc: str = "",
               detail_attrs: Optional[list] = None, sublabel: str = "",
               type_label: str = "") -> dict:
    return {
        "id": node_id,
        "label": label[:40] if len(label) > 40 else label,
        "sublabel": sublabel,
        "column": column,
        "type": node_type,
        "detail": {
            "title": detail_title or label,
            "type_label": type_label or node_type.replace("_", " ").title(),
            "description": detail_desc or None,
            "attributes": detail_attrs or [{"label": "Phase", "value": type_label or node_type.replace("_", " ").title()}],
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Explode milestones into granular graph
# ─────────────────────────────────────────────────────────────────────────────

def _explode_milestones(milestones: list[dict], origin: dict, path_id: str):
    """
    Convert a flat list of milestones into a rich set of nodes and links.
    Each certification, education item, and SkillBridge program becomes its
    own node, creating the branching multi-path structure the demo shows.
    """
    nodes = []
    links = []
    seen_ids = set()

    def add_node(n):
        if n["id"] not in seen_ids:
            nodes.append(n)
            seen_ids.add(n["id"])

    def add_link(src_id, tgt_id, value, title="", desc="", attrs=None):
        if src_id in seen_ids and tgt_id in seen_ids:
            links.append({
                "source": src_id,
                "target": tgt_id,
                "value": value,
                "path_id": path_id,
                "detail": {
                    "title": title or f"Progression",
                    "description": desc or "",
                    "attributes": attrs or [],
                },
            })

    # ── Origin node (col 0) ─────────────────────────────────────────────
    origin_title = origin.get("role_title") or "Your background"
    origin_id = "origin"
    add_node(_make_node(
        origin_id, origin_title, 0, "origin",
        detail_title="Your Starting Point",
        detail_desc=f"MOS: {origin.get('mos_code', 'N/A')} · {origin.get('branch', '')}",
        detail_attrs=[
            {"label": "MOS", "value": origin.get("mos_code") or "N/A"},
            {"label": "Skills", "value": ", ".join((origin.get("transferable_skills") or [])[:3]) or "Military experience"},
        ],
        type_label="Origin",
    ))

    # Collect role nodes by phase for linking later
    credential_ids = []  # col 1 nodes
    bridge_ids = []      # col 2 nodes
    entry_ids = []       # col 3 nodes
    mid_ids = []         # col 4 nodes
    target_ids = []      # col 5 nodes

    # Track if we have a direct placement link
    has_direct_entry = False

    for m_idx, m in enumerate(milestones):
        phase = m.get("phase", "")

        # ── Preparation phase → explode into individual credential nodes ──
        if phase == "preparation":
            certs = m.get("certifications") or []
            education = m.get("education") or []
            sb_programs = m.get("skillbridge_programs") or []

            # Individual certification nodes (col 1)
            for ci, cert in enumerate(certs):
                cert_id = f"cert_{path_id}_{m_idx}_{ci}"
                cert_name = cert.get("name", "Certification")
                weeks = cert.get("estimated_weeks", 0)
                cost = cert.get("estimated_cost", 0)
                va = cert.get("va_covered", False)
                add_node(_make_node(
                    cert_id, cert_name, 1, "certification",
                    detail_title=cert_name,
                    detail_desc=cert.get("description") or f"Industry certification from {cert.get('issuing_body', 'industry body')}.",
                    detail_attrs=[
                        {"label": "Study", "value": f"{weeks} weeks" if weeks else "Self-paced"},
                        {"label": "Cost", "value": f"${cost:.0f}" if cost else "Free"},
                        *([{"label": "VA", "value": "Covered"}] if va else []),
                    ],
                    type_label="Certification",
                ))
                credential_ids.append(cert_id)
                # Link: Origin → Cert
                add_link(origin_id, cert_id, max(30 - ci * 8, 10),
                         title=f"{cert_name} Track",
                         desc=f"Pursue {cert_name} certification.")

            # Individual education nodes
            for ei, edu in enumerate(education):
                edu_type = edu.get("education_type", "degree")
                field = edu.get("field_of_study", "")
                label = f"{'BS' if edu_type == 'bachelor' else 'AS' if edu_type == 'associate' else edu_type.title()} {field}".strip()
                if not label:
                    label = "Degree Program"
                edu_id = f"edu_{path_id}_{m_idx}_{ei}"
                months = edu.get("estimated_duration_months", 0)
                cost_range = edu.get("typical_cost_range", "")
                gi_bill = edu.get("can_use_gi_bill", False)

                # Education at col 1 for base degrees, col 2 for advanced
                col = 2 if edu_type in ("bachelor", "master") else 1
                add_node(_make_node(
                    edu_id, label, col, "education",
                    detail_title=label,
                    detail_desc=f"{edu_type.title()} degree program.",
                    detail_attrs=[
                        {"label": "Duration", "value": f"{months} months" if months else "Varies"},
                        {"label": "Cost", "value": cost_range or ("GI Bill" if gi_bill else "Varies")},
                        *([{"label": "GI Bill", "value": "Eligible"}] if gi_bill else []),
                    ],
                    type_label="Education",
                ))
                if col == 1:
                    credential_ids.append(edu_id)
                else:
                    bridge_ids.append(edu_id)
                # Link: Origin → Education
                add_link(origin_id, edu_id, max(14 - ei * 4, 6),
                         title="Degree Path",
                         desc=f"GI Bill covers tuition." if gi_bill else f"Pursue {label}.")

            # SkillBridge programs → col 2 (Bridge)
            for si, sb in enumerate(sb_programs):
                sb_id = f"sb_{path_id}_{m_idx}_{si}"
                sb_name = sb.get("program_name") or sb.get("company", "SkillBridge")
                company = sb.get("company", "")
                label = f"SkillBridge: {company}" if company else sb_name
                weeks = sb.get("duration_weeks", 0)
                add_node(_make_node(
                    sb_id, label[:40], 2, "skillbridge",
                    detail_title=sb_name,
                    detail_desc=f"180-day SkillBridge program{' with ' + company if company else ''}.",
                    detail_attrs=[
                        {"label": "Duration", "value": f"{weeks} weeks" if weeks else "180 days"},
                        {"label": "Type", "value": "SkillBridge"},
                    ],
                    type_label="SkillBridge",
                ))
                bridge_ids.append(sb_id)
                # Link: first cert → SkillBridge (cert ladder), or origin → SB
                if credential_ids:
                    add_link(credential_ids[0], sb_id, max(12 - si * 4, 6),
                             title="SkillBridge",
                             desc=f"{label} — paid DoD training.")
                else:
                    add_link(origin_id, sb_id, max(12 - si * 4, 6),
                             title="SkillBridge",
                             desc=f"Direct SkillBridge placement.")

            # Cross-links between credentials: cert → advanced cert/education
            if len(credential_ids) >= 2:
                # First cert → second cert (cert ladder)
                for ci in range(len(credential_ids) - 1):
                    add_link(credential_ids[ci], credential_ids[ci + 1], 8,
                             title="Cert Ladder",
                             desc="Natural progression in certification chain.")
            # Credential → bridge education
            for bid in bridge_ids:
                if credential_ids:
                    add_link(credential_ids[0], bid, 8,
                             title="Advanced Track",
                             desc="Credential opens advanced pathway.")

            # If no sub-items were extracted, create a single prep node
            if not certs and not education and not sb_programs:
                prep_id = f"prep_{path_id}_{m_idx}"
                add_node(_make_node(
                    prep_id, m.get("title", "Preparation"), 1, "certification",
                    detail_title=m.get("title", "Preparation"),
                    detail_desc=m.get("description", ""),
                    detail_attrs=_detail_attrs(m),
                    type_label="Preparation",
                ))
                credential_ids.append(prep_id)
                add_link(origin_id, prep_id, 30,
                         title="Preparation",
                         desc=m.get("description", ""))

        # ── Entry role (col 3) ──────────────────────────────────────────
        elif phase == "entry_role":
            role_id = m.get("milestone_id") or f"entry_{path_id}_{m_idx}"
            title = m.get("title", "Entry Role")
            sublbl = _salary_sublabel(m)
            add_node(_make_node(
                role_id, title, 3, "entry_role",
                detail_title=title,
                detail_desc=m.get("description", ""),
                detail_attrs=_detail_attrs(m) or [{"label": "Phase", "value": "Entry Role"}],
                sublabel=sublbl,
                type_label="Entry Role",
            ))
            entry_ids.append(role_id)

            # Links: credentials/bridges → entry role
            sources = bridge_ids if bridge_ids else credential_ids
            if not sources:
                sources = [origin_id]
                has_direct_entry = True
            for si, src in enumerate(sources):
                add_link(src, role_id, max(14 - si * 4, 6),
                         title=f"→ {title}",
                         desc=f"Qualifies for {title} position.")

            # Also link any remaining certs that didn't feed bridges
            if bridge_ids and credential_ids:
                for cid in credential_ids:
                    add_link(cid, role_id, 8,
                             title=f"Cert → {title}",
                             desc=f"Certification qualifies for entry role.")

        # ── Growth / mid-level role (col 4) ─────────────────────────────
        elif phase == "growth_role":
            role_id = m.get("milestone_id") or f"mid_{path_id}_{m_idx}"
            title = m.get("title", "Growth Role")
            sublbl = _salary_sublabel(m)
            add_node(_make_node(
                role_id, title, 4, "mid_role",
                detail_title=title,
                detail_desc=m.get("description", ""),
                detail_attrs=_detail_attrs(m) or [{"label": "Phase", "value": "Mid-Level"}],
                sublabel=sublbl,
                type_label="Mid-Level",
            ))
            mid_ids.append(role_id)

            # Links: entry → mid
            for ei, eid in enumerate(entry_ids):
                add_link(eid, role_id, max(18 - ei * 4, 8),
                         title=f"→ {title}",
                         desc=f"Promotion to {title} role.")

        # ── Target role (col 5) ─────────────────────────────────────────
        elif phase == "target_role":
            role_id = m.get("milestone_id") or f"target_{path_id}_{m_idx}"
            title = m.get("title", "Target Role")
            sublbl = _salary_sublabel(m)
            add_node(_make_node(
                role_id, title, 5, "target_role",
                detail_title=title,
                detail_desc=m.get("description", ""),
                detail_attrs=_detail_attrs(m) or [{"label": "Phase", "value": "Target Role"}],
                sublabel=sublbl,
                type_label="Target Role",
            ))
            target_ids.append(role_id)

            # Links: mid → target OR entry → target (if no mid)
            sources = mid_ids if mid_ids else entry_ids
            for si, src in enumerate(sources):
                add_link(src, role_id, max(16 - si * 4, 8),
                         title=f"→ {title}",
                         desc=f"Reach target: {title}.")

        # ── Stretch role (col 5, same column as target) ─────────────────
        elif phase == "stretch_role":
            role_id = m.get("milestone_id") or f"stretch_{path_id}_{m_idx}"
            title = m.get("title", "Stretch Role")
            sublbl = _salary_sublabel(m)
            add_node(_make_node(
                role_id, title, 5, "stretch_role",
                detail_title=title,
                detail_desc=m.get("description", ""),
                detail_attrs=_detail_attrs(m) or [{"label": "Phase", "value": "Stretch Goal"}],
                sublabel=sublbl,
                type_label="Stretch Goal",
            ))
            target_ids.append(role_id)

            # Links: target/mid → stretch
            sources = [tid for tid in target_ids if tid != role_id]
            if not sources:
                sources = mid_ids if mid_ids else entry_ids
            for si, src in enumerate(sources):
                add_link(src, role_id, max(12 - si * 4, 4),
                         title=f"→ {title}",
                         desc=f"Stretch goal: {title}.")

        # ── Origin phase (skip — we already added it above) ─────────────
        elif phase == "origin":
            continue

    # ── Direct placement link (origin → entry) if no credentials ────────
    if has_direct_entry and entry_ids:
        # Already added above when sources was [origin_id]
        pass
    elif not credential_ids and not bridge_ids and entry_ids:
        for eid in entry_ids:
            add_link(origin_id, eid, 10,
                     title="Direct Placement",
                     desc="Qualify on day 1 with military experience.")

    return nodes, links


# ─────────────────────────────────────────────────────────────────────────────
# Main conversion
# ─────────────────────────────────────────────────────────────────────────────

def roadmap_to_sankey(roadmap: dict, path_id: str = "primary") -> dict:
    """
    Convert a roadmap response (with milestones) to Sankey diagram payload.
    Explodes milestones into granular nodes to create a branching multi-path graph.
    """
    milestones = roadmap.get("milestones") or []
    origin = roadmap.get("origin") or {}

    if not milestones:
        nodes = [_make_node(
            "origin",
            origin.get("role_title") or "Your background",
            0, "origin",
            detail_title="Your Starting Point",
            type_label="Origin",
        )]
        return {"nodes": nodes, "links": [], "columns": COLUMNS, "summary": _build_summary(roadmap, milestones)}

    nodes, links = _explode_milestones(milestones, origin, path_id)
    summary = _build_summary(roadmap, milestones)

    return {
        "nodes": nodes,
        "links": links,
        "columns": COLUMNS,
        "summary": summary,
    }


def _build_summary(roadmap: dict, milestones: list[dict]) -> dict:
    """Build the summary block including the 4th 'most_in_demand' card."""
    entry_sal = roadmap.get("estimated_salary_at_entry") or "N/A"
    target_sal = roadmap.get("estimated_salary_at_target") or "N/A"
    total_months = roadmap.get("total_timeline_months") or 0
    path_name = (roadmap.get("alternative_roadmaps") or [{}])[0].get("path_name") if roadmap.get("alternative_roadmaps") else None
    if not path_name and milestones:
        path_name = milestones[-1].get("title", "Target Role")

    # Count certs for "most in demand" heuristic
    all_certs = []
    for m in milestones:
        all_certs.extend(m.get("certifications") or [])
    top_cert = all_certs[0].get("name", "Certification") if all_certs else "Certification"

    return {
        "fastest_path": {
            "label": "Cert Fast Track",
            "description": path_name or "Certification path",
            "timeline": f"{total_months} months",
        },
        "highest_ceiling": {
            "label": "Degree Path",
            "description": path_name or "Full progression",
            "salary": target_sal,
        },
        "most_in_demand": {
            "label": top_cert,
            "description": f"Top certification for this field",
            "salary": target_sal,
        },
        "recommended": {
            "label": "Recommended",
            "description": path_name or "Best fit for your background",
            "reason": "Based on your experience and target",
        },
        "total_paths": max(len([m for m in milestones if "role" in m.get("phase", "")]), 1),
        "salary_range": {
            "entry": entry_sal,
            "target": target_sal,
            "stretch": target_sal,
        },
    }


def build_full_pathfinder_response(roadmap: dict, path_id: str, title: str, inputs: dict) -> dict:
    """Build the full pathfinder API response with sankey, summary, inputs."""
    sankey = roadmap_to_sankey(roadmap, path_id)

    # Validate origin/target match user inputs
    _validate_endpoints(sankey, inputs, roadmap)

    return {
        "id": roadmap.get("roadmap_id") or "gen_1",
        "title": title,
        "generated_at": (roadmap.get("metadata") or {}).get("generated_at"),
        "confidence_score": (roadmap.get("metadata") or {}).get("confidence_score", 0.8),
        "inputs": inputs,
        "sankey": sankey,
        "summary": sankey["summary"],
        # Keep legacy keys for compatibility
        "roadmap_id": roadmap.get("roadmap_id"),
        "milestones": roadmap.get("milestones"),
        "origin": roadmap.get("origin"),
        "total_timeline_months": roadmap.get("total_timeline_months"),
        "estimated_salary_at_entry": roadmap.get("estimated_salary_at_entry"),
        "estimated_salary_at_target": roadmap.get("estimated_salary_at_target"),
    }


def _validate_endpoints(sankey: dict, inputs: dict, roadmap: dict) -> None:
    """
    Validate that the Sankey's origin and target nodes accurately reflect
    the user's inputs. Logs a warning and patches the node if they drift.

    Checks:
      1. Origin node (col 0) label should relate to the user's MOS/background.
      2. At least one target-role node (col 5 type target_role) should match
         the user's selected target role.
    """
    nodes = sankey.get("nodes") or []
    if not nodes:
        return

    # ── Extract user inputs ──────────────────────────────────────────────
    # inputs can come in many shapes; normalise to strings
    user_origin = ""
    user_target = ""
    if isinstance(inputs, dict):
        cr = inputs.get("current_role") or {}
        if isinstance(cr, dict):
            user_origin = cr.get("title") or cr.get("code") or ""
        elif isinstance(cr, str):
            user_origin = cr
        tgt = inputs.get("target") or {}
        if isinstance(tgt, dict):
            user_target = tgt.get("title") or tgt.get("code") or ""
        elif isinstance(tgt, str):
            user_target = tgt

    # Fallback from roadmap origin data
    if not user_origin:
        origin_data = roadmap.get("origin") or {}
        user_origin = origin_data.get("role_title") or origin_data.get("mos_code") or ""

    if not user_origin and not user_target:
        return  # nothing to validate

    # ── 1. Validate origin node ──────────────────────────────────────────
    origin_nodes = [n for n in nodes if n.get("column") == 0]
    if origin_nodes and user_origin:
        origin_node = origin_nodes[0]
        origin_label = (origin_node.get("label") or "").lower()
        user_origin_lower = user_origin.lower()
        # Check if origin node label is reasonable match
        if (user_origin_lower not in origin_label
                and origin_label not in user_origin_lower
                and origin_label not in ("your background",)):
            logger.warning(
                "Sankey origin mismatch: node='%s' input='%s' — patching",
                origin_node.get("label"), user_origin,
            )
            origin_node["label"] = user_origin[:40]
            origin_node["detail"]["title"] = user_origin

    # ── 2. Validate target node exists ───────────────────────────────────
    if user_target:
        target_nodes = [n for n in nodes if n.get("type") == "target_role"]
        if target_nodes:
            # Check if any target node label roughly matches
            user_target_lower = user_target.lower()
            has_match = any(
                user_target_lower in (n.get("label") or "").lower()
                or (n.get("label") or "").lower() in user_target_lower
                for n in target_nodes
            )
            if not has_match:
                old_label = target_nodes[0].get("label", "")
                logger.warning(
                    "Sankey target mismatch: node='%s' input='%s' — patching target node label, detail, and sublabel",
                    old_label, user_target,
                )
                # Patch the first target node fully
                target_nodes[0]["label"] = user_target[:40]
                target_nodes[0]["detail"]["title"] = user_target
                target_nodes[0]["detail"]["description"] = (
                    f"Target career: {user_target}. "
                    f"This is your selected career goal."
                )
        else:
            logger.warning(
                "Sankey has no target_role node — user expected '%s'", user_target,
            )

    # ── 3. Content-level sanity check ─────────────────────────────────────
    # Detect when the AI generated the wrong career path entirely (e.g.
    # cybersecurity content when user chose Robotics Engineers).
    if user_target:
        user_target_lower = user_target.lower()
        # Known high-frequency mismatches — keywords that indicate the wrong path
        MISMATCH_KEYWORDS = ["cybersecurity", "soc analyst", "security analyst",
                             "penetration test", "infosec", "comptia security"]
        # Only flag if user target doesn't contain these keywords
        user_is_cyber = any(kw in user_target_lower for kw in ("cyber", "security", "infosec", "soc"))
        if not user_is_cyber:
            role_nodes = [n for n in nodes if n.get("type") in ("entry_role", "mid_role", "target_role")]
            flagged = []
            for n in role_nodes:
                nlabel = (n.get("label") or "").lower()
                for kw in MISMATCH_KEYWORDS:
                    if kw in nlabel:
                        flagged.append((n.get("id"), n.get("label")))
                        break
            if flagged:
                logger.error(
                    "CONTENT MISMATCH: User target='%s' but Sankey contains "
                    "unrelated career nodes: %s. The AI likely generated the "
                    "wrong career path. Consider clearing the cache and retrying.",
                    user_target, flagged,
                )

