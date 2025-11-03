"""Unit tests for code analysis primitives."""

import pytest
from tta_dev_primitives import WorkflowContext

from tta_kb_automation.core.code_primitives import (
    AnalyzeCodeStructure,
    ExtractTODOs,
    ParseDocstrings,
    ScanCodebase,
)


@pytest.fixture
def mock_codebase(tmp_path):
    """Create a mock codebase with various Python files."""
    # Create directory structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()

    # Create source file with TODOs and docstrings
    (src_dir / "example.py").write_text('''"""Example module for testing.

This module demonstrates various code patterns.

Example:
    >>> from example import MyClass
    >>> obj = MyClass()
"""

class MyClass:
    """A sample class for testing.

    References:
        :class:`OtherClass`
        [[Wiki Link]]
    """

    def public_method(self):
        """Public method with docstring."""
        # TODO: Add input validation
        pass

    def _private_method(self):
        # Private method without docstring
        pass

def my_function():
    """Sample function with example.

    Example:
        >>> my_function()
        'result'
    """
    # TODO: Implement caching
    # TODO: Add error handling
    return "result"

# TODO: Add integration tests
''')

    # Create test file
    (tests_dir / "test_example.py").write_text('''"""Test module."""

def test_something():
    """Test function."""
    # TODO: Add more assertions
    assert True
''')

    # Create file with no docstrings
    (src_dir / "no_docs.py").write_text("""
class UndocumentedClass:
    def undocumented_method(self):
        pass

def undocumented_function():
    pass
""")

    # Create __pycache__ with .py file to test exclusion
    pycache = src_dir / "__pycache__"
    pycache.mkdir()
    (pycache / "cached.py").write_text("# This should be excluded")

    return tmp_path


@pytest.mark.asyncio
async def test_scan_codebase_basic(mock_codebase):
    """Test basic codebase scanning."""
    scanner = ScanCodebase()
    context = WorkflowContext()

    result = await scanner.execute({"root_path": str(mock_codebase)}, context)

    assert "files" in result
    assert "total_files" in result
    assert "excluded_files" in result
    assert result["total_files"] == 3  # example.py, test_example.py, no_docs.py
    assert any("example.py" in f for f in result["files"])
    assert any("test_example.py" in f for f in result["files"])
    assert any("no_docs.py" in f for f in result["files"])
    # Check that cached.py in __pycache__ was excluded
    assert any("__pycache__" in f for f in result["excluded_files"])


@pytest.mark.asyncio
async def test_scan_codebase_exclude_tests(mock_codebase):
    """Test scanning with test file exclusion."""
    scanner = ScanCodebase()
    context = WorkflowContext()

    result = await scanner.execute(
        {"root_path": str(mock_codebase), "include_tests": False}, context
    )

    assert (
        result["total_files"] == 2
    )  # example.py and no_docs.py (cache.py excluded by __pycache__ pattern)
    # Check that no test files in results (check filename, not full path)
    from pathlib import Path

    assert not any("test_" in Path(f).name for f in result["files"])
    # Verify test file is excluded
    assert any("test_example.py" in f for f in result["excluded_files"])
    # Verify __pycache__ file is also excluded
    assert any("cached.py" in f for f in result["excluded_files"])


@pytest.mark.asyncio
async def test_scan_codebase_custom_excludes(mock_codebase):
    """Test scanning with custom exclude patterns."""
    scanner = ScanCodebase()
    context = WorkflowContext()

    result = await scanner.execute(
        {
            "root_path": str(mock_codebase),
            "exclude_patterns": ["__pycache__", "no_docs"],
        },
        context,
    )

    assert not any("no_docs.py" in f for f in result["files"])
    assert any("example.py" in f for f in result["files"])


@pytest.mark.asyncio
async def test_scan_codebase_invalid_path():
    """Test scanning with invalid path."""
    scanner = ScanCodebase()
    context = WorkflowContext()

    with pytest.raises(ValueError, match="Root path does not exist"):
        await scanner.execute({"root_path": "/nonexistent/path"}, context)


@pytest.mark.asyncio
async def test_extract_todos_basic(mock_codebase):
    """Test TODO extraction from code."""
    # First scan to get files
    scanner = ScanCodebase()
    scan_result = await scanner.execute({"root_path": str(mock_codebase)}, WorkflowContext())

    # Extract TODOs
    extractor = ExtractTODOs()
    context = WorkflowContext()

    result = await extractor.execute({"files": scan_result["files"]}, context)

    assert "todos" in result
    assert "total_todos" in result
    assert "files_with_todos" in result
    assert result["total_todos"] >= 4  # At least 4 TODOs in mock codebase
    assert result["files_with_todos"] >= 2  # TODOs in at least 2 files


@pytest.mark.asyncio
async def test_extract_todos_with_context(mock_codebase):
    """Test TODO extraction with context lines."""
    scanner = ScanCodebase()
    scan_result = await scanner.execute({"root_path": str(mock_codebase)}, WorkflowContext())

    extractor = ExtractTODOs()
    result = await extractor.execute(
        {"files": scan_result["files"], "include_context": True, "context_lines": 2},
        WorkflowContext(),
    )

    # Check that TODOs have context
    for todo in result["todos"]:
        assert "context_before" in todo
        assert "context_after" in todo
        assert isinstance(todo["context_before"], list)
        assert isinstance(todo["context_after"], list)


@pytest.mark.asyncio
async def test_extract_todos_categories(mock_codebase):
    """Test TODO category inference."""
    scanner = ScanCodebase()
    scan_result = await scanner.execute({"root_path": str(mock_codebase)}, WorkflowContext())

    extractor = ExtractTODOs()
    result = await extractor.execute({"files": scan_result["files"]}, WorkflowContext())

    # Check that categories are assigned
    for todo in result["todos"]:
        assert "category" in todo
        assert todo["category"] in [
            "implementation",
            "testing",
            "documentation",
            "bugfix",
            "refactoring",
        ]

    # Check specific categorizations
    test_todos = [t for t in result["todos"] if "test" in t["file"].lower()]
    if test_todos:
        assert test_todos[0]["category"] == "testing"


@pytest.mark.asyncio
async def test_extract_todos_without_context(mock_codebase):
    """Test TODO extraction without context lines."""
    scanner = ScanCodebase()
    scan_result = await scanner.execute({"root_path": str(mock_codebase)}, WorkflowContext())

    extractor = ExtractTODOs()
    result = await extractor.execute(
        {"files": scan_result["files"], "include_context": False}, WorkflowContext()
    )

    # Check that TODOs have empty context
    for todo in result["todos"]:
        assert todo["context_before"] == []
        assert todo["context_after"] == []


@pytest.mark.asyncio
async def test_parse_docstrings_basic(mock_codebase):
    """Test docstring parsing."""
    scanner = ScanCodebase()
    scan_result = await scanner.execute({"root_path": str(mock_codebase)}, WorkflowContext())

    parser = ParseDocstrings()
    result = await parser.execute({"files": scan_result["files"]}, WorkflowContext())

    assert "docstrings" in result
    assert "total_docstrings" in result
    assert "missing_docstrings" in result
    assert result["total_docstrings"] > 0

    # Check docstring structure
    for doc in result["docstrings"]:
        assert "file" in doc
        assert "type" in doc
        assert "name" in doc
        assert "docstring" in doc
        assert "summary" in doc
        assert "line_number" in doc


@pytest.mark.asyncio
async def test_parse_docstrings_with_examples(mock_codebase):
    """Test docstring example extraction."""
    scanner = ScanCodebase()
    scan_result = await scanner.execute({"root_path": str(mock_codebase)}, WorkflowContext())

    parser = ParseDocstrings()
    result = await parser.execute(
        {"files": scan_result["files"], "extract_examples": True}, WorkflowContext()
    )

    # Find docstrings with examples
    docs_with_examples = [d for d in result["docstrings"] if d["examples"]]
    assert len(docs_with_examples) > 0


@pytest.mark.asyncio
async def test_parse_docstrings_with_references(mock_codebase):
    """Test docstring reference extraction."""
    scanner = ScanCodebase()
    scan_result = await scanner.execute({"root_path": str(mock_codebase)}, WorkflowContext())

    parser = ParseDocstrings()
    result = await parser.execute(
        {"files": scan_result["files"], "extract_references": True}, WorkflowContext()
    )

    # Find docstrings with references
    docs_with_refs = [d for d in result["docstrings"] if d["references"]]
    assert len(docs_with_refs) > 0

    # Check MyClass docstring has references
    myclass_doc = next((d for d in result["docstrings"] if d["name"] == "MyClass"), None)
    if myclass_doc:
        assert len(myclass_doc["references"]) > 0


@pytest.mark.asyncio
async def test_parse_docstrings_missing_detection(mock_codebase):
    """Test detection of missing docstrings."""
    scanner = ScanCodebase()
    scan_result = await scanner.execute({"root_path": str(mock_codebase)}, WorkflowContext())

    parser = ParseDocstrings()
    result = await parser.execute({"files": scan_result["files"]}, WorkflowContext())

    # Should detect missing docstrings in no_docs.py
    missing = result["missing_docstrings"]
    assert len(missing) > 0

    # Check structure of missing docstring entries
    for entry in missing:
        assert "file" in entry
        assert "type" in entry
        assert "name" in entry
        assert "line_number" in entry


@pytest.mark.asyncio
async def test_analyze_code_structure_basic(mock_codebase):
    """Test code structure analysis."""
    scanner = ScanCodebase()
    scan_result = await scanner.execute({"root_path": str(mock_codebase)}, WorkflowContext())

    analyzer = AnalyzeCodeStructure()
    result = await analyzer.execute({"files": scan_result["files"]}, WorkflowContext())

    assert "modules" in result
    assert "total_classes" in result
    assert "total_functions" in result
    assert "dependency_graph" in result
    assert result["total_classes"] > 0
    assert result["total_functions"] > 0


@pytest.mark.asyncio
async def test_analyze_code_structure_with_imports(mock_codebase):
    """Test import extraction."""
    scanner = ScanCodebase()
    scan_result = await scanner.execute({"root_path": str(mock_codebase)}, WorkflowContext())

    analyzer = AnalyzeCodeStructure()
    result = await analyzer.execute(
        {"files": scan_result["files"], "include_imports": True}, WorkflowContext()
    )

    # Check that modules have import information
    for module in result["modules"]:
        assert "imports" in module
        assert isinstance(module["imports"], list)


@pytest.mark.asyncio
async def test_analyze_code_structure_with_dependencies(mock_codebase):
    """Test dependency tracking."""
    scanner = ScanCodebase()
    scan_result = await scanner.execute({"root_path": str(mock_codebase)}, WorkflowContext())

    analyzer = AnalyzeCodeStructure()
    result = await analyzer.execute(
        {"files": scan_result["files"], "include_dependencies": True}, WorkflowContext()
    )

    # Check dependency graph
    assert len(result["dependency_graph"]) > 0
    for _file_path, deps in result["dependency_graph"].items():
        assert isinstance(deps, list)


@pytest.mark.asyncio
async def test_analyze_code_structure_module_details(mock_codebase):
    """Test detailed module analysis."""
    scanner = ScanCodebase()
    scan_result = await scanner.execute({"root_path": str(mock_codebase)}, WorkflowContext())

    analyzer = AnalyzeCodeStructure()
    result = await analyzer.execute({"files": scan_result["files"]}, WorkflowContext())

    # Find example.py module
    example_module = next((m for m in result["modules"] if "example.py" in m["file"]), None)

    assert example_module is not None
    assert "MyClass" in example_module["classes"]
    assert any("function" in f for f in example_module["functions"])
    assert example_module["loc"] > 0


@pytest.mark.asyncio
async def test_analyze_code_structure_counts(mock_codebase):
    """Test aggregate counts."""
    scanner = ScanCodebase()
    scan_result = await scanner.execute({"root_path": str(mock_codebase)}, WorkflowContext())

    analyzer = AnalyzeCodeStructure()
    result = await analyzer.execute({"files": scan_result["files"]}, WorkflowContext())

    # Verify counts match sum of individual modules
    total_classes = sum(len(m["classes"]) for m in result["modules"])
    total_functions = sum(len(m["functions"]) for m in result["modules"])

    assert result["total_classes"] == total_classes
    assert result["total_functions"] == total_functions
