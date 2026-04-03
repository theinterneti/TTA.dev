"""CLI subcommands for the ModelAdvisor: advise, roi, suggest-qwen."""

from __future__ import annotations

import argparse
import sys

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_kv(values: list[str]) -> dict[str, float]:
    """Parse a list of ``KEY=VALUE`` strings into a ``dict[str, float]``.

    Args:
        values: List of strings in the form ``"task=score"``, e.g.
            ``["coding=55", "math=72"]``.

    Returns:
        Dictionary mapping each key to its float value.

    Raises:
        SystemExit: If any entry cannot be split on ``=`` or converted to
            ``float``.
    """
    result: dict[str, float] = {}
    for item in values:
        if "=" not in item:
            print(f"error: expected KEY=VALUE, got {item!r}", file=sys.stderr)
            sys.exit(1)
        key, _, raw = item.partition("=")
        try:
            result[key.strip()] = float(raw.strip())
        except ValueError:
            print(
                f"error: value for {key!r} must be a number, got {raw!r}",
                file=sys.stderr,
            )
            sys.exit(1)
    return result


_DIVIDER = "═" * 54


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register_model_subcommands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Wire ``tta models`` subcommands into the main parser.

    Args:
        sub: The top-level subparsers action from the main ``argparse``
            parser into which ``models`` is added.
    """
    models_p = sub.add_parser("models", help="ModelAdvisor: tier advice, ROI, fine-tune hints")
    models_sub = models_p.add_subparsers(dest="models_command")

    # ------------------------------------------------------------------ #
    # models advise                                                        #
    # ------------------------------------------------------------------ #
    advise_p = models_sub.add_parser(
        "advise",
        help="Recommend the optimal model tier for a task",
    )
    advise_p.add_argument(
        "--task-type",
        default="coding",
        metavar="TASK",
        help=(
            "Task type: coding/reasoning/math/chat/function_calling/vision/general"
            " (default: coding)"
        ),
    )
    advise_p.add_argument(
        "--threshold",
        type=float,
        default=7.0,
        metavar="N",
        help="Quality threshold 0–10 (default: 7.0)",
    )
    advise_p.add_argument(
        "--complexity",
        default="moderate",
        metavar="LEVEL",
        help="Complexity: simple/moderate/complex (default: moderate)",
    )
    advise_p.add_argument(
        "--monthly-calls",
        type=int,
        default=100,
        metavar="N",
        help="Expected monthly call volume (default: 100)",
    )

    # ------------------------------------------------------------------ #
    # models roi                                                           #
    # ------------------------------------------------------------------ #
    roi_p = models_sub.add_parser(
        "roi",
        help="Estimate ROI of fine-tuning a Qwen model",
    )
    roi_p.add_argument(
        "--task-type",
        default="coding",
        metavar="TASK",
        help="Task type (default: coding)",
    )
    roi_p.add_argument(
        "--score",
        type=float,
        default=60.0,
        metavar="N",
        help="Current eval score 0–100 (default: 60.0)",
    )
    roi_p.add_argument(
        "--model",
        default="groq/llama-3.3-70b-versatile",
        metavar="MODEL",
        help="Current best model (default: groq/llama-3.3-70b-versatile)",
    )
    roi_p.add_argument(
        "--monthly-calls",
        type=int,
        default=100,
        metavar="N",
        help="Expected monthly call volume (default: 100)",
    )
    roi_p.add_argument(
        "--qwen-size",
        default="qwen2.5-7b",
        metavar="SIZE",
        help="Qwen model to fine-tune: qwen2.5-7b/14b/32b/72b (default: qwen2.5-7b)",
    )

    # ------------------------------------------------------------------ #
    # models suggest-qwen                                                  #
    # ------------------------------------------------------------------ #
    suggest_p = models_sub.add_parser(
        "suggest-qwen",
        help="Rank tasks by fine-tuning ROI (best first)",
    )
    suggest_p.add_argument(
        "--scores",
        nargs="*",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Space-separated task=score pairs, e.g. coding=55 math=72. "
            "Uses demo scores when omitted."
        ),
    )
    suggest_p.add_argument(
        "--monthly-calls",
        nargs="*",
        default=[],
        metavar="KEY=VALUE",
        help="Space-separated task=calls pairs, e.g. coding=200 math=50",
    )


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def handle_model_command(args: argparse.Namespace) -> int:
    """Dispatch ``tta models`` to the appropriate subcommand handler.

    Args:
        args: Parsed argument namespace from argparse.

    Returns:
        Exit code: ``0`` on success, ``1`` on error.
    """
    cmd = getattr(args, "models_command", None)
    if cmd == "advise":
        return _cmd_advise(args)
    if cmd == "roi":
        return _cmd_roi(args)
    if cmd == "suggest-qwen":
        return _cmd_suggest_qwen(args)

    # No subcommand given — show help.
    print("usage: tta models {advise,roi,suggest-qwen} [options]", file=sys.stderr)
    print("Try 'tta models --help' for more information.", file=sys.stderr)
    return 1


# ---------------------------------------------------------------------------
# advise
# ---------------------------------------------------------------------------


def _cmd_advise(args: argparse.Namespace) -> int:
    """Handle ``tta models advise``.

    Args:
        args: Parsed argument namespace containing ``task_type``,
            ``threshold``, ``complexity``, and ``monthly_calls``.

    Returns:
        Exit code: ``0`` on success, ``1`` on error.
    """
    from ttadev.primitives.llm.model_advisor.advisor import advisor

    task_type: str = args.task_type
    threshold: float = args.threshold
    complexity: str = args.complexity
    monthly_calls: int = args.monthly_calls

    try:
        rec = advisor.recommend_tier(
            task_type=task_type,
            quality_threshold=threshold,
            complexity=complexity,
            monthly_calls=monthly_calls,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    fallback_str = ", ".join(rec.fallback_models) if rec.fallback_models else "none"

    print(f"Recommendation for {task_type} (threshold: {threshold}/10, {complexity} complexity)")
    print(_DIVIDER)
    print(f"Tier:         {rec.recommended_tier}")
    print(f"Model:        {rec.primary_model}")
    print(f"Score:        {rec.quality_score:.1f}/10")
    print(f"Monthly cost: ${rec.cost_usd_per_month:.2f}")
    print()
    print(f"Rationale: {rec.rationale}")
    print()
    print(f"Fallbacks: {fallback_str}")
    return 0


# ---------------------------------------------------------------------------
# roi
# ---------------------------------------------------------------------------


def _cmd_roi(args: argparse.Namespace) -> int:
    """Handle ``tta models roi``.

    Args:
        args: Parsed argument namespace containing ``task_type``, ``score``,
            ``model``, ``monthly_calls``, and ``qwen_size``.

    Returns:
        Exit code: ``0`` on success, ``1`` on error.
    """
    from ttadev.primitives.llm.model_advisor.advisor import advisor

    task_type: str = args.task_type
    current_score: float = args.score
    current_model: str = args.model
    monthly_calls: int = args.monthly_calls
    qwen_size: str = args.qwen_size

    try:
        roi = advisor.estimate_roi(
            task_type=task_type,
            current_score=current_score,
            current_best_model=current_model,
            monthly_calls=monthly_calls,
            base_model=qwen_size,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    improvement = roi.finetuned_score_estimate - roi.current_score
    verdict = "✓ RECOMMENDED" if roi.is_recommended else "✗ NOT RECOMMENDED"

    print(f"ROI Analysis: {task_type} fine-tune on {qwen_size}")
    print(_DIVIDER)
    print(f"Current score:       {roi.current_score:.1f}/100 ({roi.current_best_model})")
    print(
        f"After fine-tuning:   {roi.finetuned_score_estimate:.1f}/100"
        f" (+{improvement:.1f}pp estimated)"
    )
    print(f"Training cost:       ${roi.training_cost_usd:.2f}")
    print(f"Monthly savings:     ${roi.monthly_savings_usd:.2f}/month ({monthly_calls} calls)")
    print(f"Breakeven:           {roi.roi_breakeven_days:.1f} days  {verdict}")
    return 0


# ---------------------------------------------------------------------------
# suggest-qwen
# ---------------------------------------------------------------------------

_DEFAULT_DEMO_SCORES: dict[str, float] = {
    "coding": 55.0,
    "math": 72.0,
    "reasoning": 61.0,
    "chat": 80.0,
    "function_calling": 58.0,
}


def _cmd_suggest_qwen(args: argparse.Namespace) -> int:
    """Handle ``tta models suggest-qwen``.

    Args:
        args: Parsed argument namespace containing ``scores`` and
            ``monthly_calls`` (both as lists of ``KEY=VALUE`` strings).

    Returns:
        Exit code: ``0`` on success, ``1`` on error.
    """
    from ttadev.primitives.llm.model_advisor.strategy import suggest_qwen_finetunes

    raw_scores: list[str] = args.scores or []
    raw_calls: list[str] = getattr(args, "monthly_calls", []) or []

    scores: dict[str, float] = _parse_kv(raw_scores) if raw_scores else _DEFAULT_DEMO_SCORES
    calls_map_float: dict[str, float] = _parse_kv(raw_calls) if raw_calls else {}
    calls_map: dict[str, int] = {k: int(v) for k, v in calls_map_float.items()}

    try:
        suggestions = suggest_qwen_finetunes(
            eval_results=scores,
            monthly_calls_per_task=calls_map if calls_map else None,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not suggestions:
        print("No fine-tuning suggestions available for the given scores.")
        return 0

    print("Qwen Fine-tuning Suggestions (best ROI first)")
    print(_DIVIDER)
    for i, s in enumerate(suggestions, start=1):
        breakeven_str = (
            f"{s.roi_breakeven_days:.0f}d" if s.roi_breakeven_days != float("inf") else "∞"
        )
        print(
            f"{i}. {s.task_type:<20} score: {s.current_score:.1f}"
            f"  improvement: +{s.expected_improvement:.1f}pp"
            f"  cost: ${s.estimated_cost_usd:.2f}"
            f"  breakeven: {breakeven_str}"
            f"  confidence: {s.confidence:.2f}"
        )
        print(f"   Rationale: {s.rationale}")
    return 0
