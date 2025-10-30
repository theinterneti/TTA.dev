#!/usr/bin/env python3
"""Diagnostic script to show detailed issues from doc_assistant."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, "local/logseq-tools")
from doc_assistant import LogseqDocumentAnalyzer


async def main():
    """Show detailed issues for each file."""
    analyzer = LogseqDocumentAnalyzer(Path("logseq"))

    # Get all markdown files
    logseq_root = Path("logseq")
    all_files = []

    pages_dir = logseq_root / "pages"
    journals_dir = logseq_root / "journals"

    if pages_dir.exists():
        all_files.extend(pages_dir.glob("*.md"))
    if journals_dir.exists():
        all_files.extend(journals_dir.glob("*.md"))

    print("Detailed Issue Analysis")
    print("=" * 60)

    for file_path in sorted(all_files):
        analysis = await analyzer.analyze_file(file_path)

        if analysis.issues:
            print(f"\n📄 {file_path.name}")
            print(f"   Quality Score: {analysis.quality_score:.1f}/100")
            print(f"   Issues: {len(analysis.issues)}")

            for issue in analysis.issues:
                print(
                    f"   • Line {issue.line_number}: [{issue.severity.upper()}] {issue.issue_type}"
                )
                print(f"     {issue.message}")


if __name__ == "__main__":
    asyncio.run(main())
