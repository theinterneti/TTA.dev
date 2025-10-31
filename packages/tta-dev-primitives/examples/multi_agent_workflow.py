from __future__ import annotations

"""
Multi-Agent Coordination Pattern Example

This example demonstrates building a multi-agent workflow using TTA.dev primitives.

Features:
 - Task decomposition by coordinator agent
 - Parallel execution by specialist agents
 - Result aggregation and synthesis
 - Error handling across agents
 - Agent coordination metrics

Usage:
    python packages/tta-dev-primitives/examples/multi_agent_workflow.py
"""

import asyncio
from typing import Any

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.observability import InstrumentedPrimitive

# ------------------------------------------------------------------------------
# Coordinator Agent
# ------------------------------------------------------------------------------


class CoordinatorAgentPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Analyze task and decompose into subtasks for specialist agents."""

    def __init__(self) -> None:
        super().__init__(name="coordinator_agent")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        task = input_data.get("task", "")
        # Simulate lightweight analysis
        await asyncio.sleep(0.05)

        subtasks = [
            {
                "agent": "data_analyst",
                "task": f"Analyze data patterns in: {task}",
                "priority": "high",
            },
            {
                "agent": "researcher",
                "task": f"Gather background info on: {task}",
                "priority": "medium",
            },
            {
                "agent": "fact_checker",
                "task": f"Verify key claims for: {task}",
                "priority": "low",
            },
            {
                "agent": "summarizer",
                "task": f"Summarize findings for: {task}",
                "priority": "low",
            },
        ]

        return {"subtasks": subtasks, "task_id": input_data.get("task_id", "t1")}


# ------------------------------------------------------------------------------
# Specialist Agents
# ------------------------------------------------------------------------------


class DataAnalystAgentPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Analyze data and return insights."""

    def __init__(self) -> None:
        super().__init__(name="data_analyst_agent")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        await asyncio.sleep(0.08)
        task = input_data.get("task", "")
        return {
            "agent": "data_analyst",
            "status": "success",
            "output": f"insights for [{task}]",
        }


class ResearcherAgentPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Gather information and generate findings."""

    def __init__(self) -> None:
        super().__init__(name="researcher_agent")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        await asyncio.sleep(0.12)
        task = input_data.get("task", "")
        return {
            "agent": "researcher",
            "status": "success",
            "output": f"references for [{task}]",
        }


class FactCheckerAgentPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Verify facts and cross-check sources."""

    def __init__(self) -> None:
        super().__init__(name="fact_checker_agent")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        await asyncio.sleep(0.06)
        task = input_data.get("task", "")
        verified = True
        return {
            "agent": "fact_checker",
            "status": "success",
            "output": f"verified={verified} for [{task}]",
        }


class SummarizerAgentPrimitive(InstrumentedPrimitive[dict[str, Any], dict[str, Any]]):
    """Synthesize information into a concise summary."""

    def __init__(self) -> None:
        super().__init__(name="summarizer_agent")

    async def _execute_impl(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        await asyncio.sleep(0.04)
        task = input_data.get("task", "")
        return {
            "agent": "summarizer",
            "status": "success",
            "output": f"summary for [{task}]",
        }


# ------------------------------------------------------------------------------
# Aggregator
# ------------------------------------------------------------------------------


class AggregatorAgentPrimitive(
    InstrumentedPrimitive[list[dict[str, Any]], dict[str, Any]]
):
    """Combine results from multiple agents into coherent output."""

    def __init__(self) -> None:
        super().__init__(name="aggregator_agent")

    async def _execute_impl(
        self, input_data: list[dict[str, Any]], context: WorkflowContext
    ) -> dict[str, Any]:
        # input_data is a list of agent outputs
        await asyncio.sleep(0.02)
        results = [r for r in input_data if r.get("status") == "success"]
        combined = {r.get("agent"): r.get("output") for r in results}
        return {"status": "complete", "results": combined}


# ------------------------------------------------------------------------------
# Workflow runner (simple orchestration)
# ------------------------------------------------------------------------------


async def demo_multi_agent() -> None:
    print("\n" + "=" * 80)
    print("DEMO: Multi-Agent Coordination")
    print("=" * 80)

    coordinator = CoordinatorAgentPrimitive()
    data_analyst = DataAnalystAgentPrimitive()
    researcher = ResearcherAgentPrimitive()
    fact_checker = FactCheckerAgentPrimitive()
    summarizer = SummarizerAgentPrimitive()
    aggregator = AggregatorAgentPrimitive()

    context = WorkflowContext(correlation_id="multi-demo-1", metadata={})

    # Step 1: Coordinator decomposes task
    coord_out = await coordinator._execute_impl(
        {"task": "Analyze quarterly metrics", "task_id": "task-42"}, context
    )
    subtasks = coord_out.get("subtasks", [])

    # Step 2: Dispatch subtasks to appropriate agents
    coroutines = []
    for st in subtasks:
        agent = st["agent"]
        if agent == "data_analyst":
            coroutines.append(data_analyst._execute_impl({"task": st["task"]}, context))
        elif agent == "researcher":
            coroutines.append(researcher._execute_impl({"task": st["task"]}, context))
        elif agent == "fact_checker":
            coroutines.append(fact_checker._execute_impl({"task": st["task"]}, context))
        elif agent == "summarizer":
            coroutines.append(summarizer._execute_impl({"task": st["task"]}, context))

    # Run in parallel and collect outputs
    outputs = await asyncio.gather(*coroutines)

    # Aggregate results
    agg_result = await aggregator._execute_impl(outputs, context)

    print("\nMulti-agent orchestration result:")
    print(agg_result)
    print("\n")


if __name__ == "__main__":
    asyncio.run(demo_multi_agent())
