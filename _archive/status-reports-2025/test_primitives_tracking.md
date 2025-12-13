# Test file for primitives-based tracking

This file will trigger the TTA.dev primitives-based agent activity tracker.

Each modification should create:
1. OpenTelemetry spans in Jaeger
2. Prometheus metrics
3. Structured logs with correlation IDs

## Expected Workflow Execution

```
validate_file_event
  └─> classify_file_type
      └─> emit_metrics
          └─> manage_session
```


---
**Logseq:** [[TTA.dev/_archive/Status-reports-2025/Test_primitives_tracking]]
