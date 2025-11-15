# Adaptive/Self-Improving Primitives

**Primitives that learn from observability data and adapt their behavior over time.**

---

## 🎯 Overview

The adaptive primitives module provides workflow primitives that **learn from execution patterns** and **automatically improve their strategies** while maintaining production safety through circuit breakers and validation.

### Key Innovation

Instead of static configuration, adaptive primitives use **observability data as input** to learn optimal strategies:

```python
from tta_dev_primitives.adaptive import AdaptiveRetryPrimitive, LearningMode

# Traditional retry - static configuration
retry = RetryPrimitive(max_retries=3, backoff_factor=2.0)

# Adaptive retry - learns optimal configuration
adaptive = AdaptiveRetryPrimitive(
    target_primitive=api_call,
    learning_mode=LearningMode.ACTIVE,
    enable_auto_persistence=True
)
# After 50 executions: max_retries=5, backoff_factor=2.5 (learned!)
```

### What Gets Learned

- **Retry strategies**: Optimal retry counts, backoff factors, delays
- **Context patterns**: Different strategies for different contexts (production/staging/dev)
- **Performance characteristics**: Success rates, latencies, error patterns
- **Resource optimization**: Cost-effective strategies based on actual usage

---

## 🏗️ Architecture

### Core Components

```
┌─────────────────────────────────────────────┐
│        AdaptivePrimitive (Base)             │
│  - Strategy selection and management        │
│  - Learning engine                          │
│  - Circuit breakers                         │
│  - Validation system                        │
└──────────────────┬──────────────────────────┘
                   │
     ┌─────────────┼─────────────┐
     │             │             │
     ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Adaptive │  │ Adaptive │  │  Custom  │
│  Retry   │  │  Cache   │  │ Adaptive │
│          │  │ (planned)│  │Primitive │
└──────────┘  └──────────┘  └──────────┘
     │
     │ Persists learned strategies
     ▼
┌─────────────────────────────────────────────┐
│    LogseqStrategyIntegration                │
│  - Knowledge base persistence               │
│  - Strategy pages                           │
│  - Performance tracking                     │
│  - Discovery queries                        │
└─────────────────────────────────────────────┘
```

### Learning Flow

```
1. Execute with Current Strategy
   └─> Collect metrics (success rate, latency, errors)

2. Analyze Performance
   └─> Compare with baseline and other strategies

3. Consider New Strategy? (Learning Mode check)
   ├─> OBSERVE: Log only, don't adapt
   ├─> VALIDATE: Create strategy, validate before use
   └─> ACTIVE: Learn and adopt validated strategies

4. Circuit Breaker Check
   └─> High failure rate? → Fallback to baseline

5. Persist to Logseq (if enabled)
   └─> Create strategy pages and journal entries
```

---

## 🚀 Quick Start

### Basic Usage

```python
from tta_dev_primitives.adaptive import (
    AdaptiveRetryPrimitive,
    LearningMode,
    LogseqStrategyIntegration
)
from tta_dev_primitives.core.base import WorkflowContext

# 1. Setup Logseq integration (optional but recommended)
logseq = LogseqStrategyIntegration("my_service")

# 2. Create adaptive retry
adaptive_retry = AdaptiveRetryPrimitive(
    target_primitive=unreliable_api,
    learning_mode=LearningMode.ACTIVE,
    logseq_integration=logseq,
    enable_auto_persistence=True
)

# 3. Use it - learning happens automatically!
context = WorkflowContext(
    correlation_id="req-123",
    metadata={"environment": "production"}
)
result = await adaptive_retry.execute(api_request, context)

# 4. Check learned strategies
for name, strategy in adaptive_retry.strategies.items():
    print(f"{name}: {strategy.metrics.success_rate:.1%} success")
```

### Custom Adaptive Primitive

```python
from tta_dev_primitives.adaptive import AdaptivePrimitive, LearningMode, LearningStrategy
from tta_dev_primitives.core.base import WorkflowContext

class AdaptiveCachePrimitive(AdaptivePrimitive[dict, dict]):
    """Cache primitive that learns optimal TTL and size."""

    async def _execute_with_strategy(
        self,
        strategy: LearningStrategy,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        """Execute caching with learned strategy."""
        ttl = strategy.parameters.get("ttl", 3600)
        max_size = strategy.parameters.get("max_size", 1000)

        # Use learned TTL and size
        cached_value = await self._cache.get(input_data, ttl=ttl)
        if cached_value:
            return cached_value

        result = await self._expensive_operation(input_data)
        await self._cache.set(input_data, result, ttl=ttl)
        return result

    async def _consider_new_strategy(
        self,
        input_data: dict,
        context: WorkflowContext,
        current_performance: StrategyMetrics
    ) -> LearningStrategy | None:
        """Learn optimal TTL from cache hit rates."""
        cache_hit_rate = await self._get_cache_hit_rate()

        if cache_hit_rate > 0.8:  # High hit rate
            # Increase TTL for better efficiency
            return LearningStrategy(
                name=f"extended_ttl_{int(cache_hit_rate * 100)}",
                description=f"Learned from {cache_hit_rate:.1%} hit rate",
                parameters={
                    "ttl": 7200,  # 2 hours
                    "max_size": 1000
                }
            )
        elif cache_hit_rate < 0.3:  # Low hit rate
            # Decrease TTL to save memory
            return LearningStrategy(
                name=f"reduced_ttl_{int(cache_hit_rate * 100)}",
                description=f"Learned from {cache_hit_rate:.1%} hit rate",
                parameters={
                    "ttl": 1800,  # 30 minutes
                    "max_size": 500
                }
            )

        return None  # No new strategy needed
```

---

## 📚 Core Concepts

### LearningStrategy

Represents a learned configuration with performance tracking:

```python
from tta_dev_primitives.adaptive import LearningStrategy, StrategyMetrics

strategy = LearningStrategy(
    name="production_high_load_v2",
    description="Learned from 50 executions under high load",
    parameters={
        "max_retries": 5,
        "backoff_factor": 2.5,
        "initial_delay": 2.0
    },
    metrics=StrategyMetrics(
        success_rate=0.94,
        avg_latency_ms=1250.5,
        contexts_seen=1
    ),
    validation_window_size=10,
    validation_successes=9
)

# Check if strategy is validated
if strategy.is_validated:
    print(f"Strategy validated with {strategy.metrics.success_rate:.1%} success")
```

### LearningMode

Controls how aggressive the learning is:

```python
from tta_dev_primitives.adaptive import LearningMode

# DISABLED - No learning (production fallback)
adaptive = AdaptivePrimitive(learning_mode=LearningMode.DISABLED)

# OBSERVE - Learn but don't apply (safe testing)
adaptive = AdaptivePrimitive(learning_mode=LearningMode.OBSERVE)

# VALIDATE - Validate before applying (recommended)
adaptive = AdaptivePrimitive(learning_mode=LearningMode.VALIDATE)

# ACTIVE - Learn and apply immediately (use with care)
adaptive = AdaptivePrimitive(learning_mode=LearningMode.ACTIVE)
```

### StrategyMetrics

Tracks performance of each strategy:

```python
from tta_dev_primitives.adaptive import StrategyMetrics

metrics = StrategyMetrics(
    success_rate=0.94,      # 94% success rate
    avg_latency_ms=1250.5,  # Average latency
    contexts_seen=1         # Number of contexts using this
)

# Compare strategies
if metrics.is_better_than(baseline_metrics):
    print("New strategy performs better!")
```

### Circuit Breaker

Automatic fallback on high failure rates:

```python
adaptive = AdaptiveRetryPrimitive(
    target_primitive=api,
    enable_circuit_breaker=True,  # Enable circuit breaker
    circuit_breaker_threshold=0.5  # Trigger at 50% failure rate
)

# If current strategy fails >50% of time:
# → Automatically falls back to baseline
# → Logs circuit breaker activation
# → Continues learning with baseline
```

---

## 🛡️ Safety Mechanisms

### 1. Baseline Fallback

Always have a safe default strategy:

```python
baseline = LearningStrategy(
    name="baseline",
    parameters={"max_retries": 3, "backoff_factor": 2.0}
)

adaptive = AdaptiveRetryPrimitive(
    target_primitive=api,
    baseline_strategy=baseline  # Always available
)
```

### 2. Validation Window

Strategies must prove themselves before adoption:

```python
adaptive = AdaptiveRetryPrimitive(
    target_primitive=api,
    validation_window_size=10  # Must succeed 8/10 times
)
```

### 3. Context Isolation

Strategies don't interfere across contexts:

```python
# Production context gets production-learned strategies
prod_context = WorkflowContext(metadata={"environment": "production"})
await adaptive.execute(data, prod_context)

# Staging context gets staging-learned strategies
staging_context = WorkflowContext(metadata={"environment": "staging"})
await adaptive.execute(data, staging_context)
```

### 4. Minimum Observations

Don't learn from insufficient data:

```python
adaptive = AdaptiveRetryPrimitive(
    target_primitive=api,
    min_observations_before_learning=10  # Need 10+ executions first
)
```

---

## 📊 Logseq Integration

### Automatic Persistence

Learned strategies are automatically saved to Logseq:

```python
from tta_dev_primitives.adaptive import LogseqStrategyIntegration

logseq = LogseqStrategyIntegration("my_service")
adaptive = AdaptiveRetryPrimitive(
    target_primitive=api,
    logseq_integration=logseq,
    enable_auto_persistence=True  # Auto-save on learn
)

# After learning:
# → Creates: logseq/pages/Strategies/my_service_production_v2.md
# → Updates: logseq/journals/YYYY_MM_DD.md
```

### Strategy Pages

Each learned strategy gets a rich Logseq page:

```markdown
# Strategy - my_service_production_v2

**Type:** AdaptiveRetryPrimitive
**Context:** production_high_load
**Created:** 2025-11-07
**Performance:** 94.0% success rate, 1250.5ms avg latency

## Parameters

- max_retries: 5
- backoff_factor: 2.5
- initial_delay: 2.0

## Performance History

| Date | Success Rate | Avg Latency | Observations |
|------|--------------|-------------|--------------|
| 2025-11-07 | 94.0% | 1250.5ms | 50 |

## Related Strategies

{{query (and [[Strategies]] [[my_service]])}}

## Notes

Learned during high-load production scenario.
```

### Discovery Queries

Find related strategies via Logseq:

```clojure
;; Find all strategies for a service
{{query (and [[Strategies]] [[my_service]])}}

;; Find high-performing strategies
{{query (and [[Strategies]] (property success_rate >= 0.9))}}

;; Find recent strategies
{{query (and [[Strategies]] (between -7d today))}}
```

---

## 🎓 Best Practices

### 1. Start Conservative

Begin with OBSERVE mode, graduate to VALIDATE, then ACTIVE:

```python
# Week 1: Observe only
adaptive = AdaptiveRetryPrimitive(learning_mode=LearningMode.OBSERVE)

# Week 2: Validate before applying
adaptive = AdaptiveRetryPrimitive(learning_mode=LearningMode.VALIDATE)

# Week 3+: Active learning (if validated strategies work well)
adaptive = AdaptiveRetryPrimitive(learning_mode=LearningMode.ACTIVE)
```

### 2. Use Context for Isolation

Different contexts should learn separately:

```python
context = WorkflowContext(
    correlation_id=request_id,
    metadata={
        "environment": "production",  # Context key
        "priority": "high",           # Context key
        "service": "api-gateway"      # Context key
    }
)
```

### 3. Enable Logseq Persistence

Always persist strategies for knowledge sharing:

```python
logseq = LogseqStrategyIntegration("service_name")
adaptive = AdaptiveRetryPrimitive(
    logseq_integration=logseq,
    enable_auto_persistence=True  # Critical for sharing
)
```

### 4. Monitor Learning

Check OpenTelemetry traces for learning events:

```python
# Traces show:
# - adaptive.strategy_selected
# - adaptive.new_strategy_considered
# - adaptive.strategy_validated
# - adaptive.circuit_breaker_triggered
```

### 5. Review Learned Strategies

Periodically check what was learned:

```python
for name, strategy in adaptive.strategies.items():
    print(f"{name}:")
    print(f"  Success Rate: {strategy.metrics.success_rate:.1%}")
    print(f"  Avg Latency: {strategy.metrics.avg_latency_ms:.1f}ms")
    print(f"  Validated: {strategy.is_validated}")
```

---

## 🔍 Observability

### OpenTelemetry Traces

All learning events are traced:

```python
# Span: adaptive.execute
#   Attribute: strategy_name = "production_v2"
#   Attribute: learning_mode = "VALIDATE"
#   Event: strategy_selected (baseline | learned)
#   Event: new_strategy_considered
#   Event: strategy_validated
#   Event: circuit_breaker_triggered
```

### Structured Logging

Rich logging for debugging:

```python
logger.info(
    "Strategy learned",
    extra={
        "strategy_name": "production_v2",
        "success_rate": 0.94,
        "observations": 50,
        "context": "production_high_load"
    }
)
```

---

## 📖 Examples

### Example 1: Automatic Learning Demo

**File:** `examples/auto_learning_demo.py`

Shows complete automatic learning and persistence with zero manual intervention.

### Example 2: Verification Suite

**File:** `examples/verify_adaptive_primitives.py`

Comprehensive test suite with 5 tests:
- Basic learning
- Context awareness
- Performance improvement
- Logseq persistence
- Observability integration

### Example 3: Production Demo

**File:** `examples/production_adaptive_demo.py`

Multi-region API simulation showing real-world usage with different failure patterns per region.

### Example 4: Logseq Integration Demo

**File:** `examples/adaptive_logseq_integration_demo.py`

Complete demonstration of knowledge base integration, strategy pages, and discovery queries.

---

## 🚧 Extending

### Creating Custom Adaptive Primitives

1. **Extend AdaptivePrimitive**
2. **Implement _execute_with_strategy()**
3. **Implement _consider_new_strategy()**

```python
from tta_dev_primitives.adaptive import AdaptivePrimitive, LearningStrategy

class MyAdaptivePrimitive(AdaptivePrimitive[InputType, OutputType]):
    async def _execute_with_strategy(
        self,
        strategy: LearningStrategy,
        input_data: InputType,
        context: WorkflowContext
    ) -> OutputType:
        # Use strategy.parameters for configuration
        param = strategy.parameters.get("my_param", default_value)
        return await self._do_work(input_data, param)

    async def _consider_new_strategy(
        self,
        input_data: InputType,
        context: WorkflowContext,
        current_performance: StrategyMetrics
    ) -> LearningStrategy | None:
        # Analyze performance and decide if new strategy needed
        if current_performance.success_rate < 0.8:
            return LearningStrategy(
                name="improved_strategy",
                parameters={"my_param": optimized_value}
            )
        return None
```

---

## 🧪 Testing

### Unit Tests

```python
import pytest
from tta_dev_primitives.adaptive import AdaptiveRetryPrimitive, LearningMode

@pytest.mark.asyncio
async def test_learning():
    adaptive = AdaptiveRetryPrimitive(
        target_primitive=mock_api,
        learning_mode=LearningMode.ACTIVE
    )

    # Execute multiple times
    for i in range(20):
        await adaptive.execute(data, context)

    # Check learning happened
    assert len(adaptive.strategies) > 1  # More than baseline
```

### Integration Tests

See `examples/verify_adaptive_primitives.py` for comprehensive test suite.

---

## 📦 API Reference

### AdaptivePrimitive

```python
class AdaptivePrimitive[TInput, TOutput](InstrumentedPrimitive):
    def __init__(
        self,
        baseline_strategy: LearningStrategy,
        learning_mode: LearningMode = LearningMode.VALIDATE,
        validation_window_size: int = 10,
        min_observations_before_learning: int = 5,
        enable_circuit_breaker: bool = True,
        circuit_breaker_threshold: float = 0.5
    )

    async def execute(
        self,
        input_data: TInput,
        context: WorkflowContext
    ) -> TOutput
```

### AdaptiveRetryPrimitive

```python
class AdaptiveRetryPrimitive(AdaptivePrimitive[TInput, TOutput]):
    def __init__(
        self,
        target_primitive: WorkflowPrimitive[TInput, TOutput],
        learning_mode: LearningMode = LearningMode.VALIDATE,
        logseq_integration: LogseqStrategyIntegration | None = None,
        enable_auto_persistence: bool = False,
        **kwargs
    )
```

### LogseqStrategyIntegration

```python
class LogseqStrategyIntegration:
    def __init__(
        self,
        service_name: str,
        logseq_base_path: Path = Path("logseq")
    )

    async def save_learned_strategy(
        self,
        strategy: LearningStrategy,
        primitive_type: str,
        context: str,
        notes: str | None = None
    ) -> Path

    async def update_strategy_performance(
        self,
        strategy_name: str,
        new_metrics: StrategyMetrics
    )
```

---

## 🔗 Related Documentation

- [ADAPTIVE_PRIMITIVES_VERIFICATION_COMPLETE.md](../../../../../ADAPTIVE_PRIMITIVES_VERIFICATION_COMPLETE.md) - Complete verification report
- [ADAPTIVE_PRIMITIVES_AUDIT.md](../../../../../ADAPTIVE_PRIMITIVES_AUDIT.md) - System audit
- [ADAPTIVE_PRIMITIVES_IMPROVEMENTS.md](../../../../../ADAPTIVE_PRIMITIVES_IMPROVEMENTS.md) - Improvements summary
- [AGENTS.md](../../../../../AGENTS.md) - Agent instructions
- [PRIMITIVES_CATALOG.md](../../../../../PRIMITIVES_CATALOG.md) - Complete catalog

---

**Version:** 0.1.0
**Status:** Production Ready ✅
**Last Updated:** November 7, 2025
