"""Find Nearby Items query and handler."""

from dataclasses import dataclass, field

from src.domain.entities.stolen_item import StolenItem
from src.domain.exceptions.domain_exceptions import InvalidLocationError
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location

DEFAULT_RADIUS_KM = 10.0
MAX_RADIUS_KM = 100.0
DEFAULT_LIMIT = 50
DEFAULT_OFFSET = 0


@dataclass
class FindNearbyItemsQuery:
    """Query to find stolen items near a location.

    This DTO carries location and search parameters from the presentation
    layer to the application layer.
    """

    latitude: float
    longitude: float
    radius_km: float = DEFAULT_RADIUS_KM
    category: str | None = None
    limit: int = DEFAULT_LIMIT
    offset: int = DEFAULT_OFFSET


@dataclass
class NearbyItem:
    """A stolen item with its distance from search location.

    Represents a single search result with distance information.
    """

    item: StolenItem
    distance_km: float


@dataclass
class FindNearbyItemsResult:
    """Result of finding nearby stolen items.

    Contains all nearby items with distances and metadata about the search.
    """

    items: list[NearbyItem] = field(default_factory=list)
    total_count: int = 0


class FindNearbyItemsHandler:
    """Handler for finding stolen items near a location.

    This query use case searches for stolen items within a geographic radius,
    sorted by distance from the search location.
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

    async def handle(self, query: FindNearbyItemsQuery) -> FindNearbyItemsResult:
        """Handle the find nearby items query.

        Args:
            query: Query containing location and search parameters

        Returns:
            Results with nearby items sorted by distance (ascending)

        Raises:
            InvalidLocationError: If coordinates are invalid
            ValueError: If radius is invalid
        """
        # Validate radius
        self._validate_radius(query.radius_km)

        # Create location value object
        location = self._create_location(query.latitude, query.longitude)

        # Parse category if provided
        category = None
        if query.category:
            category = ItemCategory.from_user_input(query.category)

        # Query repository for nearby items
        items = await self._repository.find_nearby(
            location=location,
            radius_km=query.radius_km,
            category=category,
        )

        # Calculate distances and create nearby items
        nearby_items = self._create_nearby_items(items, location)

        # Sort by distance (ascending - nearest first)
        nearby_items.sort(key=lambda item: item.distance_km)

        # Apply pagination
        total_count = len(nearby_items)
        paginated_items = nearby_items[query.offset : query.offset + query.limit]

        return FindNearbyItemsResult(items=paginated_items, total_count=total_count)

    @staticmethod
    def _validate_radius(radius_km: float) -> None:
        """Validate search radius.

        Args:
            radius_km: Radius in kilometers

        Raises:
            ValueError: If radius is invalid
        """
        if radius_km <= 0:
            raise ValueError("Radius must be positive")

        if radius_km > MAX_RADIUS_KM:
            raise ValueError(
                f"Radius {radius_km}km exceeds maximum allowed radius of {MAX_RADIUS_KM}km"
            )

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

    @staticmethod
    def _create_nearby_items(
        items: list[StolenItem], search_location: Location
    ) -> list[NearbyItem]:
        """Create nearby items with distance calculations.

        Args:
            items: List of stolen items from repository
            search_location: Location to calculate distances from

        Returns:
            List of nearby items with distances
        """
        nearby_items: list[NearbyItem] = []

        for item in items:
            distance_km = search_location.distance_to(item.location)
            nearby_items.append(NearbyItem(item=item, distance_km=distance_km))

        return nearby_items
