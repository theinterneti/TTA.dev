"""Unit tests for tracing.py agent identity integration — Task 2."""

import json
import sys
from pathlib import Path


def _fresh_tracing():
    """Reload tracing module and its identity deps with clean state."""
    for mod in list(sys.modules):
        if "agent_identity" in mod or ("tracing" in mod and "primitives" in mod):
            del sys.modules[mod]
    from ttadev.primitives.observability import tracing

    return tracing


class TestFileSpanExporterIdentity:
    def test_span_carries_tta_agent_id(self, tmp_path):
        tracing = _fresh_tracing()
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor

        out = tmp_path / "spans.jsonl"
        exporter = tracing.FileSpanExporter(str(out))
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        tracer = provider.get_tracer("test")

        with tracer.start_as_current_span("test.span"):
            pass

        data = json.loads(out.read_text().strip().splitlines()[-1])
        assert "tta_agent_id" in data
        assert data["tta_agent_id"] == tracing.get_agent_id()

    def test_span_carries_tta_agent_tool(self, tmp_path):
        tracing = _fresh_tracing()
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor

        out = tmp_path / "spans.jsonl"
        exporter = tracing.FileSpanExporter(str(out))
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        tracer = provider.get_tracer("test")

        with tracer.start_as_current_span("test.span"):
            pass

        data = json.loads(out.read_text().strip().splitlines()[-1])
        assert "tta_agent_tool" in data
        assert data["tta_agent_tool"] == tracing.get_agent_tool()

    def test_no_duplicate_identity_definitions(self):
        """tracing.py must not define its own _AGENT_ID or _get_agent_tool."""
        tracing_path = Path("ttadev/primitives/observability/tracing.py")
        source = tracing_path.read_text()
        # The old duplicates should be gone — identity comes from agent_identity
        assert "_AGENT_ID: str = " not in source or "agent_identity" in source
        assert "def _get_agent_tool" not in source

    def test_get_agent_id_importable_from_tracing(self):
        """tracing module re-exports get_agent_id for backward compat."""
        tracing = _fresh_tracing()
        assert hasattr(tracing, "get_agent_id")
        assert callable(tracing.get_agent_id)

    def test_get_agent_tool_importable_from_tracing(self):
        tracing = _fresh_tracing()
        assert hasattr(tracing, "get_agent_tool")
        assert callable(tracing.get_agent_tool)


class TestSetupTracingResource:
    def test_resource_includes_agent_id(self):
        tracing = _fresh_tracing()
        # Call setup_tracing and verify the provider resource has tta.agent_id
        tracing.setup_tracing("test-service")
        from opentelemetry import trace

        provider = trace.get_tracer_provider()
        if hasattr(provider, "resource"):
            attrs = dict(provider.resource.attributes)
            assert "tta.agent_id" in attrs
            assert attrs["tta.agent_id"] == tracing.get_agent_id()
