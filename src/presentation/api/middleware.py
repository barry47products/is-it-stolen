"""Custom middleware for FastAPI application."""

import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.infrastructure.logging import get_logger
from src.infrastructure.logging.context import clear_request_id, set_request_id

logger = get_logger(__name__)


class RequestIDMiddleware:
    """Pure ASGI middleware to add unique request ID to each request."""

    def __init__(self, app: ASGIApp) -> None:  # type: ignore[no-any-unimported]
        """Initialize middleware with ASGI app.

        Args:
            app: ASGI application to wrap
        """
        self.app = app

    async def __call__(  # type: ignore[no-any-unimported]
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Process request and add request ID.

        Args:
            scope: ASGI connection scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Generate request ID and store in scope and logging context
        request_id = str(uuid.uuid4())
        scope["state"] = {"request_id": request_id}

        # Set request ID in logging context for correlation
        set_request_id(request_id)

        async def send_with_request_id(  # type: ignore[no-any-unimported]
            message: Message,
        ) -> None:
            """Add request ID header to response.

            Args:
                message: ASGI message to send
            """
            if message["type"] == "http.response.start":
                headers = MutableHeaders(raw=message["headers"])
                headers.append("X-Request-ID", request_id)

            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            # Clear request ID from context after request completes
            clear_request_id()


class LoggingMiddleware:
    """Pure ASGI middleware to log requests and responses with timing."""

    def __init__(self, app: ASGIApp) -> None:  # type: ignore[no-any-unimported]
        """Initialize middleware with ASGI app.

        Args:
            app: ASGI application to wrap
        """
        self.app = app

    async def __call__(  # type: ignore[no-any-unimported]
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        """Log request and response with timing information.

        Args:
            scope: ASGI connection scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request info from scope
        method = scope["method"]
        path = scope["path"]
        client_host = (
            scope.get("client", ["unknown"])[0] if scope.get("client") else "unknown"
        )
        start_time = time.time()

        # Log request (request_id automatically added from context)
        logger.info(
            "Request started",
            method=method,
            path=path,
            client=client_host,
        )

        status_code = 500  # Default to 500 if response never starts

        async def send_with_logging(  # type: ignore[no-any-unimported]
            message: Message,
        ) -> None:
            """Log response details.

            Args:
                message: ASGI message to send
            """
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]

            await send(message)

            # Log after the response is complete
            if message["type"] == "http.response.body" and not message.get(
                "more_body", False
            ):
                duration_ms = (time.time() - start_time) * 1000

                logger.info(
                    "Request completed",
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration_ms=round(duration_ms, 2),
                )

        await self.app(scope, receive, send_with_logging)
