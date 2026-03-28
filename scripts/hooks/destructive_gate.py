#!/usr/bin/env python3
"""PreToolUse hook: intercept destructive Bash operations.

Uses cchooks to classify Bash commands before execution:
- DENY:  patterns that are irreversible or high blast-radius
- ASK:   patterns that are reversible but significant
- ALLOW: everything else

Run via .claude/settings.local.json hooks.PreToolUse.
"""

import re

from cchooks import create_context
from cchooks.contexts.pre_tool_use import PreToolUseContext

# ── Patterns that are blocked outright ───────────────────────────────────────
DENY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b"),
        "rm -rf is irreversible — use git clean or trash-cli instead",
    ),
    (
        re.compile(r"\bgit\s+push\s+.*--force\b|\bgit\s+push\s+.*-f\b"),
        "Force-push can overwrite shared history — explicit user approval required",
    ),
    (
        re.compile(r"\bgit\s+reset\s+--hard\b"),
        "git reset --hard discards uncommitted work — explicit user approval required",
    ),
    (
        re.compile(r"\bdrop\s+table\b|\btruncate\s+table\b|\bdelete\s+from\b", re.IGNORECASE),
        "Destructive SQL operation — explicit user approval required",
    ),
    (
        re.compile(r"\bdocker\s+(system\s+prune|volume\s+prune|network\s+prune)\b"),
        "Docker prune is irreversible — explicit user approval required",
    ),
]

# ── Patterns that require user confirmation ───────────────────────────────────
ASK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\bgit\s+branch\s+-[Dd]\b"),
        "Deleting a git branch — confirm this is intentional",
    ),
    (
        re.compile(r"\bgit\s+stash\s+(drop|clear)\b"),
        "Dropping stash entries — confirm this is intentional",
    ),
    (
        re.compile(r"\bchmod\s+777\b"),
        "chmod 777 grants world-writable permissions — confirm this is intentional",
    ),
    (
        re.compile(r"\bkill\s+-9\b|\bkillall\b"),
        "Force-killing a process — confirm this is intentional",
    ),
    (
        re.compile(r"\bgit\s+checkout\s+--\b|\bgit\s+restore\b"),
        "Discarding working-tree changes — confirm this is intentional",
    ),
]


def _strip_git_commit_message(command: str) -> str:
    """Remove the commit message body from a git commit command.

    Prevents false positives when commit messages contain words like 'rm -rf'
    in documentation or change descriptions.
    """
    # Strip heredoc bodies: $(cat <<'EOF' ... EOF)
    command = re.sub(
        r"\$\(cat\s*<<['\"]?EOF['\"]?.*?EOF\s*\)",
        "$(cat <<'EOF' ... EOF)",
        command,
        flags=re.DOTALL,
    )
    # Strip -m "..." and -m '...' arguments
    command = re.sub(r'\s-m\s+(["\']).*?\1', ' -m ""', command, flags=re.DOTALL)
    return command


def _get_command(tool_input: dict) -> str | None:
    """Extract the command string from a Bash tool input."""
    return tool_input.get("command") or tool_input.get("cmd")


def main() -> None:
    ctx = create_context()

    if not isinstance(ctx, PreToolUseContext):
        return

    if ctx.tool_name != "Bash":
        ctx.output.allow()
        return

    command = _get_command(ctx.tool_input)
    if not command:
        ctx.output.allow()
        return

    # Strip commit message bodies before pattern matching to avoid false positives
    if "git commit" in command:
        command = _strip_git_commit_message(command)

    for pattern, reason in DENY_PATTERNS:
        if pattern.search(command):
            ctx.output.deny(
                reason=f"[destructive-gate] BLOCKED: {reason}",
                system_message=(
                    f"Destructive command intercepted.\n\nReason: {reason}\n\n"
                    "To proceed, explicitly confirm this action in your next message."
                ),
            )
            return

    for pattern, reason in ASK_PATTERNS:
        if pattern.search(command):
            ctx.output.ask(
                reason=f"[destructive-gate] CONFIRM: {reason}",
                system_message=(
                    f"Potentially significant command.\n\nReason: {reason}\n\n"
                    "Proceeding — interrupt if unintended."
                ),
            )
            return

    ctx.output.allow()


if __name__ == "__main__":
    main()
