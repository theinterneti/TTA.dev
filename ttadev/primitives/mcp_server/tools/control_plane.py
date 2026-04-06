"""TTA.dev MCP server: L0 control-plane tools."""

from typing import Any

from ttadev.control_plane import (
    ControlPlaneError,
    GateStatus,
    LockScopeType,
    RunStatus,
    TaskStatus,
)

from ._helpers import (
    _control_plane_error_payload,
    _create_control_plane_service,
    _ensure_project_exists,
    _ensure_session_exists,
    _paginate,
    _serialize_lease,
    _serialize_lock,
    _serialize_ownership_records,
    _serialize_run,
    _serialize_task,
    logger,
)


def register_control_plane_tools(mcp: Any, _ro: Any, _mut: Any, _idem: Any) -> None:
    """Register L0 control-plane tools with the MCP server."""

    @mcp.tool(annotations=_mut)
    async def control_create_task(
        title: str,
        description: str = "",
        project_name: str | None = None,
        requested_role: str | None = None,
        priority: str = "normal",
        gates: list[dict[str, Any]] | None = None,
        workspace_locks: list[str] | None = None,
        file_locks: list[str] | None = None,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Create a new L0 control-plane task."""
        logger.info(
            "mcp_tool_called",
            tool="control_create_task",
            data_dir=data_dir,
            project_name=project_name,
            priority=priority,
        )
        try:
            service = _create_control_plane_service(data_dir)
            task = service.create_task(
                title,
                description=description,
                project_name=project_name,
                requested_role=requested_role,
                priority=priority,
                gates=gates,
                workspace_locks=workspace_locks,
                file_locks=file_locks,
            )
        except ControlPlaneError as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    @mcp.tool(annotations=_ro)
    async def control_list_tasks(
        status: str | None = None,
        project_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """List L0 control-plane tasks."""
        logger.info(
            "mcp_tool_called",
            tool="control_list_tasks",
            data_dir=data_dir,
            status=status,
            project_name=project_name,
        )
        try:
            service = _create_control_plane_service(data_dir)
            parsed_status = TaskStatus(status) if status is not None else None
            tasks = service.list_tasks(status=parsed_status, project_name=project_name)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        page = _paginate([_serialize_task(t) for t in tasks], limit, offset)
        return {"tasks": page["items"], **{k: v for k, v in page.items() if k != "items"}}

    @mcp.tool(annotations=_ro)
    async def control_get_task(task_id: str, data_dir: str = ".tta") -> dict[str, Any]:
        """Get a single L0 control-plane task."""
        logger.info(
            "mcp_tool_called",
            tool="control_get_task",
            data_dir=data_dir,
            task_id=task_id,
        )
        try:
            service = _create_control_plane_service(data_dir)
            task = service.get_task(task_id)
        except ControlPlaneError as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    @mcp.tool(annotations=_mut)
    async def control_claim_task(
        task_id: str,
        agent_role: str | None = None,
        lease_ttl_seconds: float = 300.0,
        trace_id: str | None = None,
        span_id: str | None = None,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Claim an L0 control-plane task and create an active run.

        Pass ``trace_id`` and ``span_id`` (hex strings) to stamp the current
        OTel span context onto the run record for attribution.
        """
        logger.info(
            "mcp_tool_called",
            tool="control_claim_task",
            data_dir=data_dir,
            task_id=task_id,
            agent_role=agent_role,
            lease_ttl_seconds=lease_ttl_seconds,
        )
        try:
            service = _create_control_plane_service(data_dir)
            claim = service.claim_task(
                task_id,
                agent_role=agent_role,
                lease_ttl_seconds=lease_ttl_seconds,
                trace_id=trace_id,
                span_id=span_id,
            )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {
            "task": _serialize_task(claim.task),
            "run": _serialize_run(claim.run),
            "lease": _serialize_lease(claim.lease),
        }

    @mcp.tool(annotations=_mut)
    async def control_decide_gate(
        task_id: str,
        gate_id: str,
        status: str,
        decided_by: str | None = None,
        decision_role: str | None = None,
        summary: str = "",
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Record a gate decision for an L0 control-plane task."""
        logger.info(
            "mcp_tool_called",
            tool="control_decide_gate",
            data_dir=data_dir,
            task_id=task_id,
            gate_id=gate_id,
            status=status,
            decision_role=decision_role,
        )
        try:
            service = _create_control_plane_service(data_dir)
            task = service.decide_gate(
                task_id,
                gate_id,
                status=GateStatus(status),
                decided_by=decided_by,
                decision_role=decision_role,
                summary=summary,
            )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    @mcp.tool(annotations=_mut)
    async def control_reopen_gate(
        task_id: str,
        gate_id: str,
        reopened_by: str | None = None,
        summary: str = "",
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Reopen a gate that is currently in changes_requested."""
        logger.info(
            "mcp_tool_called",
            tool="control_reopen_gate",
            data_dir=data_dir,
            task_id=task_id,
            gate_id=gate_id,
        )
        try:
            service = _create_control_plane_service(data_dir)
            task = service.reopen_gate(
                task_id,
                gate_id,
                reopened_by=reopened_by,
                summary=summary,
            )
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"task": _serialize_task(task)}

    @mcp.tool(annotations=_ro)
    async def control_list_locks(
        scope_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """List active L0 control-plane locks."""
        logger.info(
            "mcp_tool_called",
            tool="control_list_locks",
            data_dir=data_dir,
            scope_type=scope_type,
        )
        try:
            service = _create_control_plane_service(data_dir)
            parsed_scope_type = LockScopeType(scope_type) if scope_type is not None else None
            locks = service.list_locks(scope_type=parsed_scope_type)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        page = _paginate([_serialize_lock(lock) for lock in locks], limit, offset)
        return {"locks": page["items"], **{k: v for k, v in page.items() if k != "items"}}

    @mcp.tool(annotations=_mut)
    async def control_acquire_workspace_lock(
        task_id: str,
        run_id: str,
        workspace_name: str,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Acquire a workspace lock for an active L0 run."""
        logger.info(
            "mcp_tool_called",
            tool="control_acquire_workspace_lock",
            data_dir=data_dir,
            task_id=task_id,
            run_id=run_id,
            workspace_name=workspace_name,
        )
        try:
            service = _create_control_plane_service(data_dir)
            lock = service.acquire_workspace_lock(task_id, run_id, workspace_name)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"lock": _serialize_lock(lock)}

    @mcp.tool(annotations=_mut)
    async def control_acquire_file_lock(
        task_id: str,
        run_id: str,
        file_path: str,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Acquire a file lock for an active L0 run."""
        logger.info(
            "mcp_tool_called",
            tool="control_acquire_file_lock",
            data_dir=data_dir,
            task_id=task_id,
            run_id=run_id,
            file_path=file_path,
        )
        try:
            service = _create_control_plane_service(data_dir)
            lock = service.acquire_file_lock(task_id, run_id, file_path)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"lock": _serialize_lock(lock)}

    @mcp.tool(annotations=_idem)
    async def control_release_lock(lock_id: str, data_dir: str = ".tta") -> dict[str, Any]:
        """Release an L0 control-plane lock."""
        logger.info(
            "mcp_tool_called",
            tool="control_release_lock",
            data_dir=data_dir,
            lock_id=lock_id,
        )
        try:
            service = _create_control_plane_service(data_dir)
            service.release_lock(lock_id)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"released_lock_id": lock_id}

    @mcp.tool(annotations=_ro)
    async def control_list_runs(
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """List L0 control-plane runs."""
        logger.info(
            "mcp_tool_called",
            tool="control_list_runs",
            data_dir=data_dir,
            status=status,
        )
        try:
            service = _create_control_plane_service(data_dir)
            parsed_status = RunStatus(status) if status is not None else None
            runs = service.list_runs(status=parsed_status)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        page = _paginate([_serialize_run(r) for r in runs], limit, offset)
        return {"runs": page["items"], **{k: v for k, v in page.items() if k != "items"}}

    @mcp.tool(annotations=_ro)
    async def control_get_run(run_id: str, data_dir: str = ".tta") -> dict[str, Any]:
        """Get a single L0 control-plane run and its lease, if any."""
        logger.info(
            "mcp_tool_called",
            tool="control_get_run",
            data_dir=data_dir,
            run_id=run_id,
        )
        try:
            service = _create_control_plane_service(data_dir)
            run = service.get_run(run_id)
            lease = service.get_lease_for_run(run_id)
        except ControlPlaneError as exc:
            return _control_plane_error_payload(exc)
        return {
            "run": _serialize_run(run),
            "lease": _serialize_lease(lease),
        }

    @mcp.tool(annotations=_idem)
    async def control_heartbeat_run(
        run_id: str,
        lease_ttl_seconds: float = 300.0,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Renew the lease for an active L0 control-plane run."""
        logger.info(
            "mcp_tool_called",
            tool="control_heartbeat_run",
            data_dir=data_dir,
            run_id=run_id,
            lease_ttl_seconds=lease_ttl_seconds,
        )
        try:
            service = _create_control_plane_service(data_dir)
            lease = service.heartbeat_run(run_id, lease_ttl_seconds=lease_ttl_seconds)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"lease": _serialize_lease(lease)}

    @mcp.tool(annotations=_mut)
    async def control_complete_run(
        run_id: str,
        summary: str = "",
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Complete an active L0 control-plane run."""
        logger.info(
            "mcp_tool_called",
            tool="control_complete_run",
            data_dir=data_dir,
            run_id=run_id,
        )
        try:
            service = _create_control_plane_service(data_dir)
            run = service.complete_run(run_id, summary=summary)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"run": _serialize_run(run)}

    @mcp.tool(annotations=_mut)
    async def control_release_run(
        run_id: str,
        reason: str = "",
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """Release an active L0 control-plane run back to pending."""
        logger.info(
            "mcp_tool_called",
            tool="control_release_run",
            data_dir=data_dir,
            run_id=run_id,
        )
        try:
            service = _create_control_plane_service(data_dir)
            run = service.release_run(run_id, reason=reason)
        except (ControlPlaneError, ValueError) as exc:
            return _control_plane_error_payload(exc)
        return {"run": _serialize_run(run)}

    @mcp.tool(annotations=_ro)
    async def control_list_ownership(
        limit: int = 50,
        offset: int = 0,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """List active L0 ownership records across all projects and sessions."""
        logger.info(
            "mcp_tool_called",
            tool="control_list_ownership",
            data_dir=data_dir,
        )
        try:
            service = _create_control_plane_service(data_dir)
            active = service.list_active_ownership()
        except ControlPlaneError as exc:
            return _control_plane_error_payload(exc)
        page = _paginate(_serialize_ownership_records(active), limit, offset)
        return {"active": page["items"], **{k: v for k, v in page.items() if k != "items"}}

    @mcp.tool(annotations=_ro)
    async def control_list_project_ownership(
        project_id: str,
        limit: int = 50,
        offset: int = 0,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """List active L0 ownership records for a single project."""
        logger.info(
            "mcp_tool_called",
            tool="control_list_project_ownership",
            data_dir=data_dir,
            project_id=project_id,
        )
        try:
            _ensure_project_exists(project_id, data_dir=data_dir)
            service = _create_control_plane_service(data_dir)
            active = service.list_active_ownership(project_id=project_id)
        except ControlPlaneError as exc:
            return _control_plane_error_payload(exc)
        page = _paginate(_serialize_ownership_records(active), limit, offset)
        return {
            "project_id": project_id,
            "active": page["items"],
            **{k: v for k, v in page.items() if k != "items"},
        }

    @mcp.tool(annotations=_ro)
    async def control_list_session_ownership(
        session_id: str,
        limit: int = 50,
        offset: int = 0,
        data_dir: str = ".tta",
    ) -> dict[str, Any]:
        """List active L0 ownership records for a single session."""
        logger.info(
            "mcp_tool_called",
            tool="control_list_session_ownership",
            data_dir=data_dir,
            session_id=session_id,
        )
        try:
            _ensure_session_exists(session_id, data_dir=data_dir)
            service = _create_control_plane_service(data_dir)
            active = service.list_active_ownership(session_id=session_id)
        except ControlPlaneError as exc:
            return _control_plane_error_payload(exc)
        page = _paginate(_serialize_ownership_records(active), limit, offset)
        return {
            "session_id": session_id,
            "active": page["items"],
            **{k: v for k, v in page.items() if k != "items"},
        }
