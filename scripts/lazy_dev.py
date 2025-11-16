#!/usr/bin/env python3
"""
🤖 Lazy Dev Repo Manager - Your AI-Powered Git Assistant

Never think about git/GitHub again! This manages everything automatically:
- Branch creation with smart naming
- PR creation with AI-generated descriptions
- Issue/milestone management
- Collaboration with @copilot and @cline
- Automated workflows

Usage:
    ./scripts/lazy_dev.py                    # Interactive mode
    ./scripts/lazy_dev.py work-on "feature"  # Create branch & start work
    ./scripts/lazy_dev.py pr                 # Create PR with AI description
    ./scripts/lazy_dev.py status             # Check everything
    ./scripts/lazy_dev.py collaborate        # Start agent collaboration
"""

import asyncio
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

REPO = "theinterneti/TTA.dev"
REPO_ROOT = Path(__file__).parent.parent


class WorkType(Enum):
    """Type of work being done."""
    FEATURE = "feature"
    FIX = "fix"
    DOCS = "docs"
    REFACTOR = "refactor"
    TEST = "test"
    CHORE = "chore"


@dataclass
class RepoState:
    """Current repository state."""
    current_branch: str
    main_branch: str
    has_changes: bool
    has_staged: bool
    is_ahead: bool
    is_behind: bool
    open_prs: list[dict[str, Any]]
    open_issues: list[dict[str, Any]]


class LazyDevManager:
    """Intelligent repository management for lazy developers."""
    
    def __init__(self, repo: str = REPO):
        self.repo = repo
        self.repo_root = REPO_ROOT
    
    # ========================================================================
    # Git Operations
    # ========================================================================
    
    def run_git(self, *args: str, check: bool = True) -> str:
        """Run git command and return output."""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                capture_output=True,
                text=True,
                check=check,
                cwd=self.repo_root
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            if check:
                raise
            return ""
    
    def run_gh(self, *args: str, check: bool = True) -> str:
        """Run gh CLI command and return output."""
        try:
            result = subprocess.run(
                ["gh"] + list(args),
                capture_output=True,
                text=True,
                check=check,
                cwd=self.repo_root
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            if check:
                raise
            return ""
    
    def get_repo_state(self) -> RepoState:
        """Get current repository state."""
        current_branch = self.run_git("branch", "--show-current")
        # Detect main branch from remote, fallback to "main" if detection fails
        symbolic_ref = self.run_git("symbolic-ref", "refs/remotes/origin/HEAD", check=False)
        if symbolic_ref.startswith("refs/remotes/origin/"):
            main_branch = symbolic_ref.split("/")[-1]
        else:
            main_branch = "main"
        
        status = self.run_git("status", "--porcelain")
        staged = self.run_git("diff", "--cached", "--name-only")
        
        # Check ahead/behind
        ahead_behind = self.run_git(
            "rev-list", "--left-right", "--count",
            f"HEAD...origin/{current_branch}",
            check=False
        )
        ahead, behind = 0, 0
        if ahead_behind:
            parts = ahead_behind.split()
            if len(parts) == 2:
                ahead, behind = int(parts[0]), int(parts[1])
        
        # Get open PRs
        pr_json = self.run_gh(
            "pr", "list",
            "--repo", self.repo,
            "--json", "number,title,state,author",
            "--limit", "20"
        )
        open_prs = json.loads(pr_json) if pr_json else []
        
        # Get open issues
        issue_json = self.run_gh(
            "issue", "list",
            "--repo", self.repo,
            "--json", "number,title,state,author",
            "--limit", "20"
        )
        open_issues = json.loads(issue_json) if issue_json else []
        
        return RepoState(
            current_branch=current_branch,
            main_branch=main_branch,
            has_changes=bool(status),
            has_staged=bool(staged),
            is_ahead=ahead > 0,
            is_behind=behind > 0,
            open_prs=open_prs,
            open_issues=open_issues
        )
    
    # ========================================================================
    # Smart Branch Management
    # ========================================================================
    
    def generate_branch_name(self, description: str, work_type: WorkType) -> str:
        """Generate a smart branch name."""
        # Clean description
        clean_desc = description.lower().strip()
        clean_desc = clean_desc.replace(" ", "-")
        clean_desc = "".join(c for c in clean_desc if c.isalnum() or c == "-")
        clean_desc = clean_desc[:50]  # Limit length
        
        # Add date for uniqueness
        date_str = datetime.now(UTC).strftime("%Y%m%d")
        
        return f"{work_type.value}/{clean_desc}-{date_str}"
    
    async def create_branch(self, description: str, work_type: WorkType) -> str:
        """Create a new branch with smart naming."""
        branch_name = self.generate_branch_name(description, work_type)
        
        print(f"🌿 Creating branch: {branch_name}")
        
        # Ensure we're on main and up to date
        state = self.get_repo_state()
        if state.current_branch != state.main_branch:
            print(f"   Switching to {state.main_branch}...")
            self.run_git("checkout", state.main_branch)
        
        print("   Pulling latest changes...")
        self.run_git("pull", "origin", state.main_branch)
        
        # Create and checkout new branch
        print(f"   Creating and checking out {branch_name}...")
        self.run_git("checkout", "-b", branch_name)
        
        print(f"✅ Branch created: {branch_name}")
        return branch_name
    
    # ========================================================================
    # AI-Powered PR Creation
    # ========================================================================
    
    async def generate_pr_description(self, title: str, branch: str) -> str:
        """Generate PR description using AI (calls Copilot)."""
        # Get changed files
        files = self.run_git("diff", "--name-only", f"origin/main...{branch}")
        
        # Get commit messages
        commits = self.run_git(
            "log", f"origin/main..{branch}",
            "--pretty=format:- %s"
        )
        
        # Use gh copilot to generate description
        prompt = f"""Generate a concise PR description for:

Title: {title}

Changed files:
{files}

Commits:
{commits}

Format as:
## Summary
<1-2 sentence overview>

## Changes
- <key change 1>
- <key change 2>

## Impact
<what this enables>
"""
        
        try:
            # Try using gh copilot suggest
            description = self.run_gh(
                "copilot", "suggest",
                "-t", "git",
                prompt,
                check=False
            )
            if description:
                return description
        except Exception:
            pass
        
        # Fallback to simple description
        return f"""## Summary

{title}

## Changes

{commits if commits else '- Implementation changes'}

## Files Modified

{files}

---
*Generated automatically by lazy_dev.py*
"""
    
    async def create_pr(self, title: str | None = None, draft: bool = False) -> int:
        """Create PR with AI-generated description."""
        state = self.get_repo_state()
        
        if state.current_branch == state.main_branch:
            print("❌ Cannot create PR from main branch")
            return 0
        
        # Generate title if not provided
        if not title:
            # Extract from branch name
            parts = state.current_branch.split("/", 1)
            if len(parts) == 2:
                work_type, desc = parts
                title = f"{work_type}: {desc.replace('-', ' ').title()}"
            else:
                title = f"Update from {state.current_branch}"
        
        print(f"📋 Creating PR: {title}")
        
        # Push current branch
        if state.is_ahead or state.has_changes:
            print("   Pushing changes...")
            self.run_git("push", "-u", "origin", state.current_branch)
        
        # Generate description
        print("   Generating AI description...")
        description = await self.generate_pr_description(title, state.current_branch)
        
        # Create PR
        print("   Creating PR...")
        pr_url = self.run_gh(
            "pr", "create",
            "--repo", self.repo,
            "--title", title,
            "--body", description,
            *(["--draft"] if draft else []),
            "--base", state.main_branch
        )
        
        # Extract PR number
        pr_number = int(pr_url.split("/")[-1])
        
        print(f"✅ PR created: {pr_url}")
        
        # Auto-request @copilot review
        print("   Requesting @copilot review...")
        self.run_gh(
            "pr", "edit", str(pr_number),
            "--add-reviewer", "copilot",
            check=False
        )
        
        return pr_number
    
    # ========================================================================
    # Agent Collaboration
    # ========================================================================
    
    async def collaborate_on_pr(self, pr_number: int, agents: list[str] = None):
        """Start collaboration with AI agents on a PR."""
        if agents is None:
            agents = ["copilot", "cline"]
        
        print(f"🤝 Starting collaboration on PR #{pr_number}")
        
        # Add comment mentioning agents
        mentions = " ".join(f"@{agent}" for agent in agents)
        comment = f"""{mentions}

Please review this PR and provide feedback on:
- Code quality and best practices
- Test coverage
- Documentation completeness
- Potential issues or improvements

Work together to ensure this PR meets all quality standards.
"""
        
        print(f"   Adding collaboration comment with: {mentions}")
        self.run_gh(
            "pr", "comment", str(pr_number),
            "--body", comment
        )
        
        print(f"✅ Collaboration started! Agents will respond in PR #{pr_number}")
    
    async def collaborate_on_issue(self, issue_number: int, task: str, agents: list[str] = None):
        """Assign agents to work on an issue."""
        if agents is None:
            agents = ["copilot"]
        
        print(f"🎯 Assigning issue #{issue_number} to agents")
        
        for agent in agents:
            print(f"   Assigning @{agent}...")
            # Use gh issue develop for copilot
            if agent == "copilot":
                self.run_gh(
                    "issue", "develop", str(issue_number),
                    "--name", f"fix/{issue_number}-{task[:20]}",
                    check=False
                )
        
        # Add comment with task details
        mentions = " ".join(f"@{agent}" for agent in agents)
        comment = f"""{mentions}

Task: {task}

Please work together on this issue. Create a branch, implement the solution, and open a PR when ready.
"""
        
        self.run_gh(
            "issue", "comment", str(issue_number),
            "--body", comment
        )
        
        print(f"✅ Agents assigned to issue #{issue_number}")
    
    # ========================================================================
    # Status & Dashboard
    # ========================================================================
    
    async def show_status(self):
        """Show comprehensive repository status."""
        state = self.get_repo_state()
        
        print("=" * 60)
        print("📊 Repository Status")
        print("=" * 60)
        print()
        
        print(f"📍 Current Branch: {state.current_branch}")
        print(f"🌿 Main Branch: {state.main_branch}")
        print()
        
        print("📝 Local Changes:")
        if state.has_changes:
            print("   ⚠️  Uncommitted changes detected")
            if state.has_staged:
                print("   ✅ Staged changes ready to commit")
        else:
            print("   ✅ Working tree clean")
        print()
        
        if state.is_ahead:
            print(f"   ⬆️  Ahead of remote (unpushed commits)")
        if state.is_behind:
            print(f"   ⬇️  Behind remote (need to pull)")
        print()
        
        print(f"📋 Open PRs: {len(state.open_prs)}")
        for pr in state.open_prs[:5]:
            print(f"   #{pr['number']}: {pr['title']}")
        print()
        
        print(f"🎫 Open Issues: {len(state.open_issues)}")
        for issue in state.open_issues[:5]:
            print(f"   #{issue['number']}: {issue['title']}")
        print()
        
        print("=" * 60)
    
    async def interactive_mode(self):
        """Run interactive mode with menu."""
        while True:
            print("\n" + "=" * 60)
            print("🤖 Lazy Dev Repo Manager - What do you want to do?")
            print("=" * 60)
            print()
            print("1. 🌿 Start working on something (create branch)")
            print("2. 📋 Create a PR")
            print("3. 🤝 Collaborate with agents on PR")
            print("4. 🎯 Assign agents to an issue")
            print("5. 📊 Show status")
            print("6. 🚀 Push current work")
            print("7. 🔄 Sync with main")
            print("0. 👋 Exit")
            print()
            
            choice = input("Choose an option: ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            
            elif choice == "1":
                desc = input("What are you working on? ").strip()
                print("\nWork type:")
                for i, wt in enumerate(WorkType, 1):
                    print(f"  {i}. {wt.value}")
                type_choice = input("Choose type (or press enter for 'feature'): ").strip()
                
                if type_choice.isdigit() and 1 <= int(type_choice) <= len(list(WorkType)):
                    work_type = list(WorkType)[int(type_choice) - 1]
                else:
                    work_type = WorkType.FEATURE
                
                await self.create_branch(desc, work_type)
            
            elif choice == "2":
                title = input("PR title (or press enter for auto-generate): ").strip() or None
                draft = input("Create as draft? (y/n): ").strip().lower() == "y"
                await self.create_pr(title, draft)
            
            elif choice == "3":
                pr_num = int(input("PR number: ").strip())
                await self.collaborate_on_pr(pr_num)
            
            elif choice == "4":
                issue_num = int(input("Issue number: ").strip())
                task = input("Task description: ").strip()
                await self.collaborate_on_issue(issue_num, task)
            
            elif choice == "5":
                await self.show_status()
            
            elif choice == "6":
                state = self.get_repo_state()
                if state.has_changes or state.has_staged or state.is_ahead:
                    self.run_git("push", "-u", "origin", state.current_branch, check=False)
                    print("✅ Pushed!")
                else:
                    print("ℹ️  Nothing to push")
            
            elif choice == "7":
                state = self.get_repo_state()
                self.run_git("fetch", "origin")
                self.run_git("merge", f"origin/{state.main_branch}")
                print("✅ Synced with main!")
            
            else:
                print("Invalid choice, try again")


async def main():
    """Main entry point."""
    manager = LazyDevManager()
    
    if len(sys.argv) == 1:
        # Interactive mode
        await manager.interactive_mode()
    else:
        command = sys.argv[1]
        
        if command == "status":
            await manager.show_status()
        
        elif command == "work-on":
            if len(sys.argv) < 3:
                print("Usage: lazy_dev.py work-on <description>")
                sys.exit(1)
            desc = " ".join(sys.argv[2:])
            await manager.create_branch(desc, WorkType.FEATURE)
        
        elif command == "pr":
            title = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
            await manager.create_pr(title)
        
        elif command == "collaborate":
            await manager.interactive_mode()
        
        else:
            print(f"Unknown command: {command}")
            print("Try: status, work-on, pr, collaborate, or no arguments for interactive mode")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
