"""Per-provider non-streaming call logic for UniversalLLMPrimitive.

Each function dispatches a single LLMRequest to the appropriate provider SDK
and returns a complete LLMResponse.  Provider SDK imports are deferred to
function bodies so that importing this module never raises ImportError for
SDKs that aren't installed.
"""

from __future__ import annotations

import json
from typing import Any

from ttadev.primitives.core import WorkflowContext
from ttadev.primitives.llm._llm_types import LLMRequest, LLMResponse, ToolCall

# ── Shared helpers ────────────────────────────────────────────────────────────


def parse_openai_tool_calls(raw_calls: list[Any] | None) -> list[ToolCall] | None:
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


def build_openai_tool_kwargs(request: LLMRequest) -> dict[str, Any]:
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


# ── Generic OpenAI-compatible call ───────────────────────────────────────────


async def call_openai_compat(
    request: LLMRequest,
    ctx: WorkflowContext,
    *,
    api_key: str | None,
    base_url: str | None,
    provider_name: str,
) -> LLMResponse:
    """Generic non-streaming call for any OpenAI-compatible provider.

    Used when ``use_compat=True`` is passed to the constructor, or directly
    by providers whose :attr:`~.providers.ProviderSpec.preferred_path` is
    ``"compat"`` (Gemini, OpenRouter, Together, xAI, Ollama, HuggingFace).

    Args:
        request: LLM invocation parameters.
        ctx: Workflow execution context (unused, kept for interface parity).
        api_key: Optional API key override; falls back to env var from registry.
        base_url: Optional base URL override; falls back to registry default.
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
    key = api_key or (os.getenv(spec.env_var) if spec.env_var else "no-key")
    if not key and spec.env_var:
        raise ValueError(
            f"{spec.env_var} is not set. "
            "Set it in your environment or pass api_key to UniversalLLMPrimitive."
        )
    client = AsyncOpenAI(
        api_key=key or "no-key",
        base_url=base_url or spec.base_url,
        default_headers=spec.extra_headers,
    )
    resp = await client.chat.completions.create(
        model=request.model or spec.default_model,
        messages=request.messages,  # type: ignore[arg-type]
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        **build_openai_tool_kwargs(request),
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
        tool_calls=parse_openai_tool_calls(raw_tc),
        finish_reason=getattr(choice, "finish_reason", None),
    )


# ── Native SDK provider calls ─────────────────────────────────────────────────


async def call_groq(
    request: LLMRequest, ctx: WorkflowContext, *, api_key: str | None
) -> LLMResponse:
    """Call Groq via the groq SDK.

    Supports native tool-calling when ``request.tools`` is provided.

    Args:
        request: LLM invocation parameters.
        ctx: Workflow execution context.
        api_key: Optional API key (falls back to ``GROQ_API_KEY`` env var).

    Returns:
        LLMResponse with content, model, provider, usage metadata, and
        optional tool_calls / finish_reason.
    """
    from groq import AsyncGroq  # type: ignore[import]

    client = AsyncGroq(api_key=api_key)
    resp = await client.chat.completions.create(
        model=request.model,
        messages=request.messages,  # type: ignore[arg-type]
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        **build_openai_tool_kwargs(request),
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
        tool_calls=parse_openai_tool_calls(raw_tc),
        finish_reason=getattr(choice, "finish_reason", None),
    )


async def call_anthropic(
    request: LLMRequest, ctx: WorkflowContext, *, api_key: str | None
) -> LLMResponse:
    """Call Anthropic via the anthropic SDK.

    Supports native tool-calling when ``request.tools`` is provided.
    When the model returns ``tool_use`` blocks, they are parsed into
    ``ToolCall`` objects.  Text blocks are returned in ``content``; when
    there are no text blocks (pure tool-call response), ``content`` is
    an empty string.

    Args:
        request: LLM invocation parameters.
        ctx: Workflow execution context.
        api_key: Optional API key (falls back to ``ANTHROPIC_API_KEY`` env var).

    Returns:
        LLMResponse with content, model, provider, usage metadata, and
        optional tool_calls / finish_reason.
    """
    import anthropic  # type: ignore[import]

    client = anthropic.AsyncAnthropic(api_key=api_key)

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
        tool_calls = [ToolCall(id=b.id, name=b.name, arguments=b.input) for b in tool_use_blocks]

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


async def call_openai(
    request: LLMRequest, ctx: WorkflowContext, *, api_key: str | None, base_url: str | None
) -> LLMResponse:
    """Call OpenAI via the openai SDK.

    Supports native tool-calling when ``request.tools`` is provided.

    Args:
        request: LLM invocation parameters.
        ctx: Workflow execution context.
        api_key: Optional API key (falls back to ``OPENAI_API_KEY`` env var).
        base_url: Optional base URL override.

    Returns:
        LLMResponse with content, model, provider, usage metadata, and
        optional tool_calls / finish_reason.
    """
    from openai import AsyncOpenAI  # type: ignore[import]

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    resp = await client.chat.completions.create(
        model=request.model,
        messages=request.messages,  # type: ignore[arg-type]
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        **build_openai_tool_kwargs(request),
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
        tool_calls=parse_openai_tool_calls(raw_tc),
        finish_reason=getattr(choice, "finish_reason", None),
    )


async def call_ollama(
    request: LLMRequest, ctx: WorkflowContext, *, base_url: str | None
) -> LLMResponse:
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
        base_url: Optional base URL override (default: ``http://localhost:11434``).

    Returns:
        LLMResponse with content, model, provider, and optional
        tool_calls / finish_reason.
    """
    import httpx

    base = base_url or "http://localhost:11434"
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


# ── OpenAI-compat provider calls ──────────────────────────────────────────────


async def call_google(
    request: LLMRequest, ctx: WorkflowContext, *, api_key: str | None
) -> LLMResponse:
    """Call Google Gemini via its OpenAI-compatible endpoint.

    Uses ``https://generativelanguage.googleapis.com/v1beta/openai`` — no
    ``google-generativeai`` SDK required.  Model IDs must carry the
    ``models/`` prefix (e.g. ``models/gemini-2.5-flash-lite``).

    Args:
        request: LLM invocation parameters.
        ctx: Workflow execution context.
        api_key: Optional API key (falls back to ``GOOGLE_API_KEY`` env var).

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
    key = api_key or os.getenv(spec.env_var)
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
        **build_openai_tool_kwargs(request),
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
        tool_calls=parse_openai_tool_calls(raw_tc),
        finish_reason=getattr(choice, "finish_reason", None),
    )


async def call_openrouter(
    request: LLMRequest, ctx: WorkflowContext, *, api_key: str | None
) -> LLMResponse:
    """Call OpenRouter via the openai SDK using its OpenAI-compatible endpoint.

    Reads credentials and required headers from the central provider registry.
    Requires ``OPENROUTER_API_KEY`` in the environment or ``api_key`` argument.
    Supports native tool-calling when ``request.tools`` is provided.

    Args:
        request: LLM invocation parameters. ``request.model`` defaults to the
            provider's ``default_model`` when not specified.
        ctx: Workflow execution context (unused directly, kept for interface parity).
        api_key: Optional API key (falls back to ``OPENROUTER_API_KEY`` env var).

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
    key = api_key or os.getenv(spec.env_var)
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
        **build_openai_tool_kwargs(request),
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
        tool_calls=parse_openai_tool_calls(raw_tc),
        finish_reason=getattr(choice, "finish_reason", None),
    )


async def call_together(
    request: LLMRequest, ctx: WorkflowContext, *, api_key: str | None
) -> LLMResponse:
    """Call Together AI via the openai SDK using its OpenAI-compatible endpoint.

    Reads credentials from the central provider registry.
    Requires ``TOGETHER_API_KEY`` in the environment or ``api_key`` argument.
    Supports native tool-calling when ``request.tools`` is provided.

    Args:
        request: LLM invocation parameters. ``request.model`` defaults to the
            provider's ``default_model`` when not specified.
        ctx: Workflow execution context (unused directly, kept for interface parity).
        api_key: Optional API key (falls back to ``TOGETHER_API_KEY`` env var).

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
    key = api_key or os.getenv(spec.env_var)
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
        **build_openai_tool_kwargs(request),
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
        tool_calls=parse_openai_tool_calls(raw_tc),
        finish_reason=getattr(choice, "finish_reason", None),
    )


async def call_xai(
    request: LLMRequest, ctx: WorkflowContext, *, api_key: str | None
) -> LLMResponse:
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
        api_key: Optional API key (falls back to ``XAI_API_KEY`` env var).

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
    key = api_key or os.getenv(spec.env_var)
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
        **build_openai_tool_kwargs(request),
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
        tool_calls=parse_openai_tool_calls(raw_tc),
        finish_reason=getattr(choice, "finish_reason", None),
    )
