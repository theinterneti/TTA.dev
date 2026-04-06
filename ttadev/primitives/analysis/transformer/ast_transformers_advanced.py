"""Advanced AST NodeTransformer subclasses: Router, Cache."""

import ast
from typing import Any


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

    def _create_router_call(self, routes: dict[str, str], var_name: str, lineno: int) -> ast.Return:
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
                        ast.keyword(arg="default", value=ast.Constant(value=default_key)),
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
        core_func = self._create_core_function(func_name, fetch_body, is_async, node.lineno)

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
                        fetch_body = node.body[i + 1 :] if i + 1 < len(node.body) else []
                        # Filter out cache assignment statements
                        fetch_body = [s for s in fetch_body if not self._is_cache_assignment(s)]
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
