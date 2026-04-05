"""Unit tests for #339 — ingest functions must not block the asyncio event loop.

Verifies that:
1. ``_file_ingestion_loop()`` delegates all I/O to a thread-pool executor via
   ``loop.run_in_executor`` so the asyncio event loop remains free.
2. Even when the underlying sync method sleeps (simulating ~3.5 s I/O), the
   event loop can still schedule other coroutines concurrently — i.e. the loop
   is *not* blocked.
3. ``_ingest_all_sync()`` acquires ``_ingest_lock`` (thread-safety contract).
"""

from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ttadev.observability.server import ObservabilityServer

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_server(tmp_path: Path) -> ObservabilityServer:
    """Return an ObservabilityServer that never contacts real CGC or files."""
    return ObservabilityServer(data_dir=tmp_path / "tta")


# ---------------------------------------------------------------------------
# 1. Executor delegation — _ingest_all_sync runs in a worker thread, not
#    the event-loop thread.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingest_all_sync_runs_in_worker_thread(tmp_path: Path) -> None:
    """_ingest_all_sync must be called from a worker thread, not the event loop.

    We replace ``_ingest_all_sync`` with a side-effect that records the
    current thread, then drive one iteration of ``_file_ingestion_loop`` and
    confirm the recorded thread is NOT the event-loop thread.
    """
    srv = _make_server(tmp_path)

    event_loop_thread = threading.current_thread()
    worker_thread: threading.Thread | None = None

    def spy_ingest() -> list:
        nonlocal worker_thread
        worker_thread = threading.current_thread()
        return []

    with (
        patch.object(srv, "_ingest_all_sync", side_effect=spy_ingest),
        patch.object(srv._session_mgr, "get_current", return_value=MagicMock()),
    ):
        # Run exactly one tick of the loop (sleep + one executor call).
        task = asyncio.create_task(srv._file_ingestion_loop())
        # Give the loop time to execute one sleep(1) + executor call.
        await asyncio.sleep(1.1)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    assert worker_thread is not None, "_ingest_all_sync was never called"
    assert worker_thread is not event_loop_thread, (
        "_ingest_all_sync ran on the event-loop thread — the loop is being blocked!"
    )


# ---------------------------------------------------------------------------
# 2. Non-blocking proof — event loop stays responsive while sync I/O runs.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_event_loop_not_blocked_during_ingest(tmp_path: Path) -> None:
    """The event loop must remain responsive while the sync ingest sleeps.

    We mock ``_ingest_all_sync`` to sleep for 0.3 s (simulating slow disk I/O)
    and concurrently schedule a coroutine that records timestamps. If the loop
    were blocked, that coroutine could not run until after the sleep. We verify
    it runs during the sleep window.
    """
    slow_io_seconds = 0.3
    tick_interval = 0.05  # how often the concurrent coroutine checks in

    srv = _make_server(tmp_path)
    ticks_during_ingest: list[float] = []
    ingest_started = asyncio.Event()
    ingest_done = asyncio.Event()

    def slow_ingest() -> list:
        ingest_started.set()  # NOTE: sets from worker thread — Event is thread-safe
        time.sleep(slow_io_seconds)
        ingest_done.set()
        return []

    async def concurrent_ticker() -> None:
        """Record the time of each tick while ingestion is running."""
        await ingest_started.wait()
        while not ingest_done.is_set():
            ticks_during_ingest.append(asyncio.get_event_loop().time())
            await asyncio.sleep(tick_interval)

    with (
        patch.object(srv, "_ingest_all_sync", side_effect=slow_ingest),
        patch.object(srv._session_mgr, "get_current", return_value=MagicMock()),
    ):
        ticker_task = asyncio.create_task(concurrent_ticker())
        loop_task = asyncio.create_task(srv._file_ingestion_loop())

        # Wait for the full ingest cycle to finish (sleep(1) + _SLOW_IO_SECONDS).
        await asyncio.wait_for(ingest_done.wait(), timeout=2.5)

        loop_task.cancel()
        ticker_task.cancel()
        for t in (loop_task, ticker_task):
            try:
                await t
            except asyncio.CancelledError:
                pass

    # The ticker must have fired at least once during the slow I/O window,
    # proving the event loop was NOT blocked.
    expected_minimum_ticks = int(slow_io_seconds / tick_interval) - 1  # allow 1 miss
    assert len(ticks_during_ingest) >= expected_minimum_ticks, (
        f"Only {len(ticks_during_ingest)} ticks recorded during {slow_io_seconds}s "
        f"of I/O; expected ≥{expected_minimum_ticks}. "
        "This indicates the event loop was blocked by synchronous ingest I/O."
    )


# ---------------------------------------------------------------------------
# 3. Thread-safety — _ingest_all_sync holds _ingest_lock while running.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ingest_lock_is_held_during_ingest_all_sync(tmp_path: Path) -> None:
    """_ingest_all_sync must hold _ingest_lock for the duration of its execution.

    We patch the three sub-methods to check whether the lock is held. If any of
    them observes the lock as *free* we fail the test.
    """
    srv = _make_server(tmp_path)
    lock_states: dict[str, bool] = {}

    def check_lock(name: str) -> list:
        # try_acquire returns False if already held — that means lock IS held.
        acquired = srv._ingest_lock.acquire(blocking=False)
        lock_states[name] = not acquired  # True  ⟺  lock was already held
        if acquired:
            srv._ingest_lock.release()
        return []

    with (
        patch.object(srv, "_ingest_otel_jsonl", side_effect=lambda: check_lock("otel")),
        patch.object(srv, "_ingest_activity_logs", side_effect=lambda: check_lock("activity")),
        patch.object(srv, "_ingest_agent_tracker", side_effect=lambda: check_lock("tracker")),
    ):
        srv._ingest_all_sync()

    for method, was_locked in lock_states.items():
        assert was_locked, (
            f"_ingest_lock was NOT held when {method} ran — "
            "concurrent executor calls could corrupt offset state."
        )


# ---------------------------------------------------------------------------
# 4. _ingest_lock is a real threading.Lock (type check).
# ---------------------------------------------------------------------------


def test_ingest_lock_is_threading_lock(tmp_path: Path) -> None:
    """ObservabilityServer must expose _ingest_lock as a threading.Lock."""
    srv = _make_server(tmp_path)
    # threading.Lock() returns a _thread.lock; Lock.acquire/release are the
    # canonical interface we depend on.
    assert hasattr(srv, "_ingest_lock"), "ObservabilityServer missing _ingest_lock"
    lock = srv._ingest_lock
    # Verify it behaves as a mutex: acquire then release without deadlock.
    acquired = lock.acquire(blocking=False)
    assert acquired, "_ingest_lock was already held at construction time"
    lock.release()  # must not raise


# ---------------------------------------------------------------------------
# 5. Regression — _file_ingestion_loop uses run_in_executor (not a bare call).
#    We verify that asyncio.get_running_loop().run_in_executor is invoked.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_file_ingestion_loop_uses_run_in_executor(tmp_path: Path) -> None:
    """_file_ingestion_loop must delegate to loop.run_in_executor.

    We wrap the real event loop's run_in_executor and confirm it is called with
    ``_ingest_all_sync`` as the function argument.
    """
    srv = _make_server(tmp_path)
    executor_calls: list[tuple] = []

    loop = asyncio.get_running_loop()
    original_rie = loop.run_in_executor

    async def spy_run_in_executor(executor, func, *args):  # type: ignore[no-untyped-def]
        executor_calls.append((func, args))
        # Still delegate to the real executor so the coroutine completes.
        return await original_rie(executor, func, *args)

    # Keep a reference to the mock *inside* the patch context so we can compare
    # it after the context exits (patch restores the original at __exit__).
    recorded_mock: MagicMock | None = None

    with patch.object(srv, "_ingest_all_sync", return_value=[]) as mock_ingest:
        recorded_mock = mock_ingest
        with (
            patch.object(srv._session_mgr, "get_current", return_value=MagicMock()),
            patch.object(loop, "run_in_executor", side_effect=spy_run_in_executor),
        ):
            task = asyncio.create_task(srv._file_ingestion_loop())
            await asyncio.sleep(1.1)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    assert recorded_mock is not None
    ingest_fns = [fn for fn, _ in executor_calls]
    assert recorded_mock in ingest_fns, (
        "loop.run_in_executor was never called with _ingest_all_sync. "
        "The ingestion loop may be calling sync functions directly on the event loop."
    )
