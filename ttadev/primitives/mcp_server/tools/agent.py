"""TTA.dev MCP server: agent fleet tools."""

import asyncio
import uuid
from typing import Any

from ._helpers import _FLEET_STORE, _run_fleet_task, logger


def register_agent_tools(mcp: Any, _ro: Any, _mut: Any) -> None:
    """Register agent fleet tools with the MCP server."""

    @mcp.tool(annotations=_mut)
    async def agent_spawn_fleet(
        tasks: list[str],
        agent_hints: list[str | None] | None = None,
        provider: str = "auto",
    ) -> dict[str, Any]:
        """Dispatch multiple agent tasks concurrently and return a fleet ID.

        Each task runs in parallel via asyncio background tasks.  Results are
        stored in the in-process fleet store and are retrievable via
        :func:`agent_poll_fleet`.

        Args:
            tasks: List of task descriptions (natural language).  Must be
                non-empty; maximum 50 tasks per fleet.
            agent_hints: Optional list of agent names to use, parallel-indexed
                with ``tasks``.  ``None`` entries mean auto-select.  When
                omitted, all tasks are auto-assigned.  Valid names:
                ``developer``, ``devops``, ``git``, ``github``,
                ``performance``, ``qa``, ``security``.
            provider: LLM provider hint — ``'groq'``, ``'google'``,
                ``'ollama'``, or ``'auto'``.  Passed through to the agent
                executor for future model-routing support.

        Returns:
            ``{'fleet_id': str, 'task_count': int, 'status': 'dispatched'}``
        """
        logger.info(
            "mcp_tool_called",
            tool="agent_spawn_fleet",
            task_count=len(tasks),
            provider=provider,
        )

        if not tasks:
            return {"error": "tasks must be a non-empty list"}
        if len(tasks) > 50:
            return {"error": f"Too many tasks: {len(tasks)} (maximum 50 per fleet)"}

        hints: list[str | None]
        if agent_hints is None:
            hints = [None] * len(tasks)
        elif len(agent_hints) != len(tasks):
            return {
                "error": (
                    f"agent_hints length ({len(agent_hints)}) must match "
                    f"tasks length ({len(tasks)}) when provided"
                )
            }
        else:
            hints = list(agent_hints)

        fleet_id = "fleet-" + uuid.uuid4().hex[:8]

        _FLEET_STORE[fleet_id] = {
            "fleet_id": fleet_id,
            "task_count": len(tasks),
            "completed_count": 0,
            "provider": provider,
            "results": [
                {
                    "task_id": f"{fleet_id}-{i}",
                    "task": task,
                    "agent": hints[i] or "auto",
                    "output": None,
                    "status": "pending",
                }
                for i, task in enumerate(tasks)
            ],
        }

        for i, (task_text, hint) in enumerate(zip(tasks, hints)):
            asyncio.create_task(
                _run_fleet_task(fleet_id, i, task_text, hint, provider),
                name=f"{fleet_id}-task-{i}",
            )

        logger.info("fleet_dispatched", fleet_id=fleet_id, task_count=len(tasks))
        return {"fleet_id": fleet_id, "task_count": len(tasks), "status": "dispatched"}

    @mcp.tool(annotations=_ro)
    async def agent_poll_fleet(fleet_id: str) -> dict[str, Any]:
        """Poll the status of a previously spawned agent fleet.

        Args:
            fleet_id: The ``fleet_id`` returned by :func:`agent_spawn_fleet`.

        Returns:
            ::

                {
                    'status': 'pending' | 'running' | 'partial' | 'complete',
                    'task_count': int,
                    'completed_count': int,
                    'results': [
                        {
                            'task_id': str,
                            'task': str,
                            'agent': str,
                            'output': str | None,
                            'status': str,
                        }
                    ]
                }

            Returns ``{'error': str}`` when the ``fleet_id`` is unknown.
        """
        logger.info("mcp_tool_called", tool="agent_poll_fleet", fleet_id=fleet_id)

        fleet = _FLEET_STORE.get(fleet_id)
        if fleet is None:
            return {"error": f"Unknown fleet_id: {fleet_id!r}"}

        task_count: int = fleet["task_count"]
        completed: int = fleet["completed_count"]
        results: list[dict[str, Any]] = fleet["results"]

        if completed == 0:
            any_running = any(r["status"] == "running" for r in results)
            status = "running" if any_running else "pending"
        elif completed < task_count:
            status = "partial"
        else:
            status = "complete"

        return {
            "status": status,
            "task_count": task_count,
            "completed_count": completed,
            "results": list(results),
        }
