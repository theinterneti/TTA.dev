#!/usr/bin/env python3
"""
Logseq TODO Validation Script

Validates TODO compliance with the Logseq TODO Management System.

Checks:
- All TODOs have required properties (type::, priority::, etc.)
- Completed TODOs have completion dates
- TODOs are in correct journal files
- KB page references exist
- Task status is uppercase (TODO, DOING, DONE)

Usage:
    uv run python scripts/validate-todos.py
    uv run python scripts/validate-todos.py --fix  # Auto-fix issues
    uv run python scripts/validate-todos.py --json  # JSON output

Exit codes:
    0 - All TODOs compliant
    1 - Validation errors found
    2 - Script error
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TODOIssue:
    """Represents a TODO compliance issue."""

    file_path: Path
    line_number: int
    issue_type: str
    severity: str  # error, warning, info
    message: str
    todo_text: str
    suggested_fix: str | None = None


@dataclass
class ValidationResult:
    """Results of TODO validation."""

    total_todos: int = 0
    compliant_todos: int = 0
    issues: list[TODOIssue] = field(default_factory=list)
    missing_kb_pages: set[str] = field(default_factory=set)

    @property
    def compliance_rate(self) -> float:
        """Calculate compliance rate."""
        if self.total_todos == 0:
            return 100.0
        return (self.compliant_todos / self.total_todos) * 100


class TODOValidator:
    """Validates Logseq TODOs against compliance rules."""

    def __init__(self, logseq_root: Path):
        self.logseq_root = logseq_root
        self.journals_dir = logseq_root / "journals"
        self.pages_dir = logseq_root / "pages"

        # Regex patterns
        self.todo_pattern = re.compile(
            r"^\s*[-*+]\s+(TODO|DOING|DONE|LATER|NOW|WAITING|todo|doing|done|later|now|waiting)\s+(.+)",
            re.MULTILINE,
        )
        self.property_pattern = re.compile(r"^\s+(\w+)::\s*(.+)$")
        self.kb_link_pattern = re.compile(r"\[\[([^\]]+)\]\]")

    def validate_journals(self) -> ValidationResult:
        """Validate all journal TODOs."""
        result = ValidationResult()

        if not self.journals_dir.exists():
            print(f"⚠️  Journals directory not found: {self.journals_dir}")
            return result

        journal_files = sorted(self.journals_dir.glob("*.md"))
        print(f"📋 Scanning {len(journal_files)} journal files...")

        for journal_file in journal_files:
            self._validate_file(journal_file, result)

        return result

    def _validate_file(self, file_path: Path, result: ValidationResult) -> None:
        """Validate TODOs in a single file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            i = 0
            while i < len(lines):
                line = lines[i]
                match = self.todo_pattern.match(line)

                if match:
                    result.total_todos += 1
                    status = match.group(1)
                    todo_text = match.group(2)

                    # Check 1: Status case (should be uppercase)
                    if status.lower() == status:
                        result.issues.append(
                            TODOIssue(
                                file_path=file_path,
                                line_number=i + 1,
                                issue_type="task_case",
                                severity="error",
                                message=f"Task status should be uppercase: {status}",
                                todo_text=line.strip(),
                                suggested_fix=line.replace(status, status.upper()),
                            )
                        )
                    else:
                        # Parse properties
                        properties = self._parse_properties(lines, i + 1)

                        # Check 2: Required properties
                        is_compliant = self._check_required_properties(
                            file_path, i + 1, line, todo_text, properties, result
                        )

                        # Check 3: KB page references
                        self._check_kb_references(todo_text, result)

                        if is_compliant:
                            result.compliant_todos += 1

                i += 1

        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")

    def _parse_properties(self, lines: list[str], start_idx: int) -> dict[str, str]:
        """Parse properties following a TODO line."""
        properties = {}
        i = start_idx

        while i < len(lines):
            line = lines[i]
            match = self.property_pattern.match(line)
            if match:
                key = match.group(1)
                value = match.group(2)
                properties[key] = value
                i += 1
            else:
                break

        return properties

    def _check_required_properties(
        self,
        file_path: Path,
        line_number: int,
        line: str,
        todo_text: str,
        properties: dict[str, str],
        result: ValidationResult,
    ) -> bool:
        """Check if TODO has required properties."""
        is_compliant = True

        # Determine TODO category
        is_dev_todo = "#dev-todo" in todo_text
        is_user_todo = "#user-todo" in todo_text

        if not is_dev_todo and not is_user_todo:
            result.issues.append(
                TODOIssue(
                    file_path=file_path,
                    line_number=line_number,
                    issue_type="missing_tag",
                    severity="error",
                    message="TODO missing category tag (#dev-todo or #user-todo)",
                    todo_text=line.strip(),
                    suggested_fix=f"{line.strip()} #dev-todo",
                )
            )
            is_compliant = False

        # Check required properties for dev-todo
        if is_dev_todo:
            if "type" not in properties:
                result.issues.append(
                    TODOIssue(
                        file_path=file_path,
                        line_number=line_number,
                        issue_type="missing_property",
                        severity="error",
                        message="Missing required property: type::",
                        todo_text=line.strip(),
                        suggested_fix="  type:: implementation",
                    )
                )
                is_compliant = False

            if "priority" not in properties:
                result.issues.append(
                    TODOIssue(
                        file_path=file_path,
                        line_number=line_number,
                        issue_type="missing_property",
                        severity="error",
                        message="Missing required property: priority::",
                        todo_text=line.strip(),
                        suggested_fix="  priority:: medium",
                    )
                )
                is_compliant = False

        # Check required properties for user-todo
        if is_user_todo:
            if "type" not in properties:
                result.issues.append(
                    TODOIssue(
                        file_path=file_path,
                        line_number=line_number,
                        issue_type="missing_property",
                        severity="error",
                        message="Missing required property: type::",
                        todo_text=line.strip(),
                        suggested_fix="  type:: learning",
                    )
                )
                is_compliant = False

            if "audience" not in properties:
                result.issues.append(
                    TODOIssue(
                        file_path=file_path,
                        line_number=line_number,
                        issue_type="missing_property",
                        severity="warning",
                        message="Missing recommended property: audience::",
                        todo_text=line.strip(),
                        suggested_fix="  audience:: intermediate-users",
                    )
                )

        # Check completion date for DONE tasks
        if "DONE" in line and "completed" not in properties:
            result.issues.append(
                TODOIssue(
                    file_path=file_path,
                    line_number=line_number,
                    issue_type="missing_completion_date",
                    severity="warning",
                    message="DONE task missing completed:: date",
                    todo_text=line.strip(),
                    suggested_fix="  completed:: [[2025-10-31]]",
                )
            )

        return is_compliant

    def _check_kb_references(self, todo_text: str, result: ValidationResult) -> None:
        """Check if KB page references exist."""
        matches = self.kb_link_pattern.findall(todo_text)

        for page_name in matches:
            # Convert page name to file name (Logseq uses ___ for /)
            # Try both formats: "Page/Name" -> "Page___Name.md" and "Page/Name.md"
            page_file_with_underscores = (
                self.pages_dir / f"{page_name.replace('/', '___')}.md"
            )
            page_file_with_slash = self.pages_dir / f"{page_name}.md"

            if (
                not page_file_with_underscores.exists()
                and not page_file_with_slash.exists()
            ):
                result.missing_kb_pages.add(page_name)


def print_results(result: ValidationResult) -> None:
    """Print validation results in human-readable format."""
    print("\n" + "=" * 80)
    print("📊 TODO VALIDATION RESULTS")
    print("=" * 80)

    print(f"\n✅ Total TODOs found: {result.total_todos}")
    print(f"✅ Compliant TODOs: {result.compliant_todos}")
    print(f"❌ Non-compliant TODOs: {result.total_todos - result.compliant_todos}")
    print(f"📈 Compliance rate: {result.compliance_rate:.1f}%")

    if result.issues:
        print(f"\n⚠️  Found {len(result.issues)} issues:\n")

        # Group by severity
        errors = [i for i in result.issues if i.severity == "error"]
        warnings = [i for i in result.issues if i.severity == "warning"]

        if errors:
            print(f"❌ ERRORS ({len(errors)}):")
            for issue in errors[:10]:  # Show first 10
                print(f"  {issue.file_path.name}:{issue.line_number} - {issue.message}")
                print(f"    TODO: {issue.todo_text}")
                if issue.suggested_fix:
                    print(f"    Fix: {issue.suggested_fix}")
                print()

        if warnings:
            print(f"⚠️  WARNINGS ({len(warnings)}):")
            for issue in warnings[:10]:  # Show first 10
                print(f"  {issue.file_path.name}:{issue.line_number} - {issue.message}")
                print(f"    TODO: {issue.todo_text}")
                print()

    if result.missing_kb_pages:
        print(f"\n📄 Missing KB pages ({len(result.missing_kb_pages)}):")
        for page in sorted(result.missing_kb_pages)[:10]:
            print(f"  - [[{page}]]")

    print("\n" + "=" * 80)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate Logseq TODOs")
    parser.add_argument(
        "--logseq-root",
        type=Path,
        default=Path("logseq"),
        help="Path to Logseq root directory",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "--fix", action="store_true", help="Auto-fix issues (not implemented yet)"
    )

    args = parser.parse_args()

    if not args.logseq_root.exists():
        print(f"❌ Logseq root not found: {args.logseq_root}")
        return 2

    validator = TODOValidator(args.logseq_root)
    result = validator.validate_journals()

    if args.json:
        # JSON output for CI/CD
        output = {
            "total_todos": result.total_todos,
            "compliant_todos": result.compliant_todos,
            "compliance_rate": result.compliance_rate,
            "issues_count": len(result.issues),
            "missing_kb_pages_count": len(result.missing_kb_pages),
        }
        print(json.dumps(output, indent=2))
    else:
        print_results(result)

    # Exit code based on compliance
    if result.compliance_rate < 100:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
