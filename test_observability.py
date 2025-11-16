#!/usr/bin/env python3
"""
Quick test script for observability initialization.

Usage:
    uv run python test_observability.py [service-name]

Example:
    uv run python test_observability.py tta-dev-copilot
"""

import sys

from observability_integration import initialize_observability


def main():
    # Get service name from command line or use default
    service_name = sys.argv[1] if len(sys.argv) > 1 else "tta-dev-test"

    print(f"🔧 Initializing observability for: {service_name}")
    print("📊 Prometheus metrics will be exported on port 9464")
    print()

    # Initialize observability
    success = initialize_observability(
        service_name=service_name,
        enable_prometheus=True,
        prometheus_port=9464,
    )

    if success:
        print(f"✅ Observability successfully initialized for '{service_name}'!")
        print()
        print("📈 Metrics endpoint: http://localhost:9464/metrics")
        print("🔍 Check metrics with: curl http://localhost:9464/metrics")
        print()
        print("Next steps:")
        print("1. Run your TTA.dev application")
        print("2. Metrics will be automatically exported")
        print("3. If Grafana Alloy is running, metrics will be sent to Grafana Cloud")
    else:
        print("❌ Failed to initialize observability")
        print()
        print("This is normal if:")
        print("- You don't have OpenTelemetry packages installed")
        print("- Prometheus client is not available")
        print()
        print("The application will still work, just without observability.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
