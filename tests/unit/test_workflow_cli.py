"""Tests for tta workflow CLI — Task T10."""

from io import StringIO
from unittest.mock import patch


def _run_cli(args: list[str]) -> tuple[int, str]:
    """Run the tta CLI and capture stdout; return (exit_code, output)."""
    buf = StringIO()
    with patch("sys.stdout", buf):
        try:
            from ttadev.cli import main

            with patch("sys.argv", ["tta"] + args):
                main()
            return 0, buf.getvalue()
        except SystemExit as e:
            return int(e.code or 0), buf.getvalue()


class TestWorkflowList:
    def test_list_shows_feature_dev(self):
        code, out = _run_cli(["workflow", "list"])
        assert code == 0
        assert "feature_dev" in out

    def test_list_shows_description(self):
        code, out = _run_cli(["workflow", "list"])
        assert "end-to-end" in out.lower() or "feature" in out.lower()


class TestWorkflowShow:
    def test_show_feature_dev_lists_agents(self):
        code, out = _run_cli(["workflow", "show", "feature_dev"])
        assert code == 0
        for agent in ["developer", "qa", "security", "git", "github"]:
            assert agent in out

    def test_show_unknown_workflow_exits_nonzero(self):
        code, _ = _run_cli(["workflow", "show", "does_not_exist"])
        assert code != 0


class TestWorkflowRunDryRun:
    def test_dry_run_exits_zero(self):
        code, out = _run_cli(["workflow", "run", "feature_dev", "--goal", "add login", "--dry-run"])
        assert code == 0

    def test_dry_run_prints_step_plan(self):
        code, out = _run_cli(["workflow", "run", "feature_dev", "--goal", "add login", "--dry-run"])
        assert "developer" in out
        assert "qa" in out

    def test_dry_run_does_not_call_agents(self):
        """Ensure no agent execution happens in dry-run mode."""
        with patch("ttadev.workflows.orchestrator.WorkflowOrchestrator._execute_impl") as mock:
            _run_cli(["workflow", "run", "feature_dev", "--goal", "add login", "--dry-run"])
            mock.assert_not_called()
