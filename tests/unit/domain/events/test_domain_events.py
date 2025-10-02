"""Unit tests for domain events."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from src.domain.events.domain_events import (
    ItemRecovered,
    ItemReported,
    ItemVerified,
)
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber


class TestItemReported:
    """Test suite for ItemReported event."""

    def test_creates_item_reported_event(self) -> None:
        """Should create ItemReported event with all required fields."""
        # Arrange
        report_id = uuid4()
        reporter_phone = PhoneNumber("+447911123456")
        item_type = ItemCategory.BICYCLE
        description = "Red mountain bike"
        stolen_date = datetime.now(UTC)
        location = Location(latitude=51.5074, longitude=-0.1278)

        # Act
        event = ItemReported(
            report_id=report_id,
            reporter_phone=reporter_phone,
            item_type=item_type,
            description=description,
            stolen_date=stolen_date,
            location=location,
        )

        # Assert
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.occurred_at, datetime)
        assert event.report_id == report_id
        assert event.reporter_phone == reporter_phone
        assert event.item_type == item_type
        assert event.description == description
        assert event.stolen_date == stolen_date
        assert event.location == location

    def test_item_reported_event_is_immutable(self) -> None:
        """Should not allow modification of event fields."""
        # Arrange
        report_id = uuid4()
        reporter_phone = PhoneNumber("+447911123456")
        item_type = ItemCategory.BICYCLE
        description = "Red mountain bike"
        stolen_date = datetime.now(UTC)
        location = Location(latitude=51.5074, longitude=-0.1278)

        event = ItemReported(
            report_id=report_id,
            reporter_phone=reporter_phone,
            item_type=item_type,
            description=description,
            stolen_date=stolen_date,
            location=location,
        )

        # Act & Assert
        with pytest.raises(AttributeError):
            event.report_id = uuid4()  # type: ignore[misc]

    def test_item_reported_includes_optional_fields(self) -> None:
        """Should include optional fields when provided."""
        # Arrange
        report_id = uuid4()
        reporter_phone = PhoneNumber("+447911123456")
        item_type = ItemCategory.PHONE
        description = "iPhone 15 Pro"
        stolen_date = datetime.now(UTC)
        location = Location(latitude=51.5074, longitude=-0.1278)

        # Act
        event = ItemReported(
            report_id=report_id,
            reporter_phone=reporter_phone,
            item_type=item_type,
            description=description,
            stolen_date=stolen_date,
            location=location,
            brand="Apple",
            model="iPhone 15 Pro",
            serial_number="ABC123",
            color="Black",
        )

        # Assert
        assert event.brand == "Apple"
        assert event.model == "iPhone 15 Pro"
        assert event.serial_number == "ABC123"
        assert event.color == "Black"


class TestItemVerified:
    """Test suite for ItemVerified event."""

    def test_creates_item_verified_event(self) -> None:
        """Should create ItemVerified event with police reference."""
        # Arrange
        report_id = uuid4()
        police_reference = "POL123456789"
        verified_by = PhoneNumber("+447911123456")

        # Act
        event = ItemVerified(
            report_id=report_id,
            police_reference=police_reference,
            verified_by=verified_by,
        )

        # Assert
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.occurred_at, datetime)
        assert event.report_id == report_id
        assert event.police_reference == police_reference
        assert event.verified_by == verified_by

    def test_item_verified_event_is_immutable(self) -> None:
        """Should not allow modification of event fields."""
        # Arrange
        report_id = uuid4()
        police_reference = "POL123456789"
        verified_by = PhoneNumber("+447911123456")

        event = ItemVerified(
            report_id=report_id,
            police_reference=police_reference,
            verified_by=verified_by,
        )

        # Act & Assert
        with pytest.raises(AttributeError):
            event.police_reference = "NEW123"  # type: ignore[misc]


class TestItemRecovered:
    """Test suite for ItemRecovered event."""

    def test_creates_item_recovered_event(self) -> None:
        """Should create ItemRecovered event with recovery details."""
        # Arrange
        report_id = uuid4()
        recovered_by = PhoneNumber("+447911123456")
        recovery_location = Location(latitude=51.5074, longitude=-0.1278)
        recovery_notes = "Found in garage"

        # Act
        event = ItemRecovered(
            report_id=report_id,
            recovered_by=recovered_by,
            recovery_location=recovery_location,
            recovery_notes=recovery_notes,
        )

        # Assert
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.occurred_at, datetime)
        assert event.report_id == report_id
        assert event.recovered_by == recovered_by
        assert event.recovery_location == recovery_location
        assert event.recovery_notes == recovery_notes

    def test_item_recovered_event_is_immutable(self) -> None:
        """Should not allow modification of event fields."""
        # Arrange
        report_id = uuid4()
        recovered_by = PhoneNumber("+447911123456")
        recovery_location = Location(latitude=51.5074, longitude=-0.1278)

        event = ItemRecovered(
            report_id=report_id,
            recovered_by=recovered_by,
            recovery_location=recovery_location,
        )

        # Act & Assert
        with pytest.raises(AttributeError):
            event.recovery_notes = "New notes"  # type: ignore[misc]

    def test_item_recovered_with_optional_notes(self) -> None:
        """Should allow optional recovery notes."""
        # Arrange
        report_id = uuid4()
        recovered_by = PhoneNumber("+447911123456")
        recovery_location = Location(latitude=51.5074, longitude=-0.1278)

        # Act
        event = ItemRecovered(
            report_id=report_id,
            recovered_by=recovered_by,
            recovery_location=recovery_location,
        )

        # Assert
        assert event.recovery_notes is None
