"""Shared utilities for agent keyword matching."""

from __future__ import annotations

import re

from ttadev.agents.task import AgentTask


def _matches(task: AgentTask, keywords: frozenset[str]) -> bool:
    """Return True if any keyword matches the task instruction.

    Uses word-boundary matching (``\\b``) so that short keywords like ``"pr"``
    only match when they appear as standalone words, not as substrings inside
    unrelated words (e.g. ``"pr"`` must not match ``"project"``).

    Multi-word keywords (e.g. ``"pull request"``) and longer single-word
    keywords work correctly: ``\\b`` anchors to the start and end of the
    full phrase.
    """
    text = task.instruction.lower()
    return any(bool(re.search(r"\b" + re.escape(kw) + r"\b", text)) for kw in keywords)
