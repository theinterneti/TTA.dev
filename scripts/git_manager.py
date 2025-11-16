#!/usr/bin/env python3
"""
Git Repository Manager - Intelligent git state management for TTA.dev

Manages:
- Stashes (review, apply, drop)
- Untracked files (stage, ignore, or remove)
- Branch cleanup (merged, stale, experimental)
- Sync with remote
"""

import subprocess
import sys
from datetime import datetime
from typing import Any
from pathlib import Path


class GitManager:
    """Intelligent git repository manager."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)

    def run_git(self, *args: str) -> tuple[int, str, str]:
        """Run git command and return (returncode, stdout, stderr)."""
        result = subprocess.run(
            ["git"] + list(args),
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr

    def get_status(self) -> dict[str, Any]:
        """Get comprehensive repository status."""
        status = {}
        
        # Current branch
        _, branch, _ = self.run_git("rev-parse", "--abbrev-ref", "HEAD")
        status["current_branch"] = branch.strip()
        
        # Untracked files
        _, untracked, _ = self.run_git("ls-files", "--others", "--exclude-standard")
        status["untracked"] = [f.strip() for f in untracked.split("\n") if f.strip()]
        
        # Modified files
        _, modified, _ = self.run_git("diff", "--name-only")
        status["modified"] = [f.strip() for f in modified.split("\n") if f.strip()]
        
        # Staged files
        _, staged, _ = self.run_git("diff", "--cached", "--name-only")
        status["staged"] = [f.strip() for f in staged.split("\n") if f.strip()]
        
        # Stashes
        _, stashes, _ = self.run_git("stash", "list")
        status["stashes"] = [s.strip() for s in stashes.split("\n") if s.strip()]
        
        # Behind/ahead of remote
        _, tracking, _ = self.run_git("rev-list", "--left-right", "--count", "HEAD...@{u}")
        if tracking.strip():
            ahead, behind = tracking.strip().split("\t")
            status["ahead"] = int(ahead)
            status["behind"] = int(behind)
        else:
            status["ahead"] = 0
            status["behind"] = 0
        
        return status

    def get_branches(self, include_remote: bool = False) -> list[str]:
        """Get list of branches."""
        args = ["branch", "--format=%(refname:short)"]
        if include_remote:
            args.append("-a")
        
        _, output, _ = self.run_git(*args)
        return [b.strip() for b in output.split("\n") if b.strip()]

    def get_merged_branches(self, target: str = "main") -> list[str]:
        """Get branches that have been merged into target."""
        _, output, _ = self.run_git("branch", "--merged", target, "--format=%(refname:short)")
        branches = [b.strip() for b in output.split("\n") if b.strip()]
        # Exclude main, current branch, and protected branches
        protected = {target, "main", "develop", "master"}
        _, current, _ = self.run_git("rev-parse", "--abbrev-ref", "HEAD")
        protected.add(current.strip())
        
        return [b for b in branches if b not in protected]

    def analyze_stashes(self) -> list[dict[str, str]]:
        """Analyze stashes with detailed info."""
        stashes = []
        _, stash_list, _ = self.run_git("stash", "list")
        
        for line in stash_list.split("\n"):
            if not line.strip():
                continue
            
            # Parse stash ref (stash@{0})
            ref = line.split(":")[0].strip()
            
            # Get stash details
            _, info, _ = self.run_git("stash", "show", ref, "--stat")
            _, date_str, _ = self.run_git("show", "-s", "--format=%ci", ref)
            
            stashes.append({
                "ref": ref,
                "message": line.split(":", 1)[1].strip() if ":" in line else "",
                "date": date_str.strip(),
                "stats": info.strip(),
            })
        
        return stashes

    def clean_experimental_branches(self, dry_run: bool = True) -> list[str]:
        """Clean experimental branches (copilot/sub-pr-*, etc)."""
        experimental_patterns = [
            "copilot/sub-pr-",
            "experiment/",
            "test/",
        ]
        
        all_branches = self.get_branches()
        to_delete = []
        
        for branch in all_branches:
            for pattern in experimental_patterns:
                if pattern in branch:
                    to_delete.append(branch)
                    break
        
        if not dry_run:
            for branch in to_delete:
                self.run_git("branch", "-D", branch)
        
        return to_delete

    def sync_with_remote(self, remote: str = "TTA.dev") -> bool:
        """Sync current branch with remote."""
        code, _, err = self.run_git("fetch", remote)
        if code != 0:
            print(f"❌ Failed to fetch from {remote}: {err}")
            return False
        
        code, _, err = self.run_git("pull", remote)
        if code != 0:
            print(f"❌ Failed to pull from {remote}: {err}")
            return False
        
        return True

    def display_status_dashboard(self):
        """Display comprehensive status dashboard."""
        status = self.get_status()
        
        print("\n" + "=" * 70)
        print("🎯 TTA.dev Git Repository Status")
        print("=" * 70)
        
        print(f"\n📍 Current Branch: {status['current_branch']}")
        
        if status['behind'] > 0:
            print(f"⚠️  Behind remote by {status['behind']} commit(s)")
        if status['ahead'] > 0:
            print(f"📤 Ahead of remote by {status['ahead']} commit(s)")
        
        print(f"\n📝 Working Directory:")
        print(f"   - Untracked: {len(status['untracked'])} file(s)")
        print(f"   - Modified:  {len(status['modified'])} file(s)")
        print(f"   - Staged:    {len(status['staged'])} file(s)")
        print(f"   - Stashes:   {len(status['stashes'])} stash(es)")
        
        if status['untracked']:
            print(f"\n📄 Untracked Files:")
            for f in status['untracked'][:5]:
                print(f"   - {f}")
            if len(status['untracked']) > 5:
                print(f"   ... and {len(status['untracked']) - 5} more")
        
        if status['stashes']:
            print(f"\n💾 Stashes:")
            stashes = self.analyze_stashes()
            for stash in stashes[:3]:
                print(f"   {stash['ref']}: {stash['message']}")
                print(f"      Date: {stash['date']}")
            if len(stashes) > 3:
                print(f"   ... and {len(stashes) - 3} more")
        
        # Branch analysis
        all_branches = self.get_branches()
        merged_branches = self.get_merged_branches()
        experimental = self.clean_experimental_branches(dry_run=True)
        
        print(f"\n🌿 Branches:")
        print(f"   - Total local: {len(all_branches)}")
        print(f"   - Merged:      {len(merged_branches)}")
        print(f"   - Experimental:{len(experimental)}")
        
        print("\n" + "=" * 70)

    def interactive_cleanup(self):
        """Interactive cleanup wizard."""
        print("\n🧹 Git Repository Cleanup Wizard")
        print("=" * 70)
        
        status = self.get_status()
        
        # Handle untracked files
        if status['untracked']:
            print(f"\n📄 Found {len(status['untracked'])} untracked file(s)")
            response = input("Would you like to review them? (y/n): ").lower()
            
            if response == 'y':
                for f in status['untracked']:
                    print(f"\n📄 {f}")
                    action = input("Action? (a)dd, (i)gnore, (d)elete, (s)kip: ").lower()
                    
                    if action == 'a':
                        self.run_git("add", f)
                        print(f"✅ Added {f}")
                    elif action == 'i':
                        # Add to .gitignore
                        with open(self.repo_path / ".gitignore", "a") as gitignore:
                            gitignore.write(f"\n{f}\n")
                        print(f"✅ Added to .gitignore")
                    elif action == 'd':
                        (self.repo_path / f).unlink()
                        print(f"✅ Deleted {f}")
        
        # Handle stashes
        if status['stashes']:
            print(f"\n💾 Found {len(status['stashes'])} stash(es)")
            stashes = self.analyze_stashes()
            
            for stash in stashes:
                print(f"\n{stash['ref']}: {stash['message']}")
                print(f"Date: {stash['date']}")
                print(stash['stats'][:200])
                
                action = input("Action? (a)pply, (d)rop, (k)eep: ").lower()
                
                if action == 'a':
                    code, _, err = self.run_git("stash", "apply", stash['ref'])
                    if code == 0:
                        print(f"✅ Applied {stash['ref']}")
                    else:
                        print(f"❌ Error: {err}")
                elif action == 'd':
                    self.run_git("stash", "drop", stash['ref'])
                    print(f"✅ Dropped {stash['ref']}")
        
        # Handle branches
        merged = self.get_merged_branches()
        if merged:
            print(f"\n🌿 Found {len(merged)} merged branch(es)")
            response = input("Delete all merged branches? (y/n): ").lower()
            
            if response == 'y':
                for branch in merged:
                    self.run_git("branch", "-d", branch)
                    print(f"✅ Deleted {branch}")
        
        experimental = self.clean_experimental_branches(dry_run=True)
        if experimental:
            print(f"\n🧪 Found {len(experimental)} experimental branch(es)")
            print("Examples:", experimental[:5])
            response = input("Delete all experimental branches? (y/n): ").lower()
            
            if response == 'y':
                self.clean_experimental_branches(dry_run=False)
                print(f"✅ Deleted {len(experimental)} branches")
        
        # Sync with remote
        if status['behind'] > 0:
            print(f"\n⚠️  Your branch is {status['behind']} commit(s) behind remote")
            response = input("Pull latest changes? (y/n): ").lower()
            
            if response == 'y':
                if self.sync_with_remote():
                    print("✅ Synced with remote")

    def create_backup_branch(self) -> str:
        """Create a backup branch of current state."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup/{timestamp}"
        
        self.run_git("branch", backup_name)
        print(f"✅ Created backup branch: {backup_name}")
        return backup_name


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="TTA.dev Git Repository Manager")
    parser.add_argument("command", choices=["status", "cleanup", "backup", "sync"],
                       help="Command to execute")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without doing it")
    
    args = parser.parse_args()
    
    manager = GitManager()
    
    if args.command == "status":
        manager.display_status_dashboard()
    
    elif args.command == "cleanup":
        if args.dry_run:
            print("🔍 DRY RUN - No changes will be made")
            manager.display_status_dashboard()
        else:
            manager.interactive_cleanup()
    
    elif args.command == "backup":
        backup = manager.create_backup_branch()
        print(f"📦 Backup created: {backup}")
    
    elif args.command == "sync":
        status = manager.get_status()
        if status['behind'] > 0:
            manager.sync_with_remote()
        else:
            print("✅ Already up to date")


if __name__ == "__main__":
    main()
