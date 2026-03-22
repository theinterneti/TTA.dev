"""Quality gate: heuristic LLM response scorer.

score_response(response) -> float in [0.0, 1.0]
quality_gate_passed(response, threshold) -> bool
"""

from __future__ import annotations

import os
import re

_REFUSAL_PATTERNS: tuple[str, ...] = (
    "i cannot",
    "i'm unable to",
    "i am unable to",
    "i don't have access",
    "i do not have access",
    "i can't help",
    "i cannot help",
)

_AI_APOLOGY_PATTERNS: tuple[str, ...] = (
    "as an ai",
    "as a language model",
    "as an llm",
    "i'm just an ai",
    "i am just an ai",
)


# Read threshold from env at import time; default 0.5, clamped to [0.0, 1.0]
def _read_threshold() -> float:
    raw = os.environ.get("QUALITY_GATE_THRESHOLD", "")
    try:
        val = float(raw)
        return max(0.0, min(1.0, val))
    except (ValueError, TypeError):
        return 0.5


_DEFAULT_THRESHOLD: float = _read_threshold()


def score_response(response: str) -> float:
    """Score an LLM response for usefulness. Returns 0.0–1.0 (clamped).

    Penalty rules applied to the response string:
    - Empty or whitespace-only → 0.0 immediately
    - Length < 20 chars → penalty -0.8
    - Length < 80 chars → penalty -0.3 (stacks with above if < 20)
    - Refusal pattern match (case-insensitive) → penalty -0.6
    - AI apology pattern (case-insensitive) → penalty -0.4
    - No alphabetic content → penalty -0.5
    - Length > 200 chars → bonus +0.1
    - Length > 500 chars → bonus +0.1 (stacks)
    Score starts at 1.0. Penalties subtract. Bonuses add. Clamped to [0.0, 1.0].
    """
    # Rule 1: Empty or whitespace-only → 0.0 immediately
    if not response.strip():
        return 0.0

    score = 1.0
    length = len(response)

    # Rule 2: Length < 20 chars → penalty -0.8
    if length < 20:
        score -= 0.8

    # Rule 3: Length < 80 chars → penalty -0.3 (stacks)
    if length < 80:
        score -= 0.3

    # Rule 4 & 5: Check patterns (case-insensitive)
    lower = response.lower()

    # Rule 4: Refusal pattern → penalty -0.6
    if any(pattern in lower for pattern in _REFUSAL_PATTERNS):
        score -= 0.6

    # Rule 5: AI apology pattern → penalty -0.4
    if any(pattern in lower for pattern in _AI_APOLOGY_PATTERNS):
        score -= 0.4

    # Rule 6: No alphabetic content → penalty -0.5
    if not re.search(r"[a-zA-Z]", response):
        score -= 0.5

    # Rule 7: Length > 200 chars → bonus +0.1
    if length > 200:
        score += 0.1

    # Rule 8: Length > 500 chars → bonus +0.1 (stacks)
    if length > 500:
        score += 0.1

    # Return clamped to [0.0, 1.0]
    return max(0.0, min(1.0, score))


def quality_gate_passed(response: str, threshold: float = _DEFAULT_THRESHOLD) -> bool:
    """Return True if score_response(response) >= threshold."""
    return score_response(response) >= threshold
