#!/usr/bin/env python3
"""Session-end auto-retain: called by Claude Code Stop hook.

Reads recent git commits, posts a summary to Hindsight retain endpoint.
Exits 0 always — never blocks the session.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import httpx

_DEFAULT_URL = "http://localhost:8888"
_DEFAULT_BANK = "tta-dev"
_TIMEOUT = 5.0


def _slugify(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-") or "workspace"


def _git_root() -> Path | None:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        timeout=_TIMEOUT,
        check=False,
    )
    if result.returncode != 0:
        return None
    root = result.stdout.strip()
    return Path(root).resolve() if root else None


def _default_project_bank() -> str:
    git_root = _git_root()
    root = git_root or Path.cwd().resolve()
    kind = "project" if git_root is not None else "workspace"
    digest = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:8]
    return f"{kind}-{_slugify(root.name or kind)}-{digest}"


def _target_bank() -> str:
    return (
        os.environ.get("HINDSIGHT_BANK")
        or os.environ.get("COPILOT_HINDSIGHT_PROJECT_BANK")
        or os.environ.get("HINDSIGHT_PROJECT_BANK")
        or _default_project_bank()
        or _DEFAULT_BANK
    )


def _git_log(n: int = 10) -> str:
    """Return last n commit subject lines, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"-{n}"],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _retain(base_url: str, bank_id: str, content: str) -> bool:
    """POST content to Hindsight retain. Returns True on success."""
    try:
        url = f"{base_url}/v1/default/banks/{bank_id}/memories"
        resp = httpx.post(
            url,
            json={"items": [{"content": content}], "async": True},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return True
    except Exception as exc:
        print(f"auto_retain: Hindsight unavailable, skipping ({exc})", file=sys.stderr)
        return False


def main() -> None:
    base_url = os.environ.get("HINDSIGHT_URL", _DEFAULT_URL).rstrip("/")
    bank_id = _target_bank()
    commits = _git_log()
    subjects = commits if commits else "no commits this session"
    content = f"[type: session-end] {date.today()} — {subjects}"
    _retain(base_url, bank_id, content)


if __name__ == "__main__":
    main()
    sys.exit(0)  # always exit 0
