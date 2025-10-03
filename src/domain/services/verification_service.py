"""Verification business rules service."""

from datetime import UTC, datetime

from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.exceptions.domain_exceptions import (
    ItemAlreadyVerifiedError,
    ItemNotActiveError,
)
from src.domain.value_objects.police_reference import PoliceReference


class VerificationService:
    """Service for handling item verification business rules."""

    def verify(self, item: StolenItem, police_ref: PoliceReference) -> None:
        """Verify a stolen item report with police reference.

        Args:
            item: The stolen item to verify
            police_ref: Police reference number for verification

        Raises:
            ItemNotActiveError: If item is not in active status
            ItemAlreadyVerifiedError: If item is already verified
        """
        self._validate_can_verify(item)

        now = datetime.now(UTC)
        object.__setattr__(item, "_police_reference", police_ref)
        object.__setattr__(item, "_verified_at", now)
        item.updated_at = now

    def _validate_can_verify(self, item: StolenItem) -> None:
        """Validate that item can be verified.

        Args:
            item: The stolen item to validate

        Raises:
            ItemNotActiveError: If item is not active
            ItemAlreadyVerifiedError: If item is already verified
        """
        if item.status != ItemStatus.ACTIVE:
            raise ItemNotActiveError("Only active reports can be verified")

        if item.is_verified:
            raise ItemAlreadyVerifiedError("Report is already verified")
