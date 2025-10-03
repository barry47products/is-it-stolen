"""Unit tests for Check If Stolen query handler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.queries.check_if_stolen import (
    CheckIfStolenHandler,
    CheckIfStolenQuery,
    CheckIfStolenResult,
    ItemMatch,
)
from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.services.matching_service import ItemMatchingService
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber


class TestCheckIfStolenQuery:
    """Test suite for CheckIfStolenQuery handler."""

    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        """Create mock stolen item repository."""
        repository = AsyncMock(spec=IStolenItemRepository)
        repository.find_by_category = AsyncMock(return_value=[])
        repository.find_nearby = AsyncMock(return_value=[])
        return repository

    @pytest.fixture
    def matching_service(self) -> ItemMatchingService:
        """Create real matching service."""
        return ItemMatchingService(threshold=0.5)

    @pytest.fixture
    def handler(
        self, mock_repository: AsyncMock, matching_service: ItemMatchingService
    ) -> CheckIfStolenHandler:
        """Create query handler with mocked dependencies."""
        return CheckIfStolenHandler(
            repository=mock_repository, matching_service=matching_service
        )

    @pytest.fixture
    def sample_stolen_item(self) -> StolenItem:
        """Create sample stolen item for testing."""
        return StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike with black seat",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            brand="Giant",
            model="Talon 2",
            serial_number="GT123456",
            color="red",
        )

    @pytest.fixture
    def valid_query(self) -> CheckIfStolenQuery:
        """Create valid query."""
        return CheckIfStolenQuery(
            description="Red mountain bike",
            brand="Giant",
            model="Talon 2",
            serial_number="GT123456",
            color="red",
            category="bicycle",
        )

    @pytest.mark.asyncio
    async def test_handles_valid_query_successfully(
        self,
        handler: CheckIfStolenHandler,
        valid_query: CheckIfStolenQuery,
        mock_repository: AsyncMock,
        sample_stolen_item: StolenItem,
    ) -> None:
        """Should return matches with similarity scores."""
        # Arrange
        mock_repository.find_by_category.return_value = [sample_stolen_item]

        # Act
        result = await handler.handle(valid_query)

        # Assert
        assert isinstance(result, CheckIfStolenResult)
        assert len(result.matches) == 1
        assert result.total_count == 1
        mock_repository.find_by_category.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_matches_with_similarity_scores(
        self,
        handler: CheckIfStolenHandler,
        valid_query: CheckIfStolenQuery,
        mock_repository: AsyncMock,
        sample_stolen_item: StolenItem,
    ) -> None:
        """Should calculate and return similarity scores for each match."""
        # Arrange
        mock_repository.find_by_category.return_value = [sample_stolen_item]

        # Act
        result = await handler.handle(valid_query)

        # Assert
        match = result.matches[0]
        assert isinstance(match, ItemMatch)
        assert match.item == sample_stolen_item
        assert 0.0 <= match.similarity_score <= 1.0
        assert match.similarity_score > 0.5  # Above threshold

    @pytest.mark.asyncio
    async def test_filters_out_low_similarity_matches(
        self,
        handler: CheckIfStolenHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Should filter out items with similarity below threshold."""
        # Arrange - completely different item
        different_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.LAPTOP,
            description="Silver MacBook Pro laptop",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            brand="Apple",
            model="MacBook Pro",
            serial_number="APPLE123",
        )
        mock_repository.find_by_category.return_value = [different_item]

        query = CheckIfStolenQuery(
            description="Red mountain bike",
            brand="Giant",
            category="bicycle",
        )

        # Act
        result = await handler.handle(query)

        # Assert - no matches due to low similarity
        assert result.total_count == 0
        assert len(result.matches) == 0

    @pytest.mark.asyncio
    async def test_sorts_matches_by_similarity_descending(
        self,
        handler: CheckIfStolenHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Should sort matches by similarity score (highest first)."""
        # Arrange - multiple items with varying similarity
        perfect_match = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike with black seat",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            brand="Giant",
            model="Talon 2",
        )

        partial_match = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike with seat",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            brand="Giant",
            model="Talon",  # Similar but not exact
        )

        mock_repository.find_by_category.return_value = [partial_match, perfect_match]

        query = CheckIfStolenQuery(
            description="Red mountain bike with black seat",
            brand="Giant",
            model="Talon 2",
            category="bicycle",
        )

        # Act
        result = await handler.handle(query)

        # Assert - perfect match should be first
        assert len(result.matches) == 2
        assert result.matches[0].similarity_score > result.matches[1].similarity_score
        assert result.matches[0].item == perfect_match

    @pytest.mark.asyncio
    async def test_queries_by_category_when_specified(
        self,
        handler: CheckIfStolenHandler,
        valid_query: CheckIfStolenQuery,
        mock_repository: AsyncMock,
    ) -> None:
        """Should query repository by category when category is provided."""
        # Arrange
        mock_repository.find_by_category.return_value = []

        # Act
        await handler.handle(valid_query)

        # Assert
        mock_repository.find_by_category.assert_called_once_with(
            category=ItemCategory.BICYCLE, status=ItemStatus.ACTIVE, limit=100
        )

    @pytest.mark.asyncio
    async def test_queries_by_location_when_specified(
        self,
        handler: CheckIfStolenHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Should query repository by location when location is provided."""
        # Arrange
        mock_repository.find_nearby.return_value = []

        query = CheckIfStolenQuery(
            description="Red mountain bike",
            latitude=-33.9249,
            longitude=18.4241,
            radius_km=10.0,
        )

        # Act
        await handler.handle(query)

        # Assert
        mock_repository.find_nearby.assert_called_once()
        call_args = mock_repository.find_nearby.call_args[1]
        assert call_args["location"].latitude == -33.9249
        assert call_args["location"].longitude == 18.4241
        assert call_args["radius_km"] == 10.0

    @pytest.mark.asyncio
    async def test_applies_pagination(
        self,
        handler: CheckIfStolenHandler,
        mock_repository: AsyncMock,
        sample_stolen_item: StolenItem,
    ) -> None:
        """Should apply pagination to results."""
        # Arrange - create multiple items
        items = [sample_stolen_item for _ in range(10)]
        mock_repository.find_by_category.return_value = items

        query = CheckIfStolenQuery(
            description="Red mountain bike with black seat",
            brand="Giant",
            model="Talon 2",
            serial_number="GT123456",
            category="bicycle",
            limit=5,
            offset=2,
        )

        # Act
        result = await handler.handle(query)

        # Assert - should return 5 items starting from offset 2
        assert len(result.matches) == 5
        assert result.total_count == 10  # Total before pagination

    @pytest.mark.asyncio
    async def test_returns_empty_result_when_no_matches(
        self,
        handler: CheckIfStolenHandler,
        valid_query: CheckIfStolenQuery,
        mock_repository: AsyncMock,
    ) -> None:
        """Should return empty result when no items match."""
        # Arrange
        mock_repository.find_by_category.return_value = []

        # Act
        result = await handler.handle(valid_query)

        # Assert
        assert isinstance(result, CheckIfStolenResult)
        assert len(result.matches) == 0
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_handles_query_without_optional_fields(
        self,
        handler: CheckIfStolenHandler,
        mock_repository: AsyncMock,
        sample_stolen_item: StolenItem,
    ) -> None:
        """Should handle query with only description (minimal query)."""
        # Arrange
        mock_repository.find_by_category.return_value = [sample_stolen_item]

        query = CheckIfStolenQuery(description="Red mountain bike")

        # Act
        result = await handler.handle(query)

        # Assert - should still work and return results
        assert isinstance(result, CheckIfStolenResult)

    @pytest.mark.asyncio
    async def test_uses_default_pagination_when_not_specified(
        self,
        handler: CheckIfStolenHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Should use default limit and offset when not provided."""
        # Arrange
        mock_repository.find_by_category.return_value = []

        query = CheckIfStolenQuery(
            description="Red mountain bike",
            category="bicycle",
        )

        # Act
        await handler.handle(query)

        # Assert - should use defaults
        assert query.limit == 50  # Default limit
        assert query.offset == 0  # Default offset

    @pytest.mark.asyncio
    async def test_includes_match_reason_in_results(
        self,
        handler: CheckIfStolenHandler,
        valid_query: CheckIfStolenQuery,
        mock_repository: AsyncMock,
        sample_stolen_item: StolenItem,
    ) -> None:
        """Should include match reason for each result."""
        # Arrange
        mock_repository.find_by_category.return_value = [sample_stolen_item]

        # Act
        result = await handler.handle(valid_query)

        # Assert
        match = result.matches[0]
        assert match.match_reason is not None
        assert isinstance(match.match_reason, str)
        assert len(match.match_reason) > 0

    @pytest.mark.asyncio
    async def test_handles_repository_errors(
        self,
        handler: CheckIfStolenHandler,
        valid_query: CheckIfStolenQuery,
        mock_repository: AsyncMock,
    ) -> None:
        """Should propagate repository errors."""
        # Arrange
        mock_repository.find_by_category.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await handler.handle(valid_query)

    @pytest.mark.asyncio
    async def test_queries_by_location_with_category_filter(
        self,
        handler: CheckIfStolenHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Should query by location with category filter when both provided."""
        # Arrange
        mock_repository.find_nearby.return_value = []

        query = CheckIfStolenQuery(
            description="Red mountain bike",
            latitude=-33.9249,
            longitude=18.4241,
            radius_km=10.0,
            category="bicycle",
        )

        # Act
        await handler.handle(query)

        # Assert
        mock_repository.find_nearby.assert_called_once()
        call_args = mock_repository.find_nearby.call_args[1]
        assert call_args["category"] == ItemCategory.BICYCLE

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_latitude(
        self,
        handler: CheckIfStolenHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise InvalidLocationError for invalid latitude."""
        # Arrange
        from src.domain.exceptions.domain_exceptions import InvalidLocationError

        query = CheckIfStolenQuery(
            description="Red mountain bike",
            latitude=91.0,  # Invalid latitude
            longitude=18.4241,
        )

        # Act & Assert
        with pytest.raises(InvalidLocationError):
            await handler.handle(query)

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_longitude(
        self,
        handler: CheckIfStolenHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise InvalidLocationError for invalid longitude."""
        # Arrange
        from src.domain.exceptions.domain_exceptions import InvalidLocationError

        query = CheckIfStolenQuery(
            description="Red mountain bike",
            latitude=-33.9249,
            longitude=181.0,  # Invalid longitude
        )

        # Act & Assert
        with pytest.raises(InvalidLocationError):
            await handler.handle(query)
