"""
Example: Production Observability with Sampling and Optimization

This example demonstrates how to use Phase 4 production hardening features
including sampling, cardinality controls, and health monitoring.
"""

import asyncio

from tta_dev_primitives.core.base import WorkflowContext
from tta_dev_primitives.observability import (
    ObservabilityConfig,
    ObservablePrimitive,
    get_health_checker,
    get_metrics_collector,
    set_observability_config,
)
from tta_dev_primitives.testing import MockPrimitive


async def main() -> None:
    """Demonstrate production observability features."""

    print("=" * 70)
    print("Phase 4: Production Observability Example")
    print("=" * 70)
    print()

    # 1. Configure observability for production
    print("1. Setting up production configuration...")
    config = ObservabilityConfig.from_environment("production")
    set_observability_config(config)

    print(f"   Environment: {config.environment}")
    print(f"   Sampling rate: {config.tracing.sampling.default_rate * 100}%")
    print(f"   Adaptive sampling: {config.tracing.sampling.adaptive_enabled}")
    print(f"   Max label values: {config.metrics.max_label_values}")
    print(f"   Trace TTL: {config.storage.trace_ttl_days} days")
    print()

    # 2. Create workflow with observable primitives
    print("2. Creating workflow with observability...")

    # Create mock primitives
    validate_primitive = MockPrimitive("validate", return_value={"validated": True})
    process_primitive = MockPrimitive("process", return_value={"processed": True})
    save_primitive = MockPrimitive("save", return_value={"saved": True})

    # Wrap with observability (automatic sampling)
    workflow = (
        ObservablePrimitive(validate_primitive, "validate_input")
        >> ObservablePrimitive(process_primitive, "process_data")
        >> ObservablePrimitive(save_primitive, "save_result")
    )

    print("   Workflow created with 3 observable primitives")
    print()

    # 3. Execute workflow multiple times to generate data
    print("3. Executing workflow 100 times...")

    for i in range(100):
        context = WorkflowContext(
            workflow_id=f"workflow-{i}",
            correlation_id=f"trace-{i % 10}",  # 10 unique traces
        )
        await workflow.execute({"data": f"request-{i}"}, context)

        if (i + 1) % 25 == 0:
            print(f"   Completed {i + 1}/100 executions")

    print()

    # 4. Check metrics with cardinality
    print("4. Checking metrics and cardinality...")
    collector = get_metrics_collector()

    # Get metrics for each primitive
    for primitive_name in ["validate_input", "process_data", "save_result"]:
        metrics = collector.get_metrics(primitive_name)
        print(f"   {primitive_name}:")
        print(f"     Total executions: {metrics['total_executions']}")
        print(f"     Success rate: {metrics['success_rate'] * 100:.1f}%")
        print(f"     Avg duration: {metrics['average_duration_ms']:.2f}ms")

    # Check cardinality
    stats = collector.get_cardinality_stats()
    print(f"   Cardinality stats:")
    print(f"     Unique primitives: {stats['unique_primitives']}")
    print(f"     Total labels: {stats['total_labels']}")
    print(f"     Dropped labels: {stats['dropped_labels']}")
    print()

    # 5. Test error handling with tail-based sampling
    print("5. Testing error handling (always sampled)...")

    error_primitive = MockPrimitive("error", side_effect=ValueError("Test error"))
    error_observable = ObservablePrimitive(error_primitive, "error_test")

    try:
        context = WorkflowContext(workflow_id="error-workflow")
        await error_observable.execute({"data": "test"}, context)
    except ValueError:
        print("   Error caught and traced (always sampled)")

    # Check error metrics
    error_metrics = collector.get_metrics("error_test")
    print(f"   Failed executions: {error_metrics['failed_executions']}")
    print(f"   Error types: {error_metrics['error_counts']}")
    print()

    # 6. Check health status
    print("6. Checking observability health...")
    health = get_health_checker()

    result = health.check_health()
    print(f"   Health status: {result.status.value}")
    print(f"   Message: {result.message}")
    print(f"   Config loaded: {result.details.get('config_loaded')}")
    print(f"   Tracing available: {result.details.get('tracing_available')}")
    print()

    # 7. Get sampling status
    print("7. Sampling status:")
    sampling_status = health.get_sampling_status()
    print(f"   Enabled: {sampling_status['enabled']}")
    print(f"   Rate: {sampling_status['sampling_rate'] * 100}%")
    print(f"   Always sample errors: {sampling_status['always_sample_errors']}")
    print(f"   Always sample slow: {sampling_status['always_sample_slow']}")
    print(f"   Slow threshold: {sampling_status['slow_threshold_ms']}ms")
    print()

    # 8. Get full system status
    print("8. Full system status:")
    full_status = health.get_full_status()

    print(f"   Service: {full_status['system']['service_name']}")
    print(f"   Version: {full_status['system']['service_version']}")
    print(f"   Environment: {full_status['system']['environment']}")
    print(f"   Uptime: {full_status['system']['uptime_seconds']:.2f}s")
    print()
    print(f"   Total primitives: {full_status['metrics']['total_primitives']}")
    print(f"   Total executions: {full_status['metrics']['total_executions']}")
    print(f"   Total errors: {full_status['metrics']['total_errors']}")
    print()

    # 9. Demonstrate adaptive sampling
    print("9. Adaptive sampling (requires adaptive enabled):")
    if config.tracing.sampling.adaptive_enabled:
        print("   Adaptive sampling is enabled")
        print(
            f"   Min rate: {config.tracing.sampling.adaptive_min_rate * 100}%"
        )
        print(
            f"   Max rate: {config.tracing.sampling.adaptive_max_rate * 100}%"
        )
        print(
            f"   Target overhead: {config.tracing.sampling.adaptive_target_overhead * 100}%"
        )
    else:
        print("   Adaptive sampling is disabled (enable in config)")
    print()

    # 10. Summary
    print("=" * 70)
    print("Summary:")
    print("=" * 70)
    print(f"✅ Configuration: {config.environment} environment")
    print(f"✅ Sampling: {config.tracing.sampling.default_rate * 100}% base rate")
    print(f"✅ Executions: {full_status['metrics']['total_executions']} total")
    print(f"✅ Errors: Always sampled (tail-based)")
    print(f"✅ Cardinality: {stats['total_labels']} labels tracked")
    print(f"✅ Health: {result.status.value}")
    print()
    print("Phase 4 production hardening features demonstrated successfully!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
