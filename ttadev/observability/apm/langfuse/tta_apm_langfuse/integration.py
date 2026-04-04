"""LangFuse APM integration for TTA.dev primitives.

This module provides seamless integration between TTA.dev workflow primitives
and LangFuse observability, enabling automatic tracing, metrics collection,
and performance monitoring.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from langfuse import Langfuse
from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive

_log = logging.getLogger(__name__)


class LangFuseIntegration:
    """Main integration class for LangFuse APM.

    Provides automatic instrumentation of TTA.dev primitives with LangFuse tracing,
    metrics collection, and observability features.

    Example:
        ```python
        from tta_apm_langfuse import LangFuseIntegration
        from primitives import SequentialPrimitive

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
        session_id: str | None = None,
        user_id: str | None = None,
        **kwargs: Any,
    ):
        """Initialize LangFuse integration.

        Args:
            public_key: LangFuse public API key
            secret_key: LangFuse secret API key
            host: LangFuse host URL (default: cloud.langfuse.com)
            enabled: Enable/disable tracing (default: True)
            session_id: Optional session ID to associate with all observations.
            user_id: Optional user/agent ID to associate with all observations.
            **kwargs: Additional LangFuse client configuration
        """
        self.enabled = enabled
        self.session_id = session_id
        self.user_id = user_id
        self.client = (
            Langfuse(public_key=public_key, secret_key=secret_key, host=host, **kwargs)
            if enabled
            else None
        )

    @classmethod
    def from_env(cls) -> "LangFuseIntegration":
        """Create integration from LANGFUSE_* environment variables.

        Reads credentials from the environment so callers don't need to
        hard-code or manually pass API keys.

        Required environment variables:
            LANGFUSE_PUBLIC_KEY: Langfuse public API key (starts with ``pk-lf-``)
            LANGFUSE_SECRET_KEY: Langfuse secret API key (starts with ``sk-lf-``)

        Optional environment variables:
            LANGFUSE_BASE_URL: Langfuse host URL — used by the Langfuse SDK natively.
                               (default: ``https://cloud.langfuse.com``)
            LANGFUSE_HOST: Alias for LANGFUSE_BASE_URL (checked if BASE_URL is absent).

        Returns:
            Configured :class:`LangFuseIntegration` instance.

        Raises:
            KeyError: If ``LANGFUSE_PUBLIC_KEY`` or ``LANGFUSE_SECRET_KEY``
                      are not set.

        Example:
            ```bash
            export LANGFUSE_PUBLIC_KEY="pk-lf-..."
            export LANGFUSE_SECRET_KEY="sk-lf-..."
            export LANGFUSE_BASE_URL="https://cloud.langfuse.com"  # optional
            ```

            ```python
            from tta_apm_langfuse import LangFuseIntegration

            apm = LangFuseIntegration.from_env()
            ```
        """
        import os

        host = (
            os.environ.get("LANGFUSE_BASE_URL")
            or os.environ.get("LANGFUSE_HOST")
            or "https://cloud.langfuse.com"
        )
        instance = cls(
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            host=host,
        )

        # Auto-detect agent identity for user attribution
        try:
            from ttadev.observability.agent_identity import get_agent_id  # noqa: PLC0415

            instance.user_id = get_agent_id()
        except Exception:
            pass

        # Auto-detect active L0 run for session attribution
        try:
            from ttadev.control_plane.service import ControlPlaneService  # noqa: PLC0415

            svc = ControlPlaneService()
            active_runs = svc.list_runs()
            if active_runs:
                instance.session_id = active_runs[0].id
        except Exception:
            pass

        return instance

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
        client = self.client
        name = trace_name or primitive.__class__.__name__
        session_id = self.session_id
        user_id = self.user_id

        async def traced_execute(input_data: Any, context: WorkflowContext) -> Any:
            """Traced execution wrapper using Langfuse v4 API."""
            start_time = datetime.now()

            with client.start_as_current_observation(
                name=name,
                as_type="span",
                input=str(input_data)[:1000],
                metadata={"primitive_type": primitive.__class__.__name__},
                session_id=session_id,
                user_id=user_id,
            ) as span:
                try:
                    # Capture trace ID in workflow context metadata
                    trace_id = client.get_current_trace_id()
                    if trace_id:
                        context.metadata["langfuse_trace_id"] = trace_id

                    result = await original_execute(input_data, context)

                    duration = (datetime.now() - start_time).total_seconds()
                    span.update(
                        output=str(result)[:1000],
                        metadata={
                            "primitive_type": primitive.__class__.__name__,
                            "duration_seconds": duration,
                            "status": "success",
                        },
                    )
                    return result

                except Exception as e:
                    duration = (datetime.now() - start_time).total_seconds()
                    span.update(
                        level="ERROR",
                        status_message=f"{type(e).__name__}: {e}",
                        metadata={
                            "primitive_type": primitive.__class__.__name__,
                            "duration_seconds": duration,
                            "status": "error",
                            "error_type": type(e).__name__,
                            "error_message": str(e),
                        },
                    )
                    raise

        primitive.execute = traced_execute
        return primitive

    def create_generation(
        self,
        name: str,
        model: str,
        input: Any,  # noqa: A002
        output: Any,
        metadata: dict[str, Any] | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> str | None:
        """Record an LLM generation event.

        Args:
            name: Generation name (e.g. ``"groq/llama-3.3-70b-versatile"``).
            model: Model identifier string.
            input: Input prompt or messages list sent to the model.
            output: Generated output string returned by the model.
            metadata: Optional extra metadata (usage, cost, tier, …).
            session_id: Override session ID for this generation (falls back to
                ``self.session_id`` if not provided).
            user_id: Override user/agent ID (falls back to ``self.user_id``).

        Returns:
            The Langfuse trace ID string, or ``None`` if tracing is disabled or
            an error occurs.
        """
        if not self.enabled or not self.client:
            return None

        effective_session_id = session_id or self.session_id
        effective_user_id = user_id or self.user_id

        with self.client.start_as_current_observation(
            name=name,
            as_type="generation",
            model=model,
            input=input,
            output=output,
            metadata=metadata or {},
            session_id=effective_session_id,
            user_id=effective_user_id,
        ):
            pass  # observation is ended on context manager exit

        trace_id: str | None = None
        try:
            trace_id = self.client.get_current_trace_id()
            if trace_id:
                url = self.client.get_trace_url(trace_id)
                _log.debug("Langfuse trace: %s", url)
        except Exception:
            pass

        return trace_id

    def score_inline(
        self,
        score: float,
        name: str = "quality",
        comment: str | None = None,
    ) -> None:
        """Score the current trace without needing a trace_id.

        Call this immediately after create_generation() while still in the
        same observation context. Uses Langfuse's score_current_trace().

        Args:
            score: Numeric score value (0.0–1.0 typical).
            name: Score category (e.g. "quality", "accuracy", "latency").
            comment: Optional explanation.
        """
        if not self.enabled or self.client is None:
            return
        try:
            self.client.score_current_trace(name=name, value=score, comment=comment)
        except Exception:
            pass

    def score_response(
        self,
        trace_id: str,
        score: float,
        name: str = "quality",
        comment: str | None = None,
    ) -> None:
        """Record a quality score for a completed trace.

        Args:
            trace_id: The Langfuse trace ID (from ``context.metadata["langfuse_trace_id"]``).
            score: Numeric score (0.0–1.0 typical, but Langfuse accepts any float).
            name: Score category name (e.g. ``"quality"``, ``"accuracy"``, ``"latency"``).
            comment: Optional human-readable explanation.
        """
        if not self.enabled or self.client is None:
            return
        self.client.create_score(
            trace_id=trace_id,
            name=name,
            value=score,
            comment=comment,
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
