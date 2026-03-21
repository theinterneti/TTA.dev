#!/usr/bin/env python3
"""Pre-commit test runner: finds and runs tests for staged source files.

Called by pre-commit with staged .py file paths as argv.
Exits 0 if no test files found or tests pass. Exits non-zero if tests fail.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _find_test_file(source_path: Path) -> Path | None:
    """Map a source file to its test counterpart, or None if not found.

    Mapping:  ttadev/some/module.py  ->  tests/some/test_<stem>.py
    Returns None if source is already a test file or no match exists on disk.
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


def main(argv: list[str]) -> int:
    test_files: list[str] = []
    for arg in argv:
        p = Path(arg)
        if p.suffix != ".py":
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
