"""LLM provider selection: OpenRouter free models first, Ollama fallback.

Usage::

    from ttadev.workflows.llm_provider import get_llm_client

    cfg = get_llm_client()
    # cfg.base_url, cfg.model, cfg.api_key, cfg.provider

See: docs/agent-guides/llm-provider-strategy.md
"""

from __future__ import annotations

import os
from dataclasses import dataclass

_DEFAULT_OPENROUTER_MODEL = "google/gemma-3n-e4b-it:free"
_DEFAULT_OLLAMA_MODEL = "qwen2.5:7b"
_DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


@dataclass
class LLMClientConfig:
    """Provider-agnostic LLM client configuration."""

    base_url: str
    model: str
    api_key: str
    provider: str  # "openrouter" | "ollama"


def get_llm_client() -> LLMClientConfig:
    """Return LLM client config following the project provider strategy.

    Selection logic:
    1. If ``LLM_FORCE_PROVIDER=ollama``, use Ollama unconditionally.
    2. If ``OPENROUTER_API_KEY`` is set, use OpenRouter.
    3. Otherwise, fall back to Ollama.

    Relevant env vars:
    - ``OPENROUTER_API_KEY``   — OpenRouter API key
    - ``HINDSIGHT_LLM_MODEL``  — preferred OpenRouter model
    - ``LLM_FORCE_PROVIDER``   — set to "ollama" to bypass OpenRouter
    - ``OLLAMA_BASE_URL``      — Ollama base URL (default: localhost:11434/v1)
    - ``OLLAMA_MODEL``         — Ollama model (default: qwen2.5:7b)
    """
    force = os.environ.get("LLM_FORCE_PROVIDER", "").lower()
    if force == "ollama":
        return _ollama_config()

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if api_key:
        model = os.environ.get("HINDSIGHT_LLM_MODEL", _DEFAULT_OPENROUTER_MODEL)
        return LLMClientConfig(
            base_url=_OPENROUTER_BASE_URL,
            model=model,
            api_key=api_key,
            provider="openrouter",
        )

    return _ollama_config()


def get_llm_provider_chain() -> list[LLMClientConfig]:
    """Return ordered list of LLM providers to try, primary first.

    Selection logic (same env vars as get_llm_client):
    - If LLM_FORCE_PROVIDER=ollama  →  [ollama]
    - If OPENROUTER_API_KEY is set  →  [openrouter, ollama]
    - Otherwise                     →  [ollama]

    Never returns an empty list.
    """
    force = os.environ.get("LLM_FORCE_PROVIDER", "").lower()
    if force == "ollama":
        return [_ollama_config()]

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if api_key:
        model = os.environ.get("HINDSIGHT_LLM_MODEL", _DEFAULT_OPENROUTER_MODEL)
        openrouter_cfg = LLMClientConfig(
            base_url=_OPENROUTER_BASE_URL,
            model=model,
            api_key=api_key,
            provider="openrouter",
        )
        return [openrouter_cfg, _ollama_config()]

    return [_ollama_config()]


def _ollama_config() -> LLMClientConfig:
    base_url = os.environ.get("OLLAMA_BASE_URL", _DEFAULT_OLLAMA_BASE_URL)
    model = os.environ.get("OLLAMA_MODEL", _DEFAULT_OLLAMA_MODEL)
    return LLMClientConfig(
        base_url=base_url,
        model=model,
        api_key="ollama",  # pragma: allowlist secret
        provider="ollama",
    )
