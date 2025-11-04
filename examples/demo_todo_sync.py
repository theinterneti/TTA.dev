#!/usr/bin/env python3
"""Demo script to generate sample journal entries from TTA.dev codebase.

This script demonstrates the TODO sync functionality by:
1. Scanning real TTA.dev codebase for TODO comments
2. Classifying and enhancing TODOs
3. Generating formatted journal entries
4. Optionally writing to logseq/journals/

Usage:
    # Dry run (don't write files)
    python examples/demo_todo_sync.py --dry-run

    # Write to actual journals
    python examples/demo_todo_sync.py

    # Write to custom output directory
    python examples/demo_todo_sync.py --output-dir /tmp/test-journals

    # Scan specific package
    python examples/demo_todo_sync.py --package tta-dev-primitives
"""

import argparse
import asyncio
from datetime import datetime
from pathlib import Path

from tta_kb_automation.tools.todo_sync import TODOSync


async def demo_todo_sync(
    dry_run: bool = True,
    output_dir: str | None = None,
    package: str | None = None,
) -> None:
    """Demonstrate TODO sync functionality."""
    print("=" * 60)
    print("TTA.dev KB Automation - TODO Sync Demo")
    print("=" * 60)
    print()

    # Initialize the sync tool
    sync = TODOSync()

    # Determine paths to scan
    workspace_root = Path(__file__).parent.parent
    if package:
        paths = [str(workspace_root / "packages" / package / "src")]
        print(f"Scanning package: {package}")
    else:
        paths = [str(workspace_root / "packages")]
        print("Scanning all packages")

    print(f"Workspace root: {workspace_root}")
    print(f"Paths to scan: {paths}")
    print()

    # Configuration
    today = datetime.now().strftime("%Y_%m_%d")
    print(f"Journal date: {today}")
    print(f"Dry run: {dry_run}")
    if output_dir:
        print(f"Output directory: {output_dir}")
    print()

    # Phase 1: Scan
    print("=" * 60)
    print("Phase 1: Scanning Codebase")
    print("=" * 60)

    result = await sync.scan_and_create(
        paths=paths,
        journal_date=today,
        dry_run=dry_run,
        output_dir=output_dir,
    )

    print("\n✅ Scan complete!")
    print(f"   TODOs found: {result['todos_found']}")
    print(f"   TODOs created: {result['todos_created']}")

    if result["todos_found"] == 0:
        print("\n🎉 No TODOs found - codebase is clean!")
        return

    # Phase 2: Analyze
    print("\n" + "=" * 60)
    print("Phase 2: Analyzing TODOs")
    print("=" * 60)

    todos = result["todos"]

    # Group by type
    by_type = {}
    by_priority = {}
    by_package = {}

    for todo in todos:
        todo_type = todo.get("type", "unknown")
        priority = todo.get("priority", "unknown")
        pkg = todo.get("package", "unknown")

        by_type[todo_type] = by_type.get(todo_type, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1
        by_package[pkg] = by_package.get(pkg, 0) + 1

    print("\nBy Type:")
    for todo_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"  {todo_type:15s}: {count:3d}")

    print("\nBy Priority:")
    for priority, count in sorted(by_priority.items(), key=lambda x: x[1], reverse=True):
        print(f"  {priority:15s}: {count:3d}")

    print("\nBy Package:")
    for pkg, count in sorted(by_package.items(), key=lambda x: x[1], reverse=True):
        print(f"  {pkg:35s}: {count:3d}")

    # Phase 3: Sample TODOs
    print("\n" + "=" * 60)
    print("Phase 3: Sample TODOs")
    print("=" * 60)

    # Show first 5 TODOs
    for i, todo in enumerate(todos[:5], 1):
        print(f"\n--- TODO #{i} ---")
        print(f"Message: {todo['message']}")
        print(f"Type: {todo['type']}")
        print(f"Priority: {todo['priority']}")
        print(f"Package: {todo.get('package', 'N/A')}")
        print(f"File: {todo['file']}")
        print(f"Line: {todo.get('line_number', 'N/A')}")

        if "kb_links" in todo and todo["kb_links"]:
            print(f"Suggested KB links: {', '.join(todo['kb_links'])}")

    if len(todos) > 5:
        print(f"\n... and {len(todos) - 5} more TODOs")

    # Phase 4: Journal Entry Preview
    print("\n" + "=" * 60)
    print("Phase 4: Journal Entry Preview")
    print("=" * 60)

    if dry_run:
        print("\n⚠️  DRY RUN - No files written")
        print("\nTo write to journal, run without --dry-run:")
        print(f"  python {Path(__file__).name}")
    else:
        print(f"\n✅ Journal entry written to: {result['journal_path']}")

        # Read and display the file if it exists
        journal_path = Path(result["journal_path"])
        if journal_path.exists():
            print("\nGenerated content (first 30 lines):")
            print("-" * 60)
            content = journal_path.read_text()
            lines = content.split("\n")
            for line in lines[:30]:
                print(line)
            if len(lines) > 30:
                print(f"... and {len(lines) - 30} more lines")
            print("-" * 60)

    # Phase 5: Format a sample TODO
    print("\n" + "=" * 60)
    print("Phase 5: Formatted TODO Example")
    print("=" * 60)

    if todos:
        sample = todos[0]
        formatted = sync.format_todo_entry(sample)
        print("\nLogseq format:")
        print("-" * 60)
        print(formatted)
        print("-" * 60)

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Demo TODO sync functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Usage:")[1],
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write journal files (default: True)",
    )

    parser.add_argument(
        "--write",
        action="store_true",
        help="Write journal files (opposite of --dry-run)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        help="Custom output directory for journals (for testing)",
    )

    parser.add_argument(
        "--package",
        type=str,
        help="Specific package to scan (e.g., tta-dev-primitives)",
    )

    args = parser.parse_args()

    # Default to dry run unless --write is specified
    dry_run = not args.write if args.write else True

    try:
        asyncio.run(
            demo_todo_sync(
                dry_run=dry_run,
                output_dir=args.output_dir,
                package=args.package,
            )
        )
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
