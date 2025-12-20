"""
Root conftest.py for TTA.dev test collection.

This file ensures proper test isolation and handles the monorepo structure
where multiple test directories exist.
"""

import sys
from pathlib import Path

# Ensure the project root is in the path for imports
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Register pytest markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle namespace isolation."""
    # Filter out duplicate tests that might be collected from multiple paths
    seen = set()
    deduped = []
    for item in items:
        # Use the test's node ID for deduplication
        if item.nodeid not in seen:
            seen.add(item.nodeid)
            deduped.append(item)
    items[:] = deduped
