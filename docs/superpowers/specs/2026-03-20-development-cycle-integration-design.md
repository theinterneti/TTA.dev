# DevelopmentCycle Integration Design

**Date:** 2026-03-20
**Status:** Approved
**Author:** Claude Code + Adam (brainstorming session)

---

## Overview

This document specifies how E2B, Hindsight, and CodeGraphContext (CGC) integrate into TTA.dev — both as tools that improve the development of TTA.dev itself (Horizon 1) and as first-class platform primitives that apps built on TTA.dev can use (Horizon 2).

The central design is **The DevelopmentCycle**: a five-step loop (Orient → Recall → Write → Validate → Retain) that is first implemented as a protocol Claude Code follows, then progressively built into a composable `WorkflowPrimitive`.

---

## Goals

1. **Eliminate cold-starts** — every session begins with architectural context loaded from Hindsight
2. **Eliminate blind edits** — every non-trivial change is preceded by a CGC impact analysis
3. **Eliminate unvalidated code** — new code is proven in an E2B sandbox before committing
4. **Compound learning** — decisions, patterns, and failures are retained after every session
5. **Free by default** — apps built on TTA.dev work out of the box with Ollama, no API key required
6. **Always observable** — every step in the loop emits an OTel span

---

## The Model Layer

Three audiences, one coherent hierarchy. This is the foundation everything else sits on.

| Audience | Models | Config required |
|---|---|---|
| **Building TTA.dev** (Claude Code, Copilot, Augment) | Paid models (Claude, GPT-4o) | Developer's own keys |
| **TTA.dev platform** (agents, workflows, memory synthesis) | OpenRouter `:free` → Ollama | `OPENROUTER_API_KEY` optional |
| **Apps built on TTA.dev** (end users) | Ollama default → OpenRouter → paid (opt-in) | None — just works |

**Provider selection hierarchy for TTA.dev apps:**
1. Ollama `qwen2.5:7b` — local, always available, zero config, ~4.5GB RAM
2. OpenRouter `:free` — if `OPENROUTER_API_KEY` set (gemma-3n → mistral-small → gpt-oss-20b)
3. Paid models — if `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc. set

**The free-model amplifier** — TTA.dev's job is to make free models punch above their weight:
- **Structured prompting**: output schemas, few-shot examples, CoT scaffolds in `AgentSpec.system_prompt` + `AgentMemory` directives
- **Retry + fallback**: `RetryPrimitive` + `FallbackPrimitive` — quality gate fails → reframe prompt → try next model; transparent to caller
- **Context economy**: `CodeGraphPrimitive` delivers targeted context only; `CachePrimitive` on repeated CGC queries; tight token budgets
- **Quality gates**: `AgentResult.confidence` + `QualityGate` — silent retry on weak output; user sees clean results only

---

## The Loop

Five steps. Every step traced by OTel. Free LLM at the centre.

```
CGC          Hindsight      LLM (free)    E2B           Hindsight
  │              │               │            │               │
[1. Orient] → [2. Recall] → [3. Write] → [4. Validate] → [5. Retain]
```

### Step 1 — Orient (CGC)

**Question:** "What exists, and what will this change touch?"

Before touching any file, query CGC for:
- Callers of the target function/class
- Dependencies the module imports
- Complexity score before the edit
- Which tests cover the target
- Risk level: low / medium / high based on call-graph fan-out

**H1 (protocol):** `orient-before-edit` skill invoked by Claude Code before any non-trivial change. Uses existing CGC MCP tools directly.

**H2 (primitive):** `CodeGraphPrimitive[CodeGraphQuery, ImpactReport]` — typed, instrumented, wraps 5 CGC operations.

---

### Step 2 — Recall (Hindsight)

**Question:** "What do we know that's relevant to this task?"

Pull from the `tta-dev` Hindsight bank:
- Architectural decisions relevant to the target module
- Known failure patterns to avoid
- Coding directives (standards, SDD mandate, model strategy)
- Mental models for the affected subsystems

**H1 (protocol):** Session-start skill loads directives + mental models. Per-task: `mcp__hindsight__recall` with semantic query.

**H2 (primitive):** `AgentMemory` structured layer — injects directives into agent system prompt prefix, recalls relevant memories into task context, all before the LLM call.

---

### Step 3 — Write (LLM, free by default)

**Question:** "What should be built, given what we know?"

LLM call — grounded by Orient (what exists, what it touches) and Recall (what was decided, what failed). Provider selected by `get_llm_client()` per the hierarchy above.

**For building TTA.dev:** Claude Code (paid), grounded by the protocol steps above.

**For TTA.dev apps:** Any `ChatPrimitive` — `OpenRouterPrimitive`, `OllamaPrimitive`, `AnthropicPrimitive`. Provider strategy is automatic.

---

### Step 4 — Validate (E2B)

**Question:** "Does what was built actually work in isolation?"

New code runs in a Firecracker microVM before it lands:
- Clean environment — no local state bleed
- Exact dependency install from `pyproject.toml`
- Test suite from Step 1's `related_tests`
- Pass/fail + stdout/stderr reported; `sandbox_id` in OTel span

**H1 (protocol):** `build-test-verify` skill: E2B sandbox step after writing, before commit.

**H2 (primitive):** `CodeExecutionPrimitive` (already built) wired as a tool in the developer and QA agents. Agent writes → agent validates → agent returns only proven output.

---

### Step 5 — Retain (Hindsight)

**Question:** "What should the next session know?"

After each task: store decisions made, patterns used, anything that failed. The loop closes. Next session starts warmer.

**H1 (protocol):** End-of-task ritual in skills: `mcp__hindsight__retain` with structured content. Template enforced by session-end skill.

**H2 (primitive):** `DevelopmentCycle` auto-retains after each step. No manual effort — the loop closes itself.

---

## Memory Architecture

### Six memory types

| Type | Purpose | Example |
|---|---|---|
| **Facts** | Specific, atomic | "primitives subpackage version is 1.3.1 separate from package v0.1.0" |
| **Decisions** | Rationale preserved | "Used gemma-3n not nemotron — nemotron returns null content (reasoning-only)" |
| **Patterns** | Reusable solutions | "Use `override_registry()` context manager for AgentRegistry in tests" |
| **Failures** | What to avoid | "nemotron-3-super returns `content: null` — do not use as default" |
| **Directives** | Persistent instructions | "Always orient with CGC before editing any non-trivial file" |
| **Mental models** | Synthesized module summaries | Full summary of the primitives system architecture |

### H1 — `tta-dev` bank structure

```
tta-dev/
├── codebase-insights/       # facts + patterns (exists)
├── architectural-decisions/ # decisions (exists)
├── successful-patterns/     # patterns (populate)
├── implementation-failures/ # failures (populate)
├── directives/              # NEW — persistent rules
│   ├── dev-loop.md          # orient→recall→write→validate→retain
│   ├── coding-standards.md  # uv, ruff, pyright, SDD mandate
│   └── model-strategy.md    # free first, Ollama default, never nemotron
└── mental-models/           # NEW — synthesized module summaries
    ├── primitives.md
    ├── agents.md
    ├── workflows.md
    └── integrations.md
```

### H2 — AgentMemory (platform primitive)

Per-app, per-agent memory banks. Bank ID pattern: `{app-name}.{agent-name}` and `{app-name}.shared`.

```python
class AgentMemory:
    """Structured Hindsight layer — attached to WorkflowContext."""

    def __init__(self, bank_id: str, agent_name: str | None = None) -> None: ...

    # Recall
    async def recall(self, query: str) -> list[str]: ...
    async def get_directives(self) -> list[str]: ...
    async def get_mental_model(self, name: str) -> str: ...

    # Retain
    async def retain(self, content: str, tags: list[str] = []) -> None: ...
    async def retain_decision(self, decision: str, rationale: str) -> None: ...
    async def retain_failure(self, what: str, why: str) -> None: ...

    # Agent system prompt integration
    async def build_system_prompt_prefix(self) -> str: ...
```

**Integration with `AgentPrimitive`:** Before each `execute()`, the agent:
1. Calls `memory.build_system_prompt_prefix()` → prepends directives + mental model summary to `AgentSpec.system_prompt`
2. Calls `memory.recall(task.instruction)` → injects relevant past knowledge into task context
3. After execution: calls `memory.retain(result)` if result contains novel decisions

Agents get smarter with every run — without any code change to the agent itself. Memory is infrastructure, not agent logic.

---

## CodeGraphPrimitive

Wraps 5 CGC MCP operations as a typed `InstrumentedPrimitive`.

```python
class CodeGraphQuery(BaseModel):
    target: str                    # function/class/file name
    operations: list[CGCOp]        # which operations to run
    depth: int = 2                 # graph traversal depth

class ImpactReport(BaseModel):
    target: str
    callers: list[str]
    dependencies: list[str]
    related_tests: list[str]
    complexity: float
    risk: Literal["low", "medium", "high"]
    summary: str                   # LLM-readable paragraph

class CodeGraphPrimitive(
    InstrumentedPrimitive[CodeGraphQuery, ImpactReport]
): ...
```

**Five wrapped operations (`CGCOp`):**

| Operation | CGC tool | Purpose |
|---|---|---|
| `find_code` | `find_code` | Locate functions/classes by name or description |
| `get_relationships` | `analyze_code_relationships` | Callers, callees, imports |
| `get_complexity` | `calculate_cyclomatic_complexity` | Risk flag before edit |
| `find_tests` | `find_code` + heuristic | Which test files exercise the target |
| `raw_cypher` | `execute_cypher_query` | Power-user escape hatch |

---

## DevelopmentCycle WorkflowPrimitive

The loop as a first-class composable primitive.

```python
class DevelopmentTask(BaseModel):
    instruction: str
    target_files: list[str] = []   # hints for CGC orient step
    agent_hint: str = "developer"

class DevelopmentResult(BaseModel):
    response: str
    artifacts: list[Artifact]
    validated: bool                # E2B passed?
    impact_report: ImpactReport
    memories_retained: int

class DevelopmentCycle(
    InstrumentedPrimitive[DevelopmentTask, DevelopmentResult]
):
    # Composed internally — each step is its own primitive
    orient   = CodeGraphPrimitive()
    recall   = AgentMemory(bank_id)
    write    = AgentRegistry.get(agent_hint)()
    validate = CodeExecutionPrimitive()
    retain   = AgentMemory(bank_id)

    # Composable like any primitive:
    # cycle >> reviewer >> git_agent
    # cycle | security_cycle  (parallel)
```

**OTel trace structure:**
```
DevelopmentCycle                [root span]
├─ CGC.orient                   [duration, risk_level, target]
├─ Hindsight.recall             [n_results, query]
├─ Agent.execute                [model, tokens, confidence, agent_name]
├─ E2B.validate                 [sandbox_id, pass/fail, execution_time]
└─ Hindsight.retain             [operation_id, n_facts]
```

**Composing into workflows:**
```python
# feature_dev_workflow becomes:
feature_dev_workflow = WorkflowDefinition(
    steps=[
        WorkflowStep(agent=DevelopmentCycle(agent_hint="developer"), gate=True),
        WorkflowStep(agent=DevelopmentCycle(agent_hint="qa"),        gate=True),
        WorkflowStep(agent=DevelopmentCycle(agent_hint="security"),  gate=True),
        WorkflowStep(agent="git",                                    gate=True),
        WorkflowStep(agent="github",                                 gate=True),
    ],
    memory_config=MemoryConfig(flush_to_persistent=True),
)
```

---

## Implementation Sequence

### Phase 1 — Protocol (this week, zero new code)

**Goal:** Immediately improve the Claude Code development loop using existing MCP tools.

Deliverables:
- Populate `directives/` in Hindsight `tta-dev` bank: `dev-loop.md`, `coding-standards.md`, `model-strategy.md`
- Populate `mental-models/` in Hindsight `tta-dev` bank: one per major module (primitives, agents, workflows, integrations)
- Update `CLAUDE.md`: mandate orient-before-edit, document session-start ritual
- New `.claude/skills/session-start/` skill: loads directives + mental models + CGC orientation
- Update `build-test-verify` skill: add CGC impact check before write, E2B validation step after write
- Update `core-conventions` skill: add free-model strategy section

Success criteria: every session starts with context loaded; every non-trivial edit is preceded by a CGC query; new code is sandbox-validated before committing.

---

### Phase 2 — Primitives (after Phase 1, SDD spec per primitive)

**Goal:** Formalize the protocol as typed, tested, observable primitives.

Deliverables:
- `ttadev/primitives/code_graph/` — `CodeGraphPrimitive`, `CodeGraphQuery`, `ImpactReport`, `CGCOp` enum
- `ttadev/primitives/memory/` — `AgentMemory`, `MemoryType` enum, `DirectiveSet`, `MentalModel`
- Update `ttadev/agents/base.py` — `AgentPrimitive._execute_impl` uses `AgentMemory` if available on context
- Wire `CodeExecutionPrimitive` as a tool in `developer` and `qa` agent specs
- 100% test coverage on all new primitives; OTel on every `_execute_impl`

Each primitive gets its own SDD spec before implementation (`/specify → /plan → /tasks → /implement`).

---

### Phase 3 — DevelopmentCycle (after Phase 2, the crown jewel)

**Goal:** The loop as a single composable primitive.

Deliverables:
- `ttadev/workflows/development_cycle.py` — `DevelopmentCycle`, `DevelopmentTask`, `DevelopmentResult`
- Free-model amplifier: retry chains with model fallback, quality gates, context budget management, structured prompt templates per agent role
- Updated `feature_dev_workflow` — uses `DevelopmentCycle` at each non-git step
- New prebuilt: `quick_fix_workflow` — single cycle, no approval gates
- Dogfood: use `DevelopmentCycle` to implement Phase 2 primitives

---

### Phase 4 — Automation (progressive, as the loop proves out)

**Goal:** The loop runs itself — no manual protocol required.

Deliverables:
- Session-start hook in `settings.json` → auto-runs orient + recall on session open
- Pre-commit hook: CGC impact analysis + E2B validation before every commit
- Post-session auto-retain: Claude Code retains structured session learnings automatically
- CI integration: E2B sandbox step in merge gate workflow (`.github/workflows/merge-gate.yml`)
- Mental model refresh: triggered when CGC detects structural change in indexed modules

---

## Full System Map

```
External tools     Primitives            Agents              Workflows
─────────────────  ────────────────────  ──────────────────  ─────────────────────
CGC (MCP)       →  CodeGraphPrimitive →  developer / qa   →  DevelopmentCycle  →  OTel: orient
Hindsight (MCP) →  AgentMemory        →  all agents       →  DevelopmentCycle  →  OTel: recall/retain
E2B sandbox     →  CodeExecutionPrim  →  developer / qa   →  DevelopmentCycle  →  OTel: validate

Ollama (default)
+ OpenRouter :free  →  get_llm_client()  →  free-model amplifier  →  quality output
+ paid (opt-in)
```

**The layman's view:** "Build me a data analysis tool." `DevelopmentCycle` runs. CGC understands the codebase. Hindsight recalls what worked before. A free model writes the code. E2B proves it works. Hindsight learns. The user gets a proven artifact. They never see any of this.

---

## Constraints

- All new primitives follow the SDD mandate: spec before code
- All new primitives extend `InstrumentedPrimitive` (never raw `WorkflowPrimitive`)
- All LLM calls in TTA.dev apps use `get_llm_client()` — no hardcoded model names
- `e2b-code-interpreter` is a core dependency (already added to `pyproject.toml`)
- CGC `CodeGraphPrimitive` degrades gracefully if CGC MCP server is unreachable (warns, returns empty `ImpactReport`)
- `AgentMemory` degrades gracefully if Hindsight is unreachable (same pattern as existing `PersistentMemory`)

---

## Open Questions

None — all design decisions resolved in brainstorming session 2026-03-20.
