#!/usr/bin/env python3
"""Session-end auto-retain: called by Claude Code Stop hook.

Reads recent git commits, posts a summary to Hindsight retain endpoint.
Exits 0 always — never blocks the session.
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import date

import httpx

_DEFAULT_URL = "http://localhost:8888"
_DEFAULT_BANK = "tta-dev"
_TIMEOUT = 5.0


def _git_log(n: int = 10) -> str:
    """Return last n commit subject lines, or empty string on failure."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", f"-{n}"],
            capture_output=True,
            text=True,
            timeout=5,
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
    bank_id = os.environ.get("HINDSIGHT_BANK", _DEFAULT_BANK)
    commits = _git_log()
    subjects = commits if commits else "no commits this session"
    content = f"[type: session-end] {date.today()} — {subjects}"
    _retain(base_url, bank_id, content)


if __name__ == "__main__":
    main()
    sys.exit(0)  # always exit 0
