"""SQLAlchemy models for SkillBridge programs."""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text, DateTime, Date, ForeignKey,
    Index, create_engine
)
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ARRAY
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


class Base(DeclarativeBase):
    pass


class Program(Base):
    """A single SkillBridge program/opportunity."""

    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core fields (scraped from DoD site)
    company = Column(String(500), nullable=False, index=True)
    city = Column(String(200), nullable=True)
    state = Column(String(10), nullable=True, index=True)
    zip_code = Column(String(20), nullable=True)
    location_raw = Column(String(500), nullable=True)  # Original text
    nationwide = Column(Boolean, default=False, index=True)
    online = Column(Boolean, default=False, index=True)

    # Program details
    program_duration = Column(String(200), nullable=True)
    duration_min_days = Column(Integer, nullable=True)
    duration_max_days = Column(Integer, nullable=True)
    opportunity_type = Column(String(200), nullable=True)  # Internship, Apprenticeship, etc.
    delivery_method = Column(String(200), nullable=True)  # In-person, Virtual, Hybrid
    description = Column(Text, nullable=True)
    job_family = Column(String(500), nullable=True)  # Career field/industry
    target_moc = Column(String(500), nullable=True)  # Military Occupation Codes

    # Contact
    employer_poc_name = Column(String(300), nullable=True)
    employer_poc_email = Column(String(300), nullable=True)
    employer_website = Column(String(500), nullable=True)

    # Service branch eligibility
    army = Column(Boolean, default=False)
    navy = Column(Boolean, default=False)
    air_force = Column(Boolean, default=False)
    marines = Column(Boolean, default=False)
    coast_guard = Column(Boolean, default=False)
    space_force = Column(Boolean, default=False)

    # Geocoded location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geocode_quality = Column(String(50), nullable=True)  # exact, approximate, zip_centroid

    # Categorization (enriched)
    industry = Column(String(200), nullable=True, index=True)

    # Metadata
    source_url = Column(String(500), nullable=True)
    source_page = Column(Integer, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)

    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_programs_state_industry", "state", "industry"),
        Index("ix_programs_lat_lon", "latitude", "longitude"),
        Index("ix_programs_company_city", "company", "city"),
        Index("ix_programs_active_state", "is_active", "state"),
    )

    def __repr__(self):
        return f"<Program {self.id}: {self.company} - {self.city}, {self.state}>"

    def to_map_point(self):
        """Minimal dict for map rendering."""
        return {
            "id": self.id,
            "company": self.company,
            "city": self.city,
            "state": self.state,
            "lat": self.latitude,
            "lon": self.longitude,
            "industry": self.industry,
            "nationwide": self.nationwide,
        }


class NewsArticle(Base):
    """A scraped VA/veteran news article."""

    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    url = Column(String(1000), nullable=False, unique=True)
    source_name = Column(String(200), nullable=False, index=True)
    source_feed = Column(String(500), nullable=True)
    category = Column(String(50), nullable=False, default="policy", index=True)
    impact = Column(String(20), nullable=True)  # high, medium, null
    image_url = Column(String(1000), nullable=True)
    published_at = Column(DateTime, nullable=True, index=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_news_cat_published", "category", "published_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "source": self.source_name,
            "category": self.category,
            "catLabel": self.category.replace("_", " ").title()
                if self.category not in ("doge",) else self.category.upper(),
            "impact": self.impact,
            "image_url": self.image_url,
            "date": self.published_at.strftime("%b %d, %Y") if self.published_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }


class CommunityOrg(Base):
    """A veteran-affiliated 501(c)(3) / community organization from ProPublica."""

    __tablename__ = "community_orgs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ein = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(500), nullable=False, index=True)
    alternate_name = Column(String(500), nullable=True)
    city = Column(String(200), nullable=True, index=True)
    state = Column(String(10), nullable=True, index=True)
    zip_code = Column(String(20), nullable=True)
    address = Column(String(500), nullable=True)
    category = Column(String(50), nullable=False, default="service", index=True)  # FOB: service, outdoor, wellness, professional, arts, social, education
    ntee_code = Column(String(10), nullable=True)
    description = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    logo_url = Column(String(1000), nullable=True)  # Scraped or Clearbit logo URL
    tagline = Column(String(500), nullable=True)
    form_990_url = Column(String(1000), nullable=True)
    form_990_fiscal_year = Column(String(20), nullable=True)
    revenue = Column(Float, nullable=True)
    expenses = Column(Float, nullable=True)
    social_links = Column(JSON, nullable=True)  # {"facebook":"...", "twitter":"...", "instagram":"...", "linkedin":"...", "youtube":"..."}
    scraped_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_community_orgs_state_category", "state", "category"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "ein": self.ein,
            "name": self.name,
            "alternate_name": self.alternate_name,
            "city": self.city,
            "state": self.state,
            "zip": self.zip_code,
            "address": self.address,
            "category": self.category,
            "ntee_code": self.ntee_code,
            "description": self.description,
            "website": self.website,
            "logo_url": self.logo_url,
            "tagline": self.tagline,
            "url": self.website,  # alias for frontend "Visit Site"
            "form_990_url": self.form_990_url,
            "form_990_fiscal_year": self.form_990_fiscal_year,
            "revenue": self.revenue,
            "expenses": self.expenses,
            "social_links": self.social_links or {},
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class VeteranNetworkingResult(Base):
    """Scraped veteran networking events/opportunities (weekly scrape, queried by zip/state)."""

    __tablename__ = "veteran_networking_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), nullable=False, index=True)
    snippet = Column(Text, nullable=True)
    result_type = Column(String(50), nullable=True, default="Resource", index=True)  # Event, Chapter, Organization, Resource
    organization = Column(String(300), nullable=True)  # parent org if part of larger org
    location_text = Column(String(500), nullable=True)
    search_state = Column(String(2), nullable=True, index=True)  # 2-letter state this result was found for
    search_zip = Column(String(10), nullable=True, index=True)  # zip this result was found for (optional)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_vet_networking_state_scraped", "search_state", "scraped_at"),
        Index("ix_vet_networking_zip_scraped", "search_zip", "scraped_at"),
    )


class VeteranEvent(Base):
    """Veteran events in Supabase (weekly scrape); used by Employment Networking local search."""

    __tablename__ = "veteran_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), nullable=False, index=True)
    snippet = Column(Text, nullable=True)
    result_type = Column(String(50), nullable=True, default="Event", index=True)
    organization = Column(String(300), nullable=True)
    location_text = Column(String(500), nullable=True)
    state_code = Column(String(2), nullable=True, index=True)
    zip_code = Column(String(10), nullable=True, index=True)
    event_date = Column(Date, nullable=True)
    event_time = Column(String(100), nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    """Registered user (email-only gate)."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True)  # UUID as string
    email = Column(String(320), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class ScrapeLog(Base):
    """Track scraping runs."""

    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="running")  # running, completed, failed
    pages_scraped = Column(Integer, default=0)
    programs_found = Column(Integer, default=0)
    programs_new = Column(Integer, default=0)
    programs_updated = Column(Integer, default=0)
    programs_geocoded = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)


class CorporateErg(Base):
    """Corporate veteran ERG (Employee Resource Group) directory."""

    __tablename__ = "corporate_ergs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(500), nullable=False, unique=True, index=True)
    erg_name = Column(String(500), nullable=True)
    industry = Column(String(200), nullable=False, index=True)
    company_size = Column(String(50), nullable=True)  # small, medium, large, enterprise

    description = Column(Text, nullable=True)
    offerings = Column(ARRAY(Text), default=list, nullable=False)
    founded_year = Column(Integer, nullable=True)
    member_count = Column(Integer, nullable=True)

    careers_url = Column(String(1000), nullable=True)
    erg_url = Column(String(1000), nullable=True)
    company_website = Column(String(1000), nullable=True)
    contact_email = Column(String(320), nullable=True)
    linkedin_url = Column(String(1000), nullable=True)

    headquarters_city = Column(String(200), nullable=True)
    headquarters_state = Column(String(50), nullable=True)

    military_friendly_rating = Column(String(50), nullable=True)
    has_skillbridge = Column(Boolean, default=False, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    featured = Column(Boolean, default=False, nullable=False)

    data_sources = Column(ARRAY(Text), default=list, nullable=False)
    source_type = Column(String(50), default="scraped", nullable=False)
    submitted_by = Column(PG_UUID(as_uuid=True), nullable=True)

    scraped_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_ergs_industry", "industry"),
        Index("idx_ergs_company_size", "company_size"),
        Index("idx_ergs_verified", "verified"),
        Index("idx_ergs_featured", "featured"),
        Index("idx_ergs_rating", "military_friendly_rating"),
        Index("idx_ergs_skillbridge", "has_skillbridge"),
        Index("idx_ergs_source", "source_type"),
    )

    def to_dict(self):
        return {
            "id": str(self.id) if self.id else None,
            "company_name": self.company_name,
            "erg_name": self.erg_name,
            "industry": self.industry,
            "company_size": self.company_size,
            "description": self.description,
            "offerings": list(self.offerings) if self.offerings else [],
            "founded_year": self.founded_year,
            "member_count": self.member_count,
            "careers_url": self.careers_url,
            "erg_url": self.erg_url,
            "company_website": self.company_website,
            "contact_email": self.contact_email,
            "linkedin_url": self.linkedin_url,
            "headquarters_city": self.headquarters_city,
            "headquarters_state": self.headquarters_state,
            "military_friendly_rating": self.military_friendly_rating,
            "has_skillbridge": self.has_skillbridge,
            "verified": self.verified,
            "featured": self.featured,
            "data_sources": list(self.data_sources) if self.data_sources else [],
            "source_type": self.source_type,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ErgSubmission(Base):
    """Community-submitted ERG (pending moderation)."""

    __tablename__ = "erg_submissions"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submitted_by = Column(PG_UUID(as_uuid=True), nullable=True)
    submitter_email = Column(String(320), nullable=False)
    submitter_name = Column(String(300), nullable=True)
    submitter_role = Column(String(200), nullable=True)

    company_name = Column(String(500), nullable=False)
    erg_name = Column(String(500), nullable=True)
    industry = Column(String(200), nullable=True)
    company_size = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    offerings = Column(ARRAY(Text), default=list, nullable=False)
    founded_year = Column(Integer, nullable=True)
    member_count = Column(Integer, nullable=True)
    careers_url = Column(String(1000), nullable=True)
    erg_url = Column(String(1000), nullable=True)
    company_website = Column(String(1000), nullable=True)
    contact_email = Column(String(320), nullable=True)
    linkedin_url = Column(String(1000), nullable=True)
    headquarters_city = Column(String(200), nullable=True)
    headquarters_state = Column(String(50), nullable=True)
    has_skillbridge = Column(Boolean, default=False, nullable=False)

    status = Column(String(50), default="pending", nullable=False)
    reviewer_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    approved_erg_id = Column(PG_UUID(as_uuid=True), ForeignKey("corporate_ergs.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": str(self.id) if self.id else None,
            "submitted_by": str(self.submitted_by) if self.submitted_by else None,
            "submitter_email": self.submitter_email,
            "submitter_name": self.submitter_name,
            "submitter_role": self.submitter_role,
            "company_name": self.company_name,
            "erg_name": self.erg_name,
            "industry": self.industry,
            "company_size": self.company_size,
            "description": self.description,
            "offerings": list(self.offerings) if self.offerings else [],
            "founded_year": self.founded_year,
            "member_count": self.member_count,
            "careers_url": self.careers_url,
            "erg_url": self.erg_url,
            "company_website": self.company_website,
            "contact_email": self.contact_email,
            "linkedin_url": self.linkedin_url,
            "headquarters_city": self.headquarters_city,
            "headquarters_state": self.headquarters_state,
            "has_skillbridge": self.has_skillbridge,
            "status": self.status,
            "reviewer_notes": self.reviewer_notes,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "approved_erg_id": str(self.approved_erg_id) if self.approved_erg_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ════════════════════════════════════════════════════════════
# CAREER GRAPH MODELS
# ════════════════════════════════════════════════════════════

class Role(Base):
    """Military and civilian roles."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    branch = Column(String(50), nullable=True, index=True)
    industry = Column(String(100), nullable=True, index=True)
    level = Column(String(30), nullable=False, index=True)
    description = Column(Text, nullable=True)
    salary_low = Column(Integer, nullable=True)
    salary_high = Column(Integer, nullable=True)
    typical_experience_years = Column(Integer, default=0)
    clearance_helpful = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class Credential(Base):
    """Certifications, degrees, bootcamps, and SkillBridge programs."""
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(30), nullable=False, index=True)
    domain = Column(String(100), nullable=True, index=True)
    provider = Column(String(255), nullable=True)
    duration_months = Column(Float, nullable=True)
    cost_dollars = Column(Integer, nullable=True)
    cost_note = Column(String(255), nullable=True)
    difficulty = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class RoleSkill(Base):
    """Transferable skills for military roles."""
    __tablename__ = "role_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"))
    skill_name = Column(String(255), nullable=False)
    skill_category = Column(String(100), nullable=True)
    relevance = Column(String(20), default="high")


class CredentialPrereq(Base):
    """Prerequisites for earning a credential."""
    __tablename__ = "credential_prereqs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    credential_id = Column(Integer, ForeignKey("credentials.id", ondelete="CASCADE"))
    prereq_credential_id = Column(Integer, ForeignKey("credentials.id", ondelete="CASCADE"), nullable=True)
    prereq_education = Column(String(30), nullable=True)
    prereq_experience_years = Column(Integer, nullable=True)
    is_required = Column(Boolean, default=False)
    note = Column(String(255), nullable=True)


class CareerEdge(Base):
    """Directed edges representing career progression."""
    __tablename__ = "career_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=True, index=True)
    source_credential_id = Column(Integer, ForeignKey("credentials.id", ondelete="CASCADE"), nullable=True, index=True)
    target_role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=True, index=True)
    target_credential_id = Column(Integer, ForeignKey("credentials.id", ondelete="CASCADE"), nullable=True, index=True)
    weight = Column(Integer, default=10)
    typical_months = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    path_tags = Column(ARRAY(String), nullable=True)
    min_education = Column(String(30), nullable=True)
    max_education = Column(String(30), nullable=True)
    min_experience_years = Column(Integer, default=0)
    requires_clearance = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class RoleTargetMapping(Base):
    """Valid target roles for a given origin MOS/role."""
    __tablename__ = "role_target_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    origin_role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), index=True)
    target_role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"))
    relevance_score = Column(Float, default=0.5)
    is_featured = Column(Boolean, default=False)


class RoleEmployer(Base):
    """Employers hiring for specific roles."""
    __tablename__ = "role_employers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"))
    employer_name = Column(String(255), nullable=False)
    is_vet_friendly = Column(Boolean, default=False)
    location = Column(String(255), nullable=True)
    note = Column(String(255), nullable=True)


class DataReviewLog(Base):
    """Audit/review status of AI generated career data."""
    __tablename__ = "data_review_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    reviewer = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


# ─── Engine & Session factories ───

def get_async_engine(database_url: str):
    return create_async_engine(
        database_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )


def get_async_session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def get_sync_engine(database_url: str):
    return create_engine(database_url, echo=False, pool_pre_ping=True)


async def init_db(database_url: str):
    """Create all tables."""
    engine = get_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


def init_db_sync(database_url: str):
    """Create all tables (sync version for scripts)."""
    engine = get_sync_engine(database_url)
    Base.metadata.create_all(engine)
    engine.dispose()
