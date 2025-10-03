"""Unit tests for Find Nearby Items query handler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.queries.find_nearby_items import (
    FindNearbyItemsHandler,
    FindNearbyItemsQuery,
    FindNearbyItemsResult,
    NearbyItem,
)
from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.exceptions.domain_exceptions import InvalidLocationError
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber

MAX_RADIUS_KM = 100.0


class TestFindNearbyItemsQuery:
    """Test suite for FindNearbyItemsQuery handler."""

    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        """Create mock stolen item repository."""
        repository = AsyncMock(spec=IStolenItemRepository)
        repository.find_nearby = AsyncMock(return_value=[])
        return repository

    @pytest.fixture
    def handler(self, mock_repository: AsyncMock) -> FindNearbyItemsHandler:
        """Create query handler with mocked repository."""
        return FindNearbyItemsHandler(repository=mock_repository)

    @pytest.fixture
    def sample_stolen_item(self) -> StolenItem:
        """Create sample stolen item for testing."""
        return StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    @pytest.fixture
    def valid_query(self) -> FindNearbyItemsQuery:
        """Create valid query."""
        return FindNearbyItemsQuery(
            latitude=-33.9249,
            longitude=18.4241,
            radius_km=10.0,
        )

    @pytest.mark.asyncio
    async def test_handles_valid_query_successfully(
        self,
        handler: FindNearbyItemsHandler,
        valid_query: FindNearbyItemsQuery,
        mock_repository: AsyncMock,
        sample_stolen_item: StolenItem,
    ) -> None:
        """Should return nearby items."""
        # Arrange
        mock_repository.find_nearby.return_value = [sample_stolen_item]

        # Act
        result = await handler.handle(valid_query)

        # Assert
        assert isinstance(result, FindNearbyItemsResult)
        assert len(result.items) == 1
        assert result.total_count == 1
        mock_repository.find_nearby.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_items_with_distances(
        self,
        handler: FindNearbyItemsHandler,
        valid_query: FindNearbyItemsQuery,
        mock_repository: AsyncMock,
        sample_stolen_item: StolenItem,
    ) -> None:
        """Should include distance for each item."""
        # Arrange
        mock_repository.find_nearby.return_value = [sample_stolen_item]

        # Act
        result = await handler.handle(valid_query)

        # Assert
        nearby_item = result.items[0]
        assert isinstance(nearby_item, NearbyItem)
        assert nearby_item.item == sample_stolen_item
        assert nearby_item.distance_km >= 0.0

    @pytest.mark.asyncio
    async def test_queries_repository_with_location_and_radius(
        self,
        handler: FindNearbyItemsHandler,
        valid_query: FindNearbyItemsQuery,
        mock_repository: AsyncMock,
    ) -> None:
        """Should query repository with correct location and radius."""
        # Act
        await handler.handle(valid_query)

        # Assert
        mock_repository.find_nearby.assert_called_once()
        call_args = mock_repository.find_nearby.call_args[1]
        assert call_args["location"].latitude == valid_query.latitude
        assert call_args["location"].longitude == valid_query.longitude
        assert call_args["radius_km"] == valid_query.radius_km

    @pytest.mark.asyncio
    async def test_filters_by_category_when_specified(
        self,
        handler: FindNearbyItemsHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Should filter by category when provided."""
        # Arrange
        query = FindNearbyItemsQuery(
            latitude=-33.9249,
            longitude=18.4241,
            radius_km=10.0,
            category="bicycle",
        )

        # Act
        await handler.handle(query)

        # Assert
        call_args = mock_repository.find_nearby.call_args[1]
        assert call_args["category"] == ItemCategory.BICYCLE

    @pytest.mark.asyncio
    async def test_uses_default_radius_when_not_specified(
        self,
        handler: FindNearbyItemsHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Should use default radius of 10km."""
        # Arrange
        query = FindNearbyItemsQuery(
            latitude=-33.9249,
            longitude=18.4241,
        )

        # Act
        await handler.handle(query)

        # Assert
        call_args = mock_repository.find_nearby.call_args[1]
        assert call_args["radius_km"] == 10.0

    @pytest.mark.asyncio
    async def test_rejects_radius_above_maximum(
        self,
        handler: FindNearbyItemsHandler,
    ) -> None:
        """Should reject radius above 100km."""
        # Arrange
        query = FindNearbyItemsQuery(
            latitude=-33.9249,
            longitude=18.4241,
            radius_km=150.0,  # Above max
        )

        # Act & Assert
        with pytest.raises(ValueError, match="exceeds maximum"):
            await handler.handle(query)

    @pytest.mark.asyncio
    async def test_rejects_negative_radius(
        self,
        handler: FindNearbyItemsHandler,
    ) -> None:
        """Should reject negative radius."""
        # Arrange
        query = FindNearbyItemsQuery(
            latitude=-33.9249,
            longitude=18.4241,
            radius_km=-5.0,
        )

        # Act & Assert
        with pytest.raises(ValueError, match="must be positive"):
            await handler.handle(query)

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_latitude(
        self,
        handler: FindNearbyItemsHandler,
    ) -> None:
        """Should raise InvalidLocationError for invalid latitude."""
        # Arrange
        query = FindNearbyItemsQuery(
            latitude=91.0,  # Invalid
            longitude=18.4241,
        )

        # Act & Assert
        with pytest.raises(InvalidLocationError):
            await handler.handle(query)

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_longitude(
        self,
        handler: FindNearbyItemsHandler,
    ) -> None:
        """Should raise InvalidLocationError for invalid longitude."""
        # Arrange
        query = FindNearbyItemsQuery(
            latitude=-33.9249,
            longitude=181.0,  # Invalid
        )

        # Act & Assert
        with pytest.raises(InvalidLocationError):
            await handler.handle(query)

    @pytest.mark.asyncio
    async def test_applies_pagination(
        self,
        handler: FindNearbyItemsHandler,
        mock_repository: AsyncMock,
        sample_stolen_item: StolenItem,
    ) -> None:
        """Should apply pagination to results."""
        # Arrange
        items = [sample_stolen_item for _ in range(10)]
        mock_repository.find_nearby.return_value = items

        query = FindNearbyItemsQuery(
            latitude=-33.9249,
            longitude=18.4241,
            limit=5,
            offset=2,
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert len(result.items) == 5
        assert result.total_count == 10

    @pytest.mark.asyncio
    async def test_returns_empty_result_when_no_items(
        self,
        handler: FindNearbyItemsHandler,
        valid_query: FindNearbyItemsQuery,
        mock_repository: AsyncMock,
    ) -> None:
        """Should return empty result when no items nearby."""
        # Arrange
        mock_repository.find_nearby.return_value = []

        # Act
        result = await handler.handle(valid_query)

        # Assert
        assert isinstance(result, FindNearbyItemsResult)
        assert len(result.items) == 0
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_handles_repository_errors(
        self,
        handler: FindNearbyItemsHandler,
        valid_query: FindNearbyItemsQuery,
        mock_repository: AsyncMock,
    ) -> None:
        """Should propagate repository errors."""
        # Arrange
        mock_repository.find_nearby.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await handler.handle(valid_query)
