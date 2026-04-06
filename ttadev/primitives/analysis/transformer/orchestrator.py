"""CodeTransformer orchestrator and transform_code entry point."""

import ast
import re
from typing import Any

from ttadev.primitives.analysis.transformer.ast_detectors import (
    CachePatternDetector,
    CircuitBreakerDetector,
    CompensationDetector,
    FallbackDetector,
    GatherDetector,
    RetryLoopDetector,
    RouterPatternDetector,
    TimeoutDetector,
)
from ttadev.primitives.analysis.transformer.ast_detectors_advanced import (
    AdaptiveDetector,
    DelegationDetector,
    MemoryDetector,
    SequentialDetector,
)
from ttadev.primitives.analysis.transformer.ast_transformers import (
    FallbackTransformer,
    GatherTransformer,
    RetryLoopTransformer,
    TimeoutTransformer,
)
from ttadev.primitives.analysis.transformer.ast_transformers_advanced import (
    RouterTransformer,
)
from ttadev.primitives.analysis.transformer.ast_transformers_resilience import (
    CircuitBreakerTransformer,
    CompensationTransformer,
)
from ttadev.primitives.analysis.transformer.base import TransformResult


class CodeTransformer:
    """AST-based code transformer for TTA.dev primitives.

    Transforms manual implementations into proper primitive usage:
    - Manual retry loops → RetryPrimitive
    - Manual timeout handling → TimeoutPrimitive
    - Manual fallback logic → FallbackPrimitive
    - etc.
    """

    def __init__(self) -> None:
        """Initialize the transformer."""
        self._import_map = {
            "RetryPrimitive": "from ttadev.primitives.recovery import RetryPrimitive",
            "TimeoutPrimitive": "from ttadev.primitives.recovery import TimeoutPrimitive",
            "FallbackPrimitive": "from ttadev.primitives.recovery import FallbackPrimitive",
            "CachePrimitive": "from ttadev.primitives.performance import CachePrimitive",
            "ParallelPrimitive": "from primitives import ParallelPrimitive",
            "SequentialPrimitive": "from primitives import SequentialPrimitive",
            "RouterPrimitive": "from ttadev.primitives.core import RouterPrimitive",
            "CircuitBreakerPrimitive": "from ttadev.primitives.recovery import CircuitBreakerPrimitive",
            "CompensationPrimitive": "from ttadev.primitives.recovery import CompensationPrimitive",
            "MemoryPrimitive": "from ttadev.primitives.performance import MemoryPrimitive",
            "DelegationPrimitive": "from ttadev.primitives.orchestration import DelegationPrimitive",
            "AdaptivePrimitive": "from ttadev.primitives.adaptive import AdaptivePrimitive",
        }

    def transform(
        self,
        code: str,
        primitive: str | None = None,
        auto_detect: bool = True,
    ) -> TransformResult:
        """Transform code to use TTA.dev primitives.

        Args:
            code: Source code to transform
            primitive: Specific primitive to apply (optional)
            auto_detect: Auto-detect anti-patterns if no primitive specified

        Returns:
            TransformResult with transformed code and metadata
        """
        try:
            ast.parse(code)
        except SyntaxError as e:
            return TransformResult(
                original_code=code,
                transformed_code=code,
                changes_made=[],
                imports_added=[],
                success=False,
                error=f"Syntax error: {e}",
            )

        changes_made = []
        imports_needed = set()
        imports_needed.add("from primitives import WorkflowContext")

        # Determine which transformations to apply
        if primitive:
            transforms = [primitive]
        elif auto_detect:
            transforms = self._detect_needed_transforms(code)
        else:
            transforms = []

        # Apply transformations
        transformed_code = code
        for transform_type in transforms:
            result = self._apply_transform(transformed_code, transform_type)
            if result["changed"]:
                transformed_code = result["code"]
                changes_made.extend(result["changes"])
                if transform_type in self._import_map:
                    imports_needed.add(self._import_map[transform_type])

        # Add imports
        if changes_made:
            transformed_code = self._add_imports(transformed_code, list(imports_needed))

        return TransformResult(
            original_code=code,
            transformed_code=transformed_code,
            changes_made=changes_made,
            imports_added=list(imports_needed),
            success=True,
        )

    def _detect_needed_transforms(self, code: str) -> list[str]:
        """Detect which transformations are needed using AST analysis."""
        transforms = []

        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Fall back to regex detection on syntax errors
            return self._detect_needed_transforms_regex(code)

        # Use AST-based detectors
        retry_detector = RetryLoopDetector()
        retry_detector.visit(tree)
        if retry_detector.retry_functions:
            transforms.append("RetryPrimitive")

        timeout_detector = TimeoutDetector()
        timeout_detector.visit(tree)
        if timeout_detector.timeout_calls:
            transforms.append("TimeoutPrimitive")

        cache_detector = CachePatternDetector()
        cache_detector.visit(tree)
        if cache_detector.cache_functions:
            transforms.append("CachePrimitive")

        fallback_detector = FallbackDetector()
        fallback_detector.visit(tree)
        if fallback_detector.fallback_patterns:
            transforms.append("FallbackPrimitive")

        gather_detector = GatherDetector()
        gather_detector.visit(tree)
        if gather_detector.gather_calls:
            transforms.append("ParallelPrimitive")

        router_detector = RouterPatternDetector()
        router_detector.visit(tree)
        if router_detector.router_patterns:
            transforms.append("RouterPrimitive")

        # New detectors
        circuit_detector = CircuitBreakerDetector()
        circuit_detector.visit(tree)
        if circuit_detector.circuit_patterns:
            transforms.append("CircuitBreakerPrimitive")

        compensation_detector = CompensationDetector()
        compensation_detector.visit(tree)
        if compensation_detector.compensation_patterns:
            transforms.append("CompensationPrimitive")

        memory_detector = MemoryDetector()
        memory_detector.visit(tree)
        if memory_detector.memory_patterns:
            transforms.append("MemoryPrimitive")

        delegation_detector = DelegationDetector()
        delegation_detector.visit(tree)
        if delegation_detector.delegation_patterns:
            transforms.append("DelegationPrimitive")

        sequential_detector = SequentialDetector()
        sequential_detector.visit(tree)
        if sequential_detector.sequential_patterns:
            transforms.append("SequentialPrimitive")

        adaptive_detector = AdaptiveDetector()
        adaptive_detector.visit(tree)
        if adaptive_detector.adaptive_patterns:
            transforms.append("AdaptivePrimitive")

        return transforms

    def _detect_needed_transforms_regex(self, code: str) -> list[str]:
        """Fallback regex-based detection for when AST parsing fails."""
        transforms = []

        # Check for manual retry
        if re.search(r"for\s+\w+\s+in\s+range\s*\(\s*\d+\s*\)", code):
            if re.search(r"try:|except", code):
                transforms.append("RetryPrimitive")

        # Check for manual timeout
        if re.search(r"asyncio\.wait_for\s*\(", code):
            transforms.append("TimeoutPrimitive")

        # Check for manual fallback
        if re.search(r"except\s*:?\s*\n\s*return\s+", code):
            transforms.append("FallbackPrimitive")

        # Check for manual parallel
        if re.search(r"asyncio\.gather\s*\(", code):
            transforms.append("ParallelPrimitive")

        # Check for manual routing
        if re.search(r"if\s+\w+\s*==\s*['\"].*['\"]\s*:\s*\n.*elif", code, re.DOTALL):
            transforms.append("RouterPrimitive")

        return transforms

    def _apply_transform(self, code: str, transform_type: str) -> dict[str, Any]:
        """Apply a specific transformation to the code using AST."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Fall back to regex transforms
            return self._apply_transform_regex(code, transform_type)

        if transform_type == "RetryPrimitive":
            return self._transform_retry_ast(code, tree)
        elif transform_type == "TimeoutPrimitive":
            return self._transform_timeout_ast(code, tree)
        elif transform_type == "FallbackPrimitive":
            return self._transform_fallback_ast(code, tree)
        elif transform_type == "ParallelPrimitive":
            return self._transform_parallel_ast(code, tree)
        elif transform_type == "RouterPrimitive":
            return self._transform_router_ast(code, tree)
        elif transform_type == "CachePrimitive":
            return self._transform_cache_ast(code, tree)
        elif transform_type == "CircuitBreakerPrimitive":
            return self._transform_circuit_breaker_ast(code, tree)
        elif transform_type == "CompensationPrimitive":
            return self._transform_compensation_ast(code, tree)
        elif transform_type == "MemoryPrimitive":
            return self._transform_memory_ast(code, tree)
        elif transform_type == "DelegationPrimitive":
            return self._transform_delegation_ast(code, tree)
        elif transform_type == "SequentialPrimitive":
            return self._transform_sequential_ast(code, tree)
        elif transform_type == "AdaptivePrimitive":
            return self._transform_adaptive_ast(code, tree)
        else:
            return {"changed": False, "code": code, "changes": []}

    def _apply_transform_regex(self, code: str, transform_type: str) -> dict[str, Any]:
        """Fallback regex-based transformations."""
        if transform_type == "RetryPrimitive":
            return self._transform_retry_regex(code)
        elif transform_type == "TimeoutPrimitive":
            return self._transform_timeout_regex(code)
        elif transform_type == "FallbackPrimitive":
            return self._transform_fallback_regex(code)
        elif transform_type == "ParallelPrimitive":
            return self._transform_parallel_regex(code)
        elif transform_type == "RouterPrimitive":
            return self._transform_router_regex(code)
        else:
            return {"changed": False, "code": code, "changes": []}

    def _transform_retry_ast(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Transform retry loops using full AST rewriting."""
        # Use the new RetryLoopTransformer for full AST rewrite
        transformer = RetryLoopTransformer()
        new_tree = transformer.visit(tree)

        if not transformer.transformations:
            return {"changed": False, "code": code, "changes": []}

        # Filter out None values (removed functions) and add new ones
        new_tree.body = [
            node for node in new_tree.body if node is not None
        ] + transformer.new_functions

        ast.fix_missing_locations(new_tree)

        try:
            new_code = ast.unparse(new_tree)
        except Exception:
            # Fall back to line-based replacement if unparse fails
            return self._transform_retry_ast_fallback(code, tree)

        return {
            "changed": True,
            "code": new_code,
            "changes": transformer.transformations,
        }

    def _transform_retry_ast_fallback(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Fallback retry transformation using line-based replacement."""
        changes = []
        detector = RetryLoopDetector()
        detector.visit(tree)

        if not detector.retry_functions:
            return {"changed": False, "code": code, "changes": []}

        lines = code.split("\n")
        transformed_lines = lines.copy()
        offset = 0

        for func_info in detector.retry_functions:
            func_name = func_info["name"]
            is_async = func_info["is_async"]
            max_retries = func_info["max_retries"]
            lineno = func_info["lineno"]
            func_node = func_info["node"]

            # Find function start and end
            func_start = lineno - 1
            func_end = self._find_function_end(lines, func_start)

            # Extract the core operation from the try block
            try_node = func_info["try_node"]
            core_body = self._extract_try_body(try_node)

            # Generate new function code
            new_func = self._generate_retry_function_ast(
                func_name, func_node, core_body, max_retries, is_async
            )

            # Replace function
            new_lines = new_func.split("\n")
            transformed_lines = (
                transformed_lines[: func_start + offset]
                + new_lines
                + transformed_lines[func_end + 1 + offset :]
            )
            offset += len(new_lines) - (func_end - func_start + 1)

            changes.append(
                {
                    "type": "retry_transform",
                    "function": func_name,
                    "max_retries": max_retries,
                    "line": lineno,
                    "transformation": "AST-based rewrite",
                }
            )

        return {
            "changed": True,
            "code": "\n".join(transformed_lines),
            "changes": changes,
        }

    def _transform_timeout_ast(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Transform timeout patterns using full AST rewriting."""
        transformer = TimeoutTransformer()
        new_tree = transformer.visit(tree)

        if not transformer.transformations:
            return {"changed": False, "code": code, "changes": []}

        ast.fix_missing_locations(new_tree)

        try:
            new_code = ast.unparse(new_tree)
        except Exception:
            # Fall back to regex
            return self._transform_timeout_regex(code)

        return {
            "changed": True,
            "code": new_code,
            "changes": transformer.transformations,
        }

    def _transform_fallback_ast(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Transform fallback patterns using full AST rewriting."""
        transformer = FallbackTransformer()
        new_tree = transformer.visit(tree)

        if not transformer.transformations:
            return {"changed": False, "code": code, "changes": []}

        ast.fix_missing_locations(new_tree)

        try:
            new_code = ast.unparse(new_tree)
        except Exception:
            return self._transform_fallback_regex(code)

        return {
            "changed": True,
            "code": new_code,
            "changes": transformer.transformations,
        }

    def _transform_parallel_ast(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Transform parallel patterns using full AST rewriting."""
        transformer = GatherTransformer()
        new_tree = transformer.visit(tree)

        if not transformer.transformations:
            return {"changed": False, "code": code, "changes": []}

        ast.fix_missing_locations(new_tree)

        try:
            new_code = ast.unparse(new_tree)
        except Exception:
            return self._transform_parallel_regex(code)

        return {
            "changed": True,
            "code": new_code,
            "changes": transformer.transformations,
        }

    def _transform_router_ast(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Transform router patterns using full AST rewriting."""
        transformer = RouterTransformer()
        new_tree = transformer.visit(tree)

        if not transformer.transformations:
            return {"changed": False, "code": code, "changes": []}

        ast.fix_missing_locations(new_tree)

        try:
            new_code = ast.unparse(new_tree)
        except Exception:
            return self._transform_router_regex(code)

        return {
            "changed": True,
            "code": new_code,
            "changes": transformer.transformations,
        }

    def _transform_router_ast_fallback(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Fallback router transformation using line-based replacement."""
        changes = []
        detector = RouterPatternDetector()
        detector.visit(tree)

        if not detector.router_patterns:
            return {"changed": False, "code": code, "changes": []}

        lines = code.split("\n")
        transformed_lines = lines.copy()
        offset = 0

        for pattern_info in detector.router_patterns:
            routes = pattern_info["routes"]
            lineno = pattern_info["lineno"]

            if len(routes) < 2:
                continue

            # Find the if/elif block
            if_start = lineno - 1
            if_end = self._find_if_block_end(lines, if_start)

            # Generate router code
            router_code = self._generate_router_code(routes)

            # Replace block
            new_lines = router_code.split("\n")
            transformed_lines = (
                transformed_lines[: if_start + offset]
                + new_lines
                + transformed_lines[if_end + 1 + offset :]
            )
            offset += len(new_lines) - (if_end - if_start + 1)

            changes.append(
                {
                    "type": "router_transform",
                    "routes": list(routes.keys()),
                    "line": lineno,
                    "transformation": "AST-based rewrite",
                }
            )

        return {
            "changed": bool(changes),
            "code": "\n".join(transformed_lines),
            "changes": changes,
        }

    def _transform_cache_ast(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Transform cache patterns using AST analysis."""
        changes = []
        detector = CachePatternDetector()
        detector.visit(tree)

        if not detector.cache_functions:
            return {"changed": False, "code": code, "changes": []}

        lines = code.split("\n")
        transformed_lines = lines.copy()
        offset = 0

        for func_info in detector.cache_functions:
            func_name = func_info["name"]
            is_async = func_info["is_async"]
            lineno = func_info["lineno"]

            # Find function start and end
            func_start = lineno - 1
            func_end = self._find_function_end(lines, func_start)

            # Generate cached version
            cache_code = self._generate_cache_wrapper(func_name, is_async)

            # Replace function
            new_lines = cache_code.split("\n")
            transformed_lines = (
                transformed_lines[: func_start + offset]
                + new_lines
                + transformed_lines[func_end + 1 + offset :]
            )
            offset += len(new_lines) - (func_end - func_start + 1)

            changes.append(
                {
                    "type": "cache_transform",
                    "function": func_name,
                    "line": lineno,
                    "transformation": "AST-based rewrite",
                }
            )

        return {
            "changed": bool(changes),
            "code": "\n".join(transformed_lines),
            "changes": changes,
        }

    def _find_function_end(self, lines: list[str], start: int) -> int:
        """Find the end line of a function definition."""
        if start >= len(lines):
            return start

        # Get indentation of function def
        func_line = lines[start]
        base_indent = len(func_line) - len(func_line.lstrip())

        for i in range(start + 1, len(lines)):
            line = lines[i]
            if not line.strip():  # Empty line
                continue
            if line.strip().startswith("#"):  # Comment
                continue

            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent and line.strip():
                return i - 1

        return len(lines) - 1

    def _find_if_block_end(self, lines: list[str], start: int) -> int:
        """Find the end line of an if/elif/else block."""
        if start >= len(lines):
            return start

        base_indent = len(lines[start]) - len(lines[start].lstrip())

        for i in range(start + 1, len(lines)):
            line = lines[i]
            if not line.strip():
                continue

            current_indent = len(line) - len(line.lstrip())

            # Check if we're still in the if block (elif/else at same indent)
            if current_indent == base_indent:
                stripped = line.strip()
                if stripped.startswith("elif ") or stripped.startswith("else:"):
                    continue
                else:
                    return i - 1
            elif current_indent < base_indent:
                return i - 1

        return len(lines) - 1

    def _extract_try_body(self, try_node: ast.Try) -> str:
        """Extract the body of a try block as source code."""
        # For now, return a placeholder - in real impl would use ast.unparse
        body_parts = []
        for stmt in try_node.body:
            if isinstance(stmt, ast.Return):
                if isinstance(stmt.value, ast.Await):
                    if isinstance(stmt.value.value, ast.Call):
                        func = stmt.value.value.func
                        if isinstance(func, ast.Name):
                            body_parts.append(f"return await {func.id}(data)")
                        elif isinstance(func, ast.Attribute):
                            body_parts.append(f"return await {func.attr}(data)")
                elif isinstance(stmt.value, ast.Call):
                    func = stmt.value.func
                    if isinstance(func, ast.Name):
                        body_parts.append(f"return {func.id}(data)")
        return "\n    ".join(body_parts) if body_parts else "pass"

    def _generate_retry_function_ast(
        self,
        func_name: str,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
        core_body: str,
        max_retries: int,
        is_async: bool,
    ) -> str:
        """Generate a RetryPrimitive-wrapped function."""
        async_kw = "async " if is_async else ""
        await_kw = "await " if is_async else ""

        # Extract original args
        args_str = "data: dict, context: WorkflowContext"

        return f'''
{async_kw}def {func_name}_core({args_str}):
    """Core operation wrapped by RetryPrimitive."""
    {core_body}


# Wrap with RetryPrimitive for automatic retry handling
{func_name} = RetryPrimitive(
    primitive={func_name}_core,
    max_retries={max_retries},
    backoff_strategy="exponential",
    initial_delay=1.0,
)


# Example usage:
# result = {await_kw}{func_name}.execute(data, context)
'''

    def _generate_router_code(self, routes: dict[str, str]) -> str:
        """Generate RouterPrimitive code from routes."""
        routes_str = ",\n        ".join([f'"{k}": {v}' for k, v in routes.items()])
        default_key = list(routes.keys())[0]

        return f"""    # Using RouterPrimitive instead of if/elif chain
    router = RouterPrimitive(
        routes={{
            {routes_str}
        }},
        router_fn=lambda data, ctx: data.get("provider", "{default_key}"),
        default="{default_key}"
    )
    return await router.execute(data, context)"""

    def _generate_cache_wrapper(self, func_name: str, is_async: bool) -> str:
        """Generate a CachePrimitive-wrapped function."""
        async_kw = "async " if is_async else ""
        await_kw = "await " if is_async else ""

        return f'''
{async_kw}def {func_name}_core(data: dict, context: WorkflowContext):
    """Core operation - cache miss handler."""
    # Your expensive operation here
    pass


# Wrap with CachePrimitive for automatic caching
{func_name} = CachePrimitive(
    primitive={func_name}_core,
    ttl_seconds=3600,
    max_size=1000,
)


# Example usage:
# result = {await_kw}{func_name}.execute({{"key": key}}, context)
'''

    def _transform_circuit_breaker_ast(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Transform functions with multiple exception handlers into CircuitBreakerPrimitive."""
        transformer = CircuitBreakerTransformer()
        new_tree = transformer.visit(tree)

        if not transformer.transformations:
            return {"changed": False, "code": code, "changes": []}

        # Add new functions generated by transformer
        new_tree.body = [
            node for node in new_tree.body if node is not None
        ] + transformer.new_functions

        ast.fix_missing_locations(new_tree)

        try:
            new_code = ast.unparse(new_tree)
        except Exception:
            # Fall back to manual line replacement
            return self._transform_circuit_breaker_fallback(code, tree)

        return {
            "changed": True,
            "code": new_code,
            "changes": transformer.transformations,
        }

    def _transform_circuit_breaker_fallback(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Fallback circuit breaker transformation using line-based replacement."""
        changes = []
        detector = CircuitBreakerDetector()
        detector.visit(tree)

        if not detector.circuit_patterns:
            return {"changed": False, "code": code, "changes": []}

        lines = code.split("\n")
        transformed_lines = lines.copy()
        offset = 0

        for func_info in detector.circuit_patterns:
            func_name = func_info["name"]
            is_async = func_info["is_async"]
            lineno = func_info["lineno"]
            exception_count = func_info["exception_count"]

            # Find function boundaries
            func_start = lineno - 1
            func_end = self._find_function_end(lines, func_start)

            # Generate circuit breaker wrapper
            wrapper_code = self._generate_circuit_breaker_wrapper(
                func_name, is_async, exception_count
            )

            # Replace function
            new_lines = wrapper_code.split("\n")
            transformed_lines = (
                transformed_lines[: func_start + offset]
                + new_lines
                + transformed_lines[func_end + 1 + offset :]
            )
            offset += len(new_lines) - (func_end - func_start + 1)

            changes.append(
                {
                    "type": "circuit_breaker_transform",
                    "function": func_name,
                    "line": lineno,
                    "exception_handlers": exception_count,
                    "transformation": "fallback line-based",
                }
            )

        return {
            "changed": bool(changes),
            "code": "\n".join(transformed_lines),
            "changes": changes,
        }

    def _generate_circuit_breaker_wrapper(
        self, func_name: str, is_async: bool, exception_count: int
    ) -> str:
        """Generate a CircuitBreakerPrimitive wrapper."""
        async_kw = "async " if is_async else ""
        await_kw = "await " if is_async else ""

        return f'''
{async_kw}def {func_name}_core(data: dict, context: WorkflowContext):
    """Core operation protected by CircuitBreakerPrimitive."""
    # Your unreliable operation here
    pass


# Wrap with CircuitBreakerPrimitive for failure protection
# Original had {exception_count} exception handlers - now handled by circuit breaker
{func_name} = CircuitBreakerPrimitive(
    primitive={func_name}_core,
    failure_threshold=5,      # Open circuit after 5 failures
    recovery_timeout=60,      # Try again after 60 seconds
    expected_successes=2,     # Close after 2 successes in half-open
)


# Example usage:
# result = {await_kw}{func_name}.execute(data, context)
'''

    def _transform_compensation_ast(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Transform saga/compensation patterns into CompensationPrimitive."""
        transformer = CompensationTransformer()
        new_tree = transformer.visit(tree)

        if not transformer.transformations:
            return {"changed": False, "code": code, "changes": []}

        # Add new functions generated by transformer
        new_tree.body = [
            node for node in new_tree.body if node is not None
        ] + transformer.new_functions

        ast.fix_missing_locations(new_tree)

        try:
            new_code = ast.unparse(new_tree)
        except Exception:
            # Fall back to manual line replacement
            return self._transform_compensation_fallback(code, tree)

        return {
            "changed": True,
            "code": new_code,
            "changes": transformer.transformations,
        }

    def _transform_compensation_fallback(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Fallback compensation transformation using line-based replacement."""
        changes = []
        detector = CompensationDetector()
        detector.visit(tree)

        if not detector.compensation_patterns:
            return {"changed": False, "code": code, "changes": []}

        lines = code.split("\n")
        transformed_lines = lines.copy()
        offset = 0

        for func_info in detector.compensation_patterns:
            func_name = func_info["name"]
            is_async = func_info["is_async"]
            lineno = func_info["lineno"]
            cleanup_actions = func_info.get("cleanup_actions", [])

            # Find function boundaries
            func_start = lineno - 1
            func_end = self._find_function_end(lines, func_start)

            # Generate compensation wrapper
            wrapper_code = self._generate_compensation_wrapper(func_name, is_async, cleanup_actions)

            # Replace function
            new_lines = wrapper_code.split("\n")
            transformed_lines = (
                transformed_lines[: func_start + offset]
                + new_lines
                + transformed_lines[func_end + 1 + offset :]
            )
            offset += len(new_lines) - (func_end - func_start + 1)

            changes.append(
                {
                    "type": "compensation_transform",
                    "function": func_name,
                    "line": lineno,
                    "cleanup_actions": cleanup_actions,
                    "transformation": "fallback line-based",
                }
            )

        return {
            "changed": bool(changes),
            "code": "\n".join(transformed_lines),
            "changes": changes,
        }

    def _generate_compensation_wrapper(
        self, func_name: str, is_async: bool, cleanup_actions: list[str]
    ) -> str:
        """Generate a CompensationPrimitive wrapper."""
        async_kw = "async " if is_async else ""
        await_kw = "await " if is_async else ""
        cleanup_str = ", ".join(cleanup_actions) if cleanup_actions else "cleanup operation"

        return f'''
{async_kw}def {func_name}_forward(data: dict, context: WorkflowContext):
    """Forward operation - the main action."""
    # Your forward operation here
    pass


{async_kw}def {func_name}_compensation(data: dict, context: WorkflowContext):
    """Compensation operation - undo/cleanup if forward fails."""
    # Original cleanup: {cleanup_str}
    pass


# Wrap with CompensationPrimitive for saga pattern
{func_name} = CompensationPrimitive(
    forward={func_name}_forward,
    compensation={func_name}_compensation,
)


# Example usage:
# result = {await_kw}{func_name}.execute(data, context)
'''

    def _transform_memory_ast(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Transform conversation history patterns into MemoryPrimitive."""
        changes = []
        detector = MemoryDetector()
        detector.visit(tree)

        if not detector.memory_patterns:
            return {"changed": False, "code": code, "changes": []}

        # Group patterns by type
        message_appends = [p for p in detector.memory_patterns if p["type"] == "message_append"]
        dict_storages = [p for p in detector.memory_patterns if p["type"] == "dict_storage"]
        deque_histories = [p for p in detector.memory_patterns if p["type"] == "deque_history"]

        lines = code.split("\n")
        transformed_lines = lines.copy()

        # Generate MemoryPrimitive setup at the top of relevant functions
        if message_appends or dict_storages or deque_histories:
            # Find first pattern
            first_pattern = detector.memory_patterns[0]
            var_name = first_pattern.get("variable", "memory")
            max_size = first_pattern.get("maxlen", 100)

            changes.append(
                {
                    "type": "memory_transform",
                    "original_variable": var_name,
                    "pattern_type": first_pattern["type"],
                    "lineno": first_pattern["lineno"],
                    "max_size": max_size,
                }
            )

        return {
            "changed": bool(changes),
            "code": "\n".join(transformed_lines),
            "changes": changes,
        }

    def _transform_delegation_ast(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Transform task delegation patterns into DelegationPrimitive."""
        changes = []
        detector = DelegationDetector()
        detector.visit(tree)

        if not detector.delegation_patterns:
            return {"changed": False, "code": code, "changes": []}

        lines = code.split("\n")
        transformed_lines = lines.copy()

        for pattern in detector.delegation_patterns:
            if pattern["type"] == "model_routing":
                changes.append(
                    {
                        "type": "delegation_transform",
                        "pattern_type": "model_routing",
                        "variable": pattern["variable"],
                        "models": pattern["models"],
                        "lineno": pattern["lineno"],
                    }
                )
            elif pattern["type"] == "agent_dispatch":
                changes.append(
                    {
                        "type": "delegation_transform",
                        "pattern_type": "agent_dispatch",
                        "container": pattern["container"],
                        "method": pattern["method"],
                        "lineno": pattern["lineno"],
                    }
                )
            elif pattern["type"] == "executor_dispatch":
                changes.append(
                    {
                        "type": "delegation_transform",
                        "pattern_type": "executor_dispatch",
                        "executor": pattern["executor"],
                        "method": pattern["method"],
                        "lineno": pattern["lineno"],
                    }
                )

        return {
            "changed": bool(changes),
            "code": "\n".join(transformed_lines),
            "changes": changes,
        }

    def _transform_sequential_ast(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Transform sequential pipeline patterns into SequentialPrimitive."""
        changes = []
        detector = SequentialDetector()
        detector.visit(tree)

        if not detector.sequential_patterns:
            return {"changed": False, "code": code, "changes": []}

        lines = code.split("\n")
        transformed_lines = lines.copy()

        for pattern in detector.sequential_patterns:
            changes.append(
                {
                    "type": "sequential_transform",
                    "pattern_type": pattern["type"],
                    "steps": pattern["steps"],
                    "step_count": pattern["step_count"],
                    "parent_function": pattern["parent_function"],
                    "lineno": pattern["lineno"],
                }
            )

        return {
            "changed": bool(changes),
            "code": "\n".join(transformed_lines),
            "changes": changes,
        }

    def _transform_adaptive_ast(self, code: str, tree: ast.Module) -> dict[str, Any]:
        """Transform adaptive/learning patterns into AdaptivePrimitive."""
        changes = []
        detector = AdaptiveDetector()
        detector.visit(tree)

        if not detector.adaptive_patterns:
            return {"changed": False, "code": code, "changes": []}

        lines = code.split("\n")
        transformed_lines = lines.copy()

        for pattern in detector.adaptive_patterns:
            changes.append(
                {
                    "type": "adaptive_transform",
                    "pattern_type": pattern["type"],
                    "parent_function": pattern.get("parent_function"),
                    "lineno": pattern["lineno"],
                    "counter_vars": pattern.get("counter_vars", []),
                    "variable": pattern.get("variable"),
                }
            )

        return {
            "changed": bool(changes),
            "code": "\n".join(transformed_lines),
            "changes": changes,
        }

    def _transform_retry_regex(self, code: str) -> dict[str, Any]:
        """Transform manual retry loops into RetryPrimitive."""
        changes = []

        # Pattern: for attempt in range(n): try: ... except: ...
        pattern = r'''
            (async\s+)?def\s+(\w+)\s*\([^)]*\)\s*(?:->.*?)?:\s*\n
            (?:\s*"""[^"]*"""\s*\n)?
            \s*for\s+\w+\s+in\s+range\s*\(\s*(\d+)\s*\)\s*:\s*\n
            \s*try:\s*\n
            ([\s\S]*?)
            \s*except[^:]*:\s*\n
            ([\s\S]*?)
            (?=\n(?:def\s|class\s|$|\Z))
        '''

        match = re.search(pattern, code, re.VERBOSE | re.MULTILINE)
        if match:
            is_async = match.group(1) is not None
            func_name = match.group(2)
            max_retries = match.group(3)

            # Extract the core operation from the try block
            try_body = match.group(4).strip()

            # Generate the new code
            new_func = self._generate_retry_wrapper(func_name, try_body, int(max_retries), is_async)

            # Replace the old function
            new_code = code[: match.start()] + new_func + code[match.end() :]

            changes.append(
                {
                    "type": "retry_transform",
                    "function": func_name,
                    "max_retries": max_retries,
                    "line": code[: match.start()].count("\n") + 1,
                }
            )

            return {"changed": True, "code": new_code, "changes": changes}

        return {"changed": False, "code": code, "changes": []}

    def _transform_timeout_regex(self, code: str) -> dict[str, Any]:
        """Transform asyncio.wait_for into TimeoutPrimitive."""
        changes = []

        # Pattern: await asyncio.wait_for(coro, timeout=N)
        pattern = r"await\s+asyncio\.wait_for\s*\(\s*(\w+)\s*\([^)]*\)\s*,\s*timeout\s*=\s*(\d+(?:\.\d+)?)\s*\)"

        def replace_timeout(match: re.Match) -> str:
            func_name = match.group(1)
            timeout = match.group(2)
            changes.append(
                {
                    "type": "timeout_transform",
                    "function": func_name,
                    "timeout": timeout,
                }
            )
            return f"await TimeoutPrimitive({func_name}, timeout_seconds={timeout}).execute(data, context)"

        new_code = re.sub(pattern, replace_timeout, code)

        return {
            "changed": new_code != code,
            "code": new_code,
            "changes": changes,
        }

    def _transform_fallback_regex(self, code: str) -> dict[str, Any]:
        """Transform manual fallback into FallbackPrimitive."""
        changes = []

        # Pattern: try: primary except: fallback
        pattern = r"""
            try:\s*\n
            \s*(return\s+await\s+(\w+)\s*\([^)]*\))\s*\n
            \s*except[^:]*:\s*\n
            \s*(return\s+(\w+))\s*\n
        """

        match = re.search(pattern, code, re.VERBOSE)
        if match:
            primary_call = match.group(2)
            fallback_value = match.group(4)

            # Generate fallback wrapper
            replacement = f"""# Using FallbackPrimitive instead of try/except
fallback_workflow = FallbackPrimitive(
    primary={primary_call},
    fallbacks=[lambda data, ctx: {fallback_value}]
)
result = await fallback_workflow.execute(data, context)
return result
"""
            new_code = code[: match.start()] + replacement + code[match.end() :]

            changes.append(
                {
                    "type": "fallback_transform",
                    "primary": primary_call,
                    "fallback": fallback_value,
                }
            )

            return {"changed": True, "code": new_code, "changes": changes}

        return {"changed": False, "code": code, "changes": []}

    def _transform_parallel_regex(self, code: str) -> dict[str, Any]:
        """Transform asyncio.gather into ParallelPrimitive."""
        changes = []

        # Pattern: await asyncio.gather(coro1, coro2, ...)
        pattern = r"await\s+asyncio\.gather\s*\(\s*([^)]+)\s*\)"

        def replace_gather(match: re.Match) -> str:
            args = match.group(1)
            # Extract function names from the gather call
            func_calls = [arg.strip() for arg in args.split(",")]
            changes.append(
                {
                    "type": "parallel_transform",
                    "functions": func_calls,
                }
            )
            funcs_str = ", ".join(func_calls)
            return f"await ParallelPrimitive([{funcs_str}]).execute(data, context)"

        new_code = re.sub(pattern, replace_gather, code)

        return {
            "changed": new_code != code,
            "code": new_code,
            "changes": changes,
        }

    def _transform_router_regex(self, code: str) -> dict[str, Any]:
        """Transform if/elif chains into RouterPrimitive."""
        changes = []

        # Pattern: if x == "a": ... elif x == "b": ... else: ...
        pattern = r"""
            if\s+(\w+)\s*==\s*['"]([\w]+)['"]\s*:\s*\n
            \s*(return\s+await\s+(\w+)\s*\([^)]*\))\s*\n
            (?:\s*elif\s+\1\s*==\s*['"]([\w]+)['"]\s*:\s*\n
            \s*(return\s+await\s+(\w+)\s*\([^)]*\))\s*\n)+
            (?:\s*else:\s*\n
            \s*(.+)\s*\n)?
        """

        match = re.search(pattern, code, re.VERBOSE)
        if match:
            var_name = match.group(1)

            # Extract all routes from the if/elif chain
            routes = {}
            route_pattern = (
                r"(?:if|elif)\s+"
                + var_name
                + r'\s*==\s*["\'](\w+)["\']\s*:\s*\n\s*return\s+await\s+(\w+)'
            )
            for route_match in re.finditer(route_pattern, code):
                key = route_match.group(1)
                func = route_match.group(2)
                routes[key] = func

            if len(routes) >= 2:
                # Generate router
                routes_str = ",\n        ".join([f'"{k}": {v}' for k, v in routes.items()])
                default_key = list(routes.keys())[0]

                replacement = f"""# Using RouterPrimitive instead of if/elif chain
router = RouterPrimitive(
    routes={{
        {routes_str}
    }},
    router_fn=lambda data, ctx: data.get("{var_name}", "{default_key}"),
    default="{default_key}"
)
result = await router.execute(data, context)
return result
"""
                new_code = code[: match.start()] + replacement + code[match.end() :]

                changes.append(
                    {
                        "type": "router_transform",
                        "variable": var_name,
                        "routes": list(routes.keys()),
                    }
                )

                return {"changed": True, "code": new_code, "changes": changes}

        return {"changed": False, "code": code, "changes": []}

    def _generate_retry_wrapper(
        self, func_name: str, body: str, max_retries: int, is_async: bool
    ) -> str:
        """Generate a RetryPrimitive wrapper for a function."""
        async_kw = "async " if is_async else ""
        await_kw = "await " if is_async else ""

        # Extract the core operation
        core_op = body.strip()
        if core_op.startswith("return "):
            core_op = core_op[7:]

        return f'''
{async_kw}def {func_name}_inner(data: dict, context: WorkflowContext):
    """Inner function wrapped by RetryPrimitive."""
    {core_op}

# Wrap with RetryPrimitive
{func_name} = RetryPrimitive(
    primitive={func_name}_inner,
    max_retries={max_retries},
    backoff_strategy="exponential",
    initial_delay=1.0,
)

# Usage: result = {await_kw}{func_name}.execute(data, context)
'''

    def _add_imports(self, code: str, imports: list[str]) -> str:
        """Add imports to the top of the code."""
        lines = code.split("\n")

        # Find where to insert imports
        import_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("import ") or line.startswith("from "):
                import_idx = i + 1
            elif line.strip() and not line.startswith("#") and import_idx > 0:
                break

        # Filter out imports that already exist
        existing_imports = set()
        for line in lines:
            if line.startswith("from ") or line.startswith("import "):
                existing_imports.add(line.strip())

        new_imports = [imp for imp in imports if imp not in existing_imports]

        if new_imports:
            # Insert new imports
            for imp in reversed(new_imports):
                lines.insert(import_idx, imp)

            # Add blank line after imports if needed
            if import_idx + len(new_imports) < len(lines):
                if lines[import_idx + len(new_imports)].strip():
                    lines.insert(import_idx + len(new_imports), "")

        return "\n".join(lines)


def transform_code(
    code: str,
    primitive: str | None = None,
    auto_detect: bool = True,
) -> TransformResult:
    """Transform code to use TTA.dev primitives.

    This is the main entry point for code transformation.

    Args:
        code: Source code to transform
        primitive: Specific primitive to apply (optional)
        auto_detect: Auto-detect anti-patterns if no primitive specified

    Returns:
        TransformResult with transformed code

    Example:
        >>> code = '''
        ... async def fetch(url):
        ...     for attempt in range(3):
        ...         try:
        ...             return await httpx.get(url)
        ...         except:
        ...             pass
        ... '''
        >>> result = transform_code(code)
        >>> print(result.transformed_code)
    """
    transformer = CodeTransformer()
    return transformer.transform(code, primitive, auto_detect)
