# TTA.dev M1 — Primitive Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** All six core primitives have dedicated unit tests meeting 100% branch coverage; `UniversalLLMPrimitive` ships at `ttadev.primitives.llm`; `PRIMITIVES_CONTRACT.md` is written; semver policy is documented.

**Architecture:** All six primitives are already fully implemented — the primary work is test coverage. Tests live in `tests/primitives/{category}/` mirroring the source layout. The new `UniversalLLMPrimitive` is built TDD from scratch as a thin provider-abstraction layer at `ttadev/primitives/llm/`. Documentation artifacts (`PRIMITIVES_CONTRACT.md`, `docs/semver-policy.md`) are written last, once the surface is confirmed stable through tests.

**Tech Stack:** Python 3.11+, pytest, pytest-asyncio (`asyncio_mode = "auto"`), pytest-cov, uv

---

## Baseline Check

Before starting any task, establish a baseline.

- [ ] Run the full test suite and record how many pass/fail:
  ```bash
  uv run pytest tests/ -q 2>&1 | tail -5
  ```
- [ ] Check current coverage for the primitives under scope:
  ```bash
  uv run pytest tests/ \
    --cov=ttadev/primitives/recovery \
    --cov=ttadev/primitives/performance \
    --cov=ttadev/primitives/coordination \
    --cov-report=term-missing -q 2>&1 | tail -40
  ```
  Note which lines are uncovered. This is your target list.

---

## File Map

| File | Action | Purpose |
|------|--------|---------|
| `ttadev/primitives/recovery/retry.py` | Read only | Existing — understand `RetryPrimitive` + `RetryStrategy` API |
| `ttadev/primitives/recovery/fallback.py` | Read only | Existing — understand `FallbackPrimitive` API |
| `ttadev/primitives/recovery/timeout.py` | Read only | Existing — understand `TimeoutPrimitive` API |
| `ttadev/primitives/recovery/circuit_breaker_primitive.py` | Read only | Existing — understand `CircuitBreakerPrimitive` + `CircuitBreakerConfig` API |
| `ttadev/primitives/performance/cache.py` | Read only | Existing — understand `CachePrimitive` API |
| `tests/primitives/recovery/__init__.py` | Create | Package marker |
| `tests/primitives/recovery/test_retry_primitive.py` | Create | Unit tests for RetryPrimitive |
| `tests/primitives/recovery/test_fallback_primitive.py` | Create | Unit tests for FallbackPrimitive |
| `tests/primitives/recovery/test_timeout_primitive.py` | Create | Unit tests for TimeoutPrimitive |
| `tests/primitives/recovery/test_circuit_breaker_primitive.py` | Create | Unit tests for CircuitBreakerPrimitive |
| `tests/primitives/performance/__init__.py` | Create | Package marker |
| `tests/primitives/performance/test_cache_primitive.py` | Create | Unit tests for CachePrimitive |
| `ttadev/primitives/llm/__init__.py` | Create | Public exports for new LLM primitive |
| `ttadev/primitives/llm/universal_llm_primitive.py` | Create | New runtime LLM provider abstraction |
| `tests/primitives/llm/__init__.py` | Create | Package marker |
| `tests/primitives/llm/test_universal_llm_primitive.py` | Create | Unit tests for UniversalLLMPrimitive |
| `ttadev/primitives/__init__.py` | Modify | Export `UniversalLLMPrimitive`, `LLMRequest`, `LLMResponse` |
| `PRIMITIVES_CONTRACT.md` | Create | Formal interface + behavior contract for all primitives |
| `docs/semver-policy.md` | Create | What constitutes a breaking change in TTA.dev |

---

## Task 1: RetryPrimitive Tests

**Files:**
- Read: `ttadev/primitives/recovery/retry.py`
- Create: `tests/primitives/recovery/__init__.py`
- Create: `tests/primitives/recovery/test_retry_primitive.py`

- [ ] **Step 1: Read the RetryPrimitive source**

  ```bash
  uv run python -c "import inspect; from ttadev.primitives import RetryPrimitive, RetryStrategy; print(inspect.signature(RetryPrimitive.__init__)); print(inspect.signature(RetryStrategy))"
  ```
  Note the exact constructor parameters before writing tests.

- [ ] **Step 2: Create the package marker**

  ```bash
  touch tests/primitives/recovery/__init__.py
  ```

- [ ] **Step 3: Write the failing tests**

  Create `tests/primitives/recovery/test_retry_primitive.py`:

  ```python
  """Unit tests for RetryPrimitive — AAA pattern throughout."""
  import asyncio
  import pytest
  from ttadev.primitives import RetryPrimitive, RetryStrategy, WorkflowContext, LambdaPrimitive

  # Note: @pytest.mark.asyncio is NOT needed — pyproject.toml sets asyncio_mode = "auto"


  async def test_retry_succeeds_on_first_attempt():
      # Arrange
      calls = []

      async def operation(inp, ctx):
          calls.append(inp)
          return "ok"

      primitive = RetryPrimitive(LambdaPrimitive(operation), RetryStrategy(max_retries=3))
      ctx = WorkflowContext()

      # Act
      result = await primitive.execute("input", ctx)

      # Assert
      assert result == "ok"
      assert len(calls) == 1


  async def test_retry_succeeds_on_nth_attempt():
      # Arrange
      calls = []

      async def flaky(inp, ctx):
          calls.append(inp)
          if len(calls) < 3:
              raise ValueError("transient error")
          return "recovered"

      primitive = RetryPrimitive(LambdaPrimitive(flaky), RetryStrategy(max_retries=5))
      ctx = WorkflowContext()

      # Act
      result = await primitive.execute("input", ctx)

      # Assert
      assert result == "recovered"
      assert len(calls) == 3


  async def test_retry_raises_after_max_retries_exceeded():
      # Arrange
      async def always_fails(inp, ctx):
          raise ValueError("permanent error")

      primitive = RetryPrimitive(LambdaPrimitive(always_fails), RetryStrategy(max_retries=2))
      ctx = WorkflowContext()

      # Act / Assert
      with pytest.raises(Exception):
          await primitive.execute("input", ctx)


  async def test_retry_respects_max_retries_count():
      # Arrange
      call_count = 0

      async def always_fails(inp, ctx):
          nonlocal call_count
          call_count += 1
          raise ValueError("always fails")

      primitive = RetryPrimitive(LambdaPrimitive(always_fails), RetryStrategy(max_retries=3))
      ctx = WorkflowContext()

      # Act
      with pytest.raises(Exception):
          await primitive.execute("input", ctx)

      # Assert — initial attempt + max_retries retries
      assert call_count == 4


  async def test_retry_passes_context_to_wrapped_primitive():
      # Arrange
      received_contexts = []

      async def capture_ctx(inp, ctx):
          received_contexts.append(ctx)
          return "ok"

      primitive = RetryPrimitive(LambdaPrimitive(capture_ctx), RetryStrategy(max_retries=1))
      ctx = WorkflowContext()

      # Act
      await primitive.execute("input", ctx)

      # Assert
      assert len(received_contexts) == 1
      assert received_contexts[0] is ctx
  ```

- [ ] **Step 4: Run tests to verify they fail for the right reasons**

  ```bash
  uv run pytest tests/primitives/recovery/test_retry_primitive.py -v 2>&1 | head -40
  ```
  If tests import correctly but fail due to wrong behavior, read `retry.py` and adjust the test expectations to match the actual API signature. Do **not** change the test intent — only the API calls.

- [ ] **Step 5: Run tests — they should now pass**

  ```bash
  uv run pytest tests/primitives/recovery/test_retry_primitive.py -v
  ```
  Expected: All 5 tests PASS.

- [ ] **Step 6: Check coverage for retry.py**

  ```bash
  uv run pytest tests/primitives/recovery/test_retry_primitive.py --cov=ttadev/primitives/recovery/retry --cov-report=term-missing
  ```
  Note any uncovered branches. Add tests for each uncovered branch before committing.

- [ ] **Step 7: Commit**

  ```bash
  git add tests/primitives/recovery/__init__.py tests/primitives/recovery/test_retry_primitive.py
  git commit -m "test(primitives): add unit tests for RetryPrimitive"
  ```

---

## Task 2: FallbackPrimitive Tests

**Files:**
- Read: `ttadev/primitives/recovery/fallback.py`
- Create: `tests/primitives/recovery/test_fallback_primitive.py`

- [ ] **Step 1: Read the FallbackPrimitive source**

  ```bash
  uv run python -c "import inspect; from ttadev.primitives import FallbackPrimitive; print(inspect.signature(FallbackPrimitive.__init__))"
  ```

- [ ] **Step 2: Write the failing tests**

  Create `tests/primitives/recovery/test_fallback_primitive.py`:

  ```python
  """Unit tests for FallbackPrimitive — AAA pattern throughout."""
  import pytest
  from ttadev.primitives import FallbackPrimitive, WorkflowContext, LambdaPrimitive


  async def test_fallback_returns_primary_result_when_primary_succeeds():
      # Arrange
      async def primary(inp, ctx):
          return "primary-ok"

      async def fallback(inp, ctx):
          return "fallback-ok"

      primitive = FallbackPrimitive(LambdaPrimitive(primary), LambdaPrimitive(fallback))
      ctx = WorkflowContext()

      # Act
      result = await primitive.execute("input", ctx)

      # Assert
      assert result == "primary-ok"


  async def test_fallback_uses_fallback_when_primary_fails():
      # Arrange
      async def primary(inp, ctx):
          raise RuntimeError("primary failed")

      async def fallback(inp, ctx):
          return "fallback-ok"

      primitive = FallbackPrimitive(LambdaPrimitive(primary), LambdaPrimitive(fallback))
      ctx = WorkflowContext()

      # Act
      result = await primitive.execute("input", ctx)

      # Assert
      assert result == "fallback-ok"


  async def test_fallback_raises_when_both_fail():
      # Arrange
      async def primary(inp, ctx):
          raise RuntimeError("primary failed")

      async def fallback(inp, ctx):
          raise RuntimeError("fallback also failed")

      primitive = FallbackPrimitive(LambdaPrimitive(primary), LambdaPrimitive(fallback))
      ctx = WorkflowContext()

      # Act / Assert
      with pytest.raises(Exception):
          await primitive.execute("input", ctx)


  async def test_fallback_does_not_invoke_fallback_when_primary_succeeds():
      # Arrange
      fallback_called = []

      async def primary(inp, ctx):
          return "primary-ok"

      async def fallback(inp, ctx):
          fallback_called.append(True)
          return "fallback-ok"

      primitive = FallbackPrimitive(LambdaPrimitive(primary), LambdaPrimitive(fallback))
      ctx = WorkflowContext()

      # Act
      await primitive.execute("input", ctx)

      # Assert
      assert fallback_called == []
  ```

- [ ] **Step 3: Run tests — adjust API calls if needed, then verify PASS**

  ```bash
  uv run pytest tests/primitives/recovery/test_fallback_primitive.py -v
  ```

- [ ] **Step 4: Check coverage, add branch tests if needed**

  ```bash
  uv run pytest tests/primitives/recovery/test_fallback_primitive.py --cov=ttadev/primitives/recovery/fallback --cov-report=term-missing
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add tests/primitives/recovery/test_fallback_primitive.py
  git commit -m "test(primitives): add unit tests for FallbackPrimitive"
  ```

---

## Task 3: TimeoutPrimitive Tests

**Files:**
- Read: `ttadev/primitives/recovery/timeout.py`
- Create: `tests/primitives/recovery/test_timeout_primitive.py`

- [ ] **Step 1: Read the TimeoutPrimitive source**

  ```bash
  uv run python -c "import inspect; from ttadev.primitives import TimeoutPrimitive; print(inspect.signature(TimeoutPrimitive.__init__))"
  ```

- [ ] **Step 2: Write the failing tests**

  Create `tests/primitives/recovery/test_timeout_primitive.py`:

  ```python
  """Unit tests for TimeoutPrimitive — AAA pattern throughout."""
  import asyncio
  import pytest
  from ttadev.primitives import TimeoutPrimitive, WorkflowContext, LambdaPrimitive


  async def test_timeout_returns_result_when_operation_completes_in_time():
      # Arrange
      async def fast_op(inp, ctx):
          return "done"

      primitive = TimeoutPrimitive(LambdaPrimitive(fast_op), timeout_seconds=5.0)
      ctx = WorkflowContext()

      # Act
      result = await primitive.execute("input", ctx)

      # Assert
      assert result == "done"


  async def test_timeout_raises_when_operation_exceeds_limit():
      # Arrange
      async def slow_op(inp, ctx):
          await asyncio.sleep(10.0)
          return "never"

      primitive = TimeoutPrimitive(LambdaPrimitive(slow_op), timeout_seconds=0.01)
      ctx = WorkflowContext()

      # Act / Assert — should raise TimeoutError or asyncio.TimeoutError
      with pytest.raises((TimeoutError, asyncio.TimeoutError, Exception)):
          await primitive.execute("input", ctx)


  async def test_timeout_uses_fallback_when_provided_and_operation_times_out():
      # Arrange
      async def slow_op(inp, ctx):
          await asyncio.sleep(10.0)
          return "never"

      async def fallback_op(inp, ctx):
          return "fallback-result"

      primitive = TimeoutPrimitive(
          LambdaPrimitive(slow_op),
          timeout_seconds=0.01,
          fallback=LambdaPrimitive(fallback_op),
      )
      ctx = WorkflowContext()

      # Act
      result = await primitive.execute("input", ctx)

      # Assert
      assert result == "fallback-result"
  ```

  **Note:** Check `timeout.py` to see what exception type it raises on timeout — may be a custom `TimeoutError` subclass. Adjust the `pytest.raises` call to match.

- [ ] **Step 3: Run tests and verify PASS**

  ```bash
  uv run pytest tests/primitives/recovery/test_timeout_primitive.py -v
  ```

- [ ] **Step 4: Check coverage**

  ```bash
  uv run pytest tests/primitives/recovery/test_timeout_primitive.py --cov=ttadev/primitives/recovery/timeout --cov-report=term-missing
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add tests/primitives/recovery/test_timeout_primitive.py
  git commit -m "test(primitives): add unit tests for TimeoutPrimitive"
  ```

---

## Task 4: CircuitBreakerPrimitive Tests

**Files:**
- Read: `ttadev/primitives/recovery/circuit_breaker_primitive.py`
- Create: `tests/primitives/recovery/test_circuit_breaker_primitive.py`

- [ ] **Step 1: Read the CircuitBreakerPrimitive source**

  ```bash
  uv run python -c "import inspect; from ttadev.primitives import CircuitBreakerPrimitive; print(inspect.signature(CircuitBreakerPrimitive.__init__))"
  ```
  Also check what `CircuitBreakerConfig` fields exist and what `CircuitBreakerError` is named.

- [ ] **Step 2: Write the failing tests**

  Create `tests/primitives/recovery/test_circuit_breaker_primitive.py`:

  ```python
  """Unit tests for CircuitBreakerPrimitive — AAA pattern throughout."""
  import pytest
  # Two files export circuit breaker logic — check both after Task 4.
  # circuit_breaker.py: base state-machine logic
  # circuit_breaker_primitive.py: WorkflowPrimitive wrapper (public API)
  from ttadev.primitives import WorkflowContext, LambdaPrimitive
  from ttadev.primitives.recovery.circuit_breaker_primitive import (
      CircuitBreakerPrimitive,
      CircuitBreakerConfig,
      CircuitBreakerError,
  )


  async def test_circuit_breaker_allows_requests_when_closed():
      # Arrange
      async def op(inp, ctx):
          return "ok"

      cb = CircuitBreakerPrimitive(
          LambdaPrimitive(op),
          CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60),
      )
      ctx = WorkflowContext()

      # Act
      result = await cb.execute("input", ctx)

      # Assert
      assert result == "ok"


  async def test_circuit_breaker_opens_after_failure_threshold():
      # Arrange
      async def always_fails(inp, ctx):
          raise RuntimeError("fail")

      cb = CircuitBreakerPrimitive(
          LambdaPrimitive(always_fails),
          CircuitBreakerConfig(failure_threshold=2, recovery_timeout=60),
      )
      ctx = WorkflowContext()

      # Act — trigger enough failures to open the circuit
      for _ in range(2):
          with pytest.raises(RuntimeError):
              await cb.execute("input", ctx)

      # Assert — circuit should now be OPEN
      with pytest.raises(CircuitBreakerError):
          await cb.execute("input", ctx)


  async def test_circuit_breaker_raises_circuit_breaker_error_when_open():
      # Arrange
      fail_count = 0

      async def flaky(inp, ctx):
          nonlocal fail_count
          fail_count += 1
          raise RuntimeError("fail")

      cb = CircuitBreakerPrimitive(
          LambdaPrimitive(flaky),
          CircuitBreakerConfig(failure_threshold=1, recovery_timeout=60),
      )
      ctx = WorkflowContext()

      with pytest.raises(RuntimeError):
          await cb.execute("input", ctx)

      # Act — circuit is now open, further calls should raise CircuitBreakerError
      with pytest.raises(CircuitBreakerError):
          await cb.execute("input", ctx)

      # Assert — the underlying op was not called again (fail_count still 1)
      assert fail_count == 1


  async def test_circuit_breaker_transitions_to_half_open_after_recovery_timeout(monkeypatch):
      # Arrange
      import time
      call_count = 0

      async def op(inp, ctx):
          nonlocal call_count
          call_count += 1
          if call_count == 1:
              raise RuntimeError("first call fails")
          return "recovered"

      cb = CircuitBreakerPrimitive(
          LambdaPrimitive(op),
          CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.01),
      )
      ctx = WorkflowContext()

      # Open the circuit
      with pytest.raises(RuntimeError):
          await cb.execute("input", ctx)

      # Wait for recovery timeout
      import asyncio
      await asyncio.sleep(0.02)

      # Act — should now be in HALF_OPEN, attempt allowed
      result = await cb.execute("input", ctx)

      # Assert
      assert result == "recovered"
  ```

- [ ] **Step 3: Run tests and verify PASS**

  ```bash
  uv run pytest tests/primitives/recovery/test_circuit_breaker_primitive.py -v
  ```

- [ ] **Step 4: Check coverage**

  ```bash
  uv run pytest tests/primitives/recovery/test_circuit_breaker_primitive.py \
    --cov=ttadev/primitives/recovery/circuit_breaker \
    --cov=ttadev/primitives/recovery/circuit_breaker_primitive \
    --cov-report=term-missing
  ```

- [ ] **Step 5: Commit**

  ```bash
  git add tests/primitives/recovery/test_circuit_breaker_primitive.py
  git commit -m "test(primitives): add unit tests for CircuitBreakerPrimitive"
  ```

---

## Task 5: CachePrimitive Tests

**Files:**
- Read: `ttadev/primitives/performance/cache.py`
- Create: `tests/primitives/performance/__init__.py`
- Create: `tests/primitives/performance/test_cache_primitive.py`

- [ ] **Step 1: Read the CachePrimitive source**

  ```bash
  uv run python -c "import inspect; from ttadev.primitives import CachePrimitive; print(inspect.signature(CachePrimitive.__init__))"
  ```

- [ ] **Step 2: Create the package marker**

  ```bash
  touch tests/primitives/performance/__init__.py
  ```

- [ ] **Step 3: Write the failing tests**

  Create `tests/primitives/performance/test_cache_primitive.py`:

  ```python
  """Unit tests for CachePrimitive — AAA pattern throughout."""
  import asyncio
  import pytest
  from ttadev.primitives import CachePrimitive, WorkflowContext, LambdaPrimitive


  async def test_cache_returns_result_on_first_call():
      # Arrange
      async def compute(inp, ctx):
          return f"result-{inp}"

      cache = CachePrimitive(LambdaPrimitive(compute), ttl_seconds=60)
      ctx = WorkflowContext()

      # Act
      result = await cache.execute("key1", ctx)

      # Assert
      assert result == "result-key1"


  async def test_cache_returns_cached_result_on_second_call():
      # Arrange
      call_count = 0

      async def compute(inp, ctx):
          nonlocal call_count
          call_count += 1
          return f"result-{inp}"

      cache = CachePrimitive(LambdaPrimitive(compute), ttl_seconds=60)
      ctx = WorkflowContext()

      # Act
      await cache.execute("key1", ctx)
      result = await cache.execute("key1", ctx)

      # Assert — underlying compute only called once
      assert result == "result-key1"
      assert call_count == 1


  async def test_cache_computes_fresh_result_after_ttl_expires():
      # Arrange
      call_count = 0

      async def compute(inp, ctx):
          nonlocal call_count
          call_count += 1
          return f"result-{call_count}"

      cache = CachePrimitive(LambdaPrimitive(compute), ttl_seconds=0.01)
      ctx = WorkflowContext()

      # Act
      await cache.execute("key1", ctx)
      await asyncio.sleep(0.02)
      result = await cache.execute("key1", ctx)

      # Assert — recomputed after TTL
      assert call_count == 2
      assert result == "result-2"


  async def test_cache_uses_custom_key_function():
      # Arrange
      seen_keys = []

      async def compute(inp, ctx):
          return inp

      def custom_key(inp):
          key = f"custom:{inp}"
          seen_keys.append(key)
          return key

      cache = CachePrimitive(LambdaPrimitive(compute), ttl_seconds=60, cache_key_fn=custom_key)
      ctx = WorkflowContext()

      # Act
      await cache.execute("hello", ctx)

      # Assert
      assert "custom:hello" in seen_keys


  async def test_cache_treats_different_inputs_as_separate_keys():
      # Arrange
      call_count = 0

      async def compute(inp, ctx):
          nonlocal call_count
          call_count += 1
          return f"result-{inp}"

      cache = CachePrimitive(LambdaPrimitive(compute), ttl_seconds=60)
      ctx = WorkflowContext()

      # Act
      await cache.execute("key1", ctx)
      await cache.execute("key2", ctx)

      # Assert — two different keys = two compute calls
      assert call_count == 2
  ```

- [ ] **Step 4: Run tests and verify PASS**

  ```bash
  uv run pytest tests/primitives/performance/test_cache_primitive.py -v
  ```

- [ ] **Step 5: Check coverage**

  ```bash
  uv run pytest tests/primitives/performance/test_cache_primitive.py --cov=ttadev/primitives/performance/cache --cov-report=term-missing
  ```

- [ ] **Step 6: Commit**

  ```bash
  git add tests/primitives/performance/__init__.py tests/primitives/performance/test_cache_primitive.py
  git commit -m "test(primitives): add unit tests for CachePrimitive"
  ```

---

## Task 6: Verify Full Primitive Coverage

- [ ] **Step 1: Run coverage across all six primitives**

  ```bash
  uv run pytest tests/primitives/ \
    --cov=ttadev/primitives/recovery/retry \
    --cov=ttadev/primitives/recovery/fallback \
    --cov=ttadev/primitives/recovery/timeout \
    --cov=ttadev/primitives/recovery/circuit_breaker \
    --cov=ttadev/primitives/recovery/circuit_breaker_primitive \
    --cov=ttadev/primitives/performance/cache \
    --cov=ttadev/primitives/coordination \
    --cov-report=term-missing -q
  ```

- [ ] **Step 2: Add targeted tests for any uncovered branches**

  For each uncovered line reported, write a test that exercises that specific branch. Commit each batch of branch-coverage tests with:
  ```bash
  git commit -m "test(primitives): add branch coverage for <primitive-name>"
  ```

- [ ] **Step 3: Confirm 100% coverage on all six**

  ```bash
  uv run pytest tests/primitives/ \
    --cov=ttadev/primitives/recovery/retry \
    --cov=ttadev/primitives/recovery/fallback \
    --cov=ttadev/primitives/recovery/timeout \
    --cov=ttadev/primitives/recovery/circuit_breaker \
    --cov=ttadev/primitives/recovery/circuit_breaker_primitive \
    --cov=ttadev/primitives/performance/cache \
    --cov=ttadev/primitives/coordination \
    --cov-fail-under=100 -q
  ```
  Expected: PASS with no coverage failures.

---

## Task 6b: CoordinationPrimitive Coverage Audit

The `RedisMessageCoordinator` at `ttadev/primitives/coordination/redis_coordinator.py` has an existing test file but may not be at 100% branch coverage. Redis-dependent branches must be tested using `unittest.mock` — do **not** require a running Redis instance for unit tests.

**Files:**
- Read: `ttadev/primitives/coordination/redis_coordinator.py`
- Modify: `tests/primitives/coordination/test_redis_coordinator.py`

- [ ] **Step 1: Read the coordinator source and check current coverage**

  ```bash
  uv run pytest tests/primitives/coordination/ \
    --cov=ttadev/primitives/coordination \
    --cov-report=term-missing -q
  ```
  List every uncovered branch. If already at 100%, this task is done — skip to commit.

- [ ] **Step 2: For each uncovered branch, write a targeted mock-based test**

  Pattern for mocking Redis:

  ```python
  from unittest.mock import AsyncMock, MagicMock, patch

  async def test_coordinator_handles_connection_error():
      # Arrange — mock the Redis client to raise on connect
      with patch("ttadev.primitives.coordination.redis_coordinator.redis.asyncio.Redis") as mock_redis:
          mock_redis.return_value.ping = AsyncMock(side_effect=ConnectionError("Redis down"))
          coordinator = RedisMessageCoordinator(redis_url="redis://localhost:6379")

          # Act / Assert
          with pytest.raises(ConnectionError):
              await coordinator.connect()
  ```

  Adjust to match the actual class API — read the source first.

- [ ] **Step 3: Verify 100% coverage**

  ```bash
  uv run pytest tests/primitives/coordination/ \
    --cov=ttadev/primitives/coordination \
    --cov-fail-under=100 -q
  ```

- [ ] **Step 4: Commit**

  ```bash
  git add tests/primitives/coordination/test_redis_coordinator.py
  git commit -m "test(primitives): achieve 100% branch coverage on CoordinationPrimitive"
  ```

---

## Task 7: UniversalLLMPrimitive (New)

This is a **new primitive** at `ttadev/primitives/llm/`. It is distinct from the existing `UniversalLLMPrimitive` in `ttadev/integrations/` (which handles agentic coder budget profiles). This one handles **runtime LLM invocation** with a clean provider-abstraction interface.

**Files:**
- Create: `ttadev/primitives/llm/__init__.py`
- Create: `ttadev/primitives/llm/universal_llm_primitive.py`
- Create: `tests/primitives/llm/__init__.py`
- Create: `tests/primitives/llm/test_universal_llm_primitive.py`
- Modify: `ttadev/primitives/__init__.py`

- [ ] **Step 1: Write the failing tests first (TDD)**

  Create `tests/primitives/llm/__init__.py` (empty).

  Create `tests/primitives/llm/test_universal_llm_primitive.py`:

  ```python
  """Unit tests for UniversalLLMPrimitive (runtime LLM invocation layer)."""
  from unittest.mock import AsyncMock, patch
  import pytest
  from ttadev.primitives.llm.universal_llm_primitive import (
      UniversalLLMPrimitive,
      LLMRequest,
      LLMResponse,
      LLMProvider,
  )
  from ttadev.primitives import WorkflowContext


  async def test_llm_request_and_response_are_dataclasses():
      req = LLMRequest(
          model="llama3-8b-8192",
          messages=[{"role": "user", "content": "hello"}],
      )
      assert req.model == "llama3-8b-8192"
      assert req.temperature == 0.7  # default


  async def test_universal_llm_primitive_calls_groq_provider():
      # Arrange
      mock_response = LLMResponse(
          content="Hello back",
          model="llama3-8b-8192",
          provider="groq",
      )
      primitive = UniversalLLMPrimitive(provider=LLMProvider.GROQ, api_key="test-key")
      ctx = WorkflowContext()
      request = LLMRequest(
          model="llama3-8b-8192",
          messages=[{"role": "user", "content": "hi"}],
      )

      # Act
      with patch.object(primitive, "_call_groq", new=AsyncMock(return_value=mock_response)):
          result = await primitive.execute(request, ctx)

      # Assert
      assert result.content == "Hello back"
      assert result.provider == "groq"


  async def test_universal_llm_primitive_calls_anthropic_provider():
      # Arrange
      mock_response = LLMResponse(
          content="Hi from Claude",
          model="claude-haiku-4-5-20251001",
          provider="anthropic",
      )
      primitive = UniversalLLMPrimitive(provider=LLMProvider.ANTHROPIC, api_key="test-key")
      ctx = WorkflowContext()
      request = LLMRequest(
          model="claude-haiku-4-5-20251001",
          messages=[{"role": "user", "content": "hi"}],
      )

      # Act
      with patch.object(primitive, "_call_anthropic", new=AsyncMock(return_value=mock_response)):
          result = await primitive.execute(request, ctx)

      # Assert
      assert result.provider == "anthropic"


  async def test_universal_llm_primitive_calls_openai_provider():
      # Arrange
      mock_response = LLMResponse(
          content="OpenAI response",
          model="gpt-4o",
          provider="openai",
      )
      primitive = UniversalLLMPrimitive(provider=LLMProvider.OPENAI, api_key="test-key")
      ctx = WorkflowContext()
      request = LLMRequest(
          model="gpt-4o",
          messages=[{"role": "user", "content": "hi"}],
      )

      # Act
      with patch.object(primitive, "_call_openai", new=AsyncMock(return_value=mock_response)):
          result = await primitive.execute(request, ctx)

      # Assert
      assert result.provider == "openai"


  async def test_universal_llm_primitive_calls_ollama_provider():
      # Arrange
      mock_response = LLMResponse(
          content="Local response",
          model="llama3",
          provider="ollama",
      )
      primitive = UniversalLLMPrimitive(
          provider=LLMProvider.OLLAMA, base_url="http://localhost:11434"
      )
      ctx = WorkflowContext()
      request = LLMRequest(
          model="llama3",
          messages=[{"role": "user", "content": "hi"}],
      )

      # Act
      with patch.object(primitive, "_call_ollama", new=AsyncMock(return_value=mock_response)):
          result = await primitive.execute(request, ctx)

      # Assert
      assert result.provider == "ollama"


  def test_universal_llm_primitive_raises_value_error_for_unknown_provider():
      # Arrange — pass a non-enum value (integer) that definitely hits the isinstance guard
      with pytest.raises(ValueError):
          UniversalLLMPrimitive(provider=42)  # type: ignore[arg-type]


  def test_llm_request_default_temperature():
      req = LLMRequest(model="any", messages=[])
      assert req.temperature == 0.7


  def test_llm_request_custom_max_tokens():
      req = LLMRequest(model="any", messages=[], max_tokens=512)
      assert req.max_tokens == 512


  def test_llm_response_has_required_fields():
      resp = LLMResponse(content="text", model="any-model", provider="groq")
      assert resp.content == "text"
      assert resp.provider == "groq"
  ```

- [ ] **Step 2: Run tests — verify they all FAIL with ImportError**

  ```bash
  uv run pytest tests/primitives/llm/test_universal_llm_primitive.py -v 2>&1 | head -20
  ```
  Expected: `ModuleNotFoundError` or `ImportError` — the module doesn't exist yet.

- [ ] **Step 3: Implement UniversalLLMPrimitive**

  Create `ttadev/primitives/llm/universal_llm_primitive.py`:

  ```python
  """UniversalLLMPrimitive — runtime LLM provider abstraction.

  Provides a single interface for invoking LLMs across providers
  (Groq, Anthropic, OpenAI, Ollama). Config-driven, swappable backends.

  Note: This is distinct from ttadev/integrations/llm/universal_llm_primitive.py
  which handles agentic coder budget profiles. This module handles
  runtime LLM calls from within workflow pipelines.
  """
  from __future__ import annotations

  from dataclasses import dataclass, field
  from enum import Enum

  from ttadev.primitives.core import WorkflowPrimitive, WorkflowContext


  class LLMProvider(str, Enum):
      GROQ = "groq"
      ANTHROPIC = "anthropic"
      OPENAI = "openai"
      OLLAMA = "ollama"


  @dataclass
  class LLMRequest:
      model: str
      messages: list[dict[str, str]]
      temperature: float = 0.7
      max_tokens: int | None = None
      system: str | None = None


  @dataclass
  class LLMResponse:
      content: str
      model: str
      provider: str
      usage: dict[str, int] | None = None


  class UniversalLLMPrimitive(WorkflowPrimitive[LLMRequest, LLMResponse]):
      """Route LLM requests to the appropriate provider backend."""

      def __init__(
          self,
          provider: LLMProvider,
          api_key: str | None = None,
          base_url: str | None = None,
      ) -> None:
          super().__init__()
          if not isinstance(provider, LLMProvider):
              raise ValueError(f"Unknown provider: {provider!r}. Use LLMProvider enum.")
          self._provider = provider
          self._api_key = api_key
          self._base_url = base_url

      async def execute(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
          dispatch = {
              LLMProvider.GROQ: self._call_groq,
              LLMProvider.ANTHROPIC: self._call_anthropic,
              LLMProvider.OPENAI: self._call_openai,
              LLMProvider.OLLAMA: self._call_ollama,
          }
          return await dispatch[self._provider](request, ctx)

      async def _call_groq(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
          from groq import AsyncGroq  # type: ignore[import]

          client = AsyncGroq(api_key=self._api_key)
          resp = await client.chat.completions.create(
              model=request.model,
              messages=request.messages,  # type: ignore[arg-type]
              temperature=request.temperature,
              max_tokens=request.max_tokens,
          )
          return LLMResponse(
              content=resp.choices[0].message.content or "",
              model=resp.model,
              provider="groq",
              usage={"prompt_tokens": resp.usage.prompt_tokens, "completion_tokens": resp.usage.completion_tokens}
              if resp.usage
              else None,
          )

      async def _call_anthropic(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
          import anthropic  # type: ignore[import]

          client = anthropic.AsyncAnthropic(api_key=self._api_key)
          resp = await client.messages.create(
              model=request.model,
              max_tokens=request.max_tokens or 1024,
              system=request.system or "",
              messages=request.messages,  # type: ignore[arg-type]
          )
          return LLMResponse(
              content=resp.content[0].text if resp.content else "",
              model=resp.model,
              provider="anthropic",
              usage={"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens},
          )

      async def _call_openai(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
          from openai import AsyncOpenAI  # type: ignore[import]

          client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
          resp = await client.chat.completions.create(
              model=request.model,
              messages=request.messages,  # type: ignore[arg-type]
              temperature=request.temperature,
              max_tokens=request.max_tokens,
          )
          return LLMResponse(
              content=resp.choices[0].message.content or "",
              model=resp.model,
              provider="openai",
              usage={"prompt_tokens": resp.usage.prompt_tokens, "completion_tokens": resp.usage.completion_tokens}
              if resp.usage
              else None,
          )

      async def _call_ollama(self, request: LLMRequest, ctx: WorkflowContext) -> LLMResponse:
          import httpx

          base = self._base_url or "http://localhost:11434"
          payload = {
              "model": request.model,
              "messages": request.messages,
              "stream": False,
              "options": {"temperature": request.temperature},
          }
          async with httpx.AsyncClient() as client:
              resp = await client.post(f"{base}/api/chat", json=payload)
              resp.raise_for_status()
              data = resp.json()
          return LLMResponse(
              content=data["message"]["content"],
              model=request.model,
              provider="ollama",
          )
  ```

- [ ] **Step 4: Create the package `__init__.py`**

  Create `ttadev/primitives/llm/__init__.py`:

  ```python
  """LLM primitives — runtime LLM provider abstraction."""
  from ttadev.primitives.llm.universal_llm_primitive import (
      LLMProvider,
      LLMRequest,
      LLMResponse,
      UniversalLLMPrimitive,
  )

  __all__ = ["LLMProvider", "LLMRequest", "LLMResponse", "UniversalLLMPrimitive"]
  ```

- [ ] **Step 5: Run tests — verify they PASS**

  ```bash
  uv run pytest tests/primitives/llm/test_universal_llm_primitive.py -v
  ```
  Expected: All tests PASS.

- [ ] **Step 6: Check coverage**

  ```bash
  uv run pytest tests/primitives/llm/ --cov=ttadev/primitives/llm --cov-report=term-missing
  ```
  Add tests for any uncovered branches.

- [ ] **Step 7: Export from main __init__.py**

  In `ttadev/primitives/__init__.py`, add to the existing exports:

  ```python
  from ttadev.primitives.llm import (
      LLMProvider,
      LLMRequest,
      LLMResponse,
      UniversalLLMPrimitive,
  )
  ```

- [ ] **Step 8: Verify import works**

  ```bash
  uv run python -c "from ttadev.primitives import UniversalLLMPrimitive, LLMRequest, LLMResponse, LLMProvider; print('OK')"
  ```
  Expected: `OK`

- [ ] **Step 9: Run full lint + type check**

  ```bash
  uv run ruff check ttadev/primitives/llm/ --fix
  uv run ruff format ttadev/primitives/llm/
  uvx pyright ttadev/primitives/llm/
  ```

- [ ] **Step 10: Commit**

  ```bash
  git add ttadev/primitives/llm/ tests/primitives/llm/
  git commit -m "feat(primitives): add UniversalLLMPrimitive at ttadev.primitives.llm"
  ```

---

## Task 8: PRIMITIVES_CONTRACT.md

**Files:**
- Create: `PRIMITIVES_CONTRACT.md`

- [ ] **Step 1: Write the contract document**

  Create `PRIMITIVES_CONTRACT.md` at the repo root:

  ```markdown
  # TTA.dev Primitives Contract

  **Status:** Stable (as of TTA.dev M1)
  **Package:** `ttadev.primitives`
  **Version policy:** See [docs/semver-policy.md](docs/semver-policy.md)

  This document defines the interface guarantees for each primitive.
  Consumers may rely on these contracts across patch and minor versions.
  Breaking changes require a major version bump.

  ---

  ## Base Contract (All Primitives)

  Every primitive in `ttadev.primitives` satisfies:

  ```python
  class WorkflowPrimitive[TInput, TOutput]:
      async def execute(self, input: TInput, ctx: WorkflowContext) -> TOutput: ...
  ```

  - `execute` is always `async`
  - `execute` never mutates `input`
  - `WorkflowContext` is passed through — primitives may read and write context keys
  - Exceptions propagate unless the primitive explicitly handles them

  ---

  ## RetryPrimitive

  **Import:** `from ttadev.primitives import RetryPrimitive, RetryStrategy`

  **Guarantees:**
  - Retries the wrapped primitive up to `RetryStrategy.max_retries` times on failure
  - Uses exponential backoff: `min(backoff_base ** attempt, max_backoff)` seconds between retries
  - Raises the last exception if all retries are exhausted
  - Total attempts = 1 (initial) + max_retries

  **Not guaranteed:**
  - Specific exception types from the wrapped primitive are preserved (re-raised as-is)

  ---

  ## FallbackPrimitive

  **Import:** `from ttadev.primitives import FallbackPrimitive`

  **Guarantees:**
  - Executes primary primitive; if it raises, executes fallback
  - Returns primary result if primary succeeds (fallback is never called)
  - Returns fallback result if primary fails and fallback succeeds
  - Raises fallback exception if both fail
  - Fallback receives the same `input` and `ctx` as the primary

  ---

  ## TimeoutPrimitive

  **Import:** `from ttadev.primitives import TimeoutPrimitive`

  **Guarantees:**
  - Raises `TimeoutError` (or subclass) if wrapped primitive exceeds `timeout_seconds`
  - If `fallback` is provided, executes fallback instead of raising on timeout
  - Underlying async task is cancelled on timeout

  ---

  ## CircuitBreakerPrimitive

  **Import:** `from ttadev.primitives.recovery.circuit_breaker_primitive import CircuitBreakerPrimitive, CircuitBreakerConfig, CircuitBreakerError`

  **Guarantees:**
  - Three states: CLOSED → OPEN (after `failure_threshold` failures) → HALF_OPEN (after `recovery_timeout` seconds)
  - In OPEN state: raises `CircuitBreakerError` immediately without calling wrapped primitive
  - In HALF_OPEN state: allows one request; success → CLOSED, failure → OPEN
  - State is per-instance (not shared across instances)

  ---

  ## CachePrimitive

  **Import:** `from ttadev.primitives import CachePrimitive`

  **Guarantees:**
  - Results are cached for `ttl_seconds` from time of first computation
  - Cache key is `str(input)` by default; provide `cache_key_fn` for custom keys
  - After TTL expires, the next call recomputes and re-caches
  - Cache is in-memory per-instance (not persistent, not shared)

  ---

  ## CoordinationPrimitive (Redis)

  **Import:** `from ttadev.primitives.coordination import RedisMessageCoordinator`

  **Guarantees:**
  - Messages are durably enqueued with visibility timeout + acknowledgement pattern
  - Priority levels: HIGH, NORMAL, LOW
  - Messages not acknowledged within `visibility_timeout` are requeued
  - Requires a running Redis instance

  ---

  ## UniversalLLMPrimitive

  **Import:** `from ttadev.primitives import UniversalLLMPrimitive, LLMRequest, LLMResponse, LLMProvider`

  **Guarantees:**
  - Single `execute(LLMRequest, WorkflowContext) -> LLMResponse` interface across all providers
  - Supported providers: `LLMProvider.GROQ`, `ANTHROPIC`, `OPENAI`, `OLLAMA`
  - `LLMResponse.provider` always matches the configured provider string
  - Raises `ValueError` if an unsupported provider is passed to the constructor

  **Not guaranteed:**
  - Network availability or provider API stability
  - Response latency

  ---

  ## Change Log

  | Version | Change |
  |---------|--------|
  | M1.0    | Initial stable contract for all six core primitives + UniversalLLMPrimitive |
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add PRIMITIVES_CONTRACT.md
  git commit -m "docs: add PRIMITIVES_CONTRACT.md — stable interface guarantees for M1"
  ```

---

## Task 9: Semver Policy

**Files:**
- Create: `docs/semver-policy.md`

- [ ] **Step 1: Write the semver policy**

  Create `docs/semver-policy.md`:

  ```markdown
  # TTA.dev Semver Policy

  TTA.dev follows [Semantic Versioning 2.0](https://semver.org): `MAJOR.MINOR.PATCH`.

  ## What Constitutes a Breaking Change (MAJOR bump)

  Any change to the public API in `ttadev/primitives/__init__.py` that requires
  callers to update their code:

  - Removing or renaming a public class, function, or enum value
  - Changing a method signature (adding required parameters, removing parameters,
    changing parameter types in a non-compatible way)
  - Changing the exception type raised by a primitive's `execute()` method
  - Changing the semantics of an existing behavior (e.g., RetryPrimitive
    counting retries differently)
  - Removing a primitive from the public exports

  ## What Does NOT Constitute a Breaking Change (MINOR or PATCH bump)

  - Adding new optional parameters with defaults
  - Adding new public classes, functions, or enum values
  - Fixing bugs where the old behavior was incorrect
  - Internal refactoring with no observable behavior change
  - Documentation updates
  - Adding new primitives

  ## Contract Stability

  Primitives documented in `PRIMITIVES_CONTRACT.md` are considered stable.
  Experimental primitives (marked `[EXPERIMENTAL]` in the catalog) may change
  in any minor version.

  ## Current Version

  See `ttadev/primitives/__init__.py` — `__version__` string.

  ## Consumer Pinning

  TTA (and other consumers) should pin to `ttadev >= M1.0, < M2.0` until
  ready to migrate to new major versions. Check the CHANGELOG for migration
  guidance between major versions.
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add docs/semver-policy.md
  git commit -m "docs: add semver policy for TTA.dev primitives"
  ```

---

## Task 10: M1 Final Verification

- [ ] **Step 1: Run the full test suite**

  ```bash
  uv run pytest tests/ -q
  ```
  Expected: All tests PASS, no regressions.

- [ ] **Step 2: Run full lint + type check**

  ```bash
  uv run ruff check . --fix
  uv run ruff format .
  uvx pyright ttadev/
  ```
  Expected: No errors.

- [ ] **Step 3: Verify M1 acceptance criteria**

  - [ ] `PRIMITIVES_CONTRACT.md` exists at repo root
  - [ ] All six primitives have 100% branch coverage (run coverage check from Task 6)
  - [ ] `UniversalLLMPrimitive` importable from `ttadev.primitives`
  - [ ] `docs/semver-policy.md` exists
  - [ ] `PRIMITIVES_CATALOG.md` reflects the new `UniversalLLMPrimitive` entry

- [ ] **Step 4: Update PRIMITIVES_CATALOG.md**

  Add an entry for `UniversalLLMPrimitive` in `PRIMITIVES_CATALOG.md` following the existing format for other primitives. Include: import path, constructor signature, `LLMRequest`/`LLMResponse` schema, supported providers.

  ```bash
  git add PRIMITIVES_CATALOG.md
  git commit -m "docs: add UniversalLLMPrimitive entry to PRIMITIVES_CATALOG"
  ```

- [ ] **Step 5: Final commit tag note**

  ```bash
  git log --oneline -10
  ```
  Note the commit SHA — this is the M1 stable baseline for TTA to pin against.
