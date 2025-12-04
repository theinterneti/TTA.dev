"""
Error handling and recovery patterns for tta-dev-primitives.

This example demonstrates robust error handling strategies using
recovery primitives.
"""

import asyncio
from typing import Any

from tta_dev_primitives.core.base import LambdaPrimitive, WorkflowContext
from tta_dev_primitives.core.sequential import SequentialPrimitive
from tta_dev_primitives.recovery.fallback import FallbackPrimitive
from tta_dev_primitives.recovery.retry import RetryPrimitive, RetryStrategy
from tta_dev_primitives.recovery.timeout import TimeoutPrimitive


# Example 1: Retry with Exponential Backoff
async def retry_example() -> dict[str, Any]:
    """Demonstrate retry logic with exponential backoff."""

    attempt_counter = {"count": 0}

    def flaky_operation(x: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        """Simulates a flaky API that fails first 2 times."""
        attempt_counter["count"] += 1
        if attempt_counter["count"] < 3:
            raise ValueError(f"Attempt {attempt_counter['count']} failed!")
        return {**x, "result": "success", "attempts": attempt_counter["count"]}

    # Retry up to 5 times with exponential backoff
    retry_primitive = RetryPrimitive(
        primitive=LambdaPrimitive(flaky_operation),
        strategy=RetryStrategy(max_retries=5, backoff_base=2.0, jitter=False),
    )

    context = WorkflowContext(workflow_id="retry-demo", session_id="test-1")
    result = await retry_primitive.execute({"input": "data"}, context)

    print("Retry Example:")
    print(f"  Result: {result['result']}")
    print(f"  Total attempts: {result['attempts']}")
    print("  Success after retries!\n")

    return result


# Example 2: Fallback Chain
async def fallback_chain_example() -> dict[str, Any]:
    """Demonstrate fallback chain with multiple fallback options."""

    # Primary (fails)
    primary = LambdaPrimitive(
        lambda x, ctx: (_ for _ in ()).throw(ConnectionError("Primary service unavailable"))
    )

    # First fallback (also fails)
    first_fallback = LambdaPrimitive(
        lambda x, ctx: (_ for _ in ()).throw(ConnectionError("Fallback service unavailable"))
    )

    # Second fallback (succeeds)
    second_fallback = LambdaPrimitive(
        lambda x, ctx: {**x, "result": "from backup service", "fallback_level": 2}
    )

    # Chain fallbacks
    workflow = FallbackPrimitive(
        primary=primary,
        fallback=FallbackPrimitive(primary=first_fallback, fallback=second_fallback),
    )

    context = WorkflowContext(workflow_id="fallback-demo", session_id="test-2")
    result = await workflow.execute({"request": "data"}, context)

    print("Fallback Chain Example:")
    print(f"  Result: {result['result']}")
    print(f"  Fallback level used: {result['fallback_level']}\n")

    return result


# Example 3: Timeout Protection
async def timeout_example() -> dict[str, Any]:
    """Demonstrate timeout protection for long-running operations."""

    async def slow_operation(x: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        """Simulates a slow operation."""
        await asyncio.sleep(2.0)  # Takes 2 seconds
        return {**x, "result": "completed"}

    # Wrap with 1-second timeout
    timeout_primitive = TimeoutPrimitive(
        primitive=LambdaPrimitive(slow_operation), timeout_seconds=1.0
    )

    context = WorkflowContext(workflow_id="timeout-demo", session_id="test-3")

    try:
        result = await timeout_primitive.execute({"task": "process"}, context)
        print("Timeout Example: Operation completed (unexpected!)")
    except TimeoutError:
        print("Timeout Example: Operation timed out as expected after 1 second\n")
        result = {"timed_out": True}

    return result


# Example 4: Combined Recovery Strategies
async def combined_recovery_example() -> dict[str, Any]:
    """Combine retry, timeout, and fallback for robust error handling."""

    # Primary operation with retry and timeout
    primary_with_protection = TimeoutPrimitive(
        primitive=RetryPrimitive(
            primitive=LambdaPrimitive(
                lambda x, ctx: {**x, "result": "primary succeeded", "source": "primary"}
            ),
            strategy=RetryStrategy(max_retries=2, backoff_base=2.0, jitter=False),
        ),
        timeout_seconds=5.0,
    )

    # Fallback operation
    fallback_operation = LambdaPrimitive(
        lambda x, ctx: {**x, "result": "fallback succeeded", "source": "fallback"}
    )

    # Combine strategies
    robust_workflow = FallbackPrimitive(
        primary=primary_with_protection, fallback=fallback_operation
    )

    context = WorkflowContext(workflow_id="combined-demo", session_id="test-4")
    result = await robust_workflow.execute({"data": "important"}, context)

    print("Combined Recovery Example:")
    print(f"  Result: {result['result']}")
    print(f"  Source: {result['source']}\n")

    return result


# Example 5: Real-World API Integration with Full Error Handling
async def api_integration_example() -> dict[str, Any]:
    """Realistic example of integrating with external API."""

    # Simulate API call with potential failures
    api_call_count = {"count": 0}

    async def call_api(x: dict[str, Any], ctx: WorkflowContext) -> dict[str, Any]:
        """Simulates an API call that might fail or timeout."""
        api_call_count["count"] += 1

        # Simulate occasional failures
        if api_call_count["count"] == 1:
            raise ConnectionError("Network error")

        await asyncio.sleep(0.1)  # Simulate network latency

        return {
            **x,
            "api_response": {
                "status": "success",
                "data": {"processed": True},
                "call_number": api_call_count["count"],
            },
        }

    # Build robust API integration workflow
    api_workflow = FallbackPrimitive(
        # Primary: API with retry and timeout
        primary=TimeoutPrimitive(
            primitive=RetryPrimitive(
                primitive=LambdaPrimitive(call_api),
                strategy=RetryStrategy(max_retries=3, backoff_base=1.5, jitter=False),
            ),
            timeout_seconds=2.0,
        ),
        # Fallback: Return cached or default response
        fallback=LambdaPrimitive(
            lambda x, ctx: {
                **x,
                "api_response": {
                    "status": "cached",
                    "data": {"processed": False},
                    "source": "cache",
                },
            }
        ),
    )

    # Add pre and post processing
    full_workflow = SequentialPrimitive(
        [
            LambdaPrimitive(lambda x, ctx: {**x, "timestamp": "2024-10-28T12:00:00Z"}),
            api_workflow,
            LambdaPrimitive(lambda x, ctx: {**x, "completed": True}),
        ]
    )

    context = WorkflowContext(workflow_id="api-integration", session_id="test-5")
    result = await full_workflow.execute({"request_id": "12345"}, context)

    print("API Integration Example:")
    print(f"  API Status: {result['api_response']['status']}")
    print(f"  Call Number: {result['api_response'].get('call_number', 'N/A')}")
    print(f"  Completed: {result['completed']}\n")

    return result


async def main() -> None:
    """Run all error handling examples."""
    print("=" * 60)
    print("TTA-Dev-Primitives: Error Handling & Recovery Patterns")
    print("=" * 60)
    print()

    await retry_example()
    await fallback_chain_example()
    await timeout_example()
    await combined_recovery_example()
    await api_integration_example()

    print("=" * 60)
    print("All error handling examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
