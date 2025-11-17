"""Python-specific validation checks.

This module provides validation checks specific to Python projects:
- pytest for test execution
- pyright for type checking
- ruff for linting and formatting

For other languages, create similar modules (e.g., javascript.py, rust.py)
with language-appropriate tools:
- JavaScript: jest, eslint, tsc
- Rust: cargo test, clippy, rustfmt
- Go: go test, golangci-lint, gofmt
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.lifecycle.validation import Severity, ValidationCheck


async def check_tests_pass(project_path: Path, context: WorkflowContext) -> bool:
    """Check if all tests pass.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if pytest runs successfully
    """
    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "-q"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


async def check_type_checking_passes(project_path: Path, context: WorkflowContext) -> bool:
    """Check if type checking passes.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if pyright passes
    """
    try:
        result = subprocess.run(
            ["uvx", "pyright", "."],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


async def check_linting_passes(project_path: Path, context: WorkflowContext) -> bool:
    """Check if linting passes.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if ruff check passes
    """
    try:
        result = subprocess.run(
            ["uv", "run", "ruff", "check", "."],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


async def check_formatting_passes(project_path: Path, context: WorkflowContext) -> bool:
    """Check if code formatting passes.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if ruff format --check passes
    """
    try:
        result = subprocess.run(
            ["uv", "run", "ruff", "format", "--check", "."],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# Pre-configured validation checks

TESTS_PASS = ValidationCheck(
    name="All tests pass",
    description="All unit and integration tests must pass",
    severity=Severity.BLOCKER,
    check_function=check_tests_pass,
    failure_message="Tests are failing. All tests must pass before deployment.",
    success_message="All tests passing",
    fix_command="Run: uv run pytest -v",
    documentation_link="https://docs.pytest.org/",
)

TYPE_CHECK_PASSES = ValidationCheck(
    name="Type checking passes",
    description="Type checking with pyright must pass",
    severity=Severity.BLOCKER,
    check_function=check_type_checking_passes,
    failure_message="Type checking failed. Fix type errors before proceeding.",
    success_message="Type checking passed",
    fix_command="Run: uvx pyright . --outputjson",
    documentation_link="https://microsoft.github.io/pyright/",
)

LINT_PASSES = ValidationCheck(
    name="Linting passes",
    description="Code linting with ruff must pass",
    severity=Severity.BLOCKER,
    check_function=check_linting_passes,
    failure_message="Linting failed. Fix linting errors before proceeding.",
    success_message="Linting passed",
    fix_command="Run: uv run ruff check . --fix",
    documentation_link="https://docs.astral.sh/ruff/",
)

FORMAT_CHECK_PASSES = ValidationCheck(
    name="Formatting check passes",
    description="Code formatting with ruff must be consistent",
    severity=Severity.CRITICAL,
    check_function=check_formatting_passes,
    failure_message="Code formatting is inconsistent. Format code before proceeding.",
    success_message="Code formatting is consistent",
    fix_command="Run: uv run ruff format .",
    documentation_link="https://docs.astral.sh/ruff/formatter/",
)

# Export all checks
__all__ = [
    "TESTS_PASS",
    "TYPE_CHECK_PASSES",
    "LINT_PASSES",
    "FORMAT_CHECK_PASSES",
    "check_tests_pass",
    "check_type_checking_passes",
    "check_linting_passes",
    "check_formatting_passes",
]
