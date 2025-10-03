"""Unit tests for ListUserItems query handler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.queries.list_user_items import (
    ListUserItemsHandler,
    ListUserItemsQuery,
    ListUserItemsResult,
)
from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.exceptions.domain_exceptions import InvalidPhoneNumberError
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Create mock stolen item repository."""
    repository = AsyncMock(spec=IStolenItemRepository)
    repository.find_by_reporter = AsyncMock(return_value=[])
    return repository


@pytest.fixture
def handler(mock_repository: AsyncMock) -> ListUserItemsHandler:
    """Create handler instance."""
    return ListUserItemsHandler(repository=mock_repository)


@pytest.fixture
def sample_items() -> list[StolenItem]:
    """Create sample stolen items for testing."""
    phone = PhoneNumber("+27821234567")
    location = Location(latitude=-33.9249, longitude=18.4241)

    return [
        StolenItem(
            report_id=uuid4(),
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime(2024, 1, 15, tzinfo=UTC),
            location=location,
            status=ItemStatus.ACTIVE,
            created_at=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
            updated_at=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
        ),
        StolenItem(
            report_id=uuid4(),
            reporter_phone=phone,
            item_type=ItemCategory.PHONE,
            description="iPhone 13 Pro",
            stolen_date=datetime(2024, 1, 20, tzinfo=UTC),
            location=location,
            status=ItemStatus.RECOVERED,
            created_at=datetime(2024, 1, 20, 14, 0, tzinfo=UTC),
            updated_at=datetime(2024, 1, 25, 16, 0, tzinfo=UTC),
        ),
        StolenItem(
            report_id=uuid4(),
            reporter_phone=phone,
            item_type=ItemCategory.LAPTOP,
            description="MacBook Pro 16",
            stolen_date=datetime(2024, 1, 25, tzinfo=UTC),
            location=location,
            status=ItemStatus.ACTIVE,
            created_at=datetime(2024, 1, 25, 9, 0, tzinfo=UTC),
            updated_at=datetime(2024, 1, 25, 9, 0, tzinfo=UTC),
        ),
    ]


@pytest.fixture
def valid_query() -> ListUserItemsQuery:
    """Create a valid list user items query."""
    return ListUserItemsQuery(
        reporter_phone="+27821234567",
    )


class TestListUserItemsQuery:
    """Test suite for ListUserItemsQuery handler."""

    @pytest.mark.asyncio
    async def test_returns_all_user_items(
        self,
        handler: ListUserItemsHandler,
        valid_query: ListUserItemsQuery,
        sample_items: list[StolenItem],
        mock_repository: AsyncMock,
    ) -> None:
        """Should return all items for the user."""
        # Arrange
        mock_repository.find_by_reporter.return_value = sample_items

        # Act
        result = await handler.handle(valid_query)

        # Assert
        assert isinstance(result, ListUserItemsResult)
        assert len(result.items) == 3
        assert result.total_count == 3
        mock_repository.find_by_reporter.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_items_sorted_by_most_recent_first(
        self,
        handler: ListUserItemsHandler,
        valid_query: ListUserItemsQuery,
        sample_items: list[StolenItem],
        mock_repository: AsyncMock,
    ) -> None:
        """Should return items sorted by created_at descending."""
        # Arrange
        mock_repository.find_by_reporter.return_value = sample_items

        # Act
        result = await handler.handle(valid_query)

        # Assert
        assert len(result.items) == 3
        # Most recent first (2024-01-25, 2024-01-20, 2024-01-15)
        assert result.items[0].item_type == ItemCategory.LAPTOP
        assert result.items[1].item_type == ItemCategory.PHONE
        assert result.items[2].item_type == ItemCategory.BICYCLE

    @pytest.mark.asyncio
    async def test_filters_by_active_status(
        self,
        handler: ListUserItemsHandler,
        sample_items: list[StolenItem],
        mock_repository: AsyncMock,
    ) -> None:
        """Should filter items by active status."""
        # Arrange
        mock_repository.find_by_reporter.return_value = sample_items
        query = ListUserItemsQuery(
            reporter_phone="+27821234567",
            status="active",
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert len(result.items) == 2  # Only active items
        assert result.total_count == 2
        assert all(item.status == ItemStatus.ACTIVE for item in result.items)

    @pytest.mark.asyncio
    async def test_filters_by_recovered_status(
        self,
        handler: ListUserItemsHandler,
        sample_items: list[StolenItem],
        mock_repository: AsyncMock,
    ) -> None:
        """Should filter items by recovered status."""
        # Arrange
        mock_repository.find_by_reporter.return_value = sample_items
        query = ListUserItemsQuery(
            reporter_phone="+27821234567",
            status="recovered",
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert len(result.items) == 1  # Only recovered items
        assert result.total_count == 1
        assert result.items[0].status == ItemStatus.RECOVERED

    @pytest.mark.asyncio
    async def test_applies_pagination_with_limit(
        self,
        handler: ListUserItemsHandler,
        sample_items: list[StolenItem],
        mock_repository: AsyncMock,
    ) -> None:
        """Should apply pagination limit."""
        # Arrange
        mock_repository.find_by_reporter.return_value = sample_items
        query = ListUserItemsQuery(
            reporter_phone="+27821234567",
            limit=2,
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert len(result.items) == 2
        assert result.total_count == 3  # Total available

    @pytest.mark.asyncio
    async def test_applies_pagination_with_offset(
        self,
        handler: ListUserItemsHandler,
        sample_items: list[StolenItem],
        mock_repository: AsyncMock,
    ) -> None:
        """Should apply pagination offset."""
        # Arrange
        mock_repository.find_by_reporter.return_value = sample_items
        query = ListUserItemsQuery(
            reporter_phone="+27821234567",
            offset=1,
            limit=2,
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert len(result.items) == 2
        assert result.total_count == 3
        # Should skip first item (Laptop) and return Phone and Bicycle
        assert result.items[0].item_type == ItemCategory.PHONE
        assert result.items[1].item_type == ItemCategory.BICYCLE

    @pytest.mark.asyncio
    async def test_returns_empty_result_when_no_items(
        self,
        handler: ListUserItemsHandler,
        valid_query: ListUserItemsQuery,
        mock_repository: AsyncMock,
    ) -> None:
        """Should return empty result when user has no items."""
        # Arrange
        mock_repository.find_by_reporter.return_value = []

        # Act
        result = await handler.handle(valid_query)

        # Assert
        assert isinstance(result, ListUserItemsResult)
        assert len(result.items) == 0
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_uses_default_pagination_when_not_specified(
        self,
        handler: ListUserItemsHandler,
        valid_query: ListUserItemsQuery,
        sample_items: list[StolenItem],
        mock_repository: AsyncMock,
    ) -> None:
        """Should use default limit and offset when not specified."""
        # Arrange
        mock_repository.find_by_reporter.return_value = sample_items

        # Act
        result = await handler.handle(valid_query)

        # Assert
        assert len(result.items) == 3  # Default limit is 50, so all 3 returned
        assert result.total_count == 3

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_phone_number(
        self,
        handler: ListUserItemsHandler,
    ) -> None:
        """Should raise InvalidPhoneNumberError on invalid phone format."""
        # Arrange
        query = ListUserItemsQuery(
            reporter_phone="invalid-phone",
        )

        # Act & Assert
        with pytest.raises(InvalidPhoneNumberError):
            await handler.handle(query)

    @pytest.mark.asyncio
    async def test_handles_repository_errors(
        self,
        handler: ListUserItemsHandler,
        valid_query: ListUserItemsQuery,
        mock_repository: AsyncMock,
    ) -> None:
        """Should propagate repository errors."""
        # Arrange
        mock_repository.find_by_reporter.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await handler.handle(valid_query)

    @pytest.mark.asyncio
    async def test_combines_status_filter_and_pagination(
        self,
        handler: ListUserItemsHandler,
        sample_items: list[StolenItem],
        mock_repository: AsyncMock,
    ) -> None:
        """Should apply both status filter and pagination."""
        # Arrange
        mock_repository.find_by_reporter.return_value = sample_items
        query = ListUserItemsQuery(
            reporter_phone="+27821234567",
            status="active",
            limit=1,
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert len(result.items) == 1  # Limited to 1
        assert result.total_count == 2  # Total active items
        assert result.items[0].status == ItemStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_ignores_invalid_status_filter(
        self,
        handler: ListUserItemsHandler,
        sample_items: list[StolenItem],
        mock_repository: AsyncMock,
    ) -> None:
        """Should return all items when status filter is invalid."""
        # Arrange
        mock_repository.find_by_reporter.return_value = sample_items
        query = ListUserItemsQuery(
            reporter_phone="+27821234567",
            status="invalid_status",  # Invalid status
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert len(result.items) == 3  # All items returned
        assert result.total_count == 3
