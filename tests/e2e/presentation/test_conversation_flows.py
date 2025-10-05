"""End-to-end tests for complete conversation flows."""

import pytest
from redis.asyncio import Redis

from src.application.commands.report_stolen_item import ReportStolenItemHandler
from src.application.queries.check_if_stolen import CheckIfStolenHandler
from src.infrastructure.config.settings import get_settings
from src.infrastructure.messaging.event_bus import InMemoryEventBus
from src.infrastructure.persistence.database import get_db
from src.infrastructure.persistence.models import StolenItemModel
from src.infrastructure.persistence.repositories.postgres_stolen_item_repository import (
    PostgresStolenItemRepository,
)
from src.infrastructure.whatsapp.client import WhatsAppClient
from src.presentation.bot.message_processor import MessageProcessor
from src.presentation.bot.state_machine import ConversationStateMachine
from src.presentation.bot.states import ConversationState
from src.presentation.bot.storage import RedisConversationStorage


@pytest.mark.e2e
class TestConversationFlows:
    """End-to-end tests for complete user conversation flows."""

    @pytest.fixture(autouse=True)
    def clear_database(self) -> None:
        """Clear stolen_items table before each test."""
        with get_db() as db:
            db.query(StolenItemModel).delete()
            db.commit()

    @pytest.fixture
    async def redis_client(  # type: ignore[misc]
        self,
    ) -> Redis:  # type: ignore[type-arg]
        """Create real Redis client for testing."""
        settings = get_settings()
        client = Redis.from_url(str(settings.redis_url))
        yield client
        await client.aclose()

    @pytest.fixture
    async def storage(
        self,
        redis_client: Redis,  # type: ignore[type-arg]
    ) -> RedisConversationStorage:
        """Create storage with real Redis."""
        return RedisConversationStorage(redis_client=redis_client)

    @pytest.fixture
    async def state_machine(
        self, storage: RedisConversationStorage
    ) -> ConversationStateMachine:
        """Create state machine with real storage."""
        return ConversationStateMachine(storage=storage)

    @pytest.fixture
    async def whatsapp_client(self) -> WhatsAppClient:
        """Create mock WhatsApp client that doesn't send real messages."""
        from unittest.mock import AsyncMock, MagicMock

        client = MagicMock(spec=WhatsAppClient)
        client.send_text_message = AsyncMock()
        return client  # type: ignore[return-value]

    @pytest.fixture
    def repository(self) -> PostgresStolenItemRepository:
        """Create repository with test database."""
        return PostgresStolenItemRepository()

    @pytest.fixture
    def check_handler(
        self, repository: PostgresStolenItemRepository
    ) -> CheckIfStolenHandler:
        """Create check handler with real repository."""
        from src.domain.services.matching_service import ItemMatchingService

        matching_service = ItemMatchingService()
        return CheckIfStolenHandler(
            repository=repository, matching_service=matching_service
        )

    @pytest.fixture
    def report_handler(
        self, repository: PostgresStolenItemRepository
    ) -> ReportStolenItemHandler:
        """Create report handler with real repository."""
        event_bus = InMemoryEventBus()
        return ReportStolenItemHandler(repository=repository, event_bus=event_bus)

    @pytest.fixture
    async def message_processor(
        self,
        state_machine: ConversationStateMachine,
        whatsapp_client: WhatsAppClient,
        check_handler: CheckIfStolenHandler,
        report_handler: ReportStolenItemHandler,
    ) -> MessageProcessor:
        """Create message processor with real components."""
        processor = MessageProcessor(
            state_machine=state_machine, whatsapp_client=whatsapp_client
        )
        # Inject handlers into router
        processor.router.check_if_stolen_handler = check_handler
        processor.router.report_stolen_item_handler = report_handler
        return processor

    @pytest.mark.asyncio
    async def test_complete_report_flow_with_all_details(
        self,
        message_processor: MessageProcessor,
        storage: RedisConversationStorage,
        repository: PostgresStolenItemRepository,
    ) -> None:
        """Test complete flow of reporting a stolen item with all details."""
        # Arrange
        phone = "+27821234501"

        try:
            # Act & Assert: User starts conversation
            response = await message_processor.process_message(phone, "Hi")
            assert "welcome" in response["reply"].lower()
            assert response["state"] == ConversationState.MAIN_MENU.value

            # User chooses to report
            response = await message_processor.process_message(phone, "2")
            assert (
                "type of item" in response["reply"].lower()
                or "category" in response["reply"].lower()
            )
            assert response["state"] == ConversationState.REPORTING_CATEGORY.value

            # User provides category
            response = await message_processor.process_message(phone, "bicycle")
            assert "bicycle" in response["reply"].lower()
            assert response["state"] == ConversationState.REPORTING_DESCRIPTION.value

            # User provides description
            response = await message_processor.process_message(
                phone, "Red Specialized Rockhopper mountain bike"
            )
            assert "location" in response["reply"].lower()
            assert response["state"] == ConversationState.REPORTING_LOCATION.value

            # User provides location
            response = await message_processor.process_message(phone, "London, UK")
            assert (
                "reported" in response["reply"].lower()
                or "thank you" in response["reply"].lower()
                or "recorded" in response["reply"].lower()
            )
            assert response["state"] == ConversationState.COMPLETE.value

            # Verify conversation was completed and removed from storage
            assert await storage.exists(phone) is False

            # Verify item was saved to database
            from src.domain.value_objects.phone_number import PhoneNumber

            phone_number = PhoneNumber(phone)
            all_items = await repository.find_by_reporter(phone_number)
            assert len(all_items) > 0
            saved_item = all_items[0]
            assert "Red Specialized Rockhopper" in saved_item.description
            assert saved_item.item_type == "bicycle"

        finally:
            # Cleanup
            await storage.delete(phone)

    @pytest.mark.asyncio
    async def test_complete_check_flow_no_matches(
        self,
        message_processor: MessageProcessor,
        storage: RedisConversationStorage,
    ) -> None:
        """Test complete flow of checking an item when no matches found."""
        # Arrange
        phone = "+27821234502"

        try:
            # Act & Assert: User starts conversation
            response = await message_processor.process_message(phone, "Hello")
            assert response["state"] == ConversationState.MAIN_MENU.value

            # User chooses to check
            response = await message_processor.process_message(phone, "1")
            assert (
                "type of item" in response["reply"].lower()
                or "category" in response["reply"].lower()
            )
            assert response["state"] == ConversationState.CHECKING_CATEGORY.value

            # User provides category
            response = await message_processor.process_message(phone, "laptop")
            assert "laptop" in response["reply"].lower()
            assert response["state"] == ConversationState.CHECKING_DESCRIPTION.value

            # User provides description
            response = await message_processor.process_message(
                phone, "Apple MacBook Pro 16 inch silver"
            )
            assert "location" in response["reply"].lower()
            assert response["state"] == ConversationState.CHECKING_LOCATION.value

            # User skips location
            response = await message_processor.process_message(phone, "skip")
            assert (
                "good news" in response["reply"].lower()
                or "not found" in response["reply"].lower()
                or "no stolen items" in response["reply"].lower()
            )
            assert response["state"] == ConversationState.COMPLETE.value

            # Verify conversation completed
            assert await storage.exists(phone) is False

        finally:
            # Cleanup
            await storage.delete(phone)

    @pytest.mark.asyncio
    async def test_complete_check_flow_with_matches(
        self,
        message_processor: MessageProcessor,
        storage: RedisConversationStorage,
        report_handler: ReportStolenItemHandler,
    ) -> None:
        """Test complete flow of checking an item when matches are found."""
        # Arrange
        phone_reporter = "+27821234503"
        phone_checker = "+27821234504"

        try:
            # First, report a stolen item
            from datetime import UTC, datetime

            from src.application.commands.report_stolen_item import (
                ReportStolenItemCommand,
            )

            command = ReportStolenItemCommand(
                reporter_phone=phone_reporter,
                item_type="laptop",
                description="Dell XPS 15 laptop black",
                stolen_date=datetime.now(UTC),
                latitude=51.5074,
                longitude=-0.1278,
                brand="Dell",
            )
            await report_handler.handle(command)

            # Act & Assert: Different user checks for similar item
            response = await message_processor.process_message(phone_checker, "Hi")
            assert response["state"] == ConversationState.MAIN_MENU.value

            # User chooses to check
            response = await message_processor.process_message(phone_checker, "check")
            assert response["state"] == ConversationState.CHECKING_CATEGORY.value

            # User provides category
            response = await message_processor.process_message(phone_checker, "laptop")
            assert response["state"] == ConversationState.CHECKING_DESCRIPTION.value

            # User provides similar description
            response = await message_processor.process_message(
                phone_checker, "Dell XPS laptop"
            )
            assert response["state"] == ConversationState.CHECKING_LOCATION.value

            # User provides location
            response = await message_processor.process_message(phone_checker, "skip")
            # Should find matches
            assert (
                "found" in response["reply"].lower()
                or "match" in response["reply"].lower()
            )
            assert response["state"] == ConversationState.COMPLETE.value

        finally:
            # Cleanup
            await storage.delete(phone_reporter)
            await storage.delete(phone_checker)

    @pytest.mark.asyncio
    async def test_cancel_operation_at_any_point(
        self,
        message_processor: MessageProcessor,
        storage: RedisConversationStorage,
    ) -> None:
        """Test user can cancel operation at any point in conversation."""
        # Arrange
        phone = "+27821234505"

        try:
            # Start conversation and go to reporting flow
            await message_processor.process_message(phone, "Hi")
            await message_processor.process_message(phone, "2")  # Choose report
            await message_processor.process_message(phone, "bicycle")  # Category

            # Verify we're in the middle of the flow
            assert await storage.exists(phone) is True

            # Act: User cancels
            response = await message_processor.process_message(phone, "cancel")

            # Assert: Conversation cancelled and cleaned up
            assert (
                "cancel" in response["reply"].lower()
                or "stopped" in response["reply"].lower()
            )
            assert response["state"] == ConversationState.CANCELLED.value
            assert await storage.exists(phone) is False

        finally:
            # Cleanup
            await storage.delete(phone)

    @pytest.mark.asyncio
    async def test_invalid_category_handling(
        self,
        message_processor: MessageProcessor,
        storage: RedisConversationStorage,
    ) -> None:
        """Test handling of invalid category input."""
        # Arrange
        phone = "+27821234506"

        try:
            # Start conversation
            await message_processor.process_message(phone, "Hi")
            response = await message_processor.process_message(phone, "1")  # Check
            assert response["state"] == ConversationState.CHECKING_CATEGORY.value

            # Act: Provide invalid category
            response = await message_processor.process_message(
                phone, "invalid_category_xyz"
            )

            # Assert: Should stay in same state and ask again
            assert (
                "invalid" in response["reply"].lower()
                or "type" in response["reply"].lower()
            )
            assert response["state"] == ConversationState.CHECKING_CATEGORY.value

            # User can try again with valid category
            response = await message_processor.process_message(phone, "bicycle")
            assert response["state"] == ConversationState.CHECKING_DESCRIPTION.value

        finally:
            # Cleanup
            await storage.delete(phone)

    @pytest.mark.asyncio
    async def test_invalid_main_menu_choice_handling(
        self,
        message_processor: MessageProcessor,
        storage: RedisConversationStorage,
    ) -> None:
        """Test handling of invalid main menu choice."""
        # Arrange
        phone = "+27821234507"

        try:
            # Start conversation
            response = await message_processor.process_message(phone, "Hi")
            assert response["state"] == ConversationState.MAIN_MENU.value

            # Act: Provide invalid choice
            response = await message_processor.process_message(phone, "99")

            # Assert: Should stay in main menu and show error
            assert (
                "invalid" in response["reply"].lower()
                or "choose" in response["reply"].lower()
            )
            assert response["state"] == ConversationState.MAIN_MENU.value

            # User can try again with valid choice
            response = await message_processor.process_message(phone, "1")
            assert response["state"] == ConversationState.CHECKING_CATEGORY.value

        finally:
            # Cleanup
            await storage.delete(phone)

    @pytest.mark.asyncio
    async def test_multiple_users_concurrent_conversations(
        self,
        message_processor: MessageProcessor,
        storage: RedisConversationStorage,
    ) -> None:
        """Test multiple users can have independent concurrent conversations."""
        # Arrange
        phone1 = "+27821234508"
        phone2 = "+27821234509"

        try:
            # Act: Start two conversations in parallel
            r1 = await message_processor.process_message(phone1, "Hi")
            r2 = await message_processor.process_message(phone2, "Hello")

            # Both should be at main menu
            assert r1["state"] == ConversationState.MAIN_MENU.value
            assert r2["state"] == ConversationState.MAIN_MENU.value

            # User 1 goes to check flow
            r1 = await message_processor.process_message(phone1, "1")
            assert r1["state"] == ConversationState.CHECKING_CATEGORY.value

            # User 2 goes to report flow
            r2 = await message_processor.process_message(phone2, "2")
            assert r2["state"] == ConversationState.REPORTING_CATEGORY.value

            # Both conversations should exist independently
            assert await storage.exists(phone1) is True
            assert await storage.exists(phone2) is True

            # User 1 continues with check
            r1 = await message_processor.process_message(phone1, "laptop")
            assert r1["state"] == ConversationState.CHECKING_DESCRIPTION.value

            # User 2 continues with report
            r2 = await message_processor.process_message(phone2, "bicycle")
            assert r2["state"] == ConversationState.REPORTING_DESCRIPTION.value

            # Conversations remain independent
            ctx1 = await storage.get(phone1)
            ctx2 = await storage.get(phone2)
            assert ctx1 is not None
            assert ctx2 is not None
            assert ctx1.data.get("category") == "laptop"
            assert ctx2.data.get("category") == "bicycle"

        finally:
            # Cleanup
            await storage.delete(phone1)
            await storage.delete(phone2)
