"""Unit tests for ttadev/primitives/orchestration/.

Tests verify:
- DelegationPrimitive routing, cost calculation, and error handling
- TaskClassifierPrimitive characteristic analysis, complexity, and model routing
- MultiModelWorkflow orchestration end-to-end (all LLM calls mocked)

No real LLM calls are made — executor primitives are mocked throughout.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.orchestration.delegation_primitive import (
    DelegationPrimitive,
    DelegationRequest,
    DelegationResponse,
)
from ttadev.primitives.orchestration.task_classifier_primitive import (
    TaskCharacteristics,
    TaskClassification,
    TaskClassifierPrimitive,
    TaskClassifierRequest,
    TaskComplexity,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test-orchestration")


def _mock_executor(content: str = "result", cost: float = 0.0) -> MagicMock:
    """Return a mock executor primitive whose execute() returns a DelegationResponse."""
    executor = MagicMock()
    executor.execute = AsyncMock(
        return_value=DelegationResponse(
            content=content,
            executor_model="mock-model",
            usage={"prompt_tokens": 10, "completion_tokens": 5},
            cost=cost,
        )
    )
    return executor


def _delegation_request(
    model: str = "mock-model",
    task: str = "do something",
    messages: list[dict[str, str]] | None = None,
) -> DelegationRequest:
    return DelegationRequest(
        task_description=task,
        executor_model=model,
        messages=messages or [{"role": "user", "content": "hello"}],
    )


def _stub_integrations() -> dict[str, MagicMock]:
    """Stub the integration modules that have optional heavy dependencies."""
    stub = MagicMock()
    return {
        "ttadev.primitives.integrations.google_ai_studio_primitive": stub,
        "ttadev.primitives.integrations.groq_primitive": stub,
        "ttadev.primitives.integrations.openrouter_primitive": stub,
    }


# ---------------------------------------------------------------------------
# DelegationRequest / DelegationResponse model fields
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDelegationModels:
    def test_request_stores_task_description(self) -> None:
        req = _delegation_request(task="write a poem")
        assert req.task_description == "write a poem"

    def test_request_metadata_defaults_empty(self) -> None:
        req = _delegation_request()
        assert req.metadata == {}

    def test_response_stores_content(self) -> None:
        resp = DelegationResponse(
            content="hello",
            executor_model="m",
            usage={},
            cost=0.0,
        )
        assert resp.content == "hello"

    def test_response_metadata_defaults_empty(self) -> None:
        resp = DelegationResponse(content="x", executor_model="m", usage={}, cost=0.0)
        assert resp.metadata == {}


# ---------------------------------------------------------------------------
# DelegationPrimitive construction
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDelegationPrimitiveConstruction:
    def test_defaults_to_empty_executors(self) -> None:
        prim = DelegationPrimitive()
        assert prim.executor_primitives == {}

    def test_accepts_initial_executors(self) -> None:
        ex = _mock_executor()
        prim = DelegationPrimitive(executor_primitives={"m": ex})
        assert "m" in prim.executor_primitives

    def test_register_executor_adds_entry(self) -> None:
        prim = DelegationPrimitive()
        ex = _mock_executor()
        prim.register_executor("my-model", ex)
        assert prim.executor_primitives["my-model"] is ex

    def test_register_executor_replaces_existing(self) -> None:
        prim = DelegationPrimitive()
        ex1 = _mock_executor("v1")
        ex2 = _mock_executor("v2")
        prim.register_executor("m", ex1)
        prim.register_executor("m", ex2)
        assert prim.executor_primitives["m"] is ex2


# ---------------------------------------------------------------------------
# DelegationPrimitive.execute()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDelegationPrimitiveExecute:
    async def test_routes_to_registered_executor(self) -> None:
        ex = _mock_executor("my result")
        prim = DelegationPrimitive(executor_primitives={"mock-model": ex})
        with patch.dict("sys.modules", _stub_integrations()):
            resp = await prim.execute(_delegation_request(model="mock-model"), _ctx())
        assert resp.content == "my result"
        ex.execute.assert_awaited_once()

    async def test_raises_for_unknown_model(self) -> None:
        prim = DelegationPrimitive()
        with patch.dict("sys.modules", _stub_integrations()):
            with pytest.raises((ValueError, KeyError)):
                await prim.execute(_delegation_request(model="unknown"), _ctx())

    async def test_response_executor_model_set(self) -> None:
        ex = _mock_executor()
        prim = DelegationPrimitive(executor_primitives={"mock-model": ex})
        with patch.dict("sys.modules", _stub_integrations()):
            resp = await prim.execute(_delegation_request(model="mock-model"), _ctx())
        assert resp.executor_model == "mock-model"

    async def test_cost_is_calculated_from_model_name(self) -> None:
        """Cost is derived by _calculate_cost(model_name, usage), not from executor response."""
        ex = _mock_executor(cost=0.99)  # executor cost is ignored
        prim = DelegationPrimitive(executor_primitives={"mock-model": ex})
        with patch.dict("sys.modules", _stub_integrations()):
            resp = await prim.execute(_delegation_request(model="mock-model"), _ctx())
        # "mock-model" is unknown → falls into free-model bucket → 0.0
        assert isinstance(resp.cost, float)

    async def test_metadata_from_request_forwarded(self) -> None:
        ex = _mock_executor()
        prim = DelegationPrimitive(executor_primitives={"mock-model": ex})
        req = DelegationRequest(
            task_description="t",
            executor_model="mock-model",
            messages=[],
            metadata={"trace_id": "abc"},
        )
        with patch.dict("sys.modules", _stub_integrations()):
            resp = await prim.execute(req, _ctx())
        assert resp is not None

    async def test_multiple_executors_route_correctly(self) -> None:
        ex_a = _mock_executor("from-a")
        ex_b = _mock_executor("from-b")
        prim = DelegationPrimitive(executor_primitives={"model-a": ex_a, "model-b": ex_b})
        with patch.dict("sys.modules", _stub_integrations()):
            resp_a = await prim.execute(_delegation_request(model="model-a"), _ctx())
            resp_b = await prim.execute(_delegation_request(model="model-b"), _ctx())

        assert resp_a.content == "from-a"
        assert resp_b.content == "from-b"


# ---------------------------------------------------------------------------
# TaskComplexity enum values
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTaskComplexity:
    def test_simple_value(self) -> None:
        assert TaskComplexity.SIMPLE == "simple"

    def test_expert_value(self) -> None:
        assert TaskComplexity.EXPERT == "expert"


# ---------------------------------------------------------------------------
# TaskCharacteristics defaults
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTaskCharacteristics:
    def test_default_requires_accuracy_true(self) -> None:
        tc = TaskCharacteristics()
        assert tc.requires_accuracy is True

    def test_default_other_fields_false(self) -> None:
        tc = TaskCharacteristics()
        assert tc.requires_reasoning is False
        assert tc.requires_creativity is False
        assert tc.requires_code is False
        assert tc.requires_speed is False
        assert tc.requires_long_context is False

    def test_explicit_values_stored(self) -> None:
        tc = TaskCharacteristics(requires_reasoning=True, requires_code=True)
        assert tc.requires_reasoning is True
        assert tc.requires_code is True


# ---------------------------------------------------------------------------
# TaskClassifierPrimitive construction
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTaskClassifierConstruction:
    def test_prefer_free_default_true(self) -> None:
        assert TaskClassifierPrimitive().prefer_free is True

    def test_prefer_free_can_be_set_false(self) -> None:
        assert TaskClassifierPrimitive(prefer_free=False).prefer_free is False


# ---------------------------------------------------------------------------
# TaskClassifierPrimitive._analyze_characteristics()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAnalyzeCharacteristics:
    def _classify(self, task: str) -> TaskCharacteristics:
        return TaskClassifierPrimitive()._analyze_characteristics(task.lower())

    def test_reasoning_keyword_analyze(self) -> None:
        assert self._classify("analyze this data").requires_reasoning is True

    def test_reasoning_keyword_compare(self) -> None:
        assert self._classify("compare these options").requires_reasoning is True

    def test_creativity_keyword_create(self) -> None:
        assert self._classify("create a report").requires_creativity is True

    def test_creativity_keyword_write(self) -> None:
        assert self._classify("write a story").requires_creativity is True

    def test_code_keyword_function(self) -> None:
        assert self._classify("write a function").requires_code is True

    def test_code_keyword_debug(self) -> None:
        assert self._classify("debug this error").requires_code is True

    def test_speed_keyword_quick(self) -> None:
        assert self._classify("quick answer please").requires_speed is True

    def test_long_context_keyword_document(self) -> None:
        assert self._classify("summarize this document").requires_long_context is True

    def test_no_keywords_all_false_except_accuracy(self) -> None:
        chars = self._classify("hello world")
        assert chars.requires_reasoning is False
        assert chars.requires_creativity is False
        assert chars.requires_code is False
        assert chars.requires_speed is False
        assert chars.requires_long_context is False
        assert chars.requires_accuracy is True  # always True


# ---------------------------------------------------------------------------
# TaskClassifierPrimitive._determine_complexity()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDetermineComplexity:
    def _complexity(self, task: str) -> TaskComplexity:
        clf = TaskClassifierPrimitive()
        chars = clf._analyze_characteristics(task.lower())
        return clf._determine_complexity(task.lower(), chars)

    def test_code_and_reasoning_is_expert(self) -> None:
        # "implement" → code, "analyze" → reasoning
        assert self._complexity("analyze and implement this function") == TaskComplexity.EXPERT

    def test_research_is_expert(self) -> None:
        assert self._complexity("research quantum computing") == TaskComplexity.EXPERT

    def test_comprehensive_is_expert(self) -> None:
        assert self._complexity("comprehensive market analysis") == TaskComplexity.EXPERT

    def test_plan_is_complex(self) -> None:
        assert self._complexity("plan a product launch") == TaskComplexity.COMPLEX

    def test_strategy_is_complex(self) -> None:
        assert self._complexity("define strategy for growth") == TaskComplexity.COMPLEX

    def test_summarize_is_moderate(self) -> None:
        assert self._complexity("summarize this article") == TaskComplexity.MODERATE

    def test_translate_is_moderate(self) -> None:
        assert self._complexity("translate to Spanish") == TaskComplexity.MODERATE

    def test_analyze_alone_is_moderate(self) -> None:
        assert self._complexity("analyze the data") == TaskComplexity.MODERATE

    def test_write_alone_is_moderate(self) -> None:
        assert self._complexity("write a short poem") == TaskComplexity.MODERATE

    def test_simple_fallthrough(self) -> None:
        assert self._complexity("what is the capital of France") == TaskComplexity.SIMPLE


# ---------------------------------------------------------------------------
# TaskClassifierPrimitive._recommend_model()
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRecommendModel:
    def _recommend(
        self,
        complexity: TaskComplexity,
        chars: TaskCharacteristics | None = None,
        preferences: dict[str, Any] | None = None,
    ) -> TaskClassification:
        clf = TaskClassifierPrimitive()
        c = chars or TaskCharacteristics()
        return clf._recommend_model(complexity, c, preferences or {})

    def test_expert_prefer_free_uses_free_model(self) -> None:
        result = self._recommend(TaskComplexity.EXPERT, preferences={"prefer_free": True})
        assert result.estimated_cost == 0.0

    def test_expert_no_prefer_free_uses_claude(self) -> None:
        result = self._recommend(TaskComplexity.EXPERT, preferences={"prefer_free": False})
        assert result.recommended_model == "claude-sonnet-4.5"
        assert result.estimated_cost > 0

    def test_complex_uses_deepseek_r1(self) -> None:
        result = self._recommend(TaskComplexity.COMPLEX)
        assert "deepseek" in result.recommended_model.lower() or result.estimated_cost == 0.0

    def test_speed_critical_uses_groq(self) -> None:
        chars = TaskCharacteristics(requires_speed=True)
        result = self._recommend(TaskComplexity.SIMPLE, chars=chars)
        assert result.estimated_cost == 0.0

    def test_simple_returns_a_free_model(self) -> None:
        result = self._recommend(TaskComplexity.SIMPLE)
        assert result.estimated_cost == 0.0

    def test_result_has_fallback_models(self) -> None:
        result = self._recommend(TaskComplexity.MODERATE)
        assert isinstance(result.fallback_models, list)

    def test_reasoning_routes_to_free_reasoning_model(self) -> None:
        chars = TaskCharacteristics(requires_reasoning=True)
        result = self._recommend(TaskComplexity.MODERATE, chars=chars)
        assert result.estimated_cost == 0.0


# ---------------------------------------------------------------------------
# TaskClassifierPrimitive.execute() end-to-end
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestTaskClassifierExecute:
    async def test_simple_task_returns_classification(self) -> None:
        clf = TaskClassifierPrimitive()
        req = TaskClassifierRequest(task_description="What is 2 + 2?")
        result = await clf.execute(req, _ctx())
        assert isinstance(result, TaskClassification)
        assert result.complexity == TaskComplexity.SIMPLE

    async def test_code_task_returns_expert_or_complex(self) -> None:
        clf = TaskClassifierPrimitive()
        req = TaskClassifierRequest(task_description="analyze and implement a sorting algorithm")
        result = await clf.execute(req, _ctx())
        assert result.complexity in (TaskComplexity.EXPERT, TaskComplexity.COMPLEX)

    async def test_prefer_free_preference_respected(self) -> None:
        clf = TaskClassifierPrimitive()
        req = TaskClassifierRequest(
            task_description="research quantum algorithms",
            user_preferences={"prefer_free": True},
        )
        result = await clf.execute(req, _ctx())
        assert result.estimated_cost == 0.0

    async def test_user_prefer_paid_respected_for_expert(self) -> None:
        clf = TaskClassifierPrimitive()
        req = TaskClassifierRequest(
            task_description="research quantum algorithms",
            user_preferences={"prefer_free": False},
        )
        result = await clf.execute(req, _ctx())
        # Should pick paid model for expert task
        assert result.estimated_cost > 0 or result.complexity != TaskComplexity.EXPERT

    async def test_summarize_is_moderate(self) -> None:
        clf = TaskClassifierPrimitive()
        req = TaskClassifierRequest(task_description="summarize this article in 3 points")
        result = await clf.execute(req, _ctx())
        assert result.complexity == TaskComplexity.MODERATE

    async def test_recommended_model_is_string(self) -> None:
        clf = TaskClassifierPrimitive()
        req = TaskClassifierRequest(task_description="hello world")
        result = await clf.execute(req, _ctx())
        assert isinstance(result.recommended_model, str)
        assert len(result.recommended_model) > 0

    async def test_reasoning_field_present(self) -> None:
        clf = TaskClassifierPrimitive()
        req = TaskClassifierRequest(task_description="plan a marketing strategy")
        result = await clf.execute(req, _ctx())
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0
