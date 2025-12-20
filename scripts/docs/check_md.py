#!/usr/bin/env python3
"""
Markdown documentation checker for TTA.dev

Performs lightweight checks on markdown files:
- Link validation (internal links by default, external links in CI)
- Code block syntax validation
- Frontmatter/metadata checks
- Optionally extract and validate runnable code blocks

Usage:
    python scripts/docs/check_md.py --help
    python scripts/docs/check_md.py --links           # Check internal links only
    python scripts/docs/check_md.py --all             # All static checks
    python scripts/docs/check_md.py --run-code        # Extract and run code blocks (needs guard)
"""

import argparse
import os
import re
import sys
from pathlib import Path


class MarkdownChecker:
    """Check markdown files for common issues."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def check_internal_links(self, md_files: list[Path]) -> None:
        """Check that internal markdown links resolve to existing files."""
        print("🔗 Checking internal links...")

        # Build set of valid targets
        valid_targets = set()
        for f in md_files:
            valid_targets.add(f.name)
            valid_targets.add(f.relative_to(self.root_dir).as_posix())

        # Check links in each file
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

        for md_file in md_files:
            # Skip broken symlinks
            if not md_file.exists():
                print(f"⚠️  Skipping broken symlink: {md_file}")
                continue

            content = md_file.read_text(encoding="utf-8", errors="ignore")
            for match in link_pattern.finditer(content):
                link_text, link_target = match.groups()

                # Skip external links, anchors, and special protocols
                if link_target.startswith(("http://", "https://", "#", "mailto:", "tel:")):
                    continue

                # Remove anchor from target
                clean_target = link_target.split("#")[0]
                if not clean_target:
                    continue

                # Resolve relative to file location
                target_path = (md_file.parent / clean_target).resolve()

                if not target_path.exists():
                    rel_file = md_file.relative_to(self.root_dir)
                    self.errors.append(f"{rel_file}: Broken link [{link_text}]({link_target})")

    def check_code_blocks(self, md_files: list[Path]) -> None:
        """Check that code blocks have language specifiers."""
        print("📝 Checking code blocks...")

        fence_pattern = re.compile(r"^```(\w*)\s*$", re.MULTILINE)

        for md_file in md_files:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            for line_num, line in enumerate(content.split("\n"), 1):
                if line.strip().startswith("```"):
                    match = fence_pattern.match(line.strip())
                    if match and not match.group(1):
                        rel_file = md_file.relative_to(self.root_dir)
                        self.warnings.append(
                            f"{rel_file}:{line_num}: Code block missing language identifier"
                        )

    def extract_runnable_code_blocks(self, md_files: list[Path]) -> list[tuple[Path, int, str]]:
        """Extract Python code blocks marked as runnable."""
        print("🐍 Extracting runnable code blocks...")

        runnable_blocks = []
        in_python_block = False
        current_block_lines = []
        block_start_line = 0
        is_runnable = False

        for md_file in md_files:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()

                if stripped.startswith("```python"):
                    in_python_block = True
                    block_start_line = line_num
                    current_block_lines = []
                    # Check if marked as runnable
                    is_runnable = "# runnable" in stripped.lower() or "runnable" in stripped.lower()

                elif stripped == "```" and in_python_block:
                    in_python_block = False
                    # Check first line of block for runnable marker
                    if current_block_lines and "# runnable" in current_block_lines[0].lower():
                        is_runnable = True

                    if is_runnable and current_block_lines:
                        code = "\n".join(current_block_lines)
                        runnable_blocks.append((md_file, block_start_line, code))

                    current_block_lines = []
                    is_runnable = False

                elif in_python_block:
                    current_block_lines.append(line)

        return runnable_blocks

    def check_frontmatter(self, md_files: list[Path]) -> None:
        """Check for frontmatter in markdown files (optional)."""
        print("📋 Checking frontmatter...")

        for md_file in md_files:
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            if content.startswith("---"):
                # Has frontmatter, validate it's properly closed
                lines = content.split("\n")
                if len(lines) > 2:
                    found_close = False
                    for i, line in enumerate(lines[1:], 1):
                        if line.strip() == "---":
                            found_close = True
                            break
                        if i > 50:  # Don't scan forever
                            break

                    if not found_close:
                        rel_file = md_file.relative_to(self.root_dir)
                        self.errors.append(
                            f"{rel_file}: Frontmatter not properly closed (missing closing ---)"
                        )

    def report(self) -> int:
        """Print report and return exit code."""
        if self.errors:
            print("\n❌ Errors found:")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All checks passed!")
            return 0
        elif self.errors:
            print(f"\n❌ Found {len(self.errors)} error(s) and {len(self.warnings)} warning(s)")
            return 1
        else:
            print(f"\n⚠️  Found {len(self.warnings)} warning(s)")
            return 0


def find_markdown_files(root_dir: Path, exclude_dirs: set[str]) -> list[Path]:
    """Find all markdown files, excluding certain directories."""
    md_files = []
    for md_file in root_dir.rglob("*.md"):
        # Skip excluded directories
        if any(excluded in md_file.parts for excluded in exclude_dirs):
            continue
        md_files.append(md_file)
    return md_files


def main():
    parser = argparse.ArgumentParser(description="Check markdown documentation for TTA.dev")
    parser.add_argument("--links", action="store_true", help="Check internal links")
    parser.add_argument(
        "--code-blocks",
        action="store_true",
        help="Check code blocks have language identifiers",
    )
    parser.add_argument("--frontmatter", action="store_true", help="Check frontmatter validity")
    parser.add_argument("--all", action="store_true", help="Run all static checks")
    parser.add_argument(
        "--extract-runnable",
        action="store_true",
        help="Extract runnable code blocks (does not run them)",
    )
    parser.add_argument(
        "--run-code",
        action="store_true",
        help="Run extracted code blocks (requires RUN_DOCS_CODE=true)",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=["node_modules", ".git", "htmlcov", "__pycache__", ".venv", "archive"],
        help="Directories to exclude",
    )

    args = parser.parse_args()

    # If no specific check requested, default to --all
    if not any(
        [
            args.links,
            args.code_blocks,
            args.frontmatter,
            args.all,
            args.extract_runnable,
            args.run_code,
        ]
    ):
        args.all = True

    # Find repo root
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent.parent  # Go up to TTA.dev root

    # Find markdown files
    exclude_dirs = set(args.exclude)
    md_files = find_markdown_files(root_dir, exclude_dirs)
    print(f"📚 Found {len(md_files)} markdown files")

    # Initialize checker
    checker = MarkdownChecker(root_dir)

    # Run requested checks
    if args.all or args.links:
        checker.check_internal_links(md_files)

    if args.all or args.code_blocks:
        checker.check_code_blocks(md_files)

    if args.all or args.frontmatter:
        checker.check_frontmatter(md_files)

    if args.extract_runnable or args.run_code:
        runnable_blocks = checker.extract_runnable_code_blocks(md_files)
        print(f"\n🐍 Found {len(runnable_blocks)} runnable code blocks")

        if args.run_code:
            if os.environ.get("RUN_DOCS_CODE") != "true":
                print("\n⚠️  WARNING: Running code blocks requires RUN_DOCS_CODE=true")
                print(
                    "Set environment variable to run: RUN_DOCS_CODE=true python scripts/docs/check_md.py --run-code"
                )
                return 1

            print("\n🚀 Running code blocks...")
            # TODO: Implement safe code block execution with timeouts and mocking
            print("⚠️  Code execution not yet implemented - use with caution in CI only")
            return 1

    # Print report
    return checker.report()


if __name__ == "__main__":
    sys.exit(main())
