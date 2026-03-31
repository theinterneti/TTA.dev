"""Root test configuration.

collect_ignore lists test files that require optional tools not in the
standard dev environment (Playwright, pytest-benchmark).

To run Playwright e2e tests: playwright install && uv run pytest tests/e2e/
To run benchmarks: uv add --dev pytest-benchmark && uv run pytest tests/benchmarks/
"""

collect_ignore = [
    # Playwright e2e tests — require `playwright install` + live server
    "e2e/test_observability_dashboard.py",
    "e2e/test_dashboard_v2.py",
    # Playwright UI tests requiring a live server
    "test_observability_ui.py",
    # Playwright dashboard tests at root level — require `playwright install`
    "test_observability_dashboard.py",
    # Requires pytest-benchmark (optional dev dep)
    "benchmarks/test_primitive_performance.py",
]
