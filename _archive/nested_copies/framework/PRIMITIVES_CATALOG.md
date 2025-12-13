# TTA.dev Primitives Catalog

**Complete Reference for All Workflow Primitives**

**Last Updated:** November 7, 2025

---

## Overview

This catalog provides a complete reference for all TTA.dev workflow primitives, organized by category with import paths, usage examples, and links to source code.

**Categories:**

1. [Core Workflow Primitives](#core-workflow-primitives) - Composition and control flow
2. [Recovery Primitives](#recovery-primitives) - Error handling and resilience
3. [Performance Primitives](#performance-primitives) - Optimization and caching
4. [Orchestration Primitives](#orchestration-primitives) - Multi-agent coordination
5. [Testing Primitives](#testing-primitives) - Testing utilities
6. [Observability Primitives](#observability-primitives) - Tracing and metrics
7. [ACE Framework Agents](#ace-framework-agents) - LLM-powered code generation and learning

---

## Core Workflow Primitives

### WorkflowPrimitive[TInput, TOutput]

**Base class for all workflow primitives.**

**Import:**
```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py`](packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py)

**Type Parameters:**

- `TInput` - Input data type
- `TOutput` - Output data type

**Key Methods:**
```python
async def execute(self, input_data: TInput, context: WorkflowContext) -> TOutput:
    """Execute primitive with input data and context."""
    pass

def **rshift**(self, other) -> SequentialPrimitive:
    """Chain primitives: self >> other"""
    pass

def **or**(self, other) -> ParallelPrimitive:
    """Parallel execution: self | other"""
    pass
```

**Usage:**
```python
from abc import abstractmethod

class MyPrimitive(WorkflowPrimitive[str, dict]):
    async def execute(self, input_data: str, context: WorkflowContext) -> dict:
        """Implement your primitive logic."""
        return {"result": input_data.upper()}

# Use it

primitive = MyPrimitive()
context = WorkflowContext(workflow_id="demo")
result = await primitive.execute("hello", context)

# {"result": "HELLO"}

```

**Properties:**

- ✅ Type-safe composition
- ✅ Automatic observability
- ✅ Operator overloading (`>>`, `|`)

---

### SequentialPrimitive

**Execute primitives in sequence, passing output to input.**

**Import:**
```python
from tta_dev_primitives import SequentialPrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/core/sequential.py`](packages/tta-dev-primitives/src/tta_dev_primitives/core/sequential.py)

**Usage:**
```python

# Explicit construction

workflow = SequentialPrimitive([step1, step2, step3])

# Using >> operator (preferred)

workflow = step1 >> step2 >> step3

# Execute

context = WorkflowContext(workflow_id="demo")
result = await workflow.execute(input_data, context)
```

**Execution Flow:**
```text
input → step1 → result1 → step2 → result2 → step3 → output
```

**Properties:**

- ✅ Sequential execution
- ✅ Output becomes next input
- ✅ Automatic span creation
- ✅ Step-level metrics

**Metrics:**
```promql
sequential_step_duration_seconds{step="step1"}
sequential_total_duration_seconds
```

---

### ParallelPrimitive

**Execute primitives concurrently, collecting results.**

**Import:**
```python
from tta_dev_primitives import ParallelPrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/core/parallel.py`](packages/tta-dev-primitives/src/tta_dev_primitives/core/parallel.py)

**Usage:**
```python

# Explicit construction

workflow = ParallelPrimitive([branch1, branch2, branch3])

# Using | operator (preferred)

workflow = branch1 | branch2 | branch3

# Execute

results = await workflow.execute(input_data, context)

# Returns: [result1, result2, result3]

```

**Properties:**

- ✅ Concurrent execution
- ✅ All branches get same input
- ✅ Results collected in list
- ✅ Automatic span creation per branch

---

### ConditionalPrimitive

**Branch execution based on runtime conditions.**

**Import:**
```python
from tta_dev_primitives import ConditionalPrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/core/conditional.py`](packages/tta-dev-primitives/src/tta_dev_primitives/core/conditional.py)

**Usage:**
```python
workflow = ConditionalPrimitive(
    condition=lambda data, ctx: len(data.get("text", "")) < 1000,
    then_primitive=fast_processor,
    else_primitive=slow_processor
)
```

---

### RouterPrimitive

**Dynamic routing to multiple destinations based on logic.**

**Import:**
```python
from tta_dev_primitives.core import RouterPrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/core/routing.py`](packages/tta-dev-primitives/src/tta_dev_primitives/core/routing.py)

**Usage:**
```python
router = RouterPrimitive(
    routes={
        "fast": gpt4_mini,
        "quality": gpt4,
        "code": claude_sonnet,
    },
    router_fn=select_route,
    default="fast"
)
```

---

## Recovery Primitives

### RetryPrimitive

**Automatic retry with exponential backoff.**

**Import:**
```python
from tta_dev_primitives.recovery import RetryPrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/recovery/retry.py`](packages/tta-dev-primitives/src/tta_dev_primitives/recovery/retry.py)

**Usage:**
```python
reliable_llm = RetryPrimitive(
    primitive=llm_call,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0,
    jitter=True
)
```

---

### FallbackPrimitive

**Graceful degradation with fallback cascade.**

**Import:**
```python
from tta_dev_primitives.recovery import FallbackPrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/recovery/fallback.py`](packages/tta-dev-primitives/src/tta_dev_primitives/recovery/fallback.py)

**Usage:**
```python
workflow = FallbackPrimitive(
    primary=openai_gpt4,
    fallbacks=[anthropic_claude, google_gemini, local_llama]
)
```

---

### TimeoutPrimitive

**Circuit breaker pattern with timeout.**

**Import:**
```python
from tta_dev_primitives.recovery import TimeoutPrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/recovery/timeout.py`](packages/tta-dev-primitives/src/tta_dev_primitives/recovery/timeout.py)

**Usage:**
```python
protected_api = TimeoutPrimitive(
    primitive=external_api_call,
    timeout_seconds=30.0,
    raise_on_timeout=True
)
```

---

### CompensationPrimitive

**Saga pattern for distributed transactions with rollback.**

**Import:**
```python
from tta_dev_primitives.recovery import CompensationPrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/recovery/compensation.py`](packages/tta-dev-primitives/src/tta_dev_primitives/recovery/compensation.py)

**Usage:**
```python
workflow = CompensationPrimitive(
    primitives=[
        (create_user_step, rollback_user_creation),
        (send_email_step, rollback_email),
        (activate_account_step, None),
    ]
)
```

---

### CircuitBreakerPrimitive

**Circuit breaker pattern to prevent cascade failures.**

**Import:**
```python
from tta_dev_primitives.recovery import CircuitBreakerPrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/recovery/circuit_breaker.py`](packages/tta-dev-primitives/src/tta_dev_primitives/recovery/circuit_breaker.py)

---

## Performance Primitives

### CachePrimitive

**LRU cache with TTL for expensive operations.**

**Import:**
```python
from tta_dev_primitives.performance import CachePrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/performance/cache.py`](packages/tta-dev-primitives/src/tta_dev_primitives/performance/cache.py)

**Usage:**
```python
cached_llm = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,  # 1 hour
    max_size=1000,     # Max 1000 entries
    key_fn=lambda data, ctx: data["prompt"]
)
```

**Benefits:**

- ✅ 40-60% cost reduction (typical)
- ✅ 100x latency reduction (cache hit)
- ✅ Thread-safe with asyncio.Lock

---

### MemoryPrimitive

**Hybrid conversational memory with zero-setup fallback.**

**Import:**

```python
from tta_dev_primitives.performance import MemoryPrimitive, InMemoryStore, create_memory_key
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/performance/memory.py`](packages/tta-dev-primitives/src/tta_dev_primitives/performance/memory.py)

**Documentation:** [`packages/tta-dev-primitives/docs/memory/README.md`](packages/tta-dev-primitives/docs/memory/README.md)

**Usage:**

```python
# Zero-setup mode (no Redis required)
memory = MemoryPrimitive(max_size=100)

# Add conversation turns
await memory.add("What is a primitive?", {"role": "user"})
await memory.add("A primitive is...", {"role": "assistant"})

# Retrieve by key
result = await memory.get("What is a primitive?")

# Search by keyword
results = await memory.search("primitive")
```

**Hybrid Architecture:**

- **Zero Setup**: Works immediately with in-memory storage
- **Optional Enhancement**: Automatic upgrade to Redis if available
- **Graceful Degradation**: Falls back to in-memory if Redis fails
- **Same API**: No code changes when upgrading backends

**Benefits:**

- ✅ Works without Docker/Redis setup
- ✅ Clear upgrade path when scaling
- ✅ LRU eviction for memory management
- ✅ Keyword search built-in
- ✅ Task-specific memory namespaces

**When to Use:**

- Multi-turn conversations requiring history
- Task context that spans multiple operations
- Personalization based on past interactions
- Agent workflows needing memory recall

**Pattern Established:**

This primitive demonstrates the **"Fallback first, enhancement optional"** pattern for external integrations - future TTA.dev components should follow this approach.

---

## Orchestration Primitives

### DelegationPrimitive

**Orchestrator → Executor pattern for multi-agent workflows.**

**Import:**
```python
from tta_dev_primitives.orchestration import DelegationPrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/delegation_primitive.py`](packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/delegation_primitive.py)

**Usage:**
```python
workflow = DelegationPrimitive(
    orchestrator=claude_sonnet,  # Analyze and plan
    executor=gemini_flash,       # Execute plan
)
```

---

### MultiModelWorkflow

**Intelligent multi-model coordination.**

**Import:**
```python
from tta_dev_primitives.orchestration import MultiModelWorkflow
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/multi_model_workflow.py`](packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/multi_model_workflow.py)

---

### TaskClassifierPrimitive

**Classify tasks and route to appropriate handler.**

**Import:**
```python
from tta_dev_primitives.orchestration import TaskClassifierPrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/task_classifier_primitive.py`](packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/task_classifier_primitive.py)

---

## Testing Primitives

### MockPrimitive

**Mock primitive for testing workflows.**

**Import:**
```python
from tta_dev_primitives.testing import MockPrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/testing/mock_primitive.py`](packages/tta-dev-primitives/src/tta_dev_primitives/testing/mock_primitive.py)

**Usage:**
```python

# Mock LLM response

mock_llm = MockPrimitive(return_value={"output": "Mocked response"})

# Use in workflow

workflow = input_step >> mock_llm >> output_step

# Test

result = await workflow.execute(input_data, context)
assert mock_llm.call_count == 1
```

---

## Observability Primitives

### InstrumentedPrimitive[TInput, TOutput]

**Base class with automatic observability.**

**Import:**
```python
from tta_dev_primitives.observability import InstrumentedPrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/observability/instrumented_primitive.py`](packages/tta-dev-primitives/src/tta_dev_primitives/observability/instrumented_primitive.py)

**Automatic Features:**

- ✅ OpenTelemetry spans
- ✅ Prometheus metrics
- ✅ Structured logging
- ✅ Context propagation

---

## Adaptive/Self-Improving Primitives

### AdaptivePrimitive[TInput, TOutput]

**Base class for self-improving primitives that learn from execution patterns.**

**Import:**
```python
from tta_dev_primitives.adaptive import AdaptivePrimitive, LearningMode
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/adaptive/base.py`](packages/tta-dev-primitives/src/tta_dev_primitives/adaptive/base.py)

**Key Concepts:**

- **LearningStrategy**: Named configuration with performance metrics
- **StrategyMetrics**: Success rate, latency, contexts seen
- **LearningMode**: DISABLED, OBSERVE, VALIDATE, ACTIVE
- **Circuit Breaker**: Automatic fallback on high failure rates
- **Context-Aware**: Different strategies for different contexts

**Type Parameters:**

- `TInput` - Input data type
- `TOutput` - Output data type

**Usage:**
```python
from tta_dev_primitives.adaptive import AdaptivePrimitive, LearningMode, LearningStrategy

class MyAdaptivePrimitive(AdaptivePrimitive[str, dict]):
    async def _execute_with_strategy(
        self,
        strategy: LearningStrategy,
        input_data: str,
        context: WorkflowContext
    ) -> dict:
        """Execute using the selected strategy."""
        # Your implementation using strategy.parameters
        return {"result": input_data, "strategy": strategy.name}

    async def _consider_new_strategy(
        self,
        input_data: str,
        context: WorkflowContext,
        current_performance: StrategyMetrics
    ) -> LearningStrategy | None:
        """Consider creating a new strategy based on patterns."""
        # Your learning logic
        if current_performance.success_rate < 0.8:
            return LearningStrategy(
                name="optimized_v2",
                description="Improved based on failures",
                parameters={"timeout": 60}
            )
        return None

# Use it

adaptive = MyAdaptivePrimitive(
    baseline_strategy=LearningStrategy(name="default", parameters={"timeout": 30}),
    learning_mode=LearningMode.ACTIVE,
    enable_circuit_breaker=True
)

result = await adaptive.execute(data, context)
```

**Safety Features:**

- ✅ Baseline fallback strategy always available
- ✅ Circuit breaker on high failure rates (>50%)
- ✅ Validation window before strategy adoption
- ✅ Minimum observations required for learning
- ✅ Context isolation prevents interference

---

### AdaptiveRetryPrimitive

**Retry primitive that learns optimal retry parameters from execution patterns.**

**Import:**
```python
from tta_dev_primitives.adaptive import AdaptiveRetryPrimitive
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/adaptive/retry.py`](packages/tta-dev-primitives/src/tta_dev_primitives/adaptive/retry.py)

**What It Learns:**

- Optimal number of retries (max_retries)
- Best backoff factor (backoff_factor)
- Ideal initial delay (initial_delay)
- Context-specific strategies (production vs staging)

**Usage:**
```python
from tta_dev_primitives.adaptive import (
    AdaptiveRetryPrimitive,
    LogseqStrategyIntegration,
    LearningMode
)

# Setup Logseq integration (optional but recommended)

logseq = LogseqStrategyIntegration("my_api_service")

# Create adaptive retry

adaptive_retry = AdaptiveRetryPrimitive(
    target_primitive=unreliable_api,
    logseq_integration=logseq,
    enable_auto_persistence=True,
    learning_mode=LearningMode.ACTIVE,
    min_observations_before_learning=10
)

# Use it - learning happens automatically

result = await adaptive_retry.execute(api_request, context)

# Check learned strategies

strategies = adaptive_retry.strategies
for name, strategy in strategies.items():
    print(f"{name}: {strategy.metrics.success_rate:.1%} success")
```

**Automatic Behaviors:**

- ✅ Learns from failures and successes
- ✅ Creates context-specific strategies
- ✅ Validates strategies before adoption
- ✅ Persists to Logseq automatically
- ✅ Falls back to baseline on issues

**Example Learned Strategy:**
```python
LearningStrategy(
    name="production_high_load_v2",
    description="Learned from 50 executions in production context",
    parameters={
        "max_retries": 5,        # Learned: more retries needed
        "backoff_factor": 2.5,   # Learned: longer waits help
        "initial_delay": 2.0     # Learned: start with longer delay
    },
    metrics=StrategyMetrics(
        success_rate=0.94,       # 94% success rate
        avg_latency_ms=1250.5,   # Average latency
        contexts_seen=1          # Specific to this context
    )
)
```

---

### LogseqStrategyIntegration

**Persist learned strategies to Logseq knowledge base.**

**Import:**
```python
from tta_dev_primitives.adaptive import LogseqStrategyIntegration
```

**Source:** [`packages/tta-dev-primitives/src/tta_dev_primitives/adaptive/logseq_integration.py`](packages/tta-dev-primitives/src/tta_dev_primitives/adaptive/logseq_integration.py)

**Features:**

- **Strategy Pages**: Creates `logseq/pages/Strategies/{service_name}_{strategy_name}.md`
- **Journal Entries**: Logs learning events to daily journals
- **Query Support**: Pre-configured queries to discover related strategies
- **Performance Tracking**: Updates metrics over time
- **Cross-Service Sharing**: Strategies discoverable across services

**Usage:**
```python

# Create integration

logseq = LogseqStrategyIntegration("recommendation_engine")

# Save learned strategy

await logseq.save_learned_strategy(
    strategy=learned_strategy,
    primitive_type="AdaptiveRetryPrimitive",
    context="production_high_load",
    notes="Learned during Black Friday traffic spike"
)

# Update performance

await logseq.update_strategy_performance(
    strategy_name="production_high_load_v2",
    new_metrics=updated_metrics
)
```

**Generated Strategy Page Example:**
```markdown

# Strategy - recommendation_engine_production_v2

**Type:** AdaptiveRetryPrimitive
**Context:** production_high_load
**Created:** 2025-11-07
**Performance:** 94.0% success rate, 1250.5ms avg latency

## Parameters

- max_retries: 5
- backoff_factor: 2.5
- initial_delay: 2.0

## Performance History

| Date | Success Rate | Avg Latency | Observations |
|------|--------------|-------------|--------------|
| 2025-11-07 | 94.0% | 1250.5ms | 50 |

## Related Strategies

{{query (and [[Strategies]] [[recommendation_engine]])}}

## Notes

Learned during Black Friday traffic spike. Higher retry count needed.
```

**Benefits:**

- ✅ **Knowledge Preservation**: Strategies persist across restarts
- ✅ **Discovery**: Find similar strategies via Logseq queries
- ✅ **Transparency**: Full visibility into what was learned
- ✅ **Sharing**: Export strategies for other services
- ✅ **Auditing**: Complete learning history in journals

---

## ACE Framework Agents

**The ACE (Autonomous Cognitive Engine) framework provides advanced LLM-powered agents for code generation, analysis, and knowledge management.**

### GeneratorAgent

**Purpose**: Generates code using LLM and learned strategies.
**Import**: `from tta_dev_primitives.ace.agents.generator import GeneratorAgent`
**Source**: [`packages/tta-dev-primitives/src/tta_dev_primitives/ace/agents/generator.py`](packages/tta-dev-primitives/src/tta_dev_primitives/ace/agents/generator.py)
**Description**: Replaces template-based code generation with sophisticated LLM capabilities, incorporating learned strategies for improved output quality and relevance.

### ReflectorAgent

**Purpose**: Analyzes execution results and extracts insights.
**Import**: `from tta_dev_primitives.ace.agents.reflector import ReflectorAgent`
**Source**: [`packages/tta-dev-primitives/src/tta_dev_primitives/ace/agents/reflector.py`](packages/tta-dev-primitives/src/tta_dev_primitives/ace/agents/reflector.py)
**Description**: Performs deep analysis of execution outcomes, identifying root causes of failures, performance bottlenecks, and extracting actionable strategies for learning.

### CuratorAgent

**Purpose**: Manages the knowledge base and strategy selection.
**Import**: `from tta_dev_primitives.ace.agents.curator import CuratorAgent`
**Source**: [`packages/tta-dev-primitives/src/tta_dev_primitives/ace/agents/curator.py`](packages/tta-dev-primitives/src/tta_dev_primitives/ace/agents/curator.py)
**Description**: Intelligently manages learned strategies, including deduplication, relevance scoring, and selection for future tasks, ensuring the playbook remains efficient and effective.

---

## Complete Production Example

**Goal:** Build a production-ready LLM service with all safeguards.

```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import (
    RetryPrimitive,
    FallbackPrimitive,
    TimeoutPrimitive
)
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.core import RouterPrimitive

# Layer 1: Cache (40-60% cost reduction)

cached_llm = CachePrimitive(
    primitive=gpt4_mini,
    ttl_seconds=3600,
    max_size=1000
)

# Layer 2: Timeout (prevent hanging)

timed_llm = TimeoutPrimitive(
    primitive=cached_llm,
    timeout_seconds=30.0
)

# Layer 3: Retry (handle transient failures)

retry_llm = RetryPrimitive(
    primitive=timed_llm,
    max_retries=3,
    backoff_strategy="exponential"
)

# Layer 4: Fallback (high availability)

fallback_llm = FallbackPrimitive(
    primary=retry_llm,
    fallbacks=[claude_sonnet, gemini_flash, ollama_llama]
)

# Layer 5: Router (cost optimization)

production_llm = RouterPrimitive(
    routes={"fast": fallback_llm, "quality": gpt4},
    router_fn=lambda data, ctx: "quality" if "complex" in data.get("prompt", "") else "fast",
    default="fast"
)

# Use it

context = WorkflowContext(workflow_id="prod-service")
result = await production_llm.execute({"prompt": "Hello"}, context)
```

**Benefits:**

- ✅ 40-60% cost reduction (cache)
- ✅ 30-40% additional reduction (router)
- ✅ 99.9% availability (fallback)
- ✅ <30s worst-case latency (timeout)
- ✅ Automatic retry on failures

---

## Quick Reference Table

### Core Workflow

| Primitive | Operator | Import Path | Purpose |
|-----------|----------|-------------|---------|
| WorkflowPrimitive | - | `tta_dev_primitives` | Base class |
| SequentialPrimitive | `>>` | `tta_dev_primitives` | Execute in sequence |
| ParallelPrimitive | `|` | `tta_dev_primitives` | Execute concurrently |
| ConditionalPrimitive | - | `tta_dev_primitives` | Branch on condition |
| RouterPrimitive | - | `tta_dev_primitives.core` | Dynamic routing |

### Recovery

| Primitive | Import Path | Purpose |
|-----------|-------------|---------|
| RetryPrimitive | `tta_dev_primitives.recovery` | Retry with backoff |
| FallbackPrimitive | `tta_dev_primitives.recovery` | Graceful degradation |
| TimeoutPrimitive | `tta_dev_primitives.recovery` | Circuit breaker |
| CompensationPrimitive | `tta_dev_primitives.recovery` | Saga pattern |
| CircuitBreakerPrimitive | `tta_dev_primitives.recovery` | Circuit breaker |

### Performance

| Primitive | Import Path | Purpose |
|-----------|-------------|---------|
| CachePrimitive | `tta_dev_primitives.performance` | LRU cache with TTL |

### Adaptive/Learning

| Primitive | Import Path | Purpose |
|-----------|-------------|---------|
| AdaptivePrimitive | `tta_dev_primitives.adaptive` | Base class for self-improving primitives |
| AdaptiveRetryPrimitive | `tta_dev_primitives.adaptive` | Retry that learns optimal strategies |
| LogseqStrategyIntegration | `tta_dev_primitives.adaptive` | Persist strategies to knowledge base |

### Orchestration

| Primitive | Import Path | Purpose |
|-----------|-------------|---------|
| DelegationPrimitive | `tta_dev_primitives.orchestration` | Orchestrator→Executor |
| MultiModelWorkflow | `tta_dev_primitives.orchestration` | Multi-model coordination |
| TaskClassifierPrimitive | `tta_dev_primitives.orchestration` | Task classification |

---

## Related Documentation

- **Production Integrations:** [`docs/guides/Production_Integrations_QuickRef.md`](docs/guides/Production_Integrations_QuickRef.md)
- **GitHub Blog Implementation:** [`docs/guides/GITHUB_BLOG_IMPLEMENTATION.md`](docs/guides/GITHUB_BLOG_IMPLEMENTATION.md)
- **VS Code Integration:** [`docs/guides/VSCODE_INTEGRATION.md`](docs/guides/VSCODE_INTEGRATION.md)
- **AI Patterns:** [`docs/knowledge/AI_PATTERNS.md`](docs/knowledge/AI_PATTERNS.md)
- **Primitive Patterns:** [`docs/architecture/PRIMITIVE_PATTERNS.md`](docs/architecture/PRIMITIVE_PATTERNS.md)
- **Package README:** [`packages/tta-dev-primitives/README.md`](packages/tta-dev-primitives/README.md)
- **Agent Instructions:** [`packages/tta-dev-primitives/AGENTS.md`](packages/tta-dev-primitives/AGENTS.md)

---

**Last Updated:** November 7, 2025
**Maintained by:** TTA.dev Team
**License:** MIT License - see [LICENSE](LICENSE) for details


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Primitives_catalog]]
