"""Tests for message router."""

from unittest.mock import AsyncMock, MagicMock

import pytest

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
        # Response should now be interactive buttons dict
        assert isinstance(response["reply"], dict)
        assert response["reply"]["type"] == "interactive"
        assert response["reply"]["interactive"]["type"] == "button"
        assert "welcome" in response["reply"]["interactive"]["body"]["text"].lower()
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
                state=ConversationState.ACTIVE_FLOW,
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
        # Response should now be interactive buttons dict
        assert isinstance(response["reply"], dict)
        assert response["reply"]["type"] == "interactive"
        assert "welcome" in response["reply"]["interactive"]["body"]["text"].lower()

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
    async def test_check_flow_starts_with_flow_engine(self) -> None:
        """Test check flow uses flow engine when check_item is selected."""
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
                state=ConversationState.ACTIVE_FLOW,
                data={"flow_id": "check_item"},
            )
        )
        state_machine.update_data = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.ACTIVE_FLOW,
                data={"flow_id": "check_item", "flow_context": MagicMock()},
            )
        )

        parser = MagicMock()
        flow_engine = MagicMock()
        flow_engine.start_flow = AsyncMock(
            return_value=MagicMock(
                flow_id="check_item",
                user_id=phone_number,
                current_step="category",
                data={},
                is_complete=False,
            )
        )
        flow_engine.get_prompt = MagicMock(
            return_value="What type of item would you like to check?"
        )

        router = MessageRouter(
            state_machine,
            parser,
            flow_engine=flow_engine,
        )

        # Act
        response = await router.route_message(phone_number, "check_item")

        # Assert
        assert response["state"] == "active_flow"
        flow_engine.start_flow.assert_called_once_with("check_item", phone_number)
        flow_engine.get_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_active_flow_processes_user_input(self) -> None:
        """Test ACTIVE_FLOW state processes user input through flow engine."""
        # Arrange
        phone_number = "+1234567890"
        flow_context = MagicMock(
            flow_id="check_item",
            user_id=phone_number,
            current_step="description",
            data={"category": "bicycle"},
            is_complete=False,
        )

        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.ACTIVE_FLOW,
                data={"flow_id": "check_item", "flow_context": flow_context},
            )
        )
        state_machine.update_data = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.ACTIVE_FLOW,
                data={"flow_id": "check_item", "flow_context": MagicMock()},
            )
        )

        parser = MagicMock()
        flow_engine = MagicMock()
        flow_engine.process_input = AsyncMock(
            return_value=MagicMock(
                flow_id="check_item",
                user_id=phone_number,
                current_step="location",
                data={"category": "bicycle", "description": "red mountain bike"},
                is_complete=False,
            )
        )
        flow_engine.get_prompt = MagicMock(return_value="Where was the item last seen?")

        router = MessageRouter(
            state_machine,
            parser,
            flow_engine=flow_engine,
        )

        # Act
        response = await router.route_message(phone_number, "red mountain bike")

        # Assert
        flow_engine.process_input.assert_called_once()
        assert "Where was the item last seen?" in response["reply"]
        assert response["state"] == "active_flow"

    @pytest.mark.asyncio
    async def test_active_flow_completes_and_returns_results(self) -> None:
        """Test ACTIVE_FLOW completes flow and returns handler results."""
        # Arrange
        phone_number = "+1234567890"
        flow_context = MagicMock(
            flow_id="check_item",
            user_id=phone_number,
            current_step="execute_search",
            data={"category": "bicycle", "description": "red mountain bike"},
            is_complete=False,
        )

        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.ACTIVE_FLOW,
                data={"flow_id": "check_item", "flow_context": flow_context},
            )
        )
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        flow_engine = MagicMock()
        flow_engine.process_input = AsyncMock(
            return_value=MagicMock(
                flow_id="check_item",
                user_id=phone_number,
                current_step="execute_search",
                data={
                    "category": "bicycle",
                    "description": "red mountain bike",
                    "location": "London",
                },
                is_complete=True,
                result={"matches": 2, "items": []},
            )
        )

        router = MessageRouter(
            state_machine,
            parser,
            flow_engine=flow_engine,
        )

        # Act
        response = await router.route_message(phone_number, "London")

        # Assert
        flow_engine.process_input.assert_called_once()
        state_machine.complete.assert_called_once()
        assert "matches" in str(response["reply"]) or isinstance(response["reply"], str)
        assert response["state"] == "complete"

    @pytest.mark.asyncio
    async def test_active_flow_without_flow_engine_falls_back_to_idle(self) -> None:
        """Test ACTIVE_FLOW without flow engine falls back to idle."""
        # Arrange
        phone_number = "+1234567890"
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.ACTIVE_FLOW,
            )
        )
        state_machine.transition = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.MAIN_MENU,
            )
        )

        parser = MagicMock()
        router = MessageRouter(
            state_machine,
            parser,
            flow_engine=None,  # No flow engine
        )

        # Act
        response = await router.route_message(phone_number, "test")

        # Assert
        state_machine.transition.assert_called_once()
        assert response["state"] == "main_menu"

    @pytest.mark.asyncio
    async def test_active_flow_without_flow_context_falls_back_to_idle(self) -> None:
        """Test ACTIVE_FLOW without flow context falls back to idle."""
        # Arrange
        phone_number = "+1234567890"
        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.ACTIVE_FLOW,
                data={},  # No flow_context
            )
        )
        state_machine.transition = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.MAIN_MENU,
            )
        )

        parser = MagicMock()
        flow_engine = MagicMock()
        router = MessageRouter(
            state_machine,
            parser,
            flow_engine=flow_engine,
        )

        # Act
        response = await router.route_message(phone_number, "test")

        # Assert
        state_machine.transition.assert_called_once()
        assert response["state"] == "main_menu"

    @pytest.mark.asyncio
    async def test_active_flow_completes_without_matches_in_result(self) -> None:
        """Test ACTIVE_FLOW completes with generic message when no matches key."""
        # Arrange
        phone_number = "+1234567890"
        flow_context = MagicMock(
            flow_id="check_item",
            user_id=phone_number,
            current_step="execute_search",
            data={"category": "bicycle"},
            is_complete=False,
        )

        state_machine = MagicMock()
        state_machine.get_or_create = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.ACTIVE_FLOW,
                data={"flow_id": "check_item", "flow_context": flow_context},
            )
        )
        state_machine.complete = AsyncMock()

        parser = MagicMock()
        flow_engine = MagicMock()
        flow_engine.process_input = AsyncMock(
            return_value=MagicMock(
                flow_id="check_item",
                user_id=phone_number,
                current_step="execute_search",
                data={"category": "bicycle"},
                is_complete=True,
                result={"status": "success"},  # No "matches" key
            )
        )

        router = MessageRouter(
            state_machine,
            parser,
            flow_engine=flow_engine,
        )

        # Act
        response = await router.route_message(phone_number, "test")

        # Assert
        assert "Flow completed successfully" in response["reply"]
        assert response["state"] == "complete"

    @pytest.mark.asyncio
    async def test_report_flow_starts_with_flow_engine(self) -> None:
        """Test report flow uses flow engine when report_item is selected."""
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
                state=ConversationState.ACTIVE_FLOW,
                data={"flow_id": "report_item"},
            )
        )
        state_machine.update_data = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.ACTIVE_FLOW,
                data={"flow_id": "report_item", "flow_context": MagicMock()},
            )
        )

        parser = MagicMock()
        flow_engine = MagicMock()
        flow_engine.start_flow = AsyncMock(
            return_value=MagicMock(
                flow_id="report_item",
                user_id=phone_number,
                current_step="category",
                data={},
                is_complete=False,
            )
        )
        flow_engine.get_prompt = MagicMock(return_value="What type of item was stolen?")

        router = MessageRouter(
            state_machine,
            parser,
            flow_engine=flow_engine,
        )

        # Act
        response = await router.route_message(phone_number, "report_item")

        # Assert
        assert response["state"] == "active_flow"
        flow_engine.start_flow.assert_called_once_with("report_item", phone_number)
        flow_engine.get_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_contact_us_flow_starts_with_flow_engine(self) -> None:
        """Test contact us flow uses flow engine when contact_us is selected."""
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
                state=ConversationState.ACTIVE_FLOW,
                data={"flow_id": "contact_us"},
            )
        )
        state_machine.update_data = AsyncMock(
            return_value=ConversationContext(
                phone_number=phone_number,
                state=ConversationState.ACTIVE_FLOW,
                data={"flow_id": "contact_us", "flow_context": MagicMock()},
            )
        )

        parser = MagicMock()
        flow_engine = MagicMock()
        flow_engine.start_flow = AsyncMock(
            return_value=MagicMock(
                flow_id="contact_us",
                user_id=phone_number,
                current_step="message",
                data={},
                is_complete=False,
            )
        )
        flow_engine.get_prompt = MagicMock(
            return_value="Please describe your issue or question"
        )

        router = MessageRouter(
            state_machine,
            parser,
            flow_engine=flow_engine,
        )

        # Act
        response = await router.route_message(phone_number, "contact_us")

        # Assert
        assert response["state"] == "active_flow"
        flow_engine.start_flow.assert_called_once_with("contact_us", phone_number)
        flow_engine.get_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_contact_us_without_flow_engine(self) -> None:
        """Test contact us without flow engine returns error message."""
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
        router = MessageRouter(state_machine, parser, flow_engine=None)

        # Act
        response = await router.route_message(phone_number, "3")

        # Assert
        assert response["state"] == "main_menu"
        assert "not available" in response["reply"]
