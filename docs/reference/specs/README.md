# TTA.dev Specifications Index

This directory contains **formal Spec-Driven Development (SDD) specifications** for TTA.dev.
Specifications act as the single source of truth and contract for both human developers and AI agents.

## Directory Structure

```
specs/
├── README.md                          # This file — index and SDD guide
├── primitives/                        # Per-primitive contracts
│   ├── workflow-primitive.spec.md     # Base class + WorkflowContext
│   ├── sequential-primitive.spec.md   # Sequential composition
│   ├── parallel-primitive.spec.md     # Parallel composition
│   ├── router-primitive.spec.md       # Dynamic routing
│   ├── retry-primitive.spec.md        # Retry with backoff
│   ├── fallback-primitive.spec.md     # Primary/fallback pattern
│   ├── timeout-primitive.spec.md      # Timeout enforcement
│   ├── cache-primitive.spec.md        # Result caching
│   ├── memory-primitive.spec.md       # Conversational memory
│   └── compensation-primitive.spec.md # Saga/compensation pattern
├── observability/                     # Trace & metric contracts
│   ├── span-schema.spec.md           # OpenTelemetry span definitions
│   ├── metrics-catalog.spec.md       # Prometheus & OTel metrics
│   └── context-propagation.spec.md   # W3C trace context propagation
└── packages/                          # Package-level contracts
    ├── skill-registry.spec.md         # Skill discovery & registration
    └── integration-tests.spec.md      # Cross-package integration test contracts
```

## SDD Phases

Every specification in this directory follows a strict separation of concerns:

| Phase | Contains | Does NOT Contain |
|-------|----------|------------------|
| **Specify** (What) | Functional requirements, contracts, invariants, error behaviors | Architecture decisions, technology choices |
| **Plan** (How) | Lives in `docs/architecture/` | N/A for this directory |
| **Implement** (Build) | Lives in `platform/` source code | N/A for this directory |

## Spec Template

All specifications MUST follow this template structure. Use RFC 2119 keywords
(MUST, MUST NOT, SHOULD, SHOULD NOT, MAY) for normative requirements.

```markdown
# {Primitive Name} Specification

- **Version:** x.y.z
- **Status:** Draft | Review | Approved
- **Package:** tta-dev-primitives | tta-observability-integration | etc.
- **Source:** platform/{package}/src/.../{file}.py

## 1. Purpose

One-paragraph functional description of what this primitive does and why it exists.

## 2. Contract

### 2.1 Type Signature
Python class/function signature with Generic type parameters.

### 2.2 Constructor Parameters
Table of all parameters with types, defaults, and descriptions.

### 2.3 Behavior Invariants
Normative requirements using MUST/SHOULD/MAY:
- The primitive MUST ...
- The primitive MUST NOT ...
- The primitive SHOULD ...

### 2.4 Error Contract
Table of all exceptions with conditions under which they are raised.

### 2.5 Observability Contract
Tables of spans, metrics, and checkpoints emitted.

## 3. Composition Rules

How this primitive interacts with `>>` and `|` operators.

## 4. Edge Cases

Table of edge case inputs and expected behaviors.

## 5. Cross-References

Links to related specs, architecture docs, and test files.
```

## Cross-References

- **Architecture:** [docs/architecture/](../../architecture/) — System design and ADRs
- **Catalog:** [PRIMITIVES_CATALOG.md](../../../PRIMITIVES_CATALOG.md) — Usage examples and API reference
- **Tests:** [platform/primitives/tests/](../../../platform/primitives/tests/) — Test implementations
- **Audit Report:** [SPEC_AUDIT_REPORT.md](../../architecture/SPEC_AUDIT_REPORT.md) — Gap analysis
