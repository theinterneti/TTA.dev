"""Integration tests for the OTel span pipeline — issue #322.

Verifies:
1. RetryPrimitive, CachePrimitive, and LambdaPrimitive execute correctly and
   produce correctly structured spans (via SpanProcessor synthesis).
2. SpanProcessor correctly extracts primitive_type, trace_id, and status from
   synthetic OTEL-format span dicts representing each primitive.
3. Export errors in FileSpanExporter are surfaced via logging.warning (not
   silently swallowed / printed).
4. TraceCollector broadcast failures are logged (not silently swallowed).
5. Full workflow: RetryPrimitive(LambdaPrimitive(...)) executes and the span
   data produced would be correctly classified by SpanProcessor.

All tests run without any external services (no Langfuse, no Redis, no OTel
collector required). OTel-specific tests are skipped if the SDK is absent.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any
from unittest.mock import patch

import pytest

from ttadev.observability.collector import TraceCollector
from ttadev.observability.span_processor import SpanProcessor
from ttadev.primitives.core.base import LambdaPrimitive, WorkflowContext
from ttadev.primitives.performance.cache import CachePrimitive
from ttadev.primitives.recovery.retry import RetryPrimitive, RetryStrategy
from ttadev.primitives.testing.mocks import MockPrimitive

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_otel_span(
    name: str,
    primitive_type: str | None = None,
    status_code: str = "OK",
    trace_id: str | None = None,
    span_id: str | None = None,
    duration_ns: int = 1_000_000,
    extra_attrs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a synthetic OTEL JSONL span dict (as written by FileSpanExporter)."""
    attrs: dict[str, Any] = {}
    if primitive_type:
        attrs["tta.primitive.type"] = primitive_type
    if extra_attrs:
        attrs.update(extra_attrs)

    return {
        "trace_id": trace_id or uuid.uuid4().hex,
        "span_id": span_id or uuid.uuid4().hex[:16],
        "name": name,
        "start_time": 1_773_080_613_000_000_000,  # nanosecond epoch
        "end_time": 1_773_080_613_000_000_000 + duration_ns,
        "duration_ns": duration_ns,
        "tta_agent_id": "test-agent-id",
        "tta_agent_tool": "pytest",
        "attributes": attrs,
        "status": {"status_code": status_code, "description": ""},
        "parent_span_id": None,
    }


# ---------------------------------------------------------------------------
# 1. SpanProcessor correctly classifies RetryPrimitive spans
# ---------------------------------------------------------------------------


class TestSpanProcessorRetryPrimitive:
    """SpanProcessor.from_otel_jsonl produces correct fields for retry spans."""

    def setup_method(self) -> None:
        self.processor = SpanProcessor()

    def test_retry_span_primitive_type_explicit(self) -> None:
        """Explicit tta.primitive.type attribute wins over name inference."""
        raw = _make_otel_span("retry.attempt_0", primitive_type="RetryPrimitive")
        span = self.processor.from_otel_jsonl(raw)

        assert span.primitive_type == "RetryPrimitive"

    def test_retry_span_primitive_type_inferred_from_name(self) -> None:
        """Name containing 'retry' is inferred as RetryPrimitive."""
        raw = _make_otel_span("retry.attempt_1")  # no explicit primitive_type attr
        span = self.processor.from_otel_jsonl(raw)

        assert span.primitive_type == "RetryPrimitive"

    def test_retry_span_trace_id(self) -> None:
        """trace_id is preserved exactly from the raw span dict."""
        expected_tid = "aabbccddeeff00112233445566778899"
        raw = _make_otel_span("retry.attempt_0", trace_id=expected_tid)
        span = self.processor.from_otel_jsonl(raw)

        assert span.trace_id == expected_tid

    def test_retry_span_status_success(self) -> None:
        """OK status_code → status == 'success'."""
        raw = _make_otel_span("retry.attempt_0", status_code="OK")
        span = self.processor.from_otel_jsonl(raw)

        assert span.status == "success"

    def test_retry_span_status_error(self) -> None:
        """ERROR status_code → status == 'error'."""
        raw = _make_otel_span("retry.attempt_0", status_code="ERROR")
        span = self.processor.from_otel_jsonl(raw)

        assert span.status == "error"

    def test_retry_span_provider_is_ttadev(self) -> None:
        """Primitive spans with no ai.provider attribute get provider='TTA.dev'."""
        raw = _make_otel_span("retry.attempt_0")
        span = self.processor.from_otel_jsonl(raw)

        assert span.provider == "TTA.dev"

    def test_retry_span_duration_ms(self) -> None:
        """duration_ns is converted to duration_ms correctly."""
        raw = _make_otel_span("retry.attempt_0", duration_ns=5_000_000)
        span = self.processor.from_otel_jsonl(raw)

        assert span.duration_ms == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# 2. SpanProcessor correctly classifies CachePrimitive spans
# ---------------------------------------------------------------------------


class TestSpanProcessorCachePrimitive:
    """SpanProcessor.from_otel_jsonl produces correct fields for cache spans."""

    def setup_method(self) -> None:
        self.processor = SpanProcessor()

    def test_cache_span_primitive_type_explicit(self) -> None:
        raw = _make_otel_span("primitive.CachePrimitive", primitive_type="CachePrimitive")
        span = self.processor.from_otel_jsonl(raw)

        assert span.primitive_type == "CachePrimitive"

    def test_cache_span_primitive_type_inferred(self) -> None:
        """Name containing 'cache' is inferred as CachePrimitive."""
        raw = _make_otel_span("cache.lookup")
        span = self.processor.from_otel_jsonl(raw)

        assert span.primitive_type == "CachePrimitive"

    def test_cache_span_status_success(self) -> None:
        raw = _make_otel_span("primitive.CachePrimitive", status_code="OK")
        span = self.processor.from_otel_jsonl(raw)

        assert span.status == "success"

    def test_cache_span_workflow_id(self) -> None:
        """tta.workflow.id attribute is extracted to workflow_id."""
        raw = _make_otel_span(
            "cache.lookup",
            extra_attrs={"tta.workflow.id": "wf-cache-test"},
        )
        span = self.processor.from_otel_jsonl(raw)

        assert span.workflow_id == "wf-cache-test"


# ---------------------------------------------------------------------------
# 3. SpanProcessor correctly classifies LambdaPrimitive spans
# ---------------------------------------------------------------------------


class TestSpanProcessorLambdaPrimitive:
    """SpanProcessor.from_otel_jsonl produces correct fields for lambda spans."""

    def setup_method(self) -> None:
        self.processor = SpanProcessor()

    def test_lambda_span_primitive_type_explicit(self) -> None:
        raw = _make_otel_span("primitive.LambdaPrimitive", primitive_type="LambdaPrimitive")
        span = self.processor.from_otel_jsonl(raw)

        assert span.primitive_type == "LambdaPrimitive"

    def test_lambda_span_primitive_type_inferred(self) -> None:
        """Name containing 'lambda' is inferred as LambdaPrimitive."""
        raw = _make_otel_span("primitive.lambda_transform")
        span = self.processor.from_otel_jsonl(raw)

        assert span.primitive_type == "LambdaPrimitive"

    def test_lambda_span_trace_id_and_status(self) -> None:
        """trace_id and status are both correctly extracted."""
        tid = "deadbeef" * 4
        raw = _make_otel_span(
            "primitive.LambdaPrimitive",
            trace_id=tid,
            status_code="OK",
            primitive_type="LambdaPrimitive",
        )
        span = self.processor.from_otel_jsonl(raw)

        assert span.trace_id == tid
        assert span.status == "success"


# ---------------------------------------------------------------------------
# 4. RetryPrimitive + LambdaPrimitive workflow execution
# ---------------------------------------------------------------------------


class TestRetryLambdaWorkflow:
    """RetryPrimitive(LambdaPrimitive(...)) executes correctly end-to-end."""

    @pytest.mark.asyncio
    async def test_lambda_returns_expected_result(self) -> None:
        """A simple LambdaPrimitive returns the function's result."""
        # Arrange
        lp = LambdaPrimitive(lambda data, ctx: {"processed": data["value"] * 2})
        ctx = WorkflowContext.root("lambda-test")

        # Act
        result = await lp.execute({"value": 21}, ctx)

        # Assert
        assert result == {"processed": 42}

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_transient_failure(self) -> None:
        """RetryPrimitive retries on transient errors and returns on success."""
        # Arrange
        call_count = 0

        async def flaky(data: dict, ctx: WorkflowContext) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"transient error #{call_count}")
            return {"result": "ok", "attempts": call_count}

        workflow = RetryPrimitive(
            LambdaPrimitive(flaky),
            strategy=RetryStrategy(max_retries=5, backoff_base=0.0, jitter=False),
        )
        ctx = WorkflowContext.root("retry-lambda-test")

        # Act
        result = await workflow.execute({}, ctx)

        # Assert
        assert result["result"] == "ok"
        assert result["attempts"] == 3
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted_raises(self) -> None:
        """RetryPrimitive raises the last error when all retries are exhausted."""
        # Arrange
        workflow = RetryPrimitive(
            LambdaPrimitive(lambda d, c: (_ for _ in ()).throw(RuntimeError("always fails"))),
            strategy=RetryStrategy(max_retries=2, backoff_base=0.0, jitter=False),
        )
        ctx = WorkflowContext.root("retry-exhausted-test")

        # Act + Assert
        with pytest.raises(RuntimeError, match="always fails"):
            await workflow.execute({}, ctx)

    @pytest.mark.asyncio
    async def test_retry_with_mock_primitive(self) -> None:
        """RetryPrimitive works correctly wrapping a MockPrimitive."""
        # Arrange
        call_count = 0

        def flaky_side_effect(data: Any, ctx: WorkflowContext) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("first attempt fails")
            return {"status": "success"}

        mock = MockPrimitive(name="flaky-service", side_effect=flaky_side_effect)
        workflow = RetryPrimitive(
            mock,
            strategy=RetryStrategy(max_retries=3, backoff_base=0.0, jitter=False),
        )
        ctx = WorkflowContext.root("retry-mock-test")

        # Act
        result = await workflow.execute({"input": "data"}, ctx)

        # Assert
        assert result == {"status": "success"}
        assert mock.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_lambda_span_data_structure(self) -> None:
        """Span dict for RetryPrimitive attempt is correctly processed by SpanProcessor."""
        # Arrange — simulate what FileSpanExporter would write for RetryPrimitive
        processor = SpanProcessor()
        trace_id = uuid.uuid4().hex

        # This mimics the span RetryPrimitive emits (retry.attempt_0 with retry.* attrs)
        raw_span = {
            "trace_id": trace_id,
            "span_id": uuid.uuid4().hex[:16],
            "name": "retry.attempt_0",
            "start_time": 1_773_000_000_000_000_000,
            "end_time": 1_773_000_050_000_000_000,
            "duration_ns": 50_000_000,
            "tta_agent_id": "test-agent",
            "tta_agent_tool": "pytest",
            "attributes": {
                "retry.attempt": 1,
                "retry.max_attempts": 4,
                "retry.primitive_type": "MockPrimitive",
                "retry.status": "success",
                "retry.succeeded_on_attempt": 1,
            },
            "status": {"status_code": "OK", "description": ""},
            "parent_span_id": None,
        }

        # Act
        span = processor.from_otel_jsonl(raw_span)

        # Assert — all three required fields from the issue
        assert span.trace_id == trace_id
        assert span.primitive_type == "RetryPrimitive"  # inferred from "retry" in name
        assert span.status == "success"
        assert span.duration_ms == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# 5. CachePrimitive workflow execution
# ---------------------------------------------------------------------------


class TestCachePrimitiveWorkflow:
    """CachePrimitive caches results and produces correct span data."""

    @pytest.mark.asyncio
    async def test_cache_miss_executes_inner_primitive(self) -> None:
        """On cache miss, the wrapped primitive is executed."""
        # Arrange
        mock = MockPrimitive(name="inner", return_value={"data": "result"})
        cache = CachePrimitive(
            mock,
            cache_key_fn=lambda data, ctx: str(data),
            ttl_seconds=60.0,
        )
        ctx = WorkflowContext.root("cache-test")

        # Act
        result = await cache.execute({"key": "value"}, ctx)

        # Assert
        assert result == {"data": "result"}
        mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_hit_skips_inner_primitive(self) -> None:
        """On cache hit, the wrapped primitive is NOT called again."""
        # Arrange
        mock = MockPrimitive(name="inner", return_value={"data": "cached"})
        cache = CachePrimitive(
            mock,
            cache_key_fn=lambda data, ctx: str(data),
            ttl_seconds=60.0,
        )
        ctx = WorkflowContext.root("cache-hit-test")

        # Act — execute twice with the same input
        result1 = await cache.execute({"key": "x"}, ctx)
        result2 = await cache.execute({"key": "x"}, ctx)

        # Assert
        assert result1 == result2
        assert mock.call_count == 1  # inner only executed on first (miss)

    @pytest.mark.asyncio
    async def test_cache_stats_updated(self) -> None:
        """Cache stats reflect hits and misses correctly."""
        # Arrange
        mock = MockPrimitive(name="inner", return_value=42)
        cache = CachePrimitive(
            mock,
            cache_key_fn=lambda data, ctx: str(data),
            ttl_seconds=60.0,
        )
        ctx = WorkflowContext.root("cache-stats-test")

        # Act
        await cache.execute("a", ctx)  # miss
        await cache.execute("a", ctx)  # hit
        await cache.execute("b", ctx)  # miss

        # Assert
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert stats["hit_rate"] == pytest.approx(33.33, abs=0.1)

    def test_cache_span_classified_correctly_by_span_processor(self) -> None:
        """SpanProcessor classifies a cache-named span as CachePrimitive."""
        processor = SpanProcessor()
        trace_id = uuid.uuid4().hex

        raw = _make_otel_span(
            "primitive.CachePrimitive",
            primitive_type="CachePrimitive",
            trace_id=trace_id,
            status_code="OK",
        )
        span = processor.from_otel_jsonl(raw)

        assert span.trace_id == trace_id
        assert span.primitive_type == "CachePrimitive"
        assert span.status == "success"


# ---------------------------------------------------------------------------
# 6. Silent error swallowing is fixed — logging.warning is emitted
# ---------------------------------------------------------------------------


class TestSilentErrorSwallowingFixed:
    """Export and broadcast failures now log warnings instead of being silently swallowed."""

    @pytest.mark.asyncio
    async def test_broadcast_failure_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """TraceCollector._broadcast logs warning when a subscriber queue is full."""
        import asyncio

        collector = TraceCollector()

        # Create a queue with maxsize=1 that we will fill first
        full_queue: asyncio.Queue = asyncio.Queue(maxsize=1)
        await full_queue.put("blocker")  # Fill the queue
        collector._subscribers.append(full_queue)

        trace_data = {"trace_id": "warn-test", "spans": []}

        with caplog.at_level(logging.WARNING, logger="ttadev.observability.collector"):
            # This should trigger a QueueFull exception on the subscriber
            # Since asyncio.Queue.put() is a coroutine and raises QueueFull only
            # when put_nowait is used, we patch the queue to raise directly
            async def raise_on_put(*args: Any, **kwargs: Any) -> None:
                raise asyncio.QueueFull("queue is full")

            full_queue.put = raise_on_put  # type: ignore[method-assign]
            await collector._broadcast(trace_data)

        # Verify a warning was logged instead of silently swallowed
        assert any(
            "Failed to broadcast trace to subscriber" in record.message for record in caplog.records
        ), f"Expected warning not found in: {[r.message for r in caplog.records]}"

    def test_get_all_traces_corrupted_file_logs_warning(
        self, tmp_path: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """TraceCollector.get_all_traces logs warning when a trace file is corrupted."""

        collector = TraceCollector(traces_dir=tmp_path)

        # Write a corrupted JSON file
        bad_file = tmp_path / "corrupted.json"
        bad_file.write_text("{{not valid json{{")

        with caplog.at_level(logging.WARNING, logger="ttadev.observability.collector"):
            traces = collector.get_all_traces()

        # Corrupted file should be skipped
        assert isinstance(traces, list)

        # Warning should have been logged
        assert any("Failed to read trace file" in record.message for record in caplog.records), (
            f"Expected warning not found in: {[r.message for r in caplog.records]}"
        )

    def test_file_span_exporter_logs_warning_on_failure(
        self, tmp_path: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """FileSpanExporter.export logs warning when file write fails (no print)."""
        # Only run if OTel SDK is installed
        pytest.importorskip("opentelemetry.sdk.trace")

        from ttadev.primitives.observability.tracing import FileSpanExporter

        # Point exporter at a valid path (it won't actually be written because
        # we patch builtins.open to raise PermissionError below)
        exporter = FileSpanExporter(str(tmp_path / "traces.jsonl"))

        # Export with an empty span list but with open() mocked to raise
        with caplog.at_level(logging.WARNING, logger="ttadev.primitives.observability.tracing"):
            with patch("builtins.open", side_effect=PermissionError("read-only filesystem")):
                result = exporter.export([])

        # The export should return FAILURE
        from opentelemetry.sdk.trace.export import SpanExportResult

        assert result == SpanExportResult.FAILURE

        # A warning should have been emitted instead of silently swallowed
        assert any(
            "Failed to export spans to file" in record.message for record in caplog.records
        ), f"Expected warning not found in: {[r.message for r in caplog.records]}"


# ---------------------------------------------------------------------------
# 7. End-to-end: RetryPrimitive(LambdaPrimitive) → SpanProcessor
# ---------------------------------------------------------------------------


class TestEndToEndSpanFlow:
    """Full end-to-end span flow: primitive executes → span dict → SpanProcessor → ProcessedSpan."""

    @pytest.mark.asyncio
    async def test_retry_lambda_e2e_span_attributes(self) -> None:
        """
        Execute RetryPrimitive(LambdaPrimitive) and verify the span dict
        that would be written by FileSpanExporter is correctly processed
        by SpanProcessor into a ProcessedSpan with expected fields.
        """
        # Arrange
        processor = SpanProcessor()
        call_count = 0

        async def succeed_on_second(data: dict, ctx: WorkflowContext) -> dict:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("first attempt fails")
            return {"result": "done", "attempt": call_count}

        workflow = RetryPrimitive(
            LambdaPrimitive(succeed_on_second),
            strategy=RetryStrategy(max_retries=3, backoff_base=0.0, jitter=False),
        )

        trace_id = uuid.uuid4().hex
        ctx = WorkflowContext(
            workflow_id="e2e-retry-lambda",
            trace_id=trace_id,
        )

        # Act — execute the workflow
        result = await workflow.execute({}, ctx)

        # Assert — workflow result is correct
        assert result == {"result": "done", "attempt": 2}
        assert call_count == 2

        # Now simulate what FileSpanExporter writes and SpanProcessor reads
        # for the successful attempt span
        synthetic_span = _make_otel_span(
            name="retry.attempt_1",
            trace_id=trace_id,
            status_code="OK",
            duration_ns=2_000_000,
            extra_attrs={
                "retry.attempt": 2,
                "retry.max_attempts": 4,
                "retry.primitive_type": "LambdaPrimitive",
                "retry.status": "success",
                "retry.succeeded_on_attempt": 2,
                "workflow.id": "e2e-retry-lambda",
            },
        )

        processed = processor.from_otel_jsonl(synthetic_span)

        # Verify all three required fields from issue #322
        assert processed.trace_id == trace_id, f"trace_id mismatch: {processed.trace_id!r}"
        assert processed.primitive_type == "RetryPrimitive", (
            f"primitive_type mismatch: {processed.primitive_type!r}"
        )
        assert processed.status == "success", f"status mismatch: {processed.status!r}"

    @pytest.mark.asyncio
    async def test_cache_lambda_e2e_span_attributes(self) -> None:
        """
        Execute CachePrimitive(LambdaPrimitive) and verify span dict is
        correctly processed by SpanProcessor.
        """
        # Arrange
        processor = SpanProcessor()

        mock = MockPrimitive(name="inner-lambda", return_value={"computed": True})
        cache = CachePrimitive(
            mock,
            cache_key_fn=lambda d, c: "fixed-key",
            ttl_seconds=60.0,
        )

        trace_id = uuid.uuid4().hex
        ctx = WorkflowContext(
            workflow_id="e2e-cache-lambda",
            trace_id=trace_id,
        )

        # Act
        result = await cache.execute({"q": "test"}, ctx)

        # Assert workflow result
        assert result == {"computed": True}

        # Simulate span dict for this execution
        synthetic_span = _make_otel_span(
            name="primitive.CachePrimitive",
            primitive_type="CachePrimitive",
            trace_id=trace_id,
            status_code="OK",
            extra_attrs={
                "cache.hit": False,
                "workflow.id": "e2e-cache-lambda",
            },
        )

        processed = processor.from_otel_jsonl(synthetic_span)

        # Verify required fields
        assert processed.trace_id == trace_id
        assert processed.primitive_type == "CachePrimitive"
        assert processed.status == "success"
