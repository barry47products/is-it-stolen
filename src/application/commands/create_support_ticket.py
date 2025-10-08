"""Create Support Ticket command and handler."""

import asyncio
from dataclasses import dataclass
from typing import Any
from uuid import uuid4


@dataclass
class CreateSupportTicketCommand:
    """Command to create a support ticket.

    This DTO carries all data needed to create a support ticket from the
    presentation layer to the application layer.
    """

    phone_number: str
    message: str
    email: str | None = None


class CreateSupportTicketHandler:
    """Handler for creating support tickets.

    This is a minimal implementation to demonstrate config-driven flows.
    In production, this would persist to a database or integrate with
    a ticketing system.
    """

    async def handle(self, data: dict[str, str]) -> dict[str, Any]:
        """Handle the create support ticket command.

        Args:
            data: Flow data containing message and optional email

        Returns:
            Result with ticket_id and success message

        Raises:
            ValueError: If message is empty
        """
        message = data.get("message", "")
        email = data.get("email", "")

        if not message or not message.strip():
            raise ValueError("Message cannot be empty")

        # Skip email if user typed 'skip' or if it's empty
        email_value = None if not email or email.lower() == "skip" else email

        # Generate ticket ID
        ticket_id = uuid4()

        # In production, this would:
        # 1. Save to database (async)
        # 2. Send email notification (async)
        # 3. Integrate with ticketing system (async)
        # For now, yield control to event loop for protocol compliance
        await asyncio.sleep(0)

        return {
            "ticket_id": str(ticket_id),
            "message": "Your support ticket has been created successfully!",
            "email": email_value,
        }
