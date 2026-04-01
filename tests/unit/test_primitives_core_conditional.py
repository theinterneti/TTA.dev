"""Unit tests for ConditionalPrimitive and SwitchPrimitive.

Tests cover:
- True/false branch selection for ConditionalPrimitive
- Passthrough when no else_primitive and condition is False
- Condition function exception propagation
- Branch primitive exception propagation
- SwitchPrimitive: case matching, default, passthrough, selector exceptions
- Metrics and logging surface (no crashes)
- Tracing disabled path
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.core.conditional import ConditionalPrimitive, SwitchPrimitive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(wid: str = "cond-test") -> WorkflowContext:
    return WorkflowContext(workflow_id=wid)


def _prim(return_value: object = "result", raises: Exception | None = None) -> MagicMock:
    p = MagicMock()
    if raises is not None:
        p.execute = AsyncMock(side_effect=raises)
    else:
        p.execute = AsyncMock(return_value=return_value)
    return p


def _true_cond(*_: object) -> bool:
    return True


def _false_cond(*_: object) -> bool:
    return False


# ---------------------------------------------------------------------------
# ConditionalPrimitive — construction
# ---------------------------------------------------------------------------


class TestConditionalPrimitiveInit:
    def test_stores_condition_and_primitives(self) -> None:
        cond = lambda d, c: True  # noqa: E731
        then = _prim()
        else_ = _prim()
        cp = ConditionalPrimitive(condition=cond, then_primitive=then, else_primitive=else_)
        assert cp.condition is cond
        assert cp.then_primitive is then
        assert cp.else_primitive is else_

    def test_else_primitive_is_optional(self) -> None:
        cp = ConditionalPrimitive(condition=_true_cond, then_primitive=_prim())
        assert cp.else_primitive is None

    def test_is_workflow_primitive(self) -> None:
        from ttadev.primitives.core.base import WorkflowPrimitive

        cp = ConditionalPrimitive(condition=_true_cond, then_primitive=_prim())
        assert isinstance(cp, WorkflowPrimitive)


# ---------------------------------------------------------------------------
# ConditionalPrimitive — true branch
# ---------------------------------------------------------------------------


class TestConditionalTrueBranch:
    @pytest.mark.asyncio
    async def test_executes_then_when_condition_true(self) -> None:
        then = _prim(return_value="then_result")
        else_ = _prim(return_value="else_result")
        cp = ConditionalPrimitive(condition=_true_cond, then_primitive=then, else_primitive=else_)
        result = await cp.execute({"data": 1}, _ctx())
        assert result == "then_result"

    @pytest.mark.asyncio
    async def test_else_not_called_when_true(self) -> None:
        then = _prim()
        else_ = _prim()
        cp = ConditionalPrimitive(condition=_true_cond, then_primitive=then, else_primitive=else_)
        await cp.execute({}, _ctx())
        else_.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_then_called_with_input_and_context(self) -> None:
        ctx = _ctx("ctx-true")
        then = _prim()
        cp = ConditionalPrimitive(condition=_true_cond, then_primitive=then)
        await cp.execute("input-data", ctx)
        then.execute.assert_awaited_once_with("input-data", ctx)

    @pytest.mark.asyncio
    async def test_condition_receives_input_and_context(self) -> None:
        ctx = _ctx()
        received: list[tuple[object, object]] = []

        def cond(data: object, c: object) -> bool:
            received.append((data, c))
            return True

        cp = ConditionalPrimitive(condition=cond, then_primitive=_prim())
        await cp.execute("my-input", ctx)
        assert received == [("my-input", ctx)]


# ---------------------------------------------------------------------------
# ConditionalPrimitive — false branch
# ---------------------------------------------------------------------------


class TestConditionalFalseBranch:
    @pytest.mark.asyncio
    async def test_executes_else_when_condition_false(self) -> None:
        then = _prim(return_value="then_result")
        else_ = _prim(return_value="else_result")
        cp = ConditionalPrimitive(condition=_false_cond, then_primitive=then, else_primitive=else_)
        result = await cp.execute({}, _ctx())
        assert result == "else_result"

    @pytest.mark.asyncio
    async def test_then_not_called_when_false(self) -> None:
        then = _prim()
        else_ = _prim()
        cp = ConditionalPrimitive(condition=_false_cond, then_primitive=then, else_primitive=else_)
        await cp.execute({}, _ctx())
        then.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_passthrough_when_false_and_no_else(self) -> None:
        """No else_primitive + false condition → returns input unchanged."""
        cp = ConditionalPrimitive(condition=_false_cond, then_primitive=_prim("ignored"))
        result = await cp.execute("original-input", _ctx())
        assert result == "original-input"

    @pytest.mark.asyncio
    async def test_passthrough_preserves_complex_input(self) -> None:
        data = {"key": "value", "nested": {"list": [1, 2, 3]}}
        cp = ConditionalPrimitive(condition=_false_cond, then_primitive=_prim())
        result = await cp.execute(data, _ctx())
        assert result == data


# ---------------------------------------------------------------------------
# ConditionalPrimitive — dynamic condition
# ---------------------------------------------------------------------------


class TestConditionalDynamicCondition:
    @pytest.mark.asyncio
    async def test_branches_on_input_value(self) -> None:
        then = _prim(return_value="high")
        else_ = _prim(return_value="low")
        cp = ConditionalPrimitive(
            condition=lambda d, _: d.get("score", 0) >= 50,
            then_primitive=then,
            else_primitive=else_,
        )
        high_result = await cp.execute({"score": 80}, _ctx())
        low_result = await cp.execute({"score": 20}, _ctx())
        assert high_result == "high"
        assert low_result == "low"

    @pytest.mark.asyncio
    async def test_branches_on_context_value(self) -> None:
        then = _prim(return_value="admin_path")
        else_ = _prim(return_value="user_path")
        cp = ConditionalPrimitive(
            condition=lambda _, ctx: ctx.workflow_id == "admin",
            then_primitive=then,
            else_primitive=else_,
        )
        admin_ctx = _ctx("admin")
        user_ctx = _ctx("user")
        assert await cp.execute({}, admin_ctx) == "admin_path"
        assert await cp.execute({}, user_ctx) == "user_path"


# ---------------------------------------------------------------------------
# ConditionalPrimitive — exception handling
# ---------------------------------------------------------------------------


class TestConditionalExceptions:
    @pytest.mark.asyncio
    async def test_condition_exception_propagates(self) -> None:
        def bad_cond(_: object, __: object) -> bool:
            raise ValueError("condition blew up")

        cp = ConditionalPrimitive(condition=bad_cond, then_primitive=_prim())
        with pytest.raises(ValueError, match="condition blew up"):
            await cp.execute({}, _ctx())

    @pytest.mark.asyncio
    async def test_then_exception_propagates(self) -> None:
        cp = ConditionalPrimitive(
            condition=_true_cond,
            then_primitive=_prim(raises=RuntimeError("then failed")),
        )
        with pytest.raises(RuntimeError, match="then failed"):
            await cp.execute({}, _ctx())

    @pytest.mark.asyncio
    async def test_else_exception_propagates(self) -> None:
        cp = ConditionalPrimitive(
            condition=_false_cond,
            then_primitive=_prim(),
            else_primitive=_prim(raises=TypeError("else failed")),
        )
        with pytest.raises(TypeError, match="else failed"):
            await cp.execute({}, _ctx())


# ---------------------------------------------------------------------------
# ConditionalPrimitive — tracing disabled
# ---------------------------------------------------------------------------


class TestConditionalTracingDisabled:
    @pytest.mark.asyncio
    async def test_executes_without_tracing(self) -> None:
        with patch("ttadev.primitives.core.conditional.TRACING_AVAILABLE", False):
            then = _prim(return_value="no-span")
            cp = ConditionalPrimitive(condition=_true_cond, then_primitive=then)
            result = await cp.execute({}, _ctx())
        assert result == "no-span"


# ---------------------------------------------------------------------------
# ConditionalPrimitive — metrics surface
# ---------------------------------------------------------------------------


class TestConditionalMetrics:
    @pytest.mark.asyncio
    async def test_metrics_recorded_on_success(self) -> None:
        mock_collector = MagicMock()
        mock_collector.record_execution = MagicMock()
        with patch(
            "ttadev.primitives.core.conditional.get_enhanced_metrics_collector",
            return_value=mock_collector,
        ):
            cp = ConditionalPrimitive(condition=_true_cond, then_primitive=_prim("ok"))
            await cp.execute({}, _ctx())
        mock_collector.record_execution.assert_called()

    @pytest.mark.asyncio
    async def test_metrics_recorded_on_failure(self) -> None:
        mock_collector = MagicMock()
        mock_collector.record_execution = MagicMock()
        with patch(
            "ttadev.primitives.core.conditional.get_enhanced_metrics_collector",
            return_value=mock_collector,
        ):
            cp = ConditionalPrimitive(
                condition=_true_cond,
                then_primitive=_prim(raises=ValueError("boom")),
            )
            with pytest.raises(ValueError):
                await cp.execute({}, _ctx())
        mock_collector.record_execution.assert_called()


# ---------------------------------------------------------------------------
# SwitchPrimitive — construction
# ---------------------------------------------------------------------------


class TestSwitchPrimitiveInit:
    def test_stores_selector_cases_default(self) -> None:
        sel = lambda d, _: d.get("k")  # noqa: E731
        cases = {"a": _prim(), "b": _prim()}
        default = _prim()
        sp = SwitchPrimitive(selector=sel, cases=cases, default=default)
        assert sp.selector is sel
        assert sp.cases is cases
        assert sp.default is default

    def test_default_is_optional(self) -> None:
        sp = SwitchPrimitive(selector=lambda d, _: "a", cases={"a": _prim()})
        assert sp.default is None

    def test_is_workflow_primitive(self) -> None:
        from ttadev.primitives.core.base import WorkflowPrimitive

        sp = SwitchPrimitive(selector=lambda d, _: "x", cases={})
        assert isinstance(sp, WorkflowPrimitive)


# ---------------------------------------------------------------------------
# SwitchPrimitive — matching cases
# ---------------------------------------------------------------------------


class TestSwitchCaseMatching:
    @pytest.mark.asyncio
    async def test_executes_matching_case(self) -> None:
        cases = {
            "option_a": _prim(return_value="result_a"),
            "option_b": _prim(return_value="result_b"),
        }
        sp = SwitchPrimitive(selector=lambda d, _: d["choice"], cases=cases)
        assert await sp.execute({"choice": "option_a"}, _ctx()) == "result_a"
        assert await sp.execute({"choice": "option_b"}, _ctx()) == "result_b"

    @pytest.mark.asyncio
    async def test_non_selected_cases_not_called(self) -> None:
        prim_a = _prim(return_value="a")
        prim_b = _prim(return_value="b")
        cases = {"a": prim_a, "b": prim_b}
        sp = SwitchPrimitive(selector=lambda d, _: "a", cases=cases)
        await sp.execute({}, _ctx())
        prim_b.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_matching_case_called_with_input_and_context(self) -> None:
        ctx = _ctx("switch-ctx")
        prim_a = _prim()
        sp = SwitchPrimitive(selector=lambda d, _: "a", cases={"a": prim_a})
        await sp.execute("my-input", ctx)
        prim_a.execute.assert_awaited_once_with("my-input", ctx)

    @pytest.mark.asyncio
    async def test_selector_receives_input_and_context(self) -> None:
        ctx = _ctx()
        received: list[tuple[object, object]] = []

        def sel(data: object, c: object) -> str:
            received.append((data, c))
            return "x"

        sp = SwitchPrimitive(selector=sel, cases={"x": _prim()})
        await sp.execute("input", ctx)
        assert received == [("input", ctx)]


# ---------------------------------------------------------------------------
# SwitchPrimitive — default case
# ---------------------------------------------------------------------------


class TestSwitchDefaultCase:
    @pytest.mark.asyncio
    async def test_executes_default_when_no_match(self) -> None:
        default = _prim(return_value="default_result")
        sp = SwitchPrimitive(
            selector=lambda d, _: "unknown_key",
            cases={"a": _prim("a")},
            default=default,
        )
        result = await sp.execute({}, _ctx())
        assert result == "default_result"

    @pytest.mark.asyncio
    async def test_case_takes_priority_over_default(self) -> None:
        default = _prim(return_value="default_result")
        prim_a = _prim(return_value="case_a")
        sp = SwitchPrimitive(
            selector=lambda d, _: "a",
            cases={"a": prim_a},
            default=default,
        )
        result = await sp.execute({}, _ctx())
        assert result == "case_a"
        default.execute.assert_not_awaited()


# ---------------------------------------------------------------------------
# SwitchPrimitive — passthrough
# ---------------------------------------------------------------------------


class TestSwitchPassthrough:
    @pytest.mark.asyncio
    async def test_passthrough_when_no_match_and_no_default(self) -> None:
        sp = SwitchPrimitive(
            selector=lambda d, _: "missing",
            cases={"a": _prim("a")},
        )
        result = await sp.execute("original-data", _ctx())
        assert result == "original-data"

    @pytest.mark.asyncio
    async def test_passthrough_empty_cases(self) -> None:
        sp = SwitchPrimitive(selector=lambda d, _: "any", cases={})
        result = await sp.execute({"keep": "me"}, _ctx())
        assert result == {"keep": "me"}


# ---------------------------------------------------------------------------
# SwitchPrimitive — exception handling
# ---------------------------------------------------------------------------


class TestSwitchExceptions:
    @pytest.mark.asyncio
    async def test_selector_exception_propagates(self) -> None:
        def bad_sel(_: object, __: object) -> str:
            raise KeyError("selector error")

        sp = SwitchPrimitive(selector=bad_sel, cases={"a": _prim()})
        with pytest.raises(KeyError, match="selector error"):
            await sp.execute({}, _ctx())

    @pytest.mark.asyncio
    async def test_case_primitive_exception_propagates(self) -> None:
        sp = SwitchPrimitive(
            selector=lambda d, _: "a",
            cases={"a": _prim(raises=ValueError("case failed"))},
        )
        with pytest.raises(ValueError, match="case failed"):
            await sp.execute({}, _ctx())

    @pytest.mark.asyncio
    async def test_default_exception_propagates(self) -> None:
        sp = SwitchPrimitive(
            selector=lambda d, _: "no_match",
            cases={"a": _prim()},
            default=_prim(raises=RuntimeError("default error")),
        )
        with pytest.raises(RuntimeError, match="default error"):
            await sp.execute({}, _ctx())


# ---------------------------------------------------------------------------
# SwitchPrimitive — tracing disabled
# ---------------------------------------------------------------------------


class TestSwitchTracingDisabled:
    @pytest.mark.asyncio
    async def test_executes_without_tracing(self) -> None:
        with patch("ttadev.primitives.core.conditional.TRACING_AVAILABLE", False):
            prim_a = _prim(return_value="no-span-result")
            sp = SwitchPrimitive(selector=lambda d, _: "a", cases={"a": prim_a})
            result = await sp.execute({}, _ctx())
        assert result == "no-span-result"

    @pytest.mark.asyncio
    async def test_passthrough_without_tracing(self) -> None:
        with patch("ttadev.primitives.core.conditional.TRACING_AVAILABLE", False):
            sp = SwitchPrimitive(selector=lambda d, _: "none", cases={})
            result = await sp.execute("data", _ctx())
        assert result == "data"


# ---------------------------------------------------------------------------
# SwitchPrimitive — metrics surface
# ---------------------------------------------------------------------------


class TestSwitchMetrics:
    @pytest.mark.asyncio
    async def test_metrics_recorded_on_match(self) -> None:
        mock_collector = MagicMock()
        mock_collector.record_execution = MagicMock()
        with patch(
            "ttadev.primitives.core.conditional.get_enhanced_metrics_collector",
            return_value=mock_collector,
        ):
            sp = SwitchPrimitive(selector=lambda d, _: "x", cases={"x": _prim("ok")})
            await sp.execute({}, _ctx())
        mock_collector.record_execution.assert_called()
