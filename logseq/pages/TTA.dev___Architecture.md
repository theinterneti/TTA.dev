# TTA.dev Architecture

type:: Namespace
category:: [[Architecture]]
created:: [[2025-10-31]]

---

## Overview

This namespace contains architecture documentation, decision records, and design patterns for TTA.dev.

---

## 📦 Package Architecture

- [[TTA.dev/Packages/tta-dev-primitives]] - Core workflow primitives
- [[TTA.dev/Packages/tta-observability-integration]] - OpenTelemetry + Prometheus
- [[TTA.dev/Packages/universal-agent-context]] - Agent context management

---

## 🏗️ Architecture Decision Records (ADRs)

Migration from `docs/architecture/` in progress:

- TODO [[TTA.dev/Architecture/ADR-001 Primitive Base Class]]
- TODO [[TTA.dev/Architecture/ADR-002 Operator Overloading]]
- TODO [[TTA.dev/Architecture/ADR-003 Context Propagation]]
- TODO [[TTA.dev/Architecture/ADR-004 Observability Integration]]

---

## 🎨 Visual Architecture

### Whiteboards

- TODO [[Whiteboard - Primitive Composition Patterns]]
- TODO [[Whiteboard - Observability Flow]]
- TODO [[Whiteboard - Context Propagation]]
- TODO [[Whiteboard - Recovery Primitive Patterns]]

---

## 🔧 Design Patterns

### Composition Patterns

**Sequential Composition (`>>`):**
```python
workflow = step1 >> step2 >> step3
# Output of step1 → input of step2 → output of step2 → input of step3
```

**Parallel Composition (`|`):**
```python
workflow = branch1 | branch2 | branch3
# All branches receive same input, results collected
```

**Mixed Composition:**
```python
workflow = (
    input_processor >>
    (fast_path | slow_path | cached_path) >>
    aggregator
)
```

### Recovery Patterns

- [[TTA.dev/Primitives/RetryPrimitive]] - Exponential backoff
- [[TTA.dev/Primitives/FallbackPrimitive]] - Graceful degradation
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Circuit breaker
- [[TTA.dev/Primitives/CompensationPrimitive]] - Saga pattern

### Performance Patterns

- [[TTA.dev/Primitives/CachePrimitive]] - LRU + TTL caching
- [[TTA.dev/Primitives/RouterPrimitive]] - Tier-based routing

---

## 📊 System Diagrams

### High-Level Architecture

```
┌─────────────────────────────────────────┐
│  User Application Layer                 │
│  - Custom Primitives                    │
│  - Workflow Composition                 │
└───────────────┬─────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────┐
│  TTA.dev Primitives Layer               │
│  [[TTA Primitives]]                     │
│                                         │
│  ┌──────────┐  ┌──────────┐           │
│  │Sequential│  │ Parallel │           │
│  └──────────┘  └──────────┘           │
│                                         │
│  ┌──────────┐  ┌──────────┐           │
│  │  Retry   │  │ Fallback │           │
│  └──────────┘  └──────────┘           │
└───────────────┬─────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────┐
│  Observability Layer                    │
│  [[TTA.dev/Packages/tta-observability-integration]] │
│  - OpenTelemetry                        │
│  - Prometheus                           │
└─────────────────────────────────────────┘
```

---

## 🔗 Related Pages

- [[TTA.dev]] - Main hub
- [[TTA Primitives]] - All primitives
- [[TTA.dev/Migration Dashboard]] - Progress tracking
- [[TTA.dev/Guides]] - User guides

---

## 📝 Architecture Principles

1. **Composability**: Primitives combine via operators (`>>`, `|`)
2. **Type Safety**: Full type annotations with Python 3.11+ syntax
3. **Observability**: Built-in OpenTelemetry spans and metrics
4. **Testability**: MockPrimitive for easy testing
5. **Recovery**: First-class error handling patterns
6. **Performance**: Caching and routing for optimization

---

**Last Updated:** [[2025-10-31]]
**Status:** In Progress
**Next:** Create whiteboards and migrate ADRs
