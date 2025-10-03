"""Integration tests for VerifyItem command with real database."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.application.commands.verify_item import VerifyItemCommand, VerifyItemHandler
from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.exceptions.domain_exceptions import (
    ItemAlreadyVerifiedError,
    ItemNotActiveError,
    ItemNotFoundError,
    UnauthorizedVerificationError,
)
from src.domain.services.verification_service import VerificationService
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.infrastructure.messaging.event_bus import InMemoryEventBus
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models import StolenItemModel
from src.infrastructure.persistence.repositories.postgres_stolen_item_repository import (
    PostgresStolenItemRepository,
)


class TestVerifyItemIntegration:
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
    async def test_verifies_item_with_real_database(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should verify item and persist to real database."""
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

        handler = VerifyItemHandler(
            repository=repository,
            event_bus=event_bus,
            verification_service=VerificationService(),
        )

        command = VerifyItemCommand(
            report_id=str(item.report_id),
            police_reference="CR/2024/123456",
            verified_by_phone="+27821234567",
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result == item.report_id

        # Verify persisted in database
        retrieved = await repository.find_by_id(item.report_id)
        assert retrieved is not None
        assert retrieved.is_verified
        assert retrieved.police_reference is not None
        assert retrieved.police_reference.value == "CR/2024/123456"
        assert retrieved.verified_at is not None

    @pytest.mark.asyncio
    async def test_prevents_verification_by_non_reporter(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should prevent verification by someone other than reporter."""
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

        handler = VerifyItemHandler(
            repository=repository,
            event_bus=event_bus,
            verification_service=VerificationService(),
        )

        command = VerifyItemCommand(
            report_id=str(item.report_id),
            police_reference="CR/2024/123456",
            verified_by_phone="+27829999999",  # Different phone
        )

        # Act & Assert
        with pytest.raises(UnauthorizedVerificationError):
            await handler.handle(command)

        # Verify not persisted
        retrieved = await repository.find_by_id(item.report_id)
        assert retrieved is not None
        assert not retrieved.is_verified

    @pytest.mark.asyncio
    async def test_prevents_double_verification(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should prevent verifying an already verified item."""
        # Arrange - create and verify an item
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

        handler = VerifyItemHandler(
            repository=repository,
            event_bus=event_bus,
            verification_service=VerificationService(),
        )

        command = VerifyItemCommand(
            report_id=str(item.report_id),
            police_reference="CR/2024/123456",
            verified_by_phone="+27821234567",
        )

        # First verification
        await handler.handle(command)

        # Act & Assert - second verification should fail
        with pytest.raises(ItemAlreadyVerifiedError):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_prevents_verification_of_non_active_item(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should prevent verifying a non-active item."""
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
        await repository.save(item)

        handler = VerifyItemHandler(
            repository=repository,
            event_bus=event_bus,
            verification_service=VerificationService(),
        )

        command = VerifyItemCommand(
            report_id=str(item.report_id),
            police_reference="CR/2024/123456",
            verified_by_phone="+27821234567",
        )

        # Act & Assert
        with pytest.raises(ItemNotActiveError):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_raises_error_for_nonexistent_item(
        self,
        repository: PostgresStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Should raise error when item doesn't exist."""
        # Arrange
        handler = VerifyItemHandler(
            repository=repository,
            event_bus=event_bus,
            verification_service=VerificationService(),
        )

        command = VerifyItemCommand(
            report_id=str(uuid4()),  # Non-existent ID
            police_reference="CR/2024/123456",
            verified_by_phone="+27821234567",
        )

        # Act & Assert
        with pytest.raises(ItemNotFoundError):
            await handler.handle(command)
