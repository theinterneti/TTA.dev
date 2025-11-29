# Custom Exceptions - Phase 3 Complete

**Date:** 2025-11-07
**Status:** ✅ COMPLETE
**Next:** Prometheus Metrics Integration

---

## 🎯 Overview

Created a comprehensive exception hierarchy for the adaptive primitives module, providing clear error messages and enabling proper error handling throughout the learning workflow.

---

## ✅ Accomplishments

### 1. Exception Hierarchy Design

Created `adaptive/exceptions.py` with a well-structured exception hierarchy:

```
AdaptiveError (base)
├── LearningError - Learning process errors
│   ├── StrategyValidationError - Strategy validation failures
│   ├── StrategyAdaptationError - Strategy adaptation failures
│   ├── ValidationWindowError - Insufficient validation data
│   └── PerformanceRegressionError - Performance worse than baseline
├── CircuitBreakerError - Circuit breaker activation
├── ContextExtractionError - Context extraction failures
└── StrategyNotFoundError - Strategy lookup failures
```

### 2. Base Exception: AdaptiveError

All adaptive primitive exceptions inherit from `AdaptiveError`:

```python
class AdaptiveError(Exception):
    """Base exception for all adaptive primitive errors."""
    pass
```

**Benefits:**
- ✅ Single catch point for all adaptive errors
- ✅ Clear namespace separation
- ✅ Easy to distinguish from other exceptions
- ✅ Follows Python exception hierarchy best practices

### 3. Learning Errors

#### LearningError

Base class for all learning-related errors:

```python
class LearningError(AdaptiveError):
    """Raised when the learning process encounters an error."""
    pass
```

**Use cases:**
- Insufficient training data
- Invalid performance metrics
- Learning algorithm failure
- Strategy creation errors

#### StrategyValidationError

Raised when strategy validation fails:

```python
class StrategyValidationError(LearningError):
    """Raised when strategy validation fails."""
    pass
```

**Triggers:**
- Success rate below threshold
- Performance worse than baseline
- Insufficient validation attempts
- Context mismatch

#### StrategyAdaptationError

Raised when adapting strategies fails:

```python
class StrategyAdaptationError(LearningError):
    """Raised when strategy adaptation fails."""
    pass
```

**Triggers:**
- Parameter adjustment failure
- Invalid strategy parameters
- Conflicting performance metrics
- Adaptation threshold not met

#### ValidationWindowError

Raised when validation window requirements aren't met:

```python
class ValidationWindowError(LearningError):
    """Raised when validation window requirements are not met."""
    pass
```

**Triggers:**
- Not enough executions in window
- Window size too small
- All executions failed
- Inconsistent validation results

#### PerformanceRegressionError

Enhanced exception with detailed performance metrics:

```python
class PerformanceRegressionError(StrategyValidationError):
    """Raised when a new strategy performs worse than the baseline."""

    def __init__(
        self,
        strategy_name: str,
        metric_name: str,
        strategy_value: float,
        baseline_value: float,
    ) -> None:
        self.strategy_name = strategy_name
        self.metric_name = metric_name
        self.strategy_value = strategy_value
        self.baseline_value = baseline_value

        message = (
            f"Strategy '{strategy_name}' shows performance regression: "
            f"{metric_name}={strategy_value:.3f} < baseline={baseline_value:.3f}"
        )
        super().__init__(message)
```

**Benefits:**
- ✅ Structured error information
- ✅ Clear performance comparison
- ✅ Easy to log and track
- ✅ Helpful debugging context

### 4. Circuit Breaker Errors

Enhanced exception with failure context:

```python
class CircuitBreakerError(AdaptiveError):
    """Raised when the circuit breaker is activated."""

    def __init__(
        self,
        message: str = "Circuit breaker active",
        failure_rate: float | None = None,
        cooldown_seconds: float | None = None,
    ) -> None:
        self.failure_rate = failure_rate
        self.cooldown_seconds = cooldown_seconds

        if failure_rate is not None:
            message = f"{message} (failure_rate={failure_rate:.1%})"
        if cooldown_seconds is not None:
            message = f"{message} (resets in {cooldown_seconds}s)"

        super().__init__(message)
```

**Features:**
- ✅ Captures failure rate that triggered circuit breaker
- ✅ Includes cooldown period information
- ✅ Enhanced error message with context
- ✅ Optional parameters for flexibility

**Example usage:**
```python
raise CircuitBreakerError(
    "Too many failures detected",
    failure_rate=0.65,
    cooldown_seconds=300.0
)
# Error: Too many failures detected (failure_rate=65.0%) (resets in 300.0s)
```

### 5. Context Extraction Errors

```python
class ContextExtractionError(AdaptiveError):
    """Raised when context extraction fails."""
    pass
```

**Triggers:**
- Missing required metadata
- Invalid context extractor function
- Context extractor raised exception
- Malformed context key

### 6. Strategy Not Found Errors

Enhanced exception with helpful suggestions:

```python
class StrategyNotFoundError(AdaptiveError):
    """Raised when a requested strategy cannot be found."""

    def __init__(
        self,
        strategy_name: str,
        available_strategies: list[str] | None = None
    ) -> None:
        self.strategy_name = strategy_name
        self.available_strategies = available_strategies

        message = f"Strategy '{strategy_name}' not found"
        if available_strategies:
            message = f"{message}. Available strategies: {', '.join(available_strategies)}"

        super().__init__(message)
```

**Example usage:**
```python
raise StrategyNotFoundError(
    "fast_retry_v2",
    available_strategies=["baseline", "production_v1", "staging_v1"]
)
# Error: Strategy 'fast_retry_v2' not found. Available strategies: baseline, production_v1, staging_v1
```

**Benefits:**
- ✅ Clear error message
- ✅ Suggests valid alternatives
- ✅ Helps catch typos
- ✅ Improves developer experience

### 7. Module Integration

Updated `adaptive/__init__.py` to export all exceptions:

```python
from .exceptions import (
    AdaptiveError,
    CircuitBreakerError,
    ContextExtractionError,
    LearningError,
    PerformanceRegressionError,
    StrategyAdaptationError,
    StrategyNotFoundError,
    StrategyValidationError,
    ValidationWindowError,
)

__all__ = [
    # Core classes
    "AdaptivePrimitive",
    "AdaptiveRetryPrimitive",
    "LearningStrategy",
    "StrategyMetrics",
    "LearningMode",
    # Custom exceptions
    "AdaptiveError",
    "LearningError",
    "StrategyValidationError",
    "StrategyAdaptationError",
    "CircuitBreakerError",
    "ContextExtractionError",
    "StrategyNotFoundError",
    "ValidationWindowError",
    "PerformanceRegressionError",
]
```

---

## 📊 Usage Examples

### Basic Error Handling

```python
from tta_dev_primitives.adaptive import (
    AdaptiveRetryPrimitive,
    LearningError,
    CircuitBreakerError,
)

try:
    result = await adaptive_retry.execute(data, context)
except CircuitBreakerError as e:
    logger.warning(f"Circuit breaker active: {e}")
    # Use fallback strategy
    result = await fallback_primitive.execute(data, context)
except LearningError as e:
    logger.error(f"Learning failed: {e}")
    # Continue with baseline strategy
    result = await baseline_primitive.execute(data, context)
```

### Catching All Adaptive Errors

```python
from tta_dev_primitives.adaptive import AdaptiveError

try:
    result = await adaptive_workflow.execute(data, context)
except AdaptiveError as e:
    # Catch all adaptive primitive errors
    logger.error(f"Adaptive primitive error: {e}")
    # Fallback to non-adaptive workflow
    result = await standard_workflow.execute(data, context)
```

### Detailed Error Handling

```python
from tta_dev_primitives.adaptive import (
    StrategyValidationError,
    PerformanceRegressionError,
    StrategyNotFoundError,
)

try:
    result = await adaptive_primitive.execute(data, context)
except PerformanceRegressionError as e:
    logger.warning(
        f"Strategy {e.strategy_name} regression: "
        f"{e.metric_name}={e.strategy_value:.3f} < baseline={e.baseline_value:.3f}"
    )
    # Revert to baseline
except StrategyNotFoundError as e:
    logger.error(
        f"Strategy '{e.strategy_name}' not found. "
        f"Available: {e.available_strategies}"
    )
    # Use default strategy
except StrategyValidationError as e:
    logger.warning(f"Validation failed: {e}")
    # Continue validation
```

---

## 🎯 Error Handling Best Practices

### 1. Catch Specific Exceptions First

```python
try:
    result = await adaptive_primitive.execute(data, context)
except PerformanceRegressionError as e:
    # Handle specific case
    logger.warning(f"Performance regression: {e}")
except StrategyValidationError as e:
    # Handle validation errors
    logger.error(f"Validation failed: {e}")
except LearningError as e:
    # Handle general learning errors
    logger.error(f"Learning error: {e}")
except AdaptiveError as e:
    # Catch-all for other adaptive errors
    logger.error(f"Adaptive error: {e}")
```

### 2. Preserve Circuit Breaker State

```python
try:
    result = await adaptive_primitive.execute(data, context)
except CircuitBreakerError as e:
    # Don't retry when circuit breaker is active
    logger.warning(f"Circuit breaker: {e}")
    if e.cooldown_seconds:
        logger.info(f"Retry after {e.cooldown_seconds}s")
    # Use fallback immediately
    result = await fallback.execute(data, context)
```

### 3. Log Context for Debugging

```python
try:
    result = await adaptive_primitive.execute(data, context)
except AdaptiveError as e:
    logger.error(
        "Adaptive primitive failed",
        extra={
            "error_type": type(e).__name__,
            "error_message": str(e),
            "context_id": context.correlation_id,
            "strategy_count": len(adaptive_primitive.strategies),
        }
    )
    raise
```

### 4. Graceful Degradation

```python
def execute_with_fallback(data, context):
    try:
        # Try adaptive primitive
        return await adaptive_primitive.execute(data, context)
    except CircuitBreakerError:
        # Circuit breaker active - use baseline
        logger.warning("Using baseline due to circuit breaker")
        return await baseline_primitive.execute(data, context)
    except LearningError:
        # Learning failed - continue with existing strategies
        logger.warning("Learning disabled - using existing strategies")
        adaptive_primitive.learning_mode = LearningMode.DISABLED
        return await adaptive_primitive.execute(data, context)
    except AdaptiveError:
        # Any other adaptive error - fallback to simple implementation
        logger.error("Adaptive primitive failed - using simple fallback")
        return await simple_primitive.execute(data, context)
```

---

## 📈 Impact Summary

### Code Quality

| Aspect | Before | After |
|--------|--------|-------|
| Exception handling | Generic Exception | Domain-specific exceptions |
| Error messages | Basic strings | Structured with context |
| Debugging | Difficult to trace | Clear error categories |
| Testing | Hard to test errors | Easy to mock/test specific exceptions |

### Developer Experience

**Before:**
```python
except Exception as e:  # What kind of error?
    logger.error(f"Error: {e}")  # Not enough context
    # Hard to decide what to do
```

**After:**
```python
except PerformanceRegressionError as e:
    logger.warning(f"Regression in {e.metric_name}")
    # Clear action: revert to baseline
except CircuitBreakerError as e:
    logger.info(f"Cooldown: {e.cooldown_seconds}s")
    # Clear action: wait or use fallback
```

### Error Recovery

- ✅ **Specific error types** enable targeted recovery strategies
- ✅ **Structured error data** provides debugging context
- ✅ **Clear error messages** reduce investigation time
- ✅ **Exception hierarchy** enables catch-all handling

---

## 🔍 Testing Considerations

### Testing Exception Raising

```python
import pytest
from tta_dev_primitives.adaptive import (
    PerformanceRegressionError,
    StrategyNotFoundError,
)

def test_performance_regression_error():
    with pytest.raises(PerformanceRegressionError) as exc_info:
        raise PerformanceRegressionError(
            strategy_name="test_strategy",
            metric_name="success_rate",
            strategy_value=0.75,
            baseline_value=0.90
        )

    err = exc_info.value
    assert err.strategy_name == "test_strategy"
    assert err.metric_name == "success_rate"
    assert err.strategy_value == 0.75
    assert err.baseline_value == 0.90
    assert "performance regression" in str(err).lower()

def test_strategy_not_found_helpful_message():
    with pytest.raises(StrategyNotFoundError) as exc_info:
        raise StrategyNotFoundError(
            "missing_strategy",
            available_strategies=["baseline", "prod_v1"]
        )

    err = exc_info.value
    assert "missing_strategy" in str(err)
    assert "baseline" in str(err)
    assert "prod_v1" in str(err)
```

### Testing Error Handling

```python
async def test_circuit_breaker_error_handling(adaptive_primitive):
    # Force circuit breaker activation
    adaptive_primitive.circuit_breaker_active = True

    with pytest.raises(CircuitBreakerError) as exc_info:
        await adaptive_primitive.execute(data, context)

    err = exc_info.value
    assert err.failure_rate is not None
    assert err.cooldown_seconds is not None
```

---

## 🚀 Next Steps

### Immediate

1. ✅ **Custom Exceptions** - COMPLETE (this phase)
2. **Prometheus Metrics** - Next phase
   - Create `adaptive/metrics.py`
   - Define learning-specific metrics
   - Integrate with observability layer

### Future Integration

3. **Update base.py** - Use custom exceptions
   - Replace generic exceptions with custom ones
   - Add proper error context
   - Improve error messages

4. **Update retry.py** - Use custom exceptions
   - Strategy validation error handling
   - Circuit breaker integration
   - Context extraction error handling

5. **Integration Tests** - Test exception handling
   - Test each exception type
   - Test error recovery strategies
   - Test exception propagation

---

## 📚 Related Documentation

- [Adaptive Primitives README](../packages/tta-dev-primitives/src/tta_dev_primitives/adaptive/README.md)
- [Type Annotations Enhancement](./TYPE_ANNOTATIONS_ENHANCEMENT_COMPLETE.md)
- [Integration Tests Status](./INTEGRATION_TESTS_CURRENT_STATUS.md)
- [Python Exception Handling](https://docs.python.org/3/tutorial/errors.html)

---

**Phase 3 Custom Exceptions: ✅ COMPLETE**
**Next Phase: Prometheus Metrics**
**Created:** 2025-11-07
**Last Updated:** 2025-11-07
