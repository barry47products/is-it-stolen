"""Integration tests for Check If Stolen query with real dependencies."""

from datetime import UTC, datetime

import pytest

from src.application.queries.check_if_stolen import (
    CheckIfStolenHandler,
    CheckIfStolenQuery,
)
from src.domain.entities.stolen_item import ItemStatus
from src.domain.services.matching_service import ItemMatchingService
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models import StolenItemModel
from src.infrastructure.persistence.repositories.postgres_stolen_item_repository import (
    PostgresStolenItemRepository,
)


class TestCheckIfStolenIntegration:
    """Integration tests with real database and matching service."""

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
    def matching_service(self) -> ItemMatchingService:
        """Create real matching service."""
        return ItemMatchingService(threshold=0.7)

    @pytest.fixture
    def handler(
        self,
        repository: PostgresStolenItemRepository,
        matching_service: ItemMatchingService,
    ) -> CheckIfStolenHandler:
        """Create handler with real dependencies."""
        return CheckIfStolenHandler(
            repository=repository, matching_service=matching_service
        )

    @pytest.mark.asyncio
    async def test_finds_matches_from_real_database(
        self, handler: CheckIfStolenHandler, repository: PostgresStolenItemRepository
    ) -> None:
        """Should query real database and return matches."""
        # Arrange - create stolen item in database
        from uuid import uuid4

        from src.domain.entities.stolen_item import StolenItem

        item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike with black seat",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            brand="Giant",
            model="Talon 2",
            serial_number="GT123456",
        )
        await repository.save(item)

        query = CheckIfStolenQuery(
            description="Red mountain bike with black seat",
            brand="Giant",
            model="Talon 2",
            serial_number="GT123456",
            category="bicycle",
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_count == 1
        assert len(result.matches) == 1
        assert result.matches[0].item.report_id == item.report_id

    @pytest.mark.asyncio
    async def test_scores_matches_with_real_matching_service(
        self, handler: CheckIfStolenHandler, repository: PostgresStolenItemRepository
    ) -> None:
        """Should calculate real similarity scores."""
        # Arrange
        from uuid import uuid4

        from src.domain.entities.stolen_item import StolenItem

        perfect_match = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            brand="Giant",
            serial_number="GT123456",
        )
        await repository.save(perfect_match)

        query = CheckIfStolenQuery(
            description="Red mountain bike",
            brand="Giant",
            serial_number="GT123456",
            category="bicycle",
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert len(result.matches) == 1
        assert result.matches[0].similarity_score == 1.0  # Perfect match
        assert result.matches[0].match_reason == "Exact serial number match"

    @pytest.mark.asyncio
    async def test_location_based_search(
        self, handler: CheckIfStolenHandler, repository: PostgresStolenItemRepository
    ) -> None:
        """Should find items within location radius."""
        # Arrange
        from uuid import uuid4

        from src.domain.entities.stolen_item import StolenItem

        nearby_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),  # Cape Town
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            brand="Giant",
        )
        await repository.save(nearby_item)

        query = CheckIfStolenQuery(
            description="Red mountain bike",
            brand="Giant",
            latitude=-33.93,  # Very close to Cape Town
            longitude=18.42,
            radius_km=5.0,
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_count >= 1

    @pytest.mark.asyncio
    async def test_pagination_with_real_data(
        self, handler: CheckIfStolenHandler, repository: PostgresStolenItemRepository
    ) -> None:
        """Should apply pagination to real results."""
        # Arrange - create multiple similar items
        from uuid import uuid4

        from src.domain.entities.stolen_item import StolenItem

        for i in range(5):
            item = StolenItem(
                report_id=uuid4(),
                reporter_phone=PhoneNumber("+27821234567"),
                item_type=ItemCategory.BICYCLE,
                description=f"Red mountain bike number {i}",
                stolen_date=datetime.now(UTC),
                location=Location(latitude=-33.9249, longitude=18.4241),
                status=ItemStatus.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                brand="Giant",
            )
            await repository.save(item)

        query = CheckIfStolenQuery(
            description="Red mountain bike",
            brand="Giant",
            category="bicycle",
            limit=2,
            offset=1,
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert len(result.matches) == 2  # Limited to 2
        assert result.total_count >= 2  # Total available
