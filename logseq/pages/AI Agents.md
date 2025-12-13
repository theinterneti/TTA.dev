# AI Agents

**Tag page for AI agents, agentic patterns, and multi-agent systems**

---

## Overview

**AI Agents** in TTA.dev include:
- 🤖 Agent primitives
- 🔄 Agent orchestration
- 🧠 Agent coordination
- 💬 Multi-agent workflows
- 🎯 Agent patterns

**Goal:** Build reliable, observable, composable AI agent systems.

**See:** [[universal-agent-context]], [[TTA Primitives/DelegationPrimitive]]

---

## Pages Tagged with #AI-Agents

{{query (page-tags [[AI Agents]])}}

---

## Agent Categories

### 1. Single-Agent Patterns

**Individual agent workflows:**

**Task Execution Agent:**
```python
from tta_dev_primitives import WorkflowContext

async def task_agent(task: str) -> dict:
    """Execute a single task."""
    workflow = (
        understand_task >>
        plan_execution >>
        execute_plan >>
        validate_result
    )

    context = WorkflowContext(correlation_id=f"task-{task}")
    result = await workflow.execute({"task": task}, context)
    return result
```

**Retrieval Agent:**
```python
async def retrieval_agent(query: str) -> list[dict]:
    """Retrieve relevant documents."""
    workflow = (
        embed_query >>
        search_vector_db >>
        rank_results >>
        return_top_k
    )

    result = await workflow.execute({"query": query}, context)
    return result
```

**See:** [[TTA Primitives]]

---

### 2. Multi-Agent Patterns

**Coordinated agent systems:**

**Orchestrator-Executor Pattern:**
```python
from tta_dev_primitives.orchestration import DelegationPrimitive

async def orchestrated_workflow():
    """Orchestrator plans, executors work."""
    workflow = DelegationPrimitive(
        orchestrator=claude_sonnet,  # Smart planner
        executor=gemini_flash         # Fast executor
    )

    result = await workflow.execute(complex_task, context)
    return result
```

**Benefits:**
- Clear separation of concerns
- Optimized model selection
- Cost efficiency (30-40% reduction)
- Better quality outcomes

**See:** [[TTA Primitives/DelegationPrimitive]]

---

**Parallel Agent Execution:**
```python
async def parallel_agents():
    """Multiple agents work simultaneously."""
    workflow = (
        research_agent |
        analysis_agent |
        synthesis_agent
    ) >> aggregator_agent

    # All agents run concurrently
    results = await workflow.execute(query, context)
    return results
```

**See:** [[TTA Primitives/ParallelPrimitive]]

---

**Sequential Agent Pipeline:**
```python
async def agent_pipeline():
    """Agents pass work down pipeline."""
    workflow = (
        intake_agent >>
        classification_agent >>
        routing_agent >>
        execution_agent >>
        validation_agent
    )

    result = await workflow.execute(input_data, context)
    return result
```

**See:** [[TTA Primitives/SequentialPrimitive]]

---

### 3. Agent Coordination

**Task distribution and coordination:**

**Task Classifier:**
```python
from tta_dev_primitives.orchestration import TaskClassifierPrimitive

async def classify_and_route():
    """Classify tasks, route to specialist agents."""
    classifier = TaskClassifierPrimitive(
        classifier_model=gpt4_mini,
        agents={
            "code": code_specialist_agent,
            "analysis": analysis_agent,
            "creative": creative_agent
        }
    )

    result = await classifier.execute(task, context)
    return result
```

**See:** [[TTA Primitives/TaskClassifierPrimitive]]

---

**Multi-Model Workflow:**
```python
from tta_dev_primitives.orchestration import MultiModelWorkflow

async def multi_model_agent():
    """Coordinate multiple models intelligently."""
    workflow = MultiModelWorkflow(
        models={
            "fast": gpt4_mini,
            "quality": gpt4,
            "code": claude_sonnet
        },
        coordinator=gpt4_mini
    )

    result = await workflow.execute(request, context)
    return result
```

**See:** [[TTA Primitives/MultiModelWorkflow]]

---

### 4. Agent Context Management

**State and memory for agents:**

**Agent Context:**
```python
from universal_agent_context import AgentContext

async def stateful_agent():
    """Agent with memory and context."""
    # Create agent context
    agent_ctx = AgentContext(
        agent_id="research-agent-001",
        session_id="session-123"
    )

    # Track history
    agent_ctx.add_message("user", "Research topic X")
    agent_ctx.add_message("assistant", "Found 3 papers...")

    # Use in workflow
    workflow = research_agent >> synthesize_agent
    result = await workflow.execute(query, agent_ctx)
    return result
```

**See:** [[universal-agent-context]]

---

**Conversational Memory:**
```python
from tta_dev_primitives.performance import MemoryPrimitive

async def conversational_agent():
    """Agent with conversation memory."""
    memory = MemoryPrimitive(max_size=100)

    # Store conversation
    await memory.add("turn_1", {
        "role": "user",
        "content": "What is a primitive?"
    })

    # Search history for context
    history = await memory.search(keywords=["primitive"])

    # Generate response with context
    workflow = (
        retrieve_history >>
        generate_response >>
        store_response
    )

    result = await workflow.execute(user_input, context)
    return result
```

**See:** [[TTA Primitives/MemoryPrimitive]]

---

## Agent Design Patterns

### Pattern: Orchestrator + Executors

**Smart planning, efficient execution:**

```python
from tta_dev_primitives.orchestration import DelegationPrimitive

# Orchestrator: Smart model for planning
orchestrator = claude_sonnet  # $15/M tokens

# Executors: Fast models for execution
executor = gemini_flash      # $0.075/M tokens

# Compose
workflow = DelegationPrimitive(
    orchestrator=orchestrator,
    executor=executor
)

# Cost savings: 30-40% vs using claude_sonnet for everything
result = await workflow.execute(complex_task, context)
```

**When to use:**
- Complex multi-step tasks
- Cost optimization needed
- Quality + speed balance
- Clear plan/execute split

---

### Pattern: Specialist Agents

**Route to domain experts:**

```python
from tta_dev_primitives.core import RouterPrimitive

# Define specialist agents
specialists = {
    "code": claude_sonnet,      # Best for code
    "analysis": gpt4,           # Best for analysis
    "creative": gemini_pro,     # Best for creative
    "fast": gpt4_mini           # Best for simple
}

# Route to specialist
router = RouterPrimitive(
    routes=specialists,
    router_fn=classify_task,
    default="fast"
)

# Automatic specialist selection
result = await router.execute(task, context)
```

**When to use:**
- Different task types
- Model strengths vary
- Cost optimization
- Quality requirements differ

---

### Pattern: Collaborative Agents

**Agents work together:**

```python
async def collaborative_workflow():
    """Agents collaborate on complex problem."""
    # Phase 1: Parallel research
    research_results = await (
        web_research_agent |
        paper_research_agent |
        code_research_agent
    ).execute(topic, context)

    # Phase 2: Sequential synthesis
    workflow = (
        aggregation_agent >>
        analysis_agent >>
        synthesis_agent >>
        validation_agent
    )

    final_result = await workflow.execute(research_results, context)
    return final_result
```

**When to use:**
- Complex problems
- Multiple perspectives needed
- Comprehensive coverage
- Quality critical

---

### Pattern: Agent Pipeline

**Sequential processing with agents:**

```python
async def agent_pipeline():
    """Multi-stage agent pipeline."""
    pipeline = (
        intake_agent >>          # Understand request
        planning_agent >>        # Create plan
        execution_agent >>       # Execute plan
        validation_agent >>      # Validate results
        formatting_agent         # Format output
    )

    result = await pipeline.execute(request, context)
    return result
```

**When to use:**
- Clear stages
- Sequential dependencies
- Quality gates
- Iterative refinement

---

## Agent Observability

### Tracing Agent Workflows

**OpenTelemetry for agents:**

```python
from opentelemetry import trace

async def observable_agent():
    """Agent with full tracing."""
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("agent_workflow") as span:
        # Add agent metadata
        span.set_attribute("agent.type", "orchestrator")
        span.set_attribute("agent.model", "claude-sonnet")

        # Execute workflow
        workflow = orchestrator >> executor
        result = await workflow.execute(task, context)

        # Record completion
        span.set_attribute("agent.result_size", len(result))
        span.add_event("agent_completed")

        return result
```

**See:** [[TTA.dev/Observability]]

---

### Agent Metrics

**Prometheus metrics for agents:**

```python
from prometheus_client import Counter, Histogram

# Agent execution metrics
agent_executions = Counter(
    'agent_executions_total',
    'Total agent executions',
    ['agent_type', 'agent_model', 'status']
)

agent_duration = Histogram(
    'agent_duration_seconds',
    'Agent execution duration',
    ['agent_type']
)

# Cost tracking
agent_cost = Counter(
    'agent_cost_usd_total',
    'Total agent cost in USD',
    ['agent_model']
)
```

**Query Examples:**
```promql
# Agent success rate
sum(rate(agent_executions_total{status="success"}[5m])) /
sum(rate(agent_executions_total[5m]))

# Agent latency P95
histogram_quantile(0.95, agent_duration_seconds)

# Agent cost per day
sum(increase(agent_cost_usd_total[1d]))
```

---

## Agent TODOs

### Agent Development TODOs

**Agent-related tasks:**

{{query (and (task TODO DOING) [[#dev-todo]] (property type "agent"))}}

---

## Agent Best Practices

### ✅ DO

**Use Right Model for Job:**
```python
# ✅ Good: Orchestrator + executor
workflow = DelegationPrimitive(
    orchestrator=smart_model,  # Planning
    executor=fast_model        # Execution
)

# Cost: 30-40% lower
# Quality: Same or better
```

**Add Observability:**
```python
# ✅ Good: Full tracing
from observability_integration import initialize_observability

initialize_observability(service_name="agent-system")

# All agents automatically traced
workflow = agent1 >> agent2 >> agent3
```

**Implement Error Handling:**
```python
# ✅ Good: Recovery patterns
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive

workflow = (
    RetryPrimitive(max_retries=3) >>
    FallbackPrimitive(
        primary=primary_agent,
        fallbacks=[backup_agent]
    )
)
```

---

### ❌ DON'T

**Don't Use Expensive Models Everywhere:**
```python
# ❌ Bad: GPT-4 for everything
workflow = gpt4 >> gpt4 >> gpt4  # $$$

# ✅ Good: Tiered models
workflow = gpt4_mini >> router >> validator
```

**Don't Ignore Context:**
```python
# ❌ Bad: No context
result = await agent(query)

# ✅ Good: With context
context = WorkflowContext(
    correlation_id="session-123",
    data={"user_id": "user-789"}
)
result = await agent.execute(query, context)
```

**Don't Skip Validation:**
```python
# ❌ Bad: Trust agent output
return agent_result

# ✅ Good: Validate output
workflow = (
    agent >>
    validator >>
    sanitizer
)
```

---

## Agent Examples

### Basic Agent

**Simple task agent:**

```python
from tta_dev_primitives import WorkflowContext

async def basic_agent(task: str) -> str:
    """Execute simple task."""
    workflow = (
        parse_task >>
        execute_task >>
        format_result
    )

    context = WorkflowContext(correlation_id=f"task-{task}")
    result = await workflow.execute({"task": task}, context)
    return result
```

**See:** `platform/primitives/examples/basic_agent.py`

---

### Multi-Agent System

**Coordinated agents:**

```python
from tta_dev_primitives.orchestration import DelegationPrimitive

async def multi_agent_system(query: str) -> dict:
    """Multi-agent collaboration."""
    # Research phase (parallel)
    research = (
        web_agent |
        paper_agent |
        code_agent
    )

    # Synthesis phase (sequential)
    synthesis = DelegationPrimitive(
        orchestrator=planning_agent,
        executor=synthesis_agent
    )

    # Complete workflow
    workflow = research >> synthesis

    context = WorkflowContext(correlation_id=f"query-{query}")
    result = await workflow.execute({"query": query}, context)
    return result
```

**See:** `platform/primitives/examples/multi_agent_workflow.py`

---

### RAG Agent

**Retrieval-augmented generation:**

```python
async def rag_agent(query: str) -> str:
    """RAG with agent patterns."""
    workflow = (
        CachePrimitive(ttl_seconds=3600) >>      # Cache embeddings
        retrieval_agent >>                        # Find documents
        RouterPrimitive(                          # Route to model
            routes={"simple": gpt4_mini, "complex": gpt4}
        ) >>
        synthesis_agent >>                        # Generate answer
        validation_agent                          # Validate output
    )

    result = await workflow.execute({"query": query}, context)
    return result
```

**See:** `platform/primitives/examples/agentic_rag_workflow.py`

---

## Agent Tools

### Agent Development Tools

**GitHub Copilot Toolsets:**
- `#tta-agent-dev` - Agent development tools
- `#tta-mcp-integration` - MCP server integration
- `#tta-observability` - Agent observability

**See:** [[MCP_SERVERS]], [[.vscode/copilot-toolsets.jsonc]]

---

### Agent Testing Tools

**Testing agents:**

```python
from tta_dev_primitives.testing import MockPrimitive

async def test_agent():
    """Test agent workflow."""
    # Mock LLM
    mock_llm = MockPrimitive(
        return_value={"output": "test response"}
    )

    # Test workflow
    workflow = preprocessing >> mock_llm >> postprocessing
    result = await workflow.execute(test_input, context)

    # Assertions
    assert mock_llm.call_count == 1
    assert result["output"] == "test response"
```

**See:** [[Testing]], [[TTA Primitives/MockPrimitive]]

---

## Related Concepts

- [[TTA Primitives]] - Primitive building blocks
- [[universal-agent-context]] - Agent context package
- [[TTA Primitives/DelegationPrimitive]] - Orchestrator pattern
- [[TTA Primitives/TaskClassifierPrimitive]] - Task routing
- [[TTA Primitives/MultiModelWorkflow]] - Multi-model coordination
- [[Workflow]] - Workflow patterns
- [[Orchestration]] - Orchestration primitives

---

## Documentation

- [[AGENTS]] - Agent instructions
- [[TTA.dev/Agent Patterns]] - Agent pattern guide
- [[universal-agent-context]] - Context package docs
- [[PRIMITIVES_CATALOG]] - Primitive reference
- [[MCP_SERVERS]] - MCP integration

---

**Tags:** #ai-agents #agents #multi-agent #orchestration #coordination #index-page

**Last Updated:** 2025-11-05
**Maintained by:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Logseq/Pages/Ai agents]]
