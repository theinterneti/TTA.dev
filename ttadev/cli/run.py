"""tta run subcommands: retry, timeout, cache, echo."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ttadev.primitives.core.base import WorkflowContext, WorkflowPrimitive
from ttadev.primitives.recovery.retry import RetryPrimitive, RetryStrategy
from ttadev.primitives.recovery.timeout import TimeoutPrimitive

# ---------------------------------------------------------------------------
# ShellResult + ShellPrimitive  (T1)
# ---------------------------------------------------------------------------


@dataclass
class ShellResult:
    stdout: str
    stderr: str
    returncode: int


class ShellPrimitive(WorkflowPrimitive[list[str], ShellResult]):
    """Runs a shell command asynchronously, returns a ShellResult."""

    def __init__(self, cmd: list[str], *, raise_on_error: bool = False) -> None:
        self.cmd = cmd
        self.raise_on_error = raise_on_error

    async def execute(self, input_data: list[str], context: WorkflowContext) -> ShellResult:
        proc = await asyncio.create_subprocess_exec(
            *self.cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        raw_out, raw_err = await proc.communicate()
        result = ShellResult(
            stdout=raw_out.decode(errors="replace"),
            stderr=raw_err.decode(errors="replace"),
            returncode=proc.returncode or 0,
        )
        if self.raise_on_error and result.returncode != 0:
            raise RuntimeError(
                f"Command exited {result.returncode}: {' '.join(self.cmd)}\n{result.stderr}"
            )
        return result


# ---------------------------------------------------------------------------
# DiskCache  (T5)
# ---------------------------------------------------------------------------


class DiskCache:
    """Simple disk-backed key/value cache using JSON files."""

    def __init__(self, cache_dir: Path) -> None:
        self._dir = cache_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = hashlib.sha256(key.encode()).hexdigest()
        return self._dir / f"{safe}.json"

    def get(self, key: str) -> Any:
        p = self._path(key)
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text())
            if time.time() - data["ts"] >= data["ttl"]:
                return None
            return data["value"]
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: float) -> None:
        p = self._path(key)
        p.write_text(json.dumps({"ts": time.time(), "ttl": ttl, "value": value}))


# ---------------------------------------------------------------------------
# Helper: run a primitive and handle the result
# ---------------------------------------------------------------------------


def _execute(primitive: WorkflowPrimitive[Any, ShellResult], cmd: list[str]) -> ShellResult:
    ctx = WorkflowContext(
        workflow_id=f"tta-run-{hashlib.sha256(' '.join(cmd).encode()).hexdigest()[:8]}"
    )
    return asyncio.run(primitive.execute(cmd, ctx))


def _print_and_exit(result: ShellResult) -> None:
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# T2 — run_echo
# ---------------------------------------------------------------------------


def run_echo(args: list[str]) -> None:
    """Print args joined by spaces."""
    print(" ".join(args))


# ---------------------------------------------------------------------------
# T3 — run_retry
# ---------------------------------------------------------------------------


def run_retry(cmd: list[str], max_retries: int, data_dir: Path) -> None:
    """Run cmd, retrying up to max_retries times on non-zero exit."""
    if max_retries < 1:
        print("error: --max-retries must be >= 1", file=sys.stderr)
        sys.exit(1)

    shell = ShellPrimitive(cmd, raise_on_error=True)
    primitive = RetryPrimitive(
        shell, strategy=RetryStrategy(max_retries=max_retries, backoff_base=0.0)
    )

    try:
        result: ShellResult = _execute(primitive, cmd)
        _print_and_exit(result)
    except Exception as exc:
        print(f"[retry] All {max_retries} retries exhausted: {exc}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# T4 — run_timeout
# ---------------------------------------------------------------------------


def run_timeout(cmd: list[str], seconds: float, data_dir: Path) -> None:
    """Run cmd, killing it if it exceeds seconds."""
    if seconds <= 0:
        print("error: --seconds must be > 0", file=sys.stderr)
        sys.exit(1)

    shell = ShellPrimitive(cmd)
    primitive = TimeoutPrimitive(shell, timeout_seconds=seconds)

    try:
        result: ShellResult = _execute(primitive, cmd)
        _print_and_exit(result)
    except TimeoutError:
        print(f"[timeout] Command exceeded {seconds}s limit.", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"[timeout] Error: {exc}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# T5 — run_cache
# ---------------------------------------------------------------------------


def _default_key(cmd: list[str]) -> str:
    return hashlib.sha256(" ".join(cmd).encode()).hexdigest()[:16]


def run_cache(cmd: list[str], ttl: float, key: str | None, data_dir: Path) -> None:
    """Run cmd, serving cached stdout on hit."""
    if ttl == 0:
        print("warning: --ttl 0 disables caching (always miss)", file=sys.stderr)

    cache_key = key or _default_key(cmd)
    cache = DiskCache(data_dir / "run-cache")

    cached = cache.get(cache_key) if ttl > 0 else None
    if cached is not None:
        print("[cache hit] Returning cached output.", file=sys.stderr)
        print(cached, end="")

    # Cache miss — run the command
    shell = ShellPrimitive(cmd)
    ctx = WorkflowContext(workflow_id=f"tta-cache-{cache_key[:8]}")
    result: ShellResult = asyncio.run(shell.execute(cmd, ctx))

    if result.returncode == 0 and ttl > 0:
        cache.set(cache_key, result.stdout, ttl=ttl)

    _print_and_exit(result)
