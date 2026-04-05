"""Unit tests for ttadev/primitives/orchestration/multi_model_workflow.py.

115 stmts, target 70%+ coverage.
All LLM / executor calls mocked.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.orchestration.delegation_primitive import (
    DelegationPrimitive,
    DelegationResponse,
)
from ttadev.primitives.orchestration.multi_model_workflow import (
    MultiModelRequest,
    MultiModelResponse,
    MultiModelWorkflow,
)
from ttadev.primitives.orchestration.task_classifier_primitive import (
    TaskCharacteristics,
    TaskClassification,
    TaskClassifierPrimitive,
    TaskComplexity,
)

# ── Helpers ────────────────────────────────────────────────────────────────────


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test-mmw")


def _clf(
    complexity: TaskComplexity = TaskComplexity.SIMPLE,
    model: str = "gemini-2.5-pro",
    cost: float = 0.0,
    reasoning: str = "test",
) -> TaskClassification:
    return TaskClassification(
        complexity=complexity,
        characteristics=TaskCharacteristics(),
        recommended_model=model,
        reasoning=reasoning,
        estimated_cost=cost,
        fallback_models=["fallback-model"],
    )


def _delg(
    content: str = "Generated response with plenty of detail.",
    model: str = "gemini-2.5-pro",
    cost: float = 0.0,
) -> DelegationResponse:
    return DelegationResponse(
        content=content,
        executor_model=model,
        usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        cost=cost,
    )


def _wf(
    classification: TaskClassification | None = None,
    delegation: DelegationResponse | None = None,
) -> tuple[MultiModelWorkflow, MagicMock, MagicMock]:
    wf = MultiModelWorkflow()
    mock_clf = MagicMock(spec=TaskClassifierPrimitive)
    mock_clf.execute = AsyncMock(return_value=classification or _clf())
    wf.classifier = mock_clf

    mock_del = MagicMock(spec=DelegationPrimitive)
    mock_del.execute = AsyncMock(return_value=delegation or _delg())
    wf.delegation = mock_del

    return wf, mock_clf, mock_del


def _req(
    task: str = "Summarize the article",
    messages: list[dict[str, str]] | None = None,
    preferences: dict | None = None,
    validate: bool = False,
) -> MultiModelRequest:
    return MultiModelRequest(
        task_description=task,
        messages=messages or [{"role": "user", "content": "do it"}],
        user_preferences=preferences or {},
        validate_output=validate,
    )


# ── Model field tests ─────────────────────────────────────────────────────────


class TestMultiModelRequestModel:
    def test_task_description(self) -> None:
        assert MultiModelRequest(task_description="t", messages=[]).task_description == "t"

    def test_validate_output_defaults_false(self) -> None:
        assert MultiModelRequest(task_description="t", messages=[]).validate_output is False

    def test_user_preferences_defaults_empty(self) -> None:
        assert MultiModelRequest(task_description="t", messages=[]).user_preferences == {}

    def test_messages_stored(self) -> None:
        msgs = [{"role": "user", "content": "hi"}]
        assert MultiModelRequest(task_description="t", messages=msgs).messages == msgs


class TestMultiModelResponseModel:
    def test_content(self) -> None:
        r = MultiModelResponse(content="ans", executor_model="m", classification={}, cost=0.0)
        assert r.content == "ans"

    def test_validation_passed_defaults_none(self) -> None:
        r = MultiModelResponse(content="x", executor_model="m", classification={}, cost=0.0)
        assert r.validation_passed is None

    def test_metadata_defaults_empty(self) -> None:
        r = MultiModelResponse(content="x", executor_model="m", classification={}, cost=0.0)
        assert r.metadata == {}


# ── Construction ───────────────────────────────────────────────────────────────


class TestMultiModelWorkflowConstruction:
    def test_classifier_not_none(self) -> None:
        assert MultiModelWorkflow().classifier is not None

    def test_delegation_not_none(self) -> None:
        assert MultiModelWorkflow().delegation is not None

    def test_prefer_free_true_propagated(self) -> None:
        assert MultiModelWorkflow(prefer_free=True).classifier.prefer_free is True

    def test_prefer_free_false_propagated(self) -> None:
        assert MultiModelWorkflow(prefer_free=False).classifier.prefer_free is False

    def test_config_none_without_config_path(self) -> None:
        assert MultiModelWorkflow().config is None

    def test_executor_primitives_registered(self) -> None:
        mock_ex = MagicMock()
        wf = MultiModelWorkflow(executor_primitives={"my-model": mock_ex})
        assert "my-model" in wf.delegation.executor_primitives

    def test_none_executor_primitives_gives_empty(self) -> None:
        assert MultiModelWorkflow(executor_primitives=None).delegation.executor_primitives == {}


# ── register_executor ──────────────────────────────────────────────────────────


class TestRegisterExecutor:
    def test_registers(self) -> None:
        wf = MultiModelWorkflow()
        wf.register_executor("new-model", MagicMock())
        assert "new-model" in wf.delegation.executor_primitives

    def test_overrides_existing(self) -> None:
        wf = MultiModelWorkflow()
        ex1, ex2 = MagicMock(), MagicMock()
        wf.register_executor("m", ex1)
        wf.register_executor("m", ex2)
        assert wf.delegation.executor_primitives["m"] is ex2

    def test_multiple_all_registered(self) -> None:
        wf = MultiModelWorkflow()
        for name in ("a", "b", "c"):
            wf.register_executor(name, MagicMock())
        assert all(n in wf.delegation.executor_primitives for n in ("a", "b", "c"))


# ── execute() ────────────────────────────────────────────────────────────────


class TestMultiModelWorkflowExecute:
    async def test_returns_response(self) -> None:
        wf, _, _ = _wf()
        assert isinstance(await wf.execute(_req(), _ctx()), MultiModelResponse)

    async def test_content_from_delegation(self) -> None:
        wf, _, _ = _wf(delegation=_delg(content="specific output"))
        assert (await wf.execute(_req(), _ctx())).content == "specific output"

    async def test_classifier_called_once(self) -> None:
        wf, mock_clf, _ = _wf()
        await wf.execute(_req(), _ctx())
        mock_clf.execute.assert_awaited_once()

    async def test_delegation_called_once(self) -> None:
        wf, _, mock_del = _wf()
        await wf.execute(_req(), _ctx())
        mock_del.execute.assert_awaited_once()

    async def test_executor_model_from_classification(self) -> None:
        wf, _, _ = _wf(
            classification=_clf(model="deepseek/deepseek-r1:free"),
            delegation=_delg(model="deepseek/deepseek-r1:free"),
        )
        resp = await wf.execute(_req(), _ctx())
        assert resp.executor_model == "deepseek/deepseek-r1:free"

    async def test_classification_complexity_in_response(self) -> None:
        wf, _, _ = _wf(classification=_clf(complexity=TaskComplexity.MODERATE))
        resp = await wf.execute(_req(), _ctx())
        assert resp.classification["complexity"] == "moderate"

    async def test_classification_recommended_model(self) -> None:
        wf, _, _ = _wf(classification=_clf(model="gemini-2.5-pro"))
        resp = await wf.execute(_req(), _ctx())
        assert resp.classification["recommended_model"] == "gemini-2.5-pro"

    async def test_classification_reasoning(self) -> None:
        wf, _, _ = _wf(classification=_clf(reasoning="Free model ok"))
        resp = await wf.execute(_req(), _ctx())
        assert resp.classification["reasoning"] == "Free model ok"

    async def test_fallback_models_present(self) -> None:
        wf, _, _ = _wf()
        assert "fallback_models" in (await wf.execute(_req(), _ctx())).classification

    async def test_cost_from_delegation(self) -> None:
        wf, _, _ = _wf(delegation=_delg(cost=0.05))
        assert (await wf.execute(_req(), _ctx())).cost == pytest.approx(0.05)

    async def test_validation_skipped_by_default(self) -> None:
        wf, _, _ = _wf()
        assert (await wf.execute(_req(validate=False), _ctx())).validation_passed is None

    async def test_validation_runs_when_enabled(self) -> None:
        wf, _, _ = _wf(delegation=_delg(content="a" * 200))
        resp = await wf.execute(_req(validate=True), _ctx())
        assert resp.validation_passed is not None

    async def test_user_preferences_forwarded(self) -> None:
        wf, mock_clf, _ = _wf()
        await wf.execute(_req(preferences={"prefer_free": True}), _ctx())
        assert mock_clf.execute.call_args[0][0].user_preferences == {"prefer_free": True}

    async def test_task_description_in_metadata(self) -> None:
        wf, _, _ = _wf()
        resp = await wf.execute(_req(task="My task"), _ctx())
        assert "task_description" in resp.metadata

    async def test_classifier_receives_task_description(self) -> None:
        wf, mock_clf, _ = _wf()
        await wf.execute(_req(task="very specific description"), _ctx())
        assert mock_clf.execute.call_args[0][0].task_description == "very specific description"

    async def test_delegation_receives_recommended_model(self) -> None:
        wf, _, mock_del = _wf(classification=_clf(model="llama-3.3-70b-versatile"))
        await wf.execute(_req(), _ctx())
        assert mock_del.execute.call_args[0][0].executor_model == "llama-3.3-70b-versatile"

    async def test_delegation_receives_messages(self) -> None:
        msgs = [{"role": "user", "content": "specific messages"}]
        wf, _, mock_del = _wf()
        await wf.execute(_req(messages=msgs), _ctx())
        assert mock_del.execute.call_args[0][0].messages == msgs


# ── _validate_output() ────────────────────────────────────────────────────────


class TestValidateOutput:
    def _c(self, cx: TaskComplexity) -> TaskClassification:
        return _clf(complexity=cx)

    async def test_empty_content_fails(self) -> None:
        wf = MultiModelWorkflow()
        assert (
            await wf._validate_output(_delg(content=""), self._c(TaskComplexity.SIMPLE), _ctx())
            is False
        )

    async def test_whitespace_fails(self) -> None:
        wf = MultiModelWorkflow()
        assert (
            await wf._validate_output(
                _delg(content="   \n"), self._c(TaskComplexity.SIMPLE), _ctx()
            )
            is False
        )

    async def test_simple_min_10_passes(self) -> None:
        wf = MultiModelWorkflow()
        assert (
            await wf._validate_output(
                _delg(content="Yes, it is."), self._c(TaskComplexity.SIMPLE), _ctx()
            )
            is True
        )

    async def test_simple_under_10_fails(self) -> None:
        wf = MultiModelWorkflow()
        assert (
            await wf._validate_output(_delg(content="Hi"), self._c(TaskComplexity.SIMPLE), _ctx())
            is False
        )

    async def test_moderate_49_fails(self) -> None:
        wf = MultiModelWorkflow()
        assert (
            await wf._validate_output(
                _delg(content="a" * 49), self._c(TaskComplexity.MODERATE), _ctx()
            )
            is False
        )

    async def test_moderate_51_passes(self) -> None:
        wf = MultiModelWorkflow()
        assert (
            await wf._validate_output(
                _delg(content="a" * 51), self._c(TaskComplexity.MODERATE), _ctx()
            )
            is True
        )

    async def test_complex_99_fails(self) -> None:
        wf = MultiModelWorkflow()
        assert (
            await wf._validate_output(
                _delg(content="a" * 99), self._c(TaskComplexity.COMPLEX), _ctx()
            )
            is False
        )

    async def test_complex_101_passes(self) -> None:
        wf = MultiModelWorkflow()
        assert (
            await wf._validate_output(
                _delg(content="a" * 101), self._c(TaskComplexity.COMPLEX), _ctx()
            )
            is True
        )

    async def test_expert_150_fails(self) -> None:
        wf = MultiModelWorkflow()
        assert (
            await wf._validate_output(
                _delg(content="a" * 150), self._c(TaskComplexity.EXPERT), _ctx()
            )
            is False
        )

    async def test_expert_201_passes(self) -> None:
        wf = MultiModelWorkflow()
        assert (
            await wf._validate_output(
                _delg(content="a" * 201), self._c(TaskComplexity.EXPERT), _ctx()
            )
            is True
        )

    async def test_unknown_complexity_fallback_50(self) -> None:
        wf = MultiModelWorkflow()
        mock_clf = MagicMock()
        mock_clf.complexity.value = "unknown"
        short = await wf._validate_output(_delg(content="a" * 49), mock_clf, _ctx())
        long = await wf._validate_output(_delg(content="a" * 51), mock_clf, _ctx())
        assert short is False
        assert long is True

    async def test_strip_applied_before_length_check(self) -> None:
        wf = MultiModelWorkflow()
        # stripped content = 11 chars → passes SIMPLE threshold (10)
        padded = _delg(content="   " + "a" * 11 + "   ")
        assert await wf._validate_output(padded, self._c(TaskComplexity.SIMPLE), _ctx()) is True
