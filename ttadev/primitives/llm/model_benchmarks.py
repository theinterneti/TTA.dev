"""Published benchmark metadata for known LLM models.

Curated, read-only scores from public leaderboards and papers.
Used by ModelRegistryPrimitive to inform model selection.

All scores are expressed as percentages (0.0–100.0). MT-Bench scores
(native 1–10 scale) are multiplied by 10 to normalise to 0–100; the
``notes`` field records the original scale.

Sources:
    * Qwen2.5 report: https://qwenlm.github.io/blog/qwen2.5/
    * Qwen2.5-Coder report: https://qwenlm.github.io/blog/qwen2.5-coder/
    * Llama 3.1 blog: https://ai.meta.com/blog/meta-llama-3-1/
    * Llama 3.2 blog: https://ai.meta.com/blog/llama-3-2-connect-2024-vision-edge-mobile-devices/
    * Llama 3.3 blog: https://ai.meta.com/blog/llama-3-3/
    * Gemma 2 technical report: https://storage.googleapis.com/deepmind-media/gemma/gemma2-report.pdf
    * Mistral 7B: https://arxiv.org/abs/2310.06825
    * Mistral Nemo: https://mistral.ai/news/mistral-nemo/
    * Mixtral 8x7B: https://arxiv.org/abs/2401.04088
    * GPT-4o: https://openai.com/index/hello-gpt-4o/
    * GPT-4o Mini: https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/
    * Claude model cards: https://www.anthropic.com/news/claude-3-5-sonnet
    * Gemini 1.5: https://storage.googleapis.com/deepmind-media/gemini/gemini_v1_5_report.pdf
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "ModelBenchmarkMetadata",
    "BENCHMARK_DATA",
    "KNOWN_BENCHMARKS",
    "get_benchmarks",
    "get_best_score",
    "models_above_threshold",
]

# ── Constants ─────────────────────────────────────────────────────────────────

KNOWN_BENCHMARKS: frozenset[str] = frozenset(
    {"mmlu", "humaneval", "math", "mt_bench", "gpqa", "mbpp"}
)


# ── Data model ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ModelBenchmarkMetadata:
    """A single published benchmark result for one model.

    Attributes:
        model_id: Matches ``ModelEntry.model_id`` in the model registry.
        benchmark: Benchmark identifier — one of ``"mmlu"``, ``"humaneval"``,
            ``"math"``, ``"mt_bench"``, ``"gpqa"``, or ``"mbpp"``.
        score: Result as a percentage (0.0–100.0).  MT-Bench native scores
            (1–10) are multiplied by 10.
        source_url: Canonical paper or leaderboard URL.
        measured_date: ISO 8601 date string, e.g. ``"2024-09-15"``.
        notes: Free-text context such as shot count or evaluation protocol.
    """

    model_id: str
    benchmark: str
    score: float
    source_url: str
    measured_date: str
    notes: str = ""


# ── Curated benchmark data ────────────────────────────────────────────────────
# All values are from the papers / leaderboard pages cited in the module
# docstring. Scores reflect the best published number at the cited date.

_QWEN_URL = "https://qwenlm.github.io/blog/qwen2.5/"
_QWEN_CODER_URL = "https://qwenlm.github.io/blog/qwen2.5-coder/"
_LLAMA31_URL = "https://ai.meta.com/blog/meta-llama-3-1/"
_LLAMA32_URL = "https://ai.meta.com/blog/llama-3-2-connect-2024-vision-edge-mobile-devices/"
_LLAMA33_URL = "https://ai.meta.com/blog/llama-3-3/"
_GEMMA2_URL = "https://storage.googleapis.com/deepmind-media/gemma/gemma2-report.pdf"
_MISTRAL7B_URL = "https://arxiv.org/abs/2310.06825"
_MISTRAL_NEMO_URL = "https://mistral.ai/news/mistral-nemo/"
_MIXTRAL_URL = "https://arxiv.org/abs/2401.04088"
_GPT4O_URL = "https://openai.com/index/hello-gpt-4o/"
_GPT4O_MINI_URL = "https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/"
_CLAUDE35_URL = "https://www.anthropic.com/news/claude-3-5-sonnet"
_CLAUDE3_URL = "https://www.anthropic.com/news/claude-3-family"
_GEMINI15_URL = "https://storage.googleapis.com/deepmind-media/gemini/gemini_v1_5_report.pdf"

BENCHMARK_DATA: list[ModelBenchmarkMetadata] = [
    # ── Qwen2.5 7B ───────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="qwen2.5:7b",
        benchmark="mmlu",
        score=74.2,
        source_url=_QWEN_URL,
        measured_date="2024-09-15",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="qwen2.5:7b",
        benchmark="humaneval",
        score=84.1,
        source_url=_QWEN_URL,
        measured_date="2024-09-15",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="qwen2.5:7b",
        benchmark="math",
        score=75.5,
        source_url=_QWEN_URL,
        measured_date="2024-09-15",
        notes="4-shot, chain-of-thought",
    ),
    # ── Qwen2.5 14B ──────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="qwen2.5:14b",
        benchmark="mmlu",
        score=79.7,
        source_url=_QWEN_URL,
        measured_date="2024-09-15",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="qwen2.5:14b",
        benchmark="humaneval",
        score=86.1,
        source_url=_QWEN_URL,
        measured_date="2024-09-15",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="qwen2.5:14b",
        benchmark="math",
        score=80.0,
        source_url=_QWEN_URL,
        measured_date="2024-09-15",
        notes="4-shot, chain-of-thought",
    ),
    # ── Qwen2.5 72B ──────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="qwen2.5:72b",
        benchmark="mmlu",
        score=86.1,
        source_url=_QWEN_URL,
        measured_date="2024-09-15",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="qwen2.5:72b",
        benchmark="humaneval",
        score=86.6,
        source_url=_QWEN_URL,
        measured_date="2024-09-15",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="qwen2.5:72b",
        benchmark="math",
        score=83.1,
        source_url=_QWEN_URL,
        measured_date="2024-09-15",
        notes="4-shot, chain-of-thought",
    ),
    ModelBenchmarkMetadata(
        model_id="qwen2.5:72b",
        benchmark="gpqa",
        score=49.0,
        source_url=_QWEN_URL,
        measured_date="2024-09-15",
        notes="diamond split, 0-shot",
    ),
    # ── Qwen2.5-Coder 7B ─────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="qwen2.5-coder:7b",
        benchmark="mmlu",
        score=72.2,
        source_url=_QWEN_CODER_URL,
        measured_date="2024-11-12",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="qwen2.5-coder:7b",
        benchmark="humaneval",
        score=84.1,
        source_url=_QWEN_CODER_URL,
        measured_date="2024-11-12",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="qwen2.5-coder:7b",
        benchmark="mbpp",
        score=75.2,
        source_url=_QWEN_CODER_URL,
        measured_date="2024-11-12",
        notes="pass@1, sanitised split",
    ),
    # ── Qwen2.5-Coder 32B ────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="qwen2.5-coder:32b",
        benchmark="mmlu",
        score=83.0,
        source_url=_QWEN_CODER_URL,
        measured_date="2024-11-12",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="qwen2.5-coder:32b",
        benchmark="humaneval",
        score=92.7,
        source_url=_QWEN_CODER_URL,
        measured_date="2024-11-12",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="qwen2.5-coder:32b",
        benchmark="mbpp",
        score=90.2,
        source_url=_QWEN_CODER_URL,
        measured_date="2024-11-12",
        notes="pass@1, sanitised split",
    ),
    ModelBenchmarkMetadata(
        model_id="qwen2.5-coder:32b",
        benchmark="math",
        score=79.2,
        source_url=_QWEN_CODER_URL,
        measured_date="2024-11-12",
        notes="4-shot, chain-of-thought",
    ),
    # ── Llama 3.2 3B ─────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="llama3.2:3b",
        benchmark="mmlu",
        score=63.4,
        source_url=_LLAMA32_URL,
        measured_date="2024-09-25",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="llama3.2:3b",
        benchmark="humaneval",
        score=45.8,
        source_url=_LLAMA32_URL,
        measured_date="2024-09-25",
        notes="pass@1",
    ),
    # ── Llama 3.2 1B ─────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="llama3.2:1b",
        benchmark="mmlu",
        score=49.3,
        source_url=_LLAMA32_URL,
        measured_date="2024-09-25",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="llama3.2:1b",
        benchmark="humaneval",
        score=28.7,
        source_url=_LLAMA32_URL,
        measured_date="2024-09-25",
        notes="pass@1",
    ),
    # ── Llama 3.1 8B ─────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="llama3.1:8b",
        benchmark="mmlu",
        score=73.0,
        source_url=_LLAMA31_URL,
        measured_date="2024-07-23",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="llama3.1:8b",
        benchmark="humaneval",
        score=72.6,
        source_url=_LLAMA31_URL,
        measured_date="2024-07-23",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="llama3.1:8b",
        benchmark="math",
        score=51.9,
        source_url=_LLAMA31_URL,
        measured_date="2024-07-23",
        notes="4-shot, chain-of-thought",
    ),
    # ── Llama 3.1 70B ────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="llama3.1:70b",
        benchmark="mmlu",
        score=86.0,
        source_url=_LLAMA31_URL,
        measured_date="2024-07-23",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="llama3.1:70b",
        benchmark="humaneval",
        score=80.5,
        source_url=_LLAMA31_URL,
        measured_date="2024-07-23",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="llama3.1:70b",
        benchmark="math",
        score=68.0,
        source_url=_LLAMA31_URL,
        measured_date="2024-07-23",
        notes="4-shot, chain-of-thought",
    ),
    ModelBenchmarkMetadata(
        model_id="llama3.1:70b",
        benchmark="gpqa",
        score=46.7,
        source_url=_LLAMA31_URL,
        measured_date="2024-07-23",
        notes="diamond split, 0-shot",
    ),
    # ── Llama 3.3 70B ────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="llama3.3:70b",
        benchmark="mmlu",
        score=86.0,
        source_url=_LLAMA33_URL,
        measured_date="2024-12-06",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="llama3.3:70b",
        benchmark="humaneval",
        score=88.4,
        source_url=_LLAMA33_URL,
        measured_date="2024-12-06",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="llama3.3:70b",
        benchmark="math",
        score=77.0,
        source_url=_LLAMA33_URL,
        measured_date="2024-12-06",
        notes="4-shot, chain-of-thought",
    ),
    # ── Gemma 2 2B ───────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="gemma2:2b",
        benchmark="mmlu",
        score=52.2,
        source_url=_GEMMA2_URL,
        measured_date="2024-06-27",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="gemma2:2b",
        benchmark="humaneval",
        score=35.4,
        source_url=_GEMMA2_URL,
        measured_date="2024-06-27",
        notes="pass@1",
    ),
    # ── Gemma 2 9B ───────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="gemma2:9b",
        benchmark="mmlu",
        score=71.3,
        source_url=_GEMMA2_URL,
        measured_date="2024-06-27",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="gemma2:9b",
        benchmark="humaneval",
        score=54.3,
        source_url=_GEMMA2_URL,
        measured_date="2024-06-27",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="gemma2:9b",
        benchmark="math",
        score=44.3,
        source_url=_GEMMA2_URL,
        measured_date="2024-06-27",
        notes="4-shot, chain-of-thought",
    ),
    # ── Gemma 2 27B ──────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="gemma2:27b",
        benchmark="mmlu",
        score=75.2,
        source_url=_GEMMA2_URL,
        measured_date="2024-06-27",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="gemma2:27b",
        benchmark="humaneval",
        score=51.8,
        source_url=_GEMMA2_URL,
        measured_date="2024-06-27",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="gemma2:27b",
        benchmark="math",
        score=55.2,
        source_url=_GEMMA2_URL,
        measured_date="2024-06-27",
        notes="4-shot, chain-of-thought",
    ),
    # ── Mistral 7B ───────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="mistral:7b",
        benchmark="mmlu",
        score=62.5,
        source_url=_MISTRAL7B_URL,
        measured_date="2023-10-10",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="mistral:7b",
        benchmark="humaneval",
        score=26.2,
        source_url=_MISTRAL7B_URL,
        measured_date="2023-10-10",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="mistral:7b",
        benchmark="mt_bench",
        score=74.0,
        source_url=_MISTRAL7B_URL,
        measured_date="2023-10-10",
        notes="native score 7.40/10, scaled ×10",
    ),
    # ── Mistral Nemo 12B ─────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="mistral-nemo:12b",
        benchmark="mmlu",
        score=68.0,
        source_url=_MISTRAL_NEMO_URL,
        measured_date="2024-07-18",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="mistral-nemo:12b",
        benchmark="humaneval",
        score=51.3,
        source_url=_MISTRAL_NEMO_URL,
        measured_date="2024-07-18",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="mistral-nemo:12b",
        benchmark="mt_bench",
        score=79.0,
        source_url=_MISTRAL_NEMO_URL,
        measured_date="2024-07-18",
        notes="native score 7.90/10, scaled ×10",
    ),
    # ── Mixtral 8x7B ─────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="mixtral:8x7b",
        benchmark="mmlu",
        score=70.6,
        source_url=_MIXTRAL_URL,
        measured_date="2024-01-08",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="mixtral:8x7b",
        benchmark="humaneval",
        score=40.2,
        source_url=_MIXTRAL_URL,
        measured_date="2024-01-08",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="mixtral:8x7b",
        benchmark="mt_bench",
        score=87.0,
        source_url=_MIXTRAL_URL,
        measured_date="2024-01-08",
        notes="native score 8.70/10, scaled ×10",
    ),
    ModelBenchmarkMetadata(
        model_id="mixtral:8x7b",
        benchmark="math",
        score=28.4,
        source_url=_MIXTRAL_URL,
        measured_date="2024-01-08",
        notes="4-shot, chain-of-thought",
    ),
    # ── GPT-4o Mini ──────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="gpt-4o-mini",
        benchmark="mmlu",
        score=82.0,
        source_url=_GPT4O_MINI_URL,
        measured_date="2024-07-18",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="gpt-4o-mini",
        benchmark="humaneval",
        score=87.2,
        source_url=_GPT4O_MINI_URL,
        measured_date="2024-07-18",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="gpt-4o-mini",
        benchmark="math",
        score=70.2,
        source_url=_GPT4O_MINI_URL,
        measured_date="2024-07-18",
        notes="4-shot, chain-of-thought",
    ),
    # ── GPT-4o ───────────────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="gpt-4o",
        benchmark="mmlu",
        score=88.7,
        source_url=_GPT4O_URL,
        measured_date="2024-05-13",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="gpt-4o",
        benchmark="humaneval",
        score=90.2,
        source_url=_GPT4O_URL,
        measured_date="2024-05-13",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="gpt-4o",
        benchmark="math",
        score=76.6,
        source_url=_GPT4O_URL,
        measured_date="2024-05-13",
        notes="4-shot, chain-of-thought",
    ),
    ModelBenchmarkMetadata(
        model_id="gpt-4o",
        benchmark="gpqa",
        score=53.6,
        source_url=_GPT4O_URL,
        measured_date="2024-05-13",
        notes="diamond split, 0-shot",
    ),
    # ── Claude 3 Haiku ───────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="claude-3-haiku-20240307",
        benchmark="mmlu",
        score=75.2,
        source_url=_CLAUDE3_URL,
        measured_date="2024-03-04",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="claude-3-haiku-20240307",
        benchmark="humaneval",
        score=75.9,
        source_url=_CLAUDE3_URL,
        measured_date="2024-03-04",
        notes="pass@1",
    ),
    # ── Claude 3.5 Sonnet ────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="claude-3-5-sonnet-20241022",
        benchmark="mmlu",
        score=88.7,
        source_url=_CLAUDE35_URL,
        measured_date="2024-10-22",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="claude-3-5-sonnet-20241022",
        benchmark="humaneval",
        score=93.7,
        source_url=_CLAUDE35_URL,
        measured_date="2024-10-22",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="claude-3-5-sonnet-20241022",
        benchmark="gpqa",
        score=59.4,
        source_url=_CLAUDE35_URL,
        measured_date="2024-10-22",
        notes="diamond split, 0-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="claude-3-5-sonnet-20241022",
        benchmark="math",
        score=78.3,
        source_url=_CLAUDE35_URL,
        measured_date="2024-10-22",
        notes="4-shot, chain-of-thought",
    ),
    # ── Gemini 1.5 Flash ─────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="gemini/gemini-1.5-flash",
        benchmark="mmlu",
        score=78.9,
        source_url=_GEMINI15_URL,
        measured_date="2024-05-14",
        notes="5-shot",
    ),
    ModelBenchmarkMetadata(
        model_id="gemini/gemini-1.5-flash",
        benchmark="humaneval",
        score=74.4,
        source_url=_GEMINI15_URL,
        measured_date="2024-05-14",
        notes="pass@1",
    ),
    ModelBenchmarkMetadata(
        model_id="gemini/gemini-1.5-flash",
        benchmark="math",
        score=58.5,
        source_url=_GEMINI15_URL,
        measured_date="2024-05-14",
        notes="4-shot, chain-of-thought",
    ),
    # ── Groq / Llama 3.3 70B Versatile ──────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="groq/llama-3.3-70b-versatile",
        benchmark="mmlu",
        score=86.0,
        source_url=_LLAMA33_URL,
        measured_date="2024-12-06",
        notes="5-shot; same weights as llama3.3:70b served via Groq",
    ),
    ModelBenchmarkMetadata(
        model_id="groq/llama-3.3-70b-versatile",
        benchmark="humaneval",
        score=88.4,
        source_url=_LLAMA33_URL,
        measured_date="2024-12-06",
        notes="pass@1; same weights as llama3.3:70b served via Groq",
    ),
]


# ── Lookup helpers ────────────────────────────────────────────────────────────


def get_benchmarks(model_id: str) -> list[ModelBenchmarkMetadata]:
    """Return all benchmark entries for a given model ID.

    Args:
        model_id: The model identifier to look up (must match
            ``ModelBenchmarkMetadata.model_id`` exactly).

    Returns:
        A list of all :class:`ModelBenchmarkMetadata` records whose
        ``model_id`` matches the argument.  Returns an empty list when
        the model is unknown.

    Example::

        entries = get_benchmarks("qwen2.5:7b")
        for e in entries:
            print(e.benchmark, e.score)
    """
    return [entry for entry in BENCHMARK_DATA if entry.model_id == model_id]


def get_best_score(model_id: str, benchmark: str) -> float | None:
    """Return the highest published score for a model on a benchmark.

    When a model has multiple entries for the same benchmark (e.g. from
    different papers), the maximum is returned.

    Args:
        model_id: Model identifier matching ``ModelBenchmarkMetadata.model_id``.
        benchmark: Benchmark name, e.g. ``"mmlu"`` or ``"humaneval"``.

    Returns:
        The highest score (0.0–100.0) found, or ``None`` if no data exists
        for this model/benchmark combination.

    Example::

        score = get_best_score("gpt-4o", "humaneval")
        if score is not None and score >= 90.0:
            print("Strong coding model")
    """
    scores = [
        entry.score
        for entry in BENCHMARK_DATA
        if entry.model_id == model_id and entry.benchmark == benchmark
    ]
    return max(scores) if scores else None


def models_above_threshold(benchmark: str, min_score: float) -> list[str]:
    """Return all model IDs that meet a minimum score on a benchmark.

    Args:
        benchmark: Benchmark name, e.g. ``"mmlu"`` or ``"humaneval"``.
        min_score: Minimum score threshold (0.0–100.0, inclusive).

    Returns:
        Deduplicated list of model IDs (in stable insertion order) where the
        best published score for that benchmark is >= *min_score*.

    Example::

        top_coders = models_above_threshold("humaneval", 85.0)
        print(top_coders)
        # ['qwen2.5:14b', 'qwen2.5:72b', ...]
    """
    seen: dict[str, float] = {}
    for entry in BENCHMARK_DATA:
        if entry.benchmark == benchmark:
            current_best = seen.get(entry.model_id, float("-inf"))
            if entry.score > current_best:
                seen[entry.model_id] = entry.score

    return [mid for mid, score in seen.items() if score >= min_score]
