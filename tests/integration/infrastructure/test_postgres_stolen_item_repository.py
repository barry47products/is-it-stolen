"""Integration tests for PostgresStolenItemRepository."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.exceptions.domain_exceptions import RepositoryError
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models import StolenItemModel
from src.infrastructure.persistence.repositories.postgres_stolen_item_repository import (
    PostgresStolenItemRepository,
)


class TestPostgresStolenItemRepository:
    """Test PostgreSQL repository implementation."""

    @pytest.fixture(autouse=True)
    def clear_database(self) -> None:
        """Clear stolen_items table before each test."""
        with get_db() as db:
            db.query(StolenItemModel).delete()
            db.commit()

    @pytest.fixture
    def repository(self) -> PostgresStolenItemRepository:
        """Create repository instance."""
        return PostgresStolenItemRepository()

    @pytest.fixture
    def sample_item(self) -> StolenItem:
        """Create a sample stolen item."""
        return StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            brand="Trek",
            model="X-Caliber 8",
            serial_number="WTU123456789",
            color="Red",
            stolen_date=datetime(2025, 10, 1, tzinfo=UTC),
            location=Location(latitude=51.5074, longitude=-0.1278, address="London"),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    async def test_saves_stolen_item_to_database(
        self, repository: PostgresStolenItemRepository, sample_item: StolenItem
    ) -> None:
        """Should persist stolen item to database."""
        # Act
        await repository.save(sample_item)

        # Assert
        with get_db() as db:
            model = (
                db.query(StolenItemModel)
                .filter_by(report_id=sample_item.report_id)
                .first()
            )
            assert model is not None
            assert model.reporter_phone == sample_item.reporter_phone.value
            assert model.item_type == sample_item.item_type.value
            assert model.description == sample_item.description
            assert model.brand == sample_item.brand
            assert model.serial_number == sample_item.serial_number

    async def test_finds_item_by_id(
        self, repository: PostgresStolenItemRepository, sample_item: StolenItem
    ) -> None:
        """Should find stolen item by ID."""
        # Arrange
        await repository.save(sample_item)

        # Act
        found_item = await repository.find_by_id(sample_item.report_id)

        # Assert
        assert found_item is not None
        assert found_item.report_id == sample_item.report_id
        assert found_item.item_type == sample_item.item_type
        assert found_item.description == sample_item.description

    async def test_returns_none_when_item_not_found(
        self, repository: PostgresStolenItemRepository
    ) -> None:
        """Should return None when item doesn't exist."""
        # Act
        found_item = await repository.find_by_id(uuid4())

        # Assert
        assert found_item is None

    async def test_finds_items_by_reporter_phone(
        self, repository: PostgresStolenItemRepository
    ) -> None:
        """Should find all items reported by a phone number."""
        # Arrange
        phone = PhoneNumber("+447911123456")
        item1 = StolenItem(
            report_id=uuid4(),
            reporter_phone=phone,
            item_type=ItemCategory.BICYCLE,
            description="Item 1",
            stolen_date=datetime(2025, 10, 1, tzinfo=UTC),
            location=Location(51.5074, -0.1278),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        item2 = StolenItem(
            report_id=uuid4(),
            reporter_phone=phone,
            item_type=ItemCategory.LAPTOP,
            description="Item 2",
            stolen_date=datetime(2025, 10, 2, tzinfo=UTC),
            location=Location(51.5074, -0.1278),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        other_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+447911789012"),
            item_type=ItemCategory.PHONE,
            description="Other item",
            stolen_date=datetime(2025, 10, 3, tzinfo=UTC),
            location=Location(51.5074, -0.1278),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await repository.save(item1)
        await repository.save(item2)
        await repository.save(other_item)

        # Act
        items = await repository.find_by_reporter(phone)

        # Assert
        assert len(items) == 2
        assert all(item.reporter_phone == phone for item in items)

    async def test_finds_nearby_items_within_radius(
        self, repository: PostgresStolenItemRepository
    ) -> None:
        """Should find items within specified radius using PostGIS."""
        # Arrange - Create items at different locations
        london_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="London bike",
            stolen_date=datetime(2025, 10, 1, tzinfo=UTC),
            location=Location(latitude=51.5074, longitude=-0.1278),  # London
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        nearby_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+447911789012"),
            item_type=ItemCategory.LAPTOP,
            description="Nearby laptop",
            stolen_date=datetime(2025, 10, 2, tzinfo=UTC),
            location=Location(
                latitude=51.5155, longitude=-0.1410
            ),  # ~1.5km from London
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        far_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+447922555000"),
            item_type=ItemCategory.PHONE,
            description="Birmingham phone",
            stolen_date=datetime(2025, 10, 3, tzinfo=UTC),
            location=Location(latitude=52.4862, longitude=-1.8904),  # Birmingham ~180km
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await repository.save(london_item)
        await repository.save(nearby_item)
        await repository.save(far_item)

        # Act - Search within 5km of London
        search_location = Location(latitude=51.5074, longitude=-0.1278)
        nearby_items = await repository.find_nearby(search_location, radius_km=5.0)

        # Assert
        assert len(nearby_items) == 2
        item_ids = {item.report_id for item in nearby_items}
        assert london_item.report_id in item_ids
        assert nearby_item.report_id in item_ids
        assert far_item.report_id not in item_ids

    async def test_finds_nearby_items_filtered_by_category(
        self, repository: PostgresStolenItemRepository
    ) -> None:
        """Should filter nearby items by category."""
        # Arrange
        bike1 = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Bike 1",
            stolen_date=datetime(2025, 10, 1, tzinfo=UTC),
            location=Location(51.5074, -0.1278),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        laptop = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+447911789012"),
            item_type=ItemCategory.LAPTOP,
            description="Laptop",
            stolen_date=datetime(2025, 10, 2, tzinfo=UTC),
            location=Location(51.5074, -0.1278),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await repository.save(bike1)
        await repository.save(laptop)

        # Act
        search_location = Location(51.5074, -0.1278)
        bikes = await repository.find_nearby(
            search_location, radius_km=5.0, category=ItemCategory.BICYCLE
        )

        # Assert
        assert len(bikes) == 1
        assert bikes[0].item_type == ItemCategory.BICYCLE

    async def test_finds_items_by_category(
        self, repository: PostgresStolenItemRepository
    ) -> None:
        """Should find items by category."""
        # Arrange
        bike = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Bike",
            stolen_date=datetime(2025, 10, 1, tzinfo=UTC),
            location=Location(51.5074, -0.1278),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        laptop = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+447911789012"),
            item_type=ItemCategory.LAPTOP,
            description="Laptop",
            stolen_date=datetime(2025, 10, 2, tzinfo=UTC),
            location=Location(51.5074, -0.1278),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await repository.save(bike)
        await repository.save(laptop)

        # Act
        bikes = await repository.find_by_category(ItemCategory.BICYCLE)

        # Assert
        assert len(bikes) == 1
        assert bikes[0].item_type == ItemCategory.BICYCLE

    async def test_finds_items_by_category_and_status(
        self, repository: PostgresStolenItemRepository
    ) -> None:
        """Should filter items by status."""
        # Arrange
        active_bike = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Active bike",
            stolen_date=datetime(2025, 10, 1, tzinfo=UTC),
            location=Location(51.5074, -0.1278),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        recovered_bike = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+447911789012"),
            item_type=ItemCategory.BICYCLE,
            description="Recovered bike",
            stolen_date=datetime(2025, 10, 2, tzinfo=UTC),
            location=Location(51.5074, -0.1278),
            status=ItemStatus.RECOVERED,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        await repository.save(active_bike)
        await repository.save(recovered_bike)

        # Act
        active_bikes = await repository.find_by_category(
            ItemCategory.BICYCLE, status=ItemStatus.ACTIVE
        )

        # Assert
        assert len(active_bikes) == 1
        assert active_bikes[0].status == ItemStatus.ACTIVE

    async def test_limits_results_when_specified(
        self, repository: PostgresStolenItemRepository
    ) -> None:
        """Should limit number of results."""
        # Arrange - Create 5 bikes
        for i in range(5):
            bike = StolenItem(
                report_id=uuid4(),
                reporter_phone=PhoneNumber("+447911123456"),
                item_type=ItemCategory.BICYCLE,
                description=f"Bike {i}",
                stolen_date=datetime(2025, 10, 1, tzinfo=UTC),
                location=Location(51.5074, -0.1278),
                status=ItemStatus.ACTIVE,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            await repository.save(bike)

        # Act
        bikes = await repository.find_by_category(ItemCategory.BICYCLE, limit=3)

        # Assert
        assert len(bikes) == 3

    async def test_deletes_item_from_database(
        self, repository: PostgresStolenItemRepository, sample_item: StolenItem
    ) -> None:
        """Should delete item from database."""
        # Arrange
        await repository.save(sample_item)

        # Act
        await repository.delete(sample_item.report_id)

        # Assert
        with get_db() as db:
            model = (
                db.query(StolenItemModel)
                .filter_by(report_id=sample_item.report_id)
                .first()
            )
            assert model is None

    async def test_raises_repository_error_on_database_failure(
        self, repository: PostgresStolenItemRepository
    ) -> None:
        """Should raise RepositoryError when database operations fail."""
        # Arrange - Create item with invalid data that will cause DB error
        invalid_item = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Test",
            stolen_date=datetime(2025, 10, 1, tzinfo=UTC),
            location=Location(51.5074, -0.1278),
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        def failing_db() -> None:
            # Force a constraint violation or connection error
            raise Exception("Database connection failed")

        repository._get_db = failing_db  # type: ignore[method-assign]

        # Act & Assert
        with pytest.raises(RepositoryError) as exc_info:
            await repository.save(invalid_item)

        assert exc_info.value.code == "REPOSITORY_ERROR"
        assert exc_info.value.cause is not None

    async def test_saves_item_without_location(
        self, repository: PostgresStolenItemRepository
    ) -> None:
        """Should save item when location is None."""
        # Arrange - Create item without location
        item_without_location = StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Bike stolen somewhere",
            stolen_date=datetime(2025, 10, 1, tzinfo=UTC),
            location=None,  # type: ignore[arg-type]  # Testing defensive null handling
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Act
        await repository.save(item_without_location)

        # Assert
        with get_db() as db:
            model = (
                db.query(StolenItemModel)
                .filter_by(report_id=item_without_location.report_id)
                .first()
            )
            assert model is not None
            assert model.location_point is None
            assert model.latitude == 0.0
            assert model.longitude == 0.0
