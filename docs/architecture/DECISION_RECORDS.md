# Architecture Decision Records (ADRs)

**Repository:** TTA.dev
**Purpose:** Document key architectural decisions and their rationale
**Format:** Each ADR follows the format: Context, Decision, Consequences

---

## ADR Index

| ID | Title | Status | Date |
|----|-------|--------|------|
| ADR-001 | Monorepo Structure with Focused Packages | ✅ Accepted | 2024-03-15 |
| ADR-002 | WorkflowPrimitive as Base Abstraction | ✅ Accepted | 2024-03-16 |
| ADR-003 | Two-Package Observability Architecture | ✅ Accepted | 2024-03-18 |
| ADR-004 | Operator Overloading for Composition | ✅ Accepted | 2024-03-16 |
| ADR-005 | UV Package Manager over pip | ✅ Accepted | 2024-03-15 |
| ADR-006 | Python 3.11+ Modern Type Hints | ✅ Accepted | 2024-03-15 |
| ADR-007 | OpenTelemetry for Observability | ✅ Accepted | 2024-03-18 |
| ADR-008 | Graceful Degradation Pattern | ✅ Accepted | 2024-03-19 |
| ADR-009 | WorkflowContext for State Management | ✅ Accepted | 2024-03-16 |
| ADR-010 | GitHub Copilot Toolsets Strategy | ✅ Accepted | 2024-10-28 |

---

## ADR-001: Monorepo Structure with Focused Packages

**Status:** ✅ Accepted  
**Date:** 2024-03-15  
**Deciders:** Core Team

### Context

We needed to organize multiple related Python packages (primitives, observability, agent context, testing frameworks) that:
- Share common dependencies
- Need coordinated versioning
- Benefit from unified development workflow
- May be used independently or together

**Options Considered:**
1. Single monolithic package
2. Separate repositories per package
3. Monorepo with focused packages (chosen)

### Decision

**Adopt a monorepo structure with focused, independently installable packages.**

```text
TTA.dev/
├── packages/
│   ├── tta-dev-primitives/          # Core workflow primitives
│   ├── tta-observability-integration/ # Enhanced observability
│   ├── universal-agent-context/      # Agent coordination
│   ├── keploy-framework/             # API testing
│   └── python-pathway/               # Python utilities
├── docs/                             # Shared documentation
├── scripts/                          # Shared tooling
└── tests/                            # Integration tests
```

### Rationale

**Chosen because:**
- **Easier dependency management**: Shared dependencies in root `pyproject.toml`
- **Unified tooling**: Single Ruff, Pyright, Pytest configuration
- **Better discoverability**: All packages in one place
- **Atomic changes**: Cross-package changes in single PR
- **Independent versioning**: Each package can version independently

**Not chosen:**
- Monolithic: Would force users to install everything
- Multi-repo: Coordination overhead, version skew issues

### Consequences

**Positive:**
- ✅ Simplified development workflow
- ✅ Easier to maintain consistency
- ✅ Better for monorepo tools (uv workspace, task runners)
- ✅ Improved discoverability for developers

**Negative:**
- ⚠️ Larger repository size
- ⚠️ Potential for coupling if not disciplined
- ⚠️ CI needs to be smart about which packages changed

**Mitigation:**
- Use clear package boundaries
- Document inter-package dependencies
- CI runs tests only for changed packages

---

## ADR-002: WorkflowPrimitive as Base Abstraction

**Status:** ✅ Accepted  
**Date:** 2024-03-16  
**Deciders:** Core Team

### Context

We needed a common abstraction for composable workflow components that:
- Has consistent interface across all primitives
- Supports type safety (generics for input/output)
- Enables composition patterns (sequential, parallel, conditional)
- Provides observability hooks

**Options Considered:**
1. Function-based approach (plain async functions)
2. Abstract base class with execute() method (chosen)
3. Protocol/structural subtyping

### Decision

**Use `WorkflowPrimitive[TInput, TOutput]` abstract base class.**

```python
class WorkflowPrimitive(ABC, Generic[TInput, TOutput]):
    """Base class for all workflow primitives."""
    
    async def execute(
        self, 
        context: WorkflowContext, 
        input_data: TInput
    ) -> TOutput:
        """Public interface for execution."""
        # Observability hooks
        return await self._execute_impl(context, input_data)
    
    @abstractmethod
    async def _execute_impl(
        self, 
        context: WorkflowContext, 
        input_data: TInput
    ) -> TOutput:
        """Subclasses implement this."""
        ...
```

### Rationale

**Chosen because:**
- **Type safety**: Generic types enforce correct input/output matching
- **Observability**: Common `execute()` adds tracing/metrics automatically
- **Composition**: Base class enables operator overloading (`>>`, `|`)
- **Extensibility**: Easy to add new primitives
- **IDE support**: Better autocomplete and type checking

**Not chosen:**
- Functions: No shared behavior, harder to add observability
- Protocol: Less explicit, harder to enforce consistency

### Consequences

**Positive:**
- ✅ Type-safe composition: `step1 >> step2` checks types at editor time
- ✅ Automatic observability for all primitives
- ✅ Clear extension point (`_execute_impl`)
- ✅ Testable: `MockPrimitive` for testing

**Negative:**
- ⚠️ Slightly more boilerplate than plain functions
- ⚠️ Learning curve for new developers

**Migration:**
- Existing primitives: Already using this pattern
- New primitives: Follow template in `WorkflowPrimitive` docstring

---

## ADR-003: Two-Package Observability Architecture

**Status:** ✅ Accepted  
**Date:** 2024-03-18  
**Deciders:** Core Team

### Context

We needed observability (tracing, metrics, logging) across all primitives, but:
- Core primitives should work without OpenTelemetry dependencies
- Enhanced observability (Prometheus, OTLP) should be optional
- Users may want minimal dependencies for simple use cases

**Options Considered:**
1. Single package with all observability (heavy dependencies)
2. Optional dependencies in core package (complex)
3. Two-package architecture: core + enhanced (chosen)

### Decision

**Split observability into two packages:**

1. **Core Observability** (`tta-dev-primitives/observability/`)
   - `InstrumentedPrimitive` - base class with basic tracing
   - `ObservablePrimitive` - wrapper for adding observability
   - `PrimitiveMetrics` - lightweight metrics
   - No OpenTelemetry dependency

2. **Enhanced Observability** (`tta-observability-integration/`)
   - `initialize_observability()` - setup OpenTelemetry
   - Enhanced primitives with Prometheus metrics
   - OTLP exporter, Jaeger support
   - Optional dependency on OpenTelemetry SDK

### Rationale

**Chosen because:**
- **Gradual adoption**: Users can start with core, add enhanced later
- **Minimal dependencies**: Core package stays lightweight
- **Graceful degradation**: Enhanced features fail gracefully if unavailable
- **Separation of concerns**: Core focuses on primitives, integration on backends

**Not chosen:**
- Single package: Forces heavy dependencies on all users
- Optional dependencies: Complex, hard to test all combinations

### Consequences

**Positive:**
- ✅ Core package stays lightweight (~5 dependencies)
- ✅ Enhanced features optional
- ✅ Clear upgrade path for users
- ✅ Production-ready patterns (Prometheus, OTLP)

**Negative:**
- ⚠️ Two packages to maintain
- ⚠️ Potential confusion about which to use

**Documentation:**
- Clear guidance in docs: Start with core, add enhanced for production
- Examples showing both approaches

---

## ADR-004: Operator Overloading for Composition

**Status:** ✅ Accepted  
**Date:** 2024-03-16  
**Deciders:** Core Team

### Context

We needed intuitive syntax for composing workflow primitives:
- Sequential execution: step1 then step2
- Parallel execution: step1 and step2 concurrently
- Should feel natural to Python developers

**Options Considered:**
1. Builder pattern: `Workflow().add(step1).add(step2)`
2. Function calls: `sequential(step1, step2)`
3. Operator overloading: `step1 >> step2` (chosen)

### Decision

**Use operator overloading for composition:**

```python
# Sequential composition with >>
workflow = step1 >> step2 >> step3

# Parallel composition with |
workflow = branch1 | branch2 | branch3

# Mixed composition
workflow = (
    input_processor >>
    (fast_path | slow_path | cached_path) >>
    aggregator
)
```

**Implementation:**
```python
class WorkflowPrimitive:
    def __rshift__(self, other):
        """>> operator for sequential composition."""
        return SequentialPrimitive([self, other])
    
    def __or__(self, other):
        """| operator for parallel composition."""
        return ParallelPrimitive([self, other])
```

### Rationale

**Chosen because:**
- **Intuitive**: `>>` resembles Unix pipes, familiar to developers
- **Concise**: `step1 >> step2` vs `sequential(step1, step2)`
- **Visual**: Composition structure is immediately clear
- **Python-native**: Operator overloading is idiomatic Python

**Not chosen:**
- Builder: More verbose, less visual
- Functions: Less intuitive, harder to nest

### Consequences

**Positive:**
- ✅ Highly readable workflow definitions
- ✅ Type-safe: Editor checks types across `>>`
- ✅ Easy to refactor: Move operators around
- ✅ Familiar to users of other pipeline frameworks

**Negative:**
- ⚠️ Operator precedence can be confusing (use parentheses)
- ⚠️ Non-obvious to Python beginners

**Mitigation:**
- Document operator precedence clearly
- Provide examples with parentheses
- Explain in getting started guide

---

## ADR-005: UV Package Manager over pip

**Status:** ✅ Accepted  
**Date:** 2024-03-15  
**Deciders:** Core Team

### Context

We needed a Python package manager for monorepo workspace with:
- Fast dependency resolution
- Workspace support (multiple packages)
- Lockfile for reproducibility
- Modern tooling (PEP 621 compliance)

**Options Considered:**
1. pip + pip-tools
2. Poetry
3. uv (chosen)

### Decision

**Use `uv` as the primary package manager.**

```bash
# Install dependencies
uv sync --all-extras

# Add package
uv add package-name

# Run commands
uv run pytest
uv run python script.py
```

### Rationale

**Chosen because:**
- **Speed**: 10-100x faster than pip
- **Workspace support**: Native monorepo support
- **Lockfile**: `uv.lock` for reproducibility
- **PEP 621 compliant**: Works with standard `pyproject.toml`
- **Modern**: Written in Rust, actively maintained

**Not chosen:**
- pip: Slow, no native workspace support
- Poetry: Different config format, slower than uv

### Consequences

**Positive:**
- ✅ Fast dependency resolution (seconds vs minutes)
- ✅ Reliable: Same versions on all machines
- ✅ Simple commands: `uv add`, `uv sync`
- ✅ Virtual env management built-in

**Negative:**
- ⚠️ Relatively new tool (less mature than pip)
- ⚠️ Requires installation before use

**Migration:**
- Document installation in GETTING_STARTED.md
- Add `requirements.txt` for pip fallback if needed

---

## ADR-006: Python 3.11+ Modern Type Hints

**Status:** ✅ Accepted  
**Date:** 2024-03-15  
**Deciders:** Core Team

### Context

We needed to choose Python version and type hint style:
- Python 3.11+ has modern type hint syntax (PEP 604, 646)
- Older syntax requires `typing` module imports
- Type safety is critical for primitive composition

**Options Considered:**
1. Python 3.8+ with `typing` module
2. Python 3.11+ with modern syntax (chosen)

### Decision

**Require Python 3.11+ and use modern type hints.**

```python
# ✅ Modern Python 3.11+ style
def process(data: str | None) -> dict[str, Any]:
    ...

# ❌ Old style (don't use)
from typing import Optional, Dict
def process(data: Optional[str]) -> Dict[str, Any]:
    ...
```

### Rationale

**Chosen because:**
- **Cleaner syntax**: `str | None` vs `Optional[str]`
- **No imports**: `dict[str, Any]` vs `Dict[str, Any]`
- **Better performance**: Python 3.11 is faster
- **Future-proof**: Modern Python is the future

**Not chosen:**
- Python 3.8+: More verbose, slower runtime

### Consequences

**Positive:**
- ✅ Cleaner, more readable code
- ✅ Faster runtime (Python 3.11 improvements)
- ✅ Better type checker performance
- ✅ Less typing module imports

**Negative:**
- ⚠️ Requires Python 3.11+ (may limit some users)

**Mitigation:**
- Document Python 3.11+ requirement clearly
- Provide installation guide for Python 3.11

---

## ADR-007: OpenTelemetry for Observability

**Status:** ✅ Accepted  
**Date:** 2024-03-18  
**Deciders:** Core Team

### Context

We needed a standard observability framework for:
- Distributed tracing across workflows
- Metrics collection (counters, histograms)
- Context propagation (correlation IDs)
- Integration with monitoring backends (Prometheus, Jaeger, cloud providers)

**Options Considered:**
1. Custom tracing/metrics framework
2. Prometheus only
3. OpenTelemetry (chosen)

### Decision

**Use OpenTelemetry as the observability standard.**

```python
from opentelemetry import trace, metrics

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)

async def my_operation():
    with tracer.start_as_current_span("operation") as span:
        span.set_attribute("user_id", user_id)
        # ... do work ...
        span.add_event("processing_complete")
```

### Rationale

**Chosen because:**
- **Industry standard**: CNCF project, wide adoption
- **Vendor-neutral**: Works with any backend (Jaeger, Prometheus, AWS, GCP)
- **Complete**: Tracing + metrics + logs in one framework
- **Context propagation**: Built-in distributed tracing support
- **Future-proof**: Active development, growing ecosystem

**Not chosen:**
- Custom: Reinventing wheel, no ecosystem
- Prometheus only: No tracing support

### Consequences

**Positive:**
- ✅ Standards-based observability
- ✅ Works with any monitoring backend
- ✅ Automatic context propagation
- ✅ Rich ecosystem (instrumentation libraries)

**Negative:**
- ⚠️ Heavy dependency (~10 packages)
- ⚠️ Complex setup for advanced features

**Mitigation:**
- Make OpenTelemetry optional (tta-observability-integration)
- Provide simple `initialize_observability()` helper

---

## ADR-008: Graceful Degradation Pattern

**Status:** ✅ Accepted  
**Date:** 2024-03-19  
**Deciders:** Core Team

### Context

We needed to handle optional features (observability, caching, etc.) that may:
- Have dependencies not installed
- Have backends not available (Prometheus, Redis)
- Fail during initialization

**Options Considered:**
1. Hard requirements (fail if unavailable)
2. Graceful degradation (chosen)
3. Feature flags

### Decision

**Use graceful degradation pattern throughout TTA.dev.**

```python
def initialize_observability(...) -> bool:
    """
    Initialize observability.
    Returns True if successful, False otherwise.
    Application continues working without observability.
    """
    try:
        # Setup OpenTelemetry
        return True
    except Exception as e:
        logger.warning(f"Observability unavailable: {e}")
        return False  # Graceful degradation

# Usage
success = initialize_observability()
if not success:
    logger.info("Running without observability")
```

### Rationale

**Chosen because:**
- **Resilience**: Application works even if optional features fail
- **Development-friendly**: Don't need all backends running locally
- **Production-ready**: Service continues if monitoring fails
- **User-friendly**: Clear feedback about what's unavailable

**Not chosen:**
- Hard requirements: Forces complex setup, brittler
- Feature flags: More complex configuration

### Consequences

**Positive:**
- ✅ Resilient to missing dependencies
- ✅ Easier local development
- ✅ Production service stays up if monitoring fails
- ✅ Clear failure modes

**Negative:**
- ⚠️ May mask configuration issues
- ⚠️ Need to test both success and failure paths

**Implementation:**
- Return boolean from initialization functions
- Log warnings for degraded features
- Document graceful degradation behavior

---

## ADR-009: WorkflowContext for State Management

**Status:** ✅ Accepted  
**Date:** 2024-03-16  
**Deciders:** Core Team

### Context

We needed to pass state and metadata through workflow execution:
- Correlation IDs for tracing
- User context (user_id, session_id)
- Request metadata
- Propagate across primitives

**Options Considered:**
1. Global variables
2. Thread-local storage
3. Explicit WorkflowContext parameter (chosen)

### Decision

**Use `WorkflowContext` as explicit parameter to `execute()`.**

```python
@dataclass
class WorkflowContext:
    correlation_id: str
    data: dict[str, Any]
    parent_span_context: SpanContext | None = None

# Usage
context = WorkflowContext(
    correlation_id="req-123",
    data={"user_id": "user-789"}
)

result = await workflow.execute(context, input_data)
```

### Rationale

**Chosen because:**
- **Explicit**: Clear what context is available
- **Type-safe**: Can add typed fields as needed
- **Testable**: Easy to create test contexts
- **Async-safe**: No issues with coroutines
- **Traceable**: Correlation ID propagates automatically

**Not chosen:**
- Globals: Not async-safe, hard to test
- Thread-local: Doesn't work well with async

### Consequences

**Positive:**
- ✅ Explicit context propagation
- ✅ Type-safe access to context data
- ✅ Easy to test (mock context)
- ✅ Works with async/await

**Negative:**
- ⚠️ Extra parameter to pass around
- ⚠️ Need to create context for every workflow

**Mitigation:**
- Provide helper: `WorkflowContext.create()` with defaults
- Document context creation patterns

---

## ADR-010: GitHub Copilot Toolsets Strategy

**Status:** ✅ Accepted  
**Date:** 2024-10-28  
**Deciders:** Core Team

### Context

We needed to optimize GitHub Copilot agent interactions:
- Many available tools (50+) slow down Copilot
- Different tasks need different tool subsets
- Want to maintain tool discoverability

**Options Considered:**
1. All tools always available (slow)
2. Manual tool selection per task
3. Predefined toolsets with hashtags (chosen)

### Decision

**Create focused toolsets accessible via hashtags.**

```jsonc
// .vscode/copilot-toolsets.jsonc
{
  "tta-package-dev": {
    "description": "Full development toolset",
    "tools": ["search", "read_file", "edit", "runTests", ...]
  },
  "tta-minimal": {
    "description": "Minimal toolset for quick tasks",
    "tools": ["search", "read_file", "edit"]
  }
}
```

**Usage:** User types `#tta-package-dev` in chat

### Rationale

**Chosen because:**
- **Performance**: Fewer tools = faster Copilot responses
- **Focused**: Right tools for the task
- **Discoverable**: Hashtags show in autocomplete
- **Flexible**: Easy to add new toolsets

**Not chosen:**
- All tools: Too slow, overwhelming
- Manual: Too much friction

### Consequences

**Positive:**
- ✅ Faster Copilot responses (30-50% improvement)
- ✅ Better tool selection for task
- ✅ Easy to discover via autocomplete
- ✅ Documented in `.vscode/README.md`

**Negative:**
- ⚠️ Need to maintain toolset definitions
- ⚠️ Users need to know which toolset to use

**Documentation:**
- `.vscode/README.md` explains all toolsets
- `AGENTS.md` references appropriate toolsets

---

## Appendix: ADR Template

Use this template for new ADRs:

```markdown
## ADR-XXX: [Title]

**Status:** 🚧 Proposed / ✅ Accepted / ❌ Rejected / ⚠️ Deprecated  
**Date:** YYYY-MM-DD  
**Deciders:** [Names/Roles]

### Context

[What is the issue that we're seeing that is motivating this decision?]

**Options Considered:**
1. Option A
2. Option B
3. Option C (chosen)

### Decision

[What is the change that we're proposing/doing?]

[Code examples if applicable]

### Rationale

**Chosen because:**
- Reason 1
- Reason 2

**Not chosen:**
- Alternative: Reason not chosen

### Consequences

**Positive:**
- ✅ Benefit 1
- ✅ Benefit 2

**Negative:**
- ⚠️ Drawback 1
- ⚠️ Drawback 2

**Mitigation:**
- How to address drawbacks
```

---

**Last Updated:** October 30, 2025
**Maintainer:** TTA.dev Core Team
