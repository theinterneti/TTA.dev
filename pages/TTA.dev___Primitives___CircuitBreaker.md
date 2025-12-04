type:: primitive
category:: Recovery
status:: documented
generated:: 2025-12-04

# CircuitBreaker

**Source:** `platform/primitives/src/tta_dev_primitives/recovery/circuit_breaker.py`

## Overview

Circuit breaker pattern for preventing cascading failures.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Too many failures, requests fail immediately
- HALF_OPEN: Testing if service recovered

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Recovery]] - Recovery primitives
