"""Report Stolen Item command and handler."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.entities.stolen_item import StolenItem
from src.domain.events.domain_events import ItemReported
from src.domain.exceptions.domain_exceptions import (
    InvalidItemCategoryError,
    InvalidLocationError,
    InvalidPhoneNumberError,
)
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber
from src.infrastructure.messaging.event_bus import InMemoryEventBus


@dataclass
class ReportStolenItemCommand:
    """Command to report a stolen item.

    This DTO carries all data needed to report a stolen item from the
    presentation layer to the application layer.
    """

    reporter_phone: str
    item_type: str
    description: str
    stolen_date: datetime
    latitude: float
    longitude: float
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    color: str | None = None


class ReportStolenItemHandler:
    """Handler for reporting stolen items.

    This use case orchestrates the domain logic to create a new stolen
    item report, persist it, and publish the ItemReported event.
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

    async def handle(self, command: ReportStolenItemCommand) -> UUID:
        """Handle the report stolen item command.

        Args:
            command: Command containing report details

        Returns:
            UUID of the created report

        Raises:
            InvalidPhoneNumberError: If phone number is invalid
            InvalidItemCategoryError: If item category is invalid
            InvalidLocationError: If location coordinates are invalid
            ValueError: If description or stolen date validation fails
        """
        # Create domain value objects (validation happens here)
        reporter_phone = self._create_phone_number(command.reporter_phone)
        item_type = self._create_item_category(command.item_type)
        location = self._create_location(command.latitude, command.longitude)

        # Create stolen item entity
        stolen_item = StolenItem.create(
            reporter_phone=reporter_phone,
            item_type=item_type,
            description=command.description,
            stolen_date=command.stolen_date,
            location=location,
            brand=command.brand,
            model=command.model,
            serial_number=command.serial_number,
            color=command.color,
        )

        # Persist the item
        await self._repository.save(stolen_item)

        # Publish domain event
        event = ItemReported(
            report_id=stolen_item.report_id,
            reporter_phone=reporter_phone,
            item_type=item_type,
            description=command.description,
            stolen_date=command.stolen_date,
            location=location,
            brand=command.brand,
            model=command.model,
            serial_number=command.serial_number,
            color=command.color,
        )
        await self._event_bus.publish(event)

        return stolen_item.report_id

    @staticmethod
    def _create_phone_number(phone: str) -> PhoneNumber:
        """Create and validate phone number.

        Args:
            phone: Phone number string

        Returns:
            PhoneNumber value object

        Raises:
            InvalidPhoneNumberError: If phone number is invalid
        """
        try:
            return PhoneNumber(phone)
        except ValueError as e:
            raise InvalidPhoneNumberError(str(e)) from e

    @staticmethod
    def _create_item_category(category: str) -> ItemCategory:
        """Create and validate item category.

        Args:
            category: Category string

        Returns:
            ItemCategory enum value

        Raises:
            InvalidItemCategoryError: If category is invalid
        """
        try:
            return ItemCategory.from_user_input(category)
        except ValueError as e:
            raise InvalidItemCategoryError(str(e)) from e

    @staticmethod
    def _create_location(latitude: float, longitude: float) -> Location:
        """Create and validate location.

        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate

        Returns:
            Location value object

        Raises:
            InvalidLocationError: If coordinates are invalid
        """
        try:
            return Location(latitude=latitude, longitude=longitude)
        except ValueError as e:
            raise InvalidLocationError(str(e)) from e
