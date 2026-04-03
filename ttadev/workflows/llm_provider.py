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

import logging
import os
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from ttadev.agents.protocol import ChatPrimitive

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# User-facing error for missing / unreachable LLM providers
# ---------------------------------------------------------------------------

_NO_PROVIDER_MESSAGE = """\
\u274c  No LLM provider could connect.

To get started for free, pick one:
  1. Groq (fastest)   \u2014 https://console.groq.com  \u2192 set GROQ_API_KEY
  2. OpenRouter       \u2014 https://openrouter.ai     \u2192 set OPENROUTER_API_KEY
  3. Ollama (local)   \u2014 https://ollama.ai         \u2192 run: ollama pull gemma3:4b

Copy .env.example \u2192 .env and add your key, then re-run.
See: GETTING_STARTED.md Step 1.5
"""


class NoLLMProviderError(Exception):
    """Raised when no configured LLM provider can be reached.

    Contains a user-friendly, actionable message — never a raw traceback.
    The CLI catches this and prints it directly to stderr before exiting
    with code 1.

    Attributes:
        reason: Technical detail captured from the underlying exception,
                available for logging / debug purposes but not shown to the
                user by default.
    """

    def __init__(self, reason: str = "") -> None:
        self.reason = reason
        super().__init__(_NO_PROVIDER_MESSAGE)

    def user_message(self) -> str:
        """Return the full human-readable message for display."""
        return _NO_PROVIDER_MESSAGE


def _is_provider_error(exc: BaseException) -> bool:
    """Return ``True`` if *exc* looks like a failed LLM provider connection or auth.

    Matches errors from:

    - **openai / groq SDK**: ``AuthenticationError``, ``NotFoundError``,
      ``APIConnectionError``, ``APITimeoutError``, ``PermissionDeniedError``
    - **httpx transport**: ``ConnectError``, ``ConnectTimeout``
    - **stdlib**: ``ConnectionRefusedError``, ``ConnectionError``

    Type matching for openai/groq is done by class name + module prefix so
    that those libraries are not imported unconditionally at module load time.

    Args:
        exc: The exception to inspect.

    Returns:
        ``True`` when *exc* represents a known provider auth / connectivity failure.
    """
    import httpx

    # httpx / stdlib network errors (Ollama not running, network unreachable…)
    if isinstance(exc, (httpx.ConnectError, httpx.ConnectTimeout, ConnectionRefusedError)):
        return True

    # openai / groq SDK errors — class name check to avoid unconditional import
    _auth_conn_names = {
        "AuthenticationError",
        "NotFoundError",
        "APIConnectionError",
        "APITimeoutError",
        "PermissionDeniedError",
    }
    type_name = type(exc).__name__
    if type_name in _auth_conn_names:
        module = getattr(type(exc), "__module__", "")
        if module.startswith(("openai", "groq", "anthropic")):
            return True

    return False


_DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
_DEFAULT_OPENROUTER_MODEL = "openrouter/free"
_OLLAMA_ULTIMATE_FALLBACK = "gemma3:4b"
_DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def get_default_ollama_model() -> str:
    """Auto-detect the best available Ollama model, falling back gracefully.

    Resolution order:

    1. ``OLLAMA_MODEL`` environment variable — user-specified, always wins.
    2. First model returned by ``ollama list`` — whatever is already pulled.
    3. Hard-coded sentinel ``gemma3:4b`` — safe last resort.

    Returns:
        Model name string suitable for use with the Ollama API.
    """
    # 1. Honour explicit user override
    if model := os.environ.get("OLLAMA_MODEL"):
        return model

    # 2. Auto-detect from the locally installed model list
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")[1:]  # skip header row
            if lines and lines[0].strip():
                model_name = lines[0].split()[0]  # first column is NAME
                _log.debug("Auto-detected ollama model: %s", model_name)
                return model_name
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    # 3. Sensible fallback — more likely to be installed than qwen2.5:7b
    return _OLLAMA_ULTIMATE_FALLBACK


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
    - ``OLLAMA_MODEL``         — Ollama model (auto-detected via ``ollama list``; falls back to gemma3:4b)
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
    model = get_default_ollama_model()
    return LLMClientConfig(
        base_url=base_url,
        model=model,
        api_key="ollama",  # pragma: allowlist secret
        provider="ollama",
    )
