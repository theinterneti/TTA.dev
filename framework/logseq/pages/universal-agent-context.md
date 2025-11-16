# universal-agent-context

**Package for WorkflowContext management and multi-agent coordination**

---

## Overview

`universal-agent-context` is a TTA.dev package providing advanced context management for agent-based workflows. It extends [[WorkflowContext]] with agent-specific features like session state, tool result caching, and multi-agent coordination.

**Status:** Production-ready
**License:** MIT
**Repository:** `packages/universal-agent-context/`

---

## Key Features

### 1. Enhanced Context Management
- **Session state**: Persistent state across multiple workflow executions
- **Tool result caching**: Cache expensive tool calls within sessions
- **Context inheritance**: Child contexts inherit parent state
- **Automatic cleanup**: Memory management and TTL expiration

### 2. Multi-Agent Coordination
- **Agent registration**: Register multiple agents with capabilities
- **Task routing**: Route tasks to appropriate agents
- **Result aggregation**: Combine results from multiple agents
- **Agent communication**: Inter-agent message passing

### 3. Observability Integration
- **Context propagation**: Automatic trace and span propagation
- **Agent metrics**: Track per-agent performance and costs
- **Session tracking**: Monitor session lifecycle and state
- **Correlation IDs**: Link related operations across agents

---

## Installation

### Using uv (Recommended)

```bash
uv add universal-agent-context
```

### Using pip

```bash
pip install universal-agent-context
```

### Development Installation

```bash
# Clone repository
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev/packages/universal-agent-context

# Install with dev dependencies
uv sync --all-extras
```

---

## Basic Usage

### Enhanced WorkflowContext

```python
from universal_agent_context import UniversalAgentContext

# Create context with session state
context = UniversalAgentContext(
    workflow_id="workflow-123",
    correlation_id="request-456",
    session_id="session-789",  # New: Session identifier
    user_id="user-abc",        # New: User tracking
)

# Store session state
context.set_state("conversation_history", [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
])

# Retrieve session state
history = context.get_state("conversation_history")

# Cache tool results
context.cache_tool_result(
    tool_name="web_search",
    args={"query": "TTA.dev primitives"},
    result={"results": [...], "count": 10},
    ttl=300  # 5 minutes
)

# Retrieve cached result
cached = context.get_cached_tool_result(
    tool_name="web_search",
    args={"query": "TTA.dev primitives"}
)
```

### Multi-Agent Workflow

```python
from universal_agent_context import AgentCoordinator, Agent

# Define agents
research_agent = Agent(
    name="research_agent",
    capabilities=["web_search", "document_retrieval"],
    cost_per_call=0.01
)

analysis_agent = Agent(
    name="analysis_agent",
    capabilities=["data_analysis", "summarization"],
    cost_per_call=0.02
)

# Create coordinator
coordinator = AgentCoordinator(
    agents=[research_agent, analysis_agent],
    context=context
)

# Route task to appropriate agent
task = {
    "type": "research",
    "query": "Latest AI trends",
    "required_capabilities": ["web_search"]
}

agent = coordinator.select_agent(task)
result = await agent.execute(task, context)
```

---

## Context Propagation Patterns

### Pattern 1: Sequential Workflow with State

```python
from universal_agent_context import UniversalAgentContext
from tta_dev_primitives import SequentialPrimitive

# Create context with initial state
context = UniversalAgentContext(
    workflow_id="rag-workflow",
    session_id="user-session-1"
)

# Store query in context
context.set_state("original_query", "What are TTA primitives?")

# Build workflow - state automatically propagates
workflow = (
    retrieve_documents >>  # Accesses original_query
    rerank_documents >>    # Accesses retrieval_results
    generate_response >>   # Accesses ranked_documents
    validate_response      # Accesses generated_response
)

# Execute - each step can access previous results via context
result = await workflow.execute({"query": query}, context)

# Check accumulated state
print(f"Documents retrieved: {context.get_state('retrieval_count')}")
print(f"Generation cost: ${context.get_state('total_cost')}")
```

### Pattern 2: Parallel Agent Execution

```python
from universal_agent_context import UniversalAgentContext
from tta_dev_primitives import ParallelPrimitive

# Create shared context
context = UniversalAgentContext(
    workflow_id="multi-agent-task",
    correlation_id="request-123"
)

# Each agent adds results to shared context
async def research_with_context(data, ctx):
    result = await research_agent.execute(data, ctx)
    ctx.set_state("research_results", result)
    return result

async def analysis_with_context(data, ctx):
    result = await analysis_agent.execute(data, ctx)
    ctx.set_state("analysis_results", result)
    return result

# Run in parallel
workflow = ParallelPrimitive([
    research_with_context,
    analysis_with_context
])

results = await workflow.execute({"task": "analyze trends"}, context)

# Aggregate results from context
final_result = {
    "research": context.get_state("research_results"),
    "analysis": context.get_state("analysis_results")
}
```

### Pattern 3: Context Inheritance

```python
# Parent context (user session)
parent_context = UniversalAgentContext(
    session_id="user-session-1",
    user_id="user-123"
)

parent_context.set_state("user_preferences", {
    "language": "en",
    "detail_level": "high"
})

# Child context (specific task)
child_context = parent_context.create_child(
    workflow_id="task-1"
)

# Child inherits parent state
prefs = child_context.get_state("user_preferences")
assert prefs["language"] == "en"

# Child can add own state without affecting parent
child_context.set_state("task_progress", 50)

# Parent doesn't see child state
assert parent_context.get_state("task_progress") is None
```

---

## Tool Result Caching

### Basic Caching

```python
from universal_agent_context import UniversalAgentContext

context = UniversalAgentContext(workflow_id="tool-workflow")

# Cache expensive tool call
async def cached_web_search(query: str):
    # Check cache first
    cached = context.get_cached_tool_result(
        tool_name="web_search",
        args={"query": query}
    )

    if cached:
        print("Cache hit!")
        return cached

    # Call expensive API
    result = await expensive_web_search_api(query)

    # Cache for 5 minutes
    context.cache_tool_result(
        tool_name="web_search",
        args={"query": query},
        result=result,
        ttl=300
    )

    return result

# First call - cache miss
result1 = await cached_web_search("TTA.dev")

# Second call - cache hit (within 5 min)
result2 = await cached_web_search("TTA.dev")
```

### Context-Aware Caching

```python
# Cache includes context variables
context.cache_tool_result(
    tool_name="llm_generate",
    args={
        "prompt": "Summarize this text",
        "context_vars": {
            "user_id": context.user_id,
            "language": context.get_state("language")
        }
    },
    result={"summary": "..."},
    ttl=600
)

# Different user or language = different cache entry
```

---

## Multi-Agent Coordination

### Agent Registration

```python
from universal_agent_context import Agent, AgentCapability

# Define agent with capabilities
code_agent = Agent(
    name="code_agent",
    capabilities=[
        AgentCapability("python_code_generation", quality=0.9),
        AgentCapability("code_review", quality=0.85),
        AgentCapability("unit_test_generation", quality=0.8)
    ],
    cost_per_call=0.05,
    latency_ms=2000
)

# Register with coordinator
coordinator.register_agent(code_agent)
```

### Task Routing

```python
# Route based on capabilities
task = {
    "type": "code_generation",
    "language": "python",
    "requirements": ["type_hints", "documentation"]
}

# Coordinator selects best agent
agent = coordinator.select_agent(
    task,
    selection_strategy="best_quality"  # or "lowest_cost", "fastest"
)

# Execute task
result = await agent.execute(task, context)
```

### Result Aggregation

```python
# Multi-agent task
task = {
    "type": "code_review",
    "code": source_code
}

# Route to multiple agents
agents = coordinator.select_agents(
    task,
    min_agents=2,
    selection_strategy="diverse"  # Different agent types
)

# Execute in parallel
results = await asyncio.gather(*[
    agent.execute(task, context)
    for agent in agents
])

# Aggregate results
aggregated = coordinator.aggregate_results(
    results,
    aggregation_strategy="consensus"  # or "weighted_average", "majority_vote"
)
```

---

## Session Management

### Session Lifecycle

```python
from universal_agent_context import SessionManager

# Create session manager
session_manager = SessionManager()

# Start new session
session = await session_manager.create_session(
    user_id="user-123",
    session_config={
        "max_duration_minutes": 30,
        "max_cost_dollars": 5.0,
        "allowed_tools": ["web_search", "code_generation"]
    }
)

# Get session context
context = session.get_context()

# Execute workflows with session context
result1 = await workflow1.execute(data1, context)
result2 = await workflow2.execute(data2, context)

# Check session status
print(f"Session cost: ${session.total_cost}")
print(f"Session duration: {session.duration_seconds}s")
print(f"Workflows executed: {session.workflow_count}")

# End session
await session_manager.end_session(session.id)
```

### Session State Persistence

```python
# Configure persistent storage
session_manager = SessionManager(
    storage_backend="redis",
    redis_url="redis://localhost:6379"
)

# Session state automatically persists
context.set_state("conversation_history", messages)

# Reconnect to session later
restored_session = await session_manager.get_session(session.id)
context = restored_session.get_context()

# State is restored
history = context.get_state("conversation_history")
```

---

## Observability Integration

### Context Tracing

```python
from universal_agent_context import UniversalAgentContext
from opentelemetry import trace

# Context automatically creates spans
context = UniversalAgentContext(
    workflow_id="traced-workflow",
    tracer=trace.get_tracer(__name__)
)

# Each workflow step creates nested spans
workflow = step1 >> step2 >> step3

# Trace hierarchy:
# traced-workflow
#   ├─ step1.execute
#   ├─ step2.execute
#   └─ step3.execute

await workflow.execute(data, context)
```

### Agent Metrics

```python
from universal_agent_context import AgentMetrics

# Track per-agent metrics
metrics = AgentMetrics(context)

# Automatically tracked:
# - agent.executions_total{agent_name="research_agent"}
# - agent.execution_duration_seconds{agent_name="research_agent"}
# - agent.execution_cost_dollars{agent_name="research_agent"}
# - agent.execution_errors_total{agent_name="research_agent"}

# Query metrics
total_cost = metrics.get_total_cost(agent_name="research_agent")
avg_latency = metrics.get_average_latency(agent_name="research_agent")
```

---

## Configuration

### Context Configuration

```python
from universal_agent_context import ContextConfig

config = ContextConfig(
    # Session settings
    session_ttl_seconds=1800,        # 30 minutes
    max_session_cost_dollars=10.0,

    # Cache settings
    tool_cache_ttl_seconds=300,      # 5 minutes
    tool_cache_max_size=1000,

    # Observability
    enable_tracing=True,
    enable_metrics=True,
    log_level="INFO",

    # Multi-agent
    agent_selection_strategy="best_quality",
    max_parallel_agents=5
)

context = UniversalAgentContext(
    workflow_id="configured",
    config=config
)
```

### Environment Variables

```bash
# Session configuration
AGENT_CONTEXT_SESSION_TTL=1800
AGENT_CONTEXT_MAX_SESSION_COST=10.0

# Cache configuration
AGENT_CONTEXT_CACHE_TTL=300
AGENT_CONTEXT_CACHE_MAX_SIZE=1000

# Storage backend
AGENT_CONTEXT_STORAGE_BACKEND=redis
AGENT_CONTEXT_REDIS_URL=redis://localhost:6379

# Observability
AGENT_CONTEXT_ENABLE_TRACING=true
AGENT_CONTEXT_ENABLE_METRICS=true
```

---

## Integration with TTA Primitives

### With CachePrimitive

```python
from tta_dev_primitives.performance import CachePrimitive
from universal_agent_context import UniversalAgentContext

# Context-aware caching
context = UniversalAgentContext(workflow_id="cached")

# Cache primitive uses context for key generation
cached_llm = CachePrimitive(
    primitive=llm_call,
    ttl_seconds=3600,
    key_fn=lambda data, ctx: f"{data['prompt']}_{ctx.user_id}"
)

# Different users get different cache entries
result = await cached_llm.execute({"prompt": "..."}, context)
```

### With RouterPrimitive

```python
from tta_dev_primitives.core import RouterPrimitive
from universal_agent_context import UniversalAgentContext

# Context-aware routing
def route_based_on_context(data, ctx):
    # Access user preferences from context
    prefs = ctx.get_state("user_preferences", {})

    if prefs.get("speed") == "fast":
        return "gpt-4-mini"
    elif prefs.get("quality") == "high":
        return "gpt-4"
    else:
        return "default"

router = RouterPrimitive(
    routes={
        "gpt-4-mini": fast_llm,
        "gpt-4": quality_llm,
        "default": balanced_llm
    },
    router_fn=route_based_on_context
)

# Routing considers context
result = await router.execute({"prompt": "..."}, context)
```

---

## Testing

### Unit Tests

```python
import pytest
from universal_agent_context import UniversalAgentContext

@pytest.mark.asyncio
async def test_context_state():
    context = UniversalAgentContext(workflow_id="test")

    # Test state management
    context.set_state("key", "value")
    assert context.get_state("key") == "value"

    # Test state isolation
    child = context.create_child(workflow_id="child")
    child.set_state("child_key", "child_value")

    assert child.get_state("key") == "value"  # Inherits parent
    assert context.get_state("child_key") is None  # Parent doesn't see child

@pytest.mark.asyncio
async def test_tool_caching():
    context = UniversalAgentContext(workflow_id="test")

    # Cache result
    context.cache_tool_result(
        tool_name="test_tool",
        args={"param": "value"},
        result={"data": "cached"},
        ttl=60
    )

    # Retrieve cached result
    cached = context.get_cached_tool_result(
        tool_name="test_tool",
        args={"param": "value"}
    )

    assert cached["data"] == "cached"
```

---

## Related Packages

- [[tta-dev-primitives]] - Core workflow primitives
- [[tta-observability-integration]] - Observability features

---

## Related Documentation

- [[WorkflowContext]] - Base context class
- [[TTA.dev/Multi-Agent Patterns]] - Multi-agent architecture patterns
- [[TTA.dev/Examples/Multi-Agent Workflow]] - Multi-agent example

---

## External Resources

- [Package README](../packages/universal-agent-context/README.md)
- [API Documentation](../packages/universal-agent-context/docs/)
- [GitHub Repository](https://github.com/theinterneti/TTA.dev)

---

**Status:** Production-ready
**License:** MIT
**Source:** `packages/universal-agent-context/`
**Tests:** `packages/universal-agent-context/tests/`
