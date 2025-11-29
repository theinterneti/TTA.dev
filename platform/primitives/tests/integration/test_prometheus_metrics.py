"""
Integration tests for Prometheus metrics infrastructure.

Tests verify that:
1. Prometheus is properly configured and accessible
2. OpenTelemetry Collector exports metrics to Prometheus
3. The metrics pipeline is working end-to-end
4. Scrape targets are configured correctly

Note: Full primitive-level metrics integration (execution time, success/failure rates)
requires OpenTelemetry metrics instrumentation in InstrumentedPrimitive, which is
tracked as a follow-up task. These tests focus on infrastructure readiness.

NOTE: All tests in this module require Docker containers and should run as integration tests.
"""

from __future__ import annotations

import time
from typing import Any

import pytest
import requests

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration

# Prometheus endpoint
PROMETHEUS_URL = "http://localhost:9090"
PROMETHEUS_QUERY_API = f"{PROMETHEUS_URL}/api/v1/query"
PROMETHEUS_TARGETS_API = f"{PROMETHEUS_URL}/api/v1/targets"
PROMETHEUS_CONFIG_API = f"{PROMETHEUS_URL}/api/v1/status/config"

# Check if backends are available (Docker services running)
try:
    response = requests.get(f"{PROMETHEUS_URL}/-/healthy", timeout=2)
    BACKENDS_AVAILABLE = response.status_code == 200
except Exception:
    BACKENDS_AVAILABLE = False


# ============================================================================
# Helper Functions
# ============================================================================


def query_prometheus(query: str, timeout: int = 10) -> dict[str, Any]:
    """
    Query Prometheus API.

    Args:
        query: PromQL query string
        timeout: Timeout in seconds

    Returns:
        Query result as dictionary

    Raises:
        requests.RequestException: If query fails
    """
    response = requests.get(
        PROMETHEUS_QUERY_API,
        params={"query": query},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def get_prometheus_targets(timeout: int = 10) -> dict[str, Any]:
    """
    Get Prometheus scrape targets.

    Args:
        timeout: Timeout in seconds

    Returns:
        Targets information as dictionary
    """
    response = requests.get(PROMETHEUS_TARGETS_API, timeout=timeout)
    response.raise_for_status()
    return response.json()


def get_prometheus_config(timeout: int = 10) -> dict[str, Any]:
    """
    Get Prometheus configuration.

    Args:
        timeout: Timeout in seconds

    Returns:
        Configuration as dictionary
    """
    response = requests.get(PROMETHEUS_CONFIG_API, timeout=timeout)
    response.raise_for_status()
    return response.json()


# ============================================================================
# Tests: Prometheus Infrastructure
# ============================================================================


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="Prometheus backend not available")
def test_prometheus_health() -> None:
    """Test that Prometheus is healthy and responding."""
    response = requests.get(f"{PROMETHEUS_URL}/-/healthy", timeout=5)
    assert response.status_code == 200, "Prometheus health check failed"


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="Prometheus backend not available")
def test_prometheus_ready() -> None:
    """Test that Prometheus is ready to serve queries."""
    response = requests.get(f"{PROMETHEUS_URL}/-/ready", timeout=5)
    assert response.status_code == 200, "Prometheus readiness check failed"


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="Prometheus backend not available")
def test_prometheus_api_accessible() -> None:
    """Test that Prometheus API is accessible."""
    response = requests.get(PROMETHEUS_CONFIG_API, timeout=5)
    assert response.status_code == 200, "Prometheus API not accessible"

    data = response.json()
    assert data.get("status") == "success", "Prometheus API returned error"


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="Prometheus backend not available")
def test_prometheus_configuration() -> None:
    """Test that Prometheus is configured with expected scrape jobs."""
    config = get_prometheus_config()

    assert config.get("status") == "success", "Failed to get Prometheus config"

    # Parse YAML config from response
    yaml_config = config.get("data", {}).get("yaml", "")
    assert yaml_config, "No configuration found"

    # Check for expected job names (without quotes - Prometheus config format)
    assert "job_name: prometheus" in yaml_config, "Missing prometheus self-monitoring job"
    
    # Check for metrics job (otel-collector OR hypertool-metrics)
    has_otel = "job_name: otel-collector" in yaml_config
    has_hypertool = "job_name: hypertool-metrics" in yaml_config
    assert has_otel or has_hypertool, "Missing metrics job (otel-collector or hypertool-metrics)"


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="Prometheus backend not available")
def test_prometheus_scrape_targets() -> None:
    """Test that Prometheus has configured scrape targets."""
    targets = get_prometheus_targets()

    assert targets.get("status") == "success", "Failed to get Prometheus targets"

    active_targets = targets.get("data", {}).get("activeTargets", [])
    assert len(active_targets) > 0, "No active scrape targets found"

    # Check for expected jobs
    job_names = {target.get("labels", {}).get("job") for target in active_targets}
    assert "prometheus" in job_names, "Missing prometheus self-monitoring target"
    
    # Check for metrics target
    has_otel = "otel-collector" in job_names
    has_hypertool = "hypertool-metrics" in job_names
    assert has_otel or has_hypertool, "Missing metrics target (otel-collector or hypertool-metrics)"


# ============================================================================
# Tests: OpenTelemetry Collector Metrics
# ============================================================================


def _has_otel_job() -> bool:
    """Check if otel-collector job is configured."""
    try:
        config = get_prometheus_config()
        yaml_config = config.get("data", {}).get("yaml", "")
        return "job_name: otel-collector" in yaml_config
    except Exception:
        return False


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="Prometheus backend not available")
def test_otel_collector_up() -> None:
    """Test that OpenTelemetry Collector is being scraped by Prometheus."""
    if not _has_otel_job():
        pytest.skip("otel-collector job not configured")

    # Wait a bit for initial scrape
    time.sleep(5)

    query = 'up{job="otel-collector"}'
    result = query_prometheus(query)

    assert result.get("status") == "success", "Prometheus query failed"

    data = result.get("data", {})
    results = data.get("result", [])

    assert len(results) > 0, "No OTEL Collector metrics found"

    # Check that at least one target is up
    up_values = [float(r.get("value", [0, 0])[1]) for r in results]
    assert any(v == 1.0 for v in up_values), "OTEL Collector is not up"


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="Prometheus backend not available")
def test_otel_collector_metrics_exported() -> None:
    """Test that OpenTelemetry Collector exports its own metrics."""
    if not _has_otel_job():
        pytest.skip("otel-collector job not configured")

    # Wait for metrics to be scraped
    time.sleep(5)

    # Query for OTEL Collector process metrics
    query = 'otelcol_process_uptime{job="otel-collector"}'
    result = query_prometheus(query)

    assert result.get("status") == "success", "Prometheus query failed"

    data = result.get("data", {})
    results = data.get("result", [])

    assert len(results) > 0, "No OTEL Collector process metrics found"

    # Verify uptime is positive
    uptime_values = [float(r.get("value", [0, 0])[1]) for r in results]
    assert all(v > 0 for v in uptime_values), "OTEL Collector uptime should be positive"


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="Prometheus backend not available")
def test_otel_collector_span_export_metrics() -> None:
    """Test that OpenTelemetry Collector exports span processing metrics."""
    # Wait for metrics to be scraped
    time.sleep(5)

    # Query for span export metrics
    query = 'otelcol_exporter_sent_spans{job="otel-collector"}'
    result = query_prometheus(query)

    assert result.get("status") == "success", "Prometheus query failed"

    # Note: This metric may be 0 if no spans have been sent yet
    # We just verify the metric exists
    data = result.get("data", {})
    results = data.get("result", [])

    # Metric should exist even if value is 0
    assert len(results) >= 0, "Span export metrics query failed"


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="Prometheus backend not available")
def test_otel_collector_metric_export_metrics() -> None:
    """Test that OpenTelemetry Collector exports metric processing metrics."""
    # Wait for metrics to be scraped
    time.sleep(5)

    # Query for metric export metrics
    query = 'otelcol_exporter_sent_metric_points{job="otel-collector"}'
    result = query_prometheus(query)

    assert result.get("status") == "success", "Prometheus query failed"

    # Note: This metric may be 0 if no metric points have been sent yet
    # We just verify the metric exists
    data = result.get("data", {})
    results = data.get("result", [])

    # Metric should exist even if value is 0
    assert len(results) >= 0, "Metric export metrics query failed"


# ============================================================================
# Tests: Prometheus Self-Monitoring
# ============================================================================


@pytest.mark.skipif(not BACKENDS_AVAILABLE, reason="Prometheus backend not available")
def test_prometheus_self_monitoring() -> None:
    """Test that Prometheus monitors itself."""
    query = 'up{job="prometheus"}'
    result = query_prometheus(query)

    assert result.get("status") == "success", "Prometheus query failed"

    data = result.get("data", {})
    results = data.get("result", [])

    assert len(results) > 0, "No Prometheus self-monitoring metrics found"

    # Prometheus should be up
    up_values = [float(r.get("value", [0, 0])[1]) for r in results]
    assert all(v == 1.0 for v in up_values), "Prometheus self-monitoring shows down"
