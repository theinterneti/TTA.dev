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


class CacheTransformer(ast.NodeTransformer):
    """Transform manual cache patterns into CachePrimitive.

    Transforms:
        cache = {}
        def get_data(key):
            if key in cache:
                return cache[key]
            result = fetch_data(key)
            cache[key] = result
            return result

    Into:
        async def get_data_core(data: dict, context: WorkflowContext):
            return fetch_data(data["key"])

        get_data = CachePrimitive(primitive=get_data_core, ttl_seconds=3600)
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
        """Transform a function with cache pattern into CachePrimitive."""
        cache_info = self._find_cache_pattern(node)
        if not cache_info:
            return node

        func_name = node.name
        fetch_body = cache_info["fetch_body"]

        # Create the core function with extracted body
        core_func = self._create_core_function(
            func_name, fetch_body, is_async, node.lineno
        )

        # Create the CachePrimitive assignment
        primitive_assign = self._create_primitive_assignment(func_name)

        self.transformations.append(
            {
                "type": "cache_transform",
                "function": func_name,
                "line": node.lineno,
                "transformation": "Full AST rewrite to CachePrimitive",
            }
        )

        # Store new function, return the assignment
        self.new_functions.append(core_func)
        return primitive_assign

    def _find_cache_pattern(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> dict[str, Any] | None:
        """Find cache pattern: if key in cache: return; result = ...; cache[key] = result."""
        for i, stmt in enumerate(node.body):
            if isinstance(stmt, ast.If):
                # Check for: if key in cache
                if isinstance(stmt.test, ast.Compare):
                    if len(stmt.test.ops) == 1 and isinstance(stmt.test.ops[0], ast.In):
                        # Found cache check, get the fetch body (after the if)
                        fetch_body = (
                            node.body[i + 1 :] if i + 1 < len(node.body) else []
                        )
                        # Filter out cache assignment statements
                        fetch_body = [
                            s for s in fetch_body if not self._is_cache_assignment(s)
                        ]
                        if fetch_body:
                            return {"fetch_body": fetch_body}
        return None

    def _is_cache_assignment(self, stmt: ast.stmt) -> bool:
        """Check if statement is a cache assignment: cache[key] = value."""
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Subscript):
                    return True
        return False

    def _create_core_function(
        self, func_name: str, body: list[ast.stmt], is_async: bool, lineno: int
    ) -> ast.AsyncFunctionDef:
        """Create the core async function."""
        core_name = f"{func_name}_core"

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

        return ast.fix_missing_locations(
            ast.AsyncFunctionDef(
                name=core_name,
                args=args,
                body=body if body else [ast.Pass()],
                decorator_list=[],
                returns=None,
                lineno=lineno,
                col_offset=0,
            )
        )

    def _create_primitive_assignment(self, func_name: str) -> ast.Assign:
        """Create: func_name = CachePrimitive(primitive=func_name_core, ttl_seconds=3600)."""
        return ast.fix_missing_locations(
            ast.Assign(
                targets=[ast.Name(id=func_name, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id="CachePrimitive", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg="primitive",
                            value=ast.Name(id=f"{func_name}_core", ctx=ast.Load()),
                        ),
                        ast.keyword(
                            arg="ttl_seconds",
                            value=ast.Constant(value=3600),
                        ),
                        ast.keyword(
                            arg="max_size",
                            value=ast.Constant(value=1000),
                        ),
                    ],
                ),
                lineno=0,
                col_offset=0,
            )
        )


class CircuitBreakerTransformer(ast.NodeTransformer):
    """Transform multiple exception handlers into CircuitBreakerPrimitive.

    Transforms functions with repeated try/except for the same operations:
        def call_service():
            try:
                return service.call()
            except ConnectionError:
                return None
            except TimeoutError:
                return None

    Into:
        async def call_service_core(data: dict, context: WorkflowContext):
            return service.call()

        call_service = CircuitBreakerPrimitive(
            primitive=call_service_core,
            failure_threshold=5,
            recovery_timeout=60
        )
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
        """Transform function with multiple exception handlers."""
        circuit_info = self._find_circuit_pattern(node)
        if not circuit_info:
            return node

        func_name = node.name
        try_body = circuit_info["try_body"]
        exception_count = circuit_info["exception_count"]

        # Create the core function
        core_func = self._create_core_function(
            func_name, try_body, is_async, node.lineno
        )

        # Create the CircuitBreakerPrimitive assignment
        primitive_assign = self._create_primitive_assignment(func_name)

        self.transformations.append(
            {
                "type": "circuit_breaker_transform",
                "function": func_name,
                "exception_handlers": exception_count,
                "line": node.lineno,
                "transformation": "Full AST rewrite to CircuitBreakerPrimitive",
            }
        )

        self.new_functions.append(core_func)
        return primitive_assign

    def _find_circuit_pattern(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> dict[str, Any] | None:
        """Find pattern: try with multiple exception handlers."""
        for stmt in node.body:
            if isinstance(stmt, ast.Try):
                # Need at least 2 exception handlers to warrant circuit breaker
                if len(stmt.handlers) >= 2:
                    return {
                        "try_body": stmt.body,
                        "exception_count": len(stmt.handlers),
                    }
        return None

    def _create_core_function(
        self, func_name: str, body: list[ast.stmt], is_async: bool, lineno: int
    ) -> ast.AsyncFunctionDef:
        """Create the core async function."""
        core_name = f"{func_name}_core"

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

        return ast.fix_missing_locations(
            ast.AsyncFunctionDef(
                name=core_name,
                args=args,
                body=body if body else [ast.Pass()],
                decorator_list=[],
                returns=None,
                lineno=lineno,
                col_offset=0,
            )
        )

    def _create_primitive_assignment(self, func_name: str) -> ast.Assign:
        """Create: func = CircuitBreakerPrimitive(primitive=func_core, ...)."""
        return ast.fix_missing_locations(
            ast.Assign(
                targets=[ast.Name(id=func_name, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id="CircuitBreakerPrimitive", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg="primitive",
                            value=ast.Name(id=f"{func_name}_core", ctx=ast.Load()),
                        ),
                        ast.keyword(
                            arg="failure_threshold",
                            value=ast.Constant(value=5),
                        ),
                        ast.keyword(
                            arg="recovery_timeout",
                            value=ast.Constant(value=60),
                        ),
                    ],
                ),
                lineno=0,
                col_offset=0,
            )
        )


class CompensationTransformer(ast.NodeTransformer):
    """Transform paired do/undo operations into CompensationPrimitive.

    Transforms AI-native patterns like:
        async def index_document(doc):
            embedding_id = await vector_store.add(doc.embedding)
            try:
                await knowledge_base.update(doc)
            except:
                await vector_store.delete(embedding_id)
                raise

    Into:
        forward = vector_store.add >> knowledge_base.update
        compensation = vector_store.delete
        index_document = CompensationPrimitive(forward=forward, compensation=compensation)
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
        """Transform function with compensation pattern."""
        comp_info = self._find_compensation_pattern(node)
        if not comp_info:
            return node

        func_name = node.name

        # Create the forward function
        forward_func = self._create_forward_function(
            func_name, comp_info["forward_body"], node.lineno
        )

        # Create the compensation function
        comp_func = self._create_compensation_function(
            func_name, comp_info["compensation_body"], node.lineno
        )

        # Create the CompensationPrimitive assignment
        primitive_assign = self._create_primitive_assignment(func_name)

        self.transformations.append(
            {
                "type": "compensation_transform",
                "function": func_name,
                "line": node.lineno,
                "transformation": "Full AST rewrite to CompensationPrimitive",
            }
        )

        self.new_functions.extend([forward_func, comp_func])
        return primitive_assign

    def _find_compensation_pattern(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> dict[str, Any] | None:
        """Find pattern: try with except that has cleanup + raise."""
        forward_body = []

        for stmt in node.body:
            if isinstance(stmt, ast.Try):
                # Check for except handler with raise at the end
                for handler in stmt.handlers:
                    has_raise = False
                    cleanup_stmts = []
                    for h_stmt in handler.body:
                        if isinstance(h_stmt, ast.Raise):
                            has_raise = True
                        else:
                            cleanup_stmts.append(h_stmt)

                    if has_raise and cleanup_stmts:
                        return {
                            "forward_body": forward_body + stmt.body,
                            "compensation_body": cleanup_stmts,
                        }
            else:
                forward_body.append(stmt)

        return None

    def _create_forward_function(
        self, func_name: str, body: list[ast.stmt], lineno: int
    ) -> ast.AsyncFunctionDef:
        """Create the forward async function."""
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

        return ast.fix_missing_locations(
            ast.AsyncFunctionDef(
                name=f"{func_name}_forward",
                args=args,
                body=body if body else [ast.Pass()],
                decorator_list=[],
                returns=None,
                lineno=lineno,
                col_offset=0,
            )
        )

    def _create_compensation_function(
        self, func_name: str, body: list[ast.stmt], lineno: int
    ) -> ast.AsyncFunctionDef:
        """Create the compensation async function."""
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

        return ast.fix_missing_locations(
            ast.AsyncFunctionDef(
                name=f"{func_name}_compensation",
                args=args,
                body=body if body else [ast.Pass()],
                decorator_list=[],
                returns=None,
                lineno=lineno,
                col_offset=0,
            )
        )

    def _create_primitive_assignment(self, func_name: str) -> ast.Assign:
        """Create: func = CompensationPrimitive(forward=..., compensation=...)."""
        return ast.fix_missing_locations(
            ast.Assign(
                targets=[ast.Name(id=func_name, ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id="CompensationPrimitive", ctx=ast.Load()),
                    args=[],
                    keywords=[
                        ast.keyword(
                            arg="forward",
                            value=ast.Name(id=f"{func_name}_forward", ctx=ast.Load()),
                        ),
                        ast.keyword(
                            arg="compensation",
                            value=ast.Name(
                                id=f"{func_name}_compensation", ctx=ast.Load()
                            ),
                        ),
                    ],
                ),
                lineno=0,
                col_offset=0,
            )
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

    def _check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool
    ) -> None:
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

    def _check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool
    ) -> None:
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
                                    cleanup_actions.append(
                                        self._extract_call_name(call)
                                    )
                            elif isinstance(h_stmt.value, ast.Call):
                                cleanup_actions.append(
                                    self._extract_call_name(h_stmt.value)
                                )

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


class MemoryDetector(ast.NodeVisitor):
    """Detect conversation history/context management patterns.

    Detects:
    - Message list accumulation (messages.append({...}))
    - Dict-based context storage (context[key] = value)
    - Deque-based history (deque(maxlen=...))
    """

    def __init__(self) -> None:
        self.memory_patterns: list[dict[str, Any]] = []
        self._current_function: str | None = None
        self._current_is_async: bool = False
        self._current_lineno: int = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = False
        self._current_lineno = node.lineno
        self.generic_visit(node)
        self._current_function = None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = True
        self._current_lineno = node.lineno
        self.generic_visit(node)
        self._current_function = None

    def visit_Call(self, node: ast.Call) -> None:
        """Detect .append() calls for message lists."""
        # Pattern: messages.append({"role": ..., "content": ...})
        if isinstance(node.func, ast.Attribute) and node.func.attr == "append":
            if isinstance(node.func.value, ast.Name):
                var_name = node.func.value.id
                # Check if appending dict with role/content (chat history pattern)
                if node.args and isinstance(node.args[0], ast.Dict):
                    keys = [
                        k.value if isinstance(k, ast.Constant) else None
                        for k in node.args[0].keys
                    ]
                    if "role" in keys or "content" in keys or "message" in keys:
                        self.memory_patterns.append(
                            {
                                "type": "message_append",
                                "variable": var_name,
                                "parent_function": self._current_function,
                                "is_async": self._current_is_async,
                                "lineno": node.lineno,
                            }
                        )
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Detect dict-based context storage."""
        # Pattern: context[key] = value (in Assign context)
        if isinstance(node.ctx, ast.Store):
            if isinstance(node.value, ast.Name):
                var_name = node.value.id
                if any(
                    kw in var_name.lower()
                    for kw in ["context", "history", "memory", "store"]
                ):
                    self.memory_patterns.append(
                        {
                            "type": "dict_storage",
                            "variable": var_name,
                            "parent_function": self._current_function,
                            "is_async": self._current_is_async,
                            "lineno": node.lineno,
                        }
                    )
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Detect deque initialization for bounded history."""
        # Pattern: history = deque(maxlen=...)
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name) and node.value.func.id == "deque":
                for keyword in node.value.keywords:
                    if keyword.arg == "maxlen":
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                maxlen = None
                                if isinstance(keyword.value, ast.Constant):
                                    maxlen = keyword.value.value
                                self.memory_patterns.append(
                                    {
                                        "type": "deque_history",
                                        "variable": target.id,
                                        "maxlen": maxlen,
                                        "parent_function": self._current_function,
                                        "is_async": self._current_is_async,
                                        "lineno": node.lineno,
                                    }
                                )
        self.generic_visit(node)


class DelegationDetector(ast.NodeVisitor):
    """Detect task delegation/orchestration patterns.

    Detects:
    - Agent routing (agents[role].execute())
    - Model selection routing (if model == "gpt-4": ...)
    - Task dispatching (executor.run(task))
    """

    def __init__(self) -> None:
        self.delegation_patterns: list[dict[str, Any]] = []
        self._current_function: str | None = None
        self._current_is_async: bool = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = False
        self._check_function_for_delegation(node)
        self.generic_visit(node)
        self._current_function = None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = True
        self._check_function_for_delegation(node)
        self.generic_visit(node)
        self._current_function = None

    def _check_function_for_delegation(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Check function for delegation patterns."""
        # Look for if/elif chains with model/agent selection
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.If):
                self._check_model_routing(stmt, node)

    def _check_model_routing(
        self,
        if_node: ast.If,
        func_node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        """Check if/elif chain for model/agent routing."""
        # Pattern: if model == "gpt-4": ... elif model == "claude": ...
        models: list[str] = []
        variable: str | None = None

        def extract_model(test: ast.expr) -> tuple[str | None, str | None]:
            """Extract model name and variable from comparison."""
            if isinstance(test, ast.Compare):
                if len(test.ops) == 1 and isinstance(test.ops[0], ast.Eq):
                    left = test.left
                    right = test.comparators[0]
                    if isinstance(left, ast.Name) and isinstance(right, ast.Constant):
                        return left.id, str(right.value)
                    if isinstance(right, ast.Name) and isinstance(left, ast.Constant):
                        return right.id, str(left.value)
            return None, None

        # Check main if
        var, model = extract_model(if_node.test)
        if model and var:
            variable = var
            if any(
                kw in var.lower() for kw in ["model", "agent", "executor", "handler"]
            ):
                models.append(model)

        # Check elif branches
        current = if_node
        while current.orelse:
            if len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
                current = current.orelse[0]
                var, model = extract_model(current.test)
                if model:
                    models.append(model)
            else:
                break

        if len(models) >= 2 and variable:
            self.delegation_patterns.append(
                {
                    "type": "model_routing",
                    "variable": variable,
                    "models": models,
                    "parent_function": func_node.name,
                    "is_async": self._current_is_async,
                    "lineno": if_node.lineno,
                }
            )

    def visit_Call(self, node: ast.Call) -> None:
        """Detect executor dispatch patterns."""
        # Pattern: agents[role].execute(...) or executor.run(task)
        if isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            if attr in ["execute", "run", "invoke", "dispatch", "delegate"]:
                # Get the variable being called
                if isinstance(node.func.value, ast.Subscript):
                    # agents[role].execute()
                    if isinstance(node.func.value.value, ast.Name):
                        container = node.func.value.value.id
                        self.delegation_patterns.append(
                            {
                                "type": "agent_dispatch",
                                "container": container,
                                "method": attr,
                                "parent_function": self._current_function,
                                "is_async": self._current_is_async,
                                "lineno": node.lineno,
                            }
                        )
                elif isinstance(node.func.value, ast.Name):
                    # executor.run(task)
                    executor = node.func.value.id
                    if any(
                        kw in executor.lower()
                        for kw in ["executor", "agent", "worker", "handler"]
                    ):
                        self.delegation_patterns.append(
                            {
                                "type": "executor_dispatch",
                                "executor": executor,
                                "method": attr,
                                "parent_function": self._current_function,
                                "is_async": self._current_is_async,
                                "lineno": node.lineno,
                            }
                        )
        self.generic_visit(node)


class SequentialDetector(ast.NodeVisitor):
    """Detect sequential pipeline patterns.

    Detects:
    - Chained function calls: result = step3(step2(step1(data)))
    - Sequential assignments: r1 = step1(data); r2 = step2(r1); r3 = step3(r2)
    - Pipeline patterns with await chains
    """

    def __init__(self) -> None:
        self.sequential_patterns: list[dict[str, Any]] = []
        self._current_function: str | None = None
        self._current_is_async: bool = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = False
        self._check_sequential_chain(node)
        self.generic_visit(node)
        self._current_function = None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = True
        self._check_sequential_chain(node)
        self.generic_visit(node)
        self._current_function = None

    def _check_sequential_chain(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Check for sequential assignment chains."""
        assigns: list[tuple[str, str, int]] = []  # (target, func_name, lineno)

        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                # r = func(...)
                if len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                    target = stmt.targets[0].id
                    func_name = self._extract_func_name(stmt.value)
                    if func_name:
                        assigns.append((target, func_name, stmt.lineno))

            elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Await):
                # await func(...)
                if isinstance(stmt.value.value, ast.Call):
                    func_name = self._extract_func_name(stmt.value.value)
                    if func_name:
                        assigns.append(("_", func_name, stmt.lineno))

        # Check for chains where output becomes input
        if len(assigns) >= 3:
            steps = [a[1] for a in assigns]
            self.sequential_patterns.append(
                {
                    "type": "assignment_chain",
                    "steps": steps,
                    "parent_function": self._current_function,
                    "is_async": self._current_is_async,
                    "lineno": assigns[0][2],
                    "step_count": len(assigns),
                }
            )

    def visit_Call(self, node: ast.Call) -> None:
        """Detect nested function calls: step3(step2(step1(data)))."""
        chain = self._extract_call_chain(node)
        if len(chain) >= 3:
            self.sequential_patterns.append(
                {
                    "type": "nested_calls",
                    "steps": list(reversed(chain)),  # Innermost first
                    "parent_function": self._current_function,
                    "is_async": self._current_is_async,
                    "lineno": node.lineno,
                    "step_count": len(chain),
                }
            )
        self.generic_visit(node)

    def _extract_call_chain(self, node: ast.expr) -> list[str]:
        """Extract chain of nested calls."""
        chain: list[str] = []

        def walk(n: ast.expr) -> None:
            if isinstance(n, ast.Call):
                func_name = self._extract_func_name(n)
                if func_name:
                    chain.append(func_name)
                # Check first argument for nested call
                if n.args and isinstance(n.args[0], ast.Call):
                    walk(n.args[0])

        walk(node)
        return chain

    def _extract_func_name(self, node: ast.expr) -> str | None:
        """Extract function name from Call or Await."""
        if isinstance(node, ast.Await):
            node = node.value

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr
        return None


class AdaptiveDetector(ast.NodeVisitor):
    """Detect patterns that benefit from adaptive/learning behavior.

    Detects:
    - Success/failure tracking with counters
    - Parameter adjustment based on results
    - Strategy selection with metrics
    """

    def __init__(self) -> None:
        self.adaptive_patterns: list[dict[str, Any]] = []
        self._current_function: str | None = None
        self._current_is_async: bool = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = False
        self._check_adaptive_patterns(node)
        self.generic_visit(node)
        self._current_function = None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._current_function = node.name
        self._current_is_async = True
        self._check_adaptive_patterns(node)
        self.generic_visit(node)
        self._current_function = None

    def _check_adaptive_patterns(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Check for adaptive/learning patterns in function."""
        has_counter = False
        has_conditional_adjust = False
        counter_vars: list[str] = []

        for stmt in ast.walk(node):
            # Look for counter increments: success_count += 1, failures += 1
            if isinstance(stmt, ast.AugAssign):
                if isinstance(stmt.target, ast.Name):
                    var = stmt.target.id.lower()
                    if any(
                        kw in var
                        for kw in ["count", "success", "fail", "error", "metric"]
                    ):
                        has_counter = True
                        counter_vars.append(stmt.target.id)

            # Look for conditional parameter adjustment
            if isinstance(stmt, ast.If):
                # Check if condition references counters/rates
                cond_str = ast.dump(stmt.test)
                if any(
                    kw in cond_str.lower()
                    for kw in ["rate", "count", "threshold", "metric"]
                ):
                    # Check if body adjusts parameters
                    for body_stmt in stmt.body:
                        if isinstance(body_stmt, ast.Assign):
                            has_conditional_adjust = True

        if has_counter and has_conditional_adjust:
            self.adaptive_patterns.append(
                {
                    "type": "metric_based_adjustment",
                    "counter_vars": counter_vars,
                    "parent_function": self._current_function,
                    "is_async": self._current_is_async,
                    "lineno": node.lineno,
                }
            )

    def visit_Assign(self, node: ast.Assign) -> None:
        """Detect strategy dictionaries with performance data."""
        # Pattern: strategies = {"fast": {..., "success_rate": 0.9}, ...}
        if isinstance(node.value, ast.Dict):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var = target.id.lower()
                    if any(
                        kw in var for kw in ["strateg", "config", "option", "variant"]
                    ):
                        # Check if dict values have metrics-like keys
                        has_metrics = False
                        for v in node.value.values:
                            if isinstance(v, ast.Dict):
                                for k in v.keys:
                                    if isinstance(k, ast.Constant):
                                        key_str = str(k.value).lower()
                                        if any(
                                            m in key_str
                                            for m in [
                                                "rate",
                                                "latency",
                                                "score",
                                                "weight",
                                            ]
                                        ):
                                            has_metrics = True
                                            break

                        if has_metrics:
                            self.adaptive_patterns.append(
                                {
                                    "type": "strategy_config",
                                    "variable": target.id,
                                    "parent_function": self._current_function,
                                    "is_async": self._current_is_async,
                                    "lineno": node.lineno,
                                }
                            )
        self.generic_visit(node)


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
            "CompensationPrimitive": "from tta_dev_primitives.recovery import CompensationPrimitive",
            "MemoryPrimitive": "from tta_dev_primitives.performance import MemoryPrimitive",
            "DelegationPrimitive": "from tta_dev_primitives.orchestration import DelegationPrimitive",
            "AdaptivePrimitive": "from tta_dev_primitives.adaptive import AdaptivePrimitive",
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

    def _transform_circuit_breaker_ast(
        self, code: str, tree: ast.Module
    ) -> dict[str, Any]:
        """Transform functions with multiple exception handlers into CircuitBreakerPrimitive."""
        changes = []
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

    def _transform_circuit_breaker_fallback(
        self, code: str, tree: ast.Module
    ) -> dict[str, Any]:
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

    def _transform_compensation_ast(
        self, code: str, tree: ast.Module
    ) -> dict[str, Any]:
        """Transform saga/compensation patterns into CompensationPrimitive."""
        changes = []
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

    def _transform_compensation_fallback(
        self, code: str, tree: ast.Module
    ) -> dict[str, Any]:
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
            wrapper_code = self._generate_compensation_wrapper(
                func_name, is_async, cleanup_actions
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
        cleanup_str = (
            ", ".join(cleanup_actions) if cleanup_actions else "cleanup operation"
        )

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
        message_appends = [
            p for p in detector.memory_patterns if p["type"] == "message_append"
        ]
        dict_storages = [
            p for p in detector.memory_patterns if p["type"] == "dict_storage"
        ]
        deque_histories = [
            p for p in detector.memory_patterns if p["type"] == "deque_history"
        ]

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
