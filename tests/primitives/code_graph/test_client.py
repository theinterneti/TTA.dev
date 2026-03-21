"""Unit tests for FalkorDBClient — all FalkorDB calls mocked."""

from __future__ import annotations

import socket
import threading
import time
from unittest.mock import patch

import pytest

from ttadev.primitives.code_graph.client import FalkorDBClient, _falkordb_reachable

# ── _falkordb_reachable ───────────────────────────────────────────────────────


class TestFalkordbReachable:
    def test_returns_false_when_socket_missing(self, tmp_path) -> None:
        result = _falkordb_reachable(str(tmp_path / "nonexistent.sock"))
        assert result is False

    def test_returns_false_on_connection_refused(self, tmp_path) -> None:
        import os

        sock_path = str(tmp_path / "test.sock")
        # Bind but don't listen — connect will be refused
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(sock_path)
        try:
            result = _falkordb_reachable(sock_path)
        finally:
            s.close()
            if os.path.exists(sock_path):
                os.unlink(sock_path)
        assert result is False

    def test_returns_true_on_pong_response(self, tmp_path) -> None:
        sock_path = str(tmp_path / "pong.sock")

        def _server() -> None:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.bind(sock_path)
            s.listen(1)
            conn, _ = s.accept()
            conn.recv(1024)
            conn.send(b"+PONG\r\n")
            conn.close()
            s.close()

        t = threading.Thread(target=_server, daemon=True)
        t.start()
        time.sleep(0.05)
        result = _falkordb_reachable(sock_path)
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
        captured: list[str] = []

        def _fake_query(cypher: str, params: dict | None = None) -> list:
            captured.append(cypher)
            return []

        with patch.object(client, "_query_sync", side_effect=_fake_query):
            await client.find_code("fn", repo_path="/home/user/myrepo")

        assert all("/home/user/myrepo" in q for q in captured)


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
