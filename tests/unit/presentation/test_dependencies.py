"""Tests for dependency injection."""

import pytest

from src.presentation.api.dependencies import (
    get_event_bus,
    get_matching_service,
    get_repository,
    get_verification_service,
)


@pytest.mark.unit
class TestDependencyInjection:
    """Test dependency injection functions."""

    def test_get_event_bus_returns_singleton(self) -> None:
        """Test that event bus is a singleton."""
        # Act
        bus1 = get_event_bus()
        bus2 = get_event_bus()

        # Assert - same instance returned
        assert bus1 is bus2

    def test_get_matching_service_returns_singleton(self) -> None:
        """Test that matching service is a singleton."""
        # Act
        service1 = get_matching_service()
        service2 = get_matching_service()

        # Assert - same instance returned
        assert service1 is service2

    def test_get_verification_service_returns_singleton(self) -> None:
        """Test that verification service is a singleton."""
        # Act
        service1 = get_verification_service()
        service2 = get_verification_service()

        # Assert - same instance returned
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_get_repository_yields_new_instance(self) -> None:
        """Test that repository generator yields instance."""
        # Act
        async for repo in get_repository():
            # Assert - repository instance returned
            assert repo is not None
            break  # Only need first yield
