type:: primitive
category:: Adaptive
status:: documented
generated:: 2025-12-04

# AdaptiveTimeoutPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/adaptive/timeout.py`

## Overview

Adaptive timeout primitive that learns optimal timeout values from execution patterns.

Learns from:
- Latency percentiles (p50, p95, p99)
- Success/failure patterns
- Context-specific execution times
- Timeout occurrences

Parameters learned:
- timeout_ms: Optimal timeout value
- buffer_factor: Multiplier for percentile (e.g., 1.5x p95)
- percentile_target: Which percentile to target (50, 95, 99)



Scoring formula:
- 60% success rate (minimize timeouts)
- 40% headroom (balance between tight and loose timeouts)

## Usage Example

```python
from tta_dev_primitives.adaptive import (
        AdaptiveTimeoutPrimitive,
        LearningMode
    )

    # Create adaptive timeout that learns optimal values
    adaptive_timeout = AdaptiveTimeoutPrimitive(
        target_primitive=slow_api_call,
        learning_mode=LearningMode.ACTIVE,
        min_observations_before_learning=20
    )

    # Execute - learns from latency patterns
    result = await adaptive_timeout.execute(data, context)

    # Check learned timeouts
    stats = adaptive_timeout.get_timeout_stats()
    print(f"Learned timeout: {stats['current_timeout_ms']}ms")
    print(f"P95 latency: {stats['p95_latency_ms']}ms")
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Adaptive]] - Adaptive primitives
