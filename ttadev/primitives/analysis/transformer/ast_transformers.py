"""Core AST NodeTransformer subclasses: Retry, Timeout, Fallback, Gather."""

import ast
from typing import Any


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
        core_func = self._create_core_function(func_name, try_body, is_async, node.lineno)

        # Create the RetryPrimitive assignment
        primitive_assign = self._create_primitive_assignment(func_name, max_retries, is_async)

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
        docstring = ast.Expr(value=ast.Constant(value=f"Core operation for {func_name}."))

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
                ast.keyword(arg="backoff_strategy", value=ast.Constant(value="exponential")),
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
                        ast.keyword(arg="timeout_seconds", value=ast.Constant(value=timeout)),
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

    def _create_fallback_call(self, primary: str, fallback: str, lineno: int) -> ast.stmt:
        """Create a return statement that executes a FallbackPrimitive workflow."""
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
