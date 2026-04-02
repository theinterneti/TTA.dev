"""UniversalLLMPrimitive — runtime LLM provider abstraction.

Provides a single interface for invoking LLMs across providers
(Groq, Anthropic, OpenAI, Ollama, Gemini). Config-driven, swappable backends.

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
| Gemini    | ``GEMINI_API_KEY`` or ``GOOGLE_API_KEY`` | ``google-generativeai`` |

Install extras::

    uv sync --extra groq        # Groq
    uv sync --extra anthropic   # Anthropic
    uv sync --extra openai      # OpenAI
    uv sync --extra gemini      # Gemini
    # Ollama: run the daemon locally (https://ollama.com)
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from enum import StrEnum

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
    GEMINI = "gemini"


@dataclass
class LLMRequest:
    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.7
    max_tokens: int | None = None
    system: str | None = None
    stream: bool = False


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    usage: dict[str, int] | None = None


class UniversalLLMPrimitive(WorkflowPrimitive[LLMRequest, LLMResponse]):
    """Route LLM requests to the appropriate provider backend."""

    def __init__(
        self,
        provider: LLMProvider,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        super().__init__()
        if not isinstance(provider, LLMProvider):
            raise ValueError(f"Unknown provider: {provider!r}. Use LLMProvider enum.")
        self._provider = provider
        self._api_key = api_key
        self._base_url = base_url

    async def execute(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        """Invoke provider and return a complete response, with OTel tracing."""
        dispatch = {
            LLMProvider.GROQ: self._call_groq,
            LLMProvider.ANTHROPIC: self._call_anthropic,
            LLMProvider.OPENAI: self._call_openai,
            LLMProvider.OLLAMA: self._call_ollama,
            LLMProvider.GEMINI: self._call_gemini,
        }

        if not (OTEL_AVAILABLE and otel_trace is not None):
            return await dispatch[self._provider](request, ctx)

        tracer = otel_trace.get_tracer(__name__)
        span_name = f"gen_ai.{self._provider.value}.invoke"
        with tracer.start_as_current_span(span_name) as span:
            span.set_attribute("gen_ai.system", self._provider.value)
            span.set_attribute("gen_ai.request.model", request.model)
            span.set_attribute("gen_ai.request.temperature", request.temperature)
            try:
                response = await dispatch[self._provider](request, ctx)
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
            return response

    async def stream(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        """Yield tokens as they arrive from the provider.

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context.

        Yields:
            Token strings as they stream from the provider.
        """
        dispatch = {
            LLMProvider.GROQ: self._stream_groq,
            LLMProvider.ANTHROPIC: self._stream_anthropic,
            LLMProvider.OPENAI: self._stream_openai,
            LLMProvider.OLLAMA: self._stream_ollama,
            LLMProvider.GEMINI: self._stream_gemini,
        }
        async for token in dispatch[self._provider](request, ctx):
            yield token

    # ── Non-streaming provider calls ──────────────────────────────────────────

    async def _call_groq(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        from groq import AsyncGroq  # type: ignore[import]

        client = AsyncGroq(api_key=self._api_key)
        resp = await client.chat.completions.create(
            model=request.model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        return LLMResponse(
            content=resp.choices[0].message.content or "",
            model=resp.model,
            provider="groq",
            usage={
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
            }
            if resp.usage
            else None,
        )

    async def _call_anthropic(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        import anthropic  # type: ignore[import]

        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        resp = await client.messages.create(
            model=request.model,
            max_tokens=request.max_tokens or 1024,
            system=request.system or "",
            messages=request.messages,  # type: ignore[arg-type]
        )
        return LLMResponse(
            content=resp.content[0].text if resp.content else "",
            model=resp.model,
            provider="anthropic",
            usage={
                "input_tokens": resp.usage.input_tokens,
                "output_tokens": resp.usage.output_tokens,
            },
        )

    async def _call_openai(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        from openai import AsyncOpenAI  # type: ignore[import]

        client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
        resp = await client.chat.completions.create(
            model=request.model,
            messages=request.messages,  # type: ignore[arg-type]
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        return LLMResponse(
            content=resp.choices[0].message.content or "",
            model=resp.model,
            provider="openai",
            usage={
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
            }
            if resp.usage
            else None,
        )

    async def _call_ollama(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        import httpx

        base = self._base_url or "http://localhost:11434"
        payload = {
            "model": request.model,
            "messages": request.messages,
            "stream": False,
            "options": {"temperature": request.temperature},
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{base}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return LLMResponse(
            content=data["message"]["content"],
            model=request.model,
            provider="ollama",
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
        """Stream tokens from Ollama via NDJSON chunked response."""
        import httpx

        base = self._base_url or "http://localhost:11434"
        payload = {
            "model": request.model,
            "messages": request.messages,
            "stream": True,
            "options": {"temperature": request.temperature},
        }
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{base}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    content = data.get("message", {}).get("content", "")
                    if content:
                        yield content
                    if data.get("done"):
                        break

    async def _call_gemini(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
        """Call Google Gemini via the google-generativeai SDK.

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context.

        Returns:
            LLMResponse with content, model, provider, and usage metadata.

        Raises:
            ImportError: If google-generativeai is not installed.
        """
        try:
            import google.generativeai as genai  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "google-generativeai is required for the Gemini provider. "
                "Install it with: pip install 'ttadev[gemini]' or pip install google-generativeai"
            ) from exc

        if self._api_key:
            genai.configure(api_key=self._api_key)

        model_name = request.model or "gemini-2.0-flash"
        model = genai.GenerativeModel(model_name=model_name)
        parts = [msg.get("content", "") for msg in request.messages]
        response = await asyncio.to_thread(model.generate_content, parts)

        usage: dict[str, int] | None = None
        if hasattr(response, "usage_metadata") and response.usage_metadata is not None:
            usage = {
                "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0) or 0,
                "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0)
                or 0,
            }

        return LLMResponse(
            content=response.text,
            model=model_name,
            provider="gemini",
            usage=usage,
        )

    async def _stream_gemini(self, request: LLMRequest, ctx: WorkflowContext) -> AsyncIterator[str]:
        """Stream tokens from Google Gemini.

        Yields the full response text as a single chunk. Gemini's generate_content
        is synchronous; yielding the complete response avoids threading complexity
        while keeping the AsyncIterator[str] contract intact.

        Args:
            request: LLM invocation parameters.
            ctx: Workflow execution context.

        Yields:
            Full response content as a single string token.

        Raises:
            ImportError: If google-generativeai is not installed.
        """
        try:
            import google.generativeai as genai  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "google-generativeai is required for the Gemini provider. "
                "Install it with: pip install 'ttadev[gemini]' or pip install google-generativeai"
            ) from exc

        if self._api_key:
            genai.configure(api_key=self._api_key)

        model_name = request.model or "gemini-2.0-flash"
        model = genai.GenerativeModel(model_name=model_name)
        parts = [msg.get("content", "") for msg in request.messages]
        response = await asyncio.to_thread(model.generate_content, parts)
        yield response.text
