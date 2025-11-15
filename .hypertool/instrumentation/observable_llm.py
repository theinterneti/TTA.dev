"""
Observable LLM Wrapper for Hypertool Persona System.

Wraps LLM calls with automatic tracing, metrics collection, and persona tracking.
Integrates with both Langfuse (LLM observability) and PersonaMetricsCollector
(Prometheus metrics).

Features:
- Automatic Langfuse generation events
- Token usage tracking in Prometheus
- Persona context propagation
- Error capture and retry tracking
- Support for sync and async LLM functions
- Graceful degradation when services unavailable

Usage:
    from .observable_llm import ObservableLLM
    from .langfuse_integration import get_langfuse_integration
    from .persona_metrics import get_persona_metrics

    # Setup
    langfuse = get_langfuse_integration()
    metrics = get_persona_metrics()

    # Wrap your LLM function
    async def my_llm_call(prompt: str) -> str:
        # Your LLM API call here
        return "LLM response"

    # Create observable wrapper
    observable_llm = ObservableLLM(
        llm_function=my_llm_call,
        model="gpt-4",
        langfuse=langfuse,
        metrics=metrics
    )

    # Use it (automatic tracing + metrics)
    response = await observable_llm(
        "Write a FastAPI endpoint",
        persona="backend-engineer",
        chatmode="feature-implementation"
    )
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from functools import wraps
from typing import Any, TypeVar

from .langfuse_integration import (
    LangfuseIntegration,
    TraceContext,
    get_langfuse_integration,
)
from .persona_metrics import PersonaMetricsCollector, get_persona_metrics

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ObservableLLM:
    """
    Observable LLM wrapper with automatic tracing and metrics.

    Wraps any LLM function with Langfuse tracing and Prometheus metrics.
    Tracks token usage, latency, errors, and persona context.
    """

    def __init__(
        self,
        llm_function: Callable[..., Any],
        model: str,
        langfuse: LangfuseIntegration | None = None,
        metrics: PersonaMetricsCollector | None = None,
        default_persona: str = "unknown",
        default_chatmode: str = "default",
    ):
        """
        Initialize ObservableLLM wrapper.

        Args:
            llm_function: LLM function to wrap (sync or async)
            model: Model name (e.g., "gpt-4", "claude-3.5-sonnet")
            langfuse: LangfuseIntegration instance (default: global singleton)
            metrics: PersonaMetricsCollector instance (default: global singleton)
            default_persona: Default persona if not provided in call
            default_chatmode: Default chatmode if not provided in call
        """
        self.llm_function = llm_function
        self.model = model
        self.langfuse = langfuse or get_langfuse_integration()
        self.metrics = metrics or get_persona_metrics()
        self.default_persona = default_persona
        self.default_chatmode = default_chatmode

        # Track if function is async
        self.is_async = asyncio.iscoroutinefunction(llm_function)

        logger.info(
            f"Initialized ObservableLLM for model: {model} (async: {self.is_async})"
        )

    async def __call__(
        self,
        prompt: str,
        persona: str | None = None,
        chatmode: str | None = None,
        trace: TraceContext | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Call the LLM with automatic tracing and metrics.

        Args:
            prompt: Input prompt for the LLM
            persona: Persona name (default: from constructor)
            chatmode: Chatmode name (default: from constructor)
            trace: Existing trace context (creates new if None)
            metadata: Additional metadata to attach
            **kwargs: Additional arguments to pass to LLM function

        Returns:
            LLM response text
        """
        persona = persona or self.default_persona
        chatmode = chatmode or self.default_chatmode
        start_time = datetime.now()

        # Create trace if not provided
        created_trace = False
        if trace is None:
            trace = self.langfuse.start_trace(
                name=f"{self.model}-call",
                persona=persona,
                chatmode=chatmode,
            )
            created_trace = True

        try:
            # Call LLM (async or sync)
            if self.is_async:
                response = await self.llm_function(prompt, **kwargs)
            else:
                response = self.llm_function(prompt, **kwargs)

            # Calculate duration and token estimates
            duration = (datetime.now() - start_time).total_seconds()

            # Estimate tokens (rough approximation: 1 token ≈ 4 chars)
            prompt_tokens = len(prompt) // 4
            completion_tokens = len(response) // 4 if isinstance(response, str) else 0
            total_tokens = prompt_tokens + completion_tokens

            # Create Langfuse generation event
            self.langfuse.create_generation(
                trace=trace,
                name=f"{self.model}-generation",
                model=self.model,
                prompt=prompt,
                completion=response if isinstance(response, str) else str(response),
                usage={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                },
                metadata={
                    "duration_seconds": duration,
                    "persona": persona,
                    "chatmode": chatmode,
                    **(metadata or {}),
                },
            )

            # Update Prometheus metrics
            self.metrics.record_token_usage(
                persona=persona,
                chatmode="package-release",  # TODO: Get from context
                model=self.model,
                tokens=total_tokens,
            )

            logger.info(
                f"LLM call completed: {self.model} "
                f"(persona: {persona}, tokens: {total_tokens}, "
                f"duration: {duration:.2f}s)"
            )

            # End trace if we created it
            if created_trace:
                self.langfuse.end_trace(trace, status="success")

            return response

        except Exception as e:
            # End trace with error if we created it
            if created_trace:
                self.langfuse.end_trace(trace, status="error")

            logger.error(
                f"LLM call failed: {self.model} (persona: {persona}, error: {e})"
            )
            raise

    def wrap_sync(
        self,
        persona: str | None = None,
        chatmode: str | None = None,
    ) -> Callable[[str], str]:
        """
        Create a synchronous wrapper function.

        Args:
            persona: Default persona for all calls
            chatmode: Default chatmode for all calls

        Returns:
            Synchronous function that wraps LLM calls
        """

        @wraps(self.llm_function)
        def wrapper(prompt: str, **kwargs: Any) -> str:
            """Synchronous wrapper for LLM calls."""
            if self.is_async:
                # Run async function in event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    raise RuntimeError(
                        "Cannot use wrap_sync with async LLM in running event loop. "
                        "Use await observable_llm(...) instead."
                    )
                return loop.run_until_complete(
                    self(prompt, persona=persona, chatmode=chatmode, **kwargs)
                )
            else:
                # Run sync function directly
                return asyncio.run(
                    self(prompt, persona=persona, chatmode=chatmode, **kwargs)
                )

        return wrapper

    def wrap_async(
        self,
        persona: str | None = None,
        chatmode: str | None = None,
    ) -> Callable[[str], Any]:
        """
        Create an asynchronous wrapper function.

        Args:
            persona: Default persona for all calls
            chatmode: Default chatmode for all calls

        Returns:
            Asynchronous function that wraps LLM calls
        """

        @wraps(self.llm_function)
        async def wrapper(prompt: str, **kwargs: Any) -> str:
            """Asynchronous wrapper for LLM calls."""
            return await self(prompt, persona=persona, chatmode=chatmode, **kwargs)

        return wrapper


def observe_llm(
    model: str,
    persona: str | None = None,
    chatmode: str | None = None,
    langfuse: LangfuseIntegration | None = None,
    metrics: PersonaMetricsCollector | None = None,
) -> Callable[[Callable[..., T]], ObservableLLM]:
    """
    Decorator to make any LLM function observable.

    Usage:
        @observe_llm(model="gpt-4", persona="backend-engineer")
        async def my_llm_call(prompt: str) -> str:
            # Your LLM API call
            return "response"

        # Use it
        response = await my_llm_call("Write code")

    Args:
        model: Model name
        persona: Default persona
        chatmode: Default chatmode
        langfuse: LangfuseIntegration instance
        metrics: PersonaMetricsCollector instance

    Returns:
        Decorator function
    """

    def decorator(func: Callable[..., T]) -> ObservableLLM:
        """Decorator to wrap function."""
        return ObservableLLM(
            llm_function=func,
            model=model,
            langfuse=langfuse,
            metrics=metrics,
            default_persona=persona or "unknown",
            default_chatmode=chatmode or "default",
        )

    return decorator
