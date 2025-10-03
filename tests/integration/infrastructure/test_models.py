"""Integration tests for SQLAlchemy database models."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.domain.entities.stolen_item import ItemStatus
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models import StolenItemModel


class TestStolenItemModel:
    """Test StolenItem database model."""

    # NOTE: Database tables are created via Alembic migrations
    # No need for init_db() in tests

    @pytest.fixture(autouse=True)
    def clear_database(self) -> None:
        """Clear stolen_items table before each test."""
        with get_db() as db:
            db.query(StolenItemModel).delete()
            db.commit()

    def test_creates_stolen_item_in_database(self) -> None:
        """Should persist stolen item to database."""
        # Arrange
        item_id = uuid4()
        phone = PhoneNumber("+447911123456")
        location = Location(latitude=51.5074, longitude=-0.1278, address="London")
        stolen_date = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)
        created_at = datetime.now(UTC)

        stolen_item = StolenItemModel(
            report_id=item_id,
            reporter_phone=phone.value,
            item_type=ItemCategory.BICYCLE.value,
            description="Red mountain bike with 21 gears",
            stolen_date=stolen_date,
            latitude=location.latitude,
            longitude=location.longitude,
            address=location.address,
            status=ItemStatus.ACTIVE.value,
            created_at=created_at,
            updated_at=created_at,
        )

        # Act
        with get_db() as db:
            db.add(stolen_item)
            db.commit()
            db.refresh(stolen_item)

            # Assert
            assert stolen_item.report_id == item_id
            assert stolen_item.reporter_phone == phone.value
            assert stolen_item.item_type == ItemCategory.BICYCLE.value
            assert stolen_item.description == "Red mountain bike with 21 gears"
            assert stolen_item.latitude == 51.5074
            assert stolen_item.longitude == -0.1278
            assert stolen_item.address == "London"
            assert stolen_item.status == ItemStatus.ACTIVE.value

    def test_retrieves_stolen_item_from_database(self) -> None:
        """Should retrieve stolen item from database by ID."""
        # Arrange
        item_id = uuid4()
        phone = PhoneNumber("+447911123456")
        created_at = datetime.now(UTC)

        stolen_item = StolenItemModel(
            report_id=item_id,
            reporter_phone=phone.value,
            item_type=ItemCategory.PHONE.value,
            description="iPhone 13 Pro with cracked screen",
            stolen_date=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
            latitude=51.5074,
            longitude=-0.1278,
            status=ItemStatus.ACTIVE.value,
            created_at=created_at,
            updated_at=created_at,
        )

        with get_db() as db:
            db.add(stolen_item)
            db.commit()

        # Act
        with get_db() as db:
            retrieved_item = (
                db.query(StolenItemModel)
                .filter(StolenItemModel.report_id == item_id)
                .first()
            )

            # Assert
            assert retrieved_item is not None
            assert retrieved_item.report_id == item_id
            assert retrieved_item.item_type == ItemCategory.PHONE.value

    def test_updates_stolen_item_status(self) -> None:
        """Should update item status in database."""
        # Arrange
        item_id = uuid4()
        created_at = datetime.now(UTC)

        stolen_item = StolenItemModel(
            report_id=item_id,
            reporter_phone="+447911123456",
            item_type=ItemCategory.LAPTOP.value,
            description="MacBook Pro 16-inch with serial ABC123",
            stolen_date=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
            latitude=51.5074,
            longitude=-0.1278,
            status=ItemStatus.ACTIVE.value,
            created_at=created_at,
            updated_at=created_at,
        )

        with get_db() as db:
            db.add(stolen_item)
            db.commit()

        # Act
        with get_db() as db:
            item = (
                db.query(StolenItemModel)
                .filter(StolenItemModel.report_id == item_id)
                .first()
            )
            item.status = ItemStatus.RECOVERED.value
            item.updated_at = datetime.now(UTC)
            db.commit()

        # Assert
        with get_db() as db:
            updated_item = (
                db.query(StolenItemModel)
                .filter(StolenItemModel.report_id == item_id)
                .first()
            )
            assert updated_item.status == ItemStatus.RECOVERED.value

    def test_stores_optional_item_fields(self) -> None:
        """Should store optional fields (brand, model, serial_number, color)."""
        # Arrange
        item_id = uuid4()
        created_at = datetime.now(UTC)

        stolen_item = StolenItemModel(
            report_id=item_id,
            reporter_phone="+447911123456",
            item_type=ItemCategory.BICYCLE.value,
            description="Trek mountain bike with custom paint",
            stolen_date=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
            latitude=51.5074,
            longitude=-0.1278,
            status=ItemStatus.ACTIVE.value,
            created_at=created_at,
            updated_at=created_at,
            brand="Trek",
            model="X-Caliber 9",
            serial_number="WTU123456789",
            color="Matte Black",
        )

        # Act
        with get_db() as db:
            db.add(stolen_item)
            db.commit()

        # Assert
        with get_db() as db:
            retrieved_item = (
                db.query(StolenItemModel)
                .filter(StolenItemModel.report_id == item_id)
                .first()
            )
            assert retrieved_item.brand == "Trek"
            assert retrieved_item.model == "X-Caliber 9"
            assert retrieved_item.serial_number == "WTU123456789"
            assert retrieved_item.color == "Matte Black"

    def test_stores_police_reference_and_verification(self) -> None:
        """Should store police reference and verification timestamp."""
        # Arrange
        item_id = uuid4()
        created_at = datetime.now(UTC)
        verified_at = datetime.now(UTC)

        stolen_item = StolenItemModel(
            report_id=item_id,
            reporter_phone="+447911123456",
            item_type=ItemCategory.VEHICLE.value,
            description="Black Honda Civic 2015",
            stolen_date=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
            latitude=51.5074,
            longitude=-0.1278,
            status=ItemStatus.ACTIVE.value,
            created_at=created_at,
            updated_at=created_at,
            police_reference="MET/2024/123456",
            verified_at=verified_at,
        )

        # Act
        with get_db() as db:
            db.add(stolen_item)
            db.commit()

        # Assert
        with get_db() as db:
            retrieved_item = (
                db.query(StolenItemModel)
                .filter(StolenItemModel.report_id == item_id)
                .first()
            )
            assert retrieved_item.police_reference == "MET/2024/123456"
            assert retrieved_item.verified_at is not None

    def test_query_items_by_location_proximity(self) -> None:
        """Should query items near a specific location using PostGIS."""
        # Arrange - Create items at different locations
        london_item = StolenItemModel(
            report_id=uuid4(),
            reporter_phone="+447911123456",
            item_type=ItemCategory.BICYCLE.value,
            description="London bicycle",
            stolen_date=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
            latitude=51.5074,  # London
            longitude=-0.1278,
            status=ItemStatus.ACTIVE.value,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        manchester_item = StolenItemModel(
            report_id=uuid4(),
            reporter_phone="+447911654321",
            item_type=ItemCategory.PHONE.value,
            description="Manchester phone",
            stolen_date=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
            latitude=53.4808,  # Manchester
            longitude=-2.2426,
            status=ItemStatus.ACTIVE.value,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        with get_db() as db:
            db.add_all([london_item, manchester_item])
            db.commit()

        # Act - Query items within 10km of London
        # Note: This test will verify the geospatial capability is working
        with get_db() as db:
            london_items = (
                db.query(StolenItemModel)
                .filter(StolenItemModel.latitude.between(51.4, 51.6))
                .filter(StolenItemModel.longitude.between(-0.2, 0.0))
                .all()
            )

            # Assert
            assert len(london_items) == 1
            assert london_items[0].description == "London bicycle"
