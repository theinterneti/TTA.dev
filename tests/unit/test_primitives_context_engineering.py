"""Tests for ContextEngineeringPrimitive.

Covers (72 test cases across 11 classes):
- ContextComponent dataclass creation and field validation
- ContextBundle dataclass creation and default factory isolation
- ContextEngineeringPrimitive.__init__ — all constructor arguments
- _count_tokens — pure formula len(text) // 4
- _extract_code_from_docstring — markdown fence parsing
- _extract_source_code — inspect.getsource + fallback on OSError/TypeError
- _compress_components — priority-based budget enforcement
- _structure_context — section generation per component type
- _validate_quality — quality scoring and diagnostics
- execute() — full pipeline with mocked I/O and infrastructure
- Compression edge cases with near-zero token budgets
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.core.context_engineering import (
    ContextBundle,
    ContextComponent,
    ContextEngineeringPrimitive,
    ContextRequest,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_INFRA = "ttadev.primitives.observability.instrumented_primitive"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx() -> WorkflowContext:
    """Return a minimal WorkflowContext for test isolation."""
    return WorkflowContext(workflow_id="test-wf")


def _mock_collector() -> MagicMock:
    """Return a MagicMock satisfying EnhancedMetricsCollector's interface."""
    col: MagicMock = MagicMock()
    col.start_request = MagicMock()
    col.record_execution = MagicMock()
    col.end_request = MagicMock()
    return col


@contextmanager
def _exec_patches():  # type: ignore[return]
    """
    Patch InstrumentedPrimitive infrastructure and filesystem for execute() calls.

    Disables:
    - Real OpenTelemetry spans (TRACING_AVAILABLE=False)
    - Real EnhancedMetricsCollector (replaced with MagicMock)
    - inject_trace_context (returns context unchanged)
    - Path.glob / rglob / exists (return empty / False — no real FS scanning)

    Yields the mock_collector so callers can assert on it if needed.
    """
    mock_col = _mock_collector()
    with patch(f"{_INFRA}.get_enhanced_metrics_collector", return_value=mock_col):
        with patch(f"{_INFRA}.inject_trace_context", side_effect=lambda ctx: ctx):
            with patch(f"{_INFRA}.TRACING_AVAILABLE", False):
                with patch.object(Path, "glob", return_value=[]):
                    with patch.object(Path, "rglob", return_value=[]):
                        with patch.object(Path, "exists", return_value=False):
                            yield mock_col


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def primitive(tmp_path: Path) -> ContextEngineeringPrimitive:
    """ContextEngineeringPrimitive with tmp_path cache dir and max_tokens=10_000."""
    return ContextEngineeringPrimitive(max_tokens=10_000, source_cache_dir=tmp_path)


@pytest.fixture
def primitive_no_validate(tmp_path: Path) -> ContextEngineeringPrimitive:
    """Primitive with quality validation disabled."""
    return ContextEngineeringPrimitive(
        max_tokens=10_000,
        validate_quality=False,
        source_cache_dir=tmp_path,
    )


@pytest.fixture
def primitive_no_examples(tmp_path: Path) -> ContextEngineeringPrimitive:
    """Primitive with usage-example discovery disabled."""
    return ContextEngineeringPrimitive(
        max_tokens=10_000,
        include_examples=False,
        source_cache_dir=tmp_path,
    )


# ===========================================================================
# TestContextComponent
# ===========================================================================


class TestContextComponent:
    def test_creation_stores_all_fields(self) -> None:
        comp = ContextComponent(
            name="MyClass",
            source_code="class MyClass: pass",
            priority=1,
            token_count=5,
            component_type="target",
        )
        assert comp.name == "MyClass"
        assert comp.source_code == "class MyClass: pass"
        assert comp.priority == 1
        assert comp.token_count == 5
        assert comp.component_type == "target"

    def test_all_priority_levels_accepted(self) -> None:
        for p in (1, 2, 3):
            comp = ContextComponent(
                name="x", source_code="x", priority=p, token_count=1, component_type="target"
            )
            assert comp.priority == p

    def test_all_documented_component_types(self) -> None:
        for ct in (
            "target",
            "dependency",
            "example",
            "documentation",
            "related",
            "constraint",
        ):
            comp = ContextComponent(
                name="x", source_code="x", priority=1, token_count=1, component_type=ct
            )
            assert comp.component_type == ct

    def test_is_dataclass(self) -> None:
        from dataclasses import is_dataclass

        assert is_dataclass(ContextComponent)


# ===========================================================================
# TestContextBundle
# ===========================================================================


class TestContextBundle:
    def test_minimal_creation_with_defaults(self) -> None:
        bundle = ContextBundle(content="hello", token_count=5, quality_score=0.9)
        assert bundle.content == "hello"
        assert bundle.token_count == 5
        assert bundle.quality_score == 0.9
        assert bundle.components == []
        assert bundle.missing_components == []
        assert bundle.recommendations == []

    def test_full_creation_stores_all_fields(self) -> None:
        comp = ContextComponent(
            name="x", source_code="x", priority=1, token_count=1, component_type="target"
        )
        bundle = ContextBundle(
            content="ctx",
            token_count=100,
            quality_score=0.75,
            components=[comp],
            missing_components=["MockPrimitive"],
            recommendations=["Add examples"],
        )
        assert len(bundle.components) == 1
        assert bundle.missing_components == ["MockPrimitive"]
        assert bundle.recommendations == ["Add examples"]

    def test_is_dataclass(self) -> None:
        from dataclasses import is_dataclass

        assert is_dataclass(ContextBundle)

    def test_default_factory_list_isolation(self) -> None:
        """Each ContextBundle gets its own independent list instances."""
        b1 = ContextBundle(content="a", token_count=1, quality_score=1.0)
        b2 = ContextBundle(content="b", token_count=2, quality_score=0.5)
        b1.components.append(
            ContextComponent(
                name="c", source_code="c", priority=1, token_count=1, component_type="target"
            )
        )
        assert b2.components == []
        assert b1.missing_components is not b2.missing_components
        assert b1.recommendations is not b2.recommendations


# ===========================================================================
# TestContextEngineeringPrimitiveInit
# ===========================================================================


class TestContextEngineeringPrimitiveInit:
    def test_default_max_tokens(self, tmp_path: Path) -> None:
        p = ContextEngineeringPrimitive(source_cache_dir=tmp_path)
        assert p.max_tokens == 100_000

    def test_default_compression_strategy(self, tmp_path: Path) -> None:
        p = ContextEngineeringPrimitive(source_cache_dir=tmp_path)
        assert p.compression_strategy == "priority"

    def test_default_include_examples(self, tmp_path: Path) -> None:
        p = ContextEngineeringPrimitive(source_cache_dir=tmp_path)
        assert p.include_examples is True

    def test_default_validate_quality(self, tmp_path: Path) -> None:
        p = ContextEngineeringPrimitive(source_cache_dir=tmp_path)
        assert p.validate_quality is True

    def test_custom_max_tokens(self, tmp_path: Path) -> None:
        p = ContextEngineeringPrimitive(max_tokens=25_000, source_cache_dir=tmp_path)
        assert p.max_tokens == 25_000

    def test_custom_compression_strategy(self, tmp_path: Path) -> None:
        p = ContextEngineeringPrimitive(compression_strategy="semantic", source_cache_dir=tmp_path)
        assert p.compression_strategy == "semantic"

    def test_include_examples_false(self, tmp_path: Path) -> None:
        p = ContextEngineeringPrimitive(include_examples=False, source_cache_dir=tmp_path)
        assert p.include_examples is False

    def test_validate_quality_false(self, tmp_path: Path) -> None:
        p = ContextEngineeringPrimitive(validate_quality=False, source_cache_dir=tmp_path)
        assert p.validate_quality is False

    def test_explicit_source_cache_dir(self, tmp_path: Path) -> None:
        p = ContextEngineeringPrimitive(source_cache_dir=tmp_path)
        assert p.source_cache_dir == tmp_path

    def test_default_cache_dir_is_created(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        p = ContextEngineeringPrimitive()
        assert p.source_cache_dir.exists()

    def test_primitive_name_attribute(self, tmp_path: Path) -> None:
        p = ContextEngineeringPrimitive(source_cache_dir=tmp_path)
        assert p.name == "ContextEngineeringPrimitive"

    def test_is_instrumented_primitive_subclass(self, tmp_path: Path) -> None:
        from ttadev.primitives.observability.instrumented_primitive import InstrumentedPrimitive

        p = ContextEngineeringPrimitive(source_cache_dir=tmp_path)
        assert isinstance(p, InstrumentedPrimitive)


# ===========================================================================
# TestTokenCounting
# ===========================================================================


class TestTokenCounting:
    def test_empty_string_zero_tokens(self, primitive: ContextEngineeringPrimitive) -> None:
        assert primitive._count_tokens("") == 0

    def test_three_chars_rounds_to_zero(self, primitive: ContextEngineeringPrimitive) -> None:
        assert primitive._count_tokens("abc") == 0

    def test_four_chars_equals_one_token(self, primitive: ContextEngineeringPrimitive) -> None:
        assert primitive._count_tokens("abcd") == 1

    def test_eight_chars_equals_two_tokens(self, primitive: ContextEngineeringPrimitive) -> None:
        assert primitive._count_tokens("abcdefgh") == 2

    def test_five_chars_truncates_to_one(self, primitive: ContextEngineeringPrimitive) -> None:
        # 5 // 4 == 1
        assert primitive._count_tokens("abcde") == 1

    def test_large_string(self, primitive: ContextEngineeringPrimitive) -> None:
        assert primitive._count_tokens("x" * 400) == 100

    def test_matches_formula_for_various_lengths(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        for length in (0, 1, 3, 4, 7, 8, 16, 100, 1000):
            assert primitive._count_tokens("a" * length) == length // 4


# ===========================================================================
# TestExtractCodeFromDocstring
# ===========================================================================


class TestExtractCodeFromDocstring:
    def test_empty_docstring_returns_empty(self, primitive: ContextEngineeringPrimitive) -> None:
        assert primitive._extract_code_from_docstring("") == ""

    def test_plain_text_no_fences_returns_empty(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        assert primitive._extract_code_from_docstring("No code here just text.") == ""

    def test_single_python_fence(self, primitive: ContextEngineeringPrimitive) -> None:
        docstring = "Usage:\n```python\nx = 1\nprint(x)\n```"
        result = primitive._extract_code_from_docstring(docstring)
        assert "x = 1" in result
        assert "print(x)" in result

    def test_multiple_code_blocks_both_included(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        docstring = "Ex1:\n```python\na = 1\n```\nEx2:\n```python\nb = 2\n```"
        result = primitive._extract_code_from_docstring(docstring)
        assert "a = 1" in result
        assert "b = 2" in result

    def test_bare_code_fence_without_language_tag(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        docstring = "```\nsome_code()\n```"
        result = primitive._extract_code_from_docstring(docstring)
        assert "some_code()" in result


# ===========================================================================
# TestExtractSourceCode
# ===========================================================================


class TestExtractSourceCode:
    def test_real_file_backed_class_returns_non_empty_string(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        # WorkflowContext lives in a real .py file — getsource should succeed
        result = primitive._extract_source_code(WorkflowContext)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_fallback_on_os_error_contains_class_name(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        class LocalClass:
            __name__ = "LocalClass"

        with patch("inspect.getsource", side_effect=OSError("no source")):
            result = primitive._extract_source_code(LocalClass)  # type: ignore[arg-type]
        assert "LocalClass" in result
        assert "..." in result

    def test_fallback_on_type_error_contains_class_name(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        class LocalClass:
            __name__ = "LocalClass"

        with patch("inspect.getsource", side_effect=TypeError("builtin type")):
            result = primitive._extract_source_code(LocalClass)  # type: ignore[arg-type]
        assert "LocalClass" in result
        assert "..." in result


# ===========================================================================
# TestCompressComponents
# ===========================================================================


class TestCompressComponents:
    async def test_empty_input_returns_empty(self, primitive: ContextEngineeringPrimitive) -> None:
        result = await primitive._compress_components([], 1000, _ctx())
        assert result == []

    async def test_all_fit_within_budget(self, primitive: ContextEngineeringPrimitive) -> None:
        components = [
            ContextComponent(
                name="a",
                source_code="a" * 100,
                priority=1,
                token_count=25,
                component_type="target",
            ),
            ContextComponent(
                name="b",
                source_code="b" * 100,
                priority=2,
                token_count=25,
                component_type="dependency",
            ),
        ]
        result = await primitive._compress_components(components, 100, _ctx())
        assert len(result) == 2

    async def test_optional_component_dropped_over_budget(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        components = [
            ContextComponent(
                name="critical",
                source_code="x",
                priority=1,
                token_count=50,
                component_type="target",
            ),
            ContextComponent(
                name="optional",
                source_code="y" * 1000,
                priority=3,
                token_count=250,
                component_type="example",
            ),
        ]
        result = await primitive._compress_components(components, 100, _ctx())
        names = [c.name for c in result]
        assert "critical" in names
        assert "optional" not in names

    async def test_priority_1_always_included_even_over_budget(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        """Critical components (priority=1) are forced in even if they exceed the budget."""
        components = [
            ContextComponent(
                name="must_have",
                source_code="x" * 1000,
                priority=1,
                token_count=500,
                component_type="target",
            ),
        ]
        result = await primitive._compress_components(components, 10, _ctx())
        assert len(result) == 1
        assert result[0].name == "must_have"

    async def test_output_ordered_by_priority_ascending(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        components = [
            ContextComponent(
                name="opt",
                source_code="o",
                priority=3,
                token_count=1,
                component_type="example",
            ),
            ContextComponent(
                name="imp",
                source_code="i",
                priority=2,
                token_count=1,
                component_type="dependency",
            ),
            ContextComponent(
                name="crit",
                source_code="c",
                priority=1,
                token_count=1,
                component_type="target",
            ),
        ]
        result = await primitive._compress_components(components, 1000, _ctx())
        assert [c.priority for c in result] == sorted(c.priority for c in result)

    async def test_exactly_at_budget_both_included(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        components = [
            ContextComponent(
                name="a",
                source_code="x",
                priority=1,
                token_count=50,
                component_type="target",
            ),
            ContextComponent(
                name="b",
                source_code="y",
                priority=2,
                token_count=50,
                component_type="dependency",
            ),
        ]
        result = await primitive._compress_components(components, 100, _ctx())
        assert len(result) == 2


# ===========================================================================
# TestStructureContext
# ===========================================================================


class TestStructureContext:
    async def test_task_section_appears_with_task_key(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        request: ContextRequest = {"task": "Write tests for MyClass"}
        result = await primitive._structure_context([], request, _ctx())
        assert "# TASK" in result
        assert "Write tests for MyClass" in result

    async def test_constraints_section_always_present(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        result = await primitive._structure_context([], {"task": "x"}, _ctx())
        assert "# CONSTRAINTS" in result

    async def test_target_api_section_for_target_component(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        components = [
            ContextComponent(
                name="MyClass",
                source_code="class MyClass: pass",
                priority=1,
                token_count=5,
                component_type="target",
            ),
        ]
        result = await primitive._structure_context(components, {"task": "t"}, _ctx())
        assert "# TARGET API" in result
        assert "class MyClass: pass" in result

    async def test_dependencies_section_for_dependency_component(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        components = [
            ContextComponent(
                name="WorkflowContext",
                source_code="class WC: pass",
                priority=2,
                token_count=4,
                component_type="dependency",
            ),
        ]
        result = await primitive._structure_context(components, {"task": "t"}, _ctx())
        assert "# DEPENDENCIES" in result
        assert "WorkflowContext" in result

    async def test_usage_examples_section_for_example_component(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        components = [
            ContextComponent(
                name="usage_examples",
                source_code="example code here",
                priority=3,
                token_count=4,
                component_type="example",
            ),
        ]
        result = await primitive._structure_context(components, {"task": "t"}, _ctx())
        assert "# USAGE EXAMPLES" in result
        assert "example code here" in result

    async def test_documentation_section_for_documentation_component(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        components = [
            ContextComponent(
                name="docs",
                source_code="# Docs here",
                priority=3,
                token_count=3,
                component_type="documentation",
            ),
        ]
        result = await primitive._structure_context(components, {"task": "t"}, _ctx())
        assert "# DOCUMENTATION" in result

    async def test_related_files_section_for_related_component(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        components = [
            ContextComponent(
                name="related_files",
                source_code="related usage",
                priority=3,
                token_count=3,
                component_type="related",
            ),
        ]
        result = await primitive._structure_context(components, {"task": "t"}, _ctx())
        assert "# RELATED FILES" in result

    async def test_missing_task_key_omits_task_section(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        result = await primitive._structure_context([], {}, _ctx())
        assert "# TASK" not in result

    async def test_result_is_a_string(self, primitive: ContextEngineeringPrimitive) -> None:
        result = await primitive._structure_context([], {"task": "x"}, _ctx())
        assert isinstance(result, str)


# ===========================================================================
# TestValidateQuality
# ===========================================================================


class TestValidateQuality:
    async def test_returns_three_tuple(self, primitive: ContextEngineeringPrimitive) -> None:
        result = await primitive._validate_quality("# CONSTRAINTS", {"task": "t"}, _ctx())
        assert len(result) == 3
        score, missing, recs = result
        assert isinstance(score, float)
        assert isinstance(missing, list)
        assert isinstance(recs, list)

    async def test_quality_score_range(self, primitive: ContextEngineeringPrimitive) -> None:
        score, _, _ = await primitive._validate_quality("# CONSTRAINTS", {"task": "t"}, _ctx())
        assert 0.0 <= score <= 1.0

    async def test_missing_target_api_appears_in_missing(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        _score, missing, recs = await primitive._validate_quality(
            "# CONSTRAINTS\nsome text", {"task": "t"}, _ctx()
        )
        assert "target API" in missing
        assert any("target" in r.lower() for r in recs)

    async def test_over_token_budget_adds_recommendation(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        # max_tokens=10_000 → need >40_000 chars to trigger
        big = "# CONSTRAINTS\n" + "x" * 50_000
        _score, _missing, recs = await primitive._validate_quality(big, {"task": "t"}, _ctx())
        assert any("budget" in r.lower() or "exceeds" in r.lower() for r in recs)

    async def test_test_generation_detects_missing_mock_primitive(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        content = "# CONSTRAINTS\n# TARGET API\nWorkflowContext"
        _score, missing, _recs = await primitive._validate_quality(
            content, {"task": "t", "task_type": "test_generation"}, _ctx()
        )
        assert "MockPrimitive" in missing

    async def test_test_generation_detects_missing_workflow_context(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        content = "# CONSTRAINTS\n# TARGET API\nMockPrimitive"
        _score, missing, _recs = await primitive._validate_quality(
            content, {"task": "t", "task_type": "test_generation"}, _ctx()
        )
        assert "WorkflowContext" in missing

    async def test_fully_populated_context_high_score(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        content = "\n".join(  # noqa: FLY002
            [
                "# TARGET API (USE EXACTLY AS SHOWN)",
                "# DEPENDENCIES (USE EXACTLY AS SHOWN)",
                "MockPrimitive",
                "WorkflowContext",
                "# USAGE EXAMPLES",
                "# DOCUMENTATION",
                "# RELATED FILES (Real-World Usage)",
                "# CONSTRAINTS",
            ]
        )
        score, _missing, _recs = await primitive._validate_quality(
            content, {"task": "t", "task_type": "test_generation"}, _ctx()
        )
        assert score > 0.5


# ===========================================================================
# TestContextEngineeringPrimitiveExecute
# ===========================================================================


class TestContextEngineeringPrimitiveExecute:
    """Full pipeline integration tests through execute() with mocked infrastructure."""

    async def test_returns_context_bundle_instance(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        with _exec_patches():
            result = await primitive.execute({"task": "Write unit tests"}, _ctx())
        assert isinstance(result, ContextBundle)

    async def test_content_is_nonempty_string(self, primitive: ContextEngineeringPrimitive) -> None:
        with _exec_patches():
            result = await primitive.execute({"task": "Summarize a document"}, _ctx())
        assert isinstance(result.content, str)
        assert len(result.content) > 0

    async def test_task_string_appears_in_content(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        task = "Implement a retry mechanism with exponential back-off"
        with _exec_patches():
            result = await primitive.execute({"task": task}, _ctx())
        assert task in result.content

    async def test_constraints_always_in_content(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        with _exec_patches():
            result = await primitive.execute({"task": "test"}, _ctx())
        assert "# CONSTRAINTS" in result.content

    async def test_target_source_reflected_in_content(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        source = "class Adder:\n    def add(self, a, b):\n        return a + b"
        with _exec_patches():
            result = await primitive.execute(
                {"task": "Test Adder", "target_source": source}, _ctx()
            )
        assert source in result.content

    async def test_target_source_triggers_target_api_section(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        with _exec_patches():
            result = await primitive.execute(
                {"task": "test it", "target_source": "def my_func(): pass"}, _ctx()
            )
        assert "# TARGET API" in result.content

    async def test_target_source_component_appears_in_components_list(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        with _exec_patches():
            result = await primitive.execute(
                {"task": "test", "target_source": "class Foo: pass"}, _ctx()
            )
        assert any(c.component_type == "target" for c in result.components)

    async def test_target_class_produces_target_api_section(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        with patch("inspect.getsource", return_value="class FakeClass:\n    pass"):
            with _exec_patches():
                result = await primitive.execute(
                    {"task": "Test FakeClass", "target_class": WorkflowContext}, _ctx()
                )
        assert isinstance(result, ContextBundle)
        assert "# TARGET API" in result.content

    async def test_quality_score_in_valid_range(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        with _exec_patches():
            result = await primitive.execute({"task": "Do something"}, _ctx())
        assert 0.0 <= result.quality_score <= 1.0

    async def test_token_count_equals_formula_on_content(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        with _exec_patches():
            result = await primitive.execute({"task": "Count tokens"}, _ctx())
        assert result.token_count == len(result.content) // 4

    async def test_validate_quality_false_gives_perfect_score(
        self, primitive_no_validate: ContextEngineeringPrimitive
    ) -> None:
        with _exec_patches():
            result = await primitive_no_validate.execute({"task": "no check"}, _ctx())
        assert result.quality_score == 1.0
        assert result.missing_components == []
        assert result.recommendations == []

    async def test_missing_and_recommendations_are_lists(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        with _exec_patches():
            result = await primitive.execute({"task": "test"}, _ctx())
        assert isinstance(result.missing_components, list)
        assert isinstance(result.recommendations, list)

    async def test_test_generation_task_type_succeeds(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        with _exec_patches():
            result = await primitive.execute(
                {"task": "Generate pytest tests", "task_type": "test_generation"}, _ctx()
            )
        assert isinstance(result, ContextBundle)

    async def test_per_request_max_tokens_override(self, tmp_path: Path) -> None:
        """max_tokens in the request dict overrides the instance default."""
        prim = ContextEngineeringPrimitive(max_tokens=50_000, source_cache_dir=tmp_path)
        with _exec_patches():
            result = await prim.execute({"task": "test", "max_tokens": 100}, _ctx())
        assert isinstance(result, ContextBundle)

    async def test_empty_task_string_still_returns_bundle(
        self, primitive: ContextEngineeringPrimitive
    ) -> None:
        with _exec_patches():
            result = await primitive.execute({"task": ""}, _ctx())
        assert isinstance(result, ContextBundle)


# ===========================================================================
# TestCompressionLowBudget
# ===========================================================================


class TestCompressionLowBudget:
    async def test_tiny_budget_drops_optional_components(self, tmp_path: Path) -> None:
        prim = ContextEngineeringPrimitive(max_tokens=1, source_cache_dir=tmp_path)
        components = [
            ContextComponent(
                name="must",
                source_code="class Must: pass",
                priority=1,
                token_count=4,
                component_type="target",
            ),
            ContextComponent(
                name="optional",
                source_code="class Optional: pass",
                priority=3,
                token_count=5,
                component_type="example",
            ),
        ]
        result = await prim._compress_components(components, 1, _ctx())
        names = [c.name for c in result]
        assert "must" in names
        assert "optional" not in names

    async def test_zero_budget_priority_1_still_forced_in(self, tmp_path: Path) -> None:
        prim = ContextEngineeringPrimitive(max_tokens=0, source_cache_dir=tmp_path)
        components = [
            ContextComponent(
                name="must",
                source_code="class Must: pass",
                priority=1,
                token_count=4,
                component_type="target",
            ),
            ContextComponent(
                name="skip",
                source_code="class Skip: pass",
                priority=2,
                token_count=4,
                component_type="dependency",
            ),
        ]
        result = await prim._compress_components(components, 0, _ctx())
        names = [c.name for c in result]
        assert "must" in names
        assert "skip" not in names

    async def test_low_budget_full_execute_does_not_crash(self, tmp_path: Path) -> None:
        prim = ContextEngineeringPrimitive(max_tokens=5, source_cache_dir=tmp_path)
        with _exec_patches():
            result = await prim.execute({"task": "t", "target_source": "def f(): pass"}, _ctx())
        assert isinstance(result, ContextBundle)
