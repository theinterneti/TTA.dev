"""Tests for observability configuration."""

from __future__ import annotations

import pytest

from tta_dev_primitives.observability.config import (
    MetricsConfig,
    ObservabilityConfig,
    SamplingConfig,
    StorageConfig,
    TracingConfig,
    get_observability_config,
    set_observability_config,
)


class TestMetricsConfig:
    """Tests for MetricsConfig."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = MetricsConfig()

        assert config.enabled is True
        assert config.max_label_values == 100
        assert config.hash_high_cardinality is True
        assert config.export_interval_seconds == 60.0
        assert config.batch_size == 100

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = MetricsConfig(
            enabled=False,
            max_label_values=200,
            hash_high_cardinality=False,
            export_interval_seconds=30.0,
        )

        assert config.enabled is False
        assert config.max_label_values == 200
        assert config.hash_high_cardinality is False
        assert config.export_interval_seconds == 30.0


class TestTracingConfig:
    """Tests for TracingConfig."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = TracingConfig()

        assert config.enabled is True
        assert isinstance(config.sampling, SamplingConfig)
        assert config.export_interval_seconds == 30.0
        assert config.batch_size == 512

    def test_custom_sampling(self) -> None:
        """Test custom sampling configuration."""
        sampling = SamplingConfig(
            default_rate=0.05,
            always_sample_errors=True,
        )
        config = TracingConfig(sampling=sampling)

        assert config.sampling.default_rate == 0.05
        assert config.sampling.always_sample_errors is True


class TestStorageConfig:
    """Tests for StorageConfig."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = StorageConfig()

        assert config.trace_ttl_days == 7
        assert config.metric_ttl_days == 30
        assert config.compression_enabled is True
        assert config.compression_level == 6

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = StorageConfig(
            trace_ttl_days=14,
            compression_enabled=False,
        )

        assert config.trace_ttl_days == 14
        assert config.compression_enabled is False


class TestObservabilityConfig:
    """Tests for ObservabilityConfig."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = ObservabilityConfig()

        assert config.environment == "development"
        assert config.service_name == "tta"
        assert config.service_version == "0.1.0"
        assert isinstance(config.tracing, TracingConfig)
        assert isinstance(config.metrics, MetricsConfig)
        assert isinstance(config.storage, StorageConfig)

    def test_custom_config(self) -> None:
        """Test custom configuration."""
        config = ObservabilityConfig(
            environment="production",
            service_name="tta-api",
            service_version="2.0.0",
        )

        assert config.environment == "production"
        assert config.service_name == "tta-api"
        assert config.service_version == "2.0.0"

    def test_from_environment_development(self) -> None:
        """Test development environment config."""
        config = ObservabilityConfig.from_environment("development")

        assert config.environment == "development"
        # Development should sample everything
        assert config.tracing.sampling.default_rate == 1.0
        assert config.tracing.sampling.adaptive_enabled is False
        # Higher cardinality limit for debugging
        assert config.metrics.max_label_values == 1000
        # Shorter retention
        assert config.storage.trace_ttl_days == 1

    def test_from_environment_staging(self) -> None:
        """Test staging environment config."""
        config = ObservabilityConfig.from_environment("staging")

        assert config.environment == "staging"
        # Moderate sampling
        assert config.tracing.sampling.default_rate == 0.2
        assert config.tracing.sampling.adaptive_enabled is True
        # Moderate cardinality
        assert config.metrics.max_label_values == 200
        # Moderate retention
        assert config.storage.trace_ttl_days == 3

    def test_from_environment_production(self) -> None:
        """Test production environment config."""
        config = ObservabilityConfig.from_environment("production")

        assert config.environment == "production"
        # Low sampling for cost efficiency
        assert config.tracing.sampling.default_rate == 0.05
        assert config.tracing.sampling.adaptive_enabled is True
        # Controlled cardinality
        assert config.metrics.max_label_values == 100
        assert config.metrics.hash_high_cardinality is True
        # Standard retention
        assert config.storage.trace_ttl_days == 7
        # Compression enabled
        assert config.storage.compression_enabled is True

    def test_from_environment_defaults_to_development(self) -> None:
        """Test that unknown environment defaults to development."""
        config = ObservabilityConfig.from_environment("unknown")

        assert config.environment == "unknown"
        # Should use development settings
        assert config.tracing.sampling.default_rate == 1.0

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        config = ObservabilityConfig(
            environment="test",
            service_name="test-service",
        )

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["environment"] == "test"
        assert config_dict["service_name"] == "test-service"
        assert "tracing" in config_dict
        assert "metrics" in config_dict
        assert "storage" in config_dict

        # Check nested structure
        assert "sampling" in config_dict["tracing"]
        assert "default_rate" in config_dict["tracing"]["sampling"]


class TestGlobalConfig:
    """Tests for global configuration management."""

    def test_get_default_config(self) -> None:
        """Test getting default global config."""
        config = get_observability_config()

        assert isinstance(config, ObservabilityConfig)
        assert config.environment == "development"

    def test_set_and_get_config(self) -> None:
        """Test setting and getting global config."""
        custom_config = ObservabilityConfig(
            environment="testing",
            service_name="test-service",
        )

        set_observability_config(custom_config)

        retrieved_config = get_observability_config()

        assert retrieved_config.environment == "testing"
        assert retrieved_config.service_name == "test-service"

    def test_set_config_overwrites(self) -> None:
        """Test that set_config overwrites previous config."""
        config1 = ObservabilityConfig(environment="config1")
        set_observability_config(config1)

        config2 = ObservabilityConfig(environment="config2")
        set_observability_config(config2)

        retrieved = get_observability_config()
        assert retrieved.environment == "config2"
