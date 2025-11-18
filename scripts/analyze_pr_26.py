#!/usr/bin/env python3
"""
Analyze PR #26 to identify valuable pieces vs obsolete content.

This script compares PR #26 file changes against the current workspace
to determine what's already implemented, what's new, and what's obsolete.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# PR #26 files from GitHub API (first 100)
PR_26_FILES = [
    (".augment/rules/package-source.instructions.md", 51, "modified"),
    (".augment/rules/scripts.instructions.md", 31, "modified"),
    (".augment/rules/tests.instructions.md", 73, "modified"),
    (".github/benchmarks/baseline.json", 81, "added"),
    (".github/prometheus/prometheus.yml", 9, "added"),
    (".github/workflows/api-testing.yml", 131, "added"),
    (".github/workflows/ci.yml", 97, "modified"),
    (".github/workflows/quality-check.yml", 128, "modified"),
    (".universal-instructions/memory-management/README.md", 308, "added"),
    (".universal-instructions/memory-management/context-engineering.md", 441, "added"),
    ("packages/python-pathway/instructions/UV_WORKFLOW_FOUNDATION.md", 590, "added"),
    ("packages/python-pathway/instructions/quality.md", 34, "added"),
    ("packages/python-pathway/instructions/testing.md", 68, "added"),
    ("packages/python-pathway/instructions/tooling.md", 41, "added"),
    ("packages/tta-dev-primitives/dashboards/alertmanager/README.md", 355, "added"),
    ("packages/tta-dev-primitives/dashboards/alertmanager/alertmanager.yaml", 223, "added"),
    ("packages/tta-dev-primitives/dashboards/alertmanager/tta-alerts.yaml", 226, "added"),
    ("packages/tta-dev-primitives/dashboards/grafana/README.md", 281, "added"),
    ("packages/tta-dev-primitives/dashboards/grafana/cost-tracking.json", 413, "added"),
    ("packages/tta-dev-primitives/dashboards/grafana/slo-tracking.json", 0, "added"),
    ("packages/tta-dev-primitives/dashboards/grafana/workflow-overview.json", 0, "added"),
    ("packages/tta-dev-primitives/src/tta_dev_primitives/memory_workflow.py", 0, "added"),
    ("packages/tta-dev-primitives/src/tta_dev_primitives/paf_memory.py", 0, "added"),
    ("packages/tta-dev-primitives/src/tta_dev_primitives/session_group.py", 0, "added"),
    ("packages/tta-dev-primitives/src/tta_dev_primitives/workflow_hub.py", 0, "added"),
    ("packages/tta-dev-primitives/src/tta_dev_primitives/observability/enhanced_metrics.py", 0, "added"),
    ("packages/tta-dev-primitives/src/tta_dev_primitives/observability/instrumented_primitive.py", 0, "added"),
    ("packages/tta-dev-primitives/src/tta_dev_primitives/observability/prometheus_exporter.py", 0, "added"),
    ("packages/tta-dev-primitives/src/tta_dev_primitives/observability/context_propagation.py", 0, "added"),
    ("packages/tta-dev-primitives/src/tta_dev_primitives/observability/enhanced_collector.py", 0, "added"),
    ("packages/tta-dev-primitives/tests/observability/test_context_propagation.py", 0, "added"),
    ("packages/tta-dev-primitives/tests/observability/test_enhanced_metrics.py", 0, "added"),
    ("packages/tta-dev-primitives/tests/observability/test_instrumented_primitives.py", 0, "added"),
]

# Categories for classification
CATEGORIES = {
    "infrastructure": ["docker-compose", "workflows", "prometheus"],
    "observability": ["dashboards", "alertmanager", "grafana", "metrics", "instrumented"],
    "memory": ["memory_workflow", "paf_memory", "session_group", "memory-management"],
    "testing": ["test_", "tests/", "api-testing"],
    "docs": ["README.md", "instructions", ".md"],
    "config": ["baseline.json", ".yaml", ".yml", "quality.md", "tooling.md"],
}


def categorize_file(filepath: str) -> str:
    """Categorize a file based on its path/name."""
    for category, patterns in CATEGORIES.items():
        if any(pattern in filepath for pattern in patterns):
            return category
    return "other"


def check_file_exists(filepath: str) -> Tuple[bool, Path | None]:
    """Check if file exists in current workspace."""
    path = Path("/home/thein/repos/TTA.dev") / filepath
    return path.exists(), path if path.exists() else None


def get_file_size(path: Path | None) -> int:
    """Get file size in lines."""
    if not path or not path.exists():
        return 0
    try:
        return len(path.read_text().splitlines())
    except Exception:
        return 0


def analyze_pr_files() -> Dict:
    """Analyze all PR #26 files."""
    results = {
        "already_exists": [],
        "new_files": [],
        "modified_files": [],
        "by_category": {},
    }

    for filepath, additions, status in PR_26_FILES:
        exists, current_path = check_file_exists(filepath)
        category = categorize_file(filepath)

        if category not in results["by_category"]:
            results["by_category"][category] = {
                "already_exists": [],
                "new_files": [],
                "modified_files": [],
            }

        file_info = {
            "path": filepath,
            "pr_additions": additions,
            "status_in_pr": status,
            "category": category,
        }

        if exists:
            current_size = get_file_size(current_path)
            file_info["current_size"] = current_size
            file_info["size_diff"] = additions - current_size if status == "added" else additions

            if status == "added":
                # File added in PR but already exists = already implemented
                results["already_exists"].append(file_info)
                results["by_category"][category]["already_exists"].append(file_info)
            else:
                # Modified in PR and exists = needs comparison
                results["modified_files"].append(file_info)
                results["by_category"][category]["modified_files"].append(file_info)
        else:
            # File doesn't exist = genuinely new
            results["new_files"].append(file_info)
            results["by_category"][category]["new_files"].append(file_info)

    return results


def print_summary(results: Dict):
    """Print analysis summary."""
    print("\n" + "=" * 80)
    print("PR #26 ANALYSIS SUMMARY")
    print("=" * 80)

    print(f"\n📊 OVERALL STATUS:")
    print(f"  ✅ Already Implemented: {len(results['already_exists'])} files")
    print(f"  🆕 New Files: {len(results['new_files'])} files")
    print(f"  ⚠️  Modified Files: {len(results['modified_files'])} files")

    print(f"\n📁 BY CATEGORY:")
    for category, files in results["by_category"].items():
        total = (
            len(files["already_exists"])
            + len(files["new_files"])
            + len(files["modified_files"])
        )
        print(f"\n  {category.upper()} ({total} files):")
        print(f"    ✅ Already exists: {len(files['already_exists'])}")
        print(f"    🆕 New: {len(files['new_files'])}")
        print(f"    ⚠️  Modified: {len(files['modified_files'])}")

    print("\n" + "=" * 80)
    print("DETAILED BREAKDOWN")
    print("=" * 80)

    # Already implemented
    if results["already_exists"]:
        print("\n✅ ALREADY IMPLEMENTED (can likely close):")
        for file in results["already_exists"]:
            print(f"  {file['path']}")
            print(f"    PR: +{file['pr_additions']} lines, Current: {file['current_size']} lines")

    # New files by category
    print("\n🆕 NEW FILES (extract to focused PRs):")
    for category in results["by_category"]:
        cat_new = results["by_category"][category]["new_files"]
        if cat_new:
            print(f"\n  {category.upper()}:")
            for file in cat_new:
                print(f"    {file['path']} (+{file['pr_additions']} lines)")

    # Modified files
    if results["modified_files"]:
        print("\n⚠️  MODIFIED FILES (needs manual review):")
        for file in results["modified_files"]:
            print(f"  {file['path']}")
            print(f"    PR changes: +{file['pr_additions']} lines, Current: {file['current_size']} lines")


def generate_recommendations(results: Dict):
    """Generate action recommendations."""
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    # Calculate savings
    already_impl_lines = sum(f["pr_additions"] for f in results["already_exists"])
    new_files_lines = sum(f["pr_additions"] for f in results["new_files"])
    modified_lines = sum(f["pr_additions"] for f in results["modified_files"])

    total_lines = already_impl_lines + new_files_lines + modified_lines
    obsolete_percent = (already_impl_lines / total_lines * 100) if total_lines > 0 else 0

    print(f"\n📈 IMPACT ANALYSIS:")
    print(f"  Total PR size: {total_lines:,} lines")
    print(f"  Already implemented: {already_impl_lines:,} lines ({obsolete_percent:.1f}%)")
    print(f"  Genuinely new: {new_files_lines:,} lines")
    print(f"  Needs review: {modified_lines:,} lines")

    print(f"\n🎯 RECOMMENDED ACTIONS:")

    # Action 1: Close obsolete parts
    if results["already_exists"]:
        print(f"\n  1. DISCARD ({len(results['already_exists'])} files, {already_impl_lines:,} lines):")
        print(f"     These are already implemented in current main.")
        for file in results["already_exists"][:5]:  # Show first 5
            print(f"     - {file['path']}")
        if len(results["already_exists"]) > 5:
            print(f"     ... and {len(results['already_exists']) - 5} more")

    # Action 2: Extract valuable new content
    print(f"\n  2. EXTRACT TO NEW PRs ({len(results['new_files'])} files, {new_files_lines:,} lines):")

    # Group by category for extraction
    for category, files in results["by_category"].items():
        if files["new_files"]:
            cat_lines = sum(f["pr_additions"] for f in files["new_files"])
            print(f"\n     PR: {category.upper()} enhancements ({cat_lines:,} lines)")
            for file in files["new_files"][:3]:  # Show first 3
                print(f"     - {file['path']}")
            if len(files["new_files"]) > 3:
                print(f"     ... and {len(files['new_files']) - 3} more")

    # Action 3: Manual review needed
    if results["modified_files"]:
        print(f"\n  3. MANUAL REVIEW ({len(results['modified_files'])} files):")
        print(f"     These files exist but were modified in PR. Need diff comparison:")
        for file in results["modified_files"][:5]:
            print(f"     - {file['path']}")

    print(f"\n💡 NEXT STEPS:")
    print(f"  1. Close PR #26 (too broad, most content obsolete/already implemented)")
    print(f"  2. Create {len([c for c in results['by_category'] if results['by_category'][c]['new_files']])} focused PRs from new content:")
    for category in results["by_category"]:
        if results["by_category"][category]["new_files"]:
            print(f"     - {category.upper()} enhancements")
    print(f"  3. Review {len(results['modified_files'])} modified files manually")
    print(f"  4. Update project board with new focused PRs")


def main():
    """Main analysis function."""
    print("Analyzing PR #26: feature/keploy-framework")
    print(f"Comparing {len(PR_26_FILES)} files against current workspace...")

    results = analyze_pr_files()
    print_summary(results)
    generate_recommendations(results)

    # Save results
    output_file = Path("/home/thein/repos/TTA.dev/pr_26_analysis.json")
    output_file.write_text(json.dumps(results, indent=2))
    print(f"\n✅ Full analysis saved to: {output_file}")


if __name__ == "__main__":
    main()
