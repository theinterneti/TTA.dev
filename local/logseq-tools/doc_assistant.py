"""
Logseq Documentation Assistant - EXPERIMENTAL

A primitive and workflow for analyzing and improving Logseq documentation.

This is experimental code that lives in local/ and is NOT part of the public release.

Features:
- Analyze Logseq markdown files for quality issues
- Fix formatting problems (MD linting)
- Improve structure and clarity
- Generate missing sections
- Validate page links
- Apply Logseq best practices

Author: TTA.dev
Created: 2025-10-30
Status: Experimental / Prototype
"""

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class LogseqDocIssue:
    """Represents a documentation quality issue."""

    file_path: Path
    line_number: int
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    suggested_fix: str | None = None


@dataclass
class LogseqDocAnalysis:
    """Results of analyzing Logseq documentation."""

    file_path: Path
    total_lines: int
    issues: list[LogseqDocIssue]
    page_links: list[str]
    missing_links: list[str]
    broken_structure: bool
    quality_score: float  # 0-100


class LogseqDocumentAnalyzer:
    """Analyzes Logseq markdown files for quality issues."""

    def __init__(self, logseq_root: Path):
        self.logseq_root = Path(logseq_root)
        self.pages_dir = self.logseq_root / "pages"
        self.journals_dir = self.logseq_root / "journals"

    async def analyze_file(self, file_path: Path) -> LogseqDocAnalysis:
        """Analyze a single Logseq markdown file."""

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        issues = []
        page_links = self._extract_page_links(content)
        missing_links = await self._find_missing_links(page_links)

        # Check for common issues
        issues.extend(self._check_heading_structure(lines))
        issues.extend(self._check_list_formatting(lines))
        issues.extend(self._check_task_syntax(lines))
        issues.extend(self._check_code_blocks(lines))
        issues.extend(self._check_link_formatting(lines))

        # Calculate quality score
        quality_score = self._calculate_quality_score(len(lines), issues)

        return LogseqDocAnalysis(
            file_path=file_path,
            total_lines=len(lines),
            issues=issues,
            page_links=page_links,
            missing_links=missing_links,
            broken_structure=self._has_broken_structure(lines),
            quality_score=quality_score,
        )

    def _extract_page_links(self, content: str) -> list[str]:
        """Extract [[Page Links]] from content."""
        return re.findall(r"\[\[(.*?)\]\]", content)

    async def _find_missing_links(self, page_links: list[str]) -> list[str]:
        """Find page links that don't have corresponding files."""
        missing = []

        for link in page_links:
            # Convert page link to filename
            filename = f"{link}.md"
            page_path = self.pages_dir / filename

            if not page_path.exists():
                missing.append(link)

        return missing

    def _check_heading_structure(self, lines: list[str]) -> list[LogseqDocIssue]:
        """Check for heading structure issues."""
        issues = []
        prev_level = 0

        for i, line in enumerate(lines, 1):
            if line.startswith("#"):
                # Count heading level
                level = len(line) - len(line.lstrip("#"))

                # Check for skipped levels
                if level > prev_level + 1:
                    issues.append(
                        LogseqDocIssue(
                            file_path=Path("current"),
                            line_number=i,
                            issue_type="heading_skip",
                            severity="warning",
                            message=f"Heading level skipped from {prev_level} to {level}",
                            suggested_fix=f"Use heading level {prev_level + 1} instead",
                        )
                    )

                # Check for missing space after #
                if not line.startswith("# ") and level == 1:
                    issues.append(
                        LogseqDocIssue(
                            file_path=Path("current"),
                            line_number=i,
                            issue_type="heading_format",
                            severity="error",
                            message="Missing space after # in heading",
                            suggested_fix=line.replace("#", "# ", 1),
                        )
                    )

                prev_level = level

        return issues

    def _check_list_formatting(self, lines: list[str]) -> list[LogseqDocIssue]:
        """Check for list formatting issues."""
        issues = []
        in_list = False

        for i, line in enumerate(lines, 1):
            stripped = line.lstrip()

            # Check if this is a list item
            if stripped.startswith(("-", "*", "+")):
                if not in_list and i > 1 and lines[i - 2].strip():
                    issues.append(
                        LogseqDocIssue(
                            file_path=Path("current"),
                            line_number=i,
                            issue_type="list_spacing",
                            severity="warning",
                            message="Missing blank line before list",
                            suggested_fix="Add blank line before list",
                        )
                    )
                in_list = True
            elif in_list and stripped and not stripped.startswith((" ", "\t")):
                # End of list
                if i < len(lines) and lines[i].strip():
                    issues.append(
                        LogseqDocIssue(
                            file_path=Path("current"),
                            line_number=i,
                            issue_type="list_spacing",
                            severity="warning",
                            message="Missing blank line after list",
                            suggested_fix="Add blank line after list",
                        )
                    )
                in_list = False

        return issues

    def _check_task_syntax(self, lines: list[str]) -> list[LogseqDocIssue]:
        """Check for Logseq task syntax issues."""
        issues = []
        valid_statuses = {"TODO", "DOING", "DONE", "LATER", "NOW", "WAITING"}

        for i, line in enumerate(lines, 1):
            # Check for task markers (only in list items, not bold text)
            # Match: "- TODO" or "  - TODO" but NOT "**Status:** TODO"
            task_match = re.match(
                r"^\s*[-*+]\s+(TODO|DOING|DONE|LATER|NOW|WAITING|todo|doing|done|later)\s",
                line,
            )
            if task_match:
                status = task_match.group(1)

                # Check if lowercase (should be uppercase in Logseq)
                if status.lower() == status:
                    issues.append(
                        LogseqDocIssue(
                            file_path=Path("current"),
                            line_number=i,
                            issue_type="task_case",
                            severity="error",
                            message=f"Task status should be uppercase: {status}",
                            suggested_fix=line.replace(status, status.upper()),
                        )
                    )

        return issues

    def _check_code_blocks(self, lines: list[str]) -> list[LogseqDocIssue]:
        """Check for code block formatting issues."""
        issues = []
        in_code_block = False
        code_block_line = 0

        for i, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                if not in_code_block:
                    # Opening code block
                    in_code_block = True
                    code_block_line = i

                    # Check for language specifier
                    if line.strip() == "```":
                        issues.append(
                            LogseqDocIssue(
                                file_path=Path("current"),
                                line_number=i,
                                issue_type="code_language",
                                severity="warning",
                                message="Code block missing language specifier",
                                suggested_fix="Add language: ```python, ```bash, etc.",
                            )
                        )
                else:
                    # Closing code block
                    in_code_block = False

        # Check for unclosed code block
        if in_code_block:
            issues.append(
                LogseqDocIssue(
                    file_path=Path("current"),
                    line_number=code_block_line,
                    issue_type="code_unclosed",
                    severity="error",
                    message="Unclosed code block",
                    suggested_fix="Add closing ```",
                )
            )

        return issues

    def _check_link_formatting(self, lines: list[str]) -> list[LogseqDocIssue]:
        """Check for link formatting issues."""
        issues = []

        for i, line in enumerate(lines, 1):
            # Check for bare URLs (should be in angle brackets or as proper links)
            url_pattern = r"(?<![<\(\[])(https?://[^\s\)>]+)(?![>\)\]])"
            bare_urls = re.finditer(url_pattern, line)

            for match in bare_urls:
                issues.append(
                    LogseqDocIssue(
                        file_path=Path("current"),
                        line_number=i,
                        issue_type="bare_url",
                        severity="info",
                        message="Bare URL found",
                        suggested_fix=f"Wrap in angle brackets: <{match.group(1)}>",
                    )
                )

        return issues

    def _has_broken_structure(self, lines: list[str]) -> bool:
        """Check if document has broken structure."""
        # Very basic check - could be much more sophisticated
        has_heading = any(line.startswith("#") for line in lines)
        return not has_heading and len(lines) > 10

    def _calculate_quality_score(self, total_lines: int, issues: list[LogseqDocIssue]) -> float:
        """Calculate a quality score (0-100) based on issues found."""
        if total_lines == 0:
            return 0.0

        # Weight issues by severity
        error_weight = 10
        warning_weight = 5
        info_weight = 1

        total_deductions = sum(
            error_weight
            if issue.severity == "error"
            else warning_weight
            if issue.severity == "warning"
            else info_weight
            for issue in issues
        )

        # Calculate score
        max_possible = total_lines * 0.5  # Reasonable maximum deductions
        score = max(0, 100 - (total_deductions / max_possible * 100))

        return round(score, 2)


class LogseqDocumentFixer:
    """Automatically fixes common documentation issues."""

    def __init__(self, analyzer: LogseqDocumentAnalyzer):
        self.analyzer = analyzer

    async def fix_file(
        self, file_path: Path, fix_types: list[str] | None = None, dry_run: bool = True
    ) -> dict[str, Any]:
        """Fix issues in a file. Returns summary of fixes applied."""

        # Analyze first
        analysis = await self.analyzer.analyze_file(file_path)

        if not analysis.issues:
            return {
                "file": str(file_path),
                "fixes_applied": 0,
                "message": "No issues found",
            }

        # Read content
        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        fixes_applied = 0

        # Sort issues by line number (descending) so we can modify without affecting line numbers
        sorted_issues = sorted(analysis.issues, key=lambda x: x.line_number, reverse=True)

        for issue in sorted_issues:
            # Skip if not in fix_types (if specified)
            if fix_types and issue.issue_type not in fix_types:
                continue

            # Skip if no suggested fix
            if not issue.suggested_fix:
                continue

            # Apply fix
            if issue.issue_type == "task_case":
                lines[issue.line_number - 1] = issue.suggested_fix
                fixes_applied += 1

            elif issue.issue_type == "heading_format":
                lines[issue.line_number - 1] = issue.suggested_fix
                fixes_applied += 1

            elif issue.issue_type == "list_spacing":
                if "before" in issue.message:
                    lines.insert(issue.line_number - 1, "")
                else:
                    lines.insert(issue.line_number, "")
                fixes_applied += 1

        # Write back if not dry run
        if not dry_run and fixes_applied > 0:
            fixed_content = "\n".join(lines)
            file_path.write_text(fixed_content, encoding="utf-8")

        return {
            "file": str(file_path),
            "fixes_applied": fixes_applied,
            "issues_found": len(analysis.issues),
            "quality_score_before": analysis.quality_score,
            "dry_run": dry_run,
        }


async def analyze_logseq_docs(logseq_root: str = "logseq") -> dict[str, Any]:
    """
    Analyze all Logseq documentation files.

    Usage:
        import asyncio
        from local.logseq_tools.doc_assistant import analyze_logseq_docs

        results = asyncio.run(analyze_logseq_docs())
        print(f"Total issues: {results['total_issues']}")
    """

    analyzer = LogseqDocumentAnalyzer(Path(logseq_root))

    # Find all markdown files
    pages = list(analyzer.pages_dir.glob("*.md")) if analyzer.pages_dir.exists() else []
    journals = list(analyzer.journals_dir.glob("*.md")) if analyzer.journals_dir.exists() else []

    all_files = pages + journals

    if not all_files:
        return {
            "error": "No markdown files found in Logseq directory",
            "logseq_root": str(analyzer.logseq_root),
        }

    # Analyze all files
    analyses = await asyncio.gather(*[analyzer.analyze_file(f) for f in all_files])

    # Aggregate results
    total_issues = sum(len(a.issues) for a in analyses)
    avg_quality = sum(a.quality_score for a in analyses) / len(analyses)

    files_with_issues = [
        {
            "file": str(a.file_path.name),
            "issues": len(a.issues),
            "quality_score": a.quality_score,
            "missing_links": a.missing_links,
        }
        for a in analyses
        if a.issues
    ]

    return {
        "total_files": len(all_files),
        "total_issues": total_issues,
        "average_quality_score": round(avg_quality, 2),
        "files_with_issues": files_with_issues,
        "summary": {
            "pages_analyzed": len(pages),
            "journals_analyzed": len(journals),
            "files_needing_attention": len(files_with_issues),
        },
    }


if __name__ == "__main__":
    # Quick test
    import sys

    logseq_root = sys.argv[1] if len(sys.argv) > 1 else "logseq"

    print(f"Analyzing Logseq documentation in: {logseq_root}")
    print("=" * 60)

    results = asyncio.run(analyze_logseq_docs(logseq_root))

    if "error" in results:
        print(f"❌ Error: {results['error']}")
    else:
        print(f"✅ Analyzed {results['total_files']} files")
        print(f"📊 Total issues found: {results['total_issues']}")
        print(f"⭐ Average quality score: {results['average_quality_score']}/100")
        print()

        if results["files_with_issues"]:
            print("Files needing attention:")
            for file_info in results["files_with_issues"][:5]:  # Show top 5
                print(
                    f"  - {file_info['file']}: {file_info['issues']} issues (score: {file_info['quality_score']})"
                )
