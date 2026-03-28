"""Unit tests for AgentPipeline — Task 1: construction + basic execution (13 tests)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ttadev.primitives.code_graph import ImpactReport
from ttadev.primitives.core.base import WorkflowContext
from ttadev.workflows.development_cycle import DevelopmentResult
from ttadev.workflows.llm_provider import LLMClientConfig
from ttadev.workflows.pipeline import AgentPipeline, PipelineTask

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_mock_agent(response: str = "mock response", confidence: float = 0.8) -> MagicMock:
    """Create a mock DevelopmentCycle that returns a fixed DevelopmentResult."""
    impact = ImpactReport(
        target="",
        callers=[],
        dependencies=[],
        related_tests=[],
        complexity=0.0,
        risk="low",
        summary="",
        cgc_available=False,
    )
    result = DevelopmentResult(
        response=response,
        validated=False,
        impact_report=impact,
        memories_retained=0,
        context_prefix="",
        confidence=confidence,
        provider="mock",
        retry_count=0,
    )
    agent = MagicMock()
    agent.execute = AsyncMock(return_value=result)
    return agent


# ── Construction tests ────────────────────────────────────────────────────────


class TestAgentPipelineConstruction:
    def test_constructs_with_one_agent(self) -> None:
        agent = _make_mock_agent()
        pipeline = AgentPipeline([agent])
        assert pipeline is not None

    def test_constructs_with_multiple_agents(self) -> None:
        agents = [_make_mock_agent() for _ in range(3)]
        pipeline = AgentPipeline(agents)
        assert pipeline is not None

    def test_empty_agents_raises(self) -> None:
        with pytest.raises(ValueError, match="AgentPipeline requires at least one agent"):
            AgentPipeline([])

    def test_min_confidence_out_of_range_raises(self) -> None:
        agent = _make_mock_agent()
        with pytest.raises(ValueError, match="min_confidence must be in"):
            AgentPipeline([agent], min_confidence=1.5)

    def test_stage_transforms_wrong_length_raises(self) -> None:
        agents = [_make_mock_agent(), _make_mock_agent()]
        fn = lambda r: r["response"]  # noqa: E731
        with pytest.raises(ValueError, match="stage_transforms length must equal len"):
            AgentPipeline(agents, stage_transforms=[fn])

    def test_none_transforms_use_default(self) -> None:
        agent = _make_mock_agent()
        pipeline = AgentPipeline([agent], stage_transforms=[None])
        assert callable(pipeline._transforms[0])


# ── Execution tests ───────────────────────────────────────────────────────────


class TestAgentPipelineExecution:
    async def test_single_stage_result(self) -> None:
        agent = _make_mock_agent(response="output", confidence=0.9)
        pipeline = AgentPipeline([agent])
        result = await pipeline.execute(PipelineTask(instruction="do something"), WorkflowContext())
        assert result["completed_stages"] == 1
        assert result["stopped_early"] is False

    async def test_two_stage_output_routing(self) -> None:
        agent1 = _make_mock_agent(response="stage1 output")
        agent2 = _make_mock_agent(response="stage2 output")
        pipeline = AgentPipeline([agent1, agent2])
        await pipeline.execute(PipelineTask(instruction="start"), WorkflowContext())
        call_args = agent2.execute.call_args[0][0]  # first positional arg = DevelopmentTask
        assert call_args["instruction"] == "stage1 output"

    async def test_final_response_is_last_stage(self) -> None:
        agent1 = _make_mock_agent(response="first")
        agent2 = _make_mock_agent(response="second")
        pipeline = AgentPipeline([agent1, agent2])
        result = await pipeline.execute(PipelineTask(instruction="go"), WorkflowContext())
        assert result["final_response"] == result["stages"][-1]["response"]
        assert result["final_response"] == "second"

    async def test_provider_chain_forwarded(self) -> None:
        agent1 = _make_mock_agent()
        agent2 = _make_mock_agent()
        pipeline = AgentPipeline([agent1, agent2])
        cfg = LLMClientConfig(
            base_url="http://test",
            model="test-model",
            api_key="key",  # pragma: allowlist secret
            provider="test",
        )
        await pipeline.execute(
            PipelineTask(instruction="test", provider_chain=[cfg]), WorkflowContext()
        )
        for mock_agent in (agent1, agent2):
            call_task = mock_agent.execute.call_args[0][0]
            assert call_task["provider_chain"] == [cfg]

    async def test_quality_threshold_forwarded(self) -> None:
        agent1 = _make_mock_agent()
        agent2 = _make_mock_agent()
        pipeline = AgentPipeline([agent1, agent2])
        await pipeline.execute(
            PipelineTask(instruction="test", quality_threshold=0.75), WorkflowContext()
        )
        for mock_agent in (agent1, agent2):
            call_task = mock_agent.execute.call_args[0][0]
            assert call_task["quality_threshold"] == 0.75

    async def test_empty_instruction_raises(self) -> None:
        agent = _make_mock_agent()
        pipeline = AgentPipeline([agent])
        with pytest.raises(ValueError, match="instruction must not be empty"):
            await pipeline.execute(PipelineTask(instruction=""), WorkflowContext())

    async def test_three_stage_pipeline(self) -> None:
        agents = [_make_mock_agent(response=f"stage{i}") for i in range(3)]
        pipeline = AgentPipeline(agents)
        result = await pipeline.execute(PipelineTask(instruction="begin"), WorkflowContext())
        assert result["completed_stages"] == 3
        assert result["stopped_early"] is False
        assert len(result["stages"]) == 3

    async def test_custom_transform_at_stage1(self) -> None:
        def prefix_transform(result: DevelopmentResult) -> str:
            return f"Review this:\n{result['response']}"

        agent0 = _make_mock_agent(response="the implementation")
        agent1 = _make_mock_agent(response="the review")
        pipeline = AgentPipeline([agent0, agent1], stage_transforms=[None, prefix_transform])
        await pipeline.execute(PipelineTask(instruction="build X"), WorkflowContext())
        call_args = agent1.execute.call_args[0][0]
        assert call_args["instruction"] == "Review this:\nthe implementation"


# ── Early exit tests ──────────────────────────────────────────────────────────


class TestAgentPipelineEarlyExit:
    async def test_stops_after_low_confidence_stage(self) -> None:
        """Stage 0 returns confidence=0.3 (below 0.7 threshold).
        Pipeline should stop, agent1 should never be called, completed_stages=1."""
        agent0 = _make_mock_agent(response="stage0", confidence=0.3)
        agent1 = _make_mock_agent(response="stage1", confidence=0.8)
        pipeline = AgentPipeline([agent0, agent1], min_confidence=0.7)
        result = await pipeline.execute(PipelineTask(instruction="start"), WorkflowContext())
        assert agent1.execute.call_count == 0
        assert result["completed_stages"] == 1

    async def test_stopped_early_is_true(self) -> None:
        """Same setup: stage 0 returns confidence=0.3 (below 0.7).
        Assert stopped_early is True."""
        agent0 = _make_mock_agent(response="stage0", confidence=0.3)
        agent1 = _make_mock_agent(response="stage1", confidence=0.8)
        pipeline = AgentPipeline([agent0, agent1], min_confidence=0.7)
        result = await pipeline.execute(PipelineTask(instruction="start"), WorkflowContext())
        assert result["stopped_early"] is True

    async def test_completed_stages_reflects_stop(self) -> None:
        """3-agent pipeline, min_confidence=0.6.
        Stage 0 confidence=0.8 (ok), stage 1 confidence=0.4 (below).
        Agent2 should never be called, completed_stages=2."""
        agent0 = _make_mock_agent(response="stage0", confidence=0.8)
        agent1 = _make_mock_agent(response="stage1", confidence=0.4)
        agent2 = _make_mock_agent(response="stage2", confidence=0.9)
        pipeline = AgentPipeline([agent0, agent1, agent2], min_confidence=0.6)
        result = await pipeline.execute(PipelineTask(instruction="begin"), WorkflowContext())
        assert result["completed_stages"] == 2
        assert agent2.execute.call_count == 0

    async def test_no_early_exit_when_confidence_ok(self) -> None:
        """2-agent pipeline, min_confidence=0.5.
        Both stages return confidence=0.8 (above threshold).
        Should complete all stages, stopped_early=False."""
        agent0 = _make_mock_agent(response="stage0", confidence=0.8)
        agent1 = _make_mock_agent(response="stage1", confidence=0.8)
        pipeline = AgentPipeline([agent0, agent1], min_confidence=0.5)
        result = await pipeline.execute(PipelineTask(instruction="start"), WorkflowContext())
        assert result["stopped_early"] is False
        assert result["completed_stages"] == 2

    async def test_min_confidence_zero_never_stops(self) -> None:
        """2-agent pipeline, min_confidence=0.0.
        Stage 0 returns confidence=0.0 (absolute minimum).
        Condition 0.0 < 0.0 is False, so should NOT stop early."""
        agent0 = _make_mock_agent(response="stage0", confidence=0.0)
        agent1 = _make_mock_agent(response="stage1", confidence=0.8)
        pipeline = AgentPipeline([agent0, agent1], min_confidence=0.0)
        result = await pipeline.execute(PipelineTask(instruction="start"), WorkflowContext())
        assert result["stopped_early"] is False
        assert result["completed_stages"] == 2


# ── Stage Transform tests ─────────────────────────────────────────────────────


class TestAgentPipelineTransforms:
    async def test_default_transform_uses_response(self) -> None:
        """2-agent pipeline with no stage_transforms arg.
        Stage 0 response = "hello". Assert agent1 receives instruction="hello"
        (the default lambda r: r["response"])."""
        agent0 = _make_mock_agent(response="hello")
        agent1 = _make_mock_agent(response="processed")
        pipeline = AgentPipeline([agent0, agent1])
        await pipeline.execute(PipelineTask(instruction="start"), WorkflowContext())
        call_args = agent1.execute.call_args[0][0]
        assert call_args["instruction"] == "hello"

    async def test_custom_transform_prefix(self) -> None:
        """2-agent pipeline with custom transform.
        stage_transforms=[None, lambda r: f"Review: {r['response']}"].
        Stage 0 response = "my code". Assert agent1 receives instruction="Review: my code"."""
        agent0 = _make_mock_agent(response="my code")
        agent1 = _make_mock_agent(response="review")
        pipeline = AgentPipeline(
            [agent0, agent1],
            stage_transforms=[None, lambda r: f"Review: {r['response']}"],
        )
        await pipeline.execute(PipelineTask(instruction="implement"), WorkflowContext())
        call_args = agent1.execute.call_args[0][0]
        assert call_args["instruction"] == "Review: my code"

    async def test_transform_receives_full_result(self) -> None:
        """The transform callable receives the complete DevelopmentResult.
        Set up a transform that reads result["confidence"] and returns a string based on it."""

        def confidence_transform(result: DevelopmentResult) -> str:
            confidence = result["confidence"]
            if confidence > 0.75:
                return "High confidence output"
            return "Low confidence output"

        agent0 = _make_mock_agent(response="test", confidence=0.9)
        agent1 = _make_mock_agent(response="final")
        pipeline = AgentPipeline(
            [agent0, agent1],
            stage_transforms=[None, confidence_transform],
        )
        await pipeline.execute(PipelineTask(instruction="start"), WorkflowContext())
        call_args = agent1.execute.call_args[0][0]
        assert call_args["instruction"] == "High confidence output"

    async def test_mixed_transforms_three_stage(self) -> None:
        """3-agent pipeline with mixed transforms.
        stage_transforms=[None, custom_fn1, custom_fn2].
        Stage 0 response = "A". custom_fn1 returns "B(A)".
        Stage 1 response = "C". custom_fn2 returns "D(C)".
        Assert agent1 received "B(A)", agent2 received "D(C)"."""

        def fn1(result: DevelopmentResult) -> str:
            return f"B({result['response']})"

        def fn2(result: DevelopmentResult) -> str:
            return f"D({result['response']})"

        agent0 = _make_mock_agent(response="A")
        agent1 = _make_mock_agent(response="C")
        agent2 = _make_mock_agent(response="final")
        pipeline = AgentPipeline(
            [agent0, agent1, agent2],
            stage_transforms=[None, fn1, fn2],
        )
        await pipeline.execute(PipelineTask(instruction="begin"), WorkflowContext())
        call_args_1 = agent1.execute.call_args[0][0]
        call_args_2 = agent2.execute.call_args[0][0]
        assert call_args_1["instruction"] == "B(A)"
        assert call_args_2["instruction"] == "D(C)"


# ── OTel Span tests ───────────────────────────────────────────────────────────


class TestAgentPipelineOTel:
    async def test_span_attributes_set(self) -> None:
        """Mock the tracer and verify all 4 span attributes are set:
        - pipeline.agent_count
        - pipeline.completed_stages
        - pipeline.stopped_early
        - pipeline.final_confidence"""
        agent = _make_mock_agent(confidence=0.8)
        pipeline = AgentPipeline([agent])
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)
        pipeline._pipeline_tracer = mock_tracer

        await pipeline.execute(PipelineTask(instruction="test"), WorkflowContext())

        mock_span.set_attribute.assert_any_call("pipeline.agent_count", 1)
        mock_span.set_attribute.assert_any_call("pipeline.completed_stages", 1)
        mock_span.set_attribute.assert_any_call("pipeline.stopped_early", False)
        mock_span.set_attribute.assert_any_call("pipeline.final_confidence", 0.8)

    async def test_span_completed_stages_matches_result(self) -> None:
        """With mock tracer, verify the value passed to pipeline.completed_stages
        span attribute equals result["completed_stages"]."""
        agents = [_make_mock_agent() for _ in range(2)]
        pipeline = AgentPipeline(agents)
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)
        pipeline._pipeline_tracer = mock_tracer

        result = await pipeline.execute(PipelineTask(instruction="test"), WorkflowContext())

        # Verify the span attribute matches the result
        calls = mock_span.set_attribute.call_args_list
        completed_stages_call = next(c for c in calls if c[0][0] == "pipeline.completed_stages")
        assert completed_stages_call[0][1] == result["completed_stages"]

    async def test_no_span_when_tracer_none(self) -> None:
        """Set pipeline._pipeline_tracer = None.
        Execute normally. Assert no error raised and result is valid."""
        agent = _make_mock_agent(response="output")
        pipeline = AgentPipeline([agent])
        pipeline._pipeline_tracer = None

        result = await pipeline.execute(PipelineTask(instruction="test"), WorkflowContext())

        assert result["completed_stages"] == 1
        assert result["final_response"] == "output"
        assert result["stopped_early"] is False
