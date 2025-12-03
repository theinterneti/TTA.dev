#!/usr/bin/env python3
"""KB Automation Demo - Demonstrates all kb-automation workflows.

This script runs all the KB automation workflows to show they're working.

Usage:
    uv run python examples/kb_automation_demo.py
"""

import asyncio

# Ensure we can find the packages
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).parent.parent / "platform" / "kb-automation" / "src")
)

from tta_kb_automation.workflows import (
    build_cross_references,
    build_session_context,
    document_feature,
    pre_commit_validation,
    validate_kb_links,
)


async def run_demo():
    """Run all KB automation workflows."""
    print("=" * 60)
    print("🤖 TTA.dev KB Automation Demo")
    print("=" * 60)

    # Define paths
    kb_path = "logseq"
    code_path = "platform"

    # Check if paths exist
    kb_exists = Path(kb_path).exists()
    code_exists = Path(code_path).exists()

    print("\n📂 Paths:")
    print(f"   KB Path: {kb_path} ({'✅ exists' if kb_exists else '❌ not found'})")
    print(
        f"   Code Path: {code_path} ({'✅ exists' if code_exists else '❌ not found'})"
    )

    if not kb_exists or not code_exists:
        print(
            "\n⚠️  Some paths not found. Using available paths or creating temp structure."
        )

    # 1. Validate KB Links
    print("\n" + "=" * 60)
    print("1️⃣  VALIDATE KB LINKS")
    print("=" * 60)

    try:
        if kb_exists:
            result = await validate_kb_links(kb_path)
            print("\n📊 Results:")
            print(f"   Total pages: {result.get('total_pages', 0)}")
            print(f"   Valid links: {result.get('total_valid', 0)}")
            print(f"   Broken links: {result.get('total_broken', 0)}")
            print(f"   Orphaned pages: {result.get('total_orphaned', 0)}")
            print(f"\n📝 Summary:\n{result.get('summary', 'N/A')}")
        else:
            print("   ⏭️  Skipped (KB path not found)")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 2. Build Session Context
    print("\n" + "=" * 60)
    print("2️⃣  BUILD SESSION CONTEXT")
    print("=" * 60)

    try:
        if kb_exists and code_exists:
            result = await build_session_context(
                topic="CachePrimitive",
                kb_path=kb_path,
                code_path=code_path,
            )
            print(f"\n📊 Results for topic '{result.get('topic', 'N/A')}':")
            print(f"   KB pages found: {len(result.get('kb_pages', []))}")
            print(f"   Code files found: {len(result.get('code_files', []))}")
            print(f"   TODOs found: {len(result.get('todos', []))}")
            print(f"   Tests found: {len(result.get('tests', []))}")
            print(f"   Related topics: {result.get('related_topics', [])[:5]}")
            print(f"\n📝 Summary:\n{result.get('summary', 'N/A')}")
        else:
            print("   ⏭️  Skipped (paths not found)")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 3. Build Cross References
    print("\n" + "=" * 60)
    print("3️⃣  BUILD CROSS REFERENCES")
    print("=" * 60)

    try:
        if kb_exists and code_exists:
            result = await build_cross_references(
                kb_path=kb_path,
                code_path=code_path,
            )
            stats = result.get("stats", {})
            print("\n📊 Results:")
            print(f"   KB pages: {stats.get('total_kb_pages', 0)}")
            print(f"   Code files: {stats.get('total_code_files', 0)}")
            print(f"   KB → Code refs: {stats.get('kb_pages_with_code_refs', 0)}")
            print(f"   Code → KB refs: {stats.get('code_files_with_kb_refs', 0)}")
            print(f"   Missing references: {len(result.get('missing_references', []))}")
            print(f"   Suggestions generated: {len(result.get('suggestions', []))}")
        else:
            print("   ⏭️  Skipped (paths not found)")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 4. Document Feature (creates a temp page)
    print("\n" + "=" * 60)
    print("4️⃣  DOCUMENT FEATURE")
    print("=" * 60)

    try:
        if code_exists:
            # Use a temp directory for the demo to avoid modifying real KB
            import tempfile

            with tempfile.TemporaryDirectory() as temp_kb:
                Path(temp_kb, "pages").mkdir(parents=True)
                Path(temp_kb, "journals").mkdir(parents=True)

                result = await document_feature(
                    feature_name="RetryPrimitive",
                    code_path=code_path,
                    kb_path=temp_kb,
                )
                print("\n📊 Results:")
                print(f"   Created pages: {result.get('created_pages', [])}")
                print(f"   Updated pages: {result.get('updated_pages', [])}")
                print(f"   Code files analyzed: {result.get('code_files_analyzed', 0)}")
                print(
                    f"   Docstrings extracted: {result.get('docstrings_extracted', 0)}"
                )
                print(f"   Examples extracted: {result.get('examples_extracted', 0)}")

                # Show generated page content
                page_path = Path(result.get("page_path", ""))
                if page_path.exists():
                    content = page_path.read_text()
                    preview = content[:500] + "..." if len(content) > 500 else content
                    print(f"\n📝 Generated page preview:\n{preview}")
        else:
            print("   ⏭️  Skipped (code path not found)")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 5. Pre-commit Validation
    print("\n" + "=" * 60)
    print("5️⃣  PRE-COMMIT VALIDATION")
    print("=" * 60)

    try:
        if kb_exists and code_exists:
            result = await pre_commit_validation(
                kb_path=kb_path,
                code_path=code_path,
            )
            print("\n📊 Results:")
            print(f"   Passed: {'✅ Yes' if result.get('passed') else '❌ No'}")

            link_val = result.get("link_validation", {})
            print("   Link validation:")
            print(f"      - Broken links: {link_val.get('broken_links', 0)}")
            print(f"      - Orphaned pages: {link_val.get('orphaned_pages', 0)}")
            print(f"      - Valid links: {link_val.get('valid_links', 0)}")

            todo_check = result.get("todo_check", {})
            print("   TODO check:")
            print(f"      - TODOs in code: {todo_check.get('total_todos_in_code', 0)}")
            print(f"      - Files with TODOs: {todo_check.get('files_with_todos', 0)}")

            xref_check = result.get("cross_ref_check", {})
            print("   Cross-reference check:")
            print(f"      - Missing refs: {xref_check.get('missing_references', 0)}")

            issues = result.get("issues", [])
            if issues:
                print(f"\n⚠️  Issues found ({len(issues)}):")
                for issue in issues[:5]:
                    print(f"      - {issue}")
            else:
                print("\n✨ No issues found!")

            print(f"\n📝 Summary: {result.get('summary', 'N/A')}")
        else:
            print("   ⏭️  Skipped (paths not found)")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Final summary
    print("\n" + "=" * 60)
    print("✅ KB AUTOMATION DEMO COMPLETE")
    print("=" * 60)
    print("""
All workflows demonstrated:

1. validate_kb_links - Checks for broken [[Page]] links and orphaned pages
2. build_session_context - Generates comprehensive context from a topic name
3. build_cross_references - Maps code ↔ KB relationships
4. document_feature - Auto-generates KB pages from code analysis
5. pre_commit_validation - Runs all KB quality checks

These workflows compose TTA.dev primitives (SequentialPrimitive, ParallelPrimitive,
CachePrimitive, RetryPrimitive) for reliable, observable KB automation.

For usage in your code:
    from tta_kb_automation.workflows import validate_kb_links, pre_commit_validation
    
    # In pre-commit hook:
    result = await pre_commit_validation("logseq", "platform")
    if not result["passed"]:
        print("KB issues found:", result["issues"])
        sys.exit(1)
""")


if __name__ == "__main__":
    asyncio.run(run_demo())
