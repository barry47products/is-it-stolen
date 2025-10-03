"""Unit tests for UpdateItem command handler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.commands.update_item import UpdateItemCommand, UpdateItemHandler
from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.events.domain_events import ItemUpdated
from src.domain.exceptions.domain_exceptions import (
    ItemNotFoundError,
    UnauthorizedUpdateError,
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
) -> UpdateItemHandler:
    """Create handler instance."""
    return UpdateItemHandler(
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
        brand="Trek",
        model="X-Caliber",
        serial_number="ABC123",
        color="Red",
    )


@pytest.fixture
def valid_command(sample_stolen_item: StolenItem) -> UpdateItemCommand:
    """Create a valid update item command."""
    return UpdateItemCommand(
        report_id=str(sample_stolen_item.report_id),
        updated_by_phone="+27821234567",
        description="Red Trek mountain bike with scratches",
        brand="Trek",
        model="X-Caliber 9",
        serial_number="ABC123456",
        color="Dark Red",
    )


class TestUpdateItemCommand:
    """Test suite for UpdateItemCommand handler."""

    @pytest.mark.asyncio
    async def test_updates_item_successfully(
        self,
        handler: UpdateItemHandler,
        valid_command: UpdateItemCommand,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Should update item and publish event."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item

        # Act
        result = await handler.handle(valid_command)

        # Assert
        assert result == sample_stolen_item.report_id
        assert sample_stolen_item.description == "Red Trek mountain bike with scratches"
        assert sample_stolen_item.model == "X-Caliber 9"
        assert sample_stolen_item.serial_number == "ABC123456"
        assert sample_stolen_item.color == "Dark Red"
        mock_repository.save.assert_called_once_with(sample_stolen_item)
        mock_event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publishes_item_updated_event(
        self,
        handler: UpdateItemHandler,
        valid_command: UpdateItemCommand,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Should publish ItemUpdated event with correct data."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item

        # Act
        await handler.handle(valid_command)

        # Assert
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, ItemUpdated)
        assert event.report_id == sample_stolen_item.report_id
        assert event.updated_by.value == "+27821234567"
        assert "description" in event.updated_fields

    @pytest.mark.asyncio
    async def test_allows_partial_update(
        self,
        handler: UpdateItemHandler,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Should allow updating only some fields."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item
        command = UpdateItemCommand(
            report_id=str(sample_stolen_item.report_id),
            updated_by_phone="+27821234567",
            description="Updated description only",
        )

        # Act
        await handler.handle(command)

        # Assert
        assert sample_stolen_item.description == "Updated description only"
        assert sample_stolen_item.brand == "Trek"  # Unchanged
        assert sample_stolen_item.model == "X-Caliber"  # Unchanged

    @pytest.mark.asyncio
    async def test_raises_error_when_item_not_found(
        self,
        handler: UpdateItemHandler,
        valid_command: UpdateItemCommand,
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
        handler: UpdateItemHandler,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise UnauthorizedUpdateError when updater is not reporter."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item
        command = UpdateItemCommand(
            report_id=str(sample_stolen_item.report_id),
            updated_by_phone="+27829999999",  # Different phone
            description="Updated description",
        )

        # Act & Assert
        with pytest.raises(UnauthorizedUpdateError, match="Only the reporter"):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_description(
        self,
        handler: UpdateItemHandler,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise error on invalid description."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item
        command = UpdateItemCommand(
            report_id=str(sample_stolen_item.report_id),
            updated_by_phone="+27821234567",
            description="Short",  # Too short
        )

        # Act & Assert
        with pytest.raises(ValueError, match="at least"):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_phone_number(
        self,
        handler: UpdateItemHandler,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise error on invalid phone number format."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item
        command = UpdateItemCommand(
            report_id=str(sample_stolen_item.report_id),
            updated_by_phone="invalid",  # Invalid phone
            description="Updated description",
        )

        # Act & Assert
        with pytest.raises(ValueError):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_uuid(
        self,
        handler: UpdateItemHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise ValueError on invalid UUID format."""
        # Arrange
        command = UpdateItemCommand(
            report_id="not-a-uuid",
            updated_by_phone="+27821234567",
            description="Updated description",
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid UUID"):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_updates_item_timestamp(
        self,
        handler: UpdateItemHandler,
        valid_command: UpdateItemCommand,
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
    async def test_no_update_if_no_fields_provided(
        self,
        handler: UpdateItemHandler,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Should still succeed but make no changes if no fields provided."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item
        command = UpdateItemCommand(
            report_id=str(sample_stolen_item.report_id),
            updated_by_phone="+27821234567",
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result == sample_stolen_item.report_id
        # No changes but event still published
        mock_event_bus.publish.assert_called_once()
