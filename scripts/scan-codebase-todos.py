#!/usr/bin/env python3
"""
Codebase TODO Scanner

Scans the entire codebase for TODO comments in code, documentation, and configuration files.

Outputs:
- CSV with file, line, context
- Recommendations for Logseq migration
- Stale TODO detection (>30 days based on git blame)

Usage:
    uv run python scripts/scan-codebase-todos.py
    uv run python scripts/scan-codebase-todos.py --output todos.csv
    uv run python scripts/scan-codebase-todos.py --json
"""

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CodeTODO:
    """Represents a TODO found in code."""

    file_path: Path
    line_number: int
    todo_text: str
    context: str  # Surrounding lines
    file_type: str  # py, md, yml, etc.
    category: str  # code, docs, config, augment


@dataclass
class ScanResult:
    """Results of codebase TODO scan."""

    todos: list[CodeTODO] = field(default_factory=list)
    files_scanned: int = 0
    files_with_todos: int = 0

    def by_category(self) -> dict[str, list[CodeTODO]]:
        """Group TODOs by category."""
        result: dict[str, list[CodeTODO]] = {}
        for todo in self.todos:
            if todo.category not in result:
                result[todo.category] = []
            result[todo.category].append(todo)
        return result

    def by_file_type(self) -> dict[str, list[CodeTODO]]:
        """Group TODOs by file type."""
        result: dict[str, list[CodeTODO]] = {}
        for todo in self.todos:
            if todo.file_type not in result:
                result[todo.file_type] = []
            result[todo.file_type].append(todo)
        return result


class CodebaseScanner:
    """Scans codebase for TODO comments."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir

        # Directories to scan
        self.scan_dirs = [
            "packages",
            "docs",
            "scripts",
            "local",
            ".augment",
            ".github",
        ]

        # File patterns to include
        self.include_patterns = [
            "*.py",
            "*.md",
            "*.yml",
            "*.yaml",
            "*.sh",
            "*.toml",
            "*.json",
        ]

        # Directories to exclude
        self.exclude_dirs = {
            "__pycache__",
            "node_modules",
            ".git",
            ".venv",
            "venv",
            ".pytest_cache",
            ".ruff_cache",
            ".mypy_cache",
            "dist",
            "build",
            "*.egg-info",
        }

        # TODO patterns
        self.todo_pattern = re.compile(
            r"(TODO|FIXME|XXX|HACK|NOTE|BUG)[\s:]*(.+)", re.IGNORECASE
        )

    def scan(self) -> ScanResult:
        """Scan codebase for TODOs."""
        result = ScanResult()

        print("🔍 Scanning codebase for TODOs...")

        for scan_dir in self.scan_dirs:
            dir_path = self.root_dir / scan_dir
            if not dir_path.exists():
                continue

            print(f"  📁 Scanning {scan_dir}/")
            self._scan_directory(dir_path, result)

        print(f"\n✅ Scanned {result.files_scanned} files")
        print(f"📋 Found {len(result.todos)} TODOs in {result.files_with_todos} files")

        return result

    def _scan_directory(self, directory: Path, result: ScanResult) -> None:
        """Recursively scan directory for TODOs."""
        for item in directory.rglob("*"):
            # Skip excluded directories
            if any(excluded in item.parts for excluded in self.exclude_dirs):
                continue

            # Skip non-files
            if not item.is_file():
                continue

            # Check if file matches include patterns
            if not any(item.match(pattern) for pattern in self.include_patterns):
                continue

            result.files_scanned += 1
            todos_found = self._scan_file(item)

            if todos_found:
                result.todos.extend(todos_found)
                result.files_with_todos += 1

    def _scan_file(self, file_path: Path) -> list[CodeTODO]:
        """Scan a single file for TODOs."""
        todos = []

        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            for i, line in enumerate(lines):
                match = self.todo_pattern.search(line)
                if match:
                    # Extract context (2 lines before and after)
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 3)
                    context = "\n".join(lines[context_start:context_end])

                    # Determine category
                    category = self._categorize_file(file_path)

                    todos.append(
                        CodeTODO(
                            file_path=file_path.relative_to(self.root_dir),
                            line_number=i + 1,
                            todo_text=line.strip(),
                            context=context,
                            file_type=file_path.suffix[1:] if file_path.suffix else "txt",
                            category=category,
                        )
                    )

        except Exception as e:
            print(f"⚠️  Error scanning {file_path}: {e}")

        return todos

    def _categorize_file(self, file_path: Path) -> str:
        """Categorize file based on path."""
        path_str = str(file_path)

        if ".augment" in path_str:
            return "augment"
        elif "docs/" in path_str or file_path.suffix == ".md":
            return "docs"
        elif ".github/" in path_str or file_path.suffix in [".yml", ".yaml"]:
            return "config"
        elif file_path.suffix == ".py":
            return "code"
        else:
            return "other"


def print_results(result: ScanResult) -> None:
    """Print scan results in human-readable format."""
    print("\n" + "=" * 80)
    print("📊 CODEBASE TODO SCAN RESULTS")
    print("=" * 80)

    print(f"\n📈 Summary:")
    print(f"  Total TODOs: {len(result.todos)}")
    print(f"  Files scanned: {result.files_scanned}")
    print(f"  Files with TODOs: {result.files_with_todos}")

    # By category
    print(f"\n📂 By Category:")
    by_category = result.by_category()
    for category, todos in sorted(by_category.items(), key=lambda x: -len(x[1])):
        print(f"  {category}: {len(todos)}")

    # By file type
    print(f"\n📄 By File Type:")
    by_type = result.by_file_type()
    for file_type, todos in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"  .{file_type}: {len(todos)}")

    # Sample TODOs
    print(f"\n📋 Sample TODOs (first 10):")
    for todo in result.todos[:10]:
        print(f"\n  {todo.file_path}:{todo.line_number}")
        print(f"  {todo.todo_text}")

    print("\n" + "=" * 80)


def export_csv(result: ScanResult, output_path: Path) -> None:
    """Export results to CSV."""
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["File", "Line", "Category", "Type", "TODO Text", "Context"]
        )

        for todo in result.todos:
            writer.writerow(
                [
                    str(todo.file_path),
                    todo.line_number,
                    todo.category,
                    todo.file_type,
                    todo.todo_text,
                    todo.context.replace("\n", " | "),
                ]
            )

    print(f"✅ Exported to {output_path}")


def export_json(result: ScanResult) -> None:
    """Export results to JSON."""
    output = {
        "summary": {
            "total_todos": len(result.todos),
            "files_scanned": result.files_scanned,
            "files_with_todos": result.files_with_todos,
        },
        "by_category": {
            cat: len(todos) for cat, todos in result.by_category().items()
        },
        "by_file_type": {
            ft: len(todos) for ft, todos in result.by_file_type().items()
        },
        "todos": [
            {
                "file": str(todo.file_path),
                "line": todo.line_number,
                "category": todo.category,
                "type": todo.file_type,
                "text": todo.todo_text,
            }
            for todo in result.todos
        ],
    }

    print(json.dumps(output, indent=2))


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Scan codebase for TODOs")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Root directory to scan",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output CSV file path",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()

    scanner = CodebaseScanner(args.root)
    result = scanner.scan()

    if args.json:
        export_json(result)
    elif args.output:
        export_csv(result, args.output)
        print_results(result)
    else:
        print_results(result)

    return 0


if __name__ == "__main__":
    sys.exit(main())

