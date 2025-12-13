# TTA.dev/Best Practices/Agentic Testing

type:: Best Practices
category:: [[TTA.dev/Testing]]
audience:: AI Agents, Developers
created:: [[2025-11-03]]
related:: [[Whiteboard - Testing Architecture]], [[Whiteboard - Agentic Development Workflow]]

---

## 🎯 Purpose

**Current agentic testing best practices** for AI agents writing tests in TTA.dev.

This page provides:

- Testing strategies for AI agents
- Safety-first principles
- Mock usage patterns
- Coverage expectations
- KB integration for tests

**Vision:** Agents that write intelligent, safe, maintainable tests that serve as documentation and learning materials.

---

## 🧠 Core Testing Philosophy for AI Agents

### 1. Default to Safety

**Principle:** Tests should be safe to run by default on any environment.

```python
# ✅ GOOD: Safe by default (unit test)
def test_cache_primitive_creation():
    """Test CachePrimitive initialization.

    Safe for:
    - Local development (WSL, native Linux, macOS)
    - CI pipelines
    - Limited resource environments

    KB: [[TTA Primitives/CachePrimitive]]
    """
    cache = CachePrimitive(ttl=60, max_size=100)
    assert cache.ttl == 60
    assert cache.max_size == 100

# ❌ BAD: Unsafe by default (no marker)
async def test_prometheus_integration():
    """This starts services! Needs integration marker."""
    # Starts Prometheus on port 9090 - can crash WSL
    client = PrometheusClient("localhost:9090")
    await client.query("up")
```

**Fix:**

```python
# ✅ GOOD: Marked appropriately
@pytest.mark.integration
@pytest.mark.timeout(120)
async def test_prometheus_integration():
    """Test Prometheus metrics collection.

    Requirements:
    - Prometheus running on port 9090
    - Docker available
    - 200MB+ memory

    Local: RUN_INTEGRATION=true ./scripts/test_integration.sh
    CI: Runs in separate integration job

    KB: [[TTA.dev/Guides/Observability]]
    """
    client = PrometheusClient("localhost:9090")
    await client.query("up")
```

---

### 2. Test Pyramid Awareness

**Principle:** Know which layer of the test pyramid you're writing for.

```text
Test Pyramid for Agents
────────────────────────

           ┌────────┐
           │ Slow   │ ← Rarely write these
           │ Tests  │   (Performance, E2E)
           └────────┘
         ┌────────────┐
         │Integration │ ← Explicit opt-in
         │   Tests    │   (Service integration)
         └────────────┘
       ┌────────────────┐
       │  Unit Tests    │ ← DEFAULT: Write most here
       │  (Fast, Safe)  │   (Pure logic, mocked deps)
       └────────────────┘
     ┌──────────────────────┐
     │ Documentation Checks │ ← Always include
     │  (Static analysis)   │   (Docstrings, links)
     └──────────────────────┘
```

**Decision Tree:**

```text
Am I testing...?
        ↓
    ┌───────┴───────┐
    │               │
Pure logic    External resource?
    │               ↓
    ↓           ┌───┴───┐
Unit test      │       │
              Mock   Real
              it?    service?
               ↓       ↓
            Unit    Integration
            test    test
```

---

### 3. Comprehensive Documentation

**Principle:** Every test is documentation.

```python
# ✅ GOOD: Test as documentation
async def test_router_primitive_tier_selection():
    """Test RouterPrimitive selects correct model based on tier.

    **Scenario:** Complex query should route to quality tier

    **Given:**
    - Router configured with fast/balanced/quality tiers
    - Input contains complexity indicator

    **When:**
    - Router evaluates input

    **Then:**
    - Quality tier model is selected
    - Routing decision is traced

    **Example:**
    ```python
    router = RouterPrimitive(
        routes={"fast": gpt4_mini, "quality": gpt4},
        router_fn=complexity_router
    )
    ```

    **KB:** [[TTA Primitives/RouterPrimitive]]
    **Whiteboard:** [[Whiteboard - Workflow Composition Patterns]]
    """
    # Test implementation
```

**Docstring Template for Agents:**

```python
async def test_feature_name():
    """[One-line summary of what is tested]

    **Scenario:** [User story or use case]

    **Requirements:** [If integration test]
    - Docker running
    - Port X available
    - Service Y configured

    **Given:** [Test setup/preconditions]
    - Initial state
    - Configuration

    **When:** [Action being tested]
    - Method called
    - Input provided

    **Then:** [Expected outcome]
    - Result matches expectation
    - Side effects occurred

    **Local Usage:** [If special requirements]
    RUN_INTEGRATION=true ./scripts/test_integration.sh

    **KB:** [[Link to relevant KB page]]
    **Example:** [Link to example file]
    """
```

---

## 🛡️ Safety Patterns

### Pattern 1: Use Timeouts

```python
# ✅ GOOD: Explicit timeout
@pytest.mark.timeout(10)
async def test_api_call_with_retry():
    """Test API retry logic with timeout protection."""
    retry = RetryPrimitive(api_call, max_retries=3)
    result = await retry.execute(data, context)
    assert result

# ✅ ALSO GOOD: Marker-based timeout
@pytest.mark.integration
@pytest.mark.timeout(300)  # 5 minutes for integration
async def test_full_workflow():
    """Integration test with appropriate timeout."""
    ...
```

**Default Timeouts (from pyproject.toml):**

- Unit tests: 60 seconds
- Integration tests: 300 seconds
- Slow tests: 600 seconds

### Pattern 2: Resource Checks

```python
# ✅ GOOD: Check resources before using
@pytest.mark.integration
async def test_database_connection():
    """Test database primitive.

    Requirements:
    - PostgreSQL running on port 5432
    - Test database 'tta_test' exists
    """
    if not await check_postgres_available():
        pytest.skip("PostgreSQL not available")

    db = DatabasePrimitive("postgresql://localhost/tta_test")
    result = await db.execute(query, context)
    assert result
```

### Pattern 3: Explicit Integration Markers

```python
# ✅ GOOD: Clear markers
@pytest.mark.integration  # Requires RUN_INTEGRATION=true locally
@pytest.mark.timeout(180)
@pytest.mark.skipif(
    not os.getenv("CI"),
    reason="Integration test - use RUN_INTEGRATION=true locally"
)
async def test_opentelemetry_trace_export():
    """Test trace export to OTLP collector.

    CI: Runs in separate integration job
    Local: Requires explicit opt-in
    """
    ...
```

---

## 🎭 Mocking Strategies

### When to Mock

```text
Testing...?
        ↓
    ┌───────┴───────┐
    │               │
Internal      External
logic?        dependency?
    ↓               ↓
    │           ┌───┴───┐
    │          │       │
    │        Fast    Slow/
    │        API?    expensive?
    │          ↓       ↓
    │        Mock    Mock
    ↓        it      it
Test real
(unit test)
```

### MockPrimitive Usage

```python
# ✅ GOOD: Mock external LLM in unit test
from tta_dev_primitives.testing import MockPrimitive

async def test_workflow_with_llm():
    """Test workflow composition without calling real LLM.

    **Mocked:** LLM call (expensive, external)
    **Tested:** Workflow composition logic

    KB: [[TTA Primitives/MockPrimitive]]
    """
    # Mock the expensive LLM call
    mock_llm = MockPrimitive(
        return_value={"output": "Generated text"},
        execution_time=0.1  # Simulate 100ms call
    )

    # Test the workflow composition
    workflow = input_processor >> mock_llm >> output_formatter
    result = await workflow.execute(input_data, context)

    # Verify mock was called correctly
    assert mock_llm.call_count == 1
    assert result["formatted"]
```

### Pytest Mock for Fine-Grained Control

```python
# ✅ GOOD: Mock specific methods
from unittest.mock import AsyncMock, patch

@patch('tta_dev_primitives.recovery.retry.asyncio.sleep')
async def test_retry_backoff_timing(mock_sleep):
    """Test retry backoff without actually waiting.

    **Mocked:** asyncio.sleep (avoid waiting in tests)
    **Tested:** Backoff calculation logic
    """
    mock_sleep.return_value = None  # Don't actually sleep

    retry = RetryPrimitive(
        failing_primitive,
        max_retries=3,
        backoff_strategy="exponential"
    )

    with pytest.raises(Exception):
        await retry.execute(data, context)

    # Verify backoff delays: 1s, 2s, 4s
    assert mock_sleep.call_count == 3
    assert mock_sleep.call_args_list[0][0][0] == 1.0
    assert mock_sleep.call_args_list[1][0][0] == 2.0
    assert mock_sleep.call_args_list[2][0][0] == 4.0
```

---

## 📊 Coverage Expectations

### 100% Coverage Mandate

**For AI Agents:** New code MUST have 100% test coverage.

```bash
# Run tests with coverage
uv run pytest --cov=packages/tta-dev-primitives/src \
              --cov-report=html \
              --cov-report=term-missing

# Check coverage
open htmlcov/index.html
```

### Coverage by Code Type

```python
# ✅ COVERED: Public API (100% required)
class CachePrimitive(InstrumentedPrimitive[T, T]):
    """Public primitive - must have 100% coverage."""

    def __init__(self, ttl: int, max_size: int = 1000):
        # Test: test_cache_initialization()
        ...

    async def _execute_impl(self, data: T, context: WorkflowContext) -> T:
        # Test: test_cache_hit(), test_cache_miss()
        ...

    def _evict_lru(self):
        # Test: test_cache_eviction_lru()
        ...

    def _check_ttl(self, key: str) -> bool:
        # Test: test_cache_ttl_expiration()
        ...

# ✅ COVERED: Edge cases
def test_cache_edge_cases():
    """Test edge cases that might not be obvious."""
    # Empty cache
    # Max size = 0
    # TTL = 0
    # Concurrent access
```

### What to Test

1. **Happy path** - Normal usage
2. **Edge cases** - Boundary conditions
3. **Error cases** - Exception handling
4. **Integration points** - Component interactions (in integration tests)
5. **Performance** - Resource usage (in slow tests)

---

## 🎓 KB Integration for Tests

### Link Tests to KB Pages

```python
class TestCachePrimitive:
    """Test suite for CachePrimitive.

    **KB:** [[TTA Primitives/CachePrimitive]]
    **Implementation:** packages/tta-dev-primitives/src/.../cache.py
    **Examples:** examples/cache_usage.py
    """

    async def test_lru_eviction(self):
        """Test LRU eviction policy.

        **Scenario:** Cache exceeds max_size, oldest entry evicted
        **KB:** [[TTA Primitives/CachePrimitive#LRU Eviction]]
        """
        ...
```

### Create Flashcards from Tests

**In KB page (TTA Primitives/CachePrimitive.md):**

```markdown
## Testing Flashcards

### How do you test CachePrimitive LRU eviction? #card

```python
cache = CachePrimitive(max_size=2)

# Fill cache
await cache.execute({"key": "a"}, context)  # Entry 1
await cache.execute({"key": "b"}, context)  # Entry 2

# Trigger eviction
await cache.execute({"key": "c"}, context)  # Entry 3

# Verify 'a' was evicted (LRU)
assert "a" not in cache._cache
```

**Test:** `test_cache_lru_eviction()`

### What timeout should CachePrimitive tests use? #card

- **Unit tests:** 60s (default from pyproject.toml)
- **Integration tests:** 300s if testing with Prometheus
- **Mock external calls** to keep tests fast

### When should CachePrimitive tests use mocks? #card

**Always mock** in unit tests:
- LLM calls being cached
- API requests being cached
- Database queries being cached

**Use real services** only in integration tests with `@pytest.mark.integration`.
```

---

## 🚀 CI/CD Integration

### Test Job Strategy

```yaml
# .github/workflows/tests-split.yml

jobs:
  quick-checks:
    # Runs first, fails fast
    - Ruff format
    - Ruff lint
    - Pyright type check

  docs-validation:
    # Parallel with quick-checks
    - Markdown link validation
    - Code block checks
    - Frontmatter validation

  unit-tests:
    # Depends on: quick-checks, docs-validation
    - Fast unit tests (< 60s each)
    - High coverage required
    - No external dependencies

  integration-tests:
    # Depends on: unit-tests
    - Service integration (ports, Docker)
    - Longer timeouts (300s)
    - Separate runner for resource isolation
```

### Agent Responsibilities

When writing tests, agents should:

1. **Default to unit tests** - Fast, safe, run in CI
2. **Mark integration explicitly** - `@pytest.mark.integration`
3. **Document requirements** - What services/ports needed
4. **Set timeouts** - Prevent hanging in CI
5. **Use mocks** - Keep unit tests fast
6. **Verify locally** - Run `./scripts/test_fast.sh` before commit

---

## 📋 Testing Checklist for Agents

### Before Writing Tests

- [ ] Understand what you're testing (unit vs integration)
- [ ] Check if similar tests exist (avoid duplication)
- [ ] Plan mocking strategy (what to mock, what to test for real)
- [ ] Review related KB pages for context

### While Writing Tests

- [ ] Write comprehensive docstring (scenario, requirements, KB links)
- [ ] Use appropriate markers (`@pytest.mark.integration`, etc.)
- [ ] Set explicit timeouts for long-running tests
- [ ] Mock external dependencies in unit tests
- [ ] Use descriptive test names (`test_cache_evicts_lru_entry`)
- [ ] Add assertions with clear failure messages

### After Writing Tests

- [ ] Run tests locally (`./scripts/test_fast.sh`)
- [ ] Check coverage (`pytest --cov`)
- [ ] Verify tests pass in CI (green checkmark)
- [ ] Create flashcards in KB from test examples
- [ ] Link tests to KB pages (bi-directional)
- [ ] Update TODOs in journal (mark test-related TODO as DONE)

---

## 🎯 Test Quality Metrics

### For AI Agents to Track

```python
# Metrics agents should be aware of:

test_quality_score = (
    coverage_percentage * 0.4 +        # 40% weight: 100% = good
    (1 - integration_ratio) * 0.3 +    # 30% weight: Fewer integration tests = better
    docstring_completeness * 0.2 +     # 20% weight: All tests documented
    kb_linkage * 0.1                   # 10% weight: Tests linked to KB
)

# Target: > 0.9 (excellent)
# Acceptable: > 0.7
# Needs improvement: < 0.7
```

### Self-Evaluation Questions

1. **Coverage:** Is every line of my code tested?
2. **Safety:** Can these tests run safely on WSL by default?
3. **Speed:** Are unit tests < 1s each, integration < 30s?
4. **Documentation:** Does every test have a clear docstring?
5. **KB Integration:** Are tests linked to relevant KB pages?
6. **Mocking:** Are external dependencies mocked in unit tests?
7. **Markers:** Are integration/slow tests marked correctly?

---

## 🔗 Related Pages

- [[Whiteboard - Testing Architecture]] - Visual testing patterns
- [[Whiteboard - Agentic Development Workflow]] - Complete workflow
- [[TTA.dev/Stage Guides/Testing Stage]] - Testing lifecycle
- [[TTA.dev/Common Mistakes/Testing Antipatterns]] - What to avoid
- [[TODO Management System]] - Track testing TODOs

---

## 💡 Key Principles Summary

1. **Safety First** - Default to safe (unit) tests
2. **Document Everything** - Tests are documentation
3. **100% Coverage** - No excuses for new code
4. **Mock Liberally** - Keep unit tests fast and isolated
5. **Mark Explicitly** - Integration tests need markers
6. **Link to KB** - Bi-directional documentation
7. **Self-Review** - Use the checklist before marking DONE

---

## 📚 Example Test Suite (Reference)

```python
"""Test suite for CachePrimitive.

**KB:** [[TTA Primitives/CachePrimitive]]
**Implementation:** packages/tta-dev-primitives/src/tta_dev_primitives/performance/cache.py
**Coverage Target:** 100%
"""

import pytest
from tta_dev_primitives.performance import CachePrimitive
from tta_dev_primitives.testing import MockPrimitive
from tta_dev_primitives import WorkflowContext


class TestCachePrimitiveUnit:
    """Unit tests for CachePrimitive (fast, safe, default)."""

    async def test_initialization(self):
        """Test CachePrimitive initialization with parameters.

        KB: [[TTA Primitives/CachePrimitive#Initialization]]
        """
        cache = CachePrimitive(ttl=60, max_size=100)
        assert cache.ttl == 60
        assert cache.max_size == 100

    async def test_cache_hit(self):
        """Test cache returns cached value on hit.

        **Given:** Value cached for key "test"
        **When:** Same key requested again
        **Then:** Cached value returned, primitive not executed

        KB: [[TTA Primitives/CachePrimitive#Cache Hit]]
        """
        mock_primitive = MockPrimitive(return_value={"result": "value"})
        cache = CachePrimitive(mock_primitive, ttl=60)

        context = WorkflowContext()

        # First call - cache miss
        result1 = await cache.execute({"key": "test"}, context)
        assert mock_primitive.call_count == 1

        # Second call - cache hit
        result2 = await cache.execute({"key": "test"}, context)
        assert mock_primitive.call_count == 1  # Not called again
        assert result1 == result2

    @pytest.mark.timeout(10)
    async def test_lru_eviction(self):
        """Test LRU eviction when cache exceeds max_size.

        **Scenario:** Cache with max_size=2, add 3 items
        **Expected:** Oldest (LRU) item evicted

        KB: [[TTA Primitives/CachePrimitive#LRU Eviction]]
        """
        cache = CachePrimitive(MockPrimitive(), max_size=2)
        # ... test implementation


@pytest.mark.integration
class TestCachePrimitiveIntegration:
    """Integration tests for CachePrimitive (explicit opt-in).

    **Requirements:**
    - Prometheus running (for metrics)
    - Port 9090 available

    **Local:** RUN_INTEGRATION=true ./scripts/test_integration.sh
    """

    @pytest.mark.timeout(120)
    async def test_cache_with_prometheus_metrics(self):
        """Test cache metrics exported to Prometheus.

        **Integration Point:** Prometheus metrics collection

        KB: [[TTA.dev/Guides/Observability]]
        """
        # ... integration test implementation
```

---

**Last Updated:** November 3, 2025
**Status:** Active - Best Practices
**For:** AI Agents writing tests for TTA.dev

- [[Project Hub]]

---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev___best practices___agentic testing]]
