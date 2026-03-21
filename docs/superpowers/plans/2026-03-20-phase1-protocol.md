# Phase 1 Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the DevelopmentCycle protocol for Claude Code — structured Hindsight memory (directives + mental models), a session-start skill, and updated skills — so every session starts warm and every non-trivial edit is preceded by a CGC impact check and followed by E2B validation.

**Architecture:** No new Python code. All changes are markdown files (Hindsight bank entries, Claude Code skills, CLAUDE.md). Content is retained to the Hindsight MCP API (`tta-dev` bank) AND written as file-based memories in `.hindsight/banks/tta-dev/` for cross-agent access.

**Tech Stack:** Hindsight MCP (`mcp__hindsight__retain`, `mcp__hindsight__recall`), CGC MCP (`mcp__codegraphcontext__*`), Claude Code skills (`.claude/skills/`), CLAUDE.md

---

## Scope

This plan covers **Phase 1 only** from the DevelopmentCycle Integration Design spec (`docs/superpowers/specs/2026-03-20-development-cycle-integration-design.md`).

Phases 2–4 (CodeGraphPrimitive, AgentMemory, DevelopmentCycle, Automation) each require their own SDD spec cycle (`/specify → /plan → /tasks → /implement`) and are out of scope here.

---

## File Map

| Action | Path | Purpose |
|---|---|---|
| Create | `.hindsight/banks/tta-dev/directives/dev-loop.md` | The 5-step loop as a persistent directive |
| Create | `.hindsight/banks/tta-dev/directives/coding-standards.md` | uv, ruff, pyright, SDD, TODO format |
| Create | `.hindsight/banks/tta-dev/directives/model-strategy.md` | Free-first model hierarchy, known bad models |
| Create | `.hindsight/banks/tta-dev/mental-models/primitives.md` | Synthesized primitives system summary |
| Create | `.hindsight/banks/tta-dev/mental-models/agents.md` | Agent system summary |
| Create | `.hindsight/banks/tta-dev/mental-models/workflows.md` | Workflow system summary |
| Create | `.hindsight/banks/tta-dev/mental-models/integrations.md` | E2B, Hindsight, CGC integration summary |
| Create | `.claude/skills/session-start/SKILL.md` | Session-start ritual skill |
| Modify | `.claude/skills/build-test-verify/SKILL.md` | Add CGC orient + E2B validate steps; fix stale pyright path |
| Modify | `.claude/skills/core-conventions/SKILL.md` | Add LLM provider strategy section |
| Modify | `CLAUDE.md` | Add Session Start Protocol + Orient Before Edit + session-start skill to table |

---

## Task 1: Hindsight directives — dev-loop

**Files:**
- Create: `.hindsight/banks/tta-dev/directives/dev-loop.md`

- [ ] **Step 1: Create the file**

```markdown
---
category: directives
date: 2026-03-20
component: dev-loop
severity: critical
tags: [directive, dev-loop, orient, recall, validate, retain]
---
# Directive: The DevelopmentCycle Loop

Every non-trivial task follows five steps in order. This is mandatory, not optional.

## The Loop

1. **Orient** (CGC) — before touching any file, call `mcp__codegraphcontext__find_code`
   and `mcp__codegraphcontext__analyze_code_relationships` on the target. Understand callers,
   dependencies, complexity, and which tests cover the target.

2. **Recall** (Hindsight) — call `mcp__hindsight__recall` with a query about the target
   module or task type. Pull relevant decisions, patterns, and failures before writing.

3. **Write** — produce code, plans, or output grounded by Orient + Recall context.
   Use `get_llm_client()` for any LLM call — never hardcode a model or provider.

4. **Validate** (E2B) — for new or changed Python code, run the affected tests inside
   an E2B sandbox using `CodeExecutionPrimitive` before committing. If E2B is unavailable,
   fall back to `uv run pytest` locally but note the deviation.

5. **Retain** (Hindsight) — after each task, call `mcp__hindsight__retain` with:
   - Any decision made and its rationale
   - Any pattern used for the first time
   - Any failure encountered and why it happened

## What counts as "non-trivial"

Trivial (skip Orient): fixing a typo, updating a comment, changing a string literal.
Non-trivial (run Orient): adding/changing any function, class, import, or config value.

---
**Created:** 2026-03-20
**Verified:** [x] Yes
```

- [ ] **Step 2: Retain to Hindsight MCP**

Call `mcp__hindsight__retain` with bank_id `tta-dev`, content:
```
DIRECTIVE — The DevelopmentCycle Loop (mandatory for every non-trivial task):
1. Orient: query CGC (find_code + analyze_code_relationships) on target before editing
2. Recall: mcp__hindsight__recall on target module/task type before writing
3. Write: use get_llm_client() — never hardcode model or provider
4. Validate: run affected tests in E2B sandbox (CodeExecutionPrimitive) before committing
5. Retain: store decision + rationale, pattern used, any failure — after every task
Non-trivial = any function/class/import/config change. Trivial = typo/comment/string only.
```

- [ ] **Step 3: Verify recall works**

Call `mcp__hindsight__recall` with bank_id `tta-dev`, query `development loop steps orient validate`. Confirm the directive appears in results.

- [ ] **Step 4: Commit**

```bash
git add .hindsight/banks/tta-dev/directives/dev-loop.md
git commit -m "docs(hindsight): add dev-loop directive to tta-dev bank"
```

---

## Task 2: Hindsight directives — coding-standards and model-strategy

**Files:**
- Create: `.hindsight/banks/tta-dev/directives/coding-standards.md`
- Create: `.hindsight/banks/tta-dev/directives/model-strategy.md`

- [ ] **Step 1: Create coding-standards.md**

```markdown
---
category: directives
date: 2026-03-20
component: coding-standards
severity: critical
tags: [directive, standards, uv, ruff, sdd, todos]
---
# Directive: Coding Standards

## Non-negotiable rules

- **Package manager:** `uv` always. Never `pip`, never `poetry`.
- **Python:** 3.11+. `str | None` not `Optional[str]`. `dict[str, Any]` not `Dict`.
- **Linting:** `uv run ruff check . --fix` then `uv run ruff format .` before every commit.
- **Type checking:** `uvx pyright ttadev/` (basic mode, non-blocking in CI).
- **Testing:** pytest AAA pattern. 100% coverage for all new code. Never comment out tests.
- **Commits:** Conventional Commits — `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- **Primitives:** Always use for workflows — RetryPrimitive not manual retry loops,
  TimeoutPrimitive not asyncio.wait_for, CachePrimitive not manual dicts.
- **State:** Pass via WorkflowContext, never globals.

## SDD mandate (non-negotiable)

No implementation code before a signed-off spec.
Workflow: `/specify` → `/plan` → `/tasks` → `/implement`

## TODO format (CI-blocking if wrong)

```markdown
- TODO <description> #dev-todo
  type:: <bug|implementation|refactor|documentation>
  priority:: <critical|high|medium|low>
  package:: <package-name>
```

---
**Created:** 2026-03-20
**Verified:** [x] Yes
```

- [ ] **Step 2: Create model-strategy.md**

```markdown
---
category: directives
date: 2026-03-20
component: model-strategy
severity: critical
tags: [directive, llm, openrouter, ollama, free-models]
---
# Directive: LLM Provider Strategy

## For TTA.dev apps (end-user facing)

Provider hierarchy — always use `get_llm_client()`, never hardcode:
1. **Ollama** (default, zero config) — `qwen2.5:7b`, CPU-only homelab compatible
2. **OpenRouter :free** (if `OPENROUTER_API_KEY` set) — gemma-3n → mistral-small → gpt-oss-20b
3. **Paid models** (if paid key set) — user's choice

## For building TTA.dev itself

Paid models (Claude, Copilot, Augment) — developer's own keys. Quality matters most here.

## KNOWN BAD MODEL — never use as default

`nvidia/nemotron-3-super-120b-a12b:free` is reasoning-only — returns `content: null`.
Any pipeline reading `response.content` will get None and crash. Confirmed broken 2026-03-19.

## Free-model amplifier (platform's job)

TTA.dev makes free models work well via: structured prompting in AgentSpec,
RetryPrimitive + FallbackPrimitive for quality-gate retry, CachePrimitive for context
economy, QualityGate for silent retry on weak output.

---
**Created:** 2026-03-20
**Verified:** [x] Yes
```

- [ ] **Step 3: Retain both to Hindsight MCP**

Call `mcp__hindsight__retain` (bank_id: `tta-dev`) with:
```
DIRECTIVE — Coding standards: uv always (never pip/poetry), Python 3.11+ str|None,
ruff check+format before commit, uvx pyright ttadev/ (basic), pytest AAA 100% coverage,
Conventional Commits, always use primitives (RetryPrimitive/TimeoutPrimitive/CachePrimitive),
state via WorkflowContext never globals. SDD mandate: /specify→/plan→/tasks→/implement.
TODO format requires #dev-todo tag with type:: priority:: package:: properties (CI-blocking).
```

Call `mcp__hindsight__retain` (bank_id: `tta-dev`) with:
```
DIRECTIVE — LLM provider strategy: always use get_llm_client(), never hardcode model/provider.
TTA.dev app hierarchy: (1) Ollama qwen2.5:7b default zero-config, (2) OpenRouter :free if
OPENROUTER_API_KEY set (gemma-3n → mistral-small → gpt-oss-20b), (3) paid if key set.
KNOWN BAD: nvidia/nemotron-3-super-120b-a12b:free returns content:null (reasoning-only model),
confirmed broken 2026-03-19. Free-model amplifier: structured prompts + RetryPrimitive +
FallbackPrimitive + CachePrimitive + QualityGate.
```

- [ ] **Step 4: Commit**

```bash
git add .hindsight/banks/tta-dev/directives/
git commit -m "docs(hindsight): add coding-standards and model-strategy directives"
```

---

## Task 3: Hindsight mental models

**Files:**
- Create: `.hindsight/banks/tta-dev/mental-models/primitives.md`
- Create: `.hindsight/banks/tta-dev/mental-models/agents.md`
- Create: `.hindsight/banks/tta-dev/mental-models/workflows.md`
- Create: `.hindsight/banks/tta-dev/mental-models/integrations.md`

- [ ] **Step 1: Create primitives.md**

```markdown
---
category: mental-models
date: 2026-03-20
component: primitives
severity: high
tags: [mental-model, primitives, WorkflowPrimitive, WorkflowContext, composition]
---
# Mental Model: Primitives System

Package: `ttadev/primitives/` — version 1.3.1 (separate from package v0.1.0).
Auto-calls `setup_tracing()` on import.

## Core types

**WorkflowPrimitive[T, U]** (`ttadev/primitives/core/base.py`)
- Abstract. `execute(input_data: T, context: WorkflowContext) -> U`
- `>>` → SequentialPrimitive (chain). `|` → ParallelPrimitive (fan-out/gather).

**WorkflowContext** (Pydantic model, same file)
- W3C trace: `trace_id`, `span_id`, `baggage`
- Identity: `agent_id`, `agent_role`, `session_id`
- `spawn_agent(role)`, `create_child_context()`, `from_project(name, workflow_id)`, `checkpoint(label)`
- `memory` — attached at runtime by WorkflowOrchestrator

**InstrumentedPrimitive** (`ttadev/primitives/observability/instrumented_primitive.py`)
- Extends WorkflowPrimitive. Override `_execute_impl` not `execute`.
- Wraps with OTel spans automatically. All agents + orchestrator extend this.

## All exported primitives

LambdaPrimitive, SequentialPrimitive, ParallelPrimitive, ConditionalPrimitive,
RouterPrimitive, RetryPrimitive, FallbackPrimitive, TimeoutPrimitive,
CompensationPrimitive, CachePrimitive, MockPrimitive, GitCollaborationPrimitive.

## Integration primitives (`ttadev/primitives/integrations/`)

anthropic, openai, openrouter, groq, google-ai-studio, ollama, together-ai,
huggingface, e2b, supabase, sqlite. All implement `ChatPrimitive` protocol.
All optional deps — graceful degradation in `__init__.py` with try/except.

## Recovery primitives (`ttadev/primitives/recovery/`)

retry, timeout, fallback, circuit_breaker (two files), compensation.

## Import path

All internal imports use `from ttadev.primitives.X` — never `from primitives.X` (old, broken).

---
**Created:** 2026-03-20
**Verified:** [x] Yes
```

- [ ] **Step 2: Create agents.md**

```markdown
---
category: mental-models
date: 2026-03-20
component: agents
severity: high
tags: [mental-model, agents, AgentSpec, AgentPrimitive, AgentRegistry]
---
# Mental Model: Agent System (Phase 2)

All files: `ttadev/agents/`

## Core types

**AgentSpec** (frozen dataclass, `spec.py`): `name`, `role`, `system_prompt`,
`capabilities`, `tools: list[AgentTool]`, `quality_gates: list[QualityGate]`,
`handoff_triggers: list[HandoffTrigger]`

**AgentTool**: `name`, `description`, `rule: ToolRule` (ALWAYS/WHEN_INSTRUCTED/NEVER)
**QualityGate**: `name`, `check: Callable[[AgentResult], bool]`, `error_message`
**HandoffTrigger**: `condition: Callable[[AgentTask], bool]`, `target_agent: str`

**AgentTask** (`task.py`): `instruction`, `context: dict`, `constraints`, `agent_hint: str | None`
**AgentResult** (`task.py`): `agent_name`, `response`, `artifacts`, `suggestions`,
`spawned_agents`, `quality_gates_passed: bool`, `confidence: float` (0.0–1.0)
**Artifact**: `name`, `content`, `artifact_type` ("code"/"test"/"diff"/"report")

## AgentPrimitive (base.py)

Extends `InstrumentedPrimitive[AgentTask, AgentResult]`.
Flow: check handoff triggers → build tool handlers → run ToolCallLoop → check quality gates.
Composable: `agent_a >> agent_b` or `agent_a | agent_b`.

## AgentRegistry (registry.py)

- Global in-memory registry
- `override_registry()` context manager — REQUIRED for test isolation
- `get_registry()` — returns contextvar override or global
- `registry.get(name)` — returns agent CLASS, not instance (caller instantiates)

## ChatPrimitive protocol (protocol.py)

`chat(messages: list[dict], system: str | None, ctx: WorkflowContext) -> str`
Implemented by all LLM integration primitives.

## Built-in agents

developer, qa, devops, security, git, github, performance — each in own file.
AgentRouterPrimitive (router.py) — routes AgentTask to correct agent.

---
**Created:** 2026-03-20
**Verified:** [x] Yes
```

- [ ] **Step 3: Create workflows.md**

```markdown
---
category: mental-models
date: 2026-03-20
component: workflows
severity: high
tags: [mental-model, workflows, WorkflowOrchestrator, ApprovalGate, memory]
---
# Mental Model: Workflow System (Phase 3)

All files: `ttadev/workflows/`

## WorkflowDefinition (definition.py) — immutable frozen dataclass

`name`, `description`, `steps: list[WorkflowStep]`, `auto_approve: bool`,
`memory_config: MemoryConfig(flush_to_persistent, bank_id)`

WorkflowStep: `agent: str`, `gate: bool = True`, `input_transform: Callable | None`
WorkflowResult: `workflow_name`, `goal`, `steps`, `artifacts`, `memory_snapshot`,
`completed`, `total_confidence`

## WorkflowOrchestrator (orchestrator.py)

Extends `InstrumentedPrimitive[WorkflowGoal, WorkflowResult]` — composable with >> and |.
Input: `WorkflowGoal(goal: str, context: dict)`

Execution loop:
1. Attach WorkflowMemory to context.memory
2. For each step: build task → get agent from registry → execute → gate check
3. Gate decisions: CONTINUE / SKIP (skips next step too) / EDIT (re-run same step) / QUIT
4. Flush to PersistentMemory if memory_config.flush_to_persistent
total_confidence = avg confidence of non-skipped steps

## ApprovalGate (gate.py)

Human-in-the-loop checkpoint. `auto_approve=True` skips all prompts.
Non-TTY stdin auto-approves with log warning.
Keys: Enter=continue, s=skip, e=edit (re-runs step), q=quit, ?=full output.

## Memory layers (memory.py)

**WorkflowMemory** (Tier 1): in-context key/value. `set/get/append/snapshot`.
Lives on `context.memory`, cleared after run unless flushed.

**PersistentMemory** (Tier 2): Hindsight-backed. Graceful degradation if unavailable.
Uses `hindsight_client.Hindsight` if installed, else `_HttpHindsightShim`.
Methods: `retain(bank_id, content)`, `recall(bank_id, query)`, `reflect(bank_id, query)`.

## Prebuilt (prebuilt.py)

`feature_dev_workflow`: developer→qa→security→git→github, all gated, memory flushed.

---
**Created:** 2026-03-20
**Verified:** [x] Yes
```

- [ ] **Step 4: Create integrations.md**

```markdown
---
category: mental-models
date: 2026-03-20
component: integrations
severity: high
tags: [mental-model, e2b, hindsight, cgc, llm-providers]
---
# Mental Model: Integrations Layer

## E2B (Code Execution)

SDK: `e2b-code-interpreter==2.5.0` (core dep in pyproject.toml).
Key: `E2B_API_KEY` in `.env` (also reads `E2B_KEY`).
Primitive: `ttadev/primitives/integrations/e2b_primitive.py` → `CodeExecutionPrimitive`.
Alias: `E2BPrimitive = CodeExecutionPrimitive`.

Free tier: 20 concurrent Firecracker microVMs, 8 vCPU each, 1-hour sessions.
Auto-rotates sessions at 55 minutes. 150ms startup.
Runtime: Python 3.13.12. Confirmed working 2026-03-19.

Usage:
```python
async with CodeExecutionPrimitive() as executor:
    result = await executor.execute({"code": "print(42)"}, ctx)
    # result["output"] == "42\n", result["success"] == True
```

## Hindsight (Cross-session Memory)

Docker: API port 8888, dashboard port 9999. Volume: ~/.local/share/hindsight.
Model: HINDSIGHT_LLM_MODEL env var (currently google/gemma-3n-e4b-it:free).
MCP: configured in ~/.claude.json as HTTP transport at http://localhost:8888/mcp.

Known issue: if container exits uncleanly, delete
~/.local/share/hindsight/instances/hindsight/data/postmaster.pid before restarting.

PersistentMemory in ttadev/workflows/memory.py wraps Hindsight with graceful degradation.
Bank for this project: `tta-dev`.

## CodeGraphContext (CGC)

Version: 0.3.1 globally at ~/.local/bin/cgc.
Graph: 3 repos, 1278 files, 13098 functions, 2319 classes (as of 2026-03-17).
MCP: configured in ~/.claude.json as stdio transport.

Key MCP tools: find_code, analyze_code_relationships, calculate_cyclomatic_complexity,
find_dead_code, execute_cypher_query, get_repository_stats.

No TTA.dev primitive yet — Phase 2 will add CodeGraphPrimitive.

## LLM provider selection

`get_llm_client()` in `ttadev/workflows/llm_provider.py` (also `ttadev/integrations/`):
1. LLM_FORCE_PROVIDER=ollama → Ollama
2. OPENROUTER_API_KEY set → OpenRouter (model from HINDSIGHT_LLM_MODEL)
3. Else → Ollama (qwen2.5:7b, http://localhost:11434/v1)

---
**Created:** 2026-03-20
**Verified:** [x] Yes
```

- [ ] **Step 5: Retain all four to Hindsight MCP**

Four separate `mcp__hindsight__retain` calls (bank_id: `tta-dev`):

**primitives retain:**
```
MENTAL MODEL — Primitives system: ttadev/primitives/ v1.3.1 (separate from package v0.1.0).
WorkflowPrimitive[T,U] abstract: execute(input, ctx), >> (sequential), | (parallel).
WorkflowContext Pydantic: trace_id/span_id/baggage, agent_id/role, spawn_agent(), create_child_context(),
from_project(name, workflow_id), checkpoint(label), .memory (runtime).
InstrumentedPrimitive: override _execute_impl not execute, OTel auto-wrapping.
All internal imports: from ttadev.primitives.X — NOT from primitives.X (old broken path).
Integration primitives: anthropic/openai/openrouter/groq/google/ollama/together/huggingface/e2b/supabase/sqlite.
Recovery: retry/timeout/fallback/circuit_breaker/compensation.
```

**agents retain:**
```
MENTAL MODEL — Agent system (Phase 2): ttadev/agents/.
AgentSpec (frozen): name/role/system_prompt/capabilities/tools/quality_gates/handoff_triggers.
AgentPrimitive extends InstrumentedPrimitive[AgentTask, AgentResult].
AgentRegistry: global, override_registry() context manager for test isolation (required in tests).
get_registry() returns contextvar override or global. registry.get(name) returns CLASS not instance.
Built-ins: developer, qa, devops, security, git, github, performance.
AgentTask: instruction/context/constraints/agent_hint. AgentResult: response/artifacts/confidence(0-1)/quality_gates_passed.
ChatPrimitive protocol: chat(messages, system, ctx) -> str — all LLM integrations implement this.
```

**workflows retain:**
```
MENTAL MODEL — Workflow system (Phase 3): ttadev/workflows/.
WorkflowOrchestrator extends InstrumentedPrimitive[WorkflowGoal, WorkflowResult] — composable.
Attaches WorkflowMemory to context.memory. Gate decisions: CONTINUE/SKIP/EDIT/QUIT.
EDIT re-runs same step with new instruction (does not advance i). SKIP advances i twice (skips next step).
WorkflowMemory (Tier 1): in-context key/value, snapshot() returns deep copy.
PersistentMemory (Tier 2): Hindsight-backed, graceful degradation, retain/recall/reflect.
Prebuilt: feature_dev_workflow = developer→qa→security→git→github all gated, flush_to_persistent=True.
```

**integrations retain:**
```
MENTAL MODEL — Integrations: E2B sandbox (e2b-code-interpreter==2.5.0, E2B_API_KEY, Python 3.13.12,
confirmed working 2026-03-19, CodeExecutionPrimitive/E2BPrimitive alias, async context manager).
Hindsight (Docker :8888/:9999, HINDSIGHT_LLM_MODEL=google/gemma-3n-e4b-it:free, bank=tta-dev,
stale PID issue: delete postmaster.pid before restart, MCP at localhost:8888/mcp).
CGC (v0.3.1 ~/.local/bin/cgc, 3 repos/1278 files/13098 functions, MCP stdio in ~/.claude.json,
no TTA.dev primitive yet — Phase 2 CodeGraphPrimitive).
LLM get_llm_client(): LLM_FORCE_PROVIDER=ollama OR OPENROUTER_API_KEY→OpenRouter OR →Ollama qwen2.5:7b.
```

- [ ] **Step 6: Commit**

```bash
git add .hindsight/banks/tta-dev/mental-models/
git commit -m "docs(hindsight): add mental models for primitives, agents, workflows, integrations"
```

---

## Task 4: Create session-start skill

**Files:**
- Create: `.claude/skills/session-start/SKILL.md`

- [ ] **Step 1: Create the skill file**

```markdown
---
name: session-start
description: Use this skill at the start of every session to load context from Hindsight and orient in the codebase with CGC. Run before any task.
---

### Session Start Protocol

Run these steps at the beginning of every session, before any task work.

#### 1. Load directives

Call `mcp__hindsight__recall` with:
- bank_id: `tta-dev`
- query: `mandatory directives coding standards dev loop model strategy`

Read all results. These are non-negotiable rules for this session.

#### 2. Load mental models

Call `mcp__hindsight__recall` with:
- bank_id: `tta-dev`
- query: `mental model primitives agents workflows integrations architecture`

Read all results. This is your architectural map.

#### 3. Recall task-specific context (if task is known)

Call `mcp__hindsight__recall` with:
- bank_id: `tta-dev`
- query: `<the specific module, feature, or component you are about to work on>`

#### 4. Orient with CGC

Call `mcp__codegraphcontext__get_repository_stats` to confirm the graph is current.

If the task involves specific files/functions, also call `mcp__codegraphcontext__find_code`
for the target to understand its position in the graph.

#### 5. Acknowledge

State briefly what you loaded — directives active, mental models loaded, current graph
stats — so the user knows the session started warm.

#### Session End: Retain

Before ending the session or after completing a significant task, call
`mcp__hindsight__retain` with bank_id `tta-dev` and content covering:
- Any decision made (what + why)
- Any pattern used for the first time
- Any failure encountered (what + why)
- Any architectural insight gained

Use this format for the content:
```
[type: decision|pattern|failure|insight] <what happened>
Rationale/why: <the reason>
Context: <module or area affected>
```
```

- [ ] **Step 2: Verify the file renders correctly**

Read `.claude/skills/session-start/SKILL.md` and confirm it has valid frontmatter
(`name` and `description` fields) and all five steps are present.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/session-start/SKILL.md
git commit -m "feat(skills): add session-start skill for warm session protocol"
```

---

## Task 5: Update build-test-verify skill

**Files:**
- Modify: `.claude/skills/build-test-verify/SKILL.md`

Changes:
1. Fix stale pyright path: `platform/` → `ttadev/`
2. Prepend step 0 (Orient with CGC before writing)
3. Append step 6 (E2B sandbox validation) and step 7 (Retain)

- [ ] **Step 1: Write the updated file**

```markdown
---
name: build-test-verify
description: Use this skill when asked to build the project, run tests, lint the code, or verify that the TTA.dev platform is stable before committing.
---

### Build, Test, and Verify (TTA.dev)

Validate code changes to ensure they meet quality standards before committing.

#### Process

Execute the following steps in order. Do not skip steps.

0. **Orient** (before writing any code): query CGC for the target.
   ```
   mcp__codegraphcontext__find_code — search for the target function/class
   mcp__codegraphcontext__analyze_code_relationships — callers, dependencies
   mcp__codegraphcontext__calculate_cyclomatic_complexity — risk level
   ```
   If CGC is unavailable, note it and proceed. Do not block on CGC absence.

1. **Format**: Apply Ruff formatting (100-char line length).
   ```bash
   uv run ruff format .
   ```

2. **Lint**: Run Ruff linter with auto-fix.
   ```bash
   uv run ruff check . --fix
   ```

3. **Type Check**: Run Pyright in basic mode.
   ```bash
   uvx pyright ttadev/
   ```

4. **Run Tests**: Execute the pytest suite (100% coverage required for new code).
   ```bash
   uv run pytest -v --tb=short -m "not integration and not slow and not external"
   ```

5. **Full coverage** (when adding new code):
   ```bash
   uv run pytest --cov=ttadev --cov-report=html
   ```

6. **Validate in E2B** (when adding or changing Python code): run the tests
   identified in the Orient step inside a clean E2B sandbox.
   ```python
   from ttadev.primitives.integrations.e2b_primitive import CodeExecutionPrimitive
   from ttadev.primitives.core.base import WorkflowContext

   async with CodeExecutionPrimitive() as executor:
       result = await executor.execute({
           "code": "import subprocess; r = subprocess.run(['python', '-m', 'pytest', '<test_file>', '-v', '--tb=short'], capture_output=True, text=True); print(r.stdout); print(r.stderr)"
       }, WorkflowContext(workflow_id="validate"))
       # Check result["success"] and result["output"] for PASSED/FAILED
   ```
   If E2B is unavailable, fall back to local pytest and note the deviation.

7. **Retain**: after a successful commit, call `mcp__hindsight__retain` with bank_id
   `tta-dev` documenting any decision, pattern, or failure from this task.

#### Common Issues

- **Type errors**: Ensure all new functions have strict type annotations (`str | None`, not `Optional[str]`).
- **Test failures**: Fix the implementation, never comment out tests. Follow the AAA pattern (Arrange-Act-Assert).
- **Import errors**: All primitives imports must use `from ttadev.primitives.X` — never `from primitives.X`.
- **Quarantined tests**: Tests marked `@pytest.mark.quarantine` are auto-skipped unless selected with `-m quarantine`.

#### Deep Reference

For full testing patterns, markers, CI pipeline details, and MockPrimitive API, see
[`docs/agent-guides/testing-architecture.md`](../../docs/agent-guides/testing-architecture.md).
```

- [ ] **Step 2: Verify the diff looks right**

Key changes to confirm:
- Step 0 (Orient) is present before step 1
- Step 3 pyright path is `ttadev/` not `platform/`
- Step 5 coverage path is `--cov=ttadev` not `--cov=src`
- Step 6 (E2B validate) is present
- Step 7 (Retain) is present
- Import error note mentions `from ttadev.primitives.X` not `from primitives.X`

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/build-test-verify/SKILL.md
git commit -m "fix(skills): update build-test-verify — add CGC orient + E2B validate, fix stale paths"
```

---

## Task 6: Update core-conventions skill

**Files:**
- Modify: `.claude/skills/core-conventions/SKILL.md`

Change: add LLM Provider Strategy section before the Deep Reference footer.

- [ ] **Step 1: Write the updated file**

```markdown
---
name: core-conventions
description: Use this skill when writing or reviewing Python code in TTA.dev. Covers package manager, type hints, primitives usage, and anti-patterns.
---

### Core Conventions (TTA.dev)

Non-negotiable standards for all code in the TTA.dev repository.

#### Package Manager

**Always use `uv`, never `pip` or `poetry`.**

```bash
uv add package-name        # Add dependency
uv sync --all-extras       # Sync all dependencies
uv run pytest -v           # Run via uv
```

#### Python Version & Types

- Python 3.11+ required
- `str | None` not `Optional[str]`
- `dict[str, Any]` not `Dict[str, Any]`
- Google-style docstrings on all public functions

#### Primitives — Always Use Them

```python
# ✅ Use primitives
workflow = RetryPrimitive(primitive=api_call, max_retries=3)

# ❌ Never write manual retry/timeout loops
for attempt in range(3):  # WRONG
    try: ...
```

#### Anti-Patterns

| ❌ Don't | ✅ Do |
|---------|------|
| `try/except` retry loops | `RetryPrimitive` |
| `asyncio.wait_for()` | `TimeoutPrimitive` |
| Manual caching dicts | `CachePrimitive` |
| Global variables for state | `WorkflowContext` |
| `pip install` | `uv add` |
| `Optional[str]` | `str | None` |
| `from primitives.X` | `from ttadev.primitives.X` |

#### State Management

Pass state via `WorkflowContext`, never global variables:

```python
context = WorkflowContext(workflow_id="demo")
result = await workflow.execute(input_data, context)
```

#### LLM Provider Strategy

**Always use `get_llm_client()` — never hardcode a model or base URL.**

```python
from ttadev.workflows.llm_provider import get_llm_client

cfg = get_llm_client()
# cfg.base_url, cfg.model, cfg.api_key, cfg.provider
```

Provider hierarchy for TTA.dev apps (automatic, zero config required):
1. **Ollama** — default, always available, no API key needed (`qwen2.5:7b`)
2. **OpenRouter `:free`** — if `OPENROUTER_API_KEY` is set
3. **Paid models** — if a paid key is configured

**Never use** `nvidia/nemotron-3-super-120b-a12b:free` — it is a reasoning-only
model that returns `content: null`. Any code reading `response.content` will crash.

#### Deep Reference

- Primitives API & patterns: [`docs/agent-guides/primitives-patterns.md`](../../docs/agent-guides/primitives-patterns.md)
- Python standards: [`docs/agent-guides/python-standards.md`](../../docs/agent-guides/python-standards.md)
- LLM provider strategy: [`docs/agent-guides/llm-provider-strategy.md`](../../docs/agent-guides/llm-provider-strategy.md)
- TODO management: [`docs/agent-guides/todo-management.md`](../../docs/agent-guides/todo-management.md)
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/core-conventions/SKILL.md
git commit -m "docs(skills): add LLM provider strategy section to core-conventions"
```

---

## Task 7: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

Changes:
1. Add `session-start` to the Agent Skills table
2. Add **Session Start Protocol** section after the SDD Mandate
3. Add **Orient Before Edit** rule to the Non-Negotiable Standards

- [ ] **Step 1: Add session-start to the skills table**

In the `## Agent Skills (Tier 2)` section, add a row to the table:

```markdown
| [session-start](.claude/skills/session-start/SKILL.md) | Start of every session — load directives, mental models, CGC orientation |
```

- [ ] **Step 2: Add Session Start Protocol section**

Add this section immediately after `## SDD Mandate`:

```markdown
## Session Start Protocol

**Every session begins with `/session-start`** (or the session-start skill steps manually).

1. `mcp__hindsight__recall` — query `tta-dev` bank for directives + mental models
2. `mcp__codegraphcontext__get_repository_stats` — confirm graph is current
3. Acknowledge what was loaded before any task work begins

**Every significant task ends with `mcp__hindsight__retain`** to the `tta-dev` bank:
decisions made, patterns used, failures encountered.
```

- [ ] **Step 3: Add Orient Before Edit to Non-Negotiable Standards**

In the `## Non-Negotiable Standards (Quick Reference)` section, add:

```markdown
- **Orient before edit:** Run CGC (`find_code` + `analyze_code_relationships`) on any non-trivial target before touching it
- **Retain after task:** Store decisions, patterns, failures to `tta-dev` Hindsight bank after each significant task
```

- [ ] **Step 4: Verify CLAUDE.md structure**

Read `CLAUDE.md` and confirm:
- `session-start` appears in the Agent Skills table
- Session Start Protocol section exists after SDD Mandate
- Orient before edit and Retain after task appear in Non-Negotiable Standards

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude-md): add session-start protocol and orient-before-edit mandate"
```

---

## Task 8: End-to-end verification

- [ ] **Step 1: Verify all Hindsight content is recalled**

Call `mcp__hindsight__recall` (bank_id: `tta-dev`, query: `dev loop orient recall validate retain directive`).
Expected: returns the dev-loop directive content.

Call `mcp__hindsight__recall` (bank_id: `tta-dev`, query: `WorkflowPrimitive InstrumentedPrimitive primitives architecture`).
Expected: returns the primitives mental model content.

Call `mcp__hindsight__recall` (bank_id: `tta-dev`, query: `nemotron bad model openrouter ollama`).
Expected: returns the model-strategy directive mentioning nemotron.

- [ ] **Step 2: Verify skills exist**

```bash
ls .claude/skills/session-start/SKILL.md
grep "orient" .claude/skills/build-test-verify/SKILL.md
grep "LLM Provider" .claude/skills/core-conventions/SKILL.md
grep "session-start" CLAUDE.md
```
All four should return results.

- [ ] **Step 3: Verify no stale paths remain in skills**

```bash
grep -r "platform/" .claude/skills/ && echo "STALE PATH FOUND" || echo "clean"
grep -r "from primitives\." .claude/skills/ && echo "STALE IMPORT FOUND" || echo "clean"
```
Both should print `clean`.

- [ ] **Step 4: Final commit of plan**

```bash
git add docs/superpowers/plans/2026-03-20-phase1-protocol.md
git commit -m "docs: add Phase 1 protocol implementation plan"
```

---

## What comes next (out of scope for this plan)

Phases 2–4 each require their own SDD spec before any code is written:

| Phase | First step | Key deliverable |
|---|---|---|
| **Phase 2a** | `/specify CodeGraphPrimitive` | `ttadev/primitives/code_graph/` wrapping CGC MCP |
| **Phase 2b** | `/specify AgentMemory` | `ttadev/primitives/memory/` + AgentPrimitive integration |
| **Phase 3** | `/specify DevelopmentCycle` | `ttadev/workflows/development_cycle.py` |
| **Phase 4** | `/specify session-start-hook` | `settings.json` hook + pre-commit + CI E2B step |

The Phase 1 protocol validates the loop manually. Once it proves out in practice, the Phase 2 specs can be written with concrete requirements drawn from real usage.
