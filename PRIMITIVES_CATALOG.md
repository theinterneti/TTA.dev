# TTA.dev Primitives Catalog

**Complete Reference for All Workflow Primitives**

**Last Updated:** 2026-04-07

---

> [!NOTE]
> All import examples in this file use the current `ttadev.primitives.*` namespace.
> The `extensions` section still has a mixed-current note because some lazy-import metadata
> internally maps to older package names — prefer direct module imports there.
> For a working end-to-end proof, see [`tests/integration/test_multi_agent_proof.py`](tests/integration/test_multi_agent_proof.py).

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
5. [LLM Routing Primitives](#llm-routing-primitives) - Free model discovery and multi-tier routing
6. [Orchestration Primitives](#orchestration-primitives) - Multi-agent coordination
7. [Testing Primitives](#testing-primitives) - Testing utilities
8. [Observability Primitives](#observability-primitives) - Tracing and metrics
9. [ACE Framework Primitives](#ace-framework-primitives) - LLM-powered code generation and learning
10. [Extension Modules](#extension-modules) - Specialized non-core primitives
11. [Composition Patterns](#composition-patterns) - Multi-primitive recipes

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
from ttadev.primitives import WorkflowContext
from ttadev.primitives.recovery import CircuitBreakerPrimitive
from ttadev.primitives.recovery.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitState,
)

config = CircuitBreakerConfig(
    failure_threshold=5,      # 5 consecutive failures to open circuit
    recovery_timeout=30.0,    # seconds before testing recovery
    success_threshold=2,      # successes in HALF_OPEN to close
)
protected_service = CircuitBreakerPrimitive(primitive=unreliable_service, config=config)
ctx = WorkflowContext(workflow_id="demo")

try:
    result = await protected_service.execute(data, ctx)
except CircuitBreakerError as e:
    print(f"Circuit open: {e.failure_count} failures, last={e.last_error}")

# Inspect and manually reset
print(protected_service.state)  # CircuitState.CLOSED | OPEN | HALF_OPEN
protected_service.reset()
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

### AgentMemory

**Durable cross-session memory backed by Hindsight.**

**Import:**

```python
from ttadev.primitives.memory import AgentMemory, InMemoryBackend
```

**Source:** [`ttadev/primitives/memory/agent_memory.py`](ttadev/primitives/memory/agent_memory.py)

**Overview:**

`AgentMemory` is a thin, gracefully-degrading wrapper around the Hindsight HTTP memory API. It provides semantic recall, durable retain, directive fetching, and a `build_context_prefix()` helper that produces a system-prompt-friendly string from directives + relevant memories.

For testing and ephemeral sessions, swap in `InMemoryBackend` — it implements the same async interface with no external dependencies.

```python
from ttadev.primitives.memory import AgentMemory, InMemoryBackend

# ── Production (Hindsight at http://localhost:8888) ──────────────────────────
memory = AgentMemory(bank_id="tta-dev")

if memory.is_available():
    # Recall semantically relevant memories
    results = await memory.recall("retry strategy for LLM calls")
    for r in results:
        print(r["text"])  # MemoryResult: {id, text, type}

    # Store a new memory in structured format
    await memory.retain("[type: decision] Use RetryPrimitive for LLM calls. Rationale: uniform backoff.")

    # Build a system-prompt prefix from directives + relevant memories
    prefix = await memory.build_context_prefix("which model to use for coding tasks")
    # → "## Directives\n- Use uv always\n## Relevant context\n- Prefer Groq..."

# ── Testing / no Hindsight ────────────────────────────────────────────────────
backend = InMemoryBackend(directives=["Use uv, never pip"])
memory = AgentMemory(bank_id="test", _client=backend)
await memory.retain("groq is the fastest provider")
results = await memory.recall("fastest")
assert results[0]["text"] == "groq is the fastest provider"
```

**Key features:**

- **Graceful degradation**: All methods return safe defaults and log warnings when Hindsight is unreachable — they never raise on connectivity failures.
- **`InMemoryBackend`**: Drop-in replacement for unit tests; uses the same async interface.
- **`build_context_prefix(query)`**: Fetches directives and relevant memories concurrently and returns a markdown string suitable for prepending to agent system prompts.
- **MCP tools**: The MCP server exposes `memory_recall`, `memory_retain`, `memory_build_context`, and `memory_list_banks` so AI coding agents can interact with Hindsight directly.

**MCP tool usage (for AI agents):**

```
memory_recall   — semantic search: {query, bank_id, budget}
memory_retain   — store memory:    {content, bank_id, context}
memory_build_context — directives + recall as system-prompt prefix
memory_list_banks    — discover available banks
```

**Hindsight server:**

```bash
# Start (Docker)
docker start hindsight
# Or: docker run -d --name hindsight -p 8888:8888 -p 9999:9999 \
#   -e HINDSIGHT_API_LLM_PROVIDER=groq \
#   -e HINDSIGHT_API_LLM_API_KEY=$GROQ_API_KEY \
#   ghcr.io/ttadev/hindsight:latest

# Health check
curl http://localhost:8888/health
```

**✅ Capabilities:**

- ✅ Semantic recall with `low/mid/high` budget
- ✅ Durable retain (persists across restarts)
- ✅ Directive + mental model fetching
- ✅ Concurrent `build_context_prefix`
- ✅ `InMemoryBackend` for tests
- ✅ MCP tools for agent-facing access

**Use when:**

- Agents need to remember decisions, patterns, or failures across sessions
- You need to inject project-specific context into an LLM system prompt
- TTA players need per-session therapeutic memory (see TTA #267)

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

## LLM Routing Primitives

> Extracted and improved from TTA's 3-tier model management system.
> These primitives make multi-provider LLM routing and free model discovery reusable for any app.

### FreeModelTracker

**Async OpenRouter free-model discovery with local caching.**

```python
from ttadev.primitives.llm import FreeModelTracker, get_free_models, rank_models_for_role

# Standalone helpers
models = await get_free_models()                     # list[ORModel] — cached 1 week
best = rank_models_for_role(models, preferred=["meta-llama/llama-3.1-8b-instruct:free"])

# Stateful tracker (holds in-memory cache)
tracker = FreeModelTracker(api_key="sk-or-...")
await tracker.refresh()
model_id = await tracker.recommend()                 # str | None
```

**`ORModel` dataclass** — one entry from the `/api/v1/models` response:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Full model ID (e.g. `"meta-llama/llama-3.1-8b-instruct:free"`) |
| `context_length` | `int` | Max tokens the model supports |
| `prompt_price` | `float` | Price per prompt token (0.0 for free) |
| `completion_price` | `float` | Price per completion token (0.0 for free) |
| `tags` | `list[str]` | Provider tags |
| `is_free` | `bool` (computed) | True when both prices are 0 |

**Key features:**
- Fully async (`httpx.AsyncClient`)
- Cache lives at `~/.cache/ttadev/or_free_models.json` with a configurable TTL (default 1 week)
- Returns stale cache on network failure instead of raising
- Preferred model lists are caller-configurable, not hardcoded

---

### ModelRouterPrimitive

**YAML-configurable 3-tier LLM router: local → pinned → free-pool.**

```python
from ttadev.primitives.llm import ModelRouterPrimitive, ModelRouterRequest

# Load from YAML config
router = ModelRouterPrimitive.from_yaml("config/model_modes.yaml")

# Call with a named mode
response = await router.execute(
    ModelRouterRequest(
        mode="summarization",
        prompt="Summarize the following text...",
        system="You are a helpful assistant.",
    ),
    context,
)
print(response.text)      # LLMResponse
```

**YAML config format:**

```yaml
# model_modes.yaml
modes:
  summarization:
    tier1:
      provider: ollama
      model: llama3.2
    tier2:
      provider: groq
      model: llama-3.3-70b-versatile    # fast, free Groq tier
    tier3:
      provider: openrouter
      model: meta-llama/llama-3.1-8b-instruct:free
    tier4:
      provider: auto          # FreeModelTracker picks the model
  extraction:
    tier1:
      provider: groq
      model: mistral-saba-24b
      params:
        temperature: 0.1
    tier2:
      provider: together
      model: mistralai/Mistral-7B-Instruct-v0.3   # model required for Together
    tier3:
      provider: openrouter   # null model → tracker selects
```

**Tier providers:**

| Value | Env var | Behaviour |
|-------|---------|-----------|
| `ollama` | — | Calls local Ollama via `/api/chat`. `model` required. |
| `groq` | `GROQ_API_KEY` | Groq cloud (OpenAI-compat). If `model` is null, defaults to `llama-3.1-8b-instant`. |
| `together` | `TOGETHER_API_KEY` | Together AI (OpenAI-compat). `model` required. |
| `openrouter` or `or` | `OPENROUTER_API_KEY` | OpenRouter. If `model` is null/`"auto"`, uses `FreeModelTracker`. |
| `auto` | `OPENROUTER_API_KEY` | `FreeModelTracker` picks best free model, then calls OpenRouter. |

**Tier fallback:** On any exception the router logs a warning and tries the next tier. Raises `RuntimeError("All N tiers failed")` only when every tier fails.

**Return type:** `LLMResponse` (same as `UniversalLLMPrimitive`).

```python
from ttadev.primitives.llm import (
    ModelRouterPrimitive,
    ModelRouterRequest,
    RouterModeConfig,
    RouterTierConfig,
    TaskProfile,
    TASK_CODING, TASK_REASONING, TASK_GENERAL, TASK_SUMMARIZATION, TASK_CREATIVE,
    COMPLEXITY_SIMPLE, COMPLEXITY_MODERATE, COMPLEXITY_COMPLEX,
)
from ttadev.agents import ModelRouterChatAdapter
```

### Task-Aware Routing

Pass a `TaskProfile` to `ModelRouterRequest` and the router will rank available models by benchmark score for that task type:

```python
from ttadev.primitives.llm import ModelRouterPrimitive, ModelRouterRequest, TaskProfile, TASK_CODING, COMPLEXITY_COMPLEX

profile = TaskProfile(task_type=TASK_CODING, complexity=COMPLEXITY_COMPLEX)
response = await router.execute(
    ModelRouterRequest(mode="default", prompt="...", task_profile=profile),
    ctx,
)
```

**Task types:** `TASK_CODING`, `TASK_REASONING`, `TASK_GENERAL`, `TASK_SUMMARIZATION`, `TASK_CREATIVE`
**Complexity:** `COMPLEXITY_SIMPLE`, `COMPLEXITY_MODERATE`, `COMPLEXITY_COMPLEX`

Scoring logic lives in `ttadev/primitives/llm/task_selector.py`.

### ModelRouterChatAdapter

Bridges `ModelRouterPrimitive` to the `ChatPrimitive` protocol used by all agents. Usually constructed automatically via `AgentPrimitive.with_router()`.

```python
from ttadev.agents import ModelRouterChatAdapter

adapter = ModelRouterChatAdapter(router, mode="default", task_profile=profile)
# adapter now satisfies ChatPrimitive — pass it to any agent constructor
agent = DeveloperAgent(model=adapter)
```

The preferred pattern is `AgentPrimitive.with_router()`, which reads each agent's `default_task_profile` automatically:

```python
from ttadev.agents import DeveloperAgent

agent = DeveloperAgent.with_router(router)   # uses TaskProfile(TASK_CODING, COMPLEXITY_COMPLEX)
result = await agent.execute(task, ctx)
```

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

## Coordination Primitives

**Install:** `uv add 'redis[asyncio]'` or `uv sync --extra coordination`
**Import:** `from ttadev.primitives.coordination import ...`

Redis-backed reliable message passing between queue endpoints. Provides
priority queues, visibility-timeout reservations, ack/nack semantics,
dead-letter routing, backpressure, and `recover_pending`.

```python
from redis.asyncio import Redis
from ttadev.primitives.coordination import (
    QueueEndpoint, MessagePriority, RedisMessageCoordinator,
)

redis = Redis.from_url("redis://localhost:6379")
coord = RedisMessageCoordinator(redis, key_prefix="myapp")

worker   = QueueEndpoint(queue_type="worker", instance="1")
ingester = QueueEndpoint(queue_type="ingester")

# Send
await coord.send_message(
    sender=ingester, recipient=worker,
    message_id="job-001", message_type="process",
    payload={"file": "data.csv"},
    priority=MessagePriority.HIGH,
)

# Receive and ack
msg = await coord.receive(worker, visibility_timeout=30)
if msg:
    # ... do work ...
    await coord.ack(worker, msg.token)

# Nack (transient → retry with backoff; permanent → DLQ)
await coord.nack(worker, msg.token, failure=FailureType.TRANSIENT)

# Reclaim expired reservations (pass None to scan all endpoints)
recovered = await coord.recover_pending(worker)
```

**Types:**

| Type | Description |
|------|-------------|
| `QueueEndpoint` | Generic identity: `queue_type: str`, `instance: str` |
| `CoordinationMessage` | Message body with `message_id`, `sender`, `message_type`, `payload`, `priority` |
| `QueuedMessage` | `CoordinationMessage` + queue metadata (attempts, timestamps) |
| `ReceivedMessage` | Reserved message with `token` and `visibility_deadline` |
| `MessagePriority` | `LOW=1`, `NORMAL=5`, `HIGH=9` |
| `FailureType` | `TRANSIENT`, `PERMANENT`, `TIMEOUT` |
| `MessageResult` | `delivered: bool`, `error: str \| None` |
| `MessageCoordinator` | Abstract interface (for testing / alternative backends) |

---

---

## Composition Patterns

Real-world multi-primitive recipes that combine the building blocks above.

### LLM Fallback Chain

```python
from ttadev.primitives import (
    FallbackPrimitive, RetryPrimitive, WorkflowContext,
    UniversalLLMPrimitive, LLMProvider,
)
from ttadev.primitives.recovery.retry import RetryStrategy

groq   = UniversalLLMPrimitive(provider=LLMProvider.GROQ,      api_key="...")
claude = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="...")
ollama = UniversalLLMPrimitive(provider=LLMProvider.OLLAMA)

chain = FallbackPrimitive(
    primary=RetryPrimitive(groq, strategy=RetryStrategy(max_retries=2)),
    fallback=FallbackPrimitive(primary=claude, fallback=ollama),
)
result = await chain.execute(request, WorkflowContext(workflow_id="fallback-demo"))
```

### Circuit Breaker + Fallback

```python
from ttadev.primitives.recovery import CircuitBreakerPrimitive
from ttadev.primitives.recovery.circuit_breaker import CircuitBreakerConfig
from ttadev.primitives import FallbackPrimitive

config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30.0)
chain = FallbackPrimitive(
    primary=CircuitBreakerPrimitive(primitive=groq, config=config),
    fallback=ollama,
)
```

### Safety Gate → LLM

```python
from ttadev.primitives.safety import SafetyGatePrimitive, ThreatLevel
from ttadev.primitives import WorkflowContext

gate = SafetyGatePrimitive(threshold=ThreatLevel.MODERATE)
pipeline = gate >> llm_primitive
result = await pipeline.execute(user_input, WorkflowContext(workflow_id="safe-llm"))
```

## Spec-Driven Development (SDD) Pipeline

Five composable speckit primitives drive systematic, reproducible feature development:

| Primitive | Input | Output |
|-----------|-------|--------|
| `SpecifyPrimitive` | Free-form requirement | Formal spec (JSON) |
| `ClarifyPrimitive` | Spec + questions | Refined spec |
| `PlanPrimitive` | Spec | Implementation plan |
| `TasksPrimitive` | Plan | Ordered task list |
| `ValidationGatePrimitive` | Any | Pass-through or raise |

```python
from ttadev.primitives.speckit import (
    SpecifyPrimitive, ClarifyPrimitive, PlanPrimitive,
    TasksPrimitive, ValidationGatePrimitive,
)
from ttadev.primitives.core.base import WorkflowContext

pipeline = (
    SpecifyPrimitive()
    >> ClarifyPrimitive(max_iterations=2)
    >> PlanPrimitive()
    >> TasksPrimitive()
    >> ValidationGatePrimitive()
)

result = await pipeline.execute(
    {"requirement": "Add Redis caching to the LLM pipeline"},
    WorkflowContext(workflow_id="sdd-demo"),
)
print(result["tasks"])  # ordered, dependent task list
```

See [examples/sdd_workflow.py](examples/sdd_workflow.py) for a full runnable example.

---

## Related Documentation

- **Getting Started:** [\`GETTING_STARTED.md\`](GETTING_STARTED.md)
- **Quickstart:** [\`QUICKSTART.md\`](QUICKSTART.md)
- **Primitive Patterns:** [\`docs/architecture/PRIMITIVE_PATTERNS.md\`](docs/architecture/PRIMITIVE_PATTERNS.md)
- **Git Collaboration Reference:** [\`docs/reference/GIT_COLLABORATION_PRIMITIVE_COMPLETE.md\`](docs/reference/GIT_COLLABORATION_PRIMITIVE_COMPLETE.md)
- **Package README:** [\`ttadev/README.md\`](ttadev/README.md)
- **Agent Instructions:** [\`AGENTS.md\`](AGENTS.md)

---

**Last Updated:** 2026-04-07
**Maintained by:** TTA.dev Team
**License:** See package licenses
