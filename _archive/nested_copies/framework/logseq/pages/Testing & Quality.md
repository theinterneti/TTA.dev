# Testing & Quality

**Testing infrastructure and quality assurance for TTA.dev.**

## Overview

TTA.dev maintains high quality standards with comprehensive testing and automated quality checks.

## Testing Infrastructure

### Test Framework
- [[TTA.dev/Testing]] - Testing best practices
- **Framework:** pytest with pytest-asyncio
- **Coverage:** 100% coverage requirement
- **Location:** `packages/*/tests/`, `tests/`

### Test Types

**Unit Tests:**
- Fast, isolated tests
- Mock external dependencies
- Test individual primitives
- Use [[TTA.dev/Primitives/MockPrimitive]]

**Integration Tests:**
- Test workflow composition
- Real primitive interactions
- End-to-end scenarios
- Marked with `@pytest.mark.integration`

**Property-Based Tests:**
- Hypothesis for generative testing
- Edge case discovery
- Fuzz testing

## Quality Checks

### Automated Checks
- [[TTA.dev/CI-CD Pipeline]] - CI/CD automation
- **Linting:** Ruff (`uv run ruff check .`)
- **Formatting:** Ruff (`uv run ruff format .`)
- **Type Checking:** Pyright (`uvx pyright packages/`)

### CI/CD Workflows
- `.github/workflows/python-tests.yml` - Test execution
- `.github/workflows/quality.yml` - Quality checks
- `.github/workflows/kb-validation.yml` - KB validation

### Coverage Requirements
- **Minimum:** 100% for new code
- **Reports:** HTML coverage reports in `htmlcov/`
- **Command:** `uv run pytest --cov=packages --cov-report=html`

## Quality Standards

### Code Quality
- Type hints on all public APIs
- Docstrings on all public functions/classes
- No complex functions (max 15 lines recommended)
- Clear variable names

### Documentation Quality
- All primitives documented in [[PRIMITIVES CATALOG]]
- Examples for all public APIs
- Architecture decisions recorded in `docs/architecture/`

### Test Quality
- Test success cases
- Test failure cases
- Test edge cases
- Clear test names describing behavior

## Related Pages

- [[TTA.dev/Testing]] - Testing hub
- [[TTA.dev/CI-CD Pipeline]] - Automation
- [[Contributors]] - Contributing standards
- [[TTA.dev/Development/Coding Standards]] - Code standards

## Documentation

- `docs/TESTING_GUIDE.md` - Complete testing guide
- `docs/TESTING_QUICKREF.md` - Quick reference
- `docs/TESTING_METHODOLOGY_SUMMARY.md` - Methodology

## Tags

quality:: testing
automation:: ci-cd
standards:: high

- [[Project Hub]]

---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Testing & quality]]
