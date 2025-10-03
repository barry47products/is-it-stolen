"""Unit tests for DeleteItem command handler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.commands.delete_item import DeleteItemCommand, DeleteItemHandler
from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.events.domain_events import ItemDeleted
from src.domain.exceptions.domain_exceptions import (
    ItemAlreadyDeletedException,
    ItemNotFoundError,
    UnauthorizedDeletionError,
)
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.infrastructure.messaging.event_bus import InMemoryEventBus


@pytest.fixture
def mock_repository() -> AsyncMock:
    """Create mock stolen item repository."""
    repository = AsyncMock(spec=IStolenItemRepository)
    return repository


@pytest.fixture
def mock_event_bus() -> AsyncMock:
    """Create mock event bus."""
    event_bus = AsyncMock(spec=InMemoryEventBus)
    return event_bus


@pytest.fixture
def handler(
    mock_repository: AsyncMock,
    mock_event_bus: AsyncMock,
) -> DeleteItemHandler:
    """Create handler instance."""
    return DeleteItemHandler(
        repository=mock_repository,
        event_bus=mock_event_bus,
    )


@pytest.fixture
def sample_stolen_item() -> StolenItem:
    """Create a sample stolen item for testing."""
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
def valid_command(sample_stolen_item: StolenItem) -> DeleteItemCommand:
    """Create a valid delete item command."""
    return DeleteItemCommand(
        report_id=str(sample_stolen_item.report_id),
        deleted_by_phone="+27821234567",
        reason="Duplicate report",
    )


class TestDeleteItemCommand:
    """Test suite for DeleteItemCommand handler."""

    @pytest.mark.asyncio
    async def test_deletes_item_successfully(
        self,
        handler: DeleteItemHandler,
        valid_command: DeleteItemCommand,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Should delete item and publish event."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item

        # Act
        result = await handler.handle(valid_command)

        # Assert
        assert result == sample_stolen_item.report_id
        assert sample_stolen_item.status == ItemStatus.DELETED
        mock_repository.save.assert_called_once_with(sample_stolen_item)
        mock_event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publishes_item_deleted_event(
        self,
        handler: DeleteItemHandler,
        valid_command: DeleteItemCommand,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Should publish ItemDeleted event with correct data."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item

        # Act
        await handler.handle(valid_command)

        # Assert
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, ItemDeleted)
        assert event.report_id == sample_stolen_item.report_id
        assert event.deleted_by.value == "+27821234567"
        assert event.reason == "Duplicate report"

    @pytest.mark.asyncio
    async def test_raises_error_when_item_not_found(
        self,
        handler: DeleteItemHandler,
        valid_command: DeleteItemCommand,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise ItemNotFoundError when item does not exist."""
        # Arrange
        mock_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ItemNotFoundError, match="not found"):
            await handler.handle(valid_command)

    @pytest.mark.asyncio
    async def test_raises_error_when_not_reporter(
        self,
        handler: DeleteItemHandler,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise UnauthorizedDeletionError when deleter is not reporter."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item
        command = DeleteItemCommand(
            report_id=str(sample_stolen_item.report_id),
            deleted_by_phone="+27829999999",  # Different phone
        )

        # Act & Assert
        with pytest.raises(UnauthorizedDeletionError, match="Only the reporter"):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_raises_error_when_already_deleted(
        self,
        handler: DeleteItemHandler,
        valid_command: DeleteItemCommand,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise ItemAlreadyDeletedException when item is already deleted."""
        # Arrange
        item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
            status=ItemStatus.DELETED,  # Already deleted
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_repository.find_by_id.return_value = item

        # Act & Assert
        with pytest.raises(ItemAlreadyDeletedException, match="already deleted"):
            await handler.handle(valid_command)

    @pytest.mark.asyncio
    async def test_allows_deletion_without_reason(
        self,
        handler: DeleteItemHandler,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Should allow deletion without providing a reason."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item
        command = DeleteItemCommand(
            report_id=str(sample_stolen_item.report_id),
            deleted_by_phone="+27821234567",
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result == sample_stolen_item.report_id
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert event.reason is None

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_phone_number(
        self,
        handler: DeleteItemHandler,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise error on invalid phone number format."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item
        command = DeleteItemCommand(
            report_id=str(sample_stolen_item.report_id),
            deleted_by_phone="invalid",  # Invalid phone
        )

        # Act & Assert
        with pytest.raises(ValueError):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_uuid(
        self,
        handler: DeleteItemHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise ValueError on invalid UUID format."""
        # Arrange
        command = DeleteItemCommand(
            report_id="not-a-uuid",
            deleted_by_phone="+27821234567",
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid UUID"):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_updates_item_timestamp(
        self,
        handler: DeleteItemHandler,
        valid_command: DeleteItemCommand,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
    ) -> None:
        """Should update item's updated_at timestamp."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item
        original_updated_at = sample_stolen_item.updated_at

        # Act
        await handler.handle(valid_command)

        # Assert
        assert sample_stolen_item.updated_at > original_updated_at

    @pytest.mark.asyncio
    async def test_deletion_is_idempotent_raises_error(
        self,
        handler: DeleteItemHandler,
        valid_command: DeleteItemCommand,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise error on duplicate deletion attempt."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item

        # Act - first deletion
        await handler.handle(valid_command)

        # Act & Assert - second deletion should fail
        with pytest.raises(ItemAlreadyDeletedException):
            await handler.handle(valid_command)
