"""Resilience AST NodeTransformer subclasses: CircuitBreaker, Compensation."""

import ast
from typing import Any


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
        core_func = self._create_core_function(func_name, try_body, is_async, node.lineno)

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
                            value=ast.Name(id=f"{func_name}_compensation", ctx=ast.Load()),
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
