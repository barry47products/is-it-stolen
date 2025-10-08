"""Handler registry for dynamic loading of command and query handlers."""

import importlib
import logging
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

type HandlerClass = type[Any]


class HandlerConfig(BaseModel):
    """Configuration for a single handler."""

    class_path: str = Field(
        ..., alias="class", description="Full module path to handler class"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="List of service dependencies"
    )


class HandlersConfig(BaseModel):
    """Configuration for all handlers."""

    handlers: dict[str, HandlerConfig] = Field(
        ..., description="Handler configurations by name"
    )


class ServiceRegistry:
    """Registry for services used in dependency injection."""

    def __init__(self) -> None:
        """Initialize service registry."""
        self._services: dict[str, Any] = {}
        self._singletons: dict[str, type[Any]] = {}

    def register(self, name: str, service: Any) -> None:
        """Register a service instance.

        Args:
            name: Service name
            service: Service instance
        """
        self._services[name] = service
        logger.debug(f"Registered service: {name}")

    def register_singleton(self, name: str, service_class: type[Any]) -> None:
        """Register a singleton service class.

        The service will be instantiated once on first access.

        Args:
            name: Service name
            service_class: Service class to instantiate
        """
        self._singletons[name] = service_class
        logger.debug(f"Registered singleton service: {name}")

    def get(self, name: str) -> Any:
        """Get a service by name.

        Args:
            name: Service name

        Returns:
            Service instance

        Raises:
            KeyError: If service not registered
        """
        # Check if it's a regular service
        if name in self._services:
            return self._services[name]

        # Check if it's a singleton that needs instantiation
        if name in self._singletons:
            service = self._singletons[name]()
            self._services[name] = service  # Cache it
            del self._singletons[name]  # Remove from singletons
            return service

        raise KeyError(f"Service '{name}' not registered")


class HandlerRegistry:
    """Registry for dynamically loading and managing handlers."""

    def __init__(self, service_registry: ServiceRegistry | None = None) -> None:
        """Initialize handler registry.

        Args:
            service_registry: Optional service registry for dependency injection
        """
        self._handlers: dict[str, tuple[type[Any], list[str]]] = {}
        self._service_registry = service_registry or ServiceRegistry()

    def register_handler(
        self,
        name: str,
        handler_class: type[Any],
        dependencies: list[str] | None = None,
    ) -> None:
        """Register a handler class.

        Args:
            name: Handler name
            handler_class: Handler class
            dependencies: Optional list of dependency names
        """
        self._handlers[name] = (handler_class, dependencies or [])
        logger.debug(f"Registered handler: {name}")

    def has_handler(self, name: str) -> bool:
        """Check if handler is registered.

        Args:
            name: Handler name

        Returns:
            True if handler registered
        """
        return name in self._handlers

    def get_handler(self, name: str) -> Any:
        """Get handler instance with dependencies injected.

        Args:
            name: Handler name

        Returns:
            Handler instance with dependencies

        Raises:
            KeyError: If handler not registered
        """
        if name not in self._handlers:
            raise KeyError(f"Handler '{name}' not registered")

        handler_class, dependency_names = self._handlers[name]

        # Resolve dependencies
        dependencies = {}
        for dep_name in dependency_names:
            dependencies[dep_name] = self._service_registry.get(dep_name)

        # Create handler instance with dependencies
        return handler_class(**dependencies)

    def load_from_config(self, config_path: Path | str) -> None:
        """Load handlers from YAML configuration.

        Args:
            config_path: Path to handlers.yaml configuration file

        Raises:
            FileNotFoundError: If config file doesn't exist
            ImportError: If handler class cannot be imported
            ValueError: If configuration is invalid
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("Configuration must be a YAML mapping")

        try:
            config = HandlersConfig(**data)
        except Exception as e:
            raise ValueError(f"Invalid configuration structure: {e}") from e

        # Load each handler
        for handler_name, handler_config in config.handlers.items():
            handler_class = self._load_class(handler_config.class_path)
            self.register_handler(
                handler_name, handler_class, handler_config.dependencies
            )

        logger.info(f"Loaded {len(config.handlers)} handlers from {config_path}")

    def _load_class(self, class_path: str) -> type[Any]:
        """Dynamically load a class from module path.

        Args:
            class_path: Full module path (e.g., "module.submodule.ClassName")

        Returns:
            Loaded class

        Raises:
            ImportError: If module or class cannot be loaded
        """
        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            handler_class: type[Any] = getattr(module, class_name)
            return handler_class
        except (ValueError, ImportError, AttributeError) as e:
            raise ImportError(f"Failed to load class '{class_path}': {e}") from e
