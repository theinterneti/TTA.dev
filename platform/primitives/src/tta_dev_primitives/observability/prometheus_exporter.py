"""
Prometheus Metrics Exporter for TTA.dev Observability

Provides HTTP metrics endpoint compatible with Prometheus scraping.
Exports all collected metrics from the enhanced metrics collector.
"""

import threading
from collections.abc import Iterator
from typing import Any

try:
    from prometheus_client import (
        REGISTRY,
        start_http_server,
    )
    from prometheus_client.core import (
        CounterMetricFamily,
        GaugeMetricFamily,
        HistogramMetricFamily,
    )

    PROMETHEUS_CLIENT_AVAILABLE = True
except ImportError:
    PROMETHEUS_CLIENT_AVAILABLE = False
    start_http_server = None  # type: ignore
    REGISTRY = None  # type: ignore

from .enhanced_collector import get_enhanced_metrics_collector

_exporter_running = False
_exporter_port = 9464


def start_prometheus_exporter(port: int = 9464, host: str = "0.0.0.0") -> bool:
    """
    Start Prometheus HTTP metrics server on specified port.

    This starts an HTTP server that Prometheus can scrape for metrics.
    The /metrics endpoint will be available at http://<host>:<port>/metrics

    Args:
        port: Port to listen on (default: 9464)
        host: Host to bind to (default: 0.0.0.0)

    Returns:
        True if server started successfully, False otherwise
    """
    global _exporter_running, _exporter_port

    if not PROMETHEUS_CLIENT_AVAILABLE:
        print(
            "⚠️  prometheus-client not available. Install with: uv pip install prometheus-client"
        )
        return False

    if _exporter_running:
        print(f"✅ Prometheus metrics server already running on port {_exporter_port}")
        return True

    try:
        # Start HTTP server
        start_http_server(port, addr=host)
        _exporter_running = True
        _exporter_port = port

        print(f"✅ Prometheus metrics server started on http://{host}:{port}/metrics")
        return True

    except Exception as e:
        print(f"❌ Failed to start Prometheus server: {e}")
        return False


# Existing TTAPrometheusExporter class below...


class TTAPrometheusExporter:
    """Exports TTA.dev metrics in Prometheus format."""

    def __init__(self, port: int = 9464, host: str = "0.0.0.0") -> None:
        self.port = port
        self.host = host
        self.server_thread: threading.Thread | None = None
        self.running = False
        self.collector = get_enhanced_metrics_collector()

    def start(self) -> bool:
        """Start the Prometheus metrics HTTP server."""
        if not PROMETHEUS_CLIENT_AVAILABLE:
            print(
                "⚠️  prometheus-client not available. Install with: uv pip install prometheus-client"
            )
            return False

        if self.running:
            return True

        try:
            # Register our custom collector
            REGISTRY.register(self)

            # Start HTTP server
            start_http_server(self.port, addr=self.host)
            self.running = True

            print(
                f"✅ Prometheus metrics server started on http://{self.host}:{self.port}/metrics"
            )
            return True

        except Exception as e:
            print(f"❌ Failed to start Prometheus server: {e}")
            return False

    def stop(self) -> None:
        """Stop the metrics server."""
        if self.running:
            try:
                REGISTRY.unregister(self)
            except (KeyError, ValueError):
                pass  # Already unregistered
            self.running = False

    def collect(self) -> Iterator[Any]:
        """Collect metrics for Prometheus (called by prometheus_client)."""
        try:
            # Get all registered primitives from the collector
            primitive_names = getattr(self.collector, "primitives", {}).keys()

            for primitive_name in primitive_names:
                try:
                    metric_data = self.collector.get_all_metrics(primitive_name)

                    # Convert latency histograms
                    if "percentiles" in metric_data:
                        yield self._create_histogram_metric(primitive_name, metric_data)

                    # Convert counters
                    if "total_requests" in metric_data:
                        yield CounterMetricFamily(
                            f"tta_{primitive_name}_requests_total",
                            f"Total requests for {primitive_name}",
                            value=metric_data["total_requests"],
                        )

                    # Convert gauges
                    if "active_requests" in metric_data:
                        yield GaugeMetricFamily(
                            f"tta_{primitive_name}_active_requests",
                            f"Active requests for {primitive_name}",
                            value=metric_data["active_requests"],
                        )

                    # Convert rates
                    if "rps" in metric_data:
                        yield GaugeMetricFamily(
                            f"tta_{primitive_name}_requests_per_second",
                            f"Requests per second for {primitive_name}",
                            value=metric_data["rps"],
                        )

                    # Convert SLO metrics
                    if "slo_status" in metric_data:
                        slo = metric_data["slo_status"]
                        yield GaugeMetricFamily(
                            f"tta_{primitive_name}_availability",
                            f"Availability percentage for {primitive_name}",
                            value=slo.get("availability", 0),
                        )
                        yield GaugeMetricFamily(
                            f"tta_{primitive_name}_latency_compliance",
                            f"Latency compliance percentage for {primitive_name}",
                            value=slo.get("latency_compliance", 0),
                        )
                        yield GaugeMetricFamily(
                            f"tta_{primitive_name}_error_budget_remaining",
                            f"Error budget remaining percentage for {primitive_name}",
                            value=slo.get("error_budget_remaining", 0),
                        )

                except Exception as metric_error:
                    print(
                        f"⚠️  Error collecting metrics for {primitive_name}: {metric_error}"
                    )
                    continue

        except Exception as e:
            print(f"⚠️  Error collecting metrics: {e}")

    def _create_histogram_metric(self, metric_name: str, metric_data: dict) -> Any:
        """Create a Prometheus histogram from percentile data."""
        percentiles = metric_data.get("percentiles", {})

        # Convert percentiles to histogram buckets
        buckets = [
            ("0.5", percentiles.get("p50", 0) / 1000),  # Convert ms to seconds
            ("0.9", percentiles.get("p90", 0) / 1000),
            ("0.95", percentiles.get("p95", 0) / 1000),
            ("0.99", percentiles.get("p99", 0) / 1000),
        ]

        return HistogramMetricFamily(
            f"tta_{metric_name}_duration_seconds",
            f"Duration histogram for {metric_name}",
            buckets=buckets,
        )


# Global exporter instance
_exporter: TTAPrometheusExporter | None = None


def get_prometheus_exporter(
    port: int = 9464, host: str = "0.0.0.0"
) -> TTAPrometheusExporter:
    """Get or create the global Prometheus exporter instance."""
    global _exporter

    if _exporter is None:
        _exporter = TTAPrometheusExporter(port=port, host=host)

    return _exporter


def start_prometheus_server(port: int = 9464, host: str = "0.0.0.0") -> bool:
    """Start the Prometheus metrics server (convenience function)."""
    exporter = get_prometheus_exporter(port=port, host=host)
    return exporter.start()


def stop_prometheus_server() -> None:
    """Stop the Prometheus metrics server (convenience function)."""
    global _exporter
    if _exporter:
        _exporter.stop()
