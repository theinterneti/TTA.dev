"""LLM provider selection: Groq first, OpenRouter fallback, Ollama last resort.

Priority order:
1. Groq        — fast, reliable, system-prompt support (GROQ_API_KEY)
2. OpenRouter  — free models (OPENROUTER_API_KEY)
3. Ollama      — local fallback

Usage::

    from ttadev.workflows.llm_provider import get_llm_client

    cfg = get_llm_client()
    # cfg.base_url, cfg.model, cfg.api_key, cfg.provider

See: docs/agent-guides/llm-provider-strategy.md
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from ttadev.agents.protocol import ChatPrimitive

_DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
_DEFAULT_OPENROUTER_MODEL = "openrouter/free"
_DEFAULT_OLLAMA_MODEL = "qwen2.5:7b"
_DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


@dataclass
class LLMClientConfig:
    """Provider-agnostic LLM client configuration."""

    base_url: str
    model: str
    api_key: str
    provider: str  # "groq" | "openrouter" | "ollama"


def _groq_config() -> LLMClientConfig:
    """Build Groq provider config from environment."""
    api_key = os.environ.get("GROQ_API_KEY", "")
    model = os.environ.get("GROQ_MODEL", _DEFAULT_GROQ_MODEL)
    return LLMClientConfig(
        base_url=_GROQ_BASE_URL,
        model=model,
        api_key=api_key,
        provider="groq",
    )


def get_llm_provider_chain() -> list[LLMClientConfig]:
    """Return ordered list of LLM providers to try, primary first.

    Selection logic (same env vars as get_llm_client):
    - If LLM_FORCE_PROVIDER=ollama      →  [ollama]
    - If GROQ_API_KEY is set            →  [groq, ollama]
    - Elif OPENROUTER_API_KEY is set    →  [openrouter, ollama]
    - Otherwise                         →  [ollama]

    Never returns an empty list.
    """
    force = os.environ.get("LLM_FORCE_PROVIDER", "").lower()
    if force == "ollama":
        return [_ollama_config()]

    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        return [_groq_config(), _ollama_config()]

    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    if openrouter_key:
        model = os.environ.get("HINDSIGHT_LLM_MODEL", _DEFAULT_OPENROUTER_MODEL)
        openrouter_cfg = LLMClientConfig(
            base_url=_OPENROUTER_BASE_URL,
            model=model,
            api_key=openrouter_key,
            provider="openrouter",
        )
        return [openrouter_cfg, _ollama_config()]

    return [_ollama_config()]


def get_llm_client() -> LLMClientConfig:
    """Return LLM client config following the project provider strategy.

    Selection logic (in priority order):
    1. If ``LLM_FORCE_PROVIDER=ollama``, use Ollama unconditionally.
    2. If ``GROQ_API_KEY`` is set, use Groq (fast, reliable, system-prompt support).
    3. If ``OPENROUTER_API_KEY`` is set, use OpenRouter.
    4. Otherwise, fall back to Ollama.

    Relevant env vars:
    - ``GROQ_API_KEY``         — Groq API key (preferred provider)
    - ``GROQ_MODEL``           — Groq model (default: llama-3.3-70b-versatile)
    - ``OPENROUTER_API_KEY``   — OpenRouter API key
    - ``HINDSIGHT_LLM_MODEL``  — preferred OpenRouter model
    - ``LLM_FORCE_PROVIDER``   — set to "ollama" to bypass cloud providers
    - ``OLLAMA_BASE_URL``      — Ollama base URL (default: localhost:11434/v1)
    - ``OLLAMA_MODEL``         — Ollama model (default: qwen2.5:7b)
    """
    return get_llm_provider_chain()[0]


def build_chat_primitive(config: LLMClientConfig) -> ChatPrimitive:
    """Instantiate a ChatPrimitive from an LLMClientConfig.

    Returns an OpenAI-compatible primitive for both openrouter and ollama
    providers (both use the OpenAI wire protocol).
    """
    from ttadev.primitives.integrations.openai_primitive import OpenAIPrimitive

    primitive = OpenAIPrimitive(
        model=config.model,
        api_key=config.api_key,
        base_url=config.base_url,  # forwarded via **kwargs → AsyncOpenAI
    )
    return cast("ChatPrimitive", primitive)


def _ollama_config() -> LLMClientConfig:
    base_url = os.environ.get("OLLAMA_BASE_URL", _DEFAULT_OLLAMA_BASE_URL)
    model = os.environ.get("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL)
    return LLMClientConfig(
        base_url=base_url,
        model=model,
        api_key="ollama",  # pragma: allowlist secret
        provider="ollama",
    )
