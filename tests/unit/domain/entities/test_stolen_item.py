"""Unit tests for StolenItem entity."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber


class TestStolenItem:
    """Test suite for StolenItem entity."""

    def test_creates_stolen_item_with_valid_data(self) -> None:
        """Should create StolenItem with all valid required fields."""
        # Arrange
        reporter_phone = PhoneNumber("+447911123456")
        item_type = ItemCategory.BICYCLE
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC) - timedelta(days=1)

        # Act
        item = StolenItem.create(
            reporter_phone=reporter_phone,
            item_type=item_type,
            description="Red mountain bike",
            stolen_date=stolen_date,
            location=location,
        )

        # Assert
        assert isinstance(item.report_id, UUID)
        assert item.reporter_phone == reporter_phone
        assert item.item_type == item_type
        assert item.description == "Red mountain bike"
        assert item.stolen_date == stolen_date
        assert item.location == location
        assert item.status == ItemStatus.ACTIVE
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)

    def test_creates_stolen_item_with_optional_fields(self) -> None:
        """Should create StolenItem with optional fields."""
        # Arrange
        reporter_phone = PhoneNumber("+447911123456")
        item_type = ItemCategory.PHONE
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC) - timedelta(days=1)

        # Act
        item = StolenItem.create(
            reporter_phone=reporter_phone,
            item_type=item_type,
            description="iPhone 15 Pro",
            stolen_date=stolen_date,
            location=location,
            brand="Apple",
            model="iPhone 15 Pro",
            serial_number="ABC123456",
            color="Black",
        )

        # Assert
        assert item.brand == "Apple"
        assert item.model == "iPhone 15 Pro"
        assert item.serial_number == "ABC123456"
        assert item.color == "Black"

    def test_rejects_stolen_date_in_future(self) -> None:
        """Should raise ValueError when stolen_date is in the future."""
        # Arrange
        reporter_phone = PhoneNumber("+447911123456")
        item_type = ItemCategory.BICYCLE
        location = Location(latitude=51.5074, longitude=-0.1278)
        future_date = datetime.now(UTC) + timedelta(days=1)

        # Act & Assert
        with pytest.raises(ValueError, match="Stolen date cannot be in the future"):
            StolenItem.create(
                reporter_phone=reporter_phone,
                item_type=item_type,
                description="Red mountain bike",
                stolen_date=future_date,
                location=location,
            )

    def test_rejects_empty_description(self) -> None:
        """Should raise ValueError when description is empty."""
        # Arrange
        reporter_phone = PhoneNumber("+447911123456")
        item_type = ItemCategory.BICYCLE
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC) - timedelta(days=1)

        # Act & Assert
        with pytest.raises(ValueError, match="Description cannot be empty"):
            StolenItem.create(
                reporter_phone=reporter_phone,
                item_type=item_type,
                description="",
                stolen_date=stolen_date,
                location=location,
            )

    def test_rejects_description_too_short(self) -> None:
        """Should raise ValueError when description is too short."""
        # Arrange
        reporter_phone = PhoneNumber("+447911123456")
        item_type = ItemCategory.BICYCLE
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC) - timedelta(days=1)

        # Act & Assert
        with pytest.raises(
            ValueError, match="Description must be at least 10 characters"
        ):
            StolenItem.create(
                reporter_phone=reporter_phone,
                item_type=item_type,
                description="Too short",
                stolen_date=stolen_date,
                location=location,
            )

    def test_marks_item_as_recovered(self) -> None:
        """Should mark item as recovered."""
        # Arrange
        reporter_phone = PhoneNumber("+447911123456")
        item_type = ItemCategory.BICYCLE
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC) - timedelta(days=1)

        item = StolenItem.create(
            reporter_phone=reporter_phone,
            item_type=item_type,
            description="Red mountain bike",
            stolen_date=stolen_date,
            location=location,
        )

        # Act
        item.mark_as_recovered()

        # Assert
        assert item.status == ItemStatus.RECOVERED

    def test_cannot_recover_already_recovered_item(self) -> None:
        """Should raise ValueError when trying to recover already recovered item."""
        # Arrange
        reporter_phone = PhoneNumber("+447911123456")
        item_type = ItemCategory.BICYCLE
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC) - timedelta(days=1)

        item = StolenItem.create(
            reporter_phone=reporter_phone,
            item_type=item_type,
            description="Red mountain bike",
            stolen_date=stolen_date,
            location=location,
        )
        item.mark_as_recovered()

        # Act & Assert
        with pytest.raises(ValueError, match="Item is already recovered"):
            item.mark_as_recovered()

    def test_updates_timestamp_when_marked_as_recovered(self) -> None:
        """Should update updated_at timestamp when item marked as recovered."""
        # Arrange
        reporter_phone = PhoneNumber("+447911123456")
        item_type = ItemCategory.BICYCLE
        location = Location(latitude=51.5074, longitude=-0.1278)
        stolen_date = datetime.now(UTC) - timedelta(days=1)

        item = StolenItem.create(
            reporter_phone=reporter_phone,
            item_type=item_type,
            description="Red mountain bike",
            stolen_date=stolen_date,
            location=location,
        )
        original_updated_at = item.updated_at

        # Act
        item.mark_as_recovered()

        # Assert
        assert item.updated_at > original_updated_at
