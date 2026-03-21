"""Unit tests for CodeGraphPrimitive."""


def test_types_importable() -> None:
    from ttadev.primitives.code_graph.types import CGCOp

    assert CGCOp.find_code.value == "find_code"
    assert CGCOp.get_relationships.value == "get_relationships"
    assert CGCOp.get_complexity.value == "get_complexity"
    assert CGCOp.find_tests.value == "find_tests"
    assert CGCOp.raw_cypher.value == "raw_cypher"
