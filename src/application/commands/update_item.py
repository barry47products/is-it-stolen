"""Update Item command and handler."""

from dataclasses import dataclass
from uuid import UUID

from src.domain.events.domain_events import ItemUpdated
from src.domain.exceptions.domain_exceptions import (
    ItemNotFoundError,
    UnauthorizedUpdateError,
)
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.value_objects.phone_number import PhoneNumber
from src.infrastructure.messaging.event_bus import InMemoryEventBus


@dataclass
class UpdateItemCommand:
    """Command to update a stolen item report.

    This DTO carries all data needed to update a report from the
    presentation layer to the application layer. All fields except
    report_id and updated_by_phone are optional for partial updates.
    """

    report_id: str
    updated_by_phone: str
    description: str | None = None
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    color: str | None = None


class UpdateItemHandler:
    """Handler for updating stolen item reports.

    This use case orchestrates the domain logic to update an existing
    stolen item report, persist it, and publish the ItemUpdated event.
    Only certain mutable fields can be updated (not core identity fields).
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

    async def handle(self, command: UpdateItemCommand) -> UUID:
        """Handle the update item command.

        Args:
            command: Command containing update details

        Returns:
            UUID of the updated report

        Raises:
            ValueError: If UUID or phone number format is invalid
            ItemNotFoundError: If item does not exist
            UnauthorizedUpdateError: If updater is not the reporter
        """
        # Parse and validate inputs
        report_id = self._parse_uuid(command.report_id)
        updated_by = PhoneNumber(command.updated_by_phone)

        # Retrieve item
        item = await self._repository.find_by_id(report_id)
        if item is None:
            raise ItemNotFoundError(f"Item with ID {report_id} not found")

        # Authorization check - only reporter can update
        if item.reporter_phone.value != updated_by.value:
            raise UnauthorizedUpdateError("Only the reporter can update the item")

        # Track what fields are being updated
        updated_fields: dict[str, str | None] = {}

        # Update fields if provided
        if command.description is not None:
            updated_fields["description"] = command.description

        if command.brand is not None:
            updated_fields["brand"] = command.brand

        if command.model is not None:
            updated_fields["model"] = command.model

        if command.serial_number is not None:
            updated_fields["serial_number"] = command.serial_number

        if command.color is not None:
            updated_fields["color"] = command.color

        # Apply updates to entity
        item.update_details(
            description=command.description,
            brand=command.brand,
            model=command.model,
            serial_number=command.serial_number,
            color=command.color,
        )

        # Persist the updated item
        await self._repository.save(item)

        # Publish domain event
        event = ItemUpdated(
            report_id=item.report_id,
            updated_by=updated_by,
            updated_fields=updated_fields,
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
