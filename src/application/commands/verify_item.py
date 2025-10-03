"""Verify Item command and handler."""

from dataclasses import dataclass
from uuid import UUID

from src.domain.events.domain_events import ItemVerified
from src.domain.exceptions.domain_exceptions import (
    InvalidPoliceReferenceError,
    ItemNotFoundError,
    UnauthorizedVerificationError,
)
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.services.verification_service import VerificationService
from src.domain.value_objects.phone_number import PhoneNumber
from src.domain.value_objects.police_reference import PoliceReference
from src.infrastructure.messaging.event_bus import InMemoryEventBus


@dataclass
class VerifyItemCommand:
    """Command to verify a stolen item report with police reference.

    This DTO carries all data needed to verify a report from the
    presentation layer to the application layer.
    """

    report_id: str
    police_reference: str
    verified_by_phone: str


class VerifyItemHandler:
    """Handler for verifying stolen item reports.

    This use case orchestrates the domain logic to verify an existing
    stolen item report with a police reference, persist it, and publish
    the ItemVerified event.
    """

    def __init__(
        self,
        repository: IStolenItemRepository,
        event_bus: InMemoryEventBus,
        verification_service: VerificationService,
    ) -> None:
        """Initialize handler with dependencies.

        Args:
            repository: Repository for persisting stolen items
            event_bus: Event bus for publishing domain events
            verification_service: Service for verification business rules
        """
        self._repository = repository
        self._event_bus = event_bus
        self._verification_service = verification_service

    async def handle(self, command: VerifyItemCommand) -> UUID:
        """Handle the verify item command.

        Args:
            command: Command containing verification details

        Returns:
            UUID of the verified report

        Raises:
            ValueError: If UUID or phone number format is invalid
            InvalidPoliceReferenceError: If police reference is invalid
            ItemNotFoundError: If item does not exist
            UnauthorizedVerificationError: If verifier is not the reporter
            ItemNotActiveError: If item is not in active status
            ItemAlreadyVerifiedError: If item is already verified
        """
        # Parse and validate inputs
        report_id = self._parse_uuid(command.report_id)
        police_ref = self._create_police_reference(command.police_reference)
        verified_by = PhoneNumber(command.verified_by_phone)

        # Retrieve item
        item = await self._repository.find_by_id(report_id)
        if item is None:
            raise ItemNotFoundError(f"Item with ID {report_id} not found")

        # Authorization check - only reporter can verify
        if item.reporter_phone.value != verified_by.value:
            raise UnauthorizedVerificationError("Only the reporter can verify the item")

        # Apply verification business rules
        self._verification_service.verify(item, police_ref)

        # Persist the updated item
        await self._repository.save(item)

        # Publish domain event
        event = ItemVerified(
            report_id=item.report_id,
            police_reference=police_ref.value,
            verified_by=verified_by,
        )
        await self._event_bus.publish(event)

        return item.report_id

    @staticmethod
    def _parse_uuid(uuid_str: str) -> UUID:
        """Parse UUID string.

        Args:
            uuid_str: UUID as string

        Returns:
            UUID object

        Raises:
            ValueError: If UUID format is invalid
        """
        try:
            return UUID(uuid_str)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid UUID format: {uuid_str}") from e

    @staticmethod
    def _create_police_reference(reference: str) -> PoliceReference:
        """Create and validate police reference.

        Args:
            reference: Police reference string

        Returns:
            PoliceReference value object

        Raises:
            InvalidPoliceReferenceError: If reference format is invalid
        """
        try:
            return PoliceReference(reference)
        except ValueError as e:
            raise InvalidPoliceReferenceError(str(e)) from e
