#!/usr/bin/env python3
"""
Intelligent PR Management Tool for TTA.dev

Provides comprehensive PR management capabilities including:
- PR dashboard with visual status overview
- Analytics (age, activity, review status, CI status)
- Smart prioritization based on urgency and impact
- Automated triage and categorization
- Health monitoring and actionable recommendations
- Integration with Logseq TODO system

Usage:
    python scripts/pr_manager.py dashboard
    python scripts/pr_manager.py analyze
    python scripts/pr_manager.py triage
    python scripts/pr_manager.py health-check
    python scripts/pr_manager.py recommend
"""

import asyncio
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

# Type for PR data
PRData = dict[str, Any]


class PRManager:
    """Intelligent PR management for TTA.dev repository."""

    def __init__(self, repo: str = "theinterneti/TTA.dev"):
        """
        Initialize PR manager.

        Args:
            repo: GitHub repository in format "owner/repo"
        """
        self.repo = repo
        self.repo_root = Path(__file__).parent.parent

    async def get_open_prs(self) -> list[PRData]:
        """
        Fetch all open PRs from GitHub.

        Returns:
            List of PR data dictionaries

        Example:
            >>> manager = PRManager()
            >>> prs = await manager.get_open_prs()
            >>> print(f"Found {len(prs)} open PRs")
        """
        cmd = [
            "gh",
            "pr",
            "list",
            "--repo",
            self.repo,
            "--json",
            "number,title,author,createdAt,updatedAt,state,isDraft,"
            "reviewDecision,statusCheckRollup,labels,additions,deletions,"
            "changedFiles,comments,reviews",
            "--limit",
            "100",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    async def get_pr_checks(self, pr_number: int) -> dict[str, Any]:
        """
        Get CI/CD check status for a PR.

        Args:
            pr_number: Pull request number

        Returns:
            Dictionary with check status information
        """
        cmd = [
            "gh",
            "pr",
            "checks",
            str(pr_number),
            "--repo",
            self.repo,
            "--json",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (subprocess.SubprocessError, json.JSONDecodeError):
            pass

        return {}

    def calculate_pr_age(self, created_at: str) -> timedelta:
        """
        Calculate how old a PR is.

        Args:
            created_at: ISO 8601 timestamp of PR creation

        Returns:
            Timedelta representing PR age
        """
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        now = datetime.now(UTC)
        return now - created

    def calculate_pr_staleness(self, updated_at: str) -> timedelta:
        """
        Calculate how long since PR was last updated.

        Args:
            updated_at: ISO 8601 timestamp of last update

        Returns:
            Timedelta representing staleness
        """
        updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        now = datetime.now(UTC)
        return now - updated

    def categorize_pr(self, pr: PRData) -> str:
        """
        Categorize PR based on its properties.

        Args:
            pr: PR data dictionary

        Returns:
            Category string (critical, needs-review, stale, draft, etc.)

        Example:
            >>> manager = PRManager()
            >>> category = manager.categorize_pr(pr_data)
            >>> print(f"PR category: {category}")
        """
        age = self.calculate_pr_age(pr["createdAt"])
        staleness = self.calculate_pr_staleness(pr["updatedAt"])

        # Critical: has label "critical" or "urgent"
        labels = [label["name"] for label in pr.get("labels", [])]
        if any(label in ["critical", "urgent", "hotfix"] for label in labels):
            return "🔴 critical"

        # Draft PRs
        if pr.get("isDraft", False):
            return "📝 draft"

        # Stale: no activity in 7+ days (check before review status)
        if staleness.days >= 7:
            return "🕸️ stale"

        # Old: open for 14+ days (check before review status)
        if age.days >= 14:
            return "⏳ old"

        # Changes requested
        if pr.get("reviewDecision") == "CHANGES_REQUESTED":
            return "🔧 changes-requested"

        # Approved and passing checks
        if pr.get("reviewDecision") == "APPROVED":
            checks = pr.get("statusCheckRollup", [])
            if checks and all(check.get("conclusion") == "SUCCESS" for check in checks):
                return "✅ ready-to-merge"
            return "⚠️ approved-failing-checks"

        # Needs review: no review decision yet and not draft
        if pr.get("reviewDecision") is None and not pr.get("isDraft", False):
            return "👀 needs-review"

        # Active
        return "🟢 active"

    def prioritize_pr(self, pr: PRData) -> int:
        """
        Calculate priority score for a PR (higher = more urgent).

        Args:
            pr: PR data dictionary

        Returns:
            Priority score (0-100)

        Scoring factors:
        - Critical label: +50
        - Changes large codebase: +20
        - Review approved: +15
        - Passing CI: +10
        - Recent activity: +10
        - Has many comments: +5
        - Old age penalty: -5 per week
        """
        score = 50  # Base score

        # Labels
        labels = [label["name"] for label in pr.get("labels", [])]
        if any(label in ["critical", "urgent", "hotfix"] for label in labels):
            score += 50
        if "dependencies" in labels:
            score += 20
        if "security" in labels:
            score += 30

        # Size impact
        additions = pr.get("additions", 0)
        deletions = pr.get("deletions", 0)
        total_changes = additions + deletions
        if total_changes > 500:
            score += 20
        elif total_changes > 100:
            score += 10

        # Review status
        if pr.get("reviewDecision") == "APPROVED":
            score += 15

        # CI status
        checks = pr.get("statusCheckRollup", [])
        if checks and all(check.get("conclusion") == "SUCCESS" for check in checks):
            score += 10

        # Activity
        staleness = self.calculate_pr_staleness(pr["updatedAt"])
        if staleness.days < 1:
            score += 10
        elif staleness.days > 7:
            score -= 10

        # Engagement
        num_comments = len(pr.get("comments", []))
        num_reviews = len(pr.get("reviews", []))
        if num_comments + num_reviews > 5:
            score += 5

        # Age penalty
        age = self.calculate_pr_age(pr["createdAt"])
        weeks_old = age.days // 7
        score -= weeks_old * 5

        return max(0, min(100, score))

    def get_recommendations(self, pr: PRData) -> list[str]:
        """
        Generate actionable recommendations for a PR.

        Args:
            pr: PR data dictionary

        Returns:
            List of recommendation strings
        """
        recommendations = []
        category = self.categorize_pr(pr)
        age = self.calculate_pr_age(pr["createdAt"])
        staleness = self.calculate_pr_staleness(pr["updatedAt"])

        # Ready to merge
        if category == "✅ ready-to-merge":
            recommendations.append("🚀 Ready to merge! Consider merging soon.")

        # Needs review
        if category == "👀 needs-review":
            if age.days < 2:
                recommendations.append("⏱️ New PR - assign reviewers")
            else:
                recommendations.append("👥 Waiting for review - ping reviewers?")

        # Changes requested
        if category == "🔧 changes-requested":
            if staleness.days > 3:
                recommendations.append("📢 Address requested changes or respond")

        # Stale
        if staleness.days >= 7:
            recommendations.append(
                f"🕸️ No activity for {staleness.days} days - close or reactivate?"
            )

        # Old
        if age.days >= 14:
            recommendations.append(
                f"⏳ Open for {age.days} days - consider prioritizing or closing"
            )

        # Large PRs
        total_changes = pr.get("additions", 0) + pr.get("deletions", 0)
        if total_changes > 1000:
            recommendations.append("📏 Large PR - consider breaking into smaller PRs")

        # Draft with no recent activity
        if pr.get("isDraft", False) and staleness.days >= 3:
            recommendations.append("📝 Draft with no recent activity - still needed?")

        # Failing checks
        checks = pr.get("statusCheckRollup", [])
        failed_checks = [
            check
            for check in checks
            if check.get("conclusion") in ["FAILURE", "CANCELLED", "TIMED_OUT"]
        ]
        if failed_checks:
            recommendations.append(f"❌ {len(failed_checks)} failing check(s) - fix before merge")

        return recommendations if recommendations else ["✨ Looking good!"]

    async def display_dashboard(self) -> None:
        """
        Display interactive PR dashboard.

        Shows overview of all open PRs with key metrics and status.
        """
        print("📊 TTA.dev PR Dashboard\n")
        print("=" * 80)

        prs = await self.get_open_prs()

        if not prs:
            print("\n✅ No open PRs! All clear.\n")
            return

        # Summary statistics
        print(f"\n📈 Summary: {len(prs)} open PRs\n")

        # Categorize all PRs
        categories: dict[str, list[PRData]] = {}
        for pr in prs:
            category = self.categorize_pr(pr)
            if category not in categories:
                categories[category] = []
            categories[category].append(pr)

        # Display by category
        category_order = [
            "🔴 critical",
            "✅ ready-to-merge",
            "⚠️ approved-failing-checks",
            "🔧 changes-requested",
            "👀 needs-review",
            "📝 draft",
            "🕸️ stale",
            "⏳ old",
            "🟢 active",
        ]

        for category in category_order:
            if category not in categories:
                continue

            print(f"\n{category.upper()} ({len(categories[category])})")
            print("-" * 80)

            # Sort by priority within category
            sorted_prs = sorted(
                categories[category],
                key=lambda p: self.prioritize_pr(p),
                reverse=True,
            )

            for pr in sorted_prs:
                age = self.calculate_pr_age(pr["createdAt"])
                priority = self.prioritize_pr(pr)
                author = pr["author"]["login"]

                print(
                    f"  #{pr['number']:4d} | P{priority:3d} | "
                    f"{age.days:2d}d | @{author:15s} | {pr['title']}"
                )

        print("\n" + "=" * 80)

    async def analyze_prs(self) -> None:
        """
        Perform detailed analysis on all open PRs.

        Shows metrics, trends, and insights.
        """
        print("🔍 PR Analysis\n")
        print("=" * 80)

        prs = await self.get_open_prs()

        if not prs:
            print("\n✅ No open PRs to analyze.\n")
            return

        # Age analysis
        ages = [self.calculate_pr_age(pr["createdAt"]).days for pr in prs]
        avg_age = sum(ages) / len(ages)
        max_age = max(ages)
        min_age = min(ages)

        print("\n📅 Age Metrics:")
        print(f"  Average age: {avg_age:.1f} days")
        print(f"  Oldest PR: {max_age} days")
        print(f"  Newest PR: {min_age} days")

        # Activity analysis
        staleness_values = [self.calculate_pr_staleness(pr["updatedAt"]).days for pr in prs]
        avg_staleness = sum(staleness_values) / len(staleness_values)
        stale_count = sum(1 for s in staleness_values if s >= 7)

        print("\n💤 Activity Metrics:")
        print(f"  Average staleness: {avg_staleness:.1f} days")
        print(f"  Stale PRs (7+ days): {stale_count}")

        # Review status
        approved = sum(1 for pr in prs if pr.get("reviewDecision") == "APPROVED")
        changes_requested = sum(1 for pr in prs if pr.get("reviewDecision") == "CHANGES_REQUESTED")
        no_review = sum(1 for pr in prs if pr.get("reviewDecision") is None)

        print("\n👥 Review Status:")
        print(f"  Approved: {approved}")
        print(f"  Changes requested: {changes_requested}")
        print(f"  No review yet: {no_review}")

        # Draft status
        draft_count = sum(1 for pr in prs if pr.get("isDraft", False))
        print(f"\n📝 Draft PRs: {draft_count}")

        # Size metrics
        total_additions = sum(pr.get("additions", 0) for pr in prs)
        total_deletions = sum(pr.get("deletions", 0) for pr in prs)
        total_files = sum(pr.get("changedFiles", 0) for pr in prs)

        print("\n📏 Size Metrics:")
        print(f"  Total additions: {total_additions:,}")
        print(f"  Total deletions: {total_deletions:,}")
        print(f"  Total files changed: {total_files:,}")

        # Priority distribution
        priorities = [self.prioritize_pr(pr) for pr in prs]
        high_priority = sum(1 for p in priorities if p >= 70)
        medium_priority = sum(1 for p in priorities if 40 <= p < 70)
        low_priority = sum(1 for p in priorities if p < 40)

        print("\n🎯 Priority Distribution:")
        print(f"  High (70+): {high_priority}")
        print(f"  Medium (40-69): {medium_priority}")
        print(f"  Low (<40): {low_priority}")

        print("\n" + "=" * 80)

    async def triage_prs(self) -> None:
        """
        Automatically triage all open PRs.

        Categorizes and prioritizes PRs with actionable insights.
        """
        print("🏥 PR Triage\n")
        print("=" * 80)

        prs = await self.get_open_prs()

        if not prs:
            print("\n✅ No PRs to triage.\n")
            return

        # Sort by priority
        sorted_prs = sorted(prs, key=lambda p: self.prioritize_pr(p), reverse=True)

        for pr in sorted_prs:
            category = self.categorize_pr(pr)
            priority = self.prioritize_pr(pr)
            age = self.calculate_pr_age(pr["createdAt"])
            staleness = self.calculate_pr_staleness(pr["updatedAt"])
            author = pr["author"]["login"]

            print(f"\n{category} | Priority: {priority}")
            print(f"  PR #{pr['number']}: {pr['title']}")
            print(f"  Author: @{author}")
            print(f"  Age: {age.days} days | Last activity: {staleness.days} days ago")

            # Show recommendations
            recommendations = self.get_recommendations(pr)
            for rec in recommendations:
                print(f"  → {rec}")

            # Show labels
            labels = [label["name"] for label in pr.get("labels", [])]
            if labels:
                print(f"  🏷️ Labels: {', '.join(labels)}")

            print("-" * 80)

        print()

    async def health_check(self) -> None:
        """
        Perform health check on all open PRs.

        Identifies PRs that need attention or action.
        """
        print("🏥 PR Health Check\n")
        print("=" * 80)

        prs = await self.get_open_prs()

        if not prs:
            print("\n✅ No PRs to check.\n")
            return

        # Identify issues
        issues_found = False

        # Check for very old PRs
        old_prs = [pr for pr in prs if self.calculate_pr_age(pr["createdAt"]).days >= 30]
        if old_prs:
            issues_found = True
            print(f"\n⚠️ Very Old PRs ({len(old_prs)}):")
            for pr in old_prs:
                age = self.calculate_pr_age(pr["createdAt"]).days
                print(f"  #{pr['number']}: {pr['title']} ({age} days old)")

        # Check for stale PRs
        stale_prs = [pr for pr in prs if self.calculate_pr_staleness(pr["updatedAt"]).days >= 14]
        if stale_prs:
            issues_found = True
            print(f"\n🕸️ Very Stale PRs ({len(stale_prs)}):")
            for pr in stale_prs:
                staleness = self.calculate_pr_staleness(pr["updatedAt"]).days
                print(f"  #{pr['number']}: {pr['title']} (no activity for {staleness} days)")

        # Check for approved but not merged
        approved_not_merged = [pr for pr in prs if pr.get("reviewDecision") == "APPROVED"]
        if approved_not_merged:
            issues_found = True
            print(f"\n✅ Approved but Not Merged ({len(approved_not_merged)}):")
            for pr in approved_not_merged:
                print(f"  #{pr['number']}: {pr['title']}")

        # Check for PRs with many changes requested
        changes_requested = [pr for pr in prs if pr.get("reviewDecision") == "CHANGES_REQUESTED"]
        if changes_requested:
            issues_found = True
            print(f"\n🔧 Changes Requested ({len(changes_requested)}):")
            for pr in changes_requested:
                staleness = self.calculate_pr_staleness(pr["updatedAt"]).days
                print(f"  #{pr['number']}: {pr['title']} (last activity {staleness}d ago)")

        # Check for very large PRs
        large_prs = [pr for pr in prs if pr.get("additions", 0) + pr.get("deletions", 0) > 1000]
        if large_prs:
            issues_found = True
            print(f"\n📏 Very Large PRs ({len(large_prs)}):")
            for pr in large_prs:
                changes = pr.get("additions", 0) + pr.get("deletions", 0)
                print(f"  #{pr['number']}: {pr['title']} ({changes:,} changes)")

        if not issues_found:
            print("\n✅ All PRs look healthy!\n")
        else:
            print("\n" + "=" * 80)

    async def recommend_actions(self) -> None:
        """
        Provide comprehensive recommendations for all PRs.

        Generates actionable next steps for each PR.
        """
        print("💡 PR Recommendations\n")
        print("=" * 80)

        prs = await self.get_open_prs()

        if not prs:
            print("\n✅ No PRs to review.\n")
            return

        # Group by action type
        merge_ready = []
        needs_review = []
        needs_changes = []
        consider_closing = []

        for pr in prs:
            category = self.categorize_pr(pr)

            if category == "✅ ready-to-merge":
                merge_ready.append(pr)
            elif category in ["👀 needs-review", "🟢 active"]:
                needs_review.append(pr)
            elif category == "🔧 changes-requested":
                needs_changes.append(pr)
            elif category in ["🕸️ stale", "⏳ old"]:
                staleness = self.calculate_pr_staleness(pr["updatedAt"])
                if staleness.days >= 30:
                    consider_closing.append(pr)

        # Display recommendations
        if merge_ready:
            print(f"\n🚀 Ready to Merge ({len(merge_ready)}):")
            for pr in sorted(merge_ready, key=lambda p: self.prioritize_pr(p), reverse=True):
                print(f"  ✅ Merge PR #{pr['number']}: {pr['title']}")

        if needs_review:
            print(f"\n👀 Needs Review ({len(needs_review)}):")
            for pr in sorted(needs_review, key=lambda p: self.prioritize_pr(p), reverse=True):
                age = self.calculate_pr_age(pr["createdAt"]).days
                print(f"  👥 Review PR #{pr['number']}: {pr['title']} ({age}d old)")

        if needs_changes:
            print(f"\n🔧 Needs Changes ({len(needs_changes)}):")
            for pr in needs_changes:
                staleness = self.calculate_pr_staleness(pr["updatedAt"]).days
                print(f"  📝 Follow up on PR #{pr['number']}: {pr['title']} (waiting {staleness}d)")

        if consider_closing:
            print(f"\n🗑️ Consider Closing ({len(consider_closing)}):")
            for pr in consider_closing:
                staleness = self.calculate_pr_staleness(pr["updatedAt"]).days
                print(f"  ⏹️ Close PR #{pr['number']}: {pr['title']} (inactive {staleness}d)")

        print("\n" + "=" * 80)


async def main() -> None:
    """Main entry point for PR management tool."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/pr_manager.py <command>")
        print("\nCommands:")
        print("  dashboard     - Show PR dashboard")
        print("  analyze       - Analyze PR metrics")
        print("  triage        - Triage all PRs")
        print("  health-check  - Check PR health")
        print("  recommend     - Get PR recommendations")
        sys.exit(1)

    command = sys.argv[1]
    manager = PRManager()

    if command == "dashboard":
        await manager.display_dashboard()
    elif command == "analyze":
        await manager.analyze_prs()
    elif command == "triage":
        await manager.triage_prs()
    elif command == "health-check":
        await manager.health_check()
    elif command == "recommend":
        await manager.recommend_actions()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
