"""
SkillBridge Enrichment Service
The FOB Platform

Queries the existing programs table to find SkillBridge programs
matching a career roadmap milestone's target field and location.
"""

import logging
from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Program

logger = logging.getLogger(__name__)

# Map career fields from progression paths to job_family / industry keywords
# in the existing programs table
CAREER_FIELD_KEYWORDS = {
    "cybersecurity": [
        "cyber", "security", "information security", "network security",
        "soc", "threat", "infosec",
    ],
    "supply_chain_management": [
        "supply chain", "logistics", "warehouse", "distribution",
        "procurement", "inventory", "transportation",
    ],
    "information_technology": [
        "information technology", "systems admin", "network admin",
        "it support", "cloud", "infrastructure", "help desk",
    ],
    "nursing_healthcare": [
        "healthcare", "medical", "nursing", "health", "clinical",
        "hospital", "patient care",
    ],
    "data_analytics": [
        "data", "analytics", "business intelligence", "analyst",
        "reporting", "statistics",
    ],
}

# Map ZIP code prefixes to state abbreviation(s) for proximity filtering
# (subset — covers the most common military-area ZIPs)
ZIP_PREFIX_TO_STATE = {
    "100": "NY", "200": "DC", "201": "VA", "221": "VA",
    "300": "GA", "330": "FL", "606": "IL", "750": "TX",
    "770": "TX", "782": "TX", "802": "CO", "803": "CO",
    "850": "AZ", "900": "CA", "941": "CA", "980": "WA",
    "283": "NC", "316": "KS", "314": "MO", "961": "WA",
}


def _zip_to_state(zip_code: str) -> Optional[str]:
    """Best-effort ZIP prefix → state mapping."""
    return ZIP_PREFIX_TO_STATE.get(zip_code[:3])


class SkillBridgeEnrichmentService:
    """Enriches roadmap milestones with live SkillBridge program matches."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_programs(
        self,
        career_field: str,
        zip_code: Optional[str] = None,
        limit: int = 5,
    ) -> list[dict]:
        """
        Find SkillBridge programs matching a career field near a ZIP code.

        Returns dicts compatible with the SkillBridgeLink model fields.
        When zip_code is None, returns only nationwide/online programs.
        """
        keywords = CAREER_FIELD_KEYWORDS.get(career_field, [])
        if not keywords:
            return []

        # Build keyword filter across job_family, description, industry
        keyword_filters = []
        for kw in keywords:
            pattern = f"%{kw}%"
            keyword_filters.append(Program.job_family.ilike(pattern))
            keyword_filters.append(Program.industry.ilike(pattern))
            keyword_filters.append(Program.description.ilike(pattern))

        stmt = (
            select(Program)
            .where(Program.is_active.is_(True))
            .where(or_(*keyword_filters))
        )

        # Filter by geographic relevance
        state = _zip_to_state(zip_code) if zip_code else None
        if state:
            # Prefer in-state, but also include nationwide/online
            stmt = stmt.where(
                or_(
                    Program.state == state,
                    Program.nationwide.is_(True),
                    Program.online.is_(True),
                )
            )
        else:
            # No ZIP — only return nationwide/online programs
            stmt = stmt.where(
                or_(
                    Program.nationwide.is_(True),
                    Program.online.is_(True),
                )
            )

        stmt = stmt.limit(limit)

        result = await self.session.execute(stmt)
        programs = result.scalars().all()

        return [
            {
                "program_name": p.description[:80] if p.description else p.company,
                "company": p.company,
                "skillbridge_id": str(p.id),
                "location": f"{p.city}, {p.state}" if p.city else (
                    "Nationwide" if p.nationwide else "Online" if p.online else None
                ),
                "duration_weeks": self._days_to_weeks(p.duration_min_days),
            }
            for p in programs
        ]

    @staticmethod
    def _days_to_weeks(days: Optional[int]) -> Optional[int]:
        if days is None:
            return None
        return max(1, days // 7)
