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


def _default_transform(r: DevelopmentResult) -> str:
    return r["response"]


_DEFAULT_TRANSFORM: Callable[[DevelopmentResult], str] = _default_transform


class PipelineTask(TypedDict, total=False):
    """Input task for AgentPipeline. Only ``instruction`` is required."""

    instruction: str  # Required: initial instruction for stage 0
    provider_chain: list[LLMClientConfig]  # Optional: forwarded to all stages
    quality_threshold: float  # Optional: forwarded to all stages


class PipelineResult(TypedDict):
    """Output from an AgentPipeline execution."""

    stages: list[DevelopmentResult]  # One entry per completed stage
    final_response: str  # stages[-1]["response"] or "" if no stage ran
    completed_stages: int  # Number of stages that ran (0–N)
    stopped_early: bool  # True if min_confidence triggered early exit


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

    async def _execute_impl(self, task: PipelineTask, context: WorkflowContext) -> PipelineResult:
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
