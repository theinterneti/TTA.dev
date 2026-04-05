"""Unit tests for ``tta agents`` CLI subcommand group.

Tests
-----
T1  – ``agents list`` prints column headers and registered agent names.
T2  – ``agents list`` shows the count footer.
T3  – ``agents run <valid> <task> --dry-run`` exits 0 and prints plan, no API call.
T4  – ``agents run <valid> <task> --dry-run --timeout`` mentions TimeoutPrimitive.
T5  – ``agents run <invalid> <task>`` exits 1 and prints available agents.
T6  – ``agents run <invalid> <task>`` error message includes agent name.
T7  – ``handle_agents_command`` with no sub-command prints usage and returns 1.
T8  – ``agents run <valid> <task>`` without ANTHROPIC_API_KEY exits 1 (no mock model).
T9  – subprocess: ``tta agents list`` exits 0.
T10 – subprocess: ``tta agents run bad-agent "do something"`` exits 1.
T11 – subprocess: ``tta agents run developer "do something" --dry-run`` exits 0.
T12 – ``agents run`` dry-run output contains separator line.
T13 – ``agents list`` output is sorted alphabetically by agent name.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from ttadev.agents.registry import AgentRegistry, override_registry
from ttadev.agents.spec import AgentSpec
from ttadev.cli.agents import (
    _cmd_list,
    _cmd_run,
    handle_agents_command,
)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _make_args(**kwargs: object) -> argparse.Namespace:
    """Return a minimal Namespace for testing CLI handlers."""
    defaults: dict[str, object] = {
        "agents_command": None,
        "agent_name": "developer",
        "task": "add a docstring",
        "dry_run": False,
        "timeout": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the ``tta`` CLI as a subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "ttadev.cli", *args],
        capture_output=True,
        text=True,
    )


def _make_fake_agent(name: str, role: str = "Test Role") -> type:
    """Return a fake agent class with a ``_class_spec`` attribute."""
    spec = MagicMock(spec=AgentSpec)
    spec.name = name
    spec.role = role
    spec.capabilities = ["cap1", "cap2"]
    spec.system_prompt = f"System prompt for {name} agent."

    agent_cls = MagicMock()
    agent_cls._class_spec = spec
    return agent_cls  # type: ignore[return-value]


def _make_scoped_registry(*names: str) -> AgentRegistry:
    """Build an isolated registry pre-populated with fake agents."""
    reg = AgentRegistry()
    for name in names:
        reg.register(name, _make_fake_agent(name))
    return reg


# ─────────────────────────────────────────────────────────────────────────────
# T1 – agents list: column headers and agent names
# ─────────────────────────────────────────────────────────────────────────────


def test_agents_list_prints_headers(capsys: pytest.CaptureFixture[str]) -> None:
    """``agents list`` should print NAME / ROLE / CAPABILITIES column headers."""
    reg = _make_scoped_registry("developer")
    with override_registry(reg):
        rc = _cmd_list()
    out = capsys.readouterr().out
    assert rc == 0
    assert "NAME" in out
    assert "ROLE" in out
    assert "CAPABILITIES" in out


def test_agents_list_prints_agent_name(capsys: pytest.CaptureFixture[str]) -> None:
    """``agents list`` should display registered agent names."""
    reg = _make_scoped_registry("developer", "qa")
    with override_registry(reg):
        _cmd_list()
    out = capsys.readouterr().out
    assert "developer" in out
    assert "qa" in out


# ─────────────────────────────────────────────────────────────────────────────
# T2 – agents list: count footer
# ─────────────────────────────────────────────────────────────────────────────


def test_agents_list_prints_footer(capsys: pytest.CaptureFixture[str]) -> None:
    """``agents list`` should print the count footer line."""
    reg = _make_scoped_registry("developer", "qa", "git")
    with override_registry(reg):
        _cmd_list()
    out = capsys.readouterr().out
    assert "3 agent(s)" in out


# ─────────────────────────────────────────────────────────────────────────────
# T3 – dry-run exits 0 and prints plan without calling API
# ─────────────────────────────────────────────────────────────────────────────


def test_dry_run_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """``agents run <agent> <task> --dry-run`` should return 0."""
    reg = _make_scoped_registry("developer")
    args = _make_args(agent_name="developer", task="add docstrings", dry_run=True)
    with override_registry(reg):
        rc = _cmd_run(args)
    assert rc == 0


def test_dry_run_prints_agent_and_task(capsys: pytest.CaptureFixture[str]) -> None:
    """Dry-run output should contain the agent name and task."""
    reg = _make_scoped_registry("developer")
    args = _make_args(agent_name="developer", task="add docstrings", dry_run=True)
    with override_registry(reg):
        _cmd_run(args)
    out = capsys.readouterr().out
    assert "developer" in out
    assert "add docstrings" in out
    assert "dry-run" in out


def test_dry_run_no_api_call(capsys: pytest.CaptureFixture[str]) -> None:
    """Dry-run must not call any external API (no agent.execute called)."""
    reg = _make_scoped_registry("developer")
    args = _make_args(agent_name="developer", task="do something", dry_run=True)
    # If _run_agent were called it would try importing AnthropicPrimitive; patching
    # asyncio.run to catch any accidental execution.
    with override_registry(reg):
        with patch("asyncio.run") as mock_run:
            _cmd_run(args)
            mock_run.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# T4 – dry-run with --timeout mentions TimeoutPrimitive
# ─────────────────────────────────────────────────────────────────────────────


def test_dry_run_with_timeout_prints_timeout(capsys: pytest.CaptureFixture[str]) -> None:
    """``--dry-run --timeout N`` output should mention the timeout."""
    reg = _make_scoped_registry("developer")
    args = _make_args(agent_name="developer", task="task", dry_run=True, timeout=30.0)
    with override_registry(reg):
        _cmd_run(args)
    out = capsys.readouterr().out
    assert "30" in out
    assert "TimeoutPrimitive" in out


# ─────────────────────────────────────────────────────────────────────────────
# T5 – invalid agent exits 1 and lists available agents
# ─────────────────────────────────────────────────────────────────────────────


def test_invalid_agent_exits_one(capsys: pytest.CaptureFixture[str]) -> None:
    """``agents run <unknown>`` should return exit code 1."""
    reg = _make_scoped_registry("developer")
    args = _make_args(agent_name="nonexistent-agent", task="some task")
    with override_registry(reg):
        rc = _cmd_run(args)
    assert rc == 1


def test_invalid_agent_shows_available(
    capfd: pytest.CaptureFixture[str],
) -> None:
    """Error message for unknown agent should list registered agents."""
    reg = _make_scoped_registry("developer", "qa")
    args = _make_args(agent_name="nope", task="task")
    with override_registry(reg):
        _cmd_run(args)
    # Error is written to stderr
    err = capfd.readouterr().err
    assert "developer" in err or "qa" in err


# ─────────────────────────────────────────────────────────────────────────────
# T6 – error message includes the bad agent name
# ─────────────────────────────────────────────────────────────────────────────


def test_invalid_agent_error_includes_name(capfd: pytest.CaptureFixture[str]) -> None:
    """The error message should quote the unknown agent name."""
    reg = _make_scoped_registry("developer")
    args = _make_args(agent_name="ghost-agent", task="task")
    with override_registry(reg):
        _cmd_run(args)
    err = capfd.readouterr().err
    assert "ghost-agent" in err


# ─────────────────────────────────────────────────────────────────────────────
# T7 – no sub-command prints usage and returns 1
# ─────────────────────────────────────────────────────────────────────────────


def test_no_subcommand_returns_one(capsys: pytest.CaptureFixture[str]) -> None:
    """``handle_agents_command`` with no agents_command should return 1."""
    args = _make_args(agents_command=None)
    rc = handle_agents_command(args)
    assert rc == 1


def test_no_subcommand_prints_usage(capsys: pytest.CaptureFixture[str]) -> None:
    """``handle_agents_command`` with no agents_command should print usage."""
    args = _make_args(agents_command=None)
    handle_agents_command(args)
    out = capsys.readouterr().out
    assert "Usage" in out or "usage" in out


# ─────────────────────────────────────────────────────────────────────────────
# T8 – live run without ANTHROPIC_API_KEY exits 1
# ─────────────────────────────────────────────────────────────────────────────


def test_live_run_no_api_key_returns_one(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without ANTHROPIC_API_KEY, live run should fail gracefully (exit 1)."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    reg = _make_scoped_registry("developer")
    args = _make_args(agent_name="developer", task="do something", dry_run=False)
    with override_registry(reg):
        rc = _cmd_run(args)
    assert rc == 1


# ─────────────────────────────────────────────────────────────────────────────
# T9 – subprocess: tta agents list exits 0
# ─────────────────────────────────────────────────────────────────────────────


def test_subprocess_agents_list_exits_zero() -> None:
    """``tta agents list`` as a subprocess should exit 0."""
    result = _run_cli("agents", "list")
    assert result.returncode == 0, result.stderr


# ─────────────────────────────────────────────────────────────────────────────
# T10 – subprocess: unknown agent exits 1
# ─────────────────────────────────────────────────────────────────────────────


def test_subprocess_invalid_agent_exits_one() -> None:
    """``tta agents run bad-agent "do something"`` should exit 1."""
    result = _run_cli("agents", "run", "bad-agent", "do something")
    assert result.returncode == 1


# ─────────────────────────────────────────────────────────────────────────────
# T11 – subprocess: dry-run with valid agent exits 0
# ─────────────────────────────────────────────────────────────────────────────


def test_subprocess_dry_run_exits_zero() -> None:
    """``tta agents run developer "do something" --dry-run`` should exit 0."""
    result = _run_cli("agents", "run", "developer", "do something", "--dry-run")
    assert result.returncode == 0, result.stderr


# ─────────────────────────────────────────────────────────────────────────────
# T12 – dry-run output contains separator line
# ─────────────────────────────────────────────────────────────────────────────


def test_dry_run_output_contains_separator(capsys: pytest.CaptureFixture[str]) -> None:
    """Dry-run output should contain the ``─`` separator line."""
    reg = _make_scoped_registry("developer")
    args = _make_args(agent_name="developer", task="task", dry_run=True)
    with override_registry(reg):
        _cmd_run(args)
    out = capsys.readouterr().out
    assert "─" in out


# ─────────────────────────────────────────────────────────────────────────────
# T13 – agents list is sorted alphabetically
# ─────────────────────────────────────────────────────────────────────────────


def test_agents_list_sorted_alphabetically(capsys: pytest.CaptureFixture[str]) -> None:
    """``agents list`` output should sort agents alphabetically by name."""
    reg = _make_scoped_registry("qa", "developer", "git")
    with override_registry(reg):
        _cmd_list()
    out = capsys.readouterr().out
    lines = [line for line in out.splitlines() if line and not line.startswith("─")]
    name_lines = [
        line for line in lines if any(name in line for name in ("developer", "git", "qa"))
    ]
    names_in_order = []
    for line in name_lines:
        for name in ("developer", "git", "qa"):
            if line.strip().startswith(name):
                names_in_order.append(name)
    assert names_in_order == sorted(names_in_order)
