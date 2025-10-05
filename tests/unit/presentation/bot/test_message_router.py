"""Tests for message router."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.value_objects.item_category import ItemCategory
from src.presentation.bot.context import ConversationContext
from src.presentation.bot.message_router import MessageRouter
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
