"""
APM (Application Performance Monitoring) Setup

Initializes OpenTelemetry tracing and metrics for TTA platform.
Provides graceful degradation when monitoring infrastructure unavailable.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.trace import TracerProvider

# Import OpenTelemetry components with graceful fallback
try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logging.warning(
        "OpenTelemetry not available. Install with: "
        "uv add opentelemetry-api opentelemetry-sdk opentelemetry-exporter-prometheus"
    )

logger = logging.getLogger(__name__)

# Global state
_tracer_provider: TracerProvider | None = None
_meter_provider: MeterProvider | None = None
_initialized = False


def initialize_observability(
    service_name: str = "tta",
    service_version: str = "0.1.0",
    enable_prometheus: bool = True,
    enable_console_traces: bool = None,
    prometheus_port: int = 9464,
) -> bool:
    """
    Initialize observability for TTA application.

    This sets up OpenTelemetry tracing and metrics collection with
    Prometheus export. Gracefully degrades when OpenTelemetry unavailable.

    Args:
        service_name: Name of the service for traces/metrics
        service_version: Version of the service
        enable_prometheus: Enable Prometheus metrics export
        enable_console_traces: Enable console trace export (auto-detects if None)
        prometheus_port: Port for Prometheus scraping (default: 9464)

    Returns:
        True if successfully initialized, False if degraded to no-op

    Example:
        >>> from observability_integration import initialize_observability
        >>> success = initialize_observability(
        ...     service_name="tta", enable_prometheus=True
        ... )
        >>> if success:
        ...     print("Observability enabled")
        ... else:
        ...     print("Observability degraded (no-op mode)")

    Raises:
        RuntimeError: If initialization fails catastrophically
    """
    global _tracer_provider, _meter_provider, _initialized

    if not OPENTELEMETRY_AVAILABLE:
        logger.warning(
            "OpenTelemetry not available - observability disabled. "
            "Metrics and traces will not be collected."
        )
        return False

    if _initialized:
        logger.info("Observability already initialized")
        return True

    # Auto-detect console export based on environment
    if enable_console_traces is None:
        enable_console_traces = os.getenv("ENVIRONMENT", "development") == "development"

    try:
        # Create resource with service metadata
        resource = Resource.create(
            {
                "service.name": service_name,
                "service.version": service_version,
                "library.name": "tta-observability-integration",
                "deployment.environment": os.getenv("ENVIRONMENT", "development"),
            }
        )

        # Setup tracing
        _tracer_provider = TracerProvider(resource=resource)

        if enable_console_traces:
            # Console exporter for development
            console_processor = BatchSpanProcessor(ConsoleSpanExporter())
            _tracer_provider.add_span_processor(console_processor)
            logger.info("Console trace export enabled (development mode)")

        trace.set_tracer_provider(_tracer_provider)
        logger.info(f"Tracer initialized for service: {service_name}")

        # Setup metrics
        if enable_prometheus:
            # Prometheus metrics reader
            prometheus_reader = PrometheusMetricReader()
            _meter_provider = MeterProvider(resource=resource, metric_readers=[prometheus_reader])
            metrics.set_meter_provider(_meter_provider)
            logger.info(
                f"Prometheus metrics enabled on port {prometheus_port}. "
                f"Scrape endpoint: http://localhost:{prometheus_port}/metrics"
            )
        else:
            _meter_provider = MeterProvider(resource=resource)
            metrics.set_meter_provider(_meter_provider)
            logger.info("Metrics provider initialized (no exporters)")

        _initialized = True
        logger.info(
            f"✅ Observability fully initialized for service '{service_name}' "
            f"(version {service_version})"
        )
        return True

    except Exception as e:
        logger.error(
            f"Failed to initialize observability: {e}. Degrading to no-op mode.",
            exc_info=True,
        )
        _initialized = False
        return False


def is_observability_enabled() -> bool:
    """
    Check if observability is enabled and initialized.

    Returns:
        True if OpenTelemetry is available and initialized

    Example:
        >>> if is_observability_enabled():
        ...     tracer = trace.get_tracer(__name__)
        ...     with tracer.start_as_current_span("my_operation"):
        ...         # Your code here
        ...         pass
    """
    return OPENTELEMETRY_AVAILABLE and _initialized


def get_tracer(name: str = __name__) -> trace.Tracer | None:
    """
    Get a tracer instance for creating spans.

    Args:
        name: Name for the tracer (usually __name__)

    Returns:
        Tracer instance or None if not initialized

    Example:
        >>> from observability_integration.apm_setup import get_tracer
        >>> tracer = get_tracer(__name__)
        >>> if tracer:
        ...     with tracer.start_as_current_span("my_operation"):
        ...         # Your code here
        ...         pass
    """
    if not is_observability_enabled():
        return None

    return trace.get_tracer(name)


def get_meter(name: str = __name__) -> metrics.Meter | None:
    """
    Get a meter instance for creating metrics.

    Args:
        name: Name for the meter (usually __name__)

    Returns:
        Meter instance or None if not initialized

    Example:
        >>> from observability_integration.apm_setup import get_meter
        >>> meter = get_meter(__name__)
        >>> if meter:
        ...     counter = meter.create_counter(
        ...         "my_counter", description="Number of operations"
        ...     )
        ...     counter.add(1)
    """
    if not is_observability_enabled():
        return None

    return metrics.get_meter(name)


def shutdown_observability() -> None:
    """
    Shutdown observability providers gracefully.

    This should be called on application shutdown to ensure all
    metrics and traces are flushed.

    Example:
        >>> import atexit
        >>> from observability_integration import shutdown_observability
        >>> atexit.register(shutdown_observability)
    """
    global _tracer_provider, _meter_provider, _initialized

    if not _initialized:
        return

    logger.info("Shutting down observability providers...")

    try:
        if _tracer_provider:
            _tracer_provider.shutdown()
            logger.info("Tracer provider shutdown complete")

        if _meter_provider:
            _meter_provider.shutdown()
            logger.info("Meter provider shutdown complete")

        _initialized = False
        logger.info("✅ Observability shutdown complete")

    except Exception as e:
        logger.error(f"Error during observability shutdown: {e}", exc_info=True)
