"""Pre-built validation checks for lifecycle stages.

This module provides ready-to-use validation checks for common
project requirements.
"""

from tta_dev_primitives.lifecycle.checks.code_quality import (
    FORMAT_CHECK_PASSES,
    LINT_PASSES,
    TESTS_PASS,
    TYPE_CHECK_PASSES,
)
from tta_dev_primitives.lifecycle.checks.package_structure import (
    HAS_LICENSE,
    HAS_PYPROJECT_TOML,
    HAS_README,
    HAS_SRC_DIRECTORY,
    HAS_TESTS_DIRECTORY,
)

__all__ = [
    # Package structure checks
    "HAS_PYPROJECT_TOML",
    "HAS_README",
    "HAS_LICENSE",
    "HAS_TESTS_DIRECTORY",
    "HAS_SRC_DIRECTORY",
    # Code quality checks
    "TESTS_PASS",
    "TYPE_CHECK_PASSES",
    "LINT_PASSES",
    "FORMAT_CHECK_PASSES",
]
