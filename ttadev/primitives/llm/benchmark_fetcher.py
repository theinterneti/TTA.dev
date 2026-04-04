"""Live benchmark data fetcher for the TTA.dev model router.

Pulls model evaluation scores from two free, authoritative sources:

1. **Artificial Analysis** (https://artificialanalysis.ai) — the richest source.
   Covers both open and closed-source models; includes speed, pricing, and
   quality indices.  Requires a free API key (ARTIFICIAL_ANALYSIS_API_KEY env
   var).  Attribution to artificialanalysis.ai required per their terms.

2. **HF Open LLM Leaderboard 2** (https://huggingface.co/datasets/open-llm-leaderboard/contents)
   — no authentication required.  Covers open-source models only (GPT, Claude,
   Gemini not present).  Benchmarks: MMLU-PRO, BBH, MATH Lvl 5, GPQA, MUSR.

LiveBench (https://livebench.ai) is credited as a methodology reference: their
anti-contamination philosophy informed our use of the ``livecodebench`` metric
from Artificial Analysis rather than static MMLU scores alone.

Results are cached in ``~/.cache/ttadev/benchmark_data.json`` with a 24-hour
TTL.  On import of :mod:`model_benchmarks`, the cache is loaded and appended to
:data:`~ttadev.primitives.llm.model_benchmarks.BENCHMARK_DATA` so that
:func:`~ttadev.primitives.llm.model_benchmarks.rank_models_for_task` benefits
without any API changes.

Usage::

    fetcher = BenchmarkFetcher()

    # Sync: load whatever is already on disk (used at module import time)
    entries = fetcher.get_cached()

    # Async: pull fresh data from both sources and update cache
    import asyncio, os
    asyncio.run(fetcher.refresh(api_key=os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY")))

CLI refresh::

    uv run python -m ttadev.primitives.llm.benchmark_fetcher

"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx

from ttadev.primitives.llm.model_benchmarks import (
    BENCHMARK_DATA,
    MODEL_ID_ALIASES,
    ModelBenchmarkMetadata,
)

__all__ = ["BenchmarkFetcher"]

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

_CACHE_PATH = Path("~/.cache/ttadev/benchmark_data.json").expanduser()
_CACHE_TTL_HOURS: float = 24.0

_AA_API_URL = "https://artificialanalysis.ai/api/v2/data/llms/models"
_AA_ATTRIBUTION = "https://artificialanalysis.ai"

_HF_ROWS_URL = "https://datasets-server.huggingface.co/rows"
_HF_DATASET = "open-llm-leaderboard/contents"
_HF_PAGE_SIZE = 500  # rows per request; max is 500 for this dataset
_HF_ATTRIBUTION = "https://huggingface.co/datasets/open-llm-leaderboard/contents"

_TODAY = time.strftime("%Y-%m-%d")

# ── Artificial Analysis slug → our canonical model ID ─────────────────────────
# Slugs verified against the live AA API (April 2026, 457 models).
# AA uses canonical model slugs — NOT provider-specific suffixes.
# Maps to the IDs we use in ModelRouterPrimitive / model_benchmarks.py.
#
# Verified: GET /api/v2/data/llms/models returns {"data": [...]} where each
# item has "slug", "name", "evaluations", "pricing", "median_output_tokens_per_second".
#
# To discover new slugs: uv run python -m ttadev.primitives.llm.benchmark_fetcher --list-slugs
_AA_SLUG_MAP: dict[str, str] = {
    # ── Groq-served models (AA slug → our Groq API ID) ────────────────────────
    # AA measures models by canonical name; we map to the provider's serving ID.
    "llama-3-3-instruct-70b": "llama-3.3-70b-versatile",
    "llama-4-scout": "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-4-maverick": "meta-llama/llama-4-maverick-17b-128e-instruct",
    "kimi-k2": "moonshotai/kimi-k2-instruct",
    "qwen3-32b-instruct": "qwen/qwen3-32b",
    "gpt-oss-20b": "openai/gpt-oss-20b",
    "gpt-oss-120b": "openai/gpt-oss-120b",
    # Qwen3.6 Plus — confirmed working with OpenHands tool-use (April 2026).
    # AA may track this under "qwen3-6-plus" or "qwen3.6-plus"; add both so
    # whichever slug appears in the live API response is captured.
    "qwen3-6-plus": "qwen/qwen3.6-plus",
    "qwen3.6-plus": "qwen/qwen3.6-plus",
    # ── Gemini (Google) ───────────────────────────────────────────────────────
    "gemini-2-5-flash": "models/gemini-2.5-flash",
    "gemini-2-5-pro": "models/gemini-2.5-pro",
    "gemini-2-5-flash-lite": "models/gemini-2.5-flash-lite",
    "gemini-2-0-flash": "models/gemini-2.0-flash",
    "gemini-1-5-flash": "gemini/gemini-1.5-flash",
    # ── OpenAI ────────────────────────────────────────────────────────────────
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
    "o3": "o3",
    "o3-mini": "o3-mini",
    "o4-mini": "o4-mini",
    # ── Anthropic ─────────────────────────────────────────────────────────────
    "claude-35-sonnet": "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku": "claude-3-5-haiku-20241022",
    "claude-3-7-sonnet": "claude-3-7-sonnet-20250219",
    "claude-sonnet-4-6": "claude-sonnet-4-20250514",
    # ── DeepSeek ─────────────────────────────────────────────────────────────
    "deepseek-r1": "deepseek-r1",
    "deepseek-v3": "deepseek-v3",
    # ── Ollama-local models (also benchmarked by AA) ──────────────────────────
    "phi-4": "phi4:latest",
    "phi-4-mini": "phi4-mini:latest",
    "qwen3-14b-instruct": "qwen3:14b",
    "qwen3-30b-a3b-2507": "qwen3:30b-a3b",
    "qwen3-235b-a22b-instruct": "qwen3:235b-a22b",
}

# ── HF fullname → our canonical model ID ─────────────────────────────────────
# HF Leaderboard 2 uses "fullname" = Hugging Face model repo path.
# These are lowercase-normalised to the IDs we use for benchmark lookups.
_HF_FULLNAME_MAP: dict[str, str] = {
    "meta-llama/llama-3.3-70b-instruct": "llama-3.3-70b-versatile",
    "meta-llama/llama-3.1-8b-instruct": "llama3.1:8b",
    "meta-llama/llama-3.2-3b-instruct": "llama3.2:3b",
    "meta-llama/llama-4-scout-17b-16e-instruct": "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen/qwen2.5-7b-instruct": "qwen2.5:7b",
    "qwen/qwen2.5-14b-instruct": "qwen2.5:14b",
    "qwen/qwen2.5-72b-instruct": "qwen2.5:72b",
    "qwen/qwen3-32b": "qwen/qwen3-32b",
    "google/gemma-2-9b-it": "gemma2:9b",
    "deepseek-ai/deepseek-r1": "deepseek-r1",
    "microsoft/phi-4": "phi4:latest",
    "moonshotai/kimi-k2-instruct": "moonshotai/kimi-k2-instruct",
}


class BenchmarkFetcher:
    """Fetches and caches live benchmark scores from external APIs.

    Attributes:
        cache_path: Path to the on-disk JSON cache file.
        ttl_hours: Cache lifetime in hours (default 24).
    """

    def __init__(
        self,
        cache_path: Path = _CACHE_PATH,
        ttl_hours: float = _CACHE_TTL_HOURS,
    ) -> None:
        self.cache_path = cache_path
        self.ttl_hours = ttl_hours

    # ── Public interface ──────────────────────────────────────────────────────

    def get_cached(self) -> list[ModelBenchmarkMetadata]:
        """Load cached benchmark entries from disk (synchronous).

        Returns an empty list when the cache does not exist or is unreadable.
        Never raises; safe to call at module import time.

        Returns:
            List of :class:`ModelBenchmarkMetadata` from the last successful
            :meth:`refresh` call.
        """
        if not self.cache_path.exists():
            return []
        try:
            raw = json.loads(self.cache_path.read_text(encoding="utf-8"))
            entries: list[ModelBenchmarkMetadata] = []
            for item in raw.get("benchmarks", []):
                try:
                    entries.append(ModelBenchmarkMetadata(**item))
                except (TypeError, ValueError) as exc:
                    logger.debug("Skipping malformed cache entry: %s — %s", item, exc)
            logger.debug("Loaded %d live benchmark entries from cache.", len(entries))
            return entries
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load benchmark cache %s: %s", self.cache_path, exc)
            return []

    async def refresh(
        self,
        api_key: str | None = None,
        *,
        force: bool = False,
    ) -> list[ModelBenchmarkMetadata]:
        """Pull fresh data from all configured sources and update the cache.

        Args:
            api_key: Artificial Analysis API key.  If *None*, reads
                ``ARTIFICIAL_ANALYSIS_API_KEY`` from the environment.  When
                neither is available, the AA source is skipped gracefully.
            force: Skip the TTL check and always refetch.

        Returns:
            All benchmark entries (static + live) after refresh.
        """
        if not force and self._cache_is_fresh():
            logger.debug("Benchmark cache is fresh; skipping refresh.")
            return self.get_cached()

        aa_key = api_key or os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY")
        all_entries: list[dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Artificial Analysis (requires key)
            if aa_key:
                aa = await self._fetch_artificial_analysis(client, aa_key)
                all_entries.extend(aa)
                logger.info("Artificial Analysis: fetched %d benchmark entries.", len(aa))
            else:
                logger.info(
                    "ARTIFICIAL_ANALYSIS_API_KEY not set — skipping AA source. "
                    "Set the key for richer benchmark coverage (free at artificialanalysis.ai)."
                )

            # HF Open LLM Leaderboard 2 (no auth required)
            hf = await self._fetch_hf_leaderboard(client)
            all_entries.extend(hf)
            logger.info("HF Leaderboard 2: fetched %d benchmark entries.", len(hf))

        # Deduplicate: live data wins over static for same (model_id, benchmark)
        live_keys: set[tuple[str, str]] = set()
        deduped: list[dict[str, Any]] = []
        for entry in all_entries:
            key = (entry["model_id"], entry["benchmark"])
            if key not in live_keys:
                live_keys.add(key)
                deduped.append(entry)

        self._write_cache(deduped)
        result = [ModelBenchmarkMetadata(**e) for e in deduped]
        logger.info("Benchmark cache refreshed: %d total entries.", len(result))
        return result

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _cache_is_fresh(self) -> bool:
        """Return True when the cache file exists and is within the TTL."""
        if not self.cache_path.exists():
            return False
        try:
            raw = json.loads(self.cache_path.read_text(encoding="utf-8"))
            fetched_at: float = raw.get("fetched_at", 0.0)
            return (time.time() - fetched_at) < (self.ttl_hours * 3600)
        except Exception:  # noqa: BLE001
            return False

    def _write_cache(self, entries: list[dict[str, Any]]) -> None:
        """Write *entries* to the cache file, creating parent directories."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "fetched_at": time.time(),
            "fetched_date": _TODAY,
            "sources": [_AA_ATTRIBUTION, _HF_ATTRIBUTION],
            "benchmarks": entries,
        }
        self.cache_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.debug("Wrote benchmark cache to %s.", self.cache_path)

    # ── Artificial Analysis ───────────────────────────────────────────────────

    async def _fetch_artificial_analysis(
        self,
        client: httpx.AsyncClient,
        api_key: str,
    ) -> list[dict[str, Any]]:
        """Fetch model evaluations from the Artificial Analysis v2 API.

        Returns:
            List of benchmark entry dicts (ModelBenchmarkMetadata-compatible).
        """
        try:
            resp = await client.get(
                _AA_API_URL,
                headers={"x-api-key": api_key},
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.warning("Artificial Analysis API error %s: %s", exc.response.status_code, exc)
            return []
        except httpx.RequestError as exc:
            logger.warning("Artificial Analysis request failed: %s", exc)
            return []

        payload = resp.json()
        # AA v2 wraps the model list under {"data": [...]}
        models_list: list[dict[str, Any]] = (
            payload if isinstance(payload, list) else payload.get("data", [])
        )
        entries: list[dict[str, Any]] = []

        for model in models_list:
            slug: str = model.get("slug", "")
            canonical = self._resolve_aa_slug(slug)
            if canonical is None:
                continue

            evals: dict[str, Any] = model.get("evaluations") or {}
            speed = model.get("median_output_tokens_per_second")
            ttft = model.get("median_time_to_first_token_seconds")
            pricing: dict[str, Any] = model.get("pricing") or {}

            # Artificial Analysis returns 0–1 fractions; multiply by 100 for our scale.
            def _add(benchmark: str, raw_val: Any) -> None:
                if raw_val is None:
                    return
                score = float(raw_val)
                # Intelligence/coding/math indices are already 0–100
                if benchmark not in ("aa_intelligence", "aa_coding", "aa_math"):
                    score = score * 100.0
                entries.append(
                    {
                        "model_id": canonical,
                        "benchmark": benchmark,
                        "score": round(score, 2),
                        "source_url": _AA_ATTRIBUTION,
                        "measured_date": _TODAY,
                        "notes": (
                            f"Live from Artificial Analysis ({_TODAY}); "
                            f"AA slug: {slug!r}. "
                            "Attribution: artificialanalysis.ai"
                        ),
                    }
                )

            _add("aa_intelligence", evals.get("artificial_analysis_intelligence_index"))
            _add("aa_coding", evals.get("artificial_analysis_coding_index"))
            _add("aa_math", evals.get("artificial_analysis_math_index"))
            _add("mmlu_pro", evals.get("mmlu_pro"))
            _add("gpqa", evals.get("gpqa"))
            _add("livebench", evals.get("livecodebench"))
            _add("math", evals.get("math_500"))
            _add("aime", evals.get("aime"))

            # Speed entries (tokens/sec stored as score for routing heuristics)
            if speed is not None:
                entries.append(
                    {
                        "model_id": canonical,
                        "benchmark": "aa_speed_tok_per_sec",
                        "score": round(float(speed), 1),
                        "source_url": _AA_ATTRIBUTION,
                        "measured_date": _TODAY,
                        "notes": (
                            f"Median output tokens/sec from Artificial Analysis ({_TODAY}). "
                            "Attribution: artificialanalysis.ai"
                        ),
                    }
                )

            if ttft is not None:
                entries.append(
                    {
                        "model_id": canonical,
                        "benchmark": "aa_ttft_seconds",
                        "score": round(float(ttft), 3),
                        "source_url": _AA_ATTRIBUTION,
                        "measured_date": _TODAY,
                        "notes": (
                            f"Median TTFT seconds from Artificial Analysis ({_TODAY}). "
                            "Attribution: artificialanalysis.ai"
                        ),
                    }
                )

            # Store input token pricing as a meta-benchmark for cost-aware routing
            price_input = pricing.get("price_1m_input_tokens")
            if price_input is not None:
                entries.append(
                    {
                        "model_id": canonical,
                        "benchmark": "aa_price_per_1m_input",
                        "score": round(float(price_input), 4),
                        "source_url": _AA_ATTRIBUTION,
                        "measured_date": _TODAY,
                        "notes": (
                            f"USD per 1M input tokens from Artificial Analysis ({_TODAY}). "
                            "Attribution: artificialanalysis.ai"
                        ),
                    }
                )

        return entries

    def _resolve_aa_slug(self, slug: str) -> str | None:
        """Return our canonical model ID for an AA slug, or None to skip."""
        if not slug:
            return None
        # Direct lookup
        if slug in _AA_SLUG_MAP:
            return _AA_SLUG_MAP[slug]
        # Try the model_benchmarks alias table too (normalised)
        if slug in MODEL_ID_ALIASES:
            return MODEL_ID_ALIASES[slug]
        logger.debug("AA slug %r not in mapping — skipping.", slug)
        return None

    # ── HF Open LLM Leaderboard 2 ─────────────────────────────────────────────

    async def _fetch_hf_leaderboard(
        self,
        client: httpx.AsyncClient,
    ) -> list[dict[str, Any]]:
        """Fetch model scores from the HF Open LLM Leaderboard 2 dataset.

        Paginates through the full dataset (4500+ rows).  No authentication is
        required for this public dataset.

        Returns:
            List of benchmark entry dicts (ModelBenchmarkMetadata-compatible).
        """
        entries: list[dict[str, Any]] = []
        offset = 0

        while True:
            try:
                resp = await client.get(
                    _HF_ROWS_URL,
                    params={
                        "dataset": _HF_DATASET,
                        "config": "default",
                        "split": "train",
                        "offset": offset,
                        "limit": _HF_PAGE_SIZE,
                    },
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "HF Leaderboard error %s at offset %d: %s",
                    exc.response.status_code,
                    offset,
                    exc,
                )
                break
            except httpx.RequestError as exc:
                logger.warning("HF Leaderboard request failed at offset %d: %s", offset, exc)
                break

            payload = resp.json()
            rows: list[dict[str, Any]] = payload.get("rows", [])
            if not rows:
                break

            for row_wrapper in rows:
                row: dict[str, Any] = row_wrapper.get("row", {})
                fullname: str = row.get("fullname", "").strip()
                if not fullname:
                    continue

                canonical = self._resolve_hf_fullname(fullname)
                if canonical is None:
                    continue

                def _hf_add(benchmark: str, field: str) -> None:
                    val = row.get(field)
                    if val is None:
                        return
                    try:
                        score = float(val)
                    except (TypeError, ValueError):
                        return
                    entries.append(
                        {
                            "model_id": canonical,
                            "benchmark": benchmark,
                            "score": round(score, 2),
                            "source_url": _HF_ATTRIBUTION,
                            "measured_date": _TODAY,
                            "notes": (
                                f"HF Open LLM Leaderboard 2 ({_TODAY}); "
                                f"HF fullname: {fullname!r}. "
                                "Scores on 0-100 scale."
                            ),
                        }
                    )

                _hf_add("mmlu_pro", "MMLU-PRO")
                _hf_add("gpqa", "GPQA")
                _hf_add("bbh", "BBH")
                _hf_add("math", "MATH Lvl 5")
                _hf_add("musr", "MUSR")
                _hf_add("ifeval", "IFEval")

                avg = row.get("Average \u2b06\ufe0f")  # "Average ⬆️"
                if avg is not None:
                    try:
                        entries.append(
                            {
                                "model_id": canonical,
                                "benchmark": "hf_average",
                                "score": round(float(avg), 2),
                                "source_url": _HF_ATTRIBUTION,
                                "measured_date": _TODAY,
                                "notes": (
                                    f"HF Open LLM Leaderboard 2 average score ({_TODAY}); "
                                    f"HF fullname: {fullname!r}."
                                ),
                            }
                        )
                    except (TypeError, ValueError):
                        pass

            num_rows = payload.get("num_rows_total", 0)
            offset += len(rows)
            if offset >= num_rows:
                break

        return entries

    def _resolve_hf_fullname(self, fullname: str) -> str | None:
        """Return our canonical model ID for a HF fullname, or None to skip."""
        lower = fullname.lower()
        # Direct lookup (already lower-keyed in the map)
        if lower in _HF_FULLNAME_MAP:
            return _HF_FULLNAME_MAP[lower]
        # Try the model_benchmarks alias table with the lower form
        if lower in MODEL_ID_ALIASES:
            return MODEL_ID_ALIASES[lower]
        # Try unmodified fullname in alias table (some aliases preserve case)
        if fullname in MODEL_ID_ALIASES:
            return MODEL_ID_ALIASES[fullname]
        logger.debug("HF fullname %r not in mapping — skipping.", fullname)
        return None


# ── Module-level helper ────────────────────────────────────────────────────────


def load_live_benchmarks_into_global() -> None:
    """Append cached live benchmarks into BENCHMARK_DATA (call once at import).

    This function is idempotent on repeated calls because it checks for
    existing (model_id, benchmark) pairs before appending.

    Note: This is called automatically by :mod:`model_benchmarks` at the
    bottom of its module body.  You should not need to call it directly.
    """
    fetcher = BenchmarkFetcher()
    live = fetcher.get_cached()
    if not live:
        return

    existing_keys: set[tuple[str, str]] = {(e.model_id, e.benchmark) for e in BENCHMARK_DATA}
    added = 0
    for entry in live:
        key = (entry.model_id, entry.benchmark)
        if key not in existing_keys:
            BENCHMARK_DATA.append(entry)
            existing_keys.add(key)
            added += 1
    if added:
        logger.debug("Merged %d live benchmark entries into BENCHMARK_DATA.", added)


# ── CLI entry point ────────────────────────────────────────────────────────────


async def _cli_main() -> None:
    import sys

    force = "--force" in sys.argv or "-f" in sys.argv
    list_slugs = "--list-slugs" in sys.argv
    api_key = os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY")

    if list_slugs:
        if not api_key:
            print("ARTIFICIAL_ANALYSIS_API_KEY required for --list-slugs", flush=True)
            return
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(_AA_API_URL, headers={"x-api-key": api_key})
            resp.raise_for_status()
            payload = resp.json()
            models_list = payload if isinstance(payload, list) else payload.get("data", [])
            print(f"Artificial Analysis: {len(models_list)} models")
            for m in models_list:
                slug = m.get("slug", "")
                mapped = _AA_SLUG_MAP.get(slug, "(not mapped)")
                print(f"  {slug!r:50s}  → {mapped!r:40s}  {m.get('name', '')}")
        return

    if not api_key:
        print(
            "ℹ  ARTIFICIAL_ANALYSIS_API_KEY not set — only HF Leaderboard data will be fetched.\n"
            "   Register free at https://artificialanalysis.ai to unlock richer data.",
            flush=True,
        )

    print(f"Fetching benchmark data (force={force})...", flush=True)
    fetcher = BenchmarkFetcher()
    entries = await fetcher.refresh(api_key=api_key, force=force)
    print(f"✓ Cache updated: {len(entries)} benchmark entries", flush=True)
    print(f"  Cache file: {fetcher.cache_path}", flush=True)

    # Print a quick summary
    from collections import defaultdict

    by_model: dict[str, list[str]] = defaultdict(list)
    for e in entries:
        by_model[e.model_id].append(e.benchmark)
    print(f"\nModels with live data ({len(by_model)}):")
    for mid, benchmarks in sorted(by_model.items()):
        print(f"  {mid}: {', '.join(sorted(set(benchmarks)))}")


if __name__ == "__main__":
    asyncio.run(_cli_main())
