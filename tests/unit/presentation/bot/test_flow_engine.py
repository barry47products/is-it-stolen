"""Tests for flow execution engine."""

from pathlib import Path

import pytest

from src.infrastructure.config.flow_config_loader import FlowConfigLoader
from src.infrastructure.handlers.handler_registry import HandlerRegistry
from src.presentation.bot.flow_engine import FlowEngine


# Mock handler for testing
class MockCheckHandler:
    """Mock handler for check flow."""

    async def handle(self, query: dict) -> dict:  # type: ignore
        """Handle check query."""
        return {"result": "found", "matches": 2}


@pytest.mark.unit
class TestFlowEngine:
    """Test flow execution engine."""

    def test_initializes_with_config_and_registry(self, tmp_path: Path) -> None:
        """Test flow engine initialization."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text(
            """
flows:
  test_flow:
    name: "Test Flow"
    initial_step: "start"
    steps:
      start:
        prompt: "Hello"
"""
        )

        loader = FlowConfigLoader(config_file)
        config = loader.load()
        registry = HandlerRegistry()

        # Act
        engine = FlowEngine(config, registry)

        # Assert
        assert engine._config == config
        assert engine._handler_registry == registry

    @pytest.mark.asyncio
    async def test_starts_flow_at_initial_step(self, tmp_path: Path) -> None:
        """Test starting a flow creates context at initial step."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text(
            """
flows:
  test_flow:
    name: "Test Flow"
    initial_step: "category"
    steps:
      category:
        prompt: "What category?"
        prompt_type: "list"
        next: "done"
      done:
        handler: "test_handler"
        handler_type: "query"
"""
        )

        loader = FlowConfigLoader(config_file)
        config = loader.load()
        engine = FlowEngine(config, HandlerRegistry())

        # Act
        context = await engine.start_flow("test_flow", user_id="user123")

        # Assert
        assert context.flow_id == "test_flow"
        assert context.current_step == "category"
        assert context.user_id == "user123"
        assert context.data == {}

    @pytest.mark.asyncio
    async def test_get_prompt_returns_step_prompt(self, tmp_path: Path) -> None:
        """Test getting prompt for current step."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text(
            """
flows:
  test_flow:
    name: "Test Flow"
    initial_step: "category"
    steps:
      category:
        prompt: "What type of item?"
        prompt_type: "list"
"""
        )

        loader = FlowConfigLoader(config_file)
        config = loader.load()
        engine = FlowEngine(config, HandlerRegistry())
        context = await engine.start_flow("test_flow", user_id="user123")

        # Act
        prompt = engine.get_prompt(context)

        # Assert
        assert prompt == "What type of item?"

    @pytest.mark.asyncio
    async def test_process_input_stores_data_and_advances(self, tmp_path: Path) -> None:
        """Test processing input stores data and advances to next step."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text(
            """
flows:
  test_flow:
    name: "Test Flow"
    initial_step: "category"
    steps:
      category:
        prompt: "Category?"
        next: "description"
      description:
        prompt: "Description?"
"""
        )

        loader = FlowConfigLoader(config_file)
        config = loader.load()
        engine = FlowEngine(config, HandlerRegistry())
        context = await engine.start_flow("test_flow", user_id="user123")

        # Act
        new_context = await engine.process_input(context, "bicycle")

        # Assert
        assert new_context.current_step == "description"
        assert new_context.data["category"] == "bicycle"

    @pytest.mark.asyncio
    async def test_calls_handler_on_terminal_step(self, tmp_path: Path) -> None:
        """Test calling handler when reaching terminal step."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text(
            """
flows:
  test_flow:
    name: "Test Flow"
    initial_step: "category"
    steps:
      category:
        prompt: "Category?"
        next: "execute"
      execute:
        handler: "test_handler"
        handler_type: "query"
"""
        )

        loader = FlowConfigLoader(config_file)
        config = loader.load()

        registry = HandlerRegistry()
        registry.register_handler("test_handler", MockCheckHandler)

        engine = FlowEngine(config, registry)
        context = await engine.start_flow("test_flow", user_id="user123")

        # Act - provide category and advance to terminal step
        context = await engine.process_input(context, "bicycle")

        # Assert
        assert context.is_complete
        assert context.result == {"result": "found", "matches": 2}

    @pytest.mark.asyncio
    async def test_raises_error_for_unknown_flow(self, tmp_path: Path) -> None:
        """Test error when starting unknown flow."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text(
            """
flows:
  test_flow:
    name: "Test Flow"
    initial_step: "start"
    steps:
      start:
        prompt: "Start"
"""
        )

        loader = FlowConfigLoader(config_file)
        config = loader.load()
        engine = FlowEngine(config, HandlerRegistry())

        # Act & Assert
        with pytest.raises(ValueError, match="Flow 'unknown' not found"):
            await engine.start_flow("unknown", user_id="user123")

    @pytest.mark.asyncio
    async def test_is_complete_returns_false_for_non_terminal_steps(
        self, tmp_path: Path
    ) -> None:
        """Test is_complete returns False for non-terminal steps."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text(
            """
flows:
  test_flow:
    name: "Test Flow"
    initial_step: "category"
    steps:
      category:
        prompt: "Category?"
        next: "description"
      description:
        prompt: "Description?"
"""
        )

        loader = FlowConfigLoader(config_file)
        config = loader.load()
        engine = FlowEngine(config, HandlerRegistry())
        context = await engine.start_flow("test_flow", user_id="user123")

        # Act & Assert
        assert not context.is_complete

    @pytest.mark.asyncio
    async def test_builds_handler_params_from_collected_data(
        self, tmp_path: Path
    ) -> None:
        """Test handler receives collected data as parameters."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text(
            """
flows:
  test_flow:
    name: "Test Flow"
    initial_step: "category"
    steps:
      category:
        prompt: "Category?"
        next: "description"
      description:
        prompt: "Description?"
        next: "execute"
      execute:
        handler: "test_handler"
        handler_type: "query"
"""
        )

        loader = FlowConfigLoader(config_file)
        config = loader.load()

        # Track what parameters handler received
        received_params = {}

        class ParamCaptureHandler:
            async def handle(self, query: dict) -> dict:  # type: ignore
                received_params.update(query)
                return {"result": "ok"}

        registry = HandlerRegistry()
        registry.register_handler("test_handler", ParamCaptureHandler)

        engine = FlowEngine(config, registry)
        context = await engine.start_flow("test_flow", user_id="user123")

        # Act - collect data and execute
        context = await engine.process_input(context, "bicycle")
        context = await engine.process_input(context, "red mountain bike")

        # Assert
        assert received_params["category"] == "bicycle"
        assert received_params["description"] == "red mountain bike"

    @pytest.mark.asyncio
    async def test_completes_flow_when_current_step_has_handler(
        self, tmp_path: Path
    ) -> None:
        """Test flow completes when current step itself has a handler."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text(
            """
flows:
  test_flow:
    name: "Test Flow"
    initial_step: "execute"
    steps:
      execute:
        prompt: "Ready to execute?"
        handler: "test_handler"
        handler_type: "query"
"""
        )

        loader = FlowConfigLoader(config_file)
        config = loader.load()

        registry = HandlerRegistry()
        registry.register_handler("test_handler", MockCheckHandler)

        engine = FlowEngine(config, registry)
        context = await engine.start_flow("test_flow", user_id="user123")

        # Act - provide input on current step with handler
        context = await engine.process_input(context, "yes")

        # Assert
        assert context.is_complete
        assert context.result == {"result": "found", "matches": 2}
        assert context.data["execute"] == "yes"

    @pytest.mark.asyncio
    async def test_completes_flow_when_terminal_step_has_no_handler(
        self, tmp_path: Path
    ) -> None:
        """Test flow completes gracefully when terminal step has no handler."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text(
            """
flows:
  test_flow:
    name: "Test Flow"
    initial_step: "category"
    steps:
      category:
        prompt: "Category?"
        next: "done"
      done:
        prompt: "All done!"
"""
        )

        loader = FlowConfigLoader(config_file)
        config = loader.load()
        engine = FlowEngine(config, HandlerRegistry())
        context = await engine.start_flow("test_flow", user_id="user123")

        # Act - advance to terminal step without handler
        context = await engine.process_input(context, "bicycle")

        # Assert
        assert context.current_step == "done"
        assert context.data["category"] == "bicycle"
        assert not context.is_complete  # Not complete yet

        # Act - process final input on terminal step
        context = await engine.process_input(context, "ok")

        # Assert
        assert context.is_complete
        assert context.result is None
        assert context.data["done"] == "ok"
