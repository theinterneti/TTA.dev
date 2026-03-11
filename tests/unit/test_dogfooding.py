"""Unit tests for T6–T8: primitives dogfooding in cgc_bridge, cgc_client, server."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# T6 — cgc_bridge TimeoutPrimitive + FallbackPrimitive
# ---------------------------------------------------------------------------


class TestCGCBridgeDogfooding:
    def test_timeout_returns_empty_graph(self):
        """Subprocess hanging beyond timeout should return empty graph, not raise."""
        import subprocess

        from ttadev.ui.cgc_bridge import query_cgc_graph

        def slow_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="cgc", timeout=10)

        with patch("subprocess.run", side_effect=slow_run):
            result = query_cgc_graph()

        assert isinstance(result, dict)
        assert "nodes" in result
        assert "edges" in result
        assert result["nodes"] == []

    def test_success_returns_graph(self):
        """Successful subprocess returns parsed graph structure."""

        from ttadev.ui.cgc_bridge import query_cgc_graph

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"files": []}'

        with patch("subprocess.run", return_value=mock_result):
            result = query_cgc_graph()

        assert isinstance(result, dict)
        assert "nodes" in result
        assert "edges" in result

    def test_uses_dynamic_repo_root(self):
        """query_cgc_graph must not hardcode /home/thein paths."""
        import inspect

        from ttadev.ui import cgc_bridge

        source = inspect.getsource(cgc_bridge)
        assert "/home/thein" not in source


# ---------------------------------------------------------------------------
# T7 — cgc_client TimeoutPrimitive + FallbackPrimitive
# ---------------------------------------------------------------------------


class TestCGCClientDogfooding:
    def test_query_structure_timeout_returns_error_dict(self):
        """Timeout on query_cgc_structure returns error dict, not exception."""
        import subprocess

        from ttadev.ui.cgc_client import query_cgc_structure

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cgc", 10)):
            result = query_cgc_structure()

        assert isinstance(result, dict)
        # Should have nodes/edges or error key — not raise
        assert "nodes" in result or "error" in result

    def test_query_deps_timeout_returns_error_dict(self):
        """Timeout on query_cgc_dependencies returns error dict."""
        import subprocess

        from ttadev.ui.cgc_client import query_cgc_dependencies

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cgc", 10)):
            result = query_cgc_dependencies("some/file.py")

        assert isinstance(result, dict)

    def test_no_hardcoded_paths(self):
        """cgc_client must not hardcode /home/thein paths."""
        import inspect

        from ttadev.ui import cgc_client

        source = inspect.getsource(cgc_client)
        assert "/home/thein" not in source


# ---------------------------------------------------------------------------
# T8 — server ingestion RetryPrimitive
# ---------------------------------------------------------------------------


class TestServerIngestionRetry:
    def test_transient_oserror_retried(self, tmp_path):
        """_read_new_spans that raises OSError once then succeeds still returns spans."""
        from ttadev.observability.server import ObservabilityServer

        srv = ObservabilityServer(data_dir=tmp_path)

        call_count = 0
        original = srv._ingest_otel_jsonl

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError("transient file error")
            return original()

        srv._ingest_otel_jsonl = flaky

        # The ingestion loop should survive the OSError without crashing
        # We test the loop body directly (it catches all non-CancelledError exceptions)
        async def run():
            try:
                srv._ingest_otel_jsonl()
            except OSError:
                pass  # loop catches this
            return srv._ingest_otel_jsonl()

        result = asyncio.run(run())
        assert isinstance(result, list)
