"""
RouterPrimitive - LLM request routing workflow primitive.

Routes LLM requests to optimal provider (cheap vs premium model) based on
query complexity and length. Tracks cost savings from intelligent routing.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from tta_dev_primitives.core.base import (
    WorkflowContext,
    WorkflowPrimitive,
)

from ..apm_setup import get_meter

logger = logging.getLogger(__name__)


class RouterPrimitive(WorkflowPrimitive[Any, Any]):
    """
    Route requests to optimal LLM provider based on routing strategy.

    Enables cost optimization by routing simple requests to cheaper models
    and complex requests to premium models. Tracks all routing decisions
    and measures cost savings.

    Example:
        >>> from observability_integration.primitives import RouterPrimitive
        >>>
        >>> # Define routes
        >>> routes = {
        ...     "fast": LocalLLMPrimitive(),  # Cheap, fast
        ...     "premium": GPT4Primitive(),  # Expensive, high quality
        ... }
        >>>
        >>> # Define routing logic
        >>> def route_by_complexity(data, context):
        ...     tokens = len(data.get("prompt", "").split())
        ...     return "premium" if tokens > 100 else "fast"
        >>>
        >>> # Create router
        >>> router = RouterPrimitive(
        ...     routes=routes, router_fn=route_by_complexity, default_route="fast"
        ... )
        >>>
        >>> # Use in workflow
        >>> result = await router.execute({"prompt": "Hi"}, context)

    Metrics:
        - router_decisions_total{route, reason}: Total routing decisions
        - router_execution_seconds{route}: Execution time per route
        - router_cost_savings_usd{route}: Estimated cost savings
        - router_errors_total{route}: Routing errors
    """

    def __init__(
        self,
        routes: dict[str, WorkflowPrimitive],
        router_fn: Callable[[Any, WorkflowContext], str],
        default_route: str = "fast",
        cost_per_route: dict[str, float] | None = None,
    ):
        """
        Initialize router with available routes and routing function.

        Args:
            routes: Map of route name to primitive implementation
            router_fn: Function to select route (returns route name)
            default_route: Fallback route if router_fn fails
            cost_per_route: Optional cost per 1K tokens for each route
                           (for cost savings calculation)

        Raises:
            ValueError: If routes empty or default_route not in routes
        """
        if not routes:
            raise ValueError("Routes cannot be empty")
        if default_route not in routes:
            raise ValueError(f"Default route '{default_route}' not in routes")

        self.routes = routes
        self.router_fn = router_fn
        self.default_route = default_route
        self.cost_per_route = cost_per_route or {}

        # Initialize metrics (gracefully handles meter=None)
        meter = get_meter(__name__)
        if meter:
            self._decisions_counter = meter.create_counter(
                name="router_decisions_total",
                description="Total number of routing decisions",
                unit="1",
            )
            self._execution_histogram = meter.create_histogram(
                name="router_execution_seconds",
                description="Router execution time",
                unit="s",
            )
            self._cost_savings_counter = meter.create_counter(
                name="router_cost_savings_usd",
                description="Estimated cost savings from routing",
                unit="USD",
            )
            self._errors_counter = meter.create_counter(
                name="router_errors_total",
                description="Router errors",
                unit="1",
            )
        else:
            self._decisions_counter = None
            self._execution_histogram = None
            self._cost_savings_counter = None
            self._errors_counter = None

        logger.info(
            f"RouterPrimitive initialized with {len(routes)} routes: {list(routes.keys())}"
        )

    async def execute(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute routing decision and delegate to selected primitive.

        Args:
            input_data: Input data for the workflow
            context: Workflow execution context

        Returns:
            Result from the selected route's primitive

        Raises:
            Exception: Any exception from the routed primitive
        """
        start_time = time.time()
        selected_route = self.default_route

        try:
            # Execute routing function
            try:
                selected_route = self.router_fn(input_data, context)
                routing_reason = "routing_function"

                # Validate route exists
                if selected_route not in self.routes:
                    logger.warning(
                        f"Router returned invalid route '{selected_route}', "
                        f"using default '{self.default_route}'"
                    )
                    selected_route = self.default_route
                    routing_reason = "invalid_route_fallback"

            except Exception as e:
                logger.warning(
                    f"Routing function failed: {e}, using default route", exc_info=True
                )
                selected_route = self.default_route
                routing_reason = "routing_error_fallback"

                if self._errors_counter:
                    self._errors_counter.add(
                        1, {"route": selected_route, "error_type": type(e).__name__}
                    )

            # Record routing decision
            if self._decisions_counter:
                self._decisions_counter.add(
                    1, {"route": selected_route, "reason": routing_reason}
                )

            logger.info(f"Routing to '{selected_route}' (reason: {routing_reason})")

            # Execute selected route
            primitive = self.routes[selected_route]
            result = await primitive.execute(input_data, context)

            # Calculate and record cost savings
            # (comparing selected route cost to most expensive route)
            if self.cost_per_route and self._cost_savings_counter:
                selected_cost = self.cost_per_route.get(selected_route, 0.0)
                max_cost = max(self.cost_per_route.values())
                savings = max_cost - selected_cost

                if savings > 0:
                    self._cost_savings_counter.add(savings, {"route": selected_route})

            return result

        finally:
            # Record execution time
            duration = time.time() - start_time
            if self._execution_histogram:
                self._execution_histogram.record(duration, {"route": selected_route})

    def __repr__(self) -> str:
        """String representation of router."""
        return f"RouterPrimitive(routes={list(self.routes.keys())}, default='{self.default_route}')"
