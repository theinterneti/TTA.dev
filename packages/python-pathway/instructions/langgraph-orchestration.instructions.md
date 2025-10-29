---
applyTo:
  - pattern: "src/agent_orchestration/**/*.py"
  - pattern: "**/*_workflow.py"
  - pattern: "**/*_orchestrator.py"
tags: ["python", "langgraph", "orchestration", "workflows", "async"]
description: "LangGraph workflow patterns, state management, and agent orchestration guidelines for TTA"
---

# LangGraph Orchestration Standards

## Overview

This instruction set defines standards for implementing LangGraph workflows and agent orchestration in TTA. All orchestration code must follow LangGraph best practices and maintain clear state management.

## Core Principles

### 1. State Management
- Use LangGraph's state management for workflow state
- Keep state immutable where possible
- Use TypedDict for state schema definition
- Document all state transitions

### 2. Workflow Design
- Keep workflows focused and single-purpose
- Use subgraphs for complex workflows
- Implement proper error handling and recovery
- Log all workflow transitions

### 3. Agent Coordination
- Use LangGraph's built-in agent patterns
- Implement proper tool calling conventions
- Handle tool errors gracefully
- Maintain agent context across steps

## Implementation Standards

### Workflow Definition

```python
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated

class WorkflowState(TypedDict):
    """Define workflow state schema."""
    player_id: str
    narrative_context: str
    player_input: str
    ai_response: str
    safety_validated: bool
    step_count: int

# Create workflow graph
workflow = StateGraph(WorkflowState)

# Add nodes
workflow.add_node("validate_input", validate_input_node)
workflow.add_node("generate_response", generate_response_node)
workflow.add_node("validate_safety", validate_safety_node)

# Add edges
workflow.add_edge("validate_input", "generate_response")
workflow.add_edge("generate_response", "validate_safety")
workflow.add_edge("validate_safety", END)

# Compile
graph = workflow.compile()
```

### Async Workflow Execution

```python
async def execute_workflow(
    player_id: str,
    player_input: str,
    context: dict
) -> WorkflowResult:
    """Execute workflow asynchronously.
    
    Args:
        player_id: Player identifier
        player_input: Player's input text
        context: Workflow context
    
    Returns:
        WorkflowResult with final state
    """
    initial_state = WorkflowState(
        player_id=player_id,
        player_input=player_input,
        narrative_context=context.get("narrative", ""),
        ai_response="",
        safety_validated=False,
        step_count=0
    )
    
    result = await graph.ainvoke(initial_state)
    return WorkflowResult(result)
```

## Testing Requirements

### Unit Tests
- Test individual workflow nodes
- Test state transitions
- Test error handling
- Minimum 80% coverage for orchestration code

### Integration Tests
- Test complete workflow execution
- Test with real agents and tools
- Test error recovery
- Test performance under load

### Async Testing
```python
@pytest.mark.asyncio
async def test_workflow_execution():
    """Test workflow execution."""
    result = await execute_workflow(
        player_id="test_player",
        player_input="Hello",
        context={}
    )
    assert result.success
    assert result.state.safety_validated
```

## Performance Considerations

### Optimization Patterns
- Use streaming for long-running operations
- Implement caching for repeated computations
- Monitor workflow execution time
- Set reasonable timeouts for tool calls

### Monitoring
```python
# Log workflow metrics
logger.info(
    "workflow_executed",
    player_id=player_id,
    execution_time_ms=execution_time,
    step_count=step_count,
    success=result.success
)
```

## Error Handling

### Graceful Degradation
```python
# ✅ Correct: Handle errors gracefully
try:
    response = await agent.invoke(state)
except ToolError as e:
    logger.error(f"Tool error: {e}")
    response = await get_fallback_response(state)
```

### Retry Logic
- Implement exponential backoff for transient errors
- Set maximum retry attempts
- Log all retry attempts
- Fail gracefully after max retries

## Code Review Checklist

- [ ] State schema clearly defined
- [ ] All state transitions documented
- [ ] Error handling comprehensive
- [ ] Async/await properly used
- [ ] Tests passing (>80% coverage)
- [ ] Performance acceptable
- [ ] Logging comprehensive
- [ ] Documentation updated

## Common Patterns

### Conditional Routing
```python
def route_based_on_safety(state: WorkflowState) -> str:
    """Route workflow based on safety validation."""
    if state.safety_validated:
        return "deliver_response"
    else:
        return "handle_unsafe_content"

workflow.add_conditional_edges(
    "validate_safety",
    route_based_on_safety
)
```

### Subgraph Composition
```python
# Create subgraph for complex logic
subgraph = StateGraph(WorkflowState)
# ... add nodes and edges ...
compiled_subgraph = subgraph.compile()

# Use in main workflow
workflow.add_node("complex_logic", compiled_subgraph.invoke)
```

## References

- LangGraph Documentation: https://langchain-ai.github.io/langgraph/
- Async Python: https://docs.python.org/3/library/asyncio.html
- TTA Architecture: `Documentation/architecture/`

