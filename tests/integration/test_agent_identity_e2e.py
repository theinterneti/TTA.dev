"""Integration test — agent_id flows end-to-end through the observability stack.

Task 5: Verify that agent_id set on WorkflowContext propagates to:
  1. The OTEL JSONL file written by FileSpanExporter (tta_agent_id field)
  2. ProcessedSpan.agent_id after SpanProcessor.from_otel_jsonl()
  3. Session.agent_id after SessionManager.get_or_create_agent_session()
"""

from __future__ import annotations

import json

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from ttadev.observability.agent_identity import get_agent_id
from ttadev.observability.session_manager import SessionManager
from ttadev.observability.span_processor import SpanProcessor
from ttadev.primitives.core.base import LambdaPrimitive, WorkflowContext
from ttadev.primitives.observability.tracing import FileSpanExporter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_isolated_provider(jsonl_path: str) -> TracerProvider:
    """Return a fresh TracerProvider with a synchronous FileSpanExporter.

    Uses SimpleSpanProcessor (not Batch) so every span is flushed to disk
    before the tracer.start_as_current_span context manager exits — no
    waiting or force-flush needed.
    """
    exporter = FileSpanExporter(jsonl_path)
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.integration
async def test_agent_id_on_workflow_context_is_non_none():
    """WorkflowContext must auto-populate agent_id from the identity module."""
    ctx = WorkflowContext(workflow_id="test-wf-identity")
    assert ctx.agent_id is not None, "WorkflowContext.agent_id should be auto-populated"
    assert ctx.agent_id == get_agent_id(), (
        "WorkflowContext.agent_id must match the process-stable agent identity"
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_lambda_primitive_span_carries_agent_id(tmp_path):
    """Running a LambdaPrimitive writes a span with tta_agent_id to the JSONL file."""
    jsonl_file = tmp_path / "spans.jsonl"
    provider = _build_isolated_provider(str(jsonl_file))
    tracer = provider.get_tracer("e2e-test")

    ctx = WorkflowContext(workflow_id="wf-e2e-lambda")
    primitive = LambdaPrimitive(lambda data, _ctx: data + "-processed")

    # Execute the primitive inside a span so the tracer records it.
    with tracer.start_as_current_span(
        "LambdaPrimitive",
        attributes={
            "primitive.type": "LambdaPrimitive",
            "workflow.id": ctx.workflow_id or "unknown",
        },
    ):
        result = await primitive.execute("hello", ctx)

    assert result == "hello-processed"

    # The JSONL file must exist and contain at least one span.
    assert jsonl_file.exists(), "FileSpanExporter must create the JSONL file"
    lines = [line for line in jsonl_file.read_text().splitlines() if line.strip()]
    assert lines, "At least one span line must be written"

    span_dict = json.loads(lines[-1])
    assert "tta_agent_id" in span_dict, "Span must carry tta_agent_id field"
    assert span_dict["tta_agent_id"] is not None
    assert span_dict["tta_agent_id"] == ctx.agent_id, (
        "tta_agent_id in the JSONL span must match the WorkflowContext.agent_id"
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_span_processor_preserves_agent_id(tmp_path):
    """SpanProcessor.from_otel_jsonl() must copy tta_agent_id → ProcessedSpan.agent_id."""
    jsonl_file = tmp_path / "spans.jsonl"
    provider = _build_isolated_provider(str(jsonl_file))
    tracer = provider.get_tracer("e2e-test")

    ctx = WorkflowContext(workflow_id="wf-e2e-processor")
    primitive = LambdaPrimitive(lambda data, _ctx: {"result": data})

    with tracer.start_as_current_span(
        "LambdaPrimitive",
        attributes={
            "primitive.type": "LambdaPrimitive",
            "workflow.id": ctx.workflow_id or "unknown",
        },
    ):
        await primitive.execute({"input": 42}, ctx)

    lines = [line for line in jsonl_file.read_text().splitlines() if line.strip()]
    assert lines, "Span file must not be empty"

    raw_span = json.loads(lines[-1])
    processor = SpanProcessor()
    processed = processor.from_otel_jsonl(raw_span)

    assert processed.agent_id is not None, "ProcessedSpan.agent_id must not be None"
    assert processed.agent_id == ctx.agent_id, (
        "ProcessedSpan.agent_id must equal the WorkflowContext.agent_id"
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_session_manager_creates_session_with_agent_id(tmp_path):
    """SessionManager.get_or_create_agent_session() must persist the agent_id."""
    jsonl_file = tmp_path / "spans.jsonl"
    provider = _build_isolated_provider(str(jsonl_file))
    tracer = provider.get_tracer("e2e-test")

    ctx = WorkflowContext(workflow_id="wf-e2e-session")
    primitive = LambdaPrimitive(lambda data, _ctx: data)

    with tracer.start_as_current_span(
        "LambdaPrimitive",
        attributes={"workflow.id": ctx.workflow_id or "unknown"},
    ):
        await primitive.execute("ping", ctx)

    lines = [line for line in jsonl_file.read_text().splitlines() if line.strip()]
    assert lines, "Span file must not be empty"

    raw_span = json.loads(lines[-1])
    processor = SpanProcessor()
    processed = processor.from_otel_jsonl(raw_span)

    assert processed.agent_id is not None

    # Route through SessionManager using a temp data directory.
    sm = SessionManager(data_dir=tmp_path / ".tta")
    session = sm.get_or_create_agent_session(
        agent_id=processed.agent_id,
        agent_tool=processed.agent_tool or "unknown",
    )

    assert session.agent_id == processed.agent_id, (
        "Session.agent_id must match the agent_id extracted from the span"
    )
    assert session.agent_id == ctx.agent_id, (
        "Session.agent_id must ultimately trace back to WorkflowContext.agent_id"
    )


@pytest.mark.asyncio
@pytest.mark.integration
async def test_session_manager_reuses_existing_session(tmp_path):
    """A second call with the same agent_id must return the same session (no duplicate)."""
    sm = SessionManager(data_dir=tmp_path / ".tta")
    agent_id = get_agent_id()

    session_a = sm.get_or_create_agent_session(agent_id=agent_id, agent_tool="claude-code")
    session_b = sm.get_or_create_agent_session(agent_id=agent_id, agent_tool="claude-code")

    assert session_a.id == session_b.id, (
        "get_or_create_agent_session must return the same session for the same agent_id"
    )
