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
