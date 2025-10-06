"""Tests for message router."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.application.commands.report_stolen_item import ReportStolenItemCommand
from src.application.queries.check_if_stolen import (
    CheckIfStolenQuery,
    CheckIfStolenResult,
)
from src.domain.exceptions.domain_exceptions import ItemNotFoundError, RepositoryError
from src.domain.value_objects.item_category import ItemCategory
from src.presentation.bot.context import ConversationContext
from src.presentation.bot.error_handler import ErrorHandler
from src.presentation.bot.message_router import MessageRouter
from src.presentation.bot.response_builder import ResponseBuilder
from src.presentation.bot.states import ConversationState


@pytest.mark.unit
class TestMessageRouter:
    """Test message router."""

    @pytest.mark.asyncio
    async def test_route_message_from_idle_shows_main_menu(self) -> None:
        """Test routing from IDLE state shows main menu."""
        # Arrange
        phone_number = "+1234567890"
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.IDLE,
            )
        )
        state_machine.transition = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.MAIN_MENU,
            )
        )

        parser = MagicMock()
        router = MessageRouter(state_machine, parser)

        # Act
        response = await router.route_message(phone_number, "Hi")

        # Assert
        assert "welcome" in response["reply"].lower()
        state_machine.transition.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_message_handles_cancel_command(self) -> None:
        """Test routing handles cancel command from any state."""
        # Arrange
        phone_number = "+1234567890"
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.CHECKING_CATEGORY,
            )
        )
        state_machine.cancel = AsyncMock()

        parser = MagicMock()
        router = MessageRouter(state_machine, parser)

        # Act
        response = await router.route_message(phone_number, "cancel")

        # Assert
        assert "cancel" in response["reply"].lower()
        state_machine.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_menu_routes_to_checking_flow(self) -> None:
        """Test main menu routes to checking flow when user selects 1."""
        # Arrange
        phone_number = "+1234567890"
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.MAIN_MENU,
            )
        )
        state_machine.transition = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.CHECKING_CATEGORY,
            )
        )

        parser = MagicMock()
        router = MessageRouter(state_machine, parser)

        # Act
        response = await router.route_message(phone_number, "1")

        # Assert
        assert "check" in response["reply"].lower()

    @pytest.mark.asyncio
    async def test_main_menu_routes_to_reporting_flow(self) -> None:
        """Test main menu routes to reporting flow when user selects 2."""
        # Arrange
        phone_number = "+1234567890"
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.MAIN_MENU,
            )
        )
        state_machine.transition = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.REPORTING_CATEGORY,
            )
        )

        parser = MagicMock()
        router = MessageRouter(state_machine, parser)

        # Act
        response = await router.route_message(phone_number, "2")

        # Assert
        assert "report" in response["reply"].lower()

    @pytest.mark.asyncio
    async def test_checking_category_parses_category(self) -> None:
        """Test checking category state parses and stores category."""
        # Arrange
        phone_number = "+1234567890"
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.CHECKING_CATEGORY,
            )
        )
        state_machine.update_data = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.CHECKING_CATEGORY,
                data={"category": "bicycle"},
            )
        )
        state_machine.transition = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.CHECKING_DESCRIPTION,
            )
        )

        parser = MagicMock()
        parser.parse_category = MagicMock(return_value=ItemCategory.BICYCLE)

        router = MessageRouter(state_machine, parser)

        # Act
        response = await router.route_message(phone_number, "bike")

        # Assert
        parser.parse_category.assert_called_once_with("bike")
        assert "describe" in response["reply"].lower()

    @pytest.mark.asyncio
    async def test_checking_description_extracts_brand(self) -> None:
        """Test checking description extracts brand/model."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.CHECKING_DESCRIPTION,
            data={"category": "bicycle"},
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.transition = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.CHECKING_LOCATION,
            )
        )

        parser = MagicMock()
        parser.extract_brand_model = MagicMock(return_value="Trek 820")

        router = MessageRouter(state_machine, parser)

        # Act
        response = await router.route_message(phone_number, "Red Trek 820 bike")

        # Assert
        parser.extract_brand_model.assert_called_once_with("Red Trek 820 bike")
        assert "location" in response["reply"].lower()

    @pytest.mark.asyncio
    async def test_checking_location_completes_flow(self) -> None:
        """Test checking location completes the checking flow."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.CHECKING_LOCATION,
            data={"category": "bicycle", "description": "Red Trek bike"},
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        parser.parse_location_text = MagicMock(return_value="Main Street")

        router = MessageRouter(state_machine, parser)

        # Act
        response = await router.route_message(phone_number, "Main Street")

        # Assert
        parser.parse_location_text.assert_called_once_with("Main Street")
        state_machine.complete.assert_called_once()
        assert "searching" in response["reply"].lower()

    @pytest.mark.asyncio
    async def test_reporting_category_parses_category(self) -> None:
        """Test reporting category state parses and stores category."""
        # Arrange
        phone_number = "+1234567890"
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.REPORTING_CATEGORY,
            )
        )
        state_machine.update_data = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.REPORTING_CATEGORY,
                data={"category": "phone"},
            )
        )
        state_machine.transition = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.REPORTING_DESCRIPTION,
            )
        )

        parser = MagicMock()
        parser.parse_category = MagicMock(return_value=ItemCategory.PHONE)

        router = MessageRouter(state_machine, parser)

        # Act
        response = await router.route_message(phone_number, "phone")

        # Assert
        parser.parse_category.assert_called_once_with("phone")
        assert "detail" in response["reply"].lower()

    @pytest.mark.asyncio
    async def test_reporting_description_extracts_brand(self) -> None:
        """Test reporting description extracts brand/model."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.REPORTING_DESCRIPTION,
            data={"category": "phone"},
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.transition = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.REPORTING_LOCATION,
            )
        )

        parser = MagicMock()
        parser.extract_brand_model = MagicMock(return_value="iPhone 13")

        router = MessageRouter(state_machine, parser)

        # Act
        response = await router.route_message(phone_number, "Black iPhone 13 Pro")

        # Assert
        parser.extract_brand_model.assert_called_once()
        assert "where" in response["reply"].lower()

    @pytest.mark.asyncio
    async def test_reporting_location_completes_flow(self) -> None:
        """Test reporting location completes the reporting flow."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.REPORTING_LOCATION,
            data={"category": "phone", "description": "iPhone 13"},
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        parser.parse_location_text = MagicMock(return_value="Downtown")

        router = MessageRouter(state_machine, parser)

        # Act
        response = await router.route_message(phone_number, "Downtown")

        # Assert
        parser.parse_location_text.assert_called_once_with("Downtown")
        state_machine.complete.assert_called_once()
        assert "thank you" in response["reply"].lower()

    @pytest.mark.asyncio
    async def test_terminal_state_resets_to_idle(self) -> None:
        """Test terminal state resets conversation to idle."""
        # Arrange
        phone_number = "+1234567890"
        state_machine = MagicMock()
        # First call returns COMPLETE state, second call returns IDLE
        state_machine.get_or_create = AsyncMock(
            side_effect=[
                ConversationContext(
                    phone_number=phone_number,
                    state=ConversationState.COMPLETE,
                ),
                ConversationContext(
                    phone_number=phone_number,
                    state=ConversationState.IDLE,
                ),
            ]
        )
        state_machine.transition = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.MAIN_MENU,
            )
        )

        parser = MagicMock()
        router = MessageRouter(state_machine, parser)

        # Act
        response = await router.route_message(phone_number, "Hi")

        # Assert
        assert "welcome" in response["reply"].lower()

    @pytest.mark.asyncio
    async def test_category_not_recognized_returns_error(self) -> None:
        """Test unrecognized category returns error message."""
        # Arrange
        phone_number = "+1234567890"
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.CHECKING_CATEGORY,
            )
        )

        parser = MagicMock()
        parser.parse_category = MagicMock(return_value=None)

        router = MessageRouter(state_machine, parser)

        # Act
        response = await router.route_message(phone_number, "unknown item")

        # Assert
        assert "didn't recognize" in response["reply"].lower()

    @pytest.mark.asyncio
    async def test_main_menu_invalid_choice_prompts_again(self) -> None:
        """Test invalid main menu choice prompts user again."""
        # Arrange
        phone_number = "+1234567890"
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.MAIN_MENU,
            )
        )

        parser = MagicMock()
        router = MessageRouter(state_machine, parser)

        # Act
        response = await router.route_message(phone_number, "invalid")

        # Assert
        assert "choose an option" in response["reply"].lower()

    @pytest.mark.asyncio
    async def test_location_skip_stores_none(self) -> None:
        """Test skipping location stores None."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.CHECKING_LOCATION,
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        router = MessageRouter(state_machine, parser)

        # Act
        await router.route_message(phone_number, "skip")

        # Assert
        # Check that update_data was called with location=None
        state_machine.update_data.assert_called_once()
        call_args = state_machine.update_data.call_args[0]
        assert call_args[1]["location"] is None

    @pytest.mark.asyncio
    async def test_reporting_category_not_recognized_returns_error(self) -> None:
        """Test unrecognized category in reporting flow returns error."""
        # Arrange
        phone_number = "+1234567890"
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.REPORTING_CATEGORY,
            )
        )

        parser = MagicMock()
        parser.parse_category = MagicMock(return_value=None)

        router = MessageRouter(state_machine, parser)

        # Act
        response = await router.route_message(phone_number, "something weird")

        # Assert
        assert "didn't recognize" in response["reply"].lower()
        assert response["state"] == ConversationState.REPORTING_CATEGORY.value

    @pytest.mark.asyncio
    async def test_reporting_location_unknown_stores_none(self) -> None:
        """Test reporting location with 'unknown' stores None."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.REPORTING_LOCATION,
            data={"category": "phone", "description": "iPhone 13"},
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        router = MessageRouter(state_machine, parser)

        # Act
        await router.route_message(phone_number, "unknown")

        # Assert
        # Check that update_data was called with location=None
        state_machine.update_data.assert_called_once()
        call_args = state_machine.update_data.call_args[0]
        assert call_args[1]["location"] is None

    @pytest.mark.asyncio
    async def test_checking_location_executes_query_with_handler(self) -> None:
        """Test checking location executes query when handler is available."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.CHECKING_LOCATION,
            data={
                "category": ItemCategory.BICYCLE,
                "description": "Red Trek 820",
                "brand_model": "Trek 820",
            },
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        parser.parse_location_text = MagicMock(return_value="Main Street")

        # Mock check handler
        check_handler = AsyncMock()
        check_handler.handle = AsyncMock(return_value=CheckIfStolenResult(matches=[]))

        response_builder = ResponseBuilder()
        error_handler = ErrorHandler()
        router = MessageRouter(
            state_machine,
            parser,
            response_builder=response_builder,
            check_if_stolen_handler=check_handler,
            error_handler=error_handler,
        )

        # Act
        response = await router.route_message(phone_number, "Main Street")

        # Assert
        check_handler.handle.assert_called_once()
        assert "no stolen items found" in response["reply"].lower()
        assert response["state"] == ConversationState.COMPLETE.value

    @pytest.mark.asyncio
    async def test_checking_location_returns_matches_when_found(self) -> None:
        """Test checking location returns match count when items found."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.CHECKING_LOCATION,
            data={
                "category": ItemCategory.BICYCLE,
                "description": "Red Trek 820",
            },
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        parser.parse_location_text = MagicMock(return_value="Downtown")

        # Mock check handler with matches
        mock_match = MagicMock()
        check_handler = AsyncMock()
        check_handler.handle = AsyncMock(
            return_value=CheckIfStolenResult(matches=[mock_match, mock_match])
        )

        response_builder = ResponseBuilder()
        router = MessageRouter(
            state_machine,
            parser,
            response_builder=response_builder,
            check_if_stolen_handler=check_handler,
        )

        # Act
        response = await router.route_message(phone_number, "Downtown")

        # Assert
        assert "found 2 potential" in response["reply"].lower()
        assert response["state"] == ConversationState.COMPLETE.value

    @pytest.mark.asyncio
    async def test_checking_location_handles_query_error(self) -> None:
        """Test checking location handles errors from query handler."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.CHECKING_LOCATION,
            data={
                "category": ItemCategory.PHONE,
                "description": "iPhone 13",
            },
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        parser.parse_location_text = MagicMock(return_value="Downtown")

        # Mock check handler that raises error
        check_handler = AsyncMock()
        check_handler.handle = AsyncMock(
            side_effect=RepositoryError("Database connection failed")
        )

        error_handler = ErrorHandler()
        response_builder = ResponseBuilder()
        router = MessageRouter(
            state_machine,
            parser,
            response_builder=response_builder,
            check_if_stolen_handler=check_handler,
            error_handler=error_handler,
        )

        # Act
        response = await router.route_message(phone_number, "Downtown")

        # Assert
        assert "temporary problem" in response["reply"].lower()
        assert response["state"] == ConversationState.COMPLETE.value

    @pytest.mark.asyncio
    async def test_reporting_location_executes_command_with_handler(self) -> None:
        """Test reporting location executes command when handler is available."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.REPORTING_LOCATION,
            data={
                "category": ItemCategory.PHONE,
                "description": "Black iPhone 13 Pro",
                "brand_model": "iPhone 13",
            },
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        parser.parse_location_text = MagicMock(return_value="Downtown")

        # Mock report handler
        report_handler = AsyncMock()
        item_id = uuid4()
        report_handler.handle = AsyncMock(return_value=item_id)

        response_builder = ResponseBuilder()
        error_handler = ErrorHandler()
        router = MessageRouter(
            state_machine,
            parser,
            response_builder=response_builder,
            report_stolen_item_handler=report_handler,
            error_handler=error_handler,
        )

        # Act
        response = await router.route_message(phone_number, "Downtown")

        # Assert
        report_handler.handle.assert_called_once()
        assert "thank you" in response["reply"].lower()
        assert response["state"] == ConversationState.COMPLETE.value

    @pytest.mark.asyncio
    async def test_reporting_location_handles_command_error(self) -> None:
        """Test reporting location handles errors from command handler."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.REPORTING_LOCATION,
            data={
                "category": ItemCategory.BICYCLE,
                "description": "Red Trek 820",
            },
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        parser.parse_location_text = MagicMock(return_value="Main Street")

        # Mock report handler that raises error
        report_handler = AsyncMock()
        report_handler.handle = AsyncMock(
            side_effect=ItemNotFoundError("Item not found")
        )

        error_handler = ErrorHandler()
        response_builder = ResponseBuilder()
        router = MessageRouter(
            state_machine,
            parser,
            response_builder=response_builder,
            report_stolen_item_handler=report_handler,
            error_handler=error_handler,
        )

        # Act
        response = await router.route_message(phone_number, "Main Street")

        # Assert
        assert "doesn't exist" in response["reply"].lower()
        assert response["state"] == ConversationState.COMPLETE.value

    @pytest.mark.asyncio
    async def test_build_check_query_with_all_fields(self) -> None:
        """Test building CheckIfStolenQuery with all fields populated."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.CHECKING_LOCATION,
            data={
                "category": ItemCategory.BICYCLE,
                "description": "Red Trek 820 mountain bike",
                "brand_model": "Trek 820",
                "location": "Main Street, London",
            },
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        parser.parse_location_text = MagicMock(return_value="Main Street, London")

        # Mock check handler to capture query
        check_handler = AsyncMock()
        captured_query: CheckIfStolenQuery | None = None

        async def capture_query(query: CheckIfStolenQuery) -> CheckIfStolenResult:
            nonlocal captured_query
            captured_query = query
            return CheckIfStolenResult(matches=[])

        check_handler.handle = capture_query

        router = MessageRouter(
            state_machine,
            parser,
            check_if_stolen_handler=check_handler,
        )

        # Act
        await router.route_message(phone_number, "Main Street, London")

        # Assert
        assert captured_query is not None
        assert captured_query.description == "Red Trek 820 mountain bike"
        assert captured_query.brand == "Trek 820"
        assert str(captured_query.category) == str(ItemCategory.BICYCLE)
        # Location coordinates are None (geocoding not implemented yet)
        assert captured_query.latitude is None
        assert captured_query.longitude is None

    @pytest.mark.asyncio
    async def test_build_report_command_with_all_fields(self) -> None:
        """Test building ReportStolenItemCommand with all fields populated."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.REPORTING_LOCATION,
            data={
                "category": ItemCategory.PHONE,
                "description": "Black iPhone 13 Pro Max 256GB",
                "brand_model": "iPhone 13 Pro Max",
                "location": "Downtown Shopping Center",
            },
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        parser.parse_location_text = MagicMock(return_value="Downtown Shopping Center")

        # Mock report handler to capture command
        report_handler = AsyncMock()
        captured_command: ReportStolenItemCommand | None = None

        async def capture_command(command: ReportStolenItemCommand) -> UUID:
            nonlocal captured_command
            captured_command = command
            return uuid4()

        report_handler.handle = capture_command

        router = MessageRouter(
            state_machine,
            parser,
            report_stolen_item_handler=report_handler,
        )

        # Act
        await router.route_message(phone_number, "Downtown Shopping Center")

        # Assert
        assert captured_command is not None
        assert captured_command.reporter_phone == phone_number
        assert captured_command.description == "Black iPhone 13 Pro Max 256GB"
        assert captured_command.brand == "iPhone 13 Pro Max"
        assert str(captured_command.item_type) == str(ItemCategory.PHONE)
        # Location coordinates are placeholder (geocoding not implemented yet)
        assert captured_command.latitude == 0.0
        assert captured_command.longitude == 0.0
        assert captured_command.stolen_date is not None

    @pytest.mark.asyncio
    async def test_build_check_query_with_geocoding_service(self) -> None:
        """Test building CheckIfStolenQuery with geocoding service converts location."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.CHECKING_LOCATION,
            data={
                "category": ItemCategory.BICYCLE,
                "description": "Red Trek 820",
                "location": "London",
            },
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        parser.parse_location_text = MagicMock(return_value="London")

        # Mock geocoding service
        from src.infrastructure.geocoding.geocoding_service import GeocodingResult

        geocoding_service = AsyncMock()
        geocoding_service.geocode = AsyncMock(
            return_value=GeocodingResult(
                latitude=51.5074,
                longitude=-0.1278,
                display_name="London, UK",
                raw_response={},
            )
        )

        # Mock check handler to capture query
        check_handler = AsyncMock()
        captured_query: CheckIfStolenQuery | None = None

        async def capture_query(query: CheckIfStolenQuery) -> CheckIfStolenResult:
            nonlocal captured_query
            captured_query = query
            return CheckIfStolenResult(matches=[])

        check_handler.handle = capture_query

        router = MessageRouter(
            state_machine,
            parser,
            check_if_stolen_handler=check_handler,
            geocoding_service=geocoding_service,
        )

        # Act
        await router.route_message(phone_number, "London")

        # Assert
        assert captured_query is not None
        assert captured_query.latitude == 51.5074
        assert captured_query.longitude == -0.1278
        geocoding_service.geocode.assert_called_once_with("London")

    @pytest.mark.asyncio
    async def test_build_report_command_with_geocoding_service(self) -> None:
        """Test building ReportStolenItemCommand with geocoding service converts location."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.REPORTING_LOCATION,
            data={
                "category": ItemCategory.PHONE,
                "description": "iPhone 13",
                "location": "Paris",
            },
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        parser.parse_location_text = MagicMock(return_value="Paris")

        # Mock geocoding service
        from src.infrastructure.geocoding.geocoding_service import GeocodingResult

        geocoding_service = AsyncMock()
        geocoding_service.geocode = AsyncMock(
            return_value=GeocodingResult(
                latitude=48.8566,
                longitude=2.3522,
                display_name="Paris, France",
                raw_response={},
            )
        )

        # Mock report handler to capture command
        report_handler = AsyncMock()
        captured_command: ReportStolenItemCommand | None = None

        async def capture_command(command: ReportStolenItemCommand) -> UUID:
            nonlocal captured_command
            captured_command = command
            return uuid4()

        report_handler.handle = capture_command

        router = MessageRouter(
            state_machine,
            parser,
            report_stolen_item_handler=report_handler,
            geocoding_service=geocoding_service,
        )

        # Act
        await router.route_message(phone_number, "Paris")

        # Assert
        assert captured_command is not None
        assert captured_command.latitude == 48.8566
        assert captured_command.longitude == 2.3522
        geocoding_service.geocode.assert_called_once_with("Paris")

    @pytest.mark.asyncio
    async def test_geocode_location_handles_exceptions_gracefully(self) -> None:
        """Test _geocode_location handles exceptions and returns None."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.CHECKING_LOCATION,
            data={
                "category": ItemCategory.BICYCLE,
                "description": "Red Trek 820",
                "location": "Invalid Location",
            },
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        parser.parse_location_text = MagicMock(return_value="Invalid Location")

        # Mock geocoding service that raises exception
        geocoding_service = AsyncMock()
        geocoding_service.geocode = AsyncMock(
            side_effect=Exception("Geocoding service error")
        )

        # Mock check handler to capture query
        check_handler = AsyncMock()
        captured_query: CheckIfStolenQuery | None = None

        async def capture_query(query: CheckIfStolenQuery) -> CheckIfStolenResult:
            nonlocal captured_query
            captured_query = query
            return CheckIfStolenResult(matches=[])

        check_handler.handle = capture_query

        router = MessageRouter(
            state_machine,
            parser,
            check_if_stolen_handler=check_handler,
            geocoding_service=geocoding_service,
        )

        # Act
        await router.route_message(phone_number, "Invalid Location")

        # Assert - should still process without coordinates
        assert captured_query is not None
        assert captured_query.latitude is None
        assert captured_query.longitude is None
        geocoding_service.geocode.assert_called_once_with("Invalid Location")

    @pytest.mark.asyncio
    async def test_geocode_location_returns_none_when_no_result(self) -> None:
        """Test _geocode_location handles None result from geocoding service."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.REPORTING_LOCATION,
            data={
                "category": ItemCategory.BICYCLE,
                "description": "Red Trek 820",
                "location": "Unknown Place",
            },
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        parser.parse_location_text = MagicMock(return_value="Unknown Place")

        # Mock geocoding service that returns None
        geocoding_service = AsyncMock()
        geocoding_service.geocode = AsyncMock(return_value=None)

        # Mock report handler to capture command
        report_handler = AsyncMock()
        captured_command: ReportStolenItemCommand | None = None

        async def capture_command(command: ReportStolenItemCommand) -> UUID:
            nonlocal captured_command
            captured_command = command
            return uuid4()

        report_handler.handle = capture_command

        router = MessageRouter(
            state_machine,
            parser,
            report_stolen_item_handler=report_handler,
            geocoding_service=geocoding_service,
        )

        # Act
        await router.route_message(phone_number, "Unknown Place")

        # Assert - should use default coordinates
        assert captured_command is not None
        assert captured_command.latitude == 0.0
        assert captured_command.longitude == 0.0
        geocoding_service.geocode.assert_called_once_with("Unknown Place")

    @pytest.mark.asyncio
    async def test_geocode_location_returns_none_when_no_service(self) -> None:
        """Test _geocode_location returns None when geocoding service is not provided."""
        # Arrange
        phone_number = "+1234567890"
        context = ConversationContext(
            phone_number=phone_number,
            state=ConversationState.CHECKING_LOCATION,
            data={
                "category": ItemCategory.BICYCLE,
                "description": "Red Trek 820",
                "location": "London",
            },
        )
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(return_value=context)
        state_machine.update_data = AsyncMock(return_value=context)
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        parser.parse_location_text = MagicMock(return_value="London")

        # Mock check handler to capture query
        check_handler = AsyncMock()
        captured_query: CheckIfStolenQuery | None = None

        async def capture_query(query: CheckIfStolenQuery) -> CheckIfStolenResult:
            nonlocal captured_query
            captured_query = query
            return CheckIfStolenResult(matches=[])

        check_handler.handle = capture_query

        # Create router WITHOUT geocoding service
        router = MessageRouter(
            state_machine,
            parser,
            check_if_stolen_handler=check_handler,
            geocoding_service=None,  # No geocoding service
        )

        # Act
        await router.route_message(phone_number, "London")

        # Assert - should not have coordinates
        assert captured_query is not None
        assert captured_query.latitude is None
        assert captured_query.longitude is None

    @pytest.mark.asyncio
    async def test_geocode_location_method_returns_none_without_service(
        self,
    ) -> None:
        """Test _geocode_location method directly when service is None."""
        # Arrange
        state_machine = MagicMock()
        parser = MagicMock()

        # Create router WITHOUT geocoding service
        router = MessageRouter(
            state_machine,
            parser,
            geocoding_service=None,
        )

        # Act - call private method directly
        result = await router._geocode_location("London")

        # Assert
        assert result is None
