"""Event bus for publishing and subscribing to domain events."""

import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)


EventHandler = Callable[[Any], Awaitable[None]]


class InMemoryEventBus:
    """In-memory event bus implementation.

    This implementation stores handlers in memory and executes them
    asynchronously. Failed handlers are logged but don't stop other
    handlers from executing.
    """

    def __init__(self) -> None:
        """Initialize event bus with empty handler registry."""
        self._handlers: dict[type[Any], list[EventHandler]] = defaultdict(list)

    def subscribe(
        self,
        event_type: type[Any],
        handler: EventHandler,
    ) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Async handler function to call when event is published
        """
        self._handlers[event_type].append(handler)

    def unsubscribe(
        self,
        event_type: type[Any],
        handler: EventHandler,
    ) -> None:
        """Unsubscribe a handler from an event type.

        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove
        """
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    async def publish(self, event: Any) -> None:
        """Publish an event to all subscribed handlers.

        Handlers are executed asynchronously. If a handler fails, the error
        is logged and other handlers continue to execute.

        Args:
            event: Domain event to publish
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(
                    f"Error handling event {event_type.__name__}: {e}",
                    exc_info=True,
                )
