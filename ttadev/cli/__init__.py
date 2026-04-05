"""TTA.dev CLI dispatcher."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tta",
        description="TTA.dev — workflow primitives for AI agents.",
    )
    parser.add_argument(
        "--data-dir",
        default=".tta",
        metavar="DIR",
        help="Directory for TTA state (default: .tta)",
    )

    sub = parser.add_subparsers(dest="command")

    # ------------------------------------------------------------------ #
    # session subcommand                                                   #
    # ------------------------------------------------------------------ #
    session_p = sub.add_parser("session", help="Inspect TTA sessions")
    session_sub = session_p.add_subparsers(dest="session_command")

    # session list
    list_p = session_sub.add_parser("list", help="List recent sessions")
    list_p.add_argument("--limit", type=int, default=10, metavar="N", help="Max sessions to show")
    list_p.add_argument(
        "--project", dest="project_name", metavar="NAME", help="Filter by project name"
    )

    # session show
    show_s = session_sub.add_parser("show", help="Show session details")
    show_s.add_argument("session_id", help="Full or partial session ID")

    # session current
    session_sub.add_parser("current", help="Show the active session")

    # session end
    session_sub.add_parser("end", help="End the active session")

    # session spans
    spans_p = session_sub.add_parser("spans", help="List spans in a session")
    spans_p.add_argument("session_id", help="Full or partial session ID")
    spans_p.add_argument("--limit", type=int, default=20, metavar="N", help="Max spans to show")
    spans_p.add_argument(
        "--primitive", dest="primitive_filter", metavar="NAME", help="Filter by primitive type"
    )

    # ------------------------------------------------------------------ #
    # run subcommand                                                       #
    # ------------------------------------------------------------------ #
    run_p = sub.add_parser("run", help="Run a primitive workflow around a shell command")
    run_sub = run_p.add_subparsers(dest="run_command")

    # run retry
    retry_p = run_sub.add_parser("retry", help="Retry a command on failure")
    retry_p.add_argument("--max-retries", type=int, default=3, metavar="N")
    retry_p.add_argument("cmd", nargs=argparse.REMAINDER, metavar="-- COMMAND")

    # run timeout
    timeout_p = run_sub.add_parser("timeout", help="Kill a command after N seconds")
    timeout_p.add_argument("--seconds", type=float, default=30.0, metavar="N")
    timeout_p.add_argument("cmd", nargs=argparse.REMAINDER, metavar="-- COMMAND")

    # run cache
    cache_p = run_sub.add_parser("cache", help="Cache the output of a command")
    cache_p.add_argument("--ttl", type=float, default=3600.0, metavar="N")
    cache_p.add_argument("--key", default=None, metavar="KEY")
    cache_p.add_argument("cmd", nargs=argparse.REMAINDER, metavar="-- COMMAND")

    # run echo
    echo_p = run_sub.add_parser("echo", help="Print arguments (useful for testing)")
    echo_p.add_argument("cmd", nargs=argparse.REMAINDER, metavar="ARGS")

    # ------------------------------------------------------------------ #
    # project subcommand                                                   #
    # ------------------------------------------------------------------ #
    project_p = sub.add_parser("project", help="Manage TTA projects")
    project_sub = project_p.add_subparsers(dest="project_command")

    # project join
    join_p = project_sub.add_parser("join", help="Join or create a project")
    join_p.add_argument("name", help="Project name")

    # project list
    project_sub.add_parser("list", help="List all projects")

    # project show
    show_p = project_sub.add_parser("show", help="Show project details")
    show_p.add_argument("name", help="Project name")

    # ------------------------------------------------------------------ #
    # agent subcommand                                                     #
    # ------------------------------------------------------------------ #
    from ttadev.cli.agent import register_agent_subcommands

    register_agent_subcommands(sub)

    # ------------------------------------------------------------------ #
    # agents subcommand (plural — tta agents run / tta agents list)        #
    # ------------------------------------------------------------------ #
    from ttadev.cli.agents import register_agents_subcommands

    register_agents_subcommands(sub)

    # ------------------------------------------------------------------ #
    # workflow subcommand                                                  #
    # ------------------------------------------------------------------ #
    from ttadev.cli.workflow import register_workflow_subcommands

    register_workflow_subcommands(sub)

    # ------------------------------------------------------------------ #
    # control subcommand                                                   #
    # ------------------------------------------------------------------ #
    from ttadev.cli.control import register_control_subcommands

    register_control_subcommands(sub)

    # ------------------------------------------------------------------ #
    # models subcommand                                                    #
    # ------------------------------------------------------------------ #
    from ttadev.cli.models import register_model_subcommands

    register_model_subcommands(sub)

    # ------------------------------------------------------------------ #
    # primitives subcommand                                                #
    # ------------------------------------------------------------------ #
    from ttadev.cli.primitives import register_primitives_subcommands

    register_primitives_subcommands(sub)

    # ------------------------------------------------------------------ #
    # new subcommand                                                       #
    # ------------------------------------------------------------------ #
    new_p = sub.add_parser(
        "new",
        help="Scaffold a new TTA.dev project in a fresh directory",
    )
    new_p.add_argument("name", help="App name (alphanumeric, hyphens, underscores)")
    new_p.add_argument(
        "--output-dir",
        dest="output_dir",
        default=None,
        metavar="DIR",
        help="Parent directory for the new app (default: current directory)",
    )
    new_p.add_argument(
        "--path",
        dest="output_dir",
        metavar="DIR",
        help="Alias for --output-dir: parent directory for the new app",
    )
    new_p.add_argument(
        "--provider",
        dest="provider",
        default="groq",
        choices=["groq", "ollama", "openrouter"],
        metavar="PROVIDER",
        help="Default LLM provider in hello.py: groq, ollama, or openrouter (default: groq)",
    )
    new_p.add_argument(
        "--no-git",
        dest="no_git",
        action="store_true",
        help="Skip running `git init` in the new directory",
    )

    # ------------------------------------------------------------------ #
    # setup subcommand                                                     #
    # ------------------------------------------------------------------ #
    setup_p = sub.add_parser("setup", help="Interactive setup wizard for LLM providers")
    setup_p.add_argument(
        "--non-interactive",
        action="store_true",
        help="Fail if no TTY (CI mode)",
    )

    # ------------------------------------------------------------------ #
    # validate-keys subcommand                                             #
    # ------------------------------------------------------------------ #
    vk_p = sub.add_parser("validate-keys", help="Test all configured LLM provider connections")
    vk_p.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output JSON",
    )

    # ------------------------------------------------------------------ #
    # status subcommand                                                    #
    # ------------------------------------------------------------------ #
    status_p = sub.add_parser(
        "status", help="Show system health: providers, services, and control plane"
    )
    status_p.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Output JSON (no ANSI colours, no key values)",
    )

    # ------------------------------------------------------------------ #
    # observe subcommand                                                   #
    # ------------------------------------------------------------------ #
    observe_p = sub.add_parser(
        "observe",
        help="Start the TTA.dev observability dashboard (idempotent)",
    )
    observe_p.add_argument(
        "--port",
        type=int,
        default=8000,
        metavar="PORT",
        help="Port to serve the dashboard on (default: 8000)",
    )
    observe_p.add_argument(
        "--no-browser",
        dest="no_browser",
        action="store_true",
        help="Start the server but do not open a browser tab",
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    if args.command == "run":
        from ttadev.cli.run import run_cache, run_echo, run_retry, run_timeout

        if not args.run_command:
            parser.parse_args(["run", "--help"])
            sys.exit(0)

        # Strip leading "--" separator if present
        cmd = args.cmd
        if cmd and cmd[0] == "--":
            cmd = cmd[1:]

        if not cmd and args.run_command != "echo":
            print(
                f"error: 'tta run {args.run_command}' requires a command after --", file=sys.stderr
            )
            sys.exit(1)

        if args.run_command == "retry":
            run_retry(cmd, max_retries=args.max_retries, data_dir=data_dir)
        elif args.run_command == "timeout":
            run_timeout(cmd, seconds=args.seconds, data_dir=data_dir)
        elif args.run_command == "cache":
            run_cache(cmd, ttl=args.ttl, key=args.key, data_dir=data_dir)
        elif args.run_command == "echo":
            run_echo(cmd)
        else:
            parser.parse_args(["run", "--help"])

    elif args.command == "session":
        from ttadev.cli.session import (
            current_session,
            end_session,
            list_sessions,
            list_spans,
            show_session,
        )

        if args.session_command == "list":
            list_sessions(data_dir, limit=args.limit, project_name=args.project_name)
        elif args.session_command == "show":
            show_session(args.session_id, data_dir)
        elif args.session_command == "current":
            current_session(data_dir)
        elif args.session_command == "end":
            end_session(data_dir)
        elif args.session_command == "spans":
            list_spans(
                args.session_id,
                data_dir,
                limit=args.limit,
                primitive_filter=args.primitive_filter,
            )
        else:
            parser.parse_args(["session", "--help"])

    elif args.command == "project":
        from ttadev.cli.project import join, list_projects, show

        if args.project_command == "join":
            join(args.name, data_dir)
        elif args.project_command == "list":
            list_projects(data_dir)
        elif args.project_command == "show":
            show(args.name, data_dir)
        else:
            parser.parse_args(["project", "--help"])

    elif args.command == "agent":
        from ttadev.cli.agent import handle_agent_command

        sys.exit(handle_agent_command(args))

    elif args.command == "agents":
        from ttadev.cli.agents import handle_agents_command

        sys.exit(handle_agents_command(args))

    elif args.command == "workflow":
        from ttadev.cli.workflow import handle_workflow_command

        sys.exit(handle_workflow_command(args, data_dir))

    elif args.command == "control":
        from ttadev.cli.control import handle_control_command

        sys.exit(handle_control_command(args, data_dir))

    elif args.command == "models":
        from ttadev.cli.models import handle_model_command

        sys.exit(handle_model_command(args))

    elif args.command == "primitives":
        from ttadev.cli.primitives import handle_primitives_command

        sys.exit(handle_primitives_command(args))

    elif args.command == "new":
        from ttadev.cli.new import cmd_new

        sys.exit(cmd_new(args, project_root=Path(".")))

    elif args.command == "setup":
        from ttadev.cli.setup import cmd_setup

        sys.exit(cmd_setup(args, project_root=Path(".")))

    elif args.command == "validate-keys":
        from ttadev.cli.setup import cmd_validate_keys

        sys.exit(cmd_validate_keys(args, project_root=Path(".")))

    elif args.command == "status":
        from ttadev.cli.status import cmd_status

        sys.exit(cmd_status(args, project_root=Path("."), data_dir=data_dir))

    elif args.command == "observe":
        import asyncio
        import socket
        import webbrowser

        port = args.port
        no_browser = args.no_browser

        def _port_in_use(p: int) -> bool:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", p)) == 0

        if _port_in_use(port):
            url = f"http://localhost:{port}"
            print(f"Dashboard already running → {url}")
            if not no_browser:
                webbrowser.open(url)
            sys.exit(0)

        async def _run() -> None:
            from ttadev.observability.server import ObservabilityServer

            server = ObservabilityServer(port=port)
            await server.start()
            url = f"http://localhost:{port}"
            print(f"TTA.dev Observability Dashboard → {url}")
            print("Press Ctrl+C to stop.")
            if not no_browser:
                webbrowser.open(url)
            try:
                await asyncio.Event().wait()
            except (KeyboardInterrupt, asyncio.CancelledError):
                print("\nShutting down...")
                await server.stop()

        asyncio.run(_run())

    else:
        parser.print_help()
        sys.exit(0)
