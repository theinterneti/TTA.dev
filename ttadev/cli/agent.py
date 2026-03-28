"""CLI subcommands for the TTA agent system: list, show, run."""

from __future__ import annotations

import argparse
import json
import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ttadev.agents.task import AgentResult


def register_agent_subcommands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Wire ``tta agent`` subcommands into the main parser."""
    agent_p = sub.add_parser("agent", help="Work with TTA role-based agents")
    agent_sub = agent_p.add_subparsers(dest="agent_command")

    # ------------------------------------------------------------------ #
    # agent list                                                           #
    # ------------------------------------------------------------------ #
    list_p = agent_sub.add_parser("list", help="List all registered agents")
    list_p.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")

    # ------------------------------------------------------------------ #
    # agent show                                                           #
    # ------------------------------------------------------------------ #
    show_p = agent_sub.add_parser("show", help="Show an agent's full spec")
    show_p.add_argument("name", help="Agent name (e.g. developer)")
    show_p.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")

    # ------------------------------------------------------------------ #
    # agent run                                                            #
    # ------------------------------------------------------------------ #
    run_p = agent_sub.add_parser("run", help="Run an agent task")
    run_p.add_argument(
        "name",
        nargs="?",
        help="Agent name. Omit to use --route for automatic selection.",
    )
    run_p.add_argument("instruction", help="Task instruction for the agent")
    run_p.add_argument(
        "--route",
        action="store_true",
        help="Let the router pick the agent automatically",
    )
    run_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the prompt that would be sent without calling any API",
    )
    run_p.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")


def handle_agent_command(args: argparse.Namespace) -> int:
    """Dispatch to the appropriate agent subcommand handler."""
    cmd = getattr(args, "agent_command", None)
    if cmd == "list":
        return _cmd_list(args)
    if cmd == "show":
        return _cmd_show(args)
    if cmd == "run":
        return _cmd_run(args)
    # No subcommand — print help
    print("Usage: tta agent {list,show,run} ...")
    return 1


def _cmd_list(args: argparse.Namespace) -> int:
    from ttadev.agents.registry import get_registry

    registry = get_registry()
    agents = registry.all()

    if not agents:
        print("No agents registered.")
        return 0

    rows = []
    for agent_class in agents:
        spec = getattr(agent_class, "_class_spec", None)
        if spec is None:
            continue  # skip agents without introspectable spec
        rows.append(
            {
                "name": spec.name,
                "role": spec.role,
                "capabilities": spec.capabilities,
            }
        )

    if getattr(args, "as_json", False):
        print(json.dumps(rows, indent=2))
        return 0

    # Table output
    print(f"{'NAME':<20} {'ROLE':<35} CAPABILITIES")
    print("-" * 80)
    for row in rows:
        caps = ", ".join(row["capabilities"][:3])
        if len(row["capabilities"]) > 3:
            caps += f" (+{len(row['capabilities']) - 3} more)"
        print(f"{row['name']:<20} {row['role']:<35} {caps}")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    from ttadev.agents.registry import get_registry

    registry = get_registry()
    try:
        agent_class = registry.get(args.name)
    except KeyError as e:
        print(f"Error: {e}")
        return 1

    spec = getattr(agent_class, "_class_spec", None)
    if spec is None:
        print(f"Error: agent {args.name!r} does not expose a _class_spec for introspection.")
        return 1

    if getattr(args, "as_json", False):
        print(
            json.dumps(
                {
                    "name": spec.name,
                    "role": spec.role,
                    "system_prompt": spec.system_prompt,
                    "capabilities": spec.capabilities,
                    "tools": [
                        {"name": t.name, "description": t.description, "rule": t.rule.value}
                        for t in spec.tools
                    ],
                    "quality_gates": [g.name for g in spec.quality_gates],
                    "handoff_triggers": [
                        {"target": h.target_agent, "reason": h.reason}
                        for h in spec.handoff_triggers
                    ],
                },
                indent=2,
            )
        )
        return 0

    print(f"Agent: {spec.name}")
    print(f"Role:  {spec.role}")
    print()
    print("System Prompt:")
    print(
        textwrap.indent(
            spec.system_prompt[:500] + ("..." if len(spec.system_prompt) > 500 else ""), "  "
        )
    )
    print()
    print("Capabilities:")
    for cap in spec.capabilities:
        print(f"  - {cap}")
    print()
    print("Tools:")
    for tool in spec.tools:
        print(f"  [{tool.rule.value:>16}]  {tool.name} — {tool.description}")
    print()
    if spec.quality_gates:
        print("Quality Gates:")
        for gate in spec.quality_gates:
            print(f"  - {gate.name}: {gate.error_message}")
        print()
    if spec.handoff_triggers:
        print("Handoff Triggers:")
        for trigger in spec.handoff_triggers:
            print(f"  → {trigger.target_agent}: {trigger.reason}")
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    import asyncio

    from ttadev.agents.task import AgentTask  # noqa: PLC0415

    task = AgentTask(instruction=args.instruction, context={}, constraints=[])

    if getattr(args, "dry_run", False):
        from ttadev.agents.registry import get_registry

        agent_name = args.name or "(router will select)"
        print(f"[dry-run] Agent: {agent_name}")
        print(f"[dry-run] Instruction: {args.instruction}")
        if args.name:
            try:
                reg = get_registry()
                agent_class = reg.get(args.name)
                spec = getattr(agent_class, "_class_spec", None)
                if spec is not None:
                    print("\n[dry-run] System prompt preview:\n")
                    print(textwrap.indent(spec.system_prompt[:300] + "...", "  "))
            except KeyError:
                print(f"[dry-run] Warning: agent {args.name!r} not registered")
        return 0

    result = asyncio.run(_run_agent(args, task))
    if result is None:
        return 1

    if getattr(args, "as_json", False):
        import dataclasses

        print(json.dumps(dataclasses.asdict(result), indent=2))
        return 0

    print(f"Agent: {result.agent_name}")
    print(f"Quality gates: {'✓' if result.quality_gates_passed else '✗'}")
    print(f"Confidence: {result.confidence:.0%}")
    if result.spawned_agents:
        print(f"Sub-agents: {', '.join(result.spawned_agents)}")
    print()
    print(result.response)
    return 0


async def _run_agent(args: argparse.Namespace, task: object) -> AgentResult | None:
    from ttadev.agents.registry import get_registry
    from ttadev.primitives.core.base import WorkflowContext

    ctx = WorkflowContext()

    if getattr(args, "route", False) or not args.name:
        # Router mode — needs an orchestrator model
        print("Error: --route requires a model. Set ANTHROPIC_API_KEY and retry.")
        return None

    registry = get_registry()
    try:
        agent_class = registry.get(args.name)
    except KeyError as e:
        print(f"Error: {e}")
        return None

    # Model selection: use Anthropic if key is set, else error
    import os

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set. Add it to .env and retry.")
        return None

    from ttadev.primitives.integrations.anthropic_primitive import AnthropicPrimitive

    model = AnthropicPrimitive()
    agent = agent_class(model=model)
    return await agent.execute(task, ctx)
