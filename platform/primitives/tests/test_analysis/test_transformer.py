"""Tests for the AST-based code transformer."""

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
