"""Tests for WorkflowMemory (T4) and PersistentMemory (T5)."""

import logging

import pytest

from ttadev.workflows.memory import PersistentMemory, WorkflowMemory


class TestWorkflowMemory:
    def test_set_and_get(self):
        m = WorkflowMemory()
        m.set("key", "value")
        assert m.get("key") == "value"

    def test_get_missing_returns_default(self):
        m = WorkflowMemory()
        assert m.get("missing") is None
        assert m.get("missing", "fallback") == "fallback"

    def test_append_builds_list(self):
        m = WorkflowMemory()
        m.append("items", "a")
        m.append("items", "b")
        assert m.get("items") == ["a", "b"]

    def test_append_on_existing_non_list_raises(self):
        m = WorkflowMemory()
        m.set("x", "not-a-list")
        with pytest.raises(TypeError):
            m.append("x", "y")

    def test_snapshot_returns_copy(self):
        m = WorkflowMemory()
        m.set("k", [1, 2, 3])
        snap = m.snapshot()
        snap["k"].append(4)  # mutate the snapshot
        assert m.get("k") == [1, 2, 3]  # original unchanged

    def test_snapshot_is_dict(self):
        m = WorkflowMemory()
        m.set("a", 1)
        assert isinstance(m.snapshot(), dict)

    def test_overwrite_existing_key(self):
        m = WorkflowMemory()
        m.set("k", "first")
        m.set("k", "second")
        assert m.get("k") == "second"


class TestPersistentMemoryNoOp:
    """PersistentMemory must be a no-op when Hindsight is unavailable."""

    def test_retain_noop_when_unavailable(self):
        pm = PersistentMemory(base_url="http://localhost:9999")
        pm._available = False  # force unavailable
        pm.retain("tta.test", "some content")  # must not raise

    def test_recall_returns_empty_when_unavailable(self):
        pm = PersistentMemory(base_url="http://localhost:9999")
        pm._available = False
        result = pm.recall("tta.test", "query")
        assert result == []

    def test_reflect_returns_empty_string_when_unavailable(self):
        pm = PersistentMemory(base_url="http://localhost:9999")
        pm._available = False
        result = pm.reflect("tta.test", "query")
        assert result == ""

    def test_warning_logged_once(self, caplog):
        pm = PersistentMemory(base_url="http://localhost:not-real:1")
        pm._warned = False  # reset warn state
        pm._available = False
        with caplog.at_level(logging.WARNING):
            pm.retain("bank", "content")
        assert any(
            "unavailable" in r.message.lower() or "hindsight" in r.message.lower()
            for r in caplog.records
        )

    def test_retain_with_mock_shim(self, monkeypatch):
        retained = []

        class _FakeShim:
            def __init__(self, base_url: str) -> None:
                pass

            def retain(self, bank_id: str, content: str) -> None:
                retained.append((bank_id, content))

        import ttadev.workflows.memory as _mem

        monkeypatch.setattr(_mem, "_HttpHindsightShim", _FakeShim)
        pm = PersistentMemory(base_url="http://localhost:9999")
        pm._available = True
        pm.retain("tta.test", "hello")
        assert retained == [("tta.test", "hello")]

    def test_recall_with_mock_shim(self, monkeypatch):
        class _FakeShim:
            def __init__(self, base_url: str) -> None:
                pass

            def recall(self, bank_id: str, query: str) -> list[str]:
                return ["hit1", "hit2"]

        import ttadev.workflows.memory as _mem

        monkeypatch.setattr(_mem, "_HttpHindsightShim", _FakeShim)
        pm = PersistentMemory(base_url="http://localhost:9999")
        pm._available = True
        assert pm.recall("tta.test", "search") == ["hit1", "hit2"]

    def test_reflect_with_mock_shim(self, monkeypatch):
        class _FakeShim:
            def __init__(self, base_url: str) -> None:
                pass

            def reflect(self, bank_id: str, query: str) -> str:
                return "synthesized answer"

        import ttadev.workflows.memory as _mem

        monkeypatch.setattr(_mem, "_HttpHindsightShim", _FakeShim)
        pm = PersistentMemory(base_url="http://localhost:9999")
        pm._available = True
        assert pm.reflect("tta.test", "what happened?") == "synthesized answer"
