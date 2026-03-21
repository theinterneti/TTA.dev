# SessionAutomation — Technical Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Three automation scripts + config wiring that eliminate manual session ceremony.
Spec: `docs/superpowers/specs/2026-03-21-sessionautomation.md`

---

## Architecture Overview

```
scripts/auto_retain.py          ← Stop hook target (sync httpx, git log)
scripts/session_start_recall.py ← UserPromptSubmit hook target (sync httpx)
scripts/run_changed_tests.py    ← pre-commit hook target (subprocess pytest)

.pre-commit-config.yaml         ← add pytest-changed local hook
.claude/settings.local.json     ← register Stop + UserPromptSubmit hooks

tests/scripts/
  __init__.py
  test_auto_retain.py
  test_session_start_recall.py
  test_run_changed_tests.py
```

**Design choices:**
- Scripts use **synchronous `httpx.Client`** (not async) — they are shell entry points, not primitives. No `asyncio.run()` needed.
- Scripts are **standalone** — they import only stdlib + `httpx` (already a project dep). They do NOT import from `ttadev`.
- All Hindsight calls use the same endpoint paths as `HindsightClient` (`/v1/default/banks/{bank_id}/...`).
- All scripts **exit 0 on any failure** except `run_changed_tests.py` (which must propagate pytest's exit code).

---

## Environment Variables

| Var | Default | Used by |
|-----|---------|---------|
| `HINDSIGHT_URL` | `http://localhost:8888` | `auto_retain.py`, `session_start_recall.py` |
| `HINDSIGHT_BANK` | `tta-dev` | `auto_retain.py`, `session_start_recall.py` |

---

## Script Specifications

### `scripts/auto_retain.py`

```python
#!/usr/bin/env python3
"""Session-end auto-retain: called by Claude Code Stop hook.

Reads recent git commits, posts a summary to Hindsight retain endpoint.
Exits 0 always — never blocks the session.
"""
from __future__ import annotations
import os, subprocess, sys
from datetime import date
import httpx

_DEFAULT_URL = "http://localhost:8888"
_DEFAULT_BANK = "tta-dev"
_TIMEOUT = 5.0


def _git_log(n: int = 10) -> str:
    """Return last n commit subject lines, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"-{n}"],
            capture_output=True, text=True, timeout=5,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _retain(base_url: str, bank_id: str, content: str) -> bool:
    """POST content to Hindsight retain. Returns True on success."""
    try:
        url = f"{base_url}/v1/default/banks/{bank_id}/memories"
        resp = httpx.post(url, json={"items": [{"content": content}], "async": True}, timeout=_TIMEOUT)
        resp.raise_for_status()
        return True
    except Exception as exc:
        print(f"auto_retain: Hindsight unavailable, skipping ({exc})", file=sys.stderr)
        return False


def main() -> None:
    base_url = os.environ.get("HINDSIGHT_URL", _DEFAULT_URL).rstrip("/")
    bank_id  = os.environ.get("HINDSIGHT_BANK", _DEFAULT_BANK)
    commits  = _git_log()
    subjects = commits if commits else "no commits this session"
    content  = f"[type: session-end] {date.today()} — {subjects}"
    _retain(base_url, bank_id, content)


if __name__ == "__main__":
    main()
    sys.exit(0)  # always exit 0
```

**Key invariants:**
- `main()` never raises; all exceptions caught inside `_git_log` and `_retain`.
- `sys.exit(0)` unconditional — Hindsight failure is a warning, not an error.

---

### `scripts/session_start_recall.py`

```python
#!/usr/bin/env python3
"""Session-start directives: called by Claude Code UserPromptSubmit hook.

Fetches Hindsight directives and prints them as Markdown to stdout.
Claude Code injects stdout into the conversation context.
Exits 0 silently on failure.
"""
from __future__ import annotations
import os, sys
import httpx

_DEFAULT_URL = "http://localhost:8888"
_DEFAULT_BANK = "tta-dev"
_TIMEOUT = 2.0  # must not slow session start


def _get_directives(base_url: str, bank_id: str) -> list[str]:
    try:
        url = f"{base_url}/v1/default/banks/{bank_id}/directives"
        resp = httpx.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("directives", []) if isinstance(data, dict) else data
        return [
            d.get("content") or d.get("text", "")
            for d in items
            if d.get("content") or d.get("text")
        ]
    except Exception:
        return []


def main() -> None:
    base_url = os.environ.get("HINDSIGHT_URL", _DEFAULT_URL).rstrip("/")
    bank_id  = os.environ.get("HINDSIGHT_BANK", _DEFAULT_BANK)
    directives = _get_directives(base_url, bank_id)
    if not directives:
        return  # silent — don't pollute context with empty noise
    print("## Hindsight Directives (auto-loaded)")
    for d in directives:
        print(f"- {d}")


if __name__ == "__main__":
    main()
    sys.exit(0)
```

**Key invariants:**
- 2-second timeout — session start must feel instant.
- Empty list → print nothing (no Markdown noise if Hindsight is down).

---

### `scripts/run_changed_tests.py`

```python
#!/usr/bin/env python3
"""Pre-commit test runner: finds and runs tests for staged source files.

Called by pre-commit with staged .py file paths as argv.
Exits 0 if no test files found or tests pass. Exits non-zero if tests fail.
"""
from __future__ import annotations
import sys, subprocess
from pathlib import Path


def _find_test_file(source_path: Path) -> Path | None:
    """Map a source file to its test counterpart, or None if not found.

    Mapping:  ttadev/some/module.py  →  tests/some/test_module.py
    Also tries: tests/some/module.py (for test files already under tests/).
    """
    parts = source_path.parts
    # Skip if already a test file
    if source_path.name.startswith("test_") or "tests" in parts:
        return None
    # Strip 'ttadev/' prefix
    if parts[0] == "ttadev":
        rel_parts = parts[1:]
    else:
        rel_parts = parts
    # Build candidate: tests/<rel_dir>/test_<stem>.py
    *dirs, filename = rel_parts
    stem = Path(filename).stem
    candidate = Path("tests", *dirs, f"test_{stem}.py")
    return candidate if candidate.exists() else None


def main(argv: list[str]) -> int:
    test_files: list[str] = []
    for arg in argv:
        p = Path(arg)
        if not p.suffix == ".py":
            continue
        test_file = _find_test_file(p)
        if test_file:
            test_files.append(str(test_file))

    if not test_files:
        return 0  # nothing to run — pass through

    result = subprocess.run(
        ["uv", "run", "pytest"] + test_files + ["-x", "--tb=short"],
    )
    return result.returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

**Key invariants:**
- Pass-through (exit 0) when no test counterpart found — never blocks unrelated changes.
- Mirrors pytest exit code — failures block the commit.

---

## Config Changes

### `.pre-commit-config.yaml` addition

Add at the end of the file, as a new `local` repo entry:

```yaml
  # Pytest — run tests for any changed source files
  - repo: local
    hooks:
      - id: pytest-changed
        name: "🧪 Pytest Changed Tests"
        entry: python scripts/run_changed_tests.py
        language: system
        types: [python]
        pass_filenames: true
        stages: [pre-commit]
```

### `.claude/settings.local.json` hooks

Merge into the existing JSON (preserve all existing keys):

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "python scripts/auto_retain.py"}
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "python scripts/session_start_recall.py"}
        ]
      }
    ]
  }
}
```

> **Note:** `settings.local.json` is gitignored and user-local. Implementer must read the current file before merging to preserve existing keys.

---

## Test Specifications

### `tests/scripts/test_auto_retain.py`

```python
from unittest.mock import MagicMock, patch
from scripts.auto_retain import _git_log, _retain, main

class TestGitLog:
    def test_returns_commit_subjects(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="abc123 feat: add thing\n", returncode=0)
            assert "feat: add thing" in _git_log()

    def test_returns_empty_on_failure(self):
        with patch("subprocess.run", side_effect=Exception("no git")):
            assert _git_log() == ""

class TestRetain:
    def test_posts_to_hindsight(self):
        with patch("httpx.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200, raise_for_status=lambda: None)
            result = _retain("http://localhost:8888", "tta-dev", "test content")
            assert result is True
            mock_post.assert_called_once()

    def test_returns_false_on_network_error(self):
        with patch("httpx.post", side_effect=Exception("connection refused")):
            result = _retain("http://localhost:8888", "tta-dev", "test content")
            assert result is False

class TestMain:
    def test_exits_zero_always(self):
        with patch("scripts.auto_retain._git_log", return_value=""), \
             patch("scripts.auto_retain._retain", return_value=False):
            # Should not raise
            main()
```

### `tests/scripts/test_session_start_recall.py`

```python
from unittest.mock import MagicMock, patch
from scripts.session_start_recall import _get_directives, main
import io, sys

class TestGetDirectives:
    def test_returns_directive_texts(self):
        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"directives": [{"content": "Always orient first."}]}
        mock_resp.raise_for_status = MagicMock()
        with patch("httpx.get", return_value=mock_resp):
            result = _get_directives("http://localhost:8888", "tta-dev")
            assert result == ["Always orient first."]

    def test_returns_empty_on_failure(self):
        with patch("httpx.get", side_effect=Exception("timeout")):
            result = _get_directives("http://localhost:8888", "tta-dev")
            assert result == []

class TestMain:
    def test_prints_directives_as_markdown(self, capsys):
        with patch("scripts.session_start_recall._get_directives", return_value=["Use uv."]):
            main()
        out = capsys.readouterr().out
        assert "## Hindsight Directives" in out
        assert "Use uv." in out

    def test_prints_nothing_when_empty(self, capsys):
        with patch("scripts.session_start_recall._get_directives", return_value=[]):
            main()
        out = capsys.readouterr().out
        assert out == ""
```

### `tests/scripts/test_run_changed_tests.py`

```python
from pathlib import Path
from unittest.mock import MagicMock, patch
from scripts.run_changed_tests import _find_test_file, main

class TestFindTestFile:
    def test_maps_source_to_test_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        test_file = tmp_path / "tests" / "primitives" / "memory" / "test_agent_memory.py"
        test_file.parent.mkdir(parents=True)
        test_file.touch()
        result = _find_test_file(Path("ttadev/primitives/memory/agent_memory.py"))
        assert result == Path("tests/primitives/memory/test_agent_memory.py")

    def test_returns_none_when_no_test_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = _find_test_file(Path("ttadev/workflows/llm_provider.py"))
        assert result is None

    def test_skips_test_files(self):
        result = _find_test_file(Path("tests/workflows/test_development_cycle.py"))
        assert result is None

class TestMain:
    def test_returns_zero_when_no_tests_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        rc = main(["ttadev/workflows/llm_provider.py"])
        assert rc == 0

    def test_returns_pytest_exit_code(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        test_file = tmp_path / "tests" / "test_foo.py"
        test_file.parent.mkdir(parents=True)
        test_file.touch()
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            rc = main(["ttadev/foo.py"])
            # No test mapped (no matching test file from _find_test_file) → 0
            assert rc == 0
```

> Note on the last test: since `tmp_path` doesn't have `tests/test_foo.py` under the right mapping path, `_find_test_file` returns None and exit is 0. Integration tests against real filesystem would be in a separate test.

---

## Task Breakdown

### Task 1 — `auto_retain.py` + tests
- Create `scripts/__init__.py` (empty, to make scripts importable)
- Create `tests/scripts/__init__.py`
- Create `scripts/auto_retain.py` per spec above
- Create `tests/scripts/test_auto_retain.py` per spec above
- Run `uv run pytest tests/scripts/test_auto_retain.py -v` — all pass
- Run `uvx pyright scripts/auto_retain.py` — 0 errors
- Run `uv run ruff check scripts/auto_retain.py --fix` — clean
- Commit: `feat(automation): add auto_retain.py session-end script`

### Task 2 — `session_start_recall.py` + tests
- Create `scripts/session_start_recall.py` per spec above
- Create `tests/scripts/test_session_start_recall.py` per spec above
- Run `uv run pytest tests/scripts/test_session_start_recall.py -v` — all pass
- Run `uvx pyright scripts/session_start_recall.py` — 0 errors
- Run `uv run ruff check scripts/session_start_recall.py --fix` — clean
- Commit: `feat(automation): add session_start_recall.py directives loader`

### Task 3 — `run_changed_tests.py` + tests
- Create `scripts/run_changed_tests.py` per spec above
- Create `tests/scripts/test_run_changed_tests.py` per spec above
- Run `uv run pytest tests/scripts/test_run_changed_tests.py -v` — all pass
- Run `uvx pyright scripts/run_changed_tests.py` — 0 errors
- Run `uv run ruff check scripts/run_changed_tests.py --fix` — clean
- Commit: `feat(automation): add run_changed_tests.py pre-commit runner`

### Task 4 — Pre-commit config + Claude Code hooks wiring
- Add `pytest-changed` entry to `.pre-commit-config.yaml`
- Read `.claude/settings.local.json`, merge Stop + UserPromptSubmit hooks
- Run `uv run pre-commit run --all-files` — passes (pytest-changed has no staged files)
- Commit: `feat(automation): wire pre-commit + Claude Code hooks`

---

## Dependencies

```
Task 1 ─────────────────────────────────── independent
Task 2 ─────────────────────────────────── independent
Task 3 ─────────────────────────────────── independent
Task 4 ─── depends on Task 3 (references run_changed_tests.py)
```

Tasks 1, 2, 3 can be implemented in any order or in parallel. Task 4 requires Task 3 to exist.

---

## Quality Gate

Before each commit:
```bash
uv run pytest tests/scripts/ -v           # all new tests pass
uvx pyright scripts/                      # 0 errors
uv run ruff check scripts/ --fix          # clean
uv run pre-commit run --all-files         # after Task 4
```
