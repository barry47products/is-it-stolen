"""Domain-level constants for business logic.

This module contains enums and constants that represent core business concepts
and are independent of infrastructure or presentation concerns.
"""

from enum import Enum


class FlowId(str, Enum):
    """Configuration-driven flow identifiers.

    These match the flow IDs defined in config/flows/flows.yaml and are used
    to start and manage conversation flows.
    """

    CHECK_ITEM = "check_item"
    REPORT_ITEM = "report_item"
    CONTACT_US = "contact_us"


class ButtonId(str, Enum):
    """Interactive button identifiers for user actions.

    These match the button IDs used in WhatsApp interactive messages.
    """

    CHECK_ITEM = "check_item"
    REPORT_ITEM = "report_item"
    CONTACT_US = "contact_us"


class UserCommand(str, Enum):
    """User commands that can be entered at any time.

    These are special commands users can type to control the conversation flow.
    """

    CANCEL = "cancel"
    QUIT = "quit"
    EXIT = "exit"
    STOP = "stop"
    SKIP = "skip"
    UNKNOWN = "unknown"

    @classmethod
    def is_cancel_command(cls, text: str) -> bool:
        """Check if text is a cancel command.

        Args:
            text: User input text

        Returns:
            True if text matches any cancel command
        """
        normalized = text.lower().strip()
        return normalized in [
            cls.CANCEL.value,
            cls.QUIT.value,
            cls.EXIT.value,
            cls.STOP.value,
        ]


class MessageType(str, Enum):
    """WhatsApp message types received in webhooks.

    These correspond to the 'type' field in WhatsApp webhook messages.
    """

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    LOCATION = "location"
    INTERACTIVE = "interactive"


class InteractiveType(str, Enum):
    """Types of interactive messages in WhatsApp.

    These correspond to the 'interactive.type' field in WhatsApp messages.
    """

    BUTTON = "button"
    LIST = "list"
    BUTTON_REPLY = "button_reply"
    LIST_REPLY = "list_reply"


class PromptType(str, Enum):
    """Types of prompts in flow configuration.

    These correspond to the 'prompt_type' field in flow YAML configuration.
    """

    TEXT = "text"
    LIST = "list"
    BUTTON = "button"


class HandlerType(str, Enum):
    """Types of handlers in flow configuration.

    These correspond to the 'handler_type' field in flow YAML configuration.
    """

    QUERY = "query"
    COMMAND = "command"
