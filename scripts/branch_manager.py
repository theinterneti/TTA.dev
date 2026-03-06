#!/usr/bin/env python3
"""
🌿 Branch Manager — Automated stale branch cleanup for TTA.dev

Identifies and removes remote branches that are no longer active:
- Branches whose pull requests are merged or closed
- Branches with no associated PR that have been inactive for N days

Usage:
    ./scripts/branch_manager.py audit
    ./scripts/branch_manager.py delete-closed-pr-branches
    ./scripts/branch_manager.py delete-orphaned-branches [days]
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

# Branches that must never be deleted
PROTECTED_BRANCHES = {
    "main",
    "master",
    "develop",
}

# Branch name patterns to always keep (e.g. intentional snapshots)
PROTECTED_PATTERNS = (
    "backup/",
    "-snapshot-",
)


@dataclass
class BranchInfo:
    """Information about a remote branch."""

    name: str
    sha: str
    last_commit_date: datetime
    pr_number: int | None
    pr_title: str | None
    pr_state: str | None  # "OPEN", "MERGED", "CLOSED"


class BranchManager:
    """Manages remote branch lifecycle for the TTA.dev repository."""

    def __init__(self) -> None:
        """Initialize branch manager."""
        self.repo = self._get_repo()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_repo(self) -> str:
        """Return repository in owner/repo format."""
        try:
            result = subprocess.run(
                ["gh", "repo", "view", "--json", "nameWithOwner"],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(result.stdout)
            return data["nameWithOwner"]
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            return "theinterneti/TTA.dev"

    def _run_gh(self, *args: str) -> Any:
        """Run a gh CLI command and return parsed JSON (or empty dict/list)."""
        try:
            result = subprocess.run(
                ["gh"] + list(args),
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout) if result.stdout.strip() else {}
        except subprocess.CalledProcessError as e:
            print(f"gh error: {e.stderr.strip()}", file=sys.stderr)
            return {}
        except json.JSONDecodeError:
            return {}

    def _is_protected(self, name: str) -> bool:
        """Return True if the branch should never be deleted."""
        if name in PROTECTED_BRANCHES:
            return True
        return any(pattern in name for pattern in PROTECTED_PATTERNS)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def get_all_branches(self) -> list[dict[str, Any]]:
        """Return all remote branches via GitHub API."""
        raw = self._run_gh(
            "api",
            f"repos/{self.repo}/branches",
            "--paginate",
            "--jq",
            ".[].name",
        )
        # --paginate with --jq returns newline-separated strings, not JSON
        if isinstance(raw, dict):
            # Fallback: list via JSON
            data = self._run_gh(
                "api",
                f"repos/{self.repo}/branches?per_page=100",
                "--paginate",
            )
            return data if isinstance(data, list) else []

        # gh api --paginate --jq returns stdout directly — re-fetch as plain list
        try:
            result = subprocess.run(
                ["gh", "api", f"repos/{self.repo}/branches", "--paginate"],
                capture_output=True,
                text=True,
                check=True,
            )
            # GitHub paginates by appending JSON arrays; merge them
            branches: list[dict[str, Any]] = []
            for chunk in result.stdout.strip().split("\n"):
                chunk = chunk.strip()
                if not chunk:
                    continue
                try:
                    parsed = json.loads(chunk)
                    if isinstance(parsed, list):
                        branches.extend(parsed)
                    elif isinstance(parsed, dict):
                        branches.append(parsed)
                except json.JSONDecodeError:
                    continue
            return branches
        except subprocess.CalledProcessError as e:
            print(f"Error fetching branches: {e.stderr}", file=sys.stderr)
            return []

    def get_pr_for_branch(self, branch_name: str) -> dict[str, Any] | None:
        """Return the most recent PR (any state) for a branch, or None."""
        # Try open first
        for state in ("open", "closed"):
            data = self._run_gh(
                "pr",
                "list",
                "--repo",
                self.repo,
                "--head",
                branch_name,
                "--state",
                state,
                "--json",
                "number,title,state,mergedAt",
                "--limit",
                "1",
            )
            if isinstance(data, list) and data:
                return data[0]
        return None

    def get_branch_last_commit_date(self, sha: str) -> datetime:
        """Return the committer date for a commit SHA."""
        try:
            result = subprocess.run(
                [
                    "gh",
                    "api",
                    f"repos/{self.repo}/commits/{sha}",
                    "--jq",
                    ".commit.committer.date",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            date_str = result.stdout.strip().strip('"')
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception as exc:
            print(f"Warning: could not fetch commit date for {sha}: {exc}", file=sys.stderr)
            return datetime.now(UTC) - timedelta(days=9999)

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def analyse_branches(self, orphan_days: int = 30) -> list[BranchInfo]:
        """Return BranchInfo for every non-protected remote branch."""
        raw_branches = self.get_all_branches()
        infos: list[BranchInfo] = []

        for branch in raw_branches:
            name = branch.get("name", "")
            if not name or self._is_protected(name):
                continue

            sha = branch.get("commit", {}).get("sha", "")
            last_date = self.get_branch_last_commit_date(sha)

            pr = self.get_pr_for_branch(name)
            pr_number = pr.get("number") if pr else None
            pr_title = pr.get("title") if pr else None
            pr_state = pr.get("state") if pr else None  # OPEN / MERGED / CLOSED

            infos.append(
                BranchInfo(
                    name=name,
                    sha=sha,
                    last_commit_date=last_date,
                    pr_number=pr_number,
                    pr_title=pr_title,
                    pr_state=pr_state,
                )
            )

        return infos

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def audit(self, orphan_days: int = 30) -> None:
        """Print a markdown audit report of all branches."""
        print("Analysing branches (this may take a moment)…\n", file=sys.stderr)
        infos = self.analyse_branches(orphan_days)
        now = datetime.now(UTC)

        keep: list[BranchInfo] = []
        delete_closed_pr: list[BranchInfo] = []
        delete_orphan: list[BranchInfo] = []

        for info in infos:
            if info.pr_state in ("OPEN",):
                keep.append(info)
            elif info.pr_state in ("MERGED", "CLOSED"):
                delete_closed_pr.append(info)
            else:
                days_inactive = (now - info.last_commit_date).days
                if days_inactive >= orphan_days:
                    delete_orphan.append(info)
                else:
                    keep.append(info)

        total = len(infos)
        print("## 🌿 Branch Audit Report")
        print(f"\n**Total non-protected branches:** {total}")
        print(
            f"**To delete (closed/merged PR):** {len(delete_closed_pr)}  \n"
            f"**To delete (no PR, inactive ≥ {orphan_days} days):** {len(delete_orphan)}  \n"
            f"**To keep:** {len(keep)}"
        )

        if delete_closed_pr:
            print(f"\n### ❌ Closed/Merged PR Branches ({len(delete_closed_pr)})")
            print("| Branch | PR # | PR Title | Status |")
            print("|--------|------|----------|--------|")
            for b in sorted(delete_closed_pr, key=lambda x: x.name):
                pr_num = f"#{b.pr_number}" if b.pr_number else "—"
                pr_title = (b.pr_title or "—").replace("|", "\\|")
                print(f"| `{b.name}` | {pr_num} | {pr_title} | {b.pr_state} |")

        if delete_orphan:
            label = (
                f"\n### ⚠️  Orphaned Branches "
                f"(no PR, inactive ≥ {orphan_days} days) ({len(delete_orphan)})"
            )
            print(label)
            print("| Branch | Last commit |")
            print("|--------|-------------|")
            for b in sorted(delete_orphan, key=lambda x: x.name):
                days = (now - b.last_commit_date).days
                print(f"| `{b.name}` | {days} days ago |")

        if keep:
            print(f"\n### ✅ Branches to Keep ({len(keep)})")
            print("| Branch | PR # | Status |")
            print("|--------|------|--------|")
            for b in sorted(keep, key=lambda x: x.name):
                pr_num = f"#{b.pr_number}" if b.pr_number else "—"
                if b.pr_state:
                    status = b.pr_state
                else:
                    days = (now - b.last_commit_date).days
                    status = f"No PR — {days} days old"
                print(f"| `{b.name}` | {pr_num} | {status} |")

    def delete_closed_pr_branches(self) -> None:
        """Delete all branches whose PRs are merged or closed."""
        print("Scanning for branches with closed/merged PRs…\n", file=sys.stderr)
        infos = self.analyse_branches()
        targets = [b for b in infos if b.pr_state in ("MERGED", "CLOSED")]

        if not targets:
            print("No branches with closed/merged PRs found. Nothing to delete.")
            return

        print(f"Deleting {len(targets)} branches…\n")
        deleted = 0
        failed = 0
        for b in targets:
            try:
                subprocess.run(
                    ["gh", "api", "-X", "DELETE", f"repos/{self.repo}/git/refs/heads/{b.name}"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                print(f"  ✅ Deleted: {b.name}")
                deleted += 1
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Failed:  {b.name} — {e.stderr.strip()}")
                failed += 1

        print(f"\nDone. Deleted: {deleted}  Failed: {failed}")

    def delete_orphaned_branches(self, days: int = 30) -> None:
        """Delete branches with no PR that have been inactive for ≥ days."""
        print(f"Scanning for orphaned branches inactive for ≥ {days} days…\n", file=sys.stderr)
        infos = self.analyse_branches(days)
        now = datetime.now(UTC)
        targets = [
            b for b in infos if b.pr_state is None and (now - b.last_commit_date).days >= days
        ]

        if not targets:
            print(f"No orphaned branches inactive for ≥ {days} days found.")
            return

        print(f"Deleting {len(targets)} orphaned branches…\n")
        deleted = 0
        failed = 0
        for b in targets:
            try:
                subprocess.run(
                    ["gh", "api", "-X", "DELETE", f"repos/{self.repo}/git/refs/heads/{b.name}"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                print(f"  ✅ Deleted: {b.name}")
                deleted += 1
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Failed:  {b.name} — {e.stderr.strip()}")
                failed += 1

        print(f"\nDone. Deleted: {deleted}  Failed: {failed}")


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------


def main() -> None:
    """CLI entry point."""
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    command = args[0]
    manager = BranchManager()

    if command == "audit":
        orphan_days = int(args[1]) if len(args) > 1 else 30
        manager.audit(orphan_days)

    elif command == "delete-closed-pr-branches":
        manager.delete_closed_pr_branches()

    elif command == "delete-orphaned-branches":
        days = int(args[1]) if len(args) > 1 else 30
        manager.delete_orphaned_branches(days)

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
