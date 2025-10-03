"""Delete Item command and handler."""

from dataclasses import dataclass
from uuid import UUID

from src.domain.events.domain_events import ItemDeleted
from src.domain.exceptions.domain_exceptions import (
    ItemAlreadyDeletedException,
    ItemNotFoundError,
    UnauthorizedDeletionError,
)
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.value_objects.phone_number import PhoneNumber
from src.infrastructure.messaging.event_bus import InMemoryEventBus


@dataclass
class DeleteItemCommand:
    """Command to delete a stolen item report.

    This DTO carries all data needed to delete a report from the
    presentation layer to the application layer.
    """

    report_id: str
    deleted_by_phone: str
    reason: str | None = None


class DeleteItemHandler:
    """Handler for deleting stolen item reports.

    This use case orchestrates the domain logic to soft delete an existing
    stolen item report, persist it, and publish the ItemDeleted event.
    """

    def __init__(
        self,
        repository: IStolenItemRepository,
        event_bus: InMemoryEventBus,
    ) -> None:
        """Initialize handler with dependencies.

        Args:
            repository: Repository for persisting stolen items
            event_bus: Event bus for publishing domain events
        """
        self._repository = repository
        self._event_bus = event_bus

    async def handle(self, command: DeleteItemCommand) -> UUID:
        """Handle the delete item command.

        Args:
            command: Command containing deletion details

        Returns:
            UUID of the deleted report

        Raises:
            ValueError: If UUID or phone number format is invalid
            ItemNotFoundError: If item does not exist
            UnauthorizedDeletionError: If deleter is not the reporter
            ItemAlreadyDeletedException: If item is already deleted
        """
        # Parse and validate inputs
        report_id = self._parse_uuid(command.report_id)
        deleted_by = PhoneNumber(command.deleted_by_phone)

        # Retrieve item
        item = await self._repository.find_by_id(report_id)
        if item is None:
            raise ItemNotFoundError(f"Item with ID {report_id} not found")

        # Authorization check - only reporter can delete
        if item.reporter_phone.value != deleted_by.value:
            raise UnauthorizedDeletionError("Only the reporter can delete the item")

        # Check if already deleted
        try:
            item.mark_as_deleted()
        except ValueError as e:
            raise ItemAlreadyDeletedException(str(e)) from e

        # Persist the updated item
        await self._repository.save(item)

        # Publish domain event
        event = ItemDeleted(
            report_id=item.report_id,
            deleted_by=deleted_by,
            reason=command.reason,
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
