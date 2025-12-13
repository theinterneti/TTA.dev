# TTA.dev

type:: [[Meta-Project]]
category:: [[Project Hub]]
status:: [[Active]]
visibility:: [[Public]]
repository:: https://github.com/theinterneti/TTA.dev

---

## 🎯 Overview

- id:: tta-dev-overview
  TTA.dev is a production-ready AI development toolkit providing composable agentic primitives for building reliable AI workflows.

  **Core Value:** Transform complex async orchestration into simple, composable workflow patterns with built-in observability.

---

## 📦 Packages

### Core Packages

- [[TTA.dev/Packages/tta-dev-primitives]] - Core workflow primitives
- [[TTA.dev/Packages/tta-observability-integration]] - OpenTelemetry + Prometheus
- [[TTA.dev/Packages/universal-agent-context]] - Agent coordination
- [[TTA.dev/Packages/keploy-framework]] - API testing framework
- [[TTA.dev/Packages/python-pathway]] - Python analysis utilities

### Package Overview Table

logseq.table.version:: 2
logseq.table.hover:: row
logseq.table.stripes:: true

| Package | Purpose | Status | Version |
|---------|---------|--------|---------|
| [[TTA.dev/Packages/tta-dev-primitives]] | Core workflow primitives | [[Stable]] | 1.0.0 |
| [[TTA.dev/Packages/tta-observability-integration]] | OpenTelemetry + Prometheus | [[Stable]] | 0.2.0 |
| [[TTA.dev/Packages/universal-agent-context]] | Agent coordination | [[Experimental]] | 0.1.0 |
| [[TTA.dev/Packages/keploy-framework]] | API testing | [[Stable]] | 0.1.0 |
| [[TTA.dev/Packages/python-pathway]] | Python analysis | [[Experimental]] | 0.1.0 |

---

## 🧱 Primitives

### Core Workflow Primitives

- [[TTA.dev/Primitives/WorkflowPrimitive]] - Base class for all primitives
- [[TTA.dev/Primitives/SequentialPrimitive]] - Execute steps in sequence
- [[TTA.dev/Primitives/ParallelPrimitive]] - Execute steps in parallel
- [[TTA.dev/Primitives/ConditionalPrimitive]] - Conditional branching
- [[TTA.dev/Primitives/RouterPrimitive]] - Dynamic routing

### Recovery Primitives

- [[TTA.dev/Primitives/RetryPrimitive]] - Retry with exponential backoff
- [[TTA.dev/Primitives/FallbackPrimitive]] - Graceful degradation
- [[TTA.dev/Primitives/TimeoutPrimitive]] - Circuit breaker pattern
- [[TTA.dev/Primitives/CompensationPrimitive]] - Saga pattern for rollback

### Performance Primitives

- [[TTA.dev/Primitives/CachePrimitive]] - LRU + TTL caching

### Testing Primitives

- [[TTA.dev/Primitives/MockPrimitive]] - Testing and mocking

### All Primitives Query

{{query (page-property type [[Primitive]])}}

---

## 📚 Documentation

### Getting Started

- [[TTA.dev/Guides/Getting Started]]
- [[TTA.dev/Guides/Beginner Quickstart]]
- [[TTA.dev/Guides/First Workflow]]

### Core Concepts

- [[TTA.dev/Guides/Agentic Primitives]]
- [[TTA.dev/Guides/Workflow Composition]]
- [[TTA.dev/Guides/Context Management]]
- [[TTA.dev/Guides/Observability]]

### How-To Guides

- [[TTA.dev/Guides/How-To/Build LLM Router]]
- [[TTA.dev/Guides/How-To/Add Retry Logic]]
- [[TTA.dev/Guides/How-To/Implement Caching]]
- [[TTA.dev/Guides/How-To/Set Up Tracing]]

### Decision Guides

- [[TTA.dev/Guides/Decisions/LLM Selection]]
- [[TTA.dev/Guides/Decisions/Database Selection]]
- [[TTA.dev/Guides/Decisions/Cost Optimization]]

### Prerequisites (Embedded from Common)

{{embed ((prerequisites-full))}}

---

## 🎯 Active Tasks

### Current Sprint

{{query (and (task TODO DOING) (between [[2025-10-28]] [[2025-11-03]]))}}

### Recently Completed

{{query (and (task DONE) (between -7d today))}}

### Blocked Items

{{query (and (task TODO) (property blocked true))}}

---

## 📊 Metrics & Status

### Documentation Coverage

- **Total Primitives:** {{query (page-property type [[Primitive]])}}
- **Total Examples:** {{query (page-property type [[Example]])}}
- **Total Guides:** {{query (page-property type [[Guide]])}}

### Quality Status

- **Stable Primitives:** {{query (and (page-property type [[Primitive]]) (page-property status [[Stable]]))}}
- **Experimental:** {{query (and (page-property type [[Primitive]]) (page-property status [[Experimental]]))}}
- **High Test Coverage (>90%):** {{query (and (page-property type [[Primitive]]) (property test-coverage >= 90))}}

---

## 🏗️ Architecture

### Architecture Decision Records

- [[TTA.dev/Architecture/ADR/001 - Operator Overloading]]
- [[TTA.dev/Architecture/ADR/002 - WorkflowContext Design]]
- [[TTA.dev/Architecture/ADR/003 - Observability Integration]]

### Design Patterns

- [[TTA.dev/Architecture/Patterns/Sequential Composition]]
- [[TTA.dev/Architecture/Patterns/Parallel Execution]]
- [[TTA.dev/Architecture/Patterns/Error Recovery]]

---

## 🔗 Quick Access

- [[TTA.dev/Agents]] - AI agent instructions and coordination
- [[TTA.dev/Primitives]] - Full primitives catalog
- [[TTA.dev/Examples]] - Working code examples
- [[Templates]] - Page templates for new content
- [[TTA.dev/Common]] - Reusable content blocks
- [[TTA.dev/Development]] - Development workflows

---

## 🚀 External Links

- **Repository:** https://github.com/theinterneti/TTA.dev
- **Documentation:** https://github.com/theinterneti/TTA.dev/tree/main/docs
- **Issues:** https://github.com/theinterneti/TTA.dev/issues
- **Pull Requests:** https://github.com/theinterneti/TTA.dev/pulls

---

## 📝 Meta

**Created:** [[2025-10-30]]
**Last Updated:** [[2025-10-30]]
**Maintained By:** TTA.dev Team

- [[Project Hub]]

---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev]]
