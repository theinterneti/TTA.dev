"""TTA.dev Platform - Unified API for composable AI workflow primitives.

This is the recommended entry point for TTA.dev. It provides:
- Core workflow primitives (always available)
- Observability integration (optional, via `tta-dev[observability]`)
- Agent context management (optional, via `tta-dev[context]`)

Installation:
    # Core primitives only (minimal dependencies)
    pip install tta-dev
    # or: uv add tta-dev

    # With observability (OpenTelemetry, Prometheus)
    pip install tta-dev[observability]
    # or: uv add tta-dev[observability]

    # With agent context (multi-agent workflows)
    pip install tta-dev[context]
    # or: uv add tta-dev[context]

    # Full platform (all packages)
    pip install tta-dev[all]
    # or: uv add tta-dev[all]

Quick Start:
    from tta_dev import (
        WorkflowContext,
        SequentialPrimitive,
        ParallelPrimitive,
        RetryPrimitive,
        CachePrimitive,
    )

    # Build composable workflows
    workflow = step1 >> step2 >> step3  # Sequential
    parallel = branch1 | branch2        # Parallel

    # Execute with context
    context = WorkflowContext(workflow_id="my-workflow")
    result = await workflow.execute(input_data, context)
"""

from __future__ import annotations

__version__ = "0.1.0"

# ============================================================================
# Core Primitives (always available)
# ============================================================================
from tta_dev_primitives import (
    # Performance primitives
    CachePrimitive,
    # Recovery primitives
    CircuitBreaker,
    CompensationPrimitive,
    CompensationStrategy,
    # Core composition primitives
    ConditionalPrimitive,
    FallbackPrimitive,
    FallbackStrategy,
    # Testing utilities
    MockPrimitive,
    ParallelPrimitive,
    RetryPrimitive,
    RetryStrategy,
    RouterPrimitive,
    SequentialPrimitive,
    TimeoutPrimitive,
    # Base classes
    WorkflowContext,
    WorkflowPrimitive,
)

# Core exports (always available)
__all__ = [
    # Version
    "__version__",
    # Base classes
    "WorkflowContext",
    "WorkflowPrimitive",
    # Core composition
    "SequentialPrimitive",
    "ParallelPrimitive",
    "ConditionalPrimitive",
    "RouterPrimitive",
    # Performance
    "CachePrimitive",
    # Recovery
    "CircuitBreaker",
    "FallbackPrimitive",
    "FallbackStrategy",
    "RetryPrimitive",
    "RetryStrategy",
    "TimeoutPrimitive",
    "CompensationPrimitive",
    "CompensationStrategy",
    # Testing
    "MockPrimitive",
]

# ============================================================================
# Observability Integration (optional: install with tta-dev[observability])
# ============================================================================
try:
    from observability_integration import (
        initialize_observability,
        is_observability_enabled,
    )
    from observability_integration.primitives import (
        CachePrimitive as ObservableCachePrimitive,
    )
    from observability_integration.primitives import (
        RouterPrimitive as ObservableRouterPrimitive,
    )
    from observability_integration.primitives import (
        TimeoutPrimitive as ObservableTimeoutPrimitive,
    )

    # Add observability exports
    __all__.extend(
        [
            "initialize_observability",
            "is_observability_enabled",
            "ObservableRouterPrimitive",
            "ObservableCachePrimitive",
            "ObservableTimeoutPrimitive",
        ]
    )

    _OBSERVABILITY_AVAILABLE = True

except ImportError:
    # Observability not installed - provide None placeholders for graceful fallback
    initialize_observability = None  # type: ignore[assignment]
    is_observability_enabled = None  # type: ignore[assignment]
    ObservableRouterPrimitive = None  # type: ignore[assignment, misc]
    ObservableCachePrimitive = None  # type: ignore[assignment, misc]
    ObservableTimeoutPrimitive = None  # type: ignore[assignment, misc]

    _OBSERVABILITY_AVAILABLE = False

# ============================================================================
# Agent Context (optional: install with tta-dev[context])
# ============================================================================
try:
    from universal_agent_context.primitives import (
        AgentCoordinationPrimitive,
        AgentHandoffPrimitive,
        AgentMemoryPrimitive,
    )

    # Add agent context exports
    __all__.extend(
        [
            "AgentHandoffPrimitive",
            "AgentMemoryPrimitive",
            "AgentCoordinationPrimitive",
        ]
    )

    _CONTEXT_AVAILABLE = True

except ImportError:
    # Agent context not installed - provide None placeholders for graceful fallback
    AgentHandoffPrimitive = None  # type: ignore[assignment, misc]
    AgentMemoryPrimitive = None  # type: ignore[assignment, misc]
    AgentCoordinationPrimitive = None  # type: ignore[assignment, misc]

    _CONTEXT_AVAILABLE = False


# ============================================================================
# Availability checks
# ============================================================================
def observability_available() -> bool:
    """Check if observability integration is installed and available."""
    return _OBSERVABILITY_AVAILABLE


def context_available() -> bool:
    """Check if agent context package is installed and available."""
    return _CONTEXT_AVAILABLE


__all__.extend(
    [
        "observability_available",
        "context_available",
    ]
)
