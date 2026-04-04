"""LLM provider selection: registry-driven, priority ordered.

Priority is determined by the order of entries in ``_PROVIDER_REGISTRY``.
Cloud providers (those with a ``key_env``) are included when their key is
present in the environment.  Local providers (``is_local=True``) are always
appended at the end as a fallback.

To add a new provider, append a ``ProviderSpec`` to ``_PROVIDER_REGISTRY``.
To change priority, reorder the registry.  No other code needs to change.

Current priority:
1. Groq        — fast, reliable, system-prompt support (GROQ_API_KEY)
2. OpenRouter  — free models (OPENROUTER_API_KEY)
3. Ollama      — local fallback (always included last)

Override any single entry with ``LLM_FORCE_PROVIDER=<name>`` (e.g. "ollama").

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
from dataclasses import dataclass, field
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


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------


@dataclass
class ProviderSpec:
    """Declarative specification for one LLM provider.

    The registry is walked in order to build the provider chain.  To add a new
    provider, append a ``ProviderSpec`` to ``_PROVIDER_REGISTRY``.  To change
    priority, reorder the list.

    Attributes:
        name: Short provider identifier (e.g. ``"groq"``). Used in
            ``LLM_FORCE_PROVIDER`` and ``LLMClientConfig.provider``.
        key_env: Environment variable holding the API key.  ``None`` for local
            providers that are always available (e.g. Ollama).
        base_url: Default base URL for the provider's API.
        base_url_env: Optional env var that overrides ``base_url`` at runtime.
        model_env: Env var for selecting a non-default model.
        default_model: Model used when ``model_env`` is unset.
        is_local: When ``True``, this provider is always appended to the end of
            the chain as a local fallback, regardless of key presence.
        auto_detect_model: When ``True``, ``get_default_ollama_model()`` is
            called instead of reading ``model_env`` directly.
    """

    name: str
    key_env: str | None
    base_url: str
    model_env: str
    default_model: str
    base_url_env: str | None = field(default=None)
    is_local: bool = field(default=False)
    auto_detect_model: bool = field(default=False)


#: Ordered list of providers.  Priority = position in this list.
#: Cloud providers (``key_env`` set) are included when their key is present.
#: Local providers (``is_local=True``) are always appended last.
_PROVIDER_REGISTRY: list[ProviderSpec] = [
    ProviderSpec(
        name="groq",
        key_env="GROQ_API_KEY",
        base_url=_GROQ_BASE_URL,
        model_env="GROQ_MODEL",
        default_model=_DEFAULT_GROQ_MODEL,
    ),
    ProviderSpec(
        name="openrouter",
        key_env="OPENROUTER_API_KEY",
        base_url=_OPENROUTER_BASE_URL,
        model_env="HINDSIGHT_LLM_MODEL",
        default_model=_DEFAULT_OPENROUTER_MODEL,
    ),
    ProviderSpec(
        name="ollama",
        key_env=None,
        base_url=_DEFAULT_OLLAMA_BASE_URL,
        base_url_env="OLLAMA_BASE_URL",
        model_env="OLLAMA_MODEL",
        default_model=_OLLAMA_ULTIMATE_FALLBACK,
        is_local=True,
        auto_detect_model=True,
    ),
]


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
    provider: str  # matches ProviderSpec.name


def _config_from_spec(spec: ProviderSpec) -> LLMClientConfig:
    """Build an ``LLMClientConfig`` from a ``ProviderSpec`` and the current env.

    Args:
        spec: The provider specification to materialise.

    Returns:
        A fully populated ``LLMClientConfig`` ready to hand to an LLM client.
    """
    api_key = os.environ.get(spec.key_env, "") if spec.key_env else spec.name
    base_url = (
        os.environ.get(spec.base_url_env, spec.base_url) if spec.base_url_env else spec.base_url
    )
    model = (
        get_default_ollama_model()
        if spec.auto_detect_model
        else os.environ.get(spec.model_env, spec.default_model)
    )
    return LLMClientConfig(base_url=base_url, model=model, api_key=api_key, provider=spec.name)


def get_llm_provider_chain() -> list[LLMClientConfig]:
    """Return ordered list of LLM providers to try, primary first.

    Walks ``_PROVIDER_REGISTRY`` in order.  Cloud providers (those with a
    ``key_env``) are included when their API key is present in the environment.
    Local providers (``is_local=True``) are always appended at the end.

    ``LLM_FORCE_PROVIDER=<name>`` short-circuits to a single-entry list for
    the named provider (any registry entry, not just "ollama").

    Never returns an empty list — at minimum the local fallbacks are returned.
    """
    force = os.environ.get("LLM_FORCE_PROVIDER", "").lower()
    if force:
        for spec in _PROVIDER_REGISTRY:
            if spec.name == force:
                return [_config_from_spec(spec)]
        _log.warning("LLM_FORCE_PROVIDER=%r not found in provider registry; ignoring", force)

    cloud: list[LLMClientConfig] = []
    local: list[LLMClientConfig] = []
    for spec in _PROVIDER_REGISTRY:
        if spec.is_local:
            local.append(_config_from_spec(spec))
        elif spec.key_env and os.environ.get(spec.key_env, ""):
            cloud.append(_config_from_spec(spec))

    chain = cloud + local
    return chain if chain else local


def get_llm_client() -> LLMClientConfig:
    """Return the highest-priority available LLM client config.

    Equivalent to ``get_llm_provider_chain()[0]``.

    Relevant env vars (see ``_PROVIDER_REGISTRY`` for the full list):

    - ``LLM_FORCE_PROVIDER`` — force a specific provider by name
    - ``GROQ_API_KEY``       — activates Groq (highest priority)
    - ``GROQ_MODEL``         — Groq model override
    - ``OPENROUTER_API_KEY`` — activates OpenRouter
    - ``HINDSIGHT_LLM_MODEL``— OpenRouter model override
    - ``OLLAMA_BASE_URL``    — Ollama base URL override
    - ``OLLAMA_MODEL``       — Ollama model override (auto-detected if unset)
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
