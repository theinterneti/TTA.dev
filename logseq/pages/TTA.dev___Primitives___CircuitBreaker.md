# CircuitBreaker

type:: [[Primitive]]
category:: [[Recovery]]
package:: [[TTA.dev/Packages/tta-dev-primitives]]
status:: [[Stable]]
version:: 1.0.0
test-coverage:: 85
complexity:: [[Medium]]
python-class:: `CircuitBreaker`
import-path:: `from tta_dev_primitives.recovery import CircuitBreaker`
related-primitives:: [[TTA.dev/Primitives/RetryPrimitive]], [[TTA.dev/Primitives/FallbackPrimitive]], [[TTA.dev/Primitives/TimeoutPrimitive]]

---

## Overview

- id:: circuit-breaker-overview
  Error recovery framework implementing the circuit breaker pattern for development automation. Provides error classification, automatic retry with exponential backoff, and comprehensive error handling.

  **Think of it as:** A smart fuse that prevents cascading failures by temporarily stopping calls to a failing service.

---

## Use Cases

- id:: circuit-breaker-use-cases
  - **API protection:** Prevent overwhelming failing external services
  - **Error classification:** Automatically categorize errors (network, rate limit, transient, permanent)
  - **Retry orchestration:** Intelligent retry with exponential backoff and jitter
  - **Development automation:** Error recovery for development scripts
  - **Graceful degradation:** Stop attempting failed operations temporarily

---

## Key Benefits

- id:: circuit-breaker-benefits
  - ✅ **Error classification** - Categorize errors by type and severity
  - ✅ **Smart retries** - Exponential backoff with configurable jitter
  - ✅ **Circuit states** - CLOSED, OPEN, HALF-OPEN for controlled recovery
  - ✅ **Fallback support** - Execute fallback when circuit is open
  - ✅ **Async support** - Works with both sync and async functions
  - ✅ **Configurable thresholds** - Set failure counts, timeouts, delays

---

## API Reference

- id:: circuit-breaker-api

### Error Categories

```python
class ErrorCategory(Enum):
    NETWORK = "network"      # Network/API failures
    RATE_LIMIT = "rate_limit"  # Rate limiting
    RESOURCE = "resource"     # Resource exhaustion
    TRANSIENT = "transient"   # Temporary failures
    PERMANENT = "permanent"   # Permanent failures
```

### Error Severity

```python
class ErrorSeverity(Enum):
    LOW = "low"          # Minor issues, can continue
    MEDIUM = "medium"    # Significant but recoverable
    HIGH = "high"        # Critical, requires attention
    CRITICAL = "critical"  # System-breaking
```

### RetryConfig

```python
RetryConfig(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
)
```

---

## Examples

### Basic Retry with Decorator

- id:: circuit-breaker-decorator-example

```python
from tta_dev_primitives.recovery import with_retry, RetryConfig

config = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    exponential_base=2.0,
    jitter=True
)

@with_retry(config)
def call_external_api(endpoint: str) -> dict:
    """Call external API with automatic retry."""
    return requests.get(endpoint).json()
```

### Async Retry

- id:: circuit-breaker-async-example

```python
from tta_dev_primitives.recovery import with_retry_async, RetryConfig

config = RetryConfig(max_retries=5, base_delay=0.5)

@with_retry_async(config)
async def fetch_data(url: str) -> dict:
    """Fetch data with automatic retry."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### Error Classification

- id:: circuit-breaker-classification-example

```python
from tta_dev_primitives.recovery import classify_error, should_retry

try:
    result = call_api()
except Exception as e:
    category, severity = classify_error(e)

    if should_retry(e, attempt=1, max_retries=3):
        # Attempt retry
        result = call_api()
    else:
        # Handle permanent failure
        raise
```

---

## Circuit States

- id:: circuit-breaker-states

| State | Description | Behavior |
|-------|-------------|----------|
| **CLOSED** | Normal operation | All requests pass through |
| **OPEN** | Failure threshold exceeded | All requests fail fast |
| **HALF-OPEN** | Recovery testing | Limited requests allowed |

---

## Best Practices

- id:: circuit-breaker-best-practices

✅ **Use error classification** - Different handling for different error types
✅ **Configure jitter** - Prevent thundering herd on retries
✅ **Set appropriate thresholds** - Balance between resilience and responsiveness
✅ **Log circuit state changes** - Monitor for recurring issues
✅ **Use with fallbacks** - Combine with FallbackPrimitive for resilience

❌ **Don't retry permanent errors** - Check error classification first
❌ **Don't set delay too low** - Give services time to recover
❌ **Don't ignore circuit open** - Use fallback instead of forcing retries

---

## Related Content

### Works Well With

- [[TTA.dev/Primitives/RetryPrimitive]] - Higher-level retry abstraction
- [[TTA.dev/Primitives/FallbackPrimitive]] - Execute fallback when circuit opens
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Timeout before circuit breaker
- [[TTA.dev/Primitives/CompensationPrimitive]] - Rollback failed operations

---

## Metadata

**Source Code:** [circuit_breaker.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/src/tta_dev_primitives/recovery/circuit_breaker.py)
**Tests:** [test_circuit_breaker.py](https://github.com/theinterneti/TTA.dev/blob/main/platform/primitives/tests/recovery/test_circuit_breaker.py)

**Created:** [[2025-12-03]]
**Last Updated:** [[2025-12-03]]
**Status:** [[Stable]] - Production Ready
