"""LangFuse APM integration for TTA.dev primitives.

This module provides seamless integration between TTA.dev workflow primitives
and LangFuse observability, enabling automatic tracing, metrics collection,
and performance monitoring.
"""

import asyncio
from datetime import datetime
from typing import Any

from langfuse import Langfuse
from langfuse.decorators import langfuse_context, observe
from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class LangFuseIntegration:
    """Main integration class for LangFuse APM.

    Provides automatic instrumentation of TTA.dev primitives with LangFuse tracing,
    metrics collection, and observability features.

    Example:
        ```python
        from tta_apm_langfuse import LangFuseIntegration
        from tta_dev_primitives import SequentialPrimitive

        # Initialize integration
        apm = LangFuseIntegration(
            public_key="pk_...",
            secret_key="sk_...",
            host="https://cloud.langfuse.com"
        )

        # Instrument primitives
        workflow = SequentialPrimitive([step1, step2, step3])
        instrumented = apm.instrument(workflow)

        # Execute with automatic tracing
        result = await instrumented.execute(data, context)
        ```
    """

    def __init__(
        self,
        public_key: str,
        secret_key: str,
        host: str = "https://cloud.langfuse.com",
        enabled: bool = True,
        **kwargs: Any,
    ):
        """Initialize LangFuse integration.

        Args:
            public_key: LangFuse public API key
            secret_key: LangFuse secret API key
            host: LangFuse host URL (default: cloud.langfuse.com)
            enabled: Enable/disable tracing (default: True)
            **kwargs: Additional LangFuse client configuration
        """
        self.enabled = enabled
        self.client = (
            Langfuse(public_key=public_key, secret_key=secret_key, host=host, **kwargs)
            if enabled
            else None
        )

    def instrument(
        self, primitive: WorkflowPrimitive, trace_name: str | None = None
    ) -> WorkflowPrimitive:
        """Instrument a primitive with LangFuse tracing.

        Wraps the primitive's execute method to automatically capture:
        - Execution traces with parent/child relationships
        - Input/output data
        - Execution duration
        - Success/failure status
        - Error details

        Args:
            primitive: The primitive to instrument
            trace_name: Optional custom trace name

        Returns:
            Instrumented primitive with automatic tracing
        """
        if not self.enabled:
            return primitive

        original_execute = primitive.execute

        @observe(name=trace_name or primitive.__class__.__name__)
        async def traced_execute(input_data: Any, context: WorkflowContext) -> Any:
            """Traced execution wrapper."""
            start_time = datetime.now()

            try:
                # Add LangFuse trace ID to context
                if langfuse_context.get_current_trace_id():
                    context.metadata["langfuse_trace_id"] = langfuse_context.get_current_trace_id()

                # Execute primitive
                result = await original_execute(input_data, context)

                # Record success metrics
                duration = (datetime.now() - start_time).total_seconds()
                langfuse_context.update_current_observation(
                    metadata={
                        "primitive_type": primitive.__class__.__name__,
                        "duration_seconds": duration,
                        "status": "success",
                    }
                )

                return result

            except Exception as e:
                # Record failure metrics
                duration = (datetime.now() - start_time).total_seconds()
                langfuse_context.update_current_observation(
                    metadata={
                        "primitive_type": primitive.__class__.__name__,
                        "duration_seconds": duration,
                        "status": "error",
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                    }
                )
                raise

        primitive.execute = traced_execute
        return primitive

    def create_generation(
        self,
        name: str,
        model: str,
        input_data: Any,
        output_data: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record an LLM generation event.

        Args:
            name: Generation name
            model: Model identifier
            input_data: Input prompt/data
            output_data: Generated output
            metadata: Additional metadata
        """
        if not self.enabled or not self.client:
            return

        self.client.generation(
            name=name, model=model, input=input_data, output=output_data, metadata=metadata or {}
        )

    def flush(self) -> None:
        """Flush pending traces to LangFuse."""
        if self.enabled and self.client:
            self.client.flush()

    async def aflush(self) -> None:
        """Asynchronously flush pending traces to LangFuse."""
        if self.enabled and self.client:
            await asyncio.to_thread(self.client.flush)


def auto_instrument(
    primitives: list[WorkflowPrimitive], langfuse_integration: LangFuseIntegration
) -> list[WorkflowPrimitive]:
    """Automatically instrument a list of primitives.

    Args:
        primitives: List of primitives to instrument
        langfuse_integration: LangFuse integration instance

    Returns:
        List of instrumented primitives
    """
    return [langfuse_integration.instrument(p) for p in primitives]
