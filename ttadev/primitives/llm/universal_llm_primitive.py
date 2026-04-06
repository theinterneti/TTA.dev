"""UniversalLLMPrimitive — runtime LLM provider abstraction.

Provides a single interface for invoking LLMs across providers
(Groq, Anthropic, OpenAI, Ollama, Gemini, xAI/Grok). Config-driven,
swappable backends.

Note: Distinct from ttadev/integrations/llm/universal_llm_primitive.py
which handles agentic coder budget profiles.

Required environment variables
-------------------------------
Each provider backend reads its credentials from the environment at call time.
``UniversalLLMPrimitive`` accepts an explicit ``api_key`` argument that takes
precedence over the environment variable.

| Provider  | Environment variable(s)                  | SDK package             |
|-----------|------------------------------------------|-------------------------|
| Groq      | ``GROQ_API_KEY``                         | ``groq``                |
| Anthropic | ``ANTHROPIC_API_KEY``                    | ``anthropic``           |
| OpenAI    | ``OPENAI_API_KEY``                       | ``openai``              |
| Ollama    | *(none -- connect to localhost:11434)*   | ``httpx``               |
| Gemini    | ``GOOGLE_API_KEY``                       | ``openai`` (OAI-compat) |
| xAI       | ``XAI_API_KEY``                          | ``openai`` (OAI-compat) |

Install extras::

    uv sync --extra groq        # Groq
    uv sync --extra anthropic   # Anthropic
    uv sync --extra openai      # OpenAI
    # Ollama: run the daemon locally (https://ollama.com)

Implementation layout
---------------------
This file is the thin orchestrator.  Provider-specific logic lives in:

* :mod:`ttadev.primitives.llm._llm_types` -- dataclasses shared by all modules
* :mod:`ttadev.primitives.llm.provider_dispatch` -- non-streaming provider calls
* :mod:`ttadev.primitives.llm.streaming` -- async-generator provider streams
* :mod:`ttadev.primitives.llm.cost_tracker` -- Langfuse usage metadata builder
"""

from __future__ import annotations

import functools
from collections.abc import AsyncIterator
from typing import Any

from ttadev.primitives.core import WorkflowContext, WorkflowPrimitive

# -- Re-export types from _llm_types for backward compatibility ---------------
from ttadev.primitives.llm._llm_types import (  # noqa: F401
    LLMProvider,
    LLMRequest,
    LLMResponse,
    ToolCall,
    ToolSchema,
)
from ttadev.primitives.llm.cost_tracker import build_langfuse_usage
from ttadev.primitives.llm.provider_dispatch import (
    build_openai_tool_kwargs as _build_openai_tool_kwargs_fn,
)
from ttadev.primitives.llm.provider_dispatch import (
    parse_openai_tool_calls as _parse_openai_tool_calls_fn,
)

# Backward-compat alias for tests that import the private name directly
_build_langfuse_usage = build_langfuse_usage

# -- OpenTelemetry -- optional, degrades gracefully when not installed --------
try:
    from opentelemetry import trace as otel_trace

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    otel_trace = None  # type: ignore[assignment]

__all__ = [
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "ToolCall",
    "ToolSchema",
    "UniversalLLMPrimitive",
    "_build_langfuse_usage",
]


class UniversalLLMPrimitive(WorkflowPrimitive[LLMRequest, LLMResponse]):
    """Route LLM requests to the appropriate provider backend.

    Supports native tool-calling for all providers.  Pass a list of
    ``ToolSchema`` objects in ``LLMRequest.tools``; when the model invokes
    tools, ``LLMResponse.tool_calls`` will be populated with ``ToolCall``
    objects.

    Existing callers that omit ``tools`` experience no behaviour change --
    ``LLMResponse.tool_calls`` remains ``None``.
    """

    def __init__(
        self,
        provider: LLMProvider,
        api_key: str | None = None,
        base_url: str | None = None,
        use_compat: bool = False,
    ) -> None:
        super().__init__()
        if not isinstance(provider, LLMProvider):
            raise ValueError(f"Unknown provider: {provider!r}. Use LLMProvider enum.")
        self._provider = provider
        self._api_key = api_key
        self._base_url = base_url
        self._use_compat = use_compat

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def execute(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        """Invoke provider and return a complete response, with OTel tracing."""
        call_fn = self._resolve_call_fn(request, ctx)

        if not (OTEL_AVAILABLE and otel_trace is not None):
            return await call_fn(request, ctx)

        tracer = otel_trace.get_tracer(__name__)
        span_name = f"gen_ai.{self._provider.value}.invoke"
        with tracer.start_as_current_span(span_name) as span:
            span.set_attribute("gen_ai.system", self._provider.value)
            span.set_attribute("gen_ai.request.model", request.model)
            span.set_attribute("gen_ai.request.temperature", request.temperature)
            try:
                response = await call_fn(request, ctx)
            except Exception as e:
                span.record_exception(e)
                from opentelemetry.trace import Status, StatusCode  # noqa: PLC0415

                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
            span.set_attribute("gen_ai.response.model", response.model)
            if response.usage:
                pt = response.usage.get("prompt_tokens") or response.usage.get("input_tokens")
                ct = response.usage.get("completion_tokens") or response.usage.get("output_tokens")
                if pt is not None:
                    span.set_attribute("gen_ai.usage.prompt_tokens", pt)
                if ct is not None:
                    span.set_attribute("gen_ai.usage.completion_tokens", ct)
            try:
                from tta_apm_langfuse import (  # noqa: PLC0415  # type: ignore[import-untyped]
                    get_integration,
                )

                _lf = get_integration()
                if _lf is not None:
                    _lf.create_generation(
                        name=f"{self._provider.value}/{response.model}",
                        model=response.model,
                        input=request.messages,
                        output=response.content,
                        metadata=build_langfuse_usage(self._provider.value, response),
                    )
            except Exception:
                pass
            return response

    async def stream(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        """Yield tokens as they arrive from the provider."""
        stream_fn = self._resolve_stream_fn(request, ctx)
        async for token in stream_fn(request, ctx):
            yield token

    # ------------------------------------------------------------------
    # Dispatch resolution
    # ------------------------------------------------------------------

    def _resolve_call_fn(self, request: LLMRequest, ctx: WorkflowContext):
        """Return the non-streaming call bound method for the current config."""
        from ttadev.primitives.llm.providers import PROVIDERS  # noqa: PLC0415

        spec = PROVIDERS.get(self._provider.value)
        if self._use_compat:
            if not spec or not spec.openai_compat:
                raise ValueError(
                    f"Provider {self._provider.value!r} does not expose an OpenAI-compatible "
                    "endpoint; use_compat=True is not supported for this provider."
                )
            return functools.partial(self._call_openai_compat, provider_name=self._provider.value)

        dispatch: dict[LLMProvider, Any] = {
            LLMProvider.GROQ: self._call_groq,
            LLMProvider.ANTHROPIC: self._call_anthropic,
            LLMProvider.OPENAI: self._call_openai,
            LLMProvider.OLLAMA: self._call_ollama,
            LLMProvider.GOOGLE: self._call_google,
            LLMProvider.OPENROUTER: self._call_openrouter,
            LLMProvider.TOGETHER: self._call_together,
            LLMProvider.XAI: self._call_xai,
        }
        return dispatch[self._provider]

    def _resolve_stream_fn(self, request: LLMRequest, ctx: WorkflowContext):
        """Return the streaming bound method for the current config."""
        from ttadev.primitives.llm.providers import PROVIDERS  # noqa: PLC0415

        spec = PROVIDERS.get(self._provider.value)
        if self._use_compat:
            if not spec or not spec.openai_compat:
                raise ValueError(
                    f"Provider {self._provider.value!r} does not expose an OpenAI-compatible "
                    "endpoint; use_compat=True is not supported for this provider."
                )
            return functools.partial(self._stream_openai_compat, provider_name=self._provider.value)

        dispatch: dict[LLMProvider, Any] = {
            LLMProvider.GROQ: self._stream_groq,
            LLMProvider.ANTHROPIC: self._stream_anthropic,
            LLMProvider.OPENAI: self._stream_openai,
            LLMProvider.OLLAMA: self._stream_ollama,
            LLMProvider.GOOGLE: self._stream_google,
            LLMProvider.OPENROUTER: self._stream_openrouter,
            LLMProvider.TOGETHER: self._stream_together,
            LLMProvider.XAI: self._stream_xai,
        }
        return dispatch[self._provider]

    # ------------------------------------------------------------------
    # Provider call shims (delegate to provider_dispatch module)
    # ------------------------------------------------------------------

    async def _call_groq(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        from ttadev.primitives.llm import provider_dispatch  # noqa: PLC0415

        return await provider_dispatch.call_groq(request, ctx, api_key=self._api_key)

    async def _call_anthropic(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        from ttadev.primitives.llm import provider_dispatch  # noqa: PLC0415

        return await provider_dispatch.call_anthropic(request, ctx, api_key=self._api_key)

    async def _call_openai(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        from ttadev.primitives.llm import provider_dispatch  # noqa: PLC0415

        return await provider_dispatch.call_openai(
            request, ctx, api_key=self._api_key, base_url=self._base_url
        )

    async def _call_ollama(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        from ttadev.primitives.llm import provider_dispatch  # noqa: PLC0415

        return await provider_dispatch.call_ollama(request, ctx, base_url=self._base_url)

    async def _call_google(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        from ttadev.primitives.llm import provider_dispatch  # noqa: PLC0415

        return await provider_dispatch.call_google(request, ctx, api_key=self._api_key)

    async def _call_openrouter(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        from ttadev.primitives.llm import provider_dispatch  # noqa: PLC0415

        return await provider_dispatch.call_openrouter(request, ctx, api_key=self._api_key)

    async def _call_together(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        from ttadev.primitives.llm import provider_dispatch  # noqa: PLC0415

        return await provider_dispatch.call_together(request, ctx, api_key=self._api_key)

    async def _call_xai(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        from ttadev.primitives.llm import provider_dispatch  # noqa: PLC0415

        return await provider_dispatch.call_xai(request, ctx, api_key=self._api_key)

    async def _call_openai_compat(
        self, request: LLMRequest, ctx: WorkflowContext, *, provider_name: str
    ) -> LLMResponse:
        from ttadev.primitives.llm import provider_dispatch  # noqa: PLC0415

        return await provider_dispatch.call_openai_compat(
            request,
            ctx,
            api_key=self._api_key,
            base_url=self._base_url,
            provider_name=provider_name,
        )

    # ------------------------------------------------------------------
    # Provider stream shims (delegate to streaming module)
    # ------------------------------------------------------------------

    async def _stream_groq(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        from ttadev.primitives.llm import streaming  # noqa: PLC0415

        async for token in streaming.stream_groq(request, ctx, api_key=self._api_key):
            yield token

    async def _stream_anthropic(
        self, request: LLMRequest, ctx: WorkflowContext
    ) -> AsyncIterator[str]:
        from ttadev.primitives.llm import streaming  # noqa: PLC0415

        async for token in streaming.stream_anthropic(request, ctx, api_key=self._api_key):
            yield token

    async def _stream_openai(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        from ttadev.primitives.llm import streaming  # noqa: PLC0415

        async for token in streaming.stream_openai(
            request, ctx, api_key=self._api_key, base_url=self._base_url
        ):
            yield token

    async def _stream_ollama(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        from ttadev.primitives.llm import streaming  # noqa: PLC0415

        async for token in streaming.stream_ollama(request, ctx, base_url=self._base_url):
            yield token

    async def _stream_google(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        from ttadev.primitives.llm import streaming  # noqa: PLC0415

        async for token in streaming.stream_google(request, ctx, api_key=self._api_key):
            yield token

    async def _stream_openrouter(
        self, request: LLMRequest, ctx: WorkflowContext
    ) -> AsyncIterator[str]:
        from ttadev.primitives.llm import streaming  # noqa: PLC0415

        async for token in streaming.stream_openrouter(request, ctx, api_key=self._api_key):
            yield token

    async def _stream_together(
        self, request: LLMRequest, ctx: WorkflowContext
    ) -> AsyncIterator[str]:
        from ttadev.primitives.llm import streaming  # noqa: PLC0415

        async for token in streaming.stream_together(request, ctx, api_key=self._api_key):
            yield token

    async def _stream_xai(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        from ttadev.primitives.llm import streaming  # noqa: PLC0415

        async for token in streaming.stream_xai(request, ctx, api_key=self._api_key):
            yield token

    async def _stream_openai_compat(
        self, request: LLMRequest, ctx: WorkflowContext, *, provider_name: str
    ) -> AsyncIterator[str]:
        from ttadev.primitives.llm import streaming  # noqa: PLC0415

        async for token in streaming.stream_openai_compat(
            request,
            ctx,
            api_key=self._api_key,
            base_url=self._base_url,
            provider_name=provider_name,
        ):
            yield token

    # ------------------------------------------------------------------
    # Backward-compat static method shims
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_openai_tool_calls(raw_calls: list[Any] | None) -> list[ToolCall] | None:
        """Backward-compat shim; use provider_dispatch.parse_openai_tool_calls instead."""
        return _parse_openai_tool_calls_fn(raw_calls)

    @staticmethod
    def _build_openai_tool_kwargs(request: LLMRequest) -> dict[str, Any]:
        """Backward-compat shim; use provider_dispatch.build_openai_tool_kwargs instead."""
        return _build_openai_tool_kwargs_fn(request)
