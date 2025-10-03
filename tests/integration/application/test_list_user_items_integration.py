"""Integration tests for ListUserItems query with real database."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.application.queries.list_user_items import (
    ListUserItemsHandler,
    ListUserItemsQuery,
)
from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models import StolenItemModel
from src.infrastructure.persistence.repositories.postgres_stolen_item_repository import (
    PostgresStolenItemRepository,
)


class TestListUserItemsIntegration:
    """Integration tests with real PostgreSQL database."""

    @pytest.fixture(autouse=True)
    def clear_database(self) -> None:
        """Clear stolen_items table before each test."""
        with get_db() as db:
            db.query(StolenItemModel).delete()
            db.commit()

    @pytest.fixture
    def repository(self) -> PostgresStolenItemRepository:
        """Create real repository instance."""
        return PostgresStolenItemRepository()

    @pytest.fixture
    def handler(self, repository: PostgresStolenItemRepository) -> ListUserItemsHandler:
        """Create handler with real dependencies."""
        return ListUserItemsHandler(repository=repository)

    @pytest.mark.asyncio
    async def test_retrieves_all_user_items_from_database(
        self,
        handler: ListUserItemsHandler,
        repository: PostgresStolenItemRepository,
    ) -> None:
        """Should retrieve all items for a user from real database."""
        # Arrange - create items for user
        phone = PhoneNumber("+27821234567")
        location = Location(latitude=-33.9249, longitude=18.4241)

        item1 = StolenItem(
            report_id=uuid4(),
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=location,
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        item2 = StolenItem(
            report_id=uuid4(),
            reporter_phone=phone,
            item_type=ItemCategory.PHONE,
            description="iPhone 13 Pro",
            stolen_date=datetime.now(UTC),
            location=location,
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await repository.save(item1)
        await repository.save(item2)

        query = ListUserItemsQuery(reporter_phone="+27821234567")

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_count == 2
        assert len(result.items) == 2
        assert all(item.reporter_phone.value == "+27821234567" for item in result.items)

    @pytest.mark.asyncio
    async def test_returns_items_sorted_by_most_recent(
        self,
        handler: ListUserItemsHandler,
        repository: PostgresStolenItemRepository,
    ) -> None:
        """Should return items sorted by created_at descending."""
        # Arrange
        phone = PhoneNumber("+27821234567")
        location = Location(latitude=-33.9249, longitude=18.4241)

        # Create items with different timestamps
        item1 = StolenItem(
            report_id=uuid4(),
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime(2024, 1, 15, tzinfo=UTC),
            location=location,
            status=ItemStatus.ACTIVE,
            created_at=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
            updated_at=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
        )
        item2 = StolenItem(
            report_id=uuid4(),
            reporter_phone=phone,
            item_type=ItemCategory.PHONE,
            description="iPhone 13 Pro",
            stolen_date=datetime(2024, 1, 20, tzinfo=UTC),
            location=location,
            status=ItemStatus.ACTIVE,
            created_at=datetime(2024, 1, 20, 14, 0, tzinfo=UTC),
            updated_at=datetime(2024, 1, 20, 14, 0, tzinfo=UTC),
        )

        await repository.save(item1)
        await repository.save(item2)

        query = ListUserItemsQuery(reporter_phone="+27821234567")

        # Act
        result = await handler.handle(query)

        # Assert
        assert len(result.items) == 2
        # Most recent first
        assert result.items[0].item_type == ItemCategory.PHONE
        assert result.items[1].item_type == ItemCategory.BICYCLE

    @pytest.mark.asyncio
    async def test_filters_by_status_in_database(
        self,
        handler: ListUserItemsHandler,
        repository: PostgresStolenItemRepository,
    ) -> None:
        """Should filter items by status with real database."""
        # Arrange
        phone = PhoneNumber("+27821234567")
        location = Location(latitude=-33.9249, longitude=18.4241)

        active_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=location,
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        recovered_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=phone,
            item_type=ItemCategory.PHONE,
            description="iPhone 13 Pro",
            stolen_date=datetime.now(UTC),
            location=location,
            status=ItemStatus.RECOVERED,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await repository.save(active_item)
        await repository.save(recovered_item)

        query = ListUserItemsQuery(reporter_phone="+27821234567", status="active")

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].status == ItemStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_applies_pagination_with_real_data(
        self,
        handler: ListUserItemsHandler,
        repository: PostgresStolenItemRepository,
    ) -> None:
        """Should apply pagination with real database."""
        # Arrange - create multiple items
        phone = PhoneNumber("+27821234567")
        location = Location(latitude=-33.9249, longitude=18.4241)

        for i in range(5):
            item = StolenItem(
                report_id=uuid4(),
                reporter_phone=phone,
                item_type=ItemCategory.BICYCLE,
                description=f"Item {i}",
                stolen_date=datetime.now(UTC),
                location=location,
                status=ItemStatus.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            await repository.save(item)

        query = ListUserItemsQuery(reporter_phone="+27821234567", limit=2, offset=1)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_count == 5  # Total items
        assert len(result.items) == 2  # Limited to 2

    @pytest.mark.asyncio
    async def test_returns_empty_for_user_with_no_items(
        self,
        handler: ListUserItemsHandler,
        repository: PostgresStolenItemRepository,
    ) -> None:
        """Should return empty result for user with no items."""
        # Arrange - create item for different user
        other_phone = PhoneNumber("+27829999999")
        location = Location(latitude=-33.9249, longitude=18.4241)

        item = StolenItem(
            report_id=uuid4(),
            reporter_phone=other_phone,
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=location,
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        await repository.save(item)

        query = ListUserItemsQuery(reporter_phone="+27821234567")

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_count == 0
        assert len(result.items) == 0

    @pytest.mark.asyncio
    async def test_only_returns_items_for_specified_user(
        self,
        handler: ListUserItemsHandler,
        repository: PostgresStolenItemRepository,
    ) -> None:
        """Should only return items for the specified user."""
        # Arrange - create items for two different users
        user1_phone = PhoneNumber("+27821234567")
        user2_phone = PhoneNumber("+27829999999")
        location = Location(latitude=-33.9249, longitude=18.4241)

        user1_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=user1_phone,
            item_type=ItemCategory.BICYCLE,
            description="User 1 bike",
            stolen_date=datetime.now(UTC),
            location=location,
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        user2_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=user2_phone,
            item_type=ItemCategory.PHONE,
            description="User 2 phone",
            stolen_date=datetime.now(UTC),
            location=location,
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await repository.save(user1_item)
        await repository.save(user2_item)

        query = ListUserItemsQuery(reporter_phone="+27821234567")

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].reporter_phone.value == "+27821234567"
        assert result.items[0].description == "User 1 bike"
