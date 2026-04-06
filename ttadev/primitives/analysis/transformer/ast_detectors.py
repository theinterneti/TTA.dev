"""Core AST NodeVisitor detectors: Retry through Compensation."""

import ast
from typing import Any


class RetryLoopDetector(ast.NodeVisitor):
    """Detect retry loop patterns in AST."""

    def __init__(self) -> None:
        self.retry_functions: list[dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node, is_async=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node, is_async=True)
        self.generic_visit(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool) -> None:
        """Check if function contains a retry loop pattern."""
        for stmt in node.body:
            if isinstance(stmt, ast.For):
                # Check for: for x in range(n)
                if isinstance(stmt.iter, ast.Call):
                    if isinstance(stmt.iter.func, ast.Name):
                        if stmt.iter.func.id == "range":
                            # Check if body has try/except
                            for for_stmt in stmt.body:
                                if isinstance(for_stmt, ast.Try):
                                    # Found retry pattern!
                                    max_retries = 3
                                    if stmt.iter.args:
                                        if isinstance(stmt.iter.args[0], ast.Constant):
                                            max_retries = stmt.iter.args[0].value

                                    self.retry_functions.append(
                                        {
                                            "name": node.name,
                                            "is_async": is_async,
                                            "max_retries": max_retries,
                                            "lineno": node.lineno,
                                            "node": node,
                                            "for_node": stmt,
                                            "try_node": for_stmt,
                                        }
                                    )
                                    return


class TimeoutDetector(ast.NodeVisitor):
    """Detect asyncio.wait_for patterns."""

    def __init__(self) -> None:
        self.timeout_calls: list[dict[str, Any]] = []
        self._current_function: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        old_func = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        old_func = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_func

    def visit_Await(self, node: ast.Await) -> None:
        if isinstance(node.value, ast.Call):
            call = node.value
            # Check for asyncio.wait_for(...)
            if isinstance(call.func, ast.Attribute):
                if call.func.attr == "wait_for":
                    if isinstance(call.func.value, ast.Name):
                        if call.func.value.id == "asyncio":
                            timeout = None
                            wrapped_func = "operation"

                            # Extract timeout
                            for kw in call.keywords:
                                if kw.arg == "timeout":
                                    if isinstance(kw.value, ast.Constant):
                                        timeout = kw.value.value

                            # Extract wrapped function name
                            if call.args and isinstance(call.args[0], ast.Call):
                                if isinstance(call.args[0].func, ast.Name):
                                    wrapped_func = call.args[0].func.id
                                elif isinstance(call.args[0].func, ast.Attribute):
                                    wrapped_func = call.args[0].func.attr

                            self.timeout_calls.append(
                                {
                                    "node": node,
                                    "timeout": timeout,
                                    "lineno": node.lineno,
                                    "function": wrapped_func,
                                    "parent_function": self._current_function,
                                }
                            )
        self.generic_visit(node)


class CachePatternDetector(ast.NodeVisitor):
    """Detect manual caching patterns."""

    def __init__(self) -> None:
        self.cache_functions: list[dict[str, Any]] = []
        self._current_function: ast.FunctionDef | ast.AsyncFunctionDef | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_cache_pattern(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_cache_pattern(node, is_async=True)

    def _check_cache_pattern(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool
    ) -> None:
        """Check for manual cache pattern: if key in cache: return cache[key]."""
        for stmt in node.body:
            if isinstance(stmt, ast.If):
                # Check for: if key in cache
                if isinstance(stmt.test, ast.Compare):
                    if len(stmt.test.ops) == 1:
                        if isinstance(stmt.test.ops[0], ast.In):
                            # Found cache check pattern
                            self.cache_functions.append(
                                {
                                    "name": node.name,
                                    "is_async": is_async,
                                    "lineno": node.lineno,
                                    "node": node,
                                }
                            )
                            return


class FallbackDetector(ast.NodeVisitor):
    """Detect try/except fallback patterns."""

    def __init__(self) -> None:
        self.fallback_patterns: list[dict[str, Any]] = []
        self._current_function: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        old_func = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        old_func = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_func

    def visit_Try(self, node: ast.Try) -> None:
        # Check for: try: return x except: return y
        primary_func = self._extract_return_func(node.body)
        fallback_func = None

        for handler in node.handlers:
            fallback_func = self._extract_return_func(handler.body)
            if fallback_func:
                break

        if primary_func and fallback_func:
            self.fallback_patterns.append(
                {
                    "node": node,
                    "lineno": node.lineno,
                    "primary": primary_func,
                    "fallback": fallback_func,
                    "function": self._current_function,
                }
            )

        self.generic_visit(node)

    def _extract_return_func(self, body: list[ast.stmt]) -> str | None:
        """Extract function name from return statement."""
        for stmt in body:
            if isinstance(stmt, ast.Return) and stmt.value:
                return self._extract_func_name(stmt.value)
        return None

    def _extract_func_name(self, node: ast.expr) -> str | None:
        """Extract function name from expression."""
        if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
            return self._get_call_name(node.value)
        elif isinstance(node, ast.Call):
            return self._get_call_name(node)
        return None

    def _get_call_name(self, call: ast.Call) -> str | None:
        """Get the function name from a Call node."""
        if isinstance(call.func, ast.Name):
            return call.func.id
        elif isinstance(call.func, ast.Attribute):
            return call.func.attr
        return None


class GatherDetector(ast.NodeVisitor):
    """Detect asyncio.gather patterns."""

    def __init__(self) -> None:
        self.gather_calls: list[dict[str, Any]] = []

    def visit_Await(self, node: ast.Await) -> None:
        if isinstance(node.value, ast.Call):
            call = node.value
            # Check for asyncio.gather(...)
            if isinstance(call.func, ast.Attribute):
                if call.func.attr == "gather":
                    if isinstance(call.func.value, ast.Name):
                        if call.func.value.id == "asyncio":
                            self.gather_calls.append(
                                {
                                    "node": node,
                                    "call": call,
                                    "lineno": node.lineno,
                                    "args": call.args,
                                }
                            )
        self.generic_visit(node)


class RouterPatternDetector(ast.NodeVisitor):
    """Detect if/elif routing chains."""

    def __init__(self) -> None:
        self.router_patterns: list[dict[str, Any]] = []
        self._current_function: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        old_func = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_func

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        old_func = self._current_function
        self._current_function = node.name
        self.generic_visit(node)
        self._current_function = old_func

    def visit_If(self, node: ast.If) -> None:
        routes, variable = self._extract_routes(node)
        if len(routes) >= 2:
            self.router_patterns.append(
                {
                    "node": node,
                    "routes": routes,
                    "lineno": node.lineno,
                    "variable": variable,
                    "function": self._current_function,
                }
            )
        self.generic_visit(node)

    def _extract_routes(self, node: ast.If) -> tuple[dict[str, str], str]:
        """Extract routes from if/elif chain."""
        routes = {}
        variable = "key"

        # Check if condition is: var == "value"
        if isinstance(node.test, ast.Compare):
            if len(node.test.ops) == 1 and isinstance(node.test.ops[0], ast.Eq):
                if isinstance(node.test.left, ast.Name):
                    variable = node.test.left.id
                    if isinstance(node.test.comparators[0], ast.Constant):
                        key = str(node.test.comparators[0].value)
                        # Get the return/call in body
                        for stmt in node.body:
                            if isinstance(stmt, ast.Return):
                                if isinstance(stmt.value, ast.Await):
                                    if isinstance(stmt.value.value, ast.Call):
                                        if isinstance(stmt.value.value.func, ast.Name):
                                            routes[key] = stmt.value.value.func.id
                            elif isinstance(stmt, ast.Expr):
                                if isinstance(stmt.value, ast.Await):
                                    if isinstance(stmt.value.value, ast.Call):
                                        if isinstance(stmt.value.value.func, ast.Name):
                                            routes[key] = stmt.value.value.func.id

        # Check elif chains
        for elif_node in node.orelse:
            if isinstance(elif_node, ast.If):
                elif_routes, _ = self._extract_routes(elif_node)
                routes.update(elif_routes)

        return routes, variable


class CircuitBreakerDetector(ast.NodeVisitor):
    """Detect functions with multiple exception handlers."""

    def __init__(self) -> None:
        self.circuit_patterns: list[dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node, is_async=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node, is_async=True)
        self.generic_visit(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool) -> None:
        """Check if function has multiple exception handlers."""
        for stmt in node.body:
            if isinstance(stmt, ast.Try):
                if len(stmt.handlers) >= 2:
                    self.circuit_patterns.append(
                        {
                            "name": node.name,
                            "is_async": is_async,
                            "lineno": node.lineno,
                            "node": node,
                            "exception_count": len(stmt.handlers),
                        }
                    )
                    return


class CompensationDetector(ast.NodeVisitor):
    """Detect saga/compensation patterns (try with cleanup on failure)."""

    def __init__(self) -> None:
        self.compensation_patterns: list[dict[str, Any]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node, is_async=False)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node, is_async=True)
        self.generic_visit(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool) -> None:
        """Check for compensation pattern: try with cleanup + re-raise."""
        for stmt in node.body:
            if isinstance(stmt, ast.Try):
                for handler in stmt.handlers:
                    has_raise = False
                    cleanup_actions: list[str] = []

                    for h_stmt in handler.body:
                        if isinstance(h_stmt, ast.Raise):
                            has_raise = True
                        elif isinstance(h_stmt, ast.Expr):
                            # Extract cleanup action from expression
                            if isinstance(h_stmt.value, ast.Await):
                                call = h_stmt.value.value
                                if isinstance(call, ast.Call):
                                    cleanup_actions.append(self._extract_call_name(call))
                            elif isinstance(h_stmt.value, ast.Call):
                                cleanup_actions.append(self._extract_call_name(h_stmt.value))

                    if has_raise and cleanup_actions:
                        self.compensation_patterns.append(
                            {
                                "name": node.name,
                                "is_async": is_async,
                                "lineno": node.lineno,
                                "node": node,
                                "cleanup_actions": cleanup_actions,
                            }
                        )
                        return

    def _extract_call_name(self, call: ast.Call) -> str:
        """Extract a readable name from a Call node."""
        if isinstance(call.func, ast.Attribute):
            # e.g., db.delete or service.rollback
            parts = []
            node = call.func
            while isinstance(node, ast.Attribute):
                parts.append(node.attr)
                node = node.value
            if isinstance(node, ast.Name):
                parts.append(node.id)
            return ".".join(reversed(parts))
        elif isinstance(call.func, ast.Name):
            return call.func.id
        return "unknown"
