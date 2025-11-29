"""OTLP trace collector for TTA observability UI."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from .models import Span, SpanStatus, Trace, TraceStatus

if TYPE_CHECKING:
    from .storage import TraceStorage

logger = logging.getLogger(__name__)


class TraceCollector:
    """Collects and processes OpenTelemetry traces."""

    def __init__(self, storage: TraceStorage):
        """
        Initialize trace collector.

        Args:
            storage: Storage backend for persisting traces
        """
        self.storage = storage
        self._active_traces: dict[str, Trace] = {}

    async def collect_otlp_trace(self, otlp_data: dict[str, Any]) -> None:
        """
        Process OTLP trace data and store it.

        Args:
            otlp_data: OTLP-formatted trace data
        """
        try:
            # Extract resource spans
            resource_spans = otlp_data.get("resourceSpans", [])

            for resource_span in resource_spans:
                scope_spans = resource_span.get("scopeSpans", [])

                for scope_span in scope_spans:
                    spans_data = scope_span.get("spans", [])

                    for span_data in spans_data:
                        await self._process_span(span_data)

        except Exception:
            logger.exception("Error processing OTLP trace")

    async def _process_span(self, span_data: dict[str, Any]) -> None:  # noqa: PLR0912, PLR0915
        """Process a single OTLP span."""
        # Extract span fields
        span_id = span_data.get("spanId", "")
        trace_id = span_data.get("traceId", "")
        parent_span_id = span_data.get("parentSpanId")

        # Parse timestamps
        start_time_nano = span_data.get("startTimeUnixNano", 0)
        end_time_nano = span_data.get("endTimeUnixNano", 0)

        start_time = datetime.fromtimestamp(start_time_nano / 1e9, tz=UTC)
        end_time = (
            datetime.fromtimestamp(end_time_nano / 1e9, tz=UTC)
            if end_time_nano
            else None
        )

        # Calculate duration
        duration_ms = (
            int((end_time_nano - start_time_nano) / 1e6) if end_time_nano else None
        )

        # Extract attributes
        attributes = {}
        for attr in span_data.get("attributes", []):
            key = attr.get("key", "")
            value_dict = attr.get("value", {})
            # Get the actual value from the value dict
            if "stringValue" in value_dict:
                attributes[key] = value_dict["stringValue"]
            elif "intValue" in value_dict:
                attributes[key] = value_dict["intValue"]
            elif "doubleValue" in value_dict:
                attributes[key] = value_dict["doubleValue"]
            elif "boolValue" in value_dict:
                attributes[key] = value_dict["boolValue"]

        # Extract primitive information from attributes
        primitive_type = attributes.get("primitive.type", "Unknown")
        primitive_name = attributes.get("primitive.name", span_data.get("name", ""))
        workflow_name = attributes.get("workflow.name", "unknown_workflow")

        # Determine status
        status_code = span_data.get("status", {}).get("code", 0)
        error_code_val = 2
        span_status = (
            SpanStatus.ERROR
            if status_code == error_code_val
            else SpanStatus.SUCCESS  # ERROR
        )  # OK/UNSET

        # Extract error information
        error_message = None
        stack_trace = None
        if span_status == SpanStatus.ERROR:
            error_message = span_data.get("status", {}).get("message")
            # Look for exception events
            for event in span_data.get("events", []):
                if event.get("name") == "exception":
                    for attr in event.get("attributes", []):
                        if attr.get("key") == "exception.message":
                            error_message = attr.get("value", {}).get("stringValue")
                        elif attr.get("key") == "exception.stacktrace":
                            stack_trace = attr.get("value", {}).get("stringValue")

        # Create span model
        span = Span(
            span_id=span_id,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            primitive_type=primitive_type,
            primitive_name=primitive_name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            status=span_status,
            attributes=attributes,
            events=span_data.get("events", []),
            error_message=error_message,
            stack_trace=stack_trace,
        )

        # Get or create trace
        if trace_id not in self._active_traces:
            trace_status = (
                TraceStatus.ERROR
                if span_status == SpanStatus.ERROR
                else TraceStatus.SUCCESS
            )

            self._active_traces[trace_id] = Trace(
                trace_id=trace_id,
                workflow_name=workflow_name,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                status=trace_status,
                context_data=attributes,
                spans=[span],
            )
        else:
            # Add span to existing trace
            trace = self._active_traces[trace_id]
            trace.spans.append(span)

            # Update trace status if any span errored
            if span_status == SpanStatus.ERROR:
                trace.status = TraceStatus.ERROR
                trace.error_message = error_message

            # Update end time if this span finished later
            if end_time and (not trace.end_time or end_time > trace.end_time):
                trace.end_time = end_time

                # Recalculate duration
                if trace.start_time:
                    trace.duration_ms = int(
                        (trace.end_time - trace.start_time).total_seconds() * 1000
                    )

        # Check if trace is complete (heuristic: no parent span ID = root span)
        if not parent_span_id:
            # Save and remove from active traces
            trace = self._active_traces.pop(trace_id)
            trace.compute_stats()
            await self.storage.save_trace(trace)
            logger.info(
                "Saved complete trace",
                extra={"trace_id": trace_id, "spans": len(trace.spans)},
            )

    async def finalize_traces(self) -> None:
        """Finalize and save any remaining active traces."""
        for trace_id in list(self._active_traces.keys()):
            trace = self._active_traces.pop(trace_id)
            trace.compute_stats()
            await self.storage.save_trace(trace)
            logger.info(
                "Finalized trace",
                extra={"trace_id": trace_id, "spans": len(trace.spans)},
            )
