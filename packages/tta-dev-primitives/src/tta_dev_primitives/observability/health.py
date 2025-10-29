"""Health check and status endpoints for observability."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .config import get_observability_config
from .metrics import get_metrics_collector
from .sampling import CompositeSampler


class HealthStatus(Enum):
    """Health status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Health check result."""

    status: HealthStatus
    message: str
    details: dict[str, Any]
    timestamp: float


class ObservabilityHealth:
    """
    Health check and status monitoring for observability.

    Provides endpoints to check observability system health,
    sampling status, and metric collection status.

    Example:
        ```python
        from tta_dev_primitives.observability.health import ObservabilityHealth

        health = ObservabilityHealth()

        # Check overall health
        result = health.check_health()
        print(f"Status: {result.status.value}")
        print(f"Message: {result.message}")

        # Get sampling status
        sampling_status = health.get_sampling_status()
        print(f"Current rate: {sampling_status['current_rate']}")

        # Get metrics status
        metrics_status = health.get_metrics_status()
        print(f"Total primitives: {metrics_status['total_primitives']}")
        ```
    """

    def __init__(self) -> None:
        """Initialize health checker."""
        self._start_time = time.time()

    def check_health(self) -> HealthCheck:
        """
        Perform comprehensive health check.

        Returns:
            Health check result with status and details

        Example:
            ```python
            health = ObservabilityHealth()
            result = health.check_health()

            if result.status == HealthStatus.HEALTHY:
                print("Observability is healthy")
            else:
                print(f"Issues: {result.message}")
            ```
        """
        details: dict[str, Any] = {}
        issues: list[str] = []

        # Check configuration
        try:
            config = get_observability_config()
            details["config_loaded"] = True
            details["environment"] = config.environment
        except Exception as e:
            details["config_loaded"] = False
            issues.append(f"Config error: {e}")

        # Check metrics collector
        try:
            collector = get_metrics_collector()
            stats = collector.get_cardinality_stats()
            details["metrics_collector"] = "available"
            details["unique_primitives"] = stats.get("unique_primitives", 0)

            # Check for cardinality issues
            if stats.get("dropped_labels"):
                issues.append(
                    f"Cardinality limit reached: {stats['dropped_labels']}"
                )
        except Exception as e:
            details["metrics_collector"] = "error"
            issues.append(f"Metrics collector error: {e}")

        # Check tracing
        try:
            from .tracing import TRACING_AVAILABLE

            details["tracing_available"] = TRACING_AVAILABLE
            if not TRACING_AVAILABLE:
                issues.append("OpenTelemetry not available")
        except Exception as e:
            details["tracing_available"] = False
            issues.append(f"Tracing check error: {e}")

        # Determine overall status
        if not issues:
            status = HealthStatus.HEALTHY
            message = "All observability systems operational"
        elif len(issues) <= 1:
            status = HealthStatus.DEGRADED
            message = f"Degraded: {'; '.join(issues)}"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Unhealthy: {'; '.join(issues)}"

        # Add runtime info
        details["uptime_seconds"] = time.time() - self._start_time
        details["issues_count"] = len(issues)

        return HealthCheck(
            status=status,
            message=message,
            details=details,
            timestamp=time.time(),
        )

    def get_sampling_status(self) -> dict[str, Any]:
        """
        Get current sampling configuration and status.

        Returns:
            Sampling status including current rates and configuration

        Example:
            ```python
            health = ObservabilityHealth()
            status = health.get_sampling_status()

            print(f"Sampling rate: {status['sampling_rate']}")
            print(f"Adaptive enabled: {status['adaptive_enabled']}")
            ```
        """
        try:
            config = get_observability_config()

            status = {
                "enabled": config.tracing.enabled,
                "sampling_rate": config.tracing.sampling.default_rate,
                "always_sample_errors": config.tracing.sampling.always_sample_errors,
                "always_sample_slow": config.tracing.sampling.always_sample_slow,
                "slow_threshold_ms": config.tracing.sampling.slow_threshold_ms,
                "adaptive_enabled": config.tracing.sampling.adaptive_enabled,
            }

            if config.tracing.sampling.adaptive_enabled:
                status["adaptive_min_rate"] = config.tracing.sampling.adaptive_min_rate
                status["adaptive_max_rate"] = config.tracing.sampling.adaptive_max_rate
                status["adaptive_target_overhead"] = config.tracing.sampling.adaptive_target_overhead

            return status

        except Exception as e:
            return {
                "error": str(e),
                "enabled": False,
            }

    def get_metrics_status(self) -> dict[str, Any]:
        """
        Get current metrics collection status.

        Returns:
            Metrics status including collection stats and cardinality info

        Example:
            ```python
            health = ObservabilityHealth()
            status = health.get_metrics_status()

            print(f"Total primitives: {status['total_primitives']}")
            print(f"Cardinality: {status['cardinality']}")
            ```
        """
        try:
            config = get_observability_config()
            collector = get_metrics_collector()

            # Get all metrics
            all_metrics = collector.get_metrics()

            # Calculate aggregates
            total_executions = sum(
                m.get("total_executions", 0) for m in all_metrics.values()
            )
            total_errors = sum(
                m.get("failed_executions", 0) for m in all_metrics.values()
            )

            # Get cardinality stats
            cardinality_stats = collector.get_cardinality_stats()

            return {
                "enabled": config.metrics.enabled,
                "total_primitives": len(all_metrics),
                "total_executions": total_executions,
                "total_errors": total_errors,
                "cardinality": {
                    "max_label_values": cardinality_stats["max_label_values"],
                    "total_labels": cardinality_stats["total_labels"],
                    "dropped_labels": cardinality_stats["dropped_labels"],
                    "hash_enabled": cardinality_stats["hash_high_cardinality"],
                },
                "export_interval_seconds": config.metrics.export_interval_seconds,
            }

        except Exception as e:
            return {
                "error": str(e),
                "enabled": False,
            }

    def get_storage_status(self) -> dict[str, Any]:
        """
        Get storage configuration status.

        Returns:
            Storage configuration including TTL and compression settings

        Example:
            ```python
            health = ObservabilityHealth()
            status = health.get_storage_status()

            print(f"Trace TTL: {status['trace_ttl_days']} days")
            print(f"Compression: {status['compression_enabled']}")
            ```
        """
        try:
            config = get_observability_config()

            return {
                "trace_ttl_days": config.storage.trace_ttl_days,
                "metric_ttl_days": config.storage.metric_ttl_days,
                "compression_enabled": config.storage.compression_enabled,
                "compression_level": config.storage.compression_level,
            }

        except Exception as e:
            return {
                "error": str(e),
            }

    def get_system_info(self) -> dict[str, Any]:
        """
        Get overall system information.

        Returns:
            System information including environment, service details, and runtime info

        Example:
            ```python
            health = ObservabilityHealth()
            info = health.get_system_info()

            print(f"Service: {info['service_name']} v{info['service_version']}")
            print(f"Environment: {info['environment']}")
            print(f"Uptime: {info['uptime_seconds']}s")
            ```
        """
        try:
            config = get_observability_config()

            return {
                "service_name": config.service_name,
                "service_version": config.service_version,
                "environment": config.environment,
                "uptime_seconds": time.time() - self._start_time,
                "async_export_enabled": config.async_export,
                "max_export_workers": config.max_export_workers,
            }

        except Exception as e:
            return {
                "error": str(e),
                "uptime_seconds": time.time() - self._start_time,
            }

    def get_full_status(self) -> dict[str, Any]:
        """
        Get complete observability status.

        Returns:
            Complete status including health, sampling, metrics, storage, and system info

        Example:
            ```python
            health = ObservabilityHealth()
            status = health.get_full_status()

            print(f"Health: {status['health']['status']}")
            print(f"Sampling rate: {status['sampling']['sampling_rate']}")
            print(f"Total executions: {status['metrics']['total_executions']}")
            ```
        """
        health_check = self.check_health()

        return {
            "health": {
                "status": health_check.status.value,
                "message": health_check.message,
                "details": health_check.details,
                "timestamp": health_check.timestamp,
            },
            "system": self.get_system_info(),
            "sampling": self.get_sampling_status(),
            "metrics": self.get_metrics_status(),
            "storage": self.get_storage_status(),
        }


# Global health checker instance
_health_checker: ObservabilityHealth | None = None


def get_health_checker() -> ObservabilityHealth:
    """
    Get the global health checker instance.

    Returns:
        Global health checker

    Example:
        ```python
        from tta_dev_primitives.observability.health import get_health_checker

        health = get_health_checker()
        result = health.check_health()
        ```
    """
    global _health_checker
    if _health_checker is None:
        _health_checker = ObservabilityHealth()
    return _health_checker
