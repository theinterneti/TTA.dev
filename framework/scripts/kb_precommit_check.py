#!/usr/bin/env python3
"""
KB Pre-Commit Check: Lightweight validation for staged KB changes.

This script validates:
1. New/modified KB pages have required sections
2. Links in modified files are valid
3. Namespace conventions are followed

Usage:
    python3 framework/scripts/kb_precommit_check.py [files...]

Exit codes:
    0 - All checks passed
    1 - Validation errors found
"""

import re
import sys
from pathlib import Path

# --- Configuration ---
ROOT_DIR = Path(__file__).parent.parent.parent
LOGSEQ_DIR = ROOT_DIR / "logseq" / "pages"

# Required sections for primitive pages
PRIMITIVE_REQUIRED_SECTIONS = ["Overview", "Examples", "Related"]

# Deprecated namespace patterns
DEPRECATED_NAMESPACES = [
    r"\[\[TTA Primitives/",  # Should be [[TTA.dev/Primitives/
]

# Valid link pattern
LOGSEQ_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def check_required_sections(content: str, file_path: Path) -> list[str]:
    """Check if primitive pages have required sections."""
    errors = []

    # Only check primitive pages
    if "Primitives" not in str(file_path):
        return errors

    for section in PRIMITIVE_REQUIRED_SECTIONS:
        if f"## {section}" not in content and f"# {section}" not in content:
            errors.append(f"Missing required section: {section}")

    return errors


def check_deprecated_namespaces(content: str) -> list[str]:
    """Check for deprecated namespace patterns."""
    errors = []

    for pattern in DEPRECATED_NAMESPACES:
        matches = re.findall(pattern, content)
        if matches:
            errors.append(
                f"Deprecated namespace found: {pattern}. "
                "Use [[TTA.dev/Primitives/...]] instead."
            )

    return errors


def check_links_exist(content: str, file_path: Path) -> list[str]:
    """Check if linked pages exist (basic check)."""
    warnings = []
    links = LOGSEQ_LINK_RE.findall(content)

    for link in links:
        # Skip date links, tags, and template placeholders
        if re.match(r"\d{4}-\d{2}-\d{2}", link):
            continue
        if link.startswith("#"):
            continue
        if "YYYY" in link or "[" in link:
            continue

        # Convert link to file path
        link_path = link.replace("/", "___") + ".md"
        full_path = LOGSEQ_DIR / link_path

        if not full_path.exists():
            # Check without namespace prefix
            simple_path = LOGSEQ_DIR / (link.split("/")[-1] + ".md")
            if not simple_path.exists():
                warnings.append(f"Link target may not exist: [[{link}]]")

    return warnings


def validate_file(file_path: Path) -> tuple[list[str], list[str]]:
    """Validate a single KB file."""
    errors = []
    warnings = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"Could not read file: {e}"], []

    # Run checks
    errors.extend(check_required_sections(content, file_path))
    errors.extend(check_deprecated_namespaces(content))
    warnings.extend(check_links_exist(content, file_path))

    return errors, warnings


def main():
    """Main entry point."""
    files = sys.argv[1:] if len(sys.argv) > 1 else []

    # Filter to only KB files
    kb_files = [
        Path(f) for f in files
        if f.endswith(".md") and "logseq" in f
    ]

    if not kb_files:
        print("✅ No KB files to check")
        return 0

    total_errors = 0
    total_warnings = 0

    for file_path in kb_files:
        errors, warnings = validate_file(file_path)

        if errors or warnings:
            print(f"\n📄 {file_path}")
            for error in errors:
                print(f"  ❌ {error}")
                total_errors += 1
            for warning in warnings:
                print(f"  ⚠️  {warning}")
                total_warnings += 1

    print(f"\n{'='*50}")
    print(f"KB Pre-Commit Check: {len(kb_files)} files checked")
    print(f"  Errors: {total_errors}")
    print(f"  Warnings: {total_warnings}")

    if total_errors > 0:
        print("\n❌ Pre-commit check FAILED")
        return 1

    print("\n✅ Pre-commit check PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
