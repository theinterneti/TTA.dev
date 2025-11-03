#!/usr/bin/env python3
"""
Quick example of using the Logseq Documentation Assistant

Run from TTA.dev root:
    python local/logseq-tools/example.py
"""

import asyncio
import sys
from pathlib import Path

# Add local to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from logseq_tools.doc_assistant import (
    LogseqDocumentAnalyzer,
    LogseqDocumentFixer,
    analyze_logseq_docs,
)


async def example_full_analysis():
    """Example 1: Analyze all Logseq documentation"""

    print("=" * 60)
    print("Example 1: Full Logseq Documentation Analysis")
    print("=" * 60)

    results = await analyze_logseq_docs("logseq")

    print(f"\n✅ Analyzed {results['total_files']} files")
    print(f"📊 Total issues: {results['total_issues']}")
    print(f"⭐ Average quality: {results['average_quality_score']}/100")

    if results["files_with_issues"]:
        print(f"\n📝 {len(results['files_with_issues'])} files need attention:")
        for file_info in results["files_with_issues"][:5]:
            print(
                f"   - {file_info['file']}: {file_info['issues']} issues (score: {file_info['quality_score']})"
            )


async def example_single_file_analysis():
    """Example 2: Analyze a single file in detail"""

    print("\n" + "=" * 60)
    print("Example 2: Single File Analysis")
    print("=" * 60)

    logseq_root = Path("logseq")
    analyzer = LogseqDocumentAnalyzer(logseq_root)

    # Find a page to analyze
    pages = list((logseq_root / "pages").glob("*.md"))
    if not pages:
        print("No pages found to analyze")
        return

    test_file = pages[0]
    print(f"\n📄 Analyzing: {test_file.name}")

    analysis = await analyzer.analyze_file(test_file)

    print("\n📊 Results:")
    print(f"   Lines: {analysis.total_lines}")
    print(f"   Quality Score: {analysis.quality_score}/100")
    print(f"   Issues: {len(analysis.issues)}")
    print(f"   Page Links: {len(analysis.page_links)}")
    print(f"   Missing Links: {len(analysis.missing_links)}")

    if analysis.issues:
        print("\n🔍 Issues found:")
        for issue in analysis.issues[:5]:  # Show first 5
            print(f"   Line {issue.line_number} [{issue.severity}]: {issue.message}")

    if analysis.missing_links:
        print("\n❌ Missing page links:")
        for link in analysis.missing_links[:5]:
            print(f"   - [[{link}]]")


async def example_auto_fix():
    """Example 3: Automatically fix issues"""

    print("\n" + "=" * 60)
    print("Example 3: Auto-Fix Issues (Dry Run)")
    print("=" * 60)

    logseq_root = Path("logseq")
    analyzer = LogseqDocumentAnalyzer(logseq_root)
    fixer = LogseqDocumentFixer(analyzer)

    # Find a page to fix
    pages = list((logseq_root / "pages").glob("*.md"))
    if not pages:
        print("No pages found to fix")
        return

    test_file = pages[0]
    print(f"\n📄 Checking: {test_file.name}")

    # Dry run first
    result = await fixer.fix_file(test_file, dry_run=True)

    print("\n🔧 Fix Summary:")
    print(f"   Issues found: {result['issues_found']}")
    print(f"   Fixes available: {result['fixes_applied']}")
    print(f"   Quality score: {result['quality_score_before']}/100")
    print(f"   Dry run: {result['dry_run']}")

    if result["fixes_applied"] > 0:
        print("\n💡 To apply these fixes:")
        print(f"   result = await fixer.fix_file('{test_file}', dry_run=False)")


async def example_chat_mode():
    """Example 4: Interactive 'chat' mode for fixing docs"""

    print("\n" + "=" * 60)
    print("Example 4: Interactive Documentation Assistant")
    print("=" * 60)

    logseq_root = Path("logseq")
    analyzer = LogseqDocumentAnalyzer(logseq_root)
    fixer = LogseqDocumentFixer(analyzer)

    print("\n🤖 Logseq Documentation Assistant")
    print("   I can help you improve your Logseq documentation!")
    print()

    # Analyze all docs
    results = await analyze_logseq_docs("logseq")

    if results["total_issues"] == 0:
        print("✨ Your documentation is perfect! No issues found.")
        return

    print(f"📊 Found {results['total_issues']} issues across {results['total_files']} files")
    print(f"⭐ Average quality score: {results['average_quality_score']}/100")
    print()

    # Show top issues
    if results["files_with_issues"]:
        print("📝 Files that need attention:")
        for i, file_info in enumerate(results["files_with_issues"][:3], 1):
            print(
                f"   {i}. {file_info['file']}: {file_info['issues']} issues (score: {file_info['quality_score']})"
            )
        print()

    # Simulate fixing the worst file
    worst_file = min(results["files_with_issues"], key=lambda x: x["quality_score"])
    file_path = logseq_root / "pages" / worst_file["file"]

    if file_path.exists():
        print(f"🔧 Would you like me to fix '{worst_file['file']}'?")
        print(
            f"   This file has {worst_file['issues']} issues and a quality score of {worst_file['quality_score']}/100"
        )
        print()
        print("   In real usage, you would:")
        print("   1. Review the issues")
        print("   2. Run dry_run=True to see proposed fixes")
        print("   3. Apply fixes with dry_run=False")
        print()
        print("   Example:")
        print(f"   result = await fixer.fix_file(Path('{file_path}'), dry_run=False)")


async def main():
    """Run all examples"""

    print("🔬 Logseq Documentation Assistant - Examples")
    print("=" * 60)
    print()

    try:
        await example_full_analysis()
        await example_single_file_analysis()
        await example_auto_fix()
        await example_chat_mode()

        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you run this from the TTA.dev root directory:")
        print("  cd /home/thein/repos/TTA.dev")
        print("  python local/logseq-tools/example.py")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
