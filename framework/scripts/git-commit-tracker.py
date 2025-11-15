#!/usr/bin/env python3
"""
Git hook to track commit metrics during AI agent sessions.

This post-commit hook emits Prometheus metrics about commits.
Install by symlinking to .git/hooks/post-commit

Usage:
    ln -sf ../../scripts/git-commit-tracker.py .git/hooks/post-commit
"""

import os
import subprocess
import sys

try:
    from prometheus_client import CollectorRegistry, Counter, Gauge, push_to_gateway
except ImportError:
    # Graceful degradation if prometheus_client not available
    print(
        "⚠️  prometheus_client not installed. Metrics will not be exported.",
        file=sys.stderr,
    )
    sys.exit(0)

# Configuration
PUSHGATEWAY_URL = os.environ.get("PUSHGATEWAY_URL", "localhost:9091")
METRICS_ENABLED = os.environ.get("GIT_METRICS_ENABLED", "1") == "1"

# Create registry for this push
registry = CollectorRegistry()

# Metrics
commits_total = Counter(
    "git_commits_total",
    "Total number of commits",
    ["author", "branch"],
    registry=registry,
)

commit_lines_added = Gauge(
    "git_commit_lines_added",
    "Lines added in last commit",
    ["branch"],
    registry=registry,
)

commit_lines_removed = Gauge(
    "git_commit_lines_removed",
    "Lines removed in last commit",
    ["branch"],
    registry=registry,
)

commit_files_changed = Gauge(
    "git_commit_files_changed",
    "Files changed in last commit",
    ["branch"],
    registry=registry,
)


def get_git_info():
    """Get information about the current commit."""
    try:
        # Get current branch
        branch = (
            subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
        )

        # Get author
        author = (
            subprocess.check_output(["git", "log", "-1", "--pretty=format:%an"]).decode().strip()
        )

        # Get commit hash
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()

        # Get stats from last commit
        stats = (
            subprocess.check_output(["git", "diff", "--shortstat", "HEAD~1", "HEAD"])
            .decode()
            .strip()
        )

        return {
            "branch": branch,
            "author": author,
            "commit_hash": commit_hash,
            "stats": stats,
        }
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting git info: {e}", file=sys.stderr)
        return None


def parse_stats(stats_str):
    """Parse git diff stats string."""
    if not stats_str:
        return {"files": 0, "insertions": 0, "deletions": 0}

    parts = stats_str.split(",")
    result = {"files": 0, "insertions": 0, "deletions": 0}

    for part in parts:
        part = part.strip()
        if "file" in part:
            result["files"] = int(part.split()[0])
        elif "insertion" in part:
            result["insertions"] = int(part.split()[0])
        elif "deletion" in part:
            result["deletions"] = int(part.split()[0])

    return result


def main():
    """Main hook logic."""
    if not METRICS_ENABLED:
        sys.exit(0)

    # Get git information
    git_info = get_git_info()
    if not git_info:
        sys.exit(0)

    # Parse stats
    stats = parse_stats(git_info["stats"])

    # Update metrics
    commits_total.labels(author=git_info["author"], branch=git_info["branch"]).inc()
    commit_lines_added.labels(branch=git_info["branch"]).set(stats["insertions"])
    commit_lines_removed.labels(branch=git_info["branch"]).set(stats["deletions"])
    commit_files_changed.labels(branch=git_info["branch"]).set(stats["files"])

    # Log to stderr (stdout is for git)
    print(
        f"📊 Commit metrics: {stats['files']} files, "
        f"+{stats['insertions']}/-{stats['deletions']} lines",
        file=sys.stderr,
    )

    # Push to gateway if available
    try:
        push_to_gateway(
            PUSHGATEWAY_URL,
            job="git-commits",
            registry=registry,
            timeout=1,
        )
        print(f"✅ Metrics pushed to {PUSHGATEWAY_URL}", file=sys.stderr)
    except Exception as e:
        print(f"⚠️  Failed to push metrics: {e}", file=sys.stderr)
        # Don't fail the commit if metrics push fails


if __name__ == "__main__":
    main()
