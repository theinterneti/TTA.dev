type:: primitive
category:: Observability
status:: documented
generated:: 2025-12-04

# ObservablePrimitive

**Source:** `platform/primitives/src/tta_dev_primitives/observability/tracing.py`

## Overview

Wrapper adding observability to any primitive.

Provides:
- Distributed tracing with OpenTelemetry
- Structured logging with correlation IDs
- Metrics collection

## Usage Example

```python
workflow = (
        ObservablePrimitive(input_proc, "input_processing") >>
        ObservablePrimitive(world_build, "world_building") >>
        ObservablePrimitive(narrative_gen, "narrative_generation")
    )
```

## Related

- [[TTA.dev/Primitives]] - Primitives index
- [[TTA.dev/Primitives/Observability]] - Observability primitives
