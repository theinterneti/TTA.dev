"""Pre-built validation checks for lifecycle stages.

This module provides ready-to-use validation checks organized by type:
- generic: Language-agnostic checks (README, LICENSE, structure)
- python: Python-specific checks (pytest, ruff, pyright)

## Extending for Other Languages

To add checks for a new language, create a new module (e.g., `javascript.py`, `rust.py`)
following this pattern:

```python
# lifecycle/checks/javascript.py
from pathlib import Path
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.lifecycle.validation import Severity, ValidationCheck

async def check_jest_tests_pass(project_path: Path, context: WorkflowContext) -> bool:
    \"\"\"Check if Jest tests pass.\"\"\"
    result = subprocess.run(
        ["npm", "test"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    return result.returncode == 0

JEST_TESTS_PASS = ValidationCheck(
    name="Jest tests pass",
    description="All Jest tests must pass",
    severity=Severity.BLOCKER,
    check_function=check_jest_tests_pass,
    failure_message="Jest tests are failing. Fix tests before proceeding.",
    success_message="All Jest tests pass",
    fix_command="Run: npm test",
)
```

Then import and export your checks from this `__init__.py` file.
"""

from tta_dev_primitives.lifecycle.checks.generic import (
    HAS_LICENSE,
    HAS_PACKAGE_MANIFEST,
    HAS_README,
    HAS_SRC_DIRECTORY,
    HAS_TESTS_DIRECTORY,
)
from tta_dev_primitives.lifecycle.checks.python import (
    FORMAT_CHECK_PASSES,
    LINT_PASSES,
    TESTS_PASS,
    TYPE_CHECK_PASSES,
)

__all__ = [
    # Generic checks (language-agnostic)
    "HAS_PACKAGE_MANIFEST",
    "HAS_README",
    "HAS_LICENSE",
    "HAS_TESTS_DIRECTORY",
    "HAS_SRC_DIRECTORY",
    # Python-specific checks
    "TESTS_PASS",
    "TYPE_CHECK_PASSES",
    "LINT_PASSES",
    "FORMAT_CHECK_PASSES",
]
