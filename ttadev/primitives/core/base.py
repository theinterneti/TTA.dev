"""Base workflow primitive abstractions.

# See: [[TTA.dev/Primitives/WorkflowPrimitive]]
# See: [[TTA.dev/Primitives/LambdaPrimitive]]
"""

from __future__ import annotations

import copy
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Agent identity — optional import so primitives work without observability installed
try:
    from ttadev.observability.agent_identity import get_agent_id
    from ttadev.observability.agent_identity import get_agent_tool as _get_agent_tool

    _IDENTITY_AVAILABLE = True
except ImportError:
    _IDENTITY_AVAILABLE = False

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


class WorkflowContext(BaseModel):
    """Context passed through every primitive execution with full observability support.

    ``WorkflowContext`` is the single object that flows through every
    :meth:`WorkflowPrimitive.execute` call.  It carries distributed-tracing
    identifiers, correlation/causation chains, agent identity, and arbitrary
    metadata so that any primitive can participate in a larger observable workflow
    without needing to know about the surrounding infrastructure.

    **Creating a context:**

    Use the factory class methods rather than the constructor directly:

    .. code-block:: python

        # Root context — start a new workflow
        ctx = WorkflowContext.root("my-workflow")

        # Child context — derive from a parent for a named sub-step
        child_ctx = WorkflowContext.child(ctx, step_name="validate-input")

    Attributes:
        workflow_id: Human-readable identifier for the workflow step or phase.
            Set to the step name so logs and spans are self-describing.
        session_id: Optional game/user session identifier (TTA-specific).
            Propagated unchanged through child contexts.
        player_id: Optional player identifier (TTA-specific).
            Propagated unchanged through child contexts.
        metadata: Arbitrary key-value pairs attached by the workflow creator.
            Deep-copied into child contexts to prevent cross-step mutation.
        state: Mutable workflow state dictionary; primitives may read/write
            here to pass results forward without changing function signatures.
            Deep-copied into child contexts.
        trace_id: OpenTelemetry trace ID as a hex string, or ``None`` if
            observability is not initialised.
        span_id: Current OTel span ID as a hex string, or ``None``.
        parent_span_id: Span ID of the parent span, or ``None`` for the root.
            Set automatically by :meth:`child`.
        trace_flags: W3C trace flags integer (``1`` = sampled, ``0`` = not sampled).
            Default is ``1`` (sampled).
        correlation_id: UUID string that groups all events belonging to a single
            logical request.  Auto-generated on construction; inherited unchanged
            by child contexts.
        causation_id: ``correlation_id`` of the *parent* context, forming a
            causal chain.  ``None`` for root contexts; set automatically by
            :meth:`child`.
        agent_id: Stable per-process UUID identifying the AI agent that created
            this context.  Auto-populated from :mod:`ttadev.observability.agent_identity`
            when available.
        agent_tool: Human-readable agent tool name (``"claude-code"``,
            ``"copilot"``, …).  Auto-populated when available.
        project_id: :class:`~ttadev.observability.session.ProjectSession` ID used
            to group spans across multiple agents working on the same project.
        baggage: W3C Baggage dictionary for cross-service context propagation.
            Key-value pairs are propagated to child contexts.
        tags: Custom string tags for log filtering and grouping (e.g.
            ``{"env": "prod", "region": "us-east-1"}``).  Propagated to children.
        start_time: Unix timestamp (seconds) recorded when the context was created.
        checkpoints: Ordered list of ``(name, timestamp)`` tuples recorded via
            :meth:`checkpoint`.
        memory: Workflow memory object set by the orchestrator; ``None`` outside
            of guided workflows.  Excluded from serialisation.
    """

    # Core workflow identifiers
    workflow_id: str | None = None
    session_id: str | None = None
    player_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    state: dict[str, Any] = Field(default_factory=dict)

    # Distributed tracing (W3C Trace Context)
    trace_id: str | None = Field(default=None, description="OpenTelemetry trace ID (hex)")
    span_id: str | None = Field(default=None, description="Current span ID (hex)")
    parent_span_id: str | None = Field(default=None, description="Parent span ID (hex)")
    trace_flags: int = Field(default=1, description="W3C trace flags (sampled=1)")

    # Correlation and causation tracking
    correlation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique ID for request correlation across services",
    )
    causation_id: str | None = Field(
        default=None, description="ID of the event that caused this workflow"
    )

    # Agent identity — auto-populated from agent_identity module if available
    agent_id: str | None = Field(default=None, description="Stable per-process agent UUID")
    agent_tool: str | None = Field(
        default=None, description="Agent tool: claude-code, copilot, etc."
    )
    project_id: str | None = Field(
        default=None, description="ProjectSession ID for multi-agent grouping"
    )

    # Observability metadata
    baggage: dict[str, str] = Field(
        default_factory=dict,
        description="W3C Baggage for cross-service context propagation",
    )
    tags: dict[str, str] = Field(
        default_factory=dict, description="Custom tags for filtering and grouping"
    )

    # Timing and checkpoints
    start_time: float = Field(default_factory=time.time)
    checkpoints: list[tuple[str, float]] = Field(default_factory=list)

    # Workflow memory — set by WorkflowOrchestrator; None outside of guided workflows.
    # Typed as Any to avoid a circular import between primitives and workflows.
    memory: Any = Field(default=None, exclude=True)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode="before")
    @classmethod
    def _populate_agent_identity(cls, values: Any) -> Any:
        """Auto-fill agent_id and agent_tool from the process identity module."""
        if not isinstance(values, dict):
            return values
        if _IDENTITY_AVAILABLE:
            if values.get("agent_id") is None:
                values["agent_id"] = get_agent_id()
            if values.get("agent_tool") is None:
                values["agent_tool"] = _get_agent_tool()
        return values

    def checkpoint(self, name: str) -> None:
        """
        Record a timing checkpoint.

        Args:
            name: Name of the checkpoint
        """
        self.checkpoints.append((name, time.time()))

    def elapsed_ms(self) -> float:
        """
        Get elapsed time since workflow start in milliseconds.

        Returns:
            Elapsed time in milliseconds
        """
        return (time.time() - self.start_time) * 1000

    def create_child_context(self) -> WorkflowContext:
        """
        Create a child context for nested workflows.

        Inherits trace context and correlation ID from parent,
        but creates a new span context.

        Returns:
            New WorkflowContext with inherited trace context
        """
        return WorkflowContext(
            workflow_id=self.workflow_id,
            session_id=self.session_id,
            player_id=self.player_id,
            metadata=copy.deepcopy(self.metadata),
            state=copy.deepcopy(self.state),
            trace_id=self.trace_id,
            parent_span_id=self.span_id,  # Current span becomes parent
            correlation_id=self.correlation_id,  # Inherit correlation
            causation_id=self.correlation_id,  # Chain causation
            baggage=copy.deepcopy(self.baggage),
            tags=copy.deepcopy(self.tags),
            # Propagate agent identity and project grouping to child contexts
            agent_id=self.agent_id,
            agent_tool=self.agent_tool,
            project_id=self.project_id,
        )

    @classmethod
    def root(cls, workflow_id: str) -> WorkflowContext:
        """Create a fresh root context for a new workflow.

        Generates a new ``correlation_id``; ``causation_id`` and
        ``parent_span_id`` are left as ``None`` to mark this as a root span.
        Agent identity is auto-populated from the process identity module when
        available.

        Args:
            workflow_id: Human-readable identifier for this workflow or step.

        Returns:
            A new :class:`WorkflowContext` with no parent linkage.

        Example:
            .. code-block:: python

                ctx = WorkflowContext.root("fetch-user-profile")
                result = await my_primitive.execute(data, ctx)
        """
        return cls(workflow_id=workflow_id)

    @classmethod
    def child(cls, parent: WorkflowContext, step_name: str) -> WorkflowContext:
        """Create a child context derived from *parent* for a named sub-step.

        The child inherits the parent's ``correlation_id``, trace identifiers,
        baggage, tags, and agent identity.  The parent's ``correlation_id``
        becomes the child's ``causation_id``, and the parent's ``span_id``
        becomes the child's ``parent_span_id``, forming a complete causal chain.

        The parent context is **not mutated**.

        Args:
            parent: The parent :class:`WorkflowContext` to derive from.
            step_name: Human-readable name for this sub-step (used as
                ``workflow_id`` on the child).

        Returns:
            A new :class:`WorkflowContext` linked to *parent*.

        Example:
            .. code-block:: python

                root_ctx = WorkflowContext.root("pipeline")
                validate_ctx = WorkflowContext.child(root_ctx, "validate-input")
                transform_ctx = WorkflowContext.child(root_ctx, "transform-data")
        """
        return parent.create_child_context().model_copy(update={"workflow_id": step_name})

    @classmethod
    def from_project(cls, project: Any, workflow_id: str) -> WorkflowContext:
        """Create a WorkflowContext pre-populated with project + agent identity.

        Args:
            project: A ProjectSession instance (typed as Any to avoid a hard
                     dependency on ttadev.observability in the primitives package).
            workflow_id: The workflow step name for this context.

        Returns:
            WorkflowContext with agent_id, agent_tool, and project_id set.
        """
        return cls(
            workflow_id=workflow_id,
            project_id=getattr(project, "id", None),
        )

    def to_otel_context(self) -> dict[str, Any]:
        """
        Convert to OpenTelemetry context attributes.

        Returns:
            Dictionary of span attributes

        Example:
            ```python
            from opentelemetry import trace

            context = WorkflowContext(workflow_id="wf-123")
            span = trace.get_current_span()

            # Add workflow context as span attributes
            for key, value in context.to_otel_context().items():
                span.set_attribute(key, value)
            ```
        """
        return {
            "workflow.id": self.workflow_id or "unknown",
            "workflow.session_id": self.session_id or "unknown",
            "workflow.player_id": self.player_id or "unknown",
            "workflow.correlation_id": self.correlation_id,
            "workflow.elapsed_ms": self.elapsed_ms(),
        }

    async def spawn_agent(self, agent_name: str, task: Any) -> Any:
        """Spawn a sub-agent as a child span of the current workflow.

        Looks up ``agent_name`` in the global AgentRegistry, creates a child
        context (preserving the trace), and executes the agent.

        Imports are deferred to avoid a circular dependency between
        ``ttadev.primitives.core`` and ``ttadev.agents``.

        Args:
            agent_name: Name registered in the AgentRegistry.
            task: An AgentTask instance.

        Returns:
            AgentResult from the spawned agent.

        Raises:
            KeyError: if no agent with ``agent_name`` is registered.
        """
        from ttadev.agents.registry import get_registry  # deferred — avoids circular import

        registry = get_registry()
        agent_class = registry.get(agent_name)  # raises KeyError if not found
        child_ctx = self.create_child_context()
        agent = agent_class()
        return await agent.execute(task, child_ctx)


class WorkflowPrimitive(Generic[T, U], ABC):
    """
    Base class for composable workflow primitives.

    Primitives are the building blocks of workflows. They can be composed
    using operators:
    - `>>` for sequential execution (self then other)
    - `|` for parallel execution (self and other concurrently)

    Example:
        ```python
        workflow = primitive1 >> primitive2 >> primitive3
        result = await workflow.execute(input_data, context)
        ```
    """

    @abstractmethod
    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """
        Execute the primitive with input data and context.

        Args:
            input_data: Input data for the primitive
            context: Workflow context with session/state information

        Returns:
            Output data from the primitive

        Raises:
            Exception: If execution fails
        """
        pass

    def __rshift__(self, other: WorkflowPrimitive[U, V]) -> WorkflowPrimitive[T, V]:
        """
        Chain primitives sequentially: self >> other.

        The output of self becomes the input to other.

        Args:
            other: The primitive to execute after this one

        Returns:
            A new sequential primitive
        """
        from .sequential import SequentialPrimitive

        return SequentialPrimitive([self, other])

    def __or__(self, other: WorkflowPrimitive[T, U]) -> WorkflowPrimitive[T, list[U]]:
        """
        Execute primitives in parallel: self | other.

        Both primitives receive the same input and execute concurrently.

        Args:
            other: The primitive to execute in parallel

        Returns:
            A new parallel primitive
        """
        from .parallel import ParallelPrimitive

        return ParallelPrimitive([self, other])


class LambdaPrimitive(WorkflowPrimitive[T, U]):
    """
    Primitive that wraps a simple function or lambda.

    Useful for simple transformations or adapters.

    Example:
        ```python
        transform = LambdaPrimitive(lambda x, ctx: x.upper())
        workflow = input_primitive >> transform >> output_primitive
        ```
    """

    def __init__(self, func: Any) -> None:
        """
        Initialize with a function.

        Args:
            func: Async or sync function (input, context) -> output
        """
        self.func = func
        import inspect

        self.is_async = inspect.iscoroutinefunction(func)

    async def execute(self, input_data: T, context: WorkflowContext) -> U:
        """Execute the wrapped function."""
        if self.is_async:
            return await self.func(input_data, context)
        else:
            return self.func(input_data, context)
