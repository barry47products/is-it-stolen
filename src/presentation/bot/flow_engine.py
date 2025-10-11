"""Flow execution engine for configuration-driven conversational flows."""

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol

from src.infrastructure.config.flow_config_loader import FlowsConfig
from src.infrastructure.handlers.handler_registry import HandlerRegistry
from src.infrastructure.metrics.metrics_service import get_metrics_service

logger = logging.getLogger(__name__)


class Handler(Protocol):
    """Protocol for handlers that can be executed by the flow engine."""

    async def handle(self, query: dict[str, str]) -> dict[str, Any]:
        """Handle the query and return result.

        Args:
            query: Query parameters as key-value pairs

        Returns:
            Handler result
        """
        ...  # pragma: no cover


@dataclass
class FlowContext:
    """Context for tracking flow execution state."""

    flow_id: str
    user_id: str
    current_step: str
    data: dict[str, Any] = field(default_factory=dict)
    is_complete: bool = False
    result: dict[str, Any] | None = None


class FlowEngine:
    """Engine for executing configuration-driven conversational flows."""

    def __init__(self, config: FlowsConfig, handler_registry: HandlerRegistry) -> None:
        """Initialize flow engine.

        Args:
            config: Flow configurations
            handler_registry: Registry for handler lookup
        """
        self._config = config
        self._handler_registry = handler_registry

    def start_flow(self, flow_id: str, user_id: str) -> FlowContext:
        """Start a new flow execution.

        Args:
            flow_id: ID of flow to start
            user_id: User identifier

        Returns:
            New flow context at initial step

        Raises:
            ValueError: If flow not found
        """
        if flow_id not in self._config.flows:
            raise ValueError(f"Flow '{flow_id}' not found")

        flow = self._config.flows[flow_id]

        context = FlowContext(
            flow_id=flow_id,
            user_id=user_id,
            current_step=flow.initial_step,
            data={},
            is_complete=False,
            result=None,
        )

        # Track flow start for analytics
        metrics_service = get_metrics_service()
        metrics_service.track_flow_started(flow_id, "returning")

        logger.info(f"Started flow '{flow_id}' for user '{user_id}'")
        return context

    def get_prompt(self, context: FlowContext) -> str | None:
        """Get prompt for current step.

        Args:
            context: Current flow context

        Returns:
            Prompt text or None if terminal step
        """
        flow = self._config.flows[context.flow_id]
        step = flow.steps[context.current_step]
        return step.prompt

    async def process_input(self, context: FlowContext, user_input: str) -> FlowContext:
        """Process user input and advance flow.

        Args:
            context: Current flow context
            user_input: User's input

        Returns:
            Updated flow context
        """
        flow = self._config.flows[context.flow_id]
        current_step = flow.steps[context.current_step]
        metrics_service = get_metrics_service()

        # Track step completion
        metrics_service.track_step_completed(context.flow_id, context.current_step)

        # Store input data with step name as key
        context.data[context.current_step] = user_input

        # Check if this step has a next step
        if current_step.next:
            # Advance to next step
            context.current_step = current_step.next
            logger.debug(
                f"Advanced flow '{context.flow_id}' to step '{context.current_step}'"
            )

            # Check if the new step is a terminal handler step (no prompt, has handler)
            next_step = flow.steps[context.current_step]
            if next_step.handler and not next_step.prompt:
                # Auto-execute terminal handler step
                result = await self._execute_handler(context, next_step.handler)
                context.is_complete = True
                context.result = result
                # Track flow completion
                metrics_service.track_flow_completed(context.flow_id)
                logger.info(
                    f"Completed flow '{context.flow_id}' for user '{context.user_id}'"
                )
        elif current_step.handler:
            # Current step is terminal with handler - execute it
            result = await self._execute_handler(context, current_step.handler)
            context.is_complete = True
            context.result = result
            # Track flow completion
            metrics_service.track_flow_completed(context.flow_id)
            logger.info(
                f"Completed flow '{context.flow_id}' for user '{context.user_id}'"
            )
        else:
            # Terminal step without handler (unusual but handle gracefully)
            context.is_complete = True
            logger.info(
                f"Completed flow '{context.flow_id}' (no handler) for user '{context.user_id}'"
            )

        return context

    async def _execute_handler(
        self, context: FlowContext, handler_name: str
    ) -> dict[str, Any]:
        """Execute handler with collected data.

        Args:
            context: Flow context with collected data
            handler_name: Name of handler to execute

        Returns:
            Handler result
        """
        handler = self._handler_registry.get_handler(handler_name)

        # Pass all collected data as parameters
        result: dict[str, Any] = await handler.handle(context.data)

        logger.debug(f"Handler '{handler_name}' executed successfully")
        return result
