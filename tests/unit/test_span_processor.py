"""Unit tests for SpanProcessor — Task 1 (RED).

Tests cover all three input formats and all attribute extractors.
All tests must fail before implementation exists.
"""

import pytest

from ttadev.observability.span_processor import SpanProcessor


@pytest.fixture
def processor() -> SpanProcessor:
    return SpanProcessor()


# ---------------------------------------------------------------------------
# from_otel_jsonl
# ---------------------------------------------------------------------------


def test_from_otel_jsonl_extracts_provider(processor: SpanProcessor) -> None:
    raw = {
        "trace_id": "abc123",
        "span_id": "s1",
        "parent_span_id": None,
        "name": "retry.execute",
        "start_time": "2026-03-10T10:00:00Z",
        "duration_ns": 150_000_000,
        "status": {"status_code": "OK"},
        "attributes": {"ai.provider": "anthropic"},
    }
    span = processor.from_otel_jsonl(raw)
    assert span.provider == "Anthropic"


def test_from_otel_jsonl_extracts_model(processor: SpanProcessor) -> None:
    raw = {
        "trace_id": "abc123",
        "span_id": "s1",
        "parent_span_id": None,
        "name": "cache.execute",
        "start_time": "2026-03-10T10:00:00Z",
        "duration_ns": 50_000_000,
        "status": {"status_code": "OK"},
        "attributes": {"ai.model": "claude-sonnet-4-6"},
    }
    span = processor.from_otel_jsonl(raw)
    assert span.model == "claude-sonnet-4-6"


def test_from_otel_jsonl_extracts_agent_role(processor: SpanProcessor) -> None:
    raw = {
        "trace_id": "abc123",
        "span_id": "s1",
        "parent_span_id": None,
        "name": "workflow.execute",
        "start_time": "2026-03-10T10:00:00Z",
        "duration_ns": 200_000_000,
        "status": {"status_code": "OK"},
        "attributes": {"tta.agent.role": "backend-engineer"},
    }
    span = processor.from_otel_jsonl(raw)
    assert span.agent_role == "backend-engineer"


def test_from_otel_jsonl_missing_fields_fallback(processor: SpanProcessor) -> None:
    raw = {
        "trace_id": "abc123",
        "span_id": "s1",
        "parent_span_id": None,
        "name": "some.span",
        "start_time": "2026-03-10T10:00:00Z",
        "duration_ns": 0,
        "status": {"status_code": "OK"},
        "attributes": {},
    }
    span = processor.from_otel_jsonl(raw)
    assert span.provider == "TTA.dev"  # primitive span with no ai.provider defaults to TTA.dev
    assert span.model == "primitives"  # TTA.dev primitive spans use "primitives" as model
    assert span.agent_role is None
    assert span.workflow_id is None


def test_from_otel_jsonl_duration_converted_to_ms(processor: SpanProcessor) -> None:
    raw = {
        "trace_id": "abc123",
        "span_id": "s1",
        "parent_span_id": None,
        "name": "retry.execute",
        "start_time": "2026-03-10T10:00:00Z",
        "duration_ns": 250_000_000,
        "status": {"status_code": "OK"},
        "attributes": {},
    }
    span = processor.from_otel_jsonl(raw)
    assert span.duration_ms == pytest.approx(250.0)


def test_from_otel_jsonl_error_status(processor: SpanProcessor) -> None:
    raw = {
        "trace_id": "abc123",
        "span_id": "s1",
        "parent_span_id": None,
        "name": "retry.execute",
        "start_time": "2026-03-10T10:00:00Z",
        "duration_ns": 100_000_000,
        "status": {"status_code": "ERROR"},
        "attributes": {},
    }
    span = processor.from_otel_jsonl(raw)
    assert span.status == "error"


# ---------------------------------------------------------------------------
# from_activity_log
# ---------------------------------------------------------------------------


def test_from_activity_log_basic(processor: SpanProcessor) -> None:
    raw = {
        "trace_id": "xyz789",
        "timestamp": "2026-03-10T11:00:00",
        "activity_type": "workflow_execution",
        "provider": "github_copilot",
        "model": "claude-sonnet-4.5",
        "agent": "architect",
        "user": "thein",
        "details": {"duration_ns": 300_000_000},
    }
    span = processor.from_activity_log(raw)
    assert span.trace_id == "xyz789"
    assert span.provider == "GitHub Copilot"
    assert span.model == "claude-sonnet-4.5"
    assert span.agent_role == "architect"
    assert span.status == "success"


def test_from_activity_log_no_agent(processor: SpanProcessor) -> None:
    raw = {
        "trace_id": "xyz789",
        "timestamp": "2026-03-10T11:00:00",
        "activity_type": "api_call",
        "provider": "openrouter",
        "model": "llama-3.1-70b",
        "agent": None,
        "user": "thein",
        "details": {},
    }
    span = processor.from_activity_log(raw)
    assert span.agent_role is None


def test_from_activity_log_duration_from_details(processor: SpanProcessor) -> None:
    raw = {
        "trace_id": "xyz789",
        "timestamp": "2026-03-10T11:00:00",
        "activity_type": "api_call",
        "provider": "anthropic",
        "model": "claude-sonnet-4-6",
        "agent": None,
        "user": "thein",
        "details": {"duration_ns": 500_000_000},
    }
    span = processor.from_activity_log(raw)
    assert span.duration_ms == pytest.approx(500.0)


# ---------------------------------------------------------------------------
# from_agent_tracker
# ---------------------------------------------------------------------------


def test_from_agent_tracker_basic(processor: SpanProcessor) -> None:
    raw = {
        "timestamp": "2026-03-10T12:00:00",
        "provider": "openrouter",
        "model": "gpt-4o",
        "tta_agent": "testing-specialist",
        "user": "thein",
        "action_type": "tool_call",
        "action_data": {"tool": "bash", "args": "pytest"},
    }
    span = processor.from_agent_tracker(raw)
    assert span.provider == "OpenRouter"
    assert span.model == "gpt-4o"
    assert span.agent_role == "testing-specialist"
    assert span.name == "tool_call"


def test_from_agent_tracker_no_tta_agent(processor: SpanProcessor) -> None:
    raw = {
        "timestamp": "2026-03-10T12:00:00",
        "provider": "ollama",
        "model": "llama3",
        "tta_agent": None,
        "user": "thein",
        "action_type": "completion",
        "action_data": {},
    }
    span = processor.from_agent_tracker(raw)
    assert span.agent_role is None


# ---------------------------------------------------------------------------
# extract_primitive_type
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "span_name,expected",
    [
        ("retry.execute", "RetryPrimitive"),
        ("RetryPrimitive.execute", "RetryPrimitive"),
        ("cache.execute", "CachePrimitive"),
        ("CachePrimitive.get", "CachePrimitive"),
        ("circuit_breaker.call", "CircuitBreakerPrimitive"),
        ("timeout.wrap", "TimeoutPrimitive"),
        ("fallback.execute", "FallbackPrimitive"),
        ("parallel.run", "ParallelPrimitive"),
        ("sequential.execute", "SequentialPrimitive"),
        ("lambda.call", "LambdaPrimitive"),
        ("my_custom_fn", None),
        ("api_call", None),
    ],
)
def test_extract_primitive_type_name_inference(
    processor: SpanProcessor, span_name: str, expected: str | None
) -> None:
    result = processor.extract_primitive_type(span_name, {})
    assert result == expected


def test_extract_primitive_type_attribute_takes_priority(
    processor: SpanProcessor,
) -> None:
    # Even if name looks like "cache", the explicit attribute wins
    result = processor.extract_primitive_type(
        "cache.execute", {"tta.primitive.type": "CircuitBreakerPrimitive"}
    )
    assert result == "CircuitBreakerPrimitive"


def test_extract_primitive_type_unknown_returns_none(
    processor: SpanProcessor,
) -> None:
    result = processor.extract_primitive_type("completely_unknown_span", {})
    assert result is None
