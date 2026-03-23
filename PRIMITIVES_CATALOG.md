# TTA.dev Primitives Catalog

**Complete Reference for All Workflow Primitives**

**Last Updated:** 2026-03-23

---

> [!WARNING]
> This catalog is still being migrated from older package layouts and examples.
> The most trustworthy current proof path is in [`GETTING_STARTED.md`](GETTING_STARTED.md),
> [`QUICKSTART.md`](QUICKSTART.md), and the runnable script
> [`scripts/test_realtime_traces.py`](scripts/test_realtime_traces.py).
>
> In particular:
> - some sections still need hand-verified cleanup after the older `tta_dev_primitives` and
>   `platform/...` layouts
> - the adaptive and `extensions` sections include mixed-current notes because those surfaces are
>   not fully reconciled yet
> - examples in this file should be treated as reference-in-progress until each section is verified

## Current reality first

If you are trying to build or verify something today, prefer:

- `from ttadev.primitives import ...`
- `from ttadev.primitives import WorkflowContext`
- `uv run python -m ttadev.observability`
- `uv run python scripts/test_realtime_traces.py`

---

## Overview

This catalog provides a complete reference for all TTA.dev workflow primitives, organized by category with import paths, usage examples, and links to source code.

**Categories:**

1. [Core Workflow Primitives](#core-workflow-primitives) - Composition and control flow
2. [Recovery Primitives](#recovery-primitives) - Error handling and resilience
3. [Performance Primitives](#performance-primitives) - Optimization and caching
4. [Skill Primitives](#skill-primitives) - SKILL.md-compatible agent capabilities
5. [Orchestration Primitives](#orchestration-primitives) - Multi-agent coordination
6. [Testing Primitives](#testing-primitives) - Testing utilities
7. [Observability Primitives](#observability-primitives) - Tracing and metrics
8. [ACE Framework Primitives](#ace-framework-primitives) - LLM-powered code generation and learning
9. [Extension Modules](#extension-modules) - Specialized non-core primitives

---

## Core Workflow Primitives

### WorkflowPrimitive[TInput, TOutput]

**Base class for all workflow primitives.**

**Import:**
\`\`\`python
from ttadev.primitives import WorkflowPrimitive, WorkflowContext
\`\`\`

**Source:** [\`ttadev/primitives/core/base.py\`](ttadev/primitives/core/base.py)

**Type Parameters:**

- \`TInput\` - Input data type
- \`TOutput\` - Output data type

**Key Methods:**
\`\`\`python
async def execute(self, input_data: TInput, context: WorkflowContext) -> TOutput:
    """Execute primitive with input data and context."""
    pass

def **rshift**(self, other) -> SequentialPrimitive:
    """Chain primitives: self >> other"""
    pass

def **or**(self, other) -> ParallelPrimitive:
    """Parallel execution: self | other"""
    pass
\`\`\`

**Usage:**
\`\`\`python
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

\`\`\`

**Properties:**

- ✅ Type-safe composition
- ✅ Automatic observability
- ✅ Operator overloading (\`>>\`, \`|\`)

---

### SequentialPrimitive

**Execute primitives in sequence, passing output to input.**

**Import:**
\`\`\`python
from ttadev.primitives import SequentialPrimitive
\`\`\`

**Source:** [\`ttadev/primitives/core/sequential.py\`](ttadev/primitives/core/sequential.py)

**Usage:**
\`\`\`python

# Explicit construction

workflow = SequentialPrimitive([step1, step2, step3])

# Using >> operator (preferred)

workflow = step1 >> step2 >> step3

# Execute

context = WorkflowContext(workflow_id="demo")
result = await workflow.execute(input_data, context)
\`\`\`

**Execution Flow:**
\`\`\`text
input → step1 → result1 → step2 → result2 → step3 → output
\`\`\`

**Properties:**

- ✅ Sequential execution
- ✅ Output becomes next input
- ✅ Automatic span creation
- ✅ Step-level metrics

**Metrics:**
\`\`\`promql
sequential_step_duration_seconds{step="step1"}
sequential_total_duration_seconds
\`\`\`

Typically, your `forward` primitive will itself be a composed workflow (e.g. a
`SequentialPrimitive` of multiple steps). The `compensation` primitive is
responsible for undoing the side effects of `forward` when a failure occurs.

---

### ParallelPrimitive

**Execute primitives concurrently, collecting results.**

**Import:**
\`\`\`python
from ttadev.primitives import ParallelPrimitive
\`\`\`

**Source:** [\`ttadev/primitives/core/parallel.py\`](ttadev/primitives/core/parallel.py)

**Usage:**
\`\`\`python

# Explicit construction

workflow = ParallelPrimitive([branch1, branch2, branch3])

# Using | operator (preferred)

workflow = branch1 | branch2 | branch3

# Execute

results = await workflow.execute(input_data, context)

# Returns: [result1, result2, result3]

\`\`\`

**Properties:**

- ✅ Concurrent execution
- ✅ All branches get same input
- ✅ Results collected in list
- ✅ Automatic span creation per branch

---

### ConditionalPrimitive

**Branch execution based on runtime conditions.**

**Import:**
\`\`\`python
from ttadev.primitives import ConditionalPrimitive
\`\`\`

**Source:** [\`ttadev/primitives/core/conditional.py\`](ttadev/primitives/core/conditional.py)

**Usage:**
\`\`\`python
workflow = ConditionalPrimitive(
    condition=lambda data, ctx: len(data.get("text", "")) < 1000,
    then_primitive=fast_processor,
    else_primitive=slow_processor
)
\`\`\`

---

### RouterPrimitive

**Dynamic routing to multiple destinations based on logic.**

**Import:**
\`\`\`python
from ttadev.primitives.core import RouterPrimitive
\`\`\`

**Source:** [\`ttadev/primitives/core/routing.py\`](ttadev/primitives/core/routing.py)

**Usage:**
\`\`\`python
router = RouterPrimitive(
    routes={
        "fast": gpt4_mini,
        "quality": gpt4,
        "code": claude_sonnet,
    },
    router_fn=select_route,
    default="fast"
)
\`\`\`

---

## Recovery Primitives

### RetryPrimitive

**Automatic retry with exponential backoff.**

**Import:**
\`\`\`python
from ttadev.primitives.recovery import RetryPrimitive
\`\`\`

**Source:** [\`ttadev/primitives/recovery/retry.py\`](ttadev/primitives/recovery/retry.py)

**Usage:**
\`\`\`python
reliable_llm = RetryPrimitive(
    primitive=llm_call,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0,
    jitter=True
)
\`\`\`

---

### FallbackPrimitive

**Graceful degradation with fallback cascade.**

**Import:**
\`\`\`python
from ttadev.primitives.recovery import FallbackPrimitive
\`\`\`

**Source:** [\`ttadev/primitives/recovery/fallback.py\`](ttadev/primitives/recovery/fallback.py)

**Usage:**
\`\`\`python
workflow = FallbackPrimitive(
    primary=openai_gpt4,
    fallbacks=[anthropic_claude, google_gemini, local_llama]
)
\`\`\`

---

### TimeoutPrimitive

**Circuit breaker pattern with timeout.**

**Import:**
\`\`\`python
from ttadev.primitives.recovery import TimeoutPrimitive
\`\`\`

**Source:** [\`ttadev/primitives/recovery/timeout.py\`](ttadev/primitives/recovery/timeout.py)

**Usage:**
\`\`\`python
protected_api = TimeoutPrimitive(
    primitive=external_api_call,
    timeout_seconds=30.0,
    raise_on_timeout=True
)
\`\`\`

---

### CompensationPrimitive

**Saga pattern for distributed transactions with rollback.**

**Import:**
\`\`\`python
from ttadev.primitives.recovery import CompensationPrimitive
\`\`\`

**Source:** [\`ttadev/primitives/recovery/compensation.py\`](ttadev/primitives/recovery/compensation.py)

**Usage:**
\`\`\`python
from ttadev.primitives.recovery import CompensationPrimitive

workflow = CompensationPrimitive(
    forward=process_order,
    compensation=rollback_order,
)
\`\`\`

---

### CircuitBreakerPrimitive

**Circuit breaker pattern to prevent cascade failures.**

**Status:** ✅ Production-ready (March 2026)

**Import:**
\`\`\`python
from ttadev.primitives.recovery import CircuitBreakerPrimitive
\`\`\`

**Source:** [\`ttadev/primitives/recovery/circuit_breaker.py\`](ttadev/primitives/recovery/circuit_breaker.py)

**States:**
- **Closed** - Normal operation, requests pass through
- **Open** - Fast-fail mode, requests rejected immediately
- **Half-Open** - Testing recovery, limited requests allowed

**Usage:**
\`\`\`python
from ttadev.primitives.recovery import CircuitBreakerPrimitive

# Protect an unreliable service
protected_service = CircuitBreakerPrimitive(
    primitive=unreliable_service_call,
    failure_threshold=5,      # 5 consecutive failures to open circuit
    recovery_timeout=60.0,    # 60 seconds before testing recovery
    success_threshold=2       # 2 successes in half-open to close
)

# Use it - automatic state management
try:
    result = await protected_service.execute(data, context)
except CircuitBreakerOpenError:
    # Circuit is open, service unavailable
    return fallback_response
\`\`\`

**Features:**
- ✅ Automatic state transitions
- ✅ Async/await support
- ✅ Configurable thresholds
- ✅ Thread-safe state management
- ✅ Full test coverage (15 tests)

**Test Coverage:** 100%

---

## Performance Primitives

### CachePrimitive

**LRU cache with TTL for expensive operations.**

**Import:**
\`\`\`python
from ttadev.primitives.performance import CachePrimitive
\`\`\`

**Source:** [\`ttadev/primitives/performance/cache.py\`](ttadev/primitives/performance/cache.py)

**Usage:**
\`\`\`python
cached_llm = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,  # 1 hour
    max_size=1000,     # Max 1000 entries
    key_fn=lambda data, ctx: data["prompt"]
)
\`\`\`

**Benefits:**

- ✅ 40-60% cost reduction (typical)
- ✅ 100x latency reduction (cache hit)
- ✅ Thread-safe with asyncio.Lock

---

### MemoryPrimitive

**Hybrid conversational memory with zero-setup fallback.**

**Import:**

```python
from ttadev.primitives.performance.memory import MemoryPrimitive, InMemoryStore, create_memory_key
```

**Source:** [`ttadev/primitives/performance/memory.py`](ttadev/primitives/performance/memory.py)

**Related Spec:** [`docs/reference/specs/primitives/memory-primitive.spec.md`](docs/reference/specs/primitives/memory-primitive.spec.md)

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

## Collaboration Primitives

### GitCollaborationPrimitive

**Enforce best practices for multi-agent Git collaboration.**

**Import:**
\`\`\`python
from ttadev.primitives.collaboration import (
    GitCollaborationPrimitive,
    AgentIdentity,
    IntegrationFrequency,
    CommitFrequencyPolicy,
    MergeStrategy,
)
\`\`\`

**Source:** [\`ttadev/primitives/collaboration/git_integration.py\`](ttadev/primitives/collaboration/git_integration.py)

**Research Foundation:**
- Martin Fowler's "Patterns for Managing Source Code Branches"
- State of DevOps Report - Elite teams integrate daily or more
- Conventional Commits specification

**Key Features:**
- ✅ **Integration Frequency Enforcement** - Continuous (< 1h), Hourly (2h), Daily (24h)
- ✅ **Conventional Commits** - Enforced feat:/fix:/docs:/test:/refactor:/chore: format
- ✅ **Health Monitoring** - Uncommitted files, time tracking, divergence from main
- ✅ **Conflict Detection** - Early warning of integration issues
- ✅ **Automated Recommendations** - Actionable advice based on health checks
- ✅ **Flexible Enforcement** - Strict mode (raise errors) or warning mode (return dict)

**Usage:**
\`\`\`python
# Configure agent identity
agent = AgentIdentity(
    name="GitHub Copilot",
    email="copilot@tta.dev",
    branch_prefix="agent/copilot",
)

# Create primitive with daily integration
git_collab = GitCollaborationPrimitive(
    agent_identity=agent,
    integration_frequency=IntegrationFrequency.DAILY,
    repository_path=Path.home() / "repos" / "TTA.dev",
    enforce_hygiene=True,
)

# Check branch health
health = await git_collab.execute({"action": "status"}, context)

# Commit with validation
await git_collab.execute(
    {
        "action": "commit",
        "message": "feat: Add new feature with comprehensive tests",
        "files": ["src/feature.py", "tests/test_feature.py"],
    },
    context,
)

# Sync with main
await git_collab.execute({"action": "sync"}, context)

# Create integration PR
await git_collab.execute(
    {
        "action": "integrate",
        "title": "feat: New feature implementation",
        "body": "Complete implementation with tests",
    },
    context,
)

# Enforce commit frequency
await git_collab.execute({"action": "enforce_frequency"}, context)
\`\`\`

**Integration Frequencies:**

\`\`\`python
# Elite teams (< 1 hour between integrations)
IntegrationFrequency.CONTINUOUS

# High-performance teams (max 2 hours)
IntegrationFrequency.HOURLY

# Standard practice (max 24 hours)
IntegrationFrequency.DAILY

# Anti-pattern (max 7 days) - discouraged
IntegrationFrequency.WEEKLY
\`\`\`

**Commit Frequency Policy:**

\`\`\`python
policy = CommitFrequencyPolicy(
    max_uncommitted_changes=50,      # Max files before must commit
    max_uncommitted_time_minutes=60,  # Max 1 hour without commit
    require_tests_before_commit=True, # Source changes need tests
    min_message_length=20,            # Enforce descriptive messages
)
\`\`\`

**Actions Supported:**
1. `status` - Check branch health and get recommendations
2. `commit` - Create validated commit with conventional format
3. `sync` - Sync with main branch, detect conflicts
4. `integrate` - Create PR for integration
5. `enforce_frequency` - Verify integration frequency compliance

**Benefits:**
- 🎯 **Prevents Integration Hell** - Enforces frequent integration
- 🔒 **Maintains Quality** - Requires tests for source changes
- 📊 **Provides Visibility** - Health checks and recommendations
- 🚀 **Improves Velocity** - Small, frequent merges reduce risk
- 🤝 **Enables Collaboration** - Clear agent attribution and coordination

**Full Guide:** [\`docs/reference/GIT_COLLABORATION_PRIMITIVE_COMPLETE.md\`](docs/reference/GIT_COLLABORATION_PRIMITIVE_COMPLETE.md)

---

## Skill Primitives

**Package:** `tta-skill-primitives` (`ttadev/skills/`)

Skills are self-describing, SKILL.md-compatible agent capabilities built on `WorkflowPrimitive`. They follow the open SKILL.md specification adopted by mainstream AI agent frameworks.

### Skill[TInput, TOutput]

**Base class for agent skills — extends WorkflowPrimitive with metadata.**

**Import:**
```python
from tta_skill_primitives import Skill, SkillDescriptor
```

**Source:** [`ttadev/skills/src/tta_skill_primitives/core/base.py`](ttadev/skills/src/tta_skill_primitives/core/base.py)

**Usage:**
```python
from tta_skill_primitives import Skill, SkillDescriptor, SkillMetadata
from ttadev.primitives import WorkflowContext

class CodeReviewSkill(Skill[str, dict]):
    descriptor = SkillDescriptor(
        name="code-review",
        description="Analyse code for quality and security issues.",
        metadata=SkillMetadata(author="TTA Team", version="1.0.0", tags=["security"]),
    )

    async def execute(self, input_data: str, context: WorkflowContext) -> dict:
        return {"issues": [], "score": 100}

# Skills compose like any WorkflowPrimitive
pipeline = code_review >> security_scan >> format_report
```

**Properties:** `name`, `description`, `version`, `status`, `tags`

### SkillDescriptor

**Pydantic model for SKILL.md YAML frontmatter.**

**Import:**
```python
from tta_skill_primitives import SkillDescriptor, SkillMetadata, SkillParameter, SkillStatus
```

**Fields:**
- `name` (str, required) — unique lowercase-hyphenated identifier (1–64 chars)
- `description` (str, required) — what the skill does (1–1024 chars)
- `license` (str) — license identifier (default: "MIT")
- `compatibility` (str) — environment requirements
- `allowed_tools` (list[str]) — tools the skill may invoke
- `status` (SkillStatus) — draft / stable / deprecated
- `metadata` (SkillMetadata) — author, version, tags
- `parameters` (list[SkillParameter]) — input parameter declarations
- `instructions` (str) — markdown body from SKILL.md

### SkillRegistry

**In-memory registry for skill discovery and search.**

**Import:**
```python
from tta_skill_primitives import SkillRegistry
```

**Key Methods:**
```python
registry = SkillRegistry()
registry.register(my_skill)          # Register a skill
skill = registry.get("code-review")  # Get by name
results = registry.search(tags=["security"], status=SkillStatus.STABLE)
catalog = registry.to_prompt_catalog()  # Markdown catalog for LLM prompts
```

### SKILL.md Loader

**Parse and write SKILL.md files.**

**Import:**
```python
from tta_skill_primitives import parse_skill_md, load_skill_md, dump_skill_md
```

**Usage:**
```python
# Parse from string
descriptor = parse_skill_md("---\nname: my-skill\ndescription: ...\n---\n# Instructions")

# Load from file
descriptor = load_skill_md("skills/code-review/SKILL.md")

# Write back
text = dump_skill_md(descriptor)
```

---

## Extension Modules

> [!WARNING]
> The `ttadev.primitives.extensions` namespace is still mixed-current.
> Its lazy-import metadata exists, but some internal module mappings still point at the older
> `tta_dev_primitives.*` package names. For runnable code, prefer importing the target module
> directly from `ttadev.primitives.<module>`.

Extension modules provide specialised, non-core capabilities:

```python
from ttadev.primitives.extensions import EXTENSION_MODULES, list_extensions
from ttadev.primitives.adaptive import AdaptiveRetryPrimitive
```

| Module | Preferred Import Path | Purpose |
|--------|-----------------------|---------|
| **ace** | `ttadev.primitives.ace` | Self-learning ACE primitives and benchmark helpers |
| **adaptive** | `ttadev.primitives.adaptive` | Self-improving retry, cache, timeout, and fallback patterns |
| **analysis** | `ttadev.primitives.analysis` | AST-based pattern detection and transformation |
| **apm** | `ttadev.primitives.apm` | Application performance monitoring helpers |
| **benchmarking** | `ttadev.primitives.benchmarking` | Performance benchmarking utilities |
| **knowledge** | `ttadev.primitives.knowledge` | Knowledge and memory-oriented primitives |
| **lifecycle** | `ttadev.primitives.lifecycle` | Stage management and validation gates |
| **orchestration** | `ttadev.primitives.orchestration` | Multi-model orchestration and delegation |
| **research** | `ttadev.primitives.research` | Provider research and free-tier discovery |
| **speckit** | `ttadev.primitives.speckit` | Specification-driven development workflow |

---

## Orchestration Primitives

### DelegationPrimitive

**Orchestrator → Executor pattern for multi-agent workflows.**

**Import:**
\`\`\`python
from ttadev.primitives.orchestration import DelegationPrimitive
\`\`\`

**Source:** [\`ttadev/primitives/orchestration/delegation_primitive.py\`](ttadev/primitives/orchestration/delegation_primitive.py)

**Usage:**
\`\`\`python
workflow = DelegationPrimitive(
    orchestrator=claude_sonnet,  # Analyze and plan
    executor=gemini_flash,       # Execute plan
)
\`\`\`

---

### MultiModelWorkflow

**Intelligent multi-model coordination.**

**Import:**
\`\`\`python
from ttadev.primitives.orchestration import MultiModelWorkflow
\`\`\`

**Source:** [\`ttadev/primitives/orchestration/multi_model_workflow.py\`](ttadev/primitives/orchestration/multi_model_workflow.py)

---

### TaskClassifierPrimitive

**Classify tasks and route to appropriate handler.**

**Import:**
\`\`\`python
from ttadev.primitives.orchestration import TaskClassifierPrimitive
\`\`\`

**Source:** [\`ttadev/primitives/orchestration/task_classifier_primitive.py\`](ttadev/primitives/orchestration/task_classifier_primitive.py)

---

## Testing Primitives

### MockPrimitive

**Mock primitive for testing workflows.**

**Import:**
\`\`\`python
from ttadev.primitives.testing.mocks import MockPrimitive
\`\`\`

**Source:** [\`ttadev/primitives/testing/mock_primitive.py\`](ttadev/primitives/testing/mock_primitive.py)

**Usage:**
\`\`\`python

# Mock LLM response

mock_llm = MockPrimitive(return_value={"output": "Mocked response"})

# Use in workflow

workflow = input_step >> mock_llm >> output_step

# Test

result = await workflow.execute(input_data, context)
assert mock_llm.call_count == 1
\`\`\`

---

## Observability Primitives

### InstrumentedPrimitive[TInput, TOutput]

**Base class with automatic observability.**

**Import:**
\`\`\`python
from ttadev.primitives.observability import InstrumentedPrimitive
\`\`\`

**Source:** [\`ttadev/primitives/observability/instrumented_primitive.py\`](ttadev/primitives/observability/instrumented_primitive.py)

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
\`\`\`python
from ttadev.primitives.adaptive import AdaptivePrimitive, LearningMode
\`\`\`

**Source:** [\`ttadev/primitives/adaptive/base.py\`](ttadev/primitives/adaptive/base.py)

**Key Concepts:**

- **LearningStrategy**: Named configuration with performance metrics
- **StrategyMetrics**: Success rate, latency, contexts seen
- **LearningMode**: DISABLED, OBSERVE, VALIDATE, ACTIVE
- **Circuit Breaker**: Automatic fallback on high failure rates
- **Context-Aware**: Different strategies for different contexts

**Type Parameters:**

- \`TInput\` - Input data type
- \`TOutput\` - Output data type

**Usage:**
\`\`\`python
from ttadev.primitives import WorkflowContext
from ttadev.primitives.adaptive import (
    AdaptivePrimitive,
    LearningMode,
    LearningStrategy,
    StrategyMetrics,
)

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
\`\`\`

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
\`\`\`python
from ttadev.primitives.adaptive import AdaptiveRetryPrimitive, LearningMode
\`\`\`

**Source:** [\`ttadev/primitives/adaptive/retry.py\`](ttadev/primitives/adaptive/retry.py)

**What It Learns:**

- Optimal number of retries (`max_retries`)
- Better backoff tuning for recurring failure modes
- Context-specific strategies (for example, staging vs production)
- Whether the baseline strategy should remain dominant

**Usage:**
\`\`\`python
from ttadev.primitives import WorkflowContext
from ttadev.primitives.adaptive import AdaptiveRetryPrimitive, LearningMode

adaptive_retry = AdaptiveRetryPrimitive(
    target_primitive=unreliable_api,
    learning_mode=LearningMode.ACTIVE,
    min_observations_before_learning=10,
)

context = WorkflowContext(workflow_id="adaptive-retry-demo")
result = await adaptive_retry.execute(api_request, context)

for name, strategy in adaptive_retry.strategies.items():
    print(f"{name}: {strategy.metrics.success_rate:.1%} success")
\`\`\`

**Automatic Behaviors:**

- ✅ Learns from failures and successes
- ✅ Creates context-specific strategies
- ✅ Validates strategies before adoption
- ✅ Falls back to a baseline strategy on regressions
- ✅ Keeps learning local to the primitive instance unless you add your own persistence

**Example Learned Strategy:**
\`\`\`python
LearningStrategy(
    name="production_high_load_v2",
    description="Learned from repeated production traffic spikes",
    parameters={
        "max_retries": 5,
        "backoff_factor": 2.5,
        "initial_delay": 2.0,
    },
    metrics=StrategyMetrics(
        success_rate=0.94,
        avg_latency_ms=1250.5,
        contexts_seen=1,
    ),
)
\`\`\`

---

### Historical note: `LogseqStrategyIntegration`

`LogseqStrategyIntegration` belongs to the older adaptive/Logseq documentation story and is not
currently exported from `ttadev.primitives.adaptive`.

If you need durable strategy storage today, prefer one of these patterns:

- keep the adaptive primitive in memory and export strategy snapshots yourself
- store learned strategy metadata in your own persistence layer
- build an explicit adapter around the current knowledge or memory primitives instead of assuming a
  built-in Logseq bridge

---

## ACE Framework Primitives

**The current ACE package is centered on self-learning primitives and supporting benchmark types.**

### SelfLearningCodePrimitive

**Purpose**: Generate code, execute it, and learn from execution feedback.
**Import**: `from ttadev.primitives.ace import SelfLearningCodePrimitive, ACEInput`
**Source**: [\`ttadev/primitives/ace/cognitive_manager.py\`](ttadev/primitives/ace/cognitive_manager.py)
**Description**: Combines LLM-assisted code generation, execution feedback, and a learned playbook
of strategies.

### MockACEPlaybook

**Purpose**: Hold learned strategies during local development and tests.
**Import**: `from ttadev.primitives.ace import MockACEPlaybook`
**Source**: [\`ttadev/primitives/ace/cognitive_manager.py\`](ttadev/primitives/ace/cognitive_manager.py)
**Description**: Simple in-memory strategy store used by the ACE learning flow.

### Supporting Types

**Import**: `from ttadev.primitives.ace import ACEInput, ACEOutput, BenchmarkSuite`

- `ACEInput` / `ACEOutput` define the typed contract for the self-learning workflow
- `BenchmarkSuite` and related benchmark types live in `ttadev/primitives/ace/benchmarks.py`
- metrics helpers are exported from `ttadev.primitives.ace` for reporting and aggregation

---

## Complete Layered Example

**Goal:** Build a layered LLM workflow example with cache, timeout, retry, fallback, and routing.

\`\`\`python
from ttadev.primitives.core import RouterPrimitive
from ttadev.primitives import WorkflowContext
from ttadev.primitives.performance import CachePrimitive
from ttadev.primitives.recovery import FallbackPrimitive, RetryPrimitive, TimeoutPrimitive
from ttadev.primitives.recovery.retry import RetryStrategy

cached_llm = CachePrimitive(
    primitive=gpt4_mini,
    cache_key_fn=lambda data, ctx: data["prompt"],
    ttl_seconds=3600.0,
)

timed_llm = TimeoutPrimitive(
    primitive=cached_llm,
    timeout_seconds=30.0,
)

retry_llm = RetryPrimitive(
    primitive=timed_llm,
    strategy=RetryStrategy(max_retries=3, backoff_base=2.0),
)

fallback_llm = FallbackPrimitive(
    primary=retry_llm,
    fallback=claude_sonnet,
)

layered_llm = RouterPrimitive(
    routes={"fast": fallback_llm, "quality": gpt4},
    router_fn=lambda data, ctx: "quality" if "complex" in data.get("prompt", "") else "fast",
    default="fast",
)

context = WorkflowContext(workflow_id="layered-service")
result = await layered_llm.execute({"prompt": "Hello"}, context)
\`\`\`

**Benefits:**

- ✅ Cache repeated work for lower cost and lower latency
- ✅ Bound request duration with a timeout layer
- ✅ Retry transient failures with an explicit `RetryStrategy`
- ✅ Provide graceful degradation with a verified fallback path
- ✅ Route expensive requests only when they need the higher-quality path

---

## Quick Reference Table

### Core Workflow

| Primitive | Operator | Import Path | Purpose |
|-----------|----------|-------------|---------|
| WorkflowPrimitive | - | \`ttadev.primitives\` | Base class |
| SequentialPrimitive | \`>>\` | \`ttadev.primitives\` | Execute in sequence |
| ParallelPrimitive | \`\|\` | \`ttadev.primitives\` | Execute concurrently |
| ConditionalPrimitive | - | \`ttadev.primitives\` | Branch on condition |
| RouterPrimitive | - | \`ttadev.primitives.core\` | Dynamic routing |

### Recovery

| Primitive | Import Path | Purpose |
|-----------|-------------|---------|
| RetryPrimitive | \`ttadev.primitives.recovery\` | Retry with backoff |
| FallbackPrimitive | \`ttadev.primitives.recovery\` | Graceful degradation |
| TimeoutPrimitive | \`ttadev.primitives.recovery\` | Bound execution time |
| CompensationPrimitive | \`ttadev.primitives.recovery\` | Saga pattern |
| CircuitBreakerPrimitive | \`ttadev.primitives.recovery\` | Open/close on repeated failures |

### Performance

| Primitive | Import Path | Purpose |
|-----------|-------------|---------|
| CachePrimitive | \`ttadev.primitives.performance\` | LRU cache with TTL |
| MemoryPrimitive | \`ttadev.primitives.performance.memory\` | In-memory memory primitive and helpers |

### Adaptive/Learning

| Primitive | Import Path | Purpose |
|-----------|-------------|---------|
| AdaptivePrimitive | \`ttadev.primitives.adaptive\` | Base class for self-improving primitives |
| AdaptiveRetryPrimitive | \`ttadev.primitives.adaptive\` | Retry that learns optimal strategies |
| \`LogseqStrategyIntegration\` | historical | Older doc surface; not currently exported |

### Collaboration

| Primitive | Import Path | Purpose |
|-----------|-------------|---------|
| GitCollaborationPrimitive | \`ttadev.primitives.collaboration\` | Enforce Git best practices for multi-agent workflows |
| AgentIdentity | \`ttadev.primitives.collaboration\` | Agent identity and attribution |
| IntegrationFrequency | \`ttadev.primitives.collaboration\` | Integration frequency policies |
| CommitFrequencyPolicy | \`ttadev.primitives.collaboration\` | Commit hygiene policies |
| MergeStrategy | \`ttadev.primitives.collaboration\` | Merge strategy options |

### Orchestration

| Primitive | Import Path | Purpose |
|-----------|-------------|---------|
| DelegationPrimitive | \`ttadev.primitives.orchestration\` | Orchestrator→executor handoff |
| MultiModelWorkflow | \`ttadev.primitives.orchestration\` | Multi-model coordination |
| TaskClassifierPrimitive | \`ttadev.primitives.orchestration\` | Task classification |

### ACE Framework

| Primitive | Import Path | Purpose |
|-----------|-------------|---------|
| SelfLearningCodePrimitive | \`ttadev.primitives.ace\` | Self-learning code generation with execution feedback |
| MockACEPlaybook | \`ttadev.primitives.ace\` | In-memory learned strategy store |
| ACEInput / ACEOutput | \`ttadev.primitives.ace\` | Typed ACE workflow contract |
| BenchmarkSuite | \`ttadev.primitives.ace\` | Benchmark orchestration helpers |

---

## Related Documentation

- **Getting Started:** [\`GETTING_STARTED.md\`](GETTING_STARTED.md)
- **Quickstart:** [\`QUICKSTART.md\`](QUICKSTART.md)
- **Primitive Patterns:** [\`docs/architecture/PRIMITIVE_PATTERNS.md\`](docs/architecture/PRIMITIVE_PATTERNS.md)
- **Git Collaboration Reference:** [\`docs/reference/GIT_COLLABORATION_PRIMITIVE_COMPLETE.md\`](docs/reference/GIT_COLLABORATION_PRIMITIVE_COMPLETE.md)
- **Package README:** [\`ttadev/README.md\`](ttadev/README.md)
- **Agent Instructions:** [\`AGENTS.md\`](AGENTS.md)

---

**Last Updated:** 2026-03-23
**Maintained by:** TTA.dev Team
**License:** See package licenses
