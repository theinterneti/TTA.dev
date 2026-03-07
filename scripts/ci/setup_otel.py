#!/usr/bin/env python3
"""Configure OpenTelemetry for CI environment."""

import os
import sys


def setup_otel_env():
    """Configure OTEL environment variables for CI runners."""

    # Check if already configured
    if os.getenv("OTEL_CONFIGURED"):
        print("✅ OTEL already configured", file=sys.stderr)
        return

    # Read configuration from platform observability
    config = {
        "OTEL_SERVICE_NAME": "tta-ci-runner",
        "OTEL_EXPORTER_OTLP_ENDPOINT": os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318"
        ),
        "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
        "OTEL_TRACES_EXPORTER": "otlp",
        "OTEL_METRICS_EXPORTER": "otlp",
        "OTEL_LOGS_EXPORTER": "otlp",
        "OTEL_RESOURCE_ATTRIBUTES": _build_resource_attributes(),
        "OTEL_CONFIGURED": "true",
    }

    # Export to environment
    for key, value in config.items():
        os.environ[key] = value
        print(f"export {key}={value}")

    print("✅ OTEL environment configured", file=sys.stderr)


def _build_resource_attributes() -> str:
    """Build OTEL resource attributes from CI context."""
    attrs = {
        "service.name": "tta-ci-runner",
        "service.version": os.getenv("GITHUB_SHA", "unknown")[:8],
        "deployment.environment": "ci",
        "ci.provider": "github-actions",
        "ci.run_id": os.getenv("GITHUB_RUN_ID", "unknown"),
        "ci.workflow": os.getenv("GITHUB_WORKFLOW", "unknown"),
        "ci.actor": os.getenv("GITHUB_ACTOR", "unknown"),
        "git.ref": os.getenv("GITHUB_REF", "unknown"),
        "git.sha": os.getenv("GITHUB_SHA", "unknown"),
    }

    return ",".join(f"{k}={v}" for k, v in attrs.items())


def main():
    """CLI interface for OTEL setup."""
    setup_otel_env()


if __name__ == "__main__":
    main()
