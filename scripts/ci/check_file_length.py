#!/usr/bin/env python3
"""File length checker for TTA.dev.

Scans Python files under a target directory and warns about any that exceed
the configured line-count limit.  Exits 0 always (warn-only, never blocks CI).

Usage:
    python scripts/ci/check_file_length.py
    python scripts/ci/check_file_length.py --limit 400 --path ttadev/
"""

import argparse
import sys
from pathlib import Path


def count_lines(path: Path) -> int:
    """Return the total line count for *path* (all lines, including blank/comments)."""
    try:
        return sum(1 for _ in path.open(encoding="utf-8", errors="replace"))
    except OSError:
        return 0


def scan(root: Path, limit: int) -> list[tuple[int, Path]]:
    """Return ``(line_count, path)`` pairs for files that exceed *limit*, sorted descending."""
    violations: list[tuple[int, Path]] = []
    for py_file in sorted(root.rglob("*.py")):
        n = count_lines(py_file)
        if n > limit:
            violations.append((n, py_file))
    violations.sort(key=lambda t: t[0], reverse=True)
    return violations


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Warn about Python files that exceed the project line-length standard.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        metavar="N",
        help="Maximum allowed lines per file (default: 500).",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path("ttadev/"),
        metavar="DIR",
        help="Directory to scan (default: ttadev/).",
    )
    args = parser.parse_args()

    root: Path = args.path
    limit: int = args.limit

    divider = "━" * 48

    print(f"File length check (warn-only, limit: {limit} lines)")
    print(divider)

    if not root.exists():
        print(f"⚠️  Directory not found: {root}")
        print(divider)
        print("✅ Check complete (warn-only — no build failure)")
        sys.exit(0)

    violations = scan(root, limit)

    if not violations:
        print(f"✅ All files within {limit}-line limit.")
        print(divider)
        print("✅ Check complete (warn-only — no build failure)")
        sys.exit(0)

    for line_count, path in violations:
        print(f"⚠️  {line_count:>6} lines  {path}")

    print(divider)
    print(f"{len(violations)} file(s) exceed {limit}-line limit. See issue #355.")
    print("✅ Check complete (warn-only — no build failure)")
    sys.exit(0)


if __name__ == "__main__":
    main()
