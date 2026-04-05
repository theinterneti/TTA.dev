"""CLI subcommand group: ``tta agents``.

Provides:
    tta agents list                           — list all registered agents
    tta agents run <name> "<task>"            — run an agent task
        --dry-run                             — print plan without calling any API
        --timeout SECONDS                     — wrap execution with TimeoutPrimitive
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ttadev.agents.task import AgentResult

# ─────────────────────────────────────────────────────────────────────────────
# Separator used in output formatting
# ─────────────────────────────────────────────────────────────────────────────
_SEP = "─" * 45


def register_agents_subcommands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Wire ``tta agents`` subcommands into the main argument parser.

    Args:
        sub: The parent subparsers action to attach ``agents`` into.
    """
    agents_p = sub.add_parser("agents", help="Manage and run TTA role-based agents")
    agents_sub = agents_p.add_subparsers(dest="agents_command")

    # ------------------------------------------------------------------ #
    # agents list                                                          #
    # ------------------------------------------------------------------ #
    agents_sub.add_parser("list", help="List all registered agents")

    # ------------------------------------------------------------------ #
    # agents run                                                           #
    # ------------------------------------------------------------------ #
    run_p = agents_sub.add_parser("run", help="Run an agent with a task instruction")
    run_p.add_argument("agent_name", metavar="AGENT", help="Agent name (e.g. developer, qa, git)")
    run_p.add_argument("task", metavar="TASK", help="Task instruction for the agent")
    run_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would run without calling any API",
    )
    run_p.add_argument(
        "--timeout",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Abort execution after SECONDS (uses TimeoutPrimitive)",
    )


def handle_agents_command(args: argparse.Namespace) -> int:
    """Dispatch to the appropriate ``agents`` subcommand handler.

    Args:
        args: Parsed argument namespace from the main CLI parser.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    cmd = getattr(args, "agents_command", None)
    if cmd == "list":
        return _cmd_list()
    if cmd == "run":
        return _cmd_run(args)
    print("Usage: tta agents {list,run} ...")
    return 1


# ─────────────────────────────────────────────────────────────────────────────
# agents list
# ─────────────────────────────────────────────────────────────────────────────


def _cmd_list() -> int:
    """Print a table of all registered agents.

    Returns:
        Exit code 0 (always succeeds).
    """
    # Trigger auto-registration by importing agent modules.
    import ttadev.agents  # noqa: F401 — side-effect import
    from ttadev.agents.registry import get_registry

    registry = get_registry()
    agent_classes = registry.all()

    if not agent_classes:
        print("No agents registered.")
        return 0

    rows: list[tuple[str, str, str]] = []
    for agent_class in agent_classes:
        spec = getattr(agent_class, "_class_spec", None)
        if spec is None:
            continue
        caps = ", ".join(spec.capabilities[:3])
        if len(spec.capabilities) > 3:
            caps += ", …"
        rows.append((spec.name, spec.role, caps))

    rows.sort(key=lambda r: r[0])

    print(f"{'NAME':<20} {'ROLE':<35} CAPABILITIES")
    print("─" * 90)
    for name, role, caps in rows:
        print(f"{name:<20} {role:<35} {caps}")

    print()
    print(f'  {len(rows)} agent(s) registered.  Run: tta agents run <name> "<task>"')
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# agents run
# ─────────────────────────────────────────────────────────────────────────────


def _cmd_run(args: argparse.Namespace) -> int:
    """Execute ``tta agents run`` — resolve agent, optionally wrap with timeout.

    Args:
        args: Parsed argument namespace with ``agent_name``, ``task``,
              ``dry_run``, and ``timeout`` attributes.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    # Trigger auto-registration.
    import ttadev.agents  # noqa: F401 — side-effect import
    from ttadev.agents.registry import get_registry

    agent_name: str = args.agent_name
    task_instruction: str = args.task
    dry_run: bool = getattr(args, "dry_run", False)
    timeout_secs: float | None = getattr(args, "timeout", None)

    registry = get_registry()

    # ── Resolve agent ────────────────────────────────────────────────────────
    try:
        agent_class = registry.get(agent_name)
    except KeyError:
        available = sorted(
            ac._class_spec.name
            for ac in registry.all()
            if getattr(ac, "_class_spec", None) is not None
        )
        print(f"❌ Unknown agent: {agent_name!r}", file=sys.stderr)
        print(f"   Available agents: {', '.join(available) or '(none)'}", file=sys.stderr)
        return 1

    spec = getattr(agent_class, "_class_spec", None)
    display_name = spec.name if spec is not None else agent_name

    # ── Dry-run mode ─────────────────────────────────────────────────────────
    if dry_run:
        print(f"Running agent: {display_name}")
        print(f"Task: {task_instruction}")
        print(_SEP)
        if spec is not None:
            preview = spec.system_prompt[:300].strip()
            if len(spec.system_prompt) > 300:
                preview += "…"
            print("[dry-run] System prompt preview:")
            print(textwrap.indent(preview, "  "))
        if timeout_secs is not None:
            print(f"[dry-run] Timeout: {timeout_secs}s (TimeoutPrimitive)")
        print(_SEP)
        print("[dry-run] No API call made.")
        return 0

    # ── API key guard (fail fast before entering asyncio.run) ────────────────
    import os

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "❌ Failed: ANTHROPIC_API_KEY not set. Add it to .env and retry.",
            file=sys.stderr,
        )
        return 1

    # ── Live execution ───────────────────────────────────────────────────────
    print(f"Running agent: {display_name}")
    print(f"Task: {task_instruction}")
    print(_SEP)

    result = asyncio.run(_run_agent(agent_class, task_instruction, timeout_secs))
    print(_SEP)

    if result is None:
        return 1

    print(
        f"✅ Done  (confidence: {result.confidence:.0%}, "
        f"quality gates: {'✓' if result.quality_gates_passed else '✗'})"
    )
    print()
    print(result.response)
    return 0


async def _run_agent(
    agent_class: type,
    task_instruction: str,
    timeout_secs: float | None,
) -> AgentResult | None:
    """Instantiate and execute the agent, optionally wrapped in a TimeoutPrimitive.

    Args:
        agent_class: The agent class resolved from the registry.
        task_instruction: Raw task string from the CLI.
        timeout_secs: If provided, wraps execution with ``TimeoutPrimitive``.

    Returns:
        The ``AgentResult`` on success, or ``None`` on failure.
    """
    from ttadev.agents.task import AgentTask
    from ttadev.primitives.core.base import WorkflowContext

    spec = getattr(agent_class, "_class_spec", None)
    agent_name: str = spec.name if spec is not None else "agent"
    ctx = WorkflowContext(workflow_id=f"cli-agents-run-{agent_name}")
    task = AgentTask(instruction=task_instruction, context={}, constraints=[])

    from ttadev.primitives.integrations.anthropic_primitive import AnthropicPrimitive

    model = AnthropicPrimitive()
    agent = agent_class(model=model)

    if timeout_secs is not None:
        from ttadev.primitives.recovery.timeout import TimeoutPrimitive

        workflow = TimeoutPrimitive(primitive=agent, timeout_seconds=timeout_secs)
        try:
            return await workflow.execute(task, ctx)
        except TimeoutError:
            print(f"❌ Failed: timed out after {timeout_secs}s", file=sys.stderr)
            return None
    else:
        try:
            return await agent.execute(task, ctx)
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Failed: {exc}", file=sys.stderr)
            return None
