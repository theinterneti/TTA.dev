#!/usr/bin/env python3
"""
Comprehensive Observability Platform Demonstration

This demo showcases the TTA.dev observability platform in action, demonstrating:
1. Automatic metrics collection via InstrumentedPrimitive
2. Percentile latency tracking (p50, p90, p95, p99)
3. SLO compliance and error budget monitoring
4. Throughput and concurrency tracking
5. Cost tracking and savings from cache hits
6. Prometheus metrics export (if prometheus-client installed)

The demo creates a realistic multi-step AI workflow with:
- Sequential and parallel execution patterns
- Cache hits and misses
- Retry scenarios
- Varying latencies to demonstrate percentile tracking
- SLO violations and compliance

Run with: uv run python examples/observability_demo.py
"""

import asyncio
import random
import time
from typing import Any

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive
from tta_dev_primitives.core.parallel import ParallelPrimitive
from tta_dev_primitives.core.sequential import SequentialPrimitive
from tta_dev_primitives.observability import (
    InstrumentedPrimitive,
    get_enhanced_metrics_collector,
)
from tta_dev_primitives.performance.cache import CachePrimitive
from tta_dev_primitives.recovery.retry import RetryPrimitive, RetryStrategy

# Try to import Prometheus exporter (optional)
try:
    from tta_dev_primitives.observability.prometheus_exporter import (
        get_prometheus_exporter,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


# ============================================================================
# Demo Primitives - Simulating Real AI Workflow Components
# ============================================================================


class LLMCallPrimitive(InstrumentedPrimitive[dict, dict]):
    """
    Simulates an LLM API call with realistic latency and cost.

    Demonstrates:
    - Variable latency (50-500ms) for percentile tracking
    - Cost tracking ($0.01-$0.05 per call)
    - Occasional failures (5% error rate) for SLO tracking
    """

    def __init__(self, name: str = "llm_call", fail_rate: float = 0.05):
        super().__init__(name=name)
        self.fail_rate = fail_rate

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Simulate realistic LLM latency (50-500ms)
        latency = random.uniform(0.05, 0.5)
        await asyncio.sleep(latency)

        # Simulate occasional failures
        if random.random() < self.fail_rate:
            raise Exception("LLM API error (simulated)")

        # Simulate cost ($0.01-$0.05 per call)
        cost = random.uniform(0.01, 0.05)

        return {
            **input_data,
            "llm_response": f"Generated response for: {input_data.get('query', 'N/A')}",
            "cost": cost,
            "latency_ms": latency * 1000,
        }


class DataProcessingPrimitive(InstrumentedPrimitive[dict, dict]):
    """
    Simulates data processing with fast, consistent latency.

    Demonstrates:
    - Low latency (10-50ms) for comparison with LLM calls
    - High success rate (99.9%) for SLO compliance
    """

    def __init__(self, name: str = "data_processing"):
        super().__init__(name=name)

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Fast processing (10-50ms)
        await asyncio.sleep(random.uniform(0.01, 0.05))

        return {
            **input_data,
            "processed": True,
            "timestamp": time.time(),
        }


class ValidationPrimitive(InstrumentedPrimitive[dict, dict]):
    """
    Simulates input validation with very fast latency.

    Demonstrates:
    - Ultra-low latency (1-10ms)
    - Perfect success rate for SLO compliance
    """

    def __init__(self, name: str = "validation"):
        super().__init__(name=name)

    async def _execute_impl(self, input_data: dict, context: WorkflowContext) -> dict:
        # Very fast validation (1-10ms)
        await asyncio.sleep(random.uniform(0.001, 0.01))

        return {
            **input_data,
            "validated": True,
        }


# ============================================================================
# Demo Workflow Construction
# ============================================================================


def create_demo_workflow() -> WorkflowPrimitive[dict, dict]:
    """
    Create a realistic AI workflow demonstrating observability features.

    Workflow structure:
    1. Validation (fast, reliable)
    2. Parallel processing:
       - LLM call with retry (variable latency, occasional failures)
       - Data processing (fast, reliable)
    3. Cache wrapper (demonstrates cost savings)

    Returns:
        Composed workflow primitive
    """
    # Step 1: Fast validation
    validation = ValidationPrimitive(name="input_validation")

    # Step 2: LLM call with retry for resilience
    llm_call = LLMCallPrimitive(name="llm_generation", fail_rate=0.05)
    llm_with_retry = RetryPrimitive(
        llm_call,
        strategy=RetryStrategy(max_retries=3, backoff_base=1.5),
    )

    # Step 3: Data processing
    data_proc = DataProcessingPrimitive(name="data_enrichment")

    # Step 4: Parallel execution of LLM and data processing
    parallel_step = ParallelPrimitive([llm_with_retry, data_proc])

    # Step 5: Wrap with cache for cost savings
    # Cache key based on query to demonstrate cache hits
    cached_parallel = CachePrimitive(
        parallel_step,
        cache_key_fn=lambda data, ctx: str(data.get("query", "")),
        ttl_seconds=300.0,  # 5 minute cache
    )

    # Compose: validation >> cached parallel processing
    workflow = SequentialPrimitive([validation, cached_parallel])

    return workflow


# ============================================================================
# Metrics Display Utilities
# ============================================================================


def print_section_header(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_metrics_summary(primitive_name: str, metrics: dict[str, Any]) -> None:
    """Print formatted metrics for a primitive."""
    print(f"\n📊 Metrics for: {primitive_name}")
    print("-" * 60)

    # Percentiles
    if "percentiles" in metrics and metrics["percentiles"]:
        p = metrics["percentiles"]
        print("  Latency Percentiles:")
        print(f"    p50: {p.get('p50', 0):.2f}ms")
        print(f"    p90: {p.get('p90', 0):.2f}ms")
        print(f"    p95: {p.get('p95', 0):.2f}ms")
        print(f"    p99: {p.get('p99', 0):.2f}ms")

    # SLO
    if "slo" in metrics and metrics["slo"]:
        slo = metrics["slo"]
        compliance_icon = "✅" if slo.get("is_compliant", False) else "❌"
        print(f"\n  SLO Status: {compliance_icon}")
        print(f"    Target: {slo.get('target', 0) * 100:.1f}%")
        print(f"    Availability: {slo.get('availability', 0) * 100:.2f}%")
        print(f"    Latency Compliance: {slo.get('latency_compliance', 0) * 100:.2f}%")
        print(f"    Error Budget Remaining: {slo.get('error_budget_remaining', 0) * 100:.1f}%")

    # Throughput
    if "throughput" in metrics and metrics["throughput"]:
        t = metrics["throughput"]
        print("\n  Throughput:")
        print(f"    Total Requests: {t.get('total_requests', 0)}")
        print(f"    Active Requests: {t.get('active_requests', 0)}")
        print(f"    RPS: {t.get('requests_per_second', 0):.2f}")

    # Cost
    if "cost" in metrics and metrics["cost"]:
        c = metrics["cost"]
        if c.get("total_cost", 0) > 0 or c.get("total_savings", 0) > 0:
            print("\n  Cost Tracking:")
            print(f"    Total Cost: ${c.get('total_cost', 0):.4f}")
            print(f"    Total Savings: ${c.get('total_savings', 0):.4f}")
            print(f"    Net Cost: ${c.get('net_cost', 0):.4f}")
            if c.get("total_cost", 0) > 0:
                savings_pct = (c.get("total_savings", 0) / c.get("total_cost", 0)) * 100
                print(f"    Savings Rate: {savings_pct:.1f}%")


# ============================================================================
# Main Demo Execution
# ============================================================================


async def run_demo() -> None:
    """
    Run the comprehensive observability demo.

    Executes the workflow multiple times with different scenarios:
    1. Initial runs (cache misses)
    2. Repeated runs (cache hits - demonstrates cost savings)
    3. Varying load patterns (demonstrates percentile tracking)
    """
    print_section_header("TTA.dev Observability Platform Demo")

    # Get the global metrics collector
    collector = get_enhanced_metrics_collector()

    # Configure SLOs for different primitives
    print("🎯 Configuring SLOs...")
    collector.configure_slo(
        "input_validation",
        target=0.999,  # 99.9% availability
        threshold_ms=10.0,  # Under 10ms
    )
    collector.configure_slo(
        "llm_generation",
        target=0.95,  # 95% availability (allowing for 5% failures)
        threshold_ms=500.0,  # Under 500ms
    )
    collector.configure_slo(
        "data_enrichment",
        target=0.999,  # 99.9% availability
        threshold_ms=50.0,  # Under 50ms
    )
    print("✅ SLOs configured\n")

    # Create the workflow
    print("🔧 Building AI workflow...")
    workflow = create_demo_workflow()
    print("✅ Workflow created\n")

    # Run the workflow multiple times
    print_section_header("Phase 1: Initial Executions (Cache Misses)")

    num_initial_runs = 20
    print(f"Running workflow {num_initial_runs} times...")

    for i in range(num_initial_runs):
        context = WorkflowContext(
            workflow_id=f"demo-workflow-{i}",
            session_id="demo-session",
            metadata={"run_number": i + 1},
        )

        try:
            result = await workflow.execute(
                {"query": f"What is the meaning of life? (run {i + 1})"}, context
            )
            print(f"  ✓ Run {i + 1} completed")
        except Exception as e:
            print(f"  ✗ Run {i + 1} failed: {e}")

        # Small delay between runs
        await asyncio.sleep(0.1)

    print(f"\n✅ Completed {num_initial_runs} initial runs")

    # Display metrics after initial runs
    print_section_header("Metrics After Initial Runs")
    all_metrics = collector.get_all_primitives_metrics()
    for prim_name, prim_metrics in sorted(all_metrics.items()):
        print_metrics_summary(prim_name, prim_metrics)

    # Run again to demonstrate cache hits
    print_section_header("Phase 2: Repeated Executions (Cache Hits)")

    num_cache_runs = 10
    print(f"Running same queries {num_cache_runs} times (should hit cache)...")

    for i in range(num_cache_runs):
        context = WorkflowContext(
            workflow_id=f"demo-workflow-cached-{i}",
            session_id="demo-session",
            metadata={"run_number": num_initial_runs + i + 1, "cached": True},
        )

        try:
            result = await workflow.execute(
                {"query": "What is the meaning of life? (run 1)"},  # Same query
                context,
            )
            print(f"  ✓ Cached run {i + 1} completed")
        except Exception as e:
            print(f"  ✗ Cached run {i + 1} failed: {e}")

        await asyncio.sleep(0.05)

    print(f"\n✅ Completed {num_cache_runs} cached runs")

    # Final metrics
    print_section_header("Final Metrics Summary")
    all_metrics = collector.get_all_primitives_metrics()
    for prim_name, prim_metrics in sorted(all_metrics.items()):
        print_metrics_summary(prim_name, prim_metrics)

    # Prometheus export (if available)
    if PROMETHEUS_AVAILABLE:
        print_section_header("Prometheus Metrics Export")
        try:
            exporter = get_prometheus_exporter()
            print("✅ Prometheus exporter initialized")
            print("\n📊 Sample Prometheus metrics would be available at:")
            print("   http://localhost:8000/metrics")
            print("\nMetric types exported:")
            print("  - tta_workflow_primitive_duration_seconds (Histogram)")
            print("  - tta_workflow_slo_compliance_ratio (Gauge)")
            print("  - tta_workflow_error_budget_remaining (Gauge)")
            print("  - tta_workflow_requests_total (Counter)")
            print("  - tta_workflow_active_requests (Gauge)")
            print("  - tta_workflow_cost_total (Counter)")
            print("  - tta_workflow_savings_total (Counter)")
            print("  - tta_workflow_rps (Gauge)")
        except Exception as e:
            print(f"⚠️  Prometheus export not available: {e}")
    else:
        print_section_header("Prometheus Integration")
        print("ℹ️  Install prometheus-client to enable Prometheus metrics export:")
        print("   uv pip install prometheus-client")

    # Summary
    print_section_header("Demo Complete!")
    print("✅ Demonstrated:")
    print("  - Automatic metrics collection via InstrumentedPrimitive")
    print("  - Percentile latency tracking (p50, p90, p95, p99)")
    print("  - SLO compliance and error budget monitoring")
    print("  - Throughput and concurrency tracking")
    print("  - Cost tracking and cache savings")
    if PROMETHEUS_AVAILABLE:
        print("  - Prometheus metrics export")
    print("\n📚 Next steps:")
    print("  - View Grafana dashboards: dashboards/grafana/")
    print("  - Configure AlertManager: dashboards/alertmanager/")
    print("  - Integrate with your monitoring stack")
    print()


if __name__ == "__main__":
    asyncio.run(run_demo())
