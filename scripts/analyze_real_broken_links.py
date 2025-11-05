#!/usr/bin/env python3
"""Analyze REAL broken links in Logseq KB (filtering out tags, dates, file refs)."""

import asyncio
import re
from collections import defaultdict
from pathlib import Path

from tta_kb_automation import (
    ExtractLinks,
    ParseLogseqPages,
    ValidateLinks,
    WorkflowContext,
)


def is_false_positive(target: str) -> tuple[bool, str]:
    """Check if a broken link is actually a false positive.

    Returns: (is_false_positive, reason)
    """
    # Tags (start with #)
    if target.startswith("#"):
        return True, "tag"

    # File links
    if target.startswith("file:") or target.startswith("http"):
        return True, "external"

    # Date patterns
    if re.match(r"^\d{4}-\d{2}-\d{2}$", target):  # YYYY-MM-DD
        return True, "date"

    # Date placeholders
    if "YYYY" in target or "MM" in target or "DD" in target:
        return True, "date_placeholder"

    # Common inline tags/categories (not actual pages)
    inline_tags = {
        "Beginner",
        "Intermediate",
        "Advanced",
        "Expert",
        "Draft",
        "Stable",
        "Experimental",
        "Deprecated",
        "High",
        "Medium",
        "Low",
        "Active",
        "Public",
        "Private",
        "TODO",
        "DOING",
        "DONE",
        "Meta-Project",
        "Project Hub",
        "Critical",
        "Component Page",
        "Integration Page",
        "Primitive",
        "Core Workflow",
        "Recovery",
        "Performance",
        "Testing",
        "Implementation TODO",
        "Integration TODO",
        "Documentation TODO",
        "Testing TODO",
    }

    if target in inline_tags:
        return True, "inline_tag"

    # Generic guide/category references
    if target in [
        "Guide",
        "Developers",
        "AI Agents",
        "Copilot",
        "Development Team",
        "TTA Team",
        "Agent Guide",
        "Documentation Standards",
        "Agent Instructions",
        "Document Type",
        "Getting Started",
        "Installation TODO",
        "Introduction TODO",
        "First Workflow TODO",
        "Basic Primitives TODO",
    ]:
        return True, "generic_reference"

    # Numbered categories (Category 1, Category 2, etc.)
    if re.match(r"^Category \d+$", target):
        return True, "category_number"

    return False, ""


async def main():
    """Analyze real broken links, filtering false positives."""
    context = WorkflowContext(workflow_id="real-link-analysis")
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

    all_broken = result["broken_links"]
    valid_links_data = result.get("valid_links", [])
    valid_count = (
        len(valid_links_data)
        if isinstance(valid_links_data, list)
        else valid_links_data
    )

    # Filter out false positives
    real_broken = []
    false_positives = defaultdict(list)

    for link in all_broken:
        is_fp, reason = is_false_positive(link["target"])
        if is_fp:
            false_positives[reason].append(link)
        else:
            real_broken.append(link)

    print("\n📊 Analysis Results:")
    print(f"  ✅ Valid links: {valid_count}")
    print(f"  ❌ Total broken links: {len(all_broken)}")
    print(f"  🗑️  False positives: {len(all_broken) - len(real_broken)}")
    print(f"  ⚠️  REAL broken links: {len(real_broken)}")

    print("\n🔍 False Positive Breakdown:")
    for reason, links in sorted(
        false_positives.items(), key=lambda x: len(x[1]), reverse=True
    ):
        print(f"  {reason}: {len(links)} links")

    # Group real broken links by source and target
    by_source = defaultdict(list)
    by_target = defaultdict(list)

    for link in real_broken:
        by_source[link["source"]].append(link["target"])
        by_target[link["target"]].append(link["source"])

    print("\n📋 Top 20 pages with REAL broken links:")
    sorted_sources = sorted(by_source.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (source, targets) in enumerate(sorted_sources[:20], 1):
        print(f"  {i}. {source}: {len(targets)} broken links")

    print("\n🎯 Top 20 REAL missing pages (high impact fixes):")
    sorted_targets = sorted(by_target.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (target, sources) in enumerate(sorted_targets[:20], 1):
        print(f"  {i}. {target} (referenced by {len(sources)} pages)")

    # Save detailed report
    report_path = Path("kb-real-broken-links.txt")
    with open(report_path, "w") as f:
        f.write("REAL Broken Links Analysis (False Positives Filtered)\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total pages: {len(pages)}\n")
        f.write(f"Total links: {len(links)}\n")
        f.write(f"Valid links: {valid_count}\n")
        f.write(f"Total broken: {len(all_broken)}\n")
        f.write(f"False positives: {len(all_broken) - len(real_broken)}\n")
        f.write(f"REAL broken links: {len(real_broken)}\n\n")

        f.write("FALSE POSITIVE BREAKDOWN\n")
        f.write("=" * 80 + "\n\n")
        for reason, links in sorted(
            false_positives.items(), key=lambda x: len(x[1]), reverse=True
        ):
            f.write(f"{reason}: {len(links)} links\n")
        f.write("\n")

        f.write("=" * 80 + "\n")
        f.write("PAGES WITH MOST REAL BROKEN LINKS (Fix Priority)\n")
        f.write("=" * 80 + "\n\n")
        for i, (source, targets) in enumerate(sorted_sources[:30], 1):
            f.write(f"{i}. {source} ({len(targets)} broken links)\n")
            unique_targets = sorted(set(targets))
            for target in unique_targets:
                count = targets.count(target)
                f.write(f"   -> {target} ({count}x)\n")
            f.write("\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("MOST COMMONLY MISSING PAGES (Create Priority)\n")
        f.write("=" * 80 + "\n\n")
        for i, (target, sources) in enumerate(sorted_targets[:30], 1):
            f.write(
                f"{i}. {target} (referenced by {len(sources)} pages - HIGH IMPACT)\n"
            )
            for source in sorted(set(sources))[:10]:  # Show first 10 unique sources
                count = sources.count(source)
                f.write(f"   <- {source} ({count}x)\n")
            if len(set(sources)) > 10:
                f.write(f"   ... and {len(set(sources)) - 10} more sources\n")
            f.write("\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("ALL REAL BROKEN LINKS (Grouped by Source)\n")
        f.write("=" * 80 + "\n\n")
        for source, targets in sorted_sources:
            f.write(f"\n{source}:\n")
            unique_targets = sorted(set(targets))
            for target in unique_targets:
                count = targets.count(target)
                suffix = f" ({count}x)" if count > 1 else ""
                f.write(f"  -> {target}{suffix}\n")

    print(f"\n✅ Detailed report saved to {report_path}")
    print("\n💡 Next Steps:")
    print("   1. Review top 20 missing pages - these have the highest impact")
    print("   2. Decide: Create missing pages or remove broken references?")
    print("   3. Focus on pages with many broken links (easier to fix in bulk)")


if __name__ == "__main__":
    asyncio.run(main())
