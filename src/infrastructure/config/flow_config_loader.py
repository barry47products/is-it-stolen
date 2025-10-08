"""Flow configuration loader for YAML-based conversation flows."""

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

from src.domain.constants import HandlerType, PromptType

logger = logging.getLogger(__name__)


class FlowStep(BaseModel):
    """Configuration for a single step in a flow."""

    prompt: str | None = Field(default=None, description="Prompt message for this step")
    prompt_type: str = Field(
        default="text", description="Type of prompt (text, list, button)"
    )
    next: str | None = Field(default=None, description="Next step ID")
    handler: str | None = Field(default=None, description="Handler name for this step")
    handler_type: str | None = Field(
        default=None, description="Handler type (query, command)"
    )

    @field_validator("prompt_type")
    @classmethod
    def validate_prompt_type(cls, v: str) -> str:
        """Validate prompt type is one of allowed values."""
        allowed = {pt.value for pt in PromptType}
        if v not in allowed:
            raise ValueError(f"prompt_type must be one of {allowed}, got {v}")
        return v

    @field_validator("handler_type")
    @classmethod
    def validate_handler_type(cls, v: str | None) -> str | None:
        """Validate handler type is one of allowed values."""
        if v is None:  # pragma: no cover
            return v  # Pydantic calls validator even for None default
        allowed = {ht.value for ht in HandlerType}
        if v not in allowed:
            raise ValueError(f"handler_type must be one of {allowed}, got {v}")
        return v


class FlowTransition(BaseModel):
    """Configuration for a flow transition."""

    from_step: str = Field(..., description="Source step ID")
    to_step: str = Field(..., description="Target step ID")
    condition: str | None = Field(default=None, description="Transition condition")


class FlowConfig(BaseModel):
    """Configuration for a single conversation flow."""

    name: str = Field(..., description="Human-readable flow name")
    description: str | None = Field(default=None, description="Flow description")
    initial_step: str = Field(..., description="ID of the initial step")
    steps: dict[str, FlowStep] = Field(..., description="Flow steps by ID")

    def validate_references(self) -> None:
        """Validate all step references exist and no circular dependencies."""
        # Validate initial step exists
        if self.initial_step not in self.steps:
            raise ValueError(
                f"Initial step '{self.initial_step}' not found in steps: "
                f"{list(self.steps.keys())}"
            )

        # Validate all 'next' references exist
        for step_id, step in self.steps.items():
            if step.next is not None and step.next not in self.steps:
                raise ValueError(
                    f"Step '{step_id}' references non-existent step '{step.next}'"
                )

        # Check for circular dependencies
        self._check_circular_dependencies()

    def _check_circular_dependencies(self) -> None:
        """Check for circular dependencies in flow steps."""
        visited: set[str] = set()
        path: list[str] = []

        def visit(step_id: str) -> None:
            if step_id in path:
                cycle = " -> ".join([*path[path.index(step_id) :], step_id])
                raise ValueError(f"Circular dependency detected: {cycle}")

            if step_id in visited:  # pragma: no cover
                return  # Defensive: unreachable with single entry point traversal

            visited.add(step_id)
            path.append(step_id)

            step = self.steps[step_id]
            if step.next is not None:
                visit(step.next)

            path.pop()

        # Start from initial step
        visit(self.initial_step)


class FlowsConfig(BaseModel):
    """Configuration for all conversation flows."""

    flows: dict[str, FlowConfig] = Field(..., description="All flows by ID")

    def validate_all(self) -> None:
        """Validate all flows."""
        for flow_id, flow in self.flows.items():
            try:
                flow.validate_references()
            except ValueError as e:
                raise ValueError(f"Validation error in flow '{flow_id}': {e}") from e


class FlowConfigLoader:
    """Loader for YAML-based flow configurations."""

    def __init__(self, config_path: Path | str) -> None:
        """Initialize loader with path to configuration file.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)

    def load(self) -> FlowsConfig:
        """Load and validate flow configuration from YAML.

        Returns:
            Validated FlowsConfig instance

        Raises:
            ValueError: If configuration is invalid
            FileNotFoundError: If config file doesn't exist
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML: {e}") from e

        if not isinstance(data, dict):
            raise ValueError("Configuration must be a YAML mapping")

        try:
            config = FlowsConfig(**data)
        except Exception as e:
            raise ValueError(f"Invalid configuration structure: {e}") from e

        # Validate all flows
        config.validate_all()

        logger.info(f"Loaded {len(config.flows)} flows from {self.config_path}")
        return config
