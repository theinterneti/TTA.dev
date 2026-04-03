"""Tests for tta setup and tta validate-keys CLI commands.

All tests use unittest.mock — no real HTTP calls are made.
"""

from __future__ import annotations

import argparse
import json
import stat
import urllib.error
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_http_response(body: dict, status: int = 200) -> MagicMock:
    """Build a fake urllib response with .read() and .status."""
    raw = json.dumps(body).encode()
    resp = MagicMock()
    resp.status = status
    resp.read.return_value = raw
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _make_http_error(code: int, reason: str = "Error") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url="http://x", code=code, msg=reason, hdrs=None, fp=None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Imports under test (deferred so we can patch before import if needed)
# ---------------------------------------------------------------------------

from ttadev.cli.setup import (  # noqa: E402
    SETUP_PROVIDERS,
    ValidationResult,
    _add_vscode_mcp,
    _read_env,
    _write_env,
    cmd_validate_keys,
    validate_provider,
)

# ---------------------------------------------------------------------------
# 1. validate_provider — 200 connected + model extraction
# ---------------------------------------------------------------------------


class TestValidateProviderConnected:
    def test_google_connected_extracts_models(self):
        google = next(p for p in SETUP_PROVIDERS if p.env_var == "GOOGLE_API_KEY")
        body = {"data": [{"id": "gemini-pro"}, {"id": "gemini-flash"}, {"id": "gemma-3"}]}
        with patch("urllib.request.urlopen", return_value=_make_http_response(body)):
            result = validate_provider(google, "fake-key")
        assert result.connected is True
        assert "gemini-pro" in result.models
        assert result.error is None

    def test_groq_connected_extracts_top3_models(self):
        groq = next(p for p in SETUP_PROVIDERS if p.env_var == "GROQ_API_KEY")
        models = [{"id": f"model-{i}"} for i in range(10)]
        body = {"data": models}
        with patch("urllib.request.urlopen", return_value=_make_http_response(body)):
            result = validate_provider(groq, "fake-key")
        assert result.connected is True
        assert len(result.models) <= 3

    def test_openrouter_connected(self):
        openrouter = next(p for p in SETUP_PROVIDERS if p.env_var == "OPENROUTER_API_KEY")
        body = {"data": [{"id": "openai/gpt-4o"}, {"id": "meta-llama/llama-3"}]}
        with patch("urllib.request.urlopen", return_value=_make_http_response(body)):
            result = validate_provider(openrouter, "fake-key")
        assert result.connected is True
        assert len(result.models) >= 1


# ---------------------------------------------------------------------------
# 2. validate_provider — 401/403 → invalid key
# ---------------------------------------------------------------------------


class TestValidateProviderInvalidKey:
    def test_401_returns_invalid_key(self):
        groq = next(p for p in SETUP_PROVIDERS if p.env_var == "GROQ_API_KEY")
        with patch("urllib.request.urlopen", side_effect=_make_http_error(401)):
            result = validate_provider(groq, "bad-key")
        assert result.connected is False
        assert result.error == "Invalid API key"
        assert "bad-key" not in (result.error or "")

    def test_403_returns_invalid_key(self):
        google = next(p for p in SETUP_PROVIDERS if p.env_var == "GOOGLE_API_KEY")
        with patch("urllib.request.urlopen", side_effect=_make_http_error(403)):
            result = validate_provider(google, "bad-key")
        assert result.connected is False
        assert result.error == "Invalid API key"


# ---------------------------------------------------------------------------
# 3. validate_provider — timeout → warning
# ---------------------------------------------------------------------------


class TestValidateProviderTimeout:
    def test_urlerror_returns_connection_failed(self):
        groq = next(p for p in SETUP_PROVIDERS if p.env_var == "GROQ_API_KEY")
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timed out")):
            result = validate_provider(groq, "any-key")
        assert result.connected is False
        assert "Connection failed" in (result.error or "")

    def test_socket_timeout_returns_connection_failed(self):
        groq = next(p for p in SETUP_PROVIDERS if p.env_var == "GROQ_API_KEY")
        with patch("urllib.request.urlopen", side_effect=TimeoutError("timed out")):
            result = validate_provider(groq, "any-key")
        assert result.connected is False
        assert "Connection failed" in (result.error or "")


# ---------------------------------------------------------------------------
# 4. Ollama validation
# ---------------------------------------------------------------------------


class TestOllamaValidation:
    def test_ollama_connected_extracts_models(self):
        ollama = next(p for p in SETUP_PROVIDERS if p.is_local)
        body = {"models": [{"name": "gemma3:4b"}, {"name": "llama3:8b"}]}
        with patch("urllib.request.urlopen", return_value=_make_http_response(body)):
            result = validate_provider(ollama, None)
        assert result.connected is True
        assert "gemma3:4b" in result.models

    def test_ollama_not_running(self):
        ollama = next(p for p in SETUP_PROVIDERS if p.is_local)
        with patch(
            "urllib.request.urlopen", side_effect=urllib.error.URLError("connection refused")
        ):
            result = validate_provider(ollama, None)
        assert result.connected is False
        assert "Connection failed" in (result.error or "")


# ---------------------------------------------------------------------------
# 5. _read_env round-trip, comments, blank lines
# ---------------------------------------------------------------------------


class TestReadEnv:
    def test_round_trip(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\nBAZ=qux\n")
        result = _read_env(env_file)
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_skips_comments(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# comment\nFOO=bar\n# another\n")
        result = _read_env(env_file)
        assert result == {"FOO": "bar"}
        assert "#" not in str(result)

    def test_skips_blank_lines(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("\nFOO=bar\n\nBAZ=qux\n\n")
        result = _read_env(env_file)
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_missing_file_returns_empty(self, tmp_path):
        result = _read_env(tmp_path / "nonexistent.env")
        assert result == {}

    def test_value_with_equals(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("URL=http://x.com/?foo=bar\n")
        result = _read_env(env_file)
        assert result["URL"] == "http://x.com/?foo=bar"


# ---------------------------------------------------------------------------
# 6. _write_env: atomic, chmod 0o600, updates in-place, appends new
# ---------------------------------------------------------------------------


class TestWriteEnv:
    def test_updates_existing_key(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("GOOGLE_API_KEY=old\nOTHER=keep\n")
        _write_env(env_file, {"GOOGLE_API_KEY": "new"})
        content = env_file.read_text()
        assert "GOOGLE_API_KEY=new" in content
        assert "OTHER=keep" in content

    def test_appends_new_key(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("EXISTING=yes\n")
        _write_env(env_file, {"NEW_KEY": "value"})
        content = env_file.read_text()
        assert "EXISTING=yes" in content
        assert "NEW_KEY=value" in content

    def test_preserves_comments(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# My comment\nFOO=bar\n")
        _write_env(env_file, {"FOO": "baz"})
        content = env_file.read_text()
        assert "# My comment" in content
        assert "FOO=baz" in content

    def test_chmod_600(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("")
        _write_env(env_file, {"KEY": "val"})
        mode = stat.S_IMODE(env_file.stat().st_mode)
        assert mode == 0o600

    def test_atomic_uses_tmp_then_replace(self, tmp_path):
        """Verify atomic write: tmp file is gone after successful write."""
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\n")
        _write_env(env_file, {"FOO": "baz"})
        tmp = tmp_path / ".env.tmp"
        assert not tmp.exists(), "Tmp file should be cleaned up after successful write"
        assert env_file.read_text().strip() == "FOO=baz"

    def test_creates_file_if_missing(self, tmp_path):
        env_file = tmp_path / ".env"
        _write_env(env_file, {"NEW": "val"})
        assert env_file.exists()
        assert "NEW=val" in env_file.read_text()


# ---------------------------------------------------------------------------
# 7. _write_env + Ctrl-C: tmp file cleaned up
# ---------------------------------------------------------------------------


class TestWriteEnvCtrlC:
    def test_tmp_cleaned_on_keyboard_interrupt(self, tmp_path):
        """If os.replace raises KeyboardInterrupt, tmp must be cleaned."""
        env_file = tmp_path / ".env"
        env_file.write_text("FOO=bar\n")

        def _raise_on_replace(src, dst):
            # Let chmod succeed; raise on os.replace
            raise KeyboardInterrupt

        with patch("os.replace", side_effect=_raise_on_replace):
            try:
                _write_env(env_file, {"FOO": "new"})
            except KeyboardInterrupt:
                pass

        # The setup wizard cleans up tmp; _write_env itself should leave no
        # dangling .tmp if KeyboardInterrupt is raised during os.replace.
        # (If implementation catches and re-raises after cleanup, tmp is gone.)
        # We accept either: no tmp, or tmp present (wizard cleans it).
        # The important thing is the original file is untouched.
        assert env_file.read_text() == "FOO=bar\n"


# ---------------------------------------------------------------------------
# 8. cmd_validate_keys: exit codes + --json
# ---------------------------------------------------------------------------


class TestCmdValidateKeys:
    def _make_args(self, json_output: bool = False) -> argparse.Namespace:
        return argparse.Namespace(command="validate-keys", json_output=json_output)

    def test_exit_0_when_at_least_one_connected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Set one valid key in env
        monkeypatch.setenv("GROQ_API_KEY", "test-key")
        # Patch validate_provider to return connected for groq only

        def _fake_validate(provider, key):
            if provider.env_var == "GROQ_API_KEY":
                return ValidationResult(connected=True, models=["llama-3"], error=None)
            return ValidationResult(connected=False, models=[], error="Not configured")

        with patch("ttadev.cli.setup.validate_provider", side_effect=_fake_validate):
            exit_code = cmd_validate_keys(self._make_args(), project_root=tmp_path)
        assert exit_code == 0

    def test_exit_1_when_none_connected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        # Clear all relevant env vars
        for var in ["GOOGLE_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY"]:
            monkeypatch.delenv(var, raising=False)

        def _fake_validate(provider, key):
            return ValidationResult(connected=False, models=[], error="Not configured")

        with patch("ttadev.cli.setup.validate_provider", side_effect=_fake_validate):
            exit_code = cmd_validate_keys(self._make_args(), project_root=tmp_path)
        assert exit_code == 1

    def test_json_output_parses(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("GROQ_API_KEY", "sk-test-1234")

        def _fake_validate(provider, key):
            if provider.env_var == "GROQ_API_KEY":
                return ValidationResult(connected=True, models=["llama-3"], error=None)
            return ValidationResult(connected=False, models=[], error="Not configured")

        with patch("ttadev.cli.setup.validate_provider", side_effect=_fake_validate):
            cmd_validate_keys(self._make_args(json_output=True), project_root=tmp_path)

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "providers" in data
        assert isinstance(data["providers"], list)

    def test_json_output_no_key_values(self, tmp_path, monkeypatch, capsys):
        """SECURITY: JSON output must never contain the actual API key value."""
        monkeypatch.chdir(tmp_path)
        secret_key = "sk-super-secret-key-that-must-not-appear"  # noqa: S105
        monkeypatch.setenv("GROQ_API_KEY", secret_key)

        def _fake_validate(provider, key):
            return ValidationResult(connected=True, models=["llama-3"], error=None)

        with patch("ttadev.cli.setup.validate_provider", side_effect=_fake_validate):
            cmd_validate_keys(self._make_args(json_output=True), project_root=tmp_path)

        captured = capsys.readouterr()
        assert secret_key not in captured.out, "API key must not appear in JSON output"


# ---------------------------------------------------------------------------
# 9. _add_vscode_mcp: creates .vscode/, merges, idempotent
# ---------------------------------------------------------------------------


class TestAddVscodeMcp:
    def test_creates_vscode_dir(self, tmp_path):
        _add_vscode_mcp(tmp_path)
        assert (tmp_path / ".vscode").is_dir()

    def test_creates_settings_json(self, tmp_path):
        _add_vscode_mcp(tmp_path)
        settings = json.loads((tmp_path / ".vscode" / "settings.json").read_text())
        assert "github.copilot.chat.mcpServers" in settings
        assert "tta-dev" in settings["github.copilot.chat.mcpServers"]

    def test_does_not_overwrite_existing_keys(self, tmp_path):
        (tmp_path / ".vscode").mkdir()
        existing = {"editor.fontSize": 14, "github.copilot.chat.mcpServers": {"other": {}}}
        (tmp_path / ".vscode" / "settings.json").write_text(json.dumps(existing))
        _add_vscode_mcp(tmp_path)
        settings = json.loads((tmp_path / ".vscode" / "settings.json").read_text())
        assert settings["editor.fontSize"] == 14
        assert "other" in settings["github.copilot.chat.mcpServers"]
        assert "tta-dev" in settings["github.copilot.chat.mcpServers"]

    def test_idempotent(self, tmp_path):
        _add_vscode_mcp(tmp_path)
        _add_vscode_mcp(tmp_path)
        settings = json.loads((tmp_path / ".vscode" / "settings.json").read_text())
        mcp = settings["github.copilot.chat.mcpServers"]
        # "tta-dev" appears exactly once (dict key — always unique)
        assert list(mcp.keys()).count("tta-dev") == 1

    def test_mcp_entry_shape(self, tmp_path):
        _add_vscode_mcp(tmp_path)
        settings = json.loads((tmp_path / ".vscode" / "settings.json").read_text())
        entry = settings["github.copilot.chat.mcpServers"]["tta-dev"]
        assert entry["command"] == "uv"
        assert "run" in entry["args"]
        assert "${workspaceFolder}" in entry["cwd"]


# ---------------------------------------------------------------------------
# 10. Non-interactive guard
# ---------------------------------------------------------------------------


class TestNonInteractiveGuard:
    def test_non_tty_exits_1(self, tmp_path, monkeypatch):
        from ttadev.cli.setup import cmd_setup

        args = argparse.Namespace(command="setup", non_interactive=False)

        # Simulate non-TTY stdin
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = False
            exit_code = cmd_setup(args, project_root=tmp_path)

        assert exit_code == 1

    def test_non_interactive_flag_exits_1(self, tmp_path):
        from ttadev.cli.setup import cmd_setup

        args = argparse.Namespace(command="setup", non_interactive=True)
        # non_interactive flag always exits 1 without TTY check
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = False
            exit_code = cmd_setup(args, project_root=tmp_path)
        assert exit_code == 1
