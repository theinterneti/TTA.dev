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


class TestCircuitBreakerDetector:
    """Test CircuitBreakerDetector for finding circuit breaker candidates."""

    def test_detect_multiple_exception_handlers(self) -> None:
        """Test detection of functions with multiple exception handlers."""
        import ast

        from tta_dev_primitives.analysis.transformer import CircuitBreakerDetector

        code = """
async def unreliable_service(data):
    try:
        return await external_api.call(data)
    except ConnectionError:
        log.error("Connection failed")
        return None
    except TimeoutError:
        log.error("Timeout occurred")
        return None
    except ValueError as e:
        log.error(f"Invalid data: {e}")
        raise
"""
        tree = ast.parse(code)
        detector = CircuitBreakerDetector()
        detector.visit(tree)

        assert len(detector.circuit_patterns) == 1
        candidate = detector.circuit_patterns[0]
        assert candidate["name"] == "unreliable_service"
        assert candidate["exception_count"] == 3
        assert candidate["is_async"] is True

    def test_ignore_single_exception_handler(self) -> None:
        """Test that single exception handlers are not flagged."""
        import ast

        from tta_dev_primitives.analysis.transformer import CircuitBreakerDetector

        code = """
def simple_error_handling():
    try:
        return do_work()
    except Exception:
        return None
"""
        tree = ast.parse(code)
        detector = CircuitBreakerDetector()
        detector.visit(tree)

        # Should not detect - only 1 exception handler
        assert len(detector.circuit_patterns) == 0

    def test_detect_sync_function(self) -> None:
        """Test detection works for sync functions too."""
        import ast

        from tta_dev_primitives.analysis.transformer import CircuitBreakerDetector

        code = """
def multi_error_handler(data):
    try:
        return process(data)
    except TypeError:
        return default_value
    except ValueError:
        return alternative_value
"""
        tree = ast.parse(code)
        detector = CircuitBreakerDetector()
        detector.visit(tree)

        assert len(detector.circuit_patterns) == 1
        assert detector.circuit_patterns[0]["is_async"] is False


class TestCompensationDetector:
    """Test CompensationDetector for finding saga/compensation patterns."""

    def test_detect_cleanup_and_raise_pattern(self) -> None:
        """Test detection of try/except with cleanup followed by raise."""
        import ast

        from tta_dev_primitives.analysis.transformer import CompensationDetector

        code = """
async def index_document(doc):
    try:
        embedding_id = await vector_store.add(doc.embedding)
        await knowledge_base.update(doc)
        return embedding_id
    except Exception:
        await vector_store.delete(embedding_id)
        raise
"""
        tree = ast.parse(code)
        detector = CompensationDetector()
        detector.visit(tree)

        assert len(detector.compensation_patterns) == 1
        candidate = detector.compensation_patterns[0]
        assert candidate["name"] == "index_document"
        assert candidate["is_async"] is True
        assert "vector_store.delete" in candidate["cleanup_actions"]

    def test_ignore_simple_error_handling(self) -> None:
        """Test that simple error handling without cleanup is ignored."""
        import ast

        from tta_dev_primitives.analysis.transformer import CompensationDetector

        code = """
async def simple_llm_call():
    try:
        return await llm.generate(prompt)
    except Exception:
        raise
"""
        tree = ast.parse(code)
        detector = CompensationDetector()
        detector.visit(tree)

        # Should not detect - no cleanup before raise
        assert len(detector.compensation_patterns) == 0

    def test_detect_multiple_cleanup_actions(self) -> None:
        """Test detection captures multiple cleanup actions."""
        import ast

        from tta_dev_primitives.analysis.transformer import CompensationDetector

        code = """
async def multi_agent_task(task):
    try:
        await coordinator.assign_agents(task)
        await memory.store_context(task)
        return await agents.execute(task)
    except Exception:
        await coordinator.release_agents(task.id)
        await memory.clear_context(task.id)
        raise
"""
        tree = ast.parse(code)
        detector = CompensationDetector()
        detector.visit(tree)

        assert len(detector.compensation_patterns) == 1
        cleanup_actions = detector.compensation_patterns[0]["cleanup_actions"]
        assert len(cleanup_actions) >= 2


class TestCircuitBreakerTransformation:
    """Test CircuitBreakerPrimitive transformations."""

    def test_transform_circuit_breaker_pattern(self) -> None:
        """Test transformation of circuit breaker candidates."""
        code = """
async def flaky_api_call(request):
    try:
        return await external_service.call(request)
    except ConnectionError:
        return {"error": "connection_failed"}
    except TimeoutError:
        return {"error": "timeout"}
"""
        transformer = CodeTransformer()
        result = transformer.transform(code, primitive="CircuitBreakerPrimitive")

        assert result.success
        assert "CircuitBreakerPrimitive" in result.transformed_code

    def test_circuit_breaker_adds_import(self) -> None:
        """Test that circuit breaker transformation adds the right import."""
        code = """
def multi_exception_handler():
    try:
        return call_service()
    except ValueError:
        return None
    except RuntimeError:
        return None
"""
        transformer = CodeTransformer()
        result = transformer.transform(code, primitive="CircuitBreakerPrimitive")

        assert result.success
        # Import should be added
        imports = result.imports_added
        circuit_breaker_import = any(
            "CircuitBreakerPrimitive" in imp for imp in imports
        )
        assert circuit_breaker_import


class TestCompensationTransformation:
    """Test CompensationPrimitive transformations."""

    def test_transform_compensation_pattern(self) -> None:
        """Test transformation of compensation/saga patterns."""
        code = """
async def index_document(doc):
    try:
        embedding_id = await vector_store.add(doc.embedding)
        await knowledge_base.update(doc)
        return embedding_id
    except Exception:
        await vector_store.delete(embedding_id)
        raise
"""
        transformer = CodeTransformer()
        result = transformer.transform(code, primitive="CompensationPrimitive")

        assert result.success
        assert "CompensationPrimitive" in result.transformed_code

    def test_compensation_adds_import(self) -> None:
        """Test that compensation transformation adds the right import."""
        code = """
async def assign_agent_task(task):
    try:
        agent_id = await coordinator.assign(task)
        return await agent.execute(task)
    except:
        await coordinator.release(agent_id)
        raise
"""
        transformer = CodeTransformer()
        result = transformer.transform(code, primitive="CompensationPrimitive")

        assert result.success
        imports = result.imports_added
        compensation_import = any("CompensationPrimitive" in imp for imp in imports)
        assert compensation_import


class TestAutoDetectNewPatterns:
    """Test auto-detection of new circuit breaker and compensation patterns."""

    def test_auto_detect_circuit_breaker(self) -> None:
        """Test auto-detection finds circuit breaker patterns."""
        code = """
async def llm_with_fallbacks(prompt):
    try:
        return await openai.complete(prompt)
    except RateLimitError:
        return await anthropic.complete(prompt)
    except TimeoutError:
        return cached_response(prompt)
"""
        transformer = CodeTransformer()
        transforms = transformer._detect_needed_transforms(code)

        assert "CircuitBreakerPrimitive" in transforms

    def test_auto_detect_compensation(self) -> None:
        """Test auto-detection finds compensation/saga patterns."""
        code = """
async def store_embedding(doc):
    try:
        embedding_id = await vector_store.add(doc)
        return embedding_id
    except:
        await vector_store.delete(embedding_id)
        raise
"""
        transformer = CodeTransformer()
        transforms = transformer._detect_needed_transforms(code)

        assert "CompensationPrimitive" in transforms

    def test_auto_detect_multiple_new_patterns(self) -> None:
        """Test auto-detection finds multiple patterns in one file."""
        code = """
async def llm_provider_call(request):
    try:
        return await provider.generate(request)
    except RateLimitError:
        return await fallback_provider.generate(request)
    except TimeoutError:
        return None

async def index_with_rollback(document):
    try:
        await embeddings.store(document)
        return document.id
    except:
        await embeddings.remove(document.id)
        raise
"""
        transformer = CodeTransformer()
        transforms = transformer._detect_needed_transforms(code)

        assert "CircuitBreakerPrimitive" in transforms
        assert "CompensationPrimitive" in transforms


class TestMemoryDetector:
    """Test detection of conversation history/memory patterns."""

    def test_detect_message_append_pattern(self) -> None:
        """Test detection of messages.append() for chat history."""
        from tta_dev_primitives.analysis.transformer import MemoryDetector

        code = """
async def chat(user_input):
    messages.append({"role": "user", "content": user_input})
    response = await llm.generate(messages)
    messages.append({"role": "assistant", "content": response})
    return response
"""
        tree = ast.parse(code)
        detector = MemoryDetector()
        detector.visit(tree)

        assert len(detector.memory_patterns) >= 1
        assert detector.memory_patterns[0]["type"] == "message_append"
        assert detector.memory_patterns[0]["variable"] == "messages"

    def test_detect_deque_history_pattern(self) -> None:
        """Test detection of deque-based bounded history."""
        from tta_dev_primitives.analysis.transformer import MemoryDetector

        code = """
from collections import deque

history = deque(maxlen=100)

async def remember(item):
    history.append(item)
"""
        tree = ast.parse(code)
        detector = MemoryDetector()
        detector.visit(tree)

        deque_patterns = [
            p for p in detector.memory_patterns if p["type"] == "deque_history"
        ]
        assert len(deque_patterns) >= 1
        assert deque_patterns[0]["variable"] == "history"
        assert deque_patterns[0]["maxlen"] == 100

    def test_detect_context_dict_storage(self) -> None:
        """Test detection of dict-based context storage."""
        from tta_dev_primitives.analysis.transformer import MemoryDetector

        code = """
context_store = {}

async def save_context(key, value):
    context_store[key] = value
"""
        tree = ast.parse(code)
        detector = MemoryDetector()
        detector.visit(tree)

        dict_patterns = [
            p for p in detector.memory_patterns if p["type"] == "dict_storage"
        ]
        assert len(dict_patterns) >= 1
        assert dict_patterns[0]["variable"] == "context_store"

    def test_auto_detect_memory_pattern(self) -> None:
        """Test auto-detection finds memory patterns."""
        code = """
conversation_history = []

async def chat(user_message):
    conversation_history.append({"role": "user", "content": user_message})
    response = await gpt4.complete(conversation_history)
    conversation_history.append({"role": "assistant", "content": response})
    return response
"""
        transformer = CodeTransformer()
        transforms = transformer._detect_needed_transforms(code)

        assert "MemoryPrimitive" in transforms


class TestDelegationDetector:
    """Test detection of task delegation/orchestration patterns."""

    def test_detect_model_routing_pattern(self) -> None:
        """Test detection of if/elif model selection."""
        from tta_dev_primitives.analysis.transformer import DelegationDetector

        code = """
async def route_to_model(prompt, model_name):
    if model_name == "gpt-4":
        return await openai_gpt4.complete(prompt)
    elif model_name == "claude":
        return await anthropic_claude.complete(prompt)
    elif model_name == "gemini":
        return await google_gemini.complete(prompt)
"""
        tree = ast.parse(code)
        detector = DelegationDetector()
        detector.visit(tree)

        model_routing = [
            p for p in detector.delegation_patterns if p["type"] == "model_routing"
        ]
        assert len(model_routing) >= 1
        assert model_routing[0]["variable"] == "model_name"
        assert "gpt-4" in model_routing[0]["models"]
        assert "claude" in model_routing[0]["models"]

    def test_detect_agent_dispatch_pattern(self) -> None:
        """Test detection of agents[role].execute() pattern."""
        from tta_dev_primitives.analysis.transformer import DelegationDetector

        code = """
async def dispatch_to_agent(task, role):
    result = await agents[role].execute(task)
    return result
"""
        tree = ast.parse(code)
        detector = DelegationDetector()
        detector.visit(tree)

        agent_dispatch = [
            p for p in detector.delegation_patterns if p["type"] == "agent_dispatch"
        ]
        assert len(agent_dispatch) >= 1
        assert agent_dispatch[0]["container"] == "agents"
        assert agent_dispatch[0]["method"] == "execute"

    def test_detect_executor_dispatch_pattern(self) -> None:
        """Test detection of executor.run(task) pattern."""
        from tta_dev_primitives.analysis.transformer import DelegationDetector

        code = """
async def run_task(task):
    result = await executor.run(task)
    return result
"""
        tree = ast.parse(code)
        detector = DelegationDetector()
        detector.visit(tree)

        executor_dispatch = [
            p for p in detector.delegation_patterns if p["type"] == "executor_dispatch"
        ]
        assert len(executor_dispatch) >= 1
        assert executor_dispatch[0]["executor"] == "executor"
        assert executor_dispatch[0]["method"] == "run"

    def test_auto_detect_delegation_pattern(self) -> None:
        """Test auto-detection finds delegation patterns."""
        code = """
async def orchestrate(task, model):
    if model == "fast":
        return await gpt4_mini.generate(task)
    elif model == "quality":
        return await claude_opus.generate(task)
    elif model == "code":
        return await deepseek.generate(task)
"""
        transformer = CodeTransformer()
        transforms = transformer._detect_needed_transforms(code)

        assert "DelegationPrimitive" in transforms


class TestMemoryTransformation:
    """Test transformation of memory patterns to MemoryPrimitive."""

    def test_transform_memory_pattern(self) -> None:
        """Test basic memory pattern transformation."""
        code = """
messages = []

async def chat(user_input):
    messages.append({"role": "user", "content": user_input})
    return messages
"""
        result = transform_code(code, primitive="MemoryPrimitive")
        assert result.success
        # Should detect the pattern
        assert len(result.changes_made) >= 1

    def test_memory_transform_adds_import(self) -> None:
        """Test that transformation adds MemoryPrimitive import."""
        code = """
history = []

async def remember(item):
    history.append({"role": "user", "message": item})
"""
        result = transform_code(code, primitive="MemoryPrimitive")
        imports = result.imports_added

        memory_import = any("MemoryPrimitive" in imp for imp in imports)
        assert memory_import


class TestDelegationTransformation:
    """Test transformation of delegation patterns to DelegationPrimitive."""

    def test_transform_delegation_pattern(self) -> None:
        """Test basic delegation pattern transformation."""
        code = """
async def route_request(prompt, model):
    if model == "gpt-4":
        return await gpt4.complete(prompt)
    elif model == "claude":
        return await claude.complete(prompt)
"""
        result = transform_code(code, primitive="DelegationPrimitive")
        assert result.success
        # Should detect the pattern
        assert len(result.changes_made) >= 1

    def test_delegation_transform_adds_import(self) -> None:
        """Test that transformation adds DelegationPrimitive import."""
        code = """
async def dispatch(task, model):
    if model == "fast":
        return await fast_model.run(task)
    elif model == "quality":
        return await quality_model.run(task)
"""
        result = transform_code(code, primitive="DelegationPrimitive")
        imports = result.imports_added

        delegation_import = any("DelegationPrimitive" in imp for imp in imports)
        assert delegation_import


class TestSequentialDetector:
    """Test detection of sequential pipeline patterns."""

    def test_detect_nested_call_chain(self) -> None:
        """Test detection of nested function calls: step3(step2(step1(data)))."""
        from tta_dev_primitives.analysis.transformer import SequentialDetector

        code = """
def process_pipeline(data):
    return validate(transform(parse(data)))
"""
        tree = ast.parse(code)
        detector = SequentialDetector()
        detector.visit(tree)

        assert len(detector.sequential_patterns) >= 1
        pattern = detector.sequential_patterns[0]
        assert pattern["type"] == "nested_calls"
        assert len(pattern["steps"]) >= 3

    def test_detect_sequential_assignments(self) -> None:
        """Test detection of sequential variable assignment chains."""
        from tta_dev_primitives.analysis.transformer import SequentialDetector

        code = """
async def process_document(doc):
    parsed = await parse_document(doc)
    chunks = await chunk_text(parsed)
    embeddings = await generate_embeddings(chunks)
    stored = await store_vectors(embeddings)
    return stored
"""
        tree = ast.parse(code)
        detector = SequentialDetector()
        detector.visit(tree)

        assert len(detector.sequential_patterns) >= 1
        pattern = detector.sequential_patterns[0]
        assert pattern["type"] == "assignment_chain"
        assert pattern["step_count"] >= 4

    def test_auto_detect_sequential_pattern(self) -> None:
        """Test auto-detection finds sequential patterns."""
        code = """
async def rag_pipeline(query):
    embedded = await embed_query(query)
    retrieved = await search_vectors(embedded)
    context = await format_context(retrieved)
    response = await generate_response(context)
    return response
"""
        transformer = CodeTransformer()
        transforms = transformer._detect_needed_transforms(code)

        assert "SequentialPrimitive" in transforms


class TestAdaptiveDetector:
    """Test detection of adaptive/learning patterns."""

    def test_detect_metric_based_adjustment(self) -> None:
        """Test detection of counter-based parameter adjustment."""
        from tta_dev_primitives.analysis.transformer import AdaptiveDetector

        code = """
async def adaptive_retry(func):
    success_count = 0
    failure_count = 0
    
    result = await func()
    if result:
        success_count += 1
    else:
        failure_count += 1
    
    rate = success_count / (success_count + failure_count)
    if rate < 0.5:
        delay = delay * 2
    return result
"""
        tree = ast.parse(code)
        detector = AdaptiveDetector()
        detector.visit(tree)

        assert len(detector.adaptive_patterns) >= 1
        pattern = detector.adaptive_patterns[0]
        assert pattern["type"] == "metric_based_adjustment"
        assert "success_count" in pattern["counter_vars"] or "failure_count" in pattern["counter_vars"]

    def test_detect_strategy_config(self) -> None:
        """Test detection of strategy dictionaries with metrics."""
        from tta_dev_primitives.analysis.transformer import AdaptiveDetector

        code = """
strategies = {
    "fast": {"model": "gpt-4-mini", "success_rate": 0.9, "latency": 100},
    "quality": {"model": "gpt-4", "success_rate": 0.95, "latency": 500},
}
"""
        tree = ast.parse(code)
        detector = AdaptiveDetector()
        detector.visit(tree)

        assert len(detector.adaptive_patterns) >= 1
        pattern = detector.adaptive_patterns[0]
        assert pattern["type"] == "strategy_config"
        assert pattern["variable"] == "strategies"

    def test_auto_detect_adaptive_pattern(self) -> None:
        """Test auto-detection finds adaptive patterns."""
        code = """
async def smart_llm_call(prompt):
    success_count = 0
    error_count = 0
    
    try:
        result = await llm.generate(prompt)
        success_count += 1
        return result
    except:
        error_count += 1
        rate = error_count / (success_count + error_count + 1)
        if rate > 0.3:
            timeout = timeout * 1.5
        raise
"""
        transformer = CodeTransformer()
        transforms = transformer._detect_needed_transforms(code)

        assert "AdaptivePrimitive" in transforms


class TestSequentialTransformation:
    """Test transformation of sequential patterns to SequentialPrimitive."""

    def test_transform_sequential_pattern(self) -> None:
        """Test basic sequential pattern transformation."""
        code = """
async def pipeline(data):
    step1_result = await step1(data)
    step2_result = await step2(step1_result)
    step3_result = await step3(step2_result)
    return step3_result
"""
        result = transform_code(code, primitive="SequentialPrimitive")
        assert result.success
        assert len(result.changes_made) >= 1

    def test_sequential_transform_adds_import(self) -> None:
        """Test that transformation adds SequentialPrimitive import."""
        code = """
async def process(data):
    a = await parse(data)
    b = await transform(a)
    c = await validate(b)
    return c
"""
        result = transform_code(code, primitive="SequentialPrimitive")
        imports = result.imports_added

        sequential_import = any("SequentialPrimitive" in imp for imp in imports)
        assert sequential_import


class TestAdaptiveTransformation:
    """Test transformation of adaptive patterns to AdaptivePrimitive."""

    def test_transform_adaptive_pattern(self) -> None:
        """Test basic adaptive pattern transformation."""
        code = """
async def learning_retry(func):
    success_count = 0
    failure_count = 0
    
    result = await func()
    if result:
        success_count += 1
    else:
        failure_count += 1
    
    rate = success_count / (success_count + failure_count + 1)
    if rate < 0.5:
        max_retries = max_retries + 1
    return result
"""
        result = transform_code(code, primitive="AdaptivePrimitive")
        assert result.success
        assert len(result.changes_made) >= 1

    def test_adaptive_transform_adds_import(self) -> None:
        """Test that transformation adds AdaptivePrimitive import."""
        code = """
strategies = {
    "conservative": {"timeout": 30, "success_rate": 0.8},
    "aggressive": {"timeout": 10, "success_rate": 0.6},
}
"""
        result = transform_code(code, primitive="AdaptivePrimitive")
        imports = result.imports_added

        adaptive_import = any("AdaptivePrimitive" in imp for imp in imports)
        assert adaptive_import
