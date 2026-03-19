# Technical Plan: Phase 3 — Guided Workflow System

**Phase:** SDD Phase 2 (Technical Plan)
**Status:** Draft
**Date:** 2026-03-19
**Spec:** [phase3-guided-workflow-system.md](phase3-guided-workflow-system.md)

---

## 1. Packages Affected

| Package / Module | Change |
|---|---|
| `ttadev/workflows/` | **New package** — entire Phase 3 implementation |
| `ttadev/primitives/core/base.py` | **Modified** — add `memory: WorkflowMemory \| None` field to `WorkflowContext` |
| `ttadev/cli/__init__.py` | **Modified** — register `workflow` subcommand |
| `ttadev/cli/workflow.py` | **New** — `tta workflow list/show/run` handlers |
| `pyproject.toml` | **Modified** — add `hindsight-client` optional dep |

No changes to `ttadev/agents/`, `ttadev/primitives/` (recovery, observability), or
`ttadev/integrations/`.

---

## 2. New Package: `ttadev/workflows/`

```
ttadev/workflows/
├── __init__.py          # Public exports
├── definition.py        # WorkflowStep, WorkflowDefinition, WorkflowResult, StepResult
├── memory.py            # WorkflowMemory (Tier 1) + PersistentMemory (Tier 2, Hindsight)
├── gate.py              # ApprovalGate — blocking I/O, non-TTY auto-approve
├── orchestrator.py      # WorkflowOrchestrator — static + dynamic modes
└── prebuilt.py          # feature_dev_workflow definition
```

---

## 3. Module Designs

### 3.1 `definition.py`

```python
@dataclass(frozen=True)
class WorkflowStep:
    agent: str                          # registered agent name
    gate: bool = True                   # pause for approval before next step
    input_transform: Callable[[WorkflowState], AgentTask] | None = None

@dataclass(frozen=True)
class MemoryConfig:
    flush_to_persistent: bool = True    # write WorkflowMemory to Hindsight on complete
    bank_id: str | None = None          # override; defaults to tta.workflow.<name>

@dataclass(frozen=True)
class WorkflowDefinition:
    name: str
    description: str
    steps: list[WorkflowStep]
    auto_approve: bool = False          # bypass all gates
    memory_config: MemoryConfig = field(default_factory=MemoryConfig)

@dataclass
class StepResult:
    step_index: int
    agent_name: str
    result: AgentResult
    skipped: bool = False
    gate_decision: str = "continue"     # "continue" | "skip" | "edit" | "quit"

@dataclass
class WorkflowResult:
    workflow_name: str
    goal: str
    steps: list[StepResult]
    artifacts: list[Artifact]           # aggregated from all steps
    memory_snapshot: dict               # final WorkflowMemory state
    completed: bool                     # False if user quit early
    total_confidence: float             # mean across steps
```

### 3.2 `memory.py`

**Tier 1 — `WorkflowMemory` (in-context, per-session):**

```python
class WorkflowMemory:
    """In-context key/value store passed across workflow steps.

    Lives on WorkflowContext.memory. Cleared when run completes
    (unless flushed to PersistentMemory).
    """
    def set(self, key: str, value: Any) -> None: ...
    def get(self, key: str, default: Any = None) -> Any: ...
    def append(self, key: str, value: Any) -> None: ...   # appends to list
    def snapshot(self) -> dict[str, Any]: ...             # safe copy for agent context
```

**Tier 2 — `PersistentMemory` (cross-session, Hindsight-backed):**

```python
class PersistentMemory:
    """Cross-session memory backed by Hindsight.

    Wraps hindsight-client with graceful degradation:
    if the server is unreachable, all methods are no-ops and
    a warning is logged once per process.
    """
    def __init__(self, base_url: str = "http://localhost:8888") -> None: ...

    def retain(self, bank_id: str, content: str) -> None: ...
    def recall(self, bank_id: str, query: str) -> list[str]: ...
    def reflect(self, bank_id: str, query: str) -> str: ...
```

**Bank ID conventions:** `tta.<agent_name>` (per-agent), `tta.workflow.<name>` (per-workflow).

### 3.3 `gate.py`

```python
class GateDecision(StrEnum):
    CONTINUE = "continue"
    SKIP = "skip"
    EDIT = "edit"
    QUIT = "quit"

class ApprovalGate:
    """Human-in-the-loop checkpoint after a step completes.

    Rendering (via _render) and prompt (via _prompt_user) are separate
    so tests can subclass and capture output without touching stdin.
    """
    def __init__(self, auto_approve: bool = False) -> None: ...

    async def check(
        self,
        step_result: StepResult,
        total_steps: int,
        *,
        next_agent: str | None,
    ) -> tuple[GateDecision, str | None]:
        """Returns (decision, edited_instruction | None).

        Runs _prompt_user() in asyncio executor (non-blocking).
        If stdin is not a TTY, returns CONTINUE with a log warning.
        If auto_approve=True, returns CONTINUE immediately.
        """
```

Display format (spec Journey 4):
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Step {i}/{n} complete: {agent_name}
  Confidence: {pct}%  |  Quality gates: {status}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {output_preview — first 500 chars}
  ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Next step: {next_agent} — {next_description}
  [Enter] continue   [s] skip   [e] edit   [q] quit   [?] full output
>
```

### 3.4 `orchestrator.py`

```python
@dataclass(frozen=True)
class WorkflowGoal:
    goal: str
    context: dict[str, Any] = field(default_factory=dict)

class WorkflowOrchestrator(InstrumentedPrimitive[WorkflowGoal, WorkflowResult]):
    """Executes a WorkflowDefinition (static) or plans steps dynamically (dynamic).

    Extends InstrumentedPrimitive → fully composable with >> and |.

    Static mode: steps come from WorkflowDefinition.steps in order.
    Dynamic mode: conductor model decides next step after each result.
    """
    def __init__(
        self,
        definition: WorkflowDefinition,
        memory: PersistentMemory | None = None,
        model: ChatPrimitive | None = None,   # conductor model; None = static mode only
    ) -> None: ...

    async def _execute_impl(
        self, goal: WorkflowGoal, context: WorkflowContext
    ) -> WorkflowResult: ...
```

**Execution flow:**

```
_execute_impl:
  1. Attach WorkflowMemory to context.memory
  2. For each step (static) or conductor-planned step (dynamic):
     a. Build AgentTask from goal + previous StepResult + memory.snapshot()
        (or call input_transform if provided)
     b. Resolve agent from registry; execute with child context
     c. Append result to WorkflowMemory
     d. If gate=True and not auto_approve: call ApprovalGate.check()
        - CONTINUE: proceed
        - SKIP: mark step skipped, proceed
        - EDIT: rebuild AgentTask with edited instruction; re-run step
        - QUIT: set completed=False, break
     e. Emit approval_gate.{agent_name} span event
  3. If memory_config.flush_to_persistent: PersistentMemory.retain() key decisions
  4. Aggregate artifacts; compute total_confidence; return WorkflowResult
```

### 3.5 `prebuilt.py`

```python
feature_dev_workflow = WorkflowDefinition(
    name="feature_dev",
    description="Implement a feature end-to-end: code → tests → security → commit → PR",
    steps=[
        WorkflowStep(agent="developer", gate=True),
        WorkflowStep(agent="qa",        gate=True),
        WorkflowStep(agent="security",  gate=True),
        WorkflowStep(agent="git",       gate=True),
        WorkflowStep(agent="github",    gate=True),
    ],
    memory_config=MemoryConfig(flush_to_persistent=True),
)
```

---

## 4. WorkflowContext Modification

Add one field to `ttadev/primitives/core/base.py`:

```python
@dataclass
class WorkflowContext:
    # ... existing fields ...
    memory: WorkflowMemory | None = None   # set by WorkflowOrchestrator._execute_impl
```

`WorkflowMemory` is imported lazily (inside `TYPE_CHECKING` block or at call site) to avoid
a circular import between `primitives` and `workflows`.

---

## 5. LLM Provider Strategy

All LLM calls within Phase 3 (orchestrator conductor, `PersistentMemory.reflect()`) follow
the project-wide strategy: **OpenRouter free models first, Ollama fallback.**

See [llm-provider-strategy](../agent-guides/llm-provider-strategy.md) for the full model
rotation list, rate limit context, and Ollama setup. The `get_llm_client()` helper
(see §6 below) encapsulates this so no Phase 3 code hard-codes a provider.

## 6. External Dependency

Add `hindsight-client` as an optional dependency in `pyproject.toml`:

```toml
[project.optional-dependencies]
memory = [
    "hindsight-client>=0.1.0",
]
```

`PersistentMemory` guards the import:

```python
try:
    from hindsight_client import Hindsight  # type: ignore[import]
    _HINDSIGHT_AVAILABLE = True
except ImportError:
    _HINDSIGHT_AVAILABLE = False
```

If unavailable (import error) or unreachable (connection error), all `PersistentMemory`
methods are no-ops. A module-level `_warned` flag prevents repeated log noise.

---

## 6. CLI: `tta workflow`

New file `ttadev/cli/workflow.py` following the pattern of `session.py` / `project.py`.

### Parser registration (added to `ttadev/cli/__init__.py`):

```
tta workflow list
tta workflow show <name>
tta workflow run <name> --goal "..." [--no-confirm] [--dry-run]
```

`--no-confirm` sets `auto_approve=True`.
`--dry-run` prints the step plan without executing.

### Handler:

```python
def register_workflow_subcommands(sub: argparse._SubParsersAction) -> None: ...
def handle_workflow_command(args: argparse.Namespace, data_dir: Path) -> int: ...
```

`run` uses `asyncio.run()` to call `WorkflowOrchestrator._execute_impl()`.

---

## 7. Composition with `>>` and `|`

`WorkflowOrchestrator` extends `InstrumentedPrimitive[WorkflowGoal, WorkflowResult]`,
so it inherits `>>` and `|` from `WorkflowPrimitive`:

```python
# Chain two workflows sequentially
full_pipeline = feature_dev_workflow_orch >> deploy_workflow_orch

# Run review pipelines in parallel
review = security_review_orch | qa_review_orch
```

No changes to composition primitives needed.

---

## 8. Observability Strategy

Span tree produced by a 3-step workflow:

```
workflow.feature_dev                        [root span]
  ├── workflow.step.developer               [child span — InstrumentedPrimitive]
  │   └── agent.developer                  [child span — AgentPrimitive]
  ├── workflow.gate.developer               [event span — gate decision recorded]
  ├── workflow.step.qa                      [child span]
  │   └── agent.qa
  ├── workflow.gate.qa
  ...
```

**Span attributes** on `workflow.gate.*`:
- `gate.decision`: `"continue"` | `"skip"` | `"edit"` | `"quit"`
- `gate.step_index`: int
- `gate.agent_name`: str
- `gate.auto_approved`: bool

**Memory spans** (added to `WorkflowOrchestrator._execute_impl`):
- `memory.backend`: `"hindsight"` | `"none"`
- `memory.query`: search string (on recall)
- `memory.hit_count`: int (on recall)

All spans follow the existing `InstrumentedPrimitive` pattern — checkpoint recording,
trace context injection, graceful degradation if OpenTelemetry is absent.

---

## 9. Test Plan

| Test file | What it covers |
|---|---|
| `tests/workflows/test_definition.py` | Dataclass construction, frozen invariants, default values |
| `tests/workflows/test_memory.py` | WorkflowMemory CRUD + snapshot; PersistentMemory no-op when Hindsight absent |
| `tests/workflows/test_gate.py` | Non-TTY auto-approve; auto_approve=True; mocked stdin for each decision (Enter/s/e/q/?) |
| `tests/workflows/test_orchestrator.py` | Static 3-step run, CONTINUE; SKIP a step; QUIT early; memory snapshot passed to each step; WorkflowResult aggregation |
| `tests/workflows/test_prebuilt.py` | feature_dev_workflow is a valid WorkflowDefinition with 5 steps; all agent names registered |
| `tests/cli/test_workflow_cli.py` | `tta workflow list`; `tta workflow show feature_dev`; `tta workflow run --dry-run`; `--no-confirm` sets auto_approve |

Mock strategy: inject a `FakeModel` (returns canned AgentResult); override registry with test agents; capture stdout for display assertions.

---

## 10. Decisions

1. **`WorkflowGoal` as input type**: Rather than reusing `AgentTask` as the orchestrator's
   input, a new `WorkflowGoal(goal, context)` dataclass is introduced. This is cleaner
   (no `instruction`/`constraints` fields that don't apply) and signals intent at the type level.

2. **`memory` on WorkflowContext**: Per spec Decision 2. The field is `None` by default
   so existing code that constructs `WorkflowContext()` without memory is unaffected.
   Circular import risk is managed by the lazy import pattern.

3. **`ApprovalGate` as a class, not a free function**: Allows `auto_approve` to be
   baked in at construction time (matching the `WorkflowDefinition.auto_approve` flag)
   and allows test subclassing to intercept `_prompt_user`.

4. **Argparse (not Click)**: Consistent with the existing CLI. All other subcommands
   use argparse; introducing Click would create two competing patterns.

5. **`hindsight-client` as optional dep**: Keeps the core package lightweight. Users who
   don't run the Hindsight Docker container don't pull in the client. The `[memory]`
   extra makes the intent explicit.

6. **`WorkflowOrchestrator.__init__` takes a `WorkflowDefinition`**: Rather than
   `WorkflowOrchestrator` being a factory that returns different types, one class handles
   both static and dynamic modes. `model=None` → static; `model=<conductor>` → dynamic.
   Dynamic mode is gated behind the model argument so static mode works with zero LLM cost.
