"""Unit tests for ttadev.observability.agent_identity — Task 1."""

import importlib
import sys
from unittest.mock import patch


def _reload_module():
    """Re-import agent_identity with a clean module cache so singletons reset."""
    mod_name = "ttadev.observability.agent_identity"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    return importlib.import_module(mod_name)


class TestGetAgentId:
    def test_returns_non_empty_string(self):
        m = _reload_module()
        result = m.get_agent_id()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_stable_across_repeated_calls(self):
        m = _reload_module()
        assert m.get_agent_id() == m.get_agent_id()

    def test_env_var_override(self):
        with patch.dict("os.environ", {"TTA_AGENT_ID": "my-fixed-id"}, clear=False):
            m = _reload_module()
            assert m.get_agent_id() == "my-fixed-id"

    def test_looks_like_uuid_when_no_override(self):
        import re

        with patch.dict("os.environ", {}, clear=False):
            # Remove override if present
            env = {k: v for k, v in __import__("os").environ.items() if k != "TTA_AGENT_ID"}
            with patch.dict("os.environ", env, clear=True):
                m = _reload_module()
                uuid_re = re.compile(
                    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
                )
                assert uuid_re.match(m.get_agent_id()), f"Not a UUID: {m.get_agent_id()}"


class TestGetAgentTool:
    def test_claude_code_claudecode_env(self):
        with patch.dict("os.environ", {"CLAUDECODE": "1"}, clear=True):
            m = _reload_module()
            assert m.get_agent_tool() == "claude-code"

    def test_claude_code_entrypoint_env(self):
        with patch.dict("os.environ", {"CLAUDE_CODE_ENTRYPOINT": "cli"}, clear=True):
            m = _reload_module()
            assert m.get_agent_tool() == "claude-code"

    def test_copilot_vscode_term_program(self):
        with patch.dict("os.environ", {"TERM_PROGRAM": "vscode"}, clear=True):
            m = _reload_module()
            assert m.get_agent_tool() == "copilot"

    def test_cline_env(self):
        with patch.dict("os.environ", {"CLINE": "1"}, clear=True):
            m = _reload_module()
            assert m.get_agent_tool() == "cline"

    def test_unknown_when_no_match(self):
        with patch.dict("os.environ", {}, clear=True):
            m = _reload_module()
            assert m.get_agent_tool() == "unknown"

    def test_explicit_override_wins(self):
        with patch.dict(
            "os.environ",
            {"TTA_AGENT_TOOL": "my-bot", "CLAUDECODE": "1"},
            clear=True,
        ):
            m = _reload_module()
            assert m.get_agent_tool() == "my-bot"

    def test_stable_across_repeated_calls(self):
        with patch.dict("os.environ", {}, clear=True):
            m = _reload_module()
            assert m.get_agent_tool() == m.get_agent_tool()
