# TTA.dev/Examples/Multi-Agent Workflow

**Production-ready multi-agent coordination with task classification, parallel execution, and result aggregation.**

## Overview

Multi-agent workflow demonstrates coordinating multiple specialized agents using TTA.dev primitives for intelligent task routing and parallel execution.

**Source:** `packages/tta-dev-primitives/examples/multi_agent_workflow.py`

## Complete Example

```python
from tta_dev_primitives import SequentialPrimitive, ParallelPrimitive, WorkflowContext
from tta_dev_primitives.core import RouterPrimitive, ConditionalPrimitive
from tta_dev_primitives.recovery import RetryPrimitive, TimeoutPrimitive
import structlog

logger = structlog.get_logger()

# Agent 1: Research Agent
async def research_agent(data: dict, context: WorkflowContext) -> dict:
    """Research agent for information gathering."""
    task = data.get("task", "")

    logger.info("research_agent_started", task=task)

    # Simulate research
    research_results = {
        "findings": [
            "Finding 1: Relevant information...",
            "Finding 2: Additional context...",
            "Finding 3: Supporting evidence..."
        ],
        "sources": ["source1.com", "source2.org"],
        "confidence": 0.85
    }

    return {
        "task": task,
        "agent": "research",
        "results": research_results,
        "status": "completed"
    }

# Agent 2: Analysis Agent
async def analysis_agent(data: dict, context: WorkflowContext) -> dict:
    """Analysis agent for data processing."""
    task = data.get("task", "")

    logger.info("analysis_agent_started", task=task)

    # Simulate analysis
    analysis_results = {
        "insights": [
            "Pattern identified in data",
            "Trend: upward trajectory",
            "Anomaly detected at timestamp X"
        ],
        "metrics": {"accuracy": 0.92, "confidence": 0.88},
        "recommendations": ["Action 1", "Action 2"]
    }

    return {
        "task": task,
        "agent": "analysis",
        "results": analysis_results,
        "status": "completed"
    }

# Agent 3: Coding Agent
async def coding_agent(data: dict, context: WorkflowContext) -> dict:
    """Coding agent for implementation tasks."""
    task = data.get("task", "")

    logger.info("coding_agent_started", task=task)

    # Simulate code generation
    code_results = {
        "code": "def solution():\n    # Implementation\n    pass",
        "language": "python",
        "tests": ["test_1", "test_2"],
        "coverage": 0.95
    }

    return {
        "task": task,
        "agent": "coding",
        "results": code_results,
        "status": "completed"
    }

# Agent 4: Writing Agent
async def writing_agent(data: dict, context: WorkflowContext) -> dict:
    """Writing agent for content generation."""
    task = data.get("task", "")

    logger.info("writing_agent_started", task=task)

    # Simulate writing
    writing_results = {
        "content": "Generated content based on requirements...",
        "word_count": 500,
        "tone": "professional",
        "readability_score": 8.5
    }

    return {
        "task": task,
        "agent": "writing",
        "results": writing_results,
        "status": "completed"
    }

# Task Classifier
async def classify_task(data: dict, context: WorkflowContext) -> dict:
    """Classify task and determine appropriate agent(s)."""
    task = data.get("task", "")

    # Simple keyword-based classification
    task_lower = task.lower()

    if any(word in task_lower for word in ["research", "find", "gather", "investigate"]):
        task_type = "research"
    elif any(word in task_lower for word in ["analyze", "process", "evaluate", "compare"]):
        task_type = "analysis"
    elif any(word in task_lower for word in ["code", "implement", "program", "develop"]):
        task_type = "coding"
    elif any(word in task_lower for word in ["write", "draft", "compose", "document"]):
        task_type = "writing"
    else:
        task_type = "general"

    logger.info("task_classified", task=task, task_type=task_type)

    return {
        "task": task,
        "task_type": task_type,
        "original_data": data
    }

# Result Aggregator
async def aggregate_results(data: dict, context: WorkflowContext) -> dict:
    """Aggregate results from multiple agents."""

    # Handle both single agent and parallel agent results
    if isinstance(data, list):
        # Parallel execution results
        all_results = data
    else:
        # Single agent result
        all_results = [data]

    logger.info("aggregating_results", num_agents=len(all_results))

    # Combine results
    aggregated = {
        "task": all_results[0].get("task", ""),
        "agents_used": [r.get("agent") for r in all_results],
        "results": [r.get("results") for r in all_results],
        "all_completed": all(r.get("status") == "completed" for r in all_results)
    }

    return aggregated

# Build Multi-Agent Workflow
def build_multi_agent_workflow():
    """Build production multi-agent coordination workflow."""

    # Step 1: Classify task
    classifier = classify_task

    # Step 2: Route to appropriate agent(s)
    agent_router = RouterPrimitive(
        routes={
            "research": research_agent,
            "analysis": analysis_agent,
            "coding": coding_agent,
            "writing": writing_agent,
            "general": ParallelPrimitive([
                research_agent,
                analysis_agent
            ])  # For general tasks, use both
        },
        router_fn=lambda data, ctx: data.get("task_type", "general"),
        default="general"
    )

    # Step 3: Add reliability
    reliable_agent = TimeoutPrimitive(
        primitive=RetryPrimitive(
            primitive=agent_router,
            max_retries=2,
            backoff_strategy="exponential"
        ),
        timeout_seconds=30.0
    )

    # Step 4: Aggregate results
    aggregator = aggregate_results

    # Compose workflow
    return classifier >> reliable_agent >> aggregator

# Advanced: Parallel Multi-Agent Execution
def build_parallel_multi_agent_workflow():
    """Execute multiple agents in parallel for complex tasks."""

    # All agents in parallel
    parallel_agents = ParallelPrimitive([
        research_agent,
        analysis_agent,
        coding_agent,
        writing_agent
    ])

    # Compose workflow
    return parallel_agents >> aggregate_results

# Advanced: Conditional Agent Selection
def build_conditional_agent_workflow():
    """Use conditional logic for agent selection."""

    # Simple task → single agent
    # Complex task → multiple agents
    conditional_routing = ConditionalPrimitive(
        condition=lambda data, ctx: data.get("complexity", "simple") == "simple",
        then_primitive=research_agent,  # Single agent
        else_primitive=ParallelPrimitive([  # Multiple agents
            research_agent,
            analysis_agent
        ])
    )

    return classify_task >> conditional_routing >> aggregate_results

# Example Usage
async def main():
    # Initialize workflow
    multi_agent = build_multi_agent_workflow()

    # Create context
    context = WorkflowContext(
        correlation_id="multi-agent-example-1",
        data={"user_id": "user123"}
    )

    # Example 1: Research task
    print("\n" + "="*60)
    print("Example 1: Research Task")
    print("="*60)
    result1 = await multi_agent.execute(
        {"task": "Research the latest trends in AI"},
        context
    )
    print(f"Task: {result1['task']}")
    print(f"Agents used: {result1['agents_used']}")
    print(f"Status: {'✓ Completed' if result1['all_completed'] else '✗ Failed'}")

    # Example 2: Coding task
    print("\n" + "="*60)
    print("Example 2: Coding Task")
    print("="*60)
    result2 = await multi_agent.execute(
        {"task": "Implement a sorting algorithm in Python"},
        context
    )
    print(f"Task: {result2['task']}")
    print(f"Agents used: {result2['agents_used']}")
    print(f"Status: {'✓ Completed' if result2['all_completed'] else '✗ Failed'}")

    # Example 3: General task (uses multiple agents)
    print("\n" + "="*60)
    print("Example 3: General Task (Multiple Agents)")
    print("="*60)
    result3 = await multi_agent.execute(
        {"task": "Help me understand quantum computing"},
        context
    )
    print(f"Task: {result3['task']}")
    print(f"Agents used: {result3['agents_used']}")
    print(f"Status: {'✓ Completed' if result3['all_completed'] else '✗ Failed'}")

    # Example 4: Parallel execution
    print("\n" + "="*60)
    print("Example 4: Parallel Multi-Agent Execution")
    print("="*60)
    parallel_workflow = build_parallel_multi_agent_workflow()
    result4 = await parallel_workflow.execute(
        {"task": "Comprehensive analysis of AI market"},
        context
    )
    print(f"Task: {result4['task']}")
    print(f"Agents used: {result4['agents_used']}")
    print(f"Status: {'✓ Completed' if result4['all_completed'] else '✗ Failed'}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Architecture Patterns

### Pattern 1: Single Agent Routing

```
Task → Classify → Route to Agent → Aggregate
```

**Use when:** Task clearly maps to one agent

### Pattern 2: Parallel Multi-Agent

```
Task → [Agent1 | Agent2 | Agent3 | Agent4] → Aggregate
```

**Use when:** Need comprehensive results from all agents

### Pattern 3: Conditional Selection

```
Task → Classify → [Simple? Single Agent : Multiple Agents] → Aggregate
```

**Use when:** Complexity determines agent count

### Pattern 4: Sequential Coordination

```
Task → Agent1 → Agent2 → Agent3 → Final Result
```

**Use when:** Agents build on previous results

## Key Features

### 1. Task Classification

```python
async def classify_task(data, context):
    # Keyword matching, ML model, or LLM-based
    task_type = determine_type(data["task"])
    return {"task_type": task_type}
```

**Benefits:**
- Intelligent routing
- Right agent for the job
- Better results

### 2. Dynamic Routing

```python
RouterPrimitive(
    routes={
        "research": research_agent,
        "coding": coding_agent,
        # ...more agents
    },
    router_fn=lambda data, ctx: data["task_type"]
)
```

**Benefits:**
- Flexible agent selection
- Easy to add new agents
- Type-safe routing

### 3. Parallel Execution

```python
ParallelPrimitive([
    research_agent,
    analysis_agent,
    coding_agent
])
```

**Benefits:**
- 3x faster (for 3 agents)
- Comprehensive results
- Concurrent work streams

### 4. Result Aggregation

```python
async def aggregate_results(data, context):
    # Combine, deduplicate, prioritize
    return unified_results
```

**Benefits:**
- Single unified response
- Smart merging
- Quality synthesis

## Real-World Integrations

### With OpenAI Assistants API

```python
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def openai_assistant_agent(data: dict, context: WorkflowContext) -> dict:
    # Create assistant
    assistant = await client.beta.assistants.create(
        name="Research Agent",
        instructions="You are a research specialist...",
        model="gpt-4o"
    )

    # Create thread and run
    thread = await client.beta.threads.create()
    message = await client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=data["task"]
    )

    run = await client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )

    # Poll for completion
    while run.status != "completed":
        await asyncio.sleep(1)
        run = await client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

    # Get messages
    messages = await client.beta.threads.messages.list(thread_id=thread.id)

    return {"results": messages.data[0].content[0].text.value}
```

### With LangChain Agents

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.tools import Tool

async def langchain_agent(data: dict, context: WorkflowContext) -> dict:
    llm = ChatOpenAI(model="gpt-4o")

    tools = [
        Tool(name="Search", func=search_tool, description="Search the web"),
        Tool(name="Calculator", func=calc_tool, description="Perform calculations")
    ]

    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools)

    result = await agent_executor.ainvoke({"input": data["task"]})

    return {"results": result["output"]}
```

### With Custom LLM Agents

```python
async def custom_llm_agent(data: dict, context: WorkflowContext) -> dict:
    # Your custom agent implementation
    llm_response = await your_llm_call(
        prompt=build_agent_prompt(data["task"]),
        tools=available_tools,
        max_iterations=5
    )

    return {"results": llm_response}
```

## Advanced Patterns

### Hierarchical Agent Structure

```python
# Coordinator agent delegates to specialized agents
coordinator = build_multi_agent_workflow()

# Specialized sub-agents
data_agent = ParallelPrimitive([sql_agent, api_agent, file_agent])
ml_agent = SequentialPrimitive([preprocess, train, evaluate])

# Compose hierarchy
workflow = coordinator >> conditional_delegate >> execute_sub_agent
```

### Agent Memory and State

```python
from tta_dev_primitives.performance import MemoryPrimitive

# Shared memory across agents
shared_memory = MemoryPrimitive(max_size=100)

async def agent_with_memory(data, context):
    # Retrieve relevant history
    history = await shared_memory.search(data["task"])

    # Include in agent context
    result = await agent_call(data, history)

    # Store for future reference
    await shared_memory.add(data["task"], result)

    return result
```

### Feedback Loop

```python
# Agent → Validator → [Approved? Return : Retry with feedback]
workflow = (
    agent >>
    validator >>
    ConditionalPrimitive(
        condition=lambda data, ctx: data["quality"] > 0.8,
        then_primitive=return_result,
        else_primitive=retry_with_feedback
    )
)
```

## Monitoring

### Agent Performance Metrics

```python
from prometheus_client import Counter, Histogram

agent_executions = Counter(
    'agent_executions_total',
    'Total agent executions',
    ['agent_type']
)

agent_latency = Histogram(
    'agent_execution_seconds',
    'Agent execution time',
    ['agent_type']
)
```

### Grafana Queries

```promql
# Agent usage distribution
sum(rate(agent_executions_total[5m])) by (agent_type)

# Average agent latency
avg(rate(agent_execution_seconds_sum[5m]) / rate(agent_execution_seconds_count[5m])) by (agent_type)

# Agent success rate
sum(rate(agent_success_total[5m])) / sum(rate(agent_executions_total[5m]))
```

## Running the Example

```bash
# From repository root
cd packages/tta-dev-primitives/examples
uv run python multi_agent_workflow.py

# Expected output:
# ==========================================================
# Example 1: Research Task
# ==========================================================
# Task: Research the latest trends in AI
# Agents used: ['research']
# Status: ✓ Completed
# ...
```

## Related Examples

- [[TTA.dev/Examples/RAG Workflow]] - RAG patterns
- [[TTA.dev/Examples/Basic Workflow]] - Basic patterns
- [[TTA.dev/Examples/Cost Tracking Workflow]] - Cost optimization

## Documentation

- [[RouterPrimitive]] - Dynamic routing
- [[ParallelPrimitive]] - Parallel execution
- [[ConditionalPrimitive]] - Conditional logic
- [[SequentialPrimitive]] - Sequential composition
- [[PRIMITIVES CATALOG]] - All primitives

## Source Code

**File:** `packages/tta-dev-primitives/examples/multi_agent_workflow.py`

## Tags

example:: multi-agent
type:: production
feature:: coordination
feature:: routing
primitives:: router, parallel, conditional, sequential
pattern:: agent-orchestration

- [[Project Hub]]

---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___examples___multi-agent workflow]]
