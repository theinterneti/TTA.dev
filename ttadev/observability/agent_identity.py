"""Stable per-process agent identity.

Single source of truth for agent_id and agent_tool, shared by:
  - ttadev.primitives.observability.tracing (FileSpanExporter, setup_tracing)
  - ttadev.observability.session_manager (SessionManager.start_session)
  - ttadev.primitives.core.base (WorkflowContext auto-population)

Both values are generated/detected once at module import and cached.
Environment variable overrides take full precedence:
  TTA_AGENT_ID    — pin the agent UUID (useful in CI, tests, multi-agent scripts)
  TTA_AGENT_TOOL  — pin the tool name
"""

import os
import uuid

# ---------------------------------------------------------------------------
# Agent ID — stable UUID for this process
# ---------------------------------------------------------------------------

_AGENT_ID: str = os.environ.get("TTA_AGENT_ID") or str(uuid.uuid4())


def get_agent_id() -> str:
    """Return the stable agent ID for this process."""
    return _AGENT_ID


# ---------------------------------------------------------------------------
# Agent tool — which AI coding assistant is running this process
# ---------------------------------------------------------------------------

_AGENT_TOOL: str | None = None


def get_agent_tool() -> str:
    """Detect and cache which agent tool is running in this process.

    TTA_AGENT_TOOL is always checked first and takes precedence over the cache,
    so that tests and CI can override the value at any time.
    """
    global _AGENT_TOOL

    override = os.environ.get("TTA_AGENT_TOOL")
    if override:
        return override

    if _AGENT_TOOL is not None:
        return _AGENT_TOOL

    if os.environ.get("CLAUDECODE") or os.environ.get("CLAUDE_CODE") or os.environ.get("CLAUDE_CODE_ENTRYPOINT"):
        _AGENT_TOOL = "claude-code"
    elif "vscode" in os.environ.get("TERM_PROGRAM", "").lower():
        _AGENT_TOOL = "copilot"
    elif os.environ.get("CLINE"):
        _AGENT_TOOL = "cline"
    else:
        _AGENT_TOOL = "unknown"

    return _AGENT_TOOL
