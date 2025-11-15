"""
Example: Adaptive Primitives with Prometheus Metrics

Demonstrates how to use adaptive primitives with full Prometheus metrics integration
for observing the learning process, strategy effectiveness, and circuit breaker behavior.

This example shows:
1. Setting up OpenTelemetry metrics (optional - graceful degradation)
2. Using AdaptiveRetryPrimitive with metrics collection
3. Observing learning metrics in real-time
4. Querying metrics for analysis
5. Creating custom Grafana dashboards

Requirements:
- opentelemetry-api (optional - for metrics)
- opentelemetry-sdk (optional - for exporting)
- prometheus-client (optional - for Prometheus exporter)

Run:
    python examples/adaptive_metrics_demo.py
"""

import asyncio
import logging
import random
import time

from tta_dev_primitives.adaptive import (
    AdaptiveRetryPrimitive,
    LearningMode,
    get_adaptive_metrics,
)
from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Simulated unreliable API
class UnreliableAPIPrimitive(WorkflowPrimitive[dict, dict]):
    """Simulates an unreliable API for demonstration."""

    def __init__(self, failure_rate: float = 0.3):
        super().__init__()
        self.failure_rate = failure_rate
        self.call_count = 0

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Execute with simulated failures."""
        self.call_count += 1

        # Simulate network delay
        await asyncio.sleep(random.uniform(0.1, 0.3))

        # Simulate failures
        if random.random() < self.failure_rate:
            raise Exception(f"API call failed (attempt {self.call_count})")

        return {
            "status": "success",
            "data": f"Response from API (call {self.call_count})",
            "timestamp": time.time(),
        }


async def demo_basic_metrics():
    """Demonstrate basic metrics collection."""
    print("\n" + "=" * 80)
    print("DEMO 1: Basic Metrics Collection")
    print("=" * 80)

    # Get metrics collector
    metrics = get_adaptive_metrics()

    if not metrics.enabled:
        print("\n⚠️  OpenTelemetry not available - metrics collection disabled")
        print("Install 'opentelemetry-api' to enable metrics:")
        print("  uv pip install opentelemetry-api opentelemetry-sdk")
        print("\nContinuing with demo (metrics will be no-ops)...\n")
    else:
        print("\n✅ Metrics collection enabled with OpenTelemetry\n")

    # Simulate learning events
    print("Simulating learning events...")

    # Strategy creation
    metrics.record_strategy_created("AdaptiveRetryPrimitive", "production_v1", "production")
    print("  ✓ Recorded strategy creation: production_v1")

    # Validation success
    metrics.record_validation_success(
        "AdaptiveRetryPrimitive", "production_v1", duration_seconds=1.5
    )
    print("  ✓ Recorded validation success (1.5s)")

    # Strategy adoption
    metrics.record_strategy_adopted("AdaptiveRetryPrimitive", "production_v1", "production")
    print("  ✓ Recorded strategy adoption")

    # Strategy execution
    metrics.record_strategy_execution(
        "AdaptiveRetryPrimitive",
        "production_v1",
        success_rate=0.95,
        latency_ms=250,
    )
    print("  ✓ Recorded execution: 95% success, 250ms latency")

    # Performance improvement
    metrics.record_performance_improvement(
        "AdaptiveRetryPrimitive",
        "success_rate",
        improvement_pct=15.0,  # 15% better than baseline
    )
    print("  ✓ Recorded 15% performance improvement")

    # Update active strategies count
    metrics.update_active_strategies("AdaptiveRetryPrimitive", delta=1)
    print("  ✓ Updated active strategies count")

    print("\n✅ Basic metrics demo complete")


async def demo_adaptive_retry_with_metrics():
    """Demonstrate adaptive retry with automatic metrics collection."""
    print("\n" + "=" * 80)
    print("DEMO 2: Adaptive Retry with Automatic Metrics")
    print("=" * 80)

    # Create unreliable API
    api = UnreliableAPIPrimitive(failure_rate=0.4)  # 40% failure rate

    # Create adaptive retry with metrics
    adaptive_retry = AdaptiveRetryPrimitive(
        target_primitive=api,
        learning_mode=LearningMode.ACTIVE,
        circuit_breaker_threshold=0.5,  # Trip at 50% failure rate
        validation_window=10,  # Validate strategies over 10 executions
    )

    print(f"\nCreated adaptive retry (learning mode: {LearningMode.ACTIVE.value})")
    print("Will execute 20 operations to trigger learning...\n")

    # Execute multiple times to trigger learning
    context = WorkflowContext(correlation_id="demo-metrics")
    successes = 0
    failures = 0

    for i in range(20):
        try:
            _ = await adaptive_retry.execute({"operation": f"request_{i}"}, context)
            successes += 1
            print(f"  ✓ Request {i + 1}: Success")
        except Exception as e:
            failures += 1
            print(f"  ✗ Request {i + 1}: Failed - {e}")

        # Add small delay between requests
        await asyncio.sleep(0.1)

    print(f"\n📊 Results: {successes} successes, {failures} failures")
    print(f"📊 Success rate: {successes / 20 * 100:.1f}%")

    # Show learned strategies
    print("\n📚 Learned Strategies:")
    for name, strategy in adaptive_retry.strategies.items():
        print(f"\n  Strategy: {name}")
        print(f"    Success Rate: {strategy.metrics.success_rate * 100:.1f}%")
        print(f"    Avg Latency: {strategy.metrics.avg_latency * 1000:.0f}ms")
        print(f"    Observations: {strategy.metrics.total_executions}")

    print("\n✅ Adaptive retry with metrics demo complete")


async def demo_circuit_breaker_metrics():
    """Demonstrate circuit breaker metrics."""
    print("\n" + "=" * 80)
    print("DEMO 3: Circuit Breaker Metrics")
    print("=" * 80)

    metrics = get_adaptive_metrics()

    # Simulate circuit breaker scenarios
    print("\nSimulating circuit breaker events...")

    # Circuit breaker trip
    metrics.record_circuit_breaker_trip("AdaptiveRetryPrimitive", "high_failure_rate")
    print("  ✓ Recorded circuit breaker trip (high_failure_rate)")

    # Fallback activation
    metrics.record_fallback_activation("AdaptiveRetryPrimitive", "circuit_breaker")
    print("  ✓ Recorded fallback to baseline")

    # Simulate cooldown period
    print("\n  ⏳ Simulating cooldown period (2 seconds)...")
    await asyncio.sleep(2)

    # Circuit breaker reset
    metrics.record_circuit_breaker_reset("AdaptiveRetryPrimitive")
    print("  ✓ Recorded circuit breaker reset")

    print("\n✅ Circuit breaker metrics demo complete")


async def demo_context_metrics():
    """Demonstrate context-aware metrics."""
    print("\n" + "=" * 80)
    print("DEMO 4: Context-Aware Metrics")
    print("=" * 80)

    metrics = get_adaptive_metrics()

    # Simulate context switches
    print("\nSimulating context switches...")

    contexts = ["development", "staging", "production"]
    for i in range(len(contexts) - 1):
        from_ctx = contexts[i]
        to_ctx = contexts[i + 1]

        metrics.record_context_switch("AdaptiveRetryPrimitive", from_ctx, to_ctx)
        print(f"  ✓ Context switch: {from_ctx} → {to_ctx}")

        # Record strategy creation in new context
        metrics.record_strategy_created("AdaptiveRetryPrimitive", f"{to_ctx}_v1", to_ctx)
        print(f"  ✓ Created strategy for {to_ctx} context")

    # Simulate context drift
    print("\nSimulating context drift detection...")
    metrics.record_context_drift("AdaptiveRetryPrimitive", "production")
    print("  ✓ Detected context drift in production")

    print("\n✅ Context metrics demo complete")


async def demo_validation_metrics():
    """Demonstrate validation metrics."""
    print("\n" + "=" * 80)
    print("DEMO 5: Strategy Validation Metrics")
    print("=" * 80)

    metrics = get_adaptive_metrics()

    # Simulate validation scenarios
    print("\nSimulating strategy validation...")

    # Successful validation
    metrics.record_validation_success("AdaptiveRetryPrimitive", "prod_v2", duration_seconds=2.5)
    print("  ✓ Validation success: prod_v2 (2.5s)")

    # Failed validation - performance regression
    metrics.record_validation_failure(
        "AdaptiveRetryPrimitive",
        "prod_v3",
        reason="performance_regression",
        duration_seconds=1.8,
    )
    print("  ✗ Validation failure: prod_v3 (performance_regression)")

    # Strategy rejection
    metrics.record_strategy_rejected(
        "AdaptiveRetryPrimitive",
        "prod_v3",
        reason="insufficient_improvement",
        context="production",
    )
    print("  ✗ Strategy rejected: prod_v3 (insufficient_improvement)")

    # Failed validation - insufficient data
    metrics.record_validation_failure(
        "AdaptiveRetryPrimitive",
        "prod_v4",
        reason="insufficient_data",
        duration_seconds=0.5,
    )
    print("  ✗ Validation failure: prod_v4 (insufficient_data)")

    print("\n✅ Validation metrics demo complete")


def print_prometheus_queries():
    """Print example Prometheus queries for the metrics."""
    print("\n" + "=" * 80)
    print("Prometheus Query Examples")
    print("=" * 80)

    queries = [
        (
            "Strategy Creation Rate",
            'rate(adaptive_strategies_created_total{primitive_type="AdaptiveRetryPrimitive"}[5m])',
        ),
        (
            "Validation Success Rate",
            "rate(adaptive_validation_success_total[5m]) / "
            "rate(adaptive_validation_success_total[5m] + adaptive_validation_failure_total[5m])",
        ),
        (
            "Average Performance Improvement",
            'avg(adaptive_performance_improvement_pct{metric="success_rate"})',
        ),
        (
            "Circuit Breaker Trip Rate",
            "rate(adaptive_circuit_breaker_trips_total[5m])",
        ),
        (
            "Active Strategies by Type",
            "adaptive_active_strategies",
        ),
        (
            "Strategy Effectiveness",
            'adaptive_strategy_effectiveness{metric="success_rate"}',
        ),
        (
            "Context Switches",
            "rate(adaptive_context_switches_total[1h])",
        ),
        (
            "Learning Rate",
            'adaptive_learning_rate{primitive_type="AdaptiveRetryPrimitive"}',
        ),
    ]

    print("\nUse these queries in Prometheus or Grafana:\n")
    for name, query in queries:
        print(f"{name}:")
        print(f"  {query}\n")


def print_grafana_dashboard_json():
    """Print example Grafana dashboard JSON."""
    print("\n" + "=" * 80)
    print("Grafana Dashboard Template")
    print("=" * 80)

    dashboard = """
{
  "dashboard": {
    "title": "Adaptive Primitives - Learning Metrics",
    "panels": [
      {
        "title": "Strategy Creation Rate",
        "targets": [
          {
            "expr": "rate(adaptive_strategies_created_total[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Validation Success Rate",
        "targets": [
          {
            "expr": "rate(adaptive_validation_success_total[5m]) / rate(adaptive_validation_success_total[5m] + adaptive_validation_failure_total[5m])"
          }
        ],
        "type": "gauge"
      },
      {
        "title": "Circuit Breaker Trips",
        "targets": [
          {
            "expr": "rate(adaptive_circuit_breaker_trips_total[5m])"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Active Strategies",
        "targets": [
          {
            "expr": "adaptive_active_strategies"
          }
        ],
        "type": "stat"
      }
    ]
  }
}
"""
    print("\nGrafana Dashboard JSON (simplified):")
    print(dashboard)
    print("\nImport this JSON into Grafana to create the dashboard.")
    print("Full dashboard available in: monitoring/grafana/dashboards/adaptive-primitives.json")


async def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("ADAPTIVE PRIMITIVES - PROMETHEUS METRICS DEMO")
    print("=" * 80)
    print("\nThis demo shows how adaptive primitives automatically collect")
    print("Prometheus metrics for observing the learning process.\n")

    # Run all demos
    await demo_basic_metrics()
    await demo_adaptive_retry_with_metrics()
    await demo_circuit_breaker_metrics()
    await demo_context_metrics()
    await demo_validation_metrics()

    # Print Prometheus query examples
    print_prometheus_queries()

    # Print Grafana dashboard template
    print_grafana_dashboard_json()

    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\n📊 Metrics Integration Summary:")
    print("  ✅ Learning metrics - Track strategy creation and adoption")
    print("  ✅ Validation metrics - Monitor strategy validation success/failure")
    print("  ✅ Performance metrics - Measure strategy effectiveness")
    print("  ✅ Safety metrics - Track circuit breaker trips and fallbacks")
    print("  ✅ Context metrics - Observe context switches and drift")
    print("\n💡 Next Steps:")
    print("  1. Install OpenTelemetry: uv pip install opentelemetry-api opentelemetry-sdk")
    print("  2. Set up Prometheus exporter (see tta-observability-integration)")
    print("  3. Create Grafana dashboards using queries above")
    print("  4. Monitor learning in real-time at http://localhost:9090 (Prometheus)")
    print("  5. View dashboards at http://localhost:3000 (Grafana)")
    print()


if __name__ == "__main__":
    asyncio.run(main())
