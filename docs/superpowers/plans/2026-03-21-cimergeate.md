# CIMergeGate — Technical Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** GitHub Actions job that runs affected tests in an E2B sandbox on every PR to `main`, providing a non-bypassable complement to the local pre-commit hook.
Spec: `docs/superpowers/specs/2026-03-21-cimergeate.md`

---

## Architecture Overview

```
scripts/run_e2b_tests.py              ← CI entry point (called by workflow)
.github/workflows/e2b-validation.yml  ← GitHub Actions workflow
tests/scripts/test_run_e2b_tests.py   ← Unit tests (100% coverage, all E2B mocked)
```

**No changes to existing workflows** (`ci.yml`, etc.). Additive only.

---

## Design Decisions

### Standalone script (no imports from `ttadev`)
`run_e2b_tests.py` imports only stdlib + `e2b_code_interpreter` (already a project dep). Same pattern as the other scripts in `scripts/`.

### File mapping: copied not shared
`_find_test_file()` logic is copied from `run_changed_tests.py` verbatim. The spec explicitly places "running as a shared library" out of scope.

### E2B: asyncio.run() at top level
`e2b_code_interpreter.AsyncSandbox` is async. The script entry point is synchronous (shell script pattern). `asyncio.run()` bridges them — same pattern used across many async CLI tools.

### Project upload via tarball
The GitHub Actions runner has the checked-out code. The script tarballs the current directory (excluding `.git` and `__pycache__`), uploads it to the E2B sandbox via `sandbox.files.write()`, then extracts, installs deps, and runs pytest. This is self-contained — works with private repos, any branch/SHA, no GITHUB_TOKEN complexity.

### Graceful degradation boundary
The boundary is the `_run_pytest_in_sandbox()` function:
- No `E2B_API_KEY` → detected before entering the function → exit 0
- `E2B_API_KEY` present but E2B raises any exception → caught → exit 0 with warning
- `E2B_API_KEY` present and sandbox runs → pytest exit code propagated

### Timeout handling
E2B sandbox creation has `timeout` param. `sandbox.commands.run()` has a timeout. Both set to match the 15-minute workflow timeout. On `asyncio.TimeoutError` or `TimeoutError`: exit 0 with warning (infra failure, not test failure).

---

## Function Signatures

### `scripts/run_e2b_tests.py`

```python
def _find_test_file(source_path: Path) -> Path | None:
    """Map a source .py file to its test counterpart. Returns None if not found.
    Copied from run_changed_tests.py — kept separate per spec Out of Scope.
    Mapping: ttadev/some/module.py -> tests/some/test_module.py
    """

def _load_changed_files(input_path: str) -> list[str]:
    """Read changed file paths from a file (one per line). Returns [] on any error.
    Filters to .py files only.
    """

def _map_to_test_files(changed_paths: list[str]) -> list[str]:
    """Apply _find_test_file to each path. Returns deduplicated list of test paths."""

async def _run_pytest_in_sandbox(test_files: list[str]) -> int:
    """Create E2B sandbox, upload project, install deps, run pytest.
    Returns pytest exit code. Raises on E2B/infra error (caller handles).
    """

def main(argv: list[str]) -> int:
    """Entry point. Returns exit code (0 = pass/skip, 1+ = test failure)."""
```

### E2B interaction inside `_run_pytest_in_sandbox`

```python
async with AsyncSandbox.create(timeout=800) as sandbox:
    # 1. Tarball project (exclude .git, __pycache__, .venv)
    tar_bytes = _make_project_tar()  # uses stdlib tarfile, in-memory BytesIO

    # 2. Upload to sandbox
    await sandbox.files.write("/tmp/project.tar.gz", tar_bytes)

    # 3. Bootstrap: extract + install
    bootstrap = await sandbox.commands.run(
        "mkdir -p /project && "
        "tar -xzf /tmp/project.tar.gz -C /project && "
        "cd /project && pip install uv -q && uv sync --all-extras -q",
        timeout=600,
    )
    if bootstrap.exit_code != 0:
        raise RuntimeError(f"Bootstrap failed: {bootstrap.stderr}")

    # 4. Run pytest
    test_args = " ".join(test_files)
    result = await sandbox.commands.run(
        f"cd /project && uv run pytest {test_args} -x --tb=short",
        timeout=300,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.exit_code
```

---

## Workflow File

```yaml
name: E2B Sandbox Validation

on:
  pull_request:
    branches: [main]
    paths:
      - 'ttadev/**'
      - 'tests/**'
      - 'scripts/**'

permissions:
  contents: read

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  e2b-validation:
    name: E2B Sandbox Tests
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - uses: actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5  # v4
        with:
          fetch-depth: 0

      - uses: astral-sh/setup-uv@797cf5c0a210b8b257f62fe1fbf9a46b4fc201bf  # v2
        with:
          enable-cache: true

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Get changed Python files
        id: changed
        run: |
          git diff --name-only origin/main...HEAD -- '*.py' > /tmp/changed_files.txt
          echo "Changed files:"
          cat /tmp/changed_files.txt

      - name: Run E2B sandbox validation
        env:
          E2B_API_KEY: ${{ secrets.E2B_API_KEY }}
        run: uv run python scripts/run_e2b_tests.py /tmp/changed_files.txt
```

Action SHA pins match `ci.yml` for consistency.

---

## Test Specifications

### `tests/scripts/test_run_e2b_tests.py`

```python
class TestLoadChangedFiles:
    def test_reads_py_files(self, tmp_path): ...
    def test_filters_non_py(self, tmp_path): ...
    def test_returns_empty_on_missing_file(self): ...
    def test_returns_empty_on_empty_file(self, tmp_path): ...
    def test_strips_whitespace(self, tmp_path): ...

class TestMapToTestFiles:
    def test_maps_source_to_test(self, tmp_path, monkeypatch): ...
    def test_returns_empty_when_no_test_files(self, tmp_path, monkeypatch): ...
    def test_deduplicates(self, tmp_path, monkeypatch): ...
    def test_skips_non_py(self, tmp_path, monkeypatch): ...

class TestMain:
    def test_exits_zero_no_python_files(self, tmp_path, monkeypatch): ...
    def test_exits_zero_no_test_counterparts(self, tmp_path, monkeypatch): ...
    def test_exits_zero_missing_api_key(self, tmp_path, monkeypatch): ...
    def test_exits_zero_on_e2b_infra_error(self, tmp_path, monkeypatch): ...
    def test_exits_zero_on_e2b_timeout(self, tmp_path, monkeypatch): ...
    def test_exits_one_on_test_failure(self, tmp_path, monkeypatch): ...
    def test_exits_zero_on_test_pass(self, tmp_path, monkeypatch): ...

class TestRunPytestInSandbox:
    def test_creates_sandbox_and_runs_pytest(self): ...  # mocked AsyncSandbox
    def test_raises_on_bootstrap_failure(self): ...
    def test_returns_pytest_exit_code(self): ...
```

All tests mock `AsyncSandbox` — no real E2B calls.

---

## External Dependencies

| Dependency | Already present? | Notes |
|------------|-----------------|-------|
| `e2b-code-interpreter>=2.5.0` | Yes (pyproject.toml) | `AsyncSandbox`, `commands.run()`, `files.write()` |
| `asyncio` | Yes (stdlib) | `asyncio.run()` for entry point |
| `tarfile` | Yes (stdlib) | In-memory project tarball |
| `io.BytesIO` | Yes (stdlib) | Tarball buffer |

**No new dependencies.**

---

## Observability

This is a CI script — no OTel spans. Output goes to GitHub Actions logs:
- `print()` for status messages (visible in workflow run)
- `print(..., file=sys.stderr)` for warnings
- Exit code drives the `e2b-validation` status check

---

## File Layout

| Action | Path | Purpose |
|--------|------|---------|
| Create | `scripts/run_e2b_tests.py` | CI E2B test runner |
| Create | `.github/workflows/e2b-validation.yml` | GitHub Actions workflow |
| Create | `tests/scripts/test_run_e2b_tests.py` | Unit tests (100% coverage) |

---

## Task Breakdown

### Task 1 — `run_e2b_tests.py` + tests

- [ ] Create `scripts/run_e2b_tests.py` with all functions per spec above
- [ ] Create `tests/scripts/test_run_e2b_tests.py` with all test classes per spec above
- [ ] Run `uv run pytest tests/scripts/test_run_e2b_tests.py -v` — all pass
- [ ] Run `uvx pyright scripts/run_e2b_tests.py` — 0 errors
- [ ] Run `uv run ruff check scripts/run_e2b_tests.py --fix` — clean
- [ ] Commit: `feat(ci): add run_e2b_tests.py CI sandbox test runner`

### Task 2 — GitHub Actions workflow

- [ ] Create `.github/workflows/e2b-validation.yml` per spec above (SHA-pinned actions)
- [ ] Verify YAML is valid: `python -c "import yaml; yaml.safe_load(open('.github/workflows/e2b-validation.yml'))"`
- [ ] Commit: `feat(ci): add e2b-validation GitHub Actions workflow`

---

## Dependencies

```
Task 1 ─── independent
Task 2 ─── independent (references run_e2b_tests.py by path, but doesn't need it to exist for workflow validity)
```

Tasks can be executed in either order or in parallel.

---

## Quality Gate

Before each commit:
```bash
uv run pytest tests/scripts/test_run_e2b_tests.py -v  # all pass
uvx pyright scripts/run_e2b_tests.py                  # 0 errors
uv run ruff check scripts/run_e2b_tests.py --fix       # clean
python -c "import yaml; yaml.safe_load(open('.github/workflows/e2b-validation.yml'))"  # valid YAML
```
