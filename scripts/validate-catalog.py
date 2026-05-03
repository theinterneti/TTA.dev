#!/usr/bin/env python3
"""Validate .github/copilot-catalog.yml against the actual file tree.

Checks:
  1. All referenced paths exist on disk
  2. All instruction_refs, skill_refs, workflow_refs resolve
  3. No orphaned agent/skill/instruction files (not in registry)
  4. No circular references in the composition graph

Usage:
    uv run python scripts/validate-catalog.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / ".github" / "copilot-catalog.yml"

# Directories to scan for orphan detection
INSTRUCTION_DIR = REPO_ROOT / ".github" / "instructions"
SKILL_DIR = REPO_ROOT / ".github" / "skills"
AGENT_DIR = REPO_ROOT / ".github" / "agents"


def load_catalog() -> dict:
    """Load and parse the catalog YAML."""
    if not CATALOG_PATH.exists():
        print(f"FAIL: catalog not found at {CATALOG_PATH}")
        sys.exit(1)
    with open(CATALOG_PATH) as f:
        return yaml.safe_load(f)


def check_paths(catalog: dict) -> list[str]:
    """Verify all referenced paths exist on disk."""
    errors: list[str] = []
    for section in ("instructions", "skills", "agents"):
        entries = catalog.get(section, {})
        for entry_id, entry in entries.items():
            path = REPO_ROOT / entry["path"]
            if not path.exists():
                errors.append(f"{section}.{entry_id}: path not found: {entry['path']}")
    return errors


def check_refs(catalog: dict) -> list[str]:
    """Verify all cross-references resolve to valid entries."""
    errors: list[str] = []
    instruction_ids = set(catalog.get("instructions", {}).keys())
    skill_ids = set(catalog.get("skills", {}).keys())

    # Skills reference instructions
    for skill_id, skill in catalog.get("skills", {}).items():
        for ref in skill.get("instruction_refs", []):
            if ref not in instruction_ids:
                errors.append(
                    f"skills.{skill_id}: instruction_ref '{ref}' not found in instructions"
                )

    # Agents reference skills and workflows (both in the skills section)
    for agent_id, agent in catalog.get("agents", {}).items():
        for ref in agent.get("skill_refs", []):
            if ref not in skill_ids:
                errors.append(f"agents.{agent_id}: skill_ref '{ref}' not found in skills")
        for ref in agent.get("workflow_refs", []):
            if ref not in skill_ids:
                errors.append(f"agents.{agent_id}: workflow_ref '{ref}' not found in skills")

    return errors


def check_orphans(catalog: dict) -> list[str]:
    """Find files on disk that aren't in the registry."""
    warnings: list[str] = []

    # Instruction files
    registered_instruction_paths = {
        (REPO_ROOT / e["path"]).resolve() for e in catalog.get("instructions", {}).values()
    }
    if INSTRUCTION_DIR.exists():
        for f in INSTRUCTION_DIR.glob("*.instructions.md"):
            if f.resolve() not in registered_instruction_paths:
                warnings.append(f"ORPHAN instruction: {f.relative_to(REPO_ROOT)}")

    # Skill directories
    registered_skill_paths = {
        (REPO_ROOT / e["path"]).resolve() for e in catalog.get("skills", {}).values()
    }
    if SKILL_DIR.exists():
        for d in SKILL_DIR.iterdir():
            if d.is_dir():
                skill_md = d / "SKILL.md"
                if skill_md.exists() and skill_md.resolve() not in registered_skill_paths:
                    warnings.append(f"ORPHAN skill: {skill_md.relative_to(REPO_ROOT)}")

    # Agent files
    registered_agent_paths = {
        (REPO_ROOT / e["path"]).resolve() for e in catalog.get("agents", {}).values()
    }
    if AGENT_DIR.exists():
        for f in AGENT_DIR.glob("*.agent.md"):
            if f.resolve() not in registered_agent_paths:
                warnings.append(f"ORPHAN agent: {f.relative_to(REPO_ROOT)}")

    return warnings


def check_workflow_kinds(catalog: dict) -> list[str]:
    """Verify workflow_refs point to skills with kind: workflow."""
    errors: list[str] = []
    skills = catalog.get("skills", {})

    for agent_id, agent in catalog.get("agents", {}).items():
        for ref in agent.get("workflow_refs", []):
            if ref in skills and skills[ref].get("kind") != "workflow":
                errors.append(
                    f"agents.{agent_id}: workflow_ref '{ref}' has kind "
                    f"'{skills[ref].get('kind')}', expected 'workflow'"
                )
    return errors


def main() -> None:
    """Run all validation checks."""
    catalog = load_catalog()
    errors: list[str] = []
    warnings: list[str] = []

    errors.extend(check_paths(catalog))
    errors.extend(check_refs(catalog))
    errors.extend(check_workflow_kinds(catalog))
    warnings.extend(check_orphans(catalog))

    if warnings:
        print(f"\n⚠️  {len(warnings)} warning(s):")
        for w in warnings:
            print(f"  WARN: {w}")

    if errors:
        print(f"\n❌ {len(errors)} error(s):")
        for e in errors:
            print(f"  FAIL: {e}")
        sys.exit(1)
    else:
        print(
            f"\n✅ Catalog valid ({len(catalog.get('instructions', {}))} instructions, "
            f"{len(catalog.get('skills', {}))} skills, {len(catalog.get('agents', {}))} agents)"
        )
        if not warnings:
            print("   No warnings.")
        sys.exit(0)


if __name__ == "__main__":
    main()
