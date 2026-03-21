#!/usr/bin/env python3
"""Session-start directives: called by Claude Code UserPromptSubmit hook.

Ensures Hindsight is running (starts Docker container if needed), then
fetches directives and prints them as Markdown to stdout.
Claude Code injects stdout into the conversation context.
Exits 0 always — never blocks the session.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

import httpx

_DEFAULT_URL = "http://localhost:8888"
_DEFAULT_BANK = "tta-dev"
_TIMEOUT = 2.0  # must not slow session start
_CONTAINER = "hindsight"
_STARTUP_WAIT = 3.0  # seconds to wait after docker start


def _is_healthy(base_url: str) -> bool:
    """Return True if Hindsight health endpoint responds."""
    try:
        httpx.get(f"{base_url}/health", timeout=1.0).raise_for_status()
        return True
    except Exception:
        return False


def _ensure_hindsight(base_url: str) -> bool:
    """Start Hindsight Docker container if not running. Returns True if available."""
    if _is_healthy(base_url):
        return True
    # Not responding — try to start the container
    result = subprocess.run(
        ["docker", "start", _CONTAINER],
        capture_output=True,
        timeout=10,
    )
    if result.returncode != 0:
        return False
    time.sleep(_STARTUP_WAIT)
    return _is_healthy(base_url)


def _get_directives(base_url: str, bank_id: str) -> list[str]:
    """Fetch directive texts from Hindsight. Returns [] on any failure."""
    try:
        url = f"{base_url}/v1/default/banks/{bank_id}/directives"
        resp = httpx.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("directives", []) if isinstance(data, dict) else data
        return [
            d.get("content") or d.get("text", "")
            for d in items
            if d.get("content") or d.get("text")
        ]
    except Exception:
        return []


def main() -> None:
    base_url = os.environ.get("HINDSIGHT_URL", _DEFAULT_URL).rstrip("/")
    bank_id = os.environ.get("HINDSIGHT_BANK", _DEFAULT_BANK)

    available = _ensure_hindsight(base_url)
    if not available:
        print("<!-- Hindsight unavailable — no directives loaded -->")
        return

    directives = _get_directives(base_url, bank_id)
    if not directives:
        return  # up but empty bank — silent
    print("## Hindsight Directives (auto-loaded)")
    for d in directives:
        print(f"- {d}")


if __name__ == "__main__":
    main()
    sys.exit(0)
