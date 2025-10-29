"""Configuration management for observability."""

from __future__ import annotations

import logging
import os
from typing import Any

from pydantic import BaseModel, Field

from .sampling import SamplingConfig

logger = logging.getLogger(__name__)


class MetricsConfig(BaseModel):
    """
    Configuration for metrics collection.

    Controls metric collection behavior and cardinality limits.

    Example:
        ```python
        config = MetricsConfig(
            enabled=True,
            max_label_values=100,
            hash_high_cardinality=True,
        )
        ```
    """

    enabled: bool = Field(default=True, description="Enable metrics collection")
    max_label_values: int = Field(
        default=100, ge=1, description="Maximum unique label values per label key"
    )
    hash_high_cardinality: bool = Field(
        default=True, description="Hash high-cardinality label values"
    )
    export_interval_seconds: float = Field(
        default=60.0, ge=1.0, description="Interval between metric exports"
    )
    batch_size: int = Field(default=100, ge=1, description="Number of metrics to batch")


class TracingConfig(BaseModel):
    """
    Configuration for distributed tracing.

    Controls trace collection, sampling, and export behavior.

    Example:
        ```python
        config = TracingConfig(
            enabled=True,
            sampling=SamplingConfig(default_rate=0.1),
            export_interval_seconds=30.0,
        )
        ```
    """

    enabled: bool = Field(default=True, description="Enable distributed tracing")
    sampling: SamplingConfig = Field(
        default_factory=SamplingConfig, description="Sampling configuration"
    )
    export_interval_seconds: float = Field(
        default=30.0, ge=1.0, description="Interval between trace exports"
    )
    batch_size: int = Field(default=512, ge=1, description="Number of spans to batch")
    max_queue_size: int = Field(
        default=2048, ge=1, description="Maximum span queue size before dropping"
    )


class StorageConfig(BaseModel):
    """
    Configuration for trace and metric storage.

    Controls retention, compression, and storage optimization.

    Example:
        ```python
        config = StorageConfig(
            trace_ttl_days=7,
            compression_enabled=True,
        )
        ```
    """

    trace_ttl_days: int = Field(default=7, ge=1, description="Trace retention in days")
    metric_ttl_days: int = Field(default=30, ge=1, description="Metric retention in days")
    compression_enabled: bool = Field(default=True, description="Enable data compression")
    compression_level: int = Field(
        default=6, ge=1, le=9, description="Compression level (1=fast, 9=best)"
    )


class ObservabilityConfig(BaseModel):
    """
    Complete observability configuration.

    This is the main configuration object that combines all observability
    settings for tracing, metrics, and storage.

    Example:
        ```python
        # Development configuration
        config = ObservabilityConfig.from_environment("development")

        # Production configuration
        config = ObservabilityConfig.from_environment("production")

        # Custom configuration
        config = ObservabilityConfig(
            environment="production",
            service_name="tta-api",
            service_version="1.0.0",
            tracing=TracingConfig(
                sampling=SamplingConfig(
                    default_rate=0.05,
                    always_sample_errors=True,
                    adaptive_enabled=True,
                )
            ),
            metrics=MetricsConfig(max_label_values=100),
            storage=StorageConfig(trace_ttl_days=7),
        )
        ```
    """

    environment: str = Field(
        default="development",
        description="Environment name (development, staging, production)",
    )
    service_name: str = Field(default="tta", description="Service name for traces and metrics")
    service_version: str = Field(default="0.1.0", description="Service version")

    tracing: TracingConfig = Field(
        default_factory=TracingConfig, description="Tracing configuration"
    )
    metrics: MetricsConfig = Field(default_factory=MetricsConfig, description="Metrics configuration")
    storage: StorageConfig = Field(
        default_factory=StorageConfig, description="Storage configuration"
    )

    # Performance tuning
    async_export: bool = Field(
        default=True, description="Use async export for metrics and traces"
    )
    max_export_workers: int = Field(
        default=4, ge=1, le=32, description="Maximum concurrent export workers"
    )

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_environment(cls, environment: str | None = None) -> ObservabilityConfig:
        """
        Create configuration from environment name.

        Provides sensible defaults for different environments:
        - development: High sampling, console export, debugging enabled
        - staging: Medium sampling, observability backend export
        - production: Low sampling, optimized for scale

        Args:
            environment: Environment name (or read from ENVIRONMENT env var)

        Returns:
            Configuration instance for the environment

        Example:
            ```python
            # Read from ENVIRONMENT env var
            config = ObservabilityConfig.from_environment()

            # Explicit environment
            config = ObservabilityConfig.from_environment("production")
            ```
        """
        env = environment or os.getenv("ENVIRONMENT", "development")

        if env == "production":
            return cls(
                environment=env,
                tracing=TracingConfig(
                    sampling=SamplingConfig(
                        default_rate=0.05,  # 5% sampling
                        always_sample_errors=True,
                        always_sample_slow=True,
                        adaptive_enabled=True,
                        adaptive_min_rate=0.01,
                        adaptive_max_rate=0.2,
                    ),
                    export_interval_seconds=60.0,
                ),
                metrics=MetricsConfig(
                    max_label_values=100,
                    hash_high_cardinality=True,
                    export_interval_seconds=60.0,
                ),
                storage=StorageConfig(
                    trace_ttl_days=7,
                    compression_enabled=True,
                ),
            )
        elif env == "staging":
            return cls(
                environment=env,
                tracing=TracingConfig(
                    sampling=SamplingConfig(
                        default_rate=0.2,  # 20% sampling
                        always_sample_errors=True,
                        always_sample_slow=True,
                        adaptive_enabled=True,
                    ),
                    export_interval_seconds=30.0,
                ),
                metrics=MetricsConfig(
                    max_label_values=200,
                    hash_high_cardinality=True,
                ),
                storage=StorageConfig(trace_ttl_days=3),
            )
        else:  # development
            return cls(
                environment=env,
                tracing=TracingConfig(
                    sampling=SamplingConfig(
                        default_rate=1.0,  # 100% sampling
                        always_sample_errors=True,
                        always_sample_slow=True,
                        adaptive_enabled=False,
                    ),
                    export_interval_seconds=10.0,
                ),
                metrics=MetricsConfig(
                    max_label_values=1000,  # No practical limit
                    hash_high_cardinality=False,  # Keep readable for debugging
                ),
                storage=StorageConfig(trace_ttl_days=1),
            )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Configuration as nested dictionary
        """
        return {
            "environment": self.environment,
            "service_name": self.service_name,
            "service_version": self.service_version,
            "tracing": {
                "enabled": self.tracing.enabled,
                "sampling": {
                    "default_rate": self.tracing.sampling.default_rate,
                    "always_sample_errors": self.tracing.sampling.always_sample_errors,
                    "always_sample_slow": self.tracing.sampling.always_sample_slow,
                    "slow_threshold_ms": self.tracing.sampling.slow_threshold_ms,
                    "adaptive_enabled": self.tracing.sampling.adaptive_enabled,
                },
                "export_interval_seconds": self.tracing.export_interval_seconds,
                "batch_size": self.tracing.batch_size,
            },
            "metrics": {
                "enabled": self.metrics.enabled,
                "max_label_values": self.metrics.max_label_values,
                "hash_high_cardinality": self.metrics.hash_high_cardinality,
                "export_interval_seconds": self.metrics.export_interval_seconds,
            },
            "storage": {
                "trace_ttl_days": self.storage.trace_ttl_days,
                "metric_ttl_days": self.storage.metric_ttl_days,
                "compression_enabled": self.storage.compression_enabled,
            },
            "async_export": self.async_export,
        }


# Global configuration instance
_global_config: ObservabilityConfig | None = None


def get_observability_config() -> ObservabilityConfig:
    """
    Get the global observability configuration.

    Returns:
        Global configuration instance (creates default if not set)

    Example:
        ```python
        from tta_dev_primitives.observability.config import get_observability_config

        config = get_observability_config()
        print(f"Sampling rate: {config.tracing.sampling.default_rate}")
        ```
    """
    global _global_config
    if _global_config is None:
        _global_config = ObservabilityConfig.from_environment()
    return _global_config


def set_observability_config(config: ObservabilityConfig) -> None:
    """
    Set the global observability configuration.

    Args:
        config: Configuration to set globally

    Example:
        ```python
        from tta_dev_primitives.observability.config import (
            ObservabilityConfig,
            set_observability_config,
        )

        config = ObservabilityConfig.from_environment("production")
        set_observability_config(config)
        ```
    """
    global _global_config
    _global_config = config
    logger.info(
        f"Observability configuration set: environment={config.environment}, "
        f"sampling_rate={config.tracing.sampling.default_rate}"
    )
