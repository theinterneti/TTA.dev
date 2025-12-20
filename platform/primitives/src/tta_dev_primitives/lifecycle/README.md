# Development Lifecycle Meta-Framework

A composable, language-agnostic framework for managing software development lifecycle stages with automated validation and readiness checks.

## Overview

The Lifecycle Meta-Framework provides structured stage transitions with validation checks that ensure projects meet quality standards before progressing through development stages:

```
EXPERIMENTATION → TESTING → STAGING → DEPLOYMENT → PRODUCTION
```

## Features

- **Language-Agnostic Core**: Universal validation framework works with any programming language
- **Composable Primitives**: Built on TTA.dev workflow primitives for reliability and observability
- **Parallel Validation**: All checks run concurrently using `asyncio.gather()`
- **Staged Transitions**: Clear criteria for each stage transition
- **Rich Feedback**: Detailed reports with fix commands and documentation links
- **Force Override**: Emergency override for forced transitions (use with caution)

## Quick Start

```python
from pathlib import Path
from tta_dev_primitives.lifecycle import (
    StageManager,
    Stage,
    WorkflowContext,
    STAGE_CRITERIA_MAP,
)

# Initialize stage manager
context = WorkflowContext(
    correlation_id="lifecycle-check",
    data={"project_path": Path("/path/to/project")}
)

manager = StageManager()

# Check readiness for transition
project_path = Path("/path/to/project")
readiness = await manager.check_readiness(
    project_path=project_path,
    from_stage=Stage.STAGING,
    to_stage=Stage.DEPLOYMENT,
    context=context
)

print(readiness.get_summary())

# Attempt transition
if readiness.is_ready():
    result = await manager.transition(
        project_path=project_path,
        from_stage=Stage.STAGING,
        to_stage=Stage.DEPLOYMENT,
        context=context
    )
    print(f"✅ Transitioned to {result.to_stage}")
```

## Architecture

### Core Components

#### 1. Stage (`stage.py`)

Defines lifecycle stages and ordering:

```python
class Stage(str, Enum):
    EXPERIMENTATION = "experimentation"  # Prototyping, rapid iteration
    TESTING = "testing"                  # Automated tests, type checking
    STAGING = "staging"                  # Pre-production validation
    DEPLOYMENT = "deployment"            # Ready for production
    PRODUCTION = "production"            # Live in production
```

#### 2. ValidationCheck (`validation.py`)

Defines validation checks with severity levels:

```python
@dataclass
class ValidationCheck:
    name: str
    description: str
    severity: Severity  # BLOCKER, CRITICAL, WARNING, INFO
    check_function: Callable[[Path, WorkflowContext], Awaitable[bool]]
    failure_message: str
    success_message: str
    fix_command: str | None = None
    documentation_link: str | None = None
```

#### 3. StageCriteria (`stage_criteria.py`)

Defines entry and exit criteria for stage transitions:

```python
@dataclass
class StageCriteria:
    stage: Stage
    entry_criteria: list[ValidationCheck]
    exit_criteria: list[ValidationCheck]
    recommended_actions: list[str]
    description: str
```

#### 4. StageManager (`stage_manager.py`)

Main orchestration primitive for managing transitions:

```python
class StageManager(WorkflowPrimitive[StageTransitionInput, TransitionResult]):
    async def check_readiness(
        self,
        project_path: Path,
        from_stage: Stage,
        to_stage: Stage,
        context: WorkflowContext
    ) -> StageReadiness:
        """Check if project is ready for stage transition."""
        ...

    async def transition(
        self,
        project_path: Path,
        from_stage: Stage,
        to_stage: Stage,
        context: WorkflowContext,
        force: bool = False
    ) -> TransitionResult:
        """Attempt stage transition with validation."""
        ...
```

## Language-Agnostic Design

The framework separates universal checks from language-specific checks:

### Generic Checks (`checks/generic.py`)

Universal checks that work across all languages:

- ✅ **HAS_PACKAGE_MANIFEST**: Checks for `pyproject.toml`, `package.json`, `Cargo.toml`, etc.
- ✅ **HAS_README**: Checks for README.md or README.rst
- ✅ **HAS_LICENSE**: Checks for LICENSE file
- ✅ **HAS_TESTS_DIRECTORY**: Checks for tests/ directory
- ✅ **HAS_SRC_DIRECTORY**: Checks for src/ or lib/ directory, or source files

### Python-Specific Checks (`checks/python.py`)

Python-specific quality checks:

- ✅ **TESTS_PASS**: Runs `pytest` to verify all tests pass
- ✅ **TYPE_CHECK_PASSES**: Runs `pyright` for type checking
- ✅ **LINT_PASSES**: Runs `ruff check` for linting
- ✅ **FORMAT_CHECK_PASSES**: Runs `ruff format --check` for formatting

### Adding Checks for Other Languages

Create a new module in `checks/` directory:

```python
# checks/javascript.py
"""JavaScript/TypeScript-specific validation checks."""

import subprocess
from pathlib import Path
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.lifecycle.validation import Severity, ValidationCheck

async def check_jest_tests_pass(project_path: Path, context: WorkflowContext) -> bool:
    """Check if Jest tests pass."""
    result = subprocess.run(
        ["npm", "test"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    return result.returncode == 0

async def check_eslint_passes(project_path: Path, context: WorkflowContext) -> bool:
    """Check if ESLint passes."""
    result = subprocess.run(
        ["npx", "eslint", "."],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    return result.returncode == 0

async def check_tsc_passes(project_path: Path, context: WorkflowContext) -> bool:
    """Check if TypeScript compiler passes."""
    result = subprocess.run(
        ["npx", "tsc", "--noEmit"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    return result.returncode == 0

# Pre-configured checks
JEST_TESTS_PASS = ValidationCheck(
    name="Jest tests pass",
    description="All Jest tests must pass",
    severity=Severity.BLOCKER,
    check_function=check_jest_tests_pass,
    failure_message="Jest tests are failing. Fix tests before proceeding.",
    success_message="All Jest tests pass",
    fix_command="Run: npm test",
    documentation_link="https://jestjs.io/",
)

ESLINT_PASSES = ValidationCheck(
    name="ESLint passes",
    description="Code must pass ESLint checks",
    severity=Severity.BLOCKER,
    check_function=check_eslint_passes,
    failure_message="ESLint found issues. Fix linting errors.",
    success_message="ESLint passed",
    fix_command="Run: npx eslint . --fix",
    documentation_link="https://eslint.org/",
)

TSC_PASSES = ValidationCheck(
    name="TypeScript compiler passes",
    description="TypeScript code must compile without errors",
    severity=Severity.BLOCKER,
    check_function=check_tsc_passes,
    failure_message="TypeScript compilation failed.",
    success_message="TypeScript compilation passed",
    fix_command="Run: npx tsc --noEmit",
    documentation_link="https://www.typescriptlang.org/",
)

__all__ = [
    "JEST_TESTS_PASS",
    "ESLINT_PASSES",
    "TSC_PASSES",
    "check_jest_tests_pass",
    "check_eslint_passes",
    "check_tsc_passes",
]
```

Then update `checks/__init__.py` to import and export your checks:

```python
from tta_dev_primitives.lifecycle.checks.javascript import (
    JEST_TESTS_PASS,
    ESLINT_PASSES,
    TSC_PASSES,
)

__all__ = [
    # ... existing checks ...
    # JavaScript-specific checks
    "JEST_TESTS_PASS",
    "ESLINT_PASSES",
    "TSC_PASSES",
]
```

## Predefined Stage Criteria

The framework includes predefined criteria for each transition in `stages.py`:

### EXPERIMENTATION → TESTING

**Entry Criteria:**
- Package manifest exists (pyproject.toml, package.json, etc.)
- Source code exists (src/, lib/, or source files)

**Exit Criteria:**
- tests/ directory exists
- All tests pass
- Type checking passes

**Recommended Actions:**
- Write unit tests for core functionality
- Add type hints to all functions
- Run tests to verify they pass
- Use type checker to validate types

### TESTING → STAGING

**Entry Criteria:**
- All tests pass
- Type checking passes

**Exit Criteria:**
- README exists
- LICENSE exists
- Linting passes
- Code formatting passes

**Recommended Actions:**
- Write comprehensive README
- Choose and add license
- Fix linting issues
- Format code consistently

### STAGING → DEPLOYMENT

**Entry Criteria:**
- README exists
- All tests pass
- Linting passes

**Exit Criteria:**
- LICENSE exists (critical)
- Code formatting passes (warning)

**Recommended Actions:**
- Add LICENSE file
- Update CHANGELOG with release notes
- Bump version in package manifest
- Scan for secrets in code
- Create git tag for release
- Run final quality checks

### DEPLOYMENT → PRODUCTION

**Entry Criteria:**
- All tests pass
- LICENSE exists

**Exit Criteria:**
- Code formatting passes (warning)

**Recommended Actions:**
- Monitor production logs
- Set up alerts and monitoring
- Document deployment process
- Create rollback plan
- Verify production environment

## Validation Severity Levels

```python
class Severity(str, Enum):
    BLOCKER = "blocker"      # Must fix to proceed (prevents transition)
    CRITICAL = "critical"    # Should fix soon (allows transition with warning)
    WARNING = "warning"      # Should address eventually
    INFO = "info"            # Informational only
```

## Example Output

```
============================================================
Stage Transition: Staging → Deployment
Status: ❌ NOT READY
============================================================

🚫 BLOCKERS (2):
  • No README.md or README.rst found. Documentation is required.
    Fix: Create README.md with project description
  • Linting failed. Fix linting errors before proceeding.
    Fix: Run: uv run ruff check . --fix

⚠️  CRITICAL ISSUES (1):
  • No LICENSE file found. License is required for deployment.
    Fix: Add LICENSE file (MIT or Apache 2.0 recommended)

📋 NEXT STEPS:
  1. README exists: Create README.md with project description
  2. Linting passes: Run: uv run ruff check . --fix
  3. LICENSE exists: Add LICENSE file (MIT or Apache 2.0 recommended)

💡 RECOMMENDED ACTIONS:
  • Add LICENSE file (MIT or Apache 2.0 recommended)
  • Update CHANGELOG with release notes
  • Bump version in pyproject.toml
  • Scan for secrets in code
  • Create git tag for release
  • Run final quality checks

============================================================
```

## Advanced Usage

### Custom Stage Criteria

Create custom criteria for your workflow:

```python
from tta_dev_primitives.lifecycle import StageCriteria, Stage
from tta_dev_primitives.lifecycle.checks import (
    HAS_README,
    HAS_LICENSE,
    TESTS_PASS,
)

CUSTOM_STAGING_CRITERIA = StageCriteria(
    stage=Stage.STAGING,
    entry_criteria=[TESTS_PASS],
    exit_criteria=[HAS_README, HAS_LICENSE],
    recommended_actions=[
        "Review code with team",
        "Update documentation",
        "Test in staging environment",
    ],
    description="Custom staging validation for our team"
)
```

### Custom Validation Checks

Create custom checks for your needs:

```python
from pathlib import Path
from tta_dev_primitives.lifecycle.validation import ValidationCheck, Severity
from tta_dev_primitives.core.base import WorkflowContext

async def check_docker_file_exists(project_path: Path, context: WorkflowContext) -> bool:
    """Check if Dockerfile exists."""
    return (project_path / "Dockerfile").exists()

HAS_DOCKERFILE = ValidationCheck(
    name="Dockerfile exists",
    description="Project must have a Dockerfile for containerization",
    severity=Severity.CRITICAL,
    check_function=check_docker_file_exists,
    failure_message="No Dockerfile found. Add Dockerfile for deployment.",
    success_message="Dockerfile found",
    fix_command="Create Dockerfile",
    documentation_link="https://docs.docker.com/engine/reference/builder/",
)
```

### Force Override

For emergency situations, you can force a transition:

```python
# ⚠️  Use with extreme caution!
result = await manager.transition(
    project_path=project_path,
    from_stage=Stage.STAGING,
    to_stage=Stage.DEPLOYMENT,
    context=context,
    force=True  # Override blockers
)

print(f"⚠️  Forced transition with {len(result.readiness.blockers)} blockers overridden")
```

## Integration with Existing Tools

The framework can be integrated with existing CI/CD pipelines:

```python
# CI/CD pipeline script
import sys
from pathlib import Path
from tta_dev_primitives.lifecycle import StageManager, Stage, WorkflowContext

async def validate_deployment():
    context = WorkflowContext(correlation_id="ci-cd-check")
    manager = StageManager()
    project_path = Path.cwd()

    readiness = await manager.check_readiness(
        project_path=project_path,
        from_stage=Stage.STAGING,
        to_stage=Stage.DEPLOYMENT,
        context=context
    )

    if not readiness.is_ready():
        print(readiness.get_summary())
        sys.exit(1)

    print("✅ Ready for deployment!")
    sys.exit(0)
```

## Testing

The framework includes comprehensive test coverage:

```bash
# Run all lifecycle tests
uv run pytest packages/tta-dev-primitives/tests/lifecycle/ -v

# Run with coverage
uv run pytest packages/tta-dev-primitives/tests/lifecycle/ --cov=tta_dev_primitives.lifecycle
```

## See Also

- **Examples**: [`examples/lifecycle_demo.py`](../../examples/lifecycle_demo.py)
- **Issue #30**: [Development Lifecycle Meta-Framework](https://github.com/theinterneti/TTA.dev/issues/30)
- **TTA.dev Primitives**: Core workflow primitives documentation
- **WorkflowContext**: Context management documentation

## Contributing

When adding new language-specific checks:

1. Create a new module in `checks/` (e.g., `rust.py`, `go.py`)
2. Follow the pattern in `python.py`
3. Use async functions with subprocess for tool execution
4. Export all checks in `__all__`
5. Update `checks/__init__.py` to import and export your checks
6. Add tests for your checks
7. Update this README with examples

## License

See individual package licenses in TTA.dev monorepo.
