#!/usr/bin/env python3
"""Validate root agent instruction files stay within their line budget."""

import sys

ROOT = "."
BUDGET = 100

FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    ".github/copilot-instructions.md",
]


def main() -> int:
    failures: list[str] = []
    for path in FILES:
        try:
            with open(f"{ROOT}/{path}") as fh:
                lines = fh.readlines()
            count = len(lines)
            if count > BUDGET:
                failures.append(f"  {path}: {count} lines (budget: {BUDGET})")
            else:
                print(f"OK  {path}: {count}/{BUDGET} lines")
        except FileNotFoundError:
            failures.append(f"  {path}: NOT FOUND")

    if failures:
        print("\nFAIL — files over budget:")
        for msg in failures:
            print(msg)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
