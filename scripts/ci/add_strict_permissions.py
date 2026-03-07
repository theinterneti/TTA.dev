#!/usr/bin/env python3
"""Add strict permissions blocks to all GitHub Actions workflows."""

import re
from pathlib import Path
from typing import Any

import yaml


def add_strict_permissions(workflow_path: Path) -> bool:
    """Add strict permissions block to a workflow file.
    
    Args:
        workflow_path: Path to the workflow YAML file
        
    Returns:
        True if file was modified, False otherwise
    """
    content = workflow_path.read_text()
    
    # Skip if already has top-level permissions
    if re.search(r'^permissions:\s*$', content, re.MULTILINE):
        print(f"  ✓ {workflow_path.name} already has permissions")
        return False
    
    # Parse YAML to understand structure
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"  ⚠️  {workflow_path.name} - YAML parse error: {e}")
        return False
    
    # Determine if any jobs need write permissions
    needs_write = False
    write_scopes: set[str] = set()
    
    if isinstance(data, dict) and 'jobs' in data:
        for job_name, job_config in data['jobs'].items():
            if isinstance(job_config, dict):
                job_perms = job_config.get('permissions', {})
                if isinstance(job_perms, dict):
                    for scope, level in job_perms.items():
                        if level == 'write':
                            needs_write = True
                            write_scopes.add(scope)
    
    # Add appropriate top-level permissions
    if needs_write:
        # Keep job-level write permissions, but add read-only top-level default
        perm_block = "permissions:\n  contents: read\n\n"
        print(f"  ✏️  {workflow_path.name} - adding read-only default (jobs have write)")
    else:
        # Add strict read-only permissions
        perm_block = "permissions:\n  contents: read\n\n"
        print(f"  ✏️  {workflow_path.name} - adding strict read-only")
    
    # Insert after name/on but before jobs
    lines = content.split('\n')
    insert_idx = 0
    
    # Find where to insert (after 'on:' block)
    in_on_block = False
    for i, line in enumerate(lines):
        if line.startswith('on:'):
            in_on_block = True
        elif in_on_block and line and not line.startswith(' ') and not line.startswith('\t'):
            insert_idx = i
            break
    
    if insert_idx > 0:
        lines.insert(insert_idx, perm_block.rstrip())
        new_content = '\n'.join(lines)
        workflow_path.write_text(new_content)
        return True
    
    print(f"  ⚠️  {workflow_path.name} - couldn't find insertion point")
    return False


def main() -> None:
    """Process all workflow files."""
    workflows_dir = Path('.github/workflows')
    
    print("🔒 Adding Strict Permissions to GitHub Actions Workflows")
    print("=" * 60)
    
    workflow_files = list(workflows_dir.glob('*.yml')) + list(workflows_dir.glob('*.yaml'))
    workflow_files = [f for f in workflow_files if not f.is_relative_to(workflows_dir / '_archive')]
    
    modified_count = 0
    
    for workflow_path in sorted(workflow_files):
        if add_strict_permissions(workflow_path):
            modified_count += 1
    
    print()
    print(f"✅ Modified {modified_count}/{len(workflow_files)} workflows")
    print()
    print("🎯 Next steps:")
    print("  1. Review changes: git diff .github/workflows/")
    print("  2. Run: ./scripts/pin_workflow_actions.sh")
    print("  3. Test workflows locally if possible")
    print("  4. Commit and push")


if __name__ == '__main__':
    main()
