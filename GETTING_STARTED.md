# Getting Started with TTA.dev

**Build reliable AI applications with production-ready primitives and patterns.**

## Quick Start (5 minutes)

This guide provides a rapid introduction to TTA.dev. For a detailed overview, refer to the [README.md](README.md).

### 1. Installation

```bash
# Install with uv (recommended)
uv add tta-dev-primitives
```

### 2. UV Package Management Setup

TTA.dev uses `uv` as the primary package manager for worktree-aware dependency management:

```bash
# Check uv is installed
uv --version

# Sync all dependencies across worktrees
uv sync --all-extras

# Run tests
uv run pytest

# Format code
uv run ruff format .

# Lint code
uv run ruff check . --fix
```

**Worktree Management:**
```bash
# List all worktrees and their packages
python scripts/worktree_init.py list

# Initialize a new worktree
python scripts/worktree_init.py init /path/to/worktree

# Clean cache for specific worktree
python scripts/worktree_init.py clean /path/to/worktree
```

**Shell Aliases (Recommended):**
```bash
# Generate convenient shortcuts for your shell
python scripts/create_shell_aliases.py --list          # Show available aliases
python scripts/create_shell_aliases.py --install       # Add to shell config permanently

# Common aliases you'll get:
# uvsync      → uv sync --all-extras
# uvr         → uv run
# uvtest      → uv run pytest
# uvfmt       → uv run ruff format .
# wtlist      → uv run python scripts/worktree_init.py list
# dev-up      → uvsync && uvlint
# quality-check → uvfmt && uvlint && type-check && uvtest
```

### 3. Your First Workflow

```python
from tta_dev_primitives import (
    CachePrimitive,
    RouterPrimitive,
    RetryPrimitive,
    WorkflowContext
)

# Define your processing function
async def process_with_llm(data: dict, context: WorkflowContext) -> dict:
    # Your LLM call here
    return {"result": "processed"}

# Compose workflow with operators
workflow = (
    CachePrimitive(ttl=3600) >>      # Cache for 1 hour
    RouterPrimitive(tier="balanced") >> # Smart model selection
    RetryPrimitive(max_attempts=3) >>   # Retry on failure
    process_with_llm
)

# Execute
context = WorkflowContext(trace_id="request-123")
result = await workflow.execute({"input": "Hello"}, context)
```

### 3. See Results

Your workflow now has:
- ✅ Automatic caching (30-40% cost reduction)
- ✅ Smart routing to appropriate models
- ✅ Retry logic for transient failures
- ✅ Full observability with traces

## Core Concepts

### Primitives

Small, composable building blocks for workflows:

- **Router**: Choose models based on tier (fast/balanced/quality)
- **Cache**: LRU caching with TTL to reduce costs
- **Retry**: Exponential backoff for reliability
- **Timeout**: Circuit breaker pattern
- **Fallback**: Graceful degradation

### Composition

Combine primitives using operators:

```python
# Sequential: Execute in order
workflow = step1 >> step2 >> step3

# Parallel: Execute concurrently
workflow = step1 | step2 | step3

# Conditional: Branch based on data
workflow = router >> (fast_path if simple else complex_path)
```

### Context

Every execution has context for tracing and correlation:

```python
context = WorkflowContext(
    trace_id="abc-123",
    correlation_id="request-456",
    metadata={"user_id": "user123"}
)
```

## Common Patterns

### Pattern 1: Cached LLM Pipeline

```python
from tta_dev_primitives import CachePrimitive, RouterPrimitive

async def analyze_text(text: str) -> dict:
    workflow = (
        CachePrimitive(ttl=3600) >>
        RouterPrimitive(tier="balanced") >>
        llm_analyzer
    )

    return await workflow.execute(
        {"text": text},
        WorkflowContext()
    )
```

### Pattern 2: Resilient API Call

```python
from tta_dev_primitives import RetryPrimitive, TimeoutPrimitive, FallbackPrimitive

workflow = (
    TimeoutPrimitive(seconds=10) >>
    RetryPrimitive(max_attempts=3, backoff_factor=2.0) >>
    FallbackPrimitive(
        primary=expensive_api,
        fallback=cheap_api
    )
)
```

### Pattern 3: Parallel Processing

```python
from tta_dev_primitives import ParallelPrimitive

# Fetch data from multiple sources concurrently
workflow = ParallelPrimitive([
    fetch_user_profile,
    fetch_recommendations,
    fetch_analytics
])

results = await workflow.execute({"user_id": 123}, context)
```

### Pattern 4: Conversational Memory

```python
from tta_dev_primitives.performance import MemoryPrimitive

# Zero-setup conversational memory (no Docker/Redis required)
memory = MemoryPrimitive(max_size=100)

async def handle_conversation(user_input: str) -> str:
    # Store user message
    await memory.add(
        f"user_{timestamp}",
        {"role": "user", "content": user_input, "timestamp": timestamp}
    )

    # Search conversation history for context
    history = await memory.search(keywords=user_input.split()[:3])

    # Generate response with context
    response = await llm_generate(user_input, history)

    # Store assistant response
    await memory.add(
        f"assistant_{timestamp}",
        {"role": "assistant", "content": response, "timestamp": timestamp}
    )

    return response

# Multi-turn conversation
response1 = await handle_conversation("What is a primitive?")
response2 = await handle_conversation("Can you give me an example?")  # Has context from turn 1

# Optional: Enable Redis for persistence and scaling
memory_persistent = MemoryPrimitive(
    redis_url="redis://localhost:6379",
    enable_redis=True
)
# Same API, enhanced backend - automatic fallback if Redis unavailable
```

**Benefits:**

- ✅ **Zero Setup**: Works immediately without Docker or Redis
- ✅ **Hybrid Architecture**: Automatic upgrade to Redis if available
- ✅ **Graceful Degradation**: Falls back to in-memory if Redis fails
- ✅ **Search**: Keyword search across conversation history
- ✅ **LRU Eviction**: Built-in memory management

**Use Cases:**

- Multi-turn conversational agents
- Task context spanning operations
- Agent memory and recall
- Personalization based on history

### Pattern 5: Self-Improving Workflows

```python
from tta_dev_primitives.adaptive import (
    AdaptiveRetryPrimitive,
    LogseqStrategyIntegration,
    LearningMode
)

# Zero-setup self-improving retry (no manual tuning required)
logseq = LogseqStrategyIntegration("my_app")
adaptive_retry = AdaptiveRetryPrimitive(
    target_primitive=unreliable_api,
    logseq_integration=logseq,
    enable_auto_persistence=True,
    learning_mode=LearningMode.ACTIVE
)

# Learning happens automatically from execution patterns
result = await adaptive_retry.execute(data, context)

# Check what was learned
for name, strategy in adaptive_retry.strategies.items():
    print(f"{name}: {strategy.metrics.success_rate:.1%} success")

# Strategies automatically saved to logseq/pages/Strategies/
```

**Benefits:**

- ✅ **Automatic Learning**: Learns optimal retry parameters without manual tuning
- ✅ **Context-Aware**: Different strategies for production/staging/dev
- ✅ **Production-Safe**: Circuit breakers and validation prevent bad strategies
- ✅ **Knowledge Base**: Strategies persist to Logseq for sharing
- ✅ **Observable**: Full OpenTelemetry integration

**Use Cases:**

- Unreliable external APIs needing adaptive retry strategies
- Services with varying load patterns across contexts
- Teams wanting to share learned strategies via knowledge base
- Production systems requiring automatic optimization

## Cost Optimization

### Smart Caching

```python
# Cache reduces redundant LLM calls by 30-40%
cache = CachePrimitive(
    ttl=3600,              # 1 hour
    max_size=1000,         # Max 1000 entries
    context_aware=True     # Include context in cache key
)
```

### Tiered Routing

```python
# Route to appropriate model based on complexity
router = RouterPrimitive(
    tier="fast",      # Use cheaper, faster model
    # tier="balanced" # Balance cost and quality
    # tier="quality"  # Use best model for hard tasks
)
```

## Observability

### OpenTelemetry Integration

```python
from opentelemetry import trace
from tta_dev_primitives import WorkflowContext

# Context automatically propagates traces
tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("my_operation") as span:
    context = WorkflowContext(
        trace_id=span.get_span_context().trace_id
    )
    result = await workflow.execute(data, context)
```

### Structured Logging

```python
import logging

logger = logging.getLogger(__name__)

# Context provides correlation IDs
logger.info(
    "Workflow completed",
    extra={
        "trace_id": context.trace_id,
        "duration_ms": duration,
        "cache_hit": True
    }
)
```

## Testing

### Testing Your Workflows

```python
from tta_dev_primitives.testing import MockPrimitive, create_test_context

async def test_my_workflow():
    # Use mocks for testing
    mock_llm = MockPrimitive(
        response={"result": "test response"}
    )

    workflow = cache >> mock_llm >> processor

    context = create_test_context(trace_id="test-123")
    result = await workflow.execute({"input": "test"}, context)

    assert result["result"] == "processed test response"
    assert mock_llm.call_count == 1
```

## Next Steps

### 🎓 Structured Learning

**Learning Paths:** [`TTA.dev Learning Paths`](logseq/pages/TTA.dev___Learning%20Paths.md) - Follow structured sequences from beginner to expert

**Interactive Learning:** [`Learning TTA Primitives`](logseq/pages/Learning%20TTA%20Primitives.md) - Flashcards and exercises for mastering concepts

**Knowledge Base:** [`docs/knowledge-base/README.md`](docs/knowledge-base/README.md) - Navigate between documentation and knowledge systems

### 📋 Task Management

**TODO System:** [`TODO Management System`](logseq/pages/TODO%20Management%20System.md) - Central dashboard for all project tasks

Add tasks to today's journal: `logseq/journals/YYYY_MM_DD.md`

### Learn More

- 📚 [Architecture Overview](docs/architecture/Overview.md) - Understand the design
- 🎯 [Coding Standards](docs/development/CodingStandards.md) - Best practices
- 🔧 [MCP Integration](MCP_SERVERS.md) - Model Context Protocol
- 📦 [Package README](packages/tta-dev-primitives/README.md) - Detailed docs

### Production Examples

**Start here!** 5 validated, working examples ready to run:

| Example | What It Shows | Use When |
|---------|---------------|----------|
| [**RAG Workflow**](packages/tta-dev-primitives/examples/rag_workflow.py) | Caching + Fallback + Retry | Building document retrieval systems |
| [**Agentic RAG**](packages/tta-dev-primitives/examples/agentic_rag_workflow.py) | Router + Grading + Validation | Production RAG with quality controls |
| [**Cost Tracking**](packages/tta-dev-primitives/examples/cost_tracking_workflow.py) | Budget Enforcement + Metrics | Managing LLM API costs |
| [**Streaming**](packages/tta-dev-primitives/examples/streaming_workflow.py) | AsyncIterator + Buffering | Real-time response streaming |
| [**Multi-Agent**](packages/tta-dev-primitives/examples/multi_agent_workflow.py) | Coordinator + Parallel Execution | Complex agent orchestration |
| [**Memory Workflow**](packages/tta-dev-primitives/examples/memory_workflow.py) | Conversational Memory + Search | Multi-turn conversations with context |

**Quick Start:**

```bash
# Run any example
uv run python packages/tta-dev-primitives/examples/rag_workflow.py

# Or explore all examples
ls packages/tta-dev-primitives/examples/
```

**Implementation Guide:** [`packages/tta-dev-primitives/examples/PHASE3_EXAMPLES_COMPLETE.md`](packages/tta-dev-primitives/examples/PHASE3_EXAMPLES_COMPLETE.md) - Comprehensive documentation including:
- Complete implementation details for all examples
- InstrumentedPrimitive pattern guide
- Test results and validation
- Production usage recommendations

### Additional Examples

More patterns in the examples directory:
- [Basic workflows](packages/tta-dev-primitives/examples/basic_workflow.py) - Foundation patterns
- [Composition patterns](packages/tta-dev-primitives/examples/composition.py) - Combining primitives
- [Error handling](packages/tta-dev-primitives/examples/error_handling.py) - Recovery patterns
- [Observability](packages/tta-dev-primitives/examples/observability.py) - Tracing and metrics

### Get Help

- 📖 Documentation: See `docs/` directory
- 💻 Examples: See `packages/tta-dev-primitives/examples/`
- 🐛 Issues: Open an issue on GitHub
- 💬 Discussions: GitHub Discussions

## Cline Integration

TTA.dev provides a powerful Cline integration to streamline development and enforce best practices. For detailed information on Cline hooks, VS Code configuration, and TTA.dev primitives exposed as MCP tools, refer to [`CLINE_INTEGRATION_GUIDE.md`](CLINE_INTEGRATION_GUIDE.md).

## Advanced Topics

### Custom Primitives

Create your own primitives:

```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext

class CustomPrimitive(WorkflowPrimitive):
    """Your custom primitive."""

    async def _execute(
        self,
        data: dict,
        context: WorkflowContext
    ) -> dict:
        # Your implementation
        return processed_data
```

### Performance Tuning

Tips for optimal performance:

1. **Use caching aggressively** - Cache at multiple levels
2. **Choose appropriate tiers** - Use fast tier for simple tasks
3. **Parallel execution** - Run independent operations concurrently
4. **Monitor metrics** - Track cache hit rate, latency, costs
5. **Profile before optimizing** - Measure to find bottlenecks

### Production Checklist

Before deploying:

- [ ] All tests passing with 100% coverage
- [ ] Observability configured (traces, logs, metrics)
- [ ] Error handling tested for all failure modes
- [ ] Caching strategy validated
- [ ] Performance benchmarked
- [ ] Security review completed
- [ ] Documentation updated

## Philosophy

### Production-First

Every component is battle-tested and production-ready:
- Comprehensive test coverage
- Real-world usage validation
- Performance optimized
- Well documented

### Composable

Build complex workflows from simple primitives:
- Single Responsibility Principle
- Clear interfaces
- Operator-based composition
- Mix and match freely

### Observable

Understand what's happening:
- OpenTelemetry integration
- Structured logging
- Trace propagation
- Performance metrics

## Contributing

Interested in contributing? Check out:
- [Coding Standards](docs/development/CodingStandards.md)
- [Architecture Overview](docs/architecture/Overview.md)
- Existing examples and tests

---

**Ready to build?** Start with the [quick start](#quick-start-5-minutes) above or explore the [examples](packages/tta-dev-primitives/examples/).

---

**Last Updated:** 2025-11-10
