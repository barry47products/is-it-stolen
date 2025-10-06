"""Geocoding service for converting location text to coordinates."""

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 10
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "IsItStolen/1.0 (stolen items reporting bot)"


@dataclass(frozen=True)
class GeocodingResult:
    """Result of geocoding operation."""

    latitude: float
    longitude: float
    display_name: str
    raw_response: dict[str, Any]


class GeocodingError(Exception):
    """Base exception for geocoding errors."""


class GeocodingServiceUnavailable(GeocodingError):
    """Raised when geocoding service is unavailable."""


class GeocodingService:
    """Service for converting location text to geographic coordinates.

    Uses Nominatim (OpenStreetMap) API for geocoding.
    Implements caching via Redis to reduce API calls.
    """

    def __init__(
        self,
        redis_client: Any | None = None,
        cache_ttl_seconds: int = 86400,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize geocoding service.

        Args:
            redis_client: Optional Redis client for caching results
            cache_ttl_seconds: Cache TTL in seconds (default 24 hours)
            timeout_seconds: HTTP request timeout in seconds
        """
        self.redis_client = redis_client
        self.cache_ttl_seconds = cache_ttl_seconds
        self.timeout_seconds = timeout_seconds

    async def geocode(self, location_text: str) -> GeocodingResult | None:
        """Convert location text to coordinates.

        Args:
            location_text: Location as text (e.g., "London", "123 Main St, NYC")

        Returns:
            GeocodingResult with coordinates, or None if location not found

        Raises:
            GeocodingServiceUnavailable: If API is unreachable
        """
        if not location_text or not location_text.strip():
            return None

        location_text = location_text.strip()

        # Check cache first
        cached_result = await self._get_from_cache(location_text)
        if cached_result is not None:
            return cached_result

        # Call Nominatim API
        try:
            result = await self._call_nominatim_api(location_text)

            # Cache the result if found
            if result is not None:
                await self._save_to_cache(location_text, result)

            return result

        except httpx.TimeoutException as error:
            logger.error(f"Geocoding timeout for '{location_text}': {error}")
            raise GeocodingServiceUnavailable("Geocoding service timed out") from error
        except httpx.HTTPError as error:
            logger.error(f"Geocoding HTTP error for '{location_text}': {error}")
            raise GeocodingServiceUnavailable(
                "Geocoding service unavailable"
            ) from error

    async def _call_nominatim_api(self, location_text: str) -> GeocodingResult | None:
        """Call Nominatim geocoding API.

        Args:
            location_text: Location to geocode

        Returns:
            GeocodingResult if found, None otherwise
        """
        params = {
            "q": location_text,
            "format": "json",
            "limit": 1,
            "addressdetails": 1,
        }

        headers = {"User-Agent": USER_AGENT}

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(
                f"{NOMINATIM_BASE_URL}/search",
                params=params,
                headers=headers,
            )
            response.raise_for_status()

            results = response.json()

            if not results or len(results) == 0:
                logger.info(f"No geocoding results found for '{location_text}'")
                return None

            # Take first result
            first_result = results[0]

            return GeocodingResult(
                latitude=float(first_result["lat"]),
                longitude=float(first_result["lon"]),
                display_name=first_result.get("display_name", location_text),
                raw_response=first_result,
            )

    async def _get_from_cache(self, location_text: str) -> GeocodingResult | None:
        """Get geocoding result from cache.

        Args:
            location_text: Location to look up

        Returns:
            Cached result if found, None otherwise
        """
        if self.redis_client is None:
            return None

        cache_key = f"geocoding:{location_text.lower()}"

        try:
            cached_data = await self.redis_client.hgetall(cache_key)

            if not cached_data:
                return None

            # Reconstruct GeocodingResult from cached data
            return GeocodingResult(
                latitude=float(cached_data[b"latitude"]),
                longitude=float(cached_data[b"longitude"]),
                display_name=cached_data[b"display_name"].decode("utf-8"),
                raw_response={},  # Don't cache full raw response
            )

        except Exception as error:
            logger.warning(f"Cache read error for '{location_text}': {error}")
            return None

    async def _save_to_cache(self, location_text: str, result: GeocodingResult) -> None:
        """Save geocoding result to cache.

        Args:
            location_text: Location that was geocoded
            result: Geocoding result to cache
        """
        if self.redis_client is None:
            return

        cache_key = f"geocoding:{location_text.lower()}"

        try:
            # Store as hash for easy retrieval
            await self.redis_client.hset(
                cache_key,
                mapping={
                    "latitude": str(result.latitude),
                    "longitude": str(result.longitude),
                    "display_name": result.display_name,
                },
            )

            # Set expiry
            await self.redis_client.expire(cache_key, self.cache_ttl_seconds)

        except Exception as error:
            logger.warning(f"Cache write error for '{location_text}': {error}")
