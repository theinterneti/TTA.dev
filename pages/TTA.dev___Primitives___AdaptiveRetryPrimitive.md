type:: primitive
category:: Adaptive
status:: documented
generated:: 2025-12-04

# AdaptiveRetryPrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/adaptive/retry.py`

## Overview

Retry primitive that learns optimal retry strategies from execution patterns.

This primitive demonstrates self-improvement by:
- Learning which retry parameters work best for different error types
- Adapting strategies based on observability data (success rates, latencies)
- Using context awareness to apply different strategies in different environments
- Maintaining safety with circuit breakers and strategy validation

Key Learning Inputs from Observability:
- Error types and frequencies from spans/logs
- Success/failure patterns by retry count
- Latency distributions for different backoff strategies
- Resource usage patterns during retries
- Context patterns (environment, priority, error types)

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Adaptive]] - Adaptive primitives
