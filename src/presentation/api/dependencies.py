"""Dependency injection for FastAPI routes."""

from collections.abc import AsyncGenerator

from src.domain.services.matching_service import ItemMatchingService
from src.domain.services.verification_service import VerificationService
from src.infrastructure.messaging.event_bus import InMemoryEventBus
from src.infrastructure.persistence.repositories.postgres_stolen_item_repository import (
    PostgresStolenItemRepository,
)

# Singleton instances
_event_bus: InMemoryEventBus | None = None
_matching_service: ItemMatchingService | None = None
_verification_service: VerificationService | None = None


def get_event_bus() -> InMemoryEventBus:
    """Get or create event bus singleton.

    Returns:
        Event bus instance
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = InMemoryEventBus()
    return _event_bus


def get_matching_service() -> ItemMatchingService:
    """Get or create matching service singleton.

    Returns:
        Matching service instance
    """
    global _matching_service
    if _matching_service is None:
        _matching_service = ItemMatchingService()
    return _matching_service


def get_verification_service() -> VerificationService:
    """Get or create verification service singleton.

    Returns:
        Verification service instance
    """
    global _verification_service
    if _verification_service is None:
        _verification_service = VerificationService()
    return _verification_service


async def get_repository() -> AsyncGenerator[PostgresStolenItemRepository, None]:
    """Get repository instance for dependency injection.

    Yields:
        Repository instance
    """
    repository = PostgresStolenItemRepository()
    try:
        yield repository
    finally:
        # Cleanup if needed
        pass


# Use these functions with Depends() in route handlers:
# event_bus: InMemoryEventBus = Depends(get_event_bus)
# matching_service: ItemMatchingService = Depends(get_matching_service)
# verification_service: VerificationService = Depends(get_verification_service)
# repository: PostgresStolenItemRepository = Depends(get_repository)
