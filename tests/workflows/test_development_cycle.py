"""Unit tests for DevelopmentCycle — all dependencies mocked."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

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
) -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
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


class TestDevelopmentCycleWrite:
    @pytest.mark.asyncio
    async def test_write_short_llm_response_returns_low_confidence(self) -> None:
        """Short LLM response no longer raises — quality gate scores it low."""
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        # length < 20 (-0.8) + < 80 (-0.3) → score = -0.1, clamped to 0.0
        short_response = "Short."
        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(llm_response=short_response)
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with patch(
            "ttadev.workflows.development_cycle.get_llm_provider_chain",
            return_value=_make_chain(["openrouter"]),
        ):
            result = await cycle.execute(
                DevelopmentTask(instruction="Explain the cache primitive"),
                WorkflowContext(),
            )
        assert result["confidence"] == 0.0
        assert result["response"] == short_response


class TestDevelopmentCycleWriteFull:
    @pytest.mark.asyncio
    async def test_write_calls_llm_with_instruction(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            llm_response="Here is the implementation."
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
        mock_http.post.assert_called_once()
        call_kwargs = mock_http.post.call_args
        body = call_kwargs.kwargs.get("json", {})
        messages = body.get("messages", [])
        assert any(
            m["role"] == "user" and "Add timeout parameter" in m["content"] for m in messages
        )
        assert result["response"] == "Here is the implementation."

    @pytest.mark.asyncio
    async def test_write_includes_persona_in_system_prompt(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            llm_response="Security review done."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        await cycle.execute(
            DevelopmentTask(instruction="Review for vulns", agent_hint="security"),
            WorkflowContext(),
        )
        body = mock_http.post.call_args.kwargs.get("json", {})
        messages = body.get("messages", [])
        sys_msg = next(m["content"] for m in messages if m["role"] == "system")
        assert "security" in sys_msg.lower()

    @pytest.mark.asyncio
    async def test_write_context_prefix_in_system_prompt(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            context_prefix="## Directives\n- Use uv",
            llm_response="Done.",
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        await cycle.execute(
            DevelopmentTask(instruction="Add feature"),
            WorkflowContext(),
        )
        body = mock_http.post.call_args.kwargs.get("json", {})
        messages = body.get("messages", [])
        sys_msg = next(m["content"] for m in messages if m["role"] == "system")
        assert "Use uv" in sys_msg


class TestDevelopmentCycleValidate:
    @pytest.mark.asyncio
    async def test_validate_returns_true_when_tests_pass(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        report = ImpactReport(
            target="retry.py",
            callers=[],
            dependencies=[],
            related_tests=["tests/test_retry.py"],
            complexity=2.0,
            risk="low",
            summary="",
            cgc_available=True,
        )
        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            impact_report=report, validate_success=True, llm_response="Done."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Add timeout", target_files=["retry.py"]),
            WorkflowContext(),
        )
        assert result["validated"] is True
        mock_executor.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_returns_false_when_no_related_tests(self) -> None:
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
        result = await cycle.execute(
            DevelopmentTask(instruction="Update README"),
            WorkflowContext(),
        )
        assert result["validated"] is False
        mock_executor.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_returns_false_when_e2b_errors(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        report = ImpactReport(
            target="retry.py",
            callers=[],
            dependencies=[],
            related_tests=["tests/test_retry.py"],
            complexity=2.0,
            risk="low",
            summary="",
            cgc_available=True,
        )
        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            impact_report=report, llm_response="Done."
        )
        mock_executor.execute = AsyncMock(side_effect=Exception("E2B unavailable"))
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Add timeout", target_files=["retry.py"]),
            WorkflowContext(),
        )
        assert result["validated"] is False


class TestDevelopmentCycleRetain:
    @pytest.mark.asyncio
    async def test_retain_stores_memory_and_returns_one(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            retain_success=True, llm_response="Here is the output."
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
        mock_memory.retain.assert_called_once()
        assert result["memories_retained"] == 1

    @pytest.mark.asyncio
    async def test_retain_returns_zero_when_hindsight_unavailable(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            retain_success=False, llm_response="Output."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        result = await cycle.execute(
            DevelopmentTask(instruction="Fix bug"),
            WorkflowContext(),
        )
        assert result["memories_retained"] == 0


class TestDevelopmentCycleIntegration:
    @pytest.mark.asyncio
    async def test_full_cycle_returns_complete_result(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            context_prefix="## Directives\n- Use uv",
            llm_response="Here is the implementation plan.",
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
        assert result["response"] == "Here is the implementation plan."
        assert result["context_prefix"] == "## Directives\n- Use uv"
        assert isinstance(result["validated"], bool)
        assert isinstance(result["memories_retained"], int)

    @pytest.mark.asyncio
    async def test_agent_hint_override_per_call(self) -> None:
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(
            llm_response="QA review done."
        )
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            agent_hint="developer",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        await cycle.execute(
            DevelopmentTask(instruction="Review tests", agent_hint="qa"),
            WorkflowContext(),
        )
        body = mock_http.post.call_args.kwargs.get("json", {})
        messages = body.get("messages", [])
        sys_msg = next(m["content"] for m in messages if m["role"] == "system")
        assert "QA engineer" in sys_msg


# ── Quality Gate + Fallback Tests ─────────────────────────────────────────────

from ttadev.workflows.llm_provider import LLMClientConfig  # noqa: E402


def _make_chain(providers: list[str]) -> list[LLMClientConfig]:
    configs = {
        "openrouter": LLMClientConfig(
            base_url="https://openrouter.ai/api/v1",
            model="test-model",
            api_key="test-key",  # pragma: allowlist secret
            provider="openrouter",
        ),
        "ollama": LLMClientConfig(
            base_url="http://localhost:11434/v1",
            model="test-model",
            api_key="ollama",  # pragma: allowlist secret
            provider="ollama",
        ),
    }
    return [configs[p] for p in providers]


def _make_chain_from_names(*providers: str) -> list[LLMClientConfig]:
    """Build a fake provider chain for testing by provider name."""
    return [
        LLMClientConfig(
            base_url=f"http://{p}.test/v1",
            model="test-model",
            api_key="test-key",  # pragma: allowlist secret
            provider=p,
        )
        for p in providers
    ]


# A response long enough to pass the quality gate (>80 chars, no refusal patterns)
_GOOD_RESPONSE = (
    "Here is a thorough implementation with full type annotations, "
    "docstrings, and error handling as requested by the user. "
    "The solution uses async/await throughout."
)

# A response that fails the quality gate (short, < 80 chars)
_BAD_RESPONSE = "I cannot help with that."


class TestDevelopmentCycleQualityGate:
    @pytest.mark.asyncio
    async def test_result_includes_confidence_and_provider(self) -> None:
        """Happy path: DevelopmentResult has confidence and provider fields."""
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(llm_response=_GOOD_RESPONSE)
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with patch(
            "ttadev.workflows.development_cycle.get_llm_provider_chain",
            return_value=_make_chain(["openrouter"]),
        ):
            result = await cycle.execute(
                DevelopmentTask(instruction="Add timeout parameter"),
                WorkflowContext(),
            )
        assert result["confidence"] >= 0.0
        assert result["provider"] == "openrouter"

    @pytest.mark.asyncio
    async def test_write_no_fallback_when_primary_passes(self) -> None:
        """When primary provider passes quality gate, http.post called once."""
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(llm_response=_GOOD_RESPONSE)
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with patch(
            "ttadev.workflows.development_cycle.get_llm_provider_chain",
            return_value=_make_chain(["openrouter", "ollama"]),
        ):
            await cycle.execute(
                DevelopmentTask(instruction="Add timeout parameter"),
                WorkflowContext(),
            )
        assert mock_http.post.call_count == 1

    @pytest.mark.asyncio
    async def test_write_fallback_on_low_confidence(self) -> None:
        """Primary scores low → fallback called, result.provider = fallback provider."""
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        # First call returns refusal (fails gate), second returns good response
        bad_resp = MagicMock()
        bad_resp.raise_for_status = MagicMock()
        bad_resp.json.return_value = {"choices": [{"message": {"content": _BAD_RESPONSE}}]}

        good_resp = MagicMock()
        good_resp.raise_for_status = MagicMock()
        good_resp.json.return_value = {"choices": [{"message": {"content": _GOOD_RESPONSE}}]}

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks()
        mock_http.post = AsyncMock(side_effect=[bad_resp, good_resp])

        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with patch(
            "ttadev.workflows.development_cycle.get_llm_provider_chain",
            return_value=_make_chain(["openrouter", "ollama"]),
        ):
            result = await cycle.execute(
                DevelopmentTask(instruction="Add timeout parameter"),
                WorkflowContext(),
            )
        assert result["provider"] == "ollama"
        assert mock_http.post.call_count == 2

    @pytest.mark.asyncio
    async def test_write_uses_best_when_all_fail_gate(self) -> None:
        """All providers below threshold → best returned, no exception raised."""
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        # Both return responses that fail the quality gate
        short1 = "Short."
        short2 = "I cannot help with that specific request as it falls outside my capabilities."

        resp1 = MagicMock()
        resp1.raise_for_status = MagicMock()
        resp1.json.return_value = {"choices": [{"message": {"content": short1}}]}

        resp2 = MagicMock()
        resp2.raise_for_status = MagicMock()
        resp2.json.return_value = {"choices": [{"message": {"content": short2}}]}

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks()
        mock_http.post = AsyncMock(side_effect=[resp1, resp2])

        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with patch(
            "ttadev.workflows.development_cycle.get_llm_provider_chain",
            return_value=_make_chain(["openrouter", "ollama"]),
        ):
            # Should not raise; returns best available
            result = await cycle.execute(
                DevelopmentTask(instruction="Add timeout parameter"),
                WorkflowContext(),
            )
        assert result["confidence"] < 0.5
        assert result["response"] in (short1, short2)

    @pytest.mark.asyncio
    async def test_write_reraises_when_all_providers_raise(self) -> None:
        """All providers raise → last exception re-raised."""
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks()
        mock_http.post = AsyncMock(side_effect=RuntimeError("network error"))

        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with patch(
            "ttadev.workflows.development_cycle.get_llm_provider_chain",
            return_value=_make_chain(["openrouter", "ollama"]),
        ):
            with pytest.raises(RuntimeError, match="network error"):
                await cycle.execute(
                    DevelopmentTask(instruction="Add timeout parameter"),
                    WorkflowContext(),
                )

    @pytest.mark.asyncio
    async def test_write_provider_exception_then_fallback_succeeds(self) -> None:
        """Primary raises, fallback succeeds → result uses fallback response."""
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        good_resp = MagicMock()
        good_resp.raise_for_status = MagicMock()
        good_resp.json.return_value = {"choices": [{"message": {"content": _GOOD_RESPONSE}}]}

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks()
        mock_http.post = AsyncMock(side_effect=[RuntimeError("openrouter down"), good_resp])

        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with patch(
            "ttadev.workflows.development_cycle.get_llm_provider_chain",
            return_value=_make_chain(["openrouter", "ollama"]),
        ):
            result = await cycle.execute(
                DevelopmentTask(instruction="Add timeout parameter"),
                WorkflowContext(),
            )
        assert result["response"] == _GOOD_RESPONSE
        assert result["provider"] == "ollama"


class TestDevelopmentCyclePerCallConfig:
    @pytest.mark.asyncio
    async def test_per_call_chain_overrides_env_chain(self) -> None:
        """provider_chain in task overrides get_llm_provider_chain(); env chain never called."""
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(llm_response=_GOOD_RESPONSE)
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with patch(
            "ttadev.workflows.development_cycle.get_llm_provider_chain",
            side_effect=RuntimeError("should never be called"),
        ):
            result = await cycle.execute(
                DevelopmentTask(
                    instruction="Add timeout parameter",
                    provider_chain=_make_chain_from_names("custom"),
                ),
                WorkflowContext(),
            )
        assert result["provider"] == "custom"

    @pytest.mark.asyncio
    async def test_per_call_threshold_zero_means_no_gate(self) -> None:
        """quality_threshold=0.0 means gate always passes, even for low-scoring responses."""
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        refusal = "I cannot help with that."
        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(llm_response=refusal)
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with patch(
            "ttadev.workflows.development_cycle.get_llm_provider_chain",
            return_value=_make_chain(["openrouter"]),
        ):
            result = await cycle.execute(
                DevelopmentTask(
                    instruction="Explain the cache primitive",
                    quality_threshold=0.0,
                ),
                WorkflowContext(),
            )
        # Gate at 0.0 always passes so only one LLM call made
        assert mock_http.post.call_count == 1
        assert result["confidence"] < 0.5
        assert result["response"] == refusal

    @pytest.mark.asyncio
    async def test_empty_provider_chain_raises(self) -> None:
        """provider_chain=[] raises ValueError before any LLM call."""
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
        with pytest.raises(ValueError, match="provider_chain must not be empty"):
            await cycle.execute(
                DevelopmentTask(instruction="x", provider_chain=[]),
                WorkflowContext(),
            )

    @pytest.mark.asyncio
    async def test_quality_threshold_too_high_raises(self) -> None:
        """quality_threshold=1.5 raises ValueError."""
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
        with pytest.raises(ValueError, match="quality_threshold must be in"):
            await cycle.execute(
                DevelopmentTask(instruction="x", quality_threshold=1.5),
                WorkflowContext(),
            )

    @pytest.mark.asyncio
    async def test_quality_threshold_negative_raises(self) -> None:
        """quality_threshold=-0.1 raises ValueError."""
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
        with pytest.raises(ValueError, match="quality_threshold must be in"):
            await cycle.execute(
                DevelopmentTask(instruction="x", quality_threshold=-0.1),
                WorkflowContext(),
            )

    @pytest.mark.asyncio
    async def test_retry_count_zero_on_good_response(self) -> None:
        """Good primary response → result['retry_count'] == 0."""
        from ttadev.primitives.core.base import WorkflowContext
        from ttadev.workflows.development_cycle import DevelopmentCycle, DevelopmentTask

        mock_memory, mock_graph, mock_executor, mock_http = _make_mocks(llm_response=_GOOD_RESPONSE)
        cycle = DevelopmentCycle(
            bank_id="tta-dev",
            _memory=mock_memory,
            _graph=mock_graph,
            _executor=mock_executor,
            _http=mock_http,
        )
        with patch(
            "ttadev.workflows.development_cycle.get_llm_provider_chain",
            return_value=_make_chain(["openrouter"]),
        ):
            result = await cycle.execute(
                DevelopmentTask(instruction="Add timeout parameter"),
                WorkflowContext(),
            )
        assert result["retry_count"] == 0
