"""
AI-Powered Roadmap Generation Service
The FOB Platform

Uses Claude (Anthropic) to dynamically generate career roadmaps
for any MOS code or target role combination.  Curated paths from
progression_paths.py are injected as few-shot examples.
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Optional

import anthropic

from app.config import get_settings
from app.models.roadmap import (
    RoadmapRequest,
    RoadmapResponse,
    Pathway,
)
from app.data.progression_paths import CAREER_PROGRESSION_PATHS
from app.services.roadmap_generator import (
    get_salary_multiplier,
    get_timeline_adjustment,
    RoadmapGenerator,
)

logger = logging.getLogger(__name__)


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """You are a career transition advisor for the U.S. military veteran career platform "The FOB" (Forward Operating Base). Your role is to generate detailed, realistic career roadmaps that guide veterans from their military service to successful civilian careers.

## Your Knowledge
You have deep knowledge of:
- All U.S. military MOS codes (Army), AFSCs (Air Force), Ratings (Navy/Coast Guard), and MOSs (Marines)
- How military skills translate to civilian careers
- Industry certifications, their costs, VA coverage, and timelines
- Realistic salary ranges by region and experience level
- Major veteran-friendly employers and defense contractors
- DoD SkillBridge programs
- VA education benefits (GI Bill, VR&E, VA certification reimbursement)
- Timeline realities for career transitions

## Output Requirements
Generate a career roadmap using the generate_career_roadmap tool. The roadmap MUST follow this exact structure:

### Milestones
Each roadmap MUST have exactly 5 milestones in this sequence:
1. phase: "origin" (sequence: 0) — Current military role with transferable skills
2. phase: "preparation" (sequence: 1) — Certifications, training, SkillBridge during transition
3. phase: "entry_role" (sequence: 2) — First civilian job in the field
4. phase: "growth_role" (sequence: 3) — Mid-level role after 1-3 years
5. phase: "target_role" (sequence: 4) — Career goal position

### Preparation Milestone — CRITICAL: Generate Multiple Paths
The preparation milestone (phase: "preparation", sequence: 1) powers a visual career map
with branching alternative pathways. To create a rich, useful map, this milestone MUST
contain ALL THREE of the following arrays, each with MULTIPLE items:

- **certifications**: Include 2-3 certifications ranging from foundational to advanced.
  Each cert should be genuinely relevant to the TARGET career (not to unrelated fields).
  Include at least one entry-level cert and one advanced/specialized cert.
  Example: for Robotics Engineers, include certs like "Certified Robotics System Integrator",
  "Fanuc Robot Programming Certificate", or "Siemens Mechatronic Systems Certification".

- **education**: Include 1-2 formal degree/education paths when the target role typically
  requires or prefers them. Use education_type values: associate, bachelor, master, bootcamp.
  Example: "BS Mechanical Engineering" or "AS Robotics Technology".

- **skillbridge_programs**: Include 2 SkillBridge programs from REAL companies that offer
  relevant training. Each needs: program_name, company, duration_weeks, url.
  Example: "Lockheed Martin Engineering Apprenticeship", "Northrop Grumman STEM Intern".

The more items you provide in these arrays, the richer the visual career map will be.
Do NOT leave any of these arrays empty for the preparation milestone.

### salary_progression Array
Create one data point per milestone phase that has salary data (skip origin/preparation). Each point: {month, phase, role_title, salary_low, salary_high, salary_median}. Also add intermediate points at the start and end of each role for smooth chart rendering.

### Employer vet_status Values
Must be one of: "veteran_friendly", "veteran_owned", "defense_contractor", "general"

### Education Requirements (Degrees)
- For EACH milestone (especially entry_role, growth_role, target_role), include an "education" array when the role or industry typically requires formal degrees.
- Use industry norms: e.g. nursing/healthcare often requires Associate or Bachelor in Nursing; many management/senior roles require Bachelor's; some senior/analyst roles prefer Master's. Tech roles may need only certs/bootcamps; skilled trades may need apprenticeships or associate degrees.
- Each education item: education_type (one of: certification, bootcamp, associate, bachelor, master, skillbridge, on_the_job), field_of_study (e.g. "Nursing", "Business Administration", "Computer Science"), estimated_duration_months, can_use_gi_bill (true for degree programs), typical_cost_range (e.g. "$15,000-$40,000" or "$0 with GI Bill").
- Include degree requirements that are typical for the job title and industry even when certifications are also listed. Do not omit higher education (associate/bachelor/master) for roles where employers commonly require or prefer it.
- For each role milestone (entry_role, growth_role, target_role), set "typical_years_experience" to the typical/average years of industry experience employers expect for that role (e.g. entry 0-2, growth 2-5, target 5-10). Use a single integer; null only for origin/preparation.

### Quality Standards
- Certifications must be REAL with accurate costs, issuing bodies, and URLs
- Employers must be REAL companies that actually hire for these roles
- Timelines must be REALISTIC (not compressed to look easy)
- Skills must accurately reflect what the role requires
- Veteran tips must be TACTICAL and specific, not generic motivation
- Military advantages must be CONCRETE, not vague
- estimated_salary_at_entry and estimated_salary_at_target must be strings like "$58,000 - $82,000"

### Target Role / Goal
- When the user message specifies a Target Role and/or Target Industry, the roadmap MUST end at that target (or a very close variant, e.g. "General and Operations Managers" or "Operations Manager"). Do NOT substitute a different career goal (e.g. do not suggest Cybersecurity or Security roles if they chose General and Operations Managers or another management/operations target).
- If the user message includes a "CRITICAL — USER'S CHOSEN TARGET" section, that target overrides any suggestion from the few-shot example. Use the example only for structure and level of detail; the final target_role milestone and all progression steps MUST lead to the user's chosen target.

## Few-Shot Example
Here is an example of a high-quality curated career roadmap. Match this level of detail and realism:

{{FEW_SHOT_EXAMPLE}}

Generate a roadmap for the veteran described in the user message. Make it specific to their MOS/role, realistic, and actionable."""


# =============================================================================
# TOOL SCHEMA (forces structured JSON output)
# =============================================================================

ROADMAP_TOOL_SCHEMA = {
    "type": "object",
    "required": [
        "origin", "milestones", "total_timeline_months",
        "salary_progression", "estimated_salary_at_entry",
        "estimated_salary_at_target", "certifications_needed",
        "recommended_first_action", "recommended_skillbridge",
        "recommended_communities", "metadata"
    ],
    "properties": {
        "origin": {
            "type": "object",
            "required": ["role_title", "transferable_skills"],
            "properties": {
                "mos_code": {"type": ["string", "null"]},
                "branch": {"type": ["string", "null"]},
                "role_title": {"type": "string"},
                "transferable_skills": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "milestones": {
            "type": "array",
            "minItems": 4,
            "maxItems": 6,
            "items": {
                "type": "object",
                "required": [
                    "milestone_id", "phase", "sequence", "title",
                    "description", "timeline_start_months",
                    "timeline_end_months", "duration_months"
                ],
                "properties": {
                    "milestone_id": {"type": "string"},
                    "phase": {
                        "type": "string",
                        "enum": [
                            "origin", "preparation", "entry_role",
                            "growth_role", "target_role", "stretch_role"
                        ]
                    },
                    "sequence": {"type": "integer"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "timeline_start_months": {"type": "integer"},
                    "timeline_end_months": {"type": "integer"},
                    "duration_months": {"type": "integer"},
                    "salary_range_low": {"type": ["integer", "null"]},
                    "salary_range_high": {"type": ["integer", "null"]},
                    "salary_median": {"type": ["integer", "null"]},
                    "certifications": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": [
                                "name", "issuing_body",
                                "estimated_cost", "va_covered",
                                "estimated_weeks"
                            ],
                            "properties": {
                                "name": {"type": "string"},
                                "issuing_body": {"type": "string"},
                                "estimated_cost": {"type": "number"},
                                "va_covered": {"type": "boolean"},
                                "estimated_weeks": {"type": "integer"},
                                "url": {"type": ["string", "null"]},
                                "prerequisite_certs": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "military_discount": {"type": "boolean"},
                                "voucher_available": {"type": "boolean"}
                            }
                        }
                    },
                    "education": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "education_type": {"type": "string"},
                                "field_of_study": {"type": "string"},
                                "estimated_duration_months": {"type": "integer"},
                                "can_use_gi_bill": {"type": "boolean"},
                                "typical_cost_range": {"type": ["string", "null"]}
                            }
                        }
                    },
                    "skills_required": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": [
                                "skill_name", "proficiency_needed",
                                "military_transferable"
                            ],
                            "properties": {
                                "skill_name": {"type": "string"},
                                "proficiency_needed": {"type": "string"},
                                "military_transferable": {"type": "boolean"},
                                "gap_closing_resource": {
                                    "type": ["string", "null"]
                                }
                            }
                        }
                    },
                    "skills_from_military": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "employers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["company_name", "vet_status"],
                            "properties": {
                                "company_name": {"type": "string"},
                                "vet_status": {
                                    "type": "string",
                                    "enum": [
                                        "veteran_friendly",
                                        "veteran_owned",
                                        "defense_contractor",
                                        "general"
                                    ]
                                },
                                "careers_url": {
                                    "type": ["string", "null"]
                                },
                                "typical_roles": {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                "notes": {"type": ["string", "null"]},
                                "glassdoor_rating": {
                                    "type": ["number", "null"]
                                },
                                "estimated_salary_range": {
                                    "type": ["string", "null"]
                                }
                            }
                        }
                    },
                    "skillbridge_programs": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["program_name", "company"],
                            "properties": {
                                "program_name": {"type": "string"},
                                "company": {"type": "string"},
                                "duration_weeks": {
                                    "type": ["integer", "null"]
                                },
                                "url": {"type": ["string", "null"]}
                            }
                        }
                    },
                    "advancement_criteria": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "typical_years_experience": {
                        "type": ["integer", "null"],
                        "description": "Typical years of industry experience for this role (e.g. 2 for entry, 5 for senior)"
                    },
                    "veteran_tip": {"type": ["string", "null"]},
                    "military_advantage": {"type": ["string", "null"]}
                }
            }
        },
        "total_timeline_months": {"type": "integer"},
        "salary_progression": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "month", "phase", "role_title",
                    "salary_low", "salary_high", "salary_median"
                ],
                "properties": {
                    "month": {"type": "integer"},
                    "phase": {"type": "string"},
                    "role_title": {"type": "string"},
                    "salary_low": {"type": "integer"},
                    "salary_high": {"type": "integer"},
                    "salary_median": {"type": "integer"}
                }
            }
        },
        "estimated_salary_at_entry": {"type": "string"},
        "estimated_salary_at_target": {"type": "string"},
        "certifications_needed": {"type": "integer"},
        "education_investment": {"type": ["string", "null"]},
        "recommended_first_action": {"type": "string"},
        "recommended_skillbridge": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "program_name": {"type": "string"},
                    "company": {"type": "string"},
                    "duration_weeks": {"type": ["integer", "null"]},
                    "url": {"type": ["string", "null"]}
                }
            }
        },
        "recommended_communities": {
            "type": "array",
            "items": {"type": "string"}
        },
        "alternative_roadmaps": {
            "type": "array",
            "items": {"type": "object"}
        },
        "metadata": {
            "type": "object",
            "required": ["confidence_score", "confidence_notes"],
            "properties": {
                "generated_at": {"type": "string"},
                "data_sources": {"type": "object"},
                "confidence_score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                },
                "confidence_notes": {"type": "string"},
                "personalization_factors": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
    }
}


# =============================================================================
# AI ROADMAP GENERATOR
# =============================================================================

class AIRoadmapGenerator:
    """
    Generates career roadmaps using Claude AI.

    Falls back to curated path matching (RoadmapGenerator) if:
    - Claude API call fails
    - Response fails Pydantic validation
    - API key is not configured
    """

    def __init__(
        self,
        skillbridge_service=None,
        fallback_generator: Optional[RoadmapGenerator] = None,
    ):
        self.skillbridge_service = skillbridge_service
        self.fallback_generator = fallback_generator
        self._client = None
        self._settings = get_settings()

    @property
    def client(self) -> anthropic.Anthropic:
        """Lazy-init the Anthropic client."""
        if self._client is None:
            if not self._settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self._client = anthropic.Anthropic(
                api_key=self._settings.anthropic_api_key,
                timeout=120.0,
            )
        return self._client

    # ── Few-shot example selection ──

    def _select_few_shot_example(self, request: RoadmapRequest) -> dict:
        """Pick the most relevant curated path as a few-shot example.

        Selection priority:
          1. Target role title keyword match against path_name (avoids industry
             collisions like Robotics Engineers sharing 'technology' with cybersec).
          2. MOS code match against source_mos_codes.
          3. Target industry match.
          4. Generic fallback — a non-cybersecurity path unless the user
             actually chose a cybersecurity target.
        """
        best = None
        target_lower = (request.target_role or "").lower().strip()

        # 1. Try to match target role title keywords against curated path names
        if target_lower:
            # Extract meaningful keywords (skip short words)
            keywords = [w for w in target_lower.split() if len(w) > 3]
            for path in CAREER_PROGRESSION_PATHS:
                pname = (path.get("path_name") or "").lower()
                pfield = (path.get("target_career_field") or "").lower()
                if any(kw in pname or kw in pfield for kw in keywords):
                    best = path
                    break

        # 2. MOS code match
        if not best and request.pathway == Pathway.MOS_TO_CAREER and request.mos_code:
            mos = request.mos_code.upper().strip()
            for path in CAREER_PROGRESSION_PATHS:
                if mos in path.get("source_mos_codes", []):
                    best = path
                    break

        # 3. Target industry match — but skip cybersec if user's target is
        #    clearly not in that field
        if not best and request.target_industry:
            industry = request.target_industry.lower().strip()
            is_cyber_target = any(
                kw in target_lower
                for kw in ("cyber", "security", "soc analyst", "infosec")
            )
            for path in CAREER_PROGRESSION_PATHS:
                path_industry = (path.get("target_industry") or "").lower()
                if industry in path_industry:
                    # Don't pick a cybersec path when user wants something else
                    if "cybersec" in (path.get("path_id") or "") and not is_cyber_target:
                        continue
                    best = path
                    break

        # 4. Generic fallback — avoid cybersec unless user chose it
        if not best:
            is_cyber_target = any(
                kw in target_lower
                for kw in ("cyber", "security", "soc analyst", "infosec")
            )
            if is_cyber_target:
                best = next(
                    (p for p in CAREER_PROGRESSION_PATHS
                     if p["path_id"] == "combat_to_cybersec"),
                    CAREER_PROGRESSION_PATHS[0],
                )
            else:
                # Pick the first non-cybersec path as a more neutral example
                best = next(
                    (p for p in CAREER_PROGRESSION_PATHS
                     if "cybersec" not in (p.get("path_id") or "")),
                    CAREER_PROGRESSION_PATHS[0],
                )

        logger.info(
            "Few-shot example selected: path_id=%s for target='%s'",
            best.get("path_id"), request.target_role,
        )
        return best

    # ── Prompt building ──

    def _build_user_prompt(self, request: RoadmapRequest) -> str:
        """Build the user message for Claude."""
        multiplier = get_salary_multiplier(request.zip_code)
        timeline_adj = get_timeline_adjustment(request.timeline)

        if request.pathway == Pathway.MOS_TO_CAREER:
            core = (
                f"Generate a career roadmap for a veteran with:\n"
                f"- MOS Code: {request.mos_code or 'not specified'}\n"
                f"- Branch: {request.branch or 'not specified'}\n"
            )
            # CRITICAL: When user selected a target in the pathfinder, the roadmap MUST end at that target.
            if request.target_role or request.target_industry:
                target_name = request.target_role or request.target_industry or 'not specified'
                core += (
                    f"\n╔══════════════════════════════════════════════════════════╗\n"
                    f"║  MANDATORY TARGET — DO NOT CHANGE                       ║\n"
                    f"╚══════════════════════════════════════════════════════════╝\n"
                    f"- Target Role: {request.target_role or 'not specified'}\n"
                    f"- Target Industry: {request.target_industry or 'not specified'}\n\n"
                    f"RULES (violating any of these is WRONG):\n"
                    f"1. The milestone with phase 'target_role' MUST have title '{target_name}' (or a very close variant).\n"
                    f"2. ALL milestones (entry_role, growth_role) must be stepping stones TOWARD '{target_name}' — not toward any other career.\n"
                    f"3. Certifications and skills must be relevant to '{target_name}', NOT to unrelated fields.\n"
                    f"4. Do NOT copy the career target from the few-shot example. The example is for FORMAT ONLY.\n"
                    f"5. If the few-shot example shows a different career (e.g. cybersecurity), you MUST ignore that career path entirely and build one for '{target_name}'.\n\n"
                )
            if request.duties_description:
                core += f"- Duties: {request.duties_description}\n"
            # Include user's selected career direction if available
            if request.selected_industry:
                core += f"- Selected Industry: {request.selected_industry}\n"
            if request.selected_entry_role:
                core += f"- Target Entry Role: {request.selected_entry_role}\n"
        else:
            core = (
                f"Generate a career roadmap for a veteran targeting:\n"
                f"- Target Role: {request.target_role or 'not specified'}\n"
                f"- Target Industry: {request.target_industry or 'not specified'}\n"
            )
            if request.mos_code:
                core += f"- Current MOS: {request.mos_code}\n"
            if request.branch:
                core += f"- Branch: {request.branch}\n"

        # ZIP / salary context
        if request.zip_code:
            zip_line = f"- ZIP Code: {request.zip_code}\n"
            multiplier_line = (
                f"- Regional salary multiplier: {multiplier:.2f}x "
                f"(multiply all base salaries by this)\n"
            )
        else:
            zip_line = "- ZIP Code: National (no specific region)\n"
            multiplier_line = (
                f"- Regional salary multiplier: {multiplier:.2f}x "
                f"(national baseline)\n"
            )

        # SkillBridge interest
        skillbridge_eligible = timeline_adj["can_skillbridge"] and getattr(request, "skillbridge_interest", True)
        skillbridge_note = ""
        if not getattr(request, "skillbridge_interest", True):
            skillbridge_note = (
                "- NOTE: Veteran is NOT interested in SkillBridge. "
                "Do NOT include SkillBridge programs in the roadmap.\n"
            )

        core += (
            f"\nPersonalization:\n"
            f"{zip_line}"
            f"{multiplier_line}"
            f"- Timeline urgency: {request.timeline.value}\n"
            f"- Education willingness: "
            f"{', '.join(e.value for e in request.education_willingness)}\n"
            f"- SkillBridge eligible: {skillbridge_eligible}\n"
            f"{skillbridge_note}"
            f"\nREMINDER: The preparation milestone MUST contain at least 2-3 certifications, "
            f"1-2 education items, and 2 SkillBridge programs — all relevant to the target career. "
            f"This creates the branching visual career map.\n"
        )

        return core

    # ── Main generation ──

    async def generate(self, request: RoadmapRequest) -> dict:
        """
        Generate a career roadmap using Claude AI.
        Falls back to curated path matching on failure.
        """
        try:
            return await self._generate_with_ai(request)
        except Exception as e:
            logger.error(
                "AI roadmap generation failed: %s", e, exc_info=True
            )
            if self.fallback_generator:
                logger.info("Falling back to curated path matching")
                return await self.fallback_generator.generate(request)
            raise

    async def _generate_with_ai(self, request: RoadmapRequest) -> dict:
        """Make the Claude API call and return validated response."""

        # 1. Select few-shot example
        example = self._select_few_shot_example(request)

        # 2. Build prompts
        # Trim example to keep token count reasonable
        example_trimmed = {
            k: v for k, v in example.items()
            if k in (
                "path_id", "path_name", "target_industry",
                "target_career_field", "difficulty_rating",
                "demand_rating", "salary_ceiling",
                "total_timeline_months", "milestones",
            )
        }
        example_json = json.dumps(example_trimmed, indent=2, default=str)
        system = SYSTEM_PROMPT.replace(
            "{{FEW_SHOT_EXAMPLE}}",
            example_json[:8000]
        )
        user_prompt = self._build_user_prompt(request)

        # 3. Call Claude with tool_use
        logger.info(
            "Calling Claude AI for roadmap: pathway=%s mos=%s target=%s",
            request.pathway.value,
            request.mos_code,
            request.target_role,
        )

        response = self.client.messages.create(
            model=self._settings.anthropic_model,
            max_tokens=self._settings.anthropic_max_tokens,
            temperature=self._settings.anthropic_temperature,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
            tools=[{
                "name": "generate_career_roadmap",
                "description": (
                    "Generate a complete career roadmap JSON for a "
                    "transitioning veteran"
                ),
                "input_schema": ROADMAP_TOOL_SCHEMA,
            }],
            tool_choice={
                "type": "tool",
                "name": "generate_career_roadmap",
            },
        )

        # 4. Extract structured output
        tool_block = next(
            (b for b in response.content if b.type == "tool_use"),
            None,
        )
        if not tool_block:
            raise ValueError("Claude did not return a tool_use response")

        roadmap = tool_block.input

        # 5. Post-process
        roadmap["roadmap_id"] = self._generate_roadmap_id(request)
        roadmap["pathway_used"] = request.pathway.value
        roadmap["disclaimer"] = (
            "This roadmap is AI-generated based on labor market data "
            "and veteran career transition patterns. It provides "
            "guidance for career exploration \u2014 individual outcomes "
            "vary based on experience, location, market conditions, "
            "and effort. Use this as a starting point, not a guarantee."
        )

        # Ensure origin has MOS info
        origin = roadmap.get("origin", {})
        if request.mos_code and not origin.get("mos_code"):
            origin["mos_code"] = request.mos_code
        if request.branch and not origin.get("branch"):
            origin["branch"] = request.branch
        roadmap["origin"] = origin

        # Ensure metadata has generated_at and data_sources
        meta = roadmap.get("metadata", {})
        meta.setdefault("generated_at", datetime.utcnow().isoformat())
        meta.setdefault("data_sources", {
            "career_mapping": "Claude AI + O*NET/BLS data",
            "labor_data": "BLS Occupational Employment Statistics",
            "education": "Department of Education + VA",
            "skillbridge": "DoD SkillBridge program database",
            "progression": "AI-generated based on industry patterns",
        })
        meta.setdefault("personalization_factors", [
            f"Regional salary adjustment ({request.zip_code or 'national'})",
            f"Timeline: {request.timeline.value}",
            f"Education: {', '.join(e.value for e in request.education_willingness)}",
        ])
        roadmap["metadata"] = meta

        # Default missing optional fields
        roadmap.setdefault("alternative_roadmaps", [])
        roadmap.setdefault("education_investment", "$0 with VA benefits")
        roadmap.setdefault("recommended_communities", [])
        roadmap.setdefault("recommended_skillbridge", [])

        # 6. Validate against Pydantic (non-fatal)
        try:
            validated = RoadmapResponse(**roadmap)
            roadmap = validated.model_dump(mode="json")
        except Exception as e:
            logger.warning(
                "AI response partial Pydantic validation issue: %s", e
            )
            if "milestones" not in roadmap or not roadmap["milestones"]:
                raise

        logger.info(
            "AI roadmap generated: %s milestones, confidence=%.2f",
            len(roadmap.get("milestones", [])),
            roadmap.get("metadata", {}).get("confidence_score", 0),
        )

        return roadmap

    # ── Helpers ──

    @staticmethod
    def _generate_roadmap_id(request: RoadmapRequest) -> str:
        """Generate deterministic roadmap ID for caching."""
        key = (
            f"{request.pathway.value}:"
            f"{(request.mos_code or '').upper()}:"
            f"{(request.target_role or '').lower()}:"
            f"{(request.target_industry or '').lower()}:"
            f"{(request.selected_industry or '').lower()}:"
            f"{(request.selected_entry_role or '').lower()}:"
            f"{request.zip_code or ''}:"
            f"{request.timeline.value}:"
            f"{getattr(request, 'skillbridge_interest', True)}"
        )
        h = hashlib.md5(key.encode()).hexdigest()[:12]
        return f"rm_ai_{h}"


# =============================================================================
# AI CAREER OPTIONS GENERATOR (lightweight suggestions for MOS → career)
# =============================================================================

# Tool schema for career option suggestions
CAREER_OPTIONS_TOOL_SCHEMA = {
    "type": "object",
    "required": ["options"],
    "properties": {
        "options": {
            "type": "array",
            "minItems": 3,
            "maxItems": 5,
            "items": {
                "type": "object",
                "required": [
                    "industry", "entry_role", "career_field",
                    "demand_level", "salary_range"
                ],
                "properties": {
                    "industry": {
                        "type": "string",
                        "description": "Civilian industry name"
                    },
                    "entry_role": {
                        "type": "string",
                        "description": "Specific entry-level job title"
                    },
                    "career_field": {
                        "type": "string",
                        "description": "Broader career field category"
                    },
                    "demand_level": {
                        "type": "string",
                        "enum": ["High", "Medium", "Low"],
                        "description": "Current job market demand"
                    },
                    "salary_range": {
                        "type": "string",
                        "description": "National entry-level salary range, e.g. '$50,000 - $65,000'"
                    },
                }
            }
        }
    }
}

# In-memory cache for MOS options (persists across requests within same server process)
_mos_options_cache: dict[str, list[dict]] = {}


class AICareerOptionsGenerator:
    """
    Lightweight Claude call to suggest 3-5 career directions for any MOS code.

    Results are cached in-memory so repeat lookups are instant.
    Uses a small max_tokens and shorter timeout than full roadmap generation.
    """

    def __init__(self):
        self._settings = get_settings()
        self._client = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            if not self._settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self._client = anthropic.Anthropic(
                api_key=self._settings.anthropic_api_key,
                timeout=30.0,
            )
        return self._client

    async def suggest_career_options(
        self,
        mos_code: str,
        branch: Optional[str] = None,
        industry: Optional[str] = None,
        include_adjacent: bool = False,
    ) -> list[dict]:
        """
        Return 3-5 career direction options for a MOS code.

        Each option has: industry, entry_role, career_field, demand_level, salary_range.
        Results are cached in-memory for fast repeat lookups.
        industry: if set, bias or filter toward this target industry.
        include_adjacent: if True, return broader or adjacent career roles (related but not top direct matches).
        """
        cache_key = f"{mos_code.upper()}:{(branch or '').lower()}:{(industry or '').lower()}:adj_{include_adjacent}"
        if cache_key in _mos_options_cache:
            logger.info("Returning cached career options for %s", cache_key)
            return _mos_options_cache[cache_key]

        branch_text = f" ({branch})" if branch else ""
        industry_text = f" Prioritize or limit to the industry: {industry}." if industry else ""
        if include_adjacent:
            prompt = (
                f"Given MOS code {mos_code}{branch_text}, suggest 4 broader or adjacent civilian career "
                f"directions for a transitioning veteran—roles that are related to their skills but may be "
                f"in slightly different fields or a wider scope (e.g., adjacent industries, supporting roles, "
                f"or transferable skill applications).{industry_text}\n\n"
                f"For each option provide:\n"
                f"- industry: The civilian industry name\n"
                f"- entry_role: A specific entry-level job title\n"
                f"- career_field: The broader career field\n"
                f"- demand_level: 'High', 'Medium', or 'Low'\n"
                f"- salary_range: National entry-level salary range like '$50,000 - $65,000'\n\n"
                f"Focus on directions that are realistic next steps or adjacent to typical MOS transitions."
            )
        else:
            prompt = (
                f"Given MOS code {mos_code}{branch_text}, suggest 4 realistic "
                f"civilian career directions for a transitioning veteran.{industry_text}\n\n"
                f"For each option provide:\n"
                f"- industry: The civilian industry name (e.g., 'Technology', 'Healthcare')\n"
                f"- entry_role: A specific entry-level job title the veteran could realistically target\n"
                f"- career_field: The broader career field (e.g., 'Cybersecurity', 'Project Management')\n"
                f"- demand_level: 'High', 'Medium', or 'Low' based on current job market\n"
                f"- salary_range: National entry-level salary range like '$50,000 - $65,000'\n\n"
                f"Focus on directions where military skills genuinely transfer. "
                f"Be realistic about entry-level roles, not aspirational."
            )

        logger.info("Calling Claude AI for career options: MOS=%s", mos_code)

        try:
            response = self.client.messages.create(
                model=self._settings.anthropic_model,
                max_tokens=1500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
                tools=[{
                    "name": "suggest_career_options",
                    "description": "Return career direction options for a MOS code",
                    "input_schema": CAREER_OPTIONS_TOOL_SCHEMA,
                }],
                tool_choice={
                    "type": "tool",
                    "name": "suggest_career_options",
                },
            )

            tool_block = next(
                (b for b in response.content if b.type == "tool_use"),
                None,
            )
            if not tool_block:
                logger.warning("Claude did not return tool_use for career options")
                return []

            raw_options = tool_block.input.get("options", [])
            options = [
                {
                    "option_id": f"ai_{mos_code.lower()}_{i}",
                    "industry": opt.get("industry", ""),
                    "entry_role": opt.get("entry_role", ""),
                    "career_field": opt.get("career_field", ""),
                    "demand_level": opt.get("demand_level", "Medium"),
                    "salary_range": opt.get("salary_range", ""),
                    "source": "ai_generated",
                }
                for i, opt in enumerate(raw_options)
            ]

            # Cache for future requests
            _mos_options_cache[cache_key] = options
            logger.info(
                "Generated %d career options for MOS %s",
                len(options), mos_code,
            )
            return options

        except Exception as e:
            logger.error("AI career options generation failed: %s", e)
            return []
