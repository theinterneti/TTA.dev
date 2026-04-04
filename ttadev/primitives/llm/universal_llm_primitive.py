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
| Ollama    | *(none — connect to localhost:11434)*    | ``httpx``               |
| Gemini    | ``GOOGLE_API_KEY``                       | ``openai`` (OAI-compat) |
| xAI       | ``XAI_API_KEY``                          | ``openai`` (OAI-compat) |

Install extras::

    uv sync --extra groq        # Groq
    uv sync --extra anthropic   # Anthropic
    uv sync --extra openai      # OpenAI
    # Ollama: run the daemon locally (https://ollama.com)
    # Gemini and xAI: openai package is a core dependency — no extra needed
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ttadev.primitives.core import WorkflowContext, WorkflowPrimitive

# ── OpenTelemetry — optional, degrades gracefully when not installed ──────────
try:
    from opentelemetry import trace as otel_trace

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    otel_trace = None  # type: ignore[assignment]


class LLMProvider(StrEnum):
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"
    GOOGLE = "google"
    OPENROUTER = "openrouter"
    TOGETHER = "together"
    XAI = "xai"


@dataclass
class ToolSchema:
    """Provider-agnostic tool declaration for native LLM tool-calling.

    Describes a single callable tool that can be passed to an LLM so the
    model may elect to invoke it.  The ``parameters`` field must be a valid
    JSON Schema object (``{"type": "object", "properties": {...}, ...}``).

    Example::

        weather_tool = ToolSchema(
            name="get_weather",
            description="Return current weather for a city.",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        )
    """

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema object for the tool's parameters
    strict: bool = False  # OpenAI strict-mode tool calling

    def to_openai(self) -> dict[str, Any]:
        """Convert to OpenAI function-calling wire format.

        Returns:
            A dict with ``{"type": "function", "function": {...}}`` structure
            as expected by the OpenAI (and OpenAI-compatible) chat completions
            API.  When ``strict=True``, adds the ``"strict": true`` field
            inside the function object to enable structured outputs.
        """
        func: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
        if self.strict:
            func["strict"] = True
        return {"type": "function", "function": func}

    def to_anthropic(self) -> dict[str, Any]:
        """Convert to Anthropic tool_use wire format.

        Returns:
            A dict with ``{"name": ..., "description": ..., "input_schema": ...}``
            structure as expected by the Anthropic Messages API.  The
            ``parameters`` dict is passed verbatim as ``input_schema``; it
            must already be a valid JSON Schema object.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


@dataclass
class ToolCall:
    """A single tool invocation returned by the model.

    Populated in ``LLMResponse.tool_calls`` when the model decides to call
    one or more tools instead of (or in addition to) producing text.

    Attributes:
        id: Provider-assigned call identifier.  Used when sending tool results
            back to the model in the next turn.
        name: The name of the tool that the model wants to invoke.
        arguments: Parsed JSON arguments for the tool call, keyed by parameter
            name.  Always a ``dict`` — never a raw JSON string.
    """

    id: str
    name: str
    arguments: dict[str, Any]  # Parsed from the provider's JSON string


@dataclass
class LLMRequest:
    """Parameters for a single LLM invocation.

    Attributes:
        model: Provider model identifier (e.g. ``"gpt-4o"``, ``"llama3"``).
        messages: Chat history in OpenAI-compatible ``[{"role": ..., "content": ...}]``
            format.
        temperature: Sampling temperature (0–2).  Defaults to ``0.7``.
        max_tokens: Maximum tokens to generate.  ``None`` lets the provider
            decide.
        system: System prompt text.  Injected as a system message for providers
            that support it.
        stream: When ``True``, use the streaming interface (``primitive.stream()``).
        tools: Optional list of tool declarations to expose to the model.
            When ``None`` (default) no tool-calling behaviour is activated.
        tool_choice: How the model should select tools.  Accepted values are
            ``"auto"`` (default), ``"none"``, ``"required"``, or the name of a
            specific tool.
    """

    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.7
    max_tokens: int | None = None
    system: str | None = None
    stream: bool = False
    tools: list[ToolSchema] | None = None
    tool_choice: str = "auto"


@dataclass
class LLMResponse:
    """Result of a single LLM invocation.

    Attributes:
        content: Text content returned by the model.  May be an empty string
            when the model's response consists entirely of tool calls.
        model: Model identifier echoed from the provider response.
        provider: Name of the provider that handled the request (e.g.
            ``"openai"``, ``"anthropic"``).
        usage: Token usage metadata.  Keys vary by provider
            (``prompt_tokens``/``input_tokens``, ``completion_tokens``/
            ``output_tokens``).
        tool_calls: Populated when the model invokes one or more tools.
            ``None`` when the response is plain text (backward-compatible
            default).
        finish_reason: The reason the model stopped generating.  Common values
            are ``"stop"`` (natural end), ``"tool_calls"`` (tool invocation),
            and ``"length"`` (max_tokens reached).  ``None`` for providers
            that do not report a finish reason.
    """

    content: str
    model: str
    provider: str
    usage: dict[str, int] | None = None
    tool_calls: list[ToolCall] | None = None
    finish_reason: str | None = None


def _build_langfuse_usage(provider: str, response: LLMResponse) -> dict[str, Any]:
    """Build a metadata dict with token usage and cost data for Langfuse.

    Extracts prompt/completion token counts from the response and looks up
    per-token pricing to compute USD cost breakdowns.  All failures are caught
    so callers never see an exception from this helper.

    Args:
        provider: Provider name string (e.g. ``"groq"``, ``"openai"``).
        response: The :class:`LLMResponse` returned by the provider.

    Returns:
        Dict with ``usage``, ``cost_details``, and ``cost_tier`` keys.
        Returns a minimal dict if pricing lookup fails.
    """
    usage = response.usage or {}
    prompt_tokens: int | None = usage.get("prompt_tokens") or usage.get("input_tokens")
    completion_tokens: int | None = usage.get("completion_tokens") or usage.get("output_tokens")

    result: dict[str, Any] = {
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
    }

    try:
        from ttadev.primitives.llm.model_pricing import get_pricing  # noqa: PLC0415

        pricing = get_pricing(provider, response.model)
        if pricing is not None:
            input_cost: float | None = None
            output_cost: float | None = None
            if prompt_tokens is not None and pricing.cost_per_1k_input_tokens is not None:
                input_cost = prompt_tokens * pricing.cost_per_1k_input_tokens / 1000.0
            if completion_tokens is not None and pricing.cost_per_1k_output_tokens is not None:
                output_cost = completion_tokens * pricing.cost_per_1k_output_tokens / 1000.0
            total_cost: float | None = None
            if input_cost is not None and output_cost is not None:
                total_cost = input_cost + output_cost
            result["cost_details"] = {
                "input_cost_usd": input_cost,
                "output_cost_usd": output_cost,
                "total_cost_usd": total_cost,
            }
            result["cost_tier"] = pricing.cost_tier
    except Exception:
        pass

    return result


class UniversalLLMPrimitive(WorkflowPrimitive[LLMRequest, LLMResponse]):
    """Route LLM requests to the appropriate provider backend.

    Supports native tool-calling for all providers.  Pass a list of
    ``ToolSchema`` objects in ``LLMRequest.tools``; when the model invokes
    tools, ``LLMResponse.tool_calls`` will be populated with ``ToolCall``
    objects.

    Existing callers that omit ``tools`` experience no behaviour change —
    ``LLMResponse.tool_calls`` remains ``None``.
    """

    def __init__(
        self,
        provider: LLMProvider,
        api_key: str | None = None,
        base_url: str | None = None,
        use_compat: bool = False,
    ) -> None:
        """Create a :class:`UniversalLLMPrimitive` for the given provider.

        Args:
            provider: Which LLM provider to route requests to.
            api_key: Provider API key.  When ``None`` the key is read from the
                environment variable specified in :data:`~.providers.PROVIDERS`.
            base_url: Override the provider's base URL (useful for proxies and
                self-hosted models).
            use_compat: When ``True``, force the generic OpenAI-compatible HTTP
                path even for providers whose :attr:`~.providers.ProviderSpec.preferred_path`
                is ``"sdk"`` (e.g. Groq uses its native SDK by default, but
                ``use_compat=True`` routes through ``api.groq.com/openai/v1``
                instead).  Only valid for providers with ``openai_compat=True``
                in the registry.  Anthropic raises :exc:`ValueError` because it
                does not expose an OpenAI-compatible endpoint.
        """
        super().__init__()
        if not isinstance(provider, LLMProvider):
            raise ValueError(f"Unknown provider: {provider!r}. Use LLMProvider enum.")
        self._provider = provider
        self._api_key = api_key
        self._base_url = base_url
        self._use_compat = use_compat

    async def execute(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        """Invoke provider and return a complete response, with OTel tracing.

        Respects ``use_compat``: when ``True`` and the provider has an
        OpenAI-compatible endpoint, routes through :meth:`_call_openai_compat`
        instead of the provider-specific SDK method.
        """
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
            # Langfuse generation tracking (optional — fails silently)
            try:
                from tta_apm_langfuse import get_integration  # noqa: PLC0415

                _lf = get_integration()
                if _lf is not None:
                    _lf.create_generation(
                        name=f"{self._provider.value}/{response.model}",
                        model=response.model,
                        input=request.messages,
                        output=response.content,
                        metadata=_build_langfuse_usage(self._provider.value, response),
                    )
            except Exception:
                pass
            return response

    async def stream(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        """Yield tokens as they arrive from the provider.

        Respects ``use_compat``: when ``True`` and the provider has an
        OpenAI-compatible endpoint, routes through :meth:`_stream_openai_compat`
        instead of the provider-specific SDK stream method.

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context.

        Yields:
            Token strings as they stream from the provider.
        """
        stream_fn = self._resolve_stream_fn(request, ctx)
        async for token in stream_fn(request, ctx):
            yield token

    def _resolve_call_fn(
        self, request: LLMRequest, ctx: WorkflowContext
    ):  # -> Callable[..., Awaitable[LLMResponse]]
        """Return the non-streaming call coroutine for the current configuration.

        When ``use_compat=True``, returns a bound partial of
        :meth:`_call_openai_compat` if the provider supports it, otherwise
        falls back to the provider-specific method.
        """
        from ttadev.primitives.llm.providers import PROVIDERS  # noqa: PLC0415

        spec = PROVIDERS.get(self._provider.value)
        if self._use_compat:
            if not spec or not spec.openai_compat:
                raise ValueError(
                    f"Provider {self._provider.value!r} does not expose an OpenAI-compatible "
                    "endpoint; use_compat=True is not supported for this provider."
                )
            import functools  # noqa: PLC0415

            return functools.partial(self._call_openai_compat, provider_name=self._provider.value)

        dispatch: dict = {
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

    def _resolve_stream_fn(
        self, request: LLMRequest, ctx: WorkflowContext
    ):  # -> Callable[..., AsyncIterator[str]]
        """Return the streaming call coroutine for the current configuration."""
        from ttadev.primitives.llm.providers import PROVIDERS  # noqa: PLC0415

        spec = PROVIDERS.get(self._provider.value)
        if self._use_compat:
            if not spec or not spec.openai_compat:
                raise ValueError(
                    f"Provider {self._provider.value!r} does not expose an OpenAI-compatible "
                    "endpoint; use_compat=True is not supported for this provider."
                )
            import functools  # noqa: PLC0415

            return functools.partial(self._stream_openai_compat, provider_name=self._provider.value)

        dispatch: dict = {
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

    @staticmethod
    def _parse_openai_tool_calls(raw_calls: object) -> list[ToolCall] | None:
        """Parse OpenAI-compat tool_calls from a response message.

        Handles the OpenAI wire format where ``arguments`` is a JSON string
        that must be decoded before returning.

        Args:
            raw_calls: The ``tool_calls`` attribute from an OpenAI-compat
                response message object.  May be ``None`` or an empty sequence.

        Returns:
            A list of ``ToolCall`` objects, or ``None`` when no tool calls are
            present.
        """
        if not raw_calls:
            return None
        return [
            ToolCall(
                id=tc.id,
                name=tc.function.name,
                arguments=json.loads(tc.function.arguments),
            )
            for tc in raw_calls
        ]

    @staticmethod
    def _build_openai_tool_kwargs(request: LLMRequest) -> dict[str, Any]:
        """Build extra kwargs to pass to OpenAI-compat ``chat.completions.create``.

        When ``request.tools`` is ``None`` returns an empty dict so that
        existing callers are unaffected.

        Args:
            request: The current LLM request.

        Returns:
            A dict containing ``tools`` and ``tool_choice`` keys when tools
            are declared, otherwise an empty dict.
        """
        if not request.tools:
            return {}
        return {
            "tools": [t.to_openai() for t in request.tools],
            "tool_choice": request.tool_choice,
        }

    # ── Non-streaming provider calls ──────────────────────────────────────────

    async def _call_openai_compat(
        self, request: LLMRequest, ctx: WorkflowContext, *, provider_name: str
    ) -> LLMResponse:
        """Generic non-streaming call for any OpenAI-compatible provider.

        Used when ``use_compat=True`` is passed to the constructor, or directly
        by providers whose :attr:`~.providers.ProviderSpec.preferred_path` is
        ``"compat"`` (Gemini, OpenRouter, Together, xAI, Ollama, HuggingFace).

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context (unused, kept for interface parity).
            provider_name: Canonical provider key in :data:`~.providers.PROVIDERS`.

        Returns:
            LLMResponse with content, model, provider, usage metadata, and
            optional tool_calls / finish_reason.

        Raises:
            ValueError: If the provider is not in the registry, does not support
                OpenAI-compat, or no API key is available.
            KeyError: If *provider_name* is not in :data:`~.providers.PROVIDERS`.
        """
        import os  # noqa: PLC0415

        from openai import AsyncOpenAI  # noqa: PLC0415

        from ttadev.primitives.llm.providers import PROVIDERS  # noqa: PLC0415

        spec = PROVIDERS[provider_name]
        if not spec.openai_compat:
            raise ValueError(
                f"Provider {provider_name!r} does not support the OpenAI-compatible "
                "HTTP endpoint.  Remove use_compat=True or use the native SDK path."
            )
        key = self._api_key or (os.getenv(spec.env_var) if spec.env_var else "no-key")
        if not key and spec.env_var:
            raise ValueError(
                f"{spec.env_var} is not set. "
                "Set it in your environment or pass api_key to UniversalLLMPrimitive."
            )
        client = AsyncOpenAI(
            api_key=key or "no-key",
            base_url=self._base_url or spec.base_url,
            default_headers=spec.extra_headers,
        )
        resp = await client.chat.completions.create(
            model=request.model or spec.default_model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            **self._build_openai_tool_kwargs(request),
        )
        choice = resp.choices[0]
        raw_tc = getattr(choice.message, "tool_calls", None)
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            provider=provider_name,
            usage={
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
            }
            if resp.usage
            else None,
            tool_calls=self._parse_openai_tool_calls(raw_tc),
            finish_reason=getattr(choice, "finish_reason", None),
        )

    async def _stream_openai_compat(
        self, request: LLMRequest, ctx: WorkflowContext, *, provider_name: str
    ) -> AsyncIterator[str]:
        """Generic streaming call for any OpenAI-compatible provider.

        Used when ``use_compat=True`` is passed to the constructor, or directly
        by providers whose preferred path is ``"compat"``.

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context.
            provider_name: Canonical provider key in :data:`~.providers.PROVIDERS`.

        Yields:
            Token strings as they arrive from the provider.

        Raises:
            ValueError: If the provider does not support OpenAI-compat or
                no API key is available.
        """
        import os  # noqa: PLC0415

        from openai import AsyncOpenAI  # noqa: PLC0415

        from ttadev.primitives.llm.providers import PROVIDERS  # noqa: PLC0415

        spec = PROVIDERS[provider_name]
        if not spec.openai_compat:
            raise ValueError(
                f"Provider {provider_name!r} does not support the OpenAI-compatible "
                "HTTP endpoint.  Remove use_compat=True or use the native SDK path."
            )
        key = self._api_key or (os.getenv(spec.env_var) if spec.env_var else "no-key")
        if not key and spec.env_var:
            raise ValueError(
                f"{spec.env_var} is not set. "
                "Set it in your environment or pass api_key to UniversalLLMPrimitive."
            )
        client = AsyncOpenAI(
            api_key=key or "no-key",
            base_url=self._base_url or spec.base_url,
            default_headers=spec.extra_headers,
        )
        async with await client.chat.completions.create(
            model=request.model or spec.default_model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
        ) as stream:
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content

    # ── Non-streaming provider calls ──────────────────────────────────────────

    async def _call_groq(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        """Call Groq via the groq SDK.

        Supports native tool-calling when ``request.tools`` is provided.

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context.

        Returns:
            LLMResponse with content, model, provider, usage metadata, and
            optional tool_calls / finish_reason.
        """
        from groq import AsyncGroq  # type: ignore[import]

        client = AsyncGroq(api_key=self._api_key)
        resp = await client.chat.completions.create(
            model=request.model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            **self._build_openai_tool_kwargs(request),
        )
        choice = resp.choices[0]
        raw_tc = getattr(choice.message, "tool_calls", None)
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            provider="groq",
            usage={
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
            }
            if resp.usage
            else None,
            tool_calls=self._parse_openai_tool_calls(raw_tc),
            finish_reason=getattr(choice, "finish_reason", None),
        )

    async def _call_anthropic(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        """Call Anthropic via the anthropic SDK.

        Supports native tool-calling when ``request.tools`` is provided.
        When the model returns ``tool_use`` blocks, they are parsed into
        ``ToolCall`` objects.  Text blocks are returned in ``content``; when
        there are no text blocks (pure tool-call response), ``content`` is
        an empty string.

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context.

        Returns:
            LLMResponse with content, model, provider, usage metadata, and
            optional tool_calls / finish_reason.
        """
        import anthropic  # type: ignore[import]

        client = anthropic.AsyncAnthropic(api_key=self._api_key)

        create_kwargs: dict[str, Any] = {}
        if request.tools:
            create_kwargs["tools"] = [t.to_anthropic() for t in request.tools]

        resp = await client.messages.create(
            model=request.model,
            max_tokens=request.max_tokens or 1024,
            system=request.system or "",
            messages=request.messages,  # type: ignore[arg-type]
            **create_kwargs,
        )

        # Separate tool_use blocks from text blocks
        tool_use_blocks = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
        tool_calls: list[ToolCall] | None = None
        if tool_use_blocks:
            tool_calls = [
                ToolCall(id=b.id, name=b.name, arguments=b.input) for b in tool_use_blocks
            ]

        # Extract text: prefer typed text blocks; fall back for mocks without type
        text_blocks = [b for b in resp.content if getattr(b, "type", None) == "text"]
        if text_blocks:
            content = text_blocks[0].text
        elif resp.content and hasattr(resp.content[0], "text"):
            content = resp.content[0].text
        else:
            content = ""

        return LLMResponse(
            content=content,
            model=resp.model,
            provider="anthropic",
            usage={
                "input_tokens": resp.usage.input_tokens,
                "output_tokens": resp.usage.output_tokens,
            },
            tool_calls=tool_calls,
            finish_reason=getattr(resp, "stop_reason", None),
        )

    async def _call_openai(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        """Call OpenAI via the openai SDK.

        Supports native tool-calling when ``request.tools`` is provided.

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context.

        Returns:
            LLMResponse with content, model, provider, usage metadata, and
            optional tool_calls / finish_reason.
        """
        from openai import AsyncOpenAI  # type: ignore[import]

        client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
        resp = await client.chat.completions.create(
            model=request.model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            **self._build_openai_tool_kwargs(request),
        )
        choice = resp.choices[0]
        raw_tc = getattr(choice.message, "tool_calls", None)
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            provider="openai",
            usage={
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
            }
            if resp.usage
            else None,
            tool_calls=self._parse_openai_tool_calls(raw_tc),
            finish_reason=getattr(choice, "finish_reason", None),
        )

    async def _call_ollama(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        """Call Ollama /api/chat (non-streaming).

        Supports tool-calling via the ``tools`` key in the JSON payload when
        ``request.tools`` is provided.  Ollama uses the same OpenAI function
        schema format (``{"type": "function", "function": {...}}``).

        Note: Not all Ollama models support tool-calling.  When the model
        returns no ``tool_calls`` in its response message and ``finish_reason``
        is not ``"tool_calls"``, the response is treated as plain text.

        Supports full Ollama options: num_ctx, keep_alive, think mode, system
        messages, structured output via format, and all sampling parameters.
        Pass extra Ollama options via request.extra (dict).  Example::

            LLMRequest(
                model="qwen3:1.7b",
                messages=[...],
                extra={
                    "think": True,           # enable chain-of-thought
                    "keep_alive": "10m",     # keep model loaded for 10 min
                    "format": "json",        # structured JSON output
                    "num_ctx": 8192,         # context window size
                    "num_gpu": -1,           # all GPU layers
                },
            )

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context.

        Returns:
            LLMResponse with content, model, provider, and optional
            tool_calls / finish_reason.
        """
        import httpx

        base = self._base_url or "http://localhost:11434"
        extra: dict = getattr(request, "extra", None) or {}

        # Build Ollama options — allow callers to override any option
        options: dict = {"temperature": request.temperature}
        if request.max_tokens:
            options["num_predict"] = request.max_tokens
        for key in ("num_ctx", "top_p", "top_k", "repeat_penalty", "seed", "num_gpu", "num_thread"):
            if key in extra:
                options[key] = extra[key]

        # Build messages — inject system prompt if present
        messages = list(request.messages)
        if request.system and not any(m.get("role") == "system" for m in messages):
            messages = [{"role": "system", "content": request.system}] + messages

        payload: dict = {
            "model": request.model,
            "messages": messages,
            "stream": False,
            # Default: disable thinking mode (Qwen3/QwQ put all output in
            # message.thinking when think=True, leaving content empty)
            "think": extra.get("think", False),
            "options": options,
        }
        if "keep_alive" in extra:
            payload["keep_alive"] = extra["keep_alive"]
        if "format" in extra:
            payload["format"] = extra["format"]

        # Native tool-calling: Ollama uses the same format as OpenAI
        if request.tools:
            payload["tools"] = [t.to_openai() for t in request.tools]

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{base}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        msg = data["message"]

        # Parse tool calls when present
        ollama_tc = msg.get("tool_calls") or []
        tool_calls: list[ToolCall] | None = None
        if ollama_tc:
            tool_calls = [
                ToolCall(
                    id=f"ollama_call_{i}",
                    name=tc["function"]["name"],
                    # Ollama returns arguments as a dict, not a JSON string
                    arguments=tc["function"]["arguments"],
                )
                for i, tc in enumerate(ollama_tc)
            ]

        content = msg.get("content") or msg.get("thinking", "")
        finish_reason = "tool_calls" if tool_calls else "stop"

        return LLMResponse(
            content=content,
            model=request.model,
            provider="ollama",
            tool_calls=tool_calls,
            finish_reason=finish_reason,
        )

    # ── Streaming provider calls ───────────────────────────────────────────────

    async def _stream_groq(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        """Stream tokens from Groq."""
        from groq import AsyncGroq  # type: ignore[import]

        client = AsyncGroq(api_key=self._api_key)
        resp = await client.chat.completions.create(
            model=request.model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
        )
        async for chunk in resp:
            content = chunk.choices[0].delta.content or ""
            if content:
                yield content

    async def _stream_anthropic(
        self, request: LLMRequest, ctx: WorkflowContext
    ) -> AsyncIterator[str]:
        """Stream tokens from Anthropic via messages.stream() context manager."""
        import anthropic  # type: ignore[import]

        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        async with client.messages.stream(
            model=request.model,
            max_tokens=request.max_tokens or 1024,
            system=request.system or "",
            messages=request.messages,  # type: ignore[arg-type]
        ) as stream:
            async for text in stream.text_stream:
                if text:
                    yield text

    async def _stream_openai(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        """Stream tokens from OpenAI."""
        from openai import AsyncOpenAI  # type: ignore[import]

        client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
        resp = await client.chat.completions.create(
            model=request.model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
        )
        async for chunk in resp:
            content = chunk.choices[0].delta.content or ""
            if content:
                yield content

    async def _stream_ollama(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        """Stream tokens from Ollama /api/chat (NDJSON chunks).

        Respects the same ``request.extra`` options as :meth:`_call_ollama`.
        When ``think=True`` is passed, thinking tokens from the ``thinking``
        field are also yielded (prefixed with the raw thinking text).
        """
        import httpx

        base = self._base_url or "http://localhost:11434"
        extra: dict = getattr(request, "extra", None) or {}

        options: dict = {"temperature": request.temperature}
        if request.max_tokens:
            options["num_predict"] = request.max_tokens
        for key in ("num_ctx", "top_p", "top_k", "repeat_penalty", "seed", "num_gpu", "num_thread"):
            if key in extra:
                options[key] = extra[key]

        messages = list(request.messages)
        if request.system and not any(m.get("role") == "system" for m in messages):
            messages = [{"role": "system", "content": request.system}] + messages

        think = extra.get("think", False)
        payload: dict = {
            "model": request.model,
            "messages": messages,
            "stream": True,
            "think": think,
            "options": options,
        }
        if "keep_alive" in extra:
            payload["keep_alive"] = extra["keep_alive"]
        if "format" in extra:
            payload["format"] = extra["format"]

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{base}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    msg = data.get("message", {})
                    content = msg.get("content", "")
                    if content:
                        yield content
                    elif think and msg.get("thinking"):
                        # When thinking mode is on, yield thinking tokens too
                        yield msg["thinking"]
                    if data.get("done"):
                        break

    async def _call_google(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        """Call Google Gemini via its OpenAI-compatible endpoint.

        Uses ``https://generativelanguage.googleapis.com/v1beta/openai`` — no
        ``google-generativeai`` SDK required.  Model IDs must carry the
        ``models/`` prefix (e.g. ``models/gemini-2.5-flash-lite``).

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context.

        Returns:
            LLMResponse with content, model, provider, usage metadata, and
            optional tool_calls / finish_reason.

        Raises:
            ValueError: If no API key is available from the argument or environment.
        """
        import os

        from openai import AsyncOpenAI

        from ttadev.primitives.llm.providers import PROVIDERS

        spec = PROVIDERS["google"]
        key = self._api_key or os.getenv(spec.env_var)
        if not key:
            raise ValueError(
                "GOOGLE_API_KEY is not set. "
                "Set it in your environment or pass api_key to UniversalLLMPrimitive."
            )
        client = AsyncOpenAI(api_key=key, base_url=spec.base_url)
        resp = await client.chat.completions.create(
            model=request.model or spec.default_model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            **self._build_openai_tool_kwargs(request),
        )
        choice = resp.choices[0]
        raw_tc = getattr(choice.message, "tool_calls", None)
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            provider="google",
            usage={
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
            }
            if resp.usage
            else None,
            tool_calls=self._parse_openai_tool_calls(raw_tc),
            finish_reason=getattr(choice, "finish_reason", None),
        )

    async def _stream_google(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        """Stream tokens from Google Gemini via its OpenAI-compatible endpoint.

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context.

        Yields:
            Token strings as they stream from Gemini.

        Raises:
            ValueError: If no API key is available from the argument or environment.
        """
        import os

        from openai import AsyncOpenAI

        from ttadev.primitives.llm.providers import PROVIDERS

        spec = PROVIDERS["google"]
        key = self._api_key or os.getenv(spec.env_var)
        if not key:
            raise ValueError(
                "GOOGLE_API_KEY is not set. "
                "Set it in your environment or pass api_key to UniversalLLMPrimitive."
            )
        client = AsyncOpenAI(api_key=key, base_url=spec.base_url)
        resp = await client.chat.completions.create(
            model=request.model or spec.default_model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
        )
        async for chunk in resp:
            content = chunk.choices[0].delta.content or ""
            if content:
                yield content

    # ── OpenRouter (openai SDK, OpenAI-compat) ────────────────────────────────

    async def _call_openrouter(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        """Call OpenRouter via the openai SDK using its OpenAI-compatible endpoint.

        Reads credentials and required headers from the central provider registry.
        Requires ``OPENROUTER_API_KEY`` in the environment or ``api_key`` argument.
        Supports native tool-calling when ``request.tools`` is provided.

        Args:
            request: LLM invocation parameters. ``request.model`` defaults to the
                provider's ``default_model`` when not specified.
            ctx: Workflow execution context (unused directly, kept for interface parity).

        Returns:
            LLMResponse with content, model, provider, usage metadata, and
            optional tool_calls / finish_reason.

        Raises:
            ValueError: If no API key is available from the argument or environment.
        """
        import os

        from openai import AsyncOpenAI

        from ttadev.primitives.llm.providers import PROVIDERS

        spec = PROVIDERS["openrouter"]
        key = self._api_key or os.getenv(spec.env_var)
        if not key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. "
                "Set it in your environment or pass api_key to UniversalLLMPrimitive."
            )
        client = AsyncOpenAI(
            api_key=key,
            base_url=spec.base_url,
            default_headers=spec.extra_headers,
        )
        resp = await client.chat.completions.create(
            model=request.model or spec.default_model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            **self._build_openai_tool_kwargs(request),
        )
        choice = resp.choices[0]
        raw_tc = getattr(choice.message, "tool_calls", None)
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            provider="openrouter",
            usage={
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
            }
            if resp.usage
            else None,
            tool_calls=self._parse_openai_tool_calls(raw_tc),
            finish_reason=getattr(choice, "finish_reason", None),
        )

    async def _stream_openrouter(
        self, request: LLMRequest, ctx: WorkflowContext
    ) -> AsyncIterator[str]:
        """Stream tokens from OpenRouter via the openai SDK.

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context.

        Yields:
            Token strings as they stream from OpenRouter.

        Raises:
            ValueError: If no API key is available from the argument or environment.
        """
        import os

        from openai import AsyncOpenAI

        from ttadev.primitives.llm.providers import PROVIDERS

        spec = PROVIDERS["openrouter"]
        key = self._api_key or os.getenv(spec.env_var)
        if not key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. "
                "Set it in your environment or pass api_key to UniversalLLMPrimitive."
            )
        client = AsyncOpenAI(
            api_key=key,
            base_url=spec.base_url,
            default_headers=spec.extra_headers,
        )
        resp = await client.chat.completions.create(
            model=request.model or spec.default_model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
        )
        async for chunk in resp:
            content = chunk.choices[0].delta.content or ""
            if content:
                yield content

    # ── Together AI (openai SDK, OpenAI-compat) ───────────────────────────────

    async def _call_together(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        """Call Together AI via the openai SDK using its OpenAI-compatible endpoint.

        Reads credentials from the central provider registry.
        Requires ``TOGETHER_API_KEY`` in the environment or ``api_key`` argument.
        Supports native tool-calling when ``request.tools`` is provided.

        Args:
            request: LLM invocation parameters. ``request.model`` defaults to the
                provider's ``default_model`` when not specified.
            ctx: Workflow execution context (unused directly, kept for interface parity).

        Returns:
            LLMResponse with content, model, provider, usage metadata, and
            optional tool_calls / finish_reason.

        Raises:
            ValueError: If no API key is available from the argument or environment.
        """
        import os

        from openai import AsyncOpenAI

        from ttadev.primitives.llm.providers import PROVIDERS

        spec = PROVIDERS["together"]
        key = self._api_key or os.getenv(spec.env_var)
        if not key:
            raise ValueError(
                "TOGETHER_API_KEY is not set. "
                "Set it in your environment or pass api_key to UniversalLLMPrimitive."
            )
        client = AsyncOpenAI(api_key=key, base_url=spec.base_url)
        resp = await client.chat.completions.create(
            model=request.model or spec.default_model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            **self._build_openai_tool_kwargs(request),
        )
        choice = resp.choices[0]
        raw_tc = getattr(choice.message, "tool_calls", None)
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            provider="together",
            usage={
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
            }
            if resp.usage
            else None,
            tool_calls=self._parse_openai_tool_calls(raw_tc),
            finish_reason=getattr(choice, "finish_reason", None),
        )

    async def _stream_together(
        self, request: LLMRequest, ctx: WorkflowContext
    ) -> AsyncIterator[str]:
        """Stream tokens from Together AI via the openai SDK.

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context.

        Yields:
            Token strings as they stream from Together AI.

        Raises:
            ValueError: If no API key is available from the argument or environment.
        """
        import os

        from openai import AsyncOpenAI

        from ttadev.primitives.llm.providers import PROVIDERS

        spec = PROVIDERS["together"]
        key = self._api_key or os.getenv(spec.env_var)
        if not key:
            raise ValueError(
                "TOGETHER_API_KEY is not set. "
                "Set it in your environment or pass api_key to UniversalLLMPrimitive."
            )
        client = AsyncOpenAI(api_key=key, base_url=spec.base_url)
        resp = await client.chat.completions.create(
            model=request.model or spec.default_model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
        )
        async for chunk in resp:
            content = chunk.choices[0].delta.content or ""
            if content:
                yield content

    # ── xAI / Grok (openai SDK, OpenAI-compat) ───────────────────────────────

    async def _call_xai(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        """Call xAI (Grok) via the openai SDK using its OpenAI-compatible endpoint.

        xAI's API speaks the OpenAI wire format; the ``openai`` SDK works without
        any modification — just point it at ``https://api.x.ai/v1`` with an
        ``XAI_API_KEY``.

        Reads credentials from the central provider registry.
        Requires ``XAI_API_KEY`` in the environment or ``api_key`` argument.
        Supports native tool-calling when ``request.tools`` is provided.

        Args:
            request: LLM invocation parameters. ``request.model`` defaults to
                ``grok-3-mini`` when not specified.
            ctx: Workflow execution context (unused directly, kept for interface parity).

        Returns:
            LLMResponse with content, model, provider, usage metadata, and
            optional tool_calls / finish_reason.

        Raises:
            ValueError: If no API key is available from the argument or environment.
        """
        import os

        from openai import AsyncOpenAI

        from ttadev.primitives.llm.providers import PROVIDERS

        spec = PROVIDERS["xai"]
        key = self._api_key or os.getenv(spec.env_var)
        if not key:
            raise ValueError(
                "XAI_API_KEY is not set. "
                "Set it in your environment or pass api_key to UniversalLLMPrimitive."
            )
        client = AsyncOpenAI(api_key=key, base_url=spec.base_url)
        resp = await client.chat.completions.create(
            model=request.model or spec.default_model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            **self._build_openai_tool_kwargs(request),
        )
        choice = resp.choices[0]
        raw_tc = getattr(choice.message, "tool_calls", None)
        return LLMResponse(
            content=choice.message.content or "",
            model=resp.model,
            provider="xai",
            usage={
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
            }
            if resp.usage
            else None,
            tool_calls=self._parse_openai_tool_calls(raw_tc),
            finish_reason=getattr(choice, "finish_reason", None),
        )

    async def _stream_xai(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        """Stream tokens from xAI (Grok) via the openai SDK.

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context.

        Yields:
            Token strings as they stream from xAI.

        Raises:
            ValueError: If no API key is available from the argument or environment.
        """
        import os

        from openai import AsyncOpenAI

        from ttadev.primitives.llm.providers import PROVIDERS

        spec = PROVIDERS["xai"]
        key = self._api_key or os.getenv(spec.env_var)
        if not key:
            raise ValueError(
                "XAI_API_KEY is not set. "
                "Set it in your environment or pass api_key to UniversalLLMPrimitive."
            )
        client = AsyncOpenAI(api_key=key, base_url=spec.base_url)
        resp = await client.chat.completions.create(
            model=request.model or spec.default_model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=True,
        )
        async for chunk in resp:
            content = chunk.choices[0].delta.content or ""
            if content:
                yield content
