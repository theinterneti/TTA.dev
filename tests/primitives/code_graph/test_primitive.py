"""Unit tests for CodeGraphPrimitive — all FalkorDB calls mocked."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from ttadev.primitives.code_graph.client import FalkorDBClient
from ttadev.primitives.code_graph.types import CGCOp, CodeGraphQuery
from ttadev.primitives.core.base import WorkflowContext


def test_types_importable() -> None:
    from ttadev.primitives.code_graph.types import CGCOp

    assert CGCOp.find_code.value == "find_code"
    assert CGCOp.get_relationships.value == "get_relationships"
    assert CGCOp.get_complexity.value == "get_complexity"
    assert CGCOp.find_tests.value == "find_tests"
    assert CGCOp.raw_cypher.value == "raw_cypher"


def _mock_client(**overrides: object) -> AsyncMock:
    """Build a mock FalkorDBClient with safe defaults."""
    client = AsyncMock(spec=FalkorDBClient)
    client.is_reachable = MagicMock(return_value=True)  # sync method
    client.find_code = AsyncMock(return_value=[])
    client.get_callers = AsyncMock(return_value=[])
    client.get_callees = AsyncMock(return_value=[])
    client.get_complexity = AsyncMock(return_value=0.0)
    client.execute_cypher = AsyncMock(return_value=[])
    for k, v in overrides.items():
        setattr(client, k, v)
    return client


class TestCodeGraphPrimitiveValidation:
    @pytest.mark.asyncio
    async def test_empty_operations_returns_empty_report(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client()
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="foo", operations=[]),
            WorkflowContext(),
        )
        assert result["risk"] == "low"
        assert result["callers"] == []
        assert result["cgc_available"] is False  # no operations = no query
        client.get_callers.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_target_raises_value_error(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client()
        prim = CodeGraphPrimitive(cgc_client=client)
        with pytest.raises(ValueError, match="target is required"):
            await prim.execute(
                CodeGraphQuery(operations=[CGCOp.get_relationships]),
                WorkflowContext(),
            )

    @pytest.mark.asyncio
    async def test_raw_cypher_without_cypher_field_raises(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client()
        prim = CodeGraphPrimitive(cgc_client=client)
        with pytest.raises(ValueError, match="cypher query string is required"):
            await prim.execute(
                CodeGraphQuery(target="", operations=[CGCOp.raw_cypher]),
                WorkflowContext(),
            )


class TestCodeGraphPrimitiveOperations:
    @pytest.mark.asyncio
    async def test_get_relationships_populates_callers_and_deps(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            get_callers=AsyncMock(
                return_value=[{"name": "execute", "path": "/src/base.py", "line_number": 75}]
            ),
            get_callees=AsyncMock(
                return_value=[{"name": "_run_step", "path": "/src/orch.py", "line_number": 42}]
            ),
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="_execute_impl", operations=[CGCOp.get_relationships]),
            WorkflowContext(),
        )
        assert len(result["callers"]) == 1
        assert "execute" in result["callers"][0]
        assert len(result["dependencies"]) == 1
        assert result["cgc_available"] is True

    @pytest.mark.asyncio
    async def test_get_complexity_high_risk(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(get_complexity=AsyncMock(return_value=12.0))
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="complex_fn", operations=[CGCOp.get_complexity]),
            WorkflowContext(),
        )
        assert result["risk"] == "high"
        assert result["complexity"] == 12.0

    @pytest.mark.asyncio
    async def test_get_complexity_medium_risk_at_5(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(get_complexity=AsyncMock(return_value=5.0))
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="fn", operations=[CGCOp.get_complexity]),
            WorkflowContext(),
        )
        assert result["risk"] == "medium"

    @pytest.mark.asyncio
    async def test_risk_medium_when_five_or_more_callers(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            get_callers=AsyncMock(
                return_value=[
                    {"name": f"fn{i}", "path": "/src/f.py", "line_number": i} for i in range(5)
                ]
            ),
            get_callees=AsyncMock(return_value=[]),
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="popular_fn", operations=[CGCOp.get_relationships]),
            WorkflowContext(),
        )
        assert result["risk"] == "medium"

    @pytest.mark.asyncio
    async def test_find_tests_filters_to_test_paths(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            find_code=AsyncMock(
                return_value=[
                    {
                        "name": "RetryPrimitive",
                        "path": "/src/retry.py",
                        "line_number": 1,
                        "kind": "Class",
                    },
                    {
                        "name": "test_retry",
                        "path": "/tests/test_retry.py",
                        "line_number": 10,
                        "kind": "Function",
                    },
                ]
            ),
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="RetryPrimitive", operations=[CGCOp.find_tests]),
            WorkflowContext(),
        )
        assert result["related_tests"] == ["/tests/test_retry.py"]

    @pytest.mark.asyncio
    async def test_raw_cypher_populates_summary(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            execute_cypher=AsyncMock(return_value=[{"values": ["foo", "/bar.py"]}])
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(
                target="",
                operations=[CGCOp.raw_cypher],
                cypher="MATCH (f:Function) RETURN f.name, f.path LIMIT 1",
            ),
            WorkflowContext(),
        )
        assert result["cgc_available"] is True
        assert len(result["summary"]) > 0

    @pytest.mark.asyncio
    async def test_raw_cypher_empty_result_has_non_empty_summary(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            execute_cypher=AsyncMock(return_value=[])  # no rows returned
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(
                target="",
                operations=[CGCOp.raw_cypher],
                cypher="MATCH (f:Function) RETURN f.name LIMIT 0",
            ),
            WorkflowContext(),
        )
        assert result["cgc_available"] is True
        assert len(result["summary"]) > 0
        assert result["summary"] == "Cypher query returned no results."

    @pytest.mark.asyncio
    async def test_multiple_ops_in_one_call(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            get_complexity=AsyncMock(return_value=7.0),
            get_callers=AsyncMock(return_value=[]),
            get_callees=AsyncMock(return_value=[]),
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(
                target="fn",
                operations=[CGCOp.get_relationships, CGCOp.get_complexity],
            ),
            WorkflowContext(),
        )
        assert result["complexity"] == 7.0
        assert result["risk"] == "medium"
        client.get_callers.assert_called_once()
        client.get_complexity.assert_called_once()

    @pytest.mark.asyncio
    async def test_otel_span_emitted_with_correct_attributes(self) -> None:
        from unittest.mock import MagicMock

        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            get_callers=AsyncMock(return_value=[]),
            get_callees=AsyncMock(return_value=[]),
        )
        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

        prim = CodeGraphPrimitive(cgc_client=client)
        prim._tracer = None  # disable base-class span to avoid mock format() issues
        prim._cgc_tracer = mock_tracer  # type: ignore[assignment]

        await prim.execute(
            CodeGraphQuery(target="my_fn", operations=[CGCOp.get_relationships]),
            WorkflowContext(),
        )

        mock_tracer.start_as_current_span.assert_called_once_with("cgc.orient")
        set_attr_calls = {
            call.args[0]: call.args[1] for call in mock_span.set_attribute.call_args_list
        }
        assert set_attr_calls["target"] == "my_fn"
        assert set_attr_calls["operations"] == ["get_relationships"]
        assert set_attr_calls["risk"] in ("low", "medium", "high")
        assert set_attr_calls["cgc_available"] is True

    @pytest.mark.asyncio
    async def test_otel_span_emitted_when_cgc_unavailable(self) -> None:
        from unittest.mock import MagicMock

        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client()
        client.is_reachable = MagicMock(return_value=False)

        mock_span = MagicMock()
        mock_tracer = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(return_value=mock_span)
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(return_value=False)

        prim = CodeGraphPrimitive(cgc_client=client)
        prim._tracer = None
        prim._cgc_tracer = mock_tracer  # type: ignore[assignment]

        await prim.execute(
            CodeGraphQuery(target="my_fn", operations=[CGCOp.get_relationships]),
            WorkflowContext(),
        )

        mock_tracer.start_as_current_span.assert_called_once_with("cgc.orient")
        set_attr_calls = {
            call.args[0]: call.args[1] for call in mock_span.set_attribute.call_args_list
        }
        assert set_attr_calls["target"] == "my_fn"
        assert set_attr_calls["cgc_available"] is False


class TestCodeGraphPrimitiveDegradation:
    @pytest.mark.asyncio
    async def test_cgc_unreachable_returns_graceful_report(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client()
        client.is_reachable = MagicMock(return_value=False)
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="foo", operations=[CGCOp.get_relationships]),
            WorkflowContext(),
        )
        assert result["cgc_available"] is False
        assert result["risk"] == "low"
        assert "unavailable" in result["summary"].lower()
        client.get_callers.assert_not_called()

    @pytest.mark.asyncio
    async def test_cgc_exception_returns_graceful_report(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            get_callers=AsyncMock(side_effect=Exception("connection lost")),
            get_callees=AsyncMock(return_value=[]),
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        result = await prim.execute(
            CodeGraphQuery(target="foo", operations=[CGCOp.get_relationships]),
            WorkflowContext(),
        )
        assert result["cgc_available"] is False

    @pytest.mark.asyncio
    async def test_depth_over_5_is_clamped_not_raised(self) -> None:
        from ttadev.primitives.code_graph.primitive import CodeGraphPrimitive

        client = _mock_client(
            get_callers=AsyncMock(return_value=[]),
            get_callees=AsyncMock(return_value=[]),
        )
        prim = CodeGraphPrimitive(cgc_client=client)
        # Should not raise, should succeed
        result = await prim.execute(
            CodeGraphQuery(target="fn", operations=[CGCOp.get_relationships], depth=99),
            WorkflowContext(),
        )
        assert "risk" in result


def test_codegraphprimitive_exported_from_primitives_package() -> None:
    from ttadev.primitives import CodeGraphPrimitive

    assert CodeGraphPrimitive is not None
