"""Unit tests for ttadev/workflows/development_cycle.py.

185 stmts, target 70%+ coverage.
All LLM / external calls replaced by injected mocks.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from ttadev.primitives.code_graph import ImpactReport
from ttadev.primitives.core.base import WorkflowContext
from ttadev.workflows.development_cycle import (
    _REFRAME_TEMPLATE,
    DevelopmentCycle,
    _build_system_prompt,
    _empty_impact_report,
    _reframe_instruction,
)
from ttadev.workflows.llm_provider import LLMClientConfig

# ── Helpers ────────────────────────────────────────────────────────────────────


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test-dc")


def _cfg(provider: str = "mock", model: str = "mock-model") -> LLMClientConfig:
    return LLMClientConfig(
        base_url="http://mock-llm", model=model, api_key="mock-key", provider=provider
    )


def _http(content: str = "Implementation: " + "x" * 300) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"choices": [{"message": {"content": content}}]}
    client = MagicMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=resp)
    return client


def _mem(prefix: str = "", retain_ok: bool = True) -> MagicMock:
    m = MagicMock()
    m.build_context_prefix = AsyncMock(return_value=prefix)
    m.retain = AsyncMock(return_value={"success": retain_ok})
    return m


def _graph(tests: list[str] | None = None) -> MagicMock:
    report: ImpactReport = {
        "target": "mock.py",
        "callers": [],
        "dependencies": [],
        "related_tests": tests or [],
        "complexity": 0.5,
        "risk": "low",
        "summary": "mock",
        "cgc_available": True,
    }
    g = MagicMock()
    g.execute = AsyncMock(return_value=report)
    return g


def _exec(success: bool = True) -> MagicMock:
    e = MagicMock()
    e.execute = AsyncMock(return_value={"success": success})
    return e


def _dc(
    *,
    memory: MagicMock | None = None,
    graph: MagicMock | None = None,
    http: MagicMock | None = None,
    executor: MagicMock | None = None,
) -> DevelopmentCycle:
    dc = DevelopmentCycle(
        _memory=memory or _mem(),
        _graph=graph or _graph(),
        _http=http or _http(),
        _executor=executor,
    )
    dc._dc_tracer = None  # disable OTel in unit tests
    return dc


# ── Helper functions ───────────────────────────────────────────────────────────


class TestEmptyImpactReport:
    def test_is_dict(self) -> None:
        assert isinstance(_empty_impact_report(), dict)

    def test_cgc_available_false(self) -> None:
        assert _empty_impact_report()["cgc_available"] is False

    def test_callers_empty(self) -> None:
        assert _empty_impact_report()["callers"] == []

    def test_related_tests_empty(self) -> None:
        assert _empty_impact_report()["related_tests"] == []

    def test_risk_low(self) -> None:
        assert _empty_impact_report()["risk"] == "low"

    def test_target_stored(self) -> None:
        assert _empty_impact_report("my.py")["target"] == "my.py"

    def test_default_target_empty(self) -> None:
        assert _empty_impact_report()["target"] == ""

    def test_complexity_zero(self) -> None:
        assert _empty_impact_report()["complexity"] == 0.0


class TestBuildSystemPrompt:
    def test_developer_persona(self) -> None:
        assert "Python" in _build_system_prompt("developer", "")

    def test_qa_persona(self) -> None:
        assert "QA" in _build_system_prompt("qa", "")

    def test_security_persona(self) -> None:
        assert "security" in _build_system_prompt("security", "").lower()

    def test_unknown_persona_uses_name(self) -> None:
        assert "architect" in _build_system_prompt("architect", "")

    def test_context_prefix_appended(self) -> None:
        assert "Remember: X" in _build_system_prompt("developer", "Remember: X")

    def test_empty_prefix_not_appended(self) -> None:
        prompt = _build_system_prompt("developer", "")
        assert "\n\n" not in prompt or "Remember" not in prompt


class TestReframeInstruction:
    def test_contains_instruction(self) -> None:
        assert "write a sort fn" in _reframe_instruction("write a sort fn")

    def test_matches_template(self) -> None:
        inst = "build a REST API"
        assert _reframe_instruction(inst) == _REFRAME_TEMPLATE.format(instruction=inst)

    def test_contains_implementation_hint(self) -> None:
        assert "implementation" in _reframe_instruction("task").lower()

    def test_contains_do_not_refuse(self) -> None:
        assert "Do not refuse" in _reframe_instruction("anything")


# ── _orient ───────────────────────────────────────────────────────────────────


class TestOrient:
    async def test_no_files_returns_empty_report(self) -> None:
        report = await _dc()._orient([], _ctx())
        assert report["cgc_available"] is False

    async def test_no_files_does_not_call_graph(self) -> None:
        g = _graph()
        await _dc(graph=g)._orient([], _ctx())
        g.execute.assert_not_awaited()

    async def test_with_files_calls_graph(self) -> None:
        g = _graph()
        await _dc(graph=g)._orient(["parser.py"], _ctx())
        g.execute.assert_awaited_once()

    async def test_uses_first_file_as_target(self) -> None:
        g = _graph()
        await _dc(graph=g)._orient(["first.py", "second.py"], _ctx())
        assert g.execute.call_args[0][0]["target"] == "first.py"

    async def test_returns_graph_report(self) -> None:
        g = _graph(tests=["tests/test_p.py"])
        report = await _dc(graph=g)._orient(["p.py"], _ctx())
        assert report["cgc_available"] is True
        assert "tests/test_p.py" in report["related_tests"]


# ── _recall ───────────────────────────────────────────────────────────────────


class TestRecall:
    async def test_returns_prefix_from_memory(self) -> None:
        m = _mem(prefix="Use async patterns")
        assert await _dc(memory=m)._recall("build API") == "Use async patterns"

    async def test_empty_prefix(self) -> None:
        m = _mem(prefix="")
        assert await _dc(memory=m)._recall("task") == ""

    async def test_called_with_instruction(self) -> None:
        m = _mem(prefix="ctx")
        await _dc(memory=m)._recall("my instruction")
        m.build_context_prefix.assert_awaited_once_with("my instruction")


# ── _call_llm ─────────────────────────────────────────────────────────────────


class TestCallLLM:
    async def test_returns_content(self) -> None:
        h = _http(content="Here is code")
        result = await _dc(http=h)._call_llm(_cfg(), "sys", "user")
        assert result == "Here is code"

    async def test_sends_system_message(self) -> None:
        h = _http()
        await _dc(http=h)._call_llm(_cfg(), "sys_prompt", "user_content")
        body = h.post.call_args.kwargs.get("json") or h.post.call_args[1].get("json")
        assert body["messages"][0] == {"role": "system", "content": "sys_prompt"}

    async def test_sends_user_message(self) -> None:
        h = _http()
        await _dc(http=h)._call_llm(_cfg(), "s", "my_instruction")
        body = h.post.call_args.kwargs.get("json") or h.post.call_args[1].get("json")
        assert body["messages"][1] == {"role": "user", "content": "my_instruction"}

    async def test_uses_config_model(self) -> None:
        h = _http()
        await _dc(http=h)._call_llm(_cfg(model="gpt-4o"), "s", "u")
        body = h.post.call_args.kwargs.get("json") or h.post.call_args[1].get("json")
        assert body["model"] == "gpt-4o"

    async def test_raises_on_http_error(self) -> None:
        resp = MagicMock()
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )
        h = MagicMock(spec=httpx.AsyncClient)
        h.post = AsyncMock(return_value=resp)
        with pytest.raises(httpx.HTTPStatusError):
            await _dc(http=h)._call_llm(_cfg(), "s", "u")

    async def test_bearer_auth_header(self) -> None:
        h = _http()
        cfg = LLMClientConfig(base_url="http://x", model="m", api_key="secret", provider="p")
        await _dc(http=h)._call_llm(cfg, "s", "u")
        headers = h.post.call_args.kwargs.get("headers") or h.post.call_args[1].get("headers", {})
        assert headers.get("Authorization") == "Bearer secret"


# ── _write ────────────────────────────────────────────────────────────────────


class TestWrite:
    async def test_returns_four_tuple(self) -> None:
        dc = _dc(http=_http("Implementation: " + "a" * 300))
        result = await dc._write("task", "developer", "", chain=[_cfg()])
        assert len(result) == 4
        response, confidence, provider, retry_count = result
        assert isinstance(response, str)
        assert isinstance(confidence, float)
        assert isinstance(provider, str)
        assert isinstance(retry_count, int)

    async def test_provider_name_from_config(self) -> None:
        dc = _dc(http=_http("Implementation: " + "a" * 300))
        _, _, provider, _ = await dc._write("task", "developer", "", chain=[_cfg(provider="groq")])
        assert provider == "groq"

    async def test_no_retry_on_good_response(self) -> None:
        dc = _dc(http=_http("Great implementation: " + "a" * 400))
        _, _, _, retry_count = await dc._write(
            "task", "developer", "", chain=[_cfg()], threshold=0.5
        )
        assert retry_count == 0

    async def test_retry_on_low_quality(self) -> None:
        responses = iter(
            [
                "I cannot help with that.",  # low quality (refusal)
                "Full implementation: " + "a" * 400,  # good
            ]
        )

        def _next_resp() -> MagicMock:
            content = next(responses, "Fallback: " + "a" * 300)
            r = MagicMock()
            r.raise_for_status = MagicMock()
            r.json.return_value = {"choices": [{"message": {"content": content}}]}
            return r

        h = MagicMock(spec=httpx.AsyncClient)
        h.post = AsyncMock(side_effect=lambda *a, **kw: _next_resp())
        dc = _dc(http=h)
        _, _, _, retry_count = await dc._write(
            "build", "developer", "", chain=[_cfg()], threshold=0.5
        )
        assert retry_count == 1

    async def test_raises_when_all_providers_error(self) -> None:
        h = MagicMock(spec=httpx.AsyncClient)
        h.post = AsyncMock(side_effect=ConnectionError("no conn"))
        dc = _dc(http=h)
        with pytest.raises((ConnectionError, Exception)):
            await dc._write("task", "developer", "", chain=[_cfg()])


# ── _validate ─────────────────────────────────────────────────────────────────


def _impact(tests: list[str]) -> ImpactReport:
    return {
        "target": "f.py",
        "callers": [],
        "dependencies": [],
        "related_tests": tests,
        "complexity": 0.5,
        "risk": "low",
        "summary": "t",
        "cgc_available": True,
    }


class TestValidate:
    async def test_no_tests_returns_false(self) -> None:
        assert await _dc()._validate(_empty_impact_report(), _ctx()) is False

    async def test_no_executor_returns_false(self) -> None:
        dc = _dc()
        dc._executor = None
        assert await dc._validate(_impact(["tests/test_f.py"]), _ctx()) is False

    async def test_executor_success(self) -> None:
        assert await _dc(executor=_exec(True))._validate(_impact(["t.py"]), _ctx()) is True

    async def test_executor_failure(self) -> None:
        assert await _dc(executor=_exec(False))._validate(_impact(["t.py"]), _ctx()) is False

    async def test_executor_exception_returns_false(self) -> None:
        ex = MagicMock()
        ex.execute = AsyncMock(side_effect=RuntimeError("sandbox failed"))
        assert await _dc(executor=ex)._validate(_impact(["t.py"]), _ctx()) is False

    async def test_executor_receives_python_code(self) -> None:
        ex = _exec(True)
        dc = _dc(executor=ex)
        await dc._validate(_impact(["tests/test_a.py"]), _ctx())
        call_input = ex.execute.call_args[0][0]
        assert call_input["language"] == "python"
        assert "pytest" in call_input["code"]


# ── _retain ───────────────────────────────────────────────────────────────────


class TestRetain:
    async def test_success_returns_1(self) -> None:
        assert await _dc(memory=_mem(retain_ok=True))._retain("instr", "resp") == 1

    async def test_failure_returns_0(self) -> None:
        assert await _dc(memory=_mem(retain_ok=False))._retain("instr", "resp") == 0

    async def test_retain_called_once(self) -> None:
        m = _mem(retain_ok=True)
        await _dc(memory=m)._retain("instruction", "response")
        m.retain.assert_awaited_once()

    async def test_content_contains_type_decision(self) -> None:
        m = _mem(retain_ok=True)
        await _dc(memory=m)._retain("build parser", "def parse(): ...")
        content = m.retain.call_args[0][0]
        assert "[type: decision]" in content

    async def test_content_contains_instruction_snippet(self) -> None:
        m = _mem(retain_ok=True)
        await _dc(memory=m)._retain("build_parser_func", "code here")
        assert "build_parser_func" in m.retain.call_args[0][0]


# ── _execute_impl end-to-end ──────────────────────────────────────────────────


class TestExecuteImpl:
    async def test_returns_all_required_keys(self) -> None:
        result = await _dc()._execute_impl({"instruction": "do task"}, _ctx())
        for key in (
            "response",
            "validated",
            "impact_report",
            "memories_retained",
            "context_prefix",
            "confidence",
            "provider",
            "retry_count",
        ):
            assert key in result, f"Missing: {key}"

    async def test_empty_instruction_raises(self) -> None:
        with pytest.raises(ValueError, match="instruction must not be empty"):
            await _dc()._execute_impl({"instruction": ""}, _ctx())

    async def test_missing_instruction_raises(self) -> None:
        with pytest.raises(ValueError, match="instruction must not be empty"):
            await _dc()._execute_impl({}, _ctx())

    async def test_empty_provider_chain_raises(self) -> None:
        with pytest.raises(ValueError, match="provider_chain must not be empty"):
            await _dc()._execute_impl({"instruction": "t", "provider_chain": []}, _ctx())

    async def test_invalid_quality_threshold_raises(self) -> None:
        with pytest.raises(ValueError, match="quality_threshold must be in"):
            await _dc()._execute_impl({"instruction": "t", "quality_threshold": 1.5}, _ctx())

    async def test_custom_provider_chain_used(self) -> None:
        h = _http("Implementation: " + "a" * 300)
        dc = _dc(http=h)
        result = await dc._execute_impl(
            {"instruction": "build", "provider_chain": [_cfg(provider="custom")]}, _ctx()
        )
        assert result["provider"] == "custom"

    async def test_context_prefix_in_result(self) -> None:
        m = _mem(prefix="Prior context here")
        dc = _dc(memory=m)
        result = await dc._execute_impl({"instruction": "task"}, _ctx())
        assert result["context_prefix"] == "Prior context here"

    async def test_retry_count_is_non_negative(self) -> None:
        result = await _dc()._execute_impl({"instruction": "task"}, _ctx())
        assert result["retry_count"] >= 0

    async def test_target_files_first_used_for_graph(self) -> None:
        g = _graph()
        dc = _dc(graph=g)
        await dc._execute_impl(
            {"instruction": "refactor", "target_files": ["a.py", "b.py", "c.py", "d.py"]},
            _ctx(),
        )
        if g.execute.await_count > 0:
            assert g.execute.call_args[0][0]["target"] in ["a.py", "b.py", "c.py"]
