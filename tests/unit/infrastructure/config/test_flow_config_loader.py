"""Tests for flow configuration loader."""

from pathlib import Path

import pytest

from src.infrastructure.config.flow_config_loader import FlowConfigLoader


@pytest.mark.unit
class TestFlowConfigLoader:
    """Test flow configuration loader."""

    def test_loads_valid_flow_configuration(self, tmp_path: Path) -> None:
        """Test loading valid flow configuration from YAML."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text("""
flows:
  check_item:
    name: "Check if Stolen"
    description: "Check if an item is reported as stolen"
    initial_step: "category"
    steps:
      category:
        prompt: "What type of item?"
        prompt_type: "list"
        next: "description"
      description:
        prompt: "Describe the item"
        prompt_type: "text"
        next: "location"
      location:
        prompt: "Where was it last seen?"
        prompt_type: "text"
        next: "complete"
      complete:
        handler: "check_if_stolen"
        handler_type: "query"
""")

        loader = FlowConfigLoader(config_path=config_file)

        # Act
        config = loader.load()

        # Assert
        assert "check_item" in config.flows
        flow = config.flows["check_item"]
        assert flow.name == "Check if Stolen"
        assert flow.initial_step == "category"
        assert len(flow.steps) == 4
        assert "category" in flow.steps
        assert flow.steps["category"].prompt == "What type of item?"
        assert flow.steps["category"].prompt_type == "list"
        assert flow.steps["category"].next == "description"

    def test_validation_catches_missing_initial_step(self, tmp_path: Path) -> None:
        """Test validation catches when initial_step doesn't exist."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text("""
flows:
  test_flow:
    name: "Test"
    initial_step: "nonexistent"
    steps:
      category:
        prompt: "Category?"
        next: "complete"
""")

        loader = FlowConfigLoader(config_path=config_file)

        # Act & Assert
        with pytest.raises(ValueError, match=r"Initial step.*not found"):
            loader.load()

    def test_validation_catches_invalid_step_reference(self, tmp_path: Path) -> None:
        """Test validation catches when step references non-existent next step."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text("""
flows:
  test_flow:
    name: "Test"
    initial_step: "start"
    steps:
      start:
        prompt: "Start"
        next: "nonexistent"
""")

        loader = FlowConfigLoader(config_path=config_file)

        # Act & Assert
        with pytest.raises(ValueError, match="references non-existent step"):
            loader.load()

    def test_validation_catches_circular_dependencies(self, tmp_path: Path) -> None:
        """Test validation catches circular step dependencies."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text("""
flows:
  test_flow:
    name: "Test"
    initial_step: "step1"
    steps:
      step1:
        prompt: "Step 1"
        next: "step2"
      step2:
        prompt: "Step 2"
        next: "step1"
""")

        loader = FlowConfigLoader(config_path=config_file)

        # Act & Assert
        with pytest.raises(ValueError, match="Circular dependency detected"):
            loader.load()

    def test_handles_malformed_yaml(self, tmp_path: Path) -> None:
        """Test error handling for malformed YAML."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text("""
flows:
  test_flow:
    name: "Test
    missing_quote: here
""")

        loader = FlowConfigLoader(config_path=config_file)

        # Act & Assert
        with pytest.raises(ValueError, match="Failed to parse"):
            loader.load()

    def test_validates_required_fields(self, tmp_path: Path) -> None:
        """Test validation catches missing required fields."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text("""
flows:
  test_flow:
    initial_step: "start"
    steps:
      start:
        prompt: "Start"
""")

        loader = FlowConfigLoader(config_path=config_file)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid configuration structure"):
            loader.load()

    def test_loads_multiple_flows(self, tmp_path: Path) -> None:
        """Test loading configuration with multiple flows."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text("""
flows:
  check_item:
    name: "Check"
    initial_step: "start"
    steps:
      start:
        prompt: "Start"
  report_item:
    name: "Report"
    initial_step: "start"
    steps:
      start:
        prompt: "Start"
""")

        loader = FlowConfigLoader(config_path=config_file)

        # Act
        config = loader.load()

        # Assert
        assert len(config.flows) == 2
        assert "check_item" in config.flows
        assert "report_item" in config.flows

    def test_validates_prompt_type(self, tmp_path: Path) -> None:
        """Test validation catches invalid prompt_type."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text("""
flows:
  test_flow:
    name: "Test"
    initial_step: "start"
    steps:
      start:
        prompt: "Start"
        prompt_type: "invalid"
""")

        loader = FlowConfigLoader(config_path=config_file)

        # Act & Assert
        with pytest.raises(ValueError, match="prompt_type must be one of"):
            loader.load()

    def test_validates_handler_type(self, tmp_path: Path) -> None:
        """Test validation catches invalid handler_type."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text("""
flows:
  test_flow:
    name: "Test"
    initial_step: "start"
    steps:
      start:
        handler: "test_handler"
        handler_type: "invalid"
""")

        loader = FlowConfigLoader(config_path=config_file)

        # Act & Assert
        with pytest.raises(ValueError, match="handler_type must be one of"):
            loader.load()

    def test_handles_file_not_found(self) -> None:
        """Test error handling when config file doesn't exist."""
        # Arrange
        loader = FlowConfigLoader(config_path="/nonexistent/file.yaml")

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            loader.load()

    def test_validates_non_dict_yaml(self, tmp_path: Path) -> None:
        """Test validation catches YAML that isn't a dictionary."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text("- item1\n- item2\n")

        loader = FlowConfigLoader(config_path=config_file)

        # Act & Assert
        with pytest.raises(ValueError, match="Configuration must be a YAML mapping"):
            loader.load()

    def test_allows_handler_without_handler_type(self, tmp_path: Path) -> None:
        """Test that handler_type can be None when handler is specified."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text("""
flows:
  test_flow:
    name: "Test"
    initial_step: "start"
    steps:
      start:
        handler: "test_handler"
""")

        loader = FlowConfigLoader(config_path=config_file)

        # Act
        config = loader.load()

        # Assert
        assert config.flows["test_flow"].steps["start"].handler == "test_handler"
        assert config.flows["test_flow"].steps["start"].handler_type is None

    def test_handles_diamond_dependency_pattern(self, tmp_path: Path) -> None:
        """Test that diamond dependency pattern (visited node) works correctly."""
        # Arrange
        config_file = tmp_path / "flows.yaml"
        config_file.write_text("""
flows:
  test_flow:
    name: "Test"
    initial_step: "start"
    steps:
      start:
        prompt: "Start"
        next: "branch_a"
      branch_a:
        prompt: "Branch A"
        next: "merge"
      branch_b:
        prompt: "Branch B"
        next: "merge"
      merge:
        prompt: "Merge"
""")

        loader = FlowConfigLoader(config_path=config_file)

        # Act
        config = loader.load()

        # Assert - should load successfully without circular dependency error
        assert "test_flow" in config.flows
        assert len(config.flows["test_flow"].steps) == 4
