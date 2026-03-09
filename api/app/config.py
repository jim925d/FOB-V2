"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/skillbridge"
    database_url_sync: str = ""  # Auto-generated from database_url

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600  # 1 hour default cache

    # Geocoding
    geocoding_api_key: str = ""
    geocoding_provider: str = "opencage"  # opencage | google | nominatim
    geocoding_rate_limit: float = 1.0  # requests per second

    # Scraping
    scrape_base_url: str = "https://skillbridge.osd.mil/locations.htm"
    scrape_interval_hours: int = 168  # weekly
    scrape_delay_min: int = 2  # seconds between page requests
    scrape_delay_max: int = 5
    scrape_max_pages: int = 700  # safety limit
    scrape_user_agent: str = (
        "TheFOB-SkillBridge-Scraper/1.0 "
        "(Veteran Resource Platform; contact@thefob.com)"
    )

    # Anthropic / Claude AI
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_max_tokens: int = 8000
    anthropic_temperature: float = 0.3

    # API
    api_secret_key: str = "change-me-in-production"
    api_title: str = "The FOB — SkillBridge API"

    # Supabase (optional): for JWT verification on protected endpoints)
    supabase_url: str = ""
    supabase_jwt_secret: str = ""
    api_version: str = "1.0.0"

    # MOS → Career mapping (optional JSON file; overrides auto-detected paths)
    mos_career_mapping_path: str = Field(
        default="",
        description="Full path to mos_career_mapping.json for expanded MOS-to-career options",
    )

    # Employment networking — local search (use Google CSE for results from Google)
    google_cse_api_key: str = Field(default="", description="Google Custom Search API key (Cloud Console)")
    google_cse_cx: str = Field(default="", description="Google Programmable Search Engine ID (cx)")
    serp_api_key: str = Field(default="", description="Fallback: SerpAPI key if Google CSE not set")

    # CORS — allow Vite dev server (often 3000 or 5173) under localhost and 127.0.0.1
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def model_post_init(self, __context):
        # Render provides postgres:// or postgresql:// — convert for asyncpg
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace(
                "postgres://", "postgresql+asyncpg://", 1
            )
        elif self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )

        if not self.database_url_sync:
            self.database_url_sync = self.database_url.replace(
                "+asyncpg", "+psycopg"
            )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
