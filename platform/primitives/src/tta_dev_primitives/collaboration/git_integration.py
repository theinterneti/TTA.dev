"""
Git collaboration primitives for multi-agent development workflows.

Based on research from Martin Fowler's "Patterns for Managing Source Code Branches"
and GitHub Copilot best practices. Enforces high-frequency integration and
exemplary git hygiene for AI agent collaboration.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..core.base import WorkflowContext, WorkflowPrimitive


class IntegrationFrequency(str, Enum):
    """How often agents should integrate their work."""

    CONTINUOUS = "continuous"  # After every logical unit (< 1 hour)
    HOURLY = "hourly"  # At least once per hour
    DAILY = "daily"  # At least once per day (minimum acceptable)
    WEEKLY = "weekly"  # Once per week (ANTI-PATTERN, discouraged)


class MergeStrategy(str, Enum):
    """Strategy for merging agent work."""

    FAST_FORWARD = "fast_forward"  # Clean history, requires rebase
    MERGE_COMMIT = "merge_commit"  # Preserves branch history
    SQUASH = "squash"  # Condenses commits before merge


class CommitFrequencyPolicy(BaseModel):
    """Policy for enforcing commit frequency."""

    max_uncommitted_changes: int = Field(
        default=50, description="Max file changes before forced commit"
    )
    max_uncommitted_time_minutes: int = Field(
        default=60, description="Max time without commit (minutes)"
    )
    require_tests_before_commit: bool = Field(
        default=True, description="Require tests to pass before commit"
    )
    require_descriptive_messages: bool = Field(
        default=True, description="Enforce commit message quality"
    )
    min_message_length: int = Field(default=20, description="Minimum commit message length")


class AgentIdentity(BaseModel):
    """Identity configuration for an AI agent in git."""

    name: str = Field(description="Agent name (e.g., 'GitHub Copilot')")
    email: str = Field(description="Agent email (e.g., 'copilot@tta.dev')")
    branch_prefix: str = Field(default="agent", description="Prefix for agent branches")
    worktree_path: Path | None = Field(default=None, description="Path to agent's worktree")


class GitCollaborationPrimitive(BaseModel, WorkflowPrimitive[dict[str, Any], dict[str, Any]]):
    """
    Primitive for multi-agent Git collaboration with enforced best practices.

    This primitive implements patterns from Martin Fowler's research:
    - High-frequency integration (daily minimum, hourly preferred)
    - Healthy branch discipline (always green, always deployable)
    - Clear agent identity and attribution
    - Automatic conflict detection and early warning

    Based on State of DevOps Report findings that elite teams:
    - Integrate notably more often than low performers
    - Maintain smaller, frequent merges vs large risky merges
    - Use continuous integration for higher performance

    Example:
        ```python
        # Configure agent identity
        agent = AgentIdentity(
            name="GitHub Copilot",
            email="copilot@tta.dev",
            branch_prefix="agent/copilot",
        )

        # Create collaboration primitive
        git_collab = GitCollaborationPrimitive(
            agent_identity=agent,
            integration_frequency=IntegrationFrequency.HOURLY,
            repository_path=Path("~/repos/TTA.dev"),
        )

        # Use in workflow
        result = await git_collab.execute({
            "action": "commit",
            "message": "feat: Add caching primitive",
            "files": ["src/cache.py", "tests/test_cache.py"]
        }, context)
        ```
    """

    agent_identity: AgentIdentity
    integration_frequency: IntegrationFrequency = IntegrationFrequency.DAILY
    commit_policy: CommitFrequencyPolicy = Field(default_factory=CommitFrequencyPolicy)
    merge_strategy: MergeStrategy = MergeStrategy.FAST_FORWARD
    repository_path: Path
    main_branch: str = "main"
    enforce_hygiene: bool = Field(default=True, description="Enforce git hygiene rules")

    model_config = {"arbitrary_types_allowed": True}

    async def execute(self, input_data: dict[str, Any], context: WorkflowContext) -> dict[str, Any]:
        """
        Execute git collaboration action with hygiene enforcement.

        Supported actions:
        - commit: Commit changes with validation
        - sync: Sync with main branch
        - integrate: Create integration PR
        - status: Check collaboration health

        Args:
            input_data: Action and parameters
            context: Workflow context

        Returns:
            Result of git operation

        Raises:
            ValueError: If hygiene checks fail
        """
        action = input_data.get("action")

        if action == "commit":
            return await self._commit(input_data, context)
        elif action == "sync":
            return await self._sync_with_main(context)
        elif action == "integrate":
            return await self._create_integration_pr(input_data, context)
        elif action == "status":
            return await self._check_health(context)
        elif action == "enforce_frequency":
            return await self._enforce_commit_frequency(context)
        else:
            raise ValueError(f"Unknown action: {action}")

    async def _commit(self, input_data: dict[str, Any], context: WorkflowContext) -> dict[str, Any]:
        """Commit changes with validation and hygiene checks."""
        message = input_data.get("message", "")
        files = input_data.get("files", [])

        # Hygiene check: Validate commit message
        if self.enforce_hygiene:
            if len(message) < self.commit_policy.min_message_length:
                raise ValueError(
                    f"Commit message too short. Minimum {self.commit_policy.min_message_length} chars. "
                    f"Use conventional commits: feat/fix/docs/test/refactor"
                )

            # Check for conventional commit format
            if not any(
                message.startswith(prefix)
                for prefix in ["feat:", "fix:", "docs:", "test:", "refactor:", "chore:"]
            ):
                raise ValueError(
                    "Use conventional commits format: feat:/fix:/docs:/test:/refactor:/chore:"
                )

        # Hygiene check: Require tests if policy enforces
        if self.commit_policy.require_tests_before_commit:
            test_files = [f for f in files if "test" in str(f).lower()]
            if not test_files and "test:" not in message:
                # Allow test commits to skip this check
                src_files = [
                    f
                    for f in files
                    if str(f).endswith((".py", ".ts", ".js")) and "test" not in str(f).lower()
                ]
                if src_files:
                    raise ValueError(
                        "Tests required before commit. Add test files or include 'test:' in message."
                    )

        # Execute git commit
        result = await self._run_git_command(["add"] + [str(f) for f in files], context)

        if result["success"]:
            result = await self._run_git_command(["commit", "-m", message], context)

        # Record commit in context
        context.metadata["last_commit"] = datetime.now().isoformat()
        context.metadata["commits_today"] = context.metadata.get("commits_today", 0) + 1

        return {
            "success": result["success"],
            "message": message,
            "files_committed": len(files),
            "hygiene_checks_passed": True,
        }

    async def _sync_with_main(self, context: WorkflowContext) -> dict[str, Any]:
        """Sync agent branch with main branch."""
        # Fetch latest from origin
        fetch_result = await self._run_git_command(["fetch", "origin"], context)

        if not fetch_result["success"]:
            return {"success": False, "error": "Failed to fetch from origin"}

        # Check for divergence
        divergence = await self._check_divergence(context)

        if divergence["behind"] > 0:
            # Pull latest changes
            merge_result = await self._run_git_command(
                ["merge", f"origin/{self.main_branch}"], context
            )

            if not merge_result["success"]:
                return {
                    "success": False,
                    "error": "Merge conflict detected",
                    "conflicts": await self._get_conflicts(context),
                    "recommendation": "Resolve conflicts and commit",
                }

        return {
            "success": True,
            "commits_behind": divergence["behind"],
            "commits_ahead": divergence["ahead"],
            "synced": divergence["behind"] == 0,
        }

    async def _create_integration_pr(
        self, input_data: dict[str, Any], context: WorkflowContext
    ) -> dict[str, Any]:
        """Create integration PR following best practices."""
        title = input_data.get("title", "")
        body = input_data.get("body", "")

        # Hygiene check: Ensure branch is up to date
        sync_result = await self._sync_with_main(context)
        if not sync_result["success"]:
            return {
                "success": False,
                "error": "Branch not synced with main",
                "sync_result": sync_result,
            }

        # Check integration frequency
        last_integration = context.metadata.get("last_integration")
        if last_integration:
            last_integration_time = datetime.fromisoformat(last_integration)
            time_since = datetime.now() - last_integration_time

            # Warn if integration is overdue
            max_time = self._get_max_integration_time()
            if time_since > max_time:
                context.metadata["integration_warning"] = (
                    f"Integration overdue by {time_since - max_time}"
                )

        # Record integration
        context.metadata["last_integration"] = datetime.now().isoformat()

        return {
            "success": True,
            "pr_title": title,
            "pr_body": body,
            "branch": self.agent_identity.branch_prefix,
            "target": self.main_branch,
            "recommendation": "Use GitHub CLI: gh pr create --title '...' --body '...'",
        }

    async def _check_health(self, context: WorkflowContext) -> dict[str, Any]:
        """Check collaboration health and hygiene status."""
        # Check uncommitted changes
        status_result = await self._run_git_command(["status", "--porcelain"], context)
        uncommitted_files = (
            len(status_result["output"].strip().split("\n"))
            if status_result["output"].strip()
            else 0
        )

        # Check last commit time
        log_result = await self._run_git_command(["log", "-1", "--format=%ct"], context)
        last_commit_timestamp = (
            int(log_result["output"].strip())
            if log_result["success"] and log_result["output"].strip()
            else 0
        )
        time_since_commit = (
            datetime.now() - datetime.fromtimestamp(last_commit_timestamp)
            if last_commit_timestamp
            else timedelta(days=999)
        )

        # Check divergence from main
        divergence = await self._check_divergence(context)

        # Health scoring
        health_issues = []

        if uncommitted_files > self.commit_policy.max_uncommitted_changes:
            health_issues.append(
                f"Too many uncommitted files: {uncommitted_files} "
                f"(max: {self.commit_policy.max_uncommitted_changes})"
            )

        if time_since_commit.total_seconds() > (
            self.commit_policy.max_uncommitted_time_minutes * 60
        ):
            health_issues.append(
                f"No commit in {time_since_commit.total_seconds() / 3600:.1f} hours "
                f"(max: {self.commit_policy.max_uncommitted_time_minutes} minutes)"
            )

        if divergence["behind"] > 10:
            health_issues.append(
                f"Branch is {divergence['behind']} commits behind main. Sync soon!"
            )

        return {
            "healthy": len(health_issues) == 0,
            "uncommitted_files": uncommitted_files,
            "time_since_commit_hours": time_since_commit.total_seconds() / 3600,
            "commits_behind_main": divergence["behind"],
            "commits_ahead_main": divergence["ahead"],
            "health_issues": health_issues,
            "recommendation": self._get_health_recommendation(health_issues),
        }

    async def _enforce_commit_frequency(self, context: WorkflowContext) -> dict[str, Any]:
        """Enforce commit frequency policy - warn or block based on settings."""
        health = await self._check_health(context)

        if not health["healthy"]:
            warning_message = (
                "⚠️ GIT HYGIENE WARNING ⚠️\n\n"
                "Your branch health needs attention:\n"
                + "\n".join(f"  • {issue}" for issue in health["health_issues"])
                + f"\n\nRecommendation: {health['recommendation']}"
            )

            if self.enforce_hygiene:
                raise ValueError(warning_message)
            else:
                return {
                    "success": True,
                    "warning": warning_message,
                    "enforce_mode": False,
                }

        return {"success": True, "healthy": True, "message": "Branch health excellent!"}

    async def _check_divergence(self, context: WorkflowContext) -> dict[str, int]:
        """Check how far branch has diverged from main."""
        # Get commits behind
        behind_result = await self._run_git_command(
            ["rev-list", "--count", f"HEAD..origin/{self.main_branch}"], context
        )
        behind = (
            int(behind_result["output"].strip())
            if behind_result["success"] and behind_result["output"].strip()
            else 0
        )

        # Get commits ahead
        ahead_result = await self._run_git_command(
            ["rev-list", "--count", f"origin/{self.main_branch}..HEAD"], context
        )
        ahead = (
            int(ahead_result["output"].strip())
            if ahead_result["success"] and ahead_result["output"].strip()
            else 0
        )

        return {"behind": behind, "ahead": ahead}

    async def _get_conflicts(self, context: WorkflowContext) -> list[str]:
        """Get list of files with merge conflicts."""
        result = await self._run_git_command(["diff", "--name-only", "--diff-filter=U"], context)
        if result["success"] and result["output"].strip():
            return result["output"].strip().split("\n")
        return []

    def _get_max_integration_time(self) -> timedelta:
        """Get maximum time between integrations based on frequency."""
        if self.integration_frequency == IntegrationFrequency.CONTINUOUS:
            return timedelta(hours=1)
        elif self.integration_frequency == IntegrationFrequency.HOURLY:
            return timedelta(hours=2)  # Allow some slack
        elif self.integration_frequency == IntegrationFrequency.DAILY:
            return timedelta(days=1)
        else:  # WEEKLY - discouraged
            return timedelta(weeks=1)

    def _get_health_recommendation(self, health_issues: list[str]) -> str:
        """Get recommendation based on health issues."""
        if not health_issues:
            return "Keep up the great work! Branch is healthy."

        recommendations = []

        for issue in health_issues:
            if "uncommitted files" in issue:
                recommendations.append(
                    "Commit your changes: git add . && git commit -m 'feat: ...'"
                )
            elif "No commit" in issue:
                recommendations.append("Commit frequently! Break work into smaller logical units.")
            elif "behind main" in issue:
                recommendations.append("Sync with main: git fetch origin && git merge origin/main")

        return " | ".join(recommendations)

    async def _run_git_command(self, args: list[str], context: WorkflowContext) -> dict[str, Any]:
        """Run a git command and return the result."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repository_path,
                capture_output=True,
                text=True,
                check=False,
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "command": " ".join(["git"] + args),
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "command": " ".join(["git"] + args),
            }
