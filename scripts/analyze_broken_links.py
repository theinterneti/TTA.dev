#!/usr/bin/env python3
"""Analyze broken links in Logseq KB and generate fix recommendations."""

import asyncio
from collections import defaultdict
from pathlib import Path

from tta_kb_automation import (
    ExtractLinks,
    ParseLogseqPages,
    ValidateLinks,
    WorkflowContext,
)


async def main():
    """Analyze broken links and provide recommendations."""
    context = WorkflowContext(workflow_id="local-link-analysis")
    kb_root = Path("logseq")

    # Step 1: Parse pages
    print("📖 Parsing Logseq pages...")
    parser = ParseLogseqPages(kb_path=kb_root)
    parse_result = await parser.execute({}, context)
    pages = parse_result["pages"]
    print(f"✅ Parsed {len(pages)} pages")

    # Step 2: Extract links
    print("\n🔗 Extracting links...")
    extractor = ExtractLinks()
    links_result = await extractor.execute({"pages": pages}, context)
    links = links_result["links"]
    print(f"✅ Extracted {len(links)} links")

    # Step 3: Validate links
    print("\n✓ Validating links...")
    validator = ValidateLinks()
    result = await validator.execute({"pages": pages, "links": links}, context)

    broken = result["broken_links"]
    valid_links_data = result.get("valid_links", [])
    valid_count = len(valid_links_data) if isinstance(valid_links_data, list) else valid_links_data

    print("\n📊 Validation Results:")
    print(f"  ✅ Valid links: {valid_count}")
    print(f"  ❌ Broken links: {len(broken)}")
    total = valid_count + len(broken)
    if total > 0:
        print(f"  📈 Success rate: {valid_count / total * 100:.1f}%")

    # Group by source to see which pages have the most issues
    by_source = defaultdict(list)
    for link in broken:
        by_source[link["source"]].append(link["target"])

    # Group by target to see most commonly missing pages
    by_target = defaultdict(list)
    for link in broken:
        by_target[link["target"]].append(link["source"])

    print("\n📋 Top 15 pages with most broken links:")
    sorted_sources = sorted(by_source.items(), key=lambda x: len(x[1]), reverse=True)
    for source, targets in sorted_sources[:15]:
        print(f"  {source}: {len(targets)} broken links")

    print("\n🎯 Top 15 most commonly missing target pages:")
    sorted_targets = sorted(by_target.items(), key=lambda x: len(x[1]), reverse=True)
    for target, sources in sorted_targets[:15]:
        print(f"  {target}: referenced by {len(sources)} pages")

    # Save detailed report
    report_path = Path("kb-broken-links-analysis.txt")
    with open(report_path, "w") as f:
        f.write("KB Broken Links Analysis Report\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total pages: {len(pages)}\n")
        f.write(f"Total links: {len(links)}\n")
        f.write(f"Valid links: {valid_count}\n")
        f.write(f"Broken links: {len(broken)}\n")
        if total > 0:
            f.write(f"Success rate: {valid_count / total * 100:.1f}%\n\n")
        else:
            f.write("Success rate: N/A\n\n")

        f.write("=" * 80 + "\n")
        f.write("PAGES WITH MOST BROKEN LINKS (Fix Priority)\n")
        f.write("=" * 80 + "\n\n")
        for i, (source, targets) in enumerate(sorted_sources[:30], 1):
            f.write(f"{i}. {source} ({len(targets)} broken links)\n")
            for target in targets[:10]:  # Show first 10
                f.write(f"   -> {target}\n")
            if len(targets) > 10:
                f.write(f"   ... and {len(targets) - 10} more\n")
            f.write("\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("MOST COMMONLY MISSING PAGES (Create Priority)\n")
        f.write("=" * 80 + "\n\n")
        for i, (target, sources) in enumerate(sorted_targets[:30], 1):
            f.write(f"{i}. {target} (referenced by {len(sources)} pages - HIGH IMPACT)\n")
            for source in sources[:5]:  # Show first 5 sources
                f.write(f"   <- {source}\n")
            if len(sources) > 5:
                f.write(f"   ... and {len(sources) - 5} more sources\n")
            f.write("\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("ALL BROKEN LINKS (Full List)\n")
        f.write("=" * 80 + "\n\n")
        for source, targets in sorted_sources:
            f.write(f"\n{source}:\n")
            for target in targets:
                f.write(f"  -> {target}\n")

    print(f"\n✅ Detailed report saved to {report_path}")
    print("\n💡 Recommendations:")
    print("   1. Focus on creating the top 15 missing pages first (high impact)")
    print("   2. Fix pages with most broken links (top 15 sources)")
    print("   3. Consider if some links should be external URLs instead")


if __name__ == "__main__":
    asyncio.run(main())
