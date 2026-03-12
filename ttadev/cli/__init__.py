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

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    if args.command == "session":
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
    else:
        parser.print_help()
        sys.exit(0)
