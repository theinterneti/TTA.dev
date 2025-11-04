#!/usr/bin/env python3
"""Run KB link validation and generate report."""

import asyncio
import sys
from pathlib import Path

# Add package to path
sys.path.insert(
    0, str(Path(__file__).parent.parent / "packages" / "tta-kb-automation" / "src")
)

from tta_kb_automation.tools import LinkValidator


async def main():
    """Run validation."""
    print("🔍 Validating KB links...")
    print("KB path: logseq/")
    print()

    validator = LinkValidator(kb_path="logseq", use_cache=False)
    result = await validator.validate()

    # Print summary
    print("=" * 80)
    print(result["summary"])
    print("=" * 80)
    print()

    # Show broken links (first 20)
    broken = result.get("broken_links", [])
    if broken:
        print(f"📊 Broken Links (showing first 20 of {len(broken)}):")
        for i, link in enumerate(broken[:20], 1):
            source = link.get("source", link.get("source_page", "unknown"))
            target = link.get("target", "unknown")
            print(f"  {i}. {source} -> [[{target}]]")
        print()

    # Show orphaned pages (first 20)
    orphaned = result.get("orphaned_pages", [])
    if orphaned:
        print(f"🔗 Orphaned Pages (showing first 20 of {len(orphaned)}):")
        for i, page in enumerate(orphaned[:20], 1):
            print(f"  {i}. {page}")
        print()

    # Write full report
    report_path = Path("/tmp/kb_validation_report.md")
    with open(report_path, "w") as f:
        f.write(result["report"])
    print(f"📄 Full report written to: {report_path}")

    return 0 if len(broken) == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
