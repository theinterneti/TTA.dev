# MultiAgentOrchestration — Technical Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `AgentPipeline` — a sequential multi-agent pipeline that chains `DevelopmentCycle` instances, routes outputs between stages, supports early exit on low confidence, and emits a unified OTel span.
Spec: `docs/superpowers/specs/2026-03-21-multiagentorchestration.md`

---

## Architecture Overview

```
ttadev/workflows/pipeline.py         ← NEW: AgentPipeline, PipelineTask, PipelineResult
tests/workflows/test_pipeline.py     ← NEW: full coverage
```

No changes to existing files. No new packages. All imports from stdlib + existing `ttadev` code.

---

## Design Decisions

### `AgentPipeline` extends `InstrumentedPrimitive[PipelineTask, PipelineResult]`

Follows the identical pattern as `DevelopmentCycle`. Construction-time validation (empty agents, bad `min_confidence`, wrong `stage_transforms` length). `_execute_impl` iterates agents in order.

### Span management mirrors `DevelopmentCycle`

`DevelopmentCycle` stores `self._dc_tracer = self._tracer` and manually opens a `development_cycle.write` span inside `_execute_impl`. `AgentPipeline` does the same: `self._pipeline_tracer = self._tracer`, opens `agent_pipeline.execute` span inside `_execute_impl`, sets 4 attributes at the end.

### `WorkflowContext` passed unchanged to every stage

Stages share the caller's context. No new context created per stage — the pipeline is transparent to context propagation.

### Stage routing: default transform is `lambda r: r["response"]`

Stored as `list[Callable[[DevelopmentResult], str] | None]` normalised at construction: any `None` entry replaced with the default lambda. This avoids None-checks inside the hot loop.

### `PipelineTask` fields forwarded to each `DevelopmentTask`

`provider_chain` and `quality_threshold` from `PipelineTask` are forwarded to every stage's `DevelopmentTask`. Stage 0 uses the original `instruction`; subsequent stages use the transform output.

### Early exit check: after each stage, before the next

```python
if min_confidence is not None and stage_result["confidence"] < min_confidence:
    stopped_early = True
    break
```

`min_confidence=0.0` → condition `confidence < 0.0` is always `False` → never stops early.

---

## Full Implementation

### `ttadev/workflows/pipeline.py`

```python
"""AgentPipeline — sequential multi-agent pipeline for DevelopmentCycle composition."""

from __future__ import annotations

import logging
from collections.abc import Callable
from contextlib import nullcontext
from typing import Any, TypedDict

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.observability import InstrumentedPrimitive
from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentResult, DevelopmentTask
from ttadev.workflows.llm_provider import LLMClientConfig

logger = logging.getLogger(__name__)

_DEFAULT_TRANSFORM: Callable[[DevelopmentResult], str] = lambda r: r["response"]


class PipelineTask(TypedDict, total=False):
    """Input task for AgentPipeline.

    Only ``instruction`` is required. All other fields are optional.
    """

    instruction: str                       # Required: initial instruction for stage 0
    provider_chain: list[LLMClientConfig]  # Optional: forwarded to all stages
    quality_threshold: float               # Optional: forwarded to all stages


class PipelineResult(TypedDict):
    """Output from an AgentPipeline execution."""

    stages: list[DevelopmentResult]  # One entry per completed stage
    final_response: str              # stages[-1]["response"] or "" if no stage ran
    completed_stages: int            # Number of stages that ran (0–N)
    stopped_early: bool              # True if min_confidence triggered early exit


class AgentPipeline(InstrumentedPrimitive[PipelineTask, PipelineResult]):
    """Sequential pipeline that chains DevelopmentCycle agents.

    Runs agents in order. Each stage's response becomes the next stage's
    instruction (or a custom transform can be applied). Stops early if any
    stage's confidence falls below min_confidence.

    Args:
        agents: Ordered list of DevelopmentCycle instances (minimum 1).
        min_confidence: If set, halt after any stage with confidence < this value.
            Must be in [0.0, 1.0]. None means never stop early.
        stage_transforms: Per-stage callables mapping DevelopmentResult → str.
            Length must equal len(agents) if provided. None entries use default
            (lambda r: r["response"]).
    """

    def __init__(
        self,
        agents: list[DevelopmentCycle],
        *,
        min_confidence: float | None = None,
        stage_transforms: list[Callable[[DevelopmentResult], str] | None] | None = None,
    ) -> None:
        super().__init__(name="AgentPipeline")
        if not agents:
            raise ValueError("AgentPipeline requires at least one agent")
        if min_confidence is not None and not (0.0 <= min_confidence <= 1.0):
            raise ValueError("min_confidence must be in [0.0, 1.0]")
        if stage_transforms is not None and len(stage_transforms) != len(agents):
            raise ValueError("stage_transforms length must equal len(agents)")
        self._agents = agents
        self._min_confidence = min_confidence
        self._transforms: list[Callable[[DevelopmentResult], str]] = [
            t if t is not None else _DEFAULT_TRANSFORM
            for t in (stage_transforms or [None] * len(agents))
        ]
        self._pipeline_tracer = self._tracer

    async def _execute_impl(
        self, task: PipelineTask, context: WorkflowContext
    ) -> PipelineResult:
        instruction = task.get("instruction", "")
        if not instruction:
            raise ValueError("instruction must not be empty")
        provider_chain = task.get("provider_chain")
        quality_threshold = task.get("quality_threshold")

        span_cm: Any = (
            self._pipeline_tracer.start_as_current_span("agent_pipeline.execute")
            if self._pipeline_tracer
            else nullcontext()
        )
        with span_cm as span:
            stages: list[DevelopmentResult] = []
            stopped_early = False
            current_instruction = instruction

            for i, agent in enumerate(self._agents):
                stage_task = DevelopmentTask(instruction=current_instruction)
                if provider_chain is not None:
                    stage_task["provider_chain"] = provider_chain
                if quality_threshold is not None:
                    stage_task["quality_threshold"] = quality_threshold

                stage_result = await agent.execute(stage_task, context)
                stages.append(stage_result)

                if (
                    self._min_confidence is not None
                    and stage_result["confidence"] < self._min_confidence
                ):
                    logger.info(
                        "AgentPipeline: stage %d confidence %.2f below min %.2f — stopping early",
                        i,
                        stage_result["confidence"],
                        self._min_confidence,
                    )
                    stopped_early = True
                    break

                # Prepare next stage's instruction (skip after last stage)
                if i < len(self._agents) - 1:
                    current_instruction = self._transforms[i + 1](stage_result)

            final_confidence = stages[-1]["confidence"] if stages else 0.0
            if span is not None:
                span.set_attribute("pipeline.agent_count", len(self._agents))
                span.set_attribute("pipeline.completed_stages", len(stages))
                span.set_attribute("pipeline.stopped_early", stopped_early)
                span.set_attribute("pipeline.final_confidence", final_confidence)

            return PipelineResult(
                stages=stages,
                final_response=stages[-1]["response"] if stages else "",
                completed_stages=len(stages),
                stopped_early=stopped_early,
            )
```

---

## OTel Span

The `agent_pipeline.execute` span is a child of whatever span `InstrumentedPrimitive.execute()` creates (if any). Each stage's `DevelopmentCycle.execute()` creates its own child spans under this one automatically:

```
agent_pipeline.execute
├── development_cycle.orient    (stage 0)
├── development_cycle.recall    (stage 0)
├── development_cycle.write     (stage 0)
├── development_cycle.orient    (stage 1)
└── ...
```

---

## Test Plan Summary

### `tests/workflows/test_pipeline.py` (~25 tests across 5 classes)

**`TestAgentPipelineConstruction`** (~6 tests)

| Test | Scenario |
|------|----------|
| `test_constructs_with_one_agent` | Single-agent pipeline works |
| `test_constructs_with_multiple_agents` | 3-agent pipeline works |
| `test_empty_agents_raises` | `agents=[]` → `ValueError` at construction |
| `test_min_confidence_out_of_range_raises` | `min_confidence=1.5` → `ValueError` at construction |
| `test_stage_transforms_wrong_length_raises` | `stage_transforms` length ≠ `len(agents)` → `ValueError` |
| `test_none_transforms_use_default` | `None` entries replaced with default transform |

**`TestAgentPipelineExecution`** (~7 tests)

| Test | Scenario |
|------|----------|
| `test_single_stage_result` | One agent → `completed_stages=1`, `stopped_early=False` |
| `test_two_stage_output_routing` | Stage 0 response becomes stage 1 instruction |
| `test_final_response_is_last_stage` | `final_response == stages[-1]["response"]` |
| `test_provider_chain_forwarded` | `PipelineTask.provider_chain` passed to each stage |
| `test_quality_threshold_forwarded` | `PipelineTask.quality_threshold` passed to each stage |
| `test_empty_instruction_raises` | `instruction=""` → `ValueError` at execute time |
| `test_three_stage_pipeline` | All 3 stages run, `completed_stages=3` |

**`TestAgentPipelineEarlyExit`** (~5 tests)

| Test | Scenario |
|------|----------|
| `test_stops_after_low_confidence_stage` | Stage 0 confidence < `min_confidence` → stage 1 never runs |
| `test_stopped_early_is_true` | `result["stopped_early"] == True` |
| `test_completed_stages_reflects_stop` | `completed_stages == 1` when stopped after stage 0 |
| `test_no_early_exit_when_confidence_ok` | All stages above `min_confidence` → `stopped_early=False` |
| `test_min_confidence_zero_never_stops` | `min_confidence=0.0` → all stages always run |

**`TestAgentPipelineTransforms`** (~4 tests)

| Test | Scenario |
|------|----------|
| `test_custom_transform_applied` | Custom transform output used as next instruction |
| `test_default_transform_uses_response` | `None` transform → uses `r["response"]` |
| `test_transform_called_with_correct_result` | Transform receives the correct `DevelopmentResult` |
| `test_mixed_transforms` | Some None, some custom — both applied correctly |

**`TestAgentPipelineOTel`** (~3 tests)

| Test | Scenario |
|------|----------|
| `test_span_attributes_set` | All 4 `pipeline.*` attributes present |
| `test_span_completed_stages_matches_result` | `pipeline.completed_stages == result["completed_stages"]` |
| `test_no_span_when_tracer_none` | `_tracer=None` → executes without error |

---

## Task Breakdown

### Task 1 — `AgentPipeline` core + basic execution (independent)

- [ ] Create `ttadev/workflows/pipeline.py` with `PipelineTask`, `PipelineResult`, `AgentPipeline`
- [ ] Add construction-time validation (empty agents, bad `min_confidence`, wrong transform length)
- [ ] Implement `_execute_impl`: iterate agents, route output, build `PipelineResult`
- [ ] Add OTel span with 4 attributes
- [ ] Create `tests/workflows/test_pipeline.py` with `TestAgentPipelineConstruction` (6 tests) + `TestAgentPipelineExecution` (7 tests)
- [ ] Run `uv run pytest tests/workflows/test_pipeline.py -v` — all pass
- [ ] Run `uvx pyright ttadev/workflows/pipeline.py` — 0 errors
- [ ] Run `uv run ruff check ttadev/workflows/pipeline.py --fix` — clean
- [ ] Commit: `feat(multi-agent): add AgentPipeline with sequential execution and OTel span`

### Task 2 — Early exit on `min_confidence` (depends on Task 1)

- [ ] Add `min_confidence` check inside the agent loop in `_execute_impl`
- [ ] Set `stopped_early = True` and `break` when triggered
- [ ] Ensure `pipeline.stopped_early` span attribute reflects the result
- [ ] Add `TestAgentPipelineEarlyExit` with 5 tests
- [ ] Run `uv run pytest tests/workflows/test_pipeline.py -v` — all pass
- [ ] Run `uvx pyright ttadev/workflows/pipeline.py` — 0 errors
- [ ] Run `uv run ruff check ttadev/workflows/pipeline.py --fix` — clean
- [ ] Commit: `feat(multi-agent): add early exit on min_confidence threshold`

### Task 3 — Stage transforms (depends on Task 1)

- [ ] Add `stage_transforms` parameter to `__init__`, normalise `None` → default lambda at construction
- [ ] Apply `self._transforms[i + 1](stage_result)` when routing to next stage
- [ ] Add `TestAgentPipelineTransforms` with 4 tests + `TestAgentPipelineOTel` with 3 tests
- [ ] Run `uv run pytest tests/workflows/test_pipeline.py -v` — all pass
- [ ] Run `uvx pyright ttadev/workflows/pipeline.py` — 0 errors
- [ ] Run `uv run ruff check ttadev/workflows/pipeline.py --fix` — clean
- [ ] Commit: `feat(multi-agent): add stage_transforms for custom output routing`

---

## Dependencies

```
Task 1 ─── independent
Task 2 ─── depends on Task 1 (min_confidence check needs the agent loop)
Task 3 ─── depends on Task 1 (transforms apply inside the agent loop)
```

Tasks 2 and 3 can be executed in parallel after Task 1.

---

## Quality Gate (before each commit)

```bash
uv run pytest tests/workflows/ -v                              # all pass
uvx pyright ttadev/workflows/                                  # 0 errors
uv run ruff check ttadev/workflows/ --fix                      # clean
uv run pytest tests/workflows/ --cov=ttadev/workflows/pipeline.py --cov-report=term-missing
```
