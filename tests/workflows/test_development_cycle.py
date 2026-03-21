"""Unit tests for DevelopmentCycle — all dependencies mocked."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ttadev.primitives.code_graph import ImpactReport
from ttadev.primitives.memory.types import RetainResult


def _empty_report() -> ImpactReport:
    return ImpactReport(
        target="",
        callers=[],
        dependencies=[],
        related_tests=[],
        complexity=0.0,
        risk="low",
        summary="No orient data.",
        cgc_available=False,
    )


def _make_mocks(
    context_prefix: str = "",
    impact_report: ImpactReport | None = None,
    validate_success: bool = False,
    retain_success: bool = True,
    llm_response: str = "Here is the implementation.",
) -> tuple:
    """Return (mock_memory, mock_graph, mock_executor, mock_http)."""
    mock_memory = MagicMock()
    mock_memory.build_context_prefix = AsyncMock(return_value=context_prefix)
    mock_memory.retain = AsyncMock(
        return_value=RetainResult(
            success=retain_success, operation_id="op-1" if retain_success else None
        )
    )

    mock_graph = MagicMock()
    mock_graph.execute = AsyncMock(return_value=impact_report or _empty_report())

    mock_executor = MagicMock()
    mock_executor.execute = AsyncMock(
        return_value={
            "output": "1 passed",
            "error": None,
            "success": validate_success,
            "sandbox_id": "sb-test",
            "execution_time": 1.2,
            "logs": [],
        }
    )

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"choices": [{"message": {"content": llm_response}}]}
    mock_http = MagicMock()
    mock_http.post = AsyncMock(return_value=mock_resp)

    return mock_memory, mock_graph, mock_executor, mock_http


class TestDevelopmentCycleConstruction:
    def test_constructs_with_defaults(self) -> None:
        from ttadev.workflows.development_cycle import DevelopmentCycle

        cycle = DevelopmentCycle(bank_id="tta-dev")
        assert cycle is not None

    def test_constructs_with_injected_dependencies(self) -> None:
        from ttadev.workflows.development_cycle import DevelopmentCycle

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks()
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        assert cycle is not None


class TestDevelopmentCycleValidation:
    @pytest.mark.asyncio
    async def test_raises_on_empty_instruction(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks()
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with pytest.raises(ValueError, match="instruction must not be empty"):
            await cycle.execute(DevelopmentTask(instruction=""), WorkflowContext())

    @pytest.mark.asyncio
    async def test_raises_on_missing_instruction(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks()
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with pytest.raises(ValueError, match="instruction must not be empty"):
            await cycle.execute(DevelopmentTask(), WorkflowContext())


class TestDevelopmentCycleOrient:
    @pytest.mark.asyncio
    async def test_orient_runs_code_graph_when_target_files_given(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        report = ImpactReport(
            target="retry.py",
            callers=["test_retry.py"],
            dependencies=[],
            related_tests=["tests/test_retry.py"],
            complexity=3.0,
            risk="low",
            summary="retry.py: risk=low",
            cgc_available=True,
        )
        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            impact_report=report, llm_response="Here is the plan."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Add timeout to retry", target_files=["retry.py"]),
            WorkflowContext(),
        )
        mock_graph.execute.assert_called_once()
        assert result["impact_report"]["target"] == "retry.py"
        assert result["impact_report"]["cgc_available"] is True

    @pytest.mark.asyncio
    async def test_orient_skips_code_graph_when_no_target_files(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            llm_response="Here is the plan."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Refactor cache"),
            WorkflowContext(),
        )
        mock_graph.execute.assert_not_called()
        assert result["impact_report"]["cgc_available"] is False

    @pytest.mark.asyncio
    async def test_orient_caps_target_files_at_three(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(llm_response="Done.")
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        await cycle.execute(
            DevelopmentTask(
                instruction="Big refactor",
                target_files=["a.py", "b.py", "c.py", "d.py", "e.py"],
            ),
            WorkflowContext(),
        )
        # Only first target used in CGC query (first of capped 3)
        call_args = mock_graph.execute.call_args
        query = call_args.args[0]
        assert query["target"] == "a.py"


class TestDevelopmentCycleRecall:
    @pytest.mark.asyncio
    async def test_recall_injects_context_prefix(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            context_prefix="## Directives\n- Always orient first",
            llm_response="Implementation here.",
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Add timeout parameter"),
            WorkflowContext(),
        )
        mock_memory.build_context_prefix.assert_called_once_with("Add timeout parameter")
        assert result["context_prefix"] == "## Directives\n- Always orient first"

    @pytest.mark.asyncio
    async def test_recall_returns_empty_when_hindsight_unavailable(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            context_prefix="", llm_response="Implementation."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Fix cache bug"),
            WorkflowContext(),
        )
        assert result["context_prefix"] == ""
