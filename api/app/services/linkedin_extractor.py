"""
LinkedIn Contact Extraction Service
The FOB Platform

Uses Claude (Anthropic) to extract contact profiles from LinkedIn
search result text (copied/saved as HTML).  Keeps the API key
server-side — the frontend sends raw text to POST /api/v1/linkedin/extract.
"""

import json
import logging
from typing import Optional

import anthropic

from app.config import get_settings

logger = logging.getLogger(__name__)

EXTRACT_SYSTEM = (
    "You are a parser for LinkedIn search result pages that were printed or "
    "copied as text.\n"
    "From the given text, extract every person/profile that looks like a "
    "LinkedIn result: name, job title, company, and optionally location or "
    "military info.\n"
    "Return a JSON array of objects only. Each object must have: "
    "name (string), currentTitle (string), company (string).\n"
    "Optional fields (use \"\" if unknown): location, militaryBackground, "
    "connectionDegree (e.g. \"1st\", \"2nd\").\n"
    "If the text has no person-like entries, return [].\n"
    "Output nothing but the JSON array, no markdown or explanation."
)

MAX_INPUT_CHARS = 15_000  # safety cap on incoming text


class LinkedInExtractor:
    """
    Extracts structured contact data from raw LinkedIn page text using Claude.

    Follows the same lazy-init Anthropic client pattern as AIRoadmapGenerator.
    """

    def __init__(self):
        self._settings = get_settings()
        self._client: Optional[anthropic.Anthropic] = None

    @property
    def client(self) -> anthropic.Anthropic:
        """Lazy-init the Anthropic client."""
        if self._client is None:
            if not self._settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not configured")
            self._client = anthropic.Anthropic(
                api_key=self._settings.anthropic_api_key,
                timeout=60.0,
            )
        return self._client

    async def extract_contacts(self, text: str) -> list[dict]:
        """
        Send raw text to Claude and return a list of contact dicts.

        Each contact: { name, currentTitle, company, location?,
                        militaryBackground?, connectionDegree? }
        Returns [] if nothing found or on error.
        """
        trimmed = (text or "").strip()
        if not trimmed:
            return []

        # Cap input length
        trimmed = trimmed[:MAX_INPUT_CHARS]

        try:
            response = self.client.messages.create(
                model=self._settings.anthropic_model,
                max_tokens=4096,
                temperature=0.1,
                system=EXTRACT_SYSTEM,
                messages=[{"role": "user", "content": trimmed}],
            )

            # Extract text content from response
            block = next(
                (b for b in response.content if b.type == "text"), None
            )
            content = (block.text or "").strip() if block else ""

            parsed = self._parse_json_array(content)
            return self._normalize_contacts(parsed)

        except ValueError:
            # API key not configured — re-raise so the route can return 503
            raise
        except Exception as e:
            logger.error("LinkedIn extraction failed: %s", e, exc_info=True)
            return []

    @staticmethod
    def _parse_json_array(text: str) -> list:
        """Parse a JSON array from Claude's response, stripping markdown fences."""
        if not text:
            return []
        try:
            import re
            cleaned = re.sub(r"^```\w*\n?|\n?```$", "", text).strip()
            out = json.loads(cleaned)
            return out if isinstance(out, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    @staticmethod
    def _normalize_contacts(rows: list) -> list[dict]:
        """Normalize contact rows to a consistent shape."""
        return [
            {
                "name": str(row.get("name") or row.get("Name") or "").strip() or "Unknown",
                "currentTitle": str(
                    row.get("currentTitle")
                    or row.get("title")
                    or row.get("current_title")
                    or ""
                ).strip(),
                "company": str(row.get("company") or row.get("Company") or "").strip(),
                "location": str(row.get("location") or row.get("Location") or "").strip(),
                "militaryBackground": str(
                    row.get("militaryBackground")
                    or row.get("military_background")
                    or ""
                ).strip(),
                "connectionDegree": str(
                    row.get("connectionDegree")
                    or row.get("connection_degree")
                    or ""
                ).strip(),
            }
            for row in (rows or [])
        ]
