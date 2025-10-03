"""Integration tests for UpdateItem command with real database."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.application.commands.update_item import UpdateItemCommand, UpdateItemHandler
from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.exceptions.domain_exceptions import (
    ItemNotFoundError,
    UnauthorizedUpdateError,
)
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.infrastructure.messaging.event_bus import InMemoryEventBus
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models import StolenItemModel
from src.infrastructure.persistence.repositories.postgres_stolen_item_repository import (
    PostgresStolenItemRepository,
)


class TestUpdateItemIntegration:
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
    def event_bus(self) -> InMemoryEventBus:
        """Create real event bus instance."""
        return InMemoryEventBus()

    @pytest.mark.asyncio
    async def test_updates_item_with_real_database(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should update item and persist to real database."""
        # Arrange - create and save an item
        item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            brand="Trek",
            model="X-Caliber",
        )
        await repository.save(item)

        handler = UpdateItemHandler(
            repository=repository,
            event_bus=event_bus,
        )

        command = UpdateItemCommand(
            report_id=str(item.report_id),
            updated_by_phone="+27821234567",
            description="Red Trek mountain bike with scratches",
            model="X-Caliber 9",
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result == item.report_id

        # Verify persisted in database
        retrieved = await repository.find_by_id(item.report_id)
        assert retrieved is not None
        assert retrieved.description == "Red Trek mountain bike with scratches"
        assert retrieved.model == "X-Caliber 9"
        assert retrieved.brand == "Trek"  # Unchanged

    @pytest.mark.asyncio
    async def test_allows_partial_update_in_database(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should allow updating only specific fields."""
        # Arrange
        item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            brand="Trek",
            model="X-Caliber",
            serial_number="ABC123",
        )
        await repository.save(item)

        handler = UpdateItemHandler(
            repository=repository,
            event_bus=event_bus,
        )

        command = UpdateItemCommand(
            report_id=str(item.report_id),
            updated_by_phone="+27821234567",
            description="Updated description only",
        )

        # Act
        await handler.handle(command)

        # Assert
        retrieved = await repository.find_by_id(item.report_id)
        assert retrieved is not None
        assert retrieved.description == "Updated description only"
        assert retrieved.brand == "Trek"  # Unchanged
        assert retrieved.model == "X-Caliber"  # Unchanged
        assert retrieved.serial_number == "ABC123"  # Unchanged

    @pytest.mark.asyncio
    async def test_prevents_update_by_non_reporter(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should prevent update by someone other than reporter."""
        # Arrange
        item = StolenItem(
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
        await repository.save(item)

        handler = UpdateItemHandler(
            repository=repository,
            event_bus=event_bus,
        )

        command = UpdateItemCommand(
            report_id=str(item.report_id),
            updated_by_phone="+27829999999",  # Different phone
            description="Updated description",
        )

        # Act & Assert
        with pytest.raises(UnauthorizedUpdateError):
            await handler.handle(command)

        # Verify not persisted
        retrieved = await repository.find_by_id(item.report_id)
        assert retrieved is not None
        assert retrieved.description == "Red mountain bike"  # Unchanged

    @pytest.mark.asyncio
    async def test_raises_error_for_nonexistent_item(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should raise error when item doesn't exist."""
        # Arrange
        handler = UpdateItemHandler(
            repository=repository,
            event_bus=event_bus,
        )

        command = UpdateItemCommand(
            report_id=str(uuid4()),  # Non-existent ID
            updated_by_phone="+27821234567",
            description="Updated description",
        )

        # Act & Assert
        with pytest.raises(ItemNotFoundError):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_update_all_mutable_fields(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should update all mutable fields together."""
        # Arrange
        item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            brand="Trek",
            model="X-Caliber",
            serial_number="ABC123",
            color="Red",
        )
        await repository.save(item)

        handler = UpdateItemHandler(
            repository=repository,
            event_bus=event_bus,
        )

        command = UpdateItemCommand(
            report_id=str(item.report_id),
            updated_by_phone="+27821234567",
            description="Red Trek mountain bike with scratches",
            brand="Trek Bicycles",
            model="X-Caliber 9",
            serial_number="ABC123456",
            color="Dark Red",
        )

        # Act
        await handler.handle(command)

        # Assert
        retrieved = await repository.find_by_id(item.report_id)
        assert retrieved is not None
        assert retrieved.description == "Red Trek mountain bike with scratches"
        assert retrieved.brand == "Trek Bicycles"
        assert retrieved.model == "X-Caliber 9"
        assert retrieved.serial_number == "ABC123456"
        assert retrieved.color == "Dark Red"
