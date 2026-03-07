---
title: Agentic Primitives Quick Reference
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/architecture/agentic-primitives-quick-reference.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Architecture/Agentic Primitives Quick Reference]]

**For:** Developers implementing agentic primitives in TTA
**Last Updated:** 2025-10-20

## Overview

This quick reference provides code snippets and patterns for implementing and using agentic primitives in TTA. Use this as a cheat sheet during development.

---

## Context Window Manager

### Basic Usage

```python
from src.agent_orchestration.context.window_manager import (
    ContextWindowManager,
    ContextPruningStrategy
)

# Initialize manager
context_mgr = ContextWindowManager(
    max_tokens=8000,
    pruning_strategy=ContextPruningStrategy.HYBRID,
    pruning_threshold=0.8
)

# Create window
window = context_mgr.create_window()

# Add messages (auto-prunes when needed)
window = context_mgr.add_message(window, {
    "role": "system",
    "content": "You are a therapeutic AI..."
})

window = context_mgr.add_message(window, {
    "role": "user",
    "content": user_input
})

# Check utilization
print(f"Context: {window.utilization:.1%} full")
print(f"Remaining: {window.remaining_tokens} tokens")
```

### Integration with Orchestrator

```python
class UnifiedAgentOrchestrator:
    def __init__(self, ...):
        self.context_manager = ContextWindowManager(
            max_tokens=8000,
            pruning_strategy=ContextPruningStrategy.HYBRID
        )

    async def _build_prompt(self, state: OrchestrationState) -> str:
        # Create managed context window
        window = self.context_manager.create_window()

        # Add system prompt
        window = self.context_manager.add_message(window, {
            "role": "system",
            "content": self._get_system_prompt()
        })

        # Add conversation history (auto-pruned)
        for msg in state.therapeutic_context.get("history", []):
            window = self.context_manager.add_message(window, msg)

        # Add current input
        window = self.context_manager.add_message(window, {
            "role": "user",
            "content": state.user_input
        })

        return self._format_messages(window.messages)
```

### Custom Pruning Strategy

```python
from src.agent_orchestration.context.window_manager import ContextWindow

def custom_therapeutic_pruning(
    window: ContextWindow,
    needed_tokens: int
) -> ContextWindow:
    """Custom pruning that preserves therapeutic context."""
    # Always keep system message
    system_msgs = [m for m in window.messages if m.get("role") == "system"]

    # Keep recent therapeutic insights
    therapeutic_msgs = [
        m for m in window.messages
        if "therapeutic_insight" in m.get("metadata", {})
    ]

    # Keep most recent conversation
    recent_msgs = window.messages[-10:]

    # Combine and deduplicate
    preserved = system_msgs + therapeutic_msgs + recent_msgs
    # ... (implementation details)

    return window
```

---

## Error Recovery Framework

### Basic Usage

```python
from src.agent_orchestration.recovery.error_handler import (
    ErrorRecoveryFramework,
    RecoveryStrategy,
    ErrorCategory
)

# Initialize framework
error_recovery = ErrorRecoveryFramework()

# Register recovery strategies
error_recovery.register_strategy(RecoveryStrategy(
    name="llm_retry",
    category=ErrorCategory.LLM_ERROR,
    handler=recover_llm_error,
    max_retries=3,
    fallback=llm_fallback
))

# Handle errors
try:
    result = await some_agent_operation()
except Exception as e:
    result = await error_recovery.handle_error(
        error=e,
        agent_id="nga",
        workflow_id=workflow_id
    )
```

### Custom Recovery Strategy

```python
async def recover_llm_error(context: ErrorContext) -> Any:
    """Recover from LLM errors with exponential backoff."""
    import asyncio

    for attempt in range(3):
        # Exponential backoff
        await asyncio.sleep(2 ** attempt)

        try:
            # Retry with same parameters
            return await retry_llm_call(context.metadata["params"])
        except Exception as e:
            if attempt == 2:
                # Last attempt failed, raise
                raise
            # Log and continue
            logger.warning(f"Retry {attempt + 1} failed: {e}")

    return None

async def llm_fallback(context: ErrorContext) -> Any:
    """Fallback when all retries fail."""
    # Return cached response or safe default
    return {
        "narrative": "I'm having trouble right now. Let's try something else.",
        "fallback": True,
        "safe": True
    }
```

### Integration with Agents

```python
class NGAAdapter:
    def __init__(self, error_recovery: ErrorRecoveryFramework):
        self.error_recovery = error_recovery

    async def generate_narrative(
        self,
        prompt: str,
        context: dict
    ) -> dict:
        try:
            # Attempt narrative generation
            result = await self._call_llm(prompt, context)
            return result
        except Exception as e:
            # Use error recovery framework
            return await self.error_recovery.handle_error(
                error=e,
                agent_id="nga",
                metadata={"prompt": prompt, "context": context}
            )
```

---

## Tool Execution Observability

### Basic Usage

```python
from src.agent_orchestration.tools.metrics import (
    ToolObservabilityCollector,
    ToolExecutionStatus
)

# Initialize collector
tool_observer = ToolObservabilityCollector()

# Start tracking execution
execution_id = tool_observer.start_execution(
    tool_name="world_state_query",
    input_params={"query": "get_location", "entity": "player"},
    agent_id="wba",
    workflow_id=workflow_id
)

try:
    # Execute tool
    result = await execute_tool(params)

    # End tracking (success)
    tool_observer.end_execution(
        execution_id=execution_id,
        status=ToolExecutionStatus.SUCCESS,
        output_result=result
    )
except Exception as e:
    # End tracking (failure)
    tool_observer.end_execution(
        execution_id=execution_id,
        status=ToolExecutionStatus.FAILED,
        error=str(e)
    )

# Get metrics
metrics = tool_observer.get_tool_metrics("world_state_query")
print(f"Avg duration: {metrics['avg_duration_ms']:.2f}ms")
```

### Decorator Pattern

```python
from functools import wraps

def observe_tool_execution(tool_name: str):
    """Decorator to automatically track tool execution."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Start tracking
            execution_id = tool_observer.start_execution(
                tool_name=tool_name,
                input_params=kwargs
            )

            try:
                # Execute function
                result = await func(*args, **kwargs)

                # End tracking (success)
                tool_observer.end_execution(
                    execution_id=execution_id,
                    status=ToolExecutionStatus.SUCCESS,
                    output_result=result
                )

                return result
            except Exception as e:
                # End tracking (failure)
                tool_observer.end_execution(
                    execution_id=execution_id,
                    status=ToolExecutionStatus.FAILED,
                    error=str(e)
                )
                raise

        return wrapper
    return decorator

# Usage
@observe_tool_execution("neo4j_query")
async def query_neo4j(query: str, params: dict) -> list:
    # Tool implementation
    pass
```

### Integration with Tool Registry

```python
class ToolInvocationService:
    def __init__(self, observer: ToolObservabilityCollector):
        self.observer = observer

    async def invoke_tool(
        self,
        tool_name: str,
        params: dict,
        context: dict
    ) -> Any:
        # Start observability tracking
        execution_id = self.observer.start_execution(
            tool_name=tool_name,
            input_params=params,
            agent_id=context.get("agent_id"),
            workflow_id=context.get("workflow_id")
        )

        try:
            # Get tool from registry
            tool = self.registry.get_tool(tool_name)

            # Execute tool
            result = await tool.execute(params)

            # Validate result
            if not self._validate_result(result):
                raise ValueError(f"Invalid result from {tool_name}")

            # End tracking (success)
            self.observer.end_execution(
                execution_id=execution_id,
                status=ToolExecutionStatus.SUCCESS,
                output_result=result
            )

            return result
        except Exception as e:
            # End tracking (failure)
            self.observer.end_execution(
                execution_id=execution_id,
                status=ToolExecutionStatus.FAILED,
                error=str(e)
            )
            raise
```

---

## Common Patterns

### Pattern 1: Orchestrator with All Primitives

```python
class EnhancedOrchestrator:
    """Orchestrator using all agentic primitives."""

    def __init__(self):
        # Context management
        self.context_manager = ContextWindowManager(
            max_tokens=8000,
            pruning_strategy=ContextPruningStrategy.HYBRID
        )

        # Error recovery
        self.error_recovery = ErrorRecoveryFramework()
        self._register_recovery_strategies()

        # Tool observability
        self.tool_observer = ToolObservabilityCollector()

    async def process_input(
        self,
        user_input: str,
        session_id: str
    ) -> dict:
        """Process user input with full primitive support."""
        try:
            # 1. Build context-managed prompt
            window = self.context_manager.create_window()
            window = self._add_conversation_history(window, session_id)
            window = self.context_manager.add_message(window, {
                "role": "user",
                "content": user_input
            })

            # 2. Execute with tool observability
            execution_id = self.tool_observer.start_execution(
                tool_name="process_input",
                input_params={"input": user_input}
            )

            # 3. Process with error recovery
            result = await self._process_with_recovery(window)

            # 4. Track success
            self.tool_observer.end_execution(
                execution_id=execution_id,
                status=ToolExecutionStatus.SUCCESS,
                output_result=result
            )

            return result

        except Exception as e:
            # Error recovery handles this
            return await self.error_recovery.handle_error(
                error=e,
                agent_id="orchestrator",
                metadata={"input": user_input}
            )
```

### Pattern 2: Therapeutic Safety Integration

```python
async def process_with_safety(
    orchestrator: EnhancedOrchestrator,
    user_input: str,
    session_id: str
) -> dict:
    """Process input with therapeutic safety checks."""
    # Build context
    window = orchestrator.context_manager.create_window()

    # Add safety context
    window = orchestrator.context_manager.add_message(window, {
        "role": "system",
        "content": "Maintain therapeutic safety. Flag concerning content."
    })

    # Add user input
    window = orchestrator.context_manager.add_message(window, {
        "role": "user",
        "content": user_input
    })

    try:
        # Process with safety validation
        result = await orchestrator.process_input(user_input, session_id)

        # Validate safety
        safety_level = await validate_safety(result)
        if safety_level == SafetyLevel.UNSAFE:
            # Use error recovery for safety issues
            raise ValidationError("Unsafe content detected")

        return result

    except ValidationError as e:
        # Recovery framework handles safety fallback
        return await orchestrator.error_recovery.handle_error(
            error=e,
            agent_id="safety_validator",
            metadata={"input": user_input, "result": result}
        )
```

---

## Testing Patterns

### Testing Context Window Manager

```python
def test_context_pruning():
    """Test automatic context pruning."""
    manager = ContextWindowManager(
        max_tokens=100,
        pruning_threshold=0.5
    )

    window = manager.create_window()

    # Add messages until pruning triggers
    for i in range(20):
        window = manager.add_message(window, {
            "role": "user",
            "content": f"Message {i}" * 10
        })

    # Should have pruned
    assert window.utilization <= 1.0
    assert len(window.messages) < 20
```

### Testing Error Recovery

```python
@pytest.mark.asyncio
async def test_error_recovery():
    """Test error recovery with retry."""
    recovery = ErrorRecoveryFramework()

    # Register test strategy
    recovery.register_strategy(RecoveryStrategy(
        name="test_retry",
        category=ErrorCategory.LLM_ERROR,
        handler=mock_retry_handler,
        max_retries=3
    ))

    # Simulate error
    error = Exception("Rate limit exceeded")
    result = await recovery.handle_error(error)

    # Should have recovered
    assert result is not None
```

### Testing Tool Observability

```python
def test_tool_metrics():
    """Test tool metrics collection."""
    observer = ToolObservabilityCollector()

    # Simulate executions
    for i in range(10):
        exec_id = observer.start_execution(
            tool_name="test_tool",
            input_params={"test": i}
        )
        observer.end_execution(
            execution_id=exec_id,
            status=ToolExecutionStatus.SUCCESS
        )

    # Check metrics
    metrics = observer.get_tool_metrics("test_tool")
    assert metrics["execution_count"] == 10
    assert "avg_duration_ms" in metrics
```

---

## Configuration

### Environment Variables

```bash
# Context Window Manager
CONTEXT_MAX_TOKENS=8000
CONTEXT_PRUNING_STRATEGY=hybrid
CONTEXT_PRUNING_THRESHOLD=0.8

# Error Recovery
ERROR_RECOVERY_MAX_RETRIES=3
ERROR_RECOVERY_BACKOFF_BASE=2

# Tool Observability
TOOL_OBSERVABILITY_ENABLED=true
TOOL_METRICS_RETENTION_DAYS=30
```

### Configuration File

```yaml
# tta_config.yaml

agent_orchestration:
  context_management:
    max_tokens: 8000
    pruning_strategy: hybrid
    pruning_threshold: 0.8
    summarization_enabled: true

  error_recovery:
    enabled: true
    max_retries: 3
    backoff_base: 2
    fallback_enabled: true

  tool_observability:
    enabled: true
    trace_all_tools: true
    metrics_retention_days: 30
    performance_alerts: true
```

---

## Troubleshooting

### Context Window Issues

**Problem:** Token limit exceeded
**Solution:** Check `pruning_threshold`, ensure auto-pruning enabled

**Problem:** Important context lost
**Solution:** Implement custom pruning strategy that preserves critical messages

### Error Recovery Issues

**Problem:** Errors not recovering
**Solution:** Check recovery strategy registration, verify error classification

**Problem:** Too many retries
**Solution:** Adjust `max_retries`, implement circuit breaker

### Tool Observability Issues

**Problem:** Missing metrics
**Solution:** Ensure `start_execution` and `end_execution` called for all tools

**Problem:** High overhead
**Solution:** Use async logging, batch metrics updates

---

## Resources

- **Full Analysis:** `docs/architecture/agentic-primitives-analysis.md`
- **Implementation Plan:** `docs/architecture/agentic-primitives-implementation-plan.md`
- **Recommendations:** `docs/architecture/agentic-primitives-recommendations.md`
- **GitHub Blog:** [How to build reliable AI workflows](https://github.blog/ai-and-ml/github-copilot/how-to-build-reliable-ai-workflows-with-agentic-primitives-and-context-engineering/)

---

**Last Updated:** 2025-10-20
**Maintainer:** Development Team


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___architecture___docs architecture agentic primitives quick reference]]
