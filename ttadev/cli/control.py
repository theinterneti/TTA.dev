"""CLI subcommands for the local L0 control plane."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ttadev.control_plane import (
    ControlPlaneError,
    ControlPlaneService,
    RunStatus,
    TaskStatus,
)


def register_control_subcommands(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Wire ``tta control`` subcommands into the main parser."""
    control_p = sub.add_parser("control", help="Manage local L0 tasks, runs, and leases")
    control_sub = control_p.add_subparsers(dest="control_command")

    task_p = control_sub.add_parser("task", help="Manage control-plane tasks")
    task_sub = task_p.add_subparsers(dest="control_task_command")

    task_create = task_sub.add_parser("create", help="Create a new task")
    task_create.add_argument("title", help="Task title")
    task_create.add_argument("--description", default="", help="Task description")
    task_create.add_argument("--project", dest="project_name", default=None, help="Project name")
    task_create.add_argument("--role", dest="requested_role", default=None, help="Requested role")
    task_create.add_argument(
        "--priority",
        choices=["low", "normal", "high"],
        default="normal",
        help="Task priority",
    )

    task_list = task_sub.add_parser("list", help="List tasks")
    task_list.add_argument(
        "--status",
        choices=[status.value for status in TaskStatus],
        default=None,
        help="Filter by task status",
    )
    task_list.add_argument("--project", dest="project_name", default=None, help="Project name")

    task_show = task_sub.add_parser("show", help="Show task details")
    task_show.add_argument("task_id", help="Task ID")

    task_claim = task_sub.add_parser("claim", help="Claim a task and create a run")
    task_claim.add_argument("task_id", help="Task ID")
    task_claim.add_argument("--role", dest="agent_role", default=None, help="Agent role")
    task_claim.add_argument("--ttl", type=float, default=300.0, help="Lease TTL in seconds")

    run_p = control_sub.add_parser("run", help="Inspect and mutate control-plane runs")
    run_sub = run_p.add_subparsers(dest="control_run_command")

    run_list = run_sub.add_parser("list", help="List runs")
    run_list.add_argument(
        "--status",
        choices=[status.value for status in RunStatus],
        default=None,
        help="Filter by run status",
    )

    run_show = run_sub.add_parser("show", help="Show run details")
    run_show.add_argument("run_id", help="Run ID")

    run_heartbeat = run_sub.add_parser("heartbeat", help="Renew an active run lease")
    run_heartbeat.add_argument("run_id", help="Run ID")
    run_heartbeat.add_argument("--ttl", type=float, default=300.0, help="Lease TTL in seconds")

    run_complete = run_sub.add_parser("complete", help="Complete an active run")
    run_complete.add_argument("run_id", help="Run ID")
    run_complete.add_argument("--summary", default="", help="Completion summary")

    run_release = run_sub.add_parser("release", help="Release an active run")
    run_release.add_argument("run_id", help="Run ID")
    run_release.add_argument("--reason", default="", help="Release reason")


def handle_control_command(args: argparse.Namespace, data_dir: Path) -> int:
    """Dispatch ``tta control`` commands."""
    service = ControlPlaneService(data_dir)
    try:
        if args.control_command == "task":
            return _handle_task_command(args, service)
        if args.control_command == "run":
            return _handle_run_command(args, service)
    except ControlPlaneError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Usage: tta control {task,run} ...", file=sys.stderr)
    return 1


def _handle_task_command(args: argparse.Namespace, service: ControlPlaneService) -> int:
    if args.control_task_command == "create":
        task = service.create_task(
            args.title,
            description=args.description,
            project_name=args.project_name,
            requested_role=args.requested_role,
            priority=args.priority,
        )
        print(f"Task: {task.id}")
        print(f"  title:    {task.title}")
        print(f"  status:   {task.status.value}")
        if task.project_name:
            print(f"  project:  {task.project_name}")
        if task.requested_role:
            print(f"  role:     {task.requested_role}")
        return 0

    if args.control_task_command == "list":
        status = TaskStatus(args.status) if args.status else None
        tasks = service.list_tasks(status=status, project_name=args.project_name)
        if not tasks:
            print("No tasks found.")
            return 0
        print(f"{'TASK ID':<18} {'STATUS':<12} {'PRIORITY':<8} {'ROLE':<14} {'PROJECT':<14} TITLE")
        print("-" * 88)
        for task in tasks:
            print(
                f"{task.id:<18} {task.status.value:<12} {task.priority:<8} "
                f"{(task.requested_role or '-'): <14} {(task.project_name or '-'): <14} {task.title}"
            )
        return 0

    if args.control_task_command == "show":
        task = service.get_task(args.task_id)
        print(f"Task: {task.id}")
        print(f"  title:          {task.title}")
        print(f"  description:    {task.description or '-'}")
        print(f"  status:         {task.status.value}")
        print(f"  priority:       {task.priority}")
        print(f"  project:        {task.project_name or '-'}")
        print(f"  requested_role: {task.requested_role or '-'}")
        print(f"  active_run_id:  {task.active_run_id or '-'}")
        print(f"  claimed_by:     {task.claimed_by_agent_id or '-'}")
        print(f"  created_at:     {task.created_at}")
        print(f"  updated_at:     {task.updated_at}")
        if task.completed_at:
            print(f"  completed_at:   {task.completed_at}")
        return 0

    if args.control_task_command == "claim":
        claim = service.claim_task(
            args.task_id,
            agent_role=args.agent_role,
            lease_ttl_seconds=args.ttl,
        )
        print(f"Task: {claim.task.id}")
        print(f"Run:  {claim.run.id}")
        print(f"  status:      {claim.run.status.value}")
        print(f"  agent_id:    {claim.run.agent_id}")
        print(f"  agent_tool:  {claim.run.agent_tool}")
        print(f"  session_id:  {claim.run.session_id or '-'}")
        print(f"  expires_at:  {claim.lease.expires_at}")
        return 0

    print("Usage: tta control task {create,list,show,claim}", file=sys.stderr)
    return 1


def _handle_run_command(args: argparse.Namespace, service: ControlPlaneService) -> int:
    if args.control_run_command == "list":
        status = RunStatus(args.status) if args.status else None
        runs = service.list_runs(status=status)
        if not runs:
            print("No runs found.")
            return 0
        print(f"{'RUN ID':<17} {'TASK ID':<18} {'STATUS':<10} {'AGENT':<16} {'ROLE':<14}")
        print("-" * 82)
        for run in runs:
            print(
                f"{run.id:<17} {run.task_id:<18} {run.status.value:<10} "
                f"{run.agent_id[:16]:<16} {(run.agent_role or '-'): <14}"
            )
        return 0

    if args.control_run_command == "show":
        run = service.get_run(args.run_id)
        lease = service.get_lease_for_run(args.run_id)
        print(f"Run: {run.id}")
        print(f"  task_id:     {run.task_id}")
        print(f"  status:      {run.status.value}")
        print(f"  agent_id:    {run.agent_id}")
        print(f"  agent_tool:  {run.agent_tool}")
        print(f"  agent_role:  {run.agent_role or '-'}")
        print(f"  session_id:  {run.session_id or '-'}")
        print(f"  started_at:  {run.started_at}")
        print(f"  updated_at:  {run.updated_at}")
        print(f"  ended_at:    {run.ended_at or '-'}")
        if run.summary:
            print(f"  summary:     {run.summary}")
        print(f"  lease:       {lease.expires_at if lease else '-'}")
        return 0

    if args.control_run_command == "heartbeat":
        lease = service.heartbeat_run(args.run_id, lease_ttl_seconds=args.ttl)
        print(f"Run: {args.run_id}")
        print(f"  expires_at: {lease.expires_at}")
        return 0

    if args.control_run_command == "complete":
        run = service.complete_run(args.run_id, summary=args.summary)
        print(f"Completed run: {run.id}")
        if run.summary:
            print(f"  summary: {run.summary}")
        return 0

    if args.control_run_command == "release":
        run = service.release_run(args.run_id, reason=args.reason)
        print(f"Released run: {run.id}")
        if run.summary:
            print(f"  reason: {run.summary}")
        return 0

    print("Usage: tta control run {list,show,heartbeat,complete,release}", file=sys.stderr)
    return 1
