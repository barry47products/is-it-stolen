"""Tests for verification business rules service."""

from datetime import UTC, datetime

import pytest

from src.domain.entities.stolen_item import StolenItem
from src.domain.exceptions.domain_exceptions import (
    ItemAlreadyVerifiedError,
    ItemNotActiveError,
)
from src.domain.services.verification_service import VerificationService
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.domain.value_objects.police_reference import PoliceReference


class TestVerificationService:
    """Test verification business rules."""

    def test_verifies_active_report_with_valid_reference(self) -> None:
        """Should verify active report with valid police reference."""
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

    def test_rejects_verification_of_recovered_item(self) -> None:
        """Should reject verification of recovered item."""
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
        with pytest.raises(
            ItemNotActiveError, match="Only active reports can be verified"
        ):
            service.verify(item, police_ref)

    def test_rejects_verification_of_already_verified_item(self) -> None:
        """Should reject re-verification of already verified item."""
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
        with pytest.raises(
            ItemAlreadyVerifiedError, match="Report is already verified"
        ):
            service.verify(item, police_ref2)

    def test_verification_includes_timestamp(self) -> None:
        """Should include timestamp when verifying."""
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
        before = datetime.now(UTC)

        # Act
        service.verify(item, police_ref)

        # Assert
        after = datetime.now(UTC)
        assert item.verified_at is not None
        assert before <= item.verified_at <= after

    def test_verification_updates_item_timestamp(self) -> None:
        """Should update item's updated_at timestamp."""
        # Arrange
        item = StolenItem.create(
            reporter_phone=PhoneNumber("+447911123456"),
            item_type=ItemCategory.BICYCLE,
            description="Red mountain bike",
            stolen_date=datetime.now(UTC),
            location=Location(51.5074, -0.1278),
        )
        original_updated_at = item.updated_at
        police_ref = PoliceReference("CR/2024/123456")
        service = VerificationService()

        # Act
        service.verify(item, police_ref)

        # Assert
        assert item.updated_at > original_updated_at

    def test_cannot_unverify_report(self) -> None:
        """Should not allow unverifying a report."""
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
        service.verify(item, police_ref)

        # Act & Assert - Attempting to set is_verified to False should fail
        assert item.is_verified is True
        with pytest.raises(AttributeError):
            item.is_verified = False  # type: ignore
