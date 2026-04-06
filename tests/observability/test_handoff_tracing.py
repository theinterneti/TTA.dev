"""Tests for inter-agent handoff tracing — issue #342.

Verifies:
1. AgentPrimitive emits an "agent.handoff" OTel span with the required
   attributes when a handoff trigger fires.
2. AgentPrimitive tags the current span with agent.role and agent.name.
3. /api/v2/tracing/dag returns a valid graph when handoff spans are present.
4. /api/v2/tracing/dag returns an empty graph when no handoff spans exist.
"""

from __future__ import annotations

import asyncio
import socket
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ttadev.agents.base import AgentPrimitive
from ttadev.agents.spec import AgentSpec, HandoffTrigger
from ttadev.agents.task import AgentResult, AgentTask
from ttadev.observability.span_processor import ProcessedSpan, SpanProcessor
from ttadev.primitives.core.base import WorkflowContext

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _make_agent_spec(
    name: str = "architect",
    role: str = "architect",
    *,
    handoff_triggers: list[HandoffTrigger] | None = None,
) -> AgentSpec:
    return AgentSpec(
        name=name,
        role=role,
        system_prompt="You are a test agent.",
        capabilities=[],
        tools=[],
        handoff_triggers=handoff_triggers or [],
        quality_gates=[],
    )


def _make_stub_result(agent_name: str = "developer") -> AgentResult:
    return AgentResult(
        agent_name=agent_name,
        response="stub response",
        artifacts=[],
        suggestions=[],
        spawned_agents=[],
        quality_gates_passed=True,
        confidence=0.9,
    )


def _make_handoff_span(
    from_agent: str,
    to_agent: str,
    task_id: str = "wf-test",
    reason: str = "needs code",
) -> ProcessedSpan:
    """Synthesise a ProcessedSpan that looks like an agent.handoff span."""
    return ProcessedSpan(
        span_id=uuid.uuid4().hex[:16],
        trace_id=uuid.uuid4().hex,
        parent_span_id=None,
        name="agent.handoff",
        provider="",
        model="",
        agent_role=from_agent,
        workflow_id=task_id,
        primitive_type=None,
        started_at="2024-01-01T00:00:00",
        duration_ms=5.0,
        status="OK",
        attributes={
            "handoff.from_agent": from_agent,
            "handoff.to_agent": to_agent,
            "handoff.task_id": task_id,
            "handoff.reason": reason,
        },
    )


# ---------------------------------------------------------------------------
# AC1 — handoff span is emitted with required attributes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handoff_span_emitted_with_required_attributes():
    """Executing a handoff trigger emits agent.handoff span with all attributes."""
    pytest.importorskip("opentelemetry")

    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    trigger = HandoffTrigger(
        condition=lambda task: True,
        target_agent="developer",
        reason="needs implementation",
    )
    spec = _make_agent_spec(name="architect", role="architect", handoff_triggers=[trigger])
    stub_model = MagicMock()
    agent = AgentPrimitive(spec=spec, model=stub_model)

    task = AgentTask(
        instruction="build feature X",
        context={},
        constraints=[],
    )
    ctx = WorkflowContext(workflow_id="wf-handoff-test")
    mock_spawn = AsyncMock(return_value=_make_stub_result("developer"))

    import opentelemetry.trace as otel_trace_mod

    with (
        patch("ttadev.agents.base._TRACING_AVAILABLE", True),
        patch("ttadev.agents.base._otel_trace", otel_trace_mod),
        patch("opentelemetry.trace.get_tracer", provider.get_tracer),
        patch.object(WorkflowContext, "spawn_agent", mock_spawn),
    ):
        result = await agent._execute_impl(task, ctx)

    mock_spawn.assert_awaited_once_with("developer", task)
    assert "developer" in result.spawned_agents

    spans = exporter.get_finished_spans()
    handoff_spans = [s for s in spans if s.name == "agent.handoff"]
    assert handoff_spans, "Expected at least one 'agent.handoff' span to be emitted"

    hs = handoff_spans[0]
    attrs = dict(hs.attributes)
    assert attrs.get("handoff.from_agent") == "architect"
    assert attrs.get("handoff.to_agent") == "developer"
    assert attrs.get("handoff.task_id") == "wf-handoff-test"
    assert attrs.get("handoff.reason") == "needs implementation"


# ---------------------------------------------------------------------------
# AC2 — agent.role and agent.name are tagged on the execution span
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_execution_span_tagged_with_agent_role():
    """The agent execution span is tagged with agent.role and agent.name."""
    pytest.importorskip("opentelemetry")

    mock_span = MagicMock()
    mock_span.is_recording.return_value = True

    spec = _make_agent_spec(name="analyst", role="data-analyst")
    agent = AgentPrimitive(spec=spec, model=MagicMock())

    task = AgentTask(instruction="analyse data", context={}, constraints=[])
    ctx = WorkflowContext(workflow_id="wf-role-test")

    with (
        patch("ttadev.agents.base._TRACING_AVAILABLE", True),
        patch("ttadev.agents.base._otel_trace") as mock_otel,
        patch(
            "ttadev.agents.tool_call_loop.ToolCallLoop.execute", new_callable=AsyncMock
        ) as mock_loop,
    ):
        mock_loop.return_value = "analysis complete"
        mock_otel.get_current_span.return_value = mock_span
        mock_otel.get_tracer.return_value = MagicMock()

        await agent._execute_impl(task, ctx)

    mock_span.set_attribute.assert_any_call("agent.role", "data-analyst")
    mock_span.set_attribute.assert_any_call("agent.name", "analyst")


# ---------------------------------------------------------------------------
# AC3 — handoff span fires only when condition is True
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handoff_span_not_emitted_when_condition_false():
    """No handoff span is emitted when the trigger condition evaluates False."""
    pytest.importorskip("opentelemetry")

    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    trigger = HandoffTrigger(
        condition=lambda task: False,  # never fires
        target_agent="developer",
        reason="needs implementation",
    )
    spec = _make_agent_spec(handoff_triggers=[trigger])
    stub_model = MagicMock()
    agent = AgentPrimitive(spec=spec, model=stub_model)

    task = AgentTask(instruction="build it", context={}, constraints=[])
    ctx = WorkflowContext(workflow_id="wf-no-handoff")
    mock_spawn = AsyncMock()

    with (
        patch("ttadev.agents.base._TRACING_AVAILABLE", True),
        patch("ttadev.agents.base._otel_trace") as mock_otel,
        patch(
            "ttadev.agents.tool_call_loop.ToolCallLoop.execute", new_callable=AsyncMock
        ) as mock_loop,
        patch.object(WorkflowContext, "spawn_agent", mock_spawn),
    ):
        mock_loop.return_value = "done"
        import opentelemetry.trace as real_otel

        mock_otel.get_tracer = provider.get_tracer
        mock_otel.get_current_span = real_otel.get_current_span
        await agent._execute_impl(task, ctx)

    mock_spawn.assert_not_awaited()
    handoff_spans = [s for s in exporter.get_finished_spans() if s.name == "agent.handoff"]
    assert handoff_spans == [], "No handoff span expected when condition is False"


# ---------------------------------------------------------------------------
# AC4 — /api/v2/tracing/dag endpoint — empty when no handoffs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dag_endpoint_empty_when_no_handoffs(tmp_path: Path):
    """GET /api/v2/tracing/dag returns empty nodes/edges when no handoff spans."""
    import aiohttp

    from ttadev.observability.server import ObservabilityServer

    port = _free_port()
    server = ObservabilityServer(port=port, data_dir=tmp_path)
    tasks_before = set(asyncio.all_tasks())
    await server.start()
    await asyncio.sleep(0.3)
    tasks_after = set(asyncio.all_tasks())
    server_tasks = tasks_after - tasks_before

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://localhost:{port}/api/v2/tracing/dag") as resp:
                assert resp.status == 200
                data = await resp.json()
                assert data["available"] is True
                assert data["nodes"] == []
                assert data["edges"] == []
    finally:
        await server.stop()
        for task in server_tasks:
            task.cancel()
        if server_tasks:
            await asyncio.gather(*server_tasks, return_exceptions=True)


# ---------------------------------------------------------------------------
# AC5 — /api/v2/tracing/dag endpoint — returns graph with injected handoff spans
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dag_endpoint_returns_nodes_and_edges(tmp_path: Path):
    """GET /api/v2/tracing/dag returns nodes and edges built from handoff spans."""
    import aiohttp

    from ttadev.observability.server import ObservabilityServer

    port = _free_port()
    server = ObservabilityServer(port=port, data_dir=tmp_path)
    tasks_before = set(asyncio.all_tasks())
    await server.start()
    await asyncio.sleep(0.3)
    tasks_after = set(asyncio.all_tasks())
    server_tasks = tasks_after - tasks_before

    try:
        # Inject synthetic handoff spans directly into the session manager.
        span1 = _make_handoff_span("architect", "developer", reason="needs code")
        span2 = _make_handoff_span("developer", "tester", reason="ready to test")

        session = server._session_mgr.get_or_create_agent_session(
            agent_id="agent-test", agent_tool="test"
        )
        server._session_mgr.add_span(session.id, span1)
        server._session_mgr.add_span(session.id, span2)

        async with aiohttp.ClientSession() as http:
            async with http.get(f"http://localhost:{port}/api/v2/tracing/dag") as resp:
                assert resp.status == 200
                data = await resp.json()

        assert data["available"] is True

        node_ids = {n["id"] for n in data["nodes"]}
        assert "architect" in node_ids
        assert "developer" in node_ids
        assert "tester" in node_ids

        # architect → developer edge
        arch_dev = [
            e for e in data["edges"] if e["source"] == "architect" and e["target"] == "developer"
        ]
        assert arch_dev, "Expected architect→developer edge"
        assert arch_dev[0]["reason"] == "needs code"

        # developer → tester edge
        dev_test = [
            e for e in data["edges"] if e["source"] == "developer" and e["target"] == "tester"
        ]
        assert dev_test, "Expected developer→tester edge"

        # architect has handed off so status should be "completed"
        arch_node = next(n for n in data["nodes"] if n["id"] == "architect")
        assert arch_node["status"] == "completed"

        # tester is the leaf node so status should be "active"
        test_node = next(n for n in data["nodes"] if n["id"] == "tester")
        assert test_node["status"] == "active"

    finally:
        await server.stop()
        for task in server_tasks:
            task.cancel()
        if server_tasks:
            await asyncio.gather(*server_tasks, return_exceptions=True)


# ---------------------------------------------------------------------------
# AC6 — SpanProcessor recognises agent.handoff spans by name
# ---------------------------------------------------------------------------


def test_span_processor_parses_handoff_span():
    """SpanProcessor.from_otel_jsonl correctly parses an agent.handoff span."""
    proc = SpanProcessor()
    raw = {
        "trace_id": "a" * 32,
        "span_id": "b" * 16,
        "parent_span_id": None,
        "name": "agent.handoff",
        "start_time": 1_700_000_000 * 10**9,
        "end_time": 1_700_000_005 * 10**9,
        "duration_ns": 5 * 10**9,
        "tta_agent_id": "agent-123",
        "tta_agent_tool": "test",
        "status": {"status_code": "OK", "description": ""},
        "attributes": {
            "handoff.from_agent": "architect",
            "handoff.to_agent": "developer",
            "handoff.task_id": "wf-42",
            "handoff.reason": "start implementation",
            "tta.agent.role": "architect",
        },
    }
    span = proc.from_otel_jsonl(raw)

    assert span.name == "agent.handoff"
    assert span.agent_role == "architect"
    assert span.attributes["handoff.from_agent"] == "architect"
    assert span.attributes["handoff.to_agent"] == "developer"
    assert span.attributes["handoff.task_id"] == "wf-42"
    assert span.attributes["handoff.reason"] == "start implementation"
