"""
Career Roadmap API Router
The FOB Platform

Endpoints:
  POST /v1/roadmap/generate     - Generate a personalized career roadmap (or pathfinder Sankey)
  GET  /v1/roadmap/paths        - List available career progression paths
  GET  /v1/roadmap/paths/{id}   - Get details of a specific path
  GET  /v1/roadmap/mos/{code}/options - Quick MOS lookup
"""

import json
import hashlib
import logging
from typing import Optional

import structlog
from fastapi import APIRouter, HTTPException, Query, Request, Body
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roadmap import (
    Pathway,
    RoadmapRequest,
    TimelineUrgency,
)
from app.config import get_settings
from app.services.roadmap_generator import RoadmapGenerator
from app.services.ai_roadmap_generator import AIRoadmapGenerator, AICareerOptionsGenerator
from app.services.skillbridge_enrichment import SkillBridgeEnrichmentService
from app.services.sankey_builder import build_full_pathfinder_response
from app.data.progression_paths import (
    CAREER_PROGRESSION_PATHS,
    MOS_TO_PATHS,
    INDUSTRY_TO_PATHS,
    PATH_BY_ID,
    PATH_SUMMARY,
)
from app.data.mos_career_mapping_loader import get_options_for_mos as get_mapping_options_for_mos

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v1/roadmap", tags=["Career Roadmap"])


# ─── Helpers ───

def _normalize_industry(s: Optional[str]) -> str:
    """Normalize industry for filtering (e.g. 'Logistics & Supply Chain' -> 'logistics_supply_chain')."""
    if not s or not str(s).strip():
        return ""
    t = str(s).strip().lower().replace(" & ", " ").replace(" and ", " ")
    return "_".join(t.split())

def _build_curated_generator(skillbridge_service=None) -> RoadmapGenerator:
    """Build a RoadmapGenerator with curated paths."""
    return RoadmapGenerator(
        path_data=CAREER_PROGRESSION_PATHS,
        mos_index=MOS_TO_PATHS,
        industry_index=INDUSTRY_TO_PATHS,
        path_index=PATH_BY_ID,
        skillbridge_service=skillbridge_service,
    )


def _compute_cache_key(request: RoadmapRequest) -> str:
    """Deterministic cache key from request inputs."""
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


async def _check_cache(session: AsyncSession, roadmap_id: str) -> Optional[dict]:
    """Check generated_roadmaps table for a cached result."""
    try:
        result = await session.execute(
            text(
                "SELECT roadmap_data FROM generated_roadmaps "
                "WHERE roadmap_id = :rid AND expires_at > NOW()"
            ),
            {"rid": roadmap_id},
        )
        row = result.fetchone()
        if row:
            data = row[0]
            return json.loads(data) if isinstance(data, str) else data
    except Exception as e:
        logger.warning("Cache check failed: %s", e)
    return None


async def _store_cache(
    session: AsyncSession,
    roadmap: dict,
    request: RoadmapRequest,
):
    """Store generated roadmap in cache table."""
    try:
        await session.execute(
            text(
                "INSERT INTO generated_roadmaps "
                "(roadmap_id, pathway, mos_code, branch, target_role, "
                "target_industry, zip_code, timeline, roadmap_data, "
                "confidence_score) "
                "VALUES (:rid, :pathway, :mos, :branch, :target_role, "
                ":industry, :zip, :timeline, :data, :confidence) "
                "ON CONFLICT (roadmap_id) DO UPDATE SET "
                "roadmap_data = EXCLUDED.roadmap_data, "
                "expires_at = NOW() + INTERVAL '7 days'"
            ),
            {
                "rid": roadmap.get("roadmap_id", ""),
                "pathway": roadmap.get("pathway_used", ""),
                "mos": request.mos_code,
                "branch": request.branch,
                "target_role": request.target_role,
                "industry": request.target_industry,
                "zip": request.zip_code or "",
                "timeline": request.timeline.value,
                "data": json.dumps(roadmap, default=str),
                "confidence": (
                    roadmap.get("metadata", {}).get("confidence_score", 0)
                ),
            },
        )
        await session.commit()
        logger.info("Cached roadmap %s", roadmap.get("roadmap_id"))
    except Exception as e:
        logger.warning("Failed to cache roadmap: %s", e)


# =============================================================================
# PATHFINDER ADAPTER
# =============================================================================

def _separation_timeline_to_backend(value: str) -> str:
    """Map frontend separation_timeline (e.g. '0-6', '6-12') to backend TimelineUrgency value."""
    if not value:
        return "6_12_months"
    v = (value or "").strip().lower()
    if v in ("0-6", "0_6"):
        return "3_6_months"
    if v in ("6-12", "6_12"):
        return "6_12_months"
    if v in ("12-18", "12-18 months", "12_18"):
        return "12_plus_months"
    if v in ("18+", "18_plus"):
        return "12_plus_months"
    if v in ("6_12_months", "3_6_months", "12_plus_months", "already_separated", "just_exploring"):
        return v
    return "6_12_months"


def _pathfinder_body_to_request(body: dict) -> tuple[RoadmapRequest, str, dict]:
    """Convert pathfinder UI payload to RoadmapRequest. Returns (request, title, inputs_echo).
    Accepts either object style (current_role/target_role) or ID style (current_role_id/target_role_id).
    """
    # Support frontend payload: current_role_id, target_role_id, separation_timeline, education, years_in_role
    current = body.get("current_role")
    if current is None and body.get("current_role_id") is not None:
        cid = body["current_role_id"]
        current = {"code": cid, "title": cid, "value": cid}
    current = current or {}
    target = body.get("target_role")
    if target is None and body.get("target_role_id") is not None:
        tid = body["target_role_id"]
        target = {"id": tid, "title": tid, "value": tid, "industry_key": (body.get("target_industry") or "").strip()}
    target = target or {}
    if isinstance(current, dict):
        mos_code = current.get("code") or current.get("value") or current.get("title") or ""
        role_title = current.get("title") or current.get("code") or current.get("value") or "Your background"
    else:
        mos_code = str(current)
        role_title = str(current)
    if isinstance(target, dict):
        target_role = target.get("title") or target.get("id") or target.get("value") or ""
        # Prefer industry_key (pathfinder key from labor data, e.g. technology) for path matching
        target_industry = (target.get("industry_key") or target.get("industry") or body.get("target_industry") or "").strip()
        target_industry = target_industry.lower().replace(" ", "_").replace("-", "_") if target_industry else ""
    else:
        target_role = str(target)
        target_industry = ""
    location = body.get("location") or {}
    loc_value = location.get("value") if isinstance(location, dict) else location
    zip_code = str(loc_value) if (loc_value and str(loc_value).isdigit() and len(str(loc_value)) == 5) else None
    timeline_val = body.get("timeline") or body.get("separation_timeline")
    if timeline_val and isinstance(timeline_val, str) and "-" in timeline_val and "_" not in timeline_val:
        timeline_val = _separation_timeline_to_backend(timeline_val)
    elif not timeline_val or timeline_val in ("0-6", "6-12", "12-18", "18+"):
        timeline_val = _separation_timeline_to_backend(str(timeline_val or "6-12"))
    timeline_val = timeline_val or "6_12_months"
    try:
        timeline = TimelineUrgency(timeline_val)
    except ValueError:
        timeline = TimelineUrgency.TRANSITIONING
    pathway = Pathway.MOS_TO_CAREER if mos_code else Pathway.DREAM_JOB
    if not mos_code and (target_role or target_industry):
        pathway = Pathway.DREAM_JOB
    if mos_code and not target_role and not target_industry:
        pathway = Pathway.MOS_TO_CAREER
    req = RoadmapRequest(
        pathway=pathway,
        mos_code=mos_code or None,
        target_role=target_role or None,
        target_industry=target_industry or None,
        zip_code=zip_code,
        timeline=timeline,
        skillbridge_interest=True,
    )
    title = f"{role_title} → {target_role}" if (role_title and target_role) else (target_role or role_title or "Career Map")
    inputs_echo = {
        "current_role": current if isinstance(current, dict) else {"code": current, "title": role_title},
        "certifications": body.get("certifications") or [],
        "education": body.get("education") or body.get("education_willingness"),
        "years_experience": body.get("years_experience") or body.get("years_in_role"),
        "target": target if isinstance(target, dict) else {"id": target, "title": target_role},
        "location": loc_value or "anywhere",
        "timeline": timeline_val,
    }
    return req, title, inputs_echo


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/generate", summary="Generate a personalized career roadmap")
async def generate_roadmap(http_request: Request, body: dict = Body(default=None)):
    """
    Generate a complete personalized career roadmap for a veteran.

    **Pathfinder payload** (from Career Pathfinder UI): send
    current_role, target_role, certifications, education, years_experience,
    location, timeline. Response includes sankey diagram + summary.

    **Legacy payload**: send pathway, mos_code or target_role/target_industry,
    timeline, etc. Response is milestone-based roadmap.
    """
    if body is None:
        body = {}
    # Pathfinder UI sends current_role/target_role as objects, or current_role_id/target_role_id + separation_timeline
    pathfinder_mode = (
        isinstance(body.get("current_role"), dict)
        or isinstance(body.get("target_role"), dict)
        or (body.get("current_role_id") is not None and body.get("target_role_id") is not None)
        or (
            ("timeline" in body or "separation_timeline" in body)
            and ("current_role" in body or "target_role" in body or "current_role_id" in body or "target_role_id" in body)
            and (body.get("education") is not None or body.get("years_experience") is not None or body.get("years_in_role") is not None or "target_role" in body or "target_role_id" in body)
        )
    )
    if pathfinder_mode:
        try:
            request, title, inputs_echo = _pathfinder_body_to_request(body)
        except Exception as e:
            logger.exception("Pathfinder body parse failed: %s", e)
            raise HTTPException(status_code=422, detail={"error": str(e)})
    else:
        try:
            request = RoadmapRequest.model_validate(body)
        except Exception as e:
            raise HTTPException(status_code=422, detail={"error": str(e)})
        title = None
        inputs_echo = None

    if request.pathway == Pathway.MOS_TO_CAREER:
        if not request.mos_code and not request.duties_description and not request.target_role and not request.target_industry:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Provide current_role (with code/title) or target_role/target_industry",
                    "suggestion": "Select your current or most recent role and target career"
                }
            )
    elif request.pathway == Pathway.DREAM_JOB:
        if not request.target_role and not request.target_industry:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "DREAM_JOB requires target_role or target_industry",
                    "suggestion": "Provide a target job title or industry"
                }
            )

    use_ai = bool(settings.anthropic_api_key)
    session_factory = getattr(http_request.app.state, "session_factory", None)

    # Try with DB session (enrichment + caching) when available
    if session_factory:
        try:
            async with session_factory() as session:
                skillbridge_svc = SkillBridgeEnrichmentService(session)

                # Check cache first (AI-generated roadmaps only)
                if use_ai:
                    cache_key = _compute_cache_key(request)
                    cached = await _check_cache(session, cache_key)
                    if cached:
                        logger.info("Returning cached roadmap %s", cache_key)
                        return cached

                # Build generators
                curated = _build_curated_generator(
                    skillbridge_service=skillbridge_svc
                )

                if use_ai:
                    generator = AIRoadmapGenerator(
                        skillbridge_service=skillbridge_svc,
                        fallback_generator=curated,
                    )
                else:
                    generator = curated

                roadmap = await generator.generate(request)

                # Cache AI-generated results
                if use_ai and roadmap:
                    await _store_cache(session, roadmap, request)

                if pathfinder_mode and title and inputs_echo is not None:
                    path_id = (roadmap.get("metadata") or {}).get("path_id") or (roadmap.get("alternative_roadmaps") or [{}])[0].get("path_id") or "primary"
                    return build_full_pathfinder_response(roadmap, path_id, title, inputs_echo)
                return roadmap
        except Exception as e:
            logger.exception("Roadmap generate failed (with DB): %s", e)
            raise HTTPException(status_code=500, detail={"error": str(e), "message": "Roadmap generation failed"})

    # No DB or fallback: generate without enrichment/cache
    try:
        logger.debug("Generating roadmap without DB session")
        curated = _build_curated_generator()
        if use_ai:
            generator = AIRoadmapGenerator(fallback_generator=curated)
        else:
            generator = curated
        roadmap = await generator.generate(request)
        if pathfinder_mode and title and inputs_echo is not None:
            path_id = (roadmap.get("metadata") or {}).get("path_id") or "primary"
            return build_full_pathfinder_response(roadmap, path_id, title, inputs_echo)
        return roadmap
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Roadmap generate failed: %s", e)
        raise HTTPException(status_code=500, detail={"error": str(e), "message": "Roadmap generation failed"})


@router.get("/paths", summary="List available career progression paths")
async def list_paths(
    mos_code: Optional[str] = Query(
        None, description="Filter by MOS code to see matching paths"
    ),
    industry: Optional[str] = Query(
        None, description="Filter by target industry"
    ),
    branch: Optional[str] = Query(
        None, description="Filter by military branch"
    ),
):
    """
    List all curated career progression paths with optional filtering.

    Returns summary information — use GET /paths/{path_id} for full details.
    """
    results = list(PATH_SUMMARY)  # copy so filters don't mutate

    if mos_code:
        mos_upper = mos_code.upper().strip()
        matching_ids = MOS_TO_PATHS.get(mos_upper, [])
        results = [p for p in results if p["path_id"] in matching_ids]

    if industry:
        industry_lower = industry.lower().strip()
        matching_ids = INDUSTRY_TO_PATHS.get(industry_lower, [])
        results = [p for p in results if p["path_id"] in matching_ids]

    if branch:
        branch_lower = branch.lower().strip()
        results = [
            p for p in results
            if branch_lower in [
                b.lower() for b in PATH_BY_ID.get(
                    p["path_id"], {}
                ).get("source_branches", [])
            ]
        ]

    return {
        "total_paths": len(results),
        "paths": results,
        "available_industries": list(INDUSTRY_TO_PATHS.keys()),
        "available_mos_codes": sorted(MOS_TO_PATHS.keys()),
    }


@router.get(
    "/paths/{path_id}",
    summary="Get full details of a career progression path",
)
async def get_path_detail(path_id: str):
    """
    Get the complete career progression path with all milestones,
    certifications, employers, and guidance.
    """
    path = PATH_BY_ID.get(path_id)
    if not path:
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Path '{path_id}' not found",
                "available_paths": list(PATH_BY_ID.keys())
            }
        )
    return path


@router.get(
    "/mos/{mos_code}/options",
    summary="Career direction options for a MOS code",
)
async def mos_options(
    mos_code: str,
    branch: Optional[str] = Query(None, description="Military branch"),
    industry: Optional[str] = Query(None, description="Target industry to bias or filter options"),
    include_adjacent: bool = Query(False, description="Return broader/adjacent career roles instead of primary matches"),
):
    """
    Return industry + entry role options for a MOS code.

    For curated MOS codes, options are extracted from progression paths.
    For non-curated codes, options are AI-generated (cached after first call).
    Use industry to point MOS experience toward a specific industry.
    Use include_adjacent=true to get broader or adjacent role options when primary list doesn't match.
    """
    mos_upper = mos_code.upper().strip()

    # 1) Optional: algorithm/external MOS → career mapping file (skills/keywords)
    mapping_options = get_mapping_options_for_mos(mos_upper, industry_filter=industry)
    if mapping_options and not include_adjacent:
        # Return mapping options in API shape; optionally filter by industry already applied in loader
        options = [
            {
                "option_id": f"mapping_{mos_upper}_{i}",
                "industry": o.get("industry", ""),
                "entry_role": o.get("entry_role", ""),
                "career_field": o.get("career_field", ""),
                "demand_level": (str(o.get("demand_level") or "Medium").title()),
                "salary_range": o.get("salary_range", ""),
                "source": "mapping",
            }
            for i, o in enumerate(mapping_options)
        ]
        structlog.get_logger().info(
            "MOS options from mapping",
            mos=mos_upper,
            count=len(options),
            industry=industry or "(any)",
        )
        return {
            "mos_code": mos_upper,
            "options_count": len(options),
            "options": options,
            "ai_generation_available": bool(settings.anthropic_api_key),
        }

    # 2) Curated paths (progression_paths.py)
    path_ids = MOS_TO_PATHS.get(mos_upper, [])
    options = []
    if path_ids:
        # Extract industry/entry role from curated paths; filter by target industry when provided
        industry_norm = _normalize_industry(industry) if industry else ""
        for pid in path_ids:
            p = PATH_BY_ID.get(pid, {})
            p_industry_raw = (p.get("target_industry") or "").strip().lower()
            if industry_norm and p_industry_raw != industry_norm:
                continue
            p_industry = (p.get("target_industry") or "").replace("_", " ").title()
            entry_milestone = next(
                (m for m in p.get("milestones", [])
                 if m.get("phase") == "entry_role"),
                None,
            )
            demand = p.get("demand_rating", 3)
            entry_low = entry_milestone.get("salary_range_low") if entry_milestone else None
            entry_high = entry_milestone.get("salary_range_high") if entry_milestone else None
            salary_range = (
                f"${entry_low:,} - ${entry_high:,}"
                if entry_low and entry_high else None
            )
            options.append({
                "option_id": p.get("path_id"),
                "industry": p_industry,
                "entry_role": entry_milestone.get("title", "") if entry_milestone else p.get("path_name", ""),
                "career_field": (p.get("target_career_field") or "").replace("_", " ").title(),
                "demand_level": "High" if demand >= 4 else ("Medium" if demand >= 3 else "Low"),
                "salary_range": salary_range,
                "source": "curated",
            })
        if include_adjacent and settings.anthropic_api_key:
            try:
                generator = AICareerOptionsGenerator()
                adj = await generator.suggest_career_options(
                    mos_upper, branch, industry=industry, include_adjacent=True
                )
                options = adj
            except Exception as e:
                logger.error("Failed to generate adjacent career options: %s", e)
    elif settings.anthropic_api_key:
        # AI-generated options for non-curated MOS codes
        try:
            generator = AICareerOptionsGenerator()
            options = await generator.suggest_career_options(
                mos_upper, branch, industry=industry, include_adjacent=include_adjacent
            )
            # Filter to selected industry when provided
            if industry and options:
                industry_norm = _normalize_industry(industry)
                options = [
                    o for o in options
                    if _normalize_industry(o.get("industry")) == industry_norm
                ]
        except Exception as e:
            logger.error("Failed to generate career options: %s", e)

    return {
        "mos_code": mos_upper,
        "options_count": len(options),
        "options": options,
        "ai_generation_available": bool(settings.anthropic_api_key),
    }
