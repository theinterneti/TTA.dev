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

**IMPORTANT:** All agents must use the Logseq TODO management system. Refer to the `.clinerules` for detailed tag conventions and properties.

**🧭 Knowledge Base Hub:** [`docs/knowledge-base/README.md`](docs/knowledge-base/README.md) - **START HERE** for intelligent navigation between documentation and knowledge base systems.

- **📐 TODO Architecture:** [`logseq/pages/TTA.dev/TODO Architecture.md`](logseq/pages/TTA.dev___TODO Architecture.md) - Complete system design
- **📊 Main Dashboard:** [`logseq/pages/TODO Management System.md`](logseq/pages/TODO Management System.md) - Active queries
- **📋 Templates:** [`logseq/pages/TODO Templates.md`](logseq/pages/TODO Templates.md) - Copy-paste patterns
- **🎓 Learning Paths:** [`logseq/pages/TTA.dev/Learning Paths.md`](logseq/pages/TTA.dev___Learning Paths.md) - Structured sequences
- **📈 Metrics:** [`logseq/pages/TTA.dev/TODO Metrics Dashboard.md`](logseq/pages/TTA.dev___TODO Metrics Dashboard.md) - Analytics
- **⚡ Quick Reference:** [`logseq/pages/TODO Architecture Quick Reference.md`](logseq/pages/TODO Architecture Quick Reference.md) - Fast lookup

**Package Dashboards:**

- [`TTA.dev/Packages/tta-dev-primitives/TODOs`](logseq/pages/TTA.dev___Packages___tta-dev-primitives___TODOs.md) - Core primitives ✅
- [`TTA.dev/Packages/tta-observability-integration/TODOs`](logseq/pages/TTA.dev___Packages___tta-observability-integration___TODOs.md) - Observability ✅
- [`TTA.dev/Packages/universal-agent-context/TODOs`](logseq/pages/TTA.dev___Packages___universal-agent-context___TODOs.md) - Agent context ✅

**Migration Documentation:**

- [`docs/TODO_ARCHITECTURE_APPLICATION_COMPLETE.md`](docs/TODO_ARCHITECTURE_APPLICATION_COMPLETE.md) - **28 active TODOs** migrated/created
- [`docs/TODO_LIFECYCLE_GUIDE.md`](docs/TODO_LIFECYCLE_GUIDE.md) - Completion, archival, and embedded TODO workflows ✅
- [`docs/TODO_LIFECYCLE_IMPLEMENTATION_SUMMARY.md`](docs/TODO_LIFECYCLE_IMPLEMENTATION_SUMMARY.md) - Implementation summary

**Daily Journal:** Add TODOs to `logseq/journals/YYYY_MM_DD.md`

**Tag Convention:**

- `#dev-todo` - Development work (building TTA.dev itself)
- `#learning-todo` - User education (tutorials, flashcards, exercises)
- `#template-todo` - Reusable patterns (for agents/users)
- `#ops-todo` - Infrastructure (deployment, monitoring)

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

**See:** [`logseq/ADVANCED_FEATURES.md`](logseq/ADVANCED_FEATURES.md) for complete Logseq guide.

### 🎯 Agent Context & Tooling

For GitHub Copilot users, comprehensive instructions are available in [`.github/copilot-instructions.md`](.github/copilot-instructions.md), including:

- Package manager requirements (uv)
- Python version and type hints (3.11+)
- Testing standards and examples
- Code style and formatting rules
- Security practices
- Documentation standards
- TTA.dev primitives patterns
- TODO management with Logseq
- Development workflow
- Copilot toolsets (VS Code)

Additionally, context-specific modular instructions are in `.github/instructions/` for tests, scripts, documentation, package source, and Logseq integration.

### ⚡ Before You Code: Primitive Usage Rules

**CRITICAL:** When working on TTA.dev, **ALWAYS use primitives** for workflow patterns. Refer to the `.clinerules` file for detailed guidance on primitive usage, anti-patterns, and code quality standards.

### Repository Structure

```text
TTA.dev/
├── platform/             # Infrastructure packages (7)
│   ├── primitives/       # ✅ Core workflow primitives
│   ├── observability/    # ✅ OpenTelemetry integration
│   ├── agent-context/    # ✅ Agent context management
│   ├── agent-coordination/  # Multi-agent orchestration
│   ├── integrations/     # Pre-built integrations
│   ├── documentation/    # Docs automation
│   └── kb-automation/    # Knowledge base maintenance
│
├── apps/                 # User-facing applications (2)
│   ├── observability-ui/ # Observability dashboard UI
│   └── vscode-extension/ # VS Code extension
│
├── docs/                 # Comprehensive documentation
│   ├── planning/         # Planning documents (moved from root)
│   └── ...
├── archive/
│   └── status-reports/   # Historical status files
├── scripts/              # Automation and validation scripts
└── tests/                # Integration tests
```

---

## 📚 Package-Specific Agent Instructions

Each package has detailed agent instructions. **Always read the package-specific AGENTS.md before working on that package:**

### ✅ Production Packages (Active in Workspace)

| Package | Status | AGENTS.md | Purpose |
|---------|--------|-----------|---------|
| **tta-dev-primitives** | ✅ Active | [`platform/primitives/AGENTS.md`](platform/primitives/AGENTS.md) | Core workflow primitives (Sequential, Parallel, Router, Retry, Fallback, Cache, etc.) |
| **tta-observability-integration** | ✅ Active | [`platform/observability/README.md`](platform/observability/README.md) | OpenTelemetry tracing, metrics, logging |
| **universal-agent-context** | ✅ Active | [`platform/agent-context/AGENTS.md`](platform/agent-context/AGENTS.md) | Agent context management and orchestration |

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
| `WorkflowPrimitive[T,U]` | Base class for all primitives | `from tta_dev_primitives import WorkflowPrimitive` | [base.py](platform/primitives/src/tta_dev_primitives/core/base.py) |
| `SequentialPrimitive` | Execute steps in sequence | `from tta_dev_primitives import SequentialPrimitive` | [examples/basic_sequential.py](platform/primitives/examples/basic_sequential.py) |
| `ParallelPrimitive` | Execute steps in parallel | `from tta_dev_primitives import ParallelPrimitive` | [examples/parallel_execution.py](platform/primitives/examples/parallel_execution.py) |
| `ConditionalPrimitive` | Conditional branching | `from tta_dev_primitives import ConditionalPrimitive` | [conditional.py](platform/primitives/src/tta_dev_primitives/core/conditional.py) |
| `RouterPrimitive` | Dynamic routing (LLM selection, etc.) | `from tta_dev_primitives import RouterPrimitive` | [examples/router_llm_selection.py](platform/primitives/examples/router_llm_selection.py) |

### Recovery Primitives

| Primitive | Purpose | Import Path | Example |
|-----------|---------|-------------|---------|
| `RetryPrimitive` | Retry with backoff strategies | `from tta_dev_primitives.recovery import RetryPrimitive` | [retry.py](platform/primitives/src/tta_dev_primitives/recovery/retry.py) |
| `FallbackPrimitive` | Graceful degradation | `from tta_dev_primitives.recovery import FallbackPrimitive` | [fallback.py](platform/primitives/src/tta_dev_primitives/recovery/fallback.py) |
| `TimeoutPrimitive` | Circuit breaker pattern | `from tta_dev_primitives.recovery import TimeoutPrimitive` | [timeout.py](platform/primitives/src/tta_dev_primitives/recovery/timeout.py) |
| `CompensationPrimitive` | Saga pattern for rollback | `from tta_dev_primitives.recovery import CompensationPrimitive` | [compensation.py](platform/primitives/src/tta_dev_primitives/recovery/compensation.py) |

### Performance Primitives

| Primitive | Purpose | Import Path | Example |
|-----------|---------|-------------|---------|
| `CachePrimitive` | LRU + TTL caching | `from tta_dev_primitives.performance import CachePrimitive` | [cache.py](platform/primitives/src/tta_dev_primitives/performance/cache.py) |

### Testing Primitives

| Primitive | Purpose | Import Path | Example |
|-----------|---------|-------------|---------|
| `MockPrimitive` | Testing and mocking | `from tta_dev_primitives.testing import MockPrimitive` | [mock_primitive.py](platform/primitives/src/tta_dev_primitives/testing/mock_primitive.py) |

### Adaptive/Self-Improving Primitives ⭐ NEW

**Primitives that learn from observability data and automatically improve their behavior.**

| Primitive | Purpose | Import Path | Example |
|-----------|---------|-------------|---------|
| `AdaptivePrimitive[T,U]` | Base class for self-improving primitives | `from tta_dev_primitives.adaptive import AdaptivePrimitive` | [base.py](platform/primitives/src/tta_dev_primitives/adaptive/base.py) |
| `AdaptiveRetryPrimitive` | Retry that learns optimal strategies | `from tta_dev_primitives.adaptive import AdaptiveRetryPrimitive` | [retry.py](platform/primitives/src/tta_dev_primitives/adaptive/retry.py) |
| `LogseqStrategyIntegration` | Persist learned strategies to KB | `from tta_dev_primitives.adaptive import LogseqStrategyIntegration` | [logseq_integration.py](platform/primitives/src/tta_dev_primitives/adaptive/logseq_integration.py) |

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

- [ADAPTIVE_PRIMITIVES_VERIFICATION_COMPLETE.md](ADAPTIVE_PRIMITIVES_VERIFICATION_COMPLETE.md) - Comprehensive verification report
- [ADAPTIVE_PRIMITIVES_AUDIT.md](ADAPTIVE_PRIMITIVES_AUDIT.md) - System audit and quality review
- [ADAPTIVE_PRIMITIVES_IMPROVEMENTS.md](ADAPTIVE_PRIMITIVES_IMPROVEMENTS.md) - Latest improvements summary

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

**More patterns:** See [`platform/primitives/examples/`](platform/primitives/examples/)

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

**Full example:** [`examples/e2b_iterative_code_refinement.py`](platform/primitives/examples/e2b_iterative_code_refinement.py)

**More examples:** [`platform/primitives/examples/`](platform/primitives/examples/)

---

## 🔍 Observability

All primitives have **built-in observability**:

- **Structured Logging**: Every primitive logs execution details
- **Distributed Tracing**: OpenTelemetry spans for each operation
- **Metrics**: Prometheus-compatible metrics (execution time, success rate, etc.)
- **Context Propagation**: `WorkflowContext` carries state and correlation IDs
- **🆕 TTA UI**: LangSmith-inspired dashboard for local development

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

3. **🆕 TTA Observability UI** (`tta-observability-ui/`)
   - **LangSmith-inspired** lightweight dashboard
   - **Zero-config** SQLite storage
   - **VS Code integration** (coming in Phase 3)
   - **Real-time updates** via WebSocket
   - **Primitive-aware** visualization

**Quick Setup:**

```python
from observability_integration import initialize_observability
from observability_integration.primitives import RouterPrimitive, CachePrimitive

# Initialize observability
success = initialize_observability(
    service_name="my-app",
    enable_prometheus=True,
    enable_tta_ui=True,  # ← NEW! Enable TTA UI
    tta_ui_endpoint="http://localhost:8765"
)

# Use enhanced primitives
workflow = (
    input_step >>
    RouterPrimitive(routes={"fast": llm1, "quality": llm2}) >>
    CachePrimitive(expensive_op, ttl_seconds=3600) >>
    output_step
)
```

**Start TTA UI:**

```bash
# Terminal 1: Start observability service
tta-observability-ui start

# Terminal 2: Run your application
python my_app.py

# Browser: View traces
open http://localhost:8765
```

**Benefits:**

- 30-40% cost reduction (via Cache + Router)
- Real-time metrics in Prometheus/Grafana
- Distributed tracing across workflows
- Automatic span creation and context propagation
- 🆕 **Simple local UI** (no Docker/Jaeger needed for dev!)

**See:** 
- Integration: [`docs/architecture/COMPONENT_INTEGRATION_ANALYSIS.md`](docs/architecture/COMPONENT_INTEGRATION_ANALYSIS.md#1-tta-observability-integration)
- TTA UI: [`apps/observability-ui/QUICKSTART.md`](apps/observability-ui/QUICKSTART.md)
- Design: [`docs/architecture/OBSERVABILITY_UI_DESIGN.md`](docs/architecture/OBSERVABILITY_UI_DESIGN.md)

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

**Testing guide:** [`platform/primitives/AGENTS.md#testing`](platform/primitives/AGENTS.md)

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

**Copilot Toolsets:** See [`.vscode/copilot-toolsets.jsonc`](.vscode/copilot-toolsets.jsonc)

Available toolsets (use with `@workspace @toolset-name`):
- `@tta-backend` - Python backend, primitives, and orchestration
- `@tta-frontend` - React, TypeScript, and UI development
- `@tta-devops` - Infrastructure, CI/CD, and automation
- `@tta-testing` - QA, validation, and test automation
- `@tta-observability` - Monitoring, tracing, and metrics
- `@tta-data-scientist` - Data analysis, ML, and research

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
| [`PHASE3_EXAMPLES_COMPLETE.md`](PHASE3_EXAMPLES_COMPLETE.md) | Phase 3 examples implementation guide |
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

1. **Start with examples:** [`platform/primitives/examples/`](platform/primitives/examples/)
2. **Review Phase 3 patterns:** See [`PHASE3_EXAMPLES_COMPLETE.md`](PHASE3_EXAMPLES_COMPLETE.md) for production patterns
3. **Use composition:** Chain primitives with `>>` and `|`
4. **Add observability:** Use `WorkflowContext` for all workflows
5. **Test with mocks:** Use `MockPrimitive` for unit tests
6. **Check toolsets:** Use `@tta-backend`, `@tta-testing`, or `@tta-observability` in Copilot for role-specific tools
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

## 🤝 Cline Integration (Super-Cline)

TTA.dev is integrated with Cline to provide an enhanced development experience. This "Super-Cline" setup includes:
-   **Cline Hooks**: Automated checks and environment setup (e.g., `uv` enforcement, `uv sync` on task start).
-   **VS Code Workspace Configuration**: Recommended extensions, settings, and tasks for TTA.dev development.
-   **TTA.dev Primitives as MCP Tools**: Direct access to TTA.dev's agentic primitives as callable Cline tools.

For a detailed guide, see [`CLINE_INTEGRATION_GUIDE.md`](CLINE_INTEGRATION_GUIDE.md).

## 📞 Getting Help

1. **Check package AGENTS.md** - Most specific guidance
2. **Review examples** - Working code in `examples/`
3. **Search documentation** - `docs/` directory
4. **Check Copilot toolsets** - `.vscode/copilot-toolsets.jsonc`
5. **Open an issue** - For bugs or feature requests

---

**Last Updated:** 2025-11-10
**Maintained by:** TTA.dev Team
**License:** See individual package licenses
