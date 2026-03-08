"""Context integration — bridges universal-agent-context with agent-coordination.

This module re-exports the L1 agent-context primitives (coordination, memory, handoff)
so that consumers of ``tta-agent-coordination`` have a single import surface for both
DevOps managers (L2–L4) and multi-agent context management (L1).

It also provides ``CoordinatedManagerWorkflow``, a convenience primitive that wires
agent-context coordination around one or more agent-coordination managers.

Example::

    from tta_agent_coordination.context_integration import (
        CoordinatedManagerWorkflow,
        AgentCoordinationPrimitive,
        AgentMemoryPrimitive,
        AgentHandoffPrimitive,
    )
"""

from typing import Any

from primitives.core.base import WorkflowContext, WorkflowPrimitive
from universal_agent_context.primitives import (
    AgentCoordinationPrimitive,
    AgentHandoffPrimitive,
    AgentMemoryPrimitive,
)

__all__ = [
    # Re-exported L1 primitives
    "AgentCoordinationPrimitive",
    "AgentHandoffPrimitive",
    "AgentMemoryPrimitive",
    # Integration adapter
    "CoordinatedManagerWorkflow",
]


class CoordinatedManagerWorkflow(WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """Orchestrate multiple agent-coordination managers via agent-context primitives.

    Wraps a set of named ``WorkflowPrimitive`` managers (e.g. CICDManager,
    QualityManager, InfrastructureManager) with ``AgentCoordinationPrimitive``
    so they execute in parallel with proper context propagation, memory
    tracking, and coordination metadata.

    Args:
        managers: Mapping of manager names to their primitives.
        coordination_strategy: How to aggregate results
            (``"aggregate"``, ``"first"``, or ``"consensus"``).
        timeout_seconds: Optional timeout applied to all managers.
        require_all_success: Whether every manager must succeed.
        store_results_in_memory: When ``True``, stores the coordination
            result in agent memory under key ``"coordination_result"``.

    Example::

        from tta_agent_coordination.context_integration import (
            CoordinatedManagerWorkflow,
        )

        workflow = CoordinatedManagerWorkflow(
            managers={
                "cicd": cicd_manager,
                "quality": quality_manager,
            },
            coordination_strategy="aggregate",
            store_results_in_memory=True,
        )
        result = await workflow.execute(operation_data, context)
    """

    def __init__(
        self,
        managers: dict[str, WorkflowPrimitive],
        coordination_strategy: str = "aggregate",
        timeout_seconds: float | None = None,
        require_all_success: bool = False,
        store_results_in_memory: bool = False,
    ) -> None:
        self.managers = managers
        self.coordination_strategy = coordination_strategy
        self.timeout_seconds = timeout_seconds
        self.require_all_success = require_all_success
        self.store_results_in_memory = store_results_in_memory

        self._coordinator = AgentCoordinationPrimitive(
            agent_primitives=managers,
            coordination_strategy=coordination_strategy,
            timeout_seconds=timeout_seconds,
            require_all_success=require_all_success,
            name="CoordinatedManagerWorkflow",
        )

        self._memory: AgentMemoryPrimitive | None = None
        if store_results_in_memory:
            self._memory = AgentMemoryPrimitive(
                operation="store",
                memory_key="coordination_result",
                memory_scope="workflow",
                name="CoordinatedManagerMemory",
            )

    async def execute(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Execute managers in parallel via AgentCoordinationPrimitive.

        Args:
            input_data: Operation data forwarded to every manager.
            context: Workflow context with tracing and metadata.

        Returns:
            Coordination result dict containing ``agent_results``,
            ``coordination_metadata``, ``aggregated_result``, and
            ``failed_agents``.
        """
        result = await self._coordinator.execute(input_data, context)

        if self._memory is not None:
            memory_input = {
                "memory_value": result,
            }
            await self._memory.execute(memory_input, context)

        return result
