#!/usr/bin/env python3
"""
TTA.dev Multi-Agent Oversight System

This script helps the copilot agent review and approve commits
from other agents (augment, cline) in the worktree.

Usage:
    python scripts/agent_oversight.py status        # View pending commits
    python scripts/agent_oversight.py review        # Review commits interactively
    python scripts/agent_oversight.py approve <id>  # Approve a specific commit
    python scripts/agent_oversight.py reject <id>   # Reject a specific commit
    python scripts/agent_oversight.py sync          # Sync approved changes
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# ANSI colors
COLORS = {
    "RED": "\033[0;31m",
    "GREEN": "\033[0;32m",
    "YELLOW": "\033[1;33m",
    "BLUE": "\033[0;34m",
    "MAGENTA": "\033[0;35m",
    "CYAN": "\033[0;36m",
    "NC": "\033[0m",  # No Color
}


def colored(text: str, color: str) -> str:
    """Return colored text."""
    return f"{COLORS.get(color, '')}{text}{COLORS['NC']}"


class AgentOversight:
    """Manage oversight of multi-agent commits."""

    def __init__(self):
        self.copilot_worktree = Path("/home/thein/repos/TTA.dev-copilot")
        self.notification_dir = self.copilot_worktree / ".agent-notifications"
        self.review_log = self.copilot_worktree / ".agent-reviews.json"
        
        # Create directories if they don't exist
        self.notification_dir.mkdir(exist_ok=True)

    def get_pending_commits(self) -> list[dict[str, Any]]:
        """Get all pending commit notifications."""
        pending = []
        
        if not self.notification_dir.exists():
            return pending
        
        for notification_file in self.notification_dir.glob("pending-*.json"):
            try:
                with open(notification_file) as f:
                    data = json.load(f)
                    data["notification_file"] = str(notification_file)
                    data["id"] = notification_file.stem.replace("pending-", "")
                    pending.append(data)
            except Exception as e:
                print(f"Error reading {notification_file}: {e}")
        
        return sorted(pending, key=lambda x: x["timestamp"])

    def show_status(self):
        """Display status of pending commits."""
        pending = self.get_pending_commits()
        
        print(colored("\n🔍 TTA.dev Multi-Agent Oversight Status\n", "CYAN"))
        
        if not pending:
            print(colored("✅ No pending commits to review", "GREEN"))
            return
        
        print(colored(f"📋 {len(pending)} pending commit(s) to review:\n", "YELLOW"))
        
        for commit in pending:
            agent_color = {
                "augment": "MAGENTA",
                "cline": "BLUE",
            }.get(commit["agent"], "YELLOW")
            
            print(colored(f"  [{commit['id']}]", "CYAN"))
            print(f"    Agent:   {colored(commit['agent'], agent_color)}")
            print(f"    Branch:  {commit['branch']}")
            print(f"    Time:    {commit['timestamp']}")
            print(f"    Commit:  {commit['commit'][:8]}")
            print(f"    Message: {commit['message']}")
            print()

    def review_commit(self, commit_id: str):
        """Review a specific commit."""
        pending = self.get_pending_commits()
        commit = next((c for c in pending if c["id"] == commit_id), None)
        
        if not commit:
            print(colored(f"❌ Commit {commit_id} not found", "RED"))
            return
        
        print(colored(f"\n📝 Reviewing commit from {commit['agent']}\n", "CYAN"))
        print(f"Branch:  {commit['branch']}")
        print(f"Commit:  {commit['commit']}")
        print(f"Message: {commit['message']}")
        print(f"Time:    {commit['timestamp']}")
        
        # Show the diff
        print(colored("\n📊 Changes:\n", "YELLOW"))
        try:
            result = subprocess.run(
                ["git", "show", "--stat", commit["commit"]],
                cwd=commit["worktree"],
                capture_output=True,
                text=True,
            )
            print(result.stdout)
        except Exception as e:
            print(colored(f"❌ Error showing diff: {e}", "RED"))
        
        # Ask for approval
        response = input(colored("\nApprove this commit? (y/n/defer): ", "CYAN"))
        
        if response.lower() == "y":
            self.approve_commit(commit_id)
        elif response.lower() == "n":
            self.reject_commit(commit_id)
        else:
            print(colored("⏸️  Review deferred", "YELLOW"))

    def approve_commit(self, commit_id: str):
        """Approve a commit."""
        pending = self.get_pending_commits()
        commit = next((c for c in pending if c["id"] == commit_id), None)
        
        if not commit:
            print(colored(f"❌ Commit {commit_id} not found", "RED"))
            return
        
        # Log the approval
        self._log_review(commit, "approved")
        
        # Remove notification
        Path(commit["notification_file"]).unlink()
        
        print(colored(f"✅ Approved commit {commit['commit'][:8]} from {commit['agent']}", "GREEN"))

    def reject_commit(self, commit_id: str, reason: str = ""):
        """Reject a commit."""
        pending = self.get_pending_commits()
        commit = next((c for c in pending if c["id"] == commit_id), None)
        
        if not commit:
            print(colored(f"❌ Commit {commit_id} not found", "RED"))
            return
        
        if not reason:
            reason = input(colored("Reason for rejection: ", "YELLOW"))
        
        # Log the rejection
        commit["rejection_reason"] = reason
        self._log_review(commit, "rejected")
        
        # Remove notification
        Path(commit["notification_file"]).unlink()
        
        print(colored(f"❌ Rejected commit {commit['commit'][:8]} from {commit['agent']}", "RED"))
        print(f"Reason: {reason}")

    def _log_review(self, commit: dict[str, Any], decision: str):
        """Log a review decision."""
        reviews = []
        if self.review_log.exists():
            with open(self.review_log) as f:
                reviews = json.load(f)
        
        review_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "decision": decision,
            **commit,
        }
        # Remove the notification_file and id from log
        review_entry.pop("notification_file", None)
        review_entry.pop("id", None)
        
        reviews.append(review_entry)
        
        with open(self.review_log, "w") as f:
            json.dump(reviews, f, indent=2)

    def review_all(self):
        """Review all pending commits interactively."""
        pending = self.get_pending_commits()
        
        if not pending:
            print(colored("✅ No pending commits to review", "GREEN"))
            return
        
        for commit in pending:
            self.review_commit(commit["id"])
            print("\n" + "=" * 80 + "\n")


def main():
    """Main entry point."""
    oversight = AgentOversight()
    
    if len(sys.argv) < 2:
        print("Usage: agent_oversight.py {status|review|approve|reject} [args]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "status":
        oversight.show_status()
    elif command == "review":
        if len(sys.argv) > 2:
            oversight.review_commit(sys.argv[2])
        else:
            oversight.review_all()
    elif command == "approve":
        if len(sys.argv) < 3:
            print(colored("❌ Usage: approve <commit-id>", "RED"))
            sys.exit(1)
        oversight.approve_commit(sys.argv[2])
    elif command == "reject":
        if len(sys.argv) < 3:
            print(colored("❌ Usage: reject <commit-id>", "RED"))
            sys.exit(1)
        reason = sys.argv[3] if len(sys.argv) > 3 else ""
        oversight.reject_commit(sys.argv[2], reason)
    else:
        print(colored(f"❌ Unknown command: {command}", "RED"))
        sys.exit(1)


if __name__ == "__main__":
    main()
