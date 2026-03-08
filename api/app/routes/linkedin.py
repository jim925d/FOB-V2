"""
LinkedIn Extract Route
The FOB Platform

POST /api/v1/linkedin/extract — accepts raw text from a LinkedIn
search results page and returns structured contact data.  This keeps
the Anthropic API key server-side instead of exposing it in the
frontend bundle.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.linkedin_extractor import LinkedInExtractor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/linkedin", tags=["linkedin"])

# Singleton extractor (lazy-inits Anthropic client on first call)
_extractor: Optional[LinkedInExtractor] = None


def _get_extractor() -> LinkedInExtractor:
    global _extractor
    if _extractor is None:
        _extractor = LinkedInExtractor()
    return _extractor


# ── Request / Response Models ──


class ExtractRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=20_000,
        description="Raw text from a saved LinkedIn search results page",
    )


class ContactItem(BaseModel):
    name: str
    currentTitle: str = ""
    company: str = ""
    location: str = ""
    militaryBackground: str = ""
    connectionDegree: str = ""


class ExtractResponse(BaseModel):
    contacts: list[ContactItem] = []


# ── Endpoint ──


@router.post("/extract", response_model=ExtractResponse)
async def extract_contacts(body: ExtractRequest):
    """
    Extract structured contact profiles from LinkedIn search result text.

    The frontend sends the raw text from a saved HTML page.  Claude parses
    it into a list of contacts (name, title, company, location, etc.).
    """
    try:
        extractor = _get_extractor()
        contacts = await extractor.extract_contacts(body.text)
        return ExtractResponse(contacts=contacts)

    except ValueError as e:
        # Anthropic API key not configured
        logger.warning("LinkedIn extract unavailable: %s", e)
        raise HTTPException(
            status_code=503,
            detail="AI extraction is not configured on this server.",
        )
    except Exception as e:
        logger.error("LinkedIn extract error: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Extraction failed. Please try again.",
        )
