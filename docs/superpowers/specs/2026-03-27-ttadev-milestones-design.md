# TTA.dev Milestone Plan — Design Document

**Date:** 2026-03-27
**Status:** Approved
**Author:** Adam (theinterneti) + Claude Code

---

## Overview

TTA.dev is a universal, domain-agnostic toolkit for building reliable AI applications. It is not a game engine — it is the foundation layer beneath one. TTA (Therapeutic Text Adventure) is its primary consumer, but TTA.dev has its own identity, roadmap, and contract surface that any project can adopt.

This document defines TTA.dev's milestone structure using **capability-cluster milestones**: each milestone ships a cohesive set of capabilities that is independently valuable, documented with an explicit contract, and versioned. TTA adopts TTA.dev capabilities on its own schedule by pinning to published contracts.

---

## Architecture Relationship

```
Layer 1: TTA.dev (Universal Toolkit)     ← this roadmap
           ↓ publishes contracts
Layer 2: TTA Game Toolkit                ← consumes TTA.dev via contracts
           ↓ builds features
Layer 3: TTA Game (Player-facing)
```

TTA.dev has no awareness of TTA's game schedule. TTA pins to TTA.dev contract versions. When a contract is stable, TTA adopts it — the integration boundary is explicit, not implicit.

---

## TTA.dev Milestones

### M1 — Primitive Foundation

**Theme:** Every core primitive is stable, tested, documented, and semver-versioned. `UniversalLLMPrimitive` ships as the canonical LLM interface.

**Completion at time of writing:** ~65%

**Scope:**

| Item | Status |
|------|--------|
| `RetryPrimitive` — API audit, coverage to 100%, contract doc | Partially done |
| `FallbackPrimitive` — API audit, coverage to 100%, contract doc | Partially done |
| `TimeoutPrimitive` — API audit, coverage to 100%, contract doc | Partially done |
| `CachePrimitive` — API audit, coverage to 100%, contract doc | Partially done |
| `CircuitBreakerPrimitive` — production-hardened, contract doc | Done |
| `CoordinationPrimitive` (Redis) — contract doc, coverage | Added, needs doc |
| `UniversalLLMPrimitive` — provider abstraction over Groq, Anthropic, OpenAI, Ollama, local models. Single interface, swappable backends, config-driven. **Note:** An existing `UniversalLLMPrimitive` lives in `ttadev/integrations/` scoped to agentic coder budget profiles — that is a different concern. M1 defines a new primitive at `ttadev.primitives.llm.UniversalLLMPrimitive` for runtime LLM invocation. Both will coexist. | Not started (new) |
| `PRIMITIVES_CATALOG.md` — updated to reflect stable surface | Partially done |
| `PRIMITIVES_CONTRACT.md` — new file defining each primitive's interface, behavior guarantees, and error semantics (does not yet exist) | Not started |
| Semver policy — what constitutes a breaking change | Not started |

**Out of scope:** New primitives not already in codebase. Observability wiring. Orchestration patterns.

**Contract published:** `PRIMITIVES_CONTRACT.md` at repo root. Python package at `ttadev.primitives.*`. Contract versions are unstable until the semver policy (also M1 work) is finalized — TTA consumers should treat contracts as pinnable only after M1 closes.

**Done when:** `PRIMITIVES_CONTRACT.md` exists and is merged; all six primitives have 100% branch coverage; `UniversalLLMPrimitive` at `ttadev.primitives.llm` passes its contract tests; semver policy doc is merged; `PRIMITIVES_CATALOG.md` reflects the stable surface.

---

### M2 — Observable Pipeline

**Theme:** Any consumer wraps their agent pipeline with TTA.dev observability and gets full OTel traces, structured metrics, and Grafana-ready dashboards with minimal boilerplate.

**Completion at time of writing:** ~35%

**Scope:**

| Item | Status |
|------|--------|
| OTel span decorators/context managers — `@observable_step`, `with observable_pipeline()` | Partially done |
| Standard metric names registry — `ttadev.primitive.retry.count`, `ttadev.agent.step.duration_ms`, `ttadev.pipeline.end_to_end_latency_ms`, etc. | Not formalized |
| Grafana dashboard template (JSON) for a 3-agent pipeline (IPA→WBA→NGA pattern) | Not started |
| `observability-guide.md` — updated with usage examples | Partially done |
| OTel trace attribution on `RunRecord` and `WorkflowStepRecord` | Done |

**Out of scope:** Consumer-specific dashboards (TTA builds those). APM/LangFuse integration (post-M2 extension).

**Contract published:** OTel span attribute schema + metric name registry. Consumers instrument against these names; dashboards are generated from the schema.

**Note on dashboard template:** The Grafana template uses a 3-agent pipeline (Input Processing Agent → World Building Agent → Narrative Generation Agent) as its reference implementation, which reflects TTA's canonical pipeline. The template itself uses configurable agent labels so any 3-agent pipeline can adopt it — TTA's pattern is the worked example, not a hardcoded assumption.

**Sequencing note:** M2 depends on M1 (instrument stable primitives, not moving targets).

**Done when:** OTel span attribute schema and metric name registry are documented and merged; `@observable_step` decorator and `observable_pipeline()` context manager exist with 100% coverage; Grafana dashboard template (JSON) is committed to `docs/observability/`.

---

### M3 — Control Plane v1

**Theme:** The L0 control plane is production-hardened. The MCP tool surface is stable and versioned. The gate model supports arbitrary escalation policies, including crisis/safety escalation.

**Completion at time of writing:** ~75%

**Scope:**

| Item | Status |
|------|--------|
| `GatePolicy` — extend to support `ESCALATE_TO_HUMAN` outcome type. **Note:** `GatePolicy` does not yet exist in the codebase. The existing `WorkflowGateDecisionOutcome` enum has `CONTINUE`, `SKIP`, `EDIT`, and `QUIT`. Both `GatePolicy` and `ESCALATE_TO_HUMAN` are new additions. | Not started |
| MCP server — tool versioning, stable tool signatures, deprecation path documented | Done (needs versioning) |
| `tta control workflow status` — polished | Done |
| `tta control gate list/approve/reject/quit` — stable | Done |
| Workflow state machine — edge cases: timeout, abandoned workflows, orphaned steps | Partial |
| L0 runbook — updated to reflect hardened surface | Done |

**Out of scope:** New MCP tools not already planned. UI for control plane. Multi-tenant features.

**Contract published:** MCP tool specs (JSON Schema for each tool input/output), gate policy schema (once `GatePolicy` is designed), workflow state machine diagram.

**Sequencing note:** M3 can be worked in parallel with M1. It is largely independent of primitive stability. **Important for TTA M5 (Safety):** that game milestone specifically requires the `ESCALATE_TO_HUMAN` gate outcome type — not M3 completion generally. TTA M5 cannot start until that specific feature within M3 is done.

**Done when:** `GatePolicy` type exists with `ESCALATE_TO_HUMAN` outcome; MCP tool specs (JSON Schema) are committed for all current tools; workflow state machine handles timeout, abandoned, and orphaned-step edge cases; L0 runbook reflects hardened surface.

---

### M4 — Context Intelligence

**Theme:** Any consumer can assemble a token-budgeted LLM context from tiered sources, compress old history, and recall cross-session memory — all through a stable, composable interface.

**Completion at time of writing:** ~15%

**Scope:**

| Item | Status |
|------|--------|
| `TokenBudgetManager` — assign budgets across context tiers, enforce limits, report overflow | Not started |
| `HistoryCompressionPrimitive` — async summarization of older turns via LLM, pluggable summarizer | Not started |
| `ContextAssembler` — compose tiered context (world state, history, character, instructions) into a final prompt string within budget | Not started |
| `CrossSessionMemoryPrimitive` — wraps Hindsight recall/retain for per-entity memory across sessions | Not started |
| All four components: individually testable, composable, covered to 100% | — |

**Out of scope:** `WorldContextBuilder` itself (TTA consumer code). Neo4j traversal (TTA-specific). Dolt integration (TTA-side).

**Contract published:** `ContextAssembler` interface, tier schema, `TokenBudgetManager` config format.

**Sequencing note:** M4 depends on M1 (needs stable primitives as building blocks). M2 is a hard dependency for production readiness: M4 components shipped without observability cannot be operated in production, and TTA's integration contract for M3/M6 requires them to be production-ready. M4 components can be built before M2 is complete but should not be considered done until M2 instrumentation is applied.

**Done when:** All four components (`TokenBudgetManager`, `HistoryCompressionPrimitive`, `ContextAssembler`, `CrossSessionMemoryPrimitive`) exist at `ttadev.primitives.context.*` with 100% coverage, individually testable, composable, and instrumented with M2-standard OTel spans.

---

### M5 — Coordination & Scale

**Theme:** TTA.dev provides distributed coordination primitives that any multi-agent, multi-player, or multi-process consumer can adopt.

**Completion at time of writing:** ~15%

**Scope:**

| Item | Status |
|------|--------|
| `PubSubPrimitive` — Redis pub/sub wrapper: typed channels, backpressure, reconnection | Not started |
| `DistributedLockPrimitive` — Redis-backed distributed lock. The existing `CoordinationPrimitive` at `ttadev/primitives/coordination/` provides the Redis foundation; M5 extracts and formalizes the locking behaviour as a named, documented primitive at `ttadev.primitives.coordination.DistributedLockPrimitive`. | Partially done (foundation exists) |
| `LeaderElectionPrimitive` — single coordinator among competing agents | Not started |
| Performance benchmark suite — latency/throughput targets documented per primitive | Not started |
| Multi-consumer usage guide — "how to use TTA.dev in two separate services" | Not started |

**Out of scope:** Dolt integration (TTA-specific persistence). World reconciliation logic (TTA game logic). Kubernetes/deployment concerns.

**Contract published:** Coordination primitive interfaces, channel schema format, benchmark baseline numbers.

**Sequencing note:** M5 is largely independent. Can be worked after M1 is stable.

**Done when:** `PubSubPrimitive`, `DistributedLockPrimitive`, and `LeaderElectionPrimitive` exist at `ttadev.primitives.coordination.*` with 100% coverage; benchmark suite runs in CI; multi-consumer usage guide is committed to `docs/`.

---

### M6 — Clinical Infrastructure *(Distant Horizon)*

**Theme:** TTA.dev provides the toolkit layer for clinical-grade AI applications: audit trails, data retention policy primitives, consent management, and practitioner-facing observability.

**Completion at time of writing:** ~0%

**Scope (preliminary — to be specced when M8 of TTA is in progress):**

- `AuditLogPrimitive` — immutable, append-only event log with retention policies
- `ConsentPrimitive` — tracks consent state per entity, enforces data access rules
- `DataRetentionPrimitive` — policy-driven data lifecycle (TTL, right-to-deletion)
- Practitioner observability hooks — structured session summaries, flagged moment detection
- Regulatory compliance guide (not legal advice — design patterns only)

**Contract published:** Audit schema, consent state machine, retention policy format.

**Done when (provisional):** Scope is fully specced following TTA M8 delivery and agreed with the TTA consumer; all components exist at `ttadev.primitives.clinical.*` with 100% coverage; legal/ethical review is complete and sign-off is documented in a `CLINICAL_REVIEW.md` file committed to the repo.

**Sequencing note:** M6 is the one deliberate exception to TTA.dev's isolation from TTA's schedule. Clinical infrastructure requires real-world therapeutic use cases to be well-understood before the primitives can be designed correctly — shipping audit or consent primitives without that grounding risks building the wrong abstraction. TTA M8 (Mature Therapeutic) provides that grounding. This is a design-quality dependency, not a coupling: TTA.dev M6 will still be a general-purpose toolkit milestone, but its design will be informed by real use patterns. Requires legal/ethical review before TTA adopts.

---

## Integration Contracts: TTA ↔ TTA.dev

The explicit contracts TTA pins to at each game milestone:

| TTA Game Milestone | TTA.dev Prerequisites | Key Contracts |
|---|---|---|
| M1 — World Seed | TTA.dev M1 + M3 (complete), M2 (partial) | Primitives API, MCP tool specs, OTel span names |
| M2 — Characters | TTA.dev M1 + M2 + M3 (complete) | Above + observable pipeline |
| M3 — Narrative Engine | TTA.dev M1–M3 (complete), M4 (partial) | Above + ContextAssembler interface |
| M4 — Living Systems | TTA.dev M1–M4 (complete) | Above + TokenBudgetManager config |
| M5 — Safety | TTA.dev M3 (`ESCALATE_TO_HUMAN` gate) | Gate policy schema, escalation outcome type |
| M6 — Therapeutic Intro | TTA.dev M4 (`CrossSessionMemoryPrimitive`) | CrossSessionMemory interface, tier schema |
| M7 — Async Multiplayer | TTA.dev M5 (complete) | PubSub channel schema, DistributedLock interface |
| M8 — Mature Therapeutic | TTA.dev M1–M5 (complete), M6 (starting) | CrossSessionMemory, AuditLog (early) |
| M9 — Clinical | TTA.dev M6 (complete) | Full clinical infrastructure surface |

---

## TTA Game Milestone Arc (for reference)

The full TTA game arc, using the three-level mental health engagement framework:

| # | Title | MH Level |
|---|-------|----------|
| M1 | World Seed — From Concept to Living World | — |
| M2 | Characters & Social Fabric | — |
| M3 | Narrative Engine | — |
| M4 | Living Systems (Emergence) | — |
| M5 | Safety — Mental Health Informed | Informed |
| M6 | Therapeutic Introduction — Mental Health Aware | Aware |
| M7 | Async Multiplayer — Shared World, Parallel Timelines | — |
| M8 | Mature Therapeutic — Mental Health Aware | Aware |
| M9 | Clinical — Mental Health Practitioner | Practitioner |

**Mental health engagement levels:**
- **Informed** (Safety): Do no harm. TTRPG session zero model — lines & veils, safe exits, crisis recognition. Not therapy.
- **Aware** (Therapeutic): Game design reflects therapeutic principles (narrative therapy, mindfulness, externalization). Player experiences a richer game, not a therapeutic intervention.
- **Practitioner** (Clinical): Audit trails, practitioner oversight, consent management, regulatory compliance. A different product surface.

**Important scoping note:** Crisis detection and the Guide persona appear as minimal baseline features in TTA M1. They are scoped to the safety floor only — TTRPG-informed, not clinical. The comprehensive Safety milestone is M5.

---

## Sequencing Summary

```
TTA.dev M1 (Primitive Foundation)     ──┐
TTA.dev M3 (Control Plane v1)         ──┤──► TTA M1, M2, M3, M4, M5
                                         │
TTA.dev M2 (Observable Pipeline)      ──┤──► TTA M2, M3
  (depends on M1)                        │
                                         │
TTA.dev M4 (Context Intelligence)     ──┤──► TTA M3, M4, M6
  (depends on M1, benefits from M2)      │
                                         │
TTA.dev M5 (Coordination & Scale)     ──┤──► TTA M7
  (depends on M1)                        │
                                         │
TTA.dev M6 (Clinical Infrastructure)  ──┘──► TTA M8, M9
  (distant horizon)
```

---

## What This Is Not

- TTA.dev milestones do not track TTA game features
- TTA.dev milestones do not have game-specific logic (WorldContextBuilder, NPC memory, narrative arcs)
- TTA.dev does not own Dolt integration — that is TTA-side persistence
- TTA.dev M6 does not provide legal or regulatory advice — design patterns only
