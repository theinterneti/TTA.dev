---
applyTo: "scripts/workflow/**"
description: "Quality gate implementation guidance and thresholds for TTA workflow"
---

# TTA Quality Gates Instructions

## Overview

Quality gates are automated checks that enforce maturity criteria before components can be promoted to higher stages. They ensure consistent quality across the TTA codebase and prevent deployment of non-compliant components.

## Quality Gate Framework

### Gate Types

1. **TestCoverageGate** - Validates test coverage meets threshold
2. **TestPassRateGate** - Validates all tests pass
3. **LintingGate** - Validates code linting (ruff)
4. **TypeCheckingGate** - Validates type checking (pyright)
5. **SecurityGate** - Validates security scanning (detect-secrets)

### Gate Interface

All quality gates implement the `QualityGate` interface:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class GateResult:
    """Result of a quality gate check."""
    passed: bool
    gate_name: str
    threshold: float | None
    actual_value: float | None
    message: str
    details: dict[str, Any]

class QualityGate(ABC):
    """Base class for quality gates."""

    def __init__(self, component_path: Path, threshold: float | None = None):
        self.component_path = component_path
        self.threshold = threshold

    @abstractmethod
    def check(self) -> GateResult:
        """Execute the quality gate check."""
        pass
```

## Coverage Thresholds

### By Maturity Stage

```python
COVERAGE_THRESHOLDS = {
    "development": 60.0,   # ≥60% for dev stage
    "staging": 70.0,       # ≥70% for staging stage
    "production": 80.0,    # ≥80% for production stage
}
```

### Implementation

```python
class TestCoverageGate(QualityGate):
    """Validates test coverage meets threshold."""

    def check(self) -> GateResult:
        """Run coverage check."""
        # Find test paths (supports multiple patterns)
        test_paths = self._find_test_paths()

        # Run pytest with coverage
        result = subprocess.run(
            [
                "uv", "run", "pytest",  # Use uv run for project env
                *test_paths,
                f"--cov=src/{self.component_path.name}",
                "--cov-report=json",
                "--cov-report=term",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Parse coverage from JSON report
        coverage_data = self._parse_coverage_json()
        coverage_percent = coverage_data.get("totals", {}).get("percent_covered", 0.0)

        # Check against threshold
        passed = coverage_percent >= self.threshold

        return GateResult(
            passed=passed,
            gate_name="test_coverage",
            threshold=self.threshold,
            actual_value=coverage_percent,
            message=f"Coverage: {coverage_percent:.1f}% (threshold: {self.threshold}%)",
            details={
                "total_statements": coverage_data.get("totals", {}).get("num_statements", 0),
                "covered_statements": coverage_data.get("totals", {}).get("covered_lines", 0),
                "missing_lines": coverage_data.get("totals", {}).get("missing_lines", 0),
            }
        )
```

## Test Discovery Patterns

Quality gates support flexible test organization:

### Supported Patterns

1. **Directory-based:** `tests/<component_name>/`
2. **Single file:** `tests/test_<component_name>.py`
3. **Pattern-based:** `tests/test_<component_name>_*.py`
4. **Name variations:** Handle suffix transformations (e.g., orchestration → orchestrator)

### Implementation

```python
def _find_test_paths(self) -> list[str]:
    """Find test paths with naming variation support."""
    component_name = self.component_path.name
    test_paths = []

    # Generate naming variations
    name_variations = [component_name]
    if component_name.endswith('ion'):
        name_variations.append(component_name.rstrip('ion') + 'or')
    if component_name.endswith('tion'):
        name_variations.append(component_name.rstrip('tion') + 'tor')

    for name_var in name_variations:
        # Pattern 1: Directory-based
        dir_path = Path("tests") / name_var
        if dir_path.exists() and dir_path.is_dir():
            test_paths.append(str(dir_path))

        # Pattern 2: Single file
        single_file = Path("tests") / f"test_{name_var}.py"
        if single_file.exists():
            test_paths.append(str(single_file))

        # Pattern 3: Pattern-based
        pattern_files = list(Path("tests").glob(f"test_{name_var}_*.py"))
        test_paths.extend([str(f) for f in pattern_files])

    # Fallback to default pattern
    if not test_paths:
        test_paths = [f"tests/{component_name}/"]

    return test_paths
```

## Test Pass Rate Gate

### Implementation

```python
class TestPassRateGate(QualityGate):
    """Validates all tests pass."""

    def check(self) -> GateResult:
        """Run test pass rate check."""
        test_paths = self._find_test_paths()

        # Run pytest
        result = subprocess.run(
            [
                "uv", "run", "pytest",
                *test_paths,
                "-v",
                "--tb=short",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Parse test results
        passed, failed, total = self._parse_test_output(result.stdout)
        pass_rate = (passed / total * 100) if total > 0 else 0.0

        return GateResult(
            passed=(failed == 0),
            gate_name="test_pass_rate",
            threshold=100.0,  # All tests must pass
            actual_value=pass_rate,
            message=f"Tests: {passed}/{total} passed ({pass_rate:.1f}%)",
            details={
                "passed": passed,
                "failed": failed,
                "total": total,
                "failures": self._extract_failures(result.stdout) if failed > 0 else [],
            }
        )
```

## Linting Gate

### Implementation

```python
class LintingGate(QualityGate):
    """Validates code linting with ruff."""

    def __init__(self, component_path: Path, auto_fix: bool = False):
        super().__init__(component_path)
        self.auto_fix = auto_fix

    def check(self) -> GateResult:
        """Run linting check."""
        paths = [
            f"src/{self.component_path.name}/",
            f"tests/test_{self.component_path.name}.py",
        ]

        # Auto-fix if enabled
        if self.auto_fix:
            subprocess.run(
                ["uvx", "ruff", "check", "--fix", *paths],
                capture_output=True,
            )
            subprocess.run(
                ["uvx", "ruff", "format", *paths],
                capture_output=True,
            )

        # Run linting check
        result = subprocess.run(
            ["uvx", "ruff", "check", *paths],
            capture_output=True,
            text=True,
        )

        issues = self._parse_ruff_output(result.stdout)

        return GateResult(
            passed=(result.returncode == 0),
            gate_name="linting",
            threshold=None,
            actual_value=len(issues),
            message=f"Linting: {len(issues)} issues found",
            details={
                "issues": issues,
                "auto_fixed": self.auto_fix,
            }
        )
```

## Type Checking Gate

### Implementation

```python
class TypeCheckingGate(QualityGate):
    """Validates type checking with pyright."""

    def check(self) -> GateResult:
        """Run type checking."""
        result = subprocess.run(
            ["uvx", "pyright", f"src/{self.component_path.name}/"],
            capture_output=True,
            text=True,
        )

        errors = self._parse_pyright_output(result.stdout)

        return GateResult(
            passed=(result.returncode == 0),
            gate_name="type_checking",
            threshold=None,
            actual_value=len(errors),
            message=f"Type checking: {len(errors)} errors found",
            details={
                "errors": errors,
            }
        )
```

## Security Gate

### Implementation

```python
class SecurityGate(QualityGate):
    """Validates security scanning with detect-secrets."""

    def check(self) -> GateResult:
        """Run security scan."""
        result = subprocess.run(
            ["uvx", "detect-secrets", "scan", "--baseline", ".secrets.baseline"],
            capture_output=True,
            text=True,
        )

        secrets = self._parse_detect_secrets_output(result.stdout)

        return GateResult(
            passed=(len(secrets) == 0),
            gate_name="security",
            threshold=None,
            actual_value=len(secrets),
            message=f"Security: {len(secrets)} potential secrets found",
            details={
                "secrets": secrets,
            }
        )
```

## Quality Gate Orchestration

### Running Gates

```python
def run_quality_gates(
    component_path: Path,
    target_stage: str,
    auto_fix: bool = False
) -> dict[str, GateResult]:
    """Run all quality gates for a component."""
    results = {}

    # Get threshold for target stage
    coverage_threshold = COVERAGE_THRESHOLDS.get(target_stage, 70.0)

    # Run gates
    gates = [
        TestCoverageGate(component_path, coverage_threshold),
        TestPassRateGate(component_path),
        LintingGate(component_path, auto_fix),
        TypeCheckingGate(component_path),
        SecurityGate(component_path),
    ]

    for gate in gates:
        result = gate.check()
        results[result.gate_name] = result

    return results
```

### Reporting Results

```python
def report_quality_gates(results: dict[str, GateResult]) -> None:
    """Report quality gate results."""
    print("\n" + "="*60)
    print("QUALITY GATE RESULTS")
    print("="*60)

    all_passed = True
    for gate_name, result in results.items():
        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"\n{status} - {gate_name.upper()}")
        print(f"  {result.message}")

        if not result.passed:
            all_passed = False
            if result.details:
                print(f"  Details: {result.details}")

    print("\n" + "="*60)
    if all_passed:
        print("✓ ALL QUALITY GATES PASSED")
    else:
        print("✗ SOME QUALITY GATES FAILED")
    print("="*60 + "\n")
```

## Best Practices

### Gate Implementation

✅ **DO:**
- Use `uv run pytest` for tests (accesses project dependencies)
- Use `uvx` for standalone tools (ruff, pyright, detect-secrets)
- Support flexible test discovery patterns
- Provide detailed error messages
- Include actionable details in gate results
- Implement auto-fix for linting when possible
- Use appropriate timeouts for subprocess calls
- Handle edge cases (no tests found, empty files, etc.)

❌ **DON'T:**
- Use `uvx pytest` (runs in isolated environment without dependencies)
- Hardcode test paths (use discovery patterns)
- Fail silently (always provide clear error messages)
- Skip validation of subprocess results
- Ignore edge cases
- Use arbitrary timeouts (calculate based on expected duration)

### Threshold Configuration

✅ **DO:**
- Use configuration files for thresholds (`workflow_config.yaml`)
- Allow component-specific overrides
- Document threshold rationale
- Adjust thresholds based on component maturity
- Track threshold changes over time

❌ **DON'T:**
- Hardcode thresholds in gate implementations
- Use same threshold for all components
- Change thresholds without documentation
- Lower thresholds to pass gates (fix the code instead)

### Error Handling

✅ **DO:**
- Catch and handle subprocess errors
- Provide context in error messages
- Log errors for debugging
- Return structured error information
- Fail gracefully with clear messages

❌ **DON'T:**
- Let exceptions propagate uncaught
- Return generic error messages
- Swallow errors silently
- Assume subprocess success
- Use bare except clauses

## Troubleshooting

### Common Issues

**Issue: Tests not found**
```
Solution: Check test discovery patterns
- Verify test file naming (test_<component>.py)
- Check for naming variations (orchestration vs orchestrator)
- Ensure tests directory exists
- Review _find_test_paths() logic
```

**Issue: Coverage calculation incorrect**
```
Solution: Verify coverage scope
- Check --cov argument (should be src/<component>)
- Ensure tests are running (not skipped)
- Verify coverage.json is generated
- Check for test collection errors
```

**Issue: Linting fails after auto-fix**
```
Solution: Review auto-fix limitations
- Some issues require manual fixes
- Check for conflicting rules
- Review ruff configuration
- Run ruff check --fix manually to debug
```

**Issue: Type checking errors**
```
Solution: Address type issues
- Add type hints to functions
- Fix type mismatches
- Use proper type imports
- Review pyright configuration
```

## Configuration

### Workflow Config (`workflow_config.yaml`)

```yaml
quality_gates:
  test_coverage:
    development_threshold: 60.0
    staging_threshold: 70.0
    production_threshold: 80.0

  linting:
    auto_fix: true
    tools:
      - ruff

  type_checking:
    tool: pyright
    strict: false

  security:
    tool: detect-secrets
    baseline: .secrets.baseline
```

### Component-Specific Overrides

```yaml
components:
  orchestration:
    quality_gates:
      test_coverage:
        staging_threshold: 75.0  # Higher threshold for critical component

  player_experience:
    quality_gates:
      test_coverage:
        staging_threshold: 65.0  # Lower threshold for UI component
```

---

**Last Updated:** 2025-10-20
**Status:** Active
**Applies To:** Quality gate implementations in `scripts/workflow/`
