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

    # project subcommand
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

    if args.command == "project":
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
