"""List User Items query and handler."""

from dataclasses import dataclass, field

from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.exceptions.domain_exceptions import InvalidPhoneNumberError
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.value_objects.phone_number import PhoneNumber

DEFAULT_LIMIT = 50
DEFAULT_OFFSET = 0


@dataclass
class ListUserItemsQuery:
    """Query to list all stolen items for a user.

    This DTO carries user identification and filtering parameters from the
    presentation layer to the application layer.
    """

    reporter_phone: str
    status: str | None = None
    limit: int = DEFAULT_LIMIT
    offset: int = DEFAULT_OFFSET


@dataclass
class ListUserItemsResult:
    """Result of listing user's stolen items.

    Contains all items for the user with metadata about the total count.
    """

    items: list[StolenItem] = field(default_factory=list)
    total_count: int = 0


class ListUserItemsHandler:
    """Handler for listing a user's stolen item reports.

    This query use case retrieves all reports submitted by a specific user,
    with optional filtering by status and pagination support.
    """

    def __init__(
        self,
        repository: IStolenItemRepository,
    ) -> None:
        """Initialize handler with dependencies.

        Args:
            repository: Repository for querying stolen items
        """
        self._repository = repository

    async def handle(self, query: ListUserItemsQuery) -> ListUserItemsResult:
        """Handle the list user items query.

        Args:
            query: Query containing user phone and filter parameters

        Returns:
            Results with user's items sorted by most recent first

        Raises:
            InvalidPhoneNumberError: If phone number format is invalid
        """
        # Create and validate phone number
        phone = self._create_phone_number(query.reporter_phone)

        # Query repository for all user's items
        items = await self._repository.find_by_reporter(phone)

        # Apply status filter if specified
        if query.status:
            items = self._filter_by_status(items, query.status)

        # Sort by most recent first
        sorted_items = sorted(items, key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        total_count = len(sorted_items)
        paginated_items = sorted_items[query.offset : query.offset + query.limit]

        return ListUserItemsResult(items=paginated_items, total_count=total_count)

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
    def _filter_by_status(items: list[StolenItem], status: str) -> list[StolenItem]:
        """Filter items by status.

        Args:
            items: List of stolen items
            status: Status filter (active, recovered)

        Returns:
            Filtered list of items
        """
        status_upper = status.upper()
        if status_upper == "ACTIVE":
            return [item for item in items if item.status == ItemStatus.ACTIVE]
        elif status_upper == "RECOVERED":
            return [item for item in items if item.status == ItemStatus.RECOVERED]
        else:
            return items
