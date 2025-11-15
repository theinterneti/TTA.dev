#!/usr/bin/env python3
"""
GitHub Actions Workflow Migration Helper

This script helps manage the migration from old workflows to consolidated workflows.
It provides utilities to:
- Archive deprecated workflows
- Monitor workflow performance
- Validate consolidated workflows are working
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


# Workflow migration mapping
DEPRECATED_WORKFLOWS = {
    "pr-validation.yml": "consolidated-pr-validation.yml",
    "pr-validation-v2.yml": "consolidated-pr-validation.yml",
    "merge-validation.yml": "consolidated-merge-gate.yml",
    "merge-validation-v2.yml": "consolidated-merge-gate.yml",
    "ci.yml": "consolidated-pr-validation.yml + consolidated-platform-compatibility.yml",
    "quality-check.yml": "consolidated-pr-validation.yml + consolidated-merge-gate.yml",
    "orchestration-pr-review.yml": "consolidated-ai-review.yml",
    "gemini-dispatch.yml": "consolidated-ai-review.yml",
    "gemini-triage.yml": "consolidated-ai-review.yml",
}

CONSOLIDATED_WORKFLOWS = [
    "consolidated-pr-validation.yml",
    "consolidated-merge-gate.yml",
    "consolidated-platform-compatibility.yml",
    "consolidated-ai-review.yml",
]


def get_workflows_dir() -> Path:
    """Get the workflows directory path."""
    return Path(__file__).parent.parent / "workflows"


def list_workflows() -> Dict[str, List[str]]:
    """List all workflows categorized by status."""
    workflows_dir = get_workflows_dir()
    
    consolidated = []
    deprecated = []
    active = []
    
    for workflow_file in workflows_dir.glob("*.yml"):
        name = workflow_file.name
        if name in CONSOLIDATED_WORKFLOWS:
            consolidated.append(name)
        elif name in DEPRECATED_WORKFLOWS:
            deprecated.append(name)
        elif not name.startswith("reusable-") and name not in ["MIGRATION_PLAN.md", "README.md"]:
            active.append(name)
    
    return {
        "consolidated": sorted(consolidated),
        "deprecated": sorted(deprecated),
        "active": sorted(active),
    }


def archive_deprecated_workflows(dry_run: bool = True) -> None:
    """Archive deprecated workflows to archive directory."""
    workflows_dir = get_workflows_dir()
    archive_dir = workflows_dir / "archive"
    
    if not dry_run:
        archive_dir.mkdir(exist_ok=True)
    
    print("📦 Archiving deprecated workflows...\n")
    
    for old_workflow, new_workflow in DEPRECATED_WORKFLOWS.items():
        old_path = workflows_dir / old_workflow
        if old_path.exists():
            archive_path = archive_dir / old_workflow
            
            if dry_run:
                print(f"  [DRY RUN] Would archive: {old_workflow}")
                print(f"            → {archive_path}")
                print(f"            Replaced by: {new_workflow}\n")
            else:
                old_path.rename(archive_path)
                print(f"  ✅ Archived: {old_workflow}")
                print(f"     → {archive_path}")
                print(f"     Replaced by: {new_workflow}\n")
    
    if dry_run:
        print("\n💡 Run with --execute to actually archive workflows")


def show_migration_status() -> None:
    """Show current migration status."""
    workflows = list_workflows()
    
    print("🔧 GitHub Actions Workflow Migration Status\n")
    print("=" * 60)
    
    print("\n✅ CONSOLIDATED WORKFLOWS:")
    for workflow in workflows["consolidated"]:
        print(f"  • {workflow}")
    
    print(f"\n⚠️  DEPRECATED WORKFLOWS ({len(workflows['deprecated'])}):")
    for workflow in workflows["deprecated"]:
        replacement = DEPRECATED_WORKFLOWS.get(workflow, "Unknown")
        print(f"  • {workflow}")
        print(f"    → {replacement}")
    
    print(f"\n🔵 ACTIVE UTILITY WORKFLOWS ({len(workflows['active'])}):")
    for workflow in workflows["active"]:
        print(f"  • {workflow}")
    
    print("\n" + "=" * 60)
    print(f"\nTotal workflows: {len(workflows['consolidated']) + len(workflows['deprecated']) + len(workflows['active'])}")
    print(f"Consolidated: {len(workflows['consolidated'])}")
    print(f"Deprecated: {len(workflows['deprecated'])}")
    print(f"Active: {len(workflows['active'])}")


def validate_consolidated_workflows() -> bool:
    """Validate that consolidated workflows exist and are valid YAML."""
    print("🔍 Validating consolidated workflows...\n")
    
    workflows_dir = get_workflows_dir()
    all_valid = True
    
    for workflow in CONSOLIDATED_WORKFLOWS:
        workflow_path = workflows_dir / workflow
        
        if not workflow_path.exists():
            print(f"  ❌ {workflow} - NOT FOUND")
            all_valid = False
            continue
        
        # Basic YAML validation (check if file can be read and parsed)
        try:
            import yaml
            with open(workflow_path) as f:
                yaml.safe_load(f)
            print(f"  ✅ {workflow} - Valid YAML")
        except ImportError:
            print(f"  ⚠️  {workflow} - YAML validation skipped (PyYAML not installed)")
        except Exception as e:
            print(f"  ❌ {workflow} - Invalid YAML: {e}")
            all_valid = False
    
    print()
    return all_valid


def check_workflow_runs(limit: int = 10) -> None:
    """Check recent workflow runs using GitHub CLI."""
    print(f"📊 Recent workflow runs (last {limit})...\n")
    
    try:
        # Check if gh CLI is installed
        result = subprocess.run(
            ["gh", "run", "list", "--limit", str(limit), "--json", 
             "name,conclusion,startedAt,durationMs"],
            capture_output=True,
            text=True,
            check=True
        )
        
        runs = json.loads(result.stdout)
        
        for run in runs:
            name = run.get("name", "Unknown")
            conclusion = run.get("conclusion", "Unknown")
            duration_ms = run.get("durationMs", 0)
            duration_min = duration_ms / 1000 / 60 if duration_ms else 0
            
            status_icon = "✅" if conclusion == "success" else "❌" if conclusion == "failure" else "⏭️"
            
            print(f"  {status_icon} {name}")
            print(f"     Status: {conclusion}, Duration: {duration_min:.1f} min\n")
    
    except FileNotFoundError:
        print("  ⚠️  GitHub CLI (gh) not installed. Install it to check workflow runs.")
        print("     https://cli.github.com/\n")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Error checking workflow runs: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Actions Workflow Migration Helper"
    )
    
    parser.add_argument(
        "command",
        choices=["status", "archive", "validate", "runs"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the command (without this, it's a dry run)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Limit for workflow runs (default: 10)"
    )
    
    args = parser.parse_args()
    
    print()
    
    if args.command == "status":
        show_migration_status()
    
    elif args.command == "archive":
        archive_deprecated_workflows(dry_run=not args.execute)
    
    elif args.command == "validate":
        valid = validate_consolidated_workflows()
        if not valid:
            print("❌ Some workflows are invalid!")
            sys.exit(1)
        else:
            print("✅ All consolidated workflows are valid!")
    
    elif args.command == "runs":
        check_workflow_runs(limit=args.limit)
    
    print()


if __name__ == "__main__":
    main()
