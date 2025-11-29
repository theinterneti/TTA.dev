#!/usr/bin/env python3
"""
TTA.dev Primitive Usage Validator

Validates that code uses TTA.dev primitives instead of anti-patterns.
Uses AST analysis to detect manual asyncio orchestration.

Usage:
    python scripts/validate-primitive-usage.py [--fix]

Exit codes:
    0 - All checks passed
    1 - Validation errors found
    2 - Critical errors (can't parse files)
"""

import ast
import sys
from pathlib import Path
from typing import Any


class PrimitiveUsageChecker(ast.NodeVisitor):
    """AST visitor to check for proper TTA.dev primitive usage."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.errors: list[dict[str, Any]] = []
        self.warnings: list[dict[str, Any]] = []
        self.line_offset = 0

    def add_error(self, node: ast.AST, message: str, suggestion: str = ""):
        """Add an error with line number."""
        self.errors.append({
            "line": node.lineno,
            "col": node.col_offset,
            "message": message,
            "suggestion": suggestion,
            "severity": "error"
        })

    def add_warning(self, node: ast.AST, message: str, suggestion: str = ""):
        """Add a warning with line number."""
        self.warnings.append({
            "line": node.lineno,
            "col": node.col_offset,
            "message": message,
            "suggestion": suggestion,
            "severity": "warning"
        })

    def visit_Call(self, node: ast.Call) -> None:
        """Check function calls for anti-patterns."""
        # Check for asyncio.gather()
        if self._is_asyncio_call(node, "gather"):
            self.add_warning(
                node,
                "Direct asyncio.gather() usage detected",
                "Use ParallelPrimitive or | operator instead:\n"
                "  workflow = primitive1 | primitive2 | primitive3"
            )

        # Check for asyncio.create_task()
        elif self._is_asyncio_call(node, "create_task"):
            self.add_warning(
                node,
                "Direct asyncio.create_task() usage detected",
                "Use ParallelPrimitive for concurrent execution"
            )

        # Check for asyncio.wait_for()
        elif self._is_asyncio_call(node, "wait_for"):
            self.add_warning(
                node,
                "Direct asyncio.wait_for() usage detected",
                "Use TimeoutPrimitive instead:\n"
                "  TimeoutPrimitive(primitive=..., timeout_seconds=...)"
            )

        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Check for manual retry loops."""
        # Check if this is a retry loop pattern
        if self._is_retry_loop(node):
            self.add_warning(
                node,
                "Manual retry loop detected",
                "Use RetryPrimitive instead:\n"
                "  RetryPrimitive(primitive=..., max_retries=3, backoff_strategy='exponential')"
            )

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Check async function definitions."""
        # Check for manual async orchestration
        if self._has_manual_orchestration(node):
            self.add_warning(
                node,
                f"Function '{node.name}' appears to manually orchestrate async operations",
                "Consider using SequentialPrimitive (>>) or ParallelPrimitive (|)"
            )

        self.generic_visit(node)

    def _is_asyncio_call(self, node: ast.Call, method_name: str) -> bool:
        """Check if call is to asyncio.method_name()."""
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == method_name:
                # Check if it's asyncio module
                if isinstance(node.func.value, ast.Name):
                    if node.func.value.id == "asyncio":
                        return True
        return False

    def _is_retry_loop(self, node: ast.For) -> bool:
        """Detect manual retry loop patterns."""
        # Check if loop variable is named like 'attempt', 'retry', 'i'
        if isinstance(node.target, ast.Name):
            retry_names = {"attempt", "retry", "i", "tries"}
            if node.target.id in retry_names:
                # Check for try/except inside loop
                for child in node.body:
                    if isinstance(child, ast.Try):
                        return True
        return False

    def _has_manual_orchestration(self, node: ast.AsyncFunctionDef) -> bool:
        """Check if function manually orchestrates async operations."""
        # Count await statements
        await_count = sum(
            1 for child in ast.walk(node)
            if isinstance(child, ast.Await)
        )

        # If multiple awaits in sequence, might be manual orchestration
        # This is a heuristic - not perfect
        return await_count >= 3


def validate_file(file_path: Path, verbose: bool = False) -> tuple[int, int]:
    """
    Validate a single Python file.

    Returns:
        (error_count, warning_count)
    """
    # Get relative path safely
    try:
        rel_path = file_path.relative_to(Path.cwd())
    except ValueError:
        rel_path = file_path

    if verbose:
        print(f"🔍 Checking: {rel_path}")

    try:
        content = file_path.read_text()
        tree = ast.parse(content, filename=str(file_path))
    except SyntaxError as e:
        print(f"❌ Syntax error in {file_path}: {e}")
        return (1, 0)
    except Exception as e:
        print(f"❌ Error parsing {file_path}: {e}")
        return (1, 0)

    checker = PrimitiveUsageChecker(file_path)
    checker.visit(tree)

    # Report errors
    if checker.errors:
        print(f"\n❌ {rel_path}:")
        for error in checker.errors:
            print(f"  Line {error['line']}: {error['message']}")
            if error['suggestion']:
                print(f"    → {error['suggestion']}")

    # Report warnings
    if checker.warnings:
        if verbose or not checker.errors:
            print(f"\n⚠️  {rel_path}:")
        for warning in checker.warnings:
            print(f"  Line {warning['line']}: {warning['message']}")
            if warning['suggestion']:
                for line in warning['suggestion'].split('\n'):
                    print(f"    → {line}")

    return (len(checker.errors), len(checker.warnings))



def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped."""
    # Skip test files (they can use asyncio directly)
    if "test_" in file_path.name or file_path.name.startswith("test_"):
        return True

    # Skip __init__.py
    if file_path.name == "__init__.py":
        return True

    # Skip files with "# allowed" comment for asyncio
    try:
        content = file_path.read_text()
        if "# allowed: asyncio" in content or "# pragma: allow-asyncio" in content:
            return True
    except Exception:
        pass

    return False


def validate_packages(verbose: bool = False) -> tuple[int, int]:
    """
    Validate all Python files in packages/ directory.

    Returns:
        (total_errors, total_warnings)
    """
    packages_dir = Path("packages")
    if not packages_dir.exists():
        print("❌ packages/ directory not found")
        return (1, 0)

    total_errors = 0
    total_warnings = 0
    files_checked = 0

    print("🔍 Validating TTA.dev primitive usage...\n")

    # Walk through all Python files in packages
    for py_file in packages_dir.rglob("*.py"):
        # Skip test files and special files
        if should_skip_file(py_file):
            if verbose:
                try:
                    rel_path = py_file.relative_to(Path.cwd())
                except ValueError:
                    rel_path = py_file
                print(f"⏭️  Skipping: {rel_path}")
            continue

        errors, warnings = validate_file(py_file, verbose)
        total_errors += errors
        total_warnings += warnings
        files_checked += 1

    # Print summary
    print("\n" + "=" * 60)
    print(f"📊 Validation Summary:")
    print(f"   Files checked: {files_checked}")
    print(f"   Errors: {total_errors}")
    print(f"   Warnings: {total_warnings}")
    print("=" * 60)

    if total_errors == 0 and total_warnings == 0:
        print("\n✅ All checks passed! Code follows TTA.dev primitive patterns.")
        return (0, 0)
    elif total_errors == 0:
        print("\n⚠️  Warnings found. Consider updating code to use primitives.")
        return (0, total_warnings)
    else:
        print("\n❌ Errors found. Please fix before committing.")
        return (total_errors, total_warnings)


def print_usage():
    """Print usage information."""
    print(__doc__)
    print("\nOptions:")
    print("  -v, --verbose    Show detailed output")
    print("  -h, --help       Show this help message")
    print("\nExamples:")
    print("  python scripts/validate-primitive-usage.py")
    print("  python scripts/validate-primitive-usage.py --verbose")


def main():
    """Main entry point."""
    import sys

    verbose = False

    # Parse arguments
    for arg in sys.argv[1:]:
        if arg in ("-h", "--help"):
            print_usage()
            return 0
        elif arg in ("-v", "--verbose"):
            verbose = True
        else:
            print(f"Unknown argument: {arg}")
            print_usage()
            return 2

    errors, warnings = validate_packages(verbose)

    # Exit with appropriate code
    if errors > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
