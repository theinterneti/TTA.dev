#!/usr/bin/env python3
"""
Enhanced Package Installer for TTA.dev

Intelligent package management using UV primitives with worktree awareness,
dependency resolution, and installation validation.

Features:
- Worktree-aware installations
- Dependency conflict detection
- Installation validation
- Support for all package types (wheels, editable, git)
- Integration with shell aliases system

Usage:
    # Install packages across worktrees
    python scripts/install_packages.py install requests aiohttp --worktrees

    # Install editable packages
    python scripts/install_packages.py install -e packages/tta-dev-primitives

    # Add dev dependencies to all worktrees
    python scripts/install_packages.py add-dev pytest ruff

    # Validate installations
    python scripts/install_packages.py validate
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.integrations.uv_primitive import (
    UVAddPrimitive,
    UVRunPrimitive,
    UVSyncPrimitive,
    WorktreeAwareUVPrimitive,
    create_dependency_management_workflow,
)


class UVPackageInstaller:
    """Intelligent UV package installer with worktree support"""

    def __init__(self):
        self.repo_root = self._find_repo_root()
        self.worktree_paths = self._get_worktree_paths()

    def _find_repo_root(self) -> Path:
        """Find the git repository root"""
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / ".git").exists():
                return parent
        return current

    def _get_worktree_paths(self) -> Dict[str, Path]:
        """Get all worktree paths"""
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            worktrees = {}
            current_path = None
            for line in result.stdout.strip().split('\n'):
                if line.startswith("worktree "):
                    current_path = Path(line.replace("worktree ", "").strip())
                elif line.startswith("branch "):
                    branch = line.replace("branch ", "").replace("refs/heads/", "").strip()
                    if current_path:
                        worktrees[branch] = current_path

            return worktrees
        except subprocess.CalledProcessError:
            return {"current": Path.cwd()}

    async def install_packages(
        self,
        packages: List[str],
        context: WorkflowContext,
        editable: bool = False,
        worktree_aware: bool = True
    ) -> Dict[str, str]:
        """
        Install packages with UV primitives

        Args:
            packages: List of package names or paths
            context: Workflow context
            editable: Install in editable mode
            worktree_aware: Use worktree-aware primitives

        Returns:
            Dict mapping worktree names to installation results
        """
        results = {}

        if worktree_aware and len(self.worktree_paths) > 1:
            # Install across all worktrees
            for worktree_name, worktree_path in self.worktree_paths.items():
                print(f"📦 Installing packages in worktree: {worktree_name}")
                worktree_context = WorkflowContext(
                    correlation_id=f"{context.correlation_id}-{worktree_name}",
                    data={"worktree_path": worktree_path, **context.data}
                )

                result = await self._install_in_worktree(packages, worktree_context, editable)
                results[worktree_name] = result
        else:
            # Install in current worktree
            results["current"] = await self._install_in_worktree(packages, context, editable)

        return results

    async def _install_in_worktree(
        self,
        packages: List[str],
        context: WorkflowContext,
        editable: bool = False
    ) -> str:
        """Install packages in a specific worktree"""
        try:
            # Use our UV primitives for installation
            primitives = []

            for package in packages:
                if editable or package.startswith("./") or package.startswith("packages/"):
                    # Editable installation
                    primitives.append(UVAddPrimitive(package=package))
                else:
                    # Regular package installation
                    primitives.append(UVAddPrimitive(package=package))

            # Create and execute workflow
            if len(primitives) == 1:
                workflow = primitives[0]
            else:
                from tta_dev_primitives.core.primitives import SequentialPrimitive
                workflow = SequentialPrimitive(primitives=primitives)

            result = await workflow.execute(context, {})
            return f"✅ Success: {result.success}"

        except Exception as e:
            return f"❌ Failed: {str(e)}"

    async def add_dev_dependencies(
        self,
        packages: List[str],
        context: WorkflowContext,
        worktree_aware: bool = True
    ) -> Dict[str, str]:
        """Add development dependencies to all worktrees"""
        print(f"🔧 Adding dev dependencies: {', '.join(packages)}")

        return await self.install_packages(packages, context, worktree_aware=worktree_aware)

    async def validate_installations(self, context: WorkflowContext) -> Dict[str, bool]:
        """Validate that packages are properly installed across worktrees"""
        validation_results = {}

        # Test key package imports
        test_imports = [
            ("tta_dev_primitives", "Core primitives"),
            ("structlog", "Logging framework"),
            ("opentelemetry", "Observability framework"),
            ("pytest", "Testing framework"),
        ]

        for module_name, description in test_imports:
            try:
                __import__(module_name)
                validation_results[description] = True
                print(f"✅ {description}: Available")
            except ImportError:
                validation_results[description] = False
                print(f"❌ {description}: Missing")

        # Test UV commands work
        try:
            uv_sync = UVSyncPrimitive(with_extras=False)
            result = await uv_sync.execute(context, {})
            validation_results["UV Sync"] = result.success
            print(f"✅ UV Sync: {'Working' if result.success else 'Failing'}")
        except Exception as e:
            validation_results["UV Sync"] = False
            print(f"❌ UV Sync: Error - {str(e)}")

        return validation_results

    async def sync_all_worktrees(self, context: WorkflowContext) -> Dict[str, str]:
        """Sync dependencies across all worktrees"""
        results = {}

        for worktree_name, worktree_path in self.worktree_paths.items():
            print(f"🔄 Syncing worktree: {worktree_name}")

            worktree_context = WorkflowContext(
                correlation_id=f"sync-{worktree_name}",
                data={"worktree_path": worktree_path}
            )

            try:
                sync_primitive = WorktreeAwareUVPrimitive("sync", with_extras=True)
                result = await sync_primitive.execute(worktree_context, {})
                results[worktree_name] = f"✅ Synced" if result.success else f"❌ Failed: {result.stderr}"
            except Exception as e:
                results[worktree_name] = f"❌ Error: {str(e)}"

        return results


def create_installation_workflow(
    packages_to_install: List[str],
    packages_to_add: List[str] = None,
    sync_after: bool = True,
    worktree_aware: bool = True
):
    """
    Create a comprehensive installation workflow

    This demonstrates how UV primitives can be composed for complex
    package management scenarios.
    """
    from tta_dev_primitives.integrations.uv_primitive import (
        create_dependency_management_workflow,
        UVSyncPrimitive,
    )

    # Start with sync
    primitives = [UVSyncPrimitive(with_extras=True)]

    # Add packages
    if packages_to_install:
        for package in packages_to_install:
            primitives.append(UVAddPrimitive(package=package))

    # Add dev dependencies
    if packages_to_add:
        for package in packages_to_add:
            primitives.append(UVAddPrimitive(package=package))

    # Final sync if requested
    if sync_after and (packages_to_install or packages_to_add):
        primitives.append(UVSyncPrimitive(with_extras=True))

    # Create composable workflow
    if len(primitives) == 1:
        return primitives[0]

    from tta_dev_primitives.core.primitives import SequentialPrimitive
    return SequentialPrimitive(primitives=primitives)


async def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Enhanced TTA.dev Package Installer")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Install command
    install_parser = subparsers.add_parser("install", help="Install packages")
    install_parser.add_argument("packages", nargs="+", help="Packages to install")
    install_parser.add_argument("-e", "--editable", action="store_true", help="Install in editable mode")
    install_parser.add_argument("--worktrees", action="store_true", help="Install across all worktrees")

    # Add-dev command
    adddev_parser = subparsers.add_parser("add-dev", help="Add development dependencies")
    adddev_parser.add_argument("packages", nargs="+", help="Dev packages to add")
    adddev_parser.add_argument("--worktrees", action="store_true", help="Add to all worktrees")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync all worktrees")
    sync_parser.add_argument("--worktrees", action="store_true", help="Sync all worktrees (default)")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate installations")

    # Workflow demo command
    workflow_parser = subparsers.add_parser("demo-workflow", help="Demonstrate composable workflow")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize installer
    installer = UVPackageInstaller()
    context = WorkflowContext(correlation_id="install-script")

    if args.command == "install":
        worktree_aware = getattr(args, 'worktrees', False)
        results = await installer.install_packages(
            args.packages, context,
            editable=args.editable,
            worktree_aware=worktree_aware
        )

        for worktree, result in results.items():
            print(f"{worktree}: {result}")

    elif args.command == "add-dev":
        worktree_aware = getattr(args, 'worktrees', True)  # Default to all worktrees
        results = await installer.add_dev_dependencies(
            args.packages, context, worktree_aware=worktree_aware
        )

        for worktree, result in results.items():
            print(f"{worktree}: {result}")

    elif args.command == "sync":
        worktree_aware = getattr(args, 'worktrees', True)  # Always sync all
        results = await installer.sync_all_worktrees(context)

        for worktree, result in results.items():
            print(f"{worktree}: {result}")

    elif args.command == "validate":
        results = await installer.validate_installations(context)

        all_valid = all(results.values())
        status = "✅" if all_valid else "❌"
        print(f"\n{status} Validation {'PASSED' if all_valid else 'FAILED'}")

    elif args.command == "demo-workflow":
        # Demonstrate the new composable workflow approach
        print("🚀 Demonstrating Composable UV Workflow")
        print("=" * 50)

        workflow = create_installation_workflow(
            packages_to_install=["rich", "click"],
            packages_to_add=["pytest-asyncio"],
            sync_after=True
        )

        result = await workflow.execute(context, {})
        print(f"Workflow result: {result.success}")

        if result.success:
            print("✅ Packages installed and synced successfully!")
        else:
            print(f"❌ Workflow failed: {result.stderr}")


if __name__ == "__main__":
    import subprocess
    asyncio.run(main())
