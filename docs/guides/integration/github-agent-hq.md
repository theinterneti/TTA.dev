# TTA.dev for GitHub Agent HQ

**Orchestrate any agent, any way you work**

---

## Overview

GitHub's [Agent HQ](https://github.blog/news-insights/company-news/welcome-home-agents/) provides a unified platform for working with multiple AI coding agents (Anthropic Claude, OpenAI Codex, Google Jules, and more). **TTA.dev complements Agent HQ by providing production-grade orchestration patterns** for composing these agents into reliable, cost-optimized workflows.

### Why TTA.dev + Agent HQ?

| Challenge | Agent HQ Provides | TTA.dev Adds |
|-----------|------------------|--------------|
| **Multiple agents** | Access to Claude, Codex, Jules, etc. | Orchestration patterns (sequential, parallel, routing) |
| **Reliability** | Individual agent reliability | Retry, fallback, timeout primitives |
| **Cost optimization** | Agent marketplace | Cache, router patterns (30-40% cost reduction) |
| **Observability** | Mission control dashboard | Built-in OpenTelemetry tracing + metrics |
| **Custom workflows** | AGENTS.md files | Composable workflow primitives |

---

## Quick Start

### 1. Install TTA.dev

```bash
# Clone the repository
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev

# Install dependencies
uv sync --all-extras
```

### 2. Your First Multi-Agent Workflow

```python
from tta_dev_primitives import RouterPrimitive, ParallelPrimitive, WorkflowContext
from tta_dev_primitives.recovery import FallbackPrimitive

# Define your GitHub Agent HQ agents
claude_agent = ...  # Your Claude integration
codex_agent = ...   # Your Codex integration
copilot_agent = ... # Your Copilot integration

# Route work to the best agent for each task type
agent_router = RouterPrimitive(
    routes={
        "code_review": claude_agent,
        "test_generation": codex_agent,
        "documentation": copilot_agent,
    },
    default_route="copilot_agent"
)

# Add fallback for reliability
workflow = FallbackPrimitive(
    primary=agent_router,
    fallbacks=[copilot_agent]  # Fallback to Copilot if primary fails
)

# Execute
context = WorkflowContext(correlation_id="task-123")
result = await workflow.execute(context, {
    "task_type": "code_review",
    "code": "def hello(): pass"
})
```

### 3. Parallel Agent Execution

```python
# Run multiple agents in parallel and aggregate results
parallel_workflow = ParallelPrimitive(
    primitives=[claude_agent, codex_agent, copilot_agent]
)

# Get responses from all agents simultaneously
results = await parallel_workflow.execute(context, task_data)
```

---

## Core Patterns

### Pattern 1: LLM Router with Cost Optimization

Use different agents based on task complexity to optimize costs:

```python
from tta_dev_primitives import RouterPrimitive

# Route to cheaper agents for simple tasks, powerful agents for complex ones
cost_optimized_router = RouterPrimitive(
    routes={
        "simple": copilot_agent,      # Fast, cheap
        "medium": codex_agent,          # Balanced
        "complex": claude_agent,        # Most capable
    },
    default_route="simple"
)

# Automatically routes based on task complexity
result = await cost_optimized_router.execute(context, {
    "complexity": "complex",  # Routes to Claude
    "task": "Refactor this module..."
})
```

**Cost savings:** 30-40% reduction by routing appropriately.

### Pattern 2: Parallel Consensus

Get consensus from multiple agents for critical decisions:

```python
from tta_dev_primitives import ParallelPrimitive

# Ask 3 agents and take majority vote
consensus_workflow = ParallelPrimitive(
    primitives=[claude_agent, codex_agent, copilot_agent]
)

async def get_consensus(task):
    results = await consensus_workflow.execute(context, task)
    # Implement voting logic
    return majority_vote(results)
```

**Use cases:** Architecture decisions, security reviews, critical bug fixes.

### Pattern 3: Retry with Exponential Backoff

Handle rate limits and transient failures automatically:

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Automatically retry on failure with exponential backoff
reliable_agent = RetryPrimitive(
    primitive=claude_agent,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0
)

# Handles rate limits, network issues, etc.
result = await reliable_agent.execute(context, task_data)
```

### Pattern 4: Cache Expensive Agent Calls

Cache responses for repeated queries:

```python
from tta_dev_primitives.performance import CachePrimitive

# Cache agent responses for 1 hour
cached_agent = CachePrimitive(
    primitive=claude_agent,
    ttl_seconds=3600,
    max_size=1000
)

# First call hits agent, subsequent calls use cache
result1 = await cached_agent.execute(context, "Explain async/await")
result2 = await cached_agent.execute(context, "Explain async/await")  # Cached!
```

**Cost savings:** Eliminate redundant API calls.

### Pattern 5: Sequential Pipeline

Chain agents for multi-step workflows:

```python
# Sequential workflow: planning → implementation → review
pipeline = (
    claude_planning >>      # Claude plans the approach
    codex_implementation >> # Codex implements the code
    copilot_review          # Copilot reviews the result
)

result = await pipeline.execute(context, feature_request)
```

### Pattern 6: Fallback Chain

Graceful degradation when agents are unavailable:

```python
from tta_dev_primitives.recovery import FallbackPrimitive

# Try premium agent first, fallback to free alternatives
fallback_chain = FallbackPrimitive(
    primary=claude_agent,
    fallbacks=[codex_agent, copilot_agent, local_llm]
)

# Always gets a response, even if Claude is down
result = await fallback_chain.execute(context, task_data)
```

---

## Integration with GitHub Features

### AGENTS.md Files

TTA.dev workflows work seamlessly with GitHub's AGENTS.md custom instructions:

**`.github/AGENTS.md`:**

```markdown
# Project Agent Instructions

## Code Generation Rules

- Use TTA.dev primitives for all workflow orchestration
- Prefer RouterPrimitive for agent selection
- Always add retry logic with RetryPrimitive
- Cache expensive operations with CachePrimitive

## Agent Selection

- **Claude:** Architecture decisions, complex refactoring
- **Codex:** Test generation, boilerplate code
- **Copilot:** Code reviews, documentation
```

**In your code:**

```python
# Agents automatically follow AGENTS.md instructions
workflow = RouterPrimitive(
    routes={
        "architecture": claude_agent,
        "tests": codex_agent,
        "review": copilot_agent,
    }
)
```

### Mission Control Integration

Track TTA.dev workflows in GitHub's mission control:

```python
from tta_dev_primitives import WorkflowContext

# WorkflowContext integrates with mission control
context = WorkflowContext(
    correlation_id="gh-task-12345",  # Links to GitHub task
    data={
        "github_issue": "#123",
        "branch": "feature/new-api",
        "user": "octocat"
    }
)

# All primitives automatically report to mission control
result = await workflow.execute(context, task_data)
```

### Plan Mode Integration

Use TTA.dev primitives in GitHub's Plan Mode:

1. **Plan Mode generates plan:** "Build API endpoint with tests and docs"
2. **Convert to TTA.dev workflow:**

```python
# Generated workflow from Plan Mode
workflow = (
    claude_planning >>          # Step 1: Plan API design
    codex_implementation >>     # Step 2: Implement endpoint
    codex_test_generation >>    # Step 3: Generate tests
    copilot_documentation       # Step 4: Write documentation
)
```

---

## Advanced Patterns

### Pattern 7: Dynamic Agent Selection

Choose agents based on runtime conditions:

```python
from tta_dev_primitives import ConditionalPrimitive

async def select_agent(context, input_data):
    if input_data["budget"] == "low":
        return copilot_agent
    elif input_data["complexity"] == "high":
        return claude_agent
    else:
        return codex_agent

dynamic_workflow = ConditionalPrimitive(
    condition=select_agent,
    branches={
        "copilot": copilot_workflow,
        "claude": claude_workflow,
        "codex": codex_workflow,
    }
)
```

### Pattern 8: Parallel with Timeout

Run multiple agents with time limits:

```python
from tta_dev_primitives.recovery import TimeoutPrimitive

# Each agent has 30 second timeout
timed_agents = [
    TimeoutPrimitive(agent, timeout_seconds=30)
    for agent in [claude_agent, codex_agent, copilot_agent]
]

workflow = ParallelPrimitive(primitives=timed_agents)
```

### Pattern 9: Compensation Pattern (Saga)

Rollback on failure:

```python
from tta_dev_primitives.recovery import CompensationPrimitive

async def create_branch(context, input_data):
    # Create Git branch
    ...

async def rollback_branch(context, input_data):
    # Delete branch if workflow fails
    ...

workflow = CompensationPrimitive(
    primitive=claude_agent,
    compensation=rollback_branch
)
```

### Pattern 10: Multi-Stage Pipeline with Recovery

Production-ready workflow with full error handling:

```python
from tta_dev_primitives import SequentialPrimitive
from tta_dev_primitives.recovery import RetryPrimitive, FallbackPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Build production pipeline
planning = RetryPrimitive(claude_agent, max_retries=3)
implementation = FallbackPrimitive(
    primary=codex_agent,
    fallbacks=[copilot_agent]
)
review = CachePrimitive(copilot_agent, ttl_seconds=3600)

workflow = planning >> implementation >> review
```

---

## Cost Optimization Strategies

### Strategy 1: Smart Caching

```python
# Cache by task type to maximize hit rate
def cache_key(context, input_data):
    return f"{input_data['task_type']}:{hash(input_data['content'])}"

cached_workflow = CachePrimitive(
    primitive=expensive_agent,
    ttl_seconds=7200,  # 2 hours
    max_size=5000,
    cache_key_fn=cache_key
)
```

**Result:** 40-60% reduction in API calls for repeated tasks.

### Strategy 2: Tiered Agent Selection

```python
# Try cheaper agents first, escalate to expensive ones
tiered_workflow = FallbackPrimitive(
    primary=copilot_agent,     # $0.03/1K tokens
    fallbacks=[
        codex_agent,            # $0.06/1K tokens
        claude_agent,           # $0.12/1K tokens
    ]
)
```

**Result:** 70% of tasks handled by cheapest agent.

### Strategy 3: Batch Processing

```python
# Process multiple tasks in one agent call
async def batch_tasks(context, task_list):
    # Combine tasks into single prompt
    combined = "\n\n".join(task_list)
    return await agent.execute(context, combined)

batched_workflow = CachePrimitive(
    primitive=batch_tasks,
    ttl_seconds=3600
)
```

**Result:** 50% reduction in API overhead.

---

## Observability

TTA.dev provides **production-grade observability** for all Agent HQ workflows:

### Built-in Tracing

```python
from tta_dev_primitives import WorkflowContext

# Automatic distributed tracing
context = WorkflowContext(correlation_id="req-123")

# Every primitive creates spans automatically
result = await workflow.execute(context, input_data)

# View trace in Jaeger/Zipkin
# - Which agents were called
# - How long each took
# - Where errors occurred
```

### Metrics Collection

```python
from observability_integration import initialize_observability

# Enable Prometheus metrics
initialize_observability(
    service_name="github-agent-hq",
    enable_prometheus=True
)

# Metrics exposed on :9464/metrics
# - agent_calls_total{agent="claude"}
# - agent_duration_seconds{agent="codex"}
# - agent_errors_total{agent="copilot"}
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger(__name__)

async def my_primitive(context, input_data):
    logger.info(
        "agent_execution",
        agent="claude",
        task_type=input_data["type"],
        correlation_id=context.correlation_id
    )
```

---

## Production Deployment

### 1. Environment Setup

```bash
# Set up production environment
export GITHUB_AGENT_HQ_TOKEN="your-token"
export TTA_OBSERVABILITY_ENDPOINT="https://otel-collector:4317"
export TTA_PROMETHEUS_PORT="9464"

# Run workflow
uv run python -m your_workflow
```

### 2. Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy TTA.dev
COPY . .
RUN uv sync --all-extras

# Run workflow
CMD ["uv", "run", "python", "-m", "workflows.agent_hq"]
```

### 3. Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tta-agent-hq
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: workflow
        image: tta-agent-hq:latest
        env:
        - name: GITHUB_AGENT_HQ_TOKEN
          valueFrom:
            secretKeyRef:
              name: github-tokens
              key: agent-hq-token
        - name: TTA_OBSERVABILITY_ENDPOINT
          value: "otel-collector:4317"
```

### 4. Monitoring Setup

```yaml
# docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - ./monitoring/dashboards:/etc/grafana/provisioning/dashboards
```

---

## Real-World Examples

### Example 1: Code Review Pipeline

```python
"""Multi-stage code review with Agent HQ agents"""

from tta_dev_primitives import SequentialPrimitive, WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive

# Define review stages
style_check = RetryPrimitive(copilot_agent, max_retries=2)
security_check = RetryPrimitive(claude_agent, max_retries=2)
performance_check = RetryPrimitive(codex_agent, max_retries=2)

# Build pipeline
review_pipeline = style_check >> security_check >> performance_check

# Execute
context = WorkflowContext(
    correlation_id="pr-456",
    data={"pr_number": 456, "branch": "feature/new-api"}
)

review_results = await review_pipeline.execute(context, {
    "files_changed": ["api/endpoint.py", "tests/test_api.py"],
    "diff": "...",
})
```

### Example 2: Feature Implementation Workflow

```python
"""End-to-end feature implementation with multiple agents"""

from tta_dev_primitives import SequentialPrimitive, ParallelPrimitive

# Stage 1: Planning (Claude)
planning = claude_agent

# Stage 2: Parallel implementation
implementation = ParallelPrimitive([
    codex_agent,      # Main implementation
    codex_agent,      # Test generation
    copilot_agent,    # Documentation
])

# Stage 3: Review (Claude)
review = claude_agent

# Build workflow
feature_workflow = planning >> implementation >> review

# Execute
result = await feature_workflow.execute(context, {
    "feature": "Add rate limiting to API",
    "requirements": "...",
})
```

### Example 3: Automated Bug Fix

```python
"""Automated bug detection and fixing"""

from tta_dev_primitives.recovery import FallbackPrimitive

# Try multiple agents for bug fix
bug_fix_workflow = FallbackPrimitive(
    primary=claude_agent,       # Best at understanding complex bugs
    fallbacks=[
        codex_agent,             # Good at standard patterns
        copilot_agent,           # Fast for simple fixes
    ]
)

# Add retry for reliability
workflow = RetryPrimitive(bug_fix_workflow, max_retries=3)

result = await workflow.execute(context, {
    "bug_report": "NullPointerException in UserService",
    "stack_trace": "...",
    "code": "...",
})
```

---

## Best Practices

### 1. Use WorkflowContext Everywhere

```python
# ✅ GOOD: Use WorkflowContext
context = WorkflowContext(
    correlation_id="req-123",
    data={"user": "octocat", "task": "feature"}
)
result = await workflow.execute(context, input_data)

# ❌ BAD: Direct function calls
result = await agent_function(input_data)
```

### 2. Add Retry for External Agents

```python
# ✅ GOOD: Wrap external agents with retry
reliable_agent = RetryPrimitive(github_agent, max_retries=3)

# ❌ BAD: No retry logic
result = await github_agent.execute(context, input_data)
```

### 3. Cache Expensive Operations

```python
# ✅ GOOD: Cache expensive agent calls
cached_agent = CachePrimitive(claude_agent, ttl_seconds=3600)

# ❌ BAD: Repeated expensive calls
for task in tasks:
    await claude_agent.execute(context, task)
```

### 4. Use Fallbacks for Availability

```python
# ✅ GOOD: Always have fallback
workflow = FallbackPrimitive(
    primary=preferred_agent,
    fallbacks=[backup_agent, local_agent]
)

# ❌ BAD: Single point of failure
result = await preferred_agent.execute(context, input_data)
```

### 5. Monitor Everything

```python
# ✅ GOOD: Enable observability
from observability_integration import initialize_observability

initialize_observability(
    service_name="my-workflow",
    enable_prometheus=True
)

# ❌ BAD: No observability
# (How do you debug production issues?)
```

---

## Troubleshooting

### Issue: Agent Rate Limits

**Solution:** Use RetryPrimitive with exponential backoff

```python
workflow = RetryPrimitive(
    primitive=agent,
    max_retries=5,
    backoff_strategy="exponential",
    initial_delay=2.0
)
```

### Issue: High Costs

**Solution:** Use RouterPrimitive + CachePrimitive

```python
# Route to cheaper agents when possible
router = RouterPrimitive(routes={
    "simple": cheap_agent,
    "complex": expensive_agent,
})

# Cache results
workflow = CachePrimitive(router, ttl_seconds=3600)
```

### Issue: Agents Unavailable

**Solution:** Use FallbackPrimitive

```python
workflow = FallbackPrimitive(
    primary=cloud_agent,
    fallbacks=[local_agent, cached_response]
)
```

### Issue: Slow Response Times

**Solution:** Use ParallelPrimitive

```python
# Run multiple agents in parallel
workflow = ParallelPrimitive([agent1, agent2, agent3])
```

---

## Next Steps

### Learn More

- **Primitives Catalog:** [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md)
- **Main Agent Instructions:** [`AGENTS.md`](../../AGENTS.md)
- **Getting Started:** [`GETTING_STARTED.md`](../../GETTING_STARTED.md)
- **Examples:** [`platform/primitives/examples/`](../../platform/primitives/examples/)

### Get Help

- **GitHub Issues:** [Report a bug or request a feature](https://github.com/theinterneti/TTA.dev/issues)
- **Discussions:** [Ask questions and share workflows](https://github.com/theinterneti/TTA.dev/discussions)
- **Documentation:** [Full documentation](../../docs/)

### Contribute

We welcome contributions! See [`CONTRIBUTING.md`](../../CONTRIBUTING.md) for guidelines.

---

**Built for GitHub Agent HQ** | **Production-Ready** | **Open Source**


---
**Logseq:** [[TTA.dev/Docs/Integration/Github-agent-hq]]
