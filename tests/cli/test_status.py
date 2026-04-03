"""Tests for `tta status` CLI command.

All tests use unittest.mock — no real network calls, no real filesystem I/O
for provider validation.

Pattern: AAA (Arrange / Act / Assert).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from ttadev.cli.setup import SETUP_PROVIDERS, ValidationResult
from ttadev.cli.status import _check_port, _count_control_plane, _provider_slug, cmd_status

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _args(json_output: bool = False, data_dir: str = ".tta") -> argparse.Namespace:
    """Build a minimal Namespace that mimics parsed CLI args."""
    return argparse.Namespace(json_output=json_output, data_dir=data_dir)


def _make_validation_result(
    connected: bool,
    models: list[str] | None = None,
    error: str | None = None,
) -> ValidationResult:
    return ValidationResult(connected=connected, models=models or [], error=error)


# ---------------------------------------------------------------------------
# _provider_slug
# ---------------------------------------------------------------------------


class TestProviderSlug:
    def test_google_slug(self):
        """GOOGLE_API_KEY → 'google'."""
        # Arrange
        provider = next(p for p in SETUP_PROVIDERS if p.env_var == "GOOGLE_API_KEY")
        # Act
        slug = _provider_slug(provider)
        # Assert
        assert slug == "google"

    def test_groq_slug(self):
        """GROQ_API_KEY → 'groq'."""
        provider = next(p for p in SETUP_PROVIDERS if p.env_var == "GROQ_API_KEY")
        assert _provider_slug(provider) == "groq"

    def test_openrouter_slug(self):
        """OPENROUTER_API_KEY → 'openrouter'."""
        provider = next(p for p in SETUP_PROVIDERS if p.env_var == "OPENROUTER_API_KEY")
        assert _provider_slug(provider) == "openrouter"

    def test_ollama_slug(self):
        """Local provider → lowercase name."""
        provider = next(p for p in SETUP_PROVIDERS if p.is_local)
        assert _provider_slug(provider) == "ollama"


# ---------------------------------------------------------------------------
# _check_port
# ---------------------------------------------------------------------------


class TestCheckPort:
    def test_open_port_returns_true(self):
        """Arrange: socket.connect_ex returns 0 (success)."""
        # Arrange / Act
        with patch("socket.socket") as mock_socket_cls:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 0
            mock_socket_cls.return_value = mock_sock
            result = _check_port("localhost", 8000)
        # Assert
        assert result is True

    def test_closed_port_returns_false(self):
        """Arrange: socket.connect_ex returns non-zero (refused)."""
        with patch("socket.socket") as mock_socket_cls:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 111  # ECONNREFUSED
            mock_socket_cls.return_value = mock_sock
            result = _check_port("localhost", 9999)
        assert result is False

    def test_socket_is_closed_after_check(self):
        """Socket.close() must always be called (resource leak check)."""
        with patch("socket.socket") as mock_socket_cls:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 0
            mock_socket_cls.return_value = mock_sock
            _check_port("localhost", 8000)
        mock_sock.close.assert_called_once()


# ---------------------------------------------------------------------------
# _count_control_plane
# ---------------------------------------------------------------------------


class TestCountControlPlane:
    def test_returns_active_counts(self, tmp_path: Path):
        """Arrange: store with 2 pending tasks and 1 active run."""
        # Arrange
        from ttadev.control_plane.models import RunRecord, RunStatus, TaskRecord, TaskStatus
        from ttadev.control_plane.store import ControlPlaneStore

        store = ControlPlaneStore(tmp_path)
        now = "2026-01-01T00:00:00Z"

        store.put_task(
            TaskRecord(
                id="t1",
                title="T1",
                description="task 1",
                created_at=now,
                updated_at=now,
                status=TaskStatus.PENDING,
            )
        )
        store.put_task(
            TaskRecord(
                id="t2",
                title="T2",
                description="task 2",
                created_at=now,
                updated_at=now,
                status=TaskStatus.IN_PROGRESS,
            )
        )
        store.put_task(
            TaskRecord(
                id="t3",
                title="T3",
                description="task 3",
                created_at=now,
                updated_at=now,
                status=TaskStatus.COMPLETED,
            )
        )
        store.put_run(
            RunRecord(
                id="r1",
                task_id="t1",
                agent_id="a1",
                agent_tool="dev",
                started_at=now,
                updated_at=now,
                status=RunStatus.ACTIVE,
            )
        )
        store.put_run(
            RunRecord(
                id="r2",
                task_id="t2",
                agent_id="a1",
                agent_tool="dev",
                started_at=now,
                updated_at=now,
                status=RunStatus.COMPLETED,
            )
        )

        # Act
        active_tasks, active_runs = _count_control_plane(tmp_path)

        # Assert
        assert active_tasks == 2
        assert active_runs == 1

    def test_empty_store_returns_zeros(self, tmp_path: Path):
        """Arrange: fresh data dir with no tasks or runs."""
        active_tasks, active_runs = _count_control_plane(tmp_path)
        assert active_tasks == 0
        assert active_runs == 0

    def test_nonexistent_dir_returns_zeros(self, tmp_path: Path):
        """Arrange: data dir that doesn't exist yet."""
        # ControlPlaneStore creates the dir, but even if it errors, return (0, 0)
        active_tasks, active_runs = _count_control_plane(tmp_path / "nonexistent")
        assert (active_tasks, active_runs) == (0, 0)


# ---------------------------------------------------------------------------
# cmd_status — all providers healthy
# ---------------------------------------------------------------------------


class TestCmdStatusAllHealthy:
    def _make_ok_result(self, model: str) -> ValidationResult:
        return _make_validation_result(connected=True, models=[model])

    def test_exit_code_zero_when_providers_healthy(self, tmp_path: Path):
        """≥1 provider connected → exit code 0."""
        # Arrange
        results = [self._make_ok_result("gemini-2.0-flash"), MagicMock(connected=False, models=[], error=None), MagicMock(connected=False, models=[], error=None), MagicMock(connected=False, models=[], error=None)]  # fmt: skip

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=results),
            patch("ttadev.cli.status._check_port", return_value=False),
            patch("ttadev.cli.status._read_env", return_value={"GOOGLE_API_KEY": "fake-key"}),
        ):
            # Act
            code = cmd_status(_args(), project_root=tmp_path, data_dir=tmp_path)

        # Assert
        assert code == 0

    def test_output_contains_checkmark_for_healthy_provider(self, tmp_path: Path, capsys):
        """Healthy provider rows start with ✓."""
        results = [
            _make_validation_result(True, ["gemini-2.0-flash-lite"]),
            _make_validation_result(True, ["llama-3.3-70b-versatile"]),
            _make_validation_result(False, error=None),
            _make_validation_result(False, error=None),
        ]

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=results),
            patch("ttadev.cli.status._check_port", return_value=False),
            patch(
                "ttadev.cli.status._read_env",
                return_value={"GOOGLE_API_KEY": "k", "GROQ_API_KEY": "k"},
            ),
        ):
            cmd_status(_args(), project_root=tmp_path, data_dir=tmp_path)

        out = capsys.readouterr().out
        assert "✓" in out
        assert "google" in out
        assert "groq" in out

    def test_output_shows_latency_for_healthy_providers(self, tmp_path: Path, capsys):
        """Healthy provider rows include 'latency' keyword."""
        results = [
            _make_validation_result(True, ["some-model"]),
            _make_validation_result(False),
            _make_validation_result(False),
            _make_validation_result(False),
        ]

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=results),
            patch("ttadev.cli.status._check_port", return_value=False),
            patch("ttadev.cli.status._read_env", return_value={"GOOGLE_API_KEY": "k"}),
        ):
            cmd_status(_args(), project_root=tmp_path, data_dir=tmp_path)

        out = capsys.readouterr().out
        assert "latency" in out


# ---------------------------------------------------------------------------
# cmd_status — all providers missing/failing
# ---------------------------------------------------------------------------


class TestCmdStatusAllMissing:
    def test_exit_code_one_when_all_missing(self, tmp_path: Path):
        """All providers missing key or failing → exit code 1."""
        # Arrange: no keys in env, all validate_provider calls fail
        all_fail = [_make_validation_result(False)] * len(SETUP_PROVIDERS)

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=all_fail),
            patch("ttadev.cli.status._check_port", return_value=False),
            patch("ttadev.cli.status._read_env", return_value={}),
        ):
            # Act
            code = cmd_status(_args(), project_root=tmp_path, data_dir=tmp_path)

        # Assert
        assert code == 1

    def test_output_shows_missing_key_message(self, tmp_path: Path, capsys):
        """Missing-key providers display the MISSING key hint."""
        all_fail = [_make_validation_result(False)] * len(SETUP_PROVIDERS)

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=all_fail),
            patch("ttadev.cli.status._check_port", return_value=False),
            patch("ttadev.cli.status._read_env", return_value={}),
        ):
            cmd_status(_args(), project_root=tmp_path, data_dir=tmp_path)

        out = capsys.readouterr().out
        assert "MISSING key" in out
        assert "tta setup" in out


# ---------------------------------------------------------------------------
# cmd_status — --json output
# ---------------------------------------------------------------------------


class TestCmdStatusJsonOutput:
    def test_json_output_is_valid_json(self, tmp_path: Path, capsys):
        """--json produces parseable JSON."""
        results = [
            _make_validation_result(True, ["gemini-model"]),
            _make_validation_result(False),
            _make_validation_result(False),
            _make_validation_result(False),
        ]

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=results),
            patch("ttadev.cli.status._check_port", return_value=False),
            patch("ttadev.cli.status._read_env", return_value={"GOOGLE_API_KEY": "k"}),
        ):
            cmd_status(_args(json_output=True), project_root=tmp_path, data_dir=tmp_path)

        out = capsys.readouterr().out.strip()
        parsed = json.loads(out)  # must not raise
        assert isinstance(parsed, dict)

    def test_json_output_has_required_keys(self, tmp_path: Path, capsys):
        """JSON output contains providers, services, control_plane, config, healthy."""
        results = [_make_validation_result(False)] * len(SETUP_PROVIDERS)

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=results),
            patch("ttadev.cli.status._check_port", return_value=False),
            patch("ttadev.cli.status._read_env", return_value={}),
        ):
            cmd_status(_args(json_output=True), project_root=tmp_path, data_dir=tmp_path)

        parsed = json.loads(capsys.readouterr().out.strip())
        assert "providers" in parsed
        assert "services" in parsed
        assert "control_plane" in parsed
        assert "config" in parsed
        assert "healthy" in parsed

    def test_json_output_contains_no_key_values(self, tmp_path: Path, capsys):
        """API key values must never appear in JSON output."""
        # Arrange: use a distinctive fake key value — noqa keeps ruff happy
        secret_key = "sk-super-secret-test-key-abc123"  # noqa: S105
        results = [_make_validation_result(False)] * len(SETUP_PROVIDERS)

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=results),
            patch("ttadev.cli.status._check_port", return_value=False),
            patch(
                "ttadev.cli.status._read_env",
                return_value={"GOOGLE_API_KEY": secret_key},
            ),
        ):
            cmd_status(_args(json_output=True), project_root=tmp_path, data_dir=tmp_path)

        raw_out = capsys.readouterr().out
        assert secret_key not in raw_out

    def test_json_healthy_true_when_provider_connected(self, tmp_path: Path, capsys):
        """healthy field is True when ≥1 provider connected."""
        results = [
            _make_validation_result(True, ["model-x"]),
            *[_make_validation_result(False)] * (len(SETUP_PROVIDERS) - 1),
        ]

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=results),
            patch("ttadev.cli.status._check_port", return_value=False),
            patch("ttadev.cli.status._read_env", return_value={"GOOGLE_API_KEY": "k"}),
        ):
            cmd_status(_args(json_output=True), project_root=tmp_path, data_dir=tmp_path)

        parsed = json.loads(capsys.readouterr().out.strip())
        assert parsed["healthy"] is True

    def test_json_healthy_false_when_all_fail(self, tmp_path: Path, capsys):
        """healthy field is False when all providers fail."""
        results = [_make_validation_result(False)] * len(SETUP_PROVIDERS)

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=results),
            patch("ttadev.cli.status._check_port", return_value=False),
            patch("ttadev.cli.status._read_env", return_value={}),
        ):
            cmd_status(_args(json_output=True), project_root=tmp_path, data_dir=tmp_path)

        parsed = json.loads(capsys.readouterr().out.strip())
        assert parsed["healthy"] is False


# ---------------------------------------------------------------------------
# cmd_status — port detection
# ---------------------------------------------------------------------------


class TestCmdStatusPortDetection:
    def test_dashboard_running_shown_in_output(self, tmp_path: Path, capsys):
        """When dashboard port is open, output says (running)."""
        results = [_make_validation_result(False)] * len(SETUP_PROVIDERS)

        def _port_side(host: str, port: int, timeout: float = 2.0) -> bool:
            return port == 8000  # dashboard open, mcp closed

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=results),
            patch("ttadev.cli.status._check_port", side_effect=_port_side),
            patch("ttadev.cli.status._read_env", return_value={}),
        ):
            cmd_status(_args(), project_root=tmp_path, data_dir=tmp_path)

        out = capsys.readouterr().out
        assert "(running)" in out
        assert "not running on port 9999" in out

    def test_mcp_running_shown_in_output(self, tmp_path: Path, capsys):
        """When MCP port is open, output says (running) for mcp-server."""
        results = [_make_validation_result(False)] * len(SETUP_PROVIDERS)

        def _port_side(host: str, port: int, timeout: float = 2.0) -> bool:
            return port == 9999  # mcp open, dashboard closed

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=results),
            patch("ttadev.cli.status._check_port", side_effect=_port_side),
            patch("ttadev.cli.status._read_env", return_value={}),
        ):
            cmd_status(_args(), project_root=tmp_path, data_dir=tmp_path)

        out = capsys.readouterr().out
        assert "not running on port 8000" in out

    def test_json_services_reflect_port_state(self, tmp_path: Path, capsys):
        """JSON services array reflects actual port state."""
        results = [_make_validation_result(False)] * len(SETUP_PROVIDERS)

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=results),
            patch("ttadev.cli.status._check_port", return_value=True),
            patch("ttadev.cli.status._read_env", return_value={}),
        ):
            cmd_status(_args(json_output=True), project_root=tmp_path, data_dir=tmp_path)

        parsed = json.loads(capsys.readouterr().out.strip())
        assert all(svc["running"] is True for svc in parsed["services"])


# ---------------------------------------------------------------------------
# cmd_status — control plane counts
# ---------------------------------------------------------------------------


class TestCmdStatusControlPlane:
    def test_control_plane_counts_in_human_output(self, tmp_path: Path, capsys):
        """Active tasks and active runs appear in human-readable output."""
        results = [_make_validation_result(False)] * len(SETUP_PROVIDERS)

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=results),
            patch("ttadev.cli.status._check_port", return_value=False),
            patch("ttadev.cli.status._read_env", return_value={}),
            patch("ttadev.cli.status._count_control_plane", return_value=(3, 2)),
        ):
            cmd_status(_args(), project_root=tmp_path, data_dir=tmp_path)

        out = capsys.readouterr().out
        assert "Active tasks   3" in out
        assert "Active runs    2" in out

    def test_control_plane_counts_in_json_output(self, tmp_path: Path, capsys):
        """control_plane object in JSON contains task and run counts."""
        results = [_make_validation_result(False)] * len(SETUP_PROVIDERS)

        with (
            patch("ttadev.cli.status.validate_provider", side_effect=results),
            patch("ttadev.cli.status._check_port", return_value=False),
            patch("ttadev.cli.status._read_env", return_value={}),
            patch("ttadev.cli.status._count_control_plane", return_value=(5, 1)),
        ):
            cmd_status(_args(json_output=True), project_root=tmp_path, data_dir=tmp_path)

        parsed = json.loads(capsys.readouterr().out.strip())
        assert parsed["control_plane"]["active_tasks"] == 5
        assert parsed["control_plane"]["active_runs"] == 1


# ---------------------------------------------------------------------------
# CLI registration smoke test
# ---------------------------------------------------------------------------


class TestCliRegistration:
    def test_status_appears_in_help(self, capsys):
        """tta --help mentions the status subcommand."""
        from ttadev.cli import _build_parser

        parser = _build_parser()
        try:
            parser.parse_args(["--help"])
        except SystemExit:
            pass
        out = capsys.readouterr().out
        assert "status" in out

    def test_status_json_flag_parsed(self):
        """tta status --json sets json_output=True on the namespace."""
        from ttadev.cli import _build_parser

        parser = _build_parser()
        ns = parser.parse_args(["status", "--json"])
        assert ns.command == "status"
        assert ns.json_output is True
