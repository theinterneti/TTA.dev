# Functional Specification: MultiAgentOrchestration

**Date:** 2026-03-21
**Phase:** 6 — Multi-agent orchestration
**Status:** Approved
**Depends on:** `AgentAutonomy` (Phase 5, complete)
**Leads to:** Phase 7 — Adaptive routing

---

## Overview

`MultiAgentOrchestration` introduces `AgentPipeline`: a sequential composition of `DevelopmentCycle` agents where each stage's output becomes the next stage's input. The caller defines the agent sequence once; the pipeline manages handoffs, confidence gating, and observability automatically.

Three targeted additions:

1. **`AgentPipeline`** — runs a list of `DevelopmentCycle` agents in order, routing each stage's `response` as the next stage's instruction.

2. **Early exit on low confidence** — the pipeline can halt before completing all stages if a stage's confidence falls below a configured minimum, returning the best result seen so far.

3. **Stage transforms** — an optional callable per stage that maps the previous stage's `DevelopmentResult` to the next stage's instruction string. Defaults to `lambda r: r["response"]`.

---

## Motivation

Phase 5 left callers manually chaining agents:

```python
dev_result = await developer.execute(DevelopmentTask(instruction="..."), ctx)
review_result = await reviewer.execute(DevelopmentTask(instruction=dev_result["response"]), ctx)
```

This works but puts boilerplate on every caller: unpacking, error checking, confidence inspection. For an autonomous workflow, the pipeline should manage handoffs so the caller expresses *what* agents to run, not *how* to chain them.

`AgentPipeline` is the missing abstraction: define the agent sequence once, execute once, get a structured result that tells you what each stage produced and where (if anywhere) confidence fell below acceptable.

---

## User Journeys

### Journey 1 — Zero-config dev → review pipeline

```python
from ttadev.workflows.agents import coding_assistant, code_reviewer
from ttadev.workflows.pipeline import AgentPipeline, PipelineTask

pipeline = AgentPipeline([coding_assistant(), code_reviewer()])
result = await pipeline.execute(
    PipelineTask(instruction="add input validation to the user endpoint"),
    WorkflowContext(),
)
# result["stages"][0] — coding_assistant output
# result["stages"][1] — code_reviewer output
# result["final_response"] — last stage's response
# result["completed_stages"] — 2 (both ran)
```

### Journey 2 — Early exit when confidence too low

```python
pipeline = AgentPipeline(
    [coding_assistant(), code_reviewer()],
    min_confidence=0.5,   # stop if any stage produces confidence < 0.5
)
result = await pipeline.execute(
    PipelineTask(instruction="rewrite the circuit breaker primitive"),
    WorkflowContext(),
)
# If coding_assistant returns confidence=0.3 (below 0.5):
# → code_reviewer never runs
# result["completed_stages"] == 1
# result["stopped_early"] == True
# result["final_response"] == coding_assistant's low-confidence response
```

### Journey 3 — Custom stage transform

```python
def add_review_context(prev: DevelopmentResult) -> str:
    """Route coding output to reviewer with explicit review instruction."""
    return f"Review this implementation for correctness and edge cases:\n\n{prev['response']}"

pipeline = AgentPipeline(
    [coding_assistant(), code_reviewer()],
    stage_transforms=[None, add_review_context],  # None = default for stage 0
)
result = await pipeline.execute(
    PipelineTask(instruction="implement rate limiting"),
    WorkflowContext(),
)
```

### Journey 4 — Three-stage pipeline

```python
from ttadev.workflows.agents import coding_assistant, code_reviewer, qa_agent

pipeline = AgentPipeline([coding_assistant(), code_reviewer(), qa_agent()])
result = await pipeline.execute(
    PipelineTask(instruction="add caching to the search endpoint"),
    WorkflowContext(),
)
# result["completed_stages"] == 3
# result["stages"][2]["response"] contains generated tests
```

### Journey 5 — Per-task provider override flows through pipeline

```python
pipeline = AgentPipeline([coding_assistant(), code_reviewer()])
result = await pipeline.execute(
    PipelineTask(
        instruction="refactor the retry primitive",
        provider_chain=[precise_cfg],   # used by all stages
        quality_threshold=0.65,         # used by all stages
    ),
    WorkflowContext(),
)
```

### Journey 6 — Inspecting stage-level results

```python
result = await pipeline.execute(task, ctx)
for i, stage in enumerate(result["stages"]):
    print(f"Stage {i}: confidence={stage['confidence']:.2f} provider={stage['provider']}")
# Stage 0: confidence=0.81 provider=openrouter
# Stage 1: confidence=0.74 provider=openrouter
```

---

## Components

### 1. `PipelineTask` (TypedDict)

```python
class PipelineTask(TypedDict, total=False):
    instruction: str                       # Required: initial instruction for stage 0
    provider_chain: list[LLMClientConfig]  # Optional: passed to all stages
    quality_threshold: float               # Optional: passed to all stages
```

### 2. `PipelineResult` (TypedDict)

```python
class PipelineResult(TypedDict):
    stages: list[DevelopmentResult]   # One entry per completed stage (may be < len(agents))
    final_response: str               # Response from last completed stage
    completed_stages: int             # Number of stages that ran (0–N)
    stopped_early: bool               # True if min_confidence caused early exit
```

### 3. `AgentPipeline`

```python
class AgentPipeline(InstrumentedPrimitive[PipelineTask, PipelineResult]):
    def __init__(
        self,
        agents: list[DevelopmentCycle],
        *,
        min_confidence: float | None = None,
        stage_transforms: list[Callable[[DevelopmentResult], str] | None] | None = None,
    ) -> None: ...
```

- `agents`: ordered list; minimum 1. Validated at construction time.
- `min_confidence`: if set, halt after any stage that produces `confidence < min_confidence`. Must be in [0.0, 1.0] if provided.
- `stage_transforms`: per-stage callables. Length must equal `len(agents)` if provided. `None` entries use the default `lambda r: r["response"]`.

---

## Input/Output Contract

### `PipelineTask` fields

| Field | Type | Default | Behaviour |
|-------|------|---------|-----------|
| `instruction` | `str` | required | Stage 0 instruction |
| `provider_chain` | `list[LLMClientConfig]` | `None` | Forwarded to every stage's `DevelopmentTask` |
| `quality_threshold` | `float` | `None` | Forwarded to every stage's `DevelopmentTask` |

### `PipelineResult` fields

| Field | Type | Meaning |
|-------|------|---------|
| `stages` | `list[DevelopmentResult]` | Per-stage results; length == `completed_stages` |
| `final_response` | `str` | `stages[-1]["response"]` or `""` if no stage ran |
| `completed_stages` | `int` | How many stages ran before stop |
| `stopped_early` | `bool` | `True` if `min_confidence` triggered early exit |

### OTel span (on `agent_pipeline.execute`)

| Attribute | Type | Value |
|-----------|------|-------|
| `pipeline.agent_count` | int | Total agents in pipeline |
| `pipeline.completed_stages` | int | Stages that ran |
| `pipeline.stopped_early` | bool | Whether min_confidence triggered |
| `pipeline.final_confidence` | float | Last completed stage's confidence |

---

## Edge Cases

| Scenario | Behaviour |
|----------|-----------|
| `agents=[]` | Raises `ValueError("AgentPipeline requires at least one agent")` at construction |
| `min_confidence` out of [0.0, 1.0] | Raises `ValueError` at construction |
| `stage_transforms` length ≠ `len(agents)` | Raises `ValueError` at construction |
| Stage transform raises exception | Exception propagates (not swallowed); pipeline aborts |
| All stages produce low confidence | `stopped_early=True` after stage 1, rest skipped |
| `min_confidence=0.0` | Never stops early; all stages always run |
| Single-agent pipeline | Works; `completed_stages=1`, `stopped_early=False` (unless `min_confidence` set) |
| `PipelineTask` has no `instruction` | Raises `ValueError("instruction must not be empty")` |

---

## File Layout

| Action | Path | Purpose |
|--------|------|---------
| Create | `ttadev/workflows/pipeline.py` | `AgentPipeline`, `PipelineTask`, `PipelineResult` |
| Create | `tests/workflows/test_pipeline.py` | Full test coverage |

---

## Out of Scope

- **Branching/conditional pipelines** — agent selection based on stage output (Phase 7)
- **Parallel agent execution** — running agents concurrently (Phase 7)
- **Feedback loops** — routing output back to a prior stage (Phase 7)
- **Dynamic agent insertion** — adding agents to a running pipeline (Phase 7)
- **Cross-stage memory sharing** — agents sharing a single Hindsight bank (Phase 7)
- **Per-stage `provider_chain`/`quality_threshold` override** — `PipelineTask` applies one config to all stages; per-stage overrides deferred to Phase 7

---

## Success Criteria

1. `AgentPipeline([coding_assistant(), code_reviewer()]).execute(task, ctx)` chains dev → review correctly
2. Stage N's `response` becomes stage N+1's `instruction` by default
3. `min_confidence` stops the pipeline after the first stage below threshold
4. `PipelineResult` always has all four fields
5. `stage_transforms` correctly routes output when provided
6. `agents=[]` raises `ValueError` at construction (not at execute time)
7. Single-agent pipeline works identically to calling `DevelopmentCycle.execute` directly
8. `provider_chain` and `quality_threshold` from `PipelineTask` flow to every stage's `DevelopmentTask`
9. OTel span wraps entire pipeline execution with 4 attributes
10. `uvx pyright ttadev/workflows/pipeline.py` — 0 errors
11. 100% coverage on all new code paths
