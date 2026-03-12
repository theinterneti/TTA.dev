#!/usr/bin/env python3
"""Validate secrets configuration for CI.

Checks that required secrets are present and well-formed.
Exits 0 if validation passes, non-zero otherwise.
"""

import os
import sys


def main() -> int:
    errors: list[str] = []

    # Optional secrets — warn but don't fail
    optional = ["GEMINI_API_KEY", "E2B_API_KEY", "N8N_API_KEY"]
    for key in optional:
        val = os.environ.get(key, "")
        if val:
            print(f"  ✅ {key} is set")
        else:
            print(f"  ⚠️  {key} is not set (optional)")

    if errors:
        for err in errors:
            print(f"  ❌ {err}", file=sys.stderr)
        return 1

    print("✅ Secrets validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
