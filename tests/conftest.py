"""Root test configuration.

collect_ignore lists legacy test files that depend on packages not installed
in the standard dev environment (old package names, uninstalled optional deps).
These are kept for historical reference but excluded from the default test run.
"""

collect_ignore = [
    # Requires `requests` (not in main deps)
    "integration/simple_mcp_test.py",
    # Requires `universal_agent_context` (old package, renamed)
    "integration/test_agent_coordination_integration.py",
    # Requires old `observability` top-level package
    "observability/test_dashboard.py",
    # Requires `tta_agent_coordination` (old package name)
    "test_context_integration.py",
    # Requires `yaml` / pyyaml (not in main deps)
    "test_copilot_instructions.py",
    # Requires old `primitives` top-level package
    "test_lifecycle.py",
    # Requires old `observability_integration` package
    "test_observability.py",
    # Playwright e2e tests — require `playwright install` + live server
    "e2e/test_observability_dashboard.py",
    "e2e/test_dashboard_v2.py",
    # Playwright tests requiring a live server (not in unit test run)
    "test_observability_ui.py",
    "test_observability_dashboard.py",
    # Requires hello.py (gitignored, not present in CI)
    "test_hello.py",
    # Requires pytest-benchmark (not in main deps)
    "benchmarks/test_primitive_performance.py",
]
