#!/usr/bin/env python3
"""PreToolUse hook: require CGC orientation before editing core source.

Fires before Edit or Write tool calls.
If the target file is under a core ttadev/ package and CGC has not been
called this session, denies the edit with instructions on what to call first.

Core packages (non-trivial targets per CLAUDE.md):
  ttadev/control_plane/
  ttadev/primitives/
  ttadev/agents/
  ttadev/integrations/
  ttadev/observability/
  ttadev/cli/

Run via .claude/settings.json hooks.PreToolUse.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from cchooks import create_context
from cchooks.contexts.pre_tool_use import PreToolUseContext

# Directories that require CGC orientation before editing.
# Relative to the project root (no leading slash).
CORE_PACKAGES = (
    "ttadev/control_plane/",
    "ttadev/primitives/",
    "ttadev/agents/",
    "ttadev/integrations/",
    "ttadev/observability/",
    "ttadev/cli/",
)

EDIT_TOOLS = {"Edit", "Write"}

_FLAG_DIR = Path(os.environ.get("TMPDIR", "/tmp")) / "tta_hooks"

# Sibling session flags older than this are considered stale and ignored.
_SIBLING_FLAG_TTL_SECONDS = 4 * 3600  # 4 hours


def _flag_path(session_id: str) -> Path:
    return _FLAG_DIR / session_id / "cgc_oriented"


def _is_core_file(file_path: str, cwd: str) -> bool:
    """Return True if file_path resolves to a core ttadev package."""
    # Normalise to a path relative to project root
    resolved = Path(file_path)
    if not resolved.is_absolute():
        resolved = Path(cwd) / resolved

    try:
        # Make relative to cwd (project root)
        rel = resolved.relative_to(cwd)
        rel_str = str(rel)
    except ValueError:
        # File is outside the project — not our concern
        return False

    return any(rel_str.startswith(pkg) for pkg in CORE_PACKAGES)


def _cgc_oriented(session_id: str) -> bool:
    # Check the specific session first (fast path).
    if _flag_path(session_id).exists():
        return True
    # Sub-agent contexts may use a different session ID for MCP tool calls vs
    # Edit/Write calls.  Accept orientation if any sibling session in the same
    # flag dir has been marked — the intent (CGC was called this process tree)
    # is satisfied.  Only accept flags that are fresh enough (< _SIBLING_FLAG_TTL_SECONDS
    # old) to avoid stale flags from previous days permanently bypassing the gate.
    if _FLAG_DIR.is_dir():
        cutoff = time.time() - _SIBLING_FLAG_TTL_SECONDS
        for entry in _FLAG_DIR.iterdir():
            if not entry.is_dir():
                continue
            flag = entry / "cgc_oriented"
            if flag.exists() and flag.stat().st_mtime >= cutoff:
                return True
    return False


_GUIDANCE = """\
CGC orientation required before editing core TTA.dev source.

Call BOTH of these first:
  1. mcp__codegraphcontext__find_code  (search for the symbol or file you're modifying)
  2. mcp__codegraphcontext__analyze_code_relationships  (understand callers/callees/deps)

Why: CLAUDE.md Non-Negotiable Standard — "Orient before edit: Run CGC \
(find_code + analyze_code_relationships) on any non-trivial target before touching it."

After calling either tool, this gate clears automatically for the rest of the session.
If you have already oriented via get_repository_stats, call it again to set the session flag.\
"""


def main() -> None:
    ctx = create_context()

    if not isinstance(ctx, PreToolUseContext):
        return

    if ctx.tool_name not in EDIT_TOOLS:
        ctx.output.allow()
        return

    file_path = ctx.tool_input.get("file_path", "")
    if not file_path:
        ctx.output.allow()
        return

    if not _is_core_file(file_path, ctx.cwd):
        ctx.output.allow()
        return

    if _cgc_oriented(ctx.session_id):
        ctx.output.allow()
        return

    # Not oriented — soft-block with instructions
    ctx.output.deny(
        reason="[cgc-gate] CGC orientation required before editing core source.",
        system_message=_GUIDANCE,
    )


if __name__ == "__main__":
    main()
