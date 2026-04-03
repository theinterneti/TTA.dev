"""Tests for tta workflow CLI — Task T10."""

from io import StringIO
from pathlib import Path
from unittest.mock import AsyncMock, patch

from ttadev.workflows.definition import WorkflowResult


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


class TestWorkflowRunTrackedL0:
    def test_track_l0_prints_task_and_run_ids(self, tmp_path: Path):
        result = WorkflowResult(
            workflow_name="feature_dev",
            goal="add login",
            steps=[],
            artifacts=[],
            memory_snapshot={},
            completed=True,
            total_confidence=0.85,
            tracked_task_id="task_123",
            tracked_run_id="run_123",
        )

        with patch(
            "ttadev.workflows.orchestrator.WorkflowOrchestrator.execute",
            new=AsyncMock(return_value=result),
        ):
            code, out = _run_cli(
                [
                    "--data-dir",
                    str(tmp_path),
                    "workflow",
                    "run",
                    "feature_dev",
                    "--goal",
                    "add login",
                    "--track-l0",
                ]
            )

        assert code == 0
        assert "L0 task: task_123" in out
        assert "L0 run:  run_123" in out
        assert f"tta control task show {result.tracked_task_id}" in out


class TestWorkflowRunSessionAttribution:
    """Issue #301 — tta session list must show workflow name instead of 'unknown'."""

    def test_run_creates_session_with_workflow_agent_tool(self, tmp_path: Path):
        """workflow run writes a session with agent_tool='workflow:<name>'."""
        result = WorkflowResult(
            workflow_name="feature_dev",
            goal="add login",
            steps=[],
            artifacts=[],
            memory_snapshot={},
            completed=True,
            total_confidence=0.9,
            tracked_task_id=None,
            tracked_run_id=None,
        )

        with patch(
            "ttadev.workflows.orchestrator.WorkflowOrchestrator.execute",
            new=AsyncMock(return_value=result),
        ):
            code, _ = _run_cli(
                [
                    "--data-dir",
                    str(tmp_path),
                    "workflow",
                    "run",
                    "feature_dev",
                    "--goal",
                    "add login",
                ]
            )

        assert code == 0

        from ttadev.observability.session_manager import SessionManager

        mgr = SessionManager(data_dir=tmp_path)
        sessions = mgr.list_sessions()
        assert sessions, "Expected at least one session to be created"
        session = sessions[0]
        assert session.agent_tool == "workflow:feature_dev", (
            f"Expected agent_tool='workflow:feature_dev', got {session.agent_tool!r}"
        )
        # Session should be ended after the workflow completes
        assert session.ended_at is not None, "Session should be ended after workflow run"

    def test_run_ends_session_on_provider_error(self, tmp_path: Path):
        """Session is ended even when the LLM provider is unavailable."""
        from ttadev.workflows.llm_provider import NoLLMProviderError

        with patch(
            "ttadev.workflows.orchestrator.WorkflowOrchestrator.execute",
            new=AsyncMock(side_effect=NoLLMProviderError(reason="no ollama")),
        ):
            code, _ = _run_cli(
                [
                    "--data-dir",
                    str(tmp_path),
                    "workflow",
                    "run",
                    "feature_dev",
                    "--goal",
                    "add login",
                ]
            )

        assert code != 0  # LLM provider error → non-zero exit

        from ttadev.observability.session_manager import SessionManager

        mgr = SessionManager(data_dir=tmp_path)
        sessions = mgr.list_sessions()
        assert sessions, "Session should still be created even on error"
        assert sessions[0].ended_at is not None, "Session should be ended even on error"
        assert sessions[0].agent_tool == "workflow:feature_dev"
