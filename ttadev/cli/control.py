"""CLI subcommands for the local L0 control plane."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ttadev.control_plane import (
    ControlPlaneError,
    ControlPlaneService,
    GateStatus,
    LockScopeType,
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
    task_create.add_argument(
        "--gate",
        action="append",
        default=[],
        help="Gate spec in the form <gate_id>:<gate_type>:<required|optional>:<label>",
    )
    task_create.add_argument(
        "--gate-assign-role",
        action="append",
        default=[],
        help="Assign a required role to a gate using <gate_id>:<role>",
    )
    task_create.add_argument(
        "--gate-assign-agent",
        action="append",
        default=[],
        help="Assign a required agent to a gate using <gate_id>:<agent_id>",
    )
    task_create.add_argument(
        "--gate-assign-decider",
        action="append",
        default=[],
        help="Assign a required decider identity to a gate using <gate_id>:<identity>",
    )
    task_create.add_argument(
        "--workspace-lock",
        action="append",
        default=[],
        dest="workspace_locks",
        help="Workspace lock scope to auto-acquire during claim",
    )
    task_create.add_argument(
        "--file-lock",
        action="append",
        default=[],
        dest="file_locks",
        help="Repo-relative file lock to auto-acquire during claim",
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

    task_decide_gate = task_sub.add_parser("decide-gate", help="Record a gate decision")
    task_decide_gate.add_argument("task_id", help="Task ID")
    task_decide_gate.add_argument("gate_id", help="Gate ID")
    task_decide_gate.add_argument(
        "--status",
        required=True,
        choices=[status.value for status in GateStatus if status != GateStatus.PENDING],
        help="Gate decision status",
    )
    task_decide_gate.add_argument(
        "--role", dest="decision_role", default=None, help="Decision role"
    )
    task_decide_gate.add_argument("--by", dest="decided_by", default=None, help="Decider identity")
    task_decide_gate.add_argument("--summary", default="", help="Decision summary")

    task_reopen_gate = task_sub.add_parser(
        "reopen-gate", help="Reopen a gate after changes requested"
    )
    task_reopen_gate.add_argument("task_id", help="Task ID")
    task_reopen_gate.add_argument("gate_id", help="Gate ID")
    task_reopen_gate.add_argument(
        "--by", dest="reopened_by", default=None, help="Reopener identity"
    )
    task_reopen_gate.add_argument("--summary", default="", help="Reopen summary")

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

    lock_p = control_sub.add_parser("lock", help="Inspect and mutate control-plane locks")
    lock_sub = lock_p.add_subparsers(dest="control_lock_command")

    lock_list = lock_sub.add_parser("list", help="List active locks")
    lock_list.add_argument(
        "--scope-type",
        choices=[scope.value for scope in LockScopeType],
        default=None,
        help="Filter by lock scope type",
    )

    lock_acquire_workspace = lock_sub.add_parser(
        "acquire-workspace", help="Acquire a workspace lock for an active run"
    )
    lock_acquire_workspace.add_argument("task_id", help="Task ID")
    lock_acquire_workspace.add_argument("run_id", help="Run ID")
    lock_acquire_workspace.add_argument("workspace_name", help="Workspace coordination scope")

    lock_acquire_file = lock_sub.add_parser(
        "acquire-file", help="Acquire a file lock for an active run"
    )
    lock_acquire_file.add_argument("task_id", help="Task ID")
    lock_acquire_file.add_argument("run_id", help="Run ID")
    lock_acquire_file.add_argument("file_path", help="Repo-relative file path")

    lock_release = lock_sub.add_parser("release", help="Release a lock by ID")
    lock_release.add_argument("lock_id", help="Lock ID")


def handle_control_command(args: argparse.Namespace, data_dir: Path) -> int:
    """Dispatch ``tta control`` commands."""
    service = ControlPlaneService(data_dir)
    try:
        if args.control_command == "task":
            return _handle_task_command(args, service)
        if args.control_command == "run":
            return _handle_run_command(args, service)
        if args.control_command == "lock":
            return _handle_lock_command(args, service)
    except ControlPlaneError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Usage: tta control {task,run,lock} ...", file=sys.stderr)
    return 1


def _handle_task_command(args: argparse.Namespace, service: ControlPlaneService) -> int:
    if args.control_task_command == "create":
        gates = [_parse_gate_spec(spec) for spec in args.gate]
        _apply_gate_assignments(
            gates,
            role_specs=args.gate_assign_role,
            agent_specs=args.gate_assign_agent,
            decider_specs=args.gate_assign_decider,
        )
        task = service.create_task(
            args.title,
            description=args.description,
            project_name=args.project_name,
            requested_role=args.requested_role,
            priority=args.priority,
            gates=gates,
            workspace_locks=args.workspace_locks,
            file_locks=args.file_locks,
        )
        print(f"Task: {task.id}")
        print(f"  title:    {task.title}")
        print(f"  status:   {task.status.value}")
        if task.project_name:
            print(f"  project:  {task.project_name}")
        if task.requested_role:
            print(f"  role:     {task.requested_role}")
        if task.gates:
            print(f"  gates:    {len(task.gates)}")
        if task.workspace_locks:
            print(f"  workspace_locks: {', '.join(task.workspace_locks)}")
        if task.file_locks:
            print(f"  file_locks: {', '.join(task.file_locks)}")
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
        if task.gates:
            print("  gates:")
            for gate in task.gates:
                decision = gate.decided_by or "-"
                decided_at = gate.decided_at or "-"
                summary = gate.summary or "-"
                required = "required" if gate.required else "optional"
                assigned_role = gate.assigned_role or "-"
                assigned_agent_id = gate.assigned_agent_id or "-"
                assigned_decider = gate.assigned_decider or "-"
                print(
                    "    "
                    f"{gate.id} [{gate.gate_type.value}] {required} label={gate.label} status={gate.status.value} "
                    f"assigned_role={assigned_role} assigned_agent={assigned_agent_id} "
                    f"assigned_decider={assigned_decider} by={decision} at={decided_at} summary={summary}"
                )
                if gate.history:
                    print("      history:")
                    for entry in gate.history:
                        from_status = (
                            entry.from_status.value if entry.from_status is not None else "-"
                        )
                        print(
                            "        "
                            f"- {entry.action.value} {from_status} -> {entry.to_status.value} "
                            f"by {entry.actor} at {entry.occurred_at}"
                        )
                        if entry.summary:
                            print(f"          summary={entry.summary}")
        if task.workspace_locks:
            print(f"  workspace_locks: {', '.join(task.workspace_locks)}")
        if task.file_locks:
            print(f"  file_locks: {', '.join(task.file_locks)}")
        if task.workflow is not None:
            workflow = task.workflow
            print("  workflow:")
            print(f"    name:              {workflow.workflow_name}")
            print(f"    goal:              {workflow.workflow_goal}")
            print(f"    status:            {workflow.status.value}")
            print(f"    total_steps:       {workflow.total_steps}")
            print(
                "    current_step:      "
                f"{workflow.current_step_index + 1 if workflow.current_step_index is not None else '-'}"
            )
            print(f"    current_agent:     {workflow.current_agent or '-'}")
            print("    steps:")
            for step in workflow.steps:
                linked_gate = step.linked_gate_id or "-"
                decision = step.gate_decision.value if step.gate_decision is not None else "-"
                started_at = step.started_at or "-"
                completed_at = step.completed_at or "-"
                summary = step.last_result_summary or "-"
                confidence = (
                    f"{step.last_confidence:.0%}" if step.last_confidence is not None else "-"
                )
                print(
                    "      "
                    f"{step.step_index + 1}. {step.agent_name} "
                    f"status={step.status.value} attempts={step.attempts} "
                    f"gate={decision} linked_gate={linked_gate} "
                    f"started_at={started_at} completed_at={completed_at} "
                    f"confidence={confidence}"
                )
                print(f"         summary={summary}")
                if step.gate_history:
                    print("         gate_history:")
                    for record in step.gate_history:
                        entry_summary = record.summary or "-"
                        print(
                            "           "
                            f"- {record.decision.value} at {record.occurred_at} summary={entry_summary}"
                        )
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

    if args.control_task_command == "decide-gate":
        task = service.decide_gate(
            args.task_id,
            args.gate_id,
            status=GateStatus(args.status),
            decided_by=args.decided_by,
            decision_role=args.decision_role,
            summary=args.summary,
        )
        gate = next(gate for gate in task.gates if gate.id == args.gate_id)
        print(f"Task: {task.id}")
        print(f"Gate: {gate.id}")
        print(f"  status:     {gate.status.value}")
        print(f"  decided_by: {gate.decided_by or '-'}")
        print(f"  role:       {gate.assigned_role or args.decision_role or '-'}")
        if gate.summary:
            print(f"  summary:    {gate.summary}")
        return 0

    if args.control_task_command == "reopen-gate":
        task = service.reopen_gate(
            args.task_id,
            args.gate_id,
            reopened_by=args.reopened_by,
            summary=args.summary,
        )
        gate = next(gate for gate in task.gates if gate.id == args.gate_id)
        print(f"Task: {task.id}")
        print(f"Gate: {gate.id}")
        print(f"  status:     {gate.status.value}")
        if gate.summary:
            print(f"  summary:    {gate.summary}")
        return 0

    print(
        "Usage: tta control task {create,list,show,claim,decide-gate,reopen-gate}", file=sys.stderr
    )
    return 1


def _parse_gate_spec(spec: str) -> dict[str, str | bool]:
    """Parse a CLI gate specification into a task gate payload."""
    parts = spec.split(":", 3)
    if len(parts) != 4:
        raise ControlPlaneError(
            "Gate spec must use the form <gate_id>:<gate_type>:<required|optional>:<label>"
        )
    gate_id, gate_type, required_flag, label = parts
    if required_flag not in {"required", "optional"}:
        raise ControlPlaneError(f"Gate {gate_id} must use required|optional in the third segment")
    return {
        "id": gate_id,
        "gate_type": gate_type,
        "required": required_flag == "required",
        "label": label,
    }


def _parse_gate_assignment_spec(spec: str, label: str) -> tuple[str, str]:
    """Parse a gate assignment spec of the form <gate_id>:<value>."""
    gate_id, sep, value = spec.partition(":")
    gate_id = gate_id.strip()
    value = value.strip()
    if not sep or not gate_id or not value:
        raise ControlPlaneError(f"{label} must use the form <gate_id>:<value>")
    return gate_id, value


def _apply_gate_assignments(
    gates: list[dict[str, str | bool]],
    *,
    role_specs: list[str],
    agent_specs: list[str],
    decider_specs: list[str],
) -> None:
    """Apply CLI gate assignment flags to parsed gate payloads."""
    gate_map = {str(gate["id"]): gate for gate in gates}

    def assign(specs: list[str], field_name: str, label: str) -> None:
        seen: set[str] = set()
        for spec in specs:
            gate_id, value = _parse_gate_assignment_spec(spec, label)
            gate = gate_map.get(gate_id)
            if gate is None:
                raise ControlPlaneError(f"Unknown gate ID in {label}: {gate_id}")
            if gate_id in seen:
                raise ControlPlaneError(f"Duplicate {label} assignment for gate: {gate_id}")
            gate[field_name] = value
            seen.add(gate_id)

    assign(role_specs, "assigned_role", "--gate-assign-role")
    assign(agent_specs, "assigned_agent_id", "--gate-assign-agent")
    assign(decider_specs, "assigned_decider", "--gate-assign-decider")


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


def _handle_lock_command(args: argparse.Namespace, service: ControlPlaneService) -> int:
    if args.control_lock_command == "list":
        scope_type = LockScopeType(args.scope_type) if args.scope_type else None
        locks = service.list_locks(scope_type=scope_type)
        if not locks:
            print("No locks found.")
            return 0
        print(f"{'LOCK ID':<18} {'SCOPE':<10} {'VALUE':<28} {'TASK ID':<18} {'RUN ID':<17}")
        print("-" * 100)
        for lock in locks:
            print(
                f"{lock.id:<18} {lock.scope_type.value:<10} {lock.scope_value:<28} "
                f"{lock.task_id:<18} {lock.run_id:<17}"
            )
        return 0

    if args.control_lock_command == "acquire-workspace":
        lock = service.acquire_workspace_lock(args.task_id, args.run_id, args.workspace_name)
        print(f"Lock: {lock.id}")
        print(f"  scope_type:  {lock.scope_type.value}")
        print(f"  scope_value: {lock.scope_value}")
        print(f"  task_id:     {lock.task_id}")
        print(f"  run_id:      {lock.run_id}")
        return 0

    if args.control_lock_command == "acquire-file":
        lock = service.acquire_file_lock(args.task_id, args.run_id, args.file_path)
        print(f"Lock: {lock.id}")
        print(f"  scope_type:  {lock.scope_type.value}")
        print(f"  scope_value: {lock.scope_value}")
        print(f"  task_id:     {lock.task_id}")
        print(f"  run_id:      {lock.run_id}")
        return 0

    if args.control_lock_command == "release":
        service.release_lock(args.lock_id)
        print(f"Released lock: {args.lock_id}")
        return 0

    print("Usage: tta control lock {list,acquire-workspace,acquire-file,release}", file=sys.stderr)
    return 1
