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
        
        entry_salary = ""
        if entry and entry[0].get('detail', {}).get('attributes'):
            # Find the salary attribute
            for attr in entry[0]['detail']['attributes']:
                if attr['label'] == 'Salary':
                    entry_salary = attr['value']
                    break

        highest_salary = ""
        if highest and highest.get('detail', {}).get('attributes'):
            for attr in highest['detail']['attributes']:
                if attr['label'] == 'Salary':
                    highest_salary = attr['value']
                    break
        
        return {
            "fastest_path": {
                "label": "Fastest Path",
                "description": f"Direct to {entry[0]['label']}" if entry else "See career map",
                "timeline": "3–6 months",
            },
            "highest_ceiling": {
                "label": "Highest Ceiling",
                "description": highest['label'] if highest else target.title,
                "salary": highest_salary,
            },
            "recommended": {
                "label": "Recommended",
                "description": f"Cert track → {target.title}",
                "reason": "Best balance of speed and outcome",
            },
            "total_paths": len(set(l['source'] for l in links if l['source'].startswith('role-') or l['source'] == f'role-{origin.id}')),
            "salary_range": {
                "entry": entry_salary if entry_salary else "",
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
