"""tta workflow subcommand — list, show, and run guided workflows.

File-based workflows:
    tta workflow run <file.py> [--input JSON] [--timeout SECONDS] [--dry-run]

The Python file must expose a ``build()`` async coroutine that returns a
``WorkflowPrimitive`` instance::

    # workflows/hello.py
    from ttadev.primitives import LambdaPrimitive

    async def build():
        async def greet(data, ctx):
            return f"Hello, {data}!"
        return LambdaPrimitive(greet)
"""

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
        from ttadev.workflows.prebuilt import ALL_WORKFLOWS

        for wf in ALL_WORKFLOWS:
            _WORKFLOWS[wf.name] = wf
    return _WORKFLOWS


def _looks_like_file(name: str) -> bool:
    """Return True when *name* is clearly a file path rather than a registry name.

    A value is treated as a file path if it ends with ``.py`` or if the path
    already exists on disk (e.g. ``workflows/hello`` without the extension).

    Args:
        name: The positional ``name`` argument supplied to ``tta workflow run``.

    Returns:
        ``True`` when the value should be interpreted as a file path.
    """
    return name.endswith(".py") or Path(name).exists()


def register_workflow_subcommands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    wf_p = sub.add_parser("workflow", help="Run and inspect guided workflows")
    wf_sub = wf_p.add_subparsers(dest="workflow_command")

    # list
    wf_sub.add_parser("list", help="List available workflows")

    # show
    show_p = wf_sub.add_parser("show", help="Show workflow steps")
    show_p.add_argument("name", help="Workflow name")

    # run — handles both registry-named workflows and file-based workflows
    run_p = wf_sub.add_parser(
        "run",
        help=(
            "Run a workflow. Pass a registry name (--goal required) "
            "or a .py file path (--input / --timeout / --dry-run)."
        ),
    )
    run_p.add_argument(
        "name",
        help=(
            "Workflow registry name (e.g. feature_dev) or path to a .py file that defines build()."
        ),
    )
    # ── Named-workflow options ──────────────────────────────────────────────
    run_p.add_argument(
        "--goal",
        default=None,
        metavar="TEXT",
        help="Workflow goal (required for registry-named workflows)",
    )
    run_p.add_argument(
        "--no-confirm",
        dest="no_confirm",
        action="store_true",
        help="Skip approval gates (auto-approve all steps)",
    )
    run_p.add_argument(
        "--track-l0",
        dest="track_l0",
        action="store_true",
        help="Create inspectable L0 task/run tracking for this workflow execution",
    )
    # ── Shared / file-workflow options ─────────────────────────────────────
    run_p.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Print step plan (named) or primitive repr (file) without executing",
    )
    run_p.add_argument(
        "--input",
        dest="input",
        default=None,
        metavar="JSON",
        help="JSON-encoded input data passed to the workflow primitive (file workflows only)",
    )
    run_p.add_argument(
        "--timeout",
        dest="timeout",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Wrap the primitive in TimeoutPrimitive with this limit (file workflows only)",
    )


def handle_workflow_command(args: argparse.Namespace, data_dir: Path) -> int:
    workflows = _get_workflows()

    if args.workflow_command == "list":
        _cmd_list(workflows)
        return 0

    if args.workflow_command == "show":
        return _cmd_show(workflows, args.name)

    if args.workflow_command == "run":
        # Route: file-based workflow if the argument looks like a .py path.
        if _looks_like_file(args.name):
            return _cmd_run_file(args)
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

    # --goal is required for named workflows but was made optional in argparse
    # so that file-based workflows can share the same subparser.
    if not args.goal:
        print(
            "error: 'tta workflow run' requires --goal TEXT for named workflows",
            file=sys.stderr,
        )
        return 1

    defn = workflows.get(args.name)
    if defn is None:
        print(f"error: unknown workflow '{args.name}'", file=sys.stderr)
        return 1
    if not isinstance(defn, WorkflowDefinition):
        return 1

    if args.dry_run:
        _print_dry_run(defn, args.goal)
        return 0

    import os

    from ttadev.observability.session_manager import SessionManager
    from ttadev.primitives.core.base import WorkflowContext
    from ttadev.workflows.llm_provider import (
        NoLLMProviderError,
        _is_provider_error,
        build_chat_primitive,
        get_llm_provider_chain,
    )
    from ttadev.workflows.orchestrator import WorkflowGoal, WorkflowOrchestrator

    # ── Session attribution (Issue #301) ────────────────────────────────────
    # Record the workflow name as the agent tool so that `tta session list`
    # shows meaningful attribution instead of "unknown".
    agent_tool_label = f"workflow:{args.name}"
    os.environ["TTA_AGENT_TOOL"] = agent_tool_label

    session_mgr: SessionManager | None = None
    session = None
    if data_dir is not None:
        session_mgr = SessionManager(data_dir=data_dir)
        session = session_mgr.start_session()

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

    try:
        result = asyncio.run(orch.execute(goal, ctx))
    except NoLLMProviderError as exc:
        if session_mgr is not None and session is not None:
            session_mgr.end_session_by_id(session.id)
        print(exc.user_message(), file=sys.stderr)
        return 1
    except Exception as exc:
        if session_mgr is not None and session is not None:
            session_mgr.end_session_by_id(session.id)
        if _is_provider_error(exc):
            provider_name = provider_chain[0].provider if provider_chain else "unknown"
            err = NoLLMProviderError(reason=f"{provider_name}: {exc}")
            print(err.user_message(), file=sys.stderr)
            return 1
        raise

    if session_mgr is not None and session is not None:
        session_mgr.end_session_by_id(session.id)

    if args.track_l0 and result.tracked_task_id and result.tracked_run_id:
        print(f"L0 task: {result.tracked_task_id}")
        print(f"L0 run:  {result.tracked_run_id}")
        print(f"Inspect with: tta control task show {result.tracked_task_id}")

    status = "completed" if result.completed else "stopped early"
    print(f"\nWorkflow {status}: {len(result.steps)} step(s) run")
    print(f"Total confidence: {result.total_confidence:.0%}")
    return 0


_SEPARATOR = "─" * 41


def _cmd_run_file(args: argparse.Namespace) -> int:
    """Execute a file-based workflow: ``tta workflow run <file.py>``.

    Loads the Python file, calls its ``build()`` async coroutine to obtain a
    :class:`~ttadev.primitives.core.base.WorkflowPrimitive`, then executes it
    with the provided input data.

    Args:
        args: Parsed CLI arguments with at minimum ``.name`` (file path),
              and optionally ``.input`` (JSON string), ``.timeout`` (float),
              and ``.dry_run`` (bool).

    Returns:
        Exit code: ``0`` on success, ``1`` on any error.
    """
    import json
    import runpy
    import traceback

    from ttadev.primitives.core.base import WorkflowContext

    path = Path(args.name)

    # ── 1. File existence check ───────────────────────────────────────────
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    # ── 2. Load the Python file ───────────────────────────────────────────
    try:
        module_globals = runpy.run_path(str(path))
    except Exception as exc:  # noqa: BLE001
        print(f"error: failed to load '{path}': {exc}", file=sys.stderr)
        return 1

    # ── 3. Locate build() ─────────────────────────────────────────────────
    build_fn = module_globals.get("build")
    if build_fn is None:
        print(
            f"error: '{path}' has no build() function\n"
            "       A workflow file must define an async build() coroutine that\n"
            "       returns a WorkflowPrimitive.",
            file=sys.stderr,
        )
        return 1

    # ── 4. Call build() to obtain the primitive ───────────────────────────
    try:
        primitive = asyncio.run(build_fn())
    except Exception as exc:  # noqa: BLE001
        print(f"error: build() raised an exception: {exc}", file=sys.stderr)
        return 1

    # ── 5. Parse --input JSON ─────────────────────────────────────────────
    raw_input = getattr(args, "input", None) or "{}"
    try:
        input_data = json.loads(raw_input)
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON for --input: {exc}", file=sys.stderr)
        return 1

    # ── 6. Dry-run: print repr without executing ──────────────────────────
    if getattr(args, "dry_run", False):
        print(f"Workflow: {path}")
        print(f"Input: {json.dumps(input_data)}")
        print(_SEPARATOR)
        print(f"Primitive: {primitive!r}")
        print(_SEPARATOR)
        print("(dry-run: no execution)")
        return 0

    # ── 7. Optionally wrap in TimeoutPrimitive ────────────────────────────
    timeout: float | None = getattr(args, "timeout", None)
    if timeout is not None:
        from ttadev.primitives.recovery.timeout import TimeoutPrimitive

        primitive = TimeoutPrimitive(primitive=primitive, timeout_seconds=float(timeout))

    # ── 8. Build execution context ────────────────────────────────────────
    ctx = WorkflowContext(workflow_id=f"cli-workflow-{path.stem}")

    # ── 9. Print header ───────────────────────────────────────────────────
    print(f"Workflow: {path}")
    print(f"Input: {json.dumps(input_data)}")
    print(_SEPARATOR)

    # ── 10. Execute ───────────────────────────────────────────────────────
    try:
        result = asyncio.run(primitive.execute(input_data, ctx))
    except Exception:  # noqa: BLE001
        traceback.print_exc(file=sys.stderr)
        return 1

    # ── 11. Print result ──────────────────────────────────────────────────
    try:
        result_str = json.dumps(result)
    except (TypeError, ValueError):
        result_str = str(result)

    print(f"Result: {result_str}")
    print(_SEPARATOR)
    print("✅ Done")
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
