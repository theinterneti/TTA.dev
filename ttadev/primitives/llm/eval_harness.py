"""EmpiricalEvalHarness — run structured comparison tasks across LLM model tiers.

Runs a task prompt against a set of models, records latency, token usage,
and output quality. Produces a ranked comparison report.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive
from ttadev.primitives.llm.universal_llm_primitive import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
    UniversalLLMPrimitive,
)

__all__ = [
    "EvalTask",
    "ModelEvalResult",
    "EvalRun",
    "EvalHarnessPrimitive",
    "TASK_TYPE_PROFILES",
    "COST_PER_1K_OUTPUT_TOKENS",
]

# ── Task-type profiles ────────────────────────────────────────────────────────

TASK_TYPE_PROFILES: dict[str, dict[str, Any]] = {
    "code": {"temperature": 0.0, "max_tokens": 1024},
    "narrative": {"temperature": 0.7, "max_tokens": 512},
    "classification": {"temperature": 0.0, "max_tokens": 64},
    "extraction": {"temperature": 0.0, "max_tokens": 256},
    "general": {"temperature": 0.3, "max_tokens": 512},
}

# ── Cost estimates (USD per 1 000 output tokens) ──────────────────────────────
# Conservative; 0.0 for free / local / uncertain providers.

COST_PER_1K_OUTPUT_TOKENS: dict[str, float] = {
    "openai": 0.0006,  # gpt-4o-mini ballpark
    "anthropic": 0.0024,  # claude-haiku ballpark
    "xai": 0.0,  # uncertain — conservative free
    "groq": 0.0,  # free tier
    "together": 0.0,  # free tier
    "openrouter": 0.0,  # many free models; default 0
    "ollama": 0.0,  # local
    "google": 0.0,  # gemini flash free tier
}


# ── Data models ───────────────────────────────────────────────────────────────


@dataclass
class EvalTask:
    """A single evaluation task to run across models.

    Attributes:
        task_id: Unique identifier for this task.
        prompt: The user prompt sent to every model.
        system_prompt: Optional system/instruction prompt.
        task_type: One of ``"code"``, ``"narrative"``, ``"classification"``,
            ``"extraction"``, or ``"general"``.  Controls default temperature
            and ``max_tokens`` via :data:`TASK_TYPE_PROFILES`.
        expected_keywords: Simple scoring — each keyword (case-insensitive)
            found in the model output contributes one point to the keyword
            score.
        max_tokens: Maximum output token budget.
        temperature: Sampling temperature.  Use ``0.0`` for reproducible evals.
    """

    task_id: str
    prompt: str
    system_prompt: str | None = None
    task_type: str = "general"
    expected_keywords: list[str] = field(default_factory=list)
    max_tokens: int = 512
    temperature: float = 0.0


@dataclass
class ModelEvalResult:
    """Result of running :class:`EvalTask` against a single model.

    Attributes:
        model_id: The model identifier string (e.g. ``"gpt-4o-mini"``).
        provider: Provider key (e.g. ``"openai"``).
        output: The model's raw text output.
        latency_ms: Wall-clock round-trip time in milliseconds.
        prompt_tokens: Tokens consumed by the prompt (0 when unknown).
        completion_tokens: Tokens in the model's response (0 when unknown).
        cost_estimate_usd: Estimated cost in USD; ``0.0`` for free/local models.
        keyword_score: Fraction of expected keywords found in the output
            (0.0–1.0).  Always ``0.0`` when the run failed.
        error: Error message string if the call failed; ``None`` on success.
        raw_response: Serialisable provider response snapshot for archival.
    """

    model_id: str
    provider: str
    output: str
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    cost_estimate_usd: float
    keyword_score: float
    error: str | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvalRun:
    """A complete evaluation run across multiple models.

    Attributes:
        run_id: Unique identifier for this run, auto-generated.
        task: The :class:`EvalTask` that was executed.
        results: One :class:`ModelEvalResult` per configured model.
        started_at: Unix timestamp when the run began.
        completed_at: Unix timestamp when the run finished; ``None`` while
            still in progress.
    """

    run_id: str
    task: EvalTask
    results: list[ModelEvalResult] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    completed_at: float | None = None

    def ranked_results(self) -> list[ModelEvalResult]:
        """Return results sorted by keyword_score descending, then latency ascending.

        Models that errored (``keyword_score=0.0``) naturally sort to the
        bottom.  Among equally-scored models, faster ones rank higher.

        Returns:
            A new :class:`list` of :class:`ModelEvalResult` in ranked order.
            The original :attr:`results` list is not mutated.
        """
        return sorted(
            self.results,
            key=lambda r: (-r.keyword_score, r.latency_ms),
        )

    def to_report(self) -> str:
        """Generate a human-readable markdown comparison report.

        Includes a header with run metadata, the task prompt (truncated to
        120 characters), and a ranked markdown table:

        ``| Rank | Model | Provider | Score | Latency (ms) | Tokens | Est. Cost |``

        Returns:
            Multi-line markdown string suitable for display in a terminal or
            GitHub comment.
        """
        truncated_prompt = (
            self.task.prompt[:120] + "..." if len(self.task.prompt) > 120 else self.task.prompt
        )

        lines: list[str] = [
            f"# EvalRun Report — `{self.run_id}`",
            "",
            f"**Task:** `{self.task.task_id}` ({self.task.task_type})",
            f"**Prompt:** {truncated_prompt}",
            "",
            "| Rank | Model | Provider | Score | Latency (ms) | Tokens | Est. Cost |",
            "|------|-------|----------|-------|--------------|--------|-----------|",
        ]

        for rank, result in enumerate(self.ranked_results(), start=1):
            total_tokens = result.prompt_tokens + result.completion_tokens
            score_str = f"{result.keyword_score:.0%}"
            latency_str = f"{result.latency_ms:.1f}"
            cost_str = (
                f"${result.cost_estimate_usd:.6f}" if result.cost_estimate_usd > 0 else "$0.00"
            )
            model_label = f"{result.model_id} ⚠" if result.error else result.model_id
            lines.append(
                f"| {rank} | {model_label} | {result.provider} "
                f"| {score_str} | {latency_str} | {total_tokens} | {cost_str} |"
            )

        if self.completed_at is not None:
            duration = self.completed_at - self.started_at
            lines += [
                "",
                f"*Run completed in {duration:.2f}s across {len(self.results)} models.*",
            ]

        return "\n".join(lines)


# ── Harness primitive ─────────────────────────────────────────────────────────


class EvalHarnessPrimitive(WorkflowPrimitive[EvalTask, EvalRun]):
    """Run a task across multiple LLM models and record structured results.

    Executes the same :class:`EvalTask` against every configured
    ``(provider, model_id)`` pair concurrently, bounded by *max_concurrent*.
    Each individual model call is wrapped in a timeout guard.  Failures are
    captured as :class:`ModelEvalResult` entries with ``error`` set rather
    than being propagated, so a single flaky model does not abort the run.

    Args:
        models: List of ``(provider_key, model_id)`` pairs to evaluate.
            ``provider_key`` must be a valid
            :class:`~ttadev.primitives.llm.universal_llm_primitive.LLMProvider`
            value (e.g. ``"groq"``, ``"openai"``).
        max_concurrent: Maximum simultaneous model calls.  Defaults to ``3``.
        timeout_seconds: Per-model timeout in seconds.  A model that exceeds
            this limit receives an error result.  Defaults to ``30.0``.

    Example:
        .. code-block:: python

            harness = EvalHarnessPrimitive(
                models=[
                    ("groq", "llama-3.1-8b-instant"),
                    ("openai", "gpt-4o-mini"),
                    ("ollama", "llama3.2:latest"),
                ],
                max_concurrent=2,
                timeout_seconds=20.0,
            )
            task = EvalTask(
                task_id="multilingual-hello",
                prompt="Say hello in English, Spanish, and French.",
                task_type="general",
                expected_keywords=["hello", "hola", "bonjour"],
            )
            ctx = WorkflowContext.root("eval-run")
            run = await harness.execute(task, ctx)
            print(run.to_report())
    """

    def __init__(
        self,
        models: list[tuple[str, str]],
        max_concurrent: int = 3,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._models = models
        self._max_concurrent = max_concurrent
        self._timeout_seconds = timeout_seconds

    async def execute(self, data: EvalTask, context: WorkflowContext) -> EvalRun:
        """Run *data* against all configured models concurrently.

        Args:
            data: The evaluation task to execute.
            context: Workflow execution context; a child context is created per
                model call so traces are properly attributed.

        Returns:
            A completed :class:`EvalRun` with one :class:`ModelEvalResult` per
            model.  Error results are included rather than omitted.
        """
        run = EvalRun(
            run_id=str(uuid.uuid4()),
            task=data,
            started_at=time.time(),
        )

        semaphore = asyncio.Semaphore(self._max_concurrent)

        async def _bounded_call(provider_key: str, model_id: str) -> ModelEvalResult:
            async with semaphore:
                return await self._call_model(
                    provider_key=provider_key,
                    model_id=model_id,
                    task=data,
                    context=context,
                )

        gathered = await asyncio.gather(
            *[_bounded_call(p, m) for p, m in self._models],
            return_exceptions=True,
        )

        for (provider_key, model_id), outcome in zip(self._models, gathered):
            if isinstance(outcome, BaseException):
                # gather only surfaces exceptions here when _bounded_call itself
                # raises (which it shouldn't — _call_model swallows all errors).
                # This is a safety net.
                run.results.append(
                    ModelEvalResult(
                        model_id=model_id,
                        provider=provider_key,
                        output="",
                        latency_ms=0.0,
                        prompt_tokens=0,
                        completion_tokens=0,
                        cost_estimate_usd=0.0,
                        keyword_score=0.0,
                        error=str(outcome),
                    )
                )
            else:
                run.results.append(outcome)  # type: ignore[arg-type]

        run.completed_at = time.time()
        return run

    async def _call_model(
        self,
        *,
        provider_key: str,
        model_id: str,
        task: EvalTask,
        context: WorkflowContext,
    ) -> ModelEvalResult:
        """Invoke a single model and return a :class:`ModelEvalResult`.

        This method never raises — all exceptions are captured and returned as
        error results so the outer gather always succeeds.

        Args:
            provider_key: Provider identifier string matching
                :class:`~ttadev.primitives.llm.universal_llm_primitive.LLMProvider`.
            model_id: Model identifier to pass to the provider.
            task: Evaluation task containing the prompt and keyword list.
            context: Parent workflow context used to create a child span.

        Returns:
            :class:`ModelEvalResult` — always returned, never raises.
        """
        # Validate provider early so we return a clean error before any I/O.
        try:
            provider_enum = LLMProvider(provider_key)
        except ValueError:
            return ModelEvalResult(
                model_id=model_id,
                provider=provider_key,
                output="",
                latency_ms=0.0,
                prompt_tokens=0,
                completion_tokens=0,
                cost_estimate_usd=0.0,
                keyword_score=0.0,
                error=f"Unknown provider: {provider_key!r}",
            )

        messages: list[dict[str, str]] = [{"role": "user", "content": task.prompt}]
        request = LLMRequest(
            model=model_id,
            messages=messages,
            temperature=task.temperature,
            max_tokens=task.max_tokens,
            system=task.system_prompt,
        )

        child_ctx = WorkflowContext.child(context, step_name=f"eval-{provider_key}-{model_id}")
        primitive = UniversalLLMPrimitive(provider=provider_enum)

        t0 = time.perf_counter()
        try:
            response: LLMResponse = await asyncio.wait_for(
                primitive.execute(request, child_ctx),
                timeout=self._timeout_seconds,
            )
        except TimeoutError:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return ModelEvalResult(
                model_id=model_id,
                provider=provider_key,
                output="",
                latency_ms=elapsed_ms,
                prompt_tokens=0,
                completion_tokens=0,
                cost_estimate_usd=0.0,
                keyword_score=0.0,
                error=f"Timeout after {self._timeout_seconds}s",
            )
        except Exception as exc:  # noqa: BLE001
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return ModelEvalResult(
                model_id=model_id,
                provider=provider_key,
                output="",
                latency_ms=elapsed_ms,
                prompt_tokens=0,
                completion_tokens=0,
                cost_estimate_usd=0.0,
                keyword_score=0.0,
                error=str(exc),
            )

        elapsed_ms = (time.perf_counter() - t0) * 1000
        usage = response.usage or {}
        prompt_tokens: int = usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0)
        completion_tokens: int = usage.get("completion_tokens", 0) or usage.get("output_tokens", 0)

        cost_rate = COST_PER_1K_OUTPUT_TOKENS.get(provider_key, 0.0)
        cost_estimate = (completion_tokens / 1000.0) * cost_rate
        keyword_score = _score_keywords(response.content, task.expected_keywords)

        return ModelEvalResult(
            model_id=model_id,
            provider=provider_key,
            output=response.content,
            latency_ms=elapsed_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_estimate_usd=cost_estimate,
            keyword_score=keyword_score,
            error=None,
            raw_response={"model": response.model, "provider": response.provider},
        )


# ── Helpers ───────────────────────────────────────────────────────────────────


def _score_keywords(output: str, keywords: list[str]) -> float:
    """Return the fraction of *keywords* present in *output* (case-insensitive).

    Args:
        output: Raw text returned by the model.
        keywords: Required keyword strings.

    Returns:
        Float in ``[0.0, 1.0]``.  Returns ``1.0`` when *keywords* is empty.

    Example:
        >>> _score_keywords("Hello hola world", ["hello", "hola", "bonjour"])
        0.6666666666666666
    """
    if not keywords:
        return 1.0
    lowered = output.lower()
    hits = sum(1 for kw in keywords if kw.lower() in lowered)
    return hits / len(keywords)
