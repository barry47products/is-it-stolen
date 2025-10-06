"""Tests for geocoding service."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.infrastructure.geocoding.geocoding_service import (
    GeocodingResult,
    GeocodingService,
    GeocodingServiceUnavailable,
)


@pytest.mark.unit
class TestGeocodingService:
    """Test geocoding service."""

    @pytest.fixture
    def mock_redis(self) -> MagicMock:
        """Create mock Redis client."""
        redis = MagicMock()
        redis.hgetall = AsyncMock(return_value={})
        redis.hset = AsyncMock()
        redis.expire = AsyncMock()
        return redis

    @pytest.fixture
    def service(self, mock_redis: MagicMock) -> GeocodingService:
        """Create geocoding service with mock Redis."""
        return GeocodingService(redis_client=mock_redis, cache_ttl_seconds=300)

    @pytest.fixture
    def service_without_cache(self) -> GeocodingService:
        """Create geocoding service without caching."""
        return GeocodingService(redis_client=None)

    @pytest.mark.asyncio
    async def test_geocode_returns_coordinates_for_valid_location(
        self, service_without_cache: GeocodingService
    ) -> None:
        """Should return coordinates for valid location."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "lat": "51.5074",
                "lon": "-0.1278",
                "display_name": "London, UK",
                "address": {"city": "London", "country": "United Kingdom"},
            }
        ]

        # Act
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await service_without_cache.geocode("London")

        # Assert
        assert result is not None
        assert result.latitude == 51.5074
        assert result.longitude == -0.1278
        assert "London" in result.display_name

    @pytest.mark.asyncio
    async def test_geocode_returns_none_for_empty_text(
        self, service: GeocodingService
    ) -> None:
        """Should return None for empty location text."""
        # Act & Assert
        assert await service.geocode("") is None
        assert await service.geocode("   ") is None

    @pytest.mark.asyncio
    async def test_geocode_returns_none_when_no_results_found(
        self, service_without_cache: GeocodingService
    ) -> None:
        """Should return None when API returns no results."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = []

        # Act
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await service_without_cache.geocode("InvalidLocation12345XYZ")

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_geocode_uses_cache_on_second_call(
        self, service: GeocodingService, mock_redis: MagicMock
    ) -> None:
        """Should use cached result on second call for same location."""
        # Arrange
        location = "Paris"
        cached_data = {
            b"latitude": b"48.8566",
            b"longitude": b"2.3522",
            b"display_name": b"Paris, France",
        }

        mock_redis.hgetall = AsyncMock(return_value=cached_data)

        # Act
        result = await service.geocode(location)

        # Assert
        assert result is not None
        assert result.latitude == 48.8566
        assert result.longitude == 2.3522
        assert result.display_name == "Paris, France"

        # Verify cache was checked
        mock_redis.hgetall.assert_called_once()

    @pytest.mark.asyncio
    async def test_geocode_saves_result_to_cache(
        self, service: GeocodingService, mock_redis: MagicMock
    ) -> None:
        """Should save successful geocoding result to cache."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "lat": "40.7128",
                "lon": "-74.0060",
                "display_name": "New York, NY, USA",
            }
        ]

        # Cache miss first
        mock_redis.hgetall = AsyncMock(return_value={})

        # Act
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await service.geocode("New York")

        # Assert
        assert result is not None

        # Verify cache was written
        mock_redis.hset.assert_called_once()
        mock_redis.expire.assert_called_once_with("geocoding:new york", 300)

    @pytest.mark.asyncio
    async def test_geocode_raises_exception_on_timeout(
        self, service_without_cache: GeocodingService
    ) -> None:
        """Should raise GeocodingServiceUnavailable on timeout."""
        # Arrange
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            # Act & Assert
            with pytest.raises(GeocodingServiceUnavailable, match="timed out"):
                await service_without_cache.geocode("London")

    @pytest.mark.asyncio
    async def test_geocode_raises_exception_on_http_error(
        self, service_without_cache: GeocodingService
    ) -> None:
        """Should raise GeocodingServiceUnavailable on HTTP error."""
        # Arrange
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.HTTPError("HTTP error")
            )

            # Act & Assert
            with pytest.raises(GeocodingServiceUnavailable, match="unavailable"):
                await service_without_cache.geocode("London")

    @pytest.mark.asyncio
    async def test_geocode_strips_whitespace_from_location(
        self, service_without_cache: GeocodingService
    ) -> None:
        """Should strip whitespace from location text before geocoding."""
        # Arrange
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "lat": "51.5074",
                "lon": "-0.1278",
                "display_name": "London, UK",
            }
        ]

        # Act
        with patch("httpx.AsyncClient") as mock_client:
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            result = await service_without_cache.geocode("  London  ")

        # Assert
        assert result is not None

        # Verify API was called with stripped text
        call_args = mock_get.call_args
        assert call_args[1]["params"]["q"] == "London"

    @pytest.mark.asyncio
    async def test_geocode_handles_cache_read_errors_gracefully(
        self, service: GeocodingService, mock_redis: MagicMock
    ) -> None:
        """Should handle cache read errors and continue to API."""
        # Arrange
        mock_redis.hgetall = AsyncMock(side_effect=Exception("Redis error"))

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "lat": "51.5074",
                "lon": "-0.1278",
                "display_name": "London, UK",
            }
        ]

        # Act
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await service.geocode("London")

        # Assert - should still get result from API
        assert result is not None
        assert result.latitude == 51.5074

    @pytest.mark.asyncio
    async def test_geocode_handles_cache_write_errors_gracefully(
        self, service: GeocodingService, mock_redis: MagicMock
    ) -> None:
        """Should handle cache write errors without failing request."""
        # Arrange
        mock_redis.hgetall = AsyncMock(return_value={})
        mock_redis.hset = AsyncMock(side_effect=Exception("Redis error"))

        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "lat": "51.5074",
                "lon": "-0.1278",
                "display_name": "London, UK",
            }
        ]

        # Act
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await service.geocode("London")

        # Assert - should still get result despite cache error
        assert result is not None
        assert result.latitude == 51.5074

    @pytest.mark.asyncio
    async def test_geocoding_result_is_immutable(self) -> None:
        """Should create immutable GeocodingResult."""
        # Arrange
        result = GeocodingResult(
            latitude=51.5074,
            longitude=-0.1278,
            display_name="London, UK",
            raw_response={},
        )

        # Act & Assert
        with pytest.raises(AttributeError):
            result.latitude = 0.0  # type: ignore[misc]
