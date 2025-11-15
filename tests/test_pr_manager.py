"""
Tests for PR Manager functionality.

These tests verify the PR management tool's categorization,
prioritization, and recommendation logic.
"""

from datetime import UTC, datetime, timedelta

import pytest

from scripts.pr_manager import PRManager


class TestPRManager:
    """Test suite for PRManager class."""

    @pytest.fixture
    def manager(self):
        """Provide a PRManager instance for testing."""
        return PRManager()

    @pytest.fixture
    def sample_pr_data(self):
        """Provide sample PR data for testing."""
        now = datetime.now(UTC)
        return {
            "number": 123,
            "title": "Add new feature",
            "author": {"login": "testuser"},
            "createdAt": (now - timedelta(days=5)).isoformat(),
            "updatedAt": (now - timedelta(days=1)).isoformat(),
            "state": "OPEN",
            "isDraft": False,
            "reviewDecision": None,
            "statusCheckRollup": [],
            "labels": [],
            "additions": 100,
            "deletions": 50,
            "changedFiles": 5,
            "comments": [],
            "reviews": [],
        }

    def test_calculate_pr_age(self, manager):
        """Test PR age calculation."""
        # 5 days ago
        created_at = (datetime.now(UTC) - timedelta(days=5)).isoformat()
        age = manager.calculate_pr_age(created_at)
        assert 4 <= age.days <= 5  # Allow for timing variations

    def test_calculate_pr_staleness(self, manager):
        """Test PR staleness calculation."""
        # 2 days ago
        updated_at = (datetime.now(UTC) - timedelta(days=2)).isoformat()
        staleness = manager.calculate_pr_staleness(updated_at)
        assert 1 <= staleness.days <= 2  # Allow for timing variations

    def test_categorize_critical_pr(self, manager, sample_pr_data):
        """Test categorization of critical PR."""
        sample_pr_data["labels"] = [{"name": "critical"}]
        category = manager.categorize_pr(sample_pr_data)
        assert category == "🔴 critical"

    def test_categorize_draft_pr(self, manager, sample_pr_data):
        """Test categorization of draft PR."""
        sample_pr_data["isDraft"] = True
        category = manager.categorize_pr(sample_pr_data)
        assert category == "📝 draft"

    def test_categorize_needs_review_pr(self, manager, sample_pr_data):
        """Test categorization of PR needing review."""
        sample_pr_data["reviewDecision"] = None
        sample_pr_data["isDraft"] = False
        category = manager.categorize_pr(sample_pr_data)
        assert category == "👀 needs-review"

    def test_categorize_changes_requested_pr(self, manager, sample_pr_data):
        """Test categorization of PR with changes requested."""
        sample_pr_data["reviewDecision"] = "CHANGES_REQUESTED"
        category = manager.categorize_pr(sample_pr_data)
        assert category == "🔧 changes-requested"

    def test_categorize_ready_to_merge_pr(self, manager, sample_pr_data):
        """Test categorization of ready-to-merge PR."""
        sample_pr_data["reviewDecision"] = "APPROVED"
        sample_pr_data["statusCheckRollup"] = [
            {"conclusion": "SUCCESS"},
            {"conclusion": "SUCCESS"},
        ]
        category = manager.categorize_pr(sample_pr_data)
        assert category == "✅ ready-to-merge"

    def test_categorize_approved_failing_checks_pr(self, manager, sample_pr_data):
        """Test categorization of approved PR with failing checks."""
        sample_pr_data["reviewDecision"] = "APPROVED"
        sample_pr_data["statusCheckRollup"] = [
            {"conclusion": "SUCCESS"},
            {"conclusion": "FAILURE"},
        ]
        category = manager.categorize_pr(sample_pr_data)
        assert category == "⚠️ approved-failing-checks"

    def test_categorize_stale_pr(self, manager, sample_pr_data):
        """Test categorization of stale PR."""
        now = datetime.now(UTC)
        sample_pr_data["updatedAt"] = (now - timedelta(days=10)).isoformat()
        category = manager.categorize_pr(sample_pr_data)
        assert category == "🕸️ stale"

    def test_categorize_old_pr(self, manager, sample_pr_data):
        """Test categorization of old PR."""
        now = datetime.now(UTC)
        sample_pr_data["createdAt"] = (now - timedelta(days=20)).isoformat()
        sample_pr_data["updatedAt"] = (now - timedelta(days=2)).isoformat()
        category = manager.categorize_pr(sample_pr_data)
        assert category == "⏳ old"

    def test_prioritize_critical_pr(self, manager, sample_pr_data):
        """Test prioritization of critical PR."""
        sample_pr_data["labels"] = [{"name": "critical"}]
        priority = manager.prioritize_pr(sample_pr_data)
        assert priority >= 70  # Should be high priority

    def test_prioritize_security_pr(self, manager, sample_pr_data):
        """Test prioritization of security PR."""
        sample_pr_data["labels"] = [{"name": "security"}]
        priority = manager.prioritize_pr(sample_pr_data)
        assert priority >= 70  # Should be high priority

    def test_prioritize_large_pr(self, manager, sample_pr_data):
        """Test prioritization of large PR."""
        sample_pr_data["additions"] = 600
        sample_pr_data["deletions"] = 200
        priority = manager.prioritize_pr(sample_pr_data)
        # Large PRs get +20, so should be higher than base
        assert priority > 50

    def test_prioritize_approved_pr(self, manager, sample_pr_data):
        """Test prioritization of approved PR."""
        sample_pr_data["reviewDecision"] = "APPROVED"
        priority = manager.prioritize_pr(sample_pr_data)
        # Approved PRs get +15
        assert priority > 50

    def test_prioritize_passing_ci(self, manager, sample_pr_data):
        """Test prioritization of PR with passing CI."""
        sample_pr_data["statusCheckRollup"] = [
            {"conclusion": "SUCCESS"},
            {"conclusion": "SUCCESS"},
        ]
        priority = manager.prioritize_pr(sample_pr_data)
        # Passing CI gets +10
        assert priority > 50

    def test_prioritize_recent_activity(self, manager, sample_pr_data):
        """Test prioritization of PR with recent activity."""
        now = datetime.now(UTC)
        sample_pr_data["updatedAt"] = (now - timedelta(hours=12)).isoformat()
        priority = manager.prioritize_pr(sample_pr_data)
        # Recent activity gets +10
        assert priority > 50

    def test_prioritize_old_age_penalty(self, manager, sample_pr_data):
        """Test age penalty in prioritization."""
        now = datetime.now(UTC)
        # PR is 4 weeks old
        sample_pr_data["createdAt"] = (now - timedelta(days=28)).isoformat()
        priority_old = manager.prioritize_pr(sample_pr_data)

        # PR is 1 day old
        sample_pr_data["createdAt"] = (now - timedelta(days=1)).isoformat()
        priority_new = manager.prioritize_pr(sample_pr_data)

        # Older PR should have lower priority due to age penalty
        assert priority_old < priority_new

    def test_get_recommendations_ready_to_merge(self, manager, sample_pr_data):
        """Test recommendations for ready-to-merge PR."""
        sample_pr_data["reviewDecision"] = "APPROVED"
        sample_pr_data["statusCheckRollup"] = [{"conclusion": "SUCCESS"}]
        recommendations = manager.get_recommendations(sample_pr_data)
        assert any("Ready to merge" in rec for rec in recommendations)

    def test_get_recommendations_needs_review(self, manager, sample_pr_data):
        """Test recommendations for PR needing review."""
        sample_pr_data["reviewDecision"] = None
        sample_pr_data["isDraft"] = False
        recommendations = manager.get_recommendations(sample_pr_data)
        assert any("review" in rec.lower() for rec in recommendations)

    def test_get_recommendations_changes_requested(self, manager, sample_pr_data):
        """Test recommendations for PR with changes requested."""
        now = datetime.now(UTC)
        sample_pr_data["reviewDecision"] = "CHANGES_REQUESTED"
        sample_pr_data["updatedAt"] = (now - timedelta(days=5)).isoformat()
        recommendations = manager.get_recommendations(sample_pr_data)
        assert any("changes" in rec.lower() for rec in recommendations)

    def test_get_recommendations_stale_pr(self, manager, sample_pr_data):
        """Test recommendations for stale PR."""
        now = datetime.now(UTC)
        sample_pr_data["updatedAt"] = (now - timedelta(days=10)).isoformat()
        recommendations = manager.get_recommendations(sample_pr_data)
        assert any("activity" in rec.lower() or "stale" in rec.lower() for rec in recommendations)

    def test_get_recommendations_large_pr(self, manager, sample_pr_data):
        """Test recommendations for large PR."""
        sample_pr_data["additions"] = 1200
        sample_pr_data["deletions"] = 500
        recommendations = manager.get_recommendations(sample_pr_data)
        assert any("Large PR" in rec for rec in recommendations)

    def test_get_recommendations_failing_checks(self, manager, sample_pr_data):
        """Test recommendations for PR with failing checks."""
        sample_pr_data["statusCheckRollup"] = [
            {"conclusion": "SUCCESS"},
            {"conclusion": "FAILURE"},
            {"conclusion": "FAILURE"},
        ]
        recommendations = manager.get_recommendations(sample_pr_data)
        assert any("failing check" in rec.lower() for rec in recommendations)

    def test_get_recommendations_draft_stale(self, manager, sample_pr_data):
        """Test recommendations for stale draft PR."""
        now = datetime.now(UTC)
        sample_pr_data["isDraft"] = True
        sample_pr_data["updatedAt"] = (now - timedelta(days=5)).isoformat()
        recommendations = manager.get_recommendations(sample_pr_data)
        assert any("Draft" in rec for rec in recommendations)

    def test_priority_score_range(self, manager, sample_pr_data):
        """Test that priority score is within valid range."""
        priority = manager.prioritize_pr(sample_pr_data)
        assert 0 <= priority <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
