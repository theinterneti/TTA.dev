"""Per-provider streaming (async generator) logic for UniversalLLMPrimitive.

Each function dispatches a single LLMRequest to the appropriate provider SDK
and yields content string chunks.  Provider SDK imports are deferred to
function bodies so that importing this module never raises ImportError for
SDKs that aren't installed.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from ttadev.primitives.core import WorkflowContext
from ttadev.primitives.llm._llm_types import LLMRequest

# ── Generic OpenAI-compatible stream ─────────────────────────────────────────


async def stream_openai_compat(
    request: LLMRequest,
    ctx: WorkflowContext,
    *,
    api_key: str | None,
    base_url: str | None,
    provider_name: str,
) -> AsyncIterator[str]:
    """Stream tokens from any OpenAI-compatible provider.

    Used when ``use_compat=True`` is passed to the constructor, or directly
    by providers whose preferred_path is ``"compat"``.

    Args:
        request: LLM invocation parameters.
        ctx: Workflow execution context (unused, kept for interface parity).
        api_key: Optional API key override.
        base_url: Optional base URL override.
        provider_name: Canonical provider key in PROVIDERS.

    Yields:
        Successive content string chunks from the model.

    Raises:
        ValueError: If the provider does not support the OpenAI-compat endpoint,
            or no API key is available.
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
    response = await client.chat.completions.create(
        model=request.model or spec.default_model,
        messages=request.messages,  # type: ignore[arg-type]
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=True,
    )
    async with response as stream:
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta


# ── Native SDK streaming ──────────────────────────────────────────────────────


async def stream_groq(
    request: LLMRequest, ctx: WorkflowContext, *, api_key: str | None
) -> AsyncIterator[str]:
    """Stream tokens from Groq via the groq SDK.

    Args:
        request: LLM invocation parameters.
        ctx: Workflow execution context.
        api_key: Optional API key (falls back to ``GROQ_API_KEY`` env var).

    Yields:
        Successive content string chunks from the model.
    """
    from groq import AsyncGroq  # type: ignore[import]  # noqa: PLC0415

    client = AsyncGroq(api_key=api_key)
    stream = await client.chat.completions.create(
        model=request.model,
        messages=request.messages,  # type: ignore[arg-type]
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


async def stream_anthropic(
    request: LLMRequest, ctx: WorkflowContext, *, api_key: str | None
) -> AsyncIterator[str]:
    """Stream tokens from Anthropic via the anthropic SDK.

    Args:
        request: LLM invocation parameters.
        ctx: Workflow execution context.
        api_key: Optional API key (falls back to ``ANTHROPIC_API_KEY`` env var).

    Yields:
        Successive text delta chunks from the model.
    """
    import anthropic  # type: ignore[import]  # noqa: PLC0415

    client = anthropic.AsyncAnthropic(api_key=api_key)
    async with client.messages.stream(
        model=request.model,
        max_tokens=request.max_tokens or 1024,
        system=request.system or "",
        messages=request.messages,  # type: ignore[arg-type]
    ) as stream:
        async for text in stream.text_stream:
            if text:
                yield text


async def stream_openai(
    request: LLMRequest, ctx: WorkflowContext, *, api_key: str | None, base_url: str | None
) -> AsyncIterator[str]:
    """Stream tokens from OpenAI via the openai SDK.

    Args:
        request: LLM invocation parameters.
        ctx: Workflow execution context.
        api_key: Optional API key (falls back to ``OPENAI_API_KEY`` env var).
        base_url: Optional base URL override.

    Yields:
        Successive content string chunks from the model.
    """
    from openai import AsyncOpenAI  # type: ignore[import]  # noqa: PLC0415

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    stream = await client.chat.completions.create(
        model=request.model,
        messages=request.messages,  # type: ignore[arg-type]
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


async def stream_ollama(
    request: LLMRequest, ctx: WorkflowContext, *, base_url: str | None
) -> AsyncIterator[str]:
    """Stream tokens from Ollama /api/chat (NDJSON).

    Connects to the Ollama server and streams response tokens as NDJSON
    lines.  Each line is parsed for ``message.content``; the final line
    (``"done": true``) is silently ignored.

    Supports think mode for chain-of-thought models (Qwen3, QwQ):
    when ``extra.think=True`` content comes from ``message.thinking``.

    Args:
        request: LLM invocation parameters.
        ctx: Workflow execution context.
        base_url: Optional base URL override (default: ``http://localhost:11434``).

    Yields:
        Successive content string chunks from the model.
    """
    import httpx  # noqa: PLC0415

    base = base_url or "http://localhost:11434"
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

    payload: dict = {
        "model": request.model,
        "messages": messages,
        "stream": True,
        "think": extra.get("think", False),
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
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = data.get("message", {})
                chunk = msg.get("content") or msg.get("thinking") or ""
                if chunk:
                    yield chunk
                if data.get("done"):
                    break


# ── OpenAI-compat provider streams ────────────────────────────────────────────


async def stream_google(
    request: LLMRequest, ctx: WorkflowContext, *, api_key: str | None
) -> AsyncIterator[str]:
    """Stream tokens from Google Gemini via its OpenAI-compatible endpoint.

    Uses ``https://generativelanguage.googleapis.com/v1beta/openai`` — no
    ``google-generativeai`` SDK required.

    Args:
        request: LLM invocation parameters.
        ctx: Workflow execution context.
        api_key: Optional API key (falls back to ``GOOGLE_API_KEY`` env var).

    Yields:
        Successive content string chunks from the model.

    Raises:
        ValueError: If no API key is available from the argument or environment.
    """
    import os  # noqa: PLC0415

    from openai import AsyncOpenAI  # noqa: PLC0415

    from ttadev.primitives.llm.providers import PROVIDERS  # noqa: PLC0415

    spec = PROVIDERS["google"]
    key = api_key or os.getenv(spec.env_var)
    if not key:
        raise ValueError(
            "GOOGLE_API_KEY is not set. "
            "Set it in your environment or pass api_key to UniversalLLMPrimitive."
        )
    client = AsyncOpenAI(api_key=key, base_url=spec.base_url)
    stream = await client.chat.completions.create(
        model=request.model or spec.default_model,
        messages=request.messages,  # type: ignore[arg-type]
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


async def stream_openrouter(
    request: LLMRequest, ctx: WorkflowContext, *, api_key: str | None
) -> AsyncIterator[str]:
    """Stream tokens from OpenRouter via its OpenAI-compatible endpoint.

    Args:
        request: LLM invocation parameters.
        ctx: Workflow execution context.
        api_key: Optional API key (falls back to ``OPENROUTER_API_KEY`` env var).

    Yields:
        Successive content string chunks from the model.

    Raises:
        ValueError: If no API key is available from the argument or environment.
    """
    import os  # noqa: PLC0415

    from openai import AsyncOpenAI  # noqa: PLC0415

    from ttadev.primitives.llm.providers import PROVIDERS  # noqa: PLC0415

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
    stream = await client.chat.completions.create(
        model=request.model or spec.default_model,
        messages=request.messages,  # type: ignore[arg-type]
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


async def stream_together(
    request: LLMRequest, ctx: WorkflowContext, *, api_key: str | None
) -> AsyncIterator[str]:
    """Stream tokens from Together AI via its OpenAI-compatible endpoint.

    Args:
        request: LLM invocation parameters.
        ctx: Workflow execution context.
        api_key: Optional API key (falls back to ``TOGETHER_API_KEY`` env var).

    Yields:
        Successive content string chunks from the model.

    Raises:
        ValueError: If no API key is available from the argument or environment.
    """
    import os  # noqa: PLC0415

    from openai import AsyncOpenAI  # noqa: PLC0415

    from ttadev.primitives.llm.providers import PROVIDERS  # noqa: PLC0415

    spec = PROVIDERS["together"]
    key = api_key or os.getenv(spec.env_var)
    if not key:
        raise ValueError(
            "TOGETHER_API_KEY is not set. "
            "Set it in your environment or pass api_key to UniversalLLMPrimitive."
        )
    client = AsyncOpenAI(api_key=key, base_url=spec.base_url)
    stream = await client.chat.completions.create(
        model=request.model or spec.default_model,
        messages=request.messages,  # type: ignore[arg-type]
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


async def stream_xai(
    request: LLMRequest, ctx: WorkflowContext, *, api_key: str | None
) -> AsyncIterator[str]:
    """Stream tokens from xAI (Grok) via its OpenAI-compatible endpoint.

    Args:
        request: LLM invocation parameters.
        ctx: Workflow execution context.
        api_key: Optional API key (falls back to ``XAI_API_KEY`` env var).

    Yields:
        Successive content string chunks from the model.

    Raises:
        ValueError: If no API key is available from the argument or environment.
    """
    import os  # noqa: PLC0415

    from openai import AsyncOpenAI  # noqa: PLC0415

    from ttadev.primitives.llm.providers import PROVIDERS  # noqa: PLC0415

    spec = PROVIDERS["xai"]
    key = api_key or os.getenv(spec.env_var)
    if not key:
        raise ValueError(
            "XAI_API_KEY is not set. "
            "Set it in your environment or pass api_key to UniversalLLMPrimitive."
        )
    client = AsyncOpenAI(api_key=key, base_url=spec.base_url)
    stream = await client.chat.completions.create(
        model=request.model or spec.default_model,
        messages=request.messages,  # type: ignore[arg-type]
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta
