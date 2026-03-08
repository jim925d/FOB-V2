"""
Geocoding service — converts city/state/zip to lat/lon coordinates.

Supports multiple providers with a unified interface:
- OpenCage (recommended, generous free tier)
- Google Maps Geocoding
- Nominatim (free, but strict rate limits)

Includes:
- Rate limiting to respect provider limits
- Caching to avoid re-geocoding known locations
- Batch processing for efficiency
- Fallback strategies (zip centroid, state centroid)
"""

import asyncio
import time
from typing import Optional, Dict
from dataclasses import dataclass

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = structlog.get_logger()

# State centroids as last-resort fallback
STATE_CENTROIDS = {
    "AL":(32.8,-86.8),"AK":(64.2,-152.5),"AZ":(34.3,-111.7),"AR":(34.9,-92.4),
    "CA":(37.2,-119.7),"CO":(39.0,-105.5),"CT":(41.6,-72.7),"DE":(39.0,-75.5),
    "FL":(28.6,-82.5),"GA":(32.7,-83.5),"HI":(20.5,-157.5),"ID":(44.4,-114.6),
    "IL":(40.0,-89.2),"IN":(39.9,-86.3),"IA":(42.0,-93.5),"KS":(38.5,-98.3),
    "KY":(37.8,-85.7),"LA":(31.1,-91.9),"ME":(45.4,-69.2),"MD":(39.0,-76.8),
    "MA":(42.2,-71.7),"MI":(44.3,-84.5),"MN":(46.3,-94.3),"MS":(32.7,-89.7),
    "MO":(38.4,-92.5),"MT":(47.0,-109.6),"NE":(41.5,-99.8),"NV":(39.9,-116.4),
    "NH":(43.7,-71.6),"NJ":(40.1,-74.5),"NM":(34.4,-106.1),"NY":(42.2,-74.9),
    "NC":(35.6,-79.8),"ND":(47.5,-100.5),"OH":(40.4,-82.8),"OK":(35.6,-97.5),
    "OR":(44.1,-120.5),"PA":(40.9,-77.8),"RI":(41.7,-71.5),"SC":(33.9,-80.9),
    "SD":(44.4,-100.2),"TN":(35.9,-86.4),"TX":(31.5,-99.3),"UT":(39.3,-111.7),
    "VT":(44.1,-72.6),"VA":(37.5,-78.9),"WA":(47.4,-120.7),"WV":(38.6,-80.6),
    "WI":(44.6,-89.8),"WY":(43.0,-107.6),"DC":(38.9,-77.0),
}


@dataclass
class GeoResult:
    latitude: float
    longitude: float
    quality: str  # "exact", "approximate", "zip_centroid", "state_centroid"
    formatted_address: Optional[str] = None


class GeocodingService:
    """Provider-agnostic geocoding with caching and rate limiting."""

    def __init__(self):
        self.settings = get_settings()
        self._cache: Dict[str, GeoResult] = {}
        self._last_request_time = 0.0
        self._min_interval = 1.0 / max(self.settings.geocoding_rate_limit, 0.1)
        self.stats = {"total": 0, "cache_hits": 0, "api_calls": 0, "fallbacks": 0, "errors": 0}

    def _cache_key(self, city: str, state: str, zip_code: str = "") -> str:
        return f"{city.lower().strip()}|{state.upper().strip()}|{zip_code.strip()}"

    async def _rate_limit(self):
        """Enforce rate limiting between geocoding requests."""
        now = time.monotonic()
        elapsed = now - self._last_request_time
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        self._last_request_time = time.monotonic()

    async def geocode(
        self,
        city: str = "",
        state: str = "",
        zip_code: str = "",
        address: str = "",
    ) -> Optional[GeoResult]:
        """
        Geocode a location with fallback chain:
        1. Check cache
        2. Try full address geocoding
        3. Fall back to city + state
        4. Fall back to zip code centroid
        5. Fall back to state centroid
        """
        self.stats["total"] += 1

        # Build cache key
        key = self._cache_key(city, state, zip_code)
        if key in self._cache:
            self.stats["cache_hits"] += 1
            return self._cache[key]

        # Build query string
        query = address or self._build_query(city, state, zip_code)
        if not query or query.strip() in (",", ""):
            # Only state available — use centroid
            return self._state_fallback(state, key)

        # Try geocoding API
        result = await self._geocode_api(query)
        if result:
            self._cache[key] = result
            return result

        # Fallback: try just city + state if full address failed
        if address and city:
            simple_query = f"{city}, {state}" if state else city
            result = await self._geocode_api(simple_query)
            if result:
                result.quality = "approximate"
                self._cache[key] = result
                return result

        # Fallback: state centroid
        return self._state_fallback(state, key)

    def _build_query(self, city: str, state: str, zip_code: str) -> str:
        parts = []
        if city:
            parts.append(city.strip())
        if state:
            parts.append(state.strip())
        if zip_code:
            parts.append(zip_code.strip())
        return ", ".join(parts)

    def _state_fallback(self, state: str, cache_key: str) -> Optional[GeoResult]:
        state = state.upper().strip()
        if state in STATE_CENTROIDS:
            lat, lon = STATE_CENTROIDS[state]
            result = GeoResult(
                latitude=lat, longitude=lon,
                quality="state_centroid",
                formatted_address=f"{state} (centroid)",
            )
            self._cache[cache_key] = result
            self.stats["fallbacks"] += 1
            return result
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    async def _geocode_api(self, query: str) -> Optional[GeoResult]:
        """Call the configured geocoding provider."""
        await self._rate_limit()
        self.stats["api_calls"] += 1

        provider = self.settings.geocoding_provider.lower()

        try:
            if provider == "opencage":
                return await self._geocode_opencage(query)
            elif provider == "google":
                return await self._geocode_google(query)
            elif provider == "nominatim":
                return await self._geocode_nominatim(query)
            else:
                logger.error("Unknown geocoding provider", provider=provider)
                return None
        except Exception as e:
            logger.error("Geocoding error", query=query, error=str(e))
            self.stats["errors"] += 1
            return None

    async def _geocode_opencage(self, query: str) -> Optional[GeoResult]:
        """OpenCage Geocoding API — 2,500 free requests/day."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.opencagedata.com/geocode/v1/json",
                params={
                    "q": query,
                    "key": self.settings.geocoding_api_key,
                    "countrycode": "us",
                    "limit": 1,
                    "no_annotations": 1,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            if not results:
                return None

            r = results[0]
            geo = r.get("geometry", {})
            confidence = r.get("confidence", 0)

            quality = "exact" if confidence >= 8 else "approximate" if confidence >= 5 else "zip_centroid"

            return GeoResult(
                latitude=geo.get("lat", 0),
                longitude=geo.get("lng", 0),
                quality=quality,
                formatted_address=r.get("formatted", ""),
            )

    async def _geocode_google(self, query: str) -> Optional[GeoResult]:
        """Google Maps Geocoding API."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={
                    "address": query,
                    "key": self.settings.geocoding_api_key,
                    "components": "country:US",
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            if not results:
                return None

            r = results[0]
            loc = r.get("geometry", {}).get("location", {})
            loc_type = r.get("geometry", {}).get("location_type", "")

            quality_map = {
                "ROOFTOP": "exact",
                "RANGE_INTERPOLATED": "exact",
                "GEOMETRIC_CENTER": "approximate",
                "APPROXIMATE": "zip_centroid",
            }

            return GeoResult(
                latitude=loc.get("lat", 0),
                longitude=loc.get("lng", 0),
                quality=quality_map.get(loc_type, "approximate"),
                formatted_address=r.get("formatted_address", ""),
            )

    async def _geocode_nominatim(self, query: str) -> Optional[GeoResult]:
        """OpenStreetMap Nominatim — free but max 1 req/sec."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": query,
                    "format": "json",
                    "countrycodes": "us",
                    "limit": 1,
                },
                headers={"User-Agent": self.settings.scrape_user_agent},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

            if not data:
                return None

            r = data[0]
            return GeoResult(
                latitude=float(r.get("lat", 0)),
                longitude=float(r.get("lon", 0)),
                quality="approximate",
                formatted_address=r.get("display_name", ""),
            )

    async def batch_geocode(
        self,
        locations: list,
        concurrency: int = 5,
    ) -> Dict[str, GeoResult]:
        """
        Batch geocode a list of (city, state, zip) tuples.
        Uses a semaphore to limit concurrent requests.
        """
        sem = asyncio.Semaphore(concurrency)
        results = {}

        async def _geocode_one(city, state, zip_code):
            async with sem:
                key = self._cache_key(city, state, zip_code)
                result = await self.geocode(city=city, state=state, zip_code=zip_code)
                if result:
                    results[key] = result

        tasks = [
            _geocode_one(city, state, zip_code)
            for city, state, zip_code in locations
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(
            "Batch geocoding complete",
            total=len(locations),
            successful=len(results),
            **self.stats,
        )
        return results
