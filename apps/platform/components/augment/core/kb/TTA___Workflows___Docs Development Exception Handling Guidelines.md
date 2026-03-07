---
title: Exception Handling Guidelines
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/development/exception-handling-guidelines.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Exception Handling Guidelines]]

## Overview

This document provides guidelines for exception handling in the TTA (Therapeutic Text Adventure) codebase. Following these patterns ensures consistent, maintainable, and debuggable error handling across the project.

## Table of Contents

1. [When to Use `contextlib.suppress()`](#when-to-use-contextlibsuppress)
2. [When to Use Logging in Exception Handlers](#when-to-use-logging-in-exception-handlers)
3. [When to Propagate Exceptions vs. Handle Them](#when-to-propagate-exceptions-vs-handle-them)
4. [Anti-Patterns to Avoid](#anti-patterns-to-avoid)
5. [Testing Exception Handling Code](#testing-exception-handling-code)

---

## When to Use `contextlib.suppress()`

### Purpose

Use `contextlib.suppress()` when you want to **silently ignore specific exceptions** where:
- The exception is expected and recoverable
- No logging or user notification is needed
- The operation is optional or has a safe fallback

### Pattern

```python
import contextlib

# Suppress specific exception types
with contextlib.suppress(FileNotFoundError, PermissionError):
    os.remove(temp_file)

# Suppress all exceptions (use sparingly)
with contextlib.suppress(Exception):
    optional_cleanup_operation()
```

### Real-World Examples from TTA Codebase

#### Example 1: Optional Cleanup in Player Profile Repository

**File**: `src/player_experience/database/player_profile_repository.py`

```python
async def delete_player_profile(self, player_id: str) -> bool:
    """Delete a player profile and all associated data."""
    try:
        # Main deletion logic
        await self.redis_client.delete(f"player:{player_id}")

        # Optional cleanup - don't fail if this doesn't work
        with contextlib.suppress(Exception):
            await self.redis_client.delete(f"player:{player_id}:cache")

        return True
    except Exception as e:
        logger.error(f"Failed to delete player profile {player_id}: {e}")
        return False
```

**Why**: Cache cleanup is optional; if it fails, the main deletion still succeeded.

#### Example 2: Graceful Degradation in Router

**File**: `src/player_experience/api/routers/router.py`

```python
async def get_player_stats(player_id: str) -> dict:
    """Get player statistics with optional enrichment."""
    stats = await get_basic_stats(player_id)

    # Try to enrich with additional data, but don't fail if unavailable
    with contextlib.suppress(Exception):
        stats["achievements"] = await get_achievements(player_id)

    with contextlib.suppress(Exception):
        stats["leaderboard_rank"] = await get_leaderboard_rank(player_id)

    return stats
```

**Why**: Basic stats are essential, but enrichment data is optional.

#### Example 3: Background Task Cleanup

**File**: `src/agent_orchestration/workflow_monitor.py`

```python
async def stop_monitoring(self):
    """Stop background monitoring tasks."""
    for task in self._background_tasks:
        with contextlib.suppress(asyncio.CancelledError):
            task.cancel()
            await task
```

**Why**: `CancelledError` is expected when cancelling tasks; no logging needed.

### When NOT to Use

❌ **Don't use** when:
- You need to log the error for debugging
- The exception indicates a serious problem
- You need to notify the user
- The operation is critical to the application flow

---

## When to Use Logging in Exception Handlers

### Purpose

Use logging in exception handlers when you need to:
- **Debug issues** in production
- **Track error patterns** over time
- **Understand why** an operation failed
- **Maintain audit trails** for critical operations

### Pattern

```python
import logging

logger = logging.getLogger(__name__)

try:
    risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    # Handle or re-raise
```

### Logging Levels

- **`logger.debug()`**: Expected errors in normal operation (e.g., cache miss)
- **`logger.info()`**: Informational events (e.g., retry succeeded)
- **`logger.warning()`**: Unexpected but recoverable errors
- **`logger.error()`**: Errors that need investigation
- **`logger.critical()`**: System-threatening errors

### Real-World Examples from TTA Codebase

#### Example 1: Loop with Continue (S112 Pattern)

**File**: `src/player_experience/database/player_profile_repository.py`

```python
async def bulk_update_profiles(self, updates: list[dict]) -> dict:
    """Update multiple player profiles."""
    success_count = 0
    failed_ids = []

    for update in updates:
        try:
            await self.update_player_profile(update["player_id"], update["data"])
            success_count += 1
        except Exception as e:
            # Log which record failed and why
            logger.debug(
                f"Failed to update player profile {update.get('player_id', 'unknown')}: "
                f"{type(e).__name__}: {e}"
            )
            failed_ids.append(update.get("player_id"))
            continue  # Process remaining records

    return {"success": success_count, "failed": failed_ids}
```

**Why**: We need to know which records failed and why, but continue processing others.

#### Example 2: Critical Operation Failure

**File**: `src/agent_orchestration/state_validator.py`

```python
async def validate_workflow_state(self, workflow_id: str) -> bool:
    """Validate workflow state integrity."""
    try:
        state = await self.get_workflow_state(workflow_id)
        return self._validate_state_schema(state)
    except Exception as e:
        logger.error(
            f"Failed to validate workflow state for {workflow_id}: {e}",
            exc_info=True,  # Include full stack trace
            extra={"workflow_id": workflow_id}
        )
        return False
```

**Why**: State validation failures are serious and need full context for debugging.

#### Example 3: Retry Logic with Logging

**File**: `src/monitoring/metrics_middleware.py`

```python
async def record_metric(self, metric_name: str, value: float, retries: int = 3):
    """Record a metric with retry logic."""
    for attempt in range(retries):
        try:
            await self.metrics_client.record(metric_name, value)
            if attempt > 0:
                logger.info(f"Metric {metric_name} recorded after {attempt + 1} attempts")
            return
        except Exception as e:
            if attempt < retries - 1:
                logger.warning(
                    f"Failed to record metric {metric_name} (attempt {attempt + 1}/{retries}): {e}"
                )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                logger.error(
                    f"Failed to record metric {metric_name} after {retries} attempts: {e}",
                    exc_info=True
                )
                raise
```

**Why**: Track retry attempts and final failures for monitoring.

---

## When to Propagate Exceptions vs. Handle Them

### Propagate (Re-raise) When

✅ **Propagate** exceptions when:
- The caller is better positioned to handle the error
- You need to add context but not handle the error
- The error indicates a programming bug (e.g., `TypeError`, `AttributeError`)
- The operation is critical and cannot continue

```python
async def get_player_profile(self, player_id: str) -> PlayerProfile:
    """Get player profile - caller must handle errors."""
    try:
        data = await self.redis_client.get(f"player:{player_id}")
        if not data:
            raise PlayerNotFoundError(f"Player {player_id} not found")
        return PlayerProfile.parse_raw(data)
    except RedisConnectionError as e:
        logger.error(f"Redis connection failed while fetching player {player_id}: {e}")
        raise  # Caller must handle connection errors
```

### Handle (Catch) When

✅ **Handle** exceptions when:
- You can recover from the error
- You have a sensible default or fallback
- The error is expected in normal operation
- You're at a boundary (API endpoint, background task)

```python
async def get_player_profile_safe(self, player_id: str) -> PlayerProfile | None:
    """Get player profile with safe fallback."""
    try:
        return await self.get_player_profile(player_id)
    except PlayerNotFoundError:
        logger.debug(f"Player {player_id} not found, returning None")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching player {player_id}: {e}")
        return None
```

---

## Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Bare `try-except-pass`

**Bad**:
```python
try:
    important_operation()
except Exception:
    pass  # Silent failure - no way to debug!
```

**Good**:
```python
with contextlib.suppress(Exception):
    optional_operation()
```

**Why**: `contextlib.suppress()` is explicit about intentional suppression.

### ❌ Anti-Pattern 2: `try-except-continue` Without Logging

**Bad**:
```python
for item in items:
    try:
        process(item)
    except Exception:
        continue  # Which items failed? Why?
```

**Good**:
```python
for item in items:
    try:
        process(item)
    except Exception as e:
        logger.debug(f"Failed to process item {item.id}: {type(e).__name__}: {e}")
        continue
```

**Why**: You need to know which items failed and why for debugging.

### ❌ Anti-Pattern 3: Catching Too Broadly

**Bad**:
```python
try:
    result = calculate_score(player_data)
except Exception:
    result = 0  # Hides programming bugs!
```

**Good**:
```python
try:
    result = calculate_score(player_data)
except (ValueError, KeyError) as e:
    logger.warning(f"Invalid player data: {e}")
    result = 0
# Let other exceptions (TypeError, AttributeError) propagate
```

**Why**: Catch only exceptions you can handle; let bugs surface.

### ❌ Anti-Pattern 4: Logging and Re-raising Without Context

**Bad**:
```python
try:
    operation()
except Exception as e:
    logger.error(f"Error: {e}")
    raise  # Duplicate log entries in call stack!
```

**Good** (choose one):
```python
# Option 1: Log and handle
try:
    operation()
except Exception as e:
    logger.error(f"Operation failed: {e}")
    return default_value

# Option 2: Add context and re-raise
try:
    operation()
except Exception as e:
    raise OperationError(f"Failed to complete operation: {e}") from e

# Option 3: Just re-raise (let caller log)
try:
    operation()
except Exception:
    raise
```

---

## Testing Exception Handling Code

### Test That Exceptions Are Handled Correctly

```python
import pytest

async def test_player_profile_not_found_returns_none():
    """Test that missing player returns None instead of raising."""
    repo = PlayerProfileRepository(redis_client)

    # Should return None, not raise
    result = await repo.get_player_profile_safe("nonexistent")
    assert result is None

async def test_player_profile_not_found_raises():
    """Test that missing player raises exception."""
    repo = PlayerProfileRepository(redis_client)

    with pytest.raises(PlayerNotFoundError):
        await repo.get_player_profile("nonexistent")
```

### Test That Logging Occurs

```python
async def test_bulk_update_logs_failures(caplog):
    """Test that failed updates are logged."""
    repo = PlayerProfileRepository(redis_client)

    updates = [
        {"player_id": "valid", "data": {"score": 100}},
        {"player_id": "invalid", "data": None},  # Will fail
    ]

    with caplog.at_level(logging.DEBUG):
        result = await repo.bulk_update_profiles(updates)

    assert result["success"] == 1
    assert "invalid" in result["failed"]
    assert "Failed to update player profile invalid" in caplog.text
```

### Test That Cleanup Happens Even on Errors

```python
async def test_cleanup_on_error():
    """Test that resources are cleaned up even when operation fails."""
    monitor = WorkflowMonitor()

    try:
        await monitor.start_monitoring()
        raise ValueError("Simulated error")
    finally:
        await monitor.stop_monitoring()

    # Verify all tasks were cancelled
    assert all(task.cancelled() for task in monitor._background_tasks)
```

---

## Summary

| Pattern | Use When | Example |
|---------|----------|---------|
| `contextlib.suppress()` | Optional operations, expected errors | Cleanup, cache operations |
| Logging + Continue | Processing collections, non-critical failures | Bulk operations, background tasks |
| Logging + Return Default | Graceful degradation | API endpoints, user-facing features |
| Logging + Re-raise | Adding context, critical operations | Database operations, state changes |
| Just Re-raise | Caller should handle | Library code, utilities |

---

## References

- [PEP 343 – The "with" Statement](https://peps.python.org/pep-0343/)
- [Python contextlib Documentation](https://docs.python.org/3/library/contextlib.html)
- [Python Logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [Ruff S110 Rule](https://docs.astral.sh/ruff/rules/try-except-pass/)
- [Ruff S112 Rule](https://docs.astral.sh/ruff/rules/try-except-continue/)


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs development exception handling guidelines]]
