"""Test MCP server instantiation from examples/mcp/."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure examples/ is importable
_EXAMPLES_PATH = Path(__file__).parents[2] / "examples"
if str(_EXAMPLES_PATH) not in sys.path:
    sys.path.insert(0, str(_EXAMPLES_PATH))


def _has_example(relative: str) -> bool:
    """Return True if examples/<relative>.py exists."""
    return (_EXAMPLES_PATH / relative).exists()


@pytest.mark.skipif(
    not _has_example("mcp/agent_tool_server.py"),
    reason="examples/mcp/agent_tool_server.py not present",
)
def test_agent_tool_server_instantiation():
    """Agent Tool MCP server imports cleanly and exposes expected attributes."""
    from examples.mcp.agent_tool_server import mcp  # type: ignore[import]

    assert mcp.name, "Server must have a non-empty name"
    assert hasattr(mcp, "run"), "Server must expose a run() method"
