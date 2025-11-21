"""
Langfuse Integration for Hypertool Persona System.

Provides LLM observability with persona-based analytics, trace management,
and prompt tracking. Integrates with PersonaMetricsCollector for unified
observability.

Features:
- Persona-as-user pattern for analytics
- Automatic trace and span creation
- LLM generation tracking
- Graceful degradation when Langfuse unavailable
- Integration with existing APM infrastructure

Usage:
    from .langfuse_integration import LangfuseIntegration

    # Initialize (uses env vars by default)
    langfuse = LangfuseIntegration()

    # Start trace with persona context
    trace = langfuse.start_trace(
        name="feature-implementation",
        persona="backend-engineer",
        chatmode="feature-implementation"
    )

    # Create generation event
    generation = langfuse.create_generation(
        trace=trace,
        name="api-design",
        model="gpt-4",
        prompt="Design REST API for user profiles",
        completion="Here's the API design...",
        usage={"prompt_tokens": 150, "completion_tokens": 800}
    )
"""

import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class TraceContext:
    """Context for a Langfuse trace."""

    def __init__(
        self,
        trace_id: str,
        name: str,
        persona: str,
        chatmode: str,
        langfuse_trace: Any | None = None,
    ):
        self.trace_id = trace_id
        self.name = name
        self.persona = persona
        self.chatmode = chatmode
        self.langfuse_trace = langfuse_trace
        self.start_time = datetime.now()

    def __repr__(self) -> str:
        return f"TraceContext(trace_id={self.trace_id}, persona={self.persona})"


class SpanContext:
    """Context for a Langfuse span."""

    def __init__(
        self,
        span_id: str,
        name: str,
        trace: TraceContext,
        langfuse_span: Any | None = None,
    ):
        self.span_id = span_id
        self.name = name
        self.trace = trace
        self.langfuse_span = langfuse_span
        self.start_time = datetime.now()

    def __repr__(self) -> str:
        return f"SpanContext(span_id={self.span_id}, name={self.name})"


class GenerationContext:
    """Context for a Langfuse generation (LLM call)."""

    def __init__(
        self,
        generation_id: str,
        name: str,
        model: str,
        trace: TraceContext,
        langfuse_generation: Any | None = None,
    ):
        self.generation_id = generation_id
        self.name = name
        self.model = model
        self.trace = trace
        self.langfuse_generation = langfuse_generation
        self.start_time = datetime.now()

    def __repr__(self) -> str:
        return f"GenerationContext(generation_id={self.generation_id}, model={self.model})"


class LangfuseIntegration:
    """
    Langfuse integration for LLM observability in Hypertool.

    Implements persona-as-user pattern for analytics, automatic trace/span
    creation, and graceful degradation when Langfuse is unavailable.

    Singleton pattern ensures single Langfuse client instance.
    """

    _instance: "LangfuseIntegration | None" = None
    _initialized: bool = False

    def __new__(cls) -> "LangfuseIntegration":
        """Singleton pattern - only one instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        public_key: str | None = None,
        secret_key: str | None = None,
        host: str | None = None,
    ):
        """
        Initialize Langfuse integration.

        Args:
            public_key: Langfuse public key (default: from LANGFUSE_PUBLIC_KEY env var)
            secret_key: Langfuse secret key (default: from LANGFUSE_SECRET_KEY env var)
            host: Langfuse host URL (default: from LANGFUSE_HOST env var or https://cloud.langfuse.com)
        """
        # Only initialize once (singleton)
        if self._initialized:
            return

        self.public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
        self.host = host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        self.langfuse_client = None
        self.enabled = False

        # Try to initialize Langfuse client
        self._initialize_client()
        self._initialized = True

    def _initialize_client(self) -> None:
        """Initialize Langfuse client with graceful degradation."""
        if not self.public_key or not self.secret_key:
            logger.warning(
                "Langfuse API keys not found in environment variables. "
                "LLM tracing will be disabled. "
                "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to enable."
            )
            return

        try:
            from langfuse import Langfuse

            self.langfuse_client = Langfuse(
                public_key=self.public_key,
                secret_key=self.secret_key,
                host=self.host,
            )
            self.enabled = True
            logger.info(f"Langfuse integration initialized successfully (host: {self.host})")
        except ImportError:
            logger.warning(
                "Langfuse SDK not installed. LLM tracing will be disabled. "
                "Install with: uv add langfuse"
            )
        except Exception as e:
            logger.warning(
                f"Failed to initialize Langfuse client: {e}. LLM tracing will be disabled."
            )

    def start_trace(
        self,
        name: str,
        persona: str,
        chatmode: str,
        metadata: dict[str, Any] | None = None,
    ) -> TraceContext:
        """
        Start a new Langfuse trace with persona context.

        Implements persona-as-user pattern: persona becomes the "user" in Langfuse
        analytics, enabling persona-specific insights.

        Args:
            name: Trace name (e.g., "feature-implementation", "bug-fix")
            persona: Persona name (e.g., "backend-engineer", "testing-specialist")
            chatmode: Chat mode name (e.g., "feature-implementation", "code-review")
            metadata: Optional metadata to attach to trace

        Returns:
            TraceContext with trace information
        """
        trace_id = f"{name}-{persona}-{datetime.now().isoformat()}"

        if not self.enabled or not self.langfuse_client:
            logger.debug(f"Langfuse disabled - creating no-op trace: {trace_id}")
            return TraceContext(
                trace_id=trace_id,
                name=name,
                persona=persona,
                chatmode=chatmode,
                langfuse_trace=None,
            )

        try:
            # Create Langfuse trace with persona as user
            langfuse_trace = self.langfuse_client.trace(
                name=name,
                user_id=persona,  # Persona-as-user pattern
                metadata={
                    "persona": persona,
                    "chatmode": chatmode,
                    **(metadata or {}),
                },
            )

            logger.info(
                f"Started Langfuse trace: {name} (persona: {persona}, chatmode: {chatmode})"
            )

            return TraceContext(
                trace_id=trace_id,
                name=name,
                persona=persona,
                chatmode=chatmode,
                langfuse_trace=langfuse_trace,
            )

        except Exception as e:
            logger.error(f"Failed to start Langfuse trace: {e}")
            return TraceContext(
                trace_id=trace_id,
                name=name,
                persona=persona,
                chatmode=chatmode,
                langfuse_trace=None,
            )

    def start_span(
        self,
        trace: TraceContext,
        name: str,
        metadata: dict[str, Any] | None = None,
    ) -> SpanContext:
        """
        Start a new span within a trace.

        Args:
            trace: Parent trace context
            name: Span name (e.g., "api-design", "test-generation")
            metadata: Optional metadata to attach to span

        Returns:
            SpanContext with span information
        """
        span_id = f"{name}-{datetime.now().isoformat()}"

        if not self.enabled or not trace.langfuse_trace:
            logger.debug(f"Langfuse disabled - creating no-op span: {span_id}")
            return SpanContext(
                span_id=span_id,
                name=name,
                trace=trace,
                langfuse_span=None,
            )

        try:
            # Create Langfuse span
            langfuse_span = trace.langfuse_trace.span(
                name=name,
                metadata=metadata or {},
            )

            logger.debug(f"Started Langfuse span: {name} in trace: {trace.trace_id}")

            return SpanContext(
                span_id=span_id,
                name=name,
                trace=trace,
                langfuse_span=langfuse_span,
            )

        except Exception as e:
            logger.error(f"Failed to start Langfuse span: {e}")
            return SpanContext(
                span_id=span_id,
                name=name,
                trace=trace,
                langfuse_span=None,
            )

    def create_generation(
        self,
        trace: TraceContext,
        name: str,
        model: str,
        prompt: str,
        completion: str,
        usage: dict[str, int] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> GenerationContext:
        """
        Create a generation event (LLM call) within a trace.

        Args:
            trace: Parent trace context
            name: Generation name (e.g., "api-design-prompt")
            model: Model name (e.g., "gpt-4", "claude-3.5-sonnet")
            prompt: Input prompt text
            completion: LLM response text
            usage: Token usage dict with 'prompt_tokens' and 'completion_tokens'
            metadata: Optional metadata to attach to generation

        Returns:
            GenerationContext with generation information
        """
        generation_id = f"{name}-{model}-{datetime.now().isoformat()}"

        if not self.enabled or not trace.langfuse_trace:
            logger.debug(f"Langfuse disabled - creating no-op generation: {generation_id}")
            return GenerationContext(
                generation_id=generation_id,
                name=name,
                model=model,
                trace=trace,
                langfuse_generation=None,
            )

        try:
            # Create Langfuse generation event
            langfuse_generation = trace.langfuse_trace.generation(
                name=name,
                model=model,
                input=prompt,
                output=completion,
                usage=usage or {},
                metadata={
                    "persona": trace.persona,
                    "chatmode": trace.chatmode,
                    **(metadata or {}),
                },
            )

            logger.info(
                f"Created Langfuse generation: {name} "
                f"(model: {model}, tokens: {usage.get('prompt_tokens', 0) + usage.get('completion_tokens', 0) if usage else 'unknown'})"
            )

            return GenerationContext(
                generation_id=generation_id,
                name=name,
                model=model,
                trace=trace,
                langfuse_generation=langfuse_generation,
            )

        except Exception as e:
            logger.error(f"Failed to create Langfuse generation: {e}")
            return GenerationContext(
                generation_id=generation_id,
                name=name,
                model=model,
                trace=trace,
                langfuse_generation=None,
            )

    def end_trace(self, trace: TraceContext, status: str = "success") -> None:
        """
        End a trace and flush to Langfuse.

        Args:
            trace: Trace context to end
            status: Trace status ("success" or "error")
        """
        if not self.enabled or not trace.langfuse_trace:
            logger.debug(f"Langfuse disabled - no-op end trace: {trace.trace_id}")
            return

        try:
            # Update trace status
            trace.langfuse_trace.update(
                output={"status": status},
            )

            # Flush to Langfuse
            if self.langfuse_client:
                self.langfuse_client.flush()

            duration = (datetime.now() - trace.start_time).total_seconds()
            logger.info(
                f"Ended Langfuse trace: {trace.name} (duration: {duration:.2f}s, status: {status})"
            )

        except Exception as e:
            logger.error(f"Failed to end Langfuse trace: {e}")

    def flush(self) -> None:
        """Flush all pending Langfuse events."""
        if self.enabled and self.langfuse_client:
            try:
                self.langfuse_client.flush()
                logger.debug("Flushed Langfuse events")
            except Exception as e:
                logger.error(f"Failed to flush Langfuse: {e}")


# Global singleton instance
_langfuse_integration: LangfuseIntegration | None = None


def get_langfuse_integration() -> LangfuseIntegration:
    """
    Get the global LangfuseIntegration singleton.

    Returns:
        LangfuseIntegration instance
    """
    global _langfuse_integration
    if _langfuse_integration is None:
        _langfuse_integration = LangfuseIntegration()
    return _langfuse_integration
