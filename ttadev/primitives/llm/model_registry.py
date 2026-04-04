"""ModelRegistryPrimitive — local-first model registry with provider selection policy.

Maintains an in-memory registry of known LLM models across all configured
providers. Pre-populated with well-known cloud models; discovers Ollama
models on demand. Supports policy-based model selection (prefer local, max
cost tier, capability requirements, provider preferences, benchmark thresholds).

Design notes
------------
* **In-memory only** — no file I/O or SQLite. Registry is lost on process
  restart (a future concern).
* **TTL expiry** — entries with ``last_seen > 0`` expire after
  ``ttl_seconds`` (default 3600) and are excluded from list/select results.
  Cloud pre-populated entries have ``last_seen = 0.0`` so they never expire.
* **Thread-safe** — all mutations are protected by ``asyncio.Lock``.
* **Composable** — works alongside :class:`~ttadev.primitives.llm.model_monitor.ModelMonitorPrimitive`
  and :class:`~ttadev.primitives.llm.model_router.ModelRouterPrimitive`.
* **Benchmark-aware** — :class:`SelectionPolicy` supports filtering and
  sorting by published benchmark scores via
  :mod:`~ttadev.primitives.llm.model_benchmarks`.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive

# ── Cost-tier ordering ────────────────────────────────────────────────────────

_COST_TIER_ORDER: dict[str, int] = {
    "free": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "unknown": 99,
}


# ── Data models ───────────────────────────────────────────────────────────────


@dataclass
class ModelEntry:
    """Registry entry for a single LLM model.

    Attributes:
        model_id: Model identifier, e.g. ``"llama3.2:latest"`` or ``"gpt-4o-mini"``.
        provider: Provider key matching :data:`~ttadev.primitives.llm.providers.PROVIDERS`.
        display_name: Human-readable name for UI display.
        context_length: Maximum context window in tokens.
        supports_tool_calling: Whether the model supports function/tool calling.
        supports_vision: Whether the model accepts image inputs.
        supports_streaming: Whether the provider supports streaming responses.
        cost_tier: Cost band — one of ``"free"``, ``"low"``, ``"medium"``, ``"high"``,
            or ``"unknown"``.
        is_local: ``True`` for Ollama-served models (no cloud cost or latency).
        last_seen: Unix timestamp of the last time this entry was verified available.
            ``0.0`` means "never verified" — cloud entries use this to opt out of TTL.
        metadata: Arbitrary additional data (parameter count, quantization, etc.).
    """

    model_id: str
    provider: str
    display_name: str = ""
    context_length: int = 4096
    supports_tool_calling: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True
    cost_tier: str = "unknown"
    is_local: bool = False
    last_seen: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SelectionPolicy:
    """Policy for selecting the best available model from the registry.

    Attributes:
        prefer_local: When ``True``, Ollama-served models sort before cloud
            models regardless of cost tier.
        max_cost_tier: Upper bound on cost tier — models with a higher tier
            are excluded.  Order: ``free < low < medium < high``.
        require_tool_calling: Exclude models that do not support tool calling.
        require_vision: Exclude models that do not support image inputs.
        preferred_providers: Providers to try first (in order), before falling
            back to any remaining eligible models.
        fallback_providers: Providers to use only when no preferred-provider
            model is available.
        min_humaneval_score: When set, exclude models whose best published
            HumanEval score is below this percentage. Models with no HumanEval
            data in :data:`~ttadev.primitives.llm.model_benchmarks.BENCHMARK_DATA`
            are also excluded when this threshold is provided.
        min_mmlu_score: When set, exclude models whose best published MMLU
            score is below this percentage. Models with no MMLU data are also
            excluded when this threshold is provided.
        preferred_benchmark: When set, eligible models are sorted by their
            best score on this benchmark in descending order (higher is better),
            applied as a tertiary sort key after local-preference and
            provider-preference ordering.
    """

    prefer_local: bool = True
    max_cost_tier: str = "low"
    require_tool_calling: bool = False
    require_vision: bool = False
    preferred_providers: list[str] = field(default_factory=list)
    fallback_providers: list[str] = field(default_factory=list)
    min_humaneval_score: float | None = None
    min_mmlu_score: float | None = None
    preferred_benchmark: str | None = None


@dataclass
class RegistryRequest:
    """Input for :class:`ModelRegistryPrimitive`.

    Attributes:
        action: Dispatch key — one of ``"register"``, ``"get"``, ``"list"``,
            ``"discover_ollama"``, ``"select"``, ``"unregister"``.
        entry: :class:`ModelEntry` to register (``action="register"``).
        provider: Provider key for ``"get"`` / ``"unregister"`` actions.
        model_id: Model ID for ``"get"`` / ``"unregister"`` actions.
        filter_provider: Restrict ``"list"`` results to this provider.
        filter_cost_tier: Restrict ``"list"`` results to this exact cost tier.
        filter_tool_calling: When ``True``, ``"list"`` returns only models
            that support tool calling.
        filter_vision: When ``True``, ``"list"`` returns only models that
            support vision.
        policy: :class:`SelectionPolicy` used by the ``"select"`` action.
        benchmark_filter: When set on a ``"list"`` action, only models that
            have at least one benchmark entry for this benchmark name are
            returned.
        min_benchmark_score: Used together with *benchmark_filter* — further
            restricts ``"list"`` results to models whose best score on the
            specified benchmark is >= this value.
    """

    action: str
    entry: ModelEntry | None = None
    provider: str = ""
    model_id: str = ""
    filter_provider: str = ""
    filter_cost_tier: str = ""
    filter_tool_calling: bool | None = None
    filter_vision: bool | None = None
    policy: SelectionPolicy | None = None
    benchmark_filter: str | None = None
    min_benchmark_score: float | None = None


@dataclass
class RegistryResponse:
    """Output from :class:`ModelRegistryPrimitive`.

    Attributes:
        action: Echoes the action that produced this response.
        entry: Single :class:`ModelEntry` result for ``"get"`` and ``"select"``.
            ``None`` when the requested model is not found or no model matches
            the selection policy.
        entries: List of :class:`ModelEntry` results for ``"list"``.
        registered: ``True`` when ``"register"`` successfully added/updated the entry.
        unregistered: ``True`` when ``"unregister"`` successfully removed the entry.
        discovered_count: Number of Ollama models registered by ``"discover_ollama"``.
        error: Human-readable error message, or ``None`` on success.
    """

    action: str
    entry: ModelEntry | None = None
    entries: list[ModelEntry] = field(default_factory=list)
    registered: bool = False
    unregistered: bool = False
    discovered_count: int = 0
    error: str | None = None


# ── Well-known cloud models ───────────────────────────────────────────────────

_DEFAULT_CLOUD_MODELS: list[ModelEntry] = [
    # ── Groq (free tier, high-throughput) ─────────────────────────────────────
    ModelEntry(
        model_id="llama-3.3-70b-versatile",
        provider="groq",
        display_name="Llama 3.3 70B Versatile (Groq)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="llama-3.1-70b-versatile",
        provider="groq",
        display_name="Llama 3.1 70B Versatile (Groq)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="llama-3.1-8b-instant",
        provider="groq",
        display_name="Llama 3.1 8B Instant (Groq)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="llama3-8b-8192",
        provider="groq",
        display_name="Llama 3 8B (Groq)",
        context_length=8_192,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="llama3-70b-8192",
        provider="groq",
        display_name="Llama 3 70B (Groq)",
        context_length=8_192,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="meta-llama/llama-4-scout-17b-16e-instruct",
        provider="groq",
        display_name="Llama 4 Scout 17B (Groq)",
        context_length=131_072,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="gemma-7b-it",
        provider="groq",
        display_name="Gemma 7B IT (Groq)",
        context_length=8_192,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="moonshotai/kimi-k2-instruct",
        provider="groq",
        display_name="Kimi K2 Instruct (Groq)",
        context_length=131_072,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="qwen/qwen3-32b",
        provider="groq",
        display_name="Qwen3 32B (Groq) — thinking model",
        context_length=32_768,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"thinking_model": True},
    ),
    ModelEntry(
        model_id="compound-beta",
        provider="groq",
        display_name="Compound Beta (Groq)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"compound_model": True},
    ),
    ModelEntry(
        model_id="openai/gpt-oss-20b",
        provider="groq",
        display_name="GPT-OSS 20B (Groq)",
        context_length=8_192,
        supports_tool_calling=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="openai/gpt-oss-120b",
        provider="groq",
        display_name="GPT-OSS 120B (Groq)",
        context_length=8_192,
        supports_tool_calling=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="meta-llama/llama-4-maverick-17b-128e-instruct",
        provider="groq",
        display_name="Llama 4 Maverick 17B (Groq)",
        context_length=131_072,
        supports_tool_calling=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    # ── Gemini (models/ prefix for OpenAI-compat endpoint) ────────────────────
    ModelEntry(
        model_id="models/gemini-2.5-flash",
        provider="google",
        display_name="Gemini 2.5 Flash",
        context_length=1_048_576,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="low",
        is_local=False,
    ),
    ModelEntry(
        model_id="models/gemini-2.5-pro",
        provider="google",
        display_name="Gemini 2.5 Pro",
        context_length=1_048_576,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="medium",
        is_local=False,
    ),
    ModelEntry(
        model_id="models/gemini-2.0-flash",
        provider="google",
        display_name="Gemini 2.0 Flash",
        context_length=1_048_576,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="low",
        is_local=False,
    ),
    ModelEntry(
        model_id="models/gemini-2.0-flash-lite",
        provider="google",
        display_name="Gemini 2.0 Flash Lite",
        context_length=1_048_576,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    # Gemini 1.5 models were removed by Google (404). Use ProviderModelDiscovery.for_google()
    # for current model list.
    # ── Google Gemma (via Google AI Studio — same GOOGLE_API_KEY as Gemini) ────
    # 14,400 RPD / 30 RPM / 15K TPM — much higher RPD than Gemini frontier models.
    ModelEntry(
        model_id="gemma-3-27b-it",
        provider="google",
        display_name="Gemma 3 27B (Google AI Studio)",
        context_length=131_072,
        supports_tool_calling=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "30 RPM / 14,400 RPD / 15K TPM. Same GOOGLE_API_KEY as Gemini."},
    ),
    ModelEntry(
        model_id="gemma-3-12b-it",
        provider="google",
        display_name="Gemma 3 12B (Google AI Studio)",
        context_length=131_072,
        supports_tool_calling=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "30 RPM / 14,400 RPD / 15K TPM. Same GOOGLE_API_KEY as Gemini."},
    ),
    ModelEntry(
        model_id="gemma-3-4b-it",
        provider="google",
        display_name="Gemma 3 4B (Google AI Studio)",
        context_length=131_072,
        supports_tool_calling=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "30 RPM / 14,400 RPD / 15K TPM. Same GOOGLE_API_KEY as Gemini."},
    ),
    ModelEntry(
        model_id="gemma-3-1b-it",
        provider="google",
        display_name="Gemma 3 1B (Google AI Studio)",
        context_length=32_768,
        supports_tool_calling=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "30 RPM / 14,400 RPD / 15K TPM. Same GOOGLE_API_KEY as Gemini."},
    ),
    # ── GitHub Models (free tier — requires GITHUB_TOKEN, 50–150 req/day) ──────
    ModelEntry(
        model_id="gpt-5",
        provider="github",
        display_name="GPT-5 (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 10 RPM / 50 RPD."},
    ),
    ModelEntry(
        model_id="gpt-5-mini",
        provider="github",
        display_name="GPT-5 Mini (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 15 RPM / 150 RPD."},
    ),
    ModelEntry(
        model_id="gpt-4.1",
        provider="github",
        display_name="GPT-4.1 (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 10 RPM / 50 RPD."},
    ),
    ModelEntry(
        model_id="gpt-4.1-mini",
        provider="github",
        display_name="GPT-4.1 Mini (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 15 RPM / 150 RPD."},
    ),
    ModelEntry(
        model_id="gpt-4o",
        provider="github",
        display_name="GPT-4o (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API (GITHUB_TOKEN). 10 RPM / 50 RPD."},
    ),
    ModelEntry(
        model_id="gpt-4o-mini",
        provider="github",
        display_name="GPT-4o Mini (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 15 RPM / 150 RPD."},
    ),
    ModelEntry(
        model_id="o3",
        provider="github",
        display_name="o3 (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 10 RPM / 50 RPD.", "thinking_model": True},
    ),
    ModelEntry(
        model_id="o4-mini",
        provider="github",
        display_name="o4-mini (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 15 RPM / 150 RPD.", "thinking_model": True},
    ),
    ModelEntry(
        model_id="Llama-4-Scout-17B-16E-Instruct",
        provider="github",
        display_name="Llama 4 Scout 17B (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 10 RPM / 50 RPD."},
    ),
    ModelEntry(
        model_id="Llama-4-Maverick-17B-128E-Instruct",
        provider="github",
        display_name="Llama 4 Maverick 17B (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 10 RPM / 50 RPD."},
    ),
    ModelEntry(
        model_id="Meta-Llama-3.3-70B-Instruct",
        provider="github",
        display_name="Llama 3.3 70B (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 10 RPM / 50 RPD."},
    ),
    ModelEntry(
        model_id="Meta-Llama-3.1-405B-Instruct",
        provider="github",
        display_name="Llama 3.1 405B (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 10 RPM / 50 RPD."},
    ),
    ModelEntry(
        model_id="Meta-Llama-3.1-8B-Instruct",
        provider="github",
        display_name="Llama 3.1 8B (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 15 RPM / 150 RPD."},
    ),
    ModelEntry(
        model_id="DeepSeek-V3-0324",
        provider="github",
        display_name="DeepSeek V3 0324 (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 10 RPM / 50 RPD."},
    ),
    ModelEntry(
        model_id="DeepSeek-R1-0528",
        provider="github",
        display_name="DeepSeek R1 0528 (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 10 RPM / 50 RPD.", "thinking_model": True},
    ),
    ModelEntry(
        model_id="DeepSeek-R1",
        provider="github",
        display_name="DeepSeek R1 (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. Strong reasoning.", "thinking_model": True},
    ),
    ModelEntry(
        model_id="grok-3",
        provider="github",
        display_name="Grok 3 (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 10 RPM / 50 RPD."},
    ),
    ModelEntry(
        model_id="grok-3-mini",
        provider="github",
        display_name="Grok 3 Mini (GitHub Models)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. 15 RPM / 150 RPD."},
    ),
    ModelEntry(
        model_id="Phi-4-mini-instruct",
        provider="github",
        display_name="Phi-4 Mini Instruct (GitHub Models)",
        context_length=16_000,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. Microsoft Phi-4 Mini."},
    ),
    ModelEntry(
        model_id="Phi-4-multimodal-instruct",
        provider="github",
        display_name="Phi-4 Multimodal (GitHub Models)",
        context_length=16_000,
        supports_tool_calling=False,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. Microsoft Phi-4 multimodal."},
    ),
    ModelEntry(
        model_id="Phi-4",
        provider="github",
        display_name="Phi-4 (GitHub Models)",
        context_length=16_000,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"notes": "Free via GitHub Models API. Microsoft Phi-4."},
    ),
    # ── OpenRouter free models (:free suffix) ─────────────────────────────────
    ModelEntry(
        model_id="mistralai/mistral-7b-instruct:free",
        provider="openrouter",
        display_name="Mistral 7B Instruct Free (OpenRouter)",
        context_length=32_768,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="microsoft/phi-3-mini-128k-instruct:free",
        provider="openrouter",
        display_name="Phi-3 Mini 128K Free (OpenRouter)",
        context_length=128_000,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="meta-llama/llama-3.2-3b-instruct:free",
        provider="openrouter",
        display_name="Llama 3.2 3B Instruct Free (OpenRouter)",
        context_length=131_072,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="meta-llama/llama-3.1-8b-instruct:free",
        provider="openrouter",
        display_name="Llama 3.1 8B Instruct Free (OpenRouter)",
        context_length=131_072,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="google/gemma-3-27b-it:free",
        provider="openrouter",
        display_name="Gemma 3 27B IT Free (OpenRouter)",
        context_length=131_072,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="qwen/qwen3-30b-a3b:free",
        provider="openrouter",
        display_name="Qwen3 30B A3B Free (OpenRouter)",
        context_length=40_960,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="deepseek/deepseek-r1:free",
        provider="openrouter",
        display_name="DeepSeek R1 Free (OpenRouter) — thinking model",
        context_length=163_840,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
        metadata={"thinking_model": True, "strip_thinking": True},
    ),
    ModelEntry(
        model_id="meta-llama/llama-3.3-70b-instruct:free",
        provider="openrouter",
        display_name="Llama 3.3 70B Instruct Free (OpenRouter)",
        context_length=131_072,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="google/gemma-3-12b-it:free",
        provider="openrouter",
        display_name="Gemma 3 12B IT Free (OpenRouter)",
        context_length=131_072,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="google/gemma-3-4b-it:free",
        provider="openrouter",
        display_name="Gemma 3 4B IT Free (OpenRouter)",
        context_length=131_072,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="mistralai/mistral-small-3.1-24b-instruct:free",
        provider="openrouter",
        display_name="Mistral Small 3.1 24B Free (OpenRouter)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="openai/gpt-oss-120b:free",
        provider="openrouter",
        display_name="GPT-OSS 120B Free (OpenRouter)",
        context_length=8_192,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="openai/gpt-oss-20b:free",
        provider="openrouter",
        display_name="GPT-OSS 20B Free (OpenRouter)",
        context_length=8_192,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    # ── Together AI ───────────────────────────────────────────────────────────
    ModelEntry(
        model_id="meta-llama/Llama-3.2-3B-Instruct-Turbo",
        provider="together",
        display_name="Llama 3.2 3B Instruct Turbo (Together)",
        context_length=131_072,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="low",
        is_local=False,
    ),
    ModelEntry(
        model_id="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        provider="together",
        display_name="Llama 3.3 70B Instruct Turbo (Together)",
        context_length=131_072,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="low",
        is_local=False,
    ),
    ModelEntry(
        model_id="Qwen/Qwen2.5-72B-Instruct-Turbo",
        provider="together",
        display_name="Qwen2.5 72B Instruct Turbo (Together)",
        context_length=32_768,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="low",
        is_local=False,
    ),
    # ── Anthropic ─────────────────────────────────────────────────────────────
    ModelEntry(
        model_id="claude-3-5-haiku-20241022",
        provider="anthropic",
        display_name="Claude 3.5 Haiku",
        context_length=200_000,
        supports_tool_calling=True,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="low",
        is_local=False,
    ),
    ModelEntry(
        model_id="claude-3-5-sonnet-20241022",
        provider="anthropic",
        display_name="Claude 3.5 Sonnet",
        context_length=200_000,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="medium",
        is_local=False,
    ),
    ModelEntry(
        model_id="claude-opus-4-5",
        provider="anthropic",
        display_name="Claude Opus 4.5",
        context_length=200_000,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="high",
        is_local=False,
    ),
    # ── OpenAI ────────────────────────────────────────────────────────────────
    ModelEntry(
        model_id="gpt-4o-mini",
        provider="openai",
        display_name="GPT-4o Mini",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="low",
        is_local=False,
    ),
    ModelEntry(
        model_id="gpt-4o",
        provider="openai",
        display_name="GPT-4o",
        context_length=128_000,
        supports_tool_calling=True,
        supports_vision=True,
        supports_streaming=True,
        cost_tier="medium",
        is_local=False,
    ),
    ModelEntry(
        model_id="o3-mini",
        provider="openai",
        display_name="o3-mini",
        context_length=128_000,
        supports_tool_calling=False,
        supports_vision=False,
        supports_streaming=True,
        cost_tier="medium",
        is_local=False,
        metadata={"thinking_model": True},
    ),
    # ── Cerebras (free tier, fast inference) ──────────────────────────────────
    ModelEntry(
        model_id="openai/gpt-oss-120b",
        provider="cerebras",
        display_name="GPT-OSS 120B (Cerebras)",
        context_length=8_192,
        supports_tool_calling=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="llama3.1-8b",
        provider="cerebras",
        display_name="Llama 3.1 8B (Cerebras)",
        context_length=8_192,
        supports_tool_calling=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    # ── Cohere (shared 1000 req/month free tier) ───────────────────────────────
    ModelEntry(
        model_id="command-a-03-2025",
        provider="cohere",
        display_name="Command A (Cohere)",
        context_length=256_000,
        supports_tool_calling=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
    ModelEntry(
        model_id="command-r-plus-08-2024",
        provider="cohere",
        display_name="Command R+ (Cohere)",
        context_length=128_000,
        supports_tool_calling=True,
        supports_streaming=True,
        cost_tier="free",
        is_local=False,
    ),
]

#: Recommended Groq model IDs for multi-bucket rotation strategies.
#: List from fastest/cheapest to most capable.
GROQ_ROTATION_MODELS: list[str] = [
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama3-8b-8192",
    "qwen/qwen3-32b",
    "llama-3.3-70b-versatile",
    "moonshotai/kimi-k2-instruct",
]

#: All Gemini model IDs registered with the ``models/`` prefix required by
#: the Google Gemini OpenAI-compatible endpoint.
GEMINI_MODELS: list[str] = [
    "models/gemini-2.5-flash",
    "models/gemini-2.5-pro",
    "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-lite",
    # Gemini 1.5 models were removed by Google (404). Use ProviderModelDiscovery.for_google()
    # for current model list.
]


# ── Primitive ─────────────────────────────────────────────────────────────────


class ModelRegistryPrimitive(WorkflowPrimitive[RegistryRequest, RegistryResponse]):
    """Local-first model registry with policy-based provider selection.

    Maintains a thread-safe in-memory registry of known LLM models keyed by
    ``"{provider}:{model_id}"``.  Pre-populated with well-known cloud models
    on construction; discovers Ollama models on demand via ``discover_ollama``.

    Supported actions:

    * ``register`` — add or update a :class:`ModelEntry`.
    * ``get`` — retrieve a single entry by provider and model ID.
    * ``list`` — list all entries, optionally filtered by provider, cost tier,
      capability, or published benchmark score via *benchmark_filter* /
      *min_benchmark_score*.
    * ``discover_ollama`` — probe Ollama, register each loaded model as
      ``provider="ollama"``, ``is_local=True``, ``cost_tier="free"``.
    * ``select`` — pick the best model matching a :class:`SelectionPolicy`,
      optionally filtered by minimum HumanEval / MMLU scores and sorted by
      a preferred benchmark.
    * ``unregister`` — remove an entry from the registry.

    Args:
        ttl_seconds: How long (in seconds) an entry with ``last_seen > 0``
            remains valid.  Entries with ``last_seen == 0.0`` never expire
            (used for cloud pre-populated entries).  Default: 3600 (1 hour).
        monitor: Optional :class:`~ttadev.primitives.llm.model_monitor.ModelMonitorPrimitive`
            for health-aware selection.  When provided, unhealthy models are
            sorted below healthy ones during ``select``.
        ollama_manager: Optional pre-configured
            :class:`~ttadev.primitives.llm.ollama_primitive.OllamaModelManagerPrimitive`.
            A default instance (``localhost:11434``) is created on first use when
            ``None``.
        prepopulate: When ``True`` (default), the registry starts with well-known
            cloud models from :data:`_DEFAULT_CLOUD_MODELS`.

    Example::

        from ttadev.primitives.llm import ModelRegistryPrimitive, SelectionPolicy, RegistryRequest
        from ttadev.primitives.core.base import WorkflowContext

        registry = ModelRegistryPrimitive()
        ctx = WorkflowContext.root("model-selection")

        # Discover local Ollama models
        await registry.execute(RegistryRequest(action="discover_ollama"), ctx)

        # Select the best local-first, free model with tool calling
        resp = await registry.execute(
            RegistryRequest(
                action="select",
                policy=SelectionPolicy(
                    prefer_local=True, max_cost_tier="free", require_tool_calling=True
                ),
            ),
            ctx,
        )
        print(resp.entry)  # ModelEntry or None

        # Select a model with strong coding skills (HumanEval >= 80%)
        resp = await registry.execute(
            RegistryRequest(
                action="select",
                policy=SelectionPolicy(
                    min_humaneval_score=80.0,
                    preferred_benchmark="humaneval",
                    max_cost_tier="high",
                ),
            ),
            ctx,
        )
    """

    def __init__(
        self,
        *,
        ttl_seconds: float = 3600.0,
        monitor: Any | None = None,
        ollama_manager: Any | None = None,
        prepopulate: bool = True,
    ) -> None:
        self._registry: dict[str, ModelEntry] = {}
        self._lock = asyncio.Lock()
        self._ttl = ttl_seconds
        self._monitor = monitor
        self._ollama_manager = ollama_manager

        if prepopulate:
            for entry in _DEFAULT_CLOUD_MODELS:
                key = self._key(entry.provider, entry.model_id)
                self._registry[key] = entry

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _key(provider: str, model_id: str) -> str:
        return f"{provider}:{model_id}"

    def _is_stale(self, entry: ModelEntry) -> bool:
        """Return ``True`` if the entry has a non-zero last_seen that has expired.

        Args:
            entry: The registry entry to check.

        Returns:
            ``True`` if the entry is expired and should be excluded from results.
        """
        if entry.last_seen <= 0.0:
            return False
        return (time.time() - entry.last_seen) > self._ttl

    def _live_entries(self) -> list[ModelEntry]:
        """Return all non-expired entries from the registry.

        Must be called while holding ``self._lock``.

        Returns:
            List of entries where TTL has not expired.
        """
        return [e for e in self._registry.values() if not self._is_stale(e)]

    # ── WorkflowPrimitive interface ───────────────────────────────────────────

    async def execute(self, request: RegistryRequest, ctx: WorkflowContext) -> RegistryResponse:
        """Dispatch *request.action* to the appropriate handler.

        Args:
            request: The registry request specifying the action and parameters.
            ctx: Workflow context (forwarded to sub-primitives like OllamaModelManager).

        Returns:
            A :class:`RegistryResponse` carrying the result of the action.

        Raises:
            ValueError: If *request.action* is not one of the supported actions.
        """
        action = request.action.lower()
        if action == "register":
            return await self._register(request)
        elif action == "get":
            return await self._get(request)
        elif action == "list":
            return await self._list(request)
        elif action == "discover_ollama":
            return await self._discover_ollama(request, ctx)
        elif action == "select":
            return await self._select(request)
        elif action == "unregister":
            return await self._unregister(request)
        else:
            raise ValueError(
                f"Unknown action {action!r}. "
                "Valid: register, get, list, discover_ollama, select, unregister"
            )

    # ── Action handlers ───────────────────────────────────────────────────────

    async def _register(self, request: RegistryRequest) -> RegistryResponse:
        if request.entry is None:
            return RegistryResponse(
                action="register",
                registered=False,
                error="entry is required for register action",
            )
        entry = request.entry
        # Apply pricing catalog — override cost_tier when the catalog has an entry
        # for this provider-model pair.  Falls back to the static ModelEntry field
        # so that unknown or unlisted models are unaffected.
        from ttadev.primitives.llm.model_pricing import get_effective_cost_tier  # lazy import

        entry.cost_tier = get_effective_cost_tier(
            entry.provider, entry.model_id, fallback=entry.cost_tier
        )
        key = self._key(entry.provider, entry.model_id)
        async with self._lock:
            self._registry[key] = entry
        return RegistryResponse(action="register", registered=True, entry=entry)

    async def _get(self, request: RegistryRequest) -> RegistryResponse:
        key = self._key(request.provider, request.model_id)
        async with self._lock:
            entry = self._registry.get(key)
        if entry is None or self._is_stale(entry):
            return RegistryResponse(action="get", entry=None)
        return RegistryResponse(action="get", entry=entry)

    async def _list(self, request: RegistryRequest) -> RegistryResponse:
        async with self._lock:
            entries = self._live_entries()

        if request.filter_provider:
            entries = [e for e in entries if e.provider == request.filter_provider]
        if request.filter_cost_tier:
            entries = [e for e in entries if e.cost_tier == request.filter_cost_tier]
        if request.filter_tool_calling is True:
            entries = [e for e in entries if e.supports_tool_calling]
        if request.filter_vision is True:
            entries = [e for e in entries if e.supports_vision]

        # Benchmark-based list filtering — lazy import avoids circular imports.
        if request.benchmark_filter:
            from ttadev.primitives.llm.model_benchmarks import get_best_score

            bench = request.benchmark_filter
            min_score = request.min_benchmark_score

            def _has_benchmark(e: ModelEntry) -> bool:
                score = get_best_score(e.model_id, bench)
                if score is None:
                    return False
                if min_score is not None and score < min_score:
                    return False
                return True

            entries = [e for e in entries if _has_benchmark(e)]

        return RegistryResponse(action="list", entries=entries)

    async def _discover_ollama(
        self, request: RegistryRequest, ctx: WorkflowContext
    ) -> RegistryResponse:
        # Lazy-import to avoid circular dependency at module load time.
        from ttadev.primitives.llm.ollama_primitive import OllamaManagerRequest

        if self._ollama_manager is None:
            from ttadev.primitives.llm.ollama_primitive import OllamaModelManagerPrimitive

            manager = OllamaModelManagerPrimitive()
        else:
            manager = self._ollama_manager

        try:
            resp = await manager.execute(OllamaManagerRequest(action="list"), ctx)
        except Exception as exc:
            return RegistryResponse(
                action="discover_ollama",
                discovered_count=0,
                error=f"Ollama unreachable: {exc}",
            )

        now = time.time()
        count = 0
        async with self._lock:
            for model_info in resp.models:
                entry = ModelEntry(
                    model_id=model_info.name,
                    provider="ollama",
                    display_name=model_info.name,
                    context_length=4096,
                    supports_tool_calling=False,
                    supports_vision=False,
                    supports_streaming=True,
                    cost_tier="free",
                    is_local=True,
                    last_seen=now,
                    metadata={
                        "parameter_size": model_info.parameter_size,
                        "quantization": model_info.quantization,
                        "family": model_info.family,
                        "size_bytes": model_info.size_bytes,
                    },
                )
                key = self._key("ollama", model_info.name)
                self._registry[key] = entry
                count += 1

        return RegistryResponse(action="discover_ollama", discovered_count=count)

    async def _select(self, request: RegistryRequest) -> RegistryResponse:
        # Lazy-import benchmark helpers to avoid circular imports.
        from ttadev.primitives.llm.model_benchmarks import get_best_score

        policy = request.policy or SelectionPolicy()
        max_tier_rank = _COST_TIER_ORDER.get(policy.max_cost_tier, 99)

        async with self._lock:
            entries = self._live_entries()

        # Apply capability filters
        if policy.require_tool_calling:
            entries = [e for e in entries if e.supports_tool_calling]
        if policy.require_vision:
            entries = [e for e in entries if e.supports_vision]

        # Filter local (Ollama) models by hardware viability — skip models that
        # won't fit in available VRAM / RAM, preventing the router from recommending
        # a model that would OOM or thrash swap.
        if any(e.is_local for e in entries):
            from ttadev.primitives.llm.hardware_detector import detector as _hw_detector

            hw_profile = _hw_detector.detect()
            entries = [e for e in entries if not e.is_local or hw_profile.can_run(e.model_id)]

        # Apply cost tier ceiling
        entries = [e for e in entries if _COST_TIER_ORDER.get(e.cost_tier, 99) <= max_tier_rank]

        # Apply benchmark score filters — models with no data are excluded when
        # a threshold is set, so callers can rely on the guarantee that every
        # returned model meets the stated minimum.
        if policy.min_humaneval_score is not None:
            threshold = policy.min_humaneval_score
            entries = [
                e
                for e in entries
                if (s := get_best_score(e.model_id, "humaneval")) is not None and s >= threshold
            ]

        if policy.min_mmlu_score is not None:
            threshold = policy.min_mmlu_score
            entries = [
                e
                for e in entries
                if (s := get_best_score(e.model_id, "mmlu")) is not None and s >= threshold
            ]

        if not entries:
            return RegistryResponse(action="select", entry=None)

        def _sort_key(
            e: ModelEntry,
        ) -> tuple[int, int, int, float, int, str]:
            # Primary: local models first when prefer_local is True
            local_rank = 0 if (e.is_local and policy.prefer_local) else 1

            # Secondary: preferred_providers ordering
            if policy.preferred_providers and e.provider in policy.preferred_providers:
                provider_rank = policy.preferred_providers.index(e.provider)
            elif policy.fallback_providers and e.provider in policy.fallback_providers:
                # Fallback providers sort after preferred but before unlisted
                provider_rank = len(policy.preferred_providers) + 1
            else:
                provider_rank = len(policy.preferred_providers)

            # Tertiary: lower cost tier preferred
            cost_rank = _COST_TIER_ORDER.get(e.cost_tier, 99)

            # Quaternary: preferred_benchmark score descending (negate for ascending sort)
            if policy.preferred_benchmark is not None:
                bench_score = get_best_score(e.model_id, policy.preferred_benchmark)
                benchmark_rank = -(bench_score if bench_score is not None else 0.0)
            else:
                benchmark_rank = 0.0

            # Quinary: healthy models preferred (requires monitor)
            if self._monitor is not None:
                health_rank = 0 if self._monitor.is_healthy_sync(e.model_id, e.provider) else 1
            else:
                health_rank = 0

            # Senary: stable alphabetical tie-break
            tiebreak = f"{e.provider}:{e.model_id}"

            return (local_rank, provider_rank, cost_rank, benchmark_rank, health_rank, tiebreak)

        entries.sort(key=_sort_key)
        return RegistryResponse(action="select", entry=entries[0])

    async def _unregister(self, request: RegistryRequest) -> RegistryResponse:
        key = self._key(request.provider, request.model_id)
        async with self._lock:
            removed = self._registry.pop(key, None)
        return RegistryResponse(action="unregister", unregistered=removed is not None)
