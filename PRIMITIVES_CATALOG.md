"""Sequential workflow primitive composition."""

from __future__ import annotations

import time
from typing import Any

from ..observability.enhanced_collector import get_enhanced_metrics_collector
from ..observability.instrumented_primitive import TRACING_AVAILABLE, InstrumentedPrimitive
from ..observability.logging import get_logger
from .base import WorkflowContext, WorkflowPrimitive

logger = get_logger(__name__)


class SequentialPrimitive(InstrumentedPrimitive[Any, Any]):
    """
    Execute primitives in sequence.

    Each primitive's output becomes the next primitive's input.

    Example:
        ```python
workflow = SequentialPrimitive([
            input_processing,
            world_building,
            narrative_generation
        ])
        # Or use >> operator:
        workflow = input_processing >> world_building >> narrative_generation
```
    """

    def __init__(self, primitives: list[WorkflowPrimitive]) -> None:
        """
        Initialize with a list of primitives.

        Args:
            primitives: List of primitives to execute in order
        """
        if not primitives:
            raise ValueError("SequentialPrimitive requires at least one primitive")
        self.primitives = primitives
        # Initialize InstrumentedPrimitive with name
        super().__init__(name="SequentialPrimitive")

    async def _execute_impl(self, input_data: Any, context: WorkflowContext) -> Any:
        """
        Execute primitives sequentially with step-level instrumentation.

        This method provides comprehensive observability for each step:
        - Creates child spans for each step execution
        - Logs step start/completion with timing
        - Records per-step metrics (duration, success/failure)
        - Tracks checkpoints for timing analysis

        Args:
            input_data: Initial input data
            context: Workflow context

        Returns:
            Output from the last primitive

        Raises:
            Exception: If any primitive fails
        """
        metrics_collector = get_enhanced_metrics_collector()

        # Log workflow start
        logger.info(
            "sequential_workflow_start",
            step_count=len(self.primitives),
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        result = input_data
        for i, primitive in enumerate(self.primitives):
            step_name = f"step_{i}_{primitive.__class__.__name__}"

            # Log step start
            logger.info(
                "sequential_step_start",
                step=i,
                total_steps=len(self.primitives),
                primitive_type=primitive.__class__.__name__,
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

            # Record checkpoint
            context.checkpoint(f"sequential.step_{i}.start")
            step_start_time = time.time()

            # Create step span (if tracing available)
            if self._tracer and TRACING_AVAILABLE:
                with self._tracer.start_as_current_span(f"sequential.step_{i}") as span:
                    span.set_attribute("step.index", i)
                    span.set_attribute("step.name", step_name)
                    span.set_attribute("step.primitive_type", primitive.__class__.__name__)
                    span.set_attribute("step.total_steps", len(self.primitives))

                    try:
                        result = await primitive.execute(result, context)
                        span.set_attribute("step.status", "success")
                    except Exception as e:
                        span.set_attribute("step.status", "error")
                        span.set_attribute("step.error", str(e))
                        span.record_exception(e)
                        raise
            else:
                # Graceful degradation - execute without step span
                result = await primitive.execute(result, context)

            # Record checkpoint and metrics
            context.checkpoint(f"sequential.step_{i}.end")
            step_duration_ms = (time.time() - step_start_time) * 1000
            metrics_collector.record_execution(
                f"{self.name}.step_{i}", duration_ms=step_duration_ms, success=True
            )

            # Log step completion
            logger.info(
                "sequential_step_complete",
                step=i,
                total_steps=len(self.primitives),
                primitive_type=primitive.__class__.__name__,
                duration_ms=step_duration_ms,
                elapsed_ms=context.elapsed_ms(),
                workflow_id=context.workflow_id,
                correlation_id=context.correlation_id,
            )

        # Log workflow completion
        logger.info(
            "sequential_workflow_complete",
            step_count=len(self.primitives),
            total_duration_ms=context.elapsed_ms(),
            workflow_id=context.workflow_id,
            correlation_id=context.correlation_id,
        )

        return result

    def __rshift__(self, other: WorkflowPrimitive) -> SequentialPrimitive:
        """
        Chain another primitive: self >> other.

        Optimizes by flattening nested sequential primitives.

        Args:
            other: Primitive to append

        Returns:
            A new sequential primitive with all steps
        """
        if isinstance(other, SequentialPrimitive):
            # Flatten nested sequential primitives
            return SequentialPrimitive(self.primitives + other.primitives)
        else:
            return SequentialPrimitive(self.primitives + [other])
elf, input_data: dict[str, Any], context: WorkflowContext) -> dict[str, Any]:
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
"""Agent memory primitive for storing and retrieving architectural decisions.

This primitive provides a structured way to store, retrieve, and query
architectural decisions and important context across agent interactions.
"""

from typing import Any

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class AgentMemoryPrimitive(WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """Store and retrieve architectural decisions in agent memory.

    This primitive manages a persistent memory system for tracking architectural
    decisions, patterns, and important context that should be preserved across
    agent sessions and workflow executions.

    Args:
        operation: Operation type ("store", "retrieve", "query", "list")
        memory_key: Optional key for store/retrieve operations
        memory_store: Optional external memory store (defaults to context.metadata)
        memory_scope: Scope for memory ("workflow", "session", "global")

    Example:
        ```python
from universal_agent_context.primitives import AgentMemoryPrimitive

        # Store decision
        store_decision = AgentMemoryPrimitive(
            operation="store",
            memory_key="architecture_choice",
            memory_scope="session"
        )

        # Retrieve decision later
        retrieve_decision = AgentMemoryPrimitive(
            operation="retrieve",
            memory_key="architecture_choice"
        )

        # Use in workflow
        workflow = (
            analyze_requirements >>
            store_decision >>  # Store architectural decision
            implement_solution >>
            retrieve_decision  # Recall decision for validation
        )
```

    Memory Structure:
        Each memory entry contains:
        - key: Unique identifier
        - value: Stored data
        - timestamp: When stored
        - agent: Which agent stored it
        - scope: Memory scope
        - tags: Optional metadata tags
    """

    def __init__(
        self,
        operation: str,
        memory_key: str | None = None,
        memory_store: dict[str, Any] | None = None,
        memory_scope: str = "workflow",
        name: str | None = None,
    ) -> None:
        """Initialize agent memory primitive.

        Args:
            operation: "store", "retrieve", "query", or "list"
            memory_key: Key for store/retrieve operations
            memory_store: External memory store (defaults to context.metadata)
            memory_scope: "workflow", "session", or "global"
            name: Optional name for the primitive
        """
        self.name = name or f"AgentMemory-{operation}"
        self.operation = operation
        self.memory_key = memory_key
        self.memory_store = memory_store
        self.memory_scope = memory_scope

    async def execute(self, input_data: dict[str, Any], context: WorkflowContext) -> dict[str, Any]:
        """Execute memory operation.

        Args:
            input_data: Operation parameters
            context: Current workflow context

        Returns:
            Result of memory operation

        Raises:
            ValueError: If operation is invalid or required params missing
        """
        import time

        # Validate operation
        valid_operations = ["store", "retrieve", "query", "list"]
        if self.operation not in valid_operations:
            raise ValueError(
                f"Invalid operation: {self.operation}. Must be one of {valid_operations}"
            )

        # Get memory store (use external or context.metadata)
        memory_store = self.memory_store if self.memory_store is not None else context.metadata

        # Initialize agent_memory if not present
        if "agent_memory" not in memory_store:
            memory_store["agent_memory"] = {}

        agent_memory = memory_store["agent_memory"]

        # Get current agent
        current_agent = context.metadata.get("current_agent", "unknown")

        # Execute operation
        if self.operation == "store":
            return await self._store_memory(input_data, context, agent_memory, current_agent)
        elif self.operation == "retrieve":
            return await self._retrieve_memory(input_data, context, agent_memory)
        elif self.operation == "query":
            return await self._query_memory(input_data, context, agent_memory)
        else:  # list
            return await self._list_memory(input_data, context, agent_memory)

    async def _store_memory(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext,
        agent_memory: dict[str, Any],
        current_agent: str,
    ) -> dict[str, Any]:
        """Store a memory entry."""
        import time

        # Get memory key (from init or input_data)
        key = self.memory_key or input_data.get("memory_key")
        if not key:
            raise ValueError("memory_key required for store operation")

        # Get value to store
        value = input_data.get("memory_value") or input_data.get("value")
        if value is None:
            raise ValueError("memory_value or value required for store operation")

        # Create memory entry
        memory_entry = {
            "key": key,
            "value": value,
            "timestamp": time.time(),
            "agent": current_agent,
            "scope": self.memory_scope,
            "tags": input_data.get("tags", {}),
            "workflow_id": context.workflow_id,
            "correlation_id": context.correlation_id,
        }

        # Store in appropriate scope
        scope_key = f"{self.memory_scope}_memories"
        if scope_key not in agent_memory:
            agent_memory[scope_key] = {}

        agent_memory[scope_key][key] = memory_entry

        # Add checkpoint
        context.checkpoint(f"memory_stored_{key}")

        return {
            **input_data,
            "memory_operation": "store",
            "memory_key": key,
            "memory_stored": True,
            "memory_scope": self.memory_scope,
        }

    async def _retrieve_memory(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext,
        agent_memory: dict[str, Any],
    ) -> dict[str, Any]:
        """Retrieve a memory entry."""
        # Get memory key
        key = self.memory_key or input_data.get("memory_key")
        if not key:
            raise ValueError("memory_key required for retrieve operation")

        # Try to retrieve from scope
        scope_key = f"{self.memory_scope}_memories"
        memory_entry = agent_memory.get(scope_key, {}).get(key)

        if memory_entry is None:
            # Try other scopes if not found
            for scope in ["workflow", "session", "global"]:
                scope_key = f"{scope}_memories"
                memory_entry = agent_memory.get(scope_key, {}).get(key)
                if memory_entry:
                    break

        # Add checkpoint
        context.checkpoint(f"memory_retrieved_{key}")

        return {
            **input_data,
            "memory_operation": "retrieve",
            "memory_key": key,
            "memory_value": memory_entry.get("value") if memory_entry else None,
            "memory_entry": memory_entry,
            "memory_found": memory_entry is not None,
        }

    async def _query_memory(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext,
        agent_memory: dict[str, Any],
    ) -> dict[str, Any]:
        """Query memory entries by tags or filters."""
        query_tags = input_data.get("query_tags", {})
        query_agent = input_data.get("query_agent")

        # Get memories from scope
        scope_key = f"{self.memory_scope}_memories"
        memories = agent_memory.get(scope_key, {})

        # Filter by query criteria
        results = []
        for key, entry in memories.items():
            # Filter by agent if specified
            if query_agent and entry.get("agent") != query_agent:
                continue

            # Filter by tags if specified
            if query_tags:
                entry_tags = entry.get("tags", {})
                if not all(entry_tags.get(k) == v for k, v in query_tags.items()):
                    continue

            results.append(entry)

        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

        return {
            **input_data,
            "memory_operation": "query",
            "query_results": results,
            "result_count": len(results),
        }

    async def _list_memory(
        self,
        input_data: dict[str, Any],
        context: WorkflowContext,
        agent_memory: dict[str, Any],
    ) -> dict[str, Any]:
        """List all memory entries in scope."""
        scope_key = f"{self.memory_scope}_memories"
        memories = agent_memory.get(scope_key, {})

        # Convert to list and sort by timestamp
        memory_list = list(memories.values())
        memory_list.sort(key=lambda x: x.get("timestamp", 0), reverse=True)

        return {
            **input_data,
            "memory_operation": "list",
            "memories": memory_list,
            "memory_count": len(memory_list),
            "memory_scope": self.memory_scope,
        }
"""Agent handoff primitive for transferring tasks between agents.

This primitive enables smooth handoffs of tasks and context from one AI agent
to another, ensuring continuity and preserving important context during
multi-agent workflows.
"""

from typing import Any

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class AgentHandoffPrimitive(WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """Hand off task execution from one agent to another.

    This primitive manages the transfer of context, state, and execution
    responsibility from one agent to another in a multi-agent workflow.

    Args:
        target_agent: Name/identifier of the target agent
        handoff_strategy: Strategy for handoff ("immediate", "queued", "conditional")
        preserve_context: Whether to preserve full context or just essentials
        handoff_callback: Optional async callback invoked during handoff

    Example:
        ```python
from universal_agent_context.primitives import AgentHandoffPrimitive

        # Create handoff to specialist agent
        handoff = AgentHandoffPrimitive(
            target_agent="data_analyst",
            handoff_strategy="immediate",
            preserve_context=True
        )

        # Use in workflow
        workflow = (
            initial_processing >>
            handoff >>  # Handoff to data_analyst
            specialized_analysis
        )
```

    Context Updates:
        - Adds "agent_history" list tracking all agents in workflow
        - Adds "handoff_timestamp" for each handoff
        - Adds "handoff_reason" explaining why handoff occurred
        - Updates "current_agent" to target agent name
    """

    def __init__(
        self,
        target_agent: str,
        handoff_strategy: str = "immediate",
        preserve_context: bool = True,
        handoff_callback: Any = None,
        name: str | None = None,
    ) -> None:
        """Initialize agent handoff primitive.

        Args:
            target_agent: Name/identifier of the target agent
            handoff_strategy: "immediate", "queued", or "conditional"
            preserve_context: Whether to preserve full context
            handoff_callback: Optional callback for custom handoff logic
            name: Optional name for the primitive (defaults to "AgentHandoff")
        """
        self.name = name or f"AgentHandoff->{target_agent}"
        self.target_agent = target_agent
        self.handoff_strategy = handoff_strategy
        self.preserve_context = preserve_context
        self.handoff_callback = handoff_callback

    async def execute(self, input_data: dict[str, Any], context: WorkflowContext) -> dict[str, Any]:
        """Execute agent handoff.

        Args:
            input_data: Task data to hand off
            context: Current workflow context

        Returns:
            Enriched data with handoff metadata

        Raises:
            ValueError: If handoff strategy is invalid
        """
        import time

        # Validate strategy
        valid_strategies = ["immediate", "queued", "conditional"]
        if self.handoff_strategy not in valid_strategies:
            raise ValueError(
                f"Invalid handoff_strategy: {self.handoff_strategy}. "
                f"Must be one of {valid_strategies}"
            )

        # Get current agent from context or default
        current_agent = context.metadata.get("current_agent", "unknown")

        # Initialize or update agent history
        agent_history = context.metadata.get("agent_history", [])
        agent_history.append(
            {
                "from_agent": current_agent,
                "to_agent": self.target_agent,
                "timestamp": time.time(),
                "strategy": self.handoff_strategy,
            }
        )

        # Update context with handoff info
        context.metadata["agent_history"] = agent_history
        context.metadata["current_agent"] = self.target_agent
        context.metadata["handoff_timestamp"] = time.time()
        context.metadata["handoff_reason"] = input_data.get(
            "handoff_reason",
            f"Workflow transition from {current_agent} to {self.target_agent}",
        )

        # Add handoff checkpoint
        context.checkpoint(f"handoff_to_{self.target_agent}")

        # Prepare handoff data
        handoff_data = {
            **input_data,
            "handoff_metadata": {
                "from_agent": current_agent,
                "to_agent": self.target_agent,
                "strategy": self.handoff_strategy,
                "timestamp": time.time(),
                "context_preserved": self.preserve_context,
            },
        }

        # If not preserving full context, trim to essentials
        if not self.preserve_context:
            handoff_data = {
                "task": input_data.get("task"),
                "essential_context": input_data.get("essential_context", {}),
                "handoff_metadata": handoff_data["handoff_metadata"],
            }

        # Execute custom handoff callback if provided
        if self.handoff_callback:
            handoff_data = await self.handoff_callback(
                handoff_data, context, current_agent, self.target_agent
            )

        # Log handoff
        context.tags[f"handoff_{self.target_agent}"] = True

        return handoff_data
# TTA.dev Component Integration Analysis

**Analysis of how all components integrate with agentic primitives workflow**

**Date:** October 29, 2025
**Branch:** feature/observability-phase-1-trace-context
**Purpose:** Identify integration points and gaps across TTA.dev ecosystem

---

## Executive Summary

### 🎯 Analysis Scope

This document analyzes how TTA.dev's components integrate with the **agentic primitives workflow** (tta-dev-primitives package) and identifies integration gaps.

### 📊 Integration Health Score

**Overall:** 7.5/10 ⭐⭐⭐⭐⭐⭐⭐☆☆☆

| Component | Integration | Gaps | Score |
|-----------|-------------|------|-------|
| tta-observability-integration | ✅ Excellent | Minor documentation | 9/10 |
| universal-agent-context | ⚠️ Partial | No direct primitive usage | 5/10 |
| keploy-framework | ⚠️ Minimal | Standalone, no integration | 4/10 |
| python-pathway | ⚠️ Minimal | Utility only | 4/10 |
| VS Code Toolsets | ✅ Good | Recently added | 8/10 |
| MCP Servers | ✅ Good | Documentation complete | 8/10 |
| CI/CD (GitHub Actions) | ✅ Good | Codecov integration exists | 8/10 |
| Testing Infrastructure | ✅ Excellent | MockPrimitive well-used | 9/10 |

---

## 1. tta-observability-integration

### Integration Status: ✅ **EXCELLENT** (9/10)

### How It Integrates

#### 1.1 Direct Primitive Integration

**Pattern:** Extends `WorkflowPrimitive` base class

```python
# From: packages/tta-observability-integration/src/observability_integration/primitives/
from tta_dev_primitives.core.base import WorkflowPrimitive, WorkflowContext

class CachePrimitive(WorkflowPrimitive[Any, Any]):
    """Cache primitive with observability"""

class RouterPrimitive(WorkflowPrimitive[Any, Any]):
    """Router primitive with observability"""

class TimeoutPrimitive(WorkflowPrimitive[Any, Any]):
    """Timeout primitive with observability"""
```

**Integration Points:**

- ✅ Uses `WorkflowPrimitive` base class
- ✅ Accepts `WorkflowContext` for state management
- ✅ Composable via `>>` and `|` operators
- ✅ Implements `_execute_impl()` pattern

#### 1.2 Observability Layer

**Pattern:** Wraps primitives with OpenTelemetry

```python
# From: packages/tta-dev-primitives/src/tta_dev_primitives/observability/
class InstrumentedPrimitive(WorkflowPrimitive[T, U]):
    """Auto-instrumented primitive with tracing"""

class ObservablePrimitive(WorkflowPrimitive[Any, Any]):
    """Wrapper adding observability to any primitive"""
```

**Integration Points:**

- ✅ Automatic span creation
- ✅ Metrics collection (execution time, success rate)
- ✅ Trace context propagation via `WorkflowContext`
- ✅ Graceful degradation when OpenTelemetry unavailable

#### 1.3 APM Setup

**Pattern:** Initialize observability early in application lifecycle

```python
# From: packages/tta-observability-integration/src/observability_integration/apm_setup.py
def initialize_observability(
    service_name: str = "tta",
    enable_prometheus: bool = True,
    prometheus_port: int = 9464,
) -> bool:
    """Initialize OpenTelemetry tracing and metrics"""
```

**Usage Pattern:**

```python
# In main.py or application entry point
from observability_integration import initialize_observability

success = initialize_observability(
    service_name="tta",
    enable_prometheus=True
)

# Then use primitives
from observability_integration.primitives import RouterPrimitive, CachePrimitive

workflow = (
    input_step >>
    RouterPrimitive(routes={"fast": llm1, "quality": llm2}) >>
    CachePrimitive(expensive_operation, ttl_seconds=3600) >>
    output_step
)
```

### Strengths ✅

1. **Full WorkflowPrimitive Compatibility**
   - All observability primitives extend `WorkflowPrimitive`
   - Composable with other primitives via operators
   - Type-safe with generics

2. **Dual-Package Architecture**
   - Core observability in `tta-dev-primitives/observability/`
   - Enhanced primitives in `tta-observability-integration/primitives/`
   - Clear separation of concerns

3. **Production-Ready Features**
   - 30-40% cost reduction (Cache + Router)
   - Prometheus metrics export
   - OpenTelemetry distributed tracing
   - Graceful degradation

4. **Examples and Documentation**
   - `packages/tta-dev-primitives/examples/apm_example.py`
   - `packages/tta-dev-primitives/examples/observability_demo.py`
   - Complete API documentation

### Gaps ⚠️

1. **Documentation Discoverability**
   - ❌ Observability integration not prominent in root AGENTS.md
   - ⚠️ APM setup steps not in quick start
   - Solution: Add observability section to AGENTS.md

2. **Package Naming Confusion**
   - ⚠️ Observability code in two places:
     - `tta-dev-primitives/observability/` (core)
     - `tta-observability-integration/` (enhanced)
   - Solution: Document the split clearly in PRIMITIVES_CATALOG.md

3. **Testing Coverage**
   - ⚠️ Core observability features in tta-dev-primitives are untested
   - ✅ Enhanced primitives in tta-observability-integration have tests
   - Solution: Add tests to `tta-dev-primitives/tests/observability/`

### Recommendations

1. **Improve Discoverability**

   ```markdown
# Add to AGENTS.md

## Observability

   All primitives have built-in observability:

- Use `InstrumentedPrimitive` for automatic tracing
- Initialize with `initialize_observability()` from tta-observability-integration
- Export metrics to Prometheus on port 9464
```

2. **Consolidate Documentation**
   ```markdown
# Add to PRIMITIVES_CATALOG.md
   ## Observability Primitives

   ### Core (tta-dev-primitives)
   - InstrumentedPrimitive - Base class with auto-tracing
   - ObservablePrimitive - Wrapper for existing primitives

   ### Enhanced (tta-observability-integration)
   - CachePrimitive - Cache with metrics
   - RouterPrimitive - Route with metrics
   - TimeoutPrimitive - Timeout with metrics
```

3. **Add Test Coverage**

   ```bash
# Create missing tests

   packages/tta-dev-primitives/tests/observability/
   ├── test_instrumented_primitive.py
   ├── test_observable_primitive.py
   ├── test_metrics_collector.py
   └── test_context_propagation.py
```

---

## 2. universal-agent-context

### Integration Status: ⚠️ **PARTIAL** (5/10)

### How It Integrates

#### 2.1 Context Management

**Pattern:** Provides agent context and instructions

```
packages/universal-agent-context/
├── .augment/              # Augment CLI-specific
│   ├── instructions.md    # Agent instructions
│   ├── chatmodes/         # Role-based modes
│   └── memory/            # Decision tracking
├── .github/               # Cross-platform
│   ├── instructions/      # Modular instructions
│   └── chatmodes/         # Universal chat modes
└── AGENTS.md              # Agent coordination guide
```

**Purpose:** Provide sophisticated context management for AI agents

#### 2.2 Current Integration

**With Primitives:** ⚠️ **MINIMAL**

- ❌ Does NOT use `WorkflowPrimitive` base class
- ❌ Does NOT provide primitive-based coordination
- ❌ No composition operators
- ✅ Provides instructions for agents working with primitives

**Integration Type:** **Documentation-only**

The universal-agent-context package provides:
- Agent personality (Augster identity)
- Chat modes for different tasks
- Memory system for decisions
- BUT: No code integration with primitives

### Strengths ✅

1. **Comprehensive Agent Guidance**
   - 16 traits, 13 maxims, 3 protocols (Augster)
   - Role-based chat modes
   - Architectural decision memory

2. **Cross-Platform Support**
   - Works with Claude, Gemini, Copilot, Augment
   - YAML frontmatter for selective loading
   - Security levels defined

3. **Modular Instructions**
   - Domain-specific guidelines
   - Pattern-based loading
   - MCP tool access controls

### Gaps ⚠️

1. **No Primitive Integration**
   - ❌ Package doesn't use `WorkflowPrimitive`
   - ❌ No agent coordination primitives
   - ❌ Context management not available as primitive

   **Impact:** Agents can't compose agent coordination as part of workflows

2. **Separate Ecosystem**
   - ⚠️ Lives in separate directory structure
   - ⚠️ No cross-referencing with tta-dev-primitives
   - ⚠️ Not mentioned in PRIMITIVES_CATALOG.md

3. **Missing Integration Patterns**
   - ❌ No example of using agent context with primitives
   - ❌ No workflow showing multi-agent coordination
   - ❌ No primitive for agent handoff or delegation

### Recommendations

#### 2.1 Create Agent Coordination Primitives

```python
# NEW: packages/universal-agent-context/src/universal_agent_context/primitives/

from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class AgentHandoffPrimitive(WorkflowPrimitive[dict, dict]):
    """Hand off task from one agent to another"""

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        # Load target agent context
        # Pass data to target agent
        # Track handoff in memory
        ...

class AgentMemoryPrimitive(WorkflowPrimitive[dict, dict]):
    """Store/retrieve architectural decisions"""

class AgentCoordinationPrimitive(WorkflowPrimitive[list[dict], dict]):
    """Coordinate multiple agents in parallel"""
```

#### 2.2 Add Integration Examples

```python
# NEW: packages/universal-agent-context/examples/primitive_integration.py

from tta_dev_primitives import SequentialPrimitive, ParallelPrimitive
from universal_agent_context.primitives import AgentHandoffPrimitive, AgentMemoryPrimitive

# Example: Multi-agent workflow with memory
workflow = (
    agent1_task >>
    AgentMemoryPrimitive(decision="architecture_choice") >>
    AgentHandoffPrimitive(target_agent="agent2") >>
    agent2_task
)
```

#### 2.3 Update Documentation

```markdown
# Add to AGENTS.md
## Multi-Agent Coordination

TTA.dev supports multi-agent workflows via universal-agent-context:

- `AgentHandoffPrimitive` - Hand off tasks between agents
- `AgentMemoryPrimitive` - Share context via architectural memory
- `AgentCoordinationPrimitive` - Parallel agent execution

See: packages/universal-agent-context/AGENTS.md
```

### Priority: **HIGH**

Agent coordination is a core use case for TTA.dev. Adding primitive-based coordination would:

- Enable composable multi-agent workflows
- Provide type-safe agent handoffs
- Integrate agent memory with observability
- Make agent patterns reusable

---

## 3. keploy-framework

### Integration Status: ⚠️ **MINIMAL** (4/10)

### How It Integrates

**Current State:** Standalone API testing framework

```
packages/keploy-framework/
└── src/keploy_framework/
    ├── cli.py          # CLI for recording/replaying
    ├── recorder.py     # API recording
    └── replay.py       # API replay
```

**Purpose:** Record and replay API interactions for testing

#### Integration Points

**With Primitives:** ❌ **NONE**

- Does NOT use `WorkflowPrimitive`
- Does NOT integrate with workflow execution
- Standalone CLI tool

**Integration Type:** **Testing infrastructure only**

### Strengths ✅

1. **API Testing**
   - Records HTTP interactions
   - Replays for testing
   - Helps validate external API integrations

2. **CLI Interface**
   - Easy to use
   - Integrates with pytest
   - Documented usage

### Gaps ⚠️

1. **No Primitive Integration**
   - ❌ Can't use as part of workflow
   - ❌ No `TestingPrimitive` for API mocking
   - ❌ Not composable with other primitives

2. **Limited Primitive Testing**
   - ⚠️ Keploy doesn't test primitives themselves
   - ⚠️ Focus is on external APIs only
   - ⚠️ MockPrimitive is better for primitive testing

3. **Documentation**
   - ❌ Not mentioned in PRIMITIVES_CATALOG.md
   - ❌ Not in AGENTS.md
   - ⚠️ Only has package README

### Recommendations

#### 3.1 Create Keploy Integration Primitive

```python
# NEW: packages/keploy-framework/src/keploy_framework/primitives.py

from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from keploy_framework.recorder import KeployRecorder

class KeployRecordPrimitive(WorkflowPrimitive[dict, dict]):
    """Record API calls during primitive execution"""

    def __init__(self, primitive: WorkflowPrimitive, recording_dir: str):
        self.primitive = primitive
        self.recorder = KeployRecorder(recording_dir)

    async def _execute_impl(
        self,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        with self.recorder.recording():
            return await self.primitive.execute(input_data, context)

class KeployReplayPrimitive(WorkflowPrimitive[dict, dict]):
    """Replay recorded API calls for testing"""
```

#### 3.2 Integration Example

```python
# Example: Testing workflow with API recording

from tta_dev_primitives import SequentialPrimitive
from keploy_framework.primitives import KeployRecordPrimitive

# Wrap workflow for recording
workflow = SequentialPrimitive([
    step1,
    KeployRecordPrimitive(api_call_step, recording_dir="./recordings"),
    step3
])

# Later in tests
from keploy_framework.primitives import KeployReplayPrimitive

test_workflow = SequentialPrimitive([
    step1,
    KeployReplayPrimitive(recording_dir="./recordings"),
    step3
])
```

#### 3.3 Documentation

```markdown
# Add to PRIMITIVES_CATALOG.md
## Testing Primitives

### KeployRecordPrimitive
Record API interactions during workflow execution

### KeployReplayPrimitive
Replay recorded API interactions for testing
```

### Priority: **MEDIUM**

Keploy is useful but less critical than agent coordination. Main value:

- Simplify API testing in workflows
- Record/replay for integration tests
- Complement MockPrimitive

---

## 4. python-pathway

### Integration Status: ⚠️ **MINIMAL** (4/10)

### How It Integrates

**Current State:** Python code analysis utility

```
packages/python-pathway/
└── src/python_pathway/
    ├── analyzer.py     # Code analysis
    └── detector.py     # Pattern detection
```

**Purpose:** Analyze Python code for patterns and issues

#### Integration Points

**With Primitives:** ❌ **NONE**

- Does NOT use `WorkflowPrimitive`
- Standalone utility functions
- No workflow integration

**Integration Type:** **Development tool only**

### Strengths ✅

1. **Code Analysis**
   - Detects Python patterns
   - Helps with refactoring
   - Useful for development

2. **Utility Functions**
   - Can be called from scripts
   - Simple API

### Gaps ⚠️

1. **No Primitive Integration**
   - ❌ Not usable in workflows
   - ❌ No `AnalysisPrimitive`
   - ❌ Not composable

2. **Limited Scope**
   - ⚠️ Minimal functionality
   - ⚠️ Not well-documented
   - ⚠️ Not clear when to use

3. **No Examples**
   - ❌ No integration examples
   - ❌ Not in documentation
   - ❌ Unclear use cases

### Recommendations

#### 4.1 Create Analysis Primitive (Optional)

```python
# Optional: packages/python-pathway/src/python_pathway/primitives.py

from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from python_pathway.analyzer import PythonAnalyzer

class CodeAnalysisPrimitive(WorkflowPrimitive[str, dict]):
    """Analyze Python code for patterns"""

    async def _execute_impl(
        self,
        code: str,
        context: WorkflowContext
    ) -> dict:
        analyzer = PythonAnalyzer()
        return analyzer.analyze(code)
```

#### 4.2 Consider Deprecation

**Alternative:** python-pathway may be better as a standalone tool rather than integrated with primitives.

**Reasoning:**

- Limited use in workflows
- Analysis is typically done statically, not at runtime
- Better suited for pre-commit hooks or CI/CD

### Priority: **LOW**

Python-pathway is less critical for core workflow functionality.

---

## 5. VS Code Toolsets

### Integration Status: ✅ **GOOD** (8/10)

### How It Integrates

**Pattern:** Organize Copilot tools by workflow

```jsonc
// .vscode/copilot-toolsets.jsonc

"tta-package-dev": {
  "tools": [
    "edit", "search", "usages",
    "configurePythonEnvironment",
    "runTests", "runTasks"
  ],
  "description": "TTA.dev package development (primitives, observability)"
}

"tta-observability": {
  "tools": [
    "edit", "search",
    "query_prometheus", "query_loki_logs",
    "list_alert_rules"
  ],
  "description": "TTA.dev observability integration"
}
```

**Purpose:** Optimize Copilot tool usage for different workflows

### Strengths ✅

1. **Workflow-Specific**
   - ✅ Toolsets aligned with primitives
   - ✅ `#tta-package-dev` for primitive development
   - ✅ `#tta-observability` for tracing/metrics
   - ✅ `#tta-agent-dev` for AI agent work

2. **Performance**
   - ✅ Reduces tool count from 130+ to 8-20 per workflow
   - ✅ Faster Copilot responses
   - ✅ More focused suggestions

3. **Documentation**
   - ✅ `.vscode/README.md` explains integration
   - ✅ `docs/guides/copilot-toolsets-guide.md` has examples
   - ✅ MCP_SERVERS.md documents tool usage

### Gaps ⚠️

1. **Recently Added**
   - ⚠️ Created October 29, 2025 (today!)
   - ⚠️ Not yet battle-tested
   - ⚠️ May need iteration

2. **MCP Tool Discovery**
   - ⚠️ Some MCP tool names may be incorrect
   - ⚠️ Requires validation when servers start
   - ⚠️ Error messages not helpful

### Recommendations

1. **Test Toolsets**

   ```bash
# Validate toolsets work as expected

   @workspace #tta-package-dev
   Show me how to create a new primitive

   @workspace #tta-observability
   Show me error rates for the last hour
```

2. **Iterate Based on Usage**
   - Monitor which toolsets are used most
   - Add/remove tools as needed
   - Create new specialized toolsets

3. **Document Best Practices**
   - When to use which toolset
   - How to combine toolsets
   - Common workflows

### Priority: **COMPLETE**

Toolsets are well-integrated and documented. Monitor usage and iterate.

---

## 6. MCP Servers

### Integration Status: ✅ **GOOD** (8/10)

### How It Integrates

**Pattern:** External tools accessible via MCP protocol

```
Available MCP Servers:

1. Context7 - Library documentation
2. AI Toolkit - Agent development guidance
3. Grafana - Prometheus/Loki queries
4. Pylance - Python development tools
5. Database Client - SQL operations
6. GitHub PR - Pull request context
7. Sift/Docker - Investigation analysis
```

**Integration:** Tools accessible in Copilot toolsets

### Strengths ✅

1. **Comprehensive Registry**
   - ✅ MCP_SERVERS.md documents all servers
   - ✅ Usage examples provided
   - ✅ Troubleshooting guide

2. **Toolset Integration**
   - ✅ MCP tools included in toolsets
   - ✅ `#tta-observability` has Grafana tools
   - ✅ `#tta-agent-dev` has Context7, AI Toolkit

3. **Observability**
   - ✅ Grafana MCP provides metrics/logs
   - ✅ Complements tta-observability-integration
   - ✅ Real-time monitoring

### Gaps ⚠️

1. **No Primitive Integration**
   - ❌ MCP tools not accessible from primitives
   - ❌ Can't query Prometheus from workflow
   - ❌ Can't fetch docs programmatically

   **Impact:** Workflows can't leverage MCP capabilities at runtime

2. **Documentation Only**
   - ⚠️ MCP tools for AI agents only
   - ⚠️ Not programmatically accessible
   - ⚠️ No Python API

### Recommendations

#### 6.1 Create MCP Primitive Bridge (Advanced)

```python
# Optional: packages/tta-mcp-integration/src/tta_mcp/primitives.py

from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class MCPQueryPrimitive(WorkflowPrimitive[dict, dict]):
    """Query MCP server from workflow"""

    def __init__(self, server: str, tool: str):
        self.server = server
        self.tool = tool

    async def _execute_impl(
        self,
        query: dict,
        context: WorkflowContext
    ) -> dict:
        # Call MCP server via protocol
        # Return results
        ...

# Example usage
grafana_query = MCPQueryPrimitive(
    server="grafana",
    tool="query_prometheus"
)

workflow = (
    data_processor >>
    grafana_query >>  # Query metrics mid-workflow
    decision_maker
)
```

### Priority: **LOW**

MCP tools are primarily for AI agent assistance, not runtime workflow integration. Current integration is sufficient.

---

## 7. CI/CD (GitHub Actions)

### Integration Status: ✅ **GOOD** (8/10)

### How It Integrates

**Pattern:** Automated testing and quality checks

```yaml
# .github/workflows/quality-check.yml

- name: Run tests with coverage
  run: uv run pytest --cov=packages --cov-report=xml

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

**Workflows:**

1. `ci.yml` - Run tests on PR
2. `quality-check.yml` - Run linting, type checking, coverage
3. `mcp-validation.yml` - Validate MCP configurations
4. `auto-assign-copilot.yml` - Copilot PR reviews

### Strengths ✅

1. **Comprehensive Testing**
   - ✅ Pytest with coverage
   - ✅ Codecov integration
   - ✅ Type checking (Pyright)
   - ✅ Linting (Ruff)

2. **Primitive Testing**
   - ✅ All primitives have tests
   - ✅ MockPrimitive used extensively
   - ✅ Async tests with pytest-asyncio

3. **Quality Gates**
   - ✅ Coverage thresholds enforced
   - ✅ Type checking required
   - ✅ Linting required

### Gaps ⚠️

1. **Missing CODECOV_TOKEN**
   - ⚠️ Secret exists but needs configuration (from user's screenshot)
   - ⚠️ Coverage uploads may fail without proper setup

2. **Observability Testing**
   - ⚠️ Core observability features in tta-dev-primitives untested
   - ✅ Enhanced primitives in tta-observability-integration have tests

3. **Integration Tests**
   - ⚠️ Limited integration tests across packages
   - ⚠️ No end-to-end workflow tests
   - ⚠️ Packages tested in isolation

### Recommendations

1. **Complete Codecov Setup**

   ```yaml
# Ensure CODECOV_TOKEN is properly configured

# Test uploads work

# Set coverage thresholds
```

2. **Add Integration Tests**
   ```bash
# NEW: tests/integration/
   tests/integration/
   ├── test_observability_primitives.py
   ├── test_multi_package_workflow.py
   └── test_agent_coordination.py
```

3. **Add Observability Tests**

   ```bash
# NEW: packages/tta-dev-primitives/tests/observability/

   packages/tta-dev-primitives/tests/observability/
   ├── test_instrumented_primitive.py
   ├── test_observable_primitive.py
   ├── test_metrics_collector.py
   └── test_context_propagation.py
```

### Priority: **MEDIUM**

CI/CD is functional. Main improvements:
- Fix Codecov
- Add missing tests
- Add integration tests

---

## 8. Testing Infrastructure

### Integration Status: ✅ **EXCELLENT** (9/10)

### How It Integrates

**Pattern:** `MockPrimitive` for testing workflows

```python
# From: packages/tta-dev-primitives/src/tta_dev_primitives/testing/mocks.py

from tta_dev_primitives.testing import MockPrimitive

mock_llm = MockPrimitive(
    return_value={"response": "test output"},
    side_effect=None,
    call_delay=0.1
)

workflow = step1 >> mock_llm >> step3
result = await workflow.execute(context, input_data)

assert mock_llm.call_count == 1
```

### Strengths ✅

1. **MockPrimitive Well-Designed**
   - ✅ Extends `WorkflowPrimitive`
   - ✅ Composable with operators
   - ✅ Tracks call count and arguments
   - ✅ Simulates latency
   - ✅ Can raise exceptions

2. **Extensive Test Coverage**
   - ✅ All core primitives tested
   - ✅ All recovery primitives tested
   - ✅ All performance primitives tested
   - ✅ 100% coverage goal

3. **pytest-asyncio Integration**
   - ✅ All async tests use `@pytest.mark.asyncio`
   - ✅ Proper async/await patterns
   - ✅ Context managers tested

4. **Examples**
   - ✅ Tests serve as examples
   - ✅ Clear patterns for new primitives
   - ✅ Documented in PRIMITIVES_CATALOG.md

### Gaps ⚠️

1. **Observability Testing**
   - ❌ Core observability features untested
   - ⚠️ InstrumentedPrimitive has no tests
   - ⚠️ ObservablePrimitive has no tests

2. **Integration Testing**
   - ⚠️ Limited cross-package tests
   - ⚠️ No multi-primitive workflow tests
   - ⚠️ No performance benchmarks

### Recommendations

1. **Add Observability Tests**

   ```python
# NEW: packages/tta-dev-primitives/tests/observability/test_instrumented_primitive.py

   @pytest.mark.asyncio
   async def test_instrumented_primitive_creates_spans():
       """Test that InstrumentedPrimitive creates OpenTelemetry spans"""
       ...
```

2. **Add Integration Tests**
   ```python
# NEW: tests/integration/test_observability_primitives.py

   @pytest.mark.asyncio
   async def test_cache_router_timeout_workflow():
       """Test workflow combining Cache, Router, and Timeout primitives"""
       ...
```

### Priority: **HIGH**

Testing is excellent but needs:

- Observability test coverage
- Integration tests across packages

---

## Summary of Gaps

### 🔴 Critical Gaps

1. **universal-agent-context: No Primitive Integration**
   - Impact: Can't use agent coordination in workflows
   - Solution: Create `AgentHandoffPrimitive`, `AgentMemoryPrimitive`, `AgentCoordinationPrimitive`
   - Priority: HIGH

2. **Observability: No Test Coverage**
   - Impact: Core observability features untested
   - Solution: Add tests to `tta-dev-primitives/tests/observability/`
   - Priority: HIGH

3. **Integration: No Cross-Package Tests**
   - Impact: Don't know if packages work together
   - Solution: Add `tests/integration/` directory
   - Priority: MEDIUM

### 🟡 Important Gaps

4. **keploy-framework: No Primitive Integration**
   - Impact: API testing not composable
   - Solution: Create `KeployRecordPrimitive`, `KeployReplayPrimitive`
   - Priority: MEDIUM

5. **Observability: Documentation Discoverability**
   - Impact: Users may not find observability features
   - Solution: Improve AGENTS.md and PRIMITIVES_CATALOG.md
   - Priority: MEDIUM

6. **CI/CD: Codecov Configuration**
   - Impact: Coverage reports may not upload
   - Solution: Configure CODECOV_TOKEN properly
   - Priority: MEDIUM

### 🟢 Minor Gaps

7. **python-pathway: Limited Scope**
   - Impact: Minimal utility
   - Solution: Consider deprecation or primitive integration
   - Priority: LOW

8. **MCP: No Runtime Integration**
   - Impact: Can't query MCP from workflows
   - Solution: Optional `MCPQueryPrimitive` bridge
   - Priority: LOW

---

## Recommended Actions

### Phase 1: Critical (1 week)

1. **Add Observability Tests**

   ```bash
packages/tta-dev-primitives/tests/observability/
   ├── test_instrumented_primitive.py
   ├── test_observable_primitive.py
   ├── test_metrics_collector.py
   └── test_context_propagation.py
```

2. **Create Agent Coordination Primitives**
   ```bash
packages/universal-agent-context/src/universal_agent_context/primitives/
   ├── __init__.py
   ├── handoff.py           # AgentHandoffPrimitive
   ├── memory.py            # AgentMemoryPrimitive
   └── coordination.py      # AgentCoordinationPrimitive
```

3. **Update Documentation**
   - Add observability section to AGENTS.md
   - Add agent coordination to PRIMITIVES_CATALOG.md
   - Add integration examples

### Phase 2: Important (2 weeks)

4. **Add Integration Tests**

   ```bash
tests/integration/
   ├── test_observability_primitives.py
   ├── test_agent_coordination.py
   ├── test_multi_package_workflow.py
   └── test_end_to_end.py
```

5. **Create Keploy Primitives**
   ```bash
packages/keploy-framework/src/keploy_framework/primitives/
   ├── __init__.py
   ├── record.py            # KeployRecordPrimitive
   └── replay.py            # KeployReplayPrimitive
```

6. **Fix CI/CD**
   - Configure Codecov properly
   - Add integration test workflow
   - Set coverage thresholds

### Phase 3: Nice-to-Have (1 month)

7. **Evaluate python-pathway**
   - Decide: integrate or deprecate
   - If integrate: create `CodeAnalysisPrimitive`
   - If deprecate: document migration

8. **Consider MCP Bridge**
   - Evaluate need for runtime MCP access
   - If needed: create `MCPQueryPrimitive`
   - Document use cases

---

## Integration Health Matrix

| Component | Extends WorkflowPrimitive | Composable | Documented | Tested | Examples | Overall |
|-----------|---------------------------|------------|------------|--------|----------|---------|
| **tta-observability-integration** | ✅ Yes | ✅ Yes | ✅ Yes | ⚠️ Partial | ✅ Yes | 9/10 |
| **universal-agent-context** | ❌ No | ❌ No | ✅ Yes | ⚠️ Partial | ❌ No | 5/10 |
| **keploy-framework** | ❌ No | ❌ No | ⚠️ Partial | ✅ Yes | ⚠️ Partial | 4/10 |
| **python-pathway** | ❌ No | ❌ No | ❌ No | ⚠️ Partial | ❌ No | 4/10 |
| **VS Code Toolsets** | N/A | N/A | ✅ Yes | N/A | ✅ Yes | 8/10 |
| **MCP Servers** | N/A | N/A | ✅ Yes | N/A | ✅ Yes | 8/10 |
| **CI/CD** | N/A | N/A | ✅ Yes | ✅ Yes | N/A | 8/10 |
| **Testing (MockPrimitive)** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | 9/10 |

---

## Conclusion

TTA.dev has **excellent observability integration** and **testing infrastructure**, but has gaps in:

1. **Agent coordination** - No primitive-based multi-agent workflows
2. **API testing** - Keploy not integrated with primitives
3. **Test coverage** - Observability features untested
4. **Integration testing** - Packages tested in isolation

**Next Steps:**

1. Create agent coordination primitives (HIGH priority)
2. Add observability tests (HIGH priority)
3. Add integration tests (MEDIUM priority)
4. Create Keploy primitives (MEDIUM priority)

**Overall Integration Health: 7.5/10** - Good foundation, needs tactical improvements.

---

**Prepared by:** GitHub Copilot
**Analysis Date:** October 29, 2025
**Status:** Complete
**Next Review:** After Phase 1 implementation

# MCP Server Integration Registry

**Model Context Protocol (MCP) servers available in TTA.dev**

---

## What is MCP?

**Model Context Protocol (MCP)** is an open standard for connecting AI applications to external data sources and tools. MCP servers expose capabilities that AI agents can use to:

- Query documentation
- Access databases
- Monitor systems
- Analyze code
- Execute operations

**Official Documentation:** <https://modelcontextprotocol.io>

---

## Available MCP Servers

### 1. Context7 - Library Documentation

**Purpose:** Query up-to-date documentation for any programming library

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `mcp_context7_resolve-library-id` | Find library ID from name | `@workspace #tta-agent-dev` then ask about resolving library |
| `mcp_context7_get-library-docs` | Get documentation for library | `@workspace #tta-agent-dev` then ask for docs |

**Example Usage:**

```
@workspace #tta-agent-dev

How do I use async/await with httpx library?
```

**Configuration:**

- Integrated in `.vscode/copilot-toolsets.jsonc`
- Available in `#tta-agent-dev` toolset

**Use Cases:**

- Learning new libraries
- API reference lookup
- Best practices research
- Integration patterns

---

### 2. AI Toolkit - Agent Development

**Purpose:** Best practices and guidance for AI application development

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `aitk_get_agent_code_gen_best_practices` | Agent development patterns | Ask about agent architecture |
| `aitk_get_ai_model_guidance` | Model selection advice | Ask about choosing models |
| `aitk_get_tracing_code_gen_best_practices` | Tracing implementation | Ask about observability |
| `aitk_evaluation_planner` | Evaluation metrics planning | Ask about testing AI apps |
| `aitk_get_evaluation_code_gen_best_practices` | Evaluation code patterns | Ask about evaluation code |

**Example Usage:**

```
@workspace #tta-agent-dev

What are best practices for creating an AI agent that uses multiple LLMs?
```

**Configuration:**

- Available in `#tta-agent-dev` toolset
- Complements TTA.dev primitives

**Use Cases:**

- Agent architecture decisions
- Model selection
- Tracing and observability
- Evaluation frameworks

---

### 3. Grafana - Observability

**Purpose:** Query Prometheus metrics and Loki logs

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `list_alert_rules` | List Grafana alert rules | `@workspace #tta-observability` |
| `get_alert_rule_by_uid` | Get specific alert rule | Ask about specific alert |
| `get_dashboard_by_uid` | Retrieve dashboard config | Ask about dashboard |
| `query_prometheus` | Execute PromQL query | Ask about metrics |
| `query_loki_logs` | Execute LogQL query | Ask about logs |
| `list_contact_points` | List notification endpoints | Ask about alerts |

**Example Usage:**

```
@workspace #tta-observability

Show me the error rate for the last hour
```

**Configuration:**

- Available in `#tta-observability` toolset
- Requires `docker-compose.test.yml` running

**Use Cases:**

- Debugging production issues
- Analyzing metrics
- Investigating errors
- Dashboard creation

---

### 4. Pylance - Python Tools

**Purpose:** Python-specific development tools

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `mcp_pylance_mcp_s_pylanceDocuments` | Python documentation search | General Python development |
| `mcp_pylance_mcp_s_pylanceFileSyntaxErrors` | File syntax checking | Code validation |
| `mcp_pylance_mcp_s_pylanceImports` | Import analysis | Dependency management |
| `mcp_pylance_mcp_s_pylanceRunCodeSnippet` | Execute Python code | Testing snippets |
| `mcp_pylance_mcp_s_pylancePythonEnvironments` | Environment info | Environment setup |

**Example Usage:**

```
@workspace #tta-package-dev

Check for syntax errors in this file
```

**Configuration:**

- Integrated automatically with Pylance extension
- Available across all toolsets

**Use Cases:**

- Syntax validation
- Import resolution
- Environment management
- Quick code testing

---

### 5. Database Client - SQL Operations

**Purpose:** Execute database queries and manage schemas

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `dbclient-get-databases` | List available databases | Database exploration |
| `dbclient-get-tables` | Get table schemas | Schema analysis |
| `dbclient-execute-query` | Run SQL queries | Data retrieval |

**Example Usage:**

```
@workspace #tta-full-stack

Show me the schema for the users table
```

**Configuration:**

- Available in `#tta-full-stack` toolset
- Requires database connection config

**Use Cases:**

- Schema exploration
- Data analysis
- Query testing
- Database documentation

---

### 6. GitHub Pull Request - Code Review

**Purpose:** PR information and coding agent coordination

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `github-pull-request_activePullRequest` | Get current PR details | PR context |
| `github-pull-request_openPullRequest` | Get visible PR details | Review workflow |
| `github-pull-request_copilot-coding-agent` | Async agent task execution | Complex implementations |

**Example Usage:**

```
@workspace #tta-pr-review

Summarize the changes in this PR
```

**Configuration:**

- Available in `#tta-pr-review` toolset
- Automatically discovers PRs

**Use Cases:**

- PR reviews
- Change analysis
- Async agent tasks
- Context gathering

---

### 7. Sift (Docker) - Investigation Analysis

**Purpose:** Retrieve and analyze investigations

**Tools Provided:**

| Tool | Description | Usage |
|------|-------------|-------|
| `mcp_mcp_docker_list_sift_investigations` | List investigations | Investigation discovery |
| `mcp_mcp_docker_get_sift_investigation` | Get specific investigation | Detailed analysis |
| `mcp_mcp_docker_get_sift_analysis` | Get analysis results | Investigation results |

**Example Usage:**

```
@workspace #tta-troubleshoot

Show me recent investigations
```

**Configuration:**

- Available in `#tta-troubleshoot` toolset
- Requires Docker MCP integration

**Use Cases:**

- Debugging workflows
- Investigation tracking
- Analysis review
- Historical context

---

## MCP Tools by Toolset

### Core Development Toolsets

| Toolset | MCP Tools Included |
|---------|-------------------|
| `#tta-minimal` | None (lightweight) |
| `#tta-package-dev` | Pylance tools (automatic) |
| `#tta-testing` | Pylance tools (automatic) |
| `#tta-observability` | Grafana (Prometheus, Loki, alerts) |

### Specialized Toolsets

| Toolset | MCP Tools Included |
|---------|-------------------|
| `#tta-agent-dev` | Context7, AI Toolkit |
| `#tta-mcp-integration` | All available MCP tools |
| `#tta-docs` | Context7 |
| `#tta-pr-review` | GitHub PR tools |
| `#tta-troubleshoot` | Sift, Grafana |
| `#tta-full-stack` | Database, Grafana, Context7 |

---

## Using MCP Tools

### In Copilot Chat

```
# Specify toolset with hashtag
@workspace #tta-observability

# Ask natural language question
Show me CPU usage for the last 30 minutes

# Copilot automatically invokes appropriate MCP tools
```

### Direct Tool Invocation

You can also request specific tools:

```
@workspace Use the query_prometheus tool to get error rates
```

---

## Adding New MCP Servers

### Step 1: Configure MCP Server

Add to your MCP configuration file (location depends on your setup):

```json
{
  "mcpServers": {
    "my-custom-server": {
      "command": "node",
      "args": ["/path/to/server.js"]
    }
  }
}
```

### Step 2: Add to Toolsets

Edit `.vscode/copilot-toolsets.jsonc`:

```jsonc
"my-custom-toolset": {
  "tools": [
    "edit",
    "search",
    "mcp_my_custom_server_tool1",
    "mcp_my_custom_server_tool2"
  ],
  "description": "Custom workflow using my server",
  "icon": "tools"
}
```

### Step 3: Document Here

Add entry to this file with:

- Purpose
- Tools provided
- Example usage
- Configuration details

### Step 4: Test Integration

```bash
# Reload VS Code
# Open Copilot chat
@workspace #my-custom-toolset

Test the new MCP integration
```

---

## Troubleshooting

### MCP Tool Not Found

**Symptom:** Tool name shows as invalid in toolset

**Solutions:**

1. Check MCP server is running:

   ```bash
# For Docker-based services

   docker-compose -f docker-compose.test.yml ps
```

2. Verify tool name format:
   - Should be `mcp_servername_toolname`
   - Check exact name in MCP server documentation

3. Reload VS Code window:
   - Command Palette → "Developer: Reload Window"

### MCP Server Not Responding

**Symptom:** Tools available but return errors

**Solutions:**

1. Check server logs
2. Verify network connectivity
3. Restart MCP server
4. Check authentication/credentials

### Tool Not Available in Toolset

**Symptom:** Tool exists but not showing up

**Solutions:**

1. Verify toolset includes tool name
2. Check `.vscode/copilot-toolsets.jsonc` syntax
3. Reload VS Code
4. Try `#tta-mcp-integration` (includes all MCP tools)

---

## Best Practices

### 1. Choose Right Toolset

- Use **focused toolsets** for specific tasks
- Prefer `#tta-observability` over `#tta-full-stack` for metrics
- Combine toolsets only when necessary

### 2. Natural Language Queries

```
# ✅ Good - Natural and specific

@workspace #tta-observability
Show me error logs from the last hour containing "timeout"

# ❌ Bad - Too technical

@workspace Execute LogQL: {job="app"} |= "timeout" [1h]
```

### 3. Understand Tool Capabilities

- Read tool descriptions in this document
- Check examples before complex queries
- Start simple, add complexity as needed

### 4. Performance Considerations

- Focused toolsets load faster
- MCP calls may have latency
- Cache-able results are better

---

## Integration with TTA.dev Primitives

MCP tools complement TTA.dev primitives:

### Observability Workflow

```python
from tta_dev_primitives import WorkflowPrimitive
from observability_integration import initialize_observability

# Use primitives for workflow
workflow = step1 >> step2 >> step3

# Use MCP tools to query results
# @workspace #tta-observability
# Show me metrics for this workflow
```

### Documentation Lookup

```python
# When building agent with new library:
# @workspace #tta-agent-dev
# How do I use the langchain library for embeddings?

# Then implement using primitives
from tta_dev_primitives import SequentialPrimitive
```

### Database Operations

```python
# Use MCP to explore schema:
# @workspace #tta-full-stack
# What's the schema for analytics table?

# Then use primitives for workflow
db_query_workflow = (
    validate_input >>
    query_database >>
    transform_results
)
```

---

## MCP Server Development

Want to create your own MCP server for TTA.dev?

### Resources

- **MCP Specification:** <https://spec.modelcontextprotocol.io>
- **Example Servers:** `scripts/mcp/` directory
- **Integration Guide:** `.vscode/README.md`

### Template

```typescript
// Basic MCP server structure
import { Server } from "@modelcontextprotocol/sdk/server/index.js";

const server = new Server({
  name: "tta-custom-server",
  version: "1.0.0"
});

server.tool("my_tool", "Tool description", {
  // Tool schema
}, async (args) => {
  // Tool implementation
  return result;
});

server.start();
```

---

## Related Documentation

- **Copilot Toolsets:** [`.vscode/copilot-toolsets.jsonc`](.vscode/copilot-toolsets.jsonc)
- **Toolset Guide:** [`docs/guides/copilot-toolsets-guide.md`](docs/guides/copilot-toolsets-guide.md)
- **Integration README:** [`.vscode/README.md`](.vscode/README.md)
- **MCP Documentation:** [`docs/mcp/`](docs/mcp/)

---

## Quick Reference

### Get Documentation

```
@workspace #tta-agent-dev
Find documentation for [library name]
```

### Query Metrics

```
@workspace #tta-observability
Show [metric name] for last [time period]
```

### Analyze Code

```
@workspace #tta-package-dev
Check syntax errors in current file
```

### Review PR

```
@workspace #tta-pr-review
Summarize changes in this pull request
```

### Execute Query

```
@workspace #tta-full-stack
Run query: [SQL query]
```

---

**Last Updated:** October 29, 2025
**Maintained by:** TTA.dev Team
**MCP Version:** 1.0
**VS Code Integration:** Stable

# GitHub Copilot Instructions for TTA.dev

This file provides workspace-level guidance for GitHub Copilot when working with TTA.dev.

---

## Project Overview

**TTA.dev** is a production-ready AI development toolkit providing composable agentic primitives for building reliable AI workflows.

### Core Concepts

- **Agentic Primitives**: Reusable workflow components that compose via operators
- **Type-Safe Composition**: `>>` (sequential) and `|` (parallel) operators
- **Built-in Observability**: OpenTelemetry integration across all primitives
- **Recovery Patterns**: Retry, Fallback, Timeout, Compensation primitives
- **Monorepo Structure**: Multiple focused packages in `/packages`

---

## Monorepo Structure

### Package Architecture

```text
TTA.dev/
├── packages/
│   ├── tta-dev-primitives/          # Core workflow primitives (START HERE)
│   ├── tta-observability-integration/  # OpenTelemetry + Prometheus
│   ├── universal-agent-context/      # Agent context management
│   ├── keploy-framework/             # API testing framework
│   └── python-pathway/               # Python analysis utilities
├── docs/                             # Documentation
├── scripts/                          # Automation scripts
└── tests/                            # Integration tests
```

### When to Use Which Package

| Task | Package | Files to Focus On |
|------|---------|------------------|
| Creating new workflow primitives | `tta-dev-primitives` | `src/tta_dev_primitives/core/`, `examples/` |
| Adding recovery patterns | `tta-dev-primitives` | `src/tta_dev_primitives/recovery/` |
| Adding observability | `tta-observability-integration` | `src/observability_integration/primitives/` |
| Agent coordination | `universal-agent-context` | `src/universal_agent_context/` |
| API testing | `keploy-framework` | `src/keploy_framework/` |
| Python code analysis | `python-pathway` | `src/python_pathway/` |

---

## Key Patterns & Best Practices

### 1. Workflow Primitive Composition

**Always use primitives** instead of manual async orchestration:

```python
# ✅ GOOD - Use primitive composition
from tta_dev_primitives import SequentialPrimitive, ParallelPrimitive

workflow = (
    input_processor >>
    (fast_llm | slow_llm | cached_llm) >>
    aggregator
)

# ❌ BAD - Manual async orchestration
async def workflow(input_data):
    processed = await input_processor(input_data)
    results = await asyncio.gather(
        fast_llm(processed),
        slow_llm(processed),
        cached_llm(processed)
    )
    return await aggregator(results)
```

### 2. WorkflowContext for State Management

**Always pass state via WorkflowContext**:

```python
# ✅ GOOD - Use WorkflowContext
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    correlation_id="req-123",
    data={"user_id": "user-789"}
)
result = await workflow.execute(context, input_data)

# ❌ BAD - Global variables or function parameters
USER_ID = "user-789"  # Don't use globals
```

### 3. Type Safety

**Use Python 3.11+ type hints**:

```python
# ✅ GOOD - Modern type hints
def process(data: str | None) -> dict[str, Any]:
    ...

class MyPrimitive(WorkflowPrimitive[InputModel, OutputModel]):
    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: InputModel
    ) -> OutputModel:
        ...

# ❌ BAD - Old type hints
from typing import Optional, Dict

def process(data: Optional[str]) -> Dict[str, Any]:
    ...
```

### 4. Recovery Patterns

**Use recovery primitives** instead of manual error handling:

```python
# ✅ GOOD - Use RetryPrimitive
from tta_dev_primitives.recovery import RetryPrimitive

workflow = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential"
)

# ❌ BAD - Manual retry logic
async def api_call_with_retry():
    for i in range(3):
        try:
            return await api_call()
        except Exception:
            await asyncio.sleep(2 ** i)
    raise Exception("Failed after retries")
```

### 5. Testing

**Use MockPrimitive for testing**:

```python
# ✅ GOOD - Use MockPrimitive
from tta_dev_primitives.testing import MockPrimitive
import pytest

@pytest.mark.asyncio
async def test_workflow():
    mock_llm = MockPrimitive(return_value={"output": "test"})
    workflow = step1 >> mock_llm >> step3
    result = await workflow.execute(context, input_data)
    assert mock_llm.call_count == 1

# ❌ BAD - Complex mocking
@patch('module.llm_call')
async def test_workflow(mock_llm):
    mock_llm.return_value = {"output": "test"}
    ...
```

---

## Copilot Toolsets

TTA.dev provides **focused toolsets** to optimize your workflow. Use the appropriate toolset hashtag in your Copilot chat:

### Core Development Toolsets

| Toolset | When to Use | Tools Included |
|---------|-------------|----------------|
| `#tta-minimal` | Quick edits, reading code | search, read_file, edit, problems |
| `#tta-package-dev` | Developing primitives | All dev tools + runTests, configurePythonEnvironment |
| `#tta-testing` | Writing/running tests | runTests, edit, search, terminal, get_errors |
| `#tta-observability` | Tracing/metrics work | Prometheus, Loki, observability tools + dev tools |

### Specialized Toolsets

| Toolset | When to Use | Tools Included |
|---------|-------------|----------------|
| `#tta-agent-dev` | Building AI agents | Context7, AI Toolkit, agent development tools |
| `#tta-mcp-integration` | MCP server work | MCP tools, semantic search, documentation |
| `#tta-validation` | Running quality checks | Linting, type checking, validation scripts |
| `#tta-pr-review` | Reviewing PRs | GitHub PR tools, diff analysis, changed files |

**Full toolset documentation:** [`.vscode/README.md`](.vscode/README.md)

---

## Common Workflows

### Adding a New Primitive

1. **Create primitive class** in `packages/tta-dev-primitives/src/tta_dev_primitives/`
   - Extend `WorkflowPrimitive[InputType, OutputType]`
   - Implement `_execute_impl()` method
   - Add type hints and docstrings

2. **Add tests** in `packages/tta-dev-primitives/tests/`
   - Test success case
   - Test error cases
   - Test edge cases
   - Aim for 100% coverage

3. **Create example** in `packages/tta-dev-primitives/examples/`
   - Show real-world usage
   - Include comments explaining pattern
   - Demonstrate composition

4. **Update documentation**
   - Add to package README
   - Update `PRIMITIVES_CATALOG.md`
   - Update relevant guides in `docs/`

**Use toolset:** `#tta-package-dev`

### Adding Observability

1. **Choose package:**
   - Core tracing → `tta-observability-integration`
   - Primitive-specific → `tta-dev-primitives/observability/`

2. **Follow OpenTelemetry standards:**
   - Use span names: `primitive_name.operation`
   - Add attributes for context
   - Record events for key milestones
   - Handle errors properly

3. **Test with Prometheus:**

   ```bash
docker-compose -f docker-compose.test.yml up -d

# Run your code

# Check <http://localhost:9090>
```

**Use toolset:** `#tta-observability`

### Running Tests

```bash
# All tests
uv run pytest -v

# Specific package
uv run pytest packages/tta-dev-primitives/tests/ -v

# With coverage
uv run pytest --cov=packages --cov-report=html

# Integration tests
uv run pytest tests/integration/ -v
```

**Use toolset:** `#tta-testing`

---

## File-Type Specific Instructions

TTA.dev uses **path-based instruction files** in `.github/instructions/`:

| File Pattern | Instruction File | Key Rules |
|--------------|-----------------|-----------|
| `packages/**/src/**/*.py` | `package-source.instructions.md` | Production quality, full types, comprehensive tests |
| `**/tests/**/*.py` | `tests.instructions.md` | 100% coverage, pytest-asyncio, MockPrimitive usage |
| `scripts/**/*.py` | `scripts.instructions.md` | Use primitives for orchestration, clear documentation |
| `**/*.md`, `**/README.md` | `documentation.instructions.md` | Clear, actionable, with code examples |

**Always check the relevant instruction file** before editing files of that type.

---

## Package Manager: uv (NOT pip)

TTA.dev uses **uv** for dependency management:

```bash
# ✅ CORRECT - Use uv
uv add package-name                  # Add dependency
uv sync --all-extras                 # Sync all dependencies
uv run pytest                        # Run command in venv
uv run python script.py              # Run Python script

# ❌ WRONG - Don't use pip
pip install package-name             # Don't do this
python -m pip install package-name   # Don't do this
```

---

## Code Quality Standards

### Required Checks Before Commit

1. **Format code:** `uv run ruff format .`
2. **Lint code:** `uv run ruff check . --fix`
3. **Type check:** `uvx pyright packages/`
4. **Run tests:** `uv run pytest -v`

**Shortcut:** Use VS Code task `✅ Quality Check (All)`

### Type Checking

- **100% type coverage required** for all public APIs
- Use `pyright` (built into Pylance)
- Configure in `pyproject.toml` per package

### Testing Standards

- **100% coverage required** for all new code
- Use `pytest` with `pytest-asyncio`
- Mock external services with `MockPrimitive`
- Test success, failure, and edge cases

---

## Anti-Patterns to Avoid

| ❌ Don't Do This | ✅ Do This Instead |
|-----------------|-------------------|
| Manual async orchestration | Use `SequentialPrimitive` or `ParallelPrimitive` |
| Try/except with retry loops | Use `RetryPrimitive` |
| `asyncio.wait_for()` for timeouts | Use `TimeoutPrimitive` |
| Manual caching with dicts | Use `CachePrimitive` |
| Global variables for state | Use `WorkflowContext` |
| `pip install` | Use `uv add` |
| `Optional[T]` type hints | Use `T \| None` |
| Modifying core primitives | Extend via composition |

---

## Observability Best Practices

### Structured Logging

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "workflow_executed",
    workflow_name="my_workflow",
    duration_ms=123.45,
    status="success"
)
```

### Tracing

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def my_operation():
    with tracer.start_as_current_span("my_operation") as span:
        span.set_attribute("input_size", len(data))
        # ... do work ...
        span.add_event("processing_complete")
```

### Context Propagation

```python
# WorkflowContext automatically propagates:
# - correlation_id
# - user_id
# - request metadata
# - parent span context

context = WorkflowContext(
    correlation_id="req-123",
    data={"user_id": "user-789"}
)

# All primitives in workflow get this context
result = await workflow.execute(context, input_data)
```

---

## Example References

### Basic Workflow Composition

**File:** `packages/tta-dev-primitives/examples/basic_sequential.py`

Shows sequential composition with `>>` operator.

### Parallel Execution

**File:** `packages/tta-dev-primitives/examples/parallel_execution.py`

Shows parallel composition with `|` operator.

### LLM Router

**File:** `packages/tta-dev-primitives/examples/router_llm_selection.py`

Shows dynamic routing between different LLMs.

### Error Handling

**File:** `packages/tta-dev-primitives/examples/error_handling_patterns.py`

Shows retry, fallback, timeout patterns.

### Real-World Workflows

**File:** `packages/tta-dev-primitives/examples/real_world_workflows.py`

Shows complete production-ready workflows.

---

## Documentation Structure

### Main Documentation

| Document | Purpose |
|----------|---------|
| [`AGENTS.md`](AGENTS.md) | Primary agent instructions (START HERE) |
| [`README.md`](README.md) | Project overview |
| [`GETTING_STARTED.md`](GETTING_STARTED.md) | Setup guide |
| [`PRIMITIVES_CATALOG.md`](PRIMITIVES_CATALOG.md) | Complete primitive reference |
| [`MCP_SERVERS.md`](MCP_SERVERS.md) | MCP server integrations |

### Package Documentation

Each package in `/packages` has:

- `README.md` - API documentation
- `AGENTS.md` or `.github/copilot-instructions.md` - Agent guidance
- `examples/` - Working code examples
- `tests/` - Test suite

### Guides & Architecture

- `docs/guides/` - Usage guides and tutorials
- `docs/architecture/` - Architecture decisions
- `docs/integration/` - Integration patterns
- `docs/observability/` - Observability setup

---

## Quick Decision Guide

### "Should I create a new primitive?"

**YES if:**

- Pattern is reusable across workflows
- Has clear input/output types
- Can be composed with other primitives
- Adds observability value

**NO if:**

- One-off operation (just use a function)
- Tightly coupled to specific workflow
- Doesn't need observability

### "Should I modify an existing primitive?"

**YES if:**

- Fixing a bug
- Adding optional parameter (backward compatible)
- Improving performance without breaking API

**NO if:**

- Breaking change (create new primitive instead)
- Adding workflow-specific logic
- Changing core behavior

### "Which package does this belong in?"

- **Workflow patterns** → `tta-dev-primitives`
- **Tracing/metrics** → `tta-observability-integration`
- **Agent coordination** → `universal-agent-context`
- **API testing** → `keploy-framework`
- **Python analysis** → `python-pathway`

---

## Troubleshooting

### Import Errors

```bash
# Make sure dependencies are synced
uv sync --all-extras

# Check Python version
python --version  # Should be 3.11+

# Verify in virtual environment
which python  # Should point to .venv/bin/python
```

### Type Errors

```bash
# Run type checker
uvx pyright packages/

# Check specific file
uvx pyright packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py
```

### Test Failures

```bash
# Run with verbose output
uv run pytest -v -s

# Run specific test
uv run pytest packages/tta-dev-primitives/tests/test_sequential.py -v

# Debug with pdb
uv run pytest --pdb
```

### Observability Issues

```bash
# Start test services
docker-compose -f docker-compose.test.yml up -d

# Check Prometheus
curl http://localhost:9090/api/v1/targets

# Check logs
docker-compose -f docker-compose.test.yml logs -f
```

---

## Git Workflow

### Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/fixes

### Commit Messages

Follow conventional commits:

```text
feat(primitives): add CachePrimitive with LRU and TTL support

- Implement LRU eviction policy
- Add TTL-based expiration
- Include comprehensive tests
- Add example usage

Closes #123
```

### Pull Request Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Type hints complete
- [ ] Ruff formatting applied
- [ ] All quality checks pass
- [ ] Examples added (if new feature)

---

## Quick Links

- **Main Agent Instructions:** [`AGENTS.md`](AGENTS.md)
- **Primitive Catalog:** [`PRIMITIVES_CATALOG.md`](PRIMITIVES_CATALOG.md)
- **MCP Servers:** [`MCP_SERVERS.md`](MCP_SERVERS.md)
- **Toolsets Guide:** [`docs/guides/copilot-toolsets-guide.md`](docs/guides/copilot-toolsets-guide.md)
- **Getting Started:** [`GETTING_STARTED.md`](GETTING_STARTED.md)

---

**Last Updated:** October 29, 2025
**For:** GitHub Copilot in VS Code
**Maintained by:** TTA.dev Team

# TTA.dev Primitives Catalog

**Comprehensive reference for all workflow primitives in TTA.dev**

---

## Quick Reference

### Core Workflow Primitives

| Primitive | Purpose | Type | Import | Documentation |
|-----------|---------|------|--------|---------------|
| **WorkflowPrimitive[T,U]** | Base class for all primitives | Abstract Base | `from tta_dev_primitives import WorkflowPrimitive` | [base.py](packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py) |
| **SequentialPrimitive** | Execute operations in sequence | Composition | `from tta_dev_primitives import SequentialPrimitive` | [sequential.py](packages/tta-dev-primitives/src/tta_dev_primitives/core/sequential.py) |
| **ParallelPrimitive** | Execute operations in parallel | Composition | `from tta_dev_primitives import ParallelPrimitive` | [parallel.py](packages/tta-dev-primitives/src/tta_dev_primitives/core/parallel.py) |
| **ConditionalPrimitive** | Branch based on condition | Control Flow | `from tta_dev_primitives import ConditionalPrimitive` | [conditional.py](packages/tta-dev-primitives/src/tta_dev_primitives/core/conditional.py) |
| **SwitchPrimitive** | Multi-way branching | Control Flow | `from tta_dev_primitives import SwitchPrimitive` | [conditional.py](packages/tta-dev-primitives/src/tta_dev_primitives/core/conditional.py) |
| **RouterPrimitive** | Dynamic routing (e.g., LLM selection) | Routing | `from tta_dev_primitives import RouterPrimitive` | [routing.py](packages/tta-dev-primitives/src/tta_dev_primitives/core/routing.py) |
| **LambdaPrimitive** | Inline function wrapper | Utility | `from tta_dev_primitives import LambdaPrimitive` | [base.py](packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py) |

### Recovery Primitives

| Primitive | Purpose | Type | Import | Documentation |
|-----------|---------|------|--------|---------------|
| **RetryPrimitive** | Retry with backoff strategies | Recovery | `from tta_dev_primitives.recovery import RetryPrimitive` | [retry.py](packages/tta-dev-primitives/src/tta_dev_primitives/recovery/retry.py) |
| **FallbackPrimitive** | Graceful degradation | Recovery | `from tta_dev_primitives.recovery import FallbackPrimitive` | [fallback.py](packages/tta-dev-primitives/src/tta_dev_primitives/recovery/fallback.py) |
| **TimeoutPrimitive** | Circuit breaker pattern | Recovery | `from tta_dev_primitives.recovery import TimeoutPrimitive` | [timeout.py](packages/tta-dev-primitives/src/tta_dev_primitives/recovery/timeout.py) |
| **SagaPrimitive** | Compensating transactions | Recovery | `from tta_dev_primitives.recovery import SagaPrimitive` | [compensation.py](packages/tta-dev-primitives/src/tta_dev_primitives/recovery/compensation.py) |

### Performance Primitives

| Primitive | Purpose | Type | Import | Documentation |
|-----------|---------|------|--------|---------------|
| **CachePrimitive** | LRU + TTL caching | Performance | `from tta_dev_primitives.performance import CachePrimitive` | [cache.py](packages/tta-dev-primitives/src/tta_dev_primitives/performance/cache.py) |

### Observability Primitives

| Primitive | Purpose | Type | Import | Documentation |
|-----------|---------|------|--------|---------------|
| **InstrumentedPrimitive[T,U]** | Automatic tracing and metrics | Observability | `from tta_dev_primitives.observability import InstrumentedPrimitive` | [instrumented_primitive.py](packages/tta-dev-primitives/src/tta_dev_primitives/observability/instrumented_primitive.py) |
| **ObservablePrimitive** | Custom observability hooks | Observability | `from tta_dev_primitives.observability import ObservablePrimitive` | [tracing.py](packages/tta-dev-primitives/src/tta_dev_primitives/observability/tracing.py) |
| **APMWorkflowPrimitive** | APM integration | Observability | `from tta_dev_primitives.apm import APMWorkflowPrimitive` | [instrumented.py](packages/tta-dev-primitives/src/tta_dev_primitives/apm/instrumented.py) |

### Testing Primitives

| Primitive | Purpose | Type | Import | Documentation |
|-----------|---------|------|--------|---------------|
| **MockPrimitive** | Testing and mocking | Testing | `from tta_dev_primitives.testing import MockPrimitive` | [mocks.py](packages/tta-dev-primitives/src/tta_dev_primitives/testing/mocks.py) |

### Integration Primitives

| Primitive | Purpose | Type | Import | Documentation |
|-----------|---------|------|--------|---------------|
| **OpenAIPrimitive** | OpenAI API integration | LLM | `from tta_dev_primitives.integrations import OpenAIPrimitive` | [openai_primitive.py](packages/tta-dev-primitives/src/tta_dev_primitives/integrations/openai_primitive.py) |
| **AnthropicPrimitive** | Anthropic Claude API integration | LLM | `from tta_dev_primitives.integrations import AnthropicPrimitive` | [anthropic_primitive.py](packages/tta-dev-primitives/src/tta_dev_primitives/integrations/anthropic_primitive.py) |
| **OllamaPrimitive** | Ollama local LLM integration | LLM | `from tta_dev_primitives.integrations import OllamaPrimitive` | [ollama_primitive.py](packages/tta-dev-primitives/src/tta_dev_primitives/integrations/ollama_primitive.py) |
| **SupabasePrimitive** | Supabase database operations | Database | `from tta_dev_primitives.integrations import SupabasePrimitive` | [supabase_primitive.py](packages/tta-dev-primitives/src/tta_dev_primitives/integrations/supabase_primitive.py) |
| **SQLitePrimitive** | SQLite local database operations | Database | `from tta_dev_primitives.integrations import SQLitePrimitive` | [sqlite_primitive.py](packages/tta-dev-primitives/src/tta_dev_primitives/integrations/sqlite_primitive.py) |

### Research Primitives

| Primitive | Purpose | Type | Import | Documentation |
|-----------|---------|------|--------|---------------|
| **FreeTierResearchPrimitive** | Automated LLM free tier research | Research | `from tta_dev_primitives.research import FreeTierResearchPrimitive` | [free_tier_research.py](packages/tta-dev-primitives/src/tta_dev_primitives/research/free_tier_research.py) |

### Orchestration Primitives

| Primitive | Purpose | Type | Import | Documentation |
|-----------|---------|------|--------|---------------|
| **TaskClassifierPrimitive** | Classify tasks by complexity | Orchestration | `from tta_dev_primitives.orchestration import TaskClassifierPrimitive` | [task_classifier.py](packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/task_classifier.py) |
| **DelegationPrimitive** | Delegate tasks to executors | Orchestration | `from tta_dev_primitives.orchestration import DelegationPrimitive` | [delegation_primitive.py](packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/delegation_primitive.py) |
| **MultiModelWorkflow** | Orchestrate multi-model workflows | Orchestration | `from tta_dev_primitives.orchestration import MultiModelWorkflow` | [multi_model_workflow.py](packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/multi_model_workflow.py) |

### Agent Coordination Primitives

| Primitive | Purpose | Type | Import | Documentation |
|-----------|---------|------|--------|---------------|
| **AgentHandoffPrimitive** | Task handoff between agents | Multi-Agent | `from universal_agent_context.primitives import AgentHandoffPrimitive` | [handoff.py](packages/universal-agent-context/src/universal_agent_context/primitives/handoff.py) |
| **AgentMemoryPrimitive** | Architectural decision memory | Multi-Agent | `from universal_agent_context.primitives import AgentMemoryPrimitive` | [memory.py](packages/universal-agent-context/src/universal_agent_context/primitives/memory.py) |
| **AgentCoordinationPrimitive** | Parallel multi-agent execution | Multi-Agent | `from universal_agent_context.primitives import AgentCoordinationPrimitive` | [coordination.py](packages/universal-agent-context/src/universal_agent_context/primitives/coordination.py) |

---

## Detailed Reference

### 1. WorkflowPrimitive[T, U]

**Base class for all primitives**

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from typing import Any

class MyPrimitive(WorkflowPrimitive[InputType, OutputType]):
    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: InputType
    ) -> OutputType:
        # Your implementation
        return result
```

**Key Features:**

- Generic type parameters `[T, U]` for type safety
- Automatic context propagation
- Built-in error handling
- Composition via `>>` and `|` operators

**When to Use:**

- Creating custom primitives
- Need type-safe workflows
- Want built-in observability

**Example:** [base.py](packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py)

---

### 2. SequentialPrimitive

**Execute operations in sequence**

```python
from tta_dev_primitives import SequentialPrimitive

# Using the >> operator (recommended)
workflow = step1 >> step2 >> step3

# Or explicit construction
workflow = SequentialPrimitive(primitives=[step1, step2, step3])
```

**Key Features:**

- Executes primitives in order
- Output of each step becomes input to next
- Short-circuits on error
- Automatic tracing

**When to Use:**

- Operations depend on previous results
- Need guaranteed execution order
- Building pipelines

**Example:** [examples/basic_sequential.py](packages/tta-dev-primitives/examples/basic_sequential.py)

---

### 3. ParallelPrimitive

**Execute operations in parallel**

```python
from tta_dev_primitives import ParallelPrimitive

# Using the | operator (recommended)
workflow = branch1 | branch2 | branch3

# Or explicit construction
workflow = ParallelPrimitive(primitives=[branch1, branch2, branch3])
```

**Key Features:**

- Executes primitives concurrently
- Returns list of results
- Waits for all to complete (or first error)
- Automatic tracing

**When to Use:**

- Independent operations
- Need to reduce latency
- Fan-out/fan-in patterns

**Example:** [examples/parallel_execution.py](packages/tta-dev-primitives/examples/parallel_execution.py)

---

### 4. ConditionalPrimitive

**Branch based on condition**

```python
from tta_dev_primitives import ConditionalPrimitive

workflow = ConditionalPrimitive(
    condition=lambda ctx, data: data["score"] > 0.8,
    if_true=expensive_processing,
    if_false=cheap_processing
)
```

**Key Features:**

- Dynamic branching
- Evaluates condition at runtime
- Both branches are primitives
- Lazy evaluation (only executes chosen branch)

**When to Use:**

- Different logic based on input
- Want to skip expensive operations
- A/B testing scenarios

**Example:** [conditional.py](packages/tta-dev-primitives/src/tta_dev_primitives/core/conditional.py)

---

### 5. SwitchPrimitive

**Multi-way branching**

```python
from tta_dev_primitives import SwitchPrimitive

workflow = SwitchPrimitive(
    cases={
        "fast": gpt4_mini,
        "balanced": gpt4,
        "quality": claude_opus,
    },
    selector=lambda ctx, data: data["priority"],
    default_case="balanced"
)
```

**Key Features:**

- Multiple branches
- String-based case matching
- Optional default case
- Lazy evaluation

**When to Use:**

- More than 2 branches
- Dynamic routing based on string keys
- Strategy pattern

**Example:** [conditional.py](packages/tta-dev-primitives/src/tta_dev_primitives/core/conditional.py)

---

### 6. RouterPrimitive

**Dynamic routing (LLM selection, etc.)**

```python
from tta_dev_primitives import RouterPrimitive

router = RouterPrimitive(
    routes={
        "fast": gpt4_mini,
        "complex": gpt4,
        "local": llama_local,
    },
    routing_strategy="latency",  # or "cost", "quality", custom
    default_route="fast"
)
```

**Key Features:**

- Built-in routing strategies
- Latency/cost optimization
- Health check integration
- Automatic fallback

**When to Use:**

- LLM selection
- Service routing
- Load balancing
- Cost optimization

**Example:** [examples/router_llm_selection.py](packages/tta-dev-primitives/examples/router_llm_selection.py)

---

### 7. RetryPrimitive

**Retry with backoff strategies**

```python
from tta_dev_primitives.recovery import RetryPrimitive

workflow = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0,
    max_delay=60.0,
    jitter=True
)
```

**Key Features:**

- Multiple backoff strategies (constant, linear, exponential)
- Jitter support
- Configurable delays
- Automatic error handling

**When to Use:**

- Transient failures
- Network calls
- Rate-limited APIs
- Unreliable services

**Example:** [examples/error_handling_patterns.py](packages/tta-dev-primitives/examples/error_handling_patterns.py)

---

### 8. FallbackPrimitive

**Graceful degradation**

```python
from tta_dev_primitives.recovery import FallbackPrimitive

workflow = FallbackPrimitive(
    primary=gpt4,
    fallbacks=[gpt4_mini, cached_response, default_response]
)
```

**Key Features:**

- Multiple fallback levels
- Automatic failover
- Preserves error context
- Logs fallback events

**When to Use:**

- High availability required
- Multiple data sources
- Progressive degradation
- Backup strategies

**Example:** [examples/error_handling_patterns.py](packages/tta-dev-primitives/examples/error_handling_patterns.py)

---

### 9. TimeoutPrimitive

**Circuit breaker pattern**

```python
from tta_dev_primitives.recovery import TimeoutPrimitive

workflow = TimeoutPrimitive(
    primitive=slow_operation,
    timeout_seconds=30.0,
    on_timeout="raise"  # or "return_default"
)
```

**Key Features:**

- Hard timeout enforcement
- Prevents resource leaks
- Configurable timeout behavior
- Automatic cleanup

**When to Use:**

- Bounded execution time
- Prevent hanging
- Resource protection
- SLA enforcement

**Example:** [examples/error_handling_patterns.py](packages/tta-dev-primitives/examples/error_handling_patterns.py)

---

### 10. SagaPrimitive (CompensationPrimitive)

**Compensating transactions for rollback**

```python
from tta_dev_primitives.recovery import SagaPrimitive

workflow = SagaPrimitive(
    forward_steps=[
        (create_order, cancel_order),
        (charge_payment, refund_payment),
        (reserve_inventory, release_inventory),
    ]
)
```

**Key Features:**

- Automatic compensation on failure
- Maintains transaction consistency
- Rollback in reverse order
- Detailed compensation logs

**When to Use:**

- Distributed transactions
- Multi-step operations
- Need rollback capability
- Data consistency critical

**Example:** [compensation.py](packages/tta-dev-primitives/src/tta_dev_primitives/recovery/compensation.py)

---

### 11. CachePrimitive

**LRU + TTL caching**

```python
from tta_dev_primitives.performance import CachePrimitive

workflow = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,
    max_size=1000,
    cache_key_fn=lambda ctx, data: data["input_hash"]
)
```

**Key Features:**

- LRU eviction policy
- TTL-based expiration
- Custom cache key function
- Automatic invalidation
- 30-40% cost reduction in production

**When to Use:**

- Expensive operations
- Repeated inputs
- LLM calls
- API rate limiting

**Example:** [examples/quick_wins_demo.py](packages/tta-dev-primitives/examples/quick_wins_demo.py)

---

### 12. InstrumentedPrimitive[T, U]

**Automatic tracing and metrics**

```python
from tta_dev_primitives.observability import InstrumentedPrimitive

class MyPrimitive(InstrumentedPrimitive[InputType, OutputType]):
    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: InputType
    ) -> OutputType:
        # Your implementation
        # Automatic spans, metrics, logs!
        return result
```

**Key Features:**

- Automatic OpenTelemetry spans
- Prometheus metrics
- Structured logging
- Error tracking

**When to Use:**

- Need observability
- Production primitives
- Performance monitoring
- Debugging workflows

**Example:** [instrumented_primitive.py](packages/tta-dev-primitives/src/tta_dev_primitives/observability/instrumented_primitive.py)

---

### 13. MockPrimitive

**Testing and mocking**

```python
from tta_dev_primitives.testing import MockPrimitive

mock_llm = MockPrimitive(
    return_value={"response": "test output"},
    side_effect=None,  # or exception to raise
    call_delay=0.1  # simulate latency
)

# Use in tests
workflow = step1 >> mock_llm >> step3
result = await workflow.execute(context, input_data)

assert mock_llm.call_count == 1
assert mock_llm.last_call_args == (context, input_data)
```

**Key Features:**

- Configurable return values
- Exception simulation
- Call tracking
- Latency simulation

**When to Use:**

- Unit testing
- Integration testing
- Mocking external services
- Performance testing

**Example:** [mocks.py](packages/tta-dev-primitives/src/tta_dev_primitives/testing/mocks.py)

---

### 14. FreeTierResearchPrimitive

**Automated LLM free tier research and documentation**

```python
from tta_dev_primitives.research import FreeTierResearchPrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Create research primitive
researcher = FreeTierResearchPrimitive()

# Research all providers
context = WorkflowContext(workflow_id="free-tier-update")
request = FreeTierResearchRequest(
    providers=["openai", "anthropic", "google-gemini", "openrouter", "ollama"],
    existing_guide_path="docs/guides/llm-cost-guide.md",
    output_path="docs/guides/llm-cost-guide.md",
    generate_changelog=True
)
response = await researcher.execute(request, context)

# Check for changes
if response.changelog:
    print("Changes detected:")
    for change in response.changelog:
        print(f"  - {change}")

# Access provider information
for provider_name, info in response.providers.items():
    print(f"{info.name}: {'Free' if info.has_free_tier else 'Paid'}")
    if info.free_tier_details:
        print(f"  └─ {info.free_tier_details}")
```

**Key Features:**

- Automated provider research (OpenAI, Anthropic, Google Gemini, OpenRouter, Ollama)
- Changelog generation (detects changes from existing guide)
- Markdown guide generation
- Structured provider information (rate limits, costs, expiration)
- CLI tool for easy updates (`scripts/update-free-tiers.py`)

**Provider Information Tracked:**

- Free tier availability
- Rate limits (RPM, RPD, TPM)
- Credit card requirements
- Expiration policies
- Cost after free tier
- Setup URLs and pricing URLs
- Common confusion points

**When to Use:**

- Keeping free tier documentation current
- Researching provider pricing changes
- Generating comparison tables
- Automating documentation updates

**CLI Usage:**

```bash
# Update all providers
uv run python scripts/update-free-tiers.py

# Update specific providers
uv run python scripts/update-free-tiers.py --providers openai ollama

# Write to custom output
uv run python scripts/update-free-tiers.py --output custom-guide.md

# Disable changelog
uv run python scripts/update-free-tiers.py --no-changelog
```

**Example:** [free_tier_research.py](packages/tta-dev-primitives/src/tta_dev_primitives/research/free_tier_research.py)

---

### 15. TaskClassifierPrimitive

**Classify tasks by complexity for intelligent routing**

```python
from tta_dev_primitives.orchestration import TaskClassifierPrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Create classifier
classifier = TaskClassifierPrimitive(prefer_free=True)

# Classify a task
context = WorkflowContext(workflow_id="task-classification")
task_description = "Generate unit tests for a Python function"

classification = await classifier.execute(task_description, context)

# Check classification
print(f"Complexity: {classification['complexity']}")  # "MODERATE"
print(f"Recommended Model: {classification['recommended_model']}")  # "gemini-2.5-pro"
print(f"Reasoning: {classification['reasoning']}")
```

**Complexity Levels:**

- **SIMPLE** - Simple queries, factual questions → Groq (ultra-fast, free)
- **MODERATE** - Analysis, summarization, basic reasoning → Gemini Pro (flagship quality, free)
- **COMPLEX** - Multi-step reasoning, planning, creative tasks → DeepSeek R1 (on par with o1, free)
- **EXPERT** - Advanced reasoning, code generation, research → Claude Sonnet 4.5 (paid, highest quality)

**Key Features:**

- Intelligent task complexity classification
- Free model preference (when `prefer_free=True`)
- Quality-aware routing (uses free models when quality sufficient)
- Detailed reasoning for classification decisions
- Configurable complexity thresholds

**When to Use:**

- Multi-model orchestration workflows
- Cost optimization (route simple tasks to free models)
- Quality-aware task delegation
- Intelligent LLM selection

**Example:** [task_classifier.py](packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/task_classifier.py)

---

### 16. DelegationPrimitive

**Delegate tasks to executor models**

```python
from tta_dev_primitives.orchestration import DelegationPrimitive, DelegationRequest
from tta_dev_primitives.integrations import GoogleAIStudioPrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Create delegation primitive with executors
delegation = DelegationPrimitive(
    executor_primitives={
        "gemini-2.5-pro": GoogleAIStudioPrimitive(model="gemini-2.5-pro"),
        "llama-3.3-70b": GroqPrimitive(model="llama-3.3-70b-versatile"),
    }
)

# Create delegation request
request = DelegationRequest(
    task_description="Generate unit tests for this function",
    executor_model="gemini-2.5-pro",
    messages=[{"role": "user", "content": "def add(a, b): return a + b"}],
    metadata={"complexity": "MODERATE"}
)

# Execute delegation
context = WorkflowContext(workflow_id="delegation")
response = await delegation.execute(request, context)

# Access results
print(f"Response: {response.content}")
print(f"Cost: ${response.cost}")
print(f"Tokens: {response.usage['total_tokens']}")
```

**Key Features:**

- Delegates tasks to configured executor models
- Tracks execution metrics (tokens, cost, duration)
- Supports multiple executor types (Gemini, Groq, OpenRouter, etc.)
- Automatic cost calculation
- Detailed usage tracking

**When to Use:**

- Executing tasks with specific models
- Cost tracking for delegated operations
- Multi-model workflows
- Executor abstraction layer

**Example:** [delegation_primitive.py](packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/delegation_primitive.py)

---

### 17. MultiModelWorkflow

**Orchestrate multi-model workflows with 80-95% cost savings**

```python
from tta_dev_primitives.orchestration import MultiModelWorkflow
from tta_dev_primitives.integrations import GoogleAIStudioPrimitive, GroqPrimitive
from tta_dev_primitives.core.base import WorkflowContext

# Create workflow with executors
workflow = MultiModelWorkflow(
    executor_primitives={
        "gemini-2.5-pro": GoogleAIStudioPrimitive(model="gemini-2.5-pro"),
        "llama-3.3-70b": GroqPrimitive(model="llama-3.3-70b-versatile"),
    },
    prefer_free=True  # Prefer free models when quality sufficient
)

# Execute workflow
context = WorkflowContext(workflow_id="multi-model-orchestration")
task_description = "Generate comprehensive unit tests for a Python module"

result = await workflow.execute(task_description, context)

# Access results
print(f"Task: {result['task_description']}")
print(f"Complexity: {result['classification']['complexity']}")
print(f"Executor Used: {result['delegation']['executor_model']}")
print(f"Response: {result['delegation']['content']}")
print(f"Total Cost: ${result['delegation']['cost']}")
```

**Workflow Architecture:**

```
User Task → TaskClassifier (Claude) → DelegationPrimitive (Gemini/Groq/etc.) → Result
            ↓                          ↓
            Classify complexity        Execute with free model
            Recommend model            Track cost/tokens
```

**Key Features:**

- **Intelligent Classification** - Claude classifies task complexity
- **Cost-Optimized Delegation** - Routes to free models when possible
- **Full Observability** - Tracks all metrics (tokens, cost, duration)
- **Configurable** - Supports YAML configuration via `.tta/orchestration-config.yaml`
- **80-95% Cost Savings** - Compared to all-Claude approach

**Cost Savings Examples:**

| Use Case | All-Claude | Orchestration | Savings |
|----------|-----------|---------------|---------|
| Test Generation | $0.50/file | $0.009/file | 98% |
| PR Review | $2.00/PR | $0.30/PR | 85% |
| Documentation | $1.50/file | $0.15/file | 90% |

**When to Use:**

- Production workflows requiring cost optimization
- Multi-model orchestration
- Quality-aware task delegation
- Workflows with mixed complexity tasks

**Configuration:**

```yaml
# .tta/orchestration-config.yaml
orchestration:
  enabled: true
  prefer_free_models: true
  quality_threshold: 0.85

  orchestrator:
    model: claude-sonnet-4.5
    api_key_env: ANTHROPIC_API_KEY

  executors:
    - model: gemini-2.5-pro
      provider: google-ai-studio
      api_key_env: GOOGLE_API_KEY
      use_cases: [moderate, complex]
```

**Examples:**

- [orchestration_test_generation.py](packages/tta-dev-primitives/examples/orchestration_test_generation.py) - Automated test generation
- [orchestration_pr_review.py](packages/tta-dev-primitives/examples/orchestration_pr_review.py) - PR review automation
- [orchestration_doc_generation.py](packages/tta-dev-primitives/examples/orchestration_doc_generation.py) - Documentation generation

**Documentation:**

- [ORCHESTRATION_DEMO_GUIDE.md](packages/tta-dev-primitives/examples/ORCHESTRATION_DEMO_GUIDE.md) - Test generation guide
- [PR_REVIEW_GUIDE.md](packages/tta-dev-primitives/examples/PR_REVIEW_GUIDE.md) - PR review guide
- [DOC_GENERATION_GUIDE.md](packages/tta-dev-primitives/examples/DOC_GENERATION_GUIDE.md) - Documentation generation guide
- [orchestration-configuration-guide.md](docs/guides/orchestration-configuration-guide.md) - Configuration reference
- [MULTI_MODEL_ORCHESTRATION_SUMMARY.md](docs/guides/MULTI_MODEL_ORCHESTRATION_SUMMARY.md) - Complete implementation summary

---

### 18. AgentHandoffPrimitive

**Task handoff between agents**

```python
from universal_agent_context.primitives import AgentHandoffPrimitive

# Create handoff to specialist agent
handoff = AgentHandoffPrimitive(
    target_agent="data_analyst",
    handoff_strategy="immediate",  # "immediate", "queued", or "conditional"
    preserve_context=True
)

# Use in workflow
workflow = (
    initial_processing >>
    handoff >>  # Handoff to data_analyst
    specialized_analysis
)
```

**Key Features:**

- Three handoff strategies (immediate, queued, conditional)
- Context preservation control (full or trimmed)
- Agent history tracking in WorkflowContext
- Custom handoff callbacks
- Automatic checkpoint recording

**Context Updates:**

- `context.metadata["current_agent"]` - Updated to target agent
- `context.metadata["agent_history"]` - List of all handoffs
- `context.metadata["handoff_timestamp"]` - Time of handoff
- `context.metadata["handoff_reason"]` - Reason for handoff

**When to Use:**

- Multi-agent workflows
- Task delegation between agents
- Agent specialization (e.g., analyzer → implementer → tester)
- Workflow transitions requiring context handoff

**Example:** [handoff.py](packages/universal-agent-context/src/universal_agent_context/primitives/handoff.py)

---

### 15. AgentMemoryPrimitive

**Architectural decision memory**

```python
from universal_agent_context.primitives import AgentMemoryPrimitive

# Store decision
store_decision = AgentMemoryPrimitive(
    operation="store",
    memory_key="architecture_choice",
    memory_scope="session"  # "workflow", "session", or "global"
)

# Retrieve decision later
retrieve_decision = AgentMemoryPrimitive(
    operation="retrieve",
    memory_key="architecture_choice"
)

# Query by tags
query_memories = AgentMemoryPrimitive(
    operation="query",
    memory_scope="session"
)

# Use in workflow
workflow = (
    analyze_requirements >>
    store_decision >>  # Store architectural decision
    implement_solution >>
    retrieve_decision  # Recall decision for validation
)
```

**Key Features:**

- Four operations: store, retrieve, query, list
- Three memory scopes: workflow, session, global
- Tagged memory entries with metadata
- Automatic timestamping and agent tracking
- Cross-agent memory sharing

**Memory Entry Structure:**

```python
{
    "key": "decision_key",
    "value": {"data": "..."},
    "timestamp": 1234567890.0,
    "agent": "agent_name",
    "scope": "session",
    "tags": {"type": "architectural", "priority": "high"},
    "workflow_id": "wf-123",
    "correlation_id": "corr-456"
}
```

**When to Use:**

- Sharing decisions across agents
- Architectural decision records (ADR)
- Cross-workflow state preservation
- Agent coordination patterns
- Long-running multi-agent sessions

**Example:** [memory.py](packages/universal-agent-context/src/universal_agent_context/primitives/memory.py)

---

### 16. AgentCoordinationPrimitive

**Parallel multi-agent execution**

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
    coordination_strategy="aggregate",  # "aggregate", "first", or "consensus"
    timeout_seconds=30.0,
    require_all_success=False
)

# Use in workflow
workflow = (
    prepare_data >>
    coordinator >>  # All agents execute in parallel
    aggregate_results
)
```

**Key Features:**

- Three coordination strategies (aggregate, first-success, consensus)
- Timeout support with graceful degradation
- Parallel execution with child contexts
- Rich coordination metadata
- Failure tracking and recovery

**Coordination Strategies:**

- **aggregate**: Collect all successful results
- **first**: Return first successful result
- **consensus**: Find majority agreement among results

**Output Structure:**

```python
{
    "agent_results": {
        "agent1": {"result": "..."},
        "agent2": {"result": "..."},
    },
    "coordination_metadata": {
        "total_agents": 3,
        "successful_agents": 2,
        "failed_agents": 1,
        "failed_agent_names": ["agent3"],
        "elapsed_ms": 1234.5,
        "strategy": "aggregate"
    },
    "aggregated_result": {...},
    "failed_agents": ["agent3"]
}
```

**When to Use:**

- Parallel agent execution
- Consensus-building workflows
- Redundancy and fault tolerance
- Performance optimization (parallel processing)
- Multi-perspective analysis

**Example:** [coordination.py](packages/universal-agent-context/src/universal_agent_context/primitives/coordination.py)

---

## Multi-Agent Integration Example

```python
from tta_dev_primitives import SequentialPrimitive
from universal_agent_context.primitives import (
    AgentHandoffPrimitive,
    AgentMemoryPrimitive,
    AgentCoordinationPrimitive,
)

# Complete multi-agent workflow
workflow = (
    # Initial agent stores plan
    AgentMemoryPrimitive(operation="store", memory_key="plan") >>

    # Coordinate multiple agents in parallel
    AgentCoordinationPrimitive(
        agent_primitives={
            "analyzer": analysis_agent,
            "implementer": implementation_agent,
            "tester": testing_agent,
        },
        coordination_strategy="aggregate"
    ) >>

    # Handoff to final agent
    AgentHandoffPrimitive(target_agent="finalizer") >>

    # Retrieve plan for validation
    AgentMemoryPrimitive(operation="retrieve", memory_key="plan") >>

    # Final validation
    validation_step
)

# Execute
context = WorkflowContext(workflow_id="multi-agent-demo")
context.metadata["current_agent"] = "coordinator"
result = await workflow.execute(input_data, context)
```

---

## Composition Operators

### Sequential Composition (`>>`)

```python
# Chain operations
workflow = step1 >> step2 >> step3

# Equivalent to
workflow = SequentialPrimitive(primitives=[step1, step2, step3])
```

### Parallel Composition (`|`)

```python
# Execute in parallel
workflow = branch1 | branch2 | branch3

# Equivalent to
workflow = ParallelPrimitive(primitives=[branch1, branch2, branch3])
```

### Mixed Composition

```python
# Complex workflows
workflow = (
    input_processor >>
    (fast_path | slow_path | cached_path) >>
    aggregator >>
    output_formatter
)
```

---

## Common Patterns

### Pattern 1: LLM Router with Fallback and Cache

```python
from tta_dev_primitives import RouterPrimitive
from tta_dev_primitives.recovery import FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Cache expensive LLM calls
cached_llm = CachePrimitive(
    primitive=gpt4,
    ttl_seconds=3600
)

# Route to best LLM
router = RouterPrimitive(
    routes={"fast": gpt4_mini, "quality": cached_llm},
    default_route="fast"
)

# Add fallback
workflow = FallbackPrimitive(
    primary=router,
    fallbacks=[backup_llm]
)
```

### Pattern 2: Retry with Timeout

```python
from tta_dev_primitives.recovery import RetryPrimitive, TimeoutPrimitive

# Timeout each attempt
timed_api_call = TimeoutPrimitive(
    primitive=api_call,
    timeout_seconds=10.0
)

# Retry with backoff
workflow = RetryPrimitive(
    primitive=timed_api_call,
    max_retries=3,
    backoff_strategy="exponential"
)
```

### Pattern 3: Parallel with Aggregation

```python
from tta_dev_primitives import ParallelPrimitive

# Process in parallel
parallel_processing = ParallelPrimitive(
    primitives=[processor1, processor2, processor3]
)

# Aggregate results
workflow = parallel_processing >> aggregator
```

### Pattern 4: Conditional Routing

```python
from tta_dev_primitives import ConditionalPrimitive

# Route based on complexity
workflow = ConditionalPrimitive(
    condition=lambda ctx, data: data["complexity"] > 0.8,
    if_true=complex_processor,
    if_false=simple_processor
)
```

---

## Type Safety

All primitives support generic type parameters:

```python
from tta_dev_primitives import WorkflowPrimitive

class TypedPrimitive(WorkflowPrimitive[InputModel, OutputModel]):
    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: InputModel
    ) -> OutputModel:
        # Type checker validates input/output
        return OutputModel(...)
```

**Benefits:**

- IDE autocomplete
- Static type checking with Pyright
- Catch errors before runtime
- Better documentation

---

## Observability

### WorkflowContext

Every primitive receives `WorkflowContext`:

```python
from tta_dev_primitives import WorkflowContext

context = WorkflowContext(
    correlation_id="req-123",
    data={
        "user_id": "user-789",
        "request_type": "analysis"
    }
)
```

**Automatic Propagation:**

- Correlation IDs
- User metadata
- OpenTelemetry spans
- Structured logs

### Metrics

All primitives emit Prometheus metrics:

- `primitive_execution_duration_seconds`
- `primitive_execution_total`
- `primitive_error_total`

### Tracing

OpenTelemetry spans for all executions:

- Span name: `primitive_name.execute`
- Attributes: input size, output size, etc.
- Events: key milestones

---

## Examples Directory

All primitives have working examples in [`packages/tta-dev-primitives/examples/`](packages/tta-dev-primitives/examples/):

| Example | Demonstrates |
|---------|-------------|
| `basic_sequential.py` | Sequential composition with `>>` |
| `parallel_execution.py` | Parallel composition with `\|` |
| `router_llm_selection.py` | Dynamic LLM routing |
| `error_handling_patterns.py` | Retry, Fallback, Timeout |
| `quick_wins_demo.py` | Cache for cost optimization |
| `real_world_workflows.py` | Complete production workflows |
| `observability_demo.py` | Tracing and metrics |

---

## Testing

Test all primitives with `MockPrimitive`:

```python
from tta_dev_primitives.testing import MockPrimitive
import pytest

@pytest.mark.asyncio
async def test_workflow():
    mock = MockPrimitive(return_value={"result": "test"})
    workflow = step1 >> mock >> step3

    result = await workflow.execute(context, input_data)

    assert mock.call_count == 1
    assert result["result"] == "test"
```

**Testing Guide:** [`packages/tta-dev-primitives/tests/`](packages/tta-dev-primitives/tests/)

---

## Package Information

### Installation

```bash
# Development
uv sync --all-extras

# Production
uv add tta-dev-primitives
```

### Requirements

- Python 3.11+
- OpenTelemetry (optional)
- Prometheus (optional)

### Documentation

- **Package README:** [`packages/tta-dev-primitives/README.md`](packages/tta-dev-primitives/README.md)
- **Agent Instructions:** [`packages/tta-dev-primitives/AGENTS.md`](packages/tta-dev-primitives/AGENTS.md)
- **Architecture Docs:** [`docs/architecture/`](docs/architecture/)

---

## Contributing

To add a new primitive:

1. Extend `WorkflowPrimitive[T, U]`
2. Implement `_execute_impl()`
3. Add comprehensive tests (100% coverage)
4. Create example in `examples/`
5. Update this catalog
6. Update package README

**Contributing Guide:** [`CONTRIBUTING.md`](CONTRIBUTING.md)

---

**Last Updated:** October 29, 2025
**Maintained by:** TTA.dev Team
**License:** See package LICENSE files
icense:** See package LICENSE files
ee package LICENSE files

ee package LICENSE files
