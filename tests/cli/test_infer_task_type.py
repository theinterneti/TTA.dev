"""Stress tests for infer_task_type() — 50 prompt cases covering clear hits,
edge cases, multi-signal prompts, and known gaps.

Run with:
    uv run pytest tests/cli/test_infer_task_type.py -v
"""

import pytest

from ttadev.cli.models import infer_task_type

# ---------------------------------------------------------------------------
# Clear-hit cases (unambiguous single category)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "prompt,expected",
    [
        # coding
        ("Write a Python function to reverse a string", "coding"),
        ("Help me debug this class method", "coding"),
        ("Refactor the backend API endpoint", "coding"),
        ("Build a frontend component in React", "coding"),
        ("I need to implement a binary search algorithm", "coding"),
        ("Automate this script to run daily", "coding"),
        # chat
        ("I want to build a customer service chatbot", "chat"),
        ("Set up a helpdesk bot for my website", "chat"),
        ("Create a conversational assistant for Q&A", "chat"),
        ("Design a dialogue system for customer support", "chat"),
        # reasoning
        ("Analyze the pros and cons of this architecture", "reasoning"),
        ("Think through the tradeoffs of this design decision", "reasoning"),
        ("Explain why this algorithm is O(n log n)", "reasoning"),
        ("Plan a migration strategy for our database", "reasoning"),
        # math
        ("Solve this differential equation", "math"),
        ("Calculate the compound interest formula", "math"),
        ("Help with linear algebra matrix operations", "math"),
        ("Compute statistics on this dataset", "math"),
        # function_calling
        ("Build an agent that orchestrates API calls", "function_calling"),
        ("Create a tool-calling workflow for my pipeline", "function_calling"),
        ("Wire up function calls to my backend integrations", "function_calling"),
        # vision
        ("Analyze this image for defects", "vision"),
        ("Extract text via OCR from a screenshot", "vision"),
        ("Describe what is in this photo", "vision"),
        ("Generate a chart from this data", "vision"),
        # general
        ("Summarize this document for me", "general"),
        ("Translate this text to French", "general"),
        ("Write a blog post about machine learning", "general"),
        ("", "general"),
        ("   ", "general"),
    ],
)
def test_clear_hit(prompt: str, expected: str) -> None:
    assert infer_task_type(prompt) == expected, (
        f"prompt={str(prompt)[:60]!r}  got={infer_task_type(prompt)!r}  want={expected!r}"
    )


# ---------------------------------------------------------------------------
# Priority / tie-breaking cases
# (function_calling > vision > math > coding > reasoning > chat > general)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "prompt,expected",
    [
        # function_calling beats coding when both match
        (
            "Build a code pipeline that orchestrates tool calls",
            "function_calling",
        ),
        # vision beats coding when both match
        ("Write code to analyze an image", "vision"),
        # math beats coding when both match (but only if math keyword present)
        ("Write code to solve algebraic equations", "math"),
        # coding beats reasoning when both match
        ("Analyze and refactor my backend code", "coding"),
        # chat beats reasoning here — "chatbot"/"dialogue"/"bot" score 4 for chat,
        # "think" scores 1 for reasoning; chat wins decisively (not a tie).
        ("Think through the best chatbot dialogue strategy", "chat"),
    ],
)
def test_priority_tiebreak(prompt: str, expected: str) -> None:
    result = infer_task_type(prompt)
    assert result == expected, f"prompt={str(prompt)[:80]!r}  got={result!r}  want={expected!r}"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_empty_string_returns_general() -> None:
    assert infer_task_type("") == "general"


def test_whitespace_only_returns_general() -> None:
    assert infer_task_type("   \t\n  ") == "general"


def test_case_insensitive() -> None:
    assert infer_task_type("WRITE A FUNCTION") == "coding"
    assert infer_task_type("Help Me Debug My CODE") == "coding"


def test_partial_keyword_match() -> None:
    """'calculat' keyword matches 'calculating', 'calculate', 'calculated'."""
    assert infer_task_type("I am calculating Pi to 1000 digits") == "math"
    assert infer_task_type("This is calculated automatically") == "math"


def test_multiword_keyword() -> None:
    """'function call' is a multiword keyword — must match as substring."""
    assert infer_task_type("Use function call syntax in the agent") == "function_calling"
    assert infer_task_type("Enable tool call routing in my pipeline") == "function_calling"


def test_very_long_prompt() -> None:
    """Should not error or take excessive time on long inputs."""
    long = "debug " * 500
    assert infer_task_type(long) == "coding"


def test_non_english_gibberish_returns_general() -> None:
    assert infer_task_type("фото диаграмма") == "general"


def test_single_keyword_exact() -> None:
    assert infer_task_type("code") == "coding"
    assert infer_task_type("vision") == "vision"
    assert infer_task_type("math") == "math"


# ---------------------------------------------------------------------------
# Known-gap / ambiguous prompts — document current behaviour
# These may change as the keyword taxonomy improves; marked with xfail
# where the current result is arguably wrong.
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    reason="'agent' keyword maps to function_calling; 'write' maps to general. "
    "function_calling wins on priority — this is arguably correct but note "
    "the user may just mean a software agent class (coding).",
    strict=False,
)
def test_ambiguous_agent_as_coding() -> None:
    """User writing a software 'agent' class — could be coding OR function_calling."""
    result = infer_task_type("Write an agent class that handles retries")
    assert result == "coding"


def test_ambiguous_plan_reasoning() -> None:
    """'plan' keyword → reasoning; 'plan' in a coding context still returns reasoning."""
    result = infer_task_type("Plan the database schema")
    # Documenting current behaviour (reasoning wins over coding here)
    assert result == "reasoning"


def test_workflow_function_calling() -> None:
    """'workflow' maps to function_calling — verify this is expected."""
    result = infer_task_type("Design a workflow for my ETL pipeline")
    assert result == "function_calling"


@pytest.mark.xfail(
    reason="'Build a QA system': 'build' → coding (1pt), 'qa' → chat (1pt). "
    "Tie broken by priority (coding > chat). Semantically the intent is chat. "
    "Fix: weight 'qa'/'q&a' more heavily, or add more chat-domain keywords.",
    strict=True,
)
def test_qa_chat() -> None:
    """'qa' keyword maps to chat — but 'build' ties it with coding (known gap)."""
    assert infer_task_type("Build a QA system") == "chat"


# ---------------------------------------------------------------------------
# Return type contract
# ---------------------------------------------------------------------------

VALID_TASK_TYPES = frozenset(
    ["coding", "reasoning", "math", "chat", "function_calling", "vision", "general"]
)


@pytest.mark.parametrize(
    "prompt",
    [
        "random prompt xyz",
        "a",
        "123",
        "!@#$%",
        "help",
    ],
)
def test_always_returns_valid_task_type(prompt: str) -> None:
    result = infer_task_type(prompt)
    assert result in VALID_TASK_TYPES, f"Invalid task type {result!r} for {prompt!r}"
