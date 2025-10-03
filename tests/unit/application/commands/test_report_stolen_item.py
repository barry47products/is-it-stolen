"""Unit tests for Report Stolen Item command handler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from src.application.commands.report_stolen_item import (
    ReportStolenItemCommand,
    ReportStolenItemHandler,
)
from src.domain.entities.stolen_item import StolenItem
from src.domain.events.domain_events import ItemReported
from src.domain.exceptions.domain_exceptions import (
    InvalidItemCategoryError,
    InvalidLocationError,
    InvalidPhoneNumberError,
)
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.value_objects.item_category import ItemCategory
from src.infrastructure.messaging.event_bus import InMemoryEventBus


class TestReportStolenItemCommand:
    """Test suite for ReportStolenItemCommand handler."""

    @pytest.fixture
    def mock_repository(self) -> AsyncMock:
        """Create mock stolen item repository."""
        repository = AsyncMock(spec=IStolenItemRepository)
        repository.save = AsyncMock()
        repository.find_by_reporter = AsyncMock(return_value=[])
        return repository

    @pytest.fixture
    def event_bus(self) -> InMemoryEventBus:
        """Create in-memory event bus."""
        return InMemoryEventBus()

    @pytest.fixture
    def handler(
        self, mock_repository: AsyncMock, event_bus: InMemoryEventBus
    ) -> ReportStolenItemHandler:
        """Create command handler with mocked dependencies."""
        return ReportStolenItemHandler(repository=mock_repository, event_bus=event_bus)

    @pytest.fixture
    def valid_command(self) -> ReportStolenItemCommand:
        """Create valid command."""
        return ReportStolenItemCommand(
            reporter_phone="+27821234567",
            item_type="bicycle",
            description="Red mountain bike with black seat",
            stolen_date=datetime.now(UTC),
            latitude=-33.9249,
            longitude=18.4241,
            brand="Giant",
            model="Talon 2",
            serial_number="GT123456",
            color="red",
        )

    @pytest.mark.asyncio
    async def test_handles_valid_command_successfully(
        self,
        handler: ReportStolenItemHandler,
        valid_command: ReportStolenItemCommand,
        mock_repository: AsyncMock,
    ) -> None:
        """Should create stolen item and return report ID."""
        # Act
        report_id = await handler.handle(valid_command)

        # Assert
        assert isinstance(report_id, UUID)
        mock_repository.save.assert_called_once()
        saved_item = mock_repository.save.call_args[0][0]
        assert isinstance(saved_item, StolenItem)
        assert saved_item.description == valid_command.description

    @pytest.mark.asyncio
    async def test_creates_stolen_item_with_correct_attributes(
        self,
        handler: ReportStolenItemHandler,
        valid_command: ReportStolenItemCommand,
        mock_repository: AsyncMock,
    ) -> None:
        """Should create StolenItem with all command attributes."""
        # Act
        await handler.handle(valid_command)

        # Assert
        saved_item: StolenItem = mock_repository.save.call_args[0][0]
        assert saved_item.reporter_phone.value == valid_command.reporter_phone
        assert saved_item.item_type == ItemCategory.BICYCLE
        assert saved_item.description == valid_command.description
        assert saved_item.location.latitude == valid_command.latitude
        assert saved_item.location.longitude == valid_command.longitude
        assert saved_item.brand == valid_command.brand
        assert saved_item.model == valid_command.model
        assert saved_item.serial_number == valid_command.serial_number
        assert saved_item.color == valid_command.color

    @pytest.mark.asyncio
    async def test_publishes_item_reported_event(
        self,
        handler: ReportStolenItemHandler,
        valid_command: ReportStolenItemCommand,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should publish ItemReported event after saving."""
        # Arrange
        event_handler = AsyncMock()
        event_bus.subscribe(ItemReported, event_handler)

        # Act
        report_id = await handler.handle(valid_command)

        # Assert
        event_handler.assert_called_once()
        published_event: ItemReported = event_handler.call_args[0][0]
        assert published_event.report_id == report_id
        assert published_event.item_type == ItemCategory.BICYCLE
        assert published_event.description == valid_command.description

    @pytest.mark.asyncio
    async def test_rejects_invalid_phone_number(
        self, handler: ReportStolenItemHandler, valid_command: ReportStolenItemCommand
    ) -> None:
        """Should raise InvalidPhoneNumberError for invalid phone."""
        # Arrange
        valid_command.reporter_phone = "invalid_phone"

        # Act & Assert
        with pytest.raises(InvalidPhoneNumberError):
            await handler.handle(valid_command)

    @pytest.mark.asyncio
    async def test_rejects_invalid_item_category(
        self, handler: ReportStolenItemHandler, valid_command: ReportStolenItemCommand
    ) -> None:
        """Should raise InvalidItemCategoryError for invalid category."""
        # Arrange
        valid_command.item_type = "invalid_category"

        # Act & Assert
        with pytest.raises(InvalidItemCategoryError):
            await handler.handle(valid_command)

    @pytest.mark.asyncio
    async def test_rejects_invalid_latitude(
        self, handler: ReportStolenItemHandler, valid_command: ReportStolenItemCommand
    ) -> None:
        """Should raise InvalidLocationError for invalid latitude."""
        # Arrange
        valid_command.latitude = 91.0  # Invalid latitude

        # Act & Assert
        with pytest.raises(InvalidLocationError):
            await handler.handle(valid_command)

    @pytest.mark.asyncio
    async def test_rejects_invalid_longitude(
        self, handler: ReportStolenItemHandler, valid_command: ReportStolenItemCommand
    ) -> None:
        """Should raise InvalidLocationError for invalid longitude."""
        # Arrange
        valid_command.longitude = 181.0  # Invalid longitude

        # Act & Assert
        with pytest.raises(InvalidLocationError):
            await handler.handle(valid_command)

    @pytest.mark.asyncio
    async def test_rejects_empty_description(
        self, handler: ReportStolenItemHandler, valid_command: ReportStolenItemCommand
    ) -> None:
        """Should raise ValueError for empty description."""
        # Arrange
        valid_command.description = ""

        # Act & Assert
        with pytest.raises(ValueError, match="Description cannot be empty"):
            await handler.handle(valid_command)

    @pytest.mark.asyncio
    async def test_rejects_short_description(
        self, handler: ReportStolenItemHandler, valid_command: ReportStolenItemCommand
    ) -> None:
        """Should raise ValueError for too short description."""
        # Arrange
        valid_command.description = "Short"  # Less than 10 characters

        # Act & Assert
        with pytest.raises(ValueError, match="at least 10 characters"):
            await handler.handle(valid_command)

    @pytest.mark.asyncio
    async def test_rejects_future_stolen_date(
        self, handler: ReportStolenItemHandler, valid_command: ReportStolenItemCommand
    ) -> None:
        """Should raise ValueError for future stolen date."""
        # Arrange
        future_date = datetime(2030, 1, 1, tzinfo=UTC)
        valid_command.stolen_date = future_date

        # Act & Assert
        with pytest.raises(ValueError, match="cannot be in the future"):
            await handler.handle(valid_command)

    @pytest.mark.asyncio
    async def test_handles_repository_save_failure(
        self,
        handler: ReportStolenItemHandler,
        valid_command: ReportStolenItemCommand,
        mock_repository: AsyncMock,
    ) -> None:
        """Should propagate repository errors."""
        # Arrange
        mock_repository.save.side_effect = Exception("Database connection failed")

        # Act & Assert
        with pytest.raises(Exception, match="Database connection failed"):
            await handler.handle(valid_command)

    @pytest.mark.asyncio
    async def test_handles_command_with_optional_fields_none(
        self,
        handler: ReportStolenItemHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Should handle command with optional fields as None."""
        # Arrange
        command = ReportStolenItemCommand(
            reporter_phone="+27821234567",
            item_type="bicycle",
            description="Red mountain bike with black seat",
            stolen_date=datetime.now(UTC),
            latitude=-33.9249,
            longitude=18.4241,
            brand=None,
            model=None,
            serial_number=None,
            color=None,
        )

        # Act
        report_id = await handler.handle(command)

        # Assert
        assert isinstance(report_id, UUID)
        saved_item: StolenItem = mock_repository.save.call_args[0][0]
        assert saved_item.brand is None
        assert saved_item.model is None
        assert saved_item.serial_number is None
        assert saved_item.color is None
