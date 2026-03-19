#!/usr/bin/env python3
"""
🤖 Issue & Milestone Auto-Manager

Intelligent automation for GitHub issues and milestones.
Part of the Lazy Dev suite.

Features:
- Auto-create milestones from roadmap
- Smart issue labeling and assignment
- Auto-milestone assignment based on issue content
- Progress tracking and reporting
- Issue audit: detect stale, duplicate, and potentially resolved issues
- Integration with lazy_dev.py for seamless workflow

Usage:
    ./scripts/issue_manager.py auto-label <issue-number>
    ./scripts/issue_manager.py create-milestones
    ./scripts/issue_manager.py assign-milestone <issue-number>
    ./scripts/issue_manager.py progress
    ./scripts/issue_manager.py audit
    ./scripts/issue_manager.py close-stale [days]
    ./scripts/issue_manager.py close-duplicates
    ./scripts/issue_manager.py label-unlabeled
"""

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any


class IssuePriority(Enum):
    """Issue priority levels."""

    CRITICAL = "P0: Critical"
    HIGH = "P1: High"
    MEDIUM = "P2: Medium"
    LOW = "P3: Low"
    BACKLOG = "P4: Backlog"


class IssueCategory(Enum):
    """Issue categories matching TTA.dev structure."""

    PRIMITIVE = "primitive"
    OBSERVABILITY = "observability"
    TESTING = "testing"
    DOCS = "documentation"
    INFRA = "infrastructure"
    AGENT = "agent-coordination"
    MCP = "mcp-integration"
    EXAMPLE = "examples"


@dataclass
class Issue:
    """GitHub issue representation."""

    number: int
    title: str
    body: str
    labels: list[str]
    state: str
    milestone: str | None
    assignees: list[str]
    created_at: str
    updated_at: str


@dataclass
class Milestone:
    """GitHub milestone representation."""

    title: str
    description: str
    due_date: str | None
    state: str
    open_issues: int
    closed_issues: int


class IssueManager:
    """Manages GitHub issues and milestones intelligently."""

    def __init__(self):
        """Initialize issue manager."""
        self.repo = self._get_repo()

    def _get_repo(self) -> str:
        """Get repository in owner/repo format."""
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
            return "theinterneti/TTA.dev"  # Fallback

    def _run_gh(self, *args: str) -> dict[str, Any]:
        """Run gh CLI command and return JSON."""
        try:
            result = subprocess.run(
                ["gh"] + list(args),
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout) if result.stdout else {}
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr}", file=sys.stderr)
            return {}
        except json.JSONDecodeError:
            return {}

    def get_issue(self, number: int) -> Issue | None:
        """Get issue details."""
        data = self._run_gh(
            "issue",
            "view",
            str(number),
            "--json",
            "number,title,body,labels,state,milestone,assignees,createdAt,updatedAt",
        )

        if not data:
            return None

        return Issue(
            number=data.get("number", number),
            title=data.get("title", ""),
            body=data.get("body", ""),
            labels=[label["name"] for label in data.get("labels", [])],
            state=data.get("state", "OPEN"),
            milestone=data["milestone"]["title"] if data.get("milestone") else None,
            assignees=[a["login"] for a in data.get("assignees", [])],
            created_at=data.get("createdAt", ""),
            updated_at=data.get("updatedAt", ""),
        )

    def auto_label(self, issue_number: int) -> bool:
        """Automatically label issue based on content."""
        issue = self.get_issue(issue_number)
        if not issue:
            print(f"Issue #{issue_number} not found")
            return False

        # Analyze content
        content = f"{issue.title} {issue.body}".lower()
        labels_to_add = []

        # Category detection (using actual repo labels)
        if any(kw in content for kw in ["trace", "metric", "observability", "telemetry", "otel"]):
            labels_to_add.append("observability")
        if any(kw in content for kw in ["test", "coverage", "pytest", "testing"]):
            labels_to_add.append("testing")
        if any(kw in content for kw in ["doc", "documentation", "guide", "readme"]):
            labels_to_add.append("documentation")
        if any(kw in content for kw in ["performance", "speed", "optimize", "slow"]):
            labels_to_add.append("performance")
        if any(kw in content for kw in ["reliability", "stable", "crash", "failure"]):
            labels_to_add.append("reliability")
        if any(kw in content for kw in ["metric", "prometheus", "grafana"]):
            labels_to_add.append("metrics")
        if any(kw in content for kw in ["package", "dependency", "install"]):
            labels_to_add.append("package")

        # Priority detection (using actual repo labels: P0, P1, P2)
        if any(kw in content for kw in ["critical", "urgent", "blocker", "p0"]):
            labels_to_add.append("P0")
        elif any(kw in content for kw in ["important", "high priority", "p1"]):
            labels_to_add.append("P1")
        elif any(kw in content for kw in ["medium", "p2"]):
            labels_to_add.append("P2")

        # Type detection
        if any(kw in content for kw in ["bug", "error", "fix", "broken"]):
            labels_to_add.append("bug")
        elif any(kw in content for kw in ["feature", "enhancement", "add"]):
            labels_to_add.append("enhancement")

        # Apply labels
        if labels_to_add:
            # Remove existing labels that conflict
            existing = set(issue.labels)
            labels_to_add = list(set(labels_to_add) - existing)

            try:
                subprocess.run(
                    [
                        "gh",
                        "issue",
                        "edit",
                        str(issue_number),
                        "--add-label",
                        ",".join(labels_to_add),
                    ],
                    check=True,
                    capture_output=True,
                )
                print(f"✅ Auto-labeled issue #{issue_number}: {', '.join(labels_to_add)}")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Error adding labels: {e.stderr}", file=sys.stderr)
                return False

        print(f"ℹ️ No new labels needed for issue #{issue_number}")
        return True

    def create_milestones(self) -> bool:
        """Create milestones from roadmap structure."""
        # Standard TTA.dev milestones
        milestones = [
            {
                "title": "Phase 1: Core Primitives ✅",
                "description": "Foundation primitives (Sequential, Parallel, Router, Retry, Fallback, Cache)",
                "due_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                "state": "closed",
            },
            {
                "title": "Phase 2: Observability Integration",
                "description": "OpenTelemetry, Prometheus metrics, enhanced primitives",
                "due_date": datetime.now().strftime("%Y-%m-%d"),
                "state": "open",
            },
            {
                "title": "Phase 3: Examples & Production Patterns",
                "description": "RAG, Agentic RAG, Cost Tracking, Streaming, Multi-Agent workflows",
                "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "state": "open",
            },
            {
                "title": "Phase 4: Advanced Features",
                "description": "Adaptive primitives, self-improvement, advanced agent coordination",
                "due_date": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
                "state": "open",
            },
            {
                "title": "Ongoing: Documentation",
                "description": "Guides, tutorials, API docs, knowledge base maintenance",
                "due_date": None,
                "state": "open",
            },
            {
                "title": "Ongoing: Testing & Quality",
                "description": "Test coverage, integration tests, quality improvements",
                "due_date": None,
                "state": "open",
            },
        ]

        created_count = 0
        for milestone in milestones:
            try:
                # Check if milestone exists
                # Escape double quotes in milestone title for jq
                milestone_title_escaped = milestone["title"].replace('"', '\\"')
                result = subprocess.run(
                    [
                        "gh",
                        "api",
                        f"/repos/{self.repo}/milestones",
                        "--jq",
                        f'.[] | select(.title == "{milestone_title_escaped}") | .number',
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.stdout.strip():
                    print(f"ℹ️ Milestone already exists: {milestone['title']}")
                    continue

                # Create milestone
                cmd = [
                    "gh",
                    "api",
                    f"/repos/{self.repo}/milestones",
                    "-f",
                    f"title={milestone['title']}",
                    "-f",
                    f"description={milestone['description']}",
                    "-f",
                    f"state={milestone['state']}",
                ]

                if milestone["due_date"]:
                    cmd.extend(["-f", f"due_on={milestone['due_date']}T00:00:00Z"])

                subprocess.run(cmd, check=True, capture_output=True)
                print(f"✅ Created milestone: {milestone['title']}")
                created_count += 1

            except subprocess.CalledProcessError as e:
                print(f"Error creating milestone {milestone['title']}: {e.stderr}", file=sys.stderr)

        if created_count > 0:
            print(f"\n🎉 Created {created_count} new milestones")
        return True

    def assign_milestone(self, issue_number: int) -> bool:
        """Auto-assign milestone based on issue labels and content."""
        issue = self.get_issue(issue_number)
        if not issue:
            print(f"Issue #{issue_number} not found")
            return False

        # Already has milestone?
        if issue.milestone:
            print(f"ℹ️ Issue #{issue_number} already assigned to: {issue.milestone}")
            return True

        # Determine milestone based on labels/content
        content = f"{issue.title} {issue.body} {' '.join(issue.labels)}".lower()
        milestone_title = None

        if "primitive" in content and any(kw in content for kw in ["new", "feature", "add"]):
            milestone_title = "Phase 4: Advanced Features"
        elif "observability" in content:
            milestone_title = "Phase 2: Observability Integration"
        elif "example" in content or "pattern" in content:
            milestone_title = "Phase 3: Examples & Production Patterns"
        elif "documentation" in content or "guide" in content:
            milestone_title = "Ongoing: Documentation"
        elif "test" in content or "coverage" in content:
            milestone_title = "Ongoing: Testing & Quality"

        if milestone_title:
            try:
                subprocess.run(
                    ["gh", "issue", "edit", str(issue_number), "--milestone", milestone_title],
                    check=True,
                    capture_output=True,
                )
                print(f"✅ Assigned issue #{issue_number} to milestone: {milestone_title}")
                return True
            except subprocess.CalledProcessError as e:
                print(f"Error assigning milestone: {e.stderr}", file=sys.stderr)
                return False

        print(f"ℹ️ Could not determine milestone for issue #{issue_number}")
        return True

    def generate_logseq_todo(self, issue_number: int) -> str | None:
        """
        Generate a Logseq-formatted TODO string for a GitHub issue.
        """
        issue = self.get_issue(issue_number)
        if not issue:
            print(f"Issue #{issue_number} not found")
            return None

        # Map GitHub labels to Logseq priorities
        priority_map = {
            "P0": "high",
            "P1": "high",
            "P2": "medium",
            "P3": "low",
            "critical": "high",
            "urgent": "high",
        }

        # Determine priority
        priority = "medium"
        for label in issue.labels:
            if label in priority_map:
                priority = priority_map[label]
                break

        # Determine type based on labels
        todo_type = "implementation"
        if "documentation" in issue.labels:
            todo_type = "documentation"
        elif "bug" in issue.labels:
            todo_type = "bugfix"
        elif "testing" in issue.labels:
            todo_type = "testing"
        elif "observability" in issue.labels:
            todo_type = "observability"

        # Build the Logseq block
        # Format: - TODO Title #tags
        # Filter out P-labels for tags to avoid redundancy with priority property
        tags = [f"#{label}" for label in issue.labels if not label.startswith("P")]
        tags_str = " ".join(tags)

        lines = [
            f"- TODO {issue.title} {tags_str} #dev-todo",
            f"  issue:: #{issue.number}",
            f"  type:: {todo_type}",
            f"  priority:: {priority}",
            f"  status:: {issue.state.lower()}",
            f"  url:: https://github.com/{self.repo}/issues/{issue.number}",
        ]

        if issue.milestone:
            lines.append(f"  milestone:: [[{issue.milestone}]]")

        if issue.assignees:
            assignees_str = ", ".join([f"[[@{a}]]" for a in issue.assignees])
            lines.append(f"  assigned:: {assignees_str}")

        return "\n".join(lines)

    def _list_open_issues(self) -> list[Issue]:
        """Fetch all open issues from the repository."""
        issues: list[Issue] = []
        page = 1
        while True:
            try:
                result = subprocess.run(
                    [
                        "gh",
                        "issue",
                        "list",
                        "--repo",
                        self.repo,
                        "--state",
                        "open",
                        "--limit",
                        "100",
                        "--json",
                        "number,title,body,labels,state,milestone,assignees,createdAt,updatedAt",
                        "--jq",
                        ".",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    encoding="utf-8",
                )
                data = json.loads(result.stdout) if result.stdout else []
                for item in data:
                    issues.append(
                        Issue(
                            number=item.get("number", 0),
                            title=item.get("title", ""),
                            body=item.get("body", "") or "",
                            labels=[lb["name"] for lb in item.get("labels", [])],
                            state=item.get("state", "OPEN"),
                            milestone=(
                                item["milestone"]["title"] if item.get("milestone") else None
                            ),
                            assignees=[a["login"] for a in item.get("assignees", [])],
                            created_at=item.get("createdAt", ""),
                            updated_at=item.get("updatedAt", ""),
                        )
                    )
                break  # gh issue list returns all matching in one call
            except (subprocess.CalledProcessError, json.JSONDecodeError):
                break
            page += 1
        return issues

    def _detect_duplicates(self, issues: list[Issue]) -> list[tuple[Issue, Issue]]:
        """Detect issues that are likely duplicates based on title similarity."""
        from difflib import SequenceMatcher

        duplicates: list[tuple[Issue, Issue]] = []
        threshold = 0.85
        for i, a in enumerate(issues):
            for b in issues[i + 1 :]:
                title_a = re.sub(r"[^a-z0-9 ]", "", a.title.lower()).strip()
                title_b = re.sub(r"[^a-z0-9 ]", "", b.title.lower()).strip()
                ratio = SequenceMatcher(None, title_a, title_b).ratio()
                if ratio >= threshold:
                    duplicates.append((a, b))
        return duplicates

    def _detect_stale(self, issues: list[Issue], stale_days: int = 90) -> list[Issue]:
        """Detect issues that have had no activity for *stale_days*."""
        cutoff = datetime.now(UTC) - timedelta(days=stale_days)
        stale: list[Issue] = []
        for issue in issues:
            updated = issue.updated_at
            if not updated:
                stale.append(issue)
                continue
            try:
                updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                if updated_dt < cutoff:
                    stale.append(issue)
            except ValueError:
                stale.append(issue)
        return stale

    def _detect_potentially_resolved(self, issues: list[Issue]) -> list[Issue]:
        """Detect issues whose title mentions a path that already exists.

        This is a heuristic: an issue is flagged if *any* referenced path
        exists, even when the issue mentions multiple deliverables.  Manual
        verification is still required before closing.
        """
        repo_root = Path(__file__).resolve().parent.parent
        resolved: list[Issue] = []
        pattern = re.compile(r"create\s+`?([a-zA-Z0-9_./-]+/?)`?", re.IGNORECASE)
        for issue in issues:
            content = f"{issue.title} {issue.body}"
            matches = pattern.findall(content)
            if any((repo_root / match).exists() for match in matches):
                resolved.append(issue)
        return resolved

    def audit(self, stale_days: int = 90) -> None:
        """Run a comprehensive issue audit and print a report."""

        def _trunc(text: str, width: int = 65) -> str:
            return text if len(text) <= width else text[: width - 3] + "..."

        print("\n🔍 Issue Audit Report")
        print("=" * 80)
        print(f"Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"Staleness threshold: {stale_days} days\n")

        issues = self._list_open_issues()
        if not issues:
            print("No open issues found (or unable to fetch issues).")
            return

        print(f"📋 Total open issues: {len(issues)}\n")

        # --- Duplicates ---
        duplicates = self._detect_duplicates(issues)
        print("-" * 80)
        print(f"🔁 Duplicate Issues ({len(duplicates)} pair(s) found)\n")
        if duplicates:
            for a, b in duplicates:
                print(f'  #{a.number} ↔ #{b.number}  "{_trunc(a.title, 60)}"')
            print("\n  ➡️  Action: close the duplicate and reference the original in a comment.\n")
        else:
            print("  None detected.\n")

        # --- Stale ---
        stale = self._detect_stale(issues, stale_days)
        exempt_labels = {"pinned", "priority: critical", "priority: high", "production-readiness"}
        actionable_stale = [i for i in stale if not set(i.labels) & exempt_labels]
        print("-" * 80)
        print(
            f"⏰ Stale Issues — no activity for {stale_days}+ days "
            f"({len(actionable_stale)} actionable, {len(stale)} total)\n"
        )
        for issue in actionable_stale:
            labels = ", ".join(issue.labels) if issue.labels else "none"
            print(f"  #{issue.number:>4}  {_trunc(issue.title)}")
            print(f"         Labels: {labels}  |  Updated: {issue.updated_at[:10]}")
        if actionable_stale:
            print(
                "\n  ➡️  Action: review each issue — close if no longer "
                "relevant, or comment to keep alive.\n"
            )
        else:
            print("  None detected.\n")

        # --- Potentially Resolved ---
        resolved = self._detect_potentially_resolved(issues)
        print("-" * 80)
        print(f"✅ Potentially Resolved Issues ({len(resolved)} found)\n")
        for issue in resolved:
            print(f"  #{issue.number:>4}  {_trunc(issue.title, 70)}")
        if resolved:
            print("\n  ➡️  Action: verify completion and close with a summary comment.\n")
        else:
            print("  None detected.\n")

        # --- Issues without labels ---
        unlabeled = [i for i in issues if not i.labels]
        print("-" * 80)
        print(f"🏷️  Unlabeled Issues ({len(unlabeled)} found)\n")
        for issue in unlabeled:
            print(f"  #{issue.number:>4}  {_trunc(issue.title, 70)}")
        if unlabeled:
            print(
                "\n  ➡️  Action: add appropriate labels or run "
                "`issue_manager.py auto-label <number>`.\n"
            )
        else:
            print("  None detected.\n")

        # --- Summary ---
        print("=" * 80)
        print("📊 Audit Summary\n")
        print(f"  Total open issues:       {len(issues)}")
        print(f"  Duplicate pairs:         {len(duplicates)}")
        print(f"  Stale (actionable):      {len(actionable_stale)}")
        print(f"  Potentially resolved:    {len(resolved)}")
        print(f"  Unlabeled:               {len(unlabeled)}")
        cleanup = len(duplicates) + len(actionable_stale) + len(resolved)
        print(f"  Estimated cleanup:       ~{cleanup} issues")
        print()

    # ------------------------------------------------------------------
    # Write operations — require GH_TOKEN with issues:write permission
    # ------------------------------------------------------------------

    def _close_issue(self, number: int, comment: str) -> bool:
        """Close an issue with a comment explaining why."""
        try:
            subprocess.run(
                [
                    "gh",
                    "issue",
                    "comment",
                    str(number),
                    "--repo",
                    self.repo,
                    "--body",
                    comment,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [
                    "gh",
                    "issue",
                    "close",
                    str(number),
                    "--repo",
                    self.repo,
                    "--reason",
                    "not planned",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to close #{number}: {e.stderr or 'unknown error'}", file=sys.stderr)
            return False

    def close_stale(self, stale_days: int = 90) -> None:
        """Close stale issues that have had no activity."""
        issues = self._list_open_issues()
        stale = self._detect_stale(issues, stale_days)
        exempt_labels = {
            "pinned",
            "priority: critical",
            "priority: high",
            "production-readiness",
        }
        actionable = [i for i in stale if not set(i.labels) & exempt_labels]

        if not actionable:
            print("No actionable stale issues found.")
            return

        print(f"Closing {len(actionable)} stale issues (>{stale_days} days)...\n")
        closed = 0
        for issue in actionable:
            comment = (
                f"🤖 **Automated issue audit**\n\n"
                f"This issue has had no activity for over {stale_days} days "
                f"and does not carry a high-priority or production-readiness "
                f"label.\n\nClosing as stale. "
                f"Please reopen if this work is still needed."
            )
            if self._close_issue(issue.number, comment):
                print(f"  ✅ Closed #{issue.number}: {issue.title[:60]}")
                closed += 1

        print(f"\n🎉 Closed {closed}/{len(actionable)} stale issues.")

    def close_duplicates(self) -> None:
        """Close duplicate issues, keeping the lower-numbered original."""
        issues = self._list_open_issues()
        duplicates = self._detect_duplicates(issues)

        if not duplicates:
            print("No duplicate issues found.")
            return

        print(f"Closing {len(duplicates)} duplicate issue(s)...\n")
        closed = 0
        for original, dupe in duplicates:
            comment = (
                f"🤖 **Automated issue audit**\n\n"
                f"This issue appears to be a duplicate of #{original.number}.\n\n"
                f"Closing in favor of the original. "
                f"Please reopen if this is intentionally distinct."
            )
            if self._close_issue(dupe.number, comment):
                print(f"  ✅ Closed #{dupe.number} (duplicate of #{original.number})")
                closed += 1

        print(f"\n🎉 Closed {closed}/{len(duplicates)} duplicate issues.")

    def label_unlabeled(self) -> None:
        """Auto-label all unlabeled open issues."""
        issues = self._list_open_issues()
        unlabeled = [i for i in issues if not i.labels]

        if not unlabeled:
            print("No unlabeled issues found.")
            return

        print(f"Auto-labeling {len(unlabeled)} unlabeled issues...\n")
        labeled = 0
        for issue in unlabeled:
            if self.auto_label(issue.number):
                labeled += 1

        print(f"\n🎉 Labeled {labeled}/{len(unlabeled)} issues.")

    def show_progress(self) -> None:
        """Show milestone progress dashboard."""
        try:
            result = subprocess.run(
                [
                    "gh",
                    "api",
                    f"/repos/{self.repo}/milestones",
                    "--jq",
                    ".[] | {title, open_issues, closed_issues, state, due_on}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            print("\n📊 Milestone Progress Dashboard\n")
            print("=" * 80)

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                try:
                    milestone = json.loads(line)
                    title = milestone.get("title", "Unknown")
                    open_issues = milestone.get("open_issues", 0)
                    closed_issues = milestone.get("closed_issues", 0)
                    total = open_issues + closed_issues
                    state = milestone.get("state", "open")
                    due_date = milestone.get("due_on", "No deadline")

                    if total > 0:
                        progress = (closed_issues / total) * 100
                        bar_length = 40
                        filled = int((progress / 100) * bar_length)
                        bar = "█" * filled + "░" * (bar_length - filled)
                    else:
                        progress = 0
                        bar = "░" * 40

                    status_icon = "✅" if state == "closed" else "🚧"

                    print(f"\n{status_icon} {title}")
                    print(f"   Progress: [{bar}] {progress:.1f}%")
                    print(f"   Issues: {closed_issues}/{total} completed ({open_issues} open)")
                    if due_date and due_date != "No deadline":
                        due = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
                        print(f"   Due: {due.strftime('%Y-%m-%d')}")

                except json.JSONDecodeError:
                    continue

            print("\n" + "=" * 80)

        except subprocess.CalledProcessError as e:
            print(f"Error fetching milestones: {e.stderr}", file=sys.stderr)


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    manager = IssueManager()
    command = sys.argv[1]

    if command == "auto-label":
        if len(sys.argv) < 3:
            print("Usage: ./scripts/issue_manager.py auto-label <issue-number>")
            sys.exit(1)
        issue_number = int(sys.argv[2])
        success = manager.auto_label(issue_number)
        sys.exit(0 if success else 1)

    elif command == "create-milestones":
        success = manager.create_milestones()
        sys.exit(0 if success else 1)

    elif command == "assign-milestone":
        if len(sys.argv) < 3:
            print("Usage: ./scripts/issue_manager.py assign-milestone <issue-number>")
            sys.exit(1)
        issue_number = int(sys.argv[2])
        success = manager.assign_milestone(issue_number)
        sys.exit(0 if success else 1)

    elif command == "logseq-todo":
        if len(sys.argv) < 3:
            print("Usage: ./scripts/issue_manager.py logseq-todo <issue-number>")
            sys.exit(1)
        issue_number = int(sys.argv[2])
        todo_block = manager.generate_logseq_todo(issue_number)
        if todo_block:
            print(todo_block)
            sys.exit(0)
        else:
            sys.exit(1)

    elif command == "progress":
        manager.show_progress()
        sys.exit(0)

    elif command == "audit":
        stale_days = int(sys.argv[2]) if len(sys.argv) >= 3 else 90
        manager.audit(stale_days)
        sys.exit(0)

    elif command == "close-stale":
        stale_days = int(sys.argv[2]) if len(sys.argv) >= 3 else 90
        manager.close_stale(stale_days)
        sys.exit(0)

    elif command == "close-duplicates":
        manager.close_duplicates()
        sys.exit(0)

    elif command == "label-unlabeled":
        manager.label_unlabeled()
        sys.exit(0)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
