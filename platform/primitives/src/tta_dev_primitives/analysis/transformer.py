"""AST-based code transformer for TTA.dev primitives.

Transforms anti-patterns into proper TTA.dev primitive usage
by analyzing and rewriting the Abstract Syntax Tree.
"""

import ast
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class TransformResult:
    """Result of a code transformation."""

    original_code: str
    transformed_code: str
    changes_made: list[dict[str, Any]]
    imports_added: list[str]
    success: bool
    error: str | None = None


@dataclass
class FunctionInfo:
    """Information about a function to transform."""

    name: str
    is_async: bool
    args: list[str]
    body: list[ast.stmt]
    decorators: list[ast.expr]
    returns: ast.expr | None
    lineno: int
    col_offset: int


# =============================================================================
# AST Node Transformers - Actually rewrite function bodies
# =============================================================================


class RetryLoopTransformer(ast.NodeTransformer):
    """Transform retry loops into RetryPrimitive-wrapped functions.

    Transforms:
        def fetch():
            for i in range(3):
                try:
                    return api_call()
                except:
                    pass

    Into:
        async def fetch_core(data: dict, context: WorkflowContext):
            return api_call()

        fetch = RetryPrimitive(primitive=fetch_core, max_retries=3)
    """

    def __init__(self) -> None:
        self.transformations: list[dict[str, Any]] = []
        self.new_functions: list[ast.stmt] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        return self._transform_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        return self._transform_function(node, is_async=True)

    def _transform_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool
    ) -> ast.AST:
        """Transform a function with retry loop into RetryPrimitive."""
        retry_info = self._find_retry_pattern(node)
        if not retry_info:
            return node

        func_name = node.name
        max_retries = retry_info["max_retries"]
        try_body = retry_info["try_body"]

        # Create the core function with extracted body
        core_func = self._create_core_function(
            func_name, try_body, is_async, node.lineno
        )

        # Create the RetryPrimitive assignment
        primitive_assign = self._create_primitive_assignment(
            func_name, max_retries, is_async
        )

        self.transformations.append(
            {
                "type": "retry_transform",
                "function": func_name,
                "max_retries": max_retries,
                "line": node.lineno,
                "transformation": "Full AST rewrite",
            }
        )

        # Store new functions to add
        self.new_functions.append(core_func)
        self.new_functions.append(primitive_assign)

        # Return None to remove the original function (we'll add new ones)
        return None  # type: ignore

    def _find_retry_pattern(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> dict[str, Any] | None:
        """Find retry loop pattern in function body."""
        for stmt in node.body:
            if isinstance(stmt, ast.For):
                if isinstance(stmt.iter, ast.Call):
                    if isinstance(stmt.iter.func, ast.Name):
                        if stmt.iter.func.id == "range":
                            for for_stmt in stmt.body:
                                if isinstance(for_stmt, ast.Try):
                                    max_retries = 3
                                    if stmt.iter.args:
                                        if isinstance(stmt.iter.args[0], ast.Constant):
                                            max_retries = stmt.iter.args[0].value
                                    return {
                                        "max_retries": max_retries,
                                        "try_body": for_stmt.body,
                                        "for_node": stmt,
                                        "try_node": for_stmt,
                                    }
        return None

    def _create_core_function(
        self,
        func_name: str,
        body: list[ast.stmt],
        is_async: bool,
        lineno: int,
    ) -> ast.FunctionDef | ast.AsyncFunctionDef:
        """Create the core function with the extracted body."""
        # Create arguments: data: dict, context: WorkflowContext
        args = ast.arguments(
            posonlyargs=[],
            args=[
                ast.arg(arg="data", annotation=ast.Name(id="dict", ctx=ast.Load())),
                ast.arg(
                    arg="context",
                    annotation=ast.Name(id="WorkflowContext", ctx=ast.Load()),
                ),
            ],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[],
        )

        # Create docstring
        docstring = ast.Expr(
            value=ast.Constant(value=f"Core operation for {func_name}.")
        )

        func_class = ast.AsyncFunctionDef if is_async else ast.FunctionDef
        core_func = func_class(
            name=f"{func_name}_core",
            args=args,
            body=[docstring] + body,
            decorator_list=[],
            returns=None,
            lineno=lineno,
            col_offset=0,
        )

        return ast.fix_missing_locations(core_func)

    def _create_primitive_assignment(
        self, func_name: str, max_retries: int, is_async: bool
    ) -> ast.Assign:
        """Create the RetryPrimitive assignment."""
        # func_name = RetryPrimitive(primitive=func_name_core, max_retries=N, ...)
        call = ast.Call(
            func=ast.Name(id="RetryPrimitive", ctx=ast.Load()),
            args=[],
            keywords=[
                ast.keyword(
                    arg="primitive",
                    value=ast.Name(id=f"{func_name}_core", ctx=ast.Load()),
                ),
                ast.keyword(arg="max_retries", value=ast.Constant(value=max_retries)),
                ast.keyword(
                    arg="backoff_strategy", value=ast.Constant(value="exponential")
                ),
                ast.keyword(arg="initial_delay", value=ast.Constant(value=1.0)),
            ],
        )

        assign = ast.Assign(
            targets=[ast.Name(id=func_name, ctx=ast.Store())],
            value=call,
            lineno=0,
            col_offset=0,
        )

        return ast.fix_missing_locations(assign)


class TimeoutTransformer(ast.NodeTransformer):
    """Transform asyncio.wait_for into TimeoutPrimitive.

    Transforms:
        result = await asyncio.wait_for(slow_call(), timeout=30)

    Into:
        timeout_wrapper = TimeoutPrimitive(primitive=slow_call, timeout_seconds=30)
        result = await timeout_wrapper.execute(data, context)
    """

    def __init__(self) -> None:
        self.transformations: list[dict[str, Any]] = []

    def visit_Await(self, node: ast.Await) -> ast.AST:
        if isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute):
                if call.func.attr == "wait_for":
                    if isinstance(call.func.value, ast.Name):
                        if call.func.value.id == "asyncio":
                            return self._transform_wait_for(node, call)
        return node

    def _transform_wait_for(self, node: ast.Await, call: ast.Call) -> ast.Await:
        """Transform asyncio.wait_for to TimeoutPrimitive."""
        # Extract the coroutine and timeout
        if not call.args:
            return node

        coro = call.args[0]
        timeout = None

        for kw in call.keywords:
            if kw.arg == "timeout":
                if isinstance(kw.value, ast.Constant):
                    timeout = kw.value.value

        if timeout is None:
            return node

        # Get function name from coroutine
        func_name = "operation"
        if isinstance(coro, ast.Call):
            if isinstance(coro.func, ast.Name):
                func_name = coro.func.id

        self.transformations.append(
            {
                "type": "timeout_transform",
                "function": func_name,
                "timeout": timeout,
                "line": node.lineno,
            }
        )

        # Create: await TimeoutPrimitive(primitive=func, timeout_seconds=N).execute(data, context)
        new_call = ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Name(id="TimeoutPrimitive", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg="primitive",
                            value=coro.func if isinstance(coro, ast.Call) else coro,
                        ),
                        ast.keyword(
                            arg="timeout_seconds", value=ast.Constant(value=timeout)
                        ),
                    ],
                ),
                attr="execute",
                ctx=ast.Load(),
            ),
            args=[
                ast.Name(id="data", ctx=ast.Load()),
                ast.Name(id="context", ctx=ast.Load()),
            ],
            keywords=[],
        )

        return ast.fix_missing_locations(ast.Await(value=new_call))


class FallbackTransformer(ast.NodeTransformer):
    """Transform try/except fallback patterns into FallbackPrimitive.

    Transforms:
        try:
            return await primary()
        except:
            return await backup()

    Into:
        fallback = FallbackPrimitive(primary=primary, fallbacks=[backup])
        return await fallback.execute(data, context)
    """

    def __init__(self) -> None:
        self.transformations: list[dict[str, Any]] = []

    def visit_Try(self, node: ast.Try) -> ast.AST:
        # Check for simple try/except with returns
        primary_func = self._extract_return_func(node.body)
        fallback_func = None

        if node.handlers and len(node.handlers) == 1:
            fallback_func = self._extract_return_func(node.handlers[0].body)

        if primary_func and fallback_func:
            self.transformations.append(
                {
                    "type": "fallback_transform",
                    "primary": primary_func,
                    "fallback": fallback_func,
                    "line": node.lineno,
                }
            )

            # Create FallbackPrimitive call
            return self._create_fallback_call(primary_func, fallback_func, node.lineno)

        return node

    def _extract_return_func(self, body: list[ast.stmt]) -> str | None:
        """Extract function name from return statement."""
        for stmt in body:
            if isinstance(stmt, ast.Return):
                if isinstance(stmt.value, ast.Await):
                    if isinstance(stmt.value.value, ast.Call):
                        if isinstance(stmt.value.value.func, ast.Name):
                            return stmt.value.value.func.id
                elif isinstance(stmt.value, ast.Call):
                    if isinstance(stmt.value.func, ast.Name):
                        return stmt.value.func.id
        return None

    def _create_fallback_call(
        self, primary: str, fallback: str, lineno: int
    ) -> ast.Expr:
        """Create FallbackPrimitive expression."""
        # fallback_workflow = FallbackPrimitive(primary=primary, fallbacks=[fallback])
        # return await fallback_workflow.execute(data, context)
        call = ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Name(id="FallbackPrimitive", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg="primary",
                            value=ast.Name(id=primary, ctx=ast.Load()),
                        ),
                        ast.keyword(
                            arg="fallbacks",
                            value=ast.List(
                                elts=[ast.Name(id=fallback, ctx=ast.Load())],
                                ctx=ast.Load(),
                            ),
                        ),
                    ],
                ),
                attr="execute",
                ctx=ast.Load(),
            ),
            args=[
                ast.Name(id="data", ctx=ast.Load()),
                ast.Name(id="context", ctx=ast.Load()),
            ],
            keywords=[],
        )

        return ast.fix_missing_locations(
            ast.Return(value=ast.Await(value=call), lineno=lineno, col_offset=0)
        )


class GatherTransformer(ast.NodeTransformer):
    """Transform asyncio.gather into ParallelPrimitive.

    Transforms:
        results = await asyncio.gather(task1(), task2(), task3())

    Into:
        parallel = ParallelPrimitive([task1, task2, task3])
        results = await parallel.execute(data, context)
    """

    def __init__(self) -> None:
        self.transformations: list[dict[str, Any]] = []

    def visit_Await(self, node: ast.Await) -> ast.AST:
        if isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Attribute):
                if call.func.attr == "gather":
                    if isinstance(call.func.value, ast.Name):
                        if call.func.value.id == "asyncio":
                            return self._transform_gather(node, call)
        return node

    def _transform_gather(self, node: ast.Await, call: ast.Call) -> ast.Await:
        """Transform asyncio.gather to ParallelPrimitive."""
        # Extract function references from gather args
        funcs = []
        for arg in call.args:
            if isinstance(arg, ast.Call):
                if isinstance(arg.func, ast.Name):
                    funcs.append(arg.func.id)

        self.transformations.append(
            {
                "type": "parallel_transform",
                "functions": funcs,
                "line": node.lineno,
            }
        )

        # Create: await ParallelPrimitive([f1, f2, f3]).execute(data, context)
        func_list = ast.List(
            elts=[ast.Name(id=f, ctx=ast.Load()) for f in funcs],
            ctx=ast.Load(),
        )

        new_call = ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Name(id="ParallelPrimitive", ctx=ast.Load()),
                    args=[func_list],
                    keywords=[],
                ),
                attr="execute",
                ctx=ast.Load(),
            ),
            args=[
                ast.Name(id="data", ctx=ast.Load()),
                ast.Name(id="context", ctx=ast.Load()),
            ],
            keywords=[],
        )

        return ast.fix_missing_locations(ast.Await(value=new_call))


class RouterTransformer(ast.NodeTransformer):
    """Transform if/elif routing chains into RouterPrimitive.

    Transforms:
        if provider == "openai":
            return await call_openai(data)
        elif provider == "anthropic":
            return await call_anthropic(data)

    Into:
        router = RouterPrimitive(
            routes={"openai": call_openai, "anthropic": call_anthropic},
            router_fn=lambda data, ctx: data.get("provider"),
        )
        return await router.execute(data, context)
    """

    def __init__(self) -> None:
        self.transformations: list[dict[str, Any]] = []

    def visit_If(self, node: ast.If) -> ast.AST:
        routes = self._extract_all_routes(node)
        if len(routes) >= 2:
            var_name = self._get_comparison_var(node)

            self.transformations.append(
                {
                    "type": "router_transform",
                    "routes": list(routes.keys()),
                    "variable": var_name,
                    "line": node.lineno,
                }
            )

            return self._create_router_call(routes, var_name, node.lineno)

        return node

    def _extract_all_routes(self, node: ast.If) -> dict[str, str]:
        """Extract all routes from if/elif chain."""
        routes = {}

        # Extract from this if
        route = self._extract_route(node)
        if route:
            routes[route[0]] = route[1]

        # Extract from elif/else chain
        for else_stmt in node.orelse:
            if isinstance(else_stmt, ast.If):
                routes.update(self._extract_all_routes(else_stmt))

        return routes

    def _extract_route(self, node: ast.If) -> tuple[str, str] | None:
        """Extract a single route from an if statement."""
        if not isinstance(node.test, ast.Compare):
            return None

        if len(node.test.ops) != 1:
            return None

        if not isinstance(node.test.ops[0], ast.Eq):
            return None

        if not isinstance(node.test.comparators[0], ast.Constant):
            return None

        key = str(node.test.comparators[0].value)

        # Get function from body
        for stmt in node.body:
            if isinstance(stmt, ast.Return):
                if isinstance(stmt.value, ast.Await):
                    if isinstance(stmt.value.value, ast.Call):
                        if isinstance(stmt.value.value.func, ast.Name):
                            return (key, stmt.value.value.func.id)

        return None

    def _get_comparison_var(self, node: ast.If) -> str:
        """Get the variable being compared."""
        if isinstance(node.test, ast.Compare):
            if isinstance(node.test.left, ast.Name):
                return node.test.left.id
        return "provider"

    def _create_router_call(
        self, routes: dict[str, str], var_name: str, lineno: int
    ) -> ast.Return:
        """Create RouterPrimitive call."""
        # Build routes dict
        routes_dict = ast.Dict(
            keys=[ast.Constant(value=k) for k in routes.keys()],
            values=[ast.Name(id=v, ctx=ast.Load()) for v in routes.values()],
        )

        # router_fn lambda
        router_fn = ast.Lambda(
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg="data"), ast.arg(arg="ctx")],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            ),
            body=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id="data", ctx=ast.Load()),
                    attr="get",
                    ctx=ast.Load(),
                ),
                args=[ast.Constant(value=var_name)],
                keywords=[],
            ),
        )

        default_key = list(routes.keys())[0]

        # Create: await RouterPrimitive(...).execute(data, context)
        new_call = ast.Call(
            func=ast.Attribute(
                value=ast.Call(
                    func=ast.Name(id="RouterPrimitive", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(arg="routes", value=routes_dict),
                        ast.keyword(arg="router_fn", value=router_fn),
                        ast.keyword(
                            arg="default", value=ast.Constant(value=default_key)
                        ),
                    ],
                ),
                attr="execute",
                ctx=ast.Load(),
            ),
            args=[
                ast.Name(id="data", ctx=ast.Load()),
                ast.Name(id="context", ctx=ast.Load()),
            ],
            keywords=[],
        )

        return ast.fix_missing_locations(
            ast.Return(value=ast.Await(value=new_call), lineno=lineno, col_offset=0)
        )


# =============================================================================
# AST Detectors - Find patterns without transforming
# =============================================================================


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

    def _check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool
    ) -> None:
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

    def visit_Await(self, node: ast.Await) -> None:
        if isinstance(node.value, ast.Call):
            call = node.value
            # Check for asyncio.wait_for(...)
            if isinstance(call.func, ast.Attribute):
                if call.func.attr == "wait_for":
                    if isinstance(call.func.value, ast.Name):
                        if call.func.value.id == "asyncio":
                            timeout = None
                            for kw in call.keywords:
                                if kw.arg == "timeout":
                                    if isinstance(kw.value, ast.Constant):
                                        timeout = kw.value.value
                            self.timeout_calls.append(
                                {
                                    "node": node,
                                    "timeout": timeout,
                                    "lineno": node.lineno,
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

    def visit_Try(self, node: ast.Try) -> None:
        # Check for: try: return x except: return y
        has_try_return = False
        has_except_return = False

        for stmt in node.body:
            if isinstance(stmt, ast.Return):
                has_try_return = True
                break

        for handler in node.handlers:
            for stmt in handler.body:
                if isinstance(stmt, ast.Return):
                    has_except_return = True
                    break

        if has_try_return and has_except_return:
            self.fallback_patterns.append(
                {
                    "node": node,
                    "lineno": node.lineno,
                }
            )

        self.generic_visit(node)


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

    def visit_If(self, node: ast.If) -> None:
        routes = self._extract_routes(node)
        if len(routes) >= 2:
            self.router_patterns.append(
                {
                    "node": node,
                    "routes": routes,
                    "lineno": node.lineno,
                }
            )
        self.generic_visit(node)

    def _extract_routes(self, node: ast.If) -> dict[str, str]:
        """Extract routes from if/elif chain."""
        routes = {}

        # Check if condition is: var == "value"
        if isinstance(node.test, ast.Compare):
            if len(node.test.ops) == 1 and isinstance(node.test.ops[0], ast.Eq):
                if isinstance(node.test.left, ast.Name):
                    var_name = node.test.left.id
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
                routes.update(self._extract_routes(elif_node))

        return routes


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
            "RetryPrimitive": "from tta_dev_primitives.recovery import RetryPrimitive",
            "TimeoutPrimitive": "from tta_dev_primitives.recovery import TimeoutPrimitive",
            "FallbackPrimitive": "from tta_dev_primitives.recovery import FallbackPrimitive",
            "CachePrimitive": "from tta_dev_primitives.performance import CachePrimitive",
            "ParallelPrimitive": "from tta_dev_primitives import ParallelPrimitive",
            "SequentialPrimitive": "from tta_dev_primitives import SequentialPrimitive",
            "RouterPrimitive": "from tta_dev_primitives.core import RouterPrimitive",
            "CircuitBreakerPrimitive": "from tta_dev_primitives.recovery import CircuitBreakerPrimitive",
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
            tree = ast.parse(code)
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
        imports_needed.add("from tta_dev_primitives import WorkflowContext")

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

    def _transform_retry_ast_fallback(
        self, code: str, tree: ast.Module
    ) -> dict[str, Any]:
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

    def _transform_router_ast_fallback(
        self, code: str, tree: ast.Module
    ) -> dict[str, Any]:
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
        in_block = True

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

        return f'''    # Using RouterPrimitive instead of if/elif chain
    router = RouterPrimitive(
        routes={{
            {routes_str}
        }},
        router_fn=lambda data, ctx: data.get("provider", "{default_key}"),
        default="{default_key}"
    )
    return await router.execute(data, context)'''

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
            new_func = self._generate_retry_wrapper(
                func_name, try_body, int(max_retries), is_async
            )

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
                routes_str = ",\n        ".join(
                    [f'"{k}": {v}' for k, v in routes.items()]
                )
                default_key = list(routes.keys())[0]

                replacement = f'''# Using RouterPrimitive instead of if/elif chain
router = RouterPrimitive(
    routes={{
        {routes_str}
    }},
    router_fn=lambda data, ctx: data.get("{var_name}", "{default_key}"),
    default="{default_key}"
)
result = await router.execute(data, context)
return result
'''
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
