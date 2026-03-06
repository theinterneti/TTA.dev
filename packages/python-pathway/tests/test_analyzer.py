"""Tests for PythonAnalyzer."""

from __future__ import annotations

from pathlib import Path

import pytest

from python_pathway.analyzer import PythonAnalyzer
from python_pathway.models import AnalysisResult


@pytest.fixture()
def analyzer() -> PythonAnalyzer:
    return PythonAnalyzer()


class TestAnalyzeSource:
    """Tests for PythonAnalyzer.analyze_source."""

    def test_empty_source(self, analyzer: PythonAnalyzer) -> None:
        result = analyzer.analyze_source("")
        assert isinstance(result, AnalysisResult)
        assert result.file_path == "<string>"
        assert result.classes == []
        assert result.functions == []
        assert result.imports == []
        assert result.total_lines == 0

    def test_total_lines_counted(self, analyzer: PythonAnalyzer) -> None:
        source = "x = 1\ny = 2\nz = 3\n"
        result = analyzer.analyze_source(source)
        assert result.total_lines == 3

    def test_file_path_associated(self, analyzer: PythonAnalyzer) -> None:
        result = analyzer.analyze_source("x = 1", file_path="myfile.py")
        assert result.file_path == "myfile.py"

    def test_complexity_score_positive(self, analyzer: PythonAnalyzer) -> None:
        source = "def foo():\n    pass\n"
        result = analyzer.analyze_source(source)
        assert result.complexity_score > 0.0


class TestExtractClasses:
    """Tests for class extraction."""

    def test_simple_class(self, analyzer: PythonAnalyzer) -> None:
        source = "class Foo:\n    pass\n"
        result = analyzer.analyze_source(source)
        assert len(result.classes) == 1
        assert result.classes[0].name == "Foo"
        assert result.classes[0].line_number == 1

    def test_class_with_bases(self, analyzer: PythonAnalyzer) -> None:
        source = "class Foo(Bar, Baz):\n    pass\n"
        result = analyzer.analyze_source(source)
        assert result.classes[0].bases == ["Bar", "Baz"]

    def test_class_with_methods(self, analyzer: PythonAnalyzer) -> None:
        source = "class Foo:\n    def bar(self):\n        pass\n    def baz(self):\n        pass\n"
        result = analyzer.analyze_source(source)
        assert "bar" in result.classes[0].methods
        assert "baz" in result.classes[0].methods

    def test_abstract_class_via_abc(self, analyzer: PythonAnalyzer) -> None:
        source = "from abc import ABC\nclass MyABC(ABC):\n    pass\n"
        result = analyzer.analyze_source(source)
        assert result.classes[0].is_abstract is True

    def test_abstract_class_via_abstractmethod(self, analyzer: PythonAnalyzer) -> None:
        source = (
            "from abc import abstractmethod\n"
            "class MyABC:\n"
            "    @abstractmethod\n"
            "    def do_thing(self):\n"
            "        pass\n"
        )
        result = analyzer.analyze_source(source)
        assert result.classes[0].is_abstract is True

    def test_non_abstract_class(self, analyzer: PythonAnalyzer) -> None:
        source = "class Foo:\n    def bar(self):\n        pass\n"
        result = analyzer.analyze_source(source)
        assert result.classes[0].is_abstract is False

    def test_class_with_decorator(self, analyzer: PythonAnalyzer) -> None:
        source = "@dataclass\nclass Foo:\n    x: int = 0\n"
        result = analyzer.analyze_source(source)
        assert "dataclass" in result.classes[0].decorators

    def test_multiple_classes(self, analyzer: PythonAnalyzer) -> None:
        source = "class Foo:\n    pass\nclass Bar:\n    pass\n"
        result = analyzer.analyze_source(source)
        names = {c.name for c in result.classes}
        assert names == {"Foo", "Bar"}

    def test_no_classes(self, analyzer: PythonAnalyzer) -> None:
        result = analyzer.analyze_source("x = 1\n")
        assert result.classes == []


class TestExtractFunctions:
    """Tests for top-level function extraction."""

    def test_simple_function(self, analyzer: PythonAnalyzer) -> None:
        source = "def greet(name: str) -> str:\n    return f'hello {name}'\n"
        result = analyzer.analyze_source(source)
        assert len(result.functions) == 1
        func = result.functions[0]
        assert func.name == "greet"
        assert func.is_async is False
        assert func.line_number == 1

    def test_async_function(self, analyzer: PythonAnalyzer) -> None:
        source = "async def fetch(url: str) -> str:\n    return url\n"
        result = analyzer.analyze_source(source)
        assert result.functions[0].is_async is True

    def test_function_parameters(self, analyzer: PythonAnalyzer) -> None:
        source = "def foo(a: int, b: str, c: float) -> None:\n    pass\n"
        result = analyzer.analyze_source(source)
        assert result.functions[0].parameters == ["a", "b", "c"]

    def test_function_return_type(self, analyzer: PythonAnalyzer) -> None:
        source = "def foo() -> int:\n    return 1\n"
        result = analyzer.analyze_source(source)
        assert result.functions[0].return_type == "int"

    def test_function_no_return_type(self, analyzer: PythonAnalyzer) -> None:
        source = "def foo():\n    pass\n"
        result = analyzer.analyze_source(source)
        assert result.functions[0].return_type is None

    def test_function_with_type_hints(self, analyzer: PythonAnalyzer) -> None:
        source = "def foo(x: int) -> int:\n    return x\n"
        result = analyzer.analyze_source(source)
        assert result.functions[0].has_type_hints is True

    def test_function_without_type_hints(self, analyzer: PythonAnalyzer) -> None:
        source = "def foo(x):\n    return x\n"
        result = analyzer.analyze_source(source)
        assert result.functions[0].has_type_hints is False

    def test_function_with_decorator(self, analyzer: PythonAnalyzer) -> None:
        source = "@staticmethod\ndef foo() -> None:\n    pass\n"
        result = analyzer.analyze_source(source)
        assert "staticmethod" in result.functions[0].decorators

    def test_only_top_level_functions_returned(self, analyzer: PythonAnalyzer) -> None:
        """Methods inside classes should not appear in top-level functions."""
        source = (
            "def top_level() -> None:\n"
            "    pass\n"
            "class MyClass:\n"
            "    def method(self) -> None:\n"
            "        pass\n"
        )
        result = analyzer.analyze_source(source)
        func_names = [f.name for f in result.functions]
        assert "top_level" in func_names
        assert "method" not in func_names

    def test_multiple_functions(self, analyzer: PythonAnalyzer) -> None:
        source = "def foo() -> None:\n    pass\ndef bar() -> None:\n    pass\n"
        result = analyzer.analyze_source(source)
        assert len(result.functions) == 2


class TestExtractImports:
    """Tests for import extraction."""

    def test_simple_import(self, analyzer: PythonAnalyzer) -> None:
        source = "import os\n"
        result = analyzer.analyze_source(source)
        assert any(i.module == "os" and not i.is_from_import for i in result.imports)

    def test_import_with_alias(self, analyzer: PythonAnalyzer) -> None:
        source = "import numpy as np\n"
        result = analyzer.analyze_source(source)
        imp = next(i for i in result.imports if i.module == "numpy")
        assert imp.alias == "np"

    def test_from_import(self, analyzer: PythonAnalyzer) -> None:
        source = "from os.path import join, exists\n"
        result = analyzer.analyze_source(source)
        imp = next(i for i in result.imports if i.module == "os.path")
        assert imp.is_from_import is True
        assert "join" in imp.names
        assert "exists" in imp.names

    def test_multiple_imports(self, analyzer: PythonAnalyzer) -> None:
        source = "import os\nimport sys\nfrom pathlib import Path\n"
        result = analyzer.analyze_source(source)
        modules = {i.module for i in result.imports}
        assert {"os", "sys", "pathlib"}.issubset(modules)

    def test_no_imports(self, analyzer: PythonAnalyzer) -> None:
        result = analyzer.analyze_source("x = 1\n")
        assert result.imports == []


class TestComplexity:
    """Tests for complexity score calculation."""

    def test_base_complexity(self, analyzer: PythonAnalyzer) -> None:
        """Empty module has base complexity of 1.0."""
        result = analyzer.analyze_source("")
        assert result.complexity_score == 1.0

    def test_if_increases_complexity(self, analyzer: PythonAnalyzer) -> None:
        base = analyzer.analyze_source("x = 1\n").complexity_score
        with_if = analyzer.analyze_source("if True:\n    x = 1\n").complexity_score
        assert with_if > base

    def test_function_increases_complexity(self, analyzer: PythonAnalyzer) -> None:
        base = analyzer.analyze_source("x = 1\n").complexity_score
        with_func = analyzer.analyze_source("def foo():\n    pass\n").complexity_score
        assert with_func > base

    def test_loop_increases_complexity(self, analyzer: PythonAnalyzer) -> None:
        base = analyzer.analyze_source("x = 1\n").complexity_score
        with_loop = analyzer.analyze_source("for i in range(10):\n    pass\n").complexity_score
        assert with_loop > base


class TestAnalyzeFile:
    """Tests for PythonAnalyzer.analyze_file."""

    def test_analyze_fixture_file(self, analyzer: PythonAnalyzer) -> None:
        import os

        fixture = os.path.join(os.path.dirname(__file__), "fixtures", "sample_code.py")
        result = analyzer.analyze_file(fixture)
        assert result.total_lines > 0
        assert len(result.classes) > 0
        assert len(result.functions) > 0
        assert len(result.imports) > 0

    def test_file_not_found(self, analyzer: PythonAnalyzer) -> None:
        with pytest.raises(FileNotFoundError):
            analyzer.analyze_file("/nonexistent/path/to/file.py")

    def test_syntax_error(self, analyzer: PythonAnalyzer, tmp_path: Path) -> None:
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("def (\n    broken syntax\n", encoding="utf-8")
        with pytest.raises(SyntaxError):
            analyzer.analyze_file(str(bad_file))
