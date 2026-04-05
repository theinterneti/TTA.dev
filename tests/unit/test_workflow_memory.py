"""Unit tests for ttadev/workflows/memory.py.

74 stmts, target 70%+ coverage.
Tests: WorkflowMemory, PersistentMemory graceful degradation, _HttpHindsightShim.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from ttadev.workflows.memory import PersistentMemory, WorkflowMemory, _HttpHindsightShim

# ── WorkflowMemory: set / get ─────────────────────────────────────────────────


class TestWorkflowMemorySetGet:
    def test_get_missing_key_returns_none(self) -> None:
        mem = WorkflowMemory()
        assert mem.get("missing") is None

    def test_get_missing_key_custom_default(self) -> None:
        mem = WorkflowMemory()
        assert mem.get("missing", default="fallback") == "fallback"

    def test_get_missing_numeric_default(self) -> None:
        mem = WorkflowMemory()
        assert mem.get("num", default=42) == 42

    def test_set_and_get_string(self) -> None:
        mem = WorkflowMemory()
        mem.set("key", "value")
        assert mem.get("key") == "value"

    def test_set_and_get_integer(self) -> None:
        mem = WorkflowMemory()
        mem.set("count", 99)
        assert mem.get("count") == 99

    def test_set_and_get_nested_dict(self) -> None:
        mem = WorkflowMemory()
        mem.set("cfg", {"a": {"b": [1, 2]}})
        assert mem.get("cfg") == {"a": {"b": [1, 2]}}

    def test_set_overrides_existing(self) -> None:
        mem = WorkflowMemory()
        mem.set("k", "original")
        mem.set("k", "updated")
        assert mem.get("k") == "updated"

    def test_set_multiple_independent_keys(self) -> None:
        mem = WorkflowMemory()
        mem.set("a", 1)
        mem.set("b", 2)
        assert mem.get("a") == 1
        assert mem.get("b") == 2

    def test_set_none_value(self) -> None:
        mem = WorkflowMemory()
        mem.set("k", None)
        assert mem.get("k") is None

    def test_set_bool_false(self) -> None:
        mem = WorkflowMemory()
        mem.set("flag", False)
        assert mem.get("flag") is False


# ── WorkflowMemory: append ────────────────────────────────────────────────────


class TestWorkflowMemoryAppend:
    def test_append_new_key_creates_list(self) -> None:
        mem = WorkflowMemory()
        mem.append("items", "first")
        assert mem.get("items") == ["first"]

    def test_append_multiple_builds_list(self) -> None:
        mem = WorkflowMemory()
        mem.append("items", "a")
        mem.append("items", "b")
        mem.append("items", "c")
        assert mem.get("items") == ["a", "b", "c"]

    def test_append_preserves_order(self) -> None:
        mem = WorkflowMemory()
        for i in range(5):
            mem.append("nums", i)
        assert mem.get("nums") == [0, 1, 2, 3, 4]

    def test_append_to_string_raises_type_error(self) -> None:
        mem = WorkflowMemory()
        mem.set("k", "string")
        with pytest.raises(TypeError, match="Cannot append to key 'k'"):
            mem.append("k", "x")

    def test_append_to_dict_raises_type_error(self) -> None:
        mem = WorkflowMemory()
        mem.set("k", {"a": 1})
        with pytest.raises(TypeError):
            mem.append("k", "x")

    def test_append_to_int_raises_type_error(self) -> None:
        mem = WorkflowMemory()
        mem.set("k", 42)
        with pytest.raises(TypeError):
            mem.append("k", "x")

    def test_error_message_includes_key_name(self) -> None:
        mem = WorkflowMemory()
        mem.set("my_key", "str")
        with pytest.raises(TypeError, match="my_key"):
            mem.append("my_key", "x")

    def test_error_message_includes_type_name(self) -> None:
        mem = WorkflowMemory()
        mem.set("k", "str_val")
        with pytest.raises(TypeError, match="str"):
            mem.append("k", "x")

    def test_append_mixed_types(self) -> None:
        mem = WorkflowMemory()
        mem.append("mixed", 1)
        mem.append("mixed", "two")
        mem.append("mixed", {"three": 3})
        assert len(mem.get("mixed")) == 3  # type: ignore[arg-type]


# ── WorkflowMemory: snapshot ───────────────────────────────────────────────────


class TestWorkflowMemorySnapshot:
    def test_empty_store_returns_empty_dict(self) -> None:
        assert WorkflowMemory().snapshot() == {}

    def test_snapshot_returns_dict(self) -> None:
        assert isinstance(WorkflowMemory().snapshot(), dict)

    def test_snapshot_contains_all_keys(self) -> None:
        mem = WorkflowMemory()
        mem.set("a", 1)
        mem.set("b", 2)
        snap = mem.snapshot()
        assert "a" in snap and "b" in snap

    def test_snapshot_is_deep_copy(self) -> None:
        mem = WorkflowMemory()
        mem.set("lst", [1, 2, 3])
        snap = mem.snapshot()
        snap["lst"].append(99)  # mutate copy
        assert mem.get("lst") == [1, 2, 3]  # original unchanged

    def test_snapshot_reflects_state_at_call_time(self) -> None:
        mem = WorkflowMemory()
        mem.set("x", 1)
        snap1 = mem.snapshot()
        mem.set("x", 2)
        snap2 = mem.snapshot()
        assert snap1["x"] == 1
        assert snap2["x"] == 2

    def test_two_snapshots_are_independent(self) -> None:
        mem = WorkflowMemory()
        mem.set("v", [10])
        a = mem.snapshot()
        b = mem.snapshot()
        a["v"].append(20)
        assert b["v"] == [10]

    def test_snapshot_includes_appended_lists(self) -> None:
        mem = WorkflowMemory()
        mem.append("r", "step1")
        mem.append("r", "step2")
        assert mem.snapshot()["r"] == ["step1", "step2"]


# ── PersistentMemory: unavailable path ────────────────────────────────────────


class TestPersistentMemoryUnavailable:
    def _make(self) -> PersistentMemory:
        with patch("httpx.get", side_effect=ConnectionRefusedError("server down")):
            return PersistentMemory(base_url="http://localhost:19999")

    def test_available_false(self) -> None:
        assert self._make()._available is False

    def test_client_is_none(self) -> None:
        assert self._make()._client is None

    def test_retain_no_raise(self) -> None:
        self._make().retain("bank", "content")  # must not raise

    def test_recall_returns_empty_list(self) -> None:
        assert self._make().recall("bank", "q") == []

    def test_reflect_returns_empty_string(self) -> None:
        assert self._make().reflect("bank", "q") == ""

    def test_warned_false_initially(self) -> None:
        assert self._make()._warned is False

    def test_warned_true_after_call(self, caplog: pytest.LogCaptureFixture) -> None:
        mem = self._make()
        with caplog.at_level(logging.WARNING, logger="ttadev.workflows.memory"):
            mem.retain("bank", "content")
        assert mem._warned is True

    def test_warning_message_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        mem = self._make()
        with caplog.at_level(logging.WARNING):
            mem.retain("bank", "content")
        assert any("Hindsight unavailable" in r.message for r in caplog.records)

    def test_warn_only_once(self) -> None:
        mem = self._make()
        mem.retain("bank", "content")
        assert mem._warned is True
        mem.retain("bank", "content2")  # second call — still True, not re-warned
        assert mem._warned is True

    def test_recall_no_raise(self) -> None:
        result = self._make().recall("bank", "query")
        assert isinstance(result, list)

    def test_reflect_no_raise(self) -> None:
        result = self._make().reflect("bank", "query")
        assert isinstance(result, str)


# ── PersistentMemory: available path ──────────────────────────────────────────


class TestPersistentMemoryAvailable:
    def _make(self) -> tuple[PersistentMemory, MagicMock]:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        with patch("httpx.get", return_value=mock_resp):
            with patch("ttadev.workflows.memory._HttpHindsightShim") as mock_shim:
                shim = MagicMock()
                mock_shim.return_value = shim
                mem = PersistentMemory(base_url="http://localhost:8888")
                return mem, shim

    def test_available_true(self) -> None:
        mem, _ = self._make()
        assert mem._available is True

    def test_retain_delegates_to_client(self) -> None:
        mem, shim = self._make()
        mem.retain("bank", "content")
        shim.retain.assert_called_once_with("bank", "content")

    def test_recall_delegates_to_client(self) -> None:
        mem, shim = self._make()
        shim.recall.return_value = ["m1", "m2"]
        result = mem.recall("bank", "query")
        shim.recall.assert_called_once_with("bank", "query")
        assert result == ["m1", "m2"]

    def test_reflect_delegates_to_client(self) -> None:
        mem, shim = self._make()
        shim.reflect.return_value = "synthesis"
        result = mem.reflect("bank", "q")
        shim.reflect.assert_called_once_with("bank", "q")
        assert result == "synthesis"

    def test_no_warning_logged(self, caplog: pytest.LogCaptureFixture) -> None:
        mem, _ = self._make()
        with caplog.at_level(logging.WARNING):
            mem.retain("bank", "content")
        assert not any("Hindsight unavailable" in r.message for r in caplog.records)


# ── _HttpHindsightShim ────────────────────────────────────────────────────────


class TestHttpHindsightShim:
    def test_trailing_slash_stripped(self) -> None:
        shim = _HttpHindsightShim(base_url="http://localhost:8888/")
        assert not shim._base_url.endswith("/")

    def test_retain_posts_to_api_memories(self) -> None:
        shim = _HttpHindsightShim(base_url="http://localhost:8888")
        with patch("httpx.post", return_value=MagicMock()) as mock_post:
            shim.retain("bank1", "content")
        url = mock_post.call_args[0][0]
        assert "/api/memories" in url

    def test_recall_posts_to_api_search(self) -> None:
        shim = _HttpHindsightShim(base_url="http://localhost:8888")
        resp = MagicMock()
        resp.json.return_value = {"results": [{"content": "found"}]}
        with patch("httpx.post", return_value=resp) as mock_post:
            result = shim.recall("bank1", "query")
        url = mock_post.call_args[0][0]
        assert "/api/search" in url
        assert result == ["found"]

    def test_recall_empty_results(self) -> None:
        shim = _HttpHindsightShim(base_url="http://localhost:8888")
        resp = MagicMock()
        resp.json.return_value = {"results": []}
        with patch("httpx.post", return_value=resp):
            assert shim.recall("bank", "q") == []

    def test_reflect_posts_to_api_reflect(self) -> None:
        shim = _HttpHindsightShim(base_url="http://localhost:8888")
        resp = MagicMock()
        resp.json.return_value = {"synthesis": "the answer"}
        with patch("httpx.post", return_value=resp) as mock_post:
            result = shim.reflect("bank", "question")
        url = mock_post.call_args[0][0]
        assert "/api/reflect" in url
        assert result == "the answer"
