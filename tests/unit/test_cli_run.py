"""Unit tests for ttadev.cli.run — T1-T6 (RED → GREEN)."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest

from ttadev.cli.run import (
    DiskCache,
    ShellPrimitive,
    ShellResult,
    run_cache,
    run_echo,
    run_retry,
    run_timeout,
)
from ttadev.primitives.core.base import WorkflowContext

# ---------------------------------------------------------------------------
# T1 — ShellPrimitive
# ---------------------------------------------------------------------------


def test_shell_primitive_success(tmp_path: Path) -> None:
    import asyncio

    prim = ShellPrimitive([sys.executable, "-c", "print('hello')"])
    ctx = WorkflowContext(workflow_id="test")
    result = asyncio.run(prim.execute([], ctx))
    assert isinstance(result, ShellResult)
    assert result.returncode == 0
    assert "hello" in result.stdout


def test_shell_primitive_nonzero_exit(tmp_path: Path) -> None:
    import asyncio

    prim = ShellPrimitive([sys.executable, "-c", "import sys; sys.exit(42)"])
    ctx = WorkflowContext(workflow_id="test")
    result = asyncio.run(prim.execute([], ctx))
    assert result.returncode == 42


def test_shell_primitive_stderr_captured() -> None:
    import asyncio

    prim = ShellPrimitive([sys.executable, "-c", "import sys; sys.stderr.write('err\\n')"])
    ctx = WorkflowContext(workflow_id="test")
    result = asyncio.run(prim.execute([], ctx))
    assert "err" in result.stderr


def test_shell_primitive_raises_on_nonzero() -> None:
    """ShellPrimitive raises RuntimeError on non-zero exit so RetryPrimitive can catch it."""
    import asyncio

    prim = ShellPrimitive([sys.executable, "-c", "import sys; sys.exit(1)"], raise_on_error=True)
    ctx = WorkflowContext(workflow_id="test")
    with pytest.raises(RuntimeError):
        asyncio.run(prim.execute([], ctx))


# ---------------------------------------------------------------------------
# T2 — run_echo
# ---------------------------------------------------------------------------


def test_run_echo_prints_args(capsys: pytest.CaptureFixture[str]) -> None:
    run_echo(["hello", "world"])
    assert "hello world" in capsys.readouterr().out


def test_run_echo_empty_args(capsys: pytest.CaptureFixture[str]) -> None:
    run_echo([])
    assert capsys.readouterr().out.strip() == ""


# ---------------------------------------------------------------------------
# T3 — run_retry
# ---------------------------------------------------------------------------


def test_run_retry_succeeds_on_first_try(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_retry([sys.executable, "-c", "print('ok')"], max_retries=3, data_dir=tmp_path)
    assert "ok" in capsys.readouterr().out


def test_run_retry_retries_on_failure(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Write a script that fails twice then succeeds
    script = tmp_path / "flaky.py"
    counter = tmp_path / "count.txt"
    counter.write_text("0")
    script.write_text(
        f"""
import sys
from pathlib import Path
count = int(Path({str(counter)!r}).read_text())
Path({str(counter)!r}).write_text(str(count + 1))
if count < 2:
    sys.exit(1)
print("success")
"""
    )
    run_retry([sys.executable, str(script)], max_retries=3, data_dir=tmp_path)
    assert "success" in capsys.readouterr().out


def test_run_retry_exhausted_exits_nonzero(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        run_retry(
            [sys.executable, "-c", "import sys; sys.exit(1)"],
            max_retries=2,
            data_dir=tmp_path,
        )
    assert exc.value.code != 0


def test_run_retry_invalid_max_retries_exits_1(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        run_retry([sys.executable, "-c", ""], max_retries=0, data_dir=tmp_path)
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# T4 — run_timeout
# ---------------------------------------------------------------------------


def test_run_timeout_fast_command_passes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_timeout([sys.executable, "-c", "print('fast')"], seconds=5.0, data_dir=tmp_path)
    assert "fast" in capsys.readouterr().out


def test_run_timeout_slow_command_exits_1(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        run_timeout(
            [sys.executable, "-c", "import time; time.sleep(10)"],
            seconds=0.2,
            data_dir=tmp_path,
        )
    assert exc.value.code == 1


def test_run_timeout_zero_seconds_exits_1(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        run_timeout([sys.executable, "-c", ""], seconds=0.0, data_dir=tmp_path)
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# T5 — DiskCache + run_cache
# ---------------------------------------------------------------------------


def test_disk_cache_miss_returns_none(tmp_path: Path) -> None:
    dc = DiskCache(tmp_path / "cache")
    assert dc.get("mykey") is None


def test_disk_cache_set_and_get(tmp_path: Path) -> None:
    dc = DiskCache(tmp_path / "cache")
    dc.set("mykey", "value", ttl=60)
    assert dc.get("mykey") == "value"


def test_disk_cache_expired_returns_none(tmp_path: Path) -> None:
    dc = DiskCache(tmp_path / "cache")
    dc.set("mykey", "value", ttl=0.01)
    time.sleep(0.05)
    assert dc.get("mykey") is None


def test_run_cache_miss_runs_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run_cache(
        [sys.executable, "-c", "print('ran')"],
        ttl=60,
        key="k1",
        data_dir=tmp_path,
    )
    assert "ran" in capsys.readouterr().out


def test_run_cache_hit_skips_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cmd = [sys.executable, "-c", "print('ran')"]
    run_cache(cmd, ttl=60, key="k2", data_dir=tmp_path)
    capsys.readouterr()  # clear
    run_cache(cmd, ttl=60, key="k2", data_dir=tmp_path)
    captured = capsys.readouterr()
    assert "cache hit" in captured.err.lower()
    assert "ran" in captured.out


def test_run_cache_expired_reruns_command(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cmd = [sys.executable, "-c", "print('ran')"]
    run_cache(cmd, ttl=0.01, key="k3", data_dir=tmp_path)
    capsys.readouterr()
    time.sleep(0.05)
    run_cache(cmd, ttl=0.01, key="k3", data_dir=tmp_path)
    out = capsys.readouterr().out
    assert "cache hit" not in out.lower()
    assert "ran" in out


def test_run_cache_default_key_from_command(tmp_path: Path) -> None:
    """When no key given, cache file should still be created."""
    cmd = [sys.executable, "-c", "print('x')"]
    run_cache(cmd, ttl=60, key=None, data_dir=tmp_path)
    cache_dir = tmp_path / "run-cache"
    assert cache_dir.exists()
    assert any(cache_dir.glob("*.json"))


def test_run_cache_ttl_zero_warns(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run_cache([sys.executable, "-c", "print('x')"], ttl=0, key="k4", data_dir=tmp_path)
    assert "warn" in capsys.readouterr().err.lower()


# ---------------------------------------------------------------------------
# T6 — argparse dispatcher (subprocess)
# ---------------------------------------------------------------------------


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ttadev.cli", *args],
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else None,
    )


def test_cli_run_help_exits_zero() -> None:
    r = _run(["run", "--help"])
    assert r.returncode == 0
    assert "retry" in r.stdout
    assert "timeout" in r.stdout
    assert "cache" in r.stdout
    assert "echo" in r.stdout


def test_cli_run_echo_subprocess() -> None:
    r = _run(["run", "echo", "--", "hello", "world"])
    assert r.returncode == 0
    assert "hello world" in r.stdout


def test_cli_run_retry_subprocess(tmp_path: Path) -> None:
    r = _run(
        ["--data-dir", str(tmp_path), "run", "retry", "--", sys.executable, "-c", "print('ok')"]
    )
    assert r.returncode == 0
    assert "ok" in r.stdout


def test_cli_run_timeout_subprocess(tmp_path: Path) -> None:
    r = _run(
        [
            "--data-dir",
            str(tmp_path),
            "run",
            "timeout",
            "--seconds",
            "5",
            "--",
            sys.executable,
            "-c",
            "print('fast')",
        ]
    )
    assert r.returncode == 0
    assert "fast" in r.stdout


def test_cli_run_cache_subprocess(tmp_path: Path) -> None:
    r = _run(
        [
            "--data-dir",
            str(tmp_path),
            "run",
            "cache",
            "--key",
            "ck1",
            "--",
            sys.executable,
            "-c",
            "print('cached')",
        ]
    )
    assert r.returncode == 0
    assert "cached" in r.stdout


def test_cli_run_no_subcommand_shows_help() -> None:
    r = _run(["run"])
    # Should print help and exit 0
    assert r.returncode == 0
    assert "retry" in r.stdout or "retry" in r.stderr
