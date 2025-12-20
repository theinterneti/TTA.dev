#!/usr/bin/env python3
# pragma: allow-asyncio
"""
TTA.dev Custom Checker for Ruff Integration

This checker provides TTA-specific rules that can be run alongside Ruff.
While Ruff doesn't support external plugins, this provides equivalent
functionality through a standalone checker that can be integrated into
the development workflow.

Rules:
- TTA001: Prefer ParallelPrimitive over asyncio.gather()
- TTA002: Require WorkflowContext in primitive execute() calls
- TTA003: Use RetryPrimitive instead of manual retry loops
- TTA004: Use TimeoutPrimitive instead of asyncio.wait_for()
- TTA005: Use CachePrimitive for repeated expensive operations

Usage:
    python scripts/ruff_tta_checker.py                    # Check all packages
    python scripts/ruff_tta_checker.py <file>            # Check specific file
    python scripts/ruff_tta_checker.py --fix <file>      # Auto-fix violations
"""

import ast
import sys
from pathlib import Path
from typing import Any


class TTAChecker(ast.NodeVisitor):
    """AST-based checker for TTA.dev coding standards."""

    def __init__(self, filename: str, tree: ast.AST):
        self.filename = filename
        self.tree = tree
        self.violations: list[dict[str, Any]] = []

    def visit_Call(self, node: ast.Call) -> None:
        """Check function calls for TTA violations."""
        # TTA001: asyncio.gather() should use ParallelPrimitive
        if self._is_asyncio_call(node, "gather"):
            self.violations.append(
                {
                    "code": "TTA001",
                    "line": node.lineno,
                    "col": node.col_offset,
                    "message": "TTA001 Prefer ParallelPrimitive over asyncio.gather()",
                    "hint": "Use ParallelPrimitive([func1, func2]) or func1 | func2",
                }
            )

        # TTA004: asyncio.wait_for() should use TimeoutPrimitive
        if self._is_asyncio_call(node, "wait_for"):
            self.violations.append(
                {
                    "code": "TTA004",
                    "line": node.lineno,
                    "col": node.col_offset,
                    "message": "TTA004 Use TimeoutPrimitive instead of asyncio.wait_for()",
                    "hint": "Use TimeoutPrimitive(primitive, timeout_seconds=30)",
                }
            )

        # TTA002: Check execute() calls have WorkflowContext
        if self._is_execute_call(node):
            if not self._has_workflow_context_arg(node):
                self.violations.append(
                    {
                        "code": "TTA002",
                        "line": node.lineno,
                        "col": node.col_offset,
                        "message": "TTA002 Primitive execute() calls should pass WorkflowContext",
                        "hint": "Use: await primitive.execute(data, WorkflowContext())",
                    }
                )

        self.generic_visit(node)

    def visit_For(self, node: ast.For | ast.While) -> None:
        """Check for manual retry loops."""
        # TTA003: Manual retry loops should use RetryPrimitive
        if self._is_retry_loop(node):
            self.violations.append(
                {
                    "code": "TTA003",
                    "line": node.lineno,
                    "col": node.col_offset,
                    "message": "TTA003 Use RetryPrimitive instead of manual retry loop",
                    "hint": "Use: RetryPrimitive(primitive, max_retries=3, backoff_strategy='exponential')",
                }
            )

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Check for cache opportunities."""
        # TTA005: Functions with expensive operations should consider caching
        if self._has_expensive_operations(node):
            # Only suggest, don't enforce
            self.violations.append(
                {
                    "code": "TTA005",
                    "line": node.lineno,
                    "col": node.col_offset,
                    "message": f"TTA005 Consider CachePrimitive for expensive operation in {node.name}",
                    "hint": "Use: CachePrimitive(primitive, ttl_seconds=3600, max_size=1000)",
                    "severity": "info",
                }
            )

        self.generic_visit(node)

    def _is_asyncio_call(self, node: ast.Call, func_name: str) -> bool:
        """Check if call is asyncio.<func_name>()."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id == "asyncio" and node.func.attr == func_name
        return False

    def _is_execute_call(self, node: ast.Call) -> bool:
        """Check if call is a .execute() method."""
        if isinstance(node.func, ast.Attribute):
            return node.func.attr == "execute"
        return False

    def _has_workflow_context_arg(self, node: ast.Call) -> bool:
        """Check if execute() call has WorkflowContext argument."""
        # Check if any argument is WorkflowContext() call
        for arg in node.args:
            if isinstance(arg, ast.Call):
                if isinstance(arg.func, ast.Name):
                    if arg.func.id == "WorkflowContext":
                        return True
            # Also check for variable that might be WorkflowContext
            if isinstance(arg, ast.Name):
                if "context" in arg.id.lower():
                    return True
        return False

    def _is_retry_loop(self, node: ast.For | ast.While) -> bool:
        """Check if loop is a manual retry pattern."""
        # Look for try/except inside loop with break on success
        has_try_except = False
        has_break = False

        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                has_try_except = True
            if isinstance(child, ast.Break):
                has_break = True

        # Also check for range(N) pattern
        is_range_loop = False
        if isinstance(node, ast.For):
            if isinstance(node.iter, ast.Call):
                if isinstance(node.iter.func, ast.Name):
                    if node.iter.func.id == "range":
                        is_range_loop = True

        return has_try_except and (has_break or is_range_loop)

    def _has_expensive_operations(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """Check if function has operations that might benefit from caching."""
        # Look for LLM calls, API calls, database queries
        expensive_patterns = [
            "openai",
            "anthropic",
            "gemini",
            "llm",
            "model",
            "api",
            "fetch",
            "query",
            "execute_query",
        ]

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if any(
                        pattern in child.func.attr.lower()
                        for pattern in expensive_patterns
                    ):
                        return True
                if isinstance(child.func, ast.Name):
                    if any(
                        pattern in child.func.id.lower() for pattern in expensive_patterns
                    ):
                        return True
        return False


def check_file(filepath: Path) -> list[dict[str, Any]]:
    """Check a single file for TTA violations."""
    try:
        content = filepath.read_text()
        tree = ast.parse(content, filename=str(filepath))

        checker = TTAChecker(str(filepath), tree)
        checker.visit(tree)

        return checker.violations
    except SyntaxError as e:
        return [
            {
                "code": "SYNTAX",
                "line": e.lineno or 0,
                "col": e.offset or 0,
                "message": f"Syntax error: {e.msg}",
                "severity": "error",
            }
        ]
    except Exception as e:
        return [
            {
                "code": "ERROR",
                "line": 0,
                "col": 0,
                "message": f"Error processing file: {e}",
                "severity": "error",
            }
        ]


def check_packages(packages_dir: Path = Path("packages")) -> dict[str, list[dict[str, Any]]]:
    """Check all Python files in packages directory."""
    results = {}

    for py_file in packages_dir.rglob("*.py"):
        # Skip test files, examples, and virtual environments
        skip_patterns = ["/tests/", "/examples/", "/.venv/", "/venv/", "/__pycache__/"]
        if any(pattern in str(py_file) for pattern in skip_patterns):
            continue

        violations = check_file(py_file)
        if violations:
            try:
                rel_path = py_file.relative_to(Path.cwd())
            except ValueError:
                rel_path = py_file

            results[str(rel_path)] = violations

    return results


def format_violation(filepath: str, violation: dict[str, Any]) -> str:
    """Format a violation for display."""
    severity = violation.get("severity", "error")
    code = violation["code"]
    line = violation["line"]
    col = violation["col"]
    message = violation["message"]

    # Color codes
    colors = {
        "error": "\033[91m",  # Red
        "warning": "\033[93m",  # Yellow
        "info": "\033[94m",  # Blue
        "reset": "\033[0m",
    }

    color = colors.get(severity, colors["error"])
    reset = colors["reset"]

    output = f"{filepath}:{line}:{col}: {color}{code}{reset} {message}"

    if "hint" in violation:
        output += f"\n    {colors['info']}💡 Hint:{reset} {violation['hint']}"

    return output


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="TTA.dev Custom Checker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to check (default: all packages)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to auto-fix violations (not yet implemented)",
    )

    args = parser.parse_args()

    if args.fix:
        print("⚠️  Auto-fix not yet implemented")
        return 1

    if args.files:
        # Check specific files
        all_violations = {}
        for filepath in args.files:
            path = Path(filepath)
            if not path.exists():
                print(f"❌ File not found: {filepath}")
                continue

            violations = check_file(path)
            if violations:
                all_violations[filepath] = violations
    else:
        # Check all packages
        all_violations = check_packages()

    # Display results
    if not all_violations:
        print("✅ No TTA violations found!")
        return 0

    total_violations = 0
    for filepath, violations in sorted(all_violations.items()):
        for violation in violations:
            print(format_violation(filepath, violation))
            total_violations += 1

    print()
    print(f"Found {total_violations} TTA violation(s) in {len(all_violations)} file(s)")
    print()
    print("💡 Run with specific file: python scripts/ruff_tta_checker.py <file>")
    print("📚 See docs: .github/AGENT_CHECKLIST.md")

    return 1 if total_violations > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
