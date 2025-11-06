# Testing Antipatterns

Tags: #common-mistakes, #testing, #stage-testing, #tta-dev

## Overview

Common mistakes to avoid when testing TTA.dev primitives and workflows.

## Antipattern 1: Missing @pytest.mark.asyncio

**Problem:** Async tests without asyncio marker don't actually await

```python
# ❌ BAD - Test appears to pass but doesn't await
async def test_my_primitive():
    result = await primitive.execute()
    assert result is not None  # Never reached!
```

**Solution:**

```python
# ✅ GOOD - Properly marked async test
import pytest

@pytest.mark.asyncio
async def test_my_primitive():
    result = await primitive.execute()
    assert result is not None
```

**Impact:** HIGH - False positives, bugs slip to production

---

## Antipattern 2: Using time.sleep() in Async Code

**Problem:** Blocks event loop, prevents concurrent execution

```python
# ❌ BAD - Blocks entire event loop
import time

@pytest.mark.asyncio
async def test_with_delay():
    time.sleep(1)  # Blocks everything!
    result = await primitive.execute()
```

**Solution:**

```python
# ✅ GOOD - Non-blocking sleep
import asyncio

@pytest.mark.asyncio
async def test_with_delay():
    await asyncio.sleep(1)  # Allows other tasks to run
    result = await primitive.execute()
```

**Impact:** MEDIUM - Tests run slowly, defeats async benefits

---

## Antipattern 3: Testing Implementation Details

**Problem:** Tests break when refactoring internal implementation

```python
# ❌ BAD - Testing private implementation
def test_primitive_internals():
    primitive = MyPrimitive()
    assert primitive._cache_size == 100
    assert primitive._internal_state == "initialized"
```

**Solution:**

```python
# ✅ GOOD - Test public API only
@pytest.mark.asyncio
async def test_primitive_behavior():
    primitive = MyPrimitive()
    result = await primitive.execute(input_data, context)
    assert result["output"] == "expected"
```

**Impact:** MEDIUM - Brittle tests, refactoring becomes painful

---

## Antipattern 4: No Error Case Testing

**Problem:** Only testing happy path means bugs in error handling

```python
# ❌ BAD - Only tests success
@pytest.mark.asyncio
async def test_primitive():
    result = await primitive.execute(good_input, context)
    assert result is not None
```

**Solution:**

```python
# ✅ GOOD - Tests both success and failure
@pytest.mark.asyncio
async def test_primitive_success():
    result = await primitive.execute(good_input, context)
    assert result is not None

@pytest.mark.asyncio
async def test_primitive_handles_invalid_input():
    with pytest.raises(ValueError):
        await primitive.execute(bad_input, context)

@pytest.mark.asyncio
async def test_primitive_handles_timeout():
    with pytest.raises(TimeoutError):
        await primitive.execute(slow_input, context)
```

**Impact:** HIGH - Production failures from unhandled errors

---

## Antipattern 5: Not Mocking External Services

**Problem:** Tests depend on external APIs, flaky and slow

```python
# ❌ BAD - Calls real OpenAI API in tests
@pytest.mark.asyncio
async def test_llm_workflow():
    result = await llm.execute({"prompt": "test"}, context)
    # Depends on network, costs money, slow!
```

**Solution:**

```python
# ✅ GOOD - Mock external services
from tta_dev_primitives.testing import MockPrimitive

@pytest.mark.asyncio
async def test_llm_workflow():
    mock_llm = MockPrimitive(return_value={"output": "mocked"})
    workflow = preprocessor >> mock_llm >> postprocessor
    result = await workflow.execute({"prompt": "test"}, context)
    assert mock_llm.call_count == 1
```

**Impact:** HIGH - Slow tests, API costs, flaky CI

---

## Antipattern 6: Incomplete Coverage

**Problem:** Missing test coverage for edge cases

```python
# ❌ BAD - Only tests typical cases
@pytest.mark.asyncio
async def test_cache_primitive():
    cache = CachePrimitive(ttl=3600)
    result = await cache.execute({"key": "value"}, context)
    assert result is not None
```

**Solution:**

```python
# ✅ GOOD - Comprehensive coverage
@pytest.mark.asyncio
async def test_cache_hit():
    """Test cache returns cached value."""
    # Test implementation

@pytest.mark.asyncio
async def test_cache_miss():
    """Test cache calls underlying primitive on miss."""
    # Test implementation

@pytest.mark.asyncio
async def test_cache_ttl_expiration():
    """Test cache evicts expired entries."""
    # Test implementation

@pytest.mark.asyncio
async def test_cache_with_none_input():
    """Test cache handles None input gracefully."""
    # Test implementation
```

**Impact:** HIGH - Bugs in untested code paths

---

## Detection

How to detect these antipatterns in your codebase:

```bash
# Find async tests without @pytest.mark.asyncio
grep -r "async def test_" tests/ | grep -v "@pytest.mark.asyncio"

# Find time.sleep in async code
grep -r "time.sleep" tests/

# Check test coverage
uv run pytest --cov=packages --cov-report=term-missing
```

## Related Pages

- [[TTA.dev/Best Practices/Testing]]
- [[TTA.dev/Examples/Test Examples]]
- [[Testing TTA Primitives]]

## Quick Fix Checklist

- [ ] All async tests have @pytest.mark.asyncio
- [ ] No time.sleep() in async tests
- [ ] Tests use public APIs only
- [ ] Error cases covered
- [ ] External services mocked
- [ ] 100% test coverage achieved
