"""Unit tests for FalkorDBClient — all FalkorDB calls mocked."""

from __future__ import annotations

import socket
from unittest.mock import MagicMock, patch

import pytest

from ttadev.primitives.code_graph.client import FalkorDBClient, _falkordb_reachable

# ── _falkordb_reachable ───────────────────────────────────────────────────────


class TestFalkordbReachable:
    def test_returns_false_when_socket_missing(self, tmp_path) -> None:
        result = _falkordb_reachable(str(tmp_path / "nonexistent.sock"))
        assert result is False

    def test_returns_false_when_unix_sockets_unsupported(self, monkeypatch, tmp_path) -> None:
        monkeypatch.delattr(socket, "AF_UNIX", raising=False)
        with patch("ttadev.primitives.code_graph.client.os.path.exists", return_value=True):
            result = _falkordb_reachable(str(tmp_path / "existing.sock"))
        assert result is False

    def test_returns_false_on_connection_refused(self) -> None:
        mock_socket = MagicMock()
        mock_socket.connect.side_effect = OSError("connection refused")
        mock_factory = MagicMock()
        mock_factory.return_value.__enter__.return_value = mock_socket

        with (
            patch("ttadev.primitives.code_graph.client.os.path.exists", return_value=True),
            patch.object(socket, "AF_UNIX", 1, create=True),
            patch("ttadev.primitives.code_graph.client.socket.socket", mock_factory),
        ):
            result = _falkordb_reachable("/tmp/test.sock")

        assert result is False

    def test_returns_true_on_pong_response(self) -> None:
        mock_socket = MagicMock()
        mock_socket.recv.return_value = b"+PONG\r\n"
        mock_factory = MagicMock()
        mock_factory.return_value.__enter__.return_value = mock_socket

        with (
            patch("ttadev.primitives.code_graph.client.os.path.exists", return_value=True),
            patch.object(socket, "AF_UNIX", 1, create=True),
            patch("ttadev.primitives.code_graph.client.socket.socket", mock_factory),
        ):
            result = _falkordb_reachable("/tmp/pong.sock")

        mock_socket.connect.assert_called_once_with("/tmp/pong.sock")
        mock_socket.send.assert_called_once_with(b"*1\r\n$4\r\nPING\r\n")
        assert result is True


# ── FalkorDBClient ────────────────────────────────────────────────────────────


class TestFalkorDBClientFindCode:
    @pytest.mark.asyncio
    async def test_find_code_returns_functions_and_classes(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        call_count = 0

        def _fake_query(cypher: str, params: dict | None = None) -> list:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [["RetryPrimitive", "/src/retry.py", 10]]  # Function row
            return [["RetryPrimitive", "/src/retry.py", 5]]  # Class row

        with patch.object(client, "_query_sync", side_effect=_fake_query):
            result = await client.find_code("RetryPrimitive")

        assert len(result) == 2
        assert any(r["kind"] == "Function" for r in result)
        assert any(r["kind"] == "Class" for r in result)
        assert result[0]["name"] == "RetryPrimitive"

    @pytest.mark.asyncio
    async def test_find_code_with_repo_path_filter(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        captured_queries: list[str] = []
        captured_params: list[dict] = []

        def _fake_query(cypher: str, params: dict | None = None) -> list:
            captured_queries.append(cypher)
            captured_params.append(params or {})
            return []

        with patch.object(client, "_query_sync", side_effect=_fake_query):
            await client.find_code("fn", repo_path="/home/user/myrepo")

        assert all("$repo_path" in q for q in captured_queries)
        assert all(p.get("repo_path") == "/home/user/myrepo" for p in captured_params)


class TestFalkorDBClientRelationships:
    @pytest.mark.asyncio
    async def test_get_callers_returns_caller_dicts(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        with patch.object(client, "_query_sync", return_value=[["execute", "/src/base.py", 75]]):
            result = await client.get_callers("_execute_impl")

        assert len(result) == 1
        assert result[0]["name"] == "execute"
        assert result[0]["path"] == "/src/base.py"
        assert result[0]["line_number"] == 75

    @pytest.mark.asyncio
    async def test_get_callees_returns_callee_dicts(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        with patch.object(client, "_query_sync", return_value=[["_run_step", "/src/orch.py", 42]]):
            result = await client.get_callees("execute")

        assert result[0]["name"] == "_run_step"


class TestFalkorDBClientComplexity:
    @pytest.mark.asyncio
    async def test_get_complexity_returns_float(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        with patch.object(client, "_query_sync", return_value=[[7.0]]):
            result = await client.get_complexity("my_fn")
        assert result == 7.0

    @pytest.mark.asyncio
    async def test_get_complexity_returns_zero_when_not_found(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        with patch.object(client, "_query_sync", return_value=[]):
            result = await client.get_complexity("unknown_fn")
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_get_complexity_returns_zero_on_null(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        with patch.object(client, "_query_sync", return_value=[[None]]):
            result = await client.get_complexity("fn_no_complexity")
        assert result == 0.0


class TestFalkorDBClientCypher:
    @pytest.mark.asyncio
    async def test_execute_cypher_returns_row_dicts(self) -> None:
        client = FalkorDBClient(socket_path="/fake/path")
        with patch.object(client, "_query_sync", return_value=[["fn1", "path1"], ["fn2", "path2"]]):
            result = await client.execute_cypher("MATCH (f:Function) RETURN f.name, f.path")

        assert len(result) == 2
        assert result[0]["values"] == ["fn1", "path1"]
        assert result[1]["values"] == ["fn2", "path2"]
