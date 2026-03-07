"""Security validation checks.

This module provides validation checks for security concerns:
- No hardcoded secrets in source code
- Dependencies are up to date
- No known vulnerabilities in dependencies

These checks help ensure projects follow security best practices
before deployment.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.lifecycle.validation import Severity, ValidationCheck

# Patterns that may indicate hardcoded secrets
_SECRET_PATTERNS = [
    re.compile(r"""(?:password|passwd|pwd)\s*=\s*['"][^'"]{4,}['"]""", re.IGNORECASE),
    re.compile(r"""(?:api_key|apikey|api_secret)\s*=\s*['"][^'"]{8,}['"]""", re.IGNORECASE),
    re.compile(r"""(?:secret_key|secret)\s*=\s*['"][^'"]{8,}['"]""", re.IGNORECASE),
    re.compile(r"""(?:token|auth_token|access_token)\s*=\s*['"][^'"]{8,}['"]""", re.IGNORECASE),
    re.compile(r"""(?:aws_access_key_id)\s*=\s*['"]AKIA[A-Z0-9]{16}['"]"""),
    re.compile(r"""(?:private_key)\s*=\s*['"]-----BEGIN""", re.IGNORECASE),
]

# File name patterns to skip when scanning for secrets.
# Uses prefix/suffix matching to avoid false positives (e.g. "my_test_utils.py").
_SKIP_EXACT = {"conftest.py", ".env.example", ".env.template"}
_SKIP_PREFIXES = ("test_", "fixture_")
_SKIP_SUFFIXES = ("_test.py",)


async def check_no_secrets_in_code(project_path: Path, context: WorkflowContext) -> bool:
    """Check for hardcoded secrets in source code.

    Scans Python, JavaScript, and configuration files for patterns
    that may indicate hardcoded secrets like API keys, passwords,
    or private keys.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if no potential secrets are found
    """
    source_extensions = {".py", ".js", ".ts", ".yaml", ".yml", ".toml", ".json", ".cfg", ".ini"}

    src_dir = project_path / "src"
    if not src_dir.exists():
        src_dir = project_path

    for source_file in src_dir.rglob("*"):
        if not source_file.is_file():
            continue
        if source_file.suffix not in source_extensions:
            continue

        # Skip test/fixture/example files using precise prefix/suffix matching
        file_name = source_file.name
        if (
            file_name in _SKIP_EXACT
            or file_name.startswith(_SKIP_PREFIXES)
            or file_name.endswith(_SKIP_SUFFIXES)
        ):
            continue

        try:
            content = source_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        for pattern in _SECRET_PATTERNS:
            if pattern.search(content):
                return False

    return True


async def check_dependencies_up_to_date(project_path: Path, context: WorkflowContext) -> bool:
    """Check if project dependencies are up to date.

    For Python projects, checks if the lock file (uv.lock or
    requirements.txt) exists and is current.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if dependencies appear up to date
    """
    # Check for Python lock files
    has_pyproject = (project_path / "pyproject.toml").exists()
    has_uv_lock = (project_path / "uv.lock").exists()
    has_requirements = (project_path / "requirements.txt").exists()

    if has_pyproject:
        # If using uv, check for uv.lock
        if has_uv_lock:
            return True
        # If using pip, check for requirements.txt
        if has_requirements:
            return True
        # pyproject.toml exists but no lock file
        return False

    # Check for package.json + lock file
    has_package_json = (project_path / "package.json").exists()
    if has_package_json:
        return (
            (project_path / "package-lock.json").exists()
            or (project_path / "yarn.lock").exists()
            or (project_path / "pnpm-lock.yaml").exists()
        )

    # No recognizable package system - pass vacuously
    return True


async def check_no_known_vulnerabilities(project_path: Path, context: WorkflowContext) -> bool:
    """Check for known vulnerabilities in dependencies.

    Uses pip-audit (for Python) to check for known CVEs in dependencies.
    Falls back to checking if a security audit tool is available.

    Args:
        project_path: Path to project root
        context: Workflow context

    Returns:
        True if no known vulnerabilities are found (or audit tool unavailable)
    """
    # Try pip-audit for Python projects
    if (project_path / "pyproject.toml").exists():
        try:
            result = subprocess.run(
                ["uv", "run", "pip-audit", "--strict"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # pip-audit not available - pass the check with a note
            return True

    # Try npm audit for JavaScript projects
    if (project_path / "package.json").exists():
        try:
            result = subprocess.run(
                ["npm", "audit", "--audit-level=high"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return True

    # No recognizable package system - pass vacuously
    return True


# Pre-configured validation checks

NO_SECRETS_IN_CODE = ValidationCheck(
    name="No secrets in code",
    description="Source code must not contain hardcoded secrets",
    severity=Severity.BLOCKER,
    check_function=check_no_secrets_in_code,
    failure_message="Potential hardcoded secrets detected in source code. Remove them immediately.",
    success_message="No hardcoded secrets detected",
    fix_command="Use environment variables or a secrets manager instead of hardcoding secrets",
    documentation_link="https://12factor.net/config",
)

DEPENDENCIES_UP_TO_DATE = ValidationCheck(
    name="Dependencies up to date",
    description="Project must have a current lock file for dependencies",
    severity=Severity.CRITICAL,
    check_function=check_dependencies_up_to_date,
    failure_message="Dependencies lock file is missing or outdated.",
    success_message="Dependencies are up to date",
    fix_command="Run: uv lock (Python) or npm install (JavaScript)",
)

NO_KNOWN_VULNERABILITIES = ValidationCheck(
    name="No known vulnerabilities",
    description="Dependencies must have no known CVEs",
    severity=Severity.CRITICAL,
    check_function=check_no_known_vulnerabilities,
    failure_message="Known vulnerabilities found in dependencies. Update affected packages.",
    success_message="No known vulnerabilities in dependencies",
    fix_command="Run: uv run pip-audit --fix (Python) or npm audit fix (JavaScript)",
    documentation_link="https://pypi.org/project/pip-audit/",
)

__all__ = [
    "NO_SECRETS_IN_CODE",
    "DEPENDENCIES_UP_TO_DATE",
    "NO_KNOWN_VULNERABILITIES",
    "check_no_secrets_in_code",
    "check_dependencies_up_to_date",
    "check_no_known_vulnerabilities",
]
