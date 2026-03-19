# Spec: Phase 3 — Guided Workflow System

**Phase:** SDD Phase 1 (Functional Specification)
**Status:** Draft — awaiting sign-off
**Date:** 2026-03-19
**Scope:** Multi-agent workflow orchestration, human-in-the-loop approval gates,
and two-tier agent memory (in-context + persistent)

---

## Problem Statement

TTA.dev's agent system (Phase 2) gives us 7 specialist agents that can be invoked
individually and hand off to each other reactively. What's missing is *proactive,
structured coordination*: a way to declare a workflow that sequences agents in a
defined order, passes state between them, and gives the user meaningful control
checkpoints — not just "fire and forget".

Additionally, agents currently have no memory beyond the current invocation. Each
call starts fresh. A senior developer in a devops org builds context over time;
our agents should too.

---

## Core Concepts

```
WorkflowDefinition  =  name  +  list[WorkflowStep]  +  memory config
WorkflowStep        =  agent_name  +  input_transform  +  approval_gate?
WorkflowOrchestrator  =  WorkflowDefinition  +  AgentMemory  →  WorkflowResult
AgentMemory         =  WorkflowMemory (in-context)  +  PersistentMemory (cross-session)
```

A workflow is itself a `WorkflowPrimitive` — it composes with `>>` and `|` like
everything else in TTA.dev.

---

## User Journeys

### Journey 1: Run a pre-defined workflow end-to-end

```python
from ttadev.workflows import feature_dev_workflow

result = await feature_dev_workflow.run(
    goal="Implement issue #42: add rate limiting to the API",
    context={"repo": "TTA.dev", "issue_url": "..."},
)
# Pauses at each approval gate for user confirmation
# result.steps — each agent's output
# result.artifacts — all files produced
```

### Journey 2: Define a custom workflow

```python
from ttadev.workflows import WorkflowDefinition, WorkflowStep

review_pipeline = WorkflowDefinition(
    name="pr_review",
    steps=[
        WorkflowStep(agent="developer", gate=True),
        WorkflowStep(agent="security", gate=True),
        WorkflowStep(agent="qa", gate=False),   # no pause — auto-continue
    ],
)
result = await review_pipeline.run(goal="Review PR #88", context={})
```

### Journey 3: Dynamic orchestration (conductor decides at runtime)

```python
from ttadev.workflows import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator(
    model=AnthropicPrimitive(),  # conductor model
    memory=PersistentMemory(),
)
result = await orchestrator.run(
    goal="Implement and ship issue #42 end-to-end",
    context={},
)
# Orchestrator plans steps, executes them, adapts based on each result
```

### Journey 4: Human-in-the-loop approval gate

When a step with `gate=True` completes, execution pauses:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step 1/3 complete: developer
  Confidence: 94%  |  Quality gates: ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  The developer agent produced:
  [output preview — first 500 chars]
  ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Next step: security — check for vulnerabilities
  [Enter] continue   [s] skip this step   [q] quit   [?] show full output
> _
```

Pass `--no-confirm` (or `auto_approve=True`) to bypass all gates.

### Journey 5: Agent memory across sessions

```python
# Session 1
result = await developer_agent.execute(task, ctx)
# Memory stores: what was built, decisions made, patterns preferred

# Session 2 — new process
agent = DeveloperAgent(model=..., memory=PersistentMemory())
# Agent recalls: "Last time we discussed rate limiting, here's what was decided..."
```

### Journey 6: CLI workflow execution

```bash
# Run a named workflow
tta workflow run feature_dev --goal "implement issue #42" --repo TTA.dev

# List available workflows
tta workflow list

# Show workflow definition
tta workflow show feature_dev

# Run with auto-approve (no gates)
tta workflow run feature_dev --goal "..." --no-confirm
```

---

## WorkflowDefinition

```python
@dataclass
class WorkflowStep:
    agent: str               # registered agent name
    gate: bool = True        # pause for approval before next step
    input_transform: Callable[[WorkflowState], AgentTask] | None = None
    # defaults to: pass previous step's result + original goal as new task

@dataclass
class WorkflowDefinition:
    name: str
    description: str
    steps: list[WorkflowStep]
    memory_config: MemoryConfig = field(default_factory=MemoryConfig)
```

---

## WorkflowOrchestrator

The orchestrator handles two modes:

**Static (pre-defined steps):** Execute steps in order, passing state, pausing at gates.

**Dynamic (conductor model):** Before each step, ask the conductor model:
*"Given the goal and what's been done so far, what should happen next?"*
The conductor picks an agent (or declares the workflow complete).

Both modes share the same approval gate UX and memory system.

---

## Human-in-the-Loop Approval Gate

Approval gates mirror Claude Code's own confirmation pattern:

- **Display:** step index, agent name, confidence, quality gate status, output preview
- **Options:**
  - `[Enter]` — continue to next step
  - `s` — skip this step (mark as skipped, proceed)
  - `e` — edit the instruction before the next step runs
  - `q` — quit workflow (saves state for resume)
  - `?` — show full output
- **Opt-out:** `auto_approve=True` on `WorkflowDefinition` or `--no-confirm` CLI flag
- **Non-interactive mode:** if stdin is not a TTY (CI/scripts), gates auto-approve with a log warning

---

## Two-Tier Agent Memory

### Tier 1: WorkflowMemory (in-context, per-session)

Lives in `WorkflowContext`. Persists across steps within a single workflow run.
Cleared when the run completes (unless flushed to Tier 2).

```python
ctx.memory.set("architecture_decision", "use async queue for rate limiting")
ctx.memory.get("architecture_decision")
ctx.memory.append("observations", "the rate limiter needs Redis")
ctx.memory.snapshot()  # returns dict — can be passed to next agent's context
```

Agents receive the memory snapshot as part of their task `context` dict.

### Tier 2: PersistentMemory (cross-session, searchable)

Backed by **Hindsight** (`pip install hindsight-client`) — an open-source agent memory
server that combines semantic vector search, BM25 keyword matching, entity graph
traversal, and temporal filtering internally. No need for separate SQLite/FalkorDB
memory layers.

**Self-hosted via Docker (one command):**
```bash
docker run --rm -it -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_API_KEY=$ANTHROPIC_API_KEY \
  -v $HOME/.hindsight-docker:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest
```

**Three-method API:**
```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Store a memory (namespaced by bank_id — one per agent or workflow)
client.retain(bank_id="tta.developer", content="Decided to use token bucket for rate limiting")

# Search memories (semantic + keyword + graph + temporal, reranked)
results = client.recall(bank_id="tta.developer", query="rate limiting decisions")

# Generate a context-aware summary from relevant memories
response = client.reflect(bank_id="tta.developer", query="what do we know about rate limiting?")
```

**Bank ID naming convention:**
- Per-agent: `tta.<agent_name>` (e.g. `tta.developer`, `tta.security`)
- Per-workflow: `tta.workflow.<workflow_name>` (e.g. `tta.workflow.feature_dev`)

**Graceful degradation:** If the Hindsight server is unreachable, `PersistentMemory`
logs a warning and operates as a no-op (workflow execution continues unaffected).

**Relationship to CGC/FalkorDB:**
The `codegraphcontext` FalkorDB graph is a *code structure graph* (symbols, imports,
call graphs) — separate purpose from agent memory. No overlap; both coexist.

**Note on Hindsight for Claude Code (you):**
The Hindsight MCP server endpoint (`http://localhost:9999`) can also be wired into
Claude Code's MCP config so the coding agent shares the same memory bank as TTA.dev
agents — memories from agent workflows become available in interactive sessions.

### Memory Lifecycle

```
Step executes → result + key decisions → WorkflowMemory.append()
                                        ↓ (on workflow complete or gate confirm)
                                PersistentMemory.retain()   [Hindsight]
                                        ↓
                   searchable in future sessions via .recall() / .reflect()
```

---

## Pre-built Workflow: `feature_dev_workflow`

The reference implementation — a developer of TTA.dev using TTA.dev assets:

```
Step 1: developer  — implement the feature (gate: ✓)
Step 2: qa         — write/review tests (gate: ✓)
Step 3: security   — vulnerability scan (gate: ✓)
Step 4: git        — commit the work (gate: ✓)
Step 5: github     — open a PR with description (gate: ✓)
```

Input: `goal` (string) + optional `context` dict (repo, branch, issue URL)
Output: `WorkflowResult` with all step outputs, artifacts, and a final PR URL

---

## WorkflowResult

```python
@dataclass
class WorkflowResult:
    workflow_name: str
    goal: str
    steps: list[StepResult]       # one per executed step
    artifacts: list[Artifact]     # aggregated from all steps
    memory_snapshot: dict         # final WorkflowMemory state
    completed: bool               # False if quit early
    total_confidence: float       # average across steps
```

---

## Observability

All workflow execution is visible as nested spans:

```
workflow.feature_dev               [root span]
  ├── agent.developer              [child span]
  ├── approval_gate.developer      [event span — gate decision recorded]
  ├── agent.qa                     [child span]
  ├── approval_gate.qa
  ...
```

Memory reads/writes emit spans with `memory.backend`, `memory.query`, `memory.hit_count`.

---

## `tta workflow` CLI

```
tta workflow list                            # all registered workflows
tta workflow show <name>                     # definition: steps, gate config
tta workflow run <name> --goal "..."         # execute with approval gates
tta workflow run <name> --goal "..." --no-confirm   # auto-approve all gates
tta workflow run <name> --goal "..." --dry-run      # show plan, no execution
```

---

## Success Criteria

- [ ] `feature_dev_workflow.run(goal="...")` executes all 5 agents in sequence
- [ ] Approval gate pauses at each `gate=True` step and accepts `[Enter]`/`s`/`q`/`e`
- [ ] `--no-confirm` bypasses all gates without breaking the workflow
- [ ] `WorkflowMemory` snapshots are passed to each subsequent agent as context
- [ ] `PersistentMemory.store()` + `search()` work against SQLite backend
- [ ] `PersistentMemory` falls back gracefully when FalkorDB is unreachable
- [ ] FalkorDB backend stores + retrieves memory when socket is available
- [ ] `tta workflow list` shows registered workflows; `run` executes them
- [ ] Workflow execution appears as nested spans in the observability dashboard
- [ ] 100% test coverage on new code; all existing tests pass

---

## Out of Scope (Phase 3)

- **Parallel workflow steps** (`step_a | step_b`) — sequential is sufficient for Phase 3
- **Workflow resume after `q`** — quit is terminal in Phase 3; resume is Phase 3.2
- **Agent learning / preference adaptation** — stored memory is read-only context for now
- **Multi-user / multi-tenant workflows** — solo developer scope

---

## Decisions

1. **Workflow as WorkflowPrimitive:** The `WorkflowOrchestrator` extends
   `InstrumentedPrimitive`, making it fully composable with `>>` and `|`.
   No special-casing needed in the core.

2. **Memory in WorkflowContext:** `WorkflowContext` gains a `memory` property
   (Tier 1). This avoids a separate injection mechanism and keeps state local
   to the span tree.

3. **Hindsight as memory backend:** Handles vector, BM25, graph, and temporal
   retrieval internally — no need for separate SQLite FTS or FalkorDB memory
   layers. `PersistentMemory` wraps `hindsight-client` with graceful degradation
   when the server is unreachable. The CGC/FalkorDB code graph remains separate
   (it models code structure, not agent memory).

4. **Approval gates are sync I/O:** Gates call `input()` (blocking). In async
   context, they run in an executor thread. In non-TTY environments they
   auto-approve with a log warning. This matches how Claude Code itself handles
   confirmation prompts.

5. **`feature_dev_workflow` as dogfood:** The reference workflow uses TTA.dev
   to develop TTA.dev. This validates the system against a real task pattern
   and provides a worked example for documentation.
