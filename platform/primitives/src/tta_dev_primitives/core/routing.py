"""Routing primitive for intelligent workflow branching.

# See: [[TTA.dev/Primitives/RouterPrimitive]]
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from ..observability.enhanced_collector import get_enhanced_metrics_collector
from ..observability.instrumented_primitive import TRACING_AVAILABLE
from ..observability.logging import get_logger
from .base import WorkflowContext, WorkflowPrimitive

# Check if OpenTelemetry is available
try:
    from opentelemetry import trace

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None  # type: ignore

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
        Execute routing logic and invoke selected primitive with comprehensive instrumentation.

        This method provides observability for routing decisions:
        - Creates spans for route evaluation and execution
        - Logs routing decisions and fallbacks
        - Records per-route metrics (duration, success/failure)
        - Tracks checkpoints for timing analysis
        - Monitors routing patterns and distribution

        Args:
            input_data: Input data for routing decision
            context: Workflow context

        Returns:
            Output from selected primitive

        Raises:
            ValueError: If route key not found and no default specified
        """
        metrics_collector = get_enhanced_metrics_collector()

        # Log workflow start
        logger.info(
            "router_workflow_start",
            route_count=len(self.routes),
            available_routes=list(self.routes.keys()),
            has_default=self.default is not None,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Record start checkpoint
        context.checkpoint("router.start")
        workflow_start_time = time.time()

        # Evaluate routing function with instrumentation
        context.checkpoint("router.route_eval.start")
        route_eval_start_time = time.time()

        try:
            route_key = self.router_fn(input_data, context)
        except Exception as e:
            logger.error(
                "router_evaluation_error",
                error=str(e),
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            raise

        route_eval_duration_ms = (time.time() - route_eval_start_time) * 1000
        context.checkpoint("router.route_eval.end")

        # Log route evaluation result
        logger.info(
            "router_route_evaluated",
            route_key=route_key,
            duration_ms=route_eval_duration_ms,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Record route evaluation metrics
        metrics_collector.record_execution(
            "RouterPrimitive.route_eval",
            duration_ms=route_eval_duration_ms,
            success=True,
        )

        # Get primitive for selected route
        primitive = self.routes.get(route_key)
        used_default = False

        # Fallback to default if needed
        if not primitive and self.default:
            logger.info(
                "router_fallback_to_default",
                original_route=route_key,
                default_route=self.default,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            route_key = self.default
            primitive = self.routes.get(route_key)
            used_default = True

        if not primitive:
            available = ", ".join(self.routes.keys())
            error_msg = f"No route found for key '{route_key}'. Available routes: {available}"
            logger.error(
                "router_no_route_found",
                route_key=route_key,
                available_routes=list(self.routes.keys()),
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )
            raise ValueError(error_msg)

        # Log routing decision
        logger.info(
            "router_route_selected",
            route=route_key,
            used_default=used_default,
            primitive_type=primitive.__class__.__name__,
            available_routes=list(self.routes.keys()),
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Store routing decision in context
        if "routing_history" not in context.state:
            context.state["routing_history"] = []
        context.state["routing_history"].append(
            {
                "route": route_key,
                "used_default": used_default,
                "timestamp": time.time(),
            }
        )

        # Execute selected primitive with instrumentation
        context.checkpoint(f"router.route_{route_key}.start")
        route_start_time = time.time()

        # Create route span (if tracing available)
        tracer = trace.get_tracer(__name__) if OTEL_AVAILABLE and trace is not None else None

        if tracer and TRACING_AVAILABLE:
            with tracer.start_as_current_span(f"router.route_{route_key}") as span:
                span.set_attribute("route.key", route_key)
                span.set_attribute("route.used_default", used_default)
                span.set_attribute("route.primitive_type", primitive.__class__.__name__)
                span.set_attribute("route.available_routes", len(self.routes))

                try:
                    result = await primitive.execute(input_data, context)
                    span.set_attribute("route.status", "success")
                except Exception as e:
                    span.set_attribute("route.status", "error")
                    span.set_attribute("route.error", str(e))
                    span.record_exception(e)
                    raise
        else:
            # Graceful degradation - execute without span
            result = await primitive.execute(input_data, context)

        # Record checkpoint and metrics
        context.checkpoint(f"router.route_{route_key}.end")
        route_duration_ms = (time.time() - route_start_time) * 1000
        metrics_collector.record_execution(
            f"RouterPrimitive.route_{route_key}",
            duration_ms=route_duration_ms,
            success=True,
        )

        # Log route execution completion
        logger.info(
            "router_route_complete",
            route=route_key,
            used_default=used_default,
            primitive_type=primitive.__class__.__name__,
            duration_ms=route_duration_ms,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        # Record end checkpoint
        context.checkpoint("router.end")
        workflow_duration_ms = (time.time() - workflow_start_time) * 1000

        # Log workflow completion
        logger.info(
            "router_workflow_complete",
            route_taken=route_key,
            used_default=used_default,
            total_duration_ms=workflow_duration_ms,
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        return result
