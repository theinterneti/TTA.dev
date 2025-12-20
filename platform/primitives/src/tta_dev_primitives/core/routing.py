"""Routing primitive for intelligent workflow branching.

# See: [[TTA.dev/Primitives/RouterPrimitive]]
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..observability.logging import get_logger
from .base import WorkflowContext, WorkflowPrimitive

logger = get_logger(__name__)


class RouterPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Route input to appropriate primitive based on routing function.

    Enables intelligent routing decisions based on:
    - Cost optimization (route to cheaper providers)
    - Latency optimization (route to faster providers)
    - Load balancing (distribute across providers)
    - Feature requirements (route to capable providers)

    Example:
        ```python
        # Route based on user tier
        router = RouterPrimitive(
            routes={
                "openai": openai_primitive,
                "anthropic": anthropic_primitive,
                "local": local_llm_primitive
            },
            router_fn=lambda data, ctx: ctx.metadata.get("provider", "openai"),
            default="openai"
        )

        # Route based on complexity
        router = RouterPrimitive(
            routes={
                "simple": fast_local_model,
                "complex": premium_cloud_model
            },
            router_fn=lambda data, ctx: (
                "simple" if len(data.get("prompt", "")) < 100 else "complex"
            ),
            default="simple"
        )
        ```
    """

    def __init__(
        self,
        routes: dict[str, WorkflowPrimitive],
        router_fn: Callable[[Any, WorkflowContext], str],
        default: str | None = None,
    ) -> None:
        """
        Initialize router primitive.

        Args:
            routes: Map of route keys to primitives
            router_fn: Function to determine route from input/context
            default: Default route if router_fn returns unknown key
        """
        self.routes = routes
        self.router_fn = router_fn
        self.default = default

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute routing logic and invoke selected primitive.

        Args:
            input_data: Input data for routing decision
            context: Workflow context

        Returns:
            Output from selected primitive

        Raises:
            ValueError: If route key not found and no default specified
        """
        # Determine route
        route_key = self.router_fn(input_data, context)

        # Get primitive
        primitive = self.routes.get(route_key)

        # Fallback to default
        if not primitive and self.default:
            route_key = self.default
            primitive = self.routes.get(route_key)

        if not primitive:
            available = ", ".join(self.routes.keys())
            raise ValueError(f"No route found for key '{route_key}'. Available routes: {available}")

        # Log routing decision
        logger.info(
            "routing_decision",
            route=route_key,
            available_routes=list(self.routes.keys()),
            workflow_id=context.workflow_id,
        )

        # Store routing decision in context
        if "routing_history" not in context.state:
            context.state["routing_history"] = []
        context.state["routing_history"].append(route_key)

        # Execute selected primitive
        return await primitive.execute(input_data, context)
