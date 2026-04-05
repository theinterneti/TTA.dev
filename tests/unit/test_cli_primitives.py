"""Tests for `tta primitives list` and `tta primitives info` CLI commands.

Coverage targets
----------------
T1  – list_primitives prints category headers and known primitive names.
T2  – list_primitives prints the footer hint.
T3  – info_primitive prints module path and category for a known primitive.
T4  – info_primitive prints a description (docstring).
T5  – info_primitive prints an Example block when one exists in the docstring.
T6  – info_primitive returns exit-code 1 for an unknown name.
T7  – info_primitive suggests a correction on near-miss names.
T8  – info_primitive is case-insensitive for exact-match suggestion.
T9  – argparse dispatcher: ``tta primitives list`` subprocess exits 0.
T10 – argparse dispatcher: ``tta primitives info RetryPrimitive`` subprocess exits 0.
T11 – argparse dispatcher: ``tta primitives info UnknownXYZ`` subprocess exits 1.
T12 – ``tta primitives`` (no sub-command) exits 0 and prints help.
T13 – _CATALOGUE covers the 7 primitives highlighted in the issue.
T14 – _BY_NAME lookup is case-sensitive (exact match required).
"""

from __future__ import annotations

import argparse
import subprocess
import sys

import pytest

from ttadev.cli.primitives import (
    _BY_NAME,
    _CATALOGUE,
    _extract_example,
    _first_paragraph,
    handle_primitives_command,
    info_primitive,
    list_primitives,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_args(**kwargs: object) -> argparse.Namespace:
    """Build a minimal Namespace for command dispatch."""
    return argparse.Namespace(**kwargs)


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the `tta` CLI as a subprocess and return the result."""
    return subprocess.run(
        [sys.executable, "-m", "ttadev.cli", *args],
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# T1 – list_primitives: category headers and primitive names
# ---------------------------------------------------------------------------


def test_list_prints_category_headers(capsys: pytest.CaptureFixture[str]) -> None:
    """list_primitives should print at least two category headings."""
    args = _make_args(primitives_command="list")
    rc = list_primitives(args)
    out = capsys.readouterr().out
    assert rc == 0
    # Check several expected categories
    for cat in ("Composition", "Reliability", "Caching", "Testing"):
        assert cat in out, f"Expected category '{cat}' in output"


def test_list_prints_known_primitive_names(capsys: pytest.CaptureFixture[str]) -> None:
    """list_primitives should display the core primitives from the issue."""
    args = _make_args(primitives_command="list")
    list_primitives(args)
    out = capsys.readouterr().out
    for name in (
        "SequentialPrimitive",
        "ParallelPrimitive",
        "RetryPrimitive",
        "TimeoutPrimitive",
        "FallbackPrimitive",
        "CachePrimitive",
        "MockPrimitive",
    ):
        assert name in out, f"Expected '{name}' in list output"


# ---------------------------------------------------------------------------
# T2 – list_primitives: footer hint
# ---------------------------------------------------------------------------


def test_list_prints_footer_hint(capsys: pytest.CaptureFixture[str]) -> None:
    """list_primitives should display the `info` usage hint at the bottom."""
    args = _make_args(primitives_command="list")
    list_primitives(args)
    out = capsys.readouterr().out
    assert "tta primitives info" in out


# ---------------------------------------------------------------------------
# T3 – info_primitive: module path and category
# ---------------------------------------------------------------------------


def test_info_prints_module_path(capsys: pytest.CaptureFixture[str]) -> None:
    """info_primitive should display the module path for a known primitive."""
    args = _make_args(primitives_command="info", primitive_name="RetryPrimitive")
    rc = info_primitive(args)
    out = capsys.readouterr().out
    assert rc == 0
    assert "ttadev.primitives.recovery.retry" in out


def test_info_prints_category(capsys: pytest.CaptureFixture[str]) -> None:
    """info_primitive should display the category for a known primitive."""
    args = _make_args(primitives_command="info", primitive_name="RetryPrimitive")
    info_primitive(args)
    out = capsys.readouterr().out
    assert "Reliability" in out


# ---------------------------------------------------------------------------
# T4 – info_primitive: description from docstring
# ---------------------------------------------------------------------------


def test_info_prints_description(capsys: pytest.CaptureFixture[str]) -> None:
    """info_primitive should print a Description section."""
    args = _make_args(primitives_command="info", primitive_name="SequentialPrimitive")
    info_primitive(args)
    out = capsys.readouterr().out
    assert "Description" in out
    # The first paragraph of SequentialPrimitive's docstring mentions "sequence"
    assert "sequence" in out.lower() or "sequential" in out.lower()


# ---------------------------------------------------------------------------
# T5 – info_primitive: example block
# ---------------------------------------------------------------------------


def test_info_prints_example_block(capsys: pytest.CaptureFixture[str]) -> None:
    """info_primitive should show Example: for primitives with code fences."""
    args = _make_args(primitives_command="info", primitive_name="RetryPrimitive")
    info_primitive(args)
    out = capsys.readouterr().out
    # RetryPrimitive has a ```python block in its docstring
    assert "Example" in out
    assert "RetryPrimitive" in out or "RetryStrategy" in out


# ---------------------------------------------------------------------------
# T6 – info_primitive: unknown name exits 1
# ---------------------------------------------------------------------------


def test_info_unknown_name_returns_1(capsys: pytest.CaptureFixture[str]) -> None:
    """info_primitive should return 1 and print an error for unknown names."""
    args = _make_args(primitives_command="info", primitive_name="BogusXYZPrimitive")
    rc = info_primitive(args)
    err = capsys.readouterr().err
    assert rc == 1
    assert "unknown primitive" in err.lower()


# ---------------------------------------------------------------------------
# T7 – info_primitive: suggests correction on near-miss
# ---------------------------------------------------------------------------


def test_info_suggests_correction_on_near_miss(capsys: pytest.CaptureFixture[str]) -> None:
    """info_primitive should suggest a match when the name contains a known substring."""
    args = _make_args(
        primitives_command="info", primitive_name="Retry"
    )  # substring of RetryPrimitive
    info_primitive(args)
    err = capsys.readouterr().err
    # Should suggest "RetryPrimitive"
    assert "RetryPrimitive" in err


# ---------------------------------------------------------------------------
# T8 – info_primitive: case-insensitive exact-match suggestion
# ---------------------------------------------------------------------------


def test_info_suggests_on_wrong_case(capsys: pytest.CaptureFixture[str]) -> None:
    """info_primitive should suggest the correct spelling on case mismatch."""
    args = _make_args(primitives_command="info", primitive_name="retryprimitive")
    info_primitive(args)
    err = capsys.readouterr().err
    assert "RetryPrimitive" in err


# ---------------------------------------------------------------------------
# T9 – subprocess: tta primitives list exits 0
# ---------------------------------------------------------------------------


def test_subprocess_primitives_list_exits_zero() -> None:
    """``tta primitives list`` should exit 0 and print primitive names."""
    r = _run_cli("primitives", "list")
    assert r.returncode == 0
    assert "RetryPrimitive" in r.stdout
    assert "MockPrimitive" in r.stdout


# ---------------------------------------------------------------------------
# T10 – subprocess: tta primitives info RetryPrimitive exits 0
# ---------------------------------------------------------------------------


def test_subprocess_primitives_info_exits_zero() -> None:
    """``tta primitives info RetryPrimitive`` should exit 0."""
    r = _run_cli("primitives", "info", "RetryPrimitive")
    assert r.returncode == 0
    assert "RetryPrimitive" in r.stdout
    assert "ttadev.primitives.recovery.retry" in r.stdout


# ---------------------------------------------------------------------------
# T11 – subprocess: tta primitives info UnknownXYZ exits 1
# ---------------------------------------------------------------------------


def test_subprocess_primitives_info_unknown_exits_one() -> None:
    """``tta primitives info UnknownXYZ`` should exit 1."""
    r = _run_cli("primitives", "info", "UnknownXYZ")
    assert r.returncode == 1
    assert "unknown primitive" in r.stderr.lower()


# ---------------------------------------------------------------------------
# T12 – subprocess: tta primitives (no sub-command) exits 0 with help
# ---------------------------------------------------------------------------


def test_subprocess_primitives_no_subcommand_shows_help() -> None:
    """``tta primitives`` with no sub-command should exit 0 and show help."""
    r = _run_cli("primitives")
    assert r.returncode == 0
    assert "list" in r.stdout or "list" in r.stderr
    assert "info" in r.stdout or "info" in r.stderr


# ---------------------------------------------------------------------------
# T13 – catalogue covers the 7 primitives highlighted in the issue
# ---------------------------------------------------------------------------


def test_catalogue_covers_issue_primitives() -> None:
    """All seven primitives mentioned in issue #324 must be in the catalogue."""
    issue_primitives = {
        "SequentialPrimitive",
        "ParallelPrimitive",
        "RetryPrimitive",
        "TimeoutPrimitive",
        "FallbackPrimitive",
        "CachePrimitive",
        "MockPrimitive",
    }
    catalogue_names = {e.name for e in _CATALOGUE}
    missing = issue_primitives - catalogue_names
    assert not missing, f"Missing from catalogue: {missing}"


# ---------------------------------------------------------------------------
# T14 – _BY_NAME is case-sensitive
# ---------------------------------------------------------------------------


def test_by_name_is_case_sensitive() -> None:
    """_BY_NAME must not return an entry for wrong-case lookups."""
    assert "retryprimitive" not in _BY_NAME
    assert "RetryPrimitive" in _BY_NAME


# ---------------------------------------------------------------------------
# Unit helpers
# ---------------------------------------------------------------------------


def test_first_paragraph_strips_extra_lines() -> None:
    """_first_paragraph should return only the first non-blank paragraph."""
    doc = """
    First line.
    Still first paragraph.

    Second paragraph here.
    """
    result = _first_paragraph(doc)
    assert "First line" in result
    assert "Second paragraph" not in result


def test_extract_example_returns_code() -> None:
    """_extract_example should return code inside ```python fences."""
    doc = """
    Some description.

    Example:
        ```python
        x = RetryPrimitive(prim)
        ```
    """
    result = _extract_example(doc)
    assert result is not None
    assert "RetryPrimitive" in result


def test_extract_example_none_when_no_fence() -> None:
    """_extract_example should return None when no code fence exists."""
    doc = "Simple docstring with no example."
    assert _extract_example(doc) is None


# ---------------------------------------------------------------------------
# handle_primitives_command dispatcher
# ---------------------------------------------------------------------------


def test_handle_dispatches_list(capsys: pytest.CaptureFixture[str]) -> None:
    """handle_primitives_command should dispatch 'list' correctly."""
    args = _make_args(primitives_command="list")
    rc = handle_primitives_command(args)
    assert rc == 0
    assert "Composition" in capsys.readouterr().out


def test_handle_dispatches_info(capsys: pytest.CaptureFixture[str]) -> None:
    """handle_primitives_command should dispatch 'info' correctly."""
    args = _make_args(primitives_command="info", primitive_name="MockPrimitive")
    rc = handle_primitives_command(args)
    assert rc == 0
    assert "MockPrimitive" in capsys.readouterr().out
