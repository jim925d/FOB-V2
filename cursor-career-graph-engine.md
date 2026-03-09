# Cursor Prompt — Database-Driven Career Roadmap Engine

## What you're building

Replace the AI-per-request roadmap generator with a database-driven graph engine. Every MOS, civilian role, certification, degree, SkillBridge program, and career path lives in PostgreSQL. The roadmap generator becomes a graph traversal query that returns instant results — no AI API calls at runtime.

**This prompt covers:**
1. Database schema (8 tables)
2. Seed data structure
3. Graph query algorithm (replaces `ai_roadmap_generator.py`)
4. Updated `sankey_builder.py`
5. Batch AI seeding script (one-time, for populating initial data)
6. Admin review workflow

**Files to modify/create in `api/app/`**

---

## 1. Database Schema

Create migration: `api/migrations/career_graph_schema.sql`

```sql
-- ════════════════════════════════════════════════════════════
-- CAREER GRAPH SCHEMA
-- Replaces AI-per-request generation with queryable graph
-- ════════════════════════════════════════════════════════════

-- ── Roles (military + civilian at all levels) ──
CREATE TABLE roles (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(20) UNIQUE,          -- MOS code (11B, 25B) or slug (cybersecurity-analyst)
    title           VARCHAR(255) NOT NULL,
    category        VARCHAR(50) NOT NULL,        -- 'military' or 'civilian'
    branch          VARCHAR(50),                 -- army, navy, marines, air_force, space_force, coast_guard, NULL for civilian
    industry        VARCHAR(100),                -- technology, healthcare, finance, government, trades, etc.
    level           VARCHAR(30) NOT NULL,        -- origin, entry, mid, senior, executive
    description     TEXT,
    salary_low      INTEGER,                     -- annual, in dollars
    salary_high     INTEGER,
    typical_experience_years  INTEGER DEFAULT 0,  -- years typically needed to reach this role
    clearance_helpful BOOLEAN DEFAULT false,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_roles_category ON roles(category);
CREATE INDEX idx_roles_branch ON roles(branch);
CREATE INDEX idx_roles_industry ON roles(industry);
CREATE INDEX idx_roles_level ON roles(level);

-- ── Credentials (certs, degrees, bootcamps, SkillBridge programs) ──
CREATE TABLE credentials (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(50) UNIQUE,          -- sec-plus, bs-cybersecurity, sb-amazon-restart
    name            VARCHAR(255) NOT NULL,
    type            VARCHAR(30) NOT NULL,        -- certification, degree_associate, degree_bachelors,
                                                 -- degree_masters, degree_doctorate, bootcamp,
                                                 -- skillbridge, trade_certificate
    domain          VARCHAR(100),                -- IT/Cyber, Project Management, Healthcare, Trades, etc.
    provider        VARCHAR(255),                -- CompTIA, WGU, Amazon, Microsoft, IBEW, etc.
    duration_months DECIMAL(4,1),                -- 2.0 for a cert, 24.0 for a BS, 6.0 for SkillBridge
    cost_dollars    INTEGER,                     -- exam/tuition cost
    cost_note       VARCHAR(255),                -- "GI Bill Ch. 33 covers", "Free (military)", "VET TEC eligible"
    difficulty      VARCHAR(20),                 -- entry, moderate, intermediate, advanced, expert
    description     TEXT,
    url             VARCHAR(500),                -- link to program/cert page
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_credentials_type ON credentials(type);
CREATE INDEX idx_credentials_domain ON credentials(domain);

-- ── Role Transferable Skills (what a military role teaches) ──
CREATE TABLE role_skills (
    id              SERIAL PRIMARY KEY,
    role_id         INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    skill_name      VARCHAR(255) NOT NULL,       -- "Network Administration", "Team Leadership", etc.
    skill_category  VARCHAR(100),                -- technical, leadership, operations, analytical
    relevance       VARCHAR(20) DEFAULT 'high',  -- high, medium, low
    UNIQUE(role_id, skill_name)
);

-- ── Credential Prerequisites (what you need before earning a credential) ──
CREATE TABLE credential_prereqs (
    id                  SERIAL PRIMARY KEY,
    credential_id       INTEGER REFERENCES credentials(id) ON DELETE CASCADE,
    prereq_credential_id INTEGER REFERENCES credentials(id) ON DELETE CASCADE,  -- NULL if prereq is education level
    prereq_education    VARCHAR(30),             -- min education: high_school, some_college, associate, bachelors, masters
    prereq_experience_years INTEGER,             -- min years of experience in related field
    is_required         BOOLEAN DEFAULT false,   -- true = hard requirement, false = recommended
    note                VARCHAR(255),            -- "Security+ recommended but not required"
    UNIQUE(credential_id, prereq_credential_id)
);

-- ── Career Edges (the graph connections) ──
-- Each row is a directed edge: "from X, you can reach Y"
-- X and Y can be roles OR credentials (one of each pair is NULL)
CREATE TABLE career_edges (
    id              SERIAL PRIMARY KEY,
    
    -- Source (exactly one must be set)
    source_role_id       INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    source_credential_id INTEGER REFERENCES credentials(id) ON DELETE CASCADE,
    
    -- Target (exactly one must be set)
    target_role_id       INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    target_credential_id INTEGER REFERENCES credentials(id) ON DELETE CASCADE,
    
    -- Edge metadata
    weight          INTEGER DEFAULT 10,          -- relative importance (higher = thicker Sankey band)
    typical_months  INTEGER,                     -- how long this transition typically takes
    description     TEXT,                        -- "Security+ qualifies you for SOC Analyst positions"
    path_tags       TEXT[],                      -- ['cyber', 'fast-track'] — for grouping paths
    
    -- Conditions for when this edge applies
    min_education        VARCHAR(30),            -- edge only valid if user has at least this education
    max_education        VARCHAR(30),            -- edge only valid if user has at most this (for degree paths)
    min_experience_years INTEGER DEFAULT 0,
    requires_clearance   BOOLEAN DEFAULT false,
    
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure exactly one source and one target
    CONSTRAINT chk_source CHECK (
        (source_role_id IS NOT NULL AND source_credential_id IS NULL) OR
        (source_role_id IS NULL AND source_credential_id IS NOT NULL)
    ),
    CONSTRAINT chk_target CHECK (
        (target_role_id IS NOT NULL AND target_credential_id IS NULL) OR
        (target_role_id IS NULL AND target_credential_id IS NOT NULL)
    )
);

CREATE INDEX idx_edges_source_role ON career_edges(source_role_id) WHERE source_role_id IS NOT NULL;
CREATE INDEX idx_edges_source_cred ON career_edges(source_credential_id) WHERE source_credential_id IS NOT NULL;
CREATE INDEX idx_edges_target_role ON career_edges(target_role_id) WHERE target_role_id IS NOT NULL;
CREATE INDEX idx_edges_target_cred ON career_edges(target_credential_id) WHERE target_credential_id IS NOT NULL;
CREATE INDEX idx_edges_tags ON career_edges USING gin(path_tags);

-- ── Role-to-Target Mappings (which targets are valid for which origins) ──
-- Pre-computed: "if you're a 25B, these are the target roles we have paths for"
CREATE TABLE role_target_mappings (
    id              SERIAL PRIMARY KEY,
    origin_role_id  INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    target_role_id  INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    relevance_score DECIMAL(3,2) DEFAULT 0.5,    -- 0.0 to 1.0, how relevant this target is for this origin
    is_featured     BOOLEAN DEFAULT false,       -- show in "recommended targets" for this MOS
    UNIQUE(origin_role_id, target_role_id)
);

CREATE INDEX idx_rtm_origin ON role_target_mappings(origin_role_id);

-- ── Employers (companies that hire for specific roles) ──
CREATE TABLE role_employers (
    id              SERIAL PRIMARY KEY,
    role_id         INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    employer_name   VARCHAR(255) NOT NULL,
    is_vet_friendly BOOLEAN DEFAULT false,
    location        VARCHAR(255),                -- "Arlington, VA" or "Remote"
    note            VARCHAR(255),                -- "Has veteran ERG", "SkillBridge partner"
    UNIQUE(role_id, employer_name)
);

-- ── Audit / Review Status ──
CREATE TABLE data_review_log (
    id              SERIAL PRIMARY KEY,
    table_name      VARCHAR(50) NOT NULL,
    record_id       INTEGER NOT NULL,
    status          VARCHAR(20) DEFAULT 'pending',  -- pending, approved, rejected, needs_edit
    reviewer        VARCHAR(100),
    notes           TEXT,
    reviewed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Views for common queries ──

-- All valid targets for a given origin role
CREATE VIEW v_origin_targets AS
SELECT 
    r_origin.code AS origin_code,
    r_origin.title AS origin_title,
    r_target.code AS target_code,
    r_target.title AS target_title,
    r_target.industry,
    r_target.salary_low,
    r_target.salary_high,
    rtm.relevance_score,
    rtm.is_featured
FROM role_target_mappings rtm
JOIN roles r_origin ON r_origin.id = rtm.origin_role_id
JOIN roles r_target ON r_target.id = rtm.target_role_id
WHERE r_origin.is_active AND r_target.is_active;

-- All edges with resolved names
CREATE VIEW v_career_edges AS
SELECT 
    ce.id,
    COALESCE(sr.title, sc.name) AS source_name,
    COALESCE(sr.code, sc.code) AS source_code,
    CASE WHEN sr.id IS NOT NULL THEN 'role' ELSE 'credential' END AS source_type,
    COALESCE(tr.title, tc.name) AS target_name,
    COALESCE(tr.code, tc.code) AS target_code,
    CASE WHEN tr.id IS NOT NULL THEN 'role' ELSE 'credential' END AS target_type,
    ce.weight,
    ce.typical_months,
    ce.description,
    ce.path_tags,
    ce.min_education,
    ce.min_experience_years
FROM career_edges ce
LEFT JOIN roles sr ON sr.id = ce.source_role_id
LEFT JOIN credentials sc ON sc.id = ce.source_credential_id
LEFT JOIN roles tr ON tr.id = ce.target_role_id
LEFT JOIN credentials tc ON tc.id = ce.target_credential_id
WHERE ce.is_active;
```

---

## 2. Graph Query Algorithm

Create: `api/app/services/career_graph.py`

This replaces `ai_roadmap_generator.py` as the primary roadmap engine.

```python
"""
Career Graph Engine — Database-Driven Roadmap Generator

Given a user's starting role, education, experience, and target role,
traverses the career_edges graph to find all valid paths from origin
to target, then builds the Sankey node/link structure.

No AI API calls. All data from PostgreSQL.
Response time: <100ms.
"""

from typing import Optional
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import (
    Role, Credential, CareerEdge, RoleTargetMapping,
    RoleSkill, RoleEmployer, CredentialPrereq
)


# Education level ordering for comparisons
EDUCATION_LEVELS = {
    'no_degree': 0, 'high_school': 1, 'some_college': 2,
    'associate': 3, 'bachelors': 4, 'masters': 5, 'doctorate': 6,
    'trade_certificate': 2,  # equivalent to some_college for filtering
}


class CareerGraphEngine:
    """
    Builds career roadmaps by traversing the career_edges graph.
    
    Usage:
        engine = CareerGraphEngine(db_session)
        roadmap = await engine.generate(
            origin_code="25B",
            target_code="cybersecurity-analyst",
            education="some_college",
            years_experience=4,
            timeline="6_12_months"
        )
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate(
        self,
        origin_code: str,
        target_code: str,
        education: str = "some_college",
        years_experience: int = 0,
        timeline: str = "6_12_months",
    ) -> dict:
        """Generate a complete roadmap as Sankey-ready data."""
        
        # 1. Resolve origin and target roles
        origin = await self._get_role(origin_code)
        target = await self._get_role(target_code)
        
        if not origin or not target:
            raise ValueError(f"Role not found: {origin_code if not origin else target_code}")
        
        # 2. Get user's education level for edge filtering
        edu_level = EDUCATION_LEVELS.get(education, 2)
        
        # 3. Find all valid edges from origin toward target
        #    This is a BFS/DFS through the career_edges graph
        subgraph = await self._find_paths(
            origin_id=origin.id,
            target_id=target.id,
            edu_level=edu_level,
            years_experience=years_experience,
            education=education,
        )
        
        # 4. Build Sankey structure
        sankey = await self._build_sankey(
            subgraph=subgraph,
            origin=origin,
            target=target,
            education=education,
            years_experience=years_experience,
            timeline=timeline,
        )
        
        # 5. Build summary
        summary = self._build_summary(sankey, origin, target)
        
        return {
            "title": f"{origin.title} → {target.title}",
            "sankey": sankey,
            "summary": summary,
            "inputs": {
                "origin": origin_code,
                "target": target_code,
                "education": education,
                "years_experience": years_experience,
                "timeline": timeline,
            }
        }
    
    async def _get_role(self, code: str) -> Optional[Role]:
        """Fetch a role by its code."""
        result = await self.db.execute(
            select(Role).where(Role.code == code, Role.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def _find_paths(
        self, origin_id: int, target_id: int,
        edu_level: int, years_experience: int, education: str
    ) -> dict:
        """
        BFS traversal from origin to target through career_edges.
        Returns all reachable nodes and edges that form valid paths.
        
        The graph flows: origin → credentials → more credentials → entry roles → mid roles → target → stretch
        """
        
        # Fetch ALL active edges (the graph is small enough to load entirely)
        result = await self.db.execute(
            select(CareerEdge).where(CareerEdge.is_active == True)
        )
        all_edges = result.scalars().all()
        
        # Build adjacency list
        # Key: (type, id) → list of edges
        adj = {}
        for edge in all_edges:
            src_key = ('role', edge.source_role_id) if edge.source_role_id else ('cred', edge.source_credential_id)
            if src_key not in adj:
                adj[src_key] = []
            adj[src_key].append(edge)
        
        # BFS from origin
        visited_nodes = set()    # (type, id)
        valid_edges = []         # CareerEdge objects
        queue = [('role', origin_id)]
        visited_nodes.add(('role', origin_id))
        
        # Track depth to avoid infinite loops (max 8 hops from origin to stretch)
        depth = {('role', origin_id): 0}
        MAX_DEPTH = 8
        
        while queue:
            current = queue.pop(0)
            current_depth = depth[current]
            
            if current_depth >= MAX_DEPTH:
                continue
            
            for edge in adj.get(current, []):
                # Check if this edge is valid for the user
                if not self._edge_valid(edge, edu_level, years_experience, education):
                    continue
                
                # Determine target node
                tgt_key = ('role', edge.target_role_id) if edge.target_role_id else ('cred', edge.target_credential_id)
                
                valid_edges.append(edge)
                
                if tgt_key not in visited_nodes:
                    visited_nodes.add(tgt_key)
                    depth[tgt_key] = current_depth + 1
                    
                    # Don't traverse past stretch roles (target_id depth + 1)
                    queue.append(tgt_key)
        
        # Fetch all referenced roles and credentials
        role_ids = {nid for ntype, nid in visited_nodes if ntype == 'role'}
        cred_ids = {nid for ntype, nid in visited_nodes if ntype == 'cred'}
        
        roles = {}
        if role_ids:
            result = await self.db.execute(select(Role).where(Role.id.in_(role_ids)))
            for r in result.scalars().all():
                roles[r.id] = r
        
        creds = {}
        if cred_ids:
            result = await self.db.execute(select(Credential).where(Credential.id.in_(cred_ids)))
            for c in result.scalars().all():
                creds[c.id] = c
        
        return {
            'roles': roles,
            'credentials': creds,
            'edges': valid_edges,
            'origin_id': origin_id,
            'target_id': target_id,
        }
    
    def _edge_valid(self, edge: CareerEdge, edu_level: int, years: int, education: str) -> bool:
        """Check if an edge is valid for this user's profile."""
        
        # Check minimum education
        if edge.min_education:
            min_level = EDUCATION_LEVELS.get(edge.min_education, 0)
            if edu_level < min_level:
                return False
        
        # Check maximum education (for degree paths — don't show BS if user has BS)
        if edge.max_education:
            max_level = EDUCATION_LEVELS.get(edge.max_education, 99)
            if edu_level > max_level:
                return False
        
        # Check minimum experience
        if edge.min_experience_years and years < edge.min_experience_years:
            return False
        
        return True
    
    async def _build_sankey(self, subgraph, origin, target, education, years_experience, timeline):
        """
        Convert the subgraph into Sankey nodes + links.
        
        Column assignment:
        0 = Origin (user's starting role)
        1 = Credentials (first certs/degrees)
        2 = Advanced / Bridge (advanced certs, SkillBridge)
        3 = Entry roles
        4 = TARGET ROLE (user's selection — ALWAYS here)
        5 = Stretch goals (beyond target)
        """
        nodes = []
        links = []
        
        roles = subgraph['roles']
        creds = subgraph['credentials']
        edges = subgraph['edges']
        
        # ── Assign columns ──
        # Origin
        origin_node = self._role_to_node(origin, column=0, node_type="origin",
                                          education=education, years=years_experience)
        nodes.append(origin_node)
        
        # Target (always column 4)
        if target.id in roles:
            target_node = self._role_to_node(target, column=4, node_type="target_role")
            nodes.append(target_node)
        
        # Categorize other nodes by their distance from origin and target
        for cred_id, cred in creds.items():
            # Determine column based on credential type and graph position
            if cred.type in ('certification', 'trade_certificate') and cred.duration_months and cred.duration_months <= 4:
                col = 1  # Quick certs
            elif cred.type in ('degree_bachelors', 'degree_associate', 'degree_masters', 'degree_doctorate'):
                col = 1  # Degrees go in credentials column
            elif cred.type == 'skillbridge':
                col = 2  # SkillBridge always in bridge column
            elif cred.type == 'bootcamp':
                col = 2  # Bootcamps in bridge column
            else:
                col = 2  # Advanced certs in bridge column
            
            # Check if this credential feeds directly into entry roles or is advanced
            feeds_into_roles = any(
                e.target_role_id is not None 
                for e in edges 
                if e.source_credential_id == cred_id
            )
            is_fed_by_creds = any(
                e.source_credential_id is not None 
                for e in edges 
                if e.target_credential_id == cred_id
            )
            if is_fed_by_creds:
                col = 2  # It's an advanced/bridge credential
            
            node_type = {
                'certification': 'certification',
                'degree_bachelors': 'education',
                'degree_masters': 'education',
                'degree_associate': 'education',
                'degree_doctorate': 'education',
                'skillbridge': 'skillbridge',
                'bootcamp': 'skillbridge',
                'trade_certificate': 'certification',
            }.get(cred.type, 'certification')
            
            nodes.append(self._cred_to_node(cred, column=col, node_type=node_type))
        
        # Other roles (entry, mid, stretch)
        for role_id, role in roles.items():
            if role_id == origin.id or role_id == target.id:
                continue
            
            if role.level == 'entry':
                nodes.append(self._role_to_node(role, column=3, node_type="entry_role"))
            elif role.level == 'mid':
                # If this role IS the target, it's already added at column 4
                nodes.append(self._role_to_node(role, column=3, node_type="entry_role"))
            elif role.level in ('senior', 'executive'):
                nodes.append(self._role_to_node(role, column=5, node_type="stretch_role"))
            else:
                nodes.append(self._role_to_node(role, column=3, node_type="entry_role"))
        
        # ── Build links from edges ──
        node_id_map = {n['id']: n for n in nodes}
        
        for edge in edges:
            src_id = f"role-{edge.source_role_id}" if edge.source_role_id else f"cred-{edge.source_credential_id}"
            tgt_id = f"role-{edge.target_role_id}" if edge.target_role_id else f"cred-{edge.target_credential_id}"
            
            # Only include edges where both source and target are in our node set
            if src_id in node_id_map and tgt_id in node_id_map:
                links.append({
                    "source": src_id,
                    "target": tgt_id,
                    "value": edge.weight,
                    "detail": {
                        "title": edge.description or f"→ {node_id_map[tgt_id]['label']}",
                        "description": edge.description or "",
                        "attributes": [
                            {"label": "Timeline", "value": f"{edge.typical_months} months" if edge.typical_months else "Varies"},
                        ]
                    }
                })
        
        # Fetch employers for role nodes
        for node in nodes:
            if node['id'].startswith('role-'):
                role_id = int(node['id'].replace('role-', ''))
                employers = await self._get_employers(role_id)
                if employers and node.get('detail', {}).get('attributes'):
                    node['detail']['attributes'].append({
                        "label": "Employers",
                        "value": ", ".join(e.employer_name for e in employers[:4])
                    })
        
        return {
            "nodes": nodes,
            "links": links,
            "columns": [
                {"index": 0, "label": "Starting Point"},
                {"index": 1, "label": "Credentials"},
                {"index": 2, "label": "Advanced / Bridge"},
                {"index": 3, "label": "Entry Roles"},
                {"index": 4, "label": "Target Role"},
                {"index": 5, "label": "Growth"},
            ]
        }
    
    def _role_to_node(self, role, column, node_type, education=None, years=None):
        """Convert a Role DB object to a Sankey node."""
        attrs = []
        if role.salary_low and role.salary_high:
            attrs.append({"label": "Salary", "value": f"${role.salary_low//1000}K–${role.salary_high//1000}K"})
        if role.typical_experience_years:
            attrs.append({"label": "Timeline", "value": f"Year {role.typical_experience_years}" if role.typical_experience_years > 0 else "Immediate"})
        if education and column == 0:
            attrs.insert(0, {"label": "Role", "value": role.title})
            attrs.append({"label": "Education", "value": education.replace('_', ' ').title()})
            if years:
                attrs.append({"label": "Experience", "value": f"{years} years"})
        
        return {
            "id": f"role-{role.id}",
            "label": role.title,
            "column": column,
            "type": node_type,
            "detail": {
                "title": role.title,
                "description": role.description or "",
                "attributes": attrs,
            }
        }
    
    def _cred_to_node(self, cred, column, node_type):
        """Convert a Credential DB object to a Sankey node."""
        attrs = []
        if cred.duration_months:
            months = cred.duration_months
            dur = f"{int(months)} mo" if months < 12 else f"{months/12:.0f}–{months/12 + 1:.0f} yr"
            attrs.append({"label": "Duration", "value": dur})
        if cred.cost_dollars:
            attrs.append({"label": "Cost", "value": f"${cred.cost_dollars:,}"})
        if cred.cost_note:
            attrs.append({"label": "Funding", "value": cred.cost_note})
        if cred.difficulty:
            attrs.append({"label": "Difficulty", "value": cred.difficulty.title()})
        
        return {
            "id": f"cred-{cred.id}",
            "label": cred.name,
            "column": column,
            "type": node_type,
            "detail": {
                "title": cred.name,
                "description": cred.description or "",
                "attributes": attrs,
            }
        }
    
    async def _get_employers(self, role_id):
        result = await self.db.execute(
            select(RoleEmployer).where(RoleEmployer.role_id == role_id).limit(5)
        )
        return result.scalars().all()
    
    def _build_summary(self, sankey, origin, target):
        """Build the summary cards (fastest, highest ceiling, recommended)."""
        nodes = sankey['nodes']
        links = sankey['links']
        
        # Find stretch roles (column 5) for highest ceiling
        stretch = [n for n in nodes if n['column'] == 5]
        highest = stretch[0] if stretch else None
        
        # Entry roles for fastest path
        entry = [n for n in nodes if n['column'] == 3]
        
        return {
            "fastest_path": {
                "label": "Fastest Path",
                "description": f"Direct to {entry[0]['label']}" if entry else "See career map",
                "timeline": "3–6 months",
            },
            "highest_ceiling": {
                "label": "Highest Ceiling",
                "description": highest['label'] if highest else target.title,
                "salary": highest['detail']['attributes'][0]['value'] if highest and highest['detail']['attributes'] else "",
            },
            "recommended": {
                "label": "Recommended",
                "description": f"Cert track → {target.title}",
                "reason": "Best balance of speed and outcome",
            },
            "total_paths": len(set(l['source'] for l in links if l['source'].startswith('role-') or l['source'] == f'role-{origin.id}')),
            "salary_range": {
                "entry": f"${entry[0]['detail']['attributes'][0]['value']}" if entry and entry[0]['detail']['attributes'] else "",
                "target": f"${target.salary_low//1000}K–${target.salary_high//1000}K" if target.salary_low else "",
            }
        }
    
    async def get_available_targets(self, origin_code: str) -> list:
        """Return all valid target roles for a given origin MOS/role."""
        origin = await self._get_role(origin_code)
        if not origin:
            return []
        
        result = await self.db.execute(
            select(RoleTargetMapping, Role)
            .join(Role, Role.id == RoleTargetMapping.target_role_id)
            .where(
                RoleTargetMapping.origin_role_id == origin.id,
                Role.is_active == True,
            )
            .order_by(RoleTargetMapping.relevance_score.desc())
        )
        
        return [
            {
                "code": role.code,
                "title": role.title,
                "industry": role.industry,
                "salary_range": f"${role.salary_low//1000}K–${role.salary_high//1000}K" if role.salary_low else None,
                "relevance": mapping.relevance_score,
                "featured": mapping.is_featured,
            }
            for mapping, role in result.all()
        ]
```

---

## 3. Update the Roadmap Route

Update: `api/app/routes/roadmap.py`

Replace the AI generator call with the graph engine:

```python
from app.services.career_graph import CareerGraphEngine

@router.post("/api/v1/roadmap/generate")
async def generate_roadmap(request: RoadmapRequest, db: AsyncSession = Depends(get_db)):
    engine = CareerGraphEngine(db)
    
    try:
        roadmap = await engine.generate(
            origin_code=request.current_role.code,
            target_code=request.target_role.id,
            education=request.education,
            years_experience=parse_years(request.years_experience),
            timeline=request.timeline,
        )
        return roadmap
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Fallback to curated paths if graph is empty
        logger.error(f"Graph engine failed: {e}")
        raise HTTPException(status_code=500, detail="Could not generate roadmap")
```

---

## 4. Batch AI Seeding Script

Create: `api/scripts/seed_career_graph.py`

This runs ONCE (or periodically to expand coverage). It uses Claude to generate career path data in bulk, which you then review and approve before it goes into the production database.

```python
"""
Batch Career Graph Seeder

Uses Claude API to generate career path data for every MOS × target combination.
Output: JSON files for human review before database insertion.

Usage:
    python -m scripts.seed_career_graph --mos 25B --target cybersecurity-analyst
    python -m scripts.seed_career_graph --all    # generates for all MOS codes
"""

import json
import os
import anthropic
from pathlib import Path


ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OUTPUT_DIR = Path("scripts/seed_output/")


SYSTEM_PROMPT = """You are a career transition advisor for military veterans.
Generate career path data as structured JSON for database insertion.

For the given MOS (military role) and target civilian role, produce:

1. Required credentials (certifications, degrees, bootcamps, SkillBridge programs)
   - Include BOTH certification paths AND degree paths
   - Each credential needs: name, type, domain, provider, duration_months, cost, cost_note, difficulty, description
   
2. Intermediate roles (entry-level civilian jobs that lead to the target)
   - Each role needs: title, code (slug), level (entry/mid), industry, salary_low, salary_high, typical_experience_years, description
   
3. Stretch roles (1-2 roles beyond the target for growth)
   - Same fields as intermediate roles but level=senior or level=executive

4. Career edges connecting everything:
   - origin → credentials (which certs/degrees to pursue first)
   - credentials → more credentials (cert ladders, e.g., Security+ → CySA+)
   - credentials → entry roles (what each cert qualifies you for)
   - entry roles → target role (progression path)
   - target role → stretch roles (career growth)
   - degree → roles (direct qualification paths)
   
   Each edge needs: weight (10-30, higher = more common path), typical_months, description
   
5. Edge conditions:
   - Which edges require minimum education (e.g., degree path only if user has < bachelors)
   - Which edges require clearance

6. Employers for each role (4-5 companies, mark veteran-friendly ones)

CRITICAL RULES:
- All salary data must be realistic 2025-2026 ranges from BLS/Glassdoor
- All certifications must be REAL certifications that actually exist
- All SkillBridge programs must be REAL DoD SkillBridge programs
- Cost data must be accurate (exam fees, tuition)
- Duration must be realistic study/program time
- The user's selected target role MUST be in the output, not replaced by a similar role

Respond with ONLY valid JSON, no markdown, no commentary."""


USER_PROMPT_TEMPLATE = """Generate career path data for:

Origin MOS: {mos_code} — {mos_title}
Target Role: {target_title} ({target_industry})
Veteran's typical profile: {experience_years} years experience, {education_level} education, may have security clearance

Output the JSON with these top-level keys:
- credentials: array of credential objects
- roles: array of role objects (entry + stretch, NOT the origin or target — those already exist)
- edges: array of edge objects
- employers: array of {{ role_code, employer_name, is_vet_friendly, location, note }}
- role_target_mapping: {{ relevance_score (0-1), is_featured (bool) }}
"""


def generate_path_data(mos_code, mos_title, target_code, target_title, target_industry):
    """Call Claude to generate career path data for one MOS → target combination."""
    
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(
                mos_code=mos_code,
                mos_title=mos_title,
                target_title=target_title,
                target_industry=target_industry,
                experience_years="4-6",
                education_level="some college",
            )
        }]
    )
    
    # Parse response
    text = response.content[0].text.strip()
    # Remove markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    
    data = json.loads(text)
    
    # Save for review
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / f"{mos_code}_to_{target_code}.json"
    with open(output_file, "w") as f:
        json.dump({
            "origin": {"code": mos_code, "title": mos_title},
            "target": {"code": target_code, "title": target_title, "industry": target_industry},
            "generated_data": data,
            "status": "pending_review",
        }, f, indent=2)
    
    print(f"✓ Generated {mos_code} → {target_code} → {output_file}")
    return data


def insert_reviewed_data(json_file: str, db_url: str):
    """Insert reviewed/approved JSON data into the database."""
    # This function reads the JSON file and inserts into 
    # roles, credentials, career_edges, role_employers tables
    # Only run AFTER human review and status changed to "approved"
    pass  # Implementation: standard SQLAlchemy inserts


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mos", required=True)
    parser.add_argument("--mos-title", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--target-title", required=True)
    parser.add_argument("--industry", default="technology")
    args = parser.parse_args()
    
    generate_path_data(args.mos, args.mos_title, args.target, args.target_title, args.industry)
```

---

## 5. Seed Data — Initial MOS + Target Combinations to Generate

Run the seeder for your highest-priority combinations first:

```bash
# Army — Technology
python -m scripts.seed_career_graph --mos 25B --mos-title "IT Specialist" --target cybersecurity-analyst --target-title "Cybersecurity Analyst" --industry technology
python -m scripts.seed_career_graph --mos 25B --mos-title "IT Specialist" --target cloud-eng --target-title "Cloud Engineer" --industry technology
python -m scripts.seed_career_graph --mos 25B --mos-title "IT Specialist" --target sw-dev --target-title "Software Developer" --industry technology
python -m scripts.seed_career_graph --mos 35F --mos-title "Intelligence Analyst" --target intel-analyst --target-title "Intelligence Analyst" --industry government
python -m scripts.seed_career_graph --mos 11B --mos-title "Infantry" --target ops-mgr --target-title "Operations Manager" --industry business
python -m scripts.seed_career_graph --mos 11B --mos-title "Infantry" --target fed-pm --target-title "Federal Program Manager" --industry government

# Army — Healthcare
python -m scripts.seed_career_graph --mos 68W --mos-title "Combat Medic" --target health-admin --target-title "Healthcare Administrator" --industry healthcare

# Army — Trades  
python -m scripts.seed_career_graph --mos 12B --mos-title "Combat Engineer" --target electrician --target-title "Electrician" --industry trades

# Marines
python -m scripts.seed_career_graph --mos 0311 --mos-title "Rifleman" --target ops-mgr --target-title "Operations Manager" --industry business
python -m scripts.seed_career_graph --mos 0621 --mos-title "Radio Operator" --target net-admin --target-title "Network Administrator" --industry technology

# Air Force
python -m scripts.seed_career_graph --mos 3D0X2 --mos-title "Cyber Systems Operations" --target cybersecurity-analyst --target-title "Cybersecurity Analyst" --industry technology
python -m scripts.seed_career_graph --mos 1N0X1 --mos-title "All Source Intelligence" --target intel-analyst --target-title "Intelligence Analyst" --industry government
```

Each generates a JSON file in `scripts/seed_output/` for human review.

---

## 6. Review + Insert Workflow

After generating seed data:

1. **Review** each JSON file in `scripts/seed_output/`
2. **Verify** salary ranges against BLS/Glassdoor
3. **Verify** certifications are real (check provider websites)
4. **Verify** SkillBridge programs are active (check skillbridge.osd.mil)
5. **Mark status** as `"approved"` in the JSON file
6. **Run insert script** to load approved data into PostgreSQL
7. **Test** the graph engine with the same MOS/target — confirm it produces a valid Sankey

---

## 7. Fallback for Missing Combinations

If a user selects a MOS + target that isn't in the database yet, the route should:

1. Check if the combination exists in `role_target_mappings`
2. If not, return a helpful response instead of an error:

```python
# In the route handler
if not roadmap['sankey']['nodes']:
    # No path data for this combination yet
    return {
        "title": f"{origin.title} → {target.title}",
        "status": "no_data",
        "message": "We're still building career paths for this combination. Try one of these related targets:",
        "suggested_targets": await engine.get_available_targets(origin_code),
        "sankey": None,
        "summary": None,
    }
```

The frontend handles this by showing the suggested targets as clickable options.

---

## Implementation Order

1. Run the migration SQL to create tables
2. Create the SQLAlchemy models in `api/app/models/database.py` matching the schema
3. Create `api/app/services/career_graph.py` (the engine above)
4. Update `api/app/routes/roadmap.py` to use the graph engine
5. Run the batch seeder for your top 12 MOS/target combinations
6. Review the generated JSON files
7. Insert approved data into the database
8. Test: `POST /api/v1/roadmap/generate` with a seeded combination → should return Sankey data in <100ms
9. Test: try an un-seeded combination → should return suggested targets

---

## Verify

- [ ] All 8 tables created in PostgreSQL
- [ ] SQLAlchemy models match the schema
- [ ] `CareerGraphEngine.generate()` returns valid Sankey data for seeded combinations
- [ ] Response time < 200ms (no AI calls)
- [ ] Same inputs always produce identical output (deterministic)
- [ ] User's target role appears in column 4 with type "target_role"
- [ ] Degree paths appear in column 1 when user education is below bachelors
- [ ] Edges with `min_education` are correctly filtered
- [ ] Un-seeded combinations return `"status": "no_data"` with suggested targets
- [ ] Batch seeder generates valid JSON files
- [ ] Old `ai_roadmap_generator.py` is no longer called at runtime

Commit: `feat: database-driven career graph engine replacing AI-per-request generation`
