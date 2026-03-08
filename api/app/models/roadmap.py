"""
Career Roadmap Engine - Core Data Models
The FOB Platform

Defines the progression graph structure, milestone types,
and roadmap output format for veteran career pathways.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class Pathway(str, Enum):
    MOS_TO_CAREER = "mos_to_career"      # Pathway 1: MOS → Civilian Career
    DREAM_JOB = "dream_job"              # Pathway 2: Dream Job → Career Ladder

class MilestonePhase(str, Enum):
    ORIGIN = "origin"                    # Current military position
    PREPARATION = "preparation"          # Certifications, training, SkillBridge
    ENTRY_ROLE = "entry_role"            # First civilian job
    GROWTH_ROLE = "growth_role"          # 1-2 year role
    TARGET_ROLE = "target_role"          # End goal position
    STRETCH_ROLE = "stretch_role"        # Optional aspirational beyond target

class EducationType(str, Enum):
    CERTIFICATION = "certification"
    BOOTCAMP = "bootcamp"
    ASSOCIATE = "associate"
    BACHELOR = "bachelor"
    MASTER = "master"
    SKILLBRIDGE = "skillbridge"
    ON_THE_JOB = "on_the_job"

class TimelineUrgency(str, Enum):
    PLANNING_AHEAD = "12_plus_months"     # 12+ months out
    TRANSITIONING = "6_12_months"         # 6-12 months
    IMMINENT = "3_6_months"              # 3-6 months
    ALREADY_OUT = "already_separated"     # Already separated
    JUST_EXPLORING = "just_exploring"     # Just exploring

class EmployerVetStatus(str, Enum):
    VET_FRIENDLY = "veteran_friendly"     # Known veteran hiring programs
    VET_OWNED = "veteran_owned"
    DEFENSE_CONTRACTOR = "defense_contractor"
    GENERAL = "general"


# =============================================================================
# REQUEST MODELS
# =============================================================================

class RoadmapRequest(BaseModel):
    """Input from the veteran to generate a career roadmap."""

    pathway: Pathway
    
    # Pathway 1 inputs
    branch: Optional[str] = Field(None, description="Military branch")
    mos_code: Optional[str] = Field(None, description="MOS/AFSC/Rating code")
    duties_description: Optional[str] = Field(None, description="Free text duties")
    
    # Pathway 2 inputs
    target_role: Optional[str] = Field(None, description="Dream job title or SOC code")
    target_industry: Optional[str] = Field(None, description="Target industry")
    
    # Shared inputs
    zip_code: Optional[str] = Field(None, description="5-digit ZIP for regional data; omit for national averages")
    timeline: TimelineUrgency = Field(
        TimelineUrgency.TRANSITIONING,
        description="How soon transitioning"
    )
    education_willingness: list[EducationType] = Field(
        default_factory=lambda: [EducationType.CERTIFICATION],
        description="Types of education the veteran is open to"
    )
    skillbridge_interest: bool = Field(True, description="Whether veteran is interested in SkillBridge programs")
    selected_industry: Optional[str] = Field(None, description="Industry selected from MOS career options")
    selected_entry_role: Optional[str] = Field(None, description="Entry role selected from MOS career options")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "pathway": "mos_to_career",
                    "branch": "army",
                    "mos_code": "11B",
                    "zip_code": "80202",
                    "timeline": "6_12_months",
                    "education_willingness": ["certification", "skillbridge"]
                },
                {
                    "pathway": "dream_job",
                    "target_role": "Cybersecurity Analyst",
                    "target_industry": "technology",
                    "timeline": "already_separated",
                    "education_willingness": ["certification", "bootcamp"]
                }
            ]
        }


# =============================================================================
# PROGRESSION GRAPH MODELS (the core data structure)
# =============================================================================

class CertificationRequirement(BaseModel):
    """A certification needed at a milestone."""
    name: str                                    # e.g., "CompTIA Security+"
    issuing_body: str                            # e.g., "CompTIA"
    estimated_cost: float                        # Dollar amount
    va_covered: bool = False                     # Can VA benefits cover this?
    estimated_weeks: int                         # Study/completion time
    url: Optional[str] = None                    # Official cert page
    prerequisite_certs: list[str] = Field(default_factory=list)
    military_discount: bool = False
    voucher_available: bool = False              # Free exam voucher programs

class EducationRequirement(BaseModel):
    """An education requirement at a milestone."""
    education_type: EducationType
    field_of_study: str                          # e.g., "Computer Science"
    cip_code: Optional[str] = None               # Classification code
    estimated_duration_months: int
    can_use_gi_bill: bool = True
    typical_cost_range: Optional[str] = None     # e.g., "$15,000-$40,000"

class SkillRequirement(BaseModel):
    """A skill needed for a role in the progression."""
    skill_name: str
    proficiency_needed: str = "intermediate"     # beginner, intermediate, advanced
    military_transferable: bool = False          # Already have from service?
    gap_closing_resource: Optional[str] = None   # How to learn it

class Employer(BaseModel):
    """A specific employer relevant to a milestone role."""
    company_name: str
    vet_status: EmployerVetStatus = EmployerVetStatus.GENERAL
    careers_url: Optional[str] = None
    typical_roles: list[str] = Field(default_factory=list)
    notes: Optional[str] = None                  # e.g., "Has veteran ERG"
    glassdoor_rating: Optional[float] = None
    estimated_salary_range: Optional[str] = None

class SkillBridgeLink(BaseModel):
    """Link to a specific SkillBridge program relevant to this milestone."""
    program_name: str
    company: str
    skillbridge_id: Optional[str] = None         # Our internal SkillBridge Explorer ID
    location: Optional[str] = None
    duration_weeks: Optional[int] = None
    url: Optional[str] = None

class YellowRibbonSchool(BaseModel):
    """A Yellow Ribbon school relevant to education at this milestone."""
    school_name: str
    program_name: str
    campus_type: str                             # "online", "on-campus", "hybrid"
    distance_miles: Optional[float] = None       # From veteran's zip
    contribution_amount: Optional[str] = None    # e.g., "$5,000" or "unlimited"
    max_students: Optional[str] = None
    url: Optional[str] = None


class Milestone(BaseModel):
    """
    A single node in the career progression graph.
    
    Each milestone represents a phase in the veteran's journey
    from military service to their target civilian career.
    """
    
    # Identity
    milestone_id: str                            # Unique ID e.g., "ms_entry_soc_analyst"
    phase: MilestonePhase
    sequence: int                                # Order in the progression (0-indexed)
    
    # Role Info
    title: str                                   # Display title, e.g., "SOC Analyst I"
    soc_code: Optional[str] = None               # O*NET SOC code
    description: str                             # What this role/phase involves
    
    # Timeline
    timeline_start_months: int                   # Months from start of journey
    timeline_end_months: int                     # Months from start of journey
    duration_months: int                         # How long in this phase
    
    # Compensation
    salary_range_low: Optional[int] = None       # Regional salary floor
    salary_range_high: Optional[int] = None      # Regional salary ceiling
    salary_median: Optional[int] = None          # Regional median
    
    # Requirements
    certifications: list[CertificationRequirement] = Field(default_factory=list)
    education: list[EducationRequirement] = Field(default_factory=list)
    skills_required: list[SkillRequirement] = Field(default_factory=list)
    skills_from_military: list[str] = Field(default_factory=list)  # Skills that transfer
    
    # Connections to FOB features
    skillbridge_programs: list[SkillBridgeLink] = Field(default_factory=list)
    yellow_ribbon_schools: list[YellowRibbonSchool] = Field(default_factory=list)
    employers: list[Employer] = Field(default_factory=list)
    
    # Progression logic
    advancement_criteria: list[str] = Field(default_factory=list)  # What gets you to next
    typical_time_to_advance: Optional[str] = None  # e.g., "12-18 months"
    
    # Narrative
    veteran_tip: Optional[str] = None            # Tactical advice for vets
    military_advantage: Optional[str] = None     # Why military experience helps here


# =============================================================================
# CAREER PROGRESSION PATH (the template)
# =============================================================================

class CareerProgressionPath(BaseModel):
    """
    A complete career progression template.
    
    This is the reusable blueprint — e.g., "Infantry → Cybersecurity"
    or "Logistics → Supply Chain Management". These are curated paths
    stored in our database that get personalized per veteran.
    """
    
    path_id: str                                 # e.g., "infantry_to_cybersec"
    path_name: str                               # e.g., "Infantry → Cybersecurity Analyst"
    
    # Source MOS mapping
    source_mos_codes: list[str]                  # MOS codes this path applies to
    source_branches: list[str]                   # Which branches
    source_skill_tags: list[str]                 # General skill categories
    
    # Target career
    target_industry: str                         # e.g., "technology"
    target_career_field: str                     # e.g., "cybersecurity"
    target_soc_code: str                         # Primary target SOC code
    
    # The progression
    milestones: list[Milestone]                  # Ordered milestone sequence
    
    # Metadata
    total_timeline_months: int                   # Typical end-to-end
    difficulty_rating: int = Field(ge=1, le=5)   # 1=direct transfer, 5=major pivot
    demand_rating: int = Field(ge=1, le=5)       # Job market demand
    salary_ceiling: Optional[int] = None         # Top-end salary at target
    
    # Content
    path_description: str                        # Why this path works
    military_advantage_summary: str              # Key advantages vets bring
    common_pitfalls: list[str] = Field(default_factory=list)
    success_stories: list[str] = Field(default_factory=list)  # Brief anecdotes
    
    # Relationships
    alternative_paths: list[str] = Field(default_factory=list)  # Other path_ids
    related_communities: list[str] = Field(default_factory=list)  # FOB community IDs
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# ROADMAP RESPONSE (personalized output)
# =============================================================================

class SalaryProgressionPoint(BaseModel):
    """A data point for the salary progression chart."""
    month: int
    phase: str
    role_title: str
    salary_low: int
    salary_high: int
    salary_median: int

class RoadmapMetadata(BaseModel):
    """Metadata about the generated roadmap."""
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    data_sources: dict = Field(default_factory=lambda: {
        "career_mapping": "O*NET 28.0 + Military Crosswalk",
        "labor_data": "BLS OEWS",
        "education": "IPEDS + VA WEAMS",
        "skillbridge": "DoD SkillBridge"
    })
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_notes: str = ""
    personalization_factors: list[str] = Field(default_factory=list)

class RoadmapResponse(BaseModel):
    """
    The complete personalized career roadmap returned to the veteran.
    
    This is the final output that powers the visual journey map on the frontend.
    """
    
    # Identity
    roadmap_id: str
    pathway_used: Pathway
    
    # Origin summary
    origin: dict = Field(
        description="Veteran's starting point summary",
        default_factory=dict
        # Contains: mos_code, branch, role_title, transferable_skills[]
    )
    
    # The journey
    milestones: list[Milestone]                  # Personalized milestone sequence
    total_timeline_months: int
    
    # Salary visualization data
    salary_progression: list[SalaryProgressionPoint] = Field(default_factory=list)
    
    # Summary stats
    estimated_salary_at_entry: Optional[str] = None
    estimated_salary_at_target: Optional[str] = None
    certifications_needed: int = 0
    education_investment: Optional[str] = None   # e.g., "$0 with VA benefits"
    
    # Recommendations
    recommended_first_action: str = ""           # The single most important next step
    recommended_skillbridge: list[SkillBridgeLink] = Field(default_factory=list)
    recommended_communities: list[str] = Field(default_factory=list)
    
    # Alternative paths
    alternative_roadmaps: list[dict] = Field(
        default_factory=list,
        description="Brief summaries of other paths this veteran could take"
    )
    
    # Metadata
    metadata: RoadmapMetadata = Field(default_factory=RoadmapMetadata)
    disclaimer: str = (
        "This roadmap is based on data analysis and labor market trends. "
        "It provides guidance for career exploration — individual outcomes "
        "vary based on experience, location, market conditions, and effort. "
        "Use this as a starting point, not a guarantee."
    )
