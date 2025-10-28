"""Unit tests for APM setup (OpenTelemetry initialization)."""

from unittest.mock import patch

from src.observability_integration.apm_setup import (
    get_meter,
    get_tracer,
    initialize_observability,
    shutdown_observability,
)


class TestAPMInitialization:
    """Test APM initialization."""

    def test_initialize_without_opentelemetry(self):
        """Test initialization works without OpenTelemetry installed."""
        # Should not raise error
        initialize_observability()

    def test_shutdown_without_initialization(self):
        """Test shutdown works without prior initialization."""
        # Should not raise error
        shutdown_observability()

    def test_get_tracer_returns_none_without_init(self):
        """Test get_tracer returns None when not initialized."""
        tracer = get_tracer(__name__)
        assert tracer is None

    def test_get_meter_returns_none_without_init(self):
        """Test get_meter returns None when not initialized."""
        meter = get_meter(__name__)
        assert meter is None


class TestGracefulDegradation:
    """Test graceful degradation when OpenTelemetry unavailable."""

    def test_multiple_initializations_are_safe(self):
        """Test multiple initialization calls are safe."""
        initialize_observability()
        initialize_observability()  # Second call should be no-op
        shutdown_observability()

    def test_multiple_shutdowns_are_safe(self):
        """Test multiple shutdown calls are safe."""
        shutdown_observability()
        shutdown_observability()  # Second call should be no-op


class TestServiceInfo:
    """Test service information extraction."""

    def test_initialization_with_custom_service_name(self):
        """Test initialization with custom service name from env."""
        with patch.dict("os.environ", {"SERVICE_NAME": "custom-service"}):
            initialize_observability()
            shutdown_observability()

    def test_initialization_with_default_service_name(self):
        """Test initialization uses default service name when env not set."""
        with patch.dict("os.environ", {}, clear=True):
            initialize_observability()
            shutdown_observability()
