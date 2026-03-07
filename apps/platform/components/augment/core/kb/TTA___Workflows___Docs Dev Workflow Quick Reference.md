---
title: Development Workflow Quick Reference
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/dev-workflow-quick-reference.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Development Workflow Quick Reference]]

**Last Updated:** 2025-10-06
**Tooling Version:** Ruff 0.13.0, Pyright 1.1.350+, UV 0.8.17
**Type Checker:** Pyright (migrated from MyPy for 10-100x faster performance)

---

## Quick Start

### Before You Commit
```bash
# Quick check (2-3 seconds) - fixes issues and runs failed tests
./scripts/dev.sh dev-check

# Full validation (6-7 seconds) - lint, format check, type check, all tests
./scripts/dev.sh check-all
```

### Common Tasks
```bash
# Fix all linting and formatting issues
./scripts/dev.sh quality-fix

# Run tests with coverage
./scripts/dev.sh test-cov

# Type check manually
./scripts/dev.sh typecheck
```

---

## Pyright vs Pylance Clarification

**Important:** Pyright and Pylance are related but distinct tools:

- **Pylance** = VS Code extension (includes Pyright engine + IDE features)
  - Provides autocomplete, hover, navigation, refactoring
  - Automatically enabled when editing Python in VS Code
  - No installation needed (comes with Python extension)

- **Pyright CLI** = Standalone type checker (command-line tool)
  - Used in CI/CD workflows and convenience script
  - Run via `uvx pyright` (no installation needed)
  - Same type checking engine as Pylance

**Our Setup:**
- ✅ Pylance in VS Code for IDE features
- ✅ Pyright CLI (`uvx pyright`) for automation
- ✅ Single configuration in `pyproject.toml` used by both
- ✅ Consistent type checking across IDE and CI/CD

**For more details:** See `docs/pyright-vs-pylance-clarification.md`

---

## Development Commands

### Convenience Script (`./scripts/dev.sh`)

All commands are available through the convenience script:

```bash
./scripts/dev.sh <command>
```

#### Linting and Formatting
| Command | Description | Speed |
|---------|-------------|-------|
| `lint` | Run Ruff linter | ~1s |
| `lint-fix` | Run Ruff linter with auto-fix | ~1s |
| `format` | Format code with Ruff | ~1s |
| `format-check` | Check code formatting | ~1s |

#### Combined Quality Checks
| Command | Description | Speed |
|---------|-------------|-------|
| `quality` | Run lint + format-check | ~2s |
| `quality-fix` | Run lint-fix + format | ~2s |

#### Type Checking
| Command | Description | Speed |
|---------|-------------|-------|
| `typecheck` | Run MyPy type checker | ~3-5s |

#### Testing
| Command | Description | Speed |
|---------|-------------|-------|
| `test` | Run all tests | Varies |
| `test-fast` | Stop on first failure, run failed tests first | Faster |
| `test-cov` | Run tests with coverage report | Slower |
| `test-parallel` | Run tests in parallel | Faster |

#### Combined Workflows
| Command | Description | Speed |
|---------|-------------|-------|
| `dev-check` | quality-fix + test-fast | ~2-3s |
| `check-all` | quality + typecheck + test | ~6-7s |

---

## Direct UV Commands

If you prefer to use UV directly, we use `uvx` for standalone tools:

### Linting and Formatting
```bash
# Lint (using uvx - no installation needed)
uvx ruff check src/ tests/

# Lint with auto-fix
uvx ruff check --fix src/ tests/

# Format
uvx ruff format src/ tests/

# Format check
uvx ruff format --check src/ tests/
```

### Type Checking
```bash
# Type check with Pyright (10-100x faster than MyPy)
uvx pyright src/

# With specific version for reproducibility
uvx pyright@1.1.350 src/
```

### Testing
```bash
# Run all tests (using uvx)
uvx pytest tests/

# Stop on first failure, run failed tests first
uvx pytest tests/ -x --ff

# Run with coverage
uvx pytest tests/ --cov=src --cov-report=html --cov-report=term

# Run in parallel
uvx pytest tests/ -n auto
```

### Why `uvx` Instead of `uv run`?

**`uvx` benefits:**
- ✅ No need to install tools as project dependencies
- ✅ Always uses latest version (or pin with `uvx tool@version`)
- ✅ Faster CI/CD (no tool installation step)
- ✅ Cleaner project dependencies
- ✅ Isolated tool environments

**When to use `uv run`:**
- Scripts that import project code
- Tools that need project dependencies
- Custom project-specific commands

---

## Pre-commit Hooks

### Automatic Checks
Pre-commit hooks run automatically before each commit:

1. **Trailing whitespace** - Removes trailing whitespace
2. **End of files** - Ensures files end with newline
3. **YAML validation** - Checks YAML syntax
4. **Large files** - Prevents committing large files
5. **Secrets detection** - Detects accidentally committed secrets
6. **Ruff linting** - Lints and auto-fixes code
7. **Ruff formatting** - Formats code

**Performance:** ~6-7 seconds for full run

### Bypass Pre-commit Hooks
```bash
# Skip all hooks
git commit --no-verify -m "WIP: experimenting"

# Skip specific hook
SKIP=ruff git commit -m "message"

# Skip multiple hooks
SKIP=ruff,check-yaml git commit -m "message"
```

### Manual Pre-commit Run
```bash
# Run all hooks on all files
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files

# Run on staged files only
pre-commit run
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

#### Code Quality Workflow
**File:** `.github/workflows/code-quality.yml`

**Jobs:**
1. **Lint** - Runs Ruff linting and formatting checks
2. **Type Check** - Runs MyPy type checking

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

#### Tests Workflow
**File:** `.github/workflows/tests.yml`

**Jobs:**
- Runs full test suite with coverage

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

---

## Configuration Files

### Primary Configuration
**File:** `pyproject.toml`

Contains all tool configurations:
- Project metadata
- Dependencies
- Ruff configuration (linting, formatting, import sorting)
- MyPy configuration
- Pytest configuration

### Pre-commit Configuration
**File:** `.pre-commit-config.yaml`

Defines pre-commit hooks and their versions.

### UV Configuration
**File:** `uv.toml` (optional)

Global UV settings (not currently used).

---

## Ruff Configuration

### Enabled Rule Categories (15 total)

| Code | Category | Description |
|------|----------|-------------|
| E4, E7, E9 | pycodestyle | Error detection |
| F | pyflakes | Logical errors |
| I | isort | Import sorting |
| B | flake8-bugbear | Bug detection |
| C4 | flake8-comprehensions | Comprehension improvements |
| UP | pyupgrade | Python version upgrades |
| S | flake8-bandit | Security issues |
| T20 | flake8-print | Print statement detection |
| SIM | flake8-simplify | Code simplification |
| RET | flake8-return | Return statement improvements |
| ARG | flake8-unused-arguments | Unused argument detection |
| PTH | flake8-use-pathlib | Pathlib usage |
| ERA | eradicate | Commented-out code |
| PL | pylint | General linting |
| PERF | perflint | Performance anti-patterns |

### Auto-fixable Rules
Most rules are auto-fixable with:
```bash
./scripts/dev.sh lint-fix
# or
uv run ruff check --fix src/ tests/
```

---

## Troubleshooting

### Pre-commit Hooks Failing

**Problem:** Pre-commit hooks fail with linting errors

**Solution:**
```bash
# Auto-fix all issues
./scripts/dev.sh quality-fix

# Then commit
git add .
git commit -m "Your message"
```

### Type Checking Errors

**Problem:** MyPy reports type errors

**Solution:**
```bash
# Run type checker to see errors
./scripts/dev.sh typecheck

# Fix errors manually
# MyPy errors are not auto-fixable
```

### Slow Pre-commit Hooks

**Problem:** Pre-commit hooks taking too long

**Solution:**
```bash
# Skip hooks temporarily
git commit --no-verify -m "WIP"

# Or run quality checks manually
./scripts/dev.sh dev-check
git commit -m "Your message"
```

### Ruff Configuration Issues

**Problem:** Ruff reporting too many issues

**Solution:**
1. Check if issues are legitimate (they usually are)
2. Auto-fix what you can: `./scripts/dev.sh lint-fix`
3. Add specific ignores to `pyproject.toml` if needed:
   ```toml
   [tool.ruff.lint.per-file-ignores]
   "path/to/file.py" = ["RULE_CODE"]
   ```

---

## Best Practices

### Daily Workflow

1. **Start of day:** Pull latest changes
   ```bash
   git pull origin main
   uv sync
   ```

2. **During development:** Run quick checks frequently
   ```bash
   ./scripts/dev.sh dev-check
   ```

3. **Before commit:** Run full validation
   ```bash
   ./scripts/dev.sh check-all
   git add .
   git commit -m "feat: your feature"
   ```

4. **Before push:** Ensure CI/CD will pass
   ```bash
   ./scripts/dev.sh check-all
   git push origin feature-branch
   ```

### Code Quality Tips

1. **Let Ruff fix what it can:** Always run `lint-fix` before manual fixes
2. **Format early, format often:** Run `format` after significant changes
3. **Type check periodically:** Run `typecheck` when adding new functions
4. **Test continuously:** Run `test-fast` during development
5. **Coverage matters:** Run `test-cov` before submitting PR

---

## Migration from Old Workflow

### What Changed

**Removed:**
- ❌ Black (replaced by Ruff formatter)
- ❌ isort (replaced by Ruff import sorting)
- ❌ MyPy from pre-commit (moved to CI/CD only)

**Added:**
- ✅ Enhanced Ruff configuration (15 rule categories)
- ✅ Convenience script (`./scripts/dev.sh`)
- ✅ Faster pre-commit hooks (55% faster)

### Old Commands → New Commands

| Old | New |
|-----|-----|
| `black src/ tests/` | `./scripts/dev.sh format` |
| `isort src/ tests/` | `./scripts/dev.sh format` (included) |
| `ruff check src/ tests/` | `./scripts/dev.sh lint` |
| `mypy src/` | `./scripts/dev.sh typecheck` |
| Multiple commands | `./scripts/dev.sh dev-check` |

---

## Additional Resources

- **Exception Handling Guidelines:** `docs/development/exception-handling-guidelines.md`
- **Full Audit Report:** `docs/tooling-optimization-summary.md`
- **Ruff Documentation:** https://docs.astral.sh/ruff/
- **UV Documentation:** https://docs.astral.sh/uv/
- **Pre-commit Documentation:** https://pre-commit.com/

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│ TTA Development Workflow - Quick Reference                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ BEFORE COMMIT:                                              │
│   ./scripts/dev.sh dev-check     # Quick (2-3s)            │
│   ./scripts/dev.sh check-all     # Full (6-7s)             │
│                                                             │
│ FIX ISSUES:                                                 │
│   ./scripts/dev.sh quality-fix   # Auto-fix lint+format    │
│                                                             │
│ TESTING:                                                    │
│   ./scripts/dev.sh test-fast     # Quick test              │
│   ./scripts/dev.sh test-cov      # With coverage           │
│                                                             │
│ BYPASS HOOKS:                                               │
│   git commit --no-verify         # Skip all hooks          │
│                                                             │
│ HELP:                                                       │
│   ./scripts/dev.sh help          # Show all commands       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs dev workflow quick reference]]
