"""Demo of AdaptiveTimeoutPrimitive learning optimal timeout values."""

import asyncio
import random

from tta_dev_primitives.adaptive import AdaptiveTimeoutPrimitive, LearningMode
from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.observability.instrumented_primitive import (
    InstrumentedPrimitive,
)


class VariableLatencyService(InstrumentedPrimitive[dict, dict]):
    """Mock service with controllable latency."""

    def __init__(self, name: str, base_latency_ms: float = 100.0) -> None:
        super().__init__()
        self.name = name
        self.base_latency_ms = base_latency_ms

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute with variable latency."""
        # Simulate variable latency (50% to 150% of base)
        latency_ms = self.base_latency_ms * (0.5 + random.random())
        await asyncio.sleep(latency_ms / 1000.0)

        return {
            "service": self.name,
            "latency_ms": latency_ms,
            "input": input_data,
        }


async def main() -> None:
    """Demonstrate adaptive timeout learning."""
    print("=" * 80)
    print("AdaptiveTimeoutPrimitive Demo - Learning Optimal Timeouts")
    print("=" * 80)
    print()

    # Create service with 200ms base latency (100-300ms range)
    service = VariableLatencyService("variable_api", base_latency_ms=200.0)

    # Create adaptive timeout with conservative initial timeout
    adaptive_timeout = AdaptiveTimeoutPrimitive(
        target_primitive=service,
        baseline_timeout_ms=500.0,  # Conservative starting point
        baseline_percentile_target=95,
        baseline_buffer_factor=1.5,
        learning_mode=LearningMode.ACTIVE,
        min_observations_before_learning=10,
    )

    print("Configuration:")
    print(f"  Service: {service.name} (latency: 100-300ms)")
    print("  Initial timeout: 500ms")
    print("  Learning mode: ACTIVE")
    print("  Min observations: 10")
    print()

    # Phase 1: Initial executions
    print("Phase 1: Initial executions (baseline timeout)")
    print("-" * 80)

    for i in range(15):
        context = WorkflowContext(
            correlation_id=f"req-{i}",
            metadata={"environment": "production"},
        )

        try:
            result = await adaptive_timeout.execute({"request_id": i}, context)
            print(f"  Request {i}: SUCCESS - Latency: {result['latency_ms']:.1f}ms")
        except Exception as e:
            print(f"  Request {i}: TIMEOUT - {type(e).__name__}")

    # Check stats after initial phase
    stats = adaptive_timeout.get_timeout_stats()
    print()
    print("Stats after initial phase:")
    print(f"  Total executions: {stats['total_executions']}")
    print(f"  Success count: {stats['success_count']}")
    print(f"  Timeout count: {stats['timeout_count']}")
    print(f"  Timeout rate: {stats['timeout_rate']:.1%}")
    print(
        f"  Latency - p50: {stats['latencies']['p50_ms']:.1f}ms, "
        f"p95: {stats['latencies']['p95_ms']:.1f}ms, "
        f"p99: {stats['latencies']['p99_ms']:.1f}ms"
    )
    print(f"  Current timeout: {stats['current_timeout_ms']:.1f}ms")
    print()

    # Check if new strategy was learned
    if len(adaptive_timeout.strategies) > 1:
        print("✅ New strategy learned!")
        for name, strategy in adaptive_timeout.strategies.items():
            if name != "baseline":
                print(f"  Strategy: {name}")
                print(f"    Timeout: {strategy.parameters['timeout_ms']:.1f}ms")
                print(f"    Percentile target: p{strategy.parameters['percentile_target']}")
                print(f"    Buffer factor: {strategy.parameters['buffer_factor']}")
                print(f"    Description: {strategy.description}")
                print()

    # Phase 2: Continued execution with learned strategy
    print("Phase 2: Continued execution (with learned strategy)")
    print("-" * 80)

    for i in range(15, 30):
        context = WorkflowContext(
            correlation_id=f"req-{i}",
            metadata={"environment": "production"},
        )

        try:
            result = await adaptive_timeout.execute({"request_id": i}, context)
            print(f"  Request {i}: SUCCESS - Latency: {result['latency_ms']:.1f}ms")
        except Exception as e:
            print(f"  Request {i}: TIMEOUT - {type(e).__name__}")

    # Final stats
    stats = adaptive_timeout.get_timeout_stats()
    print()
    print("Final Statistics:")
    print("=" * 80)
    print(f"Total executions: {stats['total_executions']}")
    print(f"Success count: {stats['success_count']}")
    print(f"Timeout count: {stats['timeout_count']}")
    print(f"Timeout rate: {stats['timeout_rate']:.1%}")
    print()
    print("Latency Distribution:")
    print(f"  p50: {stats['latencies']['p50_ms']:.1f}ms")
    print(f"  p95: {stats['latencies']['p95_ms']:.1f}ms")
    print(f"  p99: {stats['latencies']['p99_ms']:.1f}ms")
    print(f"  avg: {stats['latencies']['avg_ms']:.1f}ms")
    print(f"  min: {stats['latencies']['min_ms']:.1f}ms")
    print(f"  max: {stats['latencies']['max_ms']:.1f}ms")
    print()
    print(f"Current timeout: {stats['current_timeout_ms']:.1f}ms")
    print()

    # Show all strategies
    print("Active Strategies:")
    print("-" * 80)
    for name, strategy_stats in stats["strategies"].items():
        print(f"  {name}:")
        print(f"    Timeout: {strategy_stats['timeout_ms']:.1f}ms")
        print(f"    Percentile target: p{strategy_stats['percentile_target']}")
        print(f"    Buffer factor: {strategy_stats['buffer_factor']}")
        print(f"    Success rate: {strategy_stats['success_rate']:.1%}")
        print(f"    Avg latency: {strategy_stats['avg_latency_ms']:.1f}ms")
        print()

    print("=" * 80)
    print("Demo complete! AdaptiveTimeoutPrimitive successfully learned optimal timeout.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
