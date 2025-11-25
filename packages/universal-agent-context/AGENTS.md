# Universal Agent Context (UAC) – Package Agent Instructions

**Scope:** This file is specific to the `packages/universal-agent-context` package **inside TTA.dev**.

- For **global** TTA.dev guidance (workspace layout, TODO system, testing rules), always start with the root [`AGENTS.md`](../../AGENTS.md).
- This file explains how to work with the **Universal Agent Context primitives** and how they integrate with `tta-dev-primitives`.

---

## 1. What This Package Provides

The **Universal Agent Context (UAC)** package gives you higher‑level primitives and context conventions for multi‑agent workflows built on top of `tta-dev-primitives`:

1. **Python primitives** (production code)
   - `AgentCoordinationPrimitive` – coordinate multiple agents in parallel
   - `AgentHandoffPrimitive` – explicit handoff between agents in a workflow
   - `AgentMemoryPrimitive` – simple architectural/decision memory on top of `WorkflowContext`

2. **Context instruction bundles** (exportable to other projects)
   - `.augment/` – Augment‑CLI–optimized instructions, chat modes, and workflows
   - `.github/` – cross‑platform instructions for Copilot, Claude, Gemini, Augment, etc.

This package is **one of the three production packages** in TTA.dev and is included in the uv workspace.

---

## 2. Python Primitives Overview

All UAC primitives are standard `WorkflowPrimitive` implementations and compose naturally with the rest of `tta-dev-primitives`.

**Location:**

- `packages/universal-agent-context/src/universal_agent_context/primitives/coordination.py`
- `packages/universal-agent-context/src/universal_agent_context/primitives/handoff.py`
- `packages/universal-agent-context/src/universal_agent_context/primitives/memory.py`

### 2.1 AgentCoordinationPrimitive

**Purpose:** Coordinate multiple agent primitives running in parallel and aggregate their results.

- **Class:** `AgentCoordinationPrimitive`
- **Module:** `universal_agent_context.primitives.coordination`
- **Signature:**
  - `input: dict[str, Any]`
  - `output: dict[str, Any]` with keys:
    - `agent_results`
    - `coordination_metadata`
    - `aggregated_result`
    - `failed_agents`

**Key constructor arguments:**

- `agent_primitives: dict[str, WorkflowPrimitive]`
- `coordination_strategy: "aggregate" | "first" | "consensus"`
- `timeout_seconds: float | None`
- `require_all_success: bool`

**Example (simplified):**

<augment_code_snippet path="packages/universal-agent-context/src/universal_agent_context/primitives/coordination.py" mode="EXCERPT">
````python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext
from universal_agent_context.primitives.coordination import AgentCoordinationPrimitive

agents = {"analyzer": analyzer_primitive, "validator": validator_primitive}

coordinator = AgentCoordinationPrimitive(
    agent_primitives=agents,
    coordination_strategy="aggregate",
    require_all_success=False,
)

workflow = prepare_data >> coordinator >> aggregate_results
context = WorkflowContext(workflow_id="uac-demo")
result = await workflow.execute({"input": payload}, context)
````
</augment_code_snippet>

### 2.2 AgentHandoffPrimitive

**Purpose:** Record and manage handoff of responsibility from one agent to another.

- **Class:** `AgentHandoffPrimitive`
- **Module:** `universal_agent_context.primitives.handoff`
- **Context effects:**
  - Appends to `context.metadata["agent_history"]`
  - Updates `context.metadata["current_agent"]`
  - Adds `handoff_timestamp` and `handoff_reason`
  - Adds a checkpoint `handoff_to_{target_agent}`

**Key constructor arguments:**

- `target_agent: str`
- `handoff_strategy: "immediate" | "queued" | "conditional"`
- `preserve_context: bool`
- `handoff_callback: Optional[Callable]` (async)

**Usage pattern:**

<augment_code_snippet path="packages/universal-agent-context/src/universal_agent_context/primitives/handoff.py" mode="EXCERPT">
````python
from universal_agent_context.primitives.handoff import AgentHandoffPrimitive

handoff = AgentHandoffPrimitive(
    target_agent="specialist",
    handoff_strategy="immediate",
    preserve_context=True,
)

workflow = intake >> triage >> handoff >> specialist_analysis
````
</augment_code_snippet>

### 2.3 AgentMemoryPrimitive

**Purpose:** Lightweight, context‑aware memory for architectural decisions and important facts.

- **Class:** `AgentMemoryPrimitive`
- **Module:** `universal_agent_context.primitives.memory`
- **Storage:**
  - Defaults to `context.metadata["agent_memory"]`
  - Supports scopes: `"workflow"`, `"session"`, `"global"`

**Operations:**

- `operation="store"` – store a memory entry
- `operation="retrieve"` – retrieve an entry by key
- `operation="query"` – query by `tags` and/or `agent`
- `operation="list"` – list all entries in the given scope

**Example (store + retrieve):**

<augment_code_snippet path="packages/universal-agent-context/src/universal_agent_context/primitives/memory.py" mode="EXCERPT">
````python
from universal_agent_context.primitives.memory import AgentMemoryPrimitive

store_decision = AgentMemoryPrimitive(operation="store", memory_key="architecture_choice")
retrieve_decision = AgentMemoryPrimitive(operation="retrieve", memory_key="architecture_choice")

workflow = analyze_requirements >> store_decision >> implement_solution >> retrieve_decision
````
</augment_code_snippet>

---

## 3. Integration with `tta-dev-primitives`

All UAC primitives are regular `WorkflowPrimitive` instances and therefore:

- Accept a `WorkflowContext` as the second argument to `execute()`
- Can be freely composed with core primitives using `>>` and `|`
- Inherit observability behavior from the underlying primitives and `WorkflowContext` checkpoints

**Key patterns:**

1. Use core primitives for **control flow and reliability**:
   - `SequentialPrimitive`, `ParallelPrimitive`, `ConditionalPrimitive`
   - `RetryPrimitive`, `FallbackPrimitive`, `TimeoutPrimitive`, `CompensationPrimitive` (Saga)

2. Use UAC primitives for **multi‑agent semantics and memory**:
   - Coordinate many agents with `AgentCoordinationPrimitive`
   - Move work between agents with `AgentHandoffPrimitive`
   - Persist architectural decisions with `AgentMemoryPrimitive`

3. Always pass and thread `WorkflowContext` through your workflow:

<augment_code_snippet mode="EXCERPT" path="packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py">
````python
context = WorkflowContext(workflow_id="multi-agent-demo")
result = await (prepare >> coordinator >> summarize).execute(input_data, context)
````
</augment_code_snippet>

---

## 4. Exportable Instruction Bundles

While this file focuses on the **Python primitives**, this package also contains context bundles that can be copied into other repositories:

- `.augment/` – Augment‑specific instructions, workflows, and context tooling
- `.github/` – Cross‑platform instructions (YAML frontmatter, chat modes, prompts)

See [`packages/universal-agent-context/README.md`](README.md) for detailed guidance on how to export these structures to other projects.

These directories are **optional for using the Python primitives inside TTA.dev**; you can safely ignore them when working purely in code.

---

## 5. TODOs and Knowledge Base

For any work on UAC primitives or instruction bundles:

1. Create or update TODOs in the **Logseq journal** for the current day.
2. Tag them with the appropriate package label, for example:

   - `#dev-todo`
   - `package:: universal-agent-context`

3. Link to relevant pages:

   - `[[TTA.dev/Packages/universal-agent-context/TODOs]]`
   - `[[TTA.dev/TODO Architecture]]`

Refer to the root [`AGENTS.md`](../../AGENTS.md) and `.clinerules` for the full TODO and knowledge‑base workflow.

---

## 6. When to Modify This Package

Use this package when you need:

- Multi‑agent workflows that require explicit **coordination**, **handoff**, or **memory**
- Reusable, observable primitives that integrate seamlessly with `tta-dev-primitives`
- Exportable, vendor‑neutral context instructions for AI coding tools

When making changes:

- Prefer **composition** over modifying existing primitives.
- Keep primitives small and focused (follow the same SOLID and style rules as the rest of TTA.dev).
- Maintain or improve test coverage for any new behavior.
