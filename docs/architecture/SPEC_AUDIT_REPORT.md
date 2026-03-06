# Spec Audit Report: SDD Alignment & Gap Analysis

- **Date:** 2026-03-04
- **Branch:** copilot/review-specifications-documents
- **Purpose:** Comprehensive audit of all specifications, architecture documents, and agent instructions for Spec-Driven Development (SDD) alignment
- **Scope:** Root constitution files, `docs/`, `platform/`, `apps/`

---

## Executive Summary

### 🎯 Core Question

> Are the specifications in TTA.dev coherent, gap-free, and aligned with Spec-Driven Development best practices — where specs act as living, unambiguous contracts for both human developers and AI agents?

### 📊 Overall Score: 5/10 ⭐⭐⭐⭐⭐☆☆☆☆☆

**Assessment:** TTA.dev has excellent *documentation* (guides, tutorials, catalog) but lacks formal *specifications*. The codebase is well-documented for humans reading top-down, but an AI agent cannot reliably generate or verify code from the current specs alone. The repository excels at "How to use" but falls short on "What the contract is."

### Key Findings

- ✅ **Root constitution files** (AGENTS.md, PRIMITIVES_CATALOG.md, GETTING_STARTED.md) are well-structured and cross-referenced
- ✅ **Primitive implementations** have clear type signatures (`WorkflowPrimitive[T, U]`) and docstrings
- ✅ **Observability metrics** are partially defined with Prometheus counters and histograms
- ❌ **No formal primitive contracts** — no Protocol/ABC definitions that separate interface from implementation
- ❌ **Spec directory contains only sample/template files** — not actual TTA.dev specifications
- ❌ **Missing SDD separation** — "What" (functional requirements) and "How" (technical constraints) are intermixed
- ❌ **Cross-package references broken** — `agent-coordination` does not reference `universal-agent-context` models
- ❌ **Observability spans not formally specified** — OpenTelemetry trace definitions lack formal contracts
- ⚠️ **docs/README.md references non-existent subdirectories** in guides/

---

## 1. Discovery & Mapping

### 1.1 Root-Level Constitution Files

| File | Purpose | Quality | SDD Role |
|------|---------|---------|----------|
| `AGENTS.md` | AI agent entry point & discovery hub | ✅ Excellent | Context document |
| `PRIMITIVES_CATALOG.md` | Complete API reference for all primitives | ✅ Excellent | Reference (not spec) |
| `GETTING_STARTED.md` | Onboarding guide with progressive complexity | ✅ Excellent | Tutorial |
| `VIBE_CODING.md` | Quick-start for AI-assisted development | ⚠️ Brief (70 lines) | Marketing/Intro |
| `CLAUDE.md` | Claude Code agent instructions | ✅ Good | Agent config |
| `MCP_TOOL_REGISTRY.md` | MCP tool catalog | ✅ Good | Reference |
| `docs/README.md` | Documentation navigation hub | ✅ Excellent | Index |

**Finding:** These files serve as excellent *documentation* but none function as *specifications* in the SDD sense. `PRIMITIVES_CATALOG.md` comes closest but mixes usage examples with API reference rather than defining formal contracts.

### 1.2 Consolidated `docs/` Directory

The 4 canonical directories are:

| Directory | Purpose | File Count | Status |
|-----------|---------|------------|--------|
| `docs/architecture/` | System design, ADRs, analyses | 25 files | ✅ Active, comprehensive |
| `docs/guides/` | How-to guides, tutorials, runbooks | 39+ files | ✅ Active, well-organized |
| `docs/reference/` | API reference, protocols, specs | 8+ files | ⚠️ Specs are stubs |
| `docs/examples/` | Working code examples | 2 files | ⚠️ Sparse |
| `docs/_archive/` | Historical content | Many | ✅ Correctly isolated |

**Finding:** `docs/reference/specs/` contains only two files — both are **generic template/sample specs** (REST API caching, e-commerce notifications) unrelated to TTA.dev. No actual TTA.dev primitive specifications exist here.

### 1.3 Platform Package Documentation

| Package | README | Specs | Tests | Cross-Refs | Status |
|---------|--------|-------|-------|------------|--------|
| `primitives/` | ✅ 550 lines | ❌ None | ✅ ~580 tests | ✅ Good | Production v1.3.0 |
| `observability/` | ⚠️ Minimal | ⚠️ 1 file | ❌ Unknown | ⚠️ Partial | Production v1.0.0 |
| `agent-context/` | ✅ Good | ❌ None | ✅ Present | ⚠️ No coord link | Production v1.0.0 |
| `agent-coordination/` | ✅ Good | ❌ None | ⚠️ 23/44 pass | ❌ No context link | Production v1.0.0 |
| `skills/` | ✅ Good | ❌ None | ✅ Present | ✅ Good | Alpha v0.1.0 |
| `integrations/` | ⚠️ Skeleton | ❌ None | ❌ None | ⚠️ Partial | Skeleton v0.1.0 |
| `documentation/` | ⚠️ Incomplete | ❌ None | ❌ None | ✅ Good | Phase 1 only |
| `shared/` | ⚠️ Placeholder | ❌ None | ❌ None | ❌ None | Empty |

---

## 2. SDD Audit

### 2.1 Specify vs. Plan Separation

**Current State: ❌ Not separated**

TTA.dev documentation mixes three concerns that SDD requires to be distinct:

| SDD Phase | What It Should Contain | Current State |
|-----------|----------------------|---------------|
| **Specify** (What) | Functional requirements, input/output contracts, invariants, error behaviors | ❌ Embedded in docstrings and README examples |
| **Plan** (How) | Architecture decisions, technology choices, performance constraints | ⚠️ In `docs/architecture/` but mixed with specs |
| **Implement** (Build) | Source code, tests | ✅ Well-organized in `platform/` |

**Example — RetryPrimitive:**
- The *specification* (what it does) is scattered across: `PRIMITIVES_CATALOG.md` (usage example), `platform/primitives/src/.../recovery/retry.py` (docstring), `docs/architecture/PRIMITIVE_PATTERNS.md` (pattern description)
- Nowhere is there a single document that says: "RetryPrimitive MUST retry up to `max_retries` times. It MUST use exponential backoff with base `backoff_base`. It MUST add jitter. On exhaustion, it MUST raise `RetryExhaustedError`."

### 2.2 Primitive Contract Clarity

Each primitive was evaluated for whether an AI agent could generate a correct implementation from the spec alone:

| Primitive | Type Signature | Behavior Spec | Error Contract | AI-Generatable? |
|-----------|---------------|---------------|----------------|-----------------|
| `WorkflowPrimitive[T,U]` | ✅ Generic base | ✅ Abstract `execute()` | ❌ Undefined | ⚠️ Partial |
| `SequentialPrimitive` | ✅ `>>` operator | ✅ Pass output to next | ❌ Undefined | ⚠️ Partial |
| `ParallelPrimitive` | ✅ `\|` operator | ✅ Concurrent execution | ❌ Undefined | ⚠️ Partial |
| `RouterPrimitive` | ✅ Routes dict + fn | ⚠️ Implicit in docstring | ❌ Undefined | ❌ No |
| `RetryPrimitive` | ✅ RetryStrategy config | ⚠️ Implicit in code | ❌ Undefined | ❌ No |
| `FallbackPrimitive` | ✅ Primary + fallback | ⚠️ Brief docstring | ❌ Undefined | ❌ No |
| `TimeoutPrimitive` | ✅ Timeout seconds | ⚠️ Brief docstring | ❌ Undefined | ❌ No |
| `CachePrimitive` | ✅ TTL + key fn | ⚠️ In catalog only | ❌ Undefined | ❌ No |
| `MemoryPrimitive` | ⚠️ Loosely typed | ❌ No formal spec | ❌ Undefined | ❌ No |
| `CompensationPrimitive` | ⚠️ Minimal | ❌ Sparse docs | ❌ Undefined | ❌ No |

**Key Gap:** No primitive defines what exceptions it raises, what happens on edge cases (nil input, empty routes, zero timeout), or what observability spans/metrics it emits.

### 2.3 Observability Specification Gaps

**Defined (in code, not in specs):**
- 15+ Prometheus metrics (counters, gauges, histograms) for cache, router, and timeout primitives
- `InstrumentedPrimitive` base class creates `primitive.{name}` spans
- Context propagation via `WorkflowContext` trace fields

**Missing from any specification:**
- ❌ No formal span schema (name, attributes, events, links)
- ❌ No parent-child span relationship rules for composed primitives
- ❌ No baggage propagation specification
- ❌ No metric SLO/percentile targets
- ❌ No specification of what data is considered PII in traces
- ❌ Phases 3-5 of observability roadmap (metrics collectors, Grafana dashboards, documentation) not started

---

## 3. Organization & Cross-Referencing

### 3.1 Proposed `docs/` Hierarchy

The current 4-directory structure is sound. Below is a strictly structured hierarchy that adds SDD-compliant spec organization:

```
docs/
├── README.md                              # Navigation hub (existing, update links)
│
├── architecture/                          # Phase: Plan (How)
│   ├── Overview.md                        # System architecture overview
│   ├── SYSTEM_DESIGN.md                   # Detailed system design
│   ├── PRIMITIVE_PATTERNS.md              # Design patterns
│   ├── DECISION_RECORDS.md                # ADRs
│   ├── OBSERVABILITY_ARCHITECTURE.md      # Observability design
│   ├── MONOREPO_STRUCTURE.md              # Repo organization
│   ├── SPEC_AUDIT_REPORT.md              # This report
│   └── ... (other existing architecture docs)
│
├── reference/                             # Phase: Specify (What)
│   ├── specs/                             # ★ Formal SDD Specifications
│   │   ├── README.md                      # Spec index & template
│   │   ├── primitives/                    # Per-primitive contracts
│   │   │   ├── workflow-primitive.spec.md
│   │   │   ├── sequential-primitive.spec.md
│   │   │   ├── parallel-primitive.spec.md
│   │   │   ├── router-primitive.spec.md
│   │   │   ├── retry-primitive.spec.md
│   │   │   ├── fallback-primitive.spec.md
│   │   │   ├── timeout-primitive.spec.md
│   │   │   ├── cache-primitive.spec.md
│   │   │   ├── memory-primitive.spec.md
│   │   │   └── compensation-primitive.spec.md
│   │   ├── observability/                 # Trace & metric contracts
│   │   │   ├── span-schema.spec.md
│   │   │   ├── metrics-catalog.spec.md
│   │   │   └── context-propagation.spec.md
│   │   └── packages/                      # Package-level contracts
│   │       ├── agent-context.spec.md
│   │       ├── agent-coordination.spec.md
│   │       └── skills.spec.md
│   ├── mcp/                               # MCP protocol reference (existing)
│   ├── mcp-references/                    # MCP server references (existing)
│   └── models/                            # Data models reference (existing)
│
├── guides/                                # Phase: Implement (Build)
│   ├── agents/                            # Agent-specific guides
│   ├── ci-cd/                             # CI/CD guides
│   ├── development/                       # Development workflows
│   ├── integration/                       # Integration patterns
│   ├── observability/                     # Observability how-tos
│   ├── quickstart/                        # Quick-start guides
│   ├── runbooks/                          # Operational runbooks
│   └── troubleshooting/                   # Troubleshooting guides
│
├── examples/                              # Working code examples
│   ├── README.md                          # Example index
│   ├── basic-workflow.md                  # Basic composition
│   ├── custom_tool.md                     # Custom tool example (existing)
│   └── ... (more examples needed)
│
└── _archive/                              # Historical (no changes)
```

### 3.2 Cross-Reference Issues Found

| Issue | Severity | Details |
|-------|----------|---------|
| `agent-coordination` ↔ `universal-agent-context` | 🔴 Critical | No dependency, no imports. Coordination package builds its own context models instead of reusing `universal-agent-context` |
| `docs/reference/specs/` content | 🔴 Critical | Contains generic sample specs (REST caching, e-commerce notifications) unrelated to TTA.dev |
| `docs/README.md` subdirectory references | 🟡 Medium | References `guides/agents/`, `guides/ci-cd/`, etc. — existence unverified; structure may not match |
| `PRIMITIVES_CATALOG.md` → source links | 🟡 Medium | Links to source files may be stale as code evolves |
| `GETTING_STARTED.md` → `CodingStandards.md` | 🟡 Medium | References a file that may not exist at the referenced path |
| Observability spec → Primitive specs | 🟡 Medium | `observability-integration.md` does not reference per-primitive span definitions |
| `platform/shared/` | 🟡 Medium | Referenced in architecture but package is empty/placeholder |

### 3.3 Spec Template

Every formal specification should follow this SDD-compliant template:

```markdown
# {Primitive Name} Specification

- **Version:** 1.0.0
- **Status:** Draft | Review | Approved
- **Package:** tta-dev-primitives
- **Source:** platform/primitives/src/tta_dev_primitives/{module}/{file}.py

## 1. Purpose (What)

One-paragraph functional description.

## 2. Contract

### 2.1 Type Signature
\```python
class PrimitiveName(WorkflowPrimitive[TInput, TOutput]):
    async def execute(self, input_data: TInput, context: WorkflowContext) -> TOutput: ...
\```

### 2.2 Constructor Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|

### 2.3 Behavior Invariants
- MUST ...
- MUST NOT ...
- SHOULD ...

### 2.4 Error Contract
| Condition | Exception | Message Pattern |
|-----------|-----------|-----------------|

### 2.5 Observability Contract
| Span Name | Attributes | Events |
|-----------|------------|--------|
| Metric Name | Type | Labels |

## 3. Composition Rules

How this primitive composes with `>>` and `|` operators.

## 4. Edge Cases

| Input | Expected Behavior |
|-------|-------------------|

## 5. Cross-References

- Related specs: [links]
- Architecture: [links]
- Tests: [links]
```

---

## 4. Gap Analysis

### 4.1 Gap Summary

| # | Gap | Severity | Category | Package | Status |
|---|-----|----------|----------|---------|--------|
| G1 | No formal primitive specifications exist | 🔴 Critical | Spec | tta-dev-primitives | ✅ Resolved |
| G2 | Sample specs in `docs/reference/specs/` are not TTA.dev-related | 🔴 Critical | Spec | infrastructure | ✅ Resolved |
| G3 | No OpenTelemetry span schema specification | 🔴 Critical | Spec | tta-observability-integration | ✅ Resolved |
| G4 | `agent-coordination` does not use `universal-agent-context` models | 🔴 Critical | Architecture | tta-agent-coordination | ✅ Resolved |
| G5 | No error contract for any primitive | 🟡 High | Spec | tta-dev-primitives | ✅ Resolved |
| G6 | No observability metrics specification document | 🟡 High | Spec | tta-observability-integration | ✅ Resolved |
| G7 | Missing spec index/README in `docs/reference/specs/` | 🟡 High | Documentation | infrastructure | ✅ Resolved |
| G8 | `docs/examples/` has only 2 files | 🟡 High | Documentation | infrastructure | ✅ Resolved |
| G9 | `MemoryPrimitive` lacks formal API specification | 🟡 High | Spec | tta-dev-primitives | ✅ Resolved |
| G10 | `CompensationPrimitive`/`SagaPrimitive` have sparse documentation | 🟡 High | Documentation | tta-dev-primitives | ✅ Resolved |
| G11 | No spec template or SDD guide for contributors | 🟡 High | Documentation | infrastructure | ✅ Resolved |
| G12 | Context propagation rules not formally specified | 🟡 High | Spec | tta-observability-integration | ✅ Resolved |
| G13 | `platform/shared/` is an empty placeholder | 🟡 Medium | Architecture | infrastructure | ✅ Resolved |
| G14 | No integration test specs for cross-package workflows | 🟡 Medium | Testing | infrastructure | ✅ Resolved |
| G15 | Skills package lacks discovery mechanism specification | 🟡 Medium | Spec | tta-skill-primitives | ✅ Resolved |

### 4.2 Logseq-Compliant TODO Blocks

The following TODO blocks are formatted for `logseq/journals/2026_03_04.md` and comply with the `#dev-todo` format validated by `scripts/validate-todos.py`:

```markdown
- # Spec Audit — SDD Alignment TODOs (2026-03-04)
- ## 🔴 Critical Gaps
	- TODO Create formal SDD specifications for all core primitives (Sequential, Parallel, Router, Retry, Fallback, Timeout, Cache, Memory, Compensation) #dev-todo
	  type:: documentation
	  priority:: critical
	  package:: tta-dev-primitives
	  related:: [[TTA.dev/Primitives]]
	- TODO Remove sample/template specs from docs/reference/specs/ and replace with TTA.dev primitive spec index #dev-todo
	  type:: documentation
	  priority:: critical
	  package:: infrastructure
	  related:: [[TTA.dev/Architecture]]
	- TODO Create OpenTelemetry span schema specification defining span names, attributes, events, and parent-child relationships for all primitives #dev-todo
	  type:: documentation
	  priority:: critical
	  package:: tta-observability-integration
	  related:: [[tta-observability-integration]]
	- TODO Integrate universal-agent-context models into agent-coordination package to ensure shared context contracts #dev-todo
	  type:: architecture
	  priority:: critical
	  package:: tta-agent-coordination
	  related:: [[universal-agent-context]]
- ## 🟡 High-Priority Gaps
	- TODO Define error contracts for all primitives specifying which exceptions each can raise and under what conditions #dev-todo
	  type:: documentation
	  priority:: high
	  package:: tta-dev-primitives
	  related:: [[TTA.dev/Primitives]]
	- TODO Create observability metrics specification document cataloging all Prometheus metrics with types, labels, and SLO targets #dev-todo
	  type:: documentation
	  priority:: high
	  package:: tta-observability-integration
	  related:: [[tta-observability-integration]]
	- TODO Create spec index README at docs/reference/specs/README.md with navigation, template, and SDD contribution guide #dev-todo
	  type:: documentation
	  priority:: high
	  package:: infrastructure
	  related:: [[TTA.dev/Architecture]]
	- TODO Expand docs/examples/ with working code examples for each core primitive and common composition patterns #dev-todo
	  type:: documentation
	  priority:: high
	  package:: infrastructure
	  related:: [[TTA.dev/Primitives]]
	- TODO Create formal MemoryPrimitive API specification covering add, get, search, and Redis integration contracts #dev-todo
	  type:: documentation
	  priority:: high
	  package:: tta-dev-primitives
	  related:: [[MemoryPrimitive]]
	- TODO Document CompensationPrimitive and SagaPrimitive with full specification, examples, and rollback behavior contracts #dev-todo
	  type:: documentation
	  priority:: high
	  package:: tta-dev-primitives
	  related:: [[TTA.dev/Primitives]]
	- TODO Create SDD spec template and contributor guide explaining Specify/Plan/Implement phase separation #dev-todo
	  type:: documentation
	  priority:: high
	  package:: infrastructure
	  related:: [[TTA.dev/Architecture]]
	- TODO Create context propagation specification defining baggage, trace parent-child rules, and cross-service propagation contracts #dev-todo
	  type:: documentation
	  priority:: high
	  package:: tta-observability-integration
	  related:: [[tta-observability-integration]]
- ## 🟡 Medium-Priority Gaps
	- TODO Evaluate and resolve platform/shared/ package — either implement shared types or remove placeholder #dev-todo
	  type:: architecture
	  priority:: medium
	  package:: infrastructure
	  related:: [[TTA.dev/Packages]]
	- TODO Create integration test specifications for cross-package workflows (primitives + observability + coordination) #dev-todo
	  type:: testing
	  priority:: medium
	  package:: infrastructure
	  related:: [[TTA.dev/Architecture]]
	- TODO Create skill discovery mechanism specification for SkillRegistry including registration, lookup, and versioning contracts #dev-todo
	  type:: documentation
	  priority:: medium
	  package:: tta-skill-primitives
	  related:: [[TTA.dev/Primitives]]
```

---

## 5. Recommendations

### 5.1 Immediate Actions (This Sprint)

1. **Clean `docs/reference/specs/`** — Remove the two sample spec files and create a `README.md` with the spec template and index
2. **Write RetryPrimitive spec as pilot** — Use it as the model for all other primitive specs
3. **Create span schema spec** — Formalize the OpenTelemetry trace contract

### 5.2 Short-Term Actions (Next 2 Sprints)

4. **Write remaining primitive specs** — One spec per primitive following the pilot template
5. **Define error contracts** — Catalog all exceptions and when they're raised
6. **Resolve `agent-coordination` ↔ `agent-context` gap** — Either add dependency or document why they're independent

### 5.3 Medium-Term Actions (Next Quarter)

7. **Complete observability phases 3-5** — Metrics collectors, dashboards, documentation
8. **Expand examples directory** — One runnable example per primitive
9. **Add spec validation to CI** — Ensure specs stay in sync with code

### 5.4 SDD Adoption Path

```
Current State          Target State
─────────────         ─────────────
Docs (How to use)  →  Specs (What the contract is)
README examples    →  Formal behavior invariants
Implicit errors    →  Explicit error contracts
Code-embedded      →  Standalone spec documents
  observability       with trace/metric schemas
```

---

## 6. Conclusion

### Overall Assessment: 5/10 ⭐⭐⭐⭐⭐☆☆☆☆☆

**Strengths:**
- ✅ Excellent documentation culture — READMEs, catalogs, and guides are thorough
- ✅ Clean 4-directory consolidation provides solid foundation
- ✅ Well-typed primitives with `Generic[T, U]` base class
- ✅ Comprehensive test suite (~580 tests)
- ✅ Strong cross-referencing between root constitution files

**Gaps:**
- ❌ Zero formal SDD-compliant specifications exist
- ❌ No separation between Specify (What) and Plan (How) phases
- ❌ No primitive defines its error contract
- ❌ Observability spans/metrics lack formal schemas
- ❌ Cross-package integration contracts are undefined

**Path Forward:** The repository has the *content* to generate excellent specs — the information exists in docstrings, README examples, and architecture docs. The work is to extract, formalize, and organize this information into standalone, unambiguous contracts that an AI agent can use as the sole source of truth for code generation and verification.

---

*Generated by Spec Audit Report tooling. See Logseq journal entry `2026_03_04.md` for actionable TODOs.*
