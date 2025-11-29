"""Comprehensive tests for the production CachePrimitive.

These tests validate the real implementation in
``tta_dev_primitives.performance.CachePrimitive`` rather than testing
ad-hoc cache implementations. They focus on:

* basic hit/miss behavior
* TTL-based expiration semantics
* statistics reporting via ``get_stats``.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from tta_dev_primitives.core.base import LambdaPrimitive, WorkflowContext
from tta_dev_primitives.performance import CachePrimitive


def _default_cache_key_fn(input_data: Any, context: WorkflowContext) -> str:
    """Deterministic cache key for tests.

    Uses both input data and workflow_id so we can easily control key
    collisions in tests.
    """

    return f"{input_data!r}:{context.workflow_id}"


@pytest.mark.asyncio
async def test_cache_miss_then_hit() -> None:
    """First access is a miss, subsequent access is a hit.

    Verifies that the wrapped primitive is only executed once for the
    same cache key and that stats reflect one miss and one hit.
    """

    call_count = {"value": 0}

    async def impl(input_data: dict, context: WorkflowContext) -> dict:
        call_count["value"] += 1
        return {"value": input_data["v"], "call": call_count["value"]}

    base = LambdaPrimitive(impl)
    cache = CachePrimitive(primitive=base, cache_key_fn=_default_cache_key_fn, ttl_seconds=10.0)
    ctx = WorkflowContext(workflow_id="test-cache")

    result1 = await cache.execute({"v": 1}, ctx)
    result2 = await cache.execute({"v": 1}, ctx)

    assert result1 == {"value": 1, "call": 1}
    assert result2 == {"value": 1, "call": 1}
    assert call_count["value"] == 1

    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["expirations"] == 0


@pytest.mark.asyncio
async def test_different_keys_produce_independent_entries() -> None:
    """Different input data produce different cache entries.

    Ensures that changing the input (and therefore the cache key)
    results in separate primitive executions.
    """

    call_count = {"value": 0}

    async def impl(input_data: dict, context: WorkflowContext) -> dict:
        call_count["value"] += 1
        return {"value": input_data["v"], "call": call_count["value"]}

    base = LambdaPrimitive(impl)
    cache = CachePrimitive(primitive=base, cache_key_fn=_default_cache_key_fn, ttl_seconds=10.0)
    ctx = WorkflowContext(workflow_id="test-cache-keys")

    r1 = await cache.execute({"v": 1}, ctx)
    r2 = await cache.execute({"v": 2}, ctx)

    assert r1["value"] == 1
    assert r2["value"] == 2
    assert call_count["value"] == 2

    stats = cache.get_stats()
    assert stats["misses"] == 2
    assert stats["hits"] == 0


@pytest.mark.asyncio
async def test_cache_entry_expires_after_ttl() -> None:
    """Entries expire after ttl_seconds and are recomputed.

    Uses a short TTL to keep the test fast while still exercising the
    expiration path and statistics.
    """

    call_count = {"value": 0}

    async def impl(input_data: dict, context: WorkflowContext) -> dict:
        call_count["value"] += 1
        return {"value": input_data["v"], "call": call_count["value"]}

    base = LambdaPrimitive(impl)
    cache = CachePrimitive(primitive=base, cache_key_fn=_default_cache_key_fn, ttl_seconds=0.05)
    ctx = WorkflowContext(workflow_id="test-cache-ttl")

    # First call populates cache
    await cache.execute({"v": 1}, ctx)
    assert call_count["value"] == 1

    # Wait for entry to expire
    await asyncio.sleep(0.1)

    # Second call should recompute and count as expiration + miss
    await cache.execute({"v": 1}, ctx)
    assert call_count["value"] == 2

    stats = cache.get_stats()
    assert stats["expirations"] == 1
    assert stats["misses"] == 2
    assert stats["hits"] == 0


def test_get_stats_structure_and_hit_rate() -> None:
    """get_stats returns the expected structure and hit rate."""

    async def impl(input_data: dict, context: WorkflowContext) -> dict:  # pragma: no cover - used via LambdaPrimitive
        return input_data

    base = LambdaPrimitive(impl)
    cache = CachePrimitive(primitive=base, cache_key_fn=_default_cache_key_fn, ttl_seconds=10.0)
    ctx = WorkflowContext(workflow_id="stats-test")

    # Simulate simple interaction pattern
    async def run() -> None:
        await cache.execute({"v": 1}, ctx)  # miss
        await cache.execute({"v": 1}, ctx)  # hit

    asyncio.run(run())

    stats = cache.get_stats()
    assert set(stats.keys()) == {"size", "hits", "misses", "expirations", "hit_rate"}
    assert stats["size"] == 1
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    # Hit rate is percentage; tolerate rounding
    assert 49.0 <= stats["hit_rate"] <= 51.0
