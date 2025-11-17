#!/usr/bin/env python3
"""
Sync learnings from agent worktrees to orchestrator.

This script:
1. Scans agent worktrees for new patterns in .worktree/local-patterns/
2. Copies them to orchestrator's coordination directory
3. Generates sync report
4. Updates sync status
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

# Worktree configuration
WORKTREES = {
    "augment": Path("/home/thein/repos/TTA.dev-augment"),
    "cline": Path("/home/thein/repos/TTA.dev-cline"),
    "copilot": Path("/home/thein/repos/TTA.dev-copilot"),
}

ORCHESTRATOR_ROOT = Path("/home/thein/repos/TTA.dev")
COORDINATION_DIR = ORCHESTRATOR_ROOT / ".worktree" / "coordination"
SYNC_STATUS_FILE = ORCHESTRATOR_ROOT / ".worktree" / "sync-status.json"


def load_sync_status() -> Dict:
    """Load last sync timestamps."""
    if SYNC_STATUS_FILE.exists():
        with open(SYNC_STATUS_FILE) as f:
            return json.load(f)
    return {}


def save_sync_status(status: Dict) -> None:
    """Save sync timestamps."""
    SYNC_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SYNC_STATUS_FILE, "w") as f:
        json.dump(status, f, indent=2)


def scan_logseq_patterns(worktree_path: Path) -> List[Path]:
    """Scan Logseq for pages tagged #ready-to-share."""
    patterns = []
    logseq_pages = worktree_path / "logseq" / "pages"
    
    if not logseq_pages.exists():
        return patterns
    
    for page_file in logseq_pages.glob("*.md"):
        content = page_file.read_text()
        if "#ready-to-share" in content:
            patterns.append(page_file)
    
    return patterns


def sync_agent_patterns(agent_name: str, dry_run: bool = False) -> Dict:
    """
    Sync patterns from agent worktree to orchestrator.
    
    Returns dict with:
    - new_patterns: List of newly synced patterns
    - updated_patterns: List of updated patterns
    - skipped_patterns: List of unchanged patterns
    """
    worktree_path = WORKTREES[agent_name]
    patterns_dir = worktree_path / ".worktree" / "local-patterns"
    
    result = {
        "new_patterns": [],
        "updated_patterns": [],
        "skipped_patterns": [],
        "logseq_patterns": [],
    }
    
    # Create target directory
    target_dir = COORDINATION_DIR / f"agent-{agent_name}"
    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
    
    # Sync file-based patterns
    if patterns_dir.exists():
        for pattern_file in patterns_dir.glob("*.md"):
            target_file = target_dir / pattern_file.name
            
            # Check if needs sync
            if target_file.exists():
                source_mtime = pattern_file.stat().st_mtime
                target_mtime = target_file.stat().st_mtime
                
                if source_mtime <= target_mtime:
                    result["skipped_patterns"].append(pattern_file.name)
                    continue
                
                # Updated pattern
                if not dry_run:
                    shutil.copy2(pattern_file, target_file)
                result["updated_patterns"].append(pattern_file.name)
                print(f"  ↻ Updated: {pattern_file.name}")
            else:
                # New pattern
                if not dry_run:
                    shutil.copy2(pattern_file, target_file)
                result["new_patterns"].append(pattern_file.name)
                print(f"  ✓ New: {pattern_file.name}")
    
    # Scan Logseq for tagged patterns
    logseq_patterns = scan_logseq_patterns(worktree_path)
    if logseq_patterns:
        print(f"  ℹ Found {len(logseq_patterns)} Logseq pages tagged #ready-to-share")
        result["logseq_patterns"] = [p.name for p in logseq_patterns]
    
    return result


def generate_sync_report(results: Dict[str, Dict]) -> str:
    """Generate human-readable sync report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    
    report = [
        f"Sync Report: {timestamp}",
        "=" * 60,
        "",
    ]
    
    total_new = 0
    total_updated = 0
    total_logseq = 0
    
    for agent_name, result in results.items():
        report.append(f"Agent: {agent_name}")
        report.append(f"  New patterns: {len(result['new_patterns'])}")
        report.append(f"  Updated patterns: {len(result['updated_patterns'])}")
        report.append(f"  Logseq patterns: {len(result['logseq_patterns'])}")
        report.append("")
        
        total_new += len(result["new_patterns"])
        total_updated += len(result["updated_patterns"])
        total_logseq += len(result["logseq_patterns"])
    
    report.append("Summary:")
    report.append(f"  Total new patterns: {total_new}")
    report.append(f"  Total updated patterns: {total_updated}")
    report.append(f"  Total Logseq patterns: {total_logseq}")
    report.append("")
    
    if total_new + total_updated + total_logseq > 0:
        report.append("Action Required:")
        report.append(f"  → Review {total_new + total_updated} patterns in .worktree/coordination/")
        if total_logseq > 0:
            report.append(f"  → Check {total_logseq} Logseq pages for integration")
    else:
        report.append("No new patterns to review. All agents in sync!")
    
    return "\n".join(report)


def sync_all_agents(dry_run: bool = False) -> None:
    """Sync all agent worktrees."""
    print("🔄 Syncing learnings from all agent worktrees...\n")
    
    results = {}
    
    for agent_name in WORKTREES.keys():
        print(f"📦 Agent: {agent_name}")
        
        # Check if worktree exists
        if not WORKTREES[agent_name].exists():
            print(f"  ⚠ Worktree not found: {WORKTREES[agent_name]}")
            continue
        
        # Sync patterns
        result = sync_agent_patterns(agent_name, dry_run=dry_run)
        results[agent_name] = result
        
        print()
    
    # Generate and display report
    report = generate_sync_report(results)
    print("\n" + report)
    
    # Update sync status
    if not dry_run:
        status = load_sync_status()
        status["last_sync"] = datetime.now().isoformat()
        status["agents"] = {
            agent_name: {
                "last_sync": datetime.now().isoformat(),
                "new_patterns": len(result["new_patterns"]),
                "updated_patterns": len(result["updated_patterns"]),
            }
            for agent_name, result in results.items()
        }
        save_sync_status(status)
        print(f"\n✓ Sync status saved to {SYNC_STATUS_FILE}")


def main():
    parser = argparse.ArgumentParser(
        description="Sync learnings from agent worktrees to orchestrator"
    )
    parser.add_argument(
        "--sync-all",
        action="store_true",
        help="Sync all agent worktrees",
    )
    parser.add_argument(
        "--from",
        dest="agent",
        choices=list(WORKTREES.keys()),
        help="Sync specific agent worktree",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without making changes",
    )
    
    args = parser.parse_args()
    
    if args.sync_all:
        sync_all_agents(dry_run=args.dry_run)
    elif args.agent:
        print(f"🔄 Syncing learnings from agent: {args.agent}\n")
        result = sync_agent_patterns(args.agent, dry_run=args.dry_run)
        
        # Simple report for single agent
        print(f"\n📊 Summary for {args.agent}:")
        print(f"  New: {len(result['new_patterns'])}")
        print(f"  Updated: {len(result['updated_patterns'])}")
        print(f"  Skipped: {len(result['skipped_patterns'])}")
        print(f"  Logseq: {len(result['logseq_patterns'])}")
    else:
        parser.print_help()
        print("\nExample usage:")
        print("  python sync-learnings.py --sync-all")
        print("  python sync-learnings.py --from augment")
        print("  python sync-learnings.py --sync-all --dry-run")


if __name__ == "__main__":
    main()
