"""tta workflow subcommand — list, show, and run guided workflows."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from ttadev.control_plane import ControlPlaneService

# Registry of built-in workflow definitions
_WORKFLOWS: dict[str, object] = {}


def _get_workflows() -> dict[str, object]:
    if not _WORKFLOWS:
        from ttadev.workflows.prebuilt import feature_dev_workflow

        _WORKFLOWS["feature_dev"] = feature_dev_workflow
    return _WORKFLOWS


def register_workflow_subcommands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    wf_p = sub.add_parser("workflow", help="Run and inspect guided workflows")
    wf_sub = wf_p.add_subparsers(dest="workflow_command")

    # list
    wf_sub.add_parser("list", help="List available workflows")

    # show
    show_p = wf_sub.add_parser("show", help="Show workflow steps")
    show_p.add_argument("name", help="Workflow name")

    # run
    run_p = wf_sub.add_parser("run", help="Run a workflow")
    run_p.add_argument("name", help="Workflow name")
    run_p.add_argument("--goal", required=True, metavar="TEXT", help="Workflow goal")
    run_p.add_argument(
        "--no-confirm",
        dest="no_confirm",
        action="store_true",
        help="Skip approval gates (auto-approve all steps)",
    )
    run_p.add_argument(
        "--dry-run", dest="dry_run", action="store_true", help="Print step plan without executing"
    )
    run_p.add_argument(
        "--track-l0",
        dest="track_l0",
        action="store_true",
        help="Create inspectable L0 task/run tracking for this workflow execution",
    )


def handle_workflow_command(args: argparse.Namespace, data_dir: Path) -> int:
    workflows = _get_workflows()

    if args.workflow_command == "list":
        _cmd_list(workflows)
        return 0

    if args.workflow_command == "show":
        return _cmd_show(workflows, args.name)

    if args.workflow_command == "run":
        return _cmd_run(workflows, args, data_dir)

    # No subcommand — show help
    print("Usage: tta workflow {list,show,run}", file=sys.stderr)
    return 1


def _cmd_list(workflows: dict[str, object]) -> None:
    from ttadev.workflows.definition import WorkflowDefinition

    print("Available workflows:")
    for name, defn in workflows.items():
        if isinstance(defn, WorkflowDefinition):
            print(f"  {name:<20} {defn.description}")


def _cmd_show(workflows: dict[str, object], name: str) -> int:
    from ttadev.workflows.definition import WorkflowDefinition

    defn = workflows.get(name)
    if defn is None:
        print(f"error: unknown workflow '{name}'", file=sys.stderr)
        return 1
    if not isinstance(defn, WorkflowDefinition):
        return 1

    print(f"Workflow: {defn.name}")
    print(f"  {defn.description}")
    print(f"\nSteps ({len(defn.steps)}):")
    for i, step in enumerate(defn.steps, 1):
        gate = "[gate]" if step.gate else "[no gate]"
        print(f"  {i}. {step.agent:<20} {gate}")
    return 0


def _cmd_run(workflows: dict[str, object], args: argparse.Namespace, data_dir: Path) -> int:
    from ttadev.workflows.definition import WorkflowDefinition

    defn = workflows.get(args.name)
    if defn is None:
        print(f"error: unknown workflow '{args.name}'", file=sys.stderr)
        return 1
    if not isinstance(defn, WorkflowDefinition):
        return 1

    if args.dry_run:
        _print_dry_run(defn, args.goal)
        return 0

    from ttadev.primitives.core.base import WorkflowContext
    from ttadev.workflows.llm_provider import build_chat_primitive, get_llm_provider_chain
    from ttadev.workflows.orchestrator import WorkflowGoal, WorkflowOrchestrator

    # Apply --no-confirm override
    if args.no_confirm and not defn.auto_approve:
        import dataclasses

        defn = dataclasses.replace(defn, auto_approve=True)

    provider_chain = get_llm_provider_chain()
    model_factory = lambda: build_chat_primitive(provider_chain[0])  # noqa: E731

    control_plane_service = ControlPlaneService(data_dir) if args.track_l0 else None
    orch = WorkflowOrchestrator(
        defn,
        control_plane_service=control_plane_service,
        track_in_control_plane=args.track_l0,
        model_factory=model_factory,
    )
    ctx = WorkflowContext()
    goal = WorkflowGoal(goal=args.goal)

    result = asyncio.run(orch.execute(goal, ctx))

    if args.track_l0 and result.tracked_task_id and result.tracked_run_id:
        print(f"L0 task: {result.tracked_task_id}")
        print(f"L0 run:  {result.tracked_run_id}")
        print(f"Inspect with: tta control task show {result.tracked_task_id}")

    status = "completed" if result.completed else "stopped early"
    print(f"\nWorkflow {status}: {len(result.steps)} step(s) run")
    print(f"Total confidence: {result.total_confidence:.0%}")
    return 0


def _print_dry_run(defn: object, goal: str) -> None:
    from ttadev.workflows.definition import WorkflowDefinition

    if not isinstance(defn, WorkflowDefinition):
        return
    print(f"Dry run: {defn.name}")
    print(f"Goal: {goal}")
    print(f"\nStep plan ({len(defn.steps)} steps):")
    for i, step in enumerate(defn.steps, 1):
        gate = " [gate]" if step.gate else ""
        print(f"  {i}. {step.agent}{gate}")
    print("\n(no agents were executed)")
