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
- Raises `TimeoutError` (custom subclass at `ttadev.primitives.recovery.timeout`) if wrapped primitive exceeds `timeout_seconds`
- If `fallback` is provided, executes fallback instead of raising on timeout
- Underlying async task is cancelled on timeout

---

## CircuitBreakerPrimitive

**Import:** `from ttadev.primitives.recovery.circuit_breaker_primitive import CircuitBreakerPrimitive, CircuitBreakerConfig, CircuitBreakerError`

**Guarantees:**
- CLOSED state: allows all requests through
- Opens after `CircuitBreakerConfig.failure_threshold` consecutive failures
- OPEN state: raises `CircuitBreakerError` immediately (no underlying call)
- HALF_OPEN after `recovery_timeout` seconds: allows one probe request
- Closes on successful probe; re-opens on failed probe

---

## CachePrimitive

**Import:** `from ttadev.primitives import CachePrimitive`

**Guarantees:**
- Returns cached result for same input within `ttl_seconds`
- Calls wrapped primitive and caches result on first call or after TTL expires
- `cache_key_fn(input, ctx) -> str` determines cache key (required)
- `clear_cache()` removes all cached entries
- `evict_expired()` removes entries past their TTL

---

## UniversalLLMPrimitive

**Import:** `from ttadev.primitives import UniversalLLMPrimitive, LLMRequest, LLMResponse, LLMProvider`

**Guarantees:**
- Routes `LLMRequest` to the configured provider backend
- Supported providers: `LLMProvider.GROQ`, `LLMProvider.ANTHROPIC`, `LLMProvider.OPENAI`, `LLMProvider.OLLAMA`
- Returns `LLMResponse` with `content`, `model`, `provider`, and optional `usage`
- Raises `ValueError` if `provider` is not a `LLMProvider` enum member

---

## Coordination

**Import:** `from ttadev.primitives.coordination import RedisMessageCoordinator`

See source for full API — coordination primitives are stable but not yet under full contract.
