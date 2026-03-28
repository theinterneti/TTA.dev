#!/usr/bin/env python3
"""PostToolUse hook: record that CGC was used this session.

Fires after any mcp__codegraphcontext__* tool call.
Writes a session-scoped flag file so require_cgc_before_edit.py can
confirm orientation happened before allowing edits to core source.

Run via .claude/settings.json hooks.PostToolUse.
"""

from __future__ import annotations

import os
from pathlib import Path

from cchooks import create_context
from cchooks.contexts.post_tool_use import PostToolUseContext

# CGC tools that count as "orientation" — any of these clears the gate
CGC_ORIENT_TOOLS = {
    "mcp__codegraphcontext__find_code",
    "mcp__codegraphcontext__analyze_code_relationships",
    "mcp__codegraphcontext__get_repository_stats",
    "mcp__codegraphcontext__find_dead_code",
    "mcp__codegraphcontext__find_most_complex_functions",
    "mcp__codegraphcontext__execute_cypher_query",
    "mcp__codegraphcontext__visualize_graph_query",
}

_FLAG_DIR = Path(os.environ.get("TMPDIR", "/tmp")) / "tta_hooks"


def _flag_path(session_id: str) -> Path:
    return _FLAG_DIR / session_id / "cgc_oriented"


def main() -> None:
    ctx = create_context()

    if not isinstance(ctx, PostToolUseContext):
        return  # exit 0 — allow by default for unexpected context types

    if ctx.tool_name not in CGC_ORIENT_TOOLS:
        ctx.output.accept()
        return

    # Mark this session as CGC-oriented
    flag = _flag_path(ctx.session_id)
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.touch()

    ctx.output.accept()


if __name__ == "__main__":
    main()
