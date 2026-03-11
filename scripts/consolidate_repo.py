#!/usr/bin/env python3
"""Repository consolidation migration script.

Consolidates scattered code directories into clean monorepo structure:
- platform/ → packages/tta-*/
- src/ → packages/tta-core/
- platform_tta_dev/ → apps/platform/
"""

import argparse
import shutil
from pathlib import Path


def migrate_platform_packages(repo_root: Path, dry_run: bool = True) -> None:
    """Migrate platform/* to packages/tta-*/ structure."""
    platform_dir = repo_root / "platform"
    packages_dir = repo_root / "packages"

    migrations = [
        (platform_dir / "primitives", packages_dir / "tta-primitives"),
        (platform_dir / "observability", packages_dir / "tta-observability"),
        (platform_dir / "secrets", packages_dir / "tta-secrets"),
        (platform_dir / "tools", packages_dir / "tta-tools"),
    ]

    for src, dst in migrations:
        if src.exists():
            print(f"{'[DRY-RUN] ' if dry_run else ''}Move: {src} → {dst}")
            if not dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))


def migrate_src_to_core(repo_root: Path, dry_run: bool = True) -> None:
    """Migrate src/ to packages/tta-core/."""
    src_dir = repo_root / "src"
    core_dir = repo_root / "packages" / "tta-core"

    if src_dir.exists():
        print(f"{'[DRY-RUN] ' if dry_run else ''}Move: {src_dir} → {core_dir}")
        if not dry_run:
            core_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_dir), str(core_dir))


def migrate_platform_tta_dev(repo_root: Path, dry_run: bool = True) -> None:
    """Migrate platform_tta_dev/ to apps/platform/."""
    old_app = repo_root / "platform_tta_dev"
    new_app = repo_root / "apps" / "platform"

    if old_app.exists():
        print(f"{'[DRY-RUN] ' if dry_run else ''}Move: {old_app} → {new_app}")
        if not dry_run:
            new_app.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_app), str(new_app))


def update_pyproject_paths(repo_root: Path, dry_run: bool = True) -> None:
    """Update pyproject.toml package references."""
    pyproject = repo_root / "pyproject.toml"

    if not pyproject.exists():
        return

    content = pyproject.read_text()

    # Update package paths
    replacements = [
        ('packages = ["platform/primitives/src"]', 'packages = ["packages/tta-primitives/src"]'),
        (
            'packages = ["platform/observability/src"]',
            'packages = ["packages/tta-observability/src"]',
        ),
        ('packages = ["platform/secrets/src"]', 'packages = ["packages/tta-secrets/src"]'),
        ('packages = ["src"]', 'packages = ["packages/tta-core/src"]'),
    ]

    updated = content
    for old, new in replacements:
        if old in updated:
            print(f"{'[DRY-RUN] ' if dry_run else ''}Update pyproject.toml: {old} → {new}")
            if not dry_run:
                updated = updated.replace(old, new)

    if not dry_run and updated != content:
        pyproject.write_text(updated)


def main():
    parser = argparse.ArgumentParser(description="Consolidate TTA.dev repository structure")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--execute", action="store_true", help="Actually perform migration")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    dry_run = not args.execute

    if dry_run:
        print("=== DRY RUN MODE - No changes will be made ===\n")
    else:
        print("=== EXECUTING MIGRATION ===\n")

    print("Phase 1: Migrate platform packages")
    migrate_platform_packages(repo_root, dry_run)

    print("\nPhase 2: Migrate src/ to tta-core")
    migrate_src_to_core(repo_root, dry_run)

    print("\nPhase 3: Migrate platform_tta_dev app")
    migrate_platform_tta_dev(repo_root, dry_run)

    print("\nPhase 4: Update pyproject.toml paths")
    update_pyproject_paths(repo_root, dry_run)

    if dry_run:
        print("\n✓ Dry run complete. Use --execute to perform migration.")
    else:
        print("\n✓ Migration complete!")


if __name__ == "__main__":
    main()
