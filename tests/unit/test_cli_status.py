"""Unit tests for ttadev/cli/status.py (`tta status`).

Covers:
- Healthy path: ≥1 provider reachable, all services up → exit 0
- Degraded path: one cloud provider key missing, another healthy → exit 0
- No-dashboard path: dashboard port closed → still exit 0 (non-critical)
- All providers down: no keys + Ollama absent → exit 1
- JSON output: --json flag produces valid JSON with expected keys
- _check_port: returns True/False based on socket connect result
- _count_control_plane: returns zeros when store is uninitialized
- _provider_slug: derives correct slugs from provider descriptors
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ttadev.cli.setup import SetupProvider, ValidationResult
from ttadev.cli.status import (
    _check_port,
    _count_control_plane,
    _provider_slug,
    cmd_status,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GOOGLE = SetupProvider(
    name="Google AI Studio",
    env_var="GOOGLE_API_KEY",
    signup_url="https://aistudio.google.com",
    validate_url="https://generativelanguage.googleapis.com/v1beta/models",
    auth_style="query_param",
    response_format="google",
    help_what="",
    help_how=[],
)

_GROQ = SetupProvider(
    name="Groq",
    env_var="GROQ_API_KEY",
    signup_url="https://console.groq.com",
    validate_url="https://api.groq.com/openai/v1/models",
    auth_style="bearer",
    help_what="",
    help_how=[],
)

_OLLAMA = SetupProvider(
    name="Ollama",
    env_var="",
    signup_url="https://ollama.ai",
    validate_url="http://localhost:11434/api/tags",
    auth_style="none",
    help_what="",
    help_how=[],
    is_local=True,
)

_ALL_PROVIDERS = [_GOOGLE, _GROQ, _OLLAMA]

_CONNECTED = ValidationResult(connected=True, models=["gemma-3-9b-it"], error=None)
_FAILED = ValidationResult(connected=False, models=[], error="connection refused")
_NOT_FOUND = ValidationResult(connected=False, models=[], error=None)


def _make_args(*, json_output: bool = False, data_dir: str = ".tta") -> argparse.Namespace:
    return argparse.Namespace(json_output=json_output, data_dir=data_dir)


# ---------------------------------------------------------------------------
# _provider_slug
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestProviderSlug:
    def test_cloud_provider_strips_api_key_suffix(self) -> None:
        assert _provider_slug(_GOOGLE) == "google"
        assert _provider_slug(_GROQ) == "groq"

    def test_local_provider_uses_name_lower(self) -> None:
        assert _provider_slug(_OLLAMA) == "ollama"


# ---------------------------------------------------------------------------
# _check_port
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCheckPort:
    def test_returns_true_when_port_open(self) -> None:
        with patch("ttadev.cli.status.socket.socket") as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 0
            mock_sock_cls.return_value = mock_sock
            assert _check_port("localhost", 8000) is True

    def test_returns_false_when_port_closed(self) -> None:
        with patch("ttadev.cli.status.socket.socket") as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 111  # connection refused
            mock_sock_cls.return_value = mock_sock
            assert _check_port("localhost", 8000) is False

    def test_socket_is_always_closed(self) -> None:
        with patch("ttadev.cli.status.socket.socket") as mock_sock_cls:
            mock_sock = MagicMock()
            mock_sock.connect_ex.return_value = 0
            mock_sock_cls.return_value = mock_sock
            _check_port("localhost", 8000)
            mock_sock.close.assert_called_once()


# ---------------------------------------------------------------------------
# _count_control_plane
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCountControlPlane:
    def test_returns_zeros_when_store_not_initialized(self, tmp_path: Path) -> None:
        counts = _count_control_plane(tmp_path)
        assert counts == (0, 0)

    def test_returns_zeros_on_store_error(self, tmp_path: Path) -> None:
        """Any exception from the store → returns (0, 0); raises are swallowed."""
        with patch(
            "ttadev.control_plane.store.ControlPlaneStore.list_tasks",
            side_effect=RuntimeError("boom"),
        ):
            counts = _count_control_plane(tmp_path)
        assert counts == (0, 0)


# ---------------------------------------------------------------------------
# cmd_status — human-readable output
# ---------------------------------------------------------------------------


def _patch_status(
    *,
    providers: list[SetupProvider],
    validate_results: dict[str, ValidationResult],
    env: dict[str, str],
    dashboard_up: bool = True,
    mcp_up: bool = False,
    active_tasks: int = 0,
    active_runs: int = 0,
):
    """Context manager stack that patches all external I/O for cmd_status."""
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        with (
            patch("ttadev.cli.status.SETUP_PROVIDERS", providers),
            patch(
                "ttadev.cli.status.validate_provider",
                side_effect=lambda p, k: validate_results[p.name],
            ),
            patch("ttadev.cli.status._read_env", return_value=env),
            patch("ttadev.cli.status._get_key", side_effect=lambda p, e: e.get(p.env_var)),
            patch(
                "ttadev.cli.status._check_port",
                side_effect=lambda host, port, **_: (
                    (port == 8000 and dashboard_up) or (port == 9999 and mcp_up)
                ),
            ),
            patch(
                "ttadev.cli.status._count_control_plane", return_value=(active_tasks, active_runs)
            ),
        ):
            yield

    return _ctx()


@pytest.mark.unit
class TestCmdStatusHumanOutput:
    """Human-readable output path."""

    def test_healthy_path_exits_0(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """All providers healthy → exit 0."""
        env = {"GOOGLE_API_KEY": "gk", "GROQ_API_KEY": "grk"}
        results = {
            "Google AI Studio": _CONNECTED,
            "Groq": _CONNECTED,
            "Ollama": _CONNECTED,
        }
        with _patch_status(providers=_ALL_PROVIDERS, validate_results=results, env=env):
            rc = cmd_status(_make_args(), project_root=tmp_path, data_dir=tmp_path / ".tta")
        assert rc == 0
        out = capsys.readouterr().out
        assert "✓" in out
        assert "TTA.dev status" in out

    def test_degraded_one_provider_missing_key_exits_0(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Google key missing, Groq healthy → still exit 0 (≥1 healthy)."""
        env = {"GROQ_API_KEY": "grk"}  # Google key absent
        results = {
            "Google AI Studio": _NOT_FOUND,
            "Groq": _CONNECTED,
            "Ollama": _NOT_FOUND,
        }
        with _patch_status(providers=_ALL_PROVIDERS, validate_results=results, env=env):
            rc = cmd_status(_make_args(), project_root=tmp_path, data_dir=tmp_path / ".tta")
        assert rc == 0
        out = capsys.readouterr().out
        assert "MISSING key" in out or "missing" in out.lower() or "✓" in out

    def test_no_dashboard_still_exits_0(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Dashboard port closed but a provider is healthy → exit 0."""
        env = {"GROQ_API_KEY": "grk"}
        results = {
            "Google AI Studio": _NOT_FOUND,
            "Groq": _CONNECTED,
            "Ollama": _NOT_FOUND,
        }
        with _patch_status(
            providers=_ALL_PROVIDERS,
            validate_results=results,
            env=env,
            dashboard_up=False,
        ):
            rc = cmd_status(_make_args(), project_root=tmp_path, data_dir=tmp_path / ".tta")
        assert rc == 0
        out = capsys.readouterr().out
        assert "not running" in out

    def test_all_providers_down_exits_1(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """No keys, Ollama not detected → exit 1."""
        env: dict[str, str] = {}
        results = {
            "Google AI Studio": _FAILED,
            "Groq": _FAILED,
            "Ollama": _FAILED,
        }
        with _patch_status(providers=_ALL_PROVIDERS, validate_results=results, env=env):
            rc = cmd_status(_make_args(), project_root=tmp_path, data_dir=tmp_path / ".tta")
        assert rc == 1

    def test_control_plane_counts_displayed(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Active tasks and runs appear in human output."""
        env = {"GROQ_API_KEY": "grk"}
        results = {
            "Google AI Studio": _NOT_FOUND,
            "Groq": _CONNECTED,
            "Ollama": _NOT_FOUND,
        }
        with _patch_status(
            providers=_ALL_PROVIDERS,
            validate_results=results,
            env=env,
            active_tasks=3,
            active_runs=1,
        ):
            cmd_status(_make_args(), project_root=tmp_path, data_dir=tmp_path / ".tta")
        out = capsys.readouterr().out
        assert "3" in out
        assert "1" in out

    def test_ollama_shows_not_detected(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Ollama absent shows 'not detected' (not 'MISSING key')."""
        env: dict[str, str] = {}
        results = {
            "Google AI Studio": _NOT_FOUND,
            "Groq": _NOT_FOUND,
            "Ollama": _NOT_FOUND,
        }
        with _patch_status(providers=[_OLLAMA], validate_results=results, env=env):
            cmd_status(_make_args(), project_root=tmp_path, data_dir=tmp_path / ".tta")
        out = capsys.readouterr().out
        assert "not detected" in out


# ---------------------------------------------------------------------------
# cmd_status — JSON output
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCmdStatusJsonOutput:
    def test_json_flag_produces_valid_json(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        env = {"GROQ_API_KEY": "grk"}
        results = {
            "Google AI Studio": _NOT_FOUND,
            "Groq": _CONNECTED,
            "Ollama": _NOT_FOUND,
        }
        with _patch_status(providers=_ALL_PROVIDERS, validate_results=results, env=env):
            rc = cmd_status(
                _make_args(json_output=True), project_root=tmp_path, data_dir=tmp_path / ".tta"
            )
        out = capsys.readouterr().out
        payload = json.loads(out)
        assert rc == 0
        assert "providers" in payload
        assert "services" in payload
        assert "control_plane" in payload
        assert "healthy" in payload
        assert payload["healthy"] is True

    def test_json_healthy_false_when_all_down(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        env: dict[str, str] = {}
        results = {
            "Google AI Studio": _FAILED,
            "Groq": _FAILED,
            "Ollama": _FAILED,
        }
        with _patch_status(providers=_ALL_PROVIDERS, validate_results=results, env=env):
            rc = cmd_status(
                _make_args(json_output=True), project_root=tmp_path, data_dir=tmp_path / ".tta"
            )
        payload = json.loads(capsys.readouterr().out)
        assert rc == 1
        assert payload["healthy"] is False

    def test_json_provider_list_matches_providers(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        env = {"GROQ_API_KEY": "grk"}
        results = {
            "Groq": _CONNECTED,
        }
        with _patch_status(providers=[_GROQ], validate_results=results, env=env):
            cmd_status(
                _make_args(json_output=True), project_root=tmp_path, data_dir=tmp_path / ".tta"
            )
        payload = json.loads(capsys.readouterr().out)
        assert len(payload["providers"]) == 1
        provider = payload["providers"][0]
        assert provider["name"] == "groq"
        assert provider["status"] == "healthy"
        assert provider["latency_ms"] is not None

    def test_json_control_plane_counts(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        env = {"GROQ_API_KEY": "grk"}
        results = {"Groq": _CONNECTED}
        with _patch_status(
            providers=[_GROQ],
            validate_results=results,
            env=env,
            active_tasks=5,
            active_runs=2,
        ):
            cmd_status(
                _make_args(json_output=True), project_root=tmp_path, data_dir=tmp_path / ".tta"
            )
        payload = json.loads(capsys.readouterr().out)
        assert payload["control_plane"]["active_tasks"] == 5
        assert payload["control_plane"]["active_runs"] == 2
