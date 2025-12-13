# TTA.dev Agent Instructions

**Primary Hub for AI Agent Discovery and Guidance**

---

## 🎯 Quick Start for AI Agents

Welcome to TTA.dev! This file is your entry point for understanding and working with this codebase.

### What is TTA.dev?

TTA.dev is a production-ready **AI development toolkit** providing:

- **Agentic primitives** for building reliable AI workflows
- **Composable patterns** with type-safe operators (`>>`, `|`)
- **Built-in observability** with OpenTelemetry integration
- **Multi-package monorepo** with focused, reusable components

### 📋 TODO Management & Knowledge Base

**IMPORTANT:** All agents must use the Logseq TODO management system:

**🧭 Knowledge Base Hub:** [`docs/knowledge-base/README.md`](docs/knowledge-base/README.md) - **START HERE** for intelligent navigation between documentation and knowledge base systems.

- **📐 TODO Architecture:** [`logseq/pages/TTA.dev/TODO Architecture.md`](logseq/pages/TTA.dev___TODO%20Architecture.md) - Complete system design
- **📊 Main Dashboard:** [`logseq/pages/TODO Management System.md`](logseq/pages/TODO%20Management%20System.md) - Active queries
- **📋 Templates:** [`logseq/pages/TODO Templates.md`](logseq/pages/TODO%20Templates.md) - Copy-paste patterns
- **🎓 Learning Paths:** [`logseq/pages/TTA.dev___Learning Paths.md`](logseq/pages/TTA.dev___Learning%20Paths.md) - Structured sequences
- **📈 Metrics:** [`logseq/pages/TTA.dev/TODO Metrics Dashboard.md`](logseq/pages/TTA.dev___TODO%20Metrics%20Dashboard.md) - Analytics
- **⚡ Quick Reference:** [`logseq/pages/TODO Architecture Quick Reference.md`](logseq/pages/TODO%20Architecture%20Quick%20Reference.md) - Fast lookup

**Package Dashboards:**

- [`TTA.dev/Packages/tta-dev-primitives/TODOs`](logseq/pages/TTA.dev___Packages___tta-dev-primitives___TODOs.md) - Core primitives ✅
- [`TTA.dev/Packages/tta-observability-integration/TODOs`](logseq/pages/TTA.dev___Packages___tta-observability-integration___TODOs.md) - Observability ✅
- [`TTA.dev/Packages/universal-agent-context/TODOs`](logseq/pages/TTA.dev___Packages___universal-agent-context___TODOs.md) - Agent context ✅

**Daily Journal:** Add TODOs to `logseq/journals/YYYY_MM_DD.md`

**Tag Convention:**

- `#dev-todo` - Development work (building TTA.dev itself)
- `#learning-todo` - User education (tutorials, flashcards, exercises)
- `#template-todo` - Reusable patterns (for agents/users)
- `#ops-todo` - Infrastructure (deployment, monitoring)
- `#non-actionable` - Contextual notes, not actionable tasks (ignored by codebase scanner)

**When to Update:**

1. **Creating TODOs:** Add to today's journal with appropriate tags and properties
2. **Completing Work:** Mark tasks as DONE in journal
3. **Documentation:** Link related Logseq pages in your work
4. **Blocking Issues:** Document blockers in TODO properties
5. **Daily Standup:** Review TODO dashboards in Logseq

**Quick Example:**

```markdown
## [[2025-10-31]] Daily TODOs

- TODO Implement CachePrimitive metrics #dev-todo
  type:: implementation
  priority:: high
  package:: tta-observability-integration
  related:: [[TTA Primitives/CachePrimitive]]

- TODO Create flashcards for retry patterns #user-todo
  type:: learning
  audience:: intermediate-users
  time-estimate:: 20 minutes
```

**TODO Triage Workflow:** Use the [[TODO Triage]] template to process `TODO` comments from codebase scans.

**See:** [`logseq/pages/TTA.dev___Logseq Advanced Features.md`](logseq/pages/TTA.dev___Logseq%20Advanced%20Features.md) for complete Logseq guide.
**See also:** [`docs/status-reports/todo-management/TODO_GUIDELINES.md`](docs/status-reports/todo-management/TODO_GUIDELINES.md) for detailed guidelines on actionable vs. non-actionable TODOs.

### 🎯 Know Your Copilot Context

**CRITICAL:** If you're GitHub Copilot, understand which context you're in:

- **🖥️ VS Code Extension (LOCAL):** You have MCP servers, toolsets, local filesystem
- **☁️ Coding Agent (CLOUD):** You run in GitHub Actions, NO MCP/toolsets
- **💻 GitHub CLI (TERMINAL):** You run in terminal via `gh copilot`

**Full details:** See `.github/copilot-instructions.md` section "📍 CRITICAL: Know Your Context"

**Why this matters:** Configuration, tools, and capabilities differ by context. Don't assume LOCAL features are available in CLOUD environment or vice versa.

### ⚡ Before You Code: Primitive Usage Rules

**CRITICAL:** When working on TTA.dev, **ALWAYS use primitives** for these patterns:

| Pattern | ❌ Don't Use | ✅ Use Instead |
|---------|-------------|----------------|
| Sequential workflows | Manual async chains | `SequentialPrimitive` or `>>` operator |
| Parallel execution | `asyncio.gather()` | `ParallelPrimitive` or `\|` operator |
| Error handling | Try/except loops | `RetryPrimitive`, `FallbackPrimitive` |
| Timeouts | `asyncio.wait_for()` | `TimeoutPrimitive` |
| Caching | Manual dicts | `CachePrimitive` |
| Routing | If/else chains | `RouterPrimitive` |

**Standard Import Pattern:**

```python
from tta_dev_primitives import (
    WorkflowPrimitive,
    SequentialPrimitive,
    ParallelPrimitive,
    WorkflowContext
)
from tta_dev_primitives.recovery import (
    RetryPrimitive,
    FallbackPrimitive,
    TimeoutPrimitive
)
from tta_dev_primitives.performance import CachePrimitive
```

**Before Committing:**

```bash
# Validate your code uses primitives correctly
./scripts/validate-primitive-usage.sh

# Or run full quality check
uv run ruff check . --fix && uvx pyright packages/
```

**Validation Checklist:** See [`.github/AGENT_CHECKLIST.md`](.github/AGENT_CHECKLIST.md) for complete pre-commit verification steps.

**KB Health Check:**
```bash
uv run python scripts/validate_kb_links.py
```
*   Run this script to ensure all links between documentation, code, and the knowledge base are healthy.
*   Fix any broken links or orphans before committing.

**Prompt Templates:** See `packages/tta-dev-primitives/examples/` for copy-paste code patterns.

### Repository Structure

```text
TTA.dev/
├── packages/
│   ├── tta-dev-primitives/          # ✅ Core workflow primitives
│   ├── tta-observability-integration/  # ✅ OpenTelemetry integration
│   ├── universal-agent-context/      # ✅ Agent context management
│   ├── keploy-framework/             # ⚠️ Under review - minimal implementation
│   ├── python-pathway/               # ⚠️ Under review - unclear use case
│   └── js-dev-primitives/            # 🚧 Planned - not implemented
├── docs/                             # Comprehensive documentation
│   ├── planning/                     # Planning documents (moved from root)
│   └── ...
├── archive/
│   └── status-reports/               # Historical status files
├── scripts/                          # Automation and validation scripts
└── tests/                            # Integration tests
```

---

## 📚 Package-Specific Agent Instructions

Each package has detailed agent instructions. **Always read the package-specific AGENTS.md before working on that package:**

### ✅ Production Packages (Active in Workspace)

| Package | Status | AGENTS.md | Purpose |
|---------|--------|-----------|---------|
| **tta-dev-primitives** | ✅ Active | [`packages/tta-dev-primitives/AGENTS.md`](packages/tta-dev-primitives/AGENTS.md) | Core workflow primitives (Sequential, Parallel, Router, Retry, Fallback, Cache, etc.) |
| **tta-observability-integration** | ✅ Active | [`packages/tta-observability-integration/README.md`](packages/tta-observability-integration/README.md) | OpenTelemetry tracing, metrics, logging |
| **universal-agent-context** | ✅ Active | [`packages/universal-agent-context/AGENTS.md`](packages/universal-agent-context/AGENTS.md) | Agent context management and orchestration |

### ⚠️ Packages Under Review

| Package | Status | Documentation | Issue |
|---------|--------|---------------|-------|
| **keploy-framework** | ⚠️ Under Review | Minimal | No pyproject.toml, no tests, not in workspace. **Decision needed by Nov 7, 2025** |
| **python-pathway** | ⚠️ Under Review | Minimal | No clear use case documented, not in workspace. **Decision needed by Nov 7, 2025** |
| **js-dev-primitives** | 🚧 Placeholder | None | Directory structure only, no implementation. **Decision needed by Nov 14, 2025** |

**Note:** Only the 3 production packages above are included in the uv workspace and fully supported. Packages under review require architectural decisions before use.

---

## 🧱 Agentic Primitives - Quick Reference

TTA.dev's core value is **composable workflow primitives**. Here are the key primitives you'll use:

### Core Workflow Primitives

| Primitive | Purpose | Import Path | Example |
|-----------|---------|-------------|---------|
| `WorkflowPrimitive[T,U]` | Base class for all primitives | `from tta_dev_primitives import WorkflowPrimitive` | [base.py](packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py) |
| `SequentialPrimitive` | Execute steps in sequence | `from tta_dev_primitives import SequentialPrimitive` | [examples/basic_sequential.py](packages/tta-dev-primitives/examples/basic_workflow.py) |
| `ParallelPrimitive` | Execute steps in parallel | `from tta_dev_primitives import ParallelPrimitive` | [examples/parallel_execution.py](packages/tta-dev-primitives/examples/composition.py) |
| `ConditionalPrimitive` | Conditional branching | `from tta_dev_primitives import ConditionalPrimitive` | [conditional.py](packages/tta-dev-primitives/src/tta_dev_primitives/core/conditional.py) |
| `RouterPrimitive` | Dynamic routing (LLM selection, etc.) | `from tta_dev_primitives import RouterPrimitive` | [examples/router_llm_selection.py](packages/tta-dev-primitives/examples/error_handling.py) |

### Recovery Primitives

| Primitive | Purpose | Import Path | Example |
|-----------|---------|-------------|---------|
| `RetryPrimitive` | Retry with backoff strategies | `from tta_dev_primitives.recovery import RetryPrimitive` | [retry.py](packages/tta-dev-primitives/src/tta_dev_primitives/recovery/retry.py) |
| `FallbackPrimitive` | Graceful degradation | `from tta_dev_primitives.recovery import FallbackPrimitive` | [fallback.py](packages/tta-dev-primitives/src/tta_dev_primitives/recovery/fallback.py) |
| `TimeoutPrimitive` | Circuit breaker pattern | `from tta_dev_primitives.recovery import TimeoutPrimitive` | [timeout.py](packages/tta-dev-primitives/src/tta_dev_primitives/recovery/timeout.py) |
| `CompensationPrimitive` | Saga pattern for rollback | `from tta_dev_primitives.recovery import CompensationPrimitive` | [compensation.py](packages/tta-dev-primitives/src/tta_dev_primitives/recovery/compensation.py) |

### Performance Primitives

| Primitive | Purpose | Import Path | Example |
|-----------|---------|-------------|---------|
| `CachePrimitive` | LRU + TTL caching | `from tta_dev_primitives.performance import CachePrimitive` | [cache.py](packages/tta-dev-primitives/src/tta_dev_primitives/performance/cache.py) |

### Testing Primitives

| Primitive | Purpose | Import Path | Example |
|-----------|---------|-------------|---------|
| `MockPrimitive` | Testing and mocking | `from tta_dev_primitives.testing import MockPrimitive` | [mock_primitive.py](packages/tta-dev-primitives/src/tta_dev_primitives/testing/mock_primitive.py) |

### Adaptive/Self-Improving Primitives ⭐ NEW

**Primitives that learn from observability data and automatically improve their behavior.**

| Primitive | Purpose | Import Path | Example |
|-----------|---------|-------------|---------|
| `AdaptivePrimitive[T,U]` | Base class for self-improving primitives | `from tta_dev_primitives.adaptive import AdaptivePrimitive` | [base.py](packages/tta-dev-primitives/src/tta_dev_primitives/adaptive/base.py) |
| `AdaptiveRetryPrimitive` | Retry that learns optimal strategies | `from tta_dev_primitives.adaptive import AdaptiveRetryPrimitive` | [retry.py](packages/tta-dev-primitives/src/tta_dev_primitives/adaptive/retry.py) |
| `LogseqStrategyIntegration` | Persist learned strategies to KB | `from tta_dev_primitives.adaptive import LogseqStrategyIntegration` | [logseq_integration.py](packages/tta-dev-primitives/src/tta_dev_primitives/adaptive/logseq_integration.py) |

**Quick Start:**

```python
from tta_dev_primitives.adaptive import (
    AdaptiveRetryPrimitive,
    LogseqStrategyIntegration,
    LearningMode
)

# Setup Logseq integration for automatic persistence
logseq = LogseqStrategyIntegration("my_service")

# Create adaptive retry - learns optimal retry strategies!
adaptive_retry = AdaptiveRetryPrimitive(
    target_primitive=unreliable_api,
    logseq_integration=logseq,
    enable_auto_persistence=True
)

# Use it - learning happens automatically!
result = await adaptive_retry.execute(data, context)

# Strategies automatically saved to logseq/pages/Strategies/
# Check learned strategies: logseq/pages/Strategies/my_service_*.md
```

**Key Features:**

- ✅ **Automatic Learning** - Learns from execution patterns without manual tuning
- ✅ **Context-Aware** - Different strategies for different contexts (production/staging/dev)
- ✅ **Production-Safe** - Circuit breakers and validation windows prevent bad strategies
- ✅ **Knowledge Base** - Automatically persists strategies to Logseq for discovery and sharing
- ✅ **Observable** - Full OpenTelemetry integration shows learning process
- ✅ **Composable** - Works with all other TTA.dev primitives

**Examples:**

- [auto_learning_demo.py](examples/auto_learning_demo.py) - Automatic learning and persistence ✅
- [verify_adaptive_primitives.py](examples/verify_adaptive_primitives.py) - Comprehensive verification suite ✅
- [production_adaptive_demo.py](examples/production_adaptive_demo.py) - Production multi-region simulation ✅

**Documentation:**

- [`docs/ADAPTIVE_PRIMITIVES_PHASES_1_3_COMPLETE.md`](docs/ADAPTIVE_PRIMITIVES_PHASES_1_3_COMPLETE.md) - Comprehensive verification report
- [`archive/reports_and_logs/ADAPTIVE_PRIMITIVES_AUDIT.md`](archive/reports_and_logs/ADAPTIVE_PRIMITIVES_AUDIT.md) - System audit and quality review
- [`archive/reports_and_logs/ADAPTIVE_PRIMITIVES_IMPROVEMENTS.md`](archive/reports_and_logs/ADAPTIVE_PRIMITIVES_IMPROVEMENTS.md) - Latest improvements summary

**Full catalog with detailed examples:** [`PRIMITIVES_CATALOG.md`](PRIMITIVES_CATALOG.md)

---

## 🔗 Composition Patterns

TTA.dev uses **operator overloading** for intuitive workflow composition:

### Sequential Composition (`>>`)

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

# Chain operations in sequence
workflow = step1 >> step2 >> step3

# Execute
context = WorkflowContext(data={"input": "value"})
result = await workflow.execute(context, input_data)
```

### Parallel Composition (`|`)

```python
from tta_dev_primitives import ParallelPrimitive

# Execute operations in parallel
workflow = branch1 | branch2 | branch3

# All branches run concurrently
result = await workflow.execute(context, input_data)
```

### Mixed Composition

```python
# Complex workflows with mixed patterns
workflow = (
    input_processor >>
    (fast_path | slow_path | cached_path) >>
    aggregator >>
    output_formatter
)
```

**More patterns:** See [`packages/tta-dev-primitives/examples/`](packages/tta-dev-primitives/examples/)

---

## 🏗️ Common Workflows

### 1. LLM Router with Fallback

```python
from tta_dev_primitives import RouterPrimitive
from tta_dev_primitives.recovery import FallbackPrimitive

# Route to best LLM, fallback if unavailable
router = RouterPrimitive(
    routes={
        "fast": gpt4_mini,
        "complex": gpt4,
        "local": llama_local,
    },
    default_route="fast"
)

workflow = FallbackPrimitive(
    primary=router,
    fallbacks=[backup_llm, cached_response]
)
```

### 2. Retry with Exponential Backoff

```python
from tta_dev_primitives.recovery import RetryPrimitive

# Automatically retry failed operations
workflow = RetryPrimitive(
    primitive=api_call,
    max_retries=3,
    backoff_strategy="exponential",
    initial_delay=1.0
)
```

### 3. Parallel Data Processing with Cache

```python
from tta_dev_primitives import ParallelPrimitive
from tta_dev_primitives.performance import CachePrimitive

# Cache expensive operations
cached_processor = CachePrimitive(
    primitive=expensive_llm_call,
    ttl_seconds=3600,
    max_size=1000
)

# Process in parallel with caching
workflow = ParallelPrimitive(
    primitives=[cached_processor] * 10  # 10 parallel workers
)
```

### 4. Iterative Code Refinement with E2B ⭐ NEW

**CRITICAL PATTERN:** When generating code with AI, always validate it works before using!

```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive

# Pattern: Generate → Execute → Fix → Repeat until working
class IterativeCodeGenerator:
    def __init__(self):
        self.code_executor = CodeExecutionPrimitive()
        self.max_attempts = 3

    async def generate_working_code(self, requirement: str, context):
        """Keep generating until code executes successfully."""
        for attempt in range(1, self.max_attempts + 1):
            # Step 1: Generate code (LLM)
            code = await llm_generate_code(requirement, previous_errors)

            # Step 2: Execute in E2B sandbox
            result = await self.code_executor.execute(
                {"code": code, "timeout": 30},
                context
            )

            # Step 3: Check if it works
            if result["success"]:
                return {"code": code, "output": result["logs"]}

            # Step 4: Feed error back to LLM for next iteration
            previous_errors = result["error"]

        raise Exception("Failed to generate working code")
```

**When to use this pattern:**

- ✅ Test generation workflows (generate → execute → validate)
- ✅ Documentation code snippets (ensure examples work)
- ✅ PR code validation (run tests before merge)
- ✅ AI coding assistants (validate before suggesting)
- ✅ Data processing scripts (catch errors early)

**Benefits:**

- Real validation (not just LLM opinion that "code looks good")
- Catch syntax errors, import errors, logic bugs
- $0 cost (E2B FREE tier) + ~$0.01/iteration (LLM)
- Typically 1-3 iterations = working code

**Full example:** [`examples/e2b_iterative_code_refinement.py`](packages/tta-dev-primitives/examples/e2b_iterative_code_refinement.py)

**More examples:** [`packages/tta-dev-primitives/examples/`](packages/tta-dev-primitives/examples/)

---

## 🔍 Observability

All primitives have **built-in observability**:

- **Structured Logging**: Every primitive logs execution details
- **Distributed Tracing**: OpenTelemetry spans for each operation
- **Metrics**: Prometheus-compatible metrics (execution time, success rate, etc.)
- **Context Propagation**: `WorkflowContext` carries state and correlation IDs

### WorkflowContext

```python
from tta_dev_primitives import WorkflowContext

# Create context with correlation ID
context = WorkflowContext(
    correlation_id="req-12345",
    data={
        "user_id": "user-789",
        "request_type": "analysis"
    }
)

# Context is passed through entire workflow
result = await workflow.execute(context, input_data)
```

**Full observability guide:** [`docs/observability/`](docs/observability/)

### Observability Integration

**Two-Package Architecture:**

1. **Core Observability** (`tta-dev-primitives/observability/`)
   - `InstrumentedPrimitive` - Base class with automatic tracing
   - `ObservablePrimitive` - Wrapper for adding observability to existing primitives
   - `PrimitiveMetrics` - Metrics collection
   - Built into all primitives

2. **Enhanced Primitives** (`tta-observability-integration/`)
   - `initialize_observability()` - Setup OpenTelemetry + Prometheus
   - Enhanced primitives: `RouterPrimitive`, `CachePrimitive`, `TimeoutPrimitive`
   - Prometheus metrics export on port 9464
   - Graceful degradation when OpenTelemetry unavailable

**Quick Setup:**

```python
from observability_integration import initialize_observability
from observability_integration.primitives import RouterPrimitive, CachePrimitive

# Initialize observability
success = initialize_observability(
    service_name="my-app",
    enable_prometheus=True
)

# Use enhanced primitives
workflow = (
    input_step >>
    RouterPrimitive(routes={"fast": llm1, "quality": llm2}) >>
    CachePrimitive(expensive_op, ttl_seconds=3600) >>
    output_step
)
```

**Benefits:**

- 30-40% cost reduction (via Cache + Router)
- Real-time metrics in Prometheus/Grafana
- Distributed tracing across workflows
- Automatic span creation and context propagation

**See:** [`docs/architecture/COMPONENT_INTEGRATION_ANALYSIS.md`](docs/architecture/COMPONENT_INTEGRATION_ANALYSIS.md#1-tta-observability-integration) for detailed integration guide.

---

## 🧪 Testing Patterns

Use `MockPrimitive` for testing workflows:

```python
from tta_dev_primitives.testing import MockPrimitive
import pytest

@pytest.mark.asyncio
async def test_workflow():
    # Mock a primitive
    mock_llm = MockPrimitive(
        return_value={"response": "mocked output"}
    )

    # Test workflow with mock
    workflow = step1 >> mock_llm >> step3
    result = await workflow.execute(context, input_data)

    assert result["response"] == "mocked output"
    assert mock_llm.call_count == 1
```

**Testing guide:** [`packages/tta-dev-primitives/AGENTS.md#testing`](packages/tta-dev-primitives/AGENTS.md)

---

## 🛠️ Development Environment

### Prerequisites

- **Python 3.11+** (required for modern type hints)
- **uv** package manager (NOT pip)
- **VS Code** with recommended extensions

### Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev

# Sync dependencies
uv sync --all-extras

# Run tests
uv run pytest -v
```

### VS Code Configuration

**Recommended Extensions:**

- GitHub Copilot (required for toolsets)
- Python + Pylance (type checking)
- Ruff (linting/formatting)
- GitLens (Git integration)

**Copilot Toolsets:** See `docs/guides/Copilot_Toolsets_Guide.md`

- Use `#tta-package-dev` for primitive development
- Use `#tta-testing` for test development
- Use `#tta-observability` for tracing/metrics work

**Full setup guide:** [`GETTING_STARTED.md`](GETTING_STARTED.md)

---

## 📝 Code Style & Conventions

### Type Hints

```python
# ✅ Modern Python 3.11+ style
def process(data: str | None) -> dict[str, Any]:
    ...

# ❌ Old style
def process(data: Optional[str]) -> Dict[str, Any]:
    ...
```

### Package Manager

```bash
# ✅ Use uv
uv add package-name
uv run pytest

# ❌ Don't use pip
pip install package-name  # WRONG
```

### Async Patterns

```python
# ✅ Use primitives
workflow = step1 >> step2 >> step3

# ❌ Manual async orchestration
async def workflow():
    result1 = await step1()
    result2 = await step2(result1)
    return await step3(result2)
```

**Full style guide:** [`.github/instructions/`](.github/instructions/)

---

## 🤝 Multi-Agent Coordination

When multiple AI agents work on TTA.dev:

### Package Boundaries

- **Stay within package boundaries** when making changes
- **Coordinate cross-package changes** via issues/PRs
- **Use `WorkflowContext`** for passing state between primitives
- **Document agent decisions** in commit messages

### Communication Pattern

```python
# Good: Agent documents reasoning
"""
Agent Decision: Using RetryPrimitive instead of manual try/except
Reasoning: Built-in exponential backoff + observability
Tradeoff: Slightly more memory, but better reliability
"""
```

### Conflict Resolution

1. **Check package AGENTS.md** for specific guidance
2. **Prefer composition** over modification
3. **Run full test suite** before committing
4. **Update documentation** with changes

---

## 📖 Documentation

### Key Documentation Files

| File | Purpose |
|------|---------|
| [`README.md`](README.md) | Project overview and quick start |
| [`GETTING_STARTED.md`](GETTING_STARTED.md) | Detailed setup guide |
| [`PRIMITIVES_CATALOG.md`](PRIMITIVES_CATALOG.md) | Complete primitive reference |
| [`docs/guides/PHASE3_EXAMPLES_COMPLETE.md`](docs/guides/PHASE3_EXAMPLES_COMPLETE.md) | Phase 3 examples implementation guide |
| [`MCP_SERVERS.md`](MCP_SERVERS.md) | MCP server integrations |
| [`docs/architecture/`](docs/architecture/) | Architecture decisions and patterns |
| [`docs/guides/`](docs/guides/) | Usage guides and tutorials |

### Per-Package Documentation

Each package has:

- `README.md` - Package overview and API docs
- `AGENTS.md` (or `.github/copilot-instructions.md`) - Agent-specific guidance
- `examples/` - Working code examples

---

## 🚀 Quick Wins

### For Agent Development

1. **Start with examples:** [`packages/tta-dev-primitives/examples/`](packages/tta-dev-primitives/examples/)
2. **Review Phase 3 patterns:** See [`docs/guides/PHASE3_EXAMPLES_COMPLETE.md`](docs/guides/PHASE3_EXAMPLES_COMPLETE.md) for production patterns
3. **Use composition:** Chain primitives with `>>` and `|`
4. **Add observability:** Use `WorkflowContext` for all workflows
5. **Test with mocks:** Use `MockPrimitive` for unit tests
6. **Check toolsets:** Use `#tta-agent-dev` in Copilot for agent-specific tools
7. **Try adaptive primitives:** Use `AdaptiveRetryPrimitive` for self-improving workflows

### For Self-Improving Workflows

1. **Start simple:** Use `AdaptiveRetryPrimitive` with existing unreliable operations
2. **Enable auto-persistence:** Add `LogseqStrategyIntegration` for automatic KB updates
3. **Review learned strategies:** Check `logseq/pages/Strategies/` for insights
4. **Use learning modes:** Start with `OBSERVE`, move to `VALIDATE`, then `ACTIVE`
5. **Monitor learning:** Check OpenTelemetry traces for learning events

### For Observability Work

1. **Use tta-observability-integration:** Don't reinvent tracing
2. **Leverage existing primitives:** Add to `observability/primitives/`
3. **Follow OpenTelemetry standards:** Span names, attributes, events
4. **Test with Prometheus:** Use `docker-compose.test.yml`

### For Testing

1. **100% coverage required:** All new code must be tested
2. **Use pytest-asyncio:** `@pytest.mark.asyncio` for async tests
3. **Mock external services:** Use `MockPrimitive` or `pytest-mock`
4. **Run full suite:** `uv run pytest -v` before committing

---

## ⚠️ Anti-Patterns to Avoid

| ❌ Anti-Pattern | ✅ Better Approach |
|----------------|-------------------|
| Manual async orchestration | Use `SequentialPrimitive` or `ParallelPrimitive` |
| Try/except with retry logic | Use `RetryPrimitive` |
| `asyncio.wait_for()` for timeouts | Use `TimeoutPrimitive` |
| Manual caching dictionaries | Use `CachePrimitive` |
| Global variables for state | Use `WorkflowContext` |
| Using `pip` | Use `uv` |
| Old type hints (`Optional[T]`) | Use `T \| None` |
| Modifying core primitives | Extend via composition |

---

## 🎯 Priority Framework

When making decisions, prioritize:

1. **Correctness** - Code must work and be tested
2. **Type Safety** - Full type annotations required
3. **Composability** - Use primitives for reusable patterns
4. **Testability** - Easy to test with mocks
5. **Performance** - Parallel where appropriate
6. **Observability** - Traceable and debuggable

---

## 🔗 Quick Links

- **GitHub Repository:** <https://github.com/theinterneti/TTA.dev>
- **Issues:** <https://github.com/theinterneti/TTA.dev/issues>
- **Pull Requests:** <https://github.com/theinterneti/TTA.dev/pulls>
- **CI/CD:** <https://github.com/theinterneti/TTA.dev/actions>

---

## 📞 Getting Help

1. **Check package AGENTS.md** - Most specific guidance
2. **Review examples** - Working code in `examples/`
3. **Search documentation** - `docs/` directory
4. **Check Copilot toolsets** - `.vscode/copilot-toolsets.jsonc`
5. **Open an issue** - For bugs or feature requests

---

**Last Updated:** October 29, 2025
**Maintained by:** TTA.dev Team
**License:** MIT License - see [LICENSE](LICENSE) for details


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Agents]]
