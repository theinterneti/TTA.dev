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
