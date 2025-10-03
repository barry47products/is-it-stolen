"""Integration tests for Find Nearby Items query with real PostGIS."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.application.queries.find_nearby_items import (
    FindNearbyItemsHandler,
    FindNearbyItemsQuery,
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


class TestFindNearbyItemsIntegration:
    """Integration tests with real PostgreSQL database and PostGIS."""

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
    def handler(
        self, repository: PostgresStolenItemRepository
    ) -> FindNearbyItemsHandler:
        """Create handler with real repository."""
        return FindNearbyItemsHandler(repository=repository)

    @pytest.mark.asyncio
    async def test_finds_items_within_radius_using_postgis(
        self, handler: FindNearbyItemsHandler, repository: PostgresStolenItemRepository
    ) -> None:
        """Should find items within radius using PostGIS distance calculation."""
        # Arrange - create item in Cape Town
        cape_town_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),  # Cape Town
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        await repository.save(cape_town_item)

        # Search near Cape Town (within 5km)
        query = FindNearbyItemsQuery(
            latitude=-33.93,  # Very close to Cape Town
            longitude=18.42,
            radius_km=5.0,
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert result.total_count == 1
        assert len(result.items) == 1
        assert result.items[0].item.report_id == cape_town_item.report_id

    @pytest.mark.asyncio
    async def test_excludes_items_outside_radius(
        self, handler: FindNearbyItemsHandler, repository: PostgresStolenItemRepository
    ) -> None:
        """Should exclude items outside search radius."""
        # Arrange - create items in different cities
        cape_town_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Cape Town bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.9249, longitude=18.4241),  # Cape Town
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        await repository.save(cape_town_item)

        johannesburg_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.LAPTOP,
            description="Johannesburg laptop",
            stolen_date=datetime.now(UTC),
            location=Location(
                latitude=-26.2041, longitude=28.0473
            ),  # Johannesburg (~1400km away)
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        await repository.save(johannesburg_item)

        # Search near Cape Town with 10km radius
        query = FindNearbyItemsQuery(
            latitude=-33.9249,
            longitude=18.4241,
            radius_km=10.0,
        )

        # Act
        result = await handler.handle(query)

        # Assert - only Cape Town item should be found
        assert result.total_count == 1
        assert result.items[0].item.report_id == cape_town_item.report_id

    @pytest.mark.asyncio
    async def test_sorts_items_by_distance_ascending(
        self, handler: FindNearbyItemsHandler, repository: PostgresStolenItemRepository
    ) -> None:
        """Should sort items by distance (nearest first)."""
        # Arrange - create items at varying distances

        # Near item (~1km away)
        near_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Near bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.93, longitude=18.43),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        await repository.save(near_item)

        # Far item (~5km away)
        far_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.LAPTOP,
            description="Far laptop",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.88, longitude=18.48),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        await repository.save(far_item)

        # Search with radius that includes both
        query = FindNearbyItemsQuery(
            latitude=-33.9249,
            longitude=18.4241,
            radius_km=10.0,
        )

        # Act
        result = await handler.handle(query)

        # Assert - nearest first
        assert len(result.items) == 2
        assert result.items[0].distance_km < result.items[1].distance_km
        assert result.items[0].item.report_id == near_item.report_id
        assert result.items[1].item.report_id == far_item.report_id

    @pytest.mark.asyncio
    async def test_filters_by_category(
        self, handler: FindNearbyItemsHandler, repository: PostgresStolenItemRepository
    ) -> None:
        """Should filter by category when specified."""
        # Arrange - create items of different categories
        bike = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.BICYCLE,
            description="Bike",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.93, longitude=18.42),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        await repository.save(bike)

        laptop = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+27821234567"),
            item_type=ItemCategory.LAPTOP,
            description="Laptop",
            stolen_date=datetime.now(UTC),
            location=Location(latitude=-33.93, longitude=18.42),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        await repository.save(laptop)

        # Search for bicycles only
        query = FindNearbyItemsQuery(
            latitude=-33.93,
            longitude=18.42,
            radius_km=5.0,
            category="bicycle",
        )

        # Act
        result = await handler.handle(query)

        # Assert - only bicycle returned
        assert result.total_count == 1
        assert result.items[0].item.item_type == ItemCategory.BICYCLE

    @pytest.mark.asyncio
    async def test_pagination_with_real_data(
        self, handler: FindNearbyItemsHandler, repository: PostgresStolenItemRepository
    ) -> None:
        """Should apply pagination to real results."""
        # Arrange - create multiple items
        for i in range(5):
            item = StolenItem(
                report_id=uuid4(),
                reporter_phone=PhoneNumber("+27821234567"),
                item_type=ItemCategory.BICYCLE,
                description=f"Bike {i}",
                stolen_date=datetime.now(UTC),
                location=Location(latitude=-33.93 + (i * 0.001), longitude=18.42),
                status=ItemStatus.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            await repository.save(item)

        # Search with pagination
        query = FindNearbyItemsQuery(
            latitude=-33.93,
            longitude=18.42,
            radius_km=10.0,
            limit=2,
            offset=1,
        )

        # Act
        result = await handler.handle(query)

        # Assert
        assert len(result.items) == 2  # Limited to 2
        assert result.total_count == 5  # Total available
