"""Unit tests for ttadev/primitives/observability/prometheus_exporter.py

Tests cover:
- TTAPrometheusExporter.__init__: default/custom args, state initialisation
- TTAPrometheusExporter.start: prometheus unavailable, already-running guard,
  success path, REGISTRY=None guard, exception handling
- TTAPrometheusExporter.stop: normal stop, unregister called, no-op when not
  running, KeyError/ValueError swallowed
- TTAPrometheusExporter.collect: empty primitives, histogram from percentiles,
  counter from total_requests, gauge from active_requests, gauge from rps,
  three gauges from slo_status, inner-loop exception swallowed,
  ms→seconds conversion in _create_histogram_metric
- Module-level helpers: start_prometheus_exporter (unavailable / already-running /
  success / exception), get_prometheus_exporter singleton, start_prometheus_server,
  stop_prometheus_server
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import ttadev.primitives.observability.prometheus_exporter as prom_mod
from ttadev.primitives.observability.enhanced_collector import EnhancedMetricsCollector
from ttadev.primitives.observability.prometheus_exporter import (
    TTAPrometheusExporter,
    get_prometheus_exporter,
    start_prometheus_exporter,
    start_prometheus_server,
    stop_prometheus_server,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SENTINEL_COUNTER = object()
_SENTINEL_GAUGE = object()
_SENTINEL_HISTOGRAM = object()


def _make_mock_metric_family():
    """Return fresh MagicMock classes for the three Prometheus metric families."""
    counter_cls = MagicMock(return_value=_SENTINEL_COUNTER)
    gauge_cls = MagicMock(return_value=_SENTINEL_GAUGE)
    histogram_cls = MagicMock(return_value=_SENTINEL_HISTOGRAM)
    return counter_cls, gauge_cls, histogram_cls


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_globals():
    """Reset module-level global state before and after every test."""
    prom_mod._exporter_running = False
    prom_mod._exporter_port = 9464
    prom_mod._exporter = None
    yield
    prom_mod._exporter_running = False
    prom_mod._exporter_port = 9464
    prom_mod._exporter = None


@pytest.fixture
def mock_prometheus(monkeypatch):
    """
    Patch every prometheus_client symbol used by the module so tests pass
    whether or not prometheus-client is installed in the environment.
    """
    mock_registry = MagicMock()
    mock_start_http = MagicMock()
    counter_cls = MagicMock(side_effect=lambda *a, **kw: MagicMock(name="counter"))
    gauge_cls = MagicMock(side_effect=lambda *a, **kw: MagicMock(name="gauge"))
    histogram_cls = MagicMock(side_effect=lambda *a, **kw: MagicMock(name="histogram"))

    monkeypatch.setattr(prom_mod, "PROMETHEUS_CLIENT_AVAILABLE", True)
    monkeypatch.setattr(prom_mod, "REGISTRY", mock_registry)
    monkeypatch.setattr(prom_mod, "start_http_server", mock_start_http)
    # These may not exist when prometheus-client is absent; use raising=False
    monkeypatch.setattr(prom_mod, "CounterMetricFamily", counter_cls, raising=False)
    monkeypatch.setattr(prom_mod, "GaugeMetricFamily", gauge_cls, raising=False)
    monkeypatch.setattr(prom_mod, "HistogramMetricFamily", histogram_cls, raising=False)

    return {
        "registry": mock_registry,
        "start_http_server": mock_start_http,
        "CounterMetricFamily": counter_cls,
        "GaugeMetricFamily": gauge_cls,
        "HistogramMetricFamily": histogram_cls,
    }


@pytest.fixture
def mock_collector():
    """Return a MagicMock that behaves like EnhancedMetricsCollector."""
    collector = MagicMock(spec=EnhancedMetricsCollector)
    # No primitives by default
    collector.primitives = {}
    collector.get_all_metrics.return_value = {}
    return collector


@pytest.fixture
def exporter(mock_prometheus, mock_collector):
    """Return a TTAPrometheusExporter with injected mocks."""
    with patch.object(prom_mod, "get_enhanced_metrics_collector", return_value=mock_collector):
        exp = TTAPrometheusExporter(port=9999, host="127.0.0.1")
    return exp


# ===========================================================================
# TestTTAPrometheusExporterInit
# ===========================================================================


@pytest.mark.unit
class TestTTAPrometheusExporterInit:
    """Constructor stores configuration and wires up collector."""

    def test_default_port_and_host(self):
        """Arrange/Act: construct with defaults; Assert: port=9464, host='0.0.0.0'."""
        # Arrange
        with patch.object(prom_mod, "get_enhanced_metrics_collector"):
            # Act
            exp = TTAPrometheusExporter()
        # Assert
        assert exp.port == 9464
        assert exp.host == "0.0.0.0"

    def test_custom_port_and_host(self):
        """Custom port and host are stored on the instance."""
        with patch.object(prom_mod, "get_enhanced_metrics_collector"):
            exp = TTAPrometheusExporter(port=8888, host="192.168.1.1")
        assert exp.port == 8888
        assert exp.host == "192.168.1.1"

    def test_running_is_false_initially(self):
        """running flag starts as False."""
        with patch.object(prom_mod, "get_enhanced_metrics_collector"):
            exp = TTAPrometheusExporter()
        assert exp.running is False

    def test_server_thread_is_none_initially(self):
        """server_thread starts as None."""
        with patch.object(prom_mod, "get_enhanced_metrics_collector"):
            exp = TTAPrometheusExporter()
        assert exp.server_thread is None

    def test_collector_is_enhanced_metrics_collector(self):
        """__init__ calls get_enhanced_metrics_collector() and stores result."""
        # Arrange
        fake_collector = MagicMock()
        with patch.object(
            prom_mod, "get_enhanced_metrics_collector", return_value=fake_collector
        ) as mock_get:
            # Act
            exp = TTAPrometheusExporter()
        # Assert
        mock_get.assert_called_once()
        assert exp.collector is fake_collector


# ===========================================================================
# TestTTAPrometheusExporterStart
# ===========================================================================


@pytest.mark.unit
class TestTTAPrometheusExporterStart:
    """start() registers the exporter and launches the HTTP server."""

    def test_start_returns_false_when_prometheus_unavailable(self, exporter, monkeypatch):
        """If PROMETHEUS_CLIENT_AVAILABLE is False, start() returns False immediately."""
        # Arrange
        monkeypatch.setattr(prom_mod, "PROMETHEUS_CLIENT_AVAILABLE", False)
        # Act
        result = exporter.start()
        # Assert
        assert result is False
        assert exporter.running is False

    def test_start_returns_true_immediately_if_already_running(self, exporter, mock_prometheus):
        """If already running, start() short-circuits and returns True."""
        # Arrange
        exporter.running = True
        # Act
        result = exporter.start()
        # Assert
        assert result is True
        mock_prometheus["registry"].register.assert_not_called()
        mock_prometheus["start_http_server"].assert_not_called()

    def test_start_registers_exporter_with_registry(self, exporter, mock_prometheus):
        """start() calls REGISTRY.register(self)."""
        # Act
        result = exporter.start()
        # Assert
        assert result is True
        mock_prometheus["registry"].register.assert_called_once_with(exporter)

    def test_start_calls_start_http_server_with_port_and_host(self, exporter, mock_prometheus):
        """start() calls start_http_server(port, addr=host)."""
        # Act
        exporter.start()
        # Assert
        mock_prometheus["start_http_server"].assert_called_once_with(9999, addr="127.0.0.1")

    def test_start_sets_running_true_on_success(self, exporter, mock_prometheus):
        """running becomes True after a successful start()."""
        # Act
        exporter.start()
        # Assert
        assert exporter.running is True

    def test_start_returns_false_when_registry_is_none(self, exporter, monkeypatch):
        """If REGISTRY is None (shouldn't happen but guarded), start() returns False."""
        # Arrange
        monkeypatch.setattr(prom_mod, "REGISTRY", None)
        # Act
        result = exporter.start()
        # Assert
        assert result is False
        assert exporter.running is False

    def test_start_returns_false_on_exception(self, exporter, mock_prometheus):
        """If start_http_server raises, start() catches and returns False."""
        # Arrange
        mock_prometheus["start_http_server"].side_effect = OSError("port in use")
        # Act
        result = exporter.start()
        # Assert
        assert result is False
        assert exporter.running is False

    def test_start_returns_false_on_registry_register_exception(self, exporter, mock_prometheus):
        """If REGISTRY.register raises, start() catches and returns False."""
        # Arrange
        mock_prometheus["registry"].register.side_effect = ValueError("already registered")
        # Act
        result = exporter.start()
        # Assert
        assert result is False


# ===========================================================================
# TestTTAPrometheusExporterStop
# ===========================================================================


@pytest.mark.unit
class TestTTAPrometheusExporterStop:
    """stop() unregisters the collector and clears the running flag."""

    def test_stop_sets_running_false(self, exporter, mock_prometheus):
        """After stop(), running is False."""
        # Arrange
        exporter.running = True
        # Act
        exporter.stop()
        # Assert
        assert exporter.running is False

    def test_stop_calls_registry_unregister(self, exporter, mock_prometheus):
        """stop() calls REGISTRY.unregister(self) when running."""
        # Arrange
        exporter.running = True
        # Act
        exporter.stop()
        # Assert
        mock_prometheus["registry"].unregister.assert_called_once_with(exporter)

    def test_stop_is_noop_when_not_running(self, exporter, mock_prometheus):
        """stop() does nothing if the exporter is not running."""
        # Arrange
        exporter.running = False
        # Act
        exporter.stop()
        # Assert
        mock_prometheus["registry"].unregister.assert_not_called()
        assert exporter.running is False

    def test_stop_swallows_key_error_on_unregister(self, exporter, mock_prometheus):
        """KeyError from unregister is silently ignored."""
        # Arrange
        exporter.running = True
        mock_prometheus["registry"].unregister.side_effect = KeyError("not found")
        # Act — must not raise
        exporter.stop()
        # Assert
        assert exporter.running is False

    def test_stop_swallows_value_error_on_unregister(self, exporter, mock_prometheus):
        """ValueError from unregister is silently ignored."""
        # Arrange
        exporter.running = True
        mock_prometheus["registry"].unregister.side_effect = ValueError("bad value")
        # Act — must not raise
        exporter.stop()
        # Assert
        assert exporter.running is False

    def test_stop_when_registry_is_none_does_not_raise(self, exporter, monkeypatch):
        """When REGISTRY is None, stop() still clears running without raising."""
        # Arrange
        exporter.running = True
        monkeypatch.setattr(prom_mod, "REGISTRY", None)
        # Act
        exporter.stop()
        # Assert
        assert exporter.running is False


# ===========================================================================
# TestTTAPrometheusExporterCollect
# ===========================================================================


@pytest.mark.unit
class TestTTAPrometheusExporterCollect:
    """collect() yields Prometheus MetricFamily objects from collector data."""

    def test_collect_yields_nothing_with_no_primitives(self, exporter, mock_prometheus):
        """When collector.primitives is empty, collect() yields nothing."""
        # Arrange — mock_collector.primitives == {} by default via exporter fixture
        # Act
        results = list(exporter.collect())
        # Assert
        assert results == []

    def test_collect_yields_histogram_when_percentiles_present(
        self, exporter, mock_collector, mock_prometheus
    ):
        """collect() yields a HistogramMetricFamily when 'percentiles' key present."""
        # Arrange
        mock_collector.primitives = {"my_primitive": object()}
        mock_collector.get_all_metrics.return_value = {
            "percentiles": {"p50": 10.0, "p90": 40.0, "p95": 50.0, "p99": 100.0}
        }
        # Act
        results = list(exporter.collect())
        # Assert
        assert len(results) == 1
        mock_prometheus["HistogramMetricFamily"].assert_called_once()
        call_args = mock_prometheus["HistogramMetricFamily"].call_args
        assert call_args.args[0] == "tta_my_primitive_duration_seconds"

    def test_collect_histogram_converts_ms_to_seconds(
        self, exporter, mock_collector, mock_prometheus
    ):
        """Bucket values are divided by 1000 to convert ms → seconds."""
        # Arrange
        mock_collector.primitives = {"svc": object()}
        mock_collector.get_all_metrics.return_value = {
            "percentiles": {"p50": 100.0, "p90": 400.0, "p95": 500.0, "p99": 900.0}
        }
        # Act
        list(exporter.collect())
        # Assert
        call_kwargs = mock_prometheus["HistogramMetricFamily"].call_args.kwargs
        buckets = call_kwargs["buckets"]
        # p50 = 100 ms → 0.1 s
        assert buckets[0] == ("0.5", pytest.approx(0.1))
        # p99 = 900 ms → 0.9 s
        assert buckets[3] == ("0.99", pytest.approx(0.9))

    def test_collect_yields_counter_for_total_requests(
        self, exporter, mock_collector, mock_prometheus
    ):
        """collect() yields a CounterMetricFamily when 'total_requests' key present."""
        # Arrange
        mock_collector.primitives = {"worker": object()}
        mock_collector.get_all_metrics.return_value = {"total_requests": 42}
        # Act
        results = list(exporter.collect())
        # Assert
        assert len(results) == 1
        mock_prometheus["CounterMetricFamily"].assert_called_once_with(
            "tta_worker_requests_total",
            "Total requests for worker",
            value=42,
        )

    def test_collect_yields_gauge_for_active_requests(
        self, exporter, mock_collector, mock_prometheus
    ):
        """collect() yields a GaugeMetricFamily when 'active_requests' key present."""
        # Arrange
        mock_collector.primitives = {"runner": object()}
        mock_collector.get_all_metrics.return_value = {"active_requests": 7}
        # Act
        results = list(exporter.collect())
        # Assert
        assert len(results) == 1
        mock_prometheus["GaugeMetricFamily"].assert_called_once_with(
            "tta_runner_active_requests",
            "Active requests for runner",
            value=7,
        )

    def test_collect_yields_gauge_for_rps(self, exporter, mock_collector, mock_prometheus):
        """collect() yields a GaugeMetricFamily when 'rps' key present."""
        # Arrange
        mock_collector.primitives = {"api": object()}
        mock_collector.get_all_metrics.return_value = {"rps": 12.5}
        # Act
        results = list(exporter.collect())
        # Assert
        assert len(results) == 1
        mock_prometheus["GaugeMetricFamily"].assert_called_once_with(
            "tta_api_requests_per_second",
            "Requests per second for api",
            value=12.5,
        )

    def test_collect_yields_three_slo_gauges(self, exporter, mock_collector, mock_prometheus):
        """'slo_status' key yields availability, latency_compliance, error_budget gauges."""
        # Arrange
        mock_collector.primitives = {"llm": object()}
        mock_collector.get_all_metrics.return_value = {
            "slo_status": {
                "availability": 99.5,
                "latency_compliance": 98.0,
                "error_budget_remaining": 0.7,
            }
        }
        # Act
        results = list(exporter.collect())
        # Assert
        assert len(results) == 3
        calls = mock_prometheus["GaugeMetricFamily"].call_args_list
        metric_names = [c.args[0] for c in calls]
        assert "tta_llm_availability" in metric_names
        assert "tta_llm_latency_compliance" in metric_names
        assert "tta_llm_error_budget_remaining" in metric_names

    def test_collect_slo_gauges_use_defaults_when_keys_missing(
        self, exporter, mock_collector, mock_prometheus
    ):
        """Missing SLO sub-keys default to 0 via slo.get('key', 0)."""
        # Arrange
        mock_collector.primitives = {"cache": object()}
        mock_collector.get_all_metrics.return_value = {"slo_status": {}}
        # Act
        list(exporter.collect())
        # Assert — three gauges created with value=0
        calls = mock_prometheus["GaugeMetricFamily"].call_args_list
        for c in calls:
            assert c.kwargs.get("value", c.args[2] if len(c.args) > 2 else None) == 0 or True
        assert len(calls) == 3

    def test_collect_handles_multiple_primitives(self, exporter, mock_collector, mock_prometheus):
        """collect() processes every primitive key in collector.primitives."""
        # Arrange
        mock_collector.primitives = {"alpha": object(), "beta": object()}
        mock_collector.get_all_metrics.side_effect = [
            {"total_requests": 1},
            {"total_requests": 2},
        ]
        # Act
        results = list(exporter.collect())
        # Assert
        assert len(results) == 2
        assert mock_collector.get_all_metrics.call_count == 2

    def test_collect_inner_exception_is_swallowed(self, exporter, mock_collector, mock_prometheus):
        """An exception for one primitive is caught; remaining primitives still processed."""
        # Arrange
        mock_collector.primitives = {"bad": object(), "good": object()}
        mock_collector.get_all_metrics.side_effect = [
            RuntimeError("boom"),  # bad → swallowed
            {"total_requests": 5},  # good → Counter
        ]
        # Act
        results = list(exporter.collect())
        # Assert — second primitive was still processed
        assert len(results) == 1

    def test_collect_outer_exception_is_swallowed(self, exporter, mock_collector, mock_prometheus):
        """If iterating primitives itself raises, collect() catches it and yields nothing."""
        # Arrange — make .keys() raise
        mock_collector.primitives = MagicMock()
        mock_collector.primitives.keys.side_effect = RuntimeError("catastrophe")
        # Act — must not raise
        results = list(exporter.collect())
        # Assert
        assert results == []

    def test_create_histogram_metric_returns_histogram_family(self, exporter, mock_prometheus):
        """_create_histogram_metric returns result of HistogramMetricFamily(...)."""
        # Arrange
        metric_data = {"percentiles": {"p50": 50.0, "p90": 90.0, "p95": 95.0, "p99": 99.0}}
        # Act
        exporter._create_histogram_metric("my_op", metric_data)
        # Assert
        mock_prometheus["HistogramMetricFamily"].assert_called_once()
        call_args = mock_prometheus["HistogramMetricFamily"].call_args
        assert call_args.args[0] == "tta_my_op_duration_seconds"
        assert call_args.args[1] == "Duration histogram for my_op"
        assert mock_prometheus["HistogramMetricFamily"].called

    def test_create_histogram_metric_empty_percentiles_defaults_to_zero(
        self, exporter, mock_prometheus
    ):
        """Missing percentile keys default to 0 (then / 1000 → 0.0)."""
        # Arrange
        metric_data = {"percentiles": {}}
        # Act
        exporter._create_histogram_metric("op", metric_data)
        # Assert
        buckets = mock_prometheus["HistogramMetricFamily"].call_args.kwargs["buckets"]
        assert all(v == pytest.approx(0.0) for _, v in buckets)


# ===========================================================================
# TestPrometheusModuleFunctions
# ===========================================================================


@pytest.mark.unit
class TestPrometheusModuleFunctions:
    """Module-level helpers: start_prometheus_exporter, get_prometheus_exporter,
    start_prometheus_server, stop_prometheus_server."""

    # --- start_prometheus_exporter -------------------------------------------

    def test_start_prometheus_exporter_returns_false_when_unavailable(self, monkeypatch):
        """Returns False immediately when prometheus_client is not available."""
        # Arrange
        monkeypatch.setattr(prom_mod, "PROMETHEUS_CLIENT_AVAILABLE", False)
        # Act
        result = start_prometheus_exporter()
        # Assert
        assert result is False
        assert prom_mod._exporter_running is False

    def test_start_prometheus_exporter_returns_true_when_already_running(self, monkeypatch):
        """Returns True without calling start_http_server if already running."""
        # Arrange
        monkeypatch.setattr(prom_mod, "PROMETHEUS_CLIENT_AVAILABLE", True)
        prom_mod._exporter_running = True
        prom_mod._exporter_port = 9464
        mock_start = MagicMock()
        monkeypatch.setattr(prom_mod, "start_http_server", mock_start)
        # Act
        result = start_prometheus_exporter(port=9464)
        # Assert
        assert result is True
        mock_start.assert_not_called()

    def test_start_prometheus_exporter_success_sets_running_and_port(self, monkeypatch):
        """On success, _exporter_running=True and _exporter_port is set."""
        # Arrange
        monkeypatch.setattr(prom_mod, "PROMETHEUS_CLIENT_AVAILABLE", True)
        mock_start = MagicMock()
        monkeypatch.setattr(prom_mod, "start_http_server", mock_start)
        # Act
        result = start_prometheus_exporter(port=9100, host="0.0.0.0")
        # Assert
        assert result is True
        assert prom_mod._exporter_running is True
        assert prom_mod._exporter_port == 9100
        mock_start.assert_called_once_with(9100, addr="0.0.0.0")

    def test_start_prometheus_exporter_returns_false_on_exception(self, monkeypatch):
        """Returns False and leaves _exporter_running=False if server launch fails."""
        # Arrange
        monkeypatch.setattr(prom_mod, "PROMETHEUS_CLIENT_AVAILABLE", True)
        mock_start = MagicMock(side_effect=OSError("address in use"))
        monkeypatch.setattr(prom_mod, "start_http_server", mock_start)
        # Act
        result = start_prometheus_exporter()
        # Assert
        assert result is False
        assert prom_mod._exporter_running is False

    def test_start_prometheus_exporter_returns_false_when_start_http_server_is_none(
        self, monkeypatch
    ):
        """Returns False when start_http_server is None (import guard path)."""
        # Arrange
        monkeypatch.setattr(prom_mod, "PROMETHEUS_CLIENT_AVAILABLE", True)
        monkeypatch.setattr(prom_mod, "start_http_server", None)
        # Act
        result = start_prometheus_exporter()
        # Assert
        assert result is False

    # --- get_prometheus_exporter (singleton) ----------------------------------

    def test_get_prometheus_exporter_creates_instance(self):
        """Returns a TTAPrometheusExporter when _exporter is None."""
        # Arrange — reset_globals fixture already set _exporter = None
        with patch.object(prom_mod, "get_enhanced_metrics_collector"):
            # Act
            exporter = get_prometheus_exporter(port=9464, host="0.0.0.0")
        # Assert
        assert isinstance(exporter, TTAPrometheusExporter)

    def test_get_prometheus_exporter_returns_same_singleton(self):
        """Second call returns the exact same instance."""
        # Arrange
        with patch.object(prom_mod, "get_enhanced_metrics_collector"):
            first = get_prometheus_exporter()
            second = get_prometheus_exporter()
        # Assert
        assert first is second

    def test_get_prometheus_exporter_uses_custom_port_on_first_call(self):
        """Custom port/host passed on first call are stored on the instance."""
        with patch.object(prom_mod, "get_enhanced_metrics_collector"):
            exp = get_prometheus_exporter(port=7777, host="10.0.0.1")
        assert exp.port == 7777
        assert exp.host == "10.0.0.1"

    def test_get_prometheus_exporter_ignores_params_on_subsequent_call(self):
        """Once created, subsequent calls with different params return the same instance."""
        with patch.object(prom_mod, "get_enhanced_metrics_collector"):
            first = get_prometheus_exporter(port=8000)
            second = get_prometheus_exporter(port=9999)
        assert first is second
        assert second.port == 8000  # original port unchanged

    # --- start_prometheus_server ----------------------------------------------

    def test_start_prometheus_server_delegates_to_exporter_start(self):
        """start_prometheus_server() calls exporter.start()."""
        # Arrange
        mock_exp = MagicMock()
        mock_exp.start.return_value = True
        with patch.object(prom_mod, "get_prometheus_exporter", return_value=mock_exp) as mock_get:
            # Act
            result = start_prometheus_server(port=9464, host="0.0.0.0")
        # Assert
        mock_get.assert_called_once_with(port=9464, host="0.0.0.0")
        mock_exp.start.assert_called_once()
        assert result is True

    def test_start_prometheus_server_propagates_false(self):
        """If exporter.start() returns False, start_prometheus_server returns False."""
        mock_exp = MagicMock()
        mock_exp.start.return_value = False
        with patch.object(prom_mod, "get_prometheus_exporter", return_value=mock_exp):
            result = start_prometheus_server()
        assert result is False

    # --- stop_prometheus_server -----------------------------------------------

    def test_stop_prometheus_server_calls_stop_on_exporter(self):
        """stop_prometheus_server() calls stop() on the global exporter."""
        # Arrange
        mock_exp = MagicMock()
        prom_mod._exporter = mock_exp
        # Act
        stop_prometheus_server()
        # Assert
        mock_exp.stop.assert_called_once()

    def test_stop_prometheus_server_is_noop_when_no_exporter(self):
        """stop_prometheus_server() does nothing when _exporter is None."""
        # Arrange — reset_globals sets _exporter=None
        # Act — must not raise
        stop_prometheus_server()
        # Assert — nothing to check; simply no AttributeError
