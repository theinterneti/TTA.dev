"""Provider registry — single source of truth for all LLM provider contracts.

Every provider's endpoint URL, required environment variable, authentication
headers, and default model live here.  Both :class:`UniversalLLMPrimitive`
and :class:`ModelRouterPrimitive` import from this module so there is never
a divergence in credentials or URLs between the two implementations.

Adding a new provider
---------------------
1. Add a :class:`ProviderSpec` entry to :data:`PROVIDERS`.
2. If the provider is OpenAI-compatible (``openai_compat=True``), it works
   automatically with ``ModelRouterPrimitive`` via the shared
   ``_call_openai_compat()`` helper.
3. If the provider requires an SDK (``openai_compat=False``), add a
   ``_call_<name>`` method to ``UniversalLLMPrimitive``.

Provider contract summary
-------------------------
+---------------+---------------------------+----------------+------------------+
| Provider      | Auth env var              | OpenAI-compat? | Notes            |
+===============+===========================+================+==================+
| groq          | GROQ_API_KEY              | Yes            | Free tier        |
| together      | TOGETHER_API_KEY          | Yes            | Free tier        |
| openrouter    | OPENROUTER_API_KEY        | Yes            | Free models via  |
|               |                           |                | /free suffix     |
| gemini        | GOOGLE_API_KEY            | Yes            | Google's OAI-    |
|               |                           |                | compat endpoint  |
| openai        | OPENAI_API_KEY            | Yes            | SDK preferred    |
| ollama        | (none — local daemon)     | Yes            | localhost:11434  |
| anthropic     | ANTHROPIC_API_KEY         | No (SDK only)  | claude-* models  |
+---------------+---------------------------+----------------+------------------+
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProviderSpec:
    """Contract specification for a single LLM provider.

    Attributes:
        name: Canonical provider name used in YAML configs and enum values.
        base_url: OpenAI-compatible chat completions base URL.
            Empty string for SDK-only providers (``openai_compat=False``).
        env_var: Name of the environment variable holding the API key.
            Empty string for providers that need no key (e.g. local Ollama).
        extra_headers: Additional HTTP headers required by the provider.
            For OpenRouter these carry the mandatory ``HTTP-Referer`` and
            ``X-Title`` headers.
        default_model: Sensible free-tier or widely-available model to use
            when the caller does not specify one.
        openai_compat: ``True`` if the provider speaks the OpenAI chat
            completions wire format.  ``ModelRouterPrimitive`` only works
            with OpenAI-compatible providers.
    """

    name: str
    base_url: str
    env_var: str
    extra_headers: dict[str, str] = field(default_factory=dict)
    default_model: str = ""
    openai_compat: bool = True


#: Registry of all supported LLM providers.
#:
#: Keys are the canonical provider name strings used in YAML tier configs,
#: ``LLMProvider`` enum values, and ``ModelRouterPrimitive`` dispatch.
PROVIDERS: dict[str, ProviderSpec] = {
    "groq": ProviderSpec(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        env_var="GROQ_API_KEY",
        default_model="llama-3.1-8b-instant",
        openai_compat=True,
    ),
    "together": ProviderSpec(
        name="together",
        base_url="https://api.together.xyz/v1",
        env_var="TOGETHER_API_KEY",
        default_model="meta-llama/Llama-3.2-3B-Instruct-Turbo",
        openai_compat=True,
    ),
    "openrouter": ProviderSpec(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        env_var="OPENROUTER_API_KEY",
        extra_headers={
            "HTTP-Referer": "https://github.com/theinterneti/TTA.dev",
            "X-Title": "TTA.dev",
        },
        default_model="mistralai/mistral-7b-instruct:free",
        openai_compat=True,
    ),
    "gemini": ProviderSpec(
        name="gemini",
        # Google publishes a full OpenAI-compatible endpoint:
        # https://ai.google.dev/gemini-api/docs/openai
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        env_var="GOOGLE_API_KEY",
        default_model="gemini-2.0-flash",
        openai_compat=True,
    ),
    "openai": ProviderSpec(
        name="openai",
        base_url="https://api.openai.com/v1",
        env_var="OPENAI_API_KEY",
        default_model="gpt-4o-mini",
        openai_compat=True,
    ),
    "ollama": ProviderSpec(
        name="ollama",
        base_url="http://localhost:11434/v1",
        env_var="",  # no key required for local daemon
        default_model="llama3.2",
        openai_compat=True,
    ),
    "anthropic": ProviderSpec(
        name="anthropic",
        base_url="",  # SDK-only — no OpenAI-compat endpoint
        env_var="ANTHROPIC_API_KEY",
        default_model="claude-3-5-haiku-20241022",
        openai_compat=False,
    ),
}


def get_provider(name: str) -> ProviderSpec:
    """Look up a provider by name.

    Args:
        name: Canonical provider name (e.g. ``"groq"``, ``"gemini"``).

    Returns:
        The matching :class:`ProviderSpec`.

    Raises:
        KeyError: If *name* is not registered in :data:`PROVIDERS`.
    """
    if name not in PROVIDERS:
        available = ", ".join(sorted(PROVIDERS))
        raise KeyError(f"Unknown provider {name!r}. Available: {available}")
    return PROVIDERS[name]


def openai_compat_providers() -> list[ProviderSpec]:
    """Return all providers that support the OpenAI-compatible wire format.

    Returns:
        List of :class:`ProviderSpec` instances where ``openai_compat=True``.
    """
    return [p for p in PROVIDERS.values() if p.openai_compat]
