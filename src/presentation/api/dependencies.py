"""Dependency injection for FastAPI routes."""

from collections.abc import AsyncGenerator

from redis.asyncio import Redis

from src.domain.services.matching_service import ItemMatchingService
from src.domain.services.verification_service import VerificationService
from src.infrastructure.config.settings import get_settings
from src.infrastructure.messaging.event_bus import InMemoryEventBus
from src.infrastructure.persistence.repositories.postgres_stolen_item_repository import (
    PostgresStolenItemRepository,
)
from src.infrastructure.whatsapp.client import WhatsAppClient
from src.presentation.bot.message_processor import MessageProcessor
from src.presentation.bot.state_machine import ConversationStateMachine
from src.presentation.bot.storage import RedisConversationStorage

# Singleton instances
_event_bus: InMemoryEventBus | None = None
_matching_service: ItemMatchingService | None = None
_verification_service: VerificationService | None = None
_redis_client: Redis | None = None  # type: ignore[type-arg]
_conversation_storage: RedisConversationStorage | None = None
_state_machine: ConversationStateMachine | None = None
_whatsapp_client: WhatsAppClient | None = None
_message_processor: MessageProcessor | None = None


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


def get_redis_client() -> Redis:  # type: ignore[type-arg]
    """Get or create Redis client singleton.

    Returns:
        Redis client instance
    """
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = Redis.from_url(str(settings.redis_url))
    return _redis_client


def get_conversation_storage() -> RedisConversationStorage:
    """Get or create conversation storage singleton.

    Returns:
        Conversation storage instance
    """
    global _conversation_storage
    if _conversation_storage is None:
        redis_client = get_redis_client()
        _conversation_storage = RedisConversationStorage(redis_client=redis_client)
    return _conversation_storage


def get_state_machine() -> ConversationStateMachine:
    """Get or create state machine singleton.

    Returns:
        State machine instance
    """
    global _state_machine
    if _state_machine is None:
        storage = get_conversation_storage()
        _state_machine = ConversationStateMachine(storage=storage)
    return _state_machine


def get_whatsapp_client() -> WhatsAppClient:
    """Get or create WhatsApp client singleton.

    Returns:
        WhatsApp client instance
    """
    global _whatsapp_client
    if _whatsapp_client is None:
        settings = get_settings()
        _whatsapp_client = WhatsAppClient(
            phone_number_id=settings.whatsapp_phone_number_id,
            access_token=settings.whatsapp_access_token,
        )
    return _whatsapp_client


def get_message_processor() -> MessageProcessor:
    """Get or create message processor singleton.

    Returns:
        Message processor instance
    """
    global _message_processor
    if _message_processor is None:
        state_machine = get_state_machine()
        whatsapp_client = get_whatsapp_client()
        _message_processor = MessageProcessor(
            state_machine=state_machine, whatsapp_client=whatsapp_client
        )
    return _message_processor


# Use these functions with Depends() in route handlers:
# event_bus: InMemoryEventBus = Depends(get_event_bus)
# matching_service: ItemMatchingService = Depends(get_matching_service)
# verification_service: VerificationService = Depends(get_verification_service)
# repository: PostgresStolenItemRepository = Depends(get_repository)
# message_processor: MessageProcessor = Depends(get_message_processor)
