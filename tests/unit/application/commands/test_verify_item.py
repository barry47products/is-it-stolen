"""Unit tests for VerifyItem command handler."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.commands.verify_item import VerifyItemCommand, VerifyItemHandler
from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.events.domain_events import ItemVerified
from src.domain.exceptions.domain_exceptions import (
    InvalidPoliceReferenceError,
    ItemAlreadyVerifiedError,
    ItemNotActiveError,
    ItemNotFoundError,
    UnauthorizedVerificationError,
)
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.services.verification_service import VerificationService
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.domain.value_objects.police_reference import PoliceReference
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
def verification_service() -> VerificationService:
    """Create verification service."""
    return VerificationService()


@pytest.fixture
def handler(
    mock_repository: AsyncMock,
    mock_event_bus: AsyncMock,
    verification_service: VerificationService,
) -> VerifyItemHandler:
    """Create handler instance."""
    return VerifyItemHandler(
        repository=mock_repository,
        event_bus=mock_event_bus,
        verification_service=verification_service,
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
def valid_command(sample_stolen_item: StolenItem) -> VerifyItemCommand:
    """Create a valid verify item command."""
    return VerifyItemCommand(
        report_id=str(sample_stolen_item.report_id),
        police_reference="CR/2024/123456",
        verified_by_phone="+27821234567",
    )


class TestVerifyItemCommand:
    """Test suite for VerifyItemCommand handler."""

    @pytest.mark.asyncio
    async def test_verifies_item_successfully(
        self,
        handler: VerifyItemHandler,
        valid_command: VerifyItemCommand,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Should verify item and publish event."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item

        # Act
        result = await handler.handle(valid_command)

        # Assert
        assert result == sample_stolen_item.report_id
        assert sample_stolen_item.is_verified
        assert sample_stolen_item.police_reference is not None
        mock_repository.save.assert_called_once_with(sample_stolen_item)
        mock_event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publishes_item_verified_event(
        self,
        handler: VerifyItemHandler,
        valid_command: VerifyItemCommand,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
        mock_event_bus: AsyncMock,
    ) -> None:
        """Should publish ItemVerified event with correct data."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item

        # Act
        await handler.handle(valid_command)

        # Assert
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, ItemVerified)
        assert event.report_id == sample_stolen_item.report_id
        assert event.police_reference == "CR/2024/123456"
        assert event.verified_by.value == "+27821234567"

    @pytest.mark.asyncio
    async def test_raises_error_when_item_not_found(
        self,
        handler: VerifyItemHandler,
        valid_command: VerifyItemCommand,
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
        handler: VerifyItemHandler,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise UnauthorizedVerificationError when verifier is not reporter."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item
        command = VerifyItemCommand(
            report_id=str(sample_stolen_item.report_id),
            police_reference="CR/2024/123456",
            verified_by_phone="+27829999999",  # Different phone
        )

        # Act & Assert
        with pytest.raises(UnauthorizedVerificationError, match="Only the reporter"):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_raises_error_when_item_not_active(
        self,
        handler: VerifyItemHandler,
        valid_command: VerifyItemCommand,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise ItemNotActiveError when item is not active."""
        # Arrange
        item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
            status=ItemStatus.RECOVERED,  # Not active
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_repository.find_by_id.return_value = item

        # Act & Assert
        with pytest.raises(ItemNotActiveError, match="active reports"):
            await handler.handle(valid_command)

    @pytest.mark.asyncio
    async def test_raises_error_when_already_verified(
        self,
        handler: VerifyItemHandler,
        valid_command: VerifyItemCommand,
        verification_service: VerificationService,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise ItemAlreadyVerifiedError when item is already verified."""
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
        # Verify it first
        verification_service.verify(item, PoliceReference("CR/2024/999999"))
        mock_repository.find_by_id.return_value = item

        # Act & Assert
        with pytest.raises(ItemAlreadyVerifiedError, match="already verified"):
            await handler.handle(valid_command)

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_police_reference(
        self,
        handler: VerifyItemHandler,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise InvalidPoliceReferenceError on invalid format."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item
        command = VerifyItemCommand(
            report_id=str(sample_stolen_item.report_id),
            police_reference="INVALID",  # Invalid format
            verified_by_phone="+27821234567",
        )

        # Act & Assert
        with pytest.raises(InvalidPoliceReferenceError):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_phone_number(
        self,
        handler: VerifyItemHandler,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise error on invalid phone number format."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item
        command = VerifyItemCommand(
            report_id=str(sample_stolen_item.report_id),
            police_reference="CR/2024/123456",
            verified_by_phone="invalid",  # Invalid phone
        )

        # Act & Assert
        with pytest.raises(ValueError):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_raises_error_on_invalid_uuid(
        self,
        handler: VerifyItemHandler,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise ValueError on invalid UUID format."""
        # Arrange
        command = VerifyItemCommand(
            report_id="not-a-uuid",
            police_reference="CR/2024/123456",
            verified_by_phone="+27821234567",
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid UUID"):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_updates_item_timestamp(
        self,
        handler: VerifyItemHandler,
        valid_command: VerifyItemCommand,
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
    async def test_verification_is_idempotent_raises_error(
        self,
        handler: VerifyItemHandler,
        valid_command: VerifyItemCommand,
        sample_stolen_item: StolenItem,
        mock_repository: AsyncMock,
    ) -> None:
        """Should raise error on duplicate verification attempt."""
        # Arrange
        mock_repository.find_by_id.return_value = sample_stolen_item

        # Act - first verification
        await handler.handle(valid_command)

        # Act & Assert - second verification should fail
        with pytest.raises(ItemAlreadyVerifiedError):
            await handler.handle(valid_command)
