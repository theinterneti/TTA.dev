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
        """Detect which transformations are needed based on anti-patterns."""
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
        """Apply a specific transformation to the code."""
        if transform_type == "RetryPrimitive":
            return self._transform_retry(code)
        elif transform_type == "TimeoutPrimitive":
            return self._transform_timeout(code)
        elif transform_type == "FallbackPrimitive":
            return self._transform_fallback(code)
        elif transform_type == "ParallelPrimitive":
            return self._transform_parallel(code)
        elif transform_type == "RouterPrimitive":
            return self._transform_router(code)
        else:
            return {"changed": False, "code": code, "changes": []}

    def _transform_retry(self, code: str) -> dict[str, Any]:
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

    def _transform_timeout(self, code: str) -> dict[str, Any]:
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

    def _transform_fallback(self, code: str) -> dict[str, Any]:
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

    def _transform_parallel(self, code: str) -> dict[str, Any]:
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

    def _transform_router(self, code: str) -> dict[str, Any]:
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
