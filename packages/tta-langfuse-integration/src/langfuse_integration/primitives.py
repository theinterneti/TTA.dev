"""
Langfuse-integrated workflow primitives.

Provides primitives that automatically trace LLM calls to Langfuse.
"""

import logging
import time
from typing import Any

from langfuse import get_client, observe
from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.observability.instrumented_primitive import (
    InstrumentedPrimitive,
)

from .initialization import get_langfuse_client, is_langfuse_enabled

logger = logging.getLogger(__name__)


class LangfusePrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Primitive that wraps LLM calls with Langfuse tracing.

    Automatically tracks:
    - Prompt and completion
    - Token usage
    - Latency
    - Cost (if model pricing configured)
    - Metadata and tags

    Example:
        >>> llm = LangfusePrimitive(
        ...     name="narrative_gen",
        ...     metadata={"model": "gpt-4", "type": "story"}
        ... )
        >>> result = await llm.execute(context, {"prompt": "Tell a story..."})
    """

    def __init__(
        self,
        primitive: WorkflowPrimitive[dict[str, Any], dict[str, Any]] | None = None,
        name: str = "llm_call",
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        """Initialize Langfuse primitive.

        Args:
            primitive: Underlying primitive to wrap (optional)
            name: Name for this operation in Langfuse
            metadata: Additional metadata to attach to traces
            session_id: Session ID for grouping related calls
            user_id: User ID for tracking per-user metrics
            tags: Tags for categorizing traces
        """
        super().__init__()
        self.wrapped_primitive = primitive
        self.operation_name = name
        self.metadata = metadata or {}
        self.session_id = session_id
        self.user_id = user_id
        self.tags = tags or []

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Execute primitive with Langfuse tracing.

        Args:
            input_data: Input data (should contain 'prompt' or similar)
            context: Workflow context

        Returns:
            Result from wrapped primitive or input_data if no primitive wrapped
        """
        if not is_langfuse_enabled():
            logger.debug("Langfuse not enabled, skipping tracing")
            if self.wrapped_primitive:
                return await self.wrapped_primitive.execute(input_data, context)
            return input_data

        client = get_langfuse_client()
        if not client:
            logger.warning("Langfuse client not available")
            if self.wrapped_primitive:
                return await self.wrapped_primitive.execute(input_data, context)
            return input_data

        # Start timing
        start_time = time.time()

        # Use context manager for automatic span management
        with client.start_as_current_span(
            name=self.operation_name,
            input=input_data.get("prompt") or input_data,
            metadata={
                **self.metadata,
                "workflow_id": context.workflow_id,
                "correlation_id": context.correlation_id,
            },
            level="INFO",
        ) as span:
            try:
                # Update trace metadata
                span.update_trace(
                    session_id=self.session_id or context.correlation_id,
                    user_id=self.user_id,
                    tags=self.tags,
                )

                # Create nested generation span for LLM-specific tracking
                with span.start_as_current_generation(
                    name=f"{self.operation_name}_generation",
                    input=input_data.get("prompt") or input_data,
                    metadata=self.metadata,
                ) as generation:
                    # Execute wrapped primitive
                    if self.wrapped_primitive:
                        result = await self.wrapped_primitive.execute(input_data, context)
                    else:
                        # If no primitive wrapped, just pass through
                        result = input_data

                    # Calculate latency
                    latency_ms = (time.time() - start_time) * 1000

                    # Update generation with output and metrics
                    generation.update(
                        output=result.get("response") or result,
                        metadata={
                            **self.metadata,
                            "latency_ms": latency_ms,
                            "success": True,
                        },
                    )

                    # Extract and update token usage if available
                    if "usage" in result:
                        usage = result["usage"]
                        generation.update(
                            usage_details={
                                "input": usage.get("prompt_tokens", 0),
                                "output": usage.get("completion_tokens", 0),
                                "total": usage.get("total_tokens", 0),
                            }
                        )

                    # Extract model and cost if available
                    if "model" in result:
                        generation.update(model=result["model"])

                    if "cost" in result:
                        generation.update(cost_details={"total_cost": result["cost"]})

                    return result

            except Exception as e:
                # Record error in span
                span.update(
                    level="ERROR",
                    status_message=str(e),
                    metadata={
                        **self.metadata,
                        "error_type": type(e).__name__,
                        "success": False,
                    },
                )
                raise


class LangfuseObservablePrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Primitive using Langfuse @observe decorator.

    Alternative to LangfusePrimitive that uses decorators for simpler syntax.
    The @observe decorator automatically handles trace creation, input/output capture,
    timing, and error handling.

    Example:
        >>> primitive = LangfuseObservablePrimitive(
        ...     my_llm_primitive,
        ...     name="story_generator",
        ...     as_type="generation"
        ... )
        >>> result = await primitive.execute(input_data, context)
    """

    def __init__(
        self,
        primitive: WorkflowPrimitive[dict[str, Any], dict[str, Any]],
        name: str | None = None,
        as_type: str = "generation",
    ) -> None:
        """Initialize observable primitive.

        Args:
            primitive: Primitive to wrap
            name: Operation name (defaults to primitive class name)
            as_type: Langfuse observation type. Supported types:
                - 'generation': For LLM generations (default)
                - 'span': For general operations
                - 'agent': For agent operations
                - 'tool': For tool calls
                - 'chain': For chain executions
                - 'retriever': For retrieval operations
                - 'embedding': For embedding operations
                - 'evaluator': For evaluation operations
                - 'guardrail': For guardrail operations
        """
        super().__init__()
        self.wrapped_primitive = primitive
        self.operation_name = name or primitive.__class__.__name__
        self.span_type = as_type

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Execute with Langfuse @observe decorator.

        The @observe decorator automatically:
        - Creates traces/spans
        - Captures inputs/outputs
        - Records timing
        - Handles errors
        - Propagates context

        Args:
            input_data: Input data
            context: Workflow context

        Returns:
            Result from wrapped primitive
        """
        if not is_langfuse_enabled():
            logger.debug("Langfuse not enabled, executing without tracing")
            return await self.wrapped_primitive.execute(input_data, context)

        # Create an observed wrapper function
        @observe(name=self.operation_name, as_type=self.span_type)
        async def observed_execution():
            """Wrapper function with @observe decorator."""
            # Update trace metadata with workflow context
            langfuse = get_client()
            if langfuse:
                langfuse.update_current_trace(
                    session_id=context.correlation_id,
                    metadata={
                        "workflow_id": context.workflow_id,
                        "correlation_id": context.correlation_id,
                    },
                )

                # Update current observation (span/generation)
                if self.span_type == "generation":
                    langfuse.update_current_generation(
                        metadata={
                            "workflow_id": context.workflow_id,
                            "correlation_id": context.correlation_id,
                        }
                    )
                else:
                    langfuse.update_current_span(
                        metadata={
                            "workflow_id": context.workflow_id,
                            "correlation_id": context.correlation_id,
                        }
                    )

            # Execute wrapped primitive
            return await self.wrapped_primitive.execute(input_data, context)

        # Execute the observed function
        return await observed_execution()
