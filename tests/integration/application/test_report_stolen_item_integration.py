"""Integration tests for Report Stolen Item command with real dependencies."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from src.application.commands.report_stolen_item import (
    ReportStolenItemCommand,
    ReportStolenItemHandler,
)
from src.domain.entities.stolen_item import ItemStatus
from src.domain.events.domain_events import ItemReported
from src.domain.value_objects.item_category import ItemCategory
from src.infrastructure.messaging.event_bus import InMemoryEventBus
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models import StolenItemModel
from src.infrastructure.persistence.repositories.postgres_stolen_item_repository import (
    PostgresStolenItemRepository,
)


class TestReportStolenItemIntegration:
    """Integration tests with real database and event bus."""

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

    @pytest.fixture
    def handler(
        self, repository: PostgresStolenItemRepository, event_bus: InMemoryEventBus
    ) -> ReportStolenItemHandler:
        """Create handler with real dependencies."""
        return ReportStolenItemHandler(repository=repository, event_bus=event_bus)

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
    async def test_persists_item_to_database(
        self, handler: ReportStolenItemHandler, valid_command: ReportStolenItemCommand
    ) -> None:
        """Should persist stolen item to real database."""
        # Act
        report_id = await handler.handle(valid_command)

        # Assert - verify in database
        with get_db() as db:
            model = db.query(StolenItemModel).filter_by(report_id=report_id).first()
            assert model is not None
            assert model.reporter_phone == valid_command.reporter_phone
            assert model.item_type == ItemCategory.BICYCLE.value
            assert model.description == valid_command.description
            assert model.brand == valid_command.brand
            assert model.model == valid_command.model
            assert model.serial_number == valid_command.serial_number
            assert model.color == valid_command.color
            assert model.status == ItemStatus.ACTIVE.value
            assert abs(model.latitude - valid_command.latitude) < 0.0001
            assert abs(model.longitude - valid_command.longitude) < 0.0001

    @pytest.mark.asyncio
    async def test_publishes_event_to_event_bus(
        self,
        handler: ReportStolenItemHandler,
        valid_command: ReportStolenItemCommand,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should publish ItemReported event to real event bus."""
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
        assert published_event.reporter_phone.value == valid_command.reporter_phone

    @pytest.mark.asyncio
    async def test_can_retrieve_persisted_item(
        self,
        handler: ReportStolenItemHandler,
        valid_command: ReportStolenItemCommand,
        repository: PostgresStolenItemRepository,
    ) -> None:
        """Should be able to retrieve item after persistence."""
        # Act
        report_id = await handler.handle(valid_command)

        # Assert - retrieve via repository
        retrieved_item = await repository.find_by_id(report_id)
        assert retrieved_item is not None
        assert retrieved_item.report_id == report_id
        assert retrieved_item.reporter_phone.value == valid_command.reporter_phone
        assert retrieved_item.item_type == ItemCategory.BICYCLE
        assert retrieved_item.description == valid_command.description

    @pytest.mark.asyncio
    async def test_handles_multiple_reports_from_same_user(
        self, handler: ReportStolenItemHandler, repository: PostgresStolenItemRepository
    ) -> None:
        """Should handle multiple reports from same phone number."""
        # Arrange
        command1 = ReportStolenItemCommand(
            reporter_phone="+27821234567",
            item_type="bicycle",
            description="Red mountain bike with black seat",
            stolen_date=datetime.now(UTC),
            latitude=-33.9249,
            longitude=18.4241,
        )
        command2 = ReportStolenItemCommand(
            reporter_phone="+27821234567",
            item_type="laptop",
            description="MacBook Pro 16 inch silver",
            stolen_date=datetime.now(UTC),
            latitude=-33.9249,
            longitude=18.4241,
        )

        # Act
        report_id1 = await handler.handle(command1)
        report_id2 = await handler.handle(command2)

        # Assert
        assert report_id1 != report_id2
        item1 = await repository.find_by_id(report_id1)
        item2 = await repository.find_by_id(report_id2)
        assert item1 is not None
        assert item2 is not None
        assert item1.item_type == ItemCategory.BICYCLE
        assert item2.item_type == ItemCategory.LAPTOP

    @pytest.mark.asyncio
    async def test_atomic_transaction_on_database_failure(
        self, valid_command: ReportStolenItemCommand
    ) -> None:
        """Should rollback on database failure (if transaction support added)."""
        # Arrange - create handler with broken repository
        from unittest.mock import AsyncMock

        broken_repository = AsyncMock()
        broken_repository.save.side_effect = Exception("Database failure")
        event_bus = InMemoryEventBus()
        handler = ReportStolenItemHandler(
            repository=broken_repository, event_bus=event_bus
        )

        # Act & Assert
        with pytest.raises(Exception, match="Database failure"):
            await handler.handle(valid_command)

        # Verify nothing was persisted
        with get_db() as db:
            count = db.query(StolenItemModel).count()
            assert count == 0
