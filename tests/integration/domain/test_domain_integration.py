"""Integration tests for domain layer components working together."""

from datetime import UTC, datetime

import pytest

from src.domain.entities.stolen_item import StolenItem
from src.domain.exceptions.domain_exceptions import (
    ItemAlreadyVerifiedError,
    ItemNotActiveError,
)
from src.domain.services.matching_service import ItemMatchingService
from src.domain.services.verification_service import VerificationService
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.domain.value_objects.police_reference import PoliceReference


class TestItemReportingWorkflow:
    """Test complete item reporting workflow."""

    def test_creates_and_reports_stolen_bicycle(self) -> None:
        """Should create complete stolen bicycle report with all details."""
        # Arrange
        reporter = PhoneNumber("+447911123456")
        location = Location(51.5074, -0.1278, "London, UK")
        stolen_date = datetime(2024, 10, 1, 14, 30, tzinfo=UTC)

        # Act
        item = StolenItem.create(
            reporter_phone=reporter,
            item_type=ItemCategory.BICYCLE,
            description="Red Trek mountain bike, 21 gears, scratched left handlebar",
            stolen_date=stolen_date,
            location=location,
            brand="Trek",
            model="X-Caliber 8",
            serial_number="WTU123456789",
            color="Red",
        )

        # Assert
        assert item.report_id is not None
        assert item.reporter_phone == reporter
        assert item.item_type == ItemCategory.BICYCLE
        assert item.location == location
        assert item.brand == "Trek"
        assert item.model == "X-Caliber 8"
        assert item.serial_number == "WTU123456789"
        assert item.color == "Red"
        assert item.is_verified is False
        assert item.police_reference is None

    def test_creates_phone_report_with_minimal_details(self) -> None:
        """Should create report with only required fields."""
        # Arrange
        reporter = PhoneNumber("+447911123456")
        location = Location(51.5074, -0.1278)

        # Act
        item = StolenItem.create(
            reporter_phone=reporter,
            item_type=ItemCategory.PHONE,
            description="Black iPhone 13 Pro",
            stolen_date=datetime.now(UTC),
            location=location,
        )

        # Assert
        assert item.report_id is not None
        assert item.brand is None
        assert item.model is None
        assert item.serial_number is None
        assert item.color is None


class TestItemMatchingWorkflow:
    """Test item matching with realistic scenarios."""

    def test_matches_identical_items_by_serial_number(self) -> None:
        """Should match items with same serial number."""
        # Arrange
        service = ItemMatchingService()
        location1 = Location(51.5074, -0.1278)
        location2 = Location(51.5100, -0.1300)

        reported_item = StolenItem.create(
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=location1,
            serial_number="WTU123456789",
        )

        found_item = StolenItem.create(
            reporter_phone=PhoneNumber("+447922987654"),
            item_type=ItemCategory.BICYCLE,
            description="Red bike found on street",
            stolen_date=datetime.now(UTC),
            location=location2,
            serial_number="WTU123456789",
        )

        # Act
        similarity = service.calculate_similarity(reported_item, found_item)

        # Assert
        assert similarity >= 0.8
        assert service.is_match(reported_item, found_item)

    def test_does_not_match_completely_different_items(self) -> None:
        """Should not match items with different characteristics."""
        # Arrange
        service = ItemMatchingService()
        location = Location(51.5074, -0.1278)

        bicycle = StolenItem.create(
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Red Trek mountain bike",
            stolen_date=datetime.now(UTC),
            location=location,
            serial_number="WTU123456789",
        )

        laptop = StolenItem.create(
            reporter_phone=PhoneNumber("+447922987654"),
            item_type=ItemCategory.LAPTOP,
            description="MacBook Pro 16 inch",
            stolen_date=datetime.now(UTC),
            location=location,
            serial_number="ABC987654321",
        )

        # Act
        similarity = service.calculate_similarity(bicycle, laptop)

        # Assert
        assert similarity < 0.3
        assert not service.is_match(bicycle, laptop)

    def test_matches_similar_descriptions_without_serial(self) -> None:
        """Should match items with similar descriptions when no serial."""
        # Arrange
        service = ItemMatchingService()
        location = Location(51.5074, -0.1278)

        item1 = StolenItem.create(
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Blue Giant mountain bike with black saddle",
            stolen_date=datetime.now(UTC),
            location=location,
        )

        item2 = StolenItem.create(
            reporter_phone=PhoneNumber("+447922987654"),
            item_type=ItemCategory.BICYCLE,
            description="Giant blue mountain bike black seat",
            stolen_date=datetime.now(UTC),
            location=location,
        )

        # Act
        similarity = service.calculate_similarity(item1, item2)

        # Assert
        assert similarity > 0.5


class TestVerificationWorkflow:
    """Test complete verification workflow."""

    def test_verifies_active_report_successfully(self) -> None:
        """Should verify active report with police reference."""
        # Arrange
        item = StolenItem.create(
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(51.5074, -0.1278),
        )
        police_ref = PoliceReference("CR/2024/123456")
        service = VerificationService()

        # Act
        service.verify(item, police_ref)

        # Assert
        assert item.is_verified is True
        assert item.police_reference == police_ref
        assert item.verified_at is not None

    def test_prevents_verification_of_recovered_item(self) -> None:
        """Should not allow verification of recovered items."""
        # Arrange
        item = StolenItem.create(
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(51.5074, -0.1278),
        )
        item.mark_as_recovered()
        police_ref = PoliceReference("CR/2024/123456")
        service = VerificationService()

        # Act & Assert
        with pytest.raises(ItemNotActiveError):
            service.verify(item, police_ref)

    def test_prevents_duplicate_verification(self) -> None:
        """Should not allow re-verification of verified items."""
        # Arrange
        item = StolenItem.create(
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(51.5074, -0.1278),
        )
        police_ref1 = PoliceReference("CR/2024/123456")
        police_ref2 = PoliceReference("CR/2024/999999")
        service = VerificationService()
        service.verify(item, police_ref1)

        # Act & Assert
        with pytest.raises(ItemAlreadyVerifiedError):
            service.verify(item, police_ref2)


class TestRecoveryWorkflow:
    """Test item recovery workflow."""

    def test_marks_item_as_recovered(self) -> None:
        """Should mark active item as recovered."""
        # Arrange
        item = StolenItem.create(
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(51.5074, -0.1278),
        )
        original_updated = item.updated_at

        # Act
        item.mark_as_recovered()

        # Assert
        assert item.status.value == "recovered"
        assert item.updated_at > original_updated

    def test_prevents_duplicate_recovery(self) -> None:
        """Should prevent marking already recovered item as recovered again."""
        # Arrange
        item = StolenItem.create(
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(51.5074, -0.1278),
        )
        item.mark_as_recovered()

        # Act & Assert
        with pytest.raises(ValueError, match="Item is already recovered"):
            item.mark_as_recovered()

    def test_can_verify_before_recovery(self) -> None:
        """Should allow verification before marking as recovered."""
        # Arrange
        item = StolenItem.create(
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(51.5074, -0.1278),
        )
        police_ref = PoliceReference("CR/2024/123456")
        service = VerificationService()

        # Act
        service.verify(item, police_ref)
        item.mark_as_recovered()

        # Assert
        assert item.is_verified is True
        assert item.status.value == "recovered"


class TestCompleteItemLifecycle:
    """Test complete lifecycle of a stolen item report."""

    def test_full_lifecycle_report_verify_recover(self) -> None:
        """Should handle complete lifecycle: report -> verify -> recover."""
        # Arrange
        reporter = PhoneNumber("+447911123456")
        location = Location(51.5074, -0.1278, "London, UK")
        police_ref = PoliceReference("CR/2024/123456")
        verification_service = VerificationService()

        # Act 1: Report stolen item
        item = StolenItem.create(
            reporter_phone=reporter,
            item_type=ItemCategory.BICYCLE,
            description="Red Trek mountain bike with scratched handlebar",
            stolen_date=datetime(2024, 10, 1, 14, 30, tzinfo=UTC),
            location=location,
            brand="Trek",
            serial_number="WTU123456789",
        )

        # Assert initial state
        assert item.is_verified is False
        assert item.status.value == "active"

        # Act 2: Verify with police
        verification_service.verify(item, police_ref)

        # Assert verified state
        assert item.is_verified is True
        assert item.police_reference == police_ref

        # Act 3: Mark as recovered
        item.mark_as_recovered()

        # Assert final state
        assert item.status.value == "recovered"
        assert item.is_verified is True
        assert item.police_reference == police_ref

    def test_full_lifecycle_with_matching(self) -> None:
        """Should handle report, matching, verification, and recovery."""
        # Arrange
        location = Location(51.5074, -0.1278)
        matching_service = ItemMatchingService()
        verification_service = VerificationService()
        police_ref = PoliceReference("CR/2024/123456")

        # Act 1: Report stolen item
        reported = StolenItem.create(
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Red Trek mountain bike",
            stolen_date=datetime.now(UTC),
            location=location,
            serial_number="WTU123456789",
        )

        # Act 2: Someone finds and reports similar item
        found = StolenItem.create(
            reporter_phone=PhoneNumber("+447922987654"),
            item_type=ItemCategory.BICYCLE,
            description="Red Trek bike found",
            stolen_date=datetime.now(UTC),
            location=location,
            serial_number="WTU123456789",
        )

        # Act 3: Match the items
        is_match = matching_service.is_match(reported, found)

        # Assert match
        assert is_match is True

        # Act 4: Verify both reports
        verification_service.verify(reported, police_ref)
        verification_service.verify(found, police_ref)

        # Act 5: Mark as recovered
        reported.mark_as_recovered()
        found.mark_as_recovered()

        # Assert final state
        assert reported.is_verified is True
        assert found.is_verified is True
        assert reported.status.value == "recovered"
        assert found.status.value == "recovered"
