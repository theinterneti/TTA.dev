---
title: Agentic Primitives Implementation Plan
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/architecture/agentic-primitives-implementation-plan.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Architecture/Agentic Primitives Implementation Plan]]

**Date:** 2025-10-20
**Status:** Planning
**Priority:** High

## Overview

This document provides concrete implementation guidance for integrating agentic primitives and context engineering patterns from the GitHub blog into TTA's architecture. It includes code examples, architectural patterns, and integration strategies.

---

## Phase 1: Foundation Primitives (Weeks 1-2)

### 1.1 Context Window Manager

**Purpose:** Manage LLM context windows to prevent token limit issues and optimize context quality.

**Location:** `src/agent_orchestration/context/window_manager.py`

**Architecture:**

```python
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol


class ContextPruningStrategy(Enum):
    """Strategies for pruning context when approaching token limits."""
    RECENCY = "recency"  # Keep most recent messages
    RELEVANCE = "relevance"  # Keep most relevant to current query
    HYBRID = "hybrid"  # Combine recency and relevance
    SUMMARIZE = "summarize"  # Summarize older context


@dataclass
class ContextWindow:
    """Represents a managed context window."""
    max_tokens: int
    current_tokens: int
    messages: list[dict[str, Any]]
    metadata: dict[str, Any]

    @property
    def utilization(self) -> float:
        """Return context window utilization (0.0 to 1.0)."""
        return self.current_tokens / self.max_tokens

    @property
    def remaining_tokens(self) -> int:
        """Return remaining token capacity."""
        return self.max_tokens - self.current_tokens


class TokenCounter(Protocol):
    """Protocol for token counting implementations."""
    def count_tokens(self, text: str) -> int: ...


class ContextWindowManager:
    """
    Manages LLM context windows with automatic pruning and optimization.

    Features:
    - Token counting and tracking
    - Automatic context pruning
    - Context summarization
    - Multi-scale context management (immediate, session, historical)
    """

    def __init__(
        self,
        max_tokens: int = 8000,
        token_counter: TokenCounter | None = None,
        pruning_strategy: ContextPruningStrategy = ContextPruningStrategy.HYBRID,
        pruning_threshold: float = 0.8,  # Prune when 80% full
    ):
        self.max_tokens = max_tokens
        self.token_counter = token_counter or self._default_token_counter()
        self.pruning_strategy = pruning_strategy
        self.pruning_threshold = pruning_threshold

    def create_window(self, initial_messages: list[dict] | None = None) -> ContextWindow:
        """Create a new context window."""
        messages = initial_messages or []
        current_tokens = sum(self.token_counter.count_tokens(str(m)) for m in messages)

        return ContextWindow(
            max_tokens=self.max_tokens,
            current_tokens=current_tokens,
            messages=messages,
            metadata={}
        )

    def add_message(
        self,
        window: ContextWindow,
        message: dict[str, Any],
        auto_prune: bool = True
    ) -> ContextWindow:
        """Add a message to the context window, pruning if necessary."""
        message_tokens = self.token_counter.count_tokens(str(message))

        # Check if pruning needed
        if auto_prune and (window.current_tokens + message_tokens) / window.max_tokens > self.pruning_threshold:
            window = self._prune_context(window, message_tokens)

        window.messages.append(message)
        window.current_tokens += message_tokens

        return window

    def _prune_context(self, window: ContextWindow, needed_tokens: int) -> ContextWindow:
        """Prune context based on configured strategy."""
        if self.pruning_strategy == ContextPruningStrategy.RECENCY:
            return self._prune_by_recency(window, needed_tokens)
        elif self.pruning_strategy == ContextPruningStrategy.RELEVANCE:
            return self._prune_by_relevance(window, needed_tokens)
        elif self.pruning_strategy == ContextPruningStrategy.HYBRID:
            return self._prune_hybrid(window, needed_tokens)
        elif self.pruning_strategy == ContextPruningStrategy.SUMMARIZE:
            return self._prune_with_summarization(window, needed_tokens)

        return window

    def _prune_by_recency(self, window: ContextWindow, needed_tokens: int) -> ContextWindow:
        """Keep most recent messages, remove oldest."""
        # Implementation: Remove oldest messages until we have space
        pass

    def _prune_by_relevance(self, window: ContextWindow, needed_tokens: int) -> ContextWindow:
        """Keep most relevant messages based on semantic similarity."""
        # Implementation: Score messages by relevance, keep highest scoring
        pass

    def _prune_hybrid(self, window: ContextWindow, needed_tokens: int) -> ContextWindow:
        """Combine recency and relevance for pruning decisions."""
        # Implementation: Weight recency and relevance scores
        pass

    def _prune_with_summarization(self, window: ContextWindow, needed_tokens: int) -> ContextWindow:
        """Summarize older context to save tokens."""
        # Implementation: Summarize messages beyond certain age
        pass

    def _default_token_counter(self) -> TokenCounter:
        """Default token counter using tiktoken."""
        import tiktoken

        class TiktokenCounter:
            def __init__(self):
                self.encoding = tiktoken.get_encoding("cl100k_base")

            def count_tokens(self, text: str) -> int:
                return len(self.encoding.encode(text))

        return TiktokenCounter()
```

**Integration with Existing Orchestrators:**

```python
# src/agent_orchestration/unified_orchestrator.py

from .context.window_manager import ContextWindowManager, ContextPruningStrategy

class UnifiedAgentOrchestrator:
    def __init__(self, ...):
        # ... existing init ...
        self.context_manager = ContextWindowManager(
            max_tokens=8000,
            pruning_strategy=ContextPruningStrategy.HYBRID,
            pruning_threshold=0.8
        )

    async def _build_narrative_prompt(self, state: OrchestrationState) -> str:
        """Build narrative prompt with context window management."""
        # Create context window
        window = self.context_manager.create_window()

        # Add system message
        window = self.context_manager.add_message(window, {
            "role": "system",
            "content": "You are a therapeutic narrative generator..."
        })

        # Add conversation history (with automatic pruning)
        for msg in state.therapeutic_context.get("history", []):
            window = self.context_manager.add_message(window, msg)

        # Add current context
        window = self.context_manager.add_message(window, {
            "role": "user",
            "content": state.user_input
        })

        # Build final prompt from window
        return self._format_messages(window.messages)
```

**Testing Strategy:**

```python
# tests/agent_orchestration/context/test_window_manager.py

import pytest
from src.agent_orchestration.context.window_manager import (
    ContextWindowManager,
    ContextPruningStrategy
)


def test_context_window_creation():
    """Test creating a context window."""
    manager = ContextWindowManager(max_tokens=1000)
    window = manager.create_window()

    assert window.max_tokens == 1000
    assert window.current_tokens == 0
    assert window.utilization == 0.0


def test_add_message_without_pruning():
    """Test adding messages below pruning threshold."""
    manager = ContextWindowManager(max_tokens=1000, pruning_threshold=0.8)
    window = manager.create_window()

    # Add small message
    window = manager.add_message(window, {"role": "user", "content": "Hello"})

    assert len(window.messages) == 1
    assert window.current_tokens > 0


def test_automatic_pruning():
    """Test automatic pruning when threshold exceeded."""
    manager = ContextWindowManager(
        max_tokens=100,
        pruning_strategy=ContextPruningStrategy.RECENCY,
        pruning_threshold=0.5
    )
    window = manager.create_window()

    # Add messages until pruning triggers
    for i in range(10):
        window = manager.add_message(window, {
            "role": "user",
            "content": f"Message {i}" * 10
        })

    # Should have pruned some messages
    assert window.utilization <= 1.0
    assert len(window.messages) < 10
```

---

### 1.2 Error Recovery Framework

**Purpose:** Centralized error classification and recovery strategies for reliable agent workflows.

**Location:** `src/agent_orchestration/recovery/error_handler.py`

**Architecture:**

```python
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Awaitable


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"  # Recoverable, minimal impact
    MEDIUM = "medium"  # Recoverable, some impact
    HIGH = "high"  # Requires intervention
    CRITICAL = "critical"  # System-level failure


class ErrorCategory(Enum):
    """Error categories for classification."""
    LLM_ERROR = "llm_error"  # LLM API failures
    VALIDATION_ERROR = "validation_error"  # Safety/validation failures
    STATE_ERROR = "state_error"  # State management issues
    TOOL_ERROR = "tool_error"  # Tool execution failures
    TIMEOUT_ERROR = "timeout_error"  # Timeout issues
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for an error."""
    error: Exception
    category: ErrorCategory
    severity: ErrorSeverity
    agent_id: str | None = None
    workflow_id: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class RecoveryStrategy:
    """Defines a recovery strategy for an error category."""
    name: str
    category: ErrorCategory
    handler: Callable[[ErrorContext], Awaitable[Any]]
    max_retries: int = 3
    fallback: Callable[[ErrorContext], Awaitable[Any]] | None = None


class ErrorRecoveryFramework:
    """
    Centralized error recovery framework for agent workflows.

    Features:
    - Error classification
    - Severity assessment
    - Recovery strategy selection
    - Fallback handling
    - Error metrics and logging
    """

    def __init__(self):
        self.strategies: dict[ErrorCategory, RecoveryStrategy] = {}
        self.error_counts: dict[ErrorCategory, int] = {}

    def register_strategy(self, strategy: RecoveryStrategy) -> None:
        """Register a recovery strategy for an error category."""
        self.strategies[strategy.category] = strategy

    def classify_error(self, error: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """Classify an error into category and severity."""
        # LLM errors
        if "rate limit" in str(error).lower():
            return ErrorCategory.LLM_ERROR, ErrorSeverity.MEDIUM
        if "timeout" in str(error).lower():
            return ErrorCategory.TIMEOUT_ERROR, ErrorSeverity.MEDIUM

        # Validation errors
        if "safety" in str(error).lower() or "validation" in str(error).lower():
            return ErrorCategory.VALIDATION_ERROR, ErrorSeverity.HIGH

        # State errors
        if "state" in str(error).lower() or "redis" in str(error).lower():
            return ErrorCategory.STATE_ERROR, ErrorSeverity.HIGH

        # Tool errors
        if "tool" in str(error).lower():
            return ErrorCategory.TOOL_ERROR, ErrorSeverity.MEDIUM

        return ErrorCategory.UNKNOWN, ErrorSeverity.MEDIUM

    async def handle_error(
        self,
        error: Exception,
        agent_id: str | None = None,
        workflow_id: str | None = None,
        metadata: dict[str, Any] | None = None
    ) -> Any:
        """Handle an error with appropriate recovery strategy."""
        # Classify error
        category, severity = self.classify_error(error)

        # Create error context
        context = ErrorContext(
            error=error,
            category=category,
            severity=severity,
            agent_id=agent_id,
            workflow_id=workflow_id,
            metadata=metadata
        )

        # Track error
        self.error_counts[category] = self.error_counts.get(category, 0) + 1

        # Get recovery strategy
        strategy = self.strategies.get(category)
        if not strategy:
            # No strategy registered, use default
            return await self._default_recovery(context)

        # Attempt recovery
        try:
            result = await strategy.handler(context)
            return result
        except Exception as recovery_error:
            # Recovery failed, try fallback
            if strategy.fallback:
                return await strategy.fallback(context)
            raise recovery_error

    async def _default_recovery(self, context: ErrorContext) -> Any:
        """Default recovery strategy when no specific strategy registered."""
        if context.severity == ErrorSeverity.CRITICAL:
            # Critical errors should not be recovered automatically
            raise context.error

        # Log and return None for non-critical errors
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in {context.agent_id}: {context.error}")
        return None
```

**Integration Example:**

```python
# src/agent_orchestration/unified_orchestrator.py

from .recovery.error_handler import (
    ErrorRecoveryFramework,
    RecoveryStrategy,
    ErrorCategory,
    ErrorContext
)

class UnifiedAgentOrchestrator:
    def __init__(self, ...):
        # ... existing init ...
        self.error_recovery = ErrorRecoveryFramework()
        self._register_recovery_strategies()

    def _register_recovery_strategies(self):
        """Register error recovery strategies."""
        # LLM error recovery
        self.error_recovery.register_strategy(RecoveryStrategy(
            name="llm_retry",
            category=ErrorCategory.LLM_ERROR,
            handler=self._recover_llm_error,
            max_retries=3,
            fallback=self._llm_fallback
        ))

        # Validation error recovery
        self.error_recovery.register_strategy(RecoveryStrategy(
            name="validation_fallback",
            category=ErrorCategory.VALIDATION_ERROR,
            handler=self._recover_validation_error,
            max_retries=1,
            fallback=self._validation_fallback
        ))

    async def _recover_llm_error(self, context: ErrorContext) -> Any:
        """Recover from LLM errors with retry and backoff."""
        import asyncio

        for attempt in range(3):
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            try:
                # Retry the operation
                # (implementation depends on context)
                return await self._retry_llm_call(context)
            except Exception:
                if attempt == 2:
                    raise

        return None

    async def _llm_fallback(self, context: ErrorContext) -> Any:
        """Fallback for LLM errors - use cached response or template."""
        # Return a safe, generic response
        return {
            "narrative": "I'm having trouble generating a response right now. Let's try something else.",
            "fallback": True
        }
```

---

### 1.3 Tool Execution Observability

**Purpose:** Enhanced visibility into tool execution for debugging and performance optimization.

**Location:** Extend `src/agent_orchestration/tools/metrics.py`

**Architecture:**

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ToolExecutionStatus(Enum):
    """Status of tool execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ToolExecutionTrace:
    """Detailed trace of a tool execution."""
    tool_name: str
    execution_id: str
    status: ToolExecutionStatus
    started_at: datetime
    ended_at: datetime | None = None
    duration_ms: float | None = None

    # Input/Output
    input_params: dict[str, Any] = field(default_factory=dict)
    output_result: Any | None = None
    error: str | None = None

    # Context
    agent_id: str | None = None
    workflow_id: str | None = None
    session_id: str | None = None

    # Metrics
    token_usage: dict[str, int] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class ToolObservabilityCollector:
    """
    Collects and manages tool execution observability data.

    Features:
    - Execution tracing
    - Performance metrics
    - Error tracking
    - Result validation logging
    """

    def __init__(self):
        self.traces: dict[str, ToolExecutionTrace] = {}
        self.metrics: dict[str, list[float]] = {}

    def start_execution(
        self,
        tool_name: str,
        input_params: dict[str, Any],
        agent_id: str | None = None,
        workflow_id: str | None = None
    ) -> str:
        """Start tracking a tool execution."""
        import uuid

        execution_id = str(uuid.uuid4())
        trace = ToolExecutionTrace(
            tool_name=tool_name,
            execution_id=execution_id,
            status=ToolExecutionStatus.RUNNING,
            started_at=datetime.utcnow(),
            input_params=input_params,
            agent_id=agent_id,
            workflow_id=workflow_id
        )

        self.traces[execution_id] = trace
        return execution_id

    def end_execution(
        self,
        execution_id: str,
        status: ToolExecutionStatus,
        output_result: Any | None = None,
        error: str | None = None
    ) -> None:
        """End tracking a tool execution."""
        trace = self.traces.get(execution_id)
        if not trace:
            return

        trace.ended_at = datetime.utcnow()
        trace.duration_ms = (trace.ended_at - trace.started_at).total_seconds() * 1000
        trace.status = status
        trace.output_result = output_result
        trace.error = error

        # Update metrics
        if trace.tool_name not in self.metrics:
            self.metrics[trace.tool_name] = []
        self.metrics[trace.tool_name].append(trace.duration_ms)

    def get_tool_metrics(self, tool_name: str) -> dict[str, Any]:
        """Get performance metrics for a tool."""
        durations = self.metrics.get(tool_name, [])
        if not durations:
            return {}

        return {
            "tool_name": tool_name,
            "execution_count": len(durations),
            "avg_duration_ms": sum(durations) / len(durations),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "p95_duration_ms": sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 1 else durations[0]
        }
```

---

## Next Steps

1. **Review and approve** this implementation plan
2. **Create feature branches** for each primitive
3. **Implement Phase 1** primitives (Context Window Manager, Error Recovery, Tool Observability)
4. **Write comprehensive tests** for each primitive
5. **Integrate with existing orchestrators** incrementally
6. **Monitor metrics** and iterate based on performance data

## Success Metrics

- **Context Window Manager:** Zero token limit errors, <10% context window waste
- **Error Recovery:** >95% error recovery success rate, <5% fallback usage
- **Tool Observability:** 100% tool execution visibility, <50ms observability overhead

---

**Status:** Ready for implementation
**Next Review:** After Phase 1 completion


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___architecture___docs architecture agentic primitives implementation plan]]
