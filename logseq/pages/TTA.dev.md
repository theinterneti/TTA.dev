alias:: TTA, TTA.dev
type:: [[Project]]
status:: active
description:: Production-ready AI development toolkit with composable workflow primitives

# TTA.dev Knowledge Base

Welcome to the TTA.dev knowledge base. This is the central hub for documentation, learning resources, and project management.

## Quick Navigation

- [[TTA.dev/Packages]] - Core packages documentation
- [[TTA.dev/Primitives]] - Workflow primitives catalog
- [[TTA.dev/Architecture]] - System design and patterns
- [[TTA.dev/TODOs]] - Task tracking dashboard
- [[TTA.dev/Learning Paths]] - Structured learning sequences

## Core Packages

| Package | Description | Status |
|---------|-------------|--------|
| [[tta-dev-primitives]] | Core workflow primitives | ✅ Production |
| [[tta-observability-integration]] | OpenTelemetry integration | ✅ Production |
| [[universal-agent-context]] | Agent context management | ✅ Production |

## Key Concepts

- **Primitives** - Composable building blocks for AI workflows
- **Composition** - Chain primitives with `>>` (sequential) or `|` (parallel)
- **Observability** - Built-in tracing with OpenTelemetry
- **Recovery** - Retry, fallback, timeout, and circuit breaker patterns

## Getting Started

```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.recovery import RetryPrimitive
from tta_dev_primitives.performance import CachePrimitive

workflow = CachePrimitive(ttl=3600) >> RetryPrimitive(max_retries=3) >> process
result = await workflow.execute(data, WorkflowContext())
```

## Resources

- [GitHub Repository](https://github.com/theinterneti/TTA.dev)
- [PRIMITIVES_CATALOG.md](../PRIMITIVES_CATALOG.md)
- [GETTING_STARTED.md](../GETTING_STARTED.md)
