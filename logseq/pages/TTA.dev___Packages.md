type:: [[Index]]
description:: Overview of all TTA.dev packages

# TTA.dev Packages

## Core Packages

### [[tta-dev-primitives]]
- **Path:** `platform/primitives/`
- **Description:** Core workflow primitives for composable AI applications
- **Key Features:**
  - Sequential/Parallel composition with `>>` and `|` operators
  - Recovery primitives (Retry, Fallback, Timeout, CircuitBreaker)
  - Performance primitives (Cache, Memory)
  - Type-safe with full Python type hints

### [[tta-observability-integration]]
- **Path:** `platform/observability/`
- **Description:** OpenTelemetry integration for distributed tracing
- **Key Features:**
  - Automatic span creation
  - Prometheus metrics export
  - Structured logging
  - Context propagation

### [[universal-agent-context]]
- **Path:** `platform/agent-context/`
- **Description:** Agent context management and propagation
- **Key Features:**
  - Workflow context with trace IDs
  - Correlation ID propagation
  - Metadata management

## Package Architecture

```
platform/
├── primitives/           # tta-dev-primitives
│   └── src/tta_dev_primitives/
├── observability/        # tta-observability-integration
│   └── src/tta_observability_integration/
└── agent-context/        # universal-agent-context
    └── src/universal_agent_context/
```

## Related Pages
- [[TTA.dev/Primitives]] - Detailed primitives catalog
- [[TTA.dev/Architecture]] - System architecture
