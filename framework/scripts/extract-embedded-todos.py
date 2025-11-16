#!/usr/bin/env python3
"""Extract embedded TODOs from markdown files to Logseq journal.

This script scans markdown files for TODO comments and creates properly
formatted journal entries with all required properties.

Usage:
    uv run python scripts/extract-embedded-todos.py [--dir DIR] [--dry-run]

Examples:
    # Scan all markdown files
    uv run python scripts/extract-embedded-todos.py

    # Scan specific directory
    uv run python scripts/extract-embedded-todos.py --dir docs/

    # Show what would be extracted (don't modify files)
    uv run python scripts/extract-embedded-todos.py --dry-run
"""

import argparse
import re
from datetime import date
from pathlib import Path
from typing import Any


class TodoExtractor:
    """Extract TODOs from markdown files and format for Logseq."""

    TODO_PATTERN = re.compile(
        r"(?:<!--\s*)?TODO:?\s+(.+?)(?:\s*-->)?$", re.MULTILINE | re.IGNORECASE
    )

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.logseq_journals = workspace_root / "logseq" / "journals"
        self.todos: list[dict[str, Any]] = []

    def scan_directory(self, directory: Path, exclude_dirs: list[str] | None = None) -> None:
        """Scan directory for markdown files with TODOs."""
        if exclude_dirs is None:
            exclude_dirs = [
                ".git",
                "node_modules",
                ".venv",
                "htmlcov",
                "__pycache__",
                "logseq/journals",  # Don't scan journals
            ]

        for md_file in directory.rglob("*.md"):
            # Skip excluded directories
            if any(excl in str(md_file) for excl in exclude_dirs):
                continue

            self._scan_file(md_file)

    def _scan_file(self, file_path: Path) -> None:
        """Scan a single file for TODOs."""
        try:
            content = file_path.read_text(encoding="utf-8")
            relative_path = file_path.relative_to(self.workspace_root)

            for match in self.TODO_PATTERN.finditer(content):
                line_num = content[: match.start()].count("\n") + 1
                todo_text = match.group(1).strip()

                # Extract multi-line TODO if next lines are indented
                lines = content.split("\n")
                full_todo = [todo_text]
                for i in range(line_num, len(lines)):
                    line = lines[i]
                    if line.strip() and (line.startswith("  ") or line.startswith("-")):
                        full_todo.append(line.strip())
                    elif line.strip() and not line.startswith("TODO"):
                        break

                self.todos.append(
                    {
                        "text": "\n  ".join(full_todo),
                        "file": str(relative_path),
                        "line": line_num,
                        "category": self._infer_category(file_path, todo_text),
                    }
                )

        except Exception as e:
            print(f"Warning: Could not scan {file_path}: {e}")

    def _infer_category(self, file_path: Path, todo_text: str) -> str:
        """Infer TODO category from file location and content."""
        path_str = str(file_path).lower()
        text_lower = todo_text.lower()

        # Check for explicit markers
        if "learning" in text_lower or "tutorial" in text_lower or "example" in text_lower:
            return "learning-todo"
        if "template" in text_lower:
            return "template-todo"
        if "deploy" in text_lower or "ci/cd" in text_lower or "infrastructure" in text_lower:
            return "ops-todo"

        # Infer from file location
        if "docs/examples" in path_str or "docs/guides" in path_str:
            return "learning-todo"
        if "templates" in path_str:
            return "template-todo"
        if ".github" in path_str or "scripts" in path_str:
            return "ops-todo"

        # Default to dev-todo
        return "dev-todo"

    def _infer_package(self, file_path: Path) -> str | None:
        """Infer package name from file path."""
        path_str = str(file_path)

        if "packages/tta-dev-primitives" in path_str:
            return "tta-dev-primitives"
        if "packages/tta-observability-integration" in path_str:
            return "tta-observability-integration"
        if "packages/universal-agent-context" in path_str:
            return "universal-agent-context"
        if "packages/keploy-framework" in path_str:
            return "keploy-framework"
        if "packages/python-pathway" in path_str:
            return "python-pathway"

        return None

    def _infer_type(self, file_path: Path, category: str) -> str:
        """Infer TODO type from file path and category."""
        path_str = str(file_path).lower()

        if category == "learning-todo":
            if "tutorial" in path_str:
                return "tutorial"
            if "exercise" in path_str:
                return "exercises"
            return "documentation"

        if category == "template-todo":
            if "primitive" in path_str:
                return "primitive"
            if "test" in path_str:
                return "testing"
            return "workflow"

        if category == "ops-todo":
            if "deploy" in path_str or "ci" in path_str:
                return "deployment"
            if "monitor" in path_str:
                return "monitoring"
            return "maintenance"

        # dev-todo
        if "test" in path_str:
            return "testing"
        if "doc" in path_str or "readme" in path_str:
            return "documentation"
        if ".github" in path_str or "script" in path_str:
            return "infrastructure"

        return "implementation"

    def format_for_logseq(self) -> str:
        """Format extracted TODOs as Logseq journal entries."""
        if not self.todos:
            return ""

        today = date.today()
        output = [
            f"\n## 📝 Extracted TODOs - {today.strftime('%B %d, %Y')}\n",
            "The following TODOs were found in markdown files:\n",
        ]

        for todo in self.todos:
            category = todo["category"]
            file_path = todo["file"]
            line_num = todo["line"]
            text = todo["text"]

            # Build TODO entry
            entry = [
                f"- TODO {text} #{category}",
            ]

            # Add properties based on category
            entry.append(f"  type:: {self._infer_type(Path(file_path), category)}")

            if category == "dev-todo":
                entry.append("  priority:: medium")
                package = self._infer_package(Path(file_path))
                if package:
                    entry.append(f"  package:: {package}")

            elif category == "learning-todo":
                entry.append("  audience:: intermediate-users")
                entry.append("  difficulty:: intermediate")

            elif category == "template-todo":
                entry.append("  priority:: medium")

            elif category == "ops-todo":
                entry.append("  priority:: medium")

            # Always add source file reference
            entry.append(f"  source-file:: {file_path}:{line_num}")
            entry.append("  status:: not-started")
            entry.append(f"  extracted:: [[{today.strftime('%Y-%m-%d')}]]")

            output.extend(entry)
            output.append("")  # Blank line between TODOs

        return "\n".join(output)

    def write_to_journal(self, dry_run: bool = False) -> Path:
        """Write extracted TODOs to today's journal."""
        today = date.today()
        journal_file = self.logseq_journals / f"{today.strftime('%Y_%m_%d')}.md"

        content = self.format_for_logseq()

        if dry_run:
            print("DRY RUN - Would append to journal:")
            print(content)
            return journal_file

        # Append to existing journal or create new
        if journal_file.exists():
            existing = journal_file.read_text(encoding="utf-8")
            journal_file.write_text(existing + "\n" + content, encoding="utf-8")
        else:
            header = f"# {today.strftime('%B %d, %Y')}\n\n"
            journal_file.write_text(header + content, encoding="utf-8")

        return journal_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract embedded TODOs from markdown files to Logseq journal"
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="Directory to scan (default: entire workspace)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be extracted without modifying files",
    )

    args = parser.parse_args()

    # Determine workspace root
    workspace_root = Path(__file__).parent.parent
    scan_dir = args.dir if args.dir else workspace_root

    if not scan_dir.exists():
        print(f"Error: Directory {scan_dir} does not exist")
        return 1

    # Extract TODOs
    extractor = TodoExtractor(workspace_root)
    print(f"Scanning {scan_dir} for embedded TODOs...")
    extractor.scan_directory(scan_dir)

    if not extractor.todos:
        print("No TODOs found.")
        return 0

    print(f"\nFound {len(extractor.todos)} TODOs:")
    for i, todo in enumerate(extractor.todos, 1):
        print(f"{i}. {todo['file']}:{todo['line']} - {todo['text'][:60]}...")

    # Write to journal
    journal_file = extractor.write_to_journal(dry_run=args.dry_run)

    if args.dry_run:
        print(f"\nWould write to: {journal_file}")
    else:
        print(f"\n✅ TODOs written to {journal_file}")

    return 0


if __name__ == "__main__":
    exit(main())
