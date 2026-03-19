"""Regression tests for keyword matching in agent handoff triggers.

These tests codify word-boundary requirements: short keywords like 'pr'
must NOT match as substrings inside unrelated words.
"""

from ttadev.agents.task import AgentTask


def _task(instruction: str) -> AgentTask:
    return AgentTask(instruction=instruction, context={}, constraints=[])


class TestPRKeyword:
    """'pr' should match standalone PR (GitHub abbreviation) but not substrings."""

    def test_pr_matches_standalone(self):
        from ttadev.agents.developer import DEVELOPER_SPEC

        trigger = next(t for t in DEVELOPER_SPEC.handoff_triggers if t.target_agent == "github")
        assert trigger.condition(_task("open a PR for this change")) is True

    def test_pr_matches_uppercase(self):
        from ttadev.agents.developer import DEVELOPER_SPEC

        trigger = next(t for t in DEVELOPER_SPEC.handoff_triggers if t.target_agent == "github")
        assert trigger.condition(_task("this PR needs a review")) is True

    def test_pr_does_not_match_project(self):
        from ttadev.agents.developer import DEVELOPER_SPEC

        trigger = next(t for t in DEVELOPER_SPEC.handoff_triggers if t.target_agent == "github")
        assert trigger.condition(_task("set up the project structure")) is False

    def test_pr_does_not_match_improve(self):
        from ttadev.agents.developer import DEVELOPER_SPEC

        trigger = next(t for t in DEVELOPER_SPEC.handoff_triggers if t.target_agent == "github")
        assert trigger.condition(_task("improve the error messages")) is False


class TestHelmKeyword:
    """'helm' should match Helm (k8s package manager) but not 'overwhelm'."""

    def test_helm_matches_standalone(self):
        from ttadev.agents.developer import DEVELOPER_SPEC

        trigger = next(t for t in DEVELOPER_SPEC.handoff_triggers if t.target_agent == "devops")
        assert trigger.condition(_task("deploy via helm chart")) is True

    def test_helm_does_not_match_overwhelm(self):
        from ttadev.agents.developer import DEVELOPER_SPEC

        trigger = next(t for t in DEVELOPER_SPEC.handoff_triggers if t.target_agent == "devops")
        assert trigger.condition(_task("the error messages overwhelm the logs")) is False


class TestAuthKeyword:
    """'auth' should match authentication and authorization, not just standalone 'auth'."""

    def test_auth_matches_standalone(self):
        from ttadev.agents.qa import QA_SPEC

        trigger = next(t for t in QA_SPEC.handoff_triggers if t.target_agent == "security")
        assert trigger.condition(_task("our auth module is broken")) is True

    def test_auth_matches_authentication(self):
        from ttadev.agents.qa import QA_SPEC

        trigger = next(t for t in QA_SPEC.handoff_triggers if t.target_agent == "security")
        assert trigger.condition(_task("review the authentication flow")) is True

    def test_auth_matches_authorization(self):
        from ttadev.agents.qa import QA_SPEC

        trigger = next(t for t in QA_SPEC.handoff_triggers if t.target_agent == "security")
        assert trigger.condition(_task("check our authorization logic")) is True


class TestProfilingKeyword:
    """'profil' prefix should be replaced with explicit 'profile'/'profiling' keywords."""

    def test_profiling_matches(self):
        from ttadev.agents.qa import QA_SPEC

        trigger = next(t for t in QA_SPEC.handoff_triggers if t.target_agent == "performance")
        assert trigger.condition(_task("add profiling to the hot path")) is True

    def test_profile_matches(self):
        from ttadev.agents.qa import QA_SPEC

        trigger = next(t for t in QA_SPEC.handoff_triggers if t.target_agent == "performance")
        assert trigger.condition(_task("profile this function")) is True


class TestSlowKeyword:
    """'slow' should match 'slowly' as well."""

    def test_slow_matches_standalone(self):
        from ttadev.agents.qa import QA_SPEC

        trigger = next(t for t in QA_SPEC.handoff_triggers if t.target_agent == "performance")
        assert trigger.condition(_task("response time is too slow")) is True

    def test_slow_matches_slowly(self):
        from ttadev.agents.qa import QA_SPEC

        trigger = next(t for t in QA_SPEC.handoff_triggers if t.target_agent == "performance")
        assert trigger.condition(_task("the API is running slowly")) is True


class TestWebhookKeyword:
    """'hook' in compound word 'webhook' should still trigger devops routing."""

    def test_webhook_matches(self):
        from ttadev.agents.git import GIT_SPEC

        trigger = next(t for t in GIT_SPEC.handoff_triggers if t.target_agent == "devops")
        assert trigger.condition(_task("set up a GitHub webhook for CI")) is True

    def test_hook_standalone_matches(self):
        from ttadev.agents.git import GIT_SPEC

        trigger = next(t for t in GIT_SPEC.handoff_triggers if t.target_agent == "devops")
        assert trigger.condition(_task("add a pre-commit hook")) is True
