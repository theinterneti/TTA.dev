"""Published benchmark metadata for known LLM models.

Curated, read-only scores from public leaderboards and papers.
Used by ModelRegistryPrimitive to inform model selection.

All scores are expressed as percentages (0.0–100.0) **except** for the
``"arena_elo"`` benchmark, which stores raw LMSYS Chatbot Arena ELO scores
on a 0–2000 scale.  The ``notes`` field on every ``arena_elo`` entry records
the scale explicitly.  MT-Bench scores (native 1–10 scale) are multiplied
by 10 to normalise to 0–100; the ``notes`` field records the original scale.

Sources:
    * Qwen2.5 report: https://qwenlm.github.io/blog/qwen2.5/
    * Qwen2.5-Coder report: https://qwenlm.github.io/blog/qwen2.5-coder/
    * Llama 3.1 blog: https://ai.meta.com/blog/meta-llama-3-1/
    * Llama 3.2 blog: https://ai.meta.com/blog/llama-3-2-connect-2024-vision-edge-mobile-devices/
    * Llama 3.3 blog: https://ai.meta.com/blog/llama-3-3/
    * Llama 4 blog: https://ai.meta.com/blog/llama-4-multimodal-intelligence/
    * Qwen3 technical report: https://arxiv.org/pdf/2505.09388
    * Kimi K2 GitHub: https://github.com/MoonshotAI/Kimi-K2
    * Gemma 2 technical report: https://storage.googleapis.com/deepmind-media/gemma/gemma2-report.pdf
    * Mistral 7B: https://arxiv.org/abs/2310.06825
    * Mistral Nemo: https://mistral.ai/news/mistral-nemo/
    * Mixtral 8x7B: https://arxiv.org/abs/2401.04088
    * GPT-4o: https://openai.com/index/hello-gpt-4o/
    * GPT-4o Mini: https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/
    * Claude model cards: https://www.anthropic.com/news/claude-3-5-sonnet
    * Gemini 1.5: https://storage.googleapis.com/deepmind-media/gemini/gemini_v1_5_report.pdf
    * LMSYS Chatbot Arena: https://lmsys.org/blog/2023-05-03-arena/
    * LM Market Cap benchmarks: https://lmmarketcap.com/benchmarks
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "ModelBenchmarkMetadata",
    "BENCHMARK_DATA",
    "KNOWN_BENCHMARKS",
    "MODEL_ID_ALIASES",
    "resolve_model_id",
    "get_benchmarks",
    "get_best_score",
    "models_above_threshold",
]

# ── Constants ─────────────────────────────────────────────────────────────────

KNOWN_BENCHMARKS: frozenset[str] = frozenset(
    {
        # Static curated benchmarks
        "mmlu",
        "humaneval",
        "math",
        "mt_bench",
        "gpqa",
        "mbpp",
        "arena_elo",
        # Live benchmarks from Artificial Analysis (artificialanalysis.ai)
        "mmlu_pro",
        "livebench",
        "aime",
        "aa_intelligence",
        "aa_coding",
        "aa_math",
        "aa_speed_tok_per_sec",
        "aa_ttft_seconds",
        "aa_price_per_1m_input",
        # Live benchmarks from HF Open LLM Leaderboard 2
        "bbh",
        "musr",
        "ifeval",
        "hf_average",
    }
)
#: ``"arena_elo"`` stores raw LMSYS Chatbot Arena ELO on a **0–2000 scale**,
#: NOT normalised to 0–100 like all other benchmarks.  This intentional
#: exception is noted in every ``arena_elo`` entry's ``notes`` field.


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
_QWEN3_URL = "https://arxiv.org/pdf/2505.09388"
_LLAMA31_URL = "https://ai.meta.com/blog/meta-llama-3-1/"
_LLAMA32_URL = "https://ai.meta.com/blog/llama-3-2-connect-2024-vision-edge-mobile-devices/"
_LLAMA33_URL = "https://ai.meta.com/blog/llama-3-3/"
_LLAMA4_URL = "https://ai.meta.com/blog/llama-4-multimodal-intelligence/"
_KIMI_K2_URL = "https://github.com/MoonshotAI/Kimi-K2"
_GEMMA2_URL = "https://storage.googleapis.com/deepmind-media/gemma/gemma2-report.pdf"
_MISTRAL7B_URL = "https://arxiv.org/abs/2310.06825"
_MISTRAL_NEMO_URL = "https://mistral.ai/news/mistral-nemo/"
_MIXTRAL_URL = "https://arxiv.org/abs/2401.04088"
_GPT4O_URL = "https://openai.com/index/hello-gpt-4o/"
_GPT4O_MINI_URL = "https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/"
_CLAUDE35_URL = "https://www.anthropic.com/news/claude-3-5-sonnet"
_CLAUDE3_URL = "https://www.anthropic.com/news/claude-3-family"
_GEMINI15_URL = "https://storage.googleapis.com/deepmind-media/gemini/gemini_v1_5_report.pdf"
_LMSYS_URL = "https://lmsys.org/blog/2023-05-03-arena/"
_LMMARKETCAP_URL = "https://lmmarketcap.com/benchmarks"

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
    # ── Groq / Llama 3.3 70B Versatile — Arena ELO ──────────────────────────
    ModelBenchmarkMetadata(
        model_id="llama-3.3-70b-versatile",
        benchmark="mmlu",
        score=86.0,
        source_url=_LLAMA33_URL,
        measured_date="2024-12-06",
        notes="5-shot; Groq-hosted Llama 3.3 70B",
    ),
    ModelBenchmarkMetadata(
        model_id="llama-3.3-70b-versatile",
        benchmark="humaneval",
        score=88.4,
        source_url=_LLAMA33_URL,
        measured_date="2024-12-06",
        notes="pass@1; Groq-hosted Llama 3.3 70B",
    ),
    ModelBenchmarkMetadata(
        model_id="llama-3.3-70b-versatile",
        benchmark="arena_elo",
        score=1420.0,
        source_url=_LMSYS_URL,
        measured_date="2025-01-01",
        notes="LMSYS Chatbot Arena ELO; 0–2000 scale (NOT a percentage); approximate",
    ),
    # ── Groq / Gemma 2 9B IT ─────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="gemma2-9b-it",
        benchmark="mmlu",
        score=71.3,
        source_url=_GEMMA2_URL,
        measured_date="2024-06-27",
        notes="5-shot; Groq-hosted Gemma 2 9B IT (same weights as gemma2:9b)",
    ),
    ModelBenchmarkMetadata(
        model_id="gemma2-9b-it",
        benchmark="arena_elo",
        score=1355.0,
        source_url=_LMSYS_URL,
        measured_date="2025-01-01",
        notes="LMSYS Chatbot Arena ELO; 0–2000 scale (NOT a percentage); approximate",
    ),
    # ── Groq / Mixtral 8x7B 32768 ────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="mixtral-8x7b-32768",
        benchmark="mmlu",
        score=70.6,
        source_url=_MIXTRAL_URL,
        measured_date="2024-01-08",
        notes="5-shot; Groq-hosted Mixtral 8x7B (same weights as mixtral:8x7b)",
    ),
    ModelBenchmarkMetadata(
        model_id="mixtral-8x7b-32768",
        benchmark="humaneval",
        score=40.2,
        source_url=_MIXTRAL_URL,
        measured_date="2024-01-08",
        notes="pass@1; Groq-hosted Mixtral 8x7B",
    ),
    ModelBenchmarkMetadata(
        model_id="mixtral-8x7b-32768",
        benchmark="arena_elo",
        score=1350.0,
        source_url=_LMSYS_URL,
        measured_date="2025-01-01",
        notes="LMSYS Chatbot Arena ELO; 0–2000 scale (NOT a percentage); approximate",
    ),
    # ── Gemini 2.5 Pro ───────────────────────────────────────────────────────
    ModelBenchmarkMetadata(
        model_id="models/gemini-2.5-pro",
        benchmark="mmlu",
        score=90.8,
        source_url=_LMMARKETCAP_URL,
        measured_date="2025-01-01",
        notes="5-shot; highest published MMLU for Gemini 2.5 Pro",
    ),
    # ── Gemini 2.5 Flash ─────────────────────────────────────────────────────
    # Source: Google DeepMind Gemini 2.5 Flash technical report (May 2025)
    # https://storage.googleapis.com/deepmind-media/gemini/gemini25_flash_technical_report.pdf
    ModelBenchmarkMetadata(
        model_id="models/gemini-2.5-flash",
        benchmark="mmlu",
        score=90.5,
        source_url="https://storage.googleapis.com/deepmind-media/gemini/gemini25_flash_technical_report.pdf",
        measured_date="2025-05-20",
        notes="5-shot MMLU Pro; canonical ID for all gemini-2.5-flash-* variants",
    ),
    ModelBenchmarkMetadata(
        model_id="models/gemini-2.5-flash",
        benchmark="humaneval",
        score=89.6,
        source_url="https://storage.googleapis.com/deepmind-media/gemini/gemini25_flash_technical_report.pdf",
        measured_date="2025-05-20",
        notes="0-shot HumanEval; canonical ID for all gemini-2.5-flash-* variants",
    ),
    # ── Gemini 2.5 Flash Lite ────────────────────────────────────────────────
    # Source: Google DeepMind blog (June 2025)
    # https://deepmind.google/models/gemini/flash-lite/
    ModelBenchmarkMetadata(
        model_id="models/gemini-2.5-flash-lite",
        benchmark="mmlu",
        score=84.0,
        source_url="https://deepmind.google/models/gemini/flash-lite/",
        measured_date="2025-06-17",
        notes="MMLU Pro; canonical ID for gemini-2.5-flash-lite-* and gemini-flash-lite-* variants",
    ),
    ModelBenchmarkMetadata(
        model_id="models/gemini-2.5-flash-lite",
        benchmark="humaneval",
        score=77.1,
        source_url="https://deepmind.google/models/gemini/flash-lite/",
        measured_date="2025-06-17",
        notes="HumanEval 0-shot; canonical ID for lite variants",
    ),
    # ── Gemini 2.0 Flash ─────────────────────────────────────────────────────
    # Source: Google Gemini 2.0 overview / lmmarketcap.com benchmarks
    ModelBenchmarkMetadata(
        model_id="models/gemini-2.0-flash",
        benchmark="mmlu",
        score=82.7,
        source_url=_LMMARKETCAP_URL,
        measured_date="2025-02-01",
        notes="5-shot MMLU; canonical ID for gemini-2.0-flash-* variants",
    ),
    ModelBenchmarkMetadata(
        model_id="models/gemini-2.0-flash",
        benchmark="humaneval",
        score=77.1,
        source_url=_LMMARKETCAP_URL,
        measured_date="2025-02-01",
        notes="0-shot HumanEval; canonical ID for gemini-2.0-flash-* variants",
    ),
    # ── Llama 3.1 8B Instant (Groq API ID) ───────────────────────────────────
    # Same base model as llama3.1:8b — Groq's serving ID for the Meta release.
    # Source: Meta LLaMA 3.1 paper (https://ai.meta.com/blog/meta-llama-3-1/)
    ModelBenchmarkMetadata(
        model_id="llama-3.1-8b-instant",
        benchmark="humaneval",
        score=72.6,
        source_url=_LLAMA31_URL,
        measured_date="2024-07-23",
        notes="0-shot HumanEval; Groq API ID for Meta LLaMA 3.1 8B Instruct",
    ),
    ModelBenchmarkMetadata(
        model_id="llama-3.1-8b-instant",
        benchmark="mmlu",
        score=73.0,
        source_url=_LLAMA31_URL,
        measured_date="2024-07-23",
        notes="5-shot MMLU; Groq API ID for Meta LLaMA 3.1 8B Instruct",
    ),
    # ── Mistral Saba 24B (Groq API ID) ───────────────────────────────────────
    # Source: Mistral blog https://mistral.ai/news/mistral-saba/
    ModelBenchmarkMetadata(
        model_id="mistral-saba-24b",
        benchmark="mmlu",
        score=74.6,
        source_url="https://mistral.ai/news/mistral-saba/",
        measured_date="2025-02-17",
        notes="5-shot MMLU from Mistral blog; Groq API serving ID",
    ),
    # ── Llama 4 Scout 17B (Groq API ID) ──────────────────────────────────────
    # Source: Meta Llama 4 blog https://ai.meta.com/blog/llama-4-multimodal-intelligence/
    # 17B active parameters (109B total, 16-expert MoE); released April 2025.
    ModelBenchmarkMetadata(
        model_id="meta-llama/llama-4-scout-17b-16e-instruct",
        benchmark="mmlu",
        score=80.0,
        source_url=_LLAMA4_URL,
        measured_date="2025-04-05",
        notes="MMLU from Meta Llama 4 release; Groq API serving ID",
    ),
    ModelBenchmarkMetadata(
        model_id="meta-llama/llama-4-scout-17b-16e-instruct",
        benchmark="humaneval",
        score=79.6,
        source_url=_LLAMA4_URL,
        measured_date="2025-04-05",
        notes="HumanEval pass@1 from Meta Llama 4 release; Groq API serving ID",
    ),
    # ── Qwen3-32B (Groq API ID) ───────────────────────────────────────────────
    # Source: Qwen3 technical report https://arxiv.org/pdf/2505.09388
    # 32B dense model with optional thinking (chain-of-thought) mode.
    # HumanEval score is for non-thinking mode; thinking mode scores higher.
    ModelBenchmarkMetadata(
        model_id="qwen/qwen3-32b",
        benchmark="humaneval",
        score=51.4,
        source_url=_QWEN3_URL,
        measured_date="2025-05-01",
        notes="HumanEval pass@1 non-thinking mode from Qwen3 technical report; Groq API serving ID",
    ),
    ModelBenchmarkMetadata(
        model_id="qwen/qwen3-32b",
        benchmark="math",
        score=85.7,
        source_url=_QWEN3_URL,
        measured_date="2025-05-01",
        notes="AIME 2025 score (strong math/reasoning); Groq API serving ID",
    ),
    # ── Kimi K2 Instruct (Groq API ID) ───────────────────────────────────────
    # Source: MoonshotAI Kimi K2 GitHub https://github.com/MoonshotAI/Kimi-K2
    # ~1T total params MoE, 32B active; strong agentic/coding model released 2025.
    ModelBenchmarkMetadata(
        model_id="moonshotai/kimi-k2-instruct",
        benchmark="mmlu",
        score=78.6,
        source_url=_KIMI_K2_URL,
        measured_date="2025-07-11",
        notes="MMLU from Kimi K2 GitHub release; Groq API serving ID",
    ),
    ModelBenchmarkMetadata(
        model_id="moonshotai/kimi-k2-instruct",
        benchmark="humaneval",
        score=73.2,
        source_url=_KIMI_K2_URL,
        measured_date="2025-07-11",
        notes="HumanEval pass@1 from Kimi K2 GitHub release; Groq API serving ID",
    ),
]

# ── Model ID alias table ──────────────────────────────────────────────────────
# Maps provider-specific or versioned model IDs → canonical benchmark IDs.
# ``get_best_score`` and ``get_benchmarks`` resolve these transparently so
# callers never need to know which versioned string a provider returned.
#
# Convention:
#   - Gemini versioned previews → base ``models/gemini-X.Y-*`` canonical form
#   - Groq provider-prefixed IDs → bare IDs (already have direct entries)
#   - Alias lookup is one level only (no chained aliases)

MODEL_ID_ALIASES: dict[str, str] = {
    # ── Gemini 2.5 Flash variants → canonical ────────────────────────────────
    "models/gemini-2.5-flash-preview-04-17": "models/gemini-2.5-flash",
    "models/gemini-2.5-flash-preview-05-20": "models/gemini-2.5-flash",
    "models/gemini-2.5-flash-exp-native-audio-thinking-dialog": "models/gemini-2.5-flash",
    "gemini-2.5-flash": "models/gemini-2.5-flash",
    # ── Gemini 2.5 Flash Lite variants → canonical ───────────────────────────
    "models/gemini-2.5-flash-lite-preview-06-17": "models/gemini-2.5-flash-lite",
    "models/gemini-flash-lite-latest": "models/gemini-2.5-flash-lite",
    "models/gemini-2.5-flash-lite": "models/gemini-2.5-flash-lite",
    "gemini-2.5-flash-lite": "models/gemini-2.5-flash-lite",
    # ── Gemini 2.0 Flash variants → canonical ───────────────────────────────
    "models/gemini-2.0-flash-001": "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-exp": "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-latest": "models/gemini-2.0-flash",
    "gemini-2.0-flash": "models/gemini-2.0-flash",
    # ── Gemini 2.5 Pro variants → canonical ──────────────────────────────────
    "models/gemini-2.5-pro-preview-03-25": "models/gemini-2.5-pro",
    "models/gemini-2.5-pro-preview-05-06": "models/gemini-2.5-pro",
    "models/gemini-2.5-pro-preview-06-05": "models/gemini-2.5-pro",
    "gemini-2.5-pro": "models/gemini-2.5-pro",
    # ── Gemini 1.5 variants → canonical ─────────────────────────────────────
    "models/gemini-1.5-flash": "gemini/gemini-1.5-flash",
    "models/gemini-1.5-flash-latest": "gemini/gemini-1.5-flash",
    "gemini-1.5-flash": "gemini/gemini-1.5-flash",
    # ── Groq prefixed → bare IDs (bare IDs have direct entries) ─────────────
    "groq/llama-3.3-70b-versatile": "llama-3.3-70b-versatile",
    "groq/llama-3.1-8b-instant": "llama-3.1-8b-instant",
    "groq/gemma2-9b-it": "gemma2-9b-it",
    "groq/mixtral-8x7b-32768": "mixtral-8x7b-32768",
    # ── Groq-served Llama 4 / Qwen3 / Kimi variants → canonical ─────────────
    "llama-4-scout-17b-16e-instruct": "meta-llama/llama-4-scout-17b-16e-instruct",
    "qwen3-32b": "qwen/qwen3-32b",
    "kimi-k2-instruct": "moonshotai/kimi-k2-instruct",
    # ── Ollama tag variants → canonical ──────────────────────────────────────
    "llama3.3:latest": "llama3.3:70b",
    "llama3.1:latest": "llama3.1:70b",
}


# ── Lookup helpers ────────────────────────────────────────────────────────────


def resolve_model_id(model_id: str) -> str:
    """Resolve a provider-specific or versioned model ID to its canonical form.

    Looks up *model_id* in :data:`MODEL_ID_ALIASES`.  Returns the canonical
    ID when found, otherwise returns *model_id* unchanged.  Alias resolution
    is single-level — the returned canonical ID is **not** re-resolved.

    Args:
        model_id: Any model identifier (bare, prefixed, or versioned).

    Returns:
        Canonical benchmark ID for the model, or *model_id* if no alias exists.

    Example::

        resolve_model_id("models/gemini-2.5-flash-preview-05-20")
        # → "models/gemini-2.5-flash"

        resolve_model_id("llama-3.3-70b-versatile")
        # → "llama-3.3-70b-versatile"  (already canonical)
    """
    return MODEL_ID_ALIASES.get(model_id, model_id)


def get_benchmarks(model_id: str) -> list[ModelBenchmarkMetadata]:
    """Return all benchmark entries for a given model ID.

    Transparently resolves *model_id* via :func:`resolve_model_id` so that
    versioned or provider-prefixed IDs (e.g. ``"models/gemini-2.5-flash-preview-05-20"``)
    automatically find data stored under their canonical form.

    Args:
        model_id: The model identifier to look up.

    Returns:
        A list of all :class:`ModelBenchmarkMetadata` records whose
        ``model_id`` matches the canonical form of *model_id*.  Returns an
        empty list when the model is unknown.

    Example::

        entries = get_benchmarks("qwen2.5:7b")
        for e in entries:
            print(e.benchmark, e.score)
    """
    canonical = resolve_model_id(model_id)
    return [entry for entry in BENCHMARK_DATA if entry.model_id == canonical]


def get_best_score(model_id: str, benchmark: str) -> float | None:
    """Return the highest published score for a model on a benchmark.

    When a model has multiple entries for the same benchmark (e.g. from
    different papers), the maximum is returned.  *model_id* is resolved
    via :func:`resolve_model_id` before lookup, so versioned or prefixed
    IDs (e.g. ``"models/gemini-2.5-flash-preview-05-20"``) work correctly.

    Args:
        model_id: Model identifier — bare, prefixed, or versioned.
        benchmark: Benchmark name, e.g. ``"mmlu"`` or ``"humaneval"``.

    Returns:
        The highest score (0.0–100.0) found, or ``None`` if no data exists
        for this model/benchmark combination.

    Example::

        score = get_best_score("gpt-4o", "humaneval")
        if score is not None and score >= 90.0:
            print("Strong coding model")
    """
    canonical = resolve_model_id(model_id)
    scores = [
        entry.score
        for entry in BENCHMARK_DATA
        if entry.model_id == canonical and entry.benchmark == benchmark
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


# ── Live benchmark cache integration ─────────────────────────────────────────
# Appends cached data written by BenchmarkFetcher.refresh() into BENCHMARK_DATA
# so that rank_models_for_task() sees live scores without any API changes.
# Runs at import time; safe when no cache exists.
def _load_live_benchmarks() -> None:
    import json as _json
    from pathlib import Path as _Path

    cache = _Path("~/.cache/ttadev/benchmark_data.json").expanduser()
    if not cache.exists():
        return
    try:
        raw = _json.loads(cache.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return

    existing_keys: set[tuple[str, str]] = {(e.model_id, e.benchmark) for e in BENCHMARK_DATA}
    added = 0
    for item in raw.get("benchmarks", []):
        try:
            entry = ModelBenchmarkMetadata(**item)
        except (TypeError, ValueError):
            continue
        key = (entry.model_id, entry.benchmark)
        if key not in existing_keys:
            BENCHMARK_DATA.append(entry)
            existing_keys.add(key)
            added += 1


_load_live_benchmarks()
