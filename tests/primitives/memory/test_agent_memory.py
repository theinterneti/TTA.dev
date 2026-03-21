"""Unit tests for AgentMemory — all HTTP calls mocked."""


def test_types_importable() -> None:
    from ttadev.primitives.memory.types import MemoryResult, RetainResult

    # MemoryResult fields
    r: MemoryResult = {"id": "abc", "text": "some memory", "type": "experience"}
    assert r["id"] == "abc"

    # RetainResult fields
    res: RetainResult = {"success": True, "operation_id": "op-123"}
    assert res["success"] is True
