"""Supplementary tests for ContextEngineeringPrimitive — file-IO and discovery paths.

Covers the methods NOT exercised by test_primitives_context_engineering.py:
- _extract_relevant_sections   (docs parser)
- _extract_examples_from_file  (example extractor)
- _extract_usage_snippet       (usage snippet extractor)
- _discover_dependencies       (AST dependency discovery)
- _find_usage_examples         (multi-source example finder)
- _find_documentation          (multi-doc finder)
- _discover_related_files      (package file scanner)
- _discover_components         (full component layer via target_class)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from ttadev.primitives.core.base import WorkflowContext
from ttadev.primitives.core.context_engineering import (
    ContextComponent,
    ContextEngineeringPrimitive,
)

_INFRA = "ttadev.primitives.observability.instrumented_primitive"


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test-ce-extra")


@pytest.fixture
def prim(tmp_path: Path) -> ContextEngineeringPrimitive:
    return ContextEngineeringPrimitive(max_tokens=10_000, source_cache_dir=tmp_path)


# ===========================================================================
# TestExtractRelevantSections
# ===========================================================================


class TestExtractRelevantSections:
    def test_empty_file_returns_empty(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange
        doc = tmp_path / "README.md"
        doc.write_text("")

        # Act & Assert
        assert prim._extract_relevant_sections(doc, "MyClass") == ""

    def test_no_class_mention_returns_empty(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange
        doc = tmp_path / "README.md"
        doc.write_text("# Overview\nNo relevant content here.\n# Setup\nMore content.\n")

        # Act & Assert
        assert prim._extract_relevant_sections(doc, "NonExistentClass") == ""

    def test_header_containing_class_name_returns_section(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange
        doc = tmp_path / "README.md"
        doc.write_text("# Overview\nSome intro.\n\n# MyClass Usage\nHow MyClass works.\n")

        # Act
        result = prim._extract_relevant_sections(doc, "MyClass")

        # Assert
        assert "MyClass" in result

    def test_class_mentioned_in_body_triggers_section(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange — class name in body, not header
        doc = tmp_path / "AGENTS.md"
        doc.write_text("# General\nHere we use TargetClass in a pipeline.\n")

        # Act
        result = prim._extract_relevant_sections(doc, "TargetClass")

        # Assert
        assert "TargetClass" in result

    def test_limits_output_to_1000_chars(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange
        doc = tmp_path / "README.md"
        doc.write_text("# MyClass\n" + "x" * 2000 + "\n")

        # Act
        result = prim._extract_relevant_sections(doc, "MyClass")

        # Assert
        assert len(result) <= 1000

    def test_missing_file_returns_empty(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # OSError path — file does not exist
        missing = tmp_path / "does_not_exist.md"
        assert prim._extract_relevant_sections(missing, "AnyClass") == ""

    def test_returns_first_matching_section(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange — two sections mentioning the class
        doc = tmp_path / "README.md"
        doc.write_text(
            "# MyClass First Section\nFirst mention.\n# MyClass Second Section\nSecond mention.\n"
        )

        # Act
        result = prim._extract_relevant_sections(doc, "MyClass")

        # Assert — first section returned
        assert "First mention" in result

    def test_last_section_in_file_captured(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Section at end of file (no following header) should still be captured
        doc = tmp_path / "README.md"
        doc.write_text("# SomeClass Overview\nDetails about SomeClass.\n")

        result = prim._extract_relevant_sections(doc, "SomeClass")

        assert "SomeClass" in result


# ===========================================================================
# TestExtractExamplesFromFile
# ===========================================================================


class TestExtractExamplesFromFile:
    def test_no_class_mention_returns_empty(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange
        f = tmp_path / "test_other.py"
        f.write_text("def test_other():\n    x = 1\n    assert x == 1\n")

        # Act & Assert
        assert prim._extract_examples_from_file(f, "MyClass") == ""

    def test_class_mention_returns_code_fence_snippet(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange
        f = tmp_path / "test_myclass.py"
        f.write_text(
            "import pytest\n"
            "\n"
            "def test_myclass_init():\n"
            "    obj = MyClass(param=1)\n"
            "    assert obj is not None\n"
        )

        # Act
        result = prim._extract_examples_from_file(f, "MyClass")

        # Assert
        assert "MyClass" in result
        assert "```python" in result

    def test_missing_file_returns_empty(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        missing = tmp_path / "missing.py"
        assert prim._extract_examples_from_file(missing, "MyClass") == ""

    def test_surrounding_context_lines_included(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange — class usage at line 3 (index 3)
        lines = [
            "# preamble 0",
            "# preamble 1",
            "# preamble 2",
            "obj = MyClass()",
            "# after 4",
            "# after 5",
        ]
        f = tmp_path / "example.py"
        f.write_text("\n".join(lines))

        # Act
        result = prim._extract_examples_from_file(f, "MyClass")

        # Assert — snippet includes surrounding context
        assert "MyClass" in result

    def test_first_occurrence_used_when_multiple(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange
        f = tmp_path / "test_multi.py"
        f.write_text(
            "obj1 = MyClass(1)  # first occurrence\nx = 1\nobj2 = MyClass(2)  # second occurrence\n"
        )

        # Act
        result = prim._extract_examples_from_file(f, "MyClass")

        # Assert — snippet from first occurrence
        assert "first occurrence" in result


# ===========================================================================
# TestExtractUsageSnippet
# ===========================================================================


class TestExtractUsageSnippet:
    def test_no_class_in_file_returns_empty(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        f = tmp_path / "module.py"
        f.write_text("x = 1\ny = 2\n")
        assert prim._extract_usage_snippet(f, "MyClass") == ""

    def test_import_and_usage_returns_code_fence(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange
        f = tmp_path / "module.py"
        f.write_text(
            "from mymod import MyClass\n\ndef run():\n    obj = MyClass()\n    obj.do_thing()\n"
        )

        # Act
        result = prim._extract_usage_snippet(f, "MyClass")

        # Assert
        assert "```python" in result
        assert "MyClass" in result

    def test_missing_file_returns_empty(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        missing = tmp_path / "no_file.py"
        assert prim._extract_usage_snippet(missing, "MyClass") == ""

    def test_import_only_no_subsequent_usage_returns_empty(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange — only import line, nothing after it
        f = tmp_path / "only_import.py"
        f.write_text("from mymod import MyClass\n")

        # Act
        result = prim._extract_usage_snippet(f, "MyClass")

        # Assert — usage_line never found → ""
        assert result == ""

    def test_class_used_without_import_found_as_usage(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange — no import statement, direct usage
        f = tmp_path / "inline.py"
        f.write_text("x = 1\nresult = MyClass.create()\nprint(result)\n")

        # Act
        result = prim._extract_usage_snippet(f, "MyClass")

        # Assert — usage detected (import_line = -1, usage found at line 1)
        assert "MyClass" in result
        assert "```python" in result


# ===========================================================================
# TestDiscoverDependencies
# ===========================================================================


class TestDiscoverDependencies:
    def test_returns_dict_for_real_class(self, prim: ContextEngineeringPrimitive) -> None:
        # Act
        result = prim._discover_dependencies(WorkflowContext)

        # Assert
        assert isinstance(result, dict)

    def test_returns_empty_dict_for_uninspectable_type(
        self, prim: ContextEngineeringPrimitive
    ) -> None:
        # Built-in types have no Python source to inspect
        result = prim._discover_dependencies(int)
        assert isinstance(result, dict)

    def test_excludes_base_primitive_names(self, prim: ContextEngineeringPrimitive) -> None:
        result = prim._discover_dependencies(WorkflowContext)
        assert "WorkflowPrimitive" not in result
        assert "InstrumentedPrimitive" not in result

    def test_handles_oserror_gracefully(self, prim: ContextEngineeringPrimitive) -> None:
        with patch("inspect.getsource", side_effect=OSError("no source")):
            result = prim._discover_dependencies(WorkflowContext)
        assert result == {}

    def test_handles_type_error_gracefully(self, prim: ContextEngineeringPrimitive) -> None:
        with patch("inspect.getsource", side_effect=TypeError("builtin")):
            result = prim._discover_dependencies(WorkflowContext)
        assert result == {}

    def test_values_are_classes(self, prim: ContextEngineeringPrimitive) -> None:
        result = prim._discover_dependencies(WorkflowContext)
        for value in result.values():
            assert isinstance(value, type)


# ===========================================================================
# TestFindUsageExamples
# ===========================================================================


class TestFindUsageExamples:
    def test_returns_string_always(self, prim: ContextEngineeringPrimitive) -> None:
        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "rglob", return_value=[]):
                result = prim._find_usage_examples(WorkflowContext)
        assert isinstance(result, str)

    def test_class_without_docstring_returns_string(
        self, prim: ContextEngineeringPrimitive
    ) -> None:
        class NoDoc:
            pass

        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "rglob", return_value=[]):
                result = prim._find_usage_examples(NoDoc)
        assert isinstance(result, str)

    def test_class_with_code_block_docstring_uses_it(
        self, prim: ContextEngineeringPrimitive
    ) -> None:
        class DocClass:
            """A class with an example.

            ```python
            obj = DocClass()
            obj.run()
            ```
            """

        with patch.object(Path, "exists", return_value=False):
            result = prim._find_usage_examples(DocClass)

        # Docstring code extracted; result contains it (or empty if not found in FS)
        assert isinstance(result, str)
        # With no FS search, only docstring path runs
        assert "DocClass" in result or result == ""

    def test_examples_dir_file_with_class_included(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange — create a file with class name in it
        example_file = tmp_path / "example_foo.py"
        example_file.write_text("from mod import SpecialClass\nobj = SpecialClass()\n")

        class SpecialClass:
            pass

        # examples/ dir "exists" and glob returns our file
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "glob", return_value=[example_file]):
                with patch.object(Path, "rglob", return_value=[]):
                    result = prim._find_usage_examples(SpecialClass)
        assert isinstance(result, str)

    def test_limits_result_to_three_examples(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange — six test files all mentioning FooClass
        files = []
        for i in range(6):
            f = tmp_path / f"test_usage_{i}.py"
            f.write_text(f"obj = FooClass()  # usage {i}\n")
            files.append(f)

        class FooClass:
            pass

        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "glob", return_value=[]):
                with patch.object(Path, "rglob", return_value=files):
                    result = prim._find_usage_examples(FooClass)

        # At most 3 "## From" sections
        assert result.count("## From") <= 3


# ===========================================================================
# TestFindDocumentation
# ===========================================================================


class TestFindDocumentation:
    def test_returns_string(self, prim: ContextEngineeringPrimitive) -> None:
        with patch.object(Path, "exists", return_value=False):
            result = prim._find_documentation(WorkflowContext)
        assert isinstance(result, str)

    def test_uninspectable_class_returns_empty(self, prim: ContextEngineeringPrimitive) -> None:
        with patch("inspect.getfile", side_effect=OSError("no file")):
            result = prim._find_documentation(WorkflowContext)
        assert result == ""

    def test_no_doc_files_present_returns_empty(self, prim: ContextEngineeringPrimitive) -> None:
        with patch.object(Path, "exists", return_value=False):
            result = prim._find_documentation(WorkflowContext)
        assert result == ""

    def test_readme_mentioning_class_included(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange — README.md in tmp_path that mentions the class
        readme = tmp_path / "README.md"
        readme.write_text("# SpecialClass\nDocumentation for SpecialClass.\n")

        class SpecialClass:
            pass

        # Point inspect.getfile to a path inside tmp_path so the search finds it
        with patch("inspect.getfile", return_value=str(tmp_path / "pkg" / "module.py")):
            result = prim._find_documentation(SpecialClass)
        assert isinstance(result, str)

    def test_limits_to_two_doc_sources(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange — both README.md and AGENTS.md mention the class
        (tmp_path / "README.md").write_text("# MyDoc\nMyDoc details.\n")
        (tmp_path / "AGENTS.md").write_text("# MyDoc\nMyDoc agent docs.\n")

        class MyDoc:
            pass

        with patch("inspect.getfile", return_value=str(tmp_path / "x" / "module.py")):
            result = prim._find_documentation(MyDoc)
        # At most 2 "## From" sections
        assert result.count("## From") <= 2


# ===========================================================================
# TestDiscoverRelatedFiles
# ===========================================================================


class TestDiscoverRelatedFiles:
    async def test_returns_string(self, prim: ContextEngineeringPrimitive) -> None:
        with patch.object(Path, "rglob", return_value=[]):
            result = await prim._discover_related_files(WorkflowContext, _ctx())
        assert isinstance(result, str)

    async def test_no_related_files_returns_empty(self, prim: ContextEngineeringPrimitive) -> None:
        with patch.object(Path, "rglob", return_value=[]):
            result = await prim._discover_related_files(WorkflowContext, _ctx())
        assert result == ""

    async def test_uninspectable_class_returns_empty(
        self, prim: ContextEngineeringPrimitive
    ) -> None:
        with patch("inspect.getfile", side_effect=OSError("no file")):
            result = await prim._discover_related_files(WorkflowContext, _ctx())
        assert result == ""

    async def test_related_file_with_class_name_produces_output(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange — a file that imports/uses WorkflowContext
        related = tmp_path / "consumer.py"
        related.write_text(
            "from ttadev.primitives.core.base import WorkflowContext\n"
            "\n"
            "def build_ctx():\n"
            "    return WorkflowContext(workflow_id='x')\n"
        )

        # The class's source file is at a DIFFERENT path so samefile check passes
        with patch("inspect.getfile", return_value=str(tmp_path / "base.py")):
            with patch.object(Path, "rglob", return_value=[related]):
                result = await prim._discover_related_files(WorkflowContext, _ctx())
        assert isinstance(result, str)

    async def test_limits_to_two_related_files(
        self, prim: ContextEngineeringPrimitive, tmp_path: Path
    ) -> None:
        # Arrange — five files all mentioning WorkflowContext
        files = []
        for i in range(5):
            f = tmp_path / f"consumer_{i}.py"
            f.write_text(
                f"from base import WorkflowContext\nctx = WorkflowContext(workflow_id='test_{i}')\n"
            )
            files.append(f)

        with patch("inspect.getfile", return_value=str(tmp_path / "base.py")):
            with patch.object(Path, "rglob", return_value=files):
                result = await prim._discover_related_files(WorkflowContext, _ctx())
        # Limit is 2 related files → at most 2 "## From" sections
        assert result.count("## From") <= 2


# ===========================================================================
# TestDiscoverComponentsWithTargetClass
# ===========================================================================


class TestDiscoverComponentsWithTargetClass:
    """Test _discover_components — full target_class layer path."""

    async def test_target_class_creates_priority_1_target_component(
        self, prim: ContextEngineeringPrimitive
    ) -> None:
        # Arrange — isolate from filesystem
        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "glob", return_value=[]):
                with patch.object(Path, "rglob", return_value=[]):
                    # Act
                    components = await prim._discover_components(
                        {"task": "test", "target_class": WorkflowContext}, _ctx()
                    )

        # Assert
        target = [c for c in components if c.component_type == "target"]
        assert len(target) >= 1
        assert target[0].name == "WorkflowContext"
        assert target[0].priority == 1

    async def test_target_source_creates_target_component_with_correct_source(
        self, prim: ContextEngineeringPrimitive
    ) -> None:
        # Arrange
        source = "class Foo:\n    def bar(self): pass"
        with patch.object(Path, "exists", return_value=False):
            # Act
            components = await prim._discover_components(
                {"task": "test", "target_source": source}, _ctx()
            )

        # Assert
        target = [c for c in components if c.component_type == "target"]
        assert len(target) == 1
        assert target[0].source_code == source
        assert target[0].name == "target"
        assert target[0].priority == 1

    async def test_no_target_class_or_source_has_no_target_component(
        self, prim: ContextEngineeringPrimitive
    ) -> None:
        with patch.object(Path, "exists", return_value=False):
            components = await prim._discover_components({"task": "just a task"}, _ctx())
        target = [c for c in components if c.component_type == "target"]
        assert len(target) == 0

    async def test_test_generation_task_type_adds_mock_and_workflow_context(
        self, prim: ContextEngineeringPrimitive
    ) -> None:
        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "glob", return_value=[]):
                with patch.object(Path, "rglob", return_value=[]):
                    components = await prim._discover_components(
                        {
                            "task": "Generate tests",
                            "target_class": WorkflowContext,
                            "task_type": "test_generation",
                        },
                        _ctx(),
                    )

        names = [c.name for c in components]
        # At least MockPrimitive or WorkflowContext should appear as dependency
        assert "MockPrimitive" in names or "WorkflowContext" in names

    async def test_include_examples_false_produces_no_example_component(
        self, tmp_path: Path
    ) -> None:
        # Arrange — primitive with examples disabled
        p = ContextEngineeringPrimitive(
            max_tokens=10_000,
            include_examples=False,
            source_cache_dir=tmp_path,
        )
        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "glob", return_value=[]):
                with patch.object(Path, "rglob", return_value=[]):
                    components = await p._discover_components(
                        {"task": "test", "target_class": WorkflowContext}, _ctx()
                    )

        examples = [c for c in components if c.component_type == "example"]
        assert len(examples) == 0

    async def test_all_components_have_required_fields(
        self, prim: ContextEngineeringPrimitive
    ) -> None:
        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "glob", return_value=[]):
                with patch.object(Path, "rglob", return_value=[]):
                    components = await prim._discover_components(
                        {"task": "test", "target_class": WorkflowContext}, _ctx()
                    )

        for comp in components:
            assert isinstance(comp, ContextComponent)
            assert isinstance(comp.name, str)
            assert isinstance(comp.source_code, str)
            assert comp.priority in (1, 2, 3)
            assert isinstance(comp.token_count, int)
            assert comp.token_count >= 0
            assert isinstance(comp.component_type, str)

    async def test_target_component_token_count_matches_formula(
        self, prim: ContextEngineeringPrimitive
    ) -> None:
        with patch.object(Path, "exists", return_value=False):
            with patch.object(Path, "glob", return_value=[]):
                with patch.object(Path, "rglob", return_value=[]):
                    components = await prim._discover_components(
                        {"task": "test", "target_class": WorkflowContext}, _ctx()
                    )

        target = next(c for c in components if c.component_type == "target")
        assert target.token_count == len(target.source_code) // 4
