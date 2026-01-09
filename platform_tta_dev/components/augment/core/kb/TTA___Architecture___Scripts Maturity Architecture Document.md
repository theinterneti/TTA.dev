---
title: Component Maturity Automation System - Architecture
tags: #TTA
status: Active
repo: theinterneti/TTA
path: scripts/maturity/ARCHITECTURE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Architecture/Component Maturity Automation System - Architecture]]

**Version:** 1.0
**Created:** 2025-10-21
**Status:** Design Complete

---

## Problem Statement

Component MATURITY.md files are manually maintained and become stale, leading to:
- Incorrect planning decisions (Carbon showed 73.2% coverage, actual was 50.46%)
- Wasted effort on wrong remediation strategies
- Loss of trust in maturity tracking system
- Manual toil updating metrics after every change

**Solution:** Automated system that keeps MATURITY.md files synchronized with actual code quality metrics.

---

## System Architecture

### Components

```
scripts/maturity/
├── __init__.py
├── metrics_collector.py      # Collect quality metrics programmatically
├── maturity_parser.py         # Parse existing MATURITY.md files
├── maturity_generator.py      # Generate updated MATURITY.md content
├── MATURITY_TEMPLATE.md       # Template for new components
└── README.md                  # System documentation

scripts/
└── update_component_maturity.py  # Main CLI script

.pre-commit-config.yaml        # Integration with pre-commit hooks
```

### Data Flow

```
Component Code Changes
         ↓
Pre-commit Hook Triggered
         ↓
update_component_maturity.py
         ↓
metrics_collector.py → Run pytest, ruff, pyright, bandit
         ↓
MetricsResult Object (coverage, linting, type errors, security)
         ↓
maturity_parser.py → Parse existing MATURITY.md
         ↓
maturity_generator.py → Generate updated sections
         ↓
Merge Manual + Automated Sections
         ↓
Write Updated MATURITY.md
         ↓
Auto-stage for Commit
```

---

## MATURITY.md Structure

### Section Types

**AUTOMATED SECTIONS** (updated by script):
- Header metadata (Current Stage, Last Updated)
- Test Coverage percentage and status
- Code Quality Status (linting, type checking, security)
- Maturity Criteria checklist (auto-checked based on thresholds)

**MANUAL SECTIONS** (preserved as-is):
- Component Overview
- Key Features
- Dependencies
- Next Steps
- Promotion History
- Related Documentation
- Verification Commands

### Section Markers

Use HTML comments to mark section boundaries:

```markdown
<!-- AUTO-GENERATED: DO NOT EDIT BELOW THIS LINE -->
## Test Coverage

**Current**: 73.2% ✅
**Target**: 70%
**Last Updated**: 2025-10-21

<!-- END AUTO-GENERATED -->

<!-- MANUAL SECTION -->
## Component Overview

**Purpose**: Carbon emissions tracking for TTA system
...
<!-- END MANUAL SECTION -->
```

---

## Metrics Collection

### Coverage

```python
def collect_coverage(component_path: str, test_path: str) -> CoverageMetrics:
    """
    Run pytest with coverage and parse JSON output.

    Command: uv run pytest {test_path} --cov={component_path} --cov-report=json
    Parse: .coverage.json → extract coverage percentage
    """
```

**Output:**
```python
@dataclass
class CoverageMetrics:
    percentage: float
    lines_covered: int
    lines_total: int
    missing_lines: list[int]
    timestamp: datetime
```

### Linting

```python
def collect_linting(component_path: str) -> LintingMetrics:
    """
    Run ruff check and parse JSON output.

    Command: uvx ruff check {component_path} --output-format=json
    Parse: JSON → count violations by severity
    """
```

**Output:**
```python
@dataclass
class LintingMetrics:
    total_violations: int
    by_severity: dict[str, int]  # {"error": 5, "warning": 10}
    by_rule: dict[str, int]      # {"PLC0415": 20, "PLR0912": 5}
    timestamp: datetime
```

### Type Checking

```python
def collect_type_checking(component_path: str) -> TypeCheckingMetrics:
    """
    Run pyright and parse JSON output.

    Command: uvx pyright {component_path} --outputjson
    Parse: JSON → count errors, warnings, information
    """
```

**Output:**
```python
@dataclass
class TypeCheckingMetrics:
    errors: int
    warnings: int
    information: int
    timestamp: datetime
```

### Security

```python
def collect_security(component_path: str) -> SecurityMetrics:
    """
    Run bandit and parse JSON output.

    Command: uvx bandit -r {component_path} -f json
    Parse: JSON → count issues by severity
    """
```

**Output:**
```python
@dataclass
class SecurityMetrics:
    total_issues: int
    by_severity: dict[str, int]  # {"HIGH": 0, "MEDIUM": 2, "LOW": 5}
    timestamp: datetime
```

### Test Status

```python
def collect_test_status(test_path: str) -> TestMetrics:
    """
    Run pytest and get pass/fail counts.

    Command: uv run pytest {test_path} --json-report
    Parse: JSON → extract passed, failed, skipped counts
    """
```

**Output:**
```python
@dataclass
class TestMetrics:
    passed: int
    failed: int
    skipped: int
    total: int
    timestamp: datetime
```

### Combined Result

```python
@dataclass
class MetricsResult:
    component_name: str
    coverage: CoverageMetrics
    linting: LintingMetrics
    type_checking: TypeCheckingMetrics
    security: SecurityMetrics
    tests: TestMetrics
    timestamp: datetime

    def meets_staging_criteria(self) -> bool:
        """Check if component meets dev→staging promotion criteria."""
        return (
            self.coverage.percentage >= 70.0 and
            self.linting.total_violations == 0 and
            self.type_checking.errors == 0 and
            self.security.total_issues == 0 and
            self.tests.failed == 0
        )
```

---

## Maturity Criteria Thresholds

### Development → Staging

- ✅ Test coverage ≥70%
- ✅ Linting violations = 0
- ✅ Type checking errors = 0
- ✅ Security issues = 0
- ✅ All tests passing
- ✅ API documented (manual check)
- ✅ Component README exists (manual check)

### Staging → Production

- ✅ Integration test coverage ≥80%
- ✅ All integration tests passing
- ✅ Performance meets SLAs (manual check)
- ✅ 7-day uptime ≥99.5% (manual check)
- ✅ Security review complete (manual check)
- ✅ Monitoring configured (manual check)
- ✅ Rollback procedure tested (manual check)

---

## CLI Interface

### Commands

```bash
# Update specific component
python scripts/update_component_maturity.py --component carbon

# Update all components
python scripts/update_component_maturity.py --all

# Validate MATURITY.md matches reality (CI mode)
python scripts/update_component_maturity.py --component carbon --validate

# Create MATURITY.md for new component
python scripts/update_component_maturity.py --component new_component --create

# Dry run (show changes without writing)
python scripts/update_component_maturity.py --component carbon --dry-run

# Verbose output
python scripts/update_component_maturity.py --component carbon --verbose
```

### Exit Codes

- `0`: Success
- `1`: Validation failed (MATURITY.md is stale)
- `2`: Metrics collection failed
- `3`: Component not found
- `4`: Invalid arguments

---

## Integration Points

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: update-component-maturity
      name: Update Component Maturity Files
      entry: python scripts/update_component_maturity.py --auto
      language: system
      files: ^src/components/.*\.py$
      pass_filenames: false
      stages: [commit]
```

**Behavior:**
- Runs when any `src/components/**/*.py` file changes
- Updates corresponding MATURITY.md
- Auto-stages updated MATURITY.md
- Completes in <10 seconds

### CI/CD Pipeline

```yaml
# .github/workflows/quality.yml
- name: Validate Component Maturity
  run: |
    python scripts/update_component_maturity.py --all --validate
```

**Behavior:**
- Runs on every PR
- Validates all MATURITY.md files match reality
- Fails CI if any are stale
- Forces developers to keep metrics current

### Manual Usage

Developers can run manually:
```bash
# After making changes to a component
python scripts/update_component_maturity.py --component carbon

# Before creating promotion request
python scripts/update_component_maturity.py --component carbon --validate
```

---

## Error Handling

### Tool Failures

If a quality tool fails (e.g., pytest crashes):
1. Log error with full traceback
2. Preserve last known good metrics
3. Add warning banner to MATURITY.md
4. Continue with other metrics
5. Exit with non-zero code

### Missing MATURITY.md

If component has no MATURITY.md:
1. Create from template
2. Populate with current metrics
3. Set stage to "Development"
4. Add TODO for manual sections

### Stale Manual Edits

If manual sections are edited in automated areas:
1. Warn user
2. Overwrite with automated content
3. Log what was overwritten
4. Suggest moving to manual section

---

## Performance Targets

- **Single component update**: <30 seconds
- **All components update**: <5 minutes (parallel execution)
- **Pre-commit hook**: <10 seconds (only changed components)
- **CI validation**: <2 minutes (parallel validation)

---

## Future Enhancements

1. **Trend Tracking**: Store historical metrics, show trends
2. **Regression Detection**: Alert if coverage drops >5%
3. **Dashboard**: Web UI showing all component maturity
4. **Slack Integration**: Post updates to #dev-quality channel
5. **Auto-promotion**: Create GitHub Issues for components meeting criteria

---

## Success Metrics

- ✅ MATURITY.md files always accurate (0 stale files)
- ✅ No manual metric updates required
- ✅ Developers trust maturity status
- ✅ Planning decisions based on accurate data
- ✅ Pre-commit hook adoption >90%
- ✅ CI validation catches all stale files

---

**Status**: Design Complete ✅
**Next**: Implement metrics_collector.py


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___architecture___scripts maturity architecture document]]
