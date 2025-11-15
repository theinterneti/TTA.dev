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
        for _key, entry in memories.items():
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
