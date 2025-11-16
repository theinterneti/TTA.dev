#!/usr/bin/env python3
"""
Worktree initialization utilities for TTA.dev
Provides commands for managing multiple git worktrees with proper uv setup
"""

import argparse
import subprocess
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional


class WorktreeManager:
    """Manages git worktrees with uv package management"""

    def __init__(self, repo_root: Path = None):
        self.repo_root = repo_root or Path(__file__).parent.parent
        self.worktrees_file = self.repo_root / "uv.toml"

    def get_worktrees(self) -> Dict[str, Dict]:
        """Get worktree information from uv.toml"""
        try:
            with open(self.worktrees_file) as f:
                import toml
                config = toml.load(f)

            worktrees = {}
            if "tool" in config and "uv" in config["tool"] and "workspace" in config["tool"]["uv"]:
                workspace_config = config["tool"]["uv"]["workspace"]
                if "worktrees" in workspace_config:
                    worktrees = workspace_config["worktrees"]
            return worktrees
        except Exception as e:
            print(f"Error reading uv.toml: {e}")
            return {}

    def get_current_branch(self) -> str:
        """Get current git branch"""
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def initialize_worktree(self, worktree_path: Path, sync_deps: bool = True) -> None:
        """Initialize a worktree with proper uv setup"""
        print(f"Initializing worktree: {worktree_path}")

        # Change to worktree directory
        if not worktree_path.exists():
            print(f"Worktree path does not exist: {worktree_path}")
            return

        try:
            # Sync dependencies if requested
            if sync_deps:
                print("Syncing dependencies...")
                subprocess.run(
                    ["uv", "sync", "--all-extras"],
                    cwd=worktree_path,
                    check=True
                )
                print("✅ Dependencies synced successfully")

            # Install pre-commit hooks if they exist
            if (worktree_path / ".pre-commit-config.yaml").exists():
                print("Installing pre-commit hooks...")
                subprocess.run(
                    ["uv", "run", "pre-commit", "install"],
                    cwd=worktree_path,
                    check=True
                )
                print("✅ Pre-commit hooks installed")

            print(f"✅ Worktree {worktree_path.name} initialized successfully")

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to initialize worktree: {e}")
            sys.exit(1)

    def list_worktrees(self) -> None:
        """List all git worktrees with their packages"""
        try:
            # Get git worktree list
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True
            )

            worktrees = {}
            current_line = []
            for line in result.stdout.strip().split('\n'):
                if line.startswith("worktree "):
                    if current_line:
                        self._parse_worktree_info(current_line, worktrees)
                    current_line = [line]
                else:
                    current_line.append(line)
            if current_line:
                self._parse_worktree_info(current_line, worktrees)

            # Get uv worktree config
            uv_worktrees = self.get_worktrees()

            print("Git Worktrees:")
            print("-" * 60)
            for path, info in worktrees.items():
                worktree_name = Path(path).name
                branch = info.get('branch', 'unknown')
                current_branch = self.get_current_branch()
                current_marker = " ← current" if path == str(self.repo_root) else ""

                print(f"{worktree_name}: {branch}{current_marker}")

                # Show uv packages for this branch
                if branch in uv_worktrees:
                    packages = uv_worktrees[branch].get('members', [])
                    if packages:
                        print(f"  Packages: {len(packages)}")
                        for pkg in packages[:3]:  # Show first 3
                            print(f"    - {pkg}")
                        if len(packages) > 3:
                            print(f"    ... and {len(packages) - 3} more")
                    else:
                        print("  Packages: all")
                else:
                    print("  Packages: all (default)")
                print()

        except subprocess.CalledProcessError as e:
            print(f"Error listing worktrees: {e}")

    def _parse_worktree_info(self, lines: List[str], worktrees: Dict) -> None:
        """Parse git worktree porcelain output"""
        path = None
        branch = None
        for line in lines:
            if line.startswith("worktree "):
                path = line.replace("worktree ", "").strip()
            elif line.startswith("branch "):
                branch = line.replace("branch ", "").replace("refs/heads/", "").strip()
            elif line.startswith("HEAD ") and not branch:
                branch = line.replace("HEAD ", "").strip()[:8]  # Short commit hash

        if path:
            worktrees[path] = {"branch": branch or "detached"}

    def clean_cache(self, worktree_path: Optional[Path] = None) -> None:
        """Clean uv cache for specific worktree or all worktrees"""
        if worktree_path:
            cache_dir = worktree_path / ".uv_cache"
            if cache_dir.exists():
                import shutil
                print(f"Cleaning cache for {worktree_path.name}...")
                shutil.rmtree(cache_dir)
                print("✅ Cache cleaned")
            else:
                print("No cache directory found")
        else:
            print("Cleaning cache for all worktrees...")
            # This would need to be implemented to find all worktrees
            print("Global cache cleaning not yet implemented")


def main():
    parser = argparse.ArgumentParser(description="Worktree initialization utilities for TTA.dev")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a worktree")
    init_parser.add_argument("worktree", help="Path to worktree")
    init_parser.add_argument("--no-sync", action="store_true",
                           help="Skip dependency synchronization")

    # List command
    list_parser = subparsers.add_parser("list", help="List all worktrees")

    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean uv cache")
    clean_parser.add_argument("worktree", nargs="?", help="Specific worktree path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = WorktreeManager()

    if args.command == "init":
        worktree_path = Path(args.worktree)
        sync_deps = not args.no_sync
        manager.initialize_worktree(worktree_path, sync_deps)

    elif args.command == "list":
        manager.list_worktrees()

    elif args.command == "clean":
        if args.worktree:
            manager.clean_cache(Path(args.worktree))
        else:
            manager.clean_cache()


if __name__ == "__main__":
    main()
