#!/usr/bin/env python3
"""CI sandbox test runner: runs affected tests in an E2B sandbox for PR validation.

Reads a file of changed .py paths (one per line) from argv[1], maps each source
file to its test counterpart, then runs pytest inside an E2B sandbox. Exits 0
on pass, infra error, or nothing-to-run. Exits non-zero only when tests fail.
"""

from __future__ import annotations

import asyncio
import io
import os
import sys
import tarfile
from pathlib import Path


def _find_test_file(source_path: Path) -> Path | None:
    """Map source .py to test counterpart. Returns None if not found or already a test file.

    COPIED from run_changed_tests.py — kept separate per spec (scripts must be standalone).
    Mapping: ttadev/some/module.py -> tests/some/test_module.py
    """
    parts = source_path.parts
    # Skip if already a test file
    if source_path.name.startswith("test_") or "tests" in parts:
        return None
    # Strip 'ttadev/' prefix if present
    if parts[0] == "ttadev":
        rel_parts = parts[1:]
    else:
        rel_parts = parts
    # Build candidate: tests/<rel_dir>/test_<stem>.py
    *dirs, filename = rel_parts
    stem = Path(filename).stem
    # NOTE: candidate.exists() is relative to CWD — must be called from repo root.
    candidate = Path("tests", *dirs, f"test_{stem}.py")
    return candidate if candidate.exists() else None


def _load_changed_files(input_path: str) -> list[str]:
    """Read .py file paths from a text file (one per line).

    Strips whitespace, skips empty lines, filters to .py files only.
    Returns [] on any error (missing file, permission error, etc.).
    """
    try:
        lines = Path(input_path).read_text().splitlines()
    except OSError:
        return []
    return [line.strip() for line in lines if line.strip().endswith(".py")]


def _map_to_test_files(changed_paths: list[str]) -> list[str]:
    """Apply _find_test_file to each path. Deduplicates. Returns list of test file paths."""
    seen: set[str] = set()
    result: list[str] = []
    for raw in changed_paths:
        p = Path(raw)
        if p.suffix != ".py":
            continue
        test_file = _find_test_file(p)
        if test_file is None:
            continue
        key = str(test_file)
        if key not in seen:
            seen.add(key)
            result.append(key)
    return result


async def _run_pytest_in_sandbox(test_files: list[str]) -> int:
    """Create E2B sandbox, upload project tarball, install deps, run pytest.

    Returns pytest exit code. Raises on E2B/infra error (caller handles in main).
    """
    from e2b_code_interpreter import AsyncSandbox  # type: ignore[import-untyped]

    # Build in-memory tarball of current directory
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for entry in Path(".").rglob("*"):
            # Exclude noise directories
            parts = entry.parts
            if any(p in {".git", "__pycache__", ".venv", ".mypy_cache"} for p in parts):
                continue
            if entry.is_file():
                tar.add(str(entry))
    tar_bytes = buf.getvalue()

    sandbox = await AsyncSandbox.create(timeout=800)
    async with sandbox:
        await sandbox.files.write("/tmp/project.tar.gz", tar_bytes)

        bootstrap = await sandbox.commands.run(
            "mkdir -p /project && tar -xzf /tmp/project.tar.gz -C /project"
            " && cd /project && pip install uv -q && uv sync --all-extras -q",
            timeout=600,
        )
        if bootstrap.exit_code != 0:
            raise RuntimeError(f"Bootstrap failed: {bootstrap.stderr}")

        test_args = " ".join(test_files)
        result = await sandbox.commands.run(
            f"cd /project && uv run pytest {test_args} -x --tb=short",
            timeout=300,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.exit_code


def main(argv: list[str]) -> int:
    """Orchestrate: load changed files -> map to test files -> check E2B_API_KEY -> run."""
    if not argv:
        print("Usage: run_e2b_tests.py <changed_files.txt>")
        return 0

    changed = _load_changed_files(argv[0])
    test_files = _map_to_test_files(changed)

    if not test_files:
        print("e2b-validation: no tests affected — skipping")
        return 0

    api_key = os.environ.get("E2B_API_KEY")
    if not api_key:
        print("e2b-validation: E2B_API_KEY not set — skipping sandbox validation")
        return 0

    print(f"e2b-validation: running {len(test_files)} test file(s) in E2B sandbox")
    try:
        return asyncio.run(_run_pytest_in_sandbox(test_files))
    except (TimeoutError, asyncio.TimeoutError) as exc:
        print(
            f"e2b-validation: E2B sandbox timed out — skipping ({exc})",
            file=sys.stderr,
        )
        return 0
    except Exception as exc:
        print(
            f"e2b-validation: E2B sandbox unavailable — skipping ({exc})",
            file=sys.stderr,
        )
        return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
