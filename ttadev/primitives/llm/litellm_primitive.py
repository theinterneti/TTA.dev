"""LiteLLMPrimitive — litellm-powered LLM invocation primitive.

Uses ``litellm.acompletion()`` as the execution engine, giving TTA.dev access
to 100+ LLM providers through a single unified interface with built-in routing,
fallback, and observability support.

This primitive is the **primary** LLM execution path in TTA.dev.
:class:`~ttadev.primitives.llm.universal_llm_primitive.UniversalLLMPrimitive`
is preserved as a documented fallback, composable via TTA.dev's
:class:`~ttadev.primitives.recovery.fallback.FallbackPrimitive`.

Model string format (litellm convention)::

    "<provider>/<model-name>"  →  "groq/llama-3.1-8b-instant"
                                   "anthropic/claude-3-5-haiku-20241022"
                                   "ollama/llama3.2"

See https://docs.litellm.ai/docs/providers for the full provider list.

Langfuse tracing
----------------
Set ``LANGFUSE_SECRET_KEY``, ``LANGFUSE_PUBLIC_KEY``, and optionally
``LANGFUSE_HOST`` before calling :meth:`execute`.  The callback is wired once
per process on the first call when the key is present.

Example::

    import asyncio
    from ttadev.primitives.core import WorkflowContext
    from ttadev.primitives.llm import LiteLLMPrimitive, LLMRequest

    llm = LiteLLMPrimitive()
    ctx = WorkflowContext(workflow_id="example")
    response = asyncio.run(llm.execute(
        LLMRequest(
            model="groq/llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Hello!"}],
        ),
        ctx,
    ))
    print(response.content)
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Any

from ttadev.primitives.core import WorkflowContext, WorkflowPrimitive
from ttadev.primitives.llm.litellm_config import _PROVIDER_PREFIX
from ttadev.primitives.llm.litellm_streaming import iter_stream_chunks
from ttadev.primitives.llm.litellm_tools import parse_tool_calls
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    ToolCall,
)

# ── OpenTelemetry — optional, degrades gracefully when not installed ──────────
try:
    from opentelemetry import trace as otel_trace

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    otel_trace = None  # type: ignore[assignment]

__all__ = ["LiteLLMPrimitive", "make_resilient_llm"]

# Langfuse callback is configured at most once per process.
_LANGFUSE_CONFIGURED: bool = False


def _maybe_configure_langfuse() -> None:
    """Wire litellm's Langfuse callback when ``LANGFUSE_SECRET_KEY`` is set.

    Idempotent — subsequent calls after the first successful configuration are
    silent no-ops.  Existing callbacks are preserved; ``"langfuse"`` is only
    appended if not already present.  Any exception is silently swallowed so
    that callers never fail because of observability setup.
    """
    global _LANGFUSE_CONFIGURED  # noqa: PLW0603
    if _LANGFUSE_CONFIGURED:
        return
    if not os.environ.get("LANGFUSE_SECRET_KEY"):
        return
    try:
        import litellm  # noqa: PLC0415

        existing: list[Any] = list(litellm.success_callback or [])
        if "langfuse" not in existing:
            litellm.success_callback = [*existing, "langfuse"]
        _LANGFUSE_CONFIGURED = True
    except Exception:  # noqa: BLE001
        pass


class LiteLLMPrimitive(WorkflowPrimitive[LLMRequest, LLMResponse]):
    """Execute LLM requests via litellm — 100+ providers, unified interface.

    The model is carried in each :class:`~.universal_llm_primitive.LLMRequest`
    as a litellm model string (``"<provider>/<model>"``, e.g.
    ``"groq/llama-3.1-8b-instant"``).  When a ``provider`` is supplied to the
    constructor, short model names without a ``"/"`` prefix are automatically
    expanded (e.g. ``"llama-3.1-8b-instant"`` → ``"groq/llama-3.1-8b-instant"``).

    litellm-native fallbacks (``fallbacks`` constructor arg) are preferred over
    TTA.dev's :class:`FallbackPrimitive` for multi-model fallback chains because
    they keep the request model consistent across all attempts.

    Example — provider-bound primitive::

        from ttadev.primitives.llm import LiteLLMPrimitive, LLMRequest, LLMProvider

        groq = LiteLLMPrimitive(provider=LLMProvider.GROQ)
        resp = await groq.execute(
            LLMRequest(model="llama-3.1-8b-instant", messages=[...]),
            ctx,
        )

    Example — stateless (request carries full litellm model string)::

        llm = LiteLLMPrimitive()
        resp = await llm.execute(
            LLMRequest(model="anthropic/claude-3-5-haiku-20241022", messages=[...]),
            ctx,
        )

    Example — litellm-native fallback list::

        llm = LiteLLMPrimitive(
            fallbacks=["anthropic/claude-3-haiku-20240307", "ollama/llama3.2"],
        )
        resp = await llm.execute(
            LLMRequest(model="groq/llama-3.1-8b-instant", messages=[...]),
            ctx,
        )
    """

    def __init__(
        self,
        provider: str | LLMProvider | None = None,
        *,
        fallbacks: list[str] | None = None,
        api_key: str | None = None,
        api_base: str | None = None,
        timeout: float | None = None,
        metadata: dict[str, Any] | None = None,
        max_budget: float | None = None,
    ) -> None:
        """Create a :class:`LiteLLMPrimitive`.

        Args:
            provider: Optional provider prefix.  When set, ``request.model``
                values that do not already contain a ``"/"`` are prefixed with
                ``"<provider>/"`` before being passed to litellm.  Accepts a
                :class:`~.universal_llm_primitive.LLMProvider` enum value or a
                raw litellm provider string (e.g. ``"groq"``).
            fallbacks: List of litellm model strings to try when the primary
                model call fails (uses litellm's native fallback mechanism).
                E.g. ``["anthropic/claude-3-haiku-20240307", "ollama/llama3.2"]``.
            api_key: Override API key.  When ``None`` the key is read from the
                provider's environment variable.
            api_base: Override the provider base URL (useful for proxies and
                locally-hosted models).
            timeout: Per-call timeout in seconds.  ``None`` uses litellm's
                default.
            metadata: Extra key/value pairs forwarded to litellm as
                ``metadata`` (appears in Langfuse traces, cost tracking, etc.).
            max_budget: Optional spending cap in USD for the lifetime of this
                primitive instance.  Accumulated across ``execute()`` calls via
                ``WorkflowContext.metadata["llm_cost_usd"]``.  When the running
                total exceeds this value a :class:`BudgetExceededError` is raised
                before the call is dispatched.  ``None`` disables the check.
        """
        super().__init__()
        if provider is None:
            self._provider_prefix: str | None = None
        elif isinstance(provider, LLMProvider):
            self._provider_prefix = _PROVIDER_PREFIX.get(str(provider), str(provider))
        else:
            self._provider_prefix = str(provider)

        self._fallbacks = fallbacks
        self._api_key = api_key
        self._api_base = api_base
        self._timeout = timeout
        self._metadata: dict[str, Any] = metadata or {}
        self._max_budget = max_budget

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_model(self, request: LLMRequest) -> str:
        """Return the litellm model string to use for *request*.

        If ``request.model`` already contains ``"/"`` it is used as-is.
        Otherwise the constructor ``provider`` prefix is prepended when
        available; if no provider prefix was set, the model string is used
        verbatim (litellm will attempt to infer the provider).

        Args:
            request: The incoming :class:`LLMRequest`.

        Returns:
            A litellm model string.
        """
        if "/" in request.model:
            return request.model
        if self._provider_prefix:
            return f"{self._provider_prefix}/{request.model}"
        return request.model

    def _build_kwargs(self, request: LLMRequest, model: str) -> dict[str, Any]:
        """Assemble keyword arguments for ``litellm.acompletion()``.

        Args:
            request: The incoming LLM request.
            model: The resolved litellm model string.

        Returns:
            A ``dict`` ready to unpack into ``await litellm.acompletion(**kwargs)``.
        """
        messages: list[dict[str, Any]] = list(request.messages)
        if request.system:
            messages = [{"role": "system", "content": request.system}, *messages]

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        if self._fallbacks:
            kwargs["fallbacks"] = self._fallbacks
        if self._api_key:
            kwargs["api_key"] = self._api_key
        if self._api_base:
            kwargs["api_base"] = self._api_base
        if self._timeout is not None:
            kwargs["timeout"] = self._timeout
        if self._metadata:
            kwargs["metadata"] = dict(self._metadata)
        if request.tools:
            kwargs["tools"] = [t.to_openai() for t in request.tools]
            kwargs["tool_choice"] = request.tool_choice
        if request.reasoning_effort is not None:
            kwargs["reasoning_effort"] = request.reasoning_effort
        return kwargs

    @staticmethod
    def _parse_tool_calls(raw_calls: list[Any] | None) -> list[ToolCall] | None:
        """Convert litellm/OpenAI tool-call objects to TTA.dev :class:`ToolCall`.

        litellm returns tool calls in OpenAI wire format; this method extracts
        the id, function name, and JSON-decoded arguments.  Malformed entries
        are silently skipped.

        Args:
            raw_calls: The ``tool_calls`` list from a litellm response choice.

        Returns:
            A list of :class:`ToolCall` objects, or ``None`` when *raw_calls*
            is empty or ``None``.
        """
        return parse_tool_calls(raw_calls)

    @staticmethod
    def _extract_provider(model: str) -> str:
        """Return the provider portion of a litellm model string.

        Examples::

            _extract_provider("groq/llama-3.1-8b-instant")  # "groq"
            _extract_provider("llama-3.1-8b-instant")        # "unknown"
        """
        return model.split("/", 1)[0] if "/" in model else "unknown"

    # ------------------------------------------------------------------
    # WorkflowPrimitive interface
    # ------------------------------------------------------------------

    async def execute(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        """Execute a single LLM call and return the complete response.

        Langfuse is configured lazily on the first call when
        ``LANGFUSE_SECRET_KEY`` is present in the environment.  OTel spans are
        emitted when ``opentelemetry`` is installed.

        Args:
            request: LLM invocation parameters.
            ctx: Workflow context (used for OTel span attribution and cost
                accumulation via ``ctx.metadata["llm_cost_usd"]``).

        Returns:
            The model's response wrapped in :class:`LLMResponse`.

        Raises:
            BudgetExceededError: When a ``max_budget`` was set and the running
                cost total would exceed it.
            Exception: Re-raises any litellm exception with its original type
                and message preserved.
        """
        _maybe_configure_langfuse()

        if self._max_budget is not None:
            import litellm  # noqa: PLC0415

            spent = float(ctx.metadata.get("llm_cost_usd", 0.0))
            if spent >= self._max_budget:
                raise litellm.BudgetExceededError(
                    current_cost=spent,
                    max_budget=self._max_budget,
                )

        model = self._resolve_model(request)
        provider = self._extract_provider(model)
        kwargs = self._build_kwargs(request, model)

        if not (OTEL_AVAILABLE and otel_trace is not None):
            return await self._call(kwargs, model, provider, ctx)

        tracer = otel_trace.get_tracer(__name__)
        span_name = f"gen_ai.litellm.{provider}.invoke"
        with tracer.start_as_current_span(span_name) as span:
            span.set_attribute("gen_ai.system", provider)
            span.set_attribute("gen_ai.request.model", model)
            span.set_attribute("gen_ai.request.temperature", request.temperature)
            try:
                response = await self._call(kwargs, model, provider, ctx)
            except Exception as exc:
                span.record_exception(exc)
                from opentelemetry.trace import Status, StatusCode  # noqa: PLC0415

                span.set_status(Status(StatusCode.ERROR, str(exc)))
                raise
            span.set_attribute("gen_ai.response.model", response.model)
            if response.usage:
                pt = response.usage.get("prompt_tokens") or response.usage.get("input_tokens")
                ct = response.usage.get("completion_tokens") or response.usage.get("output_tokens")
                if pt is not None:
                    span.set_attribute("gen_ai.usage.prompt_tokens", pt)
                if ct is not None:
                    span.set_attribute("gen_ai.usage.completion_tokens", ct)
            if response.cost_usd is not None:
                span.set_attribute("gen_ai.usage.cost_usd", response.cost_usd)
            return response

    async def stream(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        """Yield text tokens as they stream from the provider.

        Enables litellm streaming via ``stream=True`` in ``acompletion``.
        The ``request.stream`` field is ignored — this method always streams.

        Args:
            request: LLM invocation parameters.
            ctx: Workflow context.

        Yields:
            Non-empty text delta chunks as they arrive from the provider.
        """
        import litellm  # noqa: PLC0415

        _maybe_configure_langfuse()

        model = self._resolve_model(request)
        kwargs = self._build_kwargs(request, model)
        kwargs["stream"] = True

        stream: Any = await litellm.acompletion(**kwargs)
        async for chunk in iter_stream_chunks(stream):
            yield chunk

    async def _call(
        self,
        kwargs: dict[str, Any],
        model: str,
        provider: str,
        ctx: WorkflowContext,
    ) -> LLMResponse:
        """Issue the ``litellm.acompletion()`` call and map to :class:`LLMResponse`.

        Args:
            kwargs: Pre-built keyword arguments for ``acompletion()``.
            model: Resolved litellm model string (used as fallback in the
                response when the API doesn't echo the model name).
            provider: Provider prefix string (stored as ``LLMResponse.provider``).
            ctx: Workflow context — cost is accumulated into
                ``ctx.metadata["llm_cost_usd"]`` after each successful call.

        Returns:
            Mapped :class:`LLMResponse` with ``cost_usd`` populated when
            litellm can compute it for the model.
        """
        import litellm  # noqa: PLC0415

        raw: Any = await litellm.acompletion(**kwargs)
        choice = raw.choices[0]
        msg = choice.message

        content: str = msg.content or ""
        tool_calls = self._parse_tool_calls(getattr(msg, "tool_calls", None))

        usage: dict[str, int] | None = None
        if raw.usage:
            usage = {
                "prompt_tokens": raw.usage.prompt_tokens or 0,
                "completion_tokens": raw.usage.completion_tokens or 0,
                "total_tokens": raw.usage.total_tokens or 0,
            }

        cost_usd: float | None = None
        try:
            cost_usd = litellm.completion_cost(completion_response=raw)
            if cost_usd is not None:
                ctx.metadata["llm_cost_usd"] = (
                    float(ctx.metadata.get("llm_cost_usd", 0.0)) + cost_usd
                )
        except Exception:
            pass  # Cost calculation unsupported for this model — not fatal

        return LLMResponse(
            content=content,
            model=raw.model or model,
            provider=provider,
            usage=usage,
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            cost_usd=cost_usd,
        )


def make_resilient_llm(
    provider: str | LLMProvider | None = None,
    *,
    litellm_fallbacks: list[str] | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
    timeout: float | None = None,
    metadata: dict[str, Any] | None = None,
    retry_attempts: int = 3,
    cache: bool = True,
    cache_ttl_seconds: float = 3600.0,
) -> WorkflowPrimitive[LLMRequest, LLMResponse]:
    """Build a resilient LLM workflow using TTA.dev primitives.

    Delegates to :func:`ttadev.primitives.llm.litellm_factory.make_resilient_llm`.
    Kept here for backward-compatible import from ``litellm_primitive``.

    See :func:`~ttadev.primitives.llm.litellm_factory.make_resilient_llm` for
    full documentation.
    """
    from ttadev.primitives.llm.litellm_factory import (  # noqa: PLC0415
        make_resilient_llm as _make_resilient_llm,
    )

    return _make_resilient_llm(
        provider,
        litellm_fallbacks=litellm_fallbacks,
        api_key=api_key,
        api_base=api_base,
        timeout=timeout,
        metadata=metadata,
        retry_attempts=retry_attempts,
        cache=cache,
        cache_ttl_seconds=cache_ttl_seconds,
    )
