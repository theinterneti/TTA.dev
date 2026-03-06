"""Tests for python_pathway workflow primitives."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from tta_dev_primitives import WorkflowContext

from python_pathway.models import AnalysisResult, PatternMatch
from python_pathway.primitives import (
    CodeAnalysisPrimitive,
    DependencyAnalysisPrimitive,
    PatternDetectionPrimitive,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx() -> WorkflowContext:
    return WorkflowContext(workflow_id="test-primitives")


_SIMPLE_SOURCE = (
    "import os\n"
    "\n"
    "def greet(name: str) -> str:\n"
    "    return f'hello {name}'\n"
    "\n"
    "class Greeter:\n"
    "    pass\n"
)


@pytest.fixture()
def py_file(tmp_path: Path) -> Path:
    """Write a simple Python file into a temp directory and return the path."""
    f = tmp_path / "sample.py"
    f.write_text(_SIMPLE_SOURCE, encoding="utf-8")
    return f


@pytest.fixture()
def py_file_with_antipatterns(tmp_path: Path) -> Path:
    """Write a Python file containing anti-patterns into a temp directory."""
    source = (
        "from os import *\n"
        "\n"
        "def risky():\n"
        "    try:\n"
        "        pass\n"
        "    except:\n"
        "        pass\n"
        "\n"
        "def bad(items=[]):\n"
        "    return items\n"
    )
    f = tmp_path / "antipatterns.py"
    f.write_text(source, encoding="utf-8")
    return f


# ===================================================================
# CodeAnalysisPrimitive
# ===================================================================


class TestCodeAnalysisPrimitive:
    """Tests for CodeAnalysisPrimitive."""

    @pytest.mark.asyncio
    async def test_returns_analysis_result(self, py_file: Path) -> None:
        primitive = CodeAnalysisPrimitive()
        result = await primitive.execute(str(py_file), _ctx())
        assert isinstance(result, AnalysisResult)

    @pytest.mark.asyncio
    async def test_file_path_in_result(self, py_file: Path) -> None:
        primitive = CodeAnalysisPrimitive()
        result = await primitive.execute(str(py_file), _ctx())
        assert result.file_path == str(py_file)

    @pytest.mark.asyncio
    async def test_classes_extracted(self, py_file: Path) -> None:
        primitive = CodeAnalysisPrimitive()
        result = await primitive.execute(str(py_file), _ctx())
        class_names = [c.name for c in result.classes]
        assert "Greeter" in class_names

    @pytest.mark.asyncio
    async def test_functions_extracted(self, py_file: Path) -> None:
        primitive = CodeAnalysisPrimitive()
        result = await primitive.execute(str(py_file), _ctx())
        func_names = [f.name for f in result.functions]
        assert "greet" in func_names

    @pytest.mark.asyncio
    async def test_imports_extracted(self, py_file: Path) -> None:
        primitive = CodeAnalysisPrimitive()
        result = await primitive.execute(str(py_file), _ctx())
        modules = [i.module for i in result.imports]
        assert "os" in modules

    @pytest.mark.asyncio
    async def test_includes_patterns_by_default(self, py_file_with_antipatterns: Path) -> None:
        primitive = CodeAnalysisPrimitive(include_patterns=True)
        result = await primitive.execute(str(py_file_with_antipatterns), _ctx())
        assert len(result.patterns) > 0

    @pytest.mark.asyncio
    async def test_no_patterns_when_disabled(self, py_file: Path) -> None:
        primitive = CodeAnalysisPrimitive(include_patterns=False)
        result = await primitive.execute(str(py_file), _ctx())
        assert result.patterns == []

    @pytest.mark.asyncio
    async def test_total_lines_counted(self, py_file: Path) -> None:
        primitive = CodeAnalysisPrimitive()
        result = await primitive.execute(str(py_file), _ctx())
        assert result.total_lines == len(_SIMPLE_SOURCE.splitlines())

    @pytest.mark.asyncio
    async def test_complexity_score_positive(self, py_file: Path) -> None:
        primitive = CodeAnalysisPrimitive()
        result = await primitive.execute(str(py_file), _ctx())
        assert result.complexity_score > 0.0

    @pytest.mark.asyncio
    async def test_file_not_found_raises(self) -> None:
        primitive = CodeAnalysisPrimitive()
        with pytest.raises(FileNotFoundError):
            await primitive.execute("/nonexistent/path.py", _ctx())


# ===================================================================
# PatternDetectionPrimitive
# ===================================================================


class TestPatternDetectionPrimitive:
    """Tests for PatternDetectionPrimitive."""

    @pytest.mark.asyncio
    async def test_returns_list_of_pattern_match(self, py_file: Path) -> None:
        primitive = PatternDetectionPrimitive()
        result = await primitive.execute(str(py_file), _ctx())
        assert isinstance(result, list)
        assert all(isinstance(p, PatternMatch) for p in result)

    @pytest.mark.asyncio
    async def test_detects_anti_patterns(self, py_file_with_antipatterns: Path) -> None:
        primitive = PatternDetectionPrimitive()
        result = await primitive.execute(str(py_file_with_antipatterns), _ctx())
        names = {p.name for p in result}
        assert "bare_except" in names
        assert "mutable_default_argument" in names
        assert "star_import" in names

    @pytest.mark.asyncio
    async def test_clean_file_has_no_anti_patterns(self, py_file: Path) -> None:
        primitive = PatternDetectionPrimitive()
        result = await primitive.execute(str(py_file), _ctx())
        anti_patterns = [p for p in result if p.category == "anti_pattern"]
        assert anti_patterns == []

    @pytest.mark.asyncio
    async def test_file_not_found_raises(self) -> None:
        primitive = PatternDetectionPrimitive()
        with pytest.raises(FileNotFoundError):
            await primitive.execute("/nonexistent/path.py", _ctx())


# ===================================================================
# DependencyAnalysisPrimitive
# ===================================================================


class TestDependencyAnalysisPrimitive:
    """Tests for DependencyAnalysisPrimitive."""

    @pytest.mark.asyncio
    async def test_returns_dict_with_expected_keys(self, tmp_path: Path) -> None:
        primitive = DependencyAnalysisPrimitive()
        mock_output = MagicMock()
        mock_output.stdout = "requests 2.31.0\n  urllib3 2.0.4\n"
        mock_output.success = True

        with patch("python_pathway.primitives.UvTreePrimitive") as MockUvTree:
            instance = MockUvTree.return_value
            instance.execute = AsyncMock(return_value=mock_output)
            result = await primitive.execute(str(tmp_path), _ctx())

        assert "dependency_tree" in result
        assert "success" in result
        assert "project_path" in result

    @pytest.mark.asyncio
    async def test_project_path_matches_input(self, tmp_path: Path) -> None:
        primitive = DependencyAnalysisPrimitive()
        mock_output = MagicMock()
        mock_output.stdout = ""
        mock_output.success = True

        with patch("python_pathway.primitives.UvTreePrimitive") as MockUvTree:
            instance = MockUvTree.return_value
            instance.execute = AsyncMock(return_value=mock_output)
            result = await primitive.execute(str(tmp_path), _ctx())

        assert result["project_path"] == str(tmp_path)

    @pytest.mark.asyncio
    async def test_dependency_tree_contains_stdout(self, tmp_path: Path) -> None:
        primitive = DependencyAnalysisPrimitive()
        expected_tree = "requests 2.31.0\n  urllib3 2.0.4\n"
        mock_output = MagicMock()
        mock_output.stdout = expected_tree
        mock_output.success = True

        with patch("python_pathway.primitives.UvTreePrimitive") as MockUvTree:
            instance = MockUvTree.return_value
            instance.execute = AsyncMock(return_value=mock_output)
            result = await primitive.execute(str(tmp_path), _ctx())

        assert result["dependency_tree"] == expected_tree

    @pytest.mark.asyncio
    async def test_success_false_on_command_failure(self, tmp_path: Path) -> None:
        primitive = DependencyAnalysisPrimitive()
        mock_output = MagicMock()
        mock_output.stdout = ""
        mock_output.success = False

        with patch("python_pathway.primitives.UvTreePrimitive") as MockUvTree:
            instance = MockUvTree.return_value
            instance.execute = AsyncMock(return_value=mock_output)
            result = await primitive.execute(str(tmp_path), _ctx())

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_uv_tree_created_with_working_dir(self, tmp_path: Path) -> None:
        """Ensure UvTreePrimitive is constructed with the input path as working_dir."""
        primitive = DependencyAnalysisPrimitive()
        mock_output = MagicMock()
        mock_output.stdout = ""
        mock_output.success = True

        with patch("python_pathway.primitives.UvTreePrimitive") as MockUvTree:
            instance = MockUvTree.return_value
            instance.execute = AsyncMock(return_value=mock_output)
            await primitive.execute(str(tmp_path), _ctx())
            MockUvTree.assert_called_once_with(working_dir=str(tmp_path))
