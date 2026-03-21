#!/usr/bin/env python3
"""Session-start directives: called by Claude Code UserPromptSubmit hook.

Fetches Hindsight directives and prints them as Markdown to stdout.
Claude Code injects stdout into the conversation context.
Exits 0 silently on failure.
"""

from __future__ import annotations

import os
import sys

import httpx

_DEFAULT_URL = "http://localhost:8888"
_DEFAULT_BANK = "tta-dev"
_TIMEOUT = 2.0  # must not slow session start


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
    directives = _get_directives(base_url, bank_id)
    if not directives:
        return  # silent — don't pollute context with empty noise
    print("## Hindsight Directives (auto-loaded)")
    for d in directives:
        print(f"- {d}")


if __name__ == "__main__":
    main()
    sys.exit(0)
