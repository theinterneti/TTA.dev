#!/usr/bin/env python3
"""
Display coordination status across all worktrees.

Shows:
- Active worktrees and their status
- Pending pattern reviews
- Integration queue
- Issues and blockers
- Recent activity
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

WORKTREES = {
    "orchestrator": Path("/home/thein/repos/TTA.dev"),
    "augment": Path("/home/thein/repos/TTA.dev-augment"),
    "cline": Path("/home/thein/repos/TTA.dev-cline"),
    "copilot": Path("/home/thein/repos/TTA.dev-copilot"),
}

COORDINATION_DIR = Path("/home/thein/repos/TTA.dev/.worktree/coordination")
SYNC_STATUS_FILE = Path("/home/thein/repos/TTA.dev/.worktree/sync-status.json")


def get_branch_name(worktree_path: Path) -> str:
    """Get current branch name for worktree."""
    try:
        git_head = worktree_path / ".git" / "HEAD"
        if git_head.exists():
            content = git_head.read_text().strip()
            if content.startswith("ref: refs/heads/"):
                return content.replace("ref: refs/heads/", "")
        return "unknown"
    except Exception:
        return "error"


def check_worktree_status(name: str, path: Path) -> Dict:
    """Check status of a worktree."""
    return {
        "name": name,
        "path": str(path),
        "exists": path.exists(),
        "branch": get_branch_name(path) if path.exists() else "N/A",
    }


def count_patterns_in_dir(directory: Path) -> Dict[str, int]:
    """Count patterns by category in a directory."""
    if not directory.exists():
        return {"total": 0, "high_priority": 0, "medium_priority": 0}
    
    patterns = list(directory.glob("*.md"))
    
    # Simple heuristic: files with "critical" or "security" are high priority
    high_priority = sum(
        1 for p in patterns
        if any(keyword in p.name.lower() for keyword in ["critical", "security", "urgent"])
    )
    
    return {
        "total": len(patterns),
        "high_priority": high_priority,
        "medium_priority": len(patterns) - high_priority,
    }


def get_sync_status() -> Dict:
    """Get last sync status."""
    if SYNC_STATUS_FILE.exists():
        with open(SYNC_STATUS_FILE) as f:
            return json.load(f)
    return {}


def time_since(timestamp: str) -> str:
    """Human-readable time since timestamp."""
    try:
        dt = datetime.fromisoformat(timestamp)
        delta = datetime.now() - dt
        
        if delta < timedelta(minutes=1):
            return "just now"
        elif delta < timedelta(hours=1):
            mins = int(delta.total_seconds() / 60)
            return f"{mins} minute{'s' if mins != 1 else ''} ago"
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = delta.days
            return f"{days} day{'s' if days != 1 else ''} ago"
    except Exception:
        return "unknown"


def display_status():
    """Display full coordination status."""
    print("=" * 70)
    print("TTA.dev Worktree Coordination Status".center(70))
    print("=" * 70)
    print()
    
    # Worktree status
    print("📍 Worktrees:")
    print("-" * 70)
    for name, path in WORKTREES.items():
        status = check_worktree_status(name, path)
        if status["exists"]:
            symbol = "✓" if name == "orchestrator" else "•"
            role = "(orchestrator)" if name == "orchestrator" else ""
            print(f"{symbol} {name:15} - {status['branch']:40} {role}")
        else:
            print(f"✗ {name:15} - NOT FOUND at {path}")
    print()
    
    # Sync status
    sync_status = get_sync_status()
    if sync_status:
        last_sync = sync_status.get("last_sync")
        if last_sync:
            print(f"🔄 Last Sync: {time_since(last_sync)}")
        print()
    else:
        print("⚠ No sync status found. Run sync-learnings.py first.")
        print()
    
    # Pending reviews
    print("📋 Pending Pattern Reviews:")
    print("-" * 70)
    total_pending = 0
    for agent in ["augment", "cline", "copilot"]:
        agent_dir = COORDINATION_DIR / f"agent-{agent}"
        counts = count_patterns_in_dir(agent_dir)
        if counts["total"] > 0:
            print(f"  {agent:12} - {counts['total']} patterns ", end="")
            if counts["high_priority"] > 0:
                print(f"({counts['high_priority']} high priority)", end="")
            print()
            total_pending += counts["total"]
    
    if total_pending == 0:
        print("  ✓ No pending reviews")
    print()
    
    # Integration queue
    integration_queue = COORDINATION_DIR / "integration-queue"
    queue_counts = count_patterns_in_dir(integration_queue)
    print(f"🚀 Integration Queue: {queue_counts['total']} patterns ready")
    print()
    
    # Recommendations
    print("💡 Recommendations:")
    print("-" * 70)
    
    recommendations = []
    
    if total_pending > 10:
        recommendations.append("→ High review backlog! Review patterns in .worktree/coordination/")
    
    if total_pending > 0:
        recommendations.append("→ Review pending patterns before next integration")
    
    if not sync_status or not sync_status.get("last_sync"):
        recommendations.append("→ Run sync-learnings.py --sync-all to get latest patterns")
    elif sync_status.get("last_sync"):
        last_sync_dt = datetime.fromisoformat(sync_status["last_sync"])
        if datetime.now() - last_sync_dt > timedelta(hours=24):
            recommendations.append("→ Sync is stale (>24h). Run sync-learnings.py --sync-all")
    
    if queue_counts["total"] > 0:
        recommendations.append(f"→ {queue_counts['total']} patterns ready for integration")
    
    if not recommendations:
        recommendations.append("✓ All systems operational!")
    
    for rec in recommendations:
        print(f"  {rec}")
    
    print()
    print("=" * 70)


def main():
    display_status()


if __name__ == "__main__":
    main()
