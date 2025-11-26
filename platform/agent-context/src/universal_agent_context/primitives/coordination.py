"""Agent coordination primitive for parallel multi-agent workflows.

This primitive coordinates multiple AI agents executing tasks in parallel,
managing their outputs and ensuring proper synchronization.
"""

from typing import Any

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.observability import InstrumentedPrimitive


class AgentCoordinationPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Coordinate multiple agents executing tasks in parallel.

    This primitive manages parallel execution of multiple agents, handling their
    individual contexts, aggregating their outputs, and providing coordination
    metadata for the workflow.

    Args:
        agent_primitives: Dictionary mapping agent names to their primitives
        coordination_strategy: How to handle agent outputs ("aggregate", "first", "consensus")
        timeout_seconds: Optional timeout for agent execution
        require_all_success: Whether all agents must succeed

    Example:
        ```python
        from universal_agent_context.primitives import AgentCoordinationPrimitive

        # Define agent primitives
        agents = {
            "analyzer": data_analysis_primitive,
            "validator": validation_primitive,
            "optimizer": optimization_primitive,
        }

        # Coordinate parallel execution
        coordinator = AgentCoordinationPrimitive(
            agent_primitives=agents,
            coordination_strategy="aggregate",
            require_all_success=False
        )

        # Use in workflow
        workflow = (
            prepare_data >>
            coordinator >>  # All agents execute in parallel
            aggregate_results
        )
        ```

    Output Structure:
        Returns dict with:
        - agent_results: Dict mapping agent names to their outputs
        - coordination_metadata: Execution stats, timing, success rates
        - aggregated_result: Combined output based on strategy
        - failed_agents: List of agents that failed (if any)
    """

    def __init__(
        self,
        agent_primitives: dict[str, WorkflowPrimitive],
        coordination_strategy: str = "aggregate",
        timeout_seconds: float | None = None,
        require_all_success: bool = True,
        name: str | None = None,
    ) -> None:
        """Initialize agent coordination primitive.

        Args:
            agent_primitives: Dict mapping agent names to primitives
            coordination_strategy: "aggregate", "first", or "consensus"
            timeout_seconds: Optional timeout for all agents
            require_all_success: Whether all agents must succeed
            name: Optional name for the primitive (used for observability)
        """
        super().__init__(name=name or "AgentCoordination")

        self.agent_primitives = agent_primitives
        self.coordination_strategy = coordination_strategy
        self.timeout_seconds = timeout_seconds
        self.require_all_success = require_all_success

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Execute agent coordination.

        Args:
            input_data: Task data to distribute to agents
            context: Current workflow context

        Returns:
            Coordinated results from all agents

        Raises:
            ValueError: If coordination strategy is invalid
            RuntimeError: If require_all_success=True and any agent fails
        """
        import asyncio
        import time

        # Validate strategy
        valid_strategies = ["aggregate", "first", "consensus"]
        if self.coordination_strategy not in valid_strategies:
            raise ValueError(
                f"Invalid coordination_strategy: {self.coordination_strategy}. "
                f"Must be one of {valid_strategies}"
            )

        # Record start
        start_time = time.time()
        context.checkpoint("agent_coordination_start")

        # Create child contexts for each agent
        agent_contexts = {}
        for agent_name in self.agent_primitives:
            child_context = context.create_child_context()
            child_context.metadata["current_agent"] = agent_name
            child_context.metadata["coordination_id"] = context.correlation_id
            agent_contexts[agent_name] = child_context

        # Execute agents in parallel
        agent_tasks = []
        for agent_name, primitive in self.agent_primitives.items():
            task = primitive.execute(input_data, agent_contexts[agent_name])
            agent_tasks.append((agent_name, task))

        # Wait for completion with optional timeout
        agent_results = {}
        failed_agents = []

        if self.timeout_seconds:
            try:
                completed = await asyncio.wait_for(
                    asyncio.gather(*[task for _, task in agent_tasks], return_exceptions=True),
                    timeout=self.timeout_seconds,
                )
                for i, (agent_name, _) in enumerate(agent_tasks):
                    result = completed[i]
                    if isinstance(result, Exception):
                        failed_agents.append(agent_name)
                        agent_results[agent_name] = {"error": str(result)}
                    else:
                        agent_results[agent_name] = result
            except TimeoutError:
                failed_agents = list(self.agent_primitives.keys())
                agent_results = {name: {"error": "timeout"} for name in failed_agents}
        else:
            # No timeout
            completed = await asyncio.gather(
                *[task for _, task in agent_tasks], return_exceptions=True
            )
            for i, (agent_name, _) in enumerate(agent_tasks):
                result = completed[i]
                if isinstance(result, Exception):
                    failed_agents.append(agent_name)
                    agent_results[agent_name] = {"error": str(result)}
                else:
                    agent_results[agent_name] = result

        # Check if all required to succeed
        if self.require_all_success and failed_agents:
            raise RuntimeError(
                f"Agent coordination failed: {len(failed_agents)} agents failed: {failed_agents}"
            )

        # Calculate timing
        elapsed_ms = (time.time() - start_time) * 1000
        context.checkpoint("agent_coordination_end")

        # Aggregate results based on strategy
        if self.coordination_strategy == "aggregate":
            aggregated_result = self._aggregate_results(agent_results, failed_agents)
        elif self.coordination_strategy == "first":
            aggregated_result = self._first_success_result(agent_results, failed_agents)
        else:  # consensus
            aggregated_result = self._consensus_result(agent_results, failed_agents)

        # Build coordination metadata
        coordination_metadata = {
            "total_agents": len(self.agent_primitives),
            "successful_agents": len(agent_results) - len(failed_agents),
            "failed_agents": len(failed_agents),
            "failed_agent_names": failed_agents,
            "elapsed_ms": elapsed_ms,
            "strategy": self.coordination_strategy,
            "coordination_id": context.correlation_id,
        }

        # Update context
        context.metadata["agent_coordination"] = coordination_metadata

        return {
            "agent_results": agent_results,
            "coordination_metadata": coordination_metadata,
            "aggregated_result": aggregated_result,
            "failed_agents": failed_agents,
            "input_data": input_data,
        }

    def _aggregate_results(
        self, agent_results: dict[str, Any], failed_agents: list[str]
    ) -> dict[str, Any]:
        """Aggregate all successful agent results."""
        successful_results = {
            name: result for name, result in agent_results.items() if name not in failed_agents
        }
        return {
            "strategy": "aggregate",
            "results": successful_results,
            "summary": f"{len(successful_results)} agents completed successfully",
        }

    def _first_success_result(
        self, agent_results: dict[str, Any], failed_agents: list[str]
    ) -> dict[str, Any]:
        """Return the first successful agent result."""
        for name, result in agent_results.items():
            if name not in failed_agents:
                return {
                    "strategy": "first",
                    "result": result,
                    "agent": name,
                    "summary": f"First successful agent: {name}",
                }

        return {
            "strategy": "first",
            "result": None,
            "agent": None,
            "summary": "No agents succeeded",
        }

    def _consensus_result(
        self, agent_results: dict[str, Any], failed_agents: list[str]
    ) -> dict[str, Any]:
        """Find consensus among agent results (simple majority)."""
        from collections import Counter

        # Get successful results
        successful_results = [
            str(result) for name, result in agent_results.items() if name not in failed_agents
        ]

        if not successful_results:
            return {
                "strategy": "consensus",
                "result": None,
                "consensus": False,
                "summary": "No agents succeeded",
            }

        # Find most common result
        counter = Counter(successful_results)
        most_common = counter.most_common(1)[0]
        consensus_result, count = most_common

        return {
            "strategy": "consensus",
            "result": consensus_result,
            "consensus": count > len(successful_results) / 2,
            "vote_count": count,
            "total_votes": len(successful_results),
            "summary": f"Consensus: {count}/{len(successful_results)} agents agreed",
        }
