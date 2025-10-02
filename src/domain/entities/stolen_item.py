"""StolenItem entity - aggregate root for stolen item reports."""

from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber

MIN_DESCRIPTION_LENGTH = 10


class ItemStatus(str, Enum):
    """Status of a stolen item report."""

    ACTIVE = "active"
    RECOVERED = "recovered"
    EXPIRED = "expired"


class StolenItem:
    """Entity representing a stolen item report.

    This is the aggregate root for stolen item reports. It enforces
    business rules and maintains data integrity.
    """

    def __init__(
        self,
        report_id: UUID,
        reporter_phone: PhoneNumber,
        item_type: ItemCategory,
        description: str,
        stolen_date: datetime,
        location: Location,
        status: ItemStatus,
        created_at: datetime,
        updated_at: datetime,
        brand: str | None = None,
        model: str | None = None,
        serial_number: str | None = None,
        color: str | None = None,
    ) -> None:
        """Initialize StolenItem entity.

        Note: Use create() factory method instead of direct instantiation.
        """
        self.report_id = report_id
        self.reporter_phone = reporter_phone
        self.item_type = item_type
        self.description = description
        self.stolen_date = stolen_date
        self.location = location
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at
        self.brand = brand
        self.model = model
        self.serial_number = serial_number
        self.color = color

    @classmethod
    def create(
        cls,
        reporter_phone: PhoneNumber,
        item_type: ItemCategory,
        description: str,
        stolen_date: datetime,
        location: Location,
        brand: str | None = None,
        model: str | None = None,
        serial_number: str | None = None,
        color: str | None = None,
    ) -> "StolenItem":
        """Create a new StolenItem with validation.

        Args:
            reporter_phone: Phone number of person reporting the theft
            item_type: Category of the stolen item
            description: Detailed description of the item
            stolen_date: Date and time when item was stolen
            location: Location where item was stolen
            brand: Optional brand name
            model: Optional model name
            serial_number: Optional serial number
            color: Optional color

        Returns:
            New StolenItem instance

        Raises:
            ValueError: If validation fails
        """
        cls._validate_description(description)
        cls._validate_stolen_date(stolen_date)

        now = datetime.now(UTC)

        return cls(
            report_id=uuid4(),
            reporter_phone=reporter_phone,
            item_type=item_type,
            description=description,
            stolen_date=stolen_date,
            location=location,
            status=ItemStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            brand=brand,
            model=model,
            serial_number=serial_number,
            color=color,
        )

    @staticmethod
    def _validate_description(description: str) -> None:
        """Validate item description.

        Args:
            description: Item description to validate

        Raises:
            ValueError: If description is invalid
        """
        if not description or not description.strip():
            raise ValueError("Description cannot be empty")

        if len(description.strip()) < MIN_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description must be at least {MIN_DESCRIPTION_LENGTH} characters"
            )

    @staticmethod
    def _validate_stolen_date(stolen_date: datetime) -> None:
        """Validate stolen date is not in the future.

        Args:
            stolen_date: Date to validate

        Raises:
            ValueError: If date is in the future
        """
        now = datetime.now(UTC)
        if stolen_date > now:
            raise ValueError("Stolen date cannot be in the future")

    def mark_as_recovered(self) -> None:
        """Mark the item as recovered.

        Raises:
            ValueError: If item is already recovered
        """
        if self.status == ItemStatus.RECOVERED:
            raise ValueError("Item is already recovered")

        self.status = ItemStatus.RECOVERED
        self.updated_at = datetime.now(UTC)
