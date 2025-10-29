"""OpenTelemetry APM setup and configuration."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.trace import TracerProvider

try:
    from opentelemetry import metrics, trace
    from opentelemetry.exporter.prometheus import PrometheusMetricReader
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logging.warning(
        "OpenTelemetry not installed. Install with: pip install tta-workflow-primitives[apm]"
    )

logger = logging.getLogger(__name__)

_tracer_provider: TracerProvider | None = None
_meter_provider: MeterProvider | None = None
_initialized = False


def setup_apm(
    service_name: str = "ai-workflow-primitives",
    service_version: str = "0.1.0",
    enable_prometheus: bool = True,
    enable_console: bool = False,
    prometheus_port: int = 9464,
) -> tuple[TracerProvider | None, MeterProvider | None]:
    """Setup OpenTelemetry APM for workflow primitives.

    Args:
        service_name: Name of the service
        service_version: Version of the service
        enable_prometheus: Enable Prometheus metrics export
        enable_console: Enable console export (for debugging)
        prometheus_port: Port for Prometheus metrics endpoint

    Returns:
        Tuple of (tracer_provider, meter_provider)

    Example:
        >>> from tta_workflow_primitives.apm import setup_apm
        >>> tracer, meter = setup_apm(
        ...     service_name="my-ai-app",
        ...     enable_prometheus=True
        ... )
    """
    global _tracer_provider, _meter_provider, _initialized

    if not OPENTELEMETRY_AVAILABLE:
        logger.warning("OpenTelemetry not available, APM disabled")
        return None, None

    if _initialized:
        logger.info("APM already initialized")
        return _tracer_provider, _meter_provider

    # Create resource with service info
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": service_version,
            "library.name": "tta-workflow-primitives",
        }
    )

    # Setup tracing
    _tracer_provider = TracerProvider(resource=resource)

    if enable_console:
        # Add console exporter for debugging
        console_processor = BatchSpanProcessor(ConsoleSpanExporter())
        _tracer_provider.add_span_processor(console_processor)
        logger.info("Console trace export enabled")

    trace.set_tracer_provider(_tracer_provider)
    logger.info(f"Tracer initialized for service: {service_name}")

    # Setup metrics
    if enable_prometheus:
        # Prometheus metrics reader
        prometheus_reader = PrometheusMetricReader()
        _meter_provider = MeterProvider(resource=resource, metric_readers=[prometheus_reader])
        metrics.set_meter_provider(_meter_provider)
        logger.info(f"Prometheus metrics enabled on port {prometheus_port}")
    else:
        _meter_provider = MeterProvider(resource=resource)
        metrics.set_meter_provider(_meter_provider)
        logger.info("Metrics provider initialized (no exporters)")

    _initialized = True

    return _tracer_provider, _meter_provider


def get_tracer(name: str = __name__) -> trace.Tracer | None:
    """Get a tracer instance.

    Args:
        name: Name for the tracer (usually __name__)

    Returns:
        Tracer instance or None if not initialized

    Example:
        >>> tracer = get_tracer(__name__)
        >>> with tracer.start_as_current_span("my_operation"):
        ...     # Your code here
        ...     pass
    """
    if not OPENTELEMETRY_AVAILABLE:
        return None

    if not _initialized:
        logger.warning("APM not initialized, call setup_apm() first")
        return None

    return trace.get_tracer(name)


def get_meter(name: str = __name__) -> metrics.Meter | None:
    """Get a meter instance.

    Args:
        name: Name for the meter (usually __name__)

    Returns:
        Meter instance or None if not initialized

    Example:
        >>> meter = get_meter(__name__)
        >>> counter = meter.create_counter(
        ...     "my_counter",
        ...     description="Number of operations"
        ... )
        >>> counter.add(1)
    """
    if not OPENTELEMETRY_AVAILABLE:
        return None

    if not _initialized:
        logger.warning("APM not initialized, call setup_apm() first")
        return None

    return metrics.get_meter(name)


def is_apm_enabled() -> bool:
    """Check if APM is enabled and initialized.

    Returns:
        True if APM is enabled, False otherwise
    """
    return OPENTELEMETRY_AVAILABLE and _initialized
