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
- Integration with lazy_dev.py for seamless workflow

Usage:
    ./scripts/issue_manager.py auto-label <issue-number>
    ./scripts/issue_manager.py create-milestones
    ./scripts/issue_manager.py assign-milestone <issue-number>
    ./scripts/issue_manager.py logseq-todo <issue-number>
    ./scripts/issue_manager.py progress
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
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
            new_labels = existing.union(set(labels_to_add))

            try:
                subprocess.run(
                    ["gh", "issue", "edit", str(issue_number), "--add-label", ",".join(labels_to_add)],
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
                    ["gh", "api", f"/repos/{self.repo}/milestones", "--jq", f'.[] | select(.title == "{milestone_title_escaped}") | .number'],
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

        Follows the convention defined in .github/instructions/logseq-knowledge-base.instructions.md
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
        tags = [f"#{l}" for l in issue.labels if not l.startswith("P")]
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

    def show_progress(self) -> None:
        """Show milestone progress dashboard."""
        try:
            result = subprocess.run(
                ["gh", "api", f"/repos/{self.repo}/milestones", "--jq", ".[] | {title, open_issues, closed_issues, state, due_on}"],
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

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
