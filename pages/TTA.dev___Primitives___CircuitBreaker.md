type:: primitive
category:: Recovery
status:: documented
generated:: 2025-12-04

# CircuitBreaker

**Source:** `platform/primitives/src/tta_dev_primitives/recovery/circuit_breaker.py`

## Overview

Circuit breaker pattern for preventing cascading failures.

## Tips & Gotchas

- ⚠️ Circuit stays open for `reset_timeout` seconds
- 💡 Monitor circuit state via metrics
- 📝 Half-open state allows one test request

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Recovery]] - Recovery primitives
