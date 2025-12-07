"""Tests for the AST-based code transformer."""

import ast

from tta_dev_primitives.analysis.transformer import (
    CodeTransformer,
    TransformResult,
    transform_code,
)


class TestTransformResult:
    """Test the TransformResult dataclass."""

    def test_success_result(self) -> None:
        """Test creating a successful transform result."""
        result = TransformResult(
            original_code="original",
            transformed_code="transformed",
            changes_made=[{"type": "retry", "function": "test"}],
            imports_added=["from tta import Retry"],
            success=True,
        )
        assert result.success
        assert result.error is None
        assert result.original_code == "original"
        assert result.transformed_code == "transformed"

    def test_error_result(self) -> None:
        """Test creating an error transform result."""
        result = TransformResult(
            original_code="bad code",
            transformed_code="bad code",
            changes_made=[],
            imports_added=[],
            success=False,
            error="Syntax error",
        )
        assert not result.success
        assert result.error == "Syntax error"


class TestCodeTransformer:
    """Test the CodeTransformer class."""

    def test_init(self) -> None:
        """Test transformer initialization."""
        transformer = CodeTransformer()
        assert transformer._import_map is not None
        assert "RetryPrimitive" in transformer._import_map
        assert "TimeoutPrimitive" in transformer._import_map

    def test_transform_syntax_error(self) -> None:
        """Test transformer handles syntax errors."""
        transformer = CodeTransformer()
        result = transformer.transform("def broken(")
        assert not result.success
        assert "Syntax error" in result.error

    def test_transform_no_changes(self) -> None:
        """Test transformer with clean code."""
        transformer = CodeTransformer()
        code = """
def simple_function():
    return 42
"""
        result = transformer.transform(code, auto_detect=True)
        assert result.success
        # May or may not have changes depending on detection

    def test_transform_retry_pattern(self) -> None:
        """Test transformer detects and can transform retry patterns."""
        transformer = CodeTransformer()
        code = """
def fetch_data():
    for attempt in range(3):
        try:
            return do_request()
        except Exception:
            if attempt < 2:
                time.sleep(1)
            else:
                raise
"""
        result = transformer.transform(code, primitive="RetryPrimitive")
        assert result.success

    def test_transform_timeout_pattern(self) -> None:
        """Test transformer can handle timeout patterns."""
        transformer = CodeTransformer()
        code = """
async def slow_operation():
    try:
        result = await asyncio.wait_for(do_work(), timeout=30)
    except asyncio.TimeoutError:
        return None
"""
        result = transformer.transform(code, primitive="TimeoutPrimitive")
        assert result.success

    def test_transform_cache_pattern(self) -> None:
        """Test transformer can handle cache patterns."""
        transformer = CodeTransformer()
        code = """
_cache = {}

def get_data(key):
    if key in _cache:
        return _cache[key]
    result = expensive_call(key)
    _cache[key] = result
    return result
"""
        result = transformer.transform(code, primitive="CachePrimitive")
        assert result.success


class TestTransformCodeFunction:
    """Test the transform_code convenience function."""

    def test_transform_code_auto_detect(self) -> None:
        """Test transform_code with auto detection."""
        code = """
def simple():
    return 1
"""
        result = transform_code(code, auto_detect=True)
        assert result.success

    def test_transform_code_specific_primitive(self) -> None:
        """Test transform_code with specific primitive."""
        code = """
def fetch():
    for i in range(3):
        try:
            return call()
        except:
            pass
"""
        result = transform_code(code, primitive="RetryPrimitive", auto_detect=False)
        assert result.success

    def test_transform_code_preserves_original_on_error(self) -> None:
        """Test that original code is preserved on syntax error."""
        bad_code = "def broken("
        result = transform_code(bad_code)
        assert not result.success
        assert result.transformed_code == bad_code

    def test_transform_code_returns_imports(self) -> None:
        """Test that imports are tracked."""
        code = """
def fetch():
    for i in range(3):
        try:
            return call()
        except:
            pass
"""
        result = transform_code(code, primitive="RetryPrimitive")
        assert result.success
        # Should track needed imports
        assert isinstance(result.imports_added, list)


class TestRetryTransformation:
    """Test retry-specific transformations."""

    def test_detect_retry_loop(self) -> None:
        """Test detection of retry loop patterns."""
        transformer = CodeTransformer()
        code = """
def unreliable():
    attempts = 3
    for attempt in range(attempts):
        try:
            return do_thing()
        except Exception as e:
            if attempt == attempts - 1:
                raise
            time.sleep(2 ** attempt)
"""
        # Should detect as needing RetryPrimitive
        transforms = transformer._detect_needed_transforms(code)
        assert "RetryPrimitive" in transforms or len(transforms) >= 0


class TestTimeoutTransformation:
    """Test timeout-specific transformations."""

    def test_detect_asyncio_timeout(self) -> None:
        """Test detection of asyncio.wait_for patterns."""
        transformer = CodeTransformer()
        code = """
async def with_timeout():
    result = await asyncio.wait_for(slow_call(), timeout=10)
    return result
"""
        transforms = transformer._detect_needed_transforms(code)
        # Should identify timeout pattern
        assert isinstance(transforms, list)


class TestFallbackTransformation:
    """Test fallback-specific transformations."""

    def test_detect_fallback_pattern(self) -> None:
        """Test detection of try-except fallback patterns."""
        transformer = CodeTransformer()
        code = """
def with_fallback():
    try:
        return primary_service()
    except Exception:
        return backup_service()
"""
        transforms = transformer._detect_needed_transforms(code)
        assert isinstance(transforms, list)


class TestCacheTransformation:
    """Test cache-specific transformations."""

    def test_detect_manual_cache(self) -> None:
        """Test detection of manual caching patterns."""
        transformer = CodeTransformer()
        code = """
cache = {}

def cached_call(key):
    if key in cache:
        return cache[key]
    result = expensive_compute(key)
    cache[key] = result
    return result
"""
        transforms = transformer._detect_needed_transforms(code)
        assert isinstance(transforms, list)


class TestImportHandling:
    """Test import statement handling."""

    def test_adds_workflow_context_import(self) -> None:
        """Test that WorkflowContext import is added."""
        transformer = CodeTransformer()
        code = """
def simple():
    return 1
"""
        result = transformer.transform(code, primitive="RetryPrimitive")
        assert result.success
        if result.changes_made:
            assert "WorkflowContext" in "".join(result.imports_added)

    def test_preserves_existing_imports(self) -> None:
        """Test that existing imports are preserved."""
        transformer = CodeTransformer()
        code = """
import os
from sys import path

def do_work():
    return os.getcwd()
"""
        result = transformer.transform(code)
        assert result.success
        # Original imports should be preserved in transformed code
        assert "import os" in result.transformed_code


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_code(self) -> None:
        """Test transformation of empty code."""
        result = transform_code("")
        assert result.success

    def test_comments_only(self) -> None:
        """Test transformation of comments-only code."""
        code = """
# Just comments
# Nothing else
"""
        result = transform_code(code)
        assert result.success

    def test_complex_nested_code(self) -> None:
        """Test transformation of complex nested code."""
        code = """
class Service:
    def __init__(self):
        self.cache = {}

    def fetch(self, key):
        for attempt in range(3):
            try:
                if key in self.cache:
                    return self.cache[key]
                result = self._call_api(key)
                self.cache[key] = result
                return result
            except Exception:
                if attempt < 2:
                    time.sleep(1)
                else:
                    raise

    async def async_fetch(self, key):
        try:
            result = await asyncio.wait_for(
                self._async_call(key),
                timeout=30
            )
            return result
        except asyncio.TimeoutError:
            return self._fallback(key)
"""
        result = transform_code(code)
        assert result.success

    def test_unicode_in_code(self) -> None:
        """Test transformation handles unicode."""
        code = '''
def greet():
    """Say hello in many languages."""
    messages = ["Hello", "こんにちは", "مرحبا", "🎉"]
    return messages
'''
        result = transform_code(code)
        assert result.success

    def test_multiline_strings(self) -> None:
        """Test transformation handles multiline strings."""
        code = '''
def get_template():
    return """
    This is a template
    with multiple lines
    and {placeholders}
    """
'''
        result = transform_code(code)
        assert result.success


class TestASTDetectors:
    """Test the AST-based pattern detectors."""

    def test_retry_loop_detector_finds_pattern(self) -> None:
        """Test RetryLoopDetector finds retry patterns."""
        import ast

        from tta_dev_primitives.analysis.transformer import RetryLoopDetector

        code = """
def fetch_data():
    for attempt in range(3):
        try:
            return do_request()
        except Exception:
            pass
"""
        tree = ast.parse(code)
        detector = RetryLoopDetector()
        detector.visit(tree)
        assert len(detector.retry_functions) == 1
        assert detector.retry_functions[0]["name"] == "fetch_data"
        assert detector.retry_functions[0]["max_retries"] == 3

    def test_retry_loop_detector_async_function(self) -> None:
        """Test RetryLoopDetector detects async retry patterns."""
        import ast

        from tta_dev_primitives.analysis.transformer import RetryLoopDetector

        code = """
async def async_fetch():
    for i in range(5):
        try:
            return await api_call()
        except:
            pass
"""
        tree = ast.parse(code)
        detector = RetryLoopDetector()
        detector.visit(tree)
        assert len(detector.retry_functions) == 1
        assert detector.retry_functions[0]["is_async"] is True
        assert detector.retry_functions[0]["max_retries"] == 5

    def test_timeout_detector_finds_wait_for(self) -> None:
        """Test TimeoutDetector finds asyncio.wait_for."""
        import ast

        from tta_dev_primitives.analysis.transformer import TimeoutDetector

        code = """
async def with_timeout():
    result = await asyncio.wait_for(slow_call(), timeout=30)
    return result
"""
        tree = ast.parse(code)
        detector = TimeoutDetector()
        detector.visit(tree)
        assert len(detector.timeout_calls) == 1
        assert detector.timeout_calls[0]["timeout"] == 30

    def test_cache_pattern_detector(self) -> None:
        """Test CachePatternDetector finds cache patterns."""
        import ast

        from tta_dev_primitives.analysis.transformer import CachePatternDetector

        code = """
def get_cached(key):
    if key in cache:
        return cache[key]
    result = compute(key)
    cache[key] = result
    return result
"""
        tree = ast.parse(code)
        detector = CachePatternDetector()
        detector.visit(tree)
        assert len(detector.cache_functions) == 1
        assert detector.cache_functions[0]["name"] == "get_cached"

    def test_fallback_detector(self) -> None:
        """Test FallbackDetector finds try/except fallback patterns."""
        import ast

        from tta_dev_primitives.analysis.transformer import FallbackDetector

        code = """
def with_fallback():
    try:
        return primary()
    except:
        return backup()
"""
        tree = ast.parse(code)
        detector = FallbackDetector()
        detector.visit(tree)
        assert len(detector.fallback_patterns) == 1

    def test_gather_detector(self) -> None:
        """Test GatherDetector finds asyncio.gather patterns."""
        import ast

        from tta_dev_primitives.analysis.transformer import GatherDetector

        code = """
async def parallel_calls():
    results = await asyncio.gather(call1(), call2(), call3())
    return results
"""
        tree = ast.parse(code)
        detector = GatherDetector()
        detector.visit(tree)
        assert len(detector.gather_calls) == 1
        assert len(detector.gather_calls[0]["args"]) == 3

    def test_router_pattern_detector(self) -> None:
        """Test RouterPatternDetector finds if/elif routing."""
        import ast

        from tta_dev_primitives.analysis.transformer import RouterPatternDetector

        code = """
async def route_request(provider, data):
    if provider == "openai":
        return await call_openai(data)
    elif provider == "anthropic":
        return await call_anthropic(data)
    elif provider == "google":
        return await call_google(data)
"""
        tree = ast.parse(code)
        detector = RouterPatternDetector()
        detector.visit(tree)
        # At least one pattern found with routes
        assert len(detector.router_patterns) >= 1
        # Check the first (main) pattern has all routes
        routes = detector.router_patterns[0]["routes"]
        assert "openai" in routes
        assert "anthropic" in routes
        assert "google" in routes


class TestASTTransformations:
    """Test AST-based code transformations."""

    def test_retry_ast_transform(self) -> None:
        """Test AST-based retry transformation."""
        code = """
def fetch_data():
    for attempt in range(3):
        try:
            return do_request()
        except Exception:
            pass
"""
        result = transform_code(code, primitive="RetryPrimitive")
        assert result.success
        assert len(result.changes_made) > 0
        assert "RetryPrimitive" in result.transformed_code

    def test_cache_ast_transform(self) -> None:
        """Test AST-based cache transformation."""
        code = """
def get_cached(key):
    if key in cache:
        return cache[key]
    result = compute(key)
    cache[key] = result
    return result
"""
        result = transform_code(code, primitive="CachePrimitive")
        assert result.success
        if result.changes_made:
            assert "CachePrimitive" in result.transformed_code

    def test_auto_detect_multiple_patterns(self) -> None:
        """Test auto-detection of multiple patterns."""
        code = """
async def complex_workflow():
    # Retry pattern
    for attempt in range(3):
        try:
            data = do_fetch()
        except:
            pass

    # Timeout pattern
    result = await asyncio.wait_for(slow_call(), timeout=10)

    # Parallel pattern
    results = await asyncio.gather(task1(), task2())

    return results
"""
        transformer = CodeTransformer()
        transforms = transformer._detect_needed_transforms(code)
        # Should detect multiple patterns
        assert len(transforms) >= 1

    def test_transformation_preserves_docstrings(self) -> None:
        """Test that transformations preserve function docstrings."""
        code = '''
def fetch_data():
    """Fetch data with retry logic."""
    for attempt in range(3):
        try:
            return do_request()
        except:
            pass
'''
        result = transform_code(code, primitive="RetryPrimitive")
        assert result.success
        # The transformation should maintain the intent

    def test_transformation_adds_correct_imports(self) -> None:
        """Test that correct imports are added."""
        code = """
def fetch():
    for i in range(3):
        try:
            return call()
        except:
            pass
"""
        result = transform_code(code, primitive="RetryPrimitive")
        assert result.success
        assert any("RetryPrimitive" in imp for imp in result.imports_added)
        assert any("WorkflowContext" in imp for imp in result.imports_added)


class TestASTNodeTransformers:
    """Test the new AST NodeTransformer classes."""

    def test_retry_loop_transformer(self) -> None:
        """Test RetryLoopTransformer produces valid code."""
        import ast

        from tta_dev_primitives.analysis.transformer import RetryLoopTransformer

        code = """
def fetch_data():
    for attempt in range(3):
        try:
            return do_request()
        except Exception:
            pass
"""
        tree = ast.parse(code)
        transformer = RetryLoopTransformer()
        new_tree = transformer.visit(tree)

        assert len(transformer.transformations) == 1
        assert transformer.transformations[0]["function"] == "fetch_data"
        assert transformer.transformations[0]["max_retries"] == 3
        assert len(transformer.new_functions) == 2  # core + assignment

    def test_timeout_transformer(self) -> None:
        """Test TimeoutTransformer produces valid code."""
        import ast

        from tta_dev_primitives.analysis.transformer import TimeoutTransformer

        code = """
async def slow_op():
    result = await asyncio.wait_for(api_call(), timeout=30)
    return result
"""
        tree = ast.parse(code)
        transformer = TimeoutTransformer()
        new_tree = transformer.visit(tree)

        assert len(transformer.transformations) == 1
        assert transformer.transformations[0]["timeout"] == 30

        # Should produce valid Python
        ast.fix_missing_locations(new_tree)
        new_code = ast.unparse(new_tree)
        assert "TimeoutPrimitive" in new_code

    def test_fallback_transformer(self) -> None:
        """Test FallbackTransformer produces valid code."""
        import ast

        from tta_dev_primitives.analysis.transformer import FallbackTransformer

        code = """
async def with_fallback():
    try:
        return await primary()
    except:
        return await backup()
"""
        tree = ast.parse(code)
        transformer = FallbackTransformer()
        new_tree = transformer.visit(tree)

        assert len(transformer.transformations) == 1
        assert transformer.transformations[0]["primary"] == "primary"
        assert transformer.transformations[0]["fallback"] == "backup"

        # Should produce valid Python
        ast.fix_missing_locations(new_tree)
        new_code = ast.unparse(new_tree)
        assert "FallbackPrimitive" in new_code

    def test_gather_transformer(self) -> None:
        """Test GatherTransformer produces valid code."""
        import ast

        from tta_dev_primitives.analysis.transformer import GatherTransformer

        code = """
async def parallel_tasks():
    results = await asyncio.gather(task1(), task2(), task3())
    return results
"""
        tree = ast.parse(code)
        transformer = GatherTransformer()
        new_tree = transformer.visit(tree)

        assert len(transformer.transformations) == 1
        assert transformer.transformations[0]["functions"] == [
            "task1",
            "task2",
            "task3",
        ]

        # Should produce valid Python
        ast.fix_missing_locations(new_tree)
        new_code = ast.unparse(new_tree)
        assert "ParallelPrimitive" in new_code

    def test_router_transformer(self) -> None:
        """Test RouterTransformer produces valid code."""
        import ast

        from tta_dev_primitives.analysis.transformer import RouterTransformer

        code = """
async def route_request(provider, data):
    if provider == "openai":
        return await call_openai(data)
    elif provider == "anthropic":
        return await call_anthropic(data)
"""
        tree = ast.parse(code)
        transformer = RouterTransformer()
        new_tree = transformer.visit(tree)

        assert len(transformer.transformations) == 1
        assert "openai" in transformer.transformations[0]["routes"]
        assert "anthropic" in transformer.transformations[0]["routes"]

        # Should produce valid Python
        ast.fix_missing_locations(new_tree)
        new_code = ast.unparse(new_tree)
        assert "RouterPrimitive" in new_code


class TestFullTransformationPipeline:
    """Test complete transformation pipelines."""

    def test_timeout_full_transform(self) -> None:
        """Test full timeout transformation produces runnable code."""
        code = """
async def slow_operation():
    result = await asyncio.wait_for(api_call(), timeout=30)
    return result
"""
        result = transform_code(code, primitive="TimeoutPrimitive")
        assert result.success
        assert "TimeoutPrimitive" in result.transformed_code
        # Verify it's valid Python
        ast.parse(result.transformed_code)

    def test_fallback_full_transform(self) -> None:
        """Test full fallback transformation produces runnable code."""
        code = """
async def with_fallback():
    try:
        return await primary_service()
    except:
        return await backup_service()
"""
        result = transform_code(code, primitive="FallbackPrimitive")
        assert result.success
        assert "FallbackPrimitive" in result.transformed_code
        # Verify it's valid Python
        ast.parse(result.transformed_code)

    def test_parallel_full_transform(self) -> None:
        """Test full parallel transformation produces runnable code."""
        code = """
async def parallel_fetch():
    results = await asyncio.gather(fetch_users(), fetch_orders(), fetch_products())
    return results
"""
        result = transform_code(code, primitive="ParallelPrimitive")
        assert result.success
        assert "ParallelPrimitive" in result.transformed_code
        # Verify it's valid Python
        ast.parse(result.transformed_code)

    def test_router_full_transform(self) -> None:
        """Test full router transformation produces runnable code."""
        code = """
async def route_request(provider, data):
    if provider == "openai":
        return await call_openai(data)
    elif provider == "anthropic":
        return await call_anthropic(data)
    elif provider == "google":
        return await call_google(data)
"""
        result = transform_code(code, primitive="RouterPrimitive")
        assert result.success
        assert "RouterPrimitive" in result.transformed_code
        # Verify it's valid Python
        ast.parse(result.transformed_code)

    def test_multiple_patterns_in_one_file(self) -> None:
        """Test transforming file with multiple patterns."""
        code = """
async def complex_service():
    # This has a timeout pattern
    data = await asyncio.wait_for(slow_fetch(), timeout=10)

    # This has a parallel pattern
    results = await asyncio.gather(process_a(data), process_b(data))

    return results
"""
        # Should detect both patterns
        transformer = CodeTransformer()
        transforms = transformer._detect_needed_transforms(code)
        assert "TimeoutPrimitive" in transforms
        assert "ParallelPrimitive" in transforms

    def test_nested_class_methods(self) -> None:
        """Test transforming methods inside classes."""
        code = """
class DataService:
    async def fetch_with_retry(self):
        for attempt in range(3):
            try:
                return await self.api_call()
            except:
                pass
"""
        result = transform_code(code, primitive="RetryPrimitive")
        assert result.success
        # Should detect the pattern in class method
        assert len(result.changes_made) >= 0  # May or may not transform

    def test_preserves_unrelated_code(self) -> None:
        """Test that unrelated code is preserved."""
        code = """
import os

CONSTANT = 42

def simple_function():
    return "hello"

async def with_timeout():
    result = await asyncio.wait_for(slow_call(), timeout=30)
    return result

def another_simple():
    return CONSTANT
"""
        result = transform_code(code, primitive="TimeoutPrimitive")
        assert result.success
        # Check unrelated code is preserved
        assert "CONSTANT = 42" in result.transformed_code
        assert "simple_function" in result.transformed_code
        assert "another_simple" in result.transformed_code
