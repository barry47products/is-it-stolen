"""Repository interface for StolenItem aggregate root."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location
from src.domain.value_objects.phone_number import PhoneNumber

MAX_SEARCH_RADIUS_KM = 50


class IStolenItemRepository(ABC):
    """Repository interface for StolenItem persistence.

    This interface defines the contract for persisting and retrieving
    StolenItem aggregates. Implementations are in the infrastructure layer.
    """

    @abstractmethod
    async def save(self, item: StolenItem) -> None:
        """Persist a stolen item.

        Args:
            item: StolenItem entity to save

        Raises:
            RepositoryError: If save operation fails
        """
        ...

    @abstractmethod
    async def find_by_id(self, item_id: UUID) -> StolenItem | None:
        """Find stolen item by ID.

        Args:
            item_id: Unique identifier for the item

        Returns:
            StolenItem if found, None otherwise

        Raises:
            RepositoryError: If query fails
        """
        ...

    @abstractmethod
    async def find_by_reporter(self, reporter_phone: PhoneNumber) -> list[StolenItem]:
        """Find all items reported by a phone number.

        Args:
            reporter_phone: Phone number of the reporter

        Returns:
            List of StolenItem entities (empty if none found)

        Raises:
            RepositoryError: If query fails
        """
        ...

    @abstractmethod
    async def find_nearby(
        self,
        location: Location,
        radius_km: float,
        category: ItemCategory | None = None,
    ) -> list[StolenItem]:
        """Find items within radius of a location.

        Args:
            location: Center point for search
            radius_km: Search radius in kilometers (max 50km)
            category: Optional filter by item category

        Returns:
            List of StolenItem entities within radius

        Raises:
            ValueError: If radius_km > MAX_SEARCH_RADIUS_KM
            RepositoryError: If query fails
        """
        ...

    @abstractmethod
    async def find_by_category(
        self,
        category: ItemCategory,
        status: ItemStatus = ItemStatus.ACTIVE,
        limit: int = 100,
    ) -> list[StolenItem]:
        """Find items by category and status.

        Args:
            category: Item category to search for
            status: Item status filter (default: ACTIVE)
            limit: Maximum number of results (default: 100)

        Returns:
            List of StolenItem entities matching criteria

        Raises:
            RepositoryError: If query fails
        """
        ...

    @abstractmethod
    async def delete(self, item_id: UUID) -> bool:
        """Delete a stolen item.

        Args:
            item_id: Unique identifier for the item

        Returns:
            True if deleted, False if not found

        Raises:
            RepositoryError: If delete operation fails
        """
        ...
