# Multi-Agent Orchestration

**Patterns and primitives for coordinating multiple AI agents.**

## Overview

Multi-Agent Orchestration provides tools and patterns for building systems where multiple AI agents collaborate to solve complex problems.

## Orchestration Primitives

### Coordination Patterns
- [[TTA.dev/Orchestration/DelegationPrimitive]] - Orchestrator delegates to executors
- [[TTA.dev/Orchestration/MultiModelWorkflow]] - Coordinate multiple models
- [[TTA.dev/Orchestration/TaskClassifierPrimitive]] - Route tasks to specialists

### Context Management
- [[TTA.dev/Packages/universal-agent-context]] - Shared agent context
- [[TTA.dev/Concepts/WorkflowContext]] - Workflow state management

## Common Patterns

### Orchestrator-Executor Pattern
```python
workflow = DelegationPrimitive(
    orchestrator=planner_agent,  # Analyzes and creates plan
    executor=worker_agent         # Executes plan steps
)
```

### Specialist Routing
```python
workflow = (
    TaskClassifierPrimitive(
        routes={
            "code": code_specialist,
            "writing": writing_specialist,
            "analysis": analysis_specialist
        }
    )
)
```

### Parallel Agent Consensus
```python
workflow = (
    input_processor >>
    (agent1 | agent2 | agent3) >>  # Run agents in parallel
    consensus_aggregator            # Merge results
)
```

## Architecture Patterns

- **Hub and Spoke**: Central orchestrator, specialist agents
- **Pipeline**: Sequential agent chain with handoffs
- **Swarm**: Parallel agents with consensus
- **Hierarchical**: Nested orchestrators

## Related Topics

- [[TTA.dev/Primitives/RouterPrimitive]] - Dynamic routing
- [[TTA.dev/Primitives/ParallelPrimitive]] - Parallel execution
- [[TTA.dev/Examples/Multi-Agent Workflow]] - Code example

## Documentation

- `platform/agent-context/` - Agent context package
- [[TTA.dev/Guides/Multi-Agent Systems]] - Design guide
- [[TTA.dev/Patterns]] - Pattern catalog

## Tags

category:: orchestration
type:: multi-agent
