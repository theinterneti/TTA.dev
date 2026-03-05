"""Tests for PatternDetector."""

from __future__ import annotations

import os

import pytest

from python_pathway.detector import PatternDetector
from python_pathway.models import PatternMatch


@pytest.fixture()
def detector() -> PatternDetector:
    return PatternDetector()


@pytest.fixture()
def fixture_path() -> str:
    return os.path.join(os.path.dirname(__file__), "fixtures", "sample_code.py")


class TestSingletonDetection:
    """Tests for singleton pattern detection."""

    def test_detects_singleton(self, detector: PatternDetector) -> None:
        source = (
            "class MyService:\n"
            "    _instance = None\n"
            "    def __new__(cls):\n"
            "        if cls._instance is None:\n"
            "            cls._instance = super().__new__(cls)\n"
            "        return cls._instance\n"
        )
        patterns = detector.detect_from_source(source)
        singletons = [p for p in patterns if p.name == "singleton"]
        assert len(singletons) == 1
        assert singletons[0].category == "pattern"
        assert singletons[0].severity == "info"
        assert "MyService" in singletons[0].description

    def test_no_singleton_without_new(self, detector: PatternDetector) -> None:
        source = "class Foo:\n    _instance = None\n"
        patterns = detector.detect_from_source(source)
        assert not any(p.name == "singleton" for p in patterns)

    def test_no_singleton_without_instance_attr(self, detector: PatternDetector) -> None:
        source = "class Foo:\n    def __new__(cls):\n        return super().__new__(cls)\n"
        patterns = detector.detect_from_source(source)
        assert not any(p.name == "singleton" for p in patterns)


class TestFactoryDetection:
    """Tests for factory pattern detection."""

    def test_detects_create_prefix(self, detector: PatternDetector) -> None:
        source = "def create_widget(name):\n    return {'name': name}\n"
        patterns = detector.detect_from_source(source)
        factories = [p for p in patterns if p.name == "factory"]
        assert len(factories) == 1
        assert "create_widget" in factories[0].description

    def test_detects_factory_suffix(self, detector: PatternDetector) -> None:
        source = "def widget_factory(name):\n    return {'name': name}\n"
        patterns = detector.detect_from_source(source)
        assert any(p.name == "factory" for p in patterns)

    def test_detects_create_exact(self, detector: PatternDetector) -> None:
        source = "def create(name):\n    return {'name': name}\n"
        patterns = detector.detect_from_source(source)
        assert any(p.name == "factory" for p in patterns)

    def test_no_factory_on_regular_function(self, detector: PatternDetector) -> None:
        source = "def process_data(x):\n    return x\n"
        patterns = detector.detect_from_source(source)
        assert not any(p.name == "factory" for p in patterns)


class TestDecoratorPatternDetection:
    """Tests for decorator pattern detection."""

    def test_detects_decorator_pattern(self, detector: PatternDetector) -> None:
        source = (
            "def my_decorator(func):\n"
            "    def wrapper(*args, **kwargs):\n"
            "        return func(*args, **kwargs)\n"
            "    return wrapper\n"
        )
        patterns = detector.detect_from_source(source)
        dec_patterns = [p for p in patterns if p.name == "decorator_pattern"]
        assert len(dec_patterns) == 1
        assert "my_decorator" in dec_patterns[0].description

    def test_no_decorator_pattern_without_inner_return(self, detector: PatternDetector) -> None:
        source = (
            "def my_func(func):\n"
            "    def wrapper(*args):\n"
            "        return func(*args)\n"
            "    return 42\n"  # returns a literal, not the inner func
        )
        patterns = detector.detect_from_source(source)
        assert not any(p.name == "decorator_pattern" for p in patterns)


class TestContextManagerDetection:
    """Tests for context manager pattern detection."""

    def test_detects_context_manager(self, detector: PatternDetector) -> None:
        source = (
            "class MyCtx:\n"
            "    def __enter__(self):\n"
            "        return self\n"
            "    def __exit__(self, *args):\n"
            "        pass\n"
        )
        patterns = detector.detect_from_source(source)
        ctx_patterns = [p for p in patterns if p.name == "context_manager"]
        assert len(ctx_patterns) == 1
        assert "MyCtx" in ctx_patterns[0].description

    def test_no_context_manager_with_only_enter(self, detector: PatternDetector) -> None:
        source = "class Foo:\n    def __enter__(self):\n        return self\n"
        patterns = detector.detect_from_source(source)
        assert not any(p.name == "context_manager" for p in patterns)


class TestAsyncPatternDetection:
    """Tests for async pattern detection."""

    def test_detects_async_function(self, detector: PatternDetector) -> None:
        source = "async def fetch(url: str) -> str:\n    return url\n"
        patterns = detector.detect_from_source(source)
        async_patterns = [p for p in patterns if p.name == "async_pattern"]
        assert len(async_patterns) == 1
        assert "fetch" in async_patterns[0].description

    def test_only_top_level_async(self, detector: PatternDetector) -> None:
        """Async methods inside a class should NOT be reported as async_pattern."""
        source = "class MyClass:\n    async def do_stuff(self) -> None:\n        pass\n"
        patterns = detector.detect_from_source(source)
        assert not any(p.name == "async_pattern" for p in patterns)

    def test_no_async_pattern_for_sync_function(self, detector: PatternDetector) -> None:
        source = "def sync_func() -> None:\n    pass\n"
        patterns = detector.detect_from_source(source)
        assert not any(p.name == "async_pattern" for p in patterns)


class TestMutableDefaultArgsDetection:
    """Tests for mutable default argument anti-pattern."""

    def test_detects_list_default(self, detector: PatternDetector) -> None:
        source = "def foo(items=[]):\n    return items\n"
        patterns = detector.detect_from_source(source)
        mutable = [p for p in patterns if p.name == "mutable_default_argument"]
        assert len(mutable) == 1
        assert mutable[0].category == "anti_pattern"
        assert mutable[0].severity == "warning"

    def test_detects_dict_default(self, detector: PatternDetector) -> None:
        source = "def foo(cfg={}):\n    return cfg\n"
        patterns = detector.detect_from_source(source)
        assert any(p.name == "mutable_default_argument" for p in patterns)

    def test_detects_set_default(self, detector: PatternDetector) -> None:
        source = "def foo(items=set()):\n    return items\n"
        # set() call is ast.Call, not ast.Set — should NOT be detected
        patterns = detector.detect_from_source(source)
        assert not any(p.name == "mutable_default_argument" for p in patterns)

    def test_no_mutable_default_for_immutable(self, detector: PatternDetector) -> None:
        source = "def foo(x=1, y='hello', z=None):\n    pass\n"
        patterns = detector.detect_from_source(source)
        assert not any(p.name == "mutable_default_argument" for p in patterns)


class TestBareExceptDetection:
    """Tests for bare except anti-pattern."""

    def test_detects_bare_except(self, detector: PatternDetector) -> None:
        source = "try:\n    pass\nexcept:\n    pass\n"
        patterns = detector.detect_from_source(source)
        bare = [p for p in patterns if p.name == "bare_except"]
        assert len(bare) == 1
        assert bare[0].category == "anti_pattern"
        assert bare[0].severity == "warning"

    def test_no_bare_except_with_exception_type(self, detector: PatternDetector) -> None:
        source = "try:\n    pass\nexcept ValueError:\n    pass\n"
        patterns = detector.detect_from_source(source)
        assert not any(p.name == "bare_except" for p in patterns)


class TestMissingTypeHintsDetection:
    """Tests for missing type hints anti-pattern."""

    def test_detects_missing_hints(self, detector: PatternDetector) -> None:
        source = "def process(x, y):\n    return x + y\n"
        patterns = detector.detect_from_source(source)
        missing = [p for p in patterns if p.name == "missing_type_hints"]
        assert len(missing) == 1
        assert missing[0].category == "anti_pattern"
        assert "process" in missing[0].description

    def test_no_missing_hints_on_fully_typed(self, detector: PatternDetector) -> None:
        source = "def process(x: int, y: int) -> int:\n    return x + y\n"
        patterns = detector.detect_from_source(source)
        assert not any(p.name == "missing_type_hints" for p in patterns)

    def test_skips_private_functions(self, detector: PatternDetector) -> None:
        """Private functions (underscore prefix) should not be flagged."""
        source = "def _private(x, y):\n    return x + y\n"
        patterns = detector.detect_from_source(source)
        assert not any(p.name == "missing_type_hints" for p in patterns)

    def test_detects_missing_return_type(self, detector: PatternDetector) -> None:
        source = "def greet(name: str):\n    print(name)\n"
        patterns = detector.detect_from_source(source)
        assert any(p.name == "missing_type_hints" for p in patterns)


class TestStarImportDetection:
    """Tests for star import anti-pattern."""

    def test_detects_star_import(self, detector: PatternDetector) -> None:
        source = "from os.path import *\n"
        patterns = detector.detect_from_source(source)
        star = [p for p in patterns if p.name == "star_import"]
        assert len(star) == 1
        assert star[0].category == "anti_pattern"
        assert "os.path" in star[0].description

    def test_no_star_import_on_named_import(self, detector: PatternDetector) -> None:
        source = "from os.path import join, exists\n"
        patterns = detector.detect_from_source(source)
        assert not any(p.name == "star_import" for p in patterns)


class TestCleanCode:
    """Tests that clean code produces no anti-pattern false positives."""

    def test_clean_typed_function_no_anti_patterns(self, detector: PatternDetector) -> None:
        source = (
            "def add(x: int, y: int) -> int:\n"
            "    return x + y\n"
            "\n"
            "def multiply(x: int, y: int) -> int:\n"
            "    return x * y\n"
        )
        patterns = detector.detect_from_source(source)
        anti_patterns = [p for p in patterns if p.category == "anti_pattern"]
        assert anti_patterns == []

    def test_clean_class_no_anti_patterns(self, detector: PatternDetector) -> None:
        source = (
            "class Calculator:\n    def add(self, x: int, y: int) -> int:\n        return x + y\n"
        )
        patterns = detector.detect_from_source(source)
        anti_patterns = [p for p in patterns if p.category == "anti_pattern"]
        assert anti_patterns == []


class TestDetectFromFile:
    """Tests for PatternDetector.detect_patterns using fixture file."""

    def test_detects_all_patterns_in_fixture(
        self, detector: PatternDetector, fixture_path: str
    ) -> None:
        patterns = detector.detect_patterns(fixture_path)
        names = {p.name for p in patterns}
        # Should detect at least these patterns
        assert "singleton" in names
        assert "context_manager" in names
        assert "factory" in names
        assert "async_pattern" in names
        assert "decorator_pattern" in names

    def test_detects_all_anti_patterns_in_fixture(
        self, detector: PatternDetector, fixture_path: str
    ) -> None:
        patterns = detector.detect_patterns(fixture_path)
        names = {p.name for p in patterns}
        assert "mutable_default_argument" in names
        assert "bare_except" in names
        assert "missing_type_hints" in names
        assert "star_import" in names

    def test_returns_list_of_pattern_match(
        self, detector: PatternDetector, fixture_path: str
    ) -> None:
        patterns = detector.detect_patterns(fixture_path)
        assert all(isinstance(p, PatternMatch) for p in patterns)
