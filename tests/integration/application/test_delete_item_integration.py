"""Integration tests for DeleteItem command with real database."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.application.commands.delete_item import DeleteItemCommand, DeleteItemHandler
from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.exceptions.domain_exceptions import (
    ItemAlreadyDeletedException,
    ItemNotFoundError,
    UnauthorizedDeletionError,
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


class TestDeleteItemIntegration:
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
    async def test_deletes_item_with_real_database(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should delete item and persist to real database."""
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
        )
        await repository.save(item)

        handler = DeleteItemHandler(
            repository=repository,
            event_bus=event_bus,
        )

        command = DeleteItemCommand(
            report_id=str(item.report_id),
            deleted_by_phone="+27821234567",
            reason="Test deletion",
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result == item.report_id

        # Verify persisted in database
        retrieved = await repository.find_by_id(item.report_id)
        assert retrieved is not None
        assert retrieved.status == ItemStatus.DELETED

    @pytest.mark.asyncio
    async def test_prevents_deletion_by_non_reporter(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should prevent deletion by someone other than reporter."""
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

        handler = DeleteItemHandler(
            repository=repository,
            event_bus=event_bus,
        )

        command = DeleteItemCommand(
            report_id=str(item.report_id),
            deleted_by_phone="+27829999999",  # Different phone
        )

        # Act & Assert
        with pytest.raises(UnauthorizedDeletionError):
            await handler.handle(command)

        # Verify not persisted
        retrieved = await repository.find_by_id(item.report_id)
        assert retrieved is not None
        assert retrieved.status == ItemStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_prevents_double_deletion(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should prevent deleting an already deleted item."""
        # Arrange - create and delete an item
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

        handler = DeleteItemHandler(
            repository=repository,
            event_bus=event_bus,
        )

        command = DeleteItemCommand(
            report_id=str(item.report_id),
            deleted_by_phone="+27821234567",
        )

        # First deletion
        await handler.handle(command)

        # Act & Assert - second deletion should fail
        with pytest.raises(ItemAlreadyDeletedException):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_raises_error_for_nonexistent_item(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should raise error when item doesn't exist."""
        # Arrange
        handler = DeleteItemHandler(
            repository=repository,
            event_bus=event_bus,
        )

        command = DeleteItemCommand(
            report_id=str(uuid4()),  # Non-existent ID
            deleted_by_phone="+27821234567",
        )

        # Act & Assert
        with pytest.raises(ItemNotFoundError):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_deletion_preserves_audit_trail(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should preserve item in database for audit trail (soft delete)."""
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

        handler = DeleteItemHandler(
            repository=repository,
            event_bus=event_bus,
        )

        command = DeleteItemCommand(
            report_id=str(item.report_id),
            deleted_by_phone="+27821234567",
        )

        # Act
        await handler.handle(command)

        # Assert - item still exists in database, just marked as deleted
        retrieved = await repository.find_by_id(item.report_id)
        assert retrieved is not None
        assert retrieved.status == ItemStatus.DELETED
        assert retrieved.description == "Red mountain bike"
        assert retrieved.reporter_phone.value == "+27821234567"
