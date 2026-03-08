"""Pydantic schemas for Corporate ERG API."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ERGBase(BaseModel):
    company_name: str
    erg_name: Optional[str] = None
    industry: str
    company_size: Optional[str] = None
    description: Optional[str] = None
    offerings: List[str] = Field(default_factory=list)
    founded_year: Optional[int] = None
    member_count: Optional[int] = None
    careers_url: Optional[str] = None
    erg_url: Optional[str] = None
    company_website: Optional[str] = None
    contact_email: Optional[str] = None
    linkedin_url: Optional[str] = None
    headquarters_city: Optional[str] = None
    headquarters_state: Optional[str] = None
    military_friendly_rating: Optional[str] = None
    has_skillbridge: bool = False
    verified: bool = False
    featured: bool = False
    data_sources: List[str] = Field(default_factory=list)
    source_type: Optional[str] = None
    scraped_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ERGList(ERGBase):
    id: str

    class Config:
        from_attributes = True


class ERGDetail(ERGList):
    pass


class ERGStats(BaseModel):
    total_ergs: int
    total_companies: int
    total_industries: int
    total_named_ergs: int
    with_skillbridge: int
    verified_count: int


class IndustryCount(BaseModel):
    industry: str
    count: int


class ERGSubmitRequest(BaseModel):
    """Community submission — same shape as ERG fields."""
    company_name: str = Field(..., min_length=1, max_length=500)
    erg_name: Optional[str] = Field(None, max_length=500)
    industry: Optional[str] = Field(None, max_length=200)
    company_size: Optional[str] = None
    description: Optional[str] = Field(None, max_length=2000)
    offerings: List[str] = Field(default_factory=list)
    founded_year: Optional[int] = None
    member_count: Optional[int] = None
    careers_url: Optional[str] = None
    erg_url: Optional[str] = None
    company_website: Optional[str] = None
    contact_email: Optional[str] = None
    linkedin_url: Optional[str] = None
    headquarters_city: Optional[str] = None
    headquarters_state: Optional[str] = None
    has_skillbridge: bool = False
    submitter_email: str = Field(..., min_length=1)
    submitter_name: Optional[str] = None
    submitter_role: Optional[str] = None
    verification_agreement: bool = Field(..., description="User attests to accuracy")
