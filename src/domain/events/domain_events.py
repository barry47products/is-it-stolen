"""Domain events for stolen item lifecycle."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber


def _generate_event_id() -> UUID:
    """Generate a new event ID."""
    return uuid4()


def _generate_timestamp() -> datetime:
    """Generate current UTC timestamp."""
    return datetime.now(UTC)


@dataclass(frozen=True)
class ItemReported:
    """Event raised when a stolen item is reported.

    This event captures all details about a newly reported stolen item.
    """

    report_id: UUID
    reporter_phone: PhoneNumber
    item_type: ItemCategory
    description: str
    stolen_date: datetime
    location: Location
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    color: str | None = None
    event_id: UUID = field(default_factory=_generate_event_id)
    occurred_at: datetime = field(default_factory=_generate_timestamp)


@dataclass(frozen=True)
class ItemVerified:
    """Event raised when a stolen item report is verified by police.

    This event indicates official police verification of the theft report.
    """

    report_id: UUID
    police_reference: str
    verified_by: PhoneNumber
    event_id: UUID = field(default_factory=_generate_event_id)
    occurred_at: datetime = field(default_factory=_generate_timestamp)


@dataclass(frozen=True)
class ItemRecovered:
    """Event raised when a stolen item is recovered.

    This event captures recovery details including location and notes.
    """

    report_id: UUID
    recovered_by: PhoneNumber
    recovery_location: Location
    recovery_notes: str | None = None
    event_id: UUID = field(default_factory=_generate_event_id)
    occurred_at: datetime = field(default_factory=_generate_timestamp)
