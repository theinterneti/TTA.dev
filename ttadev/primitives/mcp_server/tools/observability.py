"""TTA.dev MCP server: LLM and memory (observability) tools."""

from __future__ import annotations

import os
import warnings
from typing import Any

try:
    from mcp.types import ToolAnnotations
except ImportError:  # pragma: no cover
    ToolAnnotations = None  # type: ignore[assignment,misc]

from ttadev.primitives.llm.providers import PROVIDERS


def _get_providers_status() -> dict[str, Any]:
    """Return provider status dict — module-level so other modules can import it."""
    result = []
    for name, spec in PROVIDERS.items():
        env_key = f"{name.upper()}_API_KEY"
        if name == "openrouter":
            env_key = "OPENROUTER_API_KEY"
        elif name == "google":
            env_key = "GOOGLE_API_KEY"
        elif name == "groq":
            env_key = "GROQ_API_KEY"
        elif name == "ollama":
            env_key = ""  # no key needed

        if name == "google":
            google_key = os.environ.get("GOOGLE_API_KEY")
            gemini_key = os.environ.get("GEMINI_API_KEY")
            if gemini_key and not google_key:
                warnings.warn(
                    "GEMINI_API_KEY is deprecated; set GOOGLE_API_KEY instead "
                    "(matches Google AI Studio convention). "
                    "Support for GEMINI_API_KEY will be removed in a future release.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            api_key_configured = bool(google_key or gemini_key)
        else:
            api_key_configured = bool(env_key and os.environ.get(env_key))

        result.append(
            {
                "name": name,
                "api_key_configured": api_key_configured,
                "default_model": getattr(spec, "default_model", None),
                "base_url": getattr(spec, "base_url", None),
                "is_local": name == "ollama",
            }
        )

    return {"providers": result, "count": len(result)}


def register_observability_tools(mcp: Any, _ro: Any, _idem: Any) -> None:
    """Register LLM and memory tools with the MCP server."""

    # Memory tools use different annotations (no openWorldHint=False)
    _ro_m = ToolAnnotations(readOnlyHint=True) if ToolAnnotations else None
    _idem_m = ToolAnnotations(idempotentHint=True) if ToolAnnotations else None  # noqa: F841

    # ========== LLM TOOLS ==========

    @mcp.tool(annotations=_ro)
    def llm_hardware_profile() -> dict:
        """Return the detected hardware profile for this machine.

        Reports CPU cores, total RAM, GPU name/VRAM and compute backend
        (cuda/rocm/metal/cpu), plus the estimated largest model size that
        will fit in memory at Q4 quantisation.

        Use this to understand what Ollama models are viable before pulling
        or routing to them.

        Returns:
            Hardware profile dict with keys: cpu_cores, ram_gb, gpus,
            backend, total_vram_gb, max_params_b_q4, max_params_b_q8.
        """
        from ttadev.primitives.llm.hardware_detector import HardwareDetector

        det = HardwareDetector()
        profile = det.detect()
        result = profile.to_dict()
        result["recommend_size_tag"] = det.recommend_size_tag()
        return result

    @mcp.tool(annotations=_ro)
    def llm_viable_ollama_models(model_ids: list[str]) -> dict:
        """Filter a list of Ollama model IDs to only those that fit in available memory.

        Checks both GPU VRAM and system RAM (Ollama can offload to CPU RAM).
        Models without a recognised parameter count are assumed viable.

        Args:
            model_ids: Candidate Ollama model IDs, e.g.
                ``["llama3.2:1b", "qwen3:14b", "llama3.3:70b"]``.

        Returns:
            Dict with ``viable`` (list that fits) and ``too_large`` (list that
            doesn't fit in available memory).
        """
        from ttadev.primitives.llm.hardware_detector import HardwareDetector

        det = HardwareDetector()
        viable = det.filter_ollama_models(model_ids)
        too_large = [m for m in model_ids if m not in viable]
        return {
            "viable": viable,
            "too_large": too_large,
            "hardware_summary": det.detect().summary(),
        }

    @mcp.tool(annotations=_ro)
    def llm_benchmark_score(model_id: str, benchmark: str | None = None) -> dict:
        """Look up benchmark scores for a model from the TTA.dev benchmark DB.

        Includes live data sourced from Artificial Analysis and the HuggingFace
        Open LLM Leaderboard (refreshed every 24 hours).

        Args:
            model_id: Model identifier as stored in the benchmark DB, e.g.
                ``"gpt-4o"``, ``"llama-3.3-70b-versatile"``.
            benchmark: Specific benchmark name (e.g. ``"humaneval"``,
                ``"mmlu"``, ``"gpqa"``).  When ``None``, all known scores
                for the model are returned.

        Returns:
            Dict with ``model_id``, ``benchmark`` (or ``"all"``), and
            ``scores`` mapping benchmark name → score (0–100 scale).
        """
        from ttadev.primitives.llm.model_benchmarks import (
            get_benchmarks,
            get_best_score,
        )

        if benchmark:
            score = get_best_score(model_id, benchmark)
            return {
                "model_id": model_id,
                "benchmark": benchmark,
                "score": score,
                "available": score is not None,
            }

        entries = get_benchmarks(model_id)
        scores = {e.benchmark: e.score for e in entries}
        return {
            "model_id": model_id,
            "benchmark": "all",
            "scores": scores,
            "best_coding": get_best_score(model_id, "humaneval"),
            "best_knowledge": get_best_score(model_id, "mmlu"),
        }

    @mcp.tool(annotations=_idem)
    async def llm_refresh_benchmarks(force: bool = False) -> dict:
        """Refresh the live benchmark cache from Artificial Analysis and HuggingFace.

        This is normally done automatically (24-hour TTL) but can be triggered
        manually here.  Network access is required; the tool is a no-op if no
        API keys are configured.

        Args:
            force: When ``True``, ignores the TTL and re-downloads regardless
                of when the cache was last refreshed.

        Returns:
            Dict with ``ok`` (bool), ``models_updated`` (int), and
            ``message`` (str).
        """
        try:
            from ttadev.primitives.llm.benchmark_fetcher import BenchmarkFetcher

            fetcher = BenchmarkFetcher()
            data = await fetcher.refresh(force=force)
            return {
                "ok": True,
                "models_updated": len(data),
                "message": f"Refreshed {len(data)} model benchmark records.",
            }
        except Exception as exc:
            return {
                "ok": False,
                "models_updated": 0,
                "message": f"Refresh failed: {exc}",
            }

    @mcp.tool(annotations=_ro)
    def llm_list_providers() -> dict:
        """List all configured LLM providers and their status.

        Returns information about each provider: whether an API key is
        configured, the default model, and the base URL.  Useful for
        agents checking which cloud providers are available before routing.

        **Environment variable names (issue #316):**

        +--------------+-----------------------------+---------------------------+
        | Provider     | Canonical env var           | Legacy / alias            |
        +==============+=============================+===========================+
        | Google       | ``GOOGLE_API_KEY``          | ``GEMINI_API_KEY`` (dep.) |
        +--------------+-----------------------------+---------------------------+
        | Groq         | ``GROQ_API_KEY``            | —                         |
        +--------------+-----------------------------+---------------------------+
        | OpenRouter   | ``OPENROUTER_API_KEY``      | —                         |
        +--------------+-----------------------------+---------------------------+
        | Ollama       | *(no key required)*         | —                         |
        +--------------+-----------------------------+---------------------------+

        The ``tta setup`` wizard stores the Google key as ``GOOGLE_API_KEY``
        (matching Google AI Studio's own convention).  ``GEMINI_API_KEY`` is
        accepted as a backward-compatible fallback but emits a
        ``DeprecationWarning``; support will be removed in a future release.

        Returns:
            Dict with ``providers`` list, each entry having ``name``,
            ``api_key_configured``, ``default_model``, ``base_url``, and
            ``is_local`` (``True`` only for Ollama).
        """
        return _get_providers_status()

    @mcp.tool(annotations=_ro)
    def llm_recommend_model(
        task: str = "coding",
        complexity: str = "moderate",
        prefer_local: bool = False,
        max_cost_tier: str = "high",
    ) -> dict:
        """Recommend the best available model for a given task and complexity.

        Consults the task-aware model selector using live provider data,
        hardware viability (for Ollama), and benchmark scores.

        Args:
            task: Task type — one of ``"coding"``, ``"reasoning"``,
                ``"math"``, ``"chat"``, ``"function_calling"``,
                ``"vision"``, ``"general"``.
            complexity: Complexity hint — ``"simple"``, ``"moderate"``,
                or ``"complex"``.
            prefer_local: When ``True``, prefers Ollama models if viable.
            max_cost_tier: Maximum cost tier to consider —
                ``"free"``, ``"low"``, ``"medium"``, ``"high"``.

        Returns:
            Dict with ``model_id``, ``provider``, ``rationale``, and
            ``fallback`` (next-best option).
        """
        from ttadev.primitives.llm.task_selector import (
            COMPLEXITY_COMPLEX,
            COMPLEXITY_MODERATE,
            COMPLEXITY_SIMPLE,
            TASK_CHAT,
            TASK_CODING,
            TASK_FUNCTION_CALLING,
            TASK_GENERAL,
            TASK_MATH,
            TASK_REASONING,
            TASK_VISION,
            TaskProfile,
            rank_models_for_task,
        )

        task_map = {
            "coding": TASK_CODING,
            "reasoning": TASK_REASONING,
            "math": TASK_MATH,
            "chat": TASK_CHAT,
            "function_calling": TASK_FUNCTION_CALLING,
            "vision": TASK_VISION,
            "general": TASK_GENERAL,
        }
        complexity_map = {
            "simple": COMPLEXITY_SIMPLE,
            "moderate": COMPLEXITY_MODERATE,
            "complex": COMPLEXITY_COMPLEX,
        }

        task_type = task_map.get(task.lower(), TASK_CODING)
        complexity_level = complexity_map.get(complexity.lower(), COMPLEXITY_MODERATE)

        profile = TaskProfile(task_type=task_type, complexity=complexity_level)

        from ttadev.primitives.llm.model_registry import (
            _COST_TIER_ORDER,
            _DEFAULT_CLOUD_MODELS,
        )

        all_entries = list(_DEFAULT_CLOUD_MODELS)
        ranked = rank_models_for_task(
            [e.model_id for e in all_entries],
            profile,
        )

        max_rank = _COST_TIER_ORDER.get(max_cost_tier, 99)
        entry_map = {e.model_id: e for e in all_entries}

        cost_filtered = [
            model_id
            for model_id in ranked
            if model_id in entry_map
            and _COST_TIER_ORDER.get(entry_map[model_id].cost_tier, 99) <= max_rank
        ]

        if prefer_local:
            local_first = [m for m in cost_filtered if entry_map.get(m) and entry_map[m].is_local]
            cloud = [m for m in cost_filtered if not (entry_map.get(m) and entry_map[m].is_local)]
            cost_filtered = local_first + cloud

        top = cost_filtered[0] if cost_filtered else None
        second = cost_filtered[1] if len(cost_filtered) > 1 else None

        def _provider(mid: str | None) -> str | None:
            if mid is None:
                return None
            e = entry_map.get(mid)
            return e.provider if e else None

        return {
            "model_id": top,
            "provider": _provider(top),
            "fallback": second,
            "fallback_provider": _provider(second),
            "task": task,
            "complexity": complexity,
            "rationale": (
                f"Selected for {task} ({complexity} complexity). "
                f"Provider: {_provider(top)}. "
                f"Prefer local: {prefer_local}."
            ),
        }

    # ========== MEMORY TOOLS ==========

    @mcp.tool(annotations=_ro_m)
    async def memory_recall(
        query: str,
        bank_id: str = "tta-dev",
        budget: str = "mid",
    ) -> dict[str, object]:
        """Recall relevant memories from a Hindsight memory bank.

        Semantically searches the Hindsight bank for memories that match the
        query. Returns the top matches with text content and optional type.

        Args:
            query: Semantic search string (must not be empty).
            bank_id: Hindsight bank identifier (default: ``"tta-dev"``).
            budget: Recall depth — ``"low"`` (fast), ``"mid"``, or ``"high"`` (thorough).

        Returns:
            Dict with ``memories`` list (each has ``id``, ``text``, ``type``)
            and ``count`` integer.
        """
        if not query:
            return {"error": "query must not be empty", "memories": [], "count": 0}
        if budget not in ("low", "mid", "high"):
            budget = "mid"
        try:
            from ttadev.primitives.memory import AgentMemory

            mem = AgentMemory(bank_id=bank_id)
            if not mem.is_available():
                return {
                    "error": "Hindsight unavailable — start with: docker start hindsight",
                    "memories": [],
                    "count": 0,
                }
            results = await mem.recall(query, budget=budget)  # type: ignore[arg-type]
            return {"memories": list(results), "count": len(results)}
        except Exception as exc:
            return {"error": str(exc), "memories": [], "count": 0}

    @mcp.tool()
    async def memory_retain(
        content: str,
        bank_id: str = "tta-dev",
        context: str = "",
    ) -> dict[str, object]:
        """Store a new memory in a Hindsight memory bank.

        Persists *content* to the specified bank for future recall. Use the
        retain format: ``"[type: decision|pattern|failure|insight] <what happened>"``
        for structured, searchable memories.

        Args:
            content: Memory content to store (must not be empty).
            bank_id: Hindsight bank identifier (default: ``"tta-dev"``).
            context: Optional context label (e.g. module or task name).

        Returns:
            Dict with ``success`` bool and optional ``operation_id``.
        """
        if not content:
            return {"success": False, "error": "content must not be empty"}
        if context:
            content = f"{content}\nContext: {context}"
        try:
            from ttadev.primitives.memory import AgentMemory

            mem = AgentMemory(bank_id=bank_id)
            if not mem.is_available():
                return {
                    "success": False,
                    "error": "Hindsight unavailable — start with: docker start hindsight",
                }
            result = await mem.retain(content)
            return dict(result)
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    @mcp.tool(annotations=_ro_m)
    async def memory_build_context(
        query: str,
        bank_id: str = "tta-dev",
    ) -> dict[str, object]:
        """Build a system-prompt-friendly context prefix from Hindsight.

        Fetches active directives and semantically relevant memories from the
        specified bank, returning a formatted string suitable for prepending to
        an agent's system prompt.

        Args:
            query: Semantic search string to find relevant memories.
            bank_id: Hindsight bank identifier (default: ``"tta-dev"``).

        Returns:
            Dict with ``context`` string (empty string if Hindsight unavailable)
            and ``available`` bool.
        """
        if not query:
            return {"error": "query must not be empty", "context": "", "available": False}
        try:
            from ttadev.primitives.memory import AgentMemory

            mem = AgentMemory(bank_id=bank_id)
            available = mem.is_available()
            if not available:
                return {
                    "context": "",
                    "available": False,
                    "error": "Hindsight unavailable — start with: docker start hindsight",
                }
            prefix = await mem.build_context_prefix(query)
            return {"context": prefix, "available": True}
        except Exception as exc:
            return {"context": "", "available": False, "error": str(exc)}

    @mcp.tool(annotations=_ro_m)
    async def memory_list_banks(
        base_url: str = "http://localhost:8888",
    ) -> dict[str, object]:
        """List all available Hindsight memory banks.

        Queries the Hindsight server for all configured banks. Useful for
        discovering which banks exist before calling recall or retain.

        Args:
            base_url: Hindsight server URL (default: ``http://localhost:8888``).

        Returns:
            Dict with ``banks`` list (each has id, name) and ``count`` integer.
        """
        try:
            import httpx

            resp = httpx.get(f"{base_url.rstrip('/')}/v1/default/banks", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                banks = data if isinstance(data, list) else data.get("banks", [])
                return {"banks": banks, "count": len(banks)}
            return {"banks": [], "count": 0, "error": f"HTTP {resp.status_code}"}
        except Exception as exc:
            return {
                "banks": [],
                "count": 0,
                "error": f"Hindsight unavailable: {exc}",
            }
