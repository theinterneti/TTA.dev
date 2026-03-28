"""UniversalLLMPrimitive — runtime LLM provider abstraction.

Provides a single interface for invoking LLMs across providers
(Groq, Anthropic, OpenAI, Ollama). Config-driven, swappable backends.

Note: Distinct from ttadev/integrations/llm/universal_llm_primitive.py
which handles agentic coder budget profiles.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ttadev.primitives.core import WorkflowContext, WorkflowPrimitive


class LLMProvider(StrEnum):
    GROQ = "groq"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"


@dataclass
class LLMRequest:
    model: str
    messages: list[dict[str, str]]
    temperature: float = 0.7
    max_tokens: int | None = None
    system: str | None = None


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
        dispatch = {
            LLMProvider.GROQ: self._call_groq,
            LLMProvider.ANTHROPIC: self._call_anthropic,
            LLMProvider.OPENAI: self._call_openai,
            LLMProvider.OLLAMA: self._call_ollama,
        }
        return await dispatch[self._provider](request, ctx)

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
