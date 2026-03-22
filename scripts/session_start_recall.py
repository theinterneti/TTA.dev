#!/usr/bin/env python3
"""Session-start directives: called by Claude Code UserPromptSubmit hook.

Ensures Hindsight is running (starts Docker container if needed), then
fetches directives and prints them as Markdown to stdout.
Claude Code injects stdout into the conversation context.
Exits 0 always — never blocks the session.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

_DEFAULT_URL = "http://localhost:8888"
_DEFAULT_BANK = "tta-dev"
_DEFAULT_GLOBAL_BANK = "adam-global"
_TIMEOUT = 2.0  # must not slow session start
_CONTAINER = "hindsight"
_STARTUP_WAIT = 3.0  # seconds to wait after docker start


def _slugify(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-") or "workspace"


def _git_root() -> Path | None:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        timeout=5,
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


def _candidate_banks() -> list[str]:
    explicit = os.environ.get("HINDSIGHT_BANK")
    if explicit:
        return [explicit]

    banks: list[str] = []
    for candidate in (
        os.environ.get("COPILOT_HINDSIGHT_GLOBAL_BANK"),
        os.environ.get("HINDSIGHT_GLOBAL_BANK"),
        _DEFAULT_GLOBAL_BANK,
        os.environ.get("COPILOT_HINDSIGHT_PROJECT_BANK"),
        os.environ.get("HINDSIGHT_PROJECT_BANK"),
        _default_project_bank(),
        _DEFAULT_BANK,
    ):
        if candidate and candidate not in banks:
            banks.append(candidate)
    return banks


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
        items = data.get("directives", data.get("items", [])) if isinstance(data, dict) else data
        return [
            d.get("content") or d.get("text", "")
            for d in items
            if d.get("content") or d.get("text")
        ]
    except Exception:
        return []


def main() -> None:
    base_url = os.environ.get("HINDSIGHT_URL", _DEFAULT_URL).rstrip("/")

    available = _ensure_hindsight(base_url)
    if not available:
        print("<!-- Hindsight unavailable — no directives loaded -->")
        return

    directives: list[str] = []
    seen: set[str] = set()
    for bank_id in _candidate_banks():
        for directive in _get_directives(base_url, bank_id):
            if directive not in seen:
                directives.append(directive)
                seen.add(directive)
    if not directives:
        return  # up but empty bank — silent
    print("## Hindsight Directives (auto-loaded)")
    for d in directives:
        print(f"- {d}")


if __name__ == "__main__":
    main()
    sys.exit(0)
