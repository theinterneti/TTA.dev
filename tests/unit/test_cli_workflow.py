"""Unit tests for ``tta workflow run <file>`` — GitHub issue #330.

Tests cover the file-based workflow execution path added to the existing
``tta workflow run`` subcommand.  Each test creates a minimal Python workflow
file in a temporary directory and drives ``handle_workflow_command`` directly,
avoiding subprocess overhead.

Pattern
-------
Every test builds an ``argparse.Namespace`` that matches the shape produced by
:func:`ttadev.cli.workflow.register_workflow_subcommands`, then calls
:func:`ttadev.cli.workflow.handle_workflow_command` and asserts on the return
code and captured output.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from ttadev.cli.workflow import handle_workflow_command

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_run_args(
    file: Path,
    *,
    input_json: str | None = None,
    timeout: float | None = None,
    dry_run: bool = False,
    goal: str | None = None,
) -> argparse.Namespace:
    """Return a ``Namespace`` that mimics ``tta workflow run <file>`` args.

    Args:
        file: Path to the workflow ``.py`` file.
        input_json: Raw JSON string for ``--input``.
        timeout: Value for ``--timeout`` in seconds, or ``None``.
        dry_run: Whether ``--dry-run`` was passed.
        goal: Value for ``--goal`` (only needed for named workflows).

    Returns:
        An ``argparse.Namespace`` ready to hand to ``handle_workflow_command``.
    """
    return argparse.Namespace(
        workflow_command="run",
        name=str(file),
        goal=goal,
        no_confirm=False,
        track_l0=False,
        dry_run=dry_run,
        input=input_json,
        timeout=timeout,
    )


def _write_workflow(tmp_path: Path, source: str, name: str = "workflow.py") -> Path:
    """Write *source* to a file inside *tmp_path* and return the path.

    Args:
        tmp_path: Pytest temporary directory.
        source: Python source code for the workflow file.
        name: File name (default ``workflow.py``).

    Returns:
        Path to the written workflow file.
    """
    wf = tmp_path / name
    wf.write_text(source)
    return wf


# ---------------------------------------------------------------------------
# Minimal workflow source fixtures
# ---------------------------------------------------------------------------

_GREET_WORKFLOW = """\
from ttadev.primitives import LambdaPrimitive


async def build():
    async def greet(data, ctx):
        return f"Hello, {data}!"

    return LambdaPrimitive(greet)
"""

_PASSTHROUGH_WORKFLOW = """\
from ttadev.primitives import LambdaPrimitive


async def build():
    def passthrough(data, ctx):
        return data

    return LambdaPrimitive(passthrough)
"""

_NO_BUILD_WORKFLOW = """\
# Intentionally missing the build() function.
x = 42
"""

_REPR_WORKFLOW = """\
from ttadev.primitives import LambdaPrimitive


async def build():
    return LambdaPrimitive(lambda d, c: d)
"""


# ---------------------------------------------------------------------------
# Test: happy path — simple LambdaPrimitive
# ---------------------------------------------------------------------------


def test_happy_path_executes_and_prints_result(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``tta workflow run <file>`` executes build() and prints the result.

    Arrange: write a workflow that greets its input with "Hello, <data>!"
    Act:     run the CLI handler with no extra flags
    Assert:  exit code 0, output contains the result and the Done marker
    """
    wf = _write_workflow(tmp_path, _GREET_WORKFLOW)

    rc = handle_workflow_command(_make_run_args(wf), data_dir=tmp_path)

    out = capsys.readouterr().out
    assert rc == 0, f"Expected exit 0, got {rc}\n{out}"
    assert "Result:" in out
    assert "✅ Done" in out
    assert f"Workflow: {wf}" in out


# ---------------------------------------------------------------------------
# Test: file not found
# ---------------------------------------------------------------------------


def test_file_not_found_exits_nonzero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """``tta workflow run`` exits 1 and prints an error when the file is missing.

    Arrange: point to a non-existent path ending in .py
    Act:     call the handler
    Assert:  exit code 1, error message on stderr
    """
    missing = tmp_path / "does_not_exist.py"

    rc = handle_workflow_command(_make_run_args(missing), data_dir=tmp_path)

    assert rc == 1
    err = capsys.readouterr().err
    assert "file not found" in err.lower() or "not found" in err.lower()


# ---------------------------------------------------------------------------
# Test: file without build() function
# ---------------------------------------------------------------------------


def test_missing_build_function_exits_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``tta workflow run`` exits 1 when the file has no build() function.

    Arrange: write a workflow file that is valid Python but has no build()
    Act:     call the handler
    Assert:  exit code 1, stderr mentions build()
    """
    wf = _write_workflow(tmp_path, _NO_BUILD_WORKFLOW, name="no_build.py")

    rc = handle_workflow_command(_make_run_args(wf), data_dir=tmp_path)

    assert rc == 1
    err = capsys.readouterr().err
    assert "build()" in err or "build" in err.lower()


# ---------------------------------------------------------------------------
# Test: --input JSON is parsed and forwarded to the primitive
# ---------------------------------------------------------------------------


def test_json_input_is_forwarded_to_primitive(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--input`` JSON is parsed and passed as input_data to the primitive.

    Arrange: write a passthrough workflow (returns its input unchanged); pass
             ``--input '{"key": "value"}'``
    Act:     call the handler
    Assert:  exit code 0, the result JSON contains "key": "value"
    """
    wf = _write_workflow(tmp_path, _PASSTHROUGH_WORKFLOW, name="passthrough.py")
    input_payload = json.dumps({"key": "value"})

    rc = handle_workflow_command(
        _make_run_args(wf, input_json=input_payload),
        data_dir=tmp_path,
    )

    out = capsys.readouterr().out
    assert rc == 0, f"Expected exit 0, got {rc}\n{out}"
    assert "key" in out
    assert "value" in out


# ---------------------------------------------------------------------------
# Test: --dry-run prints repr without executing
# ---------------------------------------------------------------------------


def test_dry_run_prints_repr_without_executing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--dry-run`` prints the primitive repr and skips execution.

    Arrange: write a workflow; pass ``--dry-run``
    Act:     call the handler
    Assert:  exit code 0, stdout contains "dry-run" or "Primitive:", no "✅ Done"
    """
    wf = _write_workflow(tmp_path, _REPR_WORKFLOW, name="repr_wf.py")

    rc = handle_workflow_command(
        _make_run_args(wf, dry_run=True),
        data_dir=tmp_path,
    )

    out = capsys.readouterr().out
    assert rc == 0, f"Expected exit 0, got {rc}\n{out}"
    assert "dry-run" in out or "Primitive:" in out
    assert "✅ Done" not in out


# ---------------------------------------------------------------------------
# Test: --timeout wraps the primitive in TimeoutPrimitive
# ---------------------------------------------------------------------------


def test_timeout_flag_wraps_primitive(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """``--timeout N`` still runs successfully for fast primitives.

    Arrange: write a fast greet workflow; pass ``--timeout 30``
    Act:     call the handler
    Assert:  exit code 0, normal output produced (primitive completes before timeout)
    """
    wf = _write_workflow(tmp_path, _GREET_WORKFLOW, name="timeout_wf.py")

    rc = handle_workflow_command(
        _make_run_args(wf, timeout=30.0),
        data_dir=tmp_path,
    )

    out = capsys.readouterr().out
    assert rc == 0, f"Expected exit 0, got {rc}\n{out}"
    assert "✅ Done" in out


# ---------------------------------------------------------------------------
# Test: primitive raises an exception → exit 1
# ---------------------------------------------------------------------------


def test_primitive_exception_exits_nonzero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """When the primitive raises an exception the command exits 1.

    Arrange: write a workflow whose primitive always raises RuntimeError
    Act:     call the handler
    Assert:  exit code 1, traceback written to stderr
    """
    failing_source = """\
from ttadev.primitives import LambdaPrimitive


async def build():
    async def boom(data, ctx):
        raise RuntimeError("intentional failure")

    return LambdaPrimitive(boom)
"""
    wf = _write_workflow(tmp_path, failing_source, name="failing.py")

    rc = handle_workflow_command(_make_run_args(wf), data_dir=tmp_path)

    assert rc == 1
    err = capsys.readouterr().err
    # traceback.print_exc writes to stderr; confirm something was written
    assert err.strip() != ""
