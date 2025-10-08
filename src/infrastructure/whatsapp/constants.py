"""WhatsApp Cloud API constants and configuration values.

This module contains constants specific to the WhatsApp Business Cloud API,
including API endpoints, validation limits, and protocol constants.
"""

from enum import Enum

# API Configuration
WHATSAPP_API_VERSION = "v21.0"
WHATSAPP_BASE_URL = "https://graph.facebook.com"

# Timeouts and Retry Configuration
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RETRIES = 3
INITIAL_BACKOFF_SECONDS = 1.0
BACKOFF_MULTIPLIER = 2.0

# HTTP Status Codes
HTTP_OK = 200
HTTP_TOO_MANY_REQUESTS = 429

# Webhook Verification
WEBHOOK_MODE_SUBSCRIBE = "subscribe"
WEBHOOK_SIGNATURE_PREFIX = "sha256="

# WhatsApp API Message Fields
MESSAGING_PRODUCT = "whatsapp"
RECIPIENT_TYPE_INDIVIDUAL = "individual"

# Interactive Message Limits (WhatsApp API constraints)
MAX_BUTTONS_PER_MESSAGE = 3
MAX_BUTTON_TITLE_LENGTH = 20
MAX_SECTIONS_PER_LIST = 10
MAX_ROWS_PER_LIST = 10
MIN_BUTTONS_REQUIRED = 1
MIN_SECTIONS_REQUIRED = 1

# Message Type Constants
MESSAGE_TYPE_TEXT = "text"
MESSAGE_TYPE_TEMPLATE = "template"
MESSAGE_TYPE_IMAGE = "image"
MESSAGE_TYPE_INTERACTIVE = "interactive"

# Interactive Type Constants
INTERACTIVE_TYPE_BUTTON = "button"
INTERACTIVE_TYPE_LIST = "list"

# Interactive Component Types
COMPONENT_TYPE_BODY = "body"
COMPONENT_TYPE_HEADER = "header"
REPLY_TYPE = "reply"
PARAMETER_TYPE_TEXT = "text"


class WhatsAppMessageField(str, Enum):
    """Field names in WhatsApp message payloads."""

    TYPE = "type"
    FROM = "from"
    ID = "id"
    TIMESTAMP = "timestamp"
    TEXT = "text"
    BODY = "body"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    LOCATION = "location"
    INTERACTIVE = "interactive"
    BUTTON_REPLY = "button_reply"
    LIST_REPLY = "list_reply"
    TITLE = "title"
    DESCRIPTION = "description"
    LATITUDE = "latitude"
    LONGITUDE = "longitude"
    NAME = "name"
    ADDRESS = "address"
    MEDIA_ID = "id"
    MIME_TYPE = "mime_type"
    URL = "url"


class WhatsAppWebhookField(str, Enum):
    """Field names in WhatsApp webhook payloads."""

    ENTRY = "entry"
    CHANGES = "changes"
    VALUE = "value"
    MESSAGES = "messages"
    ERROR = "error"
    MESSAGE = "message"
    CODE = "code"
