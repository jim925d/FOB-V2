"""
Roadmap Generation Service
The FOB Platform

Core engine that:
1. Takes veteran input (MOS or dream job)
2. Matches to curated progression paths
3. Personalizes milestones with regional data
4. Returns a complete career roadmap

This service orchestrates between:
- Curated progression path data
- O*NET career mapping (existing Career Pathfinder)
- BLS regional salary data
- SkillBridge Explorer (existing)
- Yellow Ribbon school data (existing)
"""

import hashlib
import logging
from datetime import datetime
from typing import Optional

from app.models.roadmap import (
    Pathway,
    RoadmapRequest,
    RoadmapResponse,
    TimelineUrgency,
)

logger = logging.getLogger(__name__)

_MOS_CODE_RE = r"^[0-9]{2}[A-Z][0-9A-Z]?$"

# =============================================================================
# REGIONAL SALARY ADJUSTMENTS
# =============================================================================

# Cost-of-living multipliers by metro area (BLS-derived approximations)
# In production, these come from BLS OEWS API by area code
REGIONAL_SALARY_MULTIPLIERS = {
    # Format: first 3 digits of ZIP → multiplier
    "100": 1.30,  # New York City
    "200": 1.20,  # Washington DC
    "221": 1.20,  # Northern Virginia
    "300": 0.95,  # Atlanta
    "330": 1.00,  # Miami
    "606": 1.05,  # Chicago
    "750": 0.95,  # Dallas
    "770": 0.90,  # Houston
    "802": 1.05,  # Denver / Colorado Springs
    "803": 1.05,  # Denver metro
    "850": 0.95,  # Phoenix
    "900": 1.25,  # Los Angeles
    "941": 1.35,  # San Francisco
    "980": 1.20,  # Seattle
    "782": 0.85,  # San Antonio (big military area)
    "283": 0.90,  # Fayetteville/Fort Liberty
    "316": 0.85,  # Fort Riley area
    "314": 0.90,  # Fort Leonard Wood
    "961": 1.10,  # Joint Base Lewis-McChord
}

DEFAULT_MULTIPLIER = 1.0


def get_salary_multiplier(zip_code: Optional[str]) -> float:
    """Get regional salary multiplier from ZIP code prefix."""
    if not zip_code:
        return DEFAULT_MULTIPLIER
    prefix = zip_code[:3]
    return REGIONAL_SALARY_MULTIPLIERS.get(prefix, DEFAULT_MULTIPLIER)


def adjust_salary(base_salary: Optional[int], multiplier: float) -> Optional[int]:
    """Apply regional multiplier to a salary figure."""
    if base_salary is None:
        return None
    adjusted = int(base_salary * multiplier)
    # Round to nearest thousand for cleaner display
    return round(adjusted / 1000) * 1000


# =============================================================================
# TIMELINE ADJUSTMENTS
# =============================================================================

def get_timeline_adjustment(urgency: TimelineUrgency) -> dict:
    """
    Adjust milestone timelines based on veteran's transition urgency.
    
    Returns adjustment factors and recommendations.
    """
    adjustments = {
        TimelineUrgency.PLANNING_AHEAD: {
            "prep_multiplier": 1.0,      # Full preparation time
            "overlap_months": 0,          # No overlap needed
            "can_skillbridge": True,
            "recommended_first_action": "Begin certification study while on active duty",
            "timeline_note": "You have time to prepare thoroughly. Use TA for certifications and apply for SkillBridge early."
        },
        TimelineUrgency.TRANSITIONING: {
            "prep_multiplier": 0.8,       # Slightly compressed prep
            "overlap_months": 0,
            "can_skillbridge": True,
            "recommended_first_action": "Apply for SkillBridge immediately — slots fill fast",
            "timeline_note": "Good timeline. Focus on SkillBridge application and begin certification study now."
        },
        TimelineUrgency.IMMINENT: {
            "prep_multiplier": 0.5,       # Compressed prep — prioritize essentials
            "overlap_months": 2,          # Some phases overlap
            "can_skillbridge": False,     # Likely too late for SkillBridge
            "recommended_first_action": "Focus on one key certification and start applying to entry roles now",
            "timeline_note": "Timeline is tight. Prioritize the single most impactful certification and begin job applications immediately."
        },
        TimelineUrgency.ALREADY_OUT: {
            "prep_multiplier": 0.3,       # Minimal prep — get working
            "overlap_months": 3,          # Heavy overlap — prep while working
            "can_skillbridge": False,
            "recommended_first_action": "Apply to entry roles immediately while studying for certification",
            "timeline_note": "Already separated — prioritize employment. Study for certifications while working in an entry role."
        },
    }
    return adjustments.get(urgency, adjustments[TimelineUrgency.TRANSITIONING])


# =============================================================================
# MAIN ROADMAP GENERATOR
# =============================================================================

class RoadmapGenerator:
    """
    Core engine for generating personalized career roadmaps.
    
    Usage:
        generator = RoadmapGenerator(
            path_data=CAREER_PROGRESSION_PATHS,
            mos_index=MOS_TO_PATHS,
            industry_index=INDUSTRY_TO_PATHS,
            path_index=PATH_BY_ID
        )
        roadmap = await generator.generate(request)
    """
    
    def __init__(
        self,
        path_data: list[dict],
        mos_index: dict[str, list[str]],
        industry_index: dict[str, list[str]],
        path_index: dict[str, dict],
        # These would be injected service dependencies in production
        skillbridge_service=None,
        yellow_ribbon_service=None,
        bls_service=None,
    ):
        self.path_data = path_data
        self.mos_index = mos_index
        self.industry_index = industry_index
        self.path_index = path_index
        self.skillbridge_service = skillbridge_service
        self.yellow_ribbon_service = yellow_ribbon_service
        self.bls_service = bls_service
    
    async def generate(self, request: RoadmapRequest) -> RoadmapResponse:
        """
        Generate a complete personalized career roadmap.
        
        Pipeline:
        1. Match veteran to progression path(s)
        2. Select best-fit path
        3. Personalize milestones (salary, employers, timeline)
        4. Enrich with SkillBridge and Yellow Ribbon data
        5. Build salary progression chart data
        6. Package response
        """
        
        # Step 1: Find matching paths
        # When user selected both MOS and a target role/industry, prefer paths that match the target
        # so the Sankey reflects their choice (e.g. General and Operations Managers, not Security).
        if request.pathway == Pathway.MOS_TO_CAREER:
            if request.target_role or request.target_industry:
                matched_paths = self._match_by_target(
                    request.target_role, request.target_industry
                )
                if matched_paths and request.mos_code:
                    mos_path_ids = {
                        p["path_id"] for p in self._match_by_mos(request.mos_code, request.branch)
                    }
                    matched_paths = [p for p in matched_paths if p["path_id"] in mos_path_ids]
                # No curated path for this target → use synthetic path so roadmap shows user's choice
                if not matched_paths:
                    matched_paths = [self._build_synthetic_path(request)]
            else:
                matched_paths = self._match_by_mos(request.mos_code, request.branch)
                if not matched_paths:
                    matched_paths = self._fallback_paths(request)
        else:
            matched_paths = self._match_by_target(
                request.target_role, request.target_industry
            )
        
        if not matched_paths:
            matched_paths = self._fallback_paths(request)
        if not matched_paths:
            return self._build_no_match_response(request)
        
        # Step 2: Select primary path (highest demand * match quality)
        primary_path = matched_paths[0]
        alternative_paths = matched_paths[1:3]  # Up to 2 alternatives
        
        # Step 3: Personalize milestones
        salary_multiplier = get_salary_multiplier(request.zip_code) if request.zip_code else DEFAULT_MULTIPLIER
        timeline_adj = get_timeline_adjustment(request.timeline)

        # SkillBridge eligibility: both timeline-based AND user preference
        can_skillbridge = timeline_adj["can_skillbridge"] and getattr(request, "skillbridge_interest", True)

        personalized_milestones = self._personalize_milestones(
            primary_path["milestones"],
            salary_multiplier=salary_multiplier,
            timeline_adjustment=timeline_adj,
            education_willingness=request.education_willingness,
            can_skillbridge=can_skillbridge,
        )

        # Step 4: Enrich with live data (if services available)
        if self.skillbridge_service and getattr(request, "skillbridge_interest", True):
            self._current_career_field = primary_path.get("target_career_field", "")
            personalized_milestones = await self._enrich_skillbridge(
                personalized_milestones, request.zip_code
            )

        if self.yellow_ribbon_service:
            personalized_milestones = await self._enrich_yellow_ribbon(
                personalized_milestones, request.zip_code
            )

        if self.bls_service:
            personalized_milestones = await self._enrich_bls_salary(
                personalized_milestones, request.zip_code
            )
        
        # Step 5: Build salary progression data
        salary_progression = self._build_salary_progression(personalized_milestones)
        
        # Step 6: Calculate summary stats
        entry_milestone = next(
            (m for m in personalized_milestones if m.get("phase") == "entry_role"), None
        )
        target_milestone = next(
            (m for m in personalized_milestones if m.get("phase") == "target_role"), None
        )
        
        cert_count = sum(
            len(m.get("certifications", []))
            for m in personalized_milestones
        )
        
        # Step 7: Determine total timeline
        total_months = max(
            m.get("timeline_end_months", 0) for m in personalized_milestones
        )
        
        # Step 8: Build response
        roadmap_id = self._generate_roadmap_id(request)
        
        response = {
            "roadmap_id": roadmap_id,
            "pathway_used": request.pathway.value,
            "origin": {
                "mos_code": request.mos_code,
                "branch": request.branch,
                "role_title": primary_path["milestones"][0].get("title", ""),
                "transferable_skills": primary_path["milestones"][0].get(
                    "skills_from_military", []
                ),
            },
            "milestones": personalized_milestones,
            "total_timeline_months": total_months,
            "salary_progression": salary_progression,
            "estimated_salary_at_entry": self._format_salary_range(entry_milestone),
            "estimated_salary_at_target": self._format_salary_range(target_milestone),
            "certifications_needed": cert_count,
            "education_investment": self._estimate_education_cost(
                personalized_milestones, request.education_willingness
            ),
            "recommended_first_action": timeline_adj["recommended_first_action"],
            "recommended_skillbridge": self._get_recommended_skillbridge(
                personalized_milestones
            ),
            "recommended_communities": primary_path.get("related_communities", []),
            "alternative_roadmaps": [
                {
                    "path_id": alt["path_id"],
                    "path_name": alt["path_name"],
                    "total_timeline_months": alt["total_timeline_months"],
                    "difficulty_rating": alt["difficulty_rating"],
                    "salary_ceiling": alt.get("salary_ceiling"),
                }
                for alt in alternative_paths
            ],
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "path_id": primary_path.get("path_id"),
                "target_role": primary_path.get("path_name", "").split("→")[-1].strip() if primary_path.get("path_name") else None,
                "target_industry": primary_path.get("target_industry"),
                "data_sources": {
                    "career_mapping": "O*NET 28.0 + Military Crosswalk",
                    "labor_data": "BLS OEWS (regionalized)",
                    "education": "IPEDS + VA WEAMS",
                    "skillbridge": "DoD SkillBridge",
                    "progression": "FOB Curated Career Paths v1.0",
                },
                "confidence_score": self._calculate_confidence(primary_path, request),
                "confidence_notes": self._confidence_notes(primary_path, request),
                "personalization_factors": [
                    f"Regional salary adjusted for ZIP {request.zip_code} (×{salary_multiplier:.2f})",
                    f"Timeline adjusted for {request.timeline.value}",
                    f"Education filter: {', '.join(e.value for e in request.education_willingness)}",
                ],
            },
            "disclaimer": (
                "This roadmap is based on data analysis and labor market trends. "
                "It provides guidance for career exploration — individual outcomes "
                "vary based on experience, location, market conditions, and effort. "
                "Use this as a starting point, not a guarantee."
            ),
        }
        
        return response
    
    # =========================================================================
    # MATCHING
    # =========================================================================
    
    def _match_by_mos(
        self, mos_code: Optional[str], branch: Optional[str]
    ) -> list[dict]:
        """Find progression paths matching a MOS code."""
        if not mos_code:
            return []
        
        mos_upper = mos_code.upper().strip()
        path_ids = self.mos_index.get(mos_upper, [])
        
        matched = []
        for pid in path_ids:
            path = self.path_index.get(pid)
            if path:
                # Score by demand rating (higher is better)
                score = path.get("demand_rating", 3)
                if branch and branch.lower() in [
                    b.lower() for b in path.get("source_branches", [])
                ]:
                    score += 1  # Bonus for branch match
                matched.append((score, path))
        
        # Sort by score descending
        matched.sort(key=lambda x: x[0], reverse=True)
        return [path for _, path in matched]
    
    def _match_by_target(
        self, target_role: Optional[str], target_industry: Optional[str]
    ) -> list[dict]:
        """Find progression paths matching a target role or industry."""
        matched = []
        
        if target_industry:
            industry_lower = target_industry.lower().strip().replace(" ", "_").replace("-", "_")
            path_ids = self.industry_index.get(industry_lower, [])
            for pid in path_ids:
                path = self.path_index.get(pid)
                if path:
                    matched.append(path)
            if not path_ids and industry_lower:
                for ind_key, path_ids in self.industry_index.items():
                    if industry_lower in ind_key or ind_key in industry_lower:
                        for pid in path_ids:
                            path = self.path_index.get(pid)
                            if path and path not in matched:
                                matched.append(path)
        
        if target_role and not matched:
            role_lower = target_role.lower()
            for path in self.path_data:
                if (
                    role_lower in path.get("path_name", "").lower()
                    or role_lower in path.get("target_career_field", "").lower()
                    or role_lower in path.get("path_description", "").lower()
                ):
                    matched.append(path)
        
        return matched

    def _fallback_paths(self, request: RoadmapRequest) -> list[dict]:
        """Return at least one path so we always generate a roadmap."""
        if not self.path_data:
            return []
        # If user gave an explicit target but we couldn't match curated paths,
        # return a synthetic path that actually ends at the chosen target.
        if request.target_role:
            return [self._build_synthetic_path(request)]
        if request.pathway == Pathway.DREAM_JOB and (
            request.target_industry or request.target_role
        ):
            by_target = self._match_by_target(
                request.target_role, request.target_industry
            )
            if by_target:
                return by_target
        return [self.path_data[0]]

    def _build_synthetic_path(self, request: RoadmapRequest) -> dict:
        """
        Build a lightweight, deterministic roadmap when no curated path matches.
        This keeps the Sankey aligned with the user's selected target role.
        """
        mos_code = (request.mos_code or "").strip()
        target_role = (request.target_role or "").strip() or "Target Role"
        industry_key = (request.target_industry or "other").strip().lower()

        # Friendly origin title
        origin_title = "Your background"
        if mos_code:
            try:
                from app.data.mos_titles import get_mos_title  # local import to avoid circulars

                mos_title = get_mos_title(mos_code)
                if mos_title:
                    origin_title = mos_title
                else:
                    origin_title = mos_code
            except Exception:
                origin_title = mos_code

        # Very simple role ladder heuristics
        role_lower = target_role.lower()
        if "manager" in role_lower:
            entry_role = "Operations Supervisor"
            growth_role = "Operations Manager"
            stretch_role = "Director of Operations"
        elif "analyst" in role_lower:
            entry_role = "Junior Analyst"
            growth_role = "Analyst"
            stretch_role = "Senior Analyst"
        elif "engineer" in role_lower or "developer" in role_lower:
            entry_role = "Junior " + target_role
            growth_role = target_role
            stretch_role = "Senior " + target_role
        else:
            entry_role = "Entry " + target_role
            growth_role = "Intermediate " + target_role
            stretch_role = "Senior " + target_role

        # Industry-sensitive credential suggestion (kept minimal for UI)
        if industry_key in ("business_finance", "management", "other"):
            cert_name = "CAPM (Project Management)"
        elif industry_key in ("technology", "cybersecurity"):
            cert_name = "CompTIA Security+"
        elif industry_key in ("healthcare",):
            cert_name = "Certified Healthcare Operations (baseline)"
        else:
            cert_name = "Foundational Credential"

        pid_seed = f"{mos_code}:{target_role}:{industry_key}"
        path_id = "synthetic_" + hashlib.sha1(pid_seed.encode("utf-8")).hexdigest()[:10]

        milestones = [
            {
                "milestone_id": f"{path_id}_m0",
                "phase": "origin",
                "sequence": 0,
                "title": origin_title,
                "description": "Starting point based on your background.",
                "timeline_start_months": 0,
                "timeline_end_months": 0,
                "duration_months": 0,
                "skills_from_military": [],
            },
            {
                "milestone_id": f"{path_id}_m1",
                "phase": "preparation",
                "sequence": 1,
                "title": "Credential & Transition Prep",
                "description": "Translate your experience, build core skills, and complete one foundational credential.",
                "timeline_start_months": 0,
                "timeline_end_months": 3,
                "duration_months": 3,
                "certifications": [
                    {
                        "name": cert_name,
                        "issuing_body": "Industry standard",
                        "estimated_cost": 0.0,
                        "va_covered": True,
                        "estimated_weeks": 8,
                    }
                ],
                "education": [
                    {
                        "education_type": "bachelor",
                        "field_of_study": f"Related to {target_role}",
                        "estimated_duration_months": 36,
                        "can_use_gi_bill": True,
                        "typical_cost_range": "$0 with GI Bill"
                    }
                ],
                "skillbridge_programs": [
                    {
                        "program_name": f"{target_role} Apprenticeship",
                        "company": "Industry Partner",
                        "duration_weeks": 12,
                        "url": ""
                    }
                ],
            },
            {
                "milestone_id": f"{path_id}_m2",
                "phase": "entry_role",
                "sequence": 2,
                "title": entry_role,
                "description": "Get into a first role adjacent to your target and build relevant experience.",
                "timeline_start_months": 3,
                "timeline_end_months": 12,
                "duration_months": 9,
            },
            {
                "milestone_id": f"{path_id}_m3",
                "phase": "growth_role",
                "sequence": 3,
                "title": growth_role,
                "description": "Expand scope and ownership; build repeatable accomplishments.",
                "timeline_start_months": 12,
                "timeline_end_months": 24,
                "duration_months": 12,
            },
            {
                "milestone_id": f"{path_id}_m4",
                "phase": "target_role",
                "sequence": 4,
                "title": target_role,
                "description": "Your selected target role.",
                "timeline_start_months": 24,
                "timeline_end_months": 36,
                "duration_months": 12,
            },
            {
                "milestone_id": f"{path_id}_m5",
                "phase": "stretch_role",
                "sequence": 5,
                "title": stretch_role,
                "description": "Optional next step after reaching your target role.",
                "timeline_start_months": 36,
                "timeline_end_months": 48,
                "duration_months": 12,
            },
        ]

        return {
            "path_id": path_id,
            "path_name": f"{origin_title} → {target_role}",
            "source_mos_codes": [mos_code] if mos_code else [],
            "source_branches": [],
            "source_skill_tags": [],
            "target_industry": industry_key or "other",
            "target_career_field": industry_key or "other",
            "target_soc_code": None,
            "total_timeline_months": 48,
            "difficulty_rating": 3,
            "demand_rating": 3,
            "salary_ceiling": None,
            "path_description": "Synthetic roadmap generated because no curated path matched the selected target.",
            "milestones": milestones,
        }
    
    # =========================================================================
    # PERSONALIZATION
    # =========================================================================
    
    def _personalize_milestones(
        self,
        milestones: list[dict],
        salary_multiplier: float,
        timeline_adjustment: dict,
        education_willingness: list,
        can_skillbridge: bool,
    ) -> list[dict]:
        """
        Create personalized copies of milestone templates.
        
        Adjusts:
        - Salaries for regional cost of living
        - Timelines based on urgency
        - Filters SkillBridge if not available
        - Filters education options by willingness
        """
        personalized = []
        prep_multiplier = timeline_adjustment["prep_multiplier"]
        overlap = timeline_adjustment["overlap_months"]
        
        for milestone in milestones:
            m = dict(milestone)  # Shallow copy
            
            # Adjust salaries
            m["salary_range_low"] = adjust_salary(
                m.get("salary_range_low"), salary_multiplier
            )
            m["salary_range_high"] = adjust_salary(
                m.get("salary_range_high"), salary_multiplier
            )
            m["salary_median"] = adjust_salary(
                m.get("salary_median"), salary_multiplier
            )
            
            # Adjust regional employer salaries
            if "employers" in m:
                for emp in m["employers"]:
                    if emp.get("estimated_salary_range"):
                        # Parse and adjust salary ranges in employer data
                        # In production, this would use BLS data per employer location
                        pass  # Keep curated ranges for now; BLS enrichment handles this
            
            # Adjust timeline for preparation phase
            phase = m.get("phase", "")
            if phase == "preparation":
                original_duration = m.get("duration_months", 0)
                m["duration_months"] = max(1, int(original_duration * prep_multiplier))
                m["timeline_end_months"] = m["timeline_start_months"] + m["duration_months"]
            
            # Apply overlap compression for later phases if urgent
            if phase in ("entry_role", "growth_role") and overlap > 0:
                m["timeline_start_months"] = max(
                    0, m.get("timeline_start_months", 0) - overlap
                )
                m["timeline_end_months"] = max(
                    m["timeline_start_months"] + 1,
                    m.get("timeline_end_months", 0) - overlap
                )
            
            # Filter SkillBridge if not available
            if not can_skillbridge and "skillbridge_programs" in m:
                m["skillbridge_note"] = (
                    "SkillBridge requires 180+ days remaining in service. "
                    "These programs may not be available given your timeline, "
                    "but similar training options exist through VA benefits."
                )
            
            # Filter education by willingness
            if "education" in m:
                ed_types = [e.value for e in education_willingness]
                m["education"] = [
                    e for e in m["education"]
                    if e.get("education_type") in ed_types
                    or e.get("education_type") == "on_the_job"
                ]
            
            # Default typical years experience for role phases (for card header display)
            if m.get("typical_years_experience") is None and phase in ("entry_role", "growth_role", "target_role"):
                m["typical_years_experience"] = {"entry_role": 1, "growth_role": 3, "target_role": 5}.get(phase)
            
            personalized.append(m)
        
        return personalized
    
    # =========================================================================
    # ENRICHMENT (hooks for live data services)
    # =========================================================================
    
    async def _enrich_skillbridge(
        self, milestones: list[dict], zip_code: str
    ) -> list[dict]:
        """
        Enrich preparation and entry milestones with live SkillBridge
        program data from the programs table.
        """
        for m in milestones:
            phase = m.get("phase", "")
            if phase not in ("preparation", "entry_role"):
                continue

            # Determine career field from the parent path context
            # (the generator stores this when personalizing)
            career_field = getattr(self, "_current_career_field", None)
            if not career_field:
                continue

            try:
                live_programs = await self.skillbridge_service.find_programs(
                    career_field=career_field,
                    zip_code=zip_code,
                    limit=3,
                )
                if live_programs:
                    existing = m.get("skillbridge_programs", [])
                    # Append live matches, avoiding duplicates by company name
                    existing_companies = {
                        p.get("company", "").lower() for p in existing
                    }
                    for lp in live_programs:
                        if lp["company"].lower() not in existing_companies:
                            existing.append(lp)
                            existing_companies.add(lp["company"].lower())
                    m["skillbridge_programs"] = existing[:6]
            except Exception as e:
                logger.warning("SkillBridge enrichment failed: %s", e)

        return milestones
    
    async def _enrich_yellow_ribbon(
        self, milestones: list[dict], zip_code: str
    ) -> list[dict]:
        """
        Enrich education milestones with Yellow Ribbon school data.
        Connects to existing Yellow Ribbon search.
        """
        # TODO: Query Yellow Ribbon schools by:
        # - CIP code matching education requirements
        # - Distance from veteran's ZIP
        # - Contribution amounts
        # For now, using curated data
        return milestones
    
    async def _enrich_bls_salary(
        self, milestones: list[dict], zip_code: str
    ) -> list[dict]:
        """
        Replace estimated salaries with BLS OEWS data for the region.
        """
        # TODO: Query BLS OEWS API by:
        # - SOC code from milestone
        # - Metro area from ZIP code lookup
        # This replaces the multiplier-based approach with real data
        return milestones
    
    # =========================================================================
    # SALARY PROGRESSION CHART
    # =========================================================================
    
    def _build_salary_progression(
        self, milestones: list[dict]
    ) -> list[dict]:
        """Build data points for the salary progression visualization."""
        points = []
        
        for m in milestones:
            if m.get("salary_median") is not None:
                # Start of phase
                points.append({
                    "month": m.get("timeline_start_months", 0),
                    "phase": m.get("phase", ""),
                    "role_title": m.get("title", ""),
                    "salary_low": m.get("salary_range_low", 0),
                    "salary_high": m.get("salary_range_high", 0),
                    "salary_median": m.get("salary_median", 0),
                })
                # End of phase (same salary)
                points.append({
                    "month": m.get("timeline_end_months", 0),
                    "phase": m.get("phase", ""),
                    "role_title": m.get("title", ""),
                    "salary_low": m.get("salary_range_low", 0),
                    "salary_high": m.get("salary_range_high", 0),
                    "salary_median": m.get("salary_median", 0),
                })
        
        return points
    
    # =========================================================================
    # HELPERS
    # =========================================================================
    
    def _generate_roadmap_id(self, request: RoadmapRequest) -> str:
        """Generate a deterministic roadmap ID for caching."""
        key = f"{request.pathway}:{request.mos_code}:{request.zip_code}:{request.timeline}"
        hash_val = hashlib.md5(key.encode()).hexdigest()[:12]
        return f"rm_{hash_val}"
    
    def _format_salary_range(self, milestone: Optional[dict]) -> Optional[str]:
        """Format a milestone's salary range as a display string."""
        if not milestone:
            return None
        low = milestone.get("salary_range_low")
        high = milestone.get("salary_range_high")
        if low and high:
            return f"${low:,} - ${high:,}"
        return None
    
    def _estimate_education_cost(
        self, milestones: list[dict], education_willingness: list
    ) -> str:
        """Estimate total education investment considering VA benefits."""
        # Most paths are $0 with VA benefits for certifications
        has_degree = any(
            e.value in ("associate", "bachelor", "master")
            for e in education_willingness
        )
        if has_degree:
            return "$0 with GI Bill (degree programs covered)"
        return "$0 - $500 with VA certification benefits"
    
    def _get_recommended_skillbridge(self, milestones: list[dict]) -> list[dict]:
        """Extract top SkillBridge recommendations across all milestones."""
        all_sb = []
        for m in milestones:
            all_sb.extend(m.get("skillbridge_programs", []))
        return all_sb[:3]  # Top 3
    
    def _calculate_confidence(self, path: dict, request: RoadmapRequest) -> float:
        """Calculate confidence score for this roadmap match."""
        base = 0.7
        
        # Higher confidence if MOS directly matches
        if request.mos_code and request.mos_code.upper() in [
            m.upper() for m in path.get("source_mos_codes", [])
        ]:
            base += 0.15
        
        # Higher confidence for well-established paths
        if path.get("demand_rating", 0) >= 4:
            base += 0.05
        
        # Lower confidence for tight timelines
        if request.timeline in (TimelineUrgency.IMMINENT, TimelineUrgency.ALREADY_OUT):
            base -= 0.05
        
        # Higher confidence for lower difficulty
        if path.get("difficulty_rating", 3) <= 2:
            base += 0.05
        
        return min(0.95, round(base, 2))
    
    def _confidence_notes(self, path: dict, request: RoadmapRequest) -> str:
        """Generate human-readable confidence notes."""
        difficulty = path.get("difficulty_rating", 3)
        demand = path.get("demand_rating", 3)
        
        if difficulty <= 2 and demand >= 4:
            return "Strong match. This career path has a direct connection to your military experience and high market demand."
        elif difficulty <= 3 and demand >= 3:
            return "Good match. This path requires some additional training but has solid market demand."
        elif difficulty >= 4:
            return "This is a significant career pivot requiring substantial investment. The roadmap provides a realistic timeline."
        return "Moderate match. Review the milestones carefully and consider alternative paths."
    
    def _build_no_match_response(self, request: RoadmapRequest) -> dict:
        """Return a helpful response when no paths match."""
        return {
            "roadmap_id": "no_match",
            "pathway_used": request.pathway.value,
            "origin": {
                "mos_code": request.mos_code,
                "branch": request.branch,
            },
            "milestones": [],
            "total_timeline_months": 0,
            "salary_progression": [],
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "confidence_score": 0.0,
                "confidence_notes": (
                    "No curated progression paths found for this combination. "
                    "Try the Career Pathfinder tool for general career matching, "
                    "or select a target industry using the Dream Job pathway."
                ),
            },
            "recommended_first_action": (
                "Use the Career Pathfinder to explore civilian roles matching "
                "your military skills, then return here with a target career."
            ),
            "disclaimer": (
                "We are continuously expanding our career progression database. "
                "If your MOS is not yet covered, the Career Pathfinder tool "
                "can still match you to civilian roles."
            ),
        }
