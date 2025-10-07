"""Tests for handler registry."""

from pathlib import Path

import pytest

from src.infrastructure.handlers.handler_registry import (
    HandlerRegistry,
    ServiceRegistry,
)


# Mock handler for testing
class MockQueryHandler:
    """Mock query handler for testing."""

    def __init__(self, repository=None):  # type: ignore
        """Initialize with optional repository."""
        self.repository = repository

    async def handle(self, query):  # type: ignore
        """Handle query."""
        return {"result": "success", "has_repo": self.repository is not None}


class MockCommandHandler:
    """Mock command handler for testing."""

    def __init__(self, repository=None, event_bus=None):  # type: ignore
        """Initialize with dependencies."""
        self.repository = repository
        self.event_bus = event_bus

    async def handle(self, command):  # type: ignore
        """Handle command."""
        return {
            "result": "executed",
            "has_repo": self.repository is not None,
            "has_bus": self.event_bus is not None,
        }


class MockRepository:
    """Mock repository for testing."""

    def __init__(self) -> None:
        """Initialize repository."""
        self.name = "mock_repository"


class MockEventBus:
    """Mock event bus for testing."""

    def __init__(self) -> None:
        """Initialize event bus."""
        self.name = "mock_event_bus"


@pytest.mark.unit
class TestServiceRegistry:
    """Test service registry for dependency injection."""

    def test_registers_service(self) -> None:
        """Test registering a service."""
        # Arrange
        registry = ServiceRegistry()
        service = MockRepository()

        # Act
        registry.register("repository", service)

        # Assert
        assert registry.get("repository") is service

    def test_registers_singleton_service(self) -> None:
        """Test singleton services are cached."""
        # Arrange
        registry = ServiceRegistry()

        # Act
        registry.register_singleton("repository", MockRepository)
        service1 = registry.get("repository")
        service2 = registry.get("repository")

        # Assert
        assert service1 is service2
        assert isinstance(service1, MockRepository)

    def test_raises_error_for_missing_service(self) -> None:
        """Test error when requesting unregistered service."""
        # Arrange
        registry = ServiceRegistry()

        # Act & Assert
        with pytest.raises(KeyError, match="Service 'nonexistent' not registered"):
            registry.get("nonexistent")

    def test_overrides_existing_service(self) -> None:
        """Test registering service with same name overrides."""
        # Arrange
        registry = ServiceRegistry()
        service1 = MockRepository()
        service2 = MockRepository()

        # Act
        registry.register("repository", service1)
        registry.register("repository", service2)

        # Assert
        assert registry.get("repository") is service2


@pytest.mark.unit
class TestHandlerRegistry:
    """Test handler registry for dynamic handler loading."""

    def test_registers_handler_class(self) -> None:
        """Test registering a handler class."""
        # Arrange
        registry = HandlerRegistry()

        # Act
        registry.register_handler("mock_query", MockQueryHandler)

        # Assert
        assert registry.has_handler("mock_query")

    def test_creates_handler_instance(self) -> None:
        """Test creating handler instance without dependencies."""
        # Arrange
        registry = HandlerRegistry()
        registry.register_handler("mock_query", MockQueryHandler)

        # Act
        handler = registry.get_handler("mock_query")

        # Assert
        assert isinstance(handler, MockQueryHandler)
        assert handler.repository is None

    def test_injects_dependencies(self) -> None:
        """Test dependency injection when creating handler."""
        # Arrange
        service_registry = ServiceRegistry()
        service_registry.register("repository", MockRepository())

        handler_registry = HandlerRegistry(service_registry=service_registry)
        handler_registry.register_handler(
            "mock_query", MockQueryHandler, dependencies=["repository"]
        )

        # Act
        handler = handler_registry.get_handler("mock_query")

        # Assert
        assert isinstance(handler, MockQueryHandler)
        assert isinstance(handler.repository, MockRepository)

    def test_injects_multiple_dependencies(self) -> None:
        """Test injecting multiple dependencies."""
        # Arrange
        service_registry = ServiceRegistry()
        service_registry.register("repository", MockRepository())
        service_registry.register("event_bus", MockEventBus())

        handler_registry = HandlerRegistry(service_registry=service_registry)
        handler_registry.register_handler(
            "mock_command",
            MockCommandHandler,
            dependencies=["repository", "event_bus"],
        )

        # Act
        handler = handler_registry.get_handler("mock_command")

        # Assert
        assert isinstance(handler, MockCommandHandler)
        assert isinstance(handler.repository, MockRepository)
        assert isinstance(handler.event_bus, MockEventBus)

    def test_raises_error_for_missing_handler(self) -> None:
        """Test error when requesting unregistered handler."""
        # Arrange
        registry = HandlerRegistry()

        # Act & Assert
        with pytest.raises(KeyError, match="Handler 'nonexistent' not registered"):
            registry.get_handler("nonexistent")

    def test_loads_handlers_from_config(self, tmp_path: Path) -> None:
        """Test loading handlers from YAML configuration."""
        # Arrange
        config_file = tmp_path / "handlers.yaml"
        config_file.write_text(
            """
handlers:
  check_if_stolen:
    class: "tests.unit.infrastructure.handlers.test_handler_registry.MockQueryHandler"
    dependencies: []
  report_stolen_item:
    class: "tests.unit.infrastructure.handlers.test_handler_registry.MockCommandHandler"
    dependencies: []
"""
        )

        registry = HandlerRegistry()

        # Act
        registry.load_from_config(config_file)

        # Assert
        assert registry.has_handler("check_if_stolen")
        assert registry.has_handler("report_stolen_item")

    def test_loads_handlers_with_dependencies_from_config(self, tmp_path: Path) -> None:
        """Test loading handlers with dependencies from config."""
        # Arrange
        config_file = tmp_path / "handlers.yaml"
        config_file.write_text(
            """
handlers:
  mock_command:
    class: "tests.unit.infrastructure.handlers.test_handler_registry.MockCommandHandler"
    dependencies:
      - repository
      - event_bus
"""
        )

        service_registry = ServiceRegistry()
        service_registry.register("repository", MockRepository())
        service_registry.register("event_bus", MockEventBus())

        handler_registry = HandlerRegistry(service_registry=service_registry)

        # Act
        handler_registry.load_from_config(config_file)
        handler = handler_registry.get_handler("mock_command")

        # Assert
        assert isinstance(handler, MockCommandHandler)
        assert isinstance(handler.repository, MockRepository)
        assert isinstance(handler.event_bus, MockEventBus)

    def test_raises_error_for_invalid_class_path(self, tmp_path: Path) -> None:
        """Test error for invalid module path in config."""
        # Arrange
        config_file = tmp_path / "handlers.yaml"
        config_file.write_text(
            """
handlers:
  invalid:
    class: "nonexistent.module.Handler"
    dependencies: []
"""
        )

        registry = HandlerRegistry()

        # Act & Assert
        with pytest.raises(ImportError):
            registry.load_from_config(config_file)

    def test_raises_error_for_missing_dependency(self, tmp_path: Path) -> None:
        """Test error when handler dependency not in service registry."""
        # Arrange
        config_file = tmp_path / "handlers.yaml"
        config_file.write_text(
            """
handlers:
  mock_query:
    class: "tests.unit.infrastructure.handlers.test_handler_registry.MockQueryHandler"
    dependencies:
      - missing_service
"""
        )

        registry = HandlerRegistry(service_registry=ServiceRegistry())

        # Act
        registry.load_from_config(config_file)

        # Assert - should raise when getting handler
        with pytest.raises(KeyError, match="Service 'missing_service' not registered"):
            registry.get_handler("mock_query")

    def test_raises_error_for_nonexistent_config_file(self) -> None:
        """Test error when config file doesn't exist."""
        # Arrange
        registry = HandlerRegistry()

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            registry.load_from_config("/nonexistent/handlers.yaml")

    def test_raises_error_for_malformed_yaml_config(self, tmp_path: Path) -> None:
        """Test error for malformed YAML in config file."""
        # Arrange
        config_file = tmp_path / "handlers.yaml"
        config_file.write_text("handlers:\n  invalid: {missing quote")

        registry = HandlerRegistry()

        # Act & Assert
        with pytest.raises(ValueError, match="Failed to parse YAML"):
            registry.load_from_config(config_file)

    def test_raises_error_for_non_dict_yaml_config(self, tmp_path: Path) -> None:
        """Test error when YAML is not a dictionary."""
        # Arrange
        config_file = tmp_path / "handlers.yaml"
        config_file.write_text("- item1\n- item2\n")

        registry = HandlerRegistry()

        # Act & Assert
        with pytest.raises(ValueError, match="Configuration must be a YAML mapping"):
            registry.load_from_config(config_file)

    def test_raises_error_for_invalid_config_structure(self, tmp_path: Path) -> None:
        """Test error for invalid config structure (missing required fields)."""
        # Arrange
        config_file = tmp_path / "handlers.yaml"
        config_file.write_text(
            """
handlers:
  invalid:
    dependencies: []
"""
        )

        registry = HandlerRegistry()

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid configuration structure"):
            registry.load_from_config(config_file)
