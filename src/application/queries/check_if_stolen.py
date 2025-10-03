"""Check If Stolen query and handler."""

from dataclasses import dataclass, field

from src.domain.entities.stolen_item import ItemStatus, StolenItem
from src.domain.exceptions.domain_exceptions import InvalidLocationError
from src.domain.repositories.stolen_item_repository import IStolenItemRepository
from src.domain.services.matching_service import ItemMatchingService
from src.domain.value_objects.item_category import ItemCategory
from src.domain.value_objects.location import Location

DEFAULT_LIMIT = 50
DEFAULT_OFFSET = 0
MAX_LIMIT = 100


@dataclass
class CheckIfStolenQuery:
    """Query to check if an item has been reported stolen.

    This DTO carries all search criteria from the presentation layer
    to the application layer.
    """

    description: str
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    color: str | None = None
    category: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float | None = None
    limit: int = DEFAULT_LIMIT
    offset: int = DEFAULT_OFFSET


@dataclass
class ItemMatch:
    """A stolen item match with similarity score.

    Represents a single search result with its similarity score
    and reason for matching.
    """

    item: StolenItem
    similarity_score: float
    match_reason: str


@dataclass
class CheckIfStolenResult:
    """Result of checking if an item is stolen.

    Contains all matches with their scores and metadata about the search.
    """

    matches: list[ItemMatch] = field(default_factory=list)
    total_count: int = 0


class CheckIfStolenHandler:
    """Handler for checking if items have been reported stolen.

    This query use case searches for stolen items and returns matches
    with similarity scores, sorted by relevance.
    """

    def __init__(
        self,
        repository: IStolenItemRepository,
        matching_service: ItemMatchingService,
    ) -> None:
        """Initialize handler with dependencies.

        Args:
            repository: Repository for querying stolen items
            matching_service: Service for calculating similarity scores
        """
        self._repository = repository
        self._matching_service = matching_service

    async def handle(self, query: CheckIfStolenQuery) -> CheckIfStolenResult:
        """Handle the check if stolen query.

        Args:
            query: Query containing item details to search for

        Returns:
            Results with matches sorted by similarity score (descending)

        Raises:
            InvalidLocationError: If location coordinates are invalid
        """
        # Query repository based on provided filters
        candidate_items = await self._query_candidates(query)

        # Create a temporary StolenItem for comparison
        search_item = self._create_search_item(query)

        # Score and filter matches
        matches = self._score_and_filter_matches(search_item, candidate_items)

        # Sort by similarity score (descending)
        matches.sort(key=lambda m: m.similarity_score, reverse=True)

        # Apply pagination
        total_count = len(matches)
        paginated_matches = matches[query.offset : query.offset + query.limit]

        return CheckIfStolenResult(matches=paginated_matches, total_count=total_count)

    async def _query_candidates(self, query: CheckIfStolenQuery) -> list[StolenItem]:
        """Query repository for candidate items based on filters.

        Args:
            query: Search query with filters

        Returns:
            List of candidate stolen items

        Raises:
            InvalidLocationError: If location coordinates are invalid
        """
        # Location-based search takes precedence
        if query.latitude is not None and query.longitude is not None:
            location = self._create_location(query.latitude, query.longitude)
            radius = query.radius_km if query.radius_km is not None else 10.0

            category = None
            if query.category:
                category = ItemCategory.from_user_input(query.category)

            return await self._repository.find_nearby(
                location=location,
                radius_km=radius,
                category=category,
            )

        # Category-based search
        if query.category:
            category = ItemCategory.from_user_input(query.category)
            return await self._repository.find_by_category(
                category=category,
                status=ItemStatus.ACTIVE,
                limit=MAX_LIMIT,
            )

        # Fallback: search all active items (limited)
        # Note: This could be inefficient for large databases
        # In production, consider requiring at least one filter
        return await self._repository.find_by_category(
            category=ItemCategory.BICYCLE,  # Default category for now
            status=ItemStatus.ACTIVE,
            limit=MAX_LIMIT,
        )

    def _create_search_item(self, query: CheckIfStolenQuery) -> StolenItem:
        """Create a temporary StolenItem from query for comparison.

        Args:
            query: Search query

        Returns:
            StolenItem instance for matching comparison
        """
        from datetime import UTC, datetime
        from uuid import uuid4

        from src.domain.value_objects.phone_number import PhoneNumber

        # Create minimal StolenItem for comparison purposes
        # This is not persisted - only used for matching
        category = (
            ItemCategory.from_user_input(query.category)
            if query.category
            else ItemCategory.BICYCLE
        )

        return StolenItem(
            report_id=uuid4(),
            reporter_phone=PhoneNumber("+12025550000"),  # Dummy US phone
            item_type=category,
            description=query.description,
            stolen_date=datetime.now(UTC),
            location=Location(latitude=0.0, longitude=0.0),  # Dummy location
            status=ItemStatus.ACTIVE,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            brand=query.brand,
            model=query.model,
            serial_number=query.serial_number,
            color=query.color,
        )

    def _score_and_filter_matches(
        self, search_item: StolenItem, candidates: list[StolenItem]
    ) -> list[ItemMatch]:
        """Score candidates and filter by threshold.

        Args:
            search_item: Item to search for
            candidates: Candidate items from database

        Returns:
            List of matches above threshold with scores
        """
        matches: list[ItemMatch] = []

        for candidate in candidates:
            score = self._matching_service.calculate_similarity(search_item, candidate)

            # Filter by threshold
            if score >= self._matching_service.threshold:
                reason = self._determine_match_reason(search_item, candidate, score)
                matches.append(
                    ItemMatch(
                        item=candidate, similarity_score=score, match_reason=reason
                    )
                )

        return matches

    @staticmethod
    def _determine_match_reason(
        search_item: StolenItem, candidate: StolenItem, score: float
    ) -> str:
        """Determine why items matched.

        Args:
            search_item: Item being searched for
            candidate: Candidate item from database
            score: Similarity score

        Returns:
            Human-readable match reason
        """
        # Check for exact serial number match
        if (
            search_item.serial_number
            and candidate.serial_number
            and search_item.serial_number == candidate.serial_number
        ):
            return "Exact serial number match"

        # High similarity
        if score >= 0.9:
            return "Very high similarity match"

        # Good similarity
        if score >= 0.8:
            return "High similarity match"

        # Moderate similarity
        return "Moderate similarity match"

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
