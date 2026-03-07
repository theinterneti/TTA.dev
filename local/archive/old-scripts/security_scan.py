#!/usr/bin/env python3
"""
TTA.dev Security Scanner - Local CodeQL-equivalent scanning.

This script runs the same security checks that GitHub's CodeQL runs,
but LOCALLY before you commit. No more embarrassing automated review comments!

Usage:
    uv run python scripts/security_scan.py              # Scan staged files
    uv run python scripts/security_scan.py --all       # Scan all Python files
    uv run python scripts/security_scan.py --fix       # Auto-fix where possible
    uv run python scripts/security_scan.py path/to/file.py  # Scan specific file

Requirements:
    uv add --dev semgrep bandit

Exit codes:
    0 - No issues found
    1 - Security issues found
    2 - Scanner error
"""

import argparse
import subprocess
import sys
from pathlib import Path


def get_staged_files() -> list[str]:
    """Get list of staged Python files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
    )
    return [f for f in result.stdout.strip().split("\n") if f.endswith(".py") and f]


def get_all_python_files() -> list[str]:
    """Get all Python files in the project (excluding archives)."""
    exclude_dirs = {"_archive", "archive", ".venv", "venv", "__pycache__", "node_modules"}
    files = []
    for path in Path(".").rglob("*.py"):
        if not any(excluded in path.parts for excluded in exclude_dirs):
            files.append(str(path))
    return files


def run_semgrep(files: list[str], fix: bool = False) -> tuple[int, str]:
    """Run Semgrep security scanner (via uvx due to dependency conflicts)."""
    if not files:
        return 0, "No files to scan"

    cmd = [
        "uvx",
        "semgrep",
        "--config=auto",
        "--config=p/python",
        "--config=p/security-audit",
        "--config=p/secrets",
        "--error",  # Exit with error code on findings
        "--quiet",
    ]

    if fix:
        cmd.append("--autofix")

    cmd.extend(files)

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout + result.stderr
    return result.returncode, output


def run_bandit(files: list[str]) -> tuple[int, str]:
    """Run Bandit Python security linter."""
    if not files:
        return 0, "No files to scan"

    cmd = [
        "bandit",
        "-c",
        ".bandit.yaml",
        "-ll",  # Only medium+ severity
        "-r",
    ] + files

    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout + result.stderr
    return result.returncode, output


def run_detect_secrets(files: list[str]) -> tuple[int, str]:
    """Run detect-secrets to find hardcoded secrets."""
    if not files:
        return 0, "No files to scan"

    cmd = ["detect-secrets", "scan"] + files

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Parse output to check for secrets
    import json

    try:
        data = json.loads(result.stdout)
        if data.get("results"):
            secrets_found = []
            for file_path, secrets in data["results"].items():
                for secret in secrets:
                    secrets_found.append(f"  {file_path}:{secret['line_number']}: {secret['type']}")
            if secrets_found:
                return 1, "🔐 Secrets detected:\n" + "\n".join(secrets_found)
    except json.JSONDecodeError:
        pass

    return 0, "No secrets detected"


def print_header(title: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="TTA.dev Security Scanner - Local CodeQL-equivalent scanning"
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Scan all Python files (not just staged)",
    )
    parser.add_argument(
        "--fix",
        "-f",
        action="store_true",
        help="Auto-fix issues where possible",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Specific files to scan (default: staged files)",
    )

    args = parser.parse_args()

    # Determine files to scan
    if args.files:
        files = args.files
        print(f"🎯 Scanning specified files: {len(files)} file(s)")
    elif args.all:
        files = get_all_python_files()
        print(f"🎯 Scanning all Python files: {len(files)} file(s)")
    else:
        files = get_staged_files()
        if not files:
            print("✅ No staged Python files to scan")
            return 0
        print(f"🎯 Scanning staged files: {len(files)} file(s)")

    total_issues = 0
    all_passed = True

    # Run Semgrep
    print_header("🔒 Semgrep Security Scan (CodeQL-equivalent)")
    try:
        code, output = run_semgrep(files, fix=args.fix)
        if code != 0:
            print(output)
            all_passed = False
            total_issues += 1
        else:
            print("✅ No security issues found")
    except FileNotFoundError:
        print("⚠️  Semgrep not installed. Run: uv add --dev semgrep")

    # Run Bandit
    print_header("🛡️ Bandit Python Security Linter")
    try:
        code, output = run_bandit(files)
        if code != 0:
            print(output)
            all_passed = False
            total_issues += 1
        else:
            print("✅ No security issues found")
    except FileNotFoundError:
        print("⚠️  Bandit not installed. Run: uv add --dev bandit")

    # Run detect-secrets
    print_header("🔐 Secrets Detection")
    try:
        code, output = run_detect_secrets(files)
        if code != 0:
            print(output)
            all_passed = False
            total_issues += 1
        else:
            print("✅ " + output)
    except FileNotFoundError:
        print("⚠️  detect-secrets not installed. Run: uv add --dev detect-secrets")

    # Summary
    print_header("📊 Security Scan Summary")
    if all_passed:
        print("✅ All security checks passed!")
        print("🚀 Your code is ready to commit without triggering GitHub security alerts.")
        return 0
    else:
        print(f"❌ Found {total_issues} security issue category(s)")
        print("🛠️  Fix these issues before committing to avoid GitHub CodeQL alerts.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
