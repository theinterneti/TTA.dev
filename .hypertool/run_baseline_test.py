#!/usr/bin/env python3
"""
Simple Test - Manual Testing Baseline

Runs the baseline test workflow with Prometheus registry cleanup.
"""

import asyncio
import sys
from pathlib import Path

# Add .hypertool to path
sys.path.insert(0, str(Path(__file__).parent / ".."))

# Clear Prometheus registry before importing our modules
try:
    from prometheus_client import REGISTRY

    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        try:
            REGISTRY.unregister(collector)
        except Exception:
            pass
except Exception:
    pass

# Now import test workflow
from instrumentation.test_instrumented_workflow import main

if __name__ == "__main__":
    asyncio.run(main())
