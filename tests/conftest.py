"""Root test configuration.

collect_ignore lists test files that require optional tools not in the
standard dev environment (Playwright, pytest-benchmark).

To run Playwright e2e tests: playwright install && uv run pytest tests/e2e/
To run benchmarks: uv add --dev pytest-benchmark && uv run pytest tests/benchmarks/
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Write TEST_STATUS.md after every run so agents always have current state."""
    terminalreporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if terminalreporter is None:
        return

    stats = terminalreporter.stats
    passed = len(stats.get("passed", []))
    failed = len(stats.get("failed", []))
    skipped = len(stats.get("skipped", []))
    errors = len(stats.get("error", []))
    duration = getattr(terminalreporter, "_session_start", None)
    elapsed = f"{duration.elapsed().seconds:.1f}s" if duration is not None else "unknown"

    total_problems = failed + errors
    icon = "✅" if total_problems == 0 else "❌"
    summary = f"{icon} **{passed} passed"
    if failed:
        summary += f", {failed} failed"
    if errors:
        summary += f", {errors} error(s)"
    if skipped:
        summary += f", {skipped} skipped"
    summary += f"** ({elapsed})"

    lines: list[str] = [
        "# Test Status",
        "",
        f"_Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} — `make watch`_",
        "",
        f"## {summary}",
        "",
    ]

    failing_reports = stats.get("failed", []) + stats.get("error", [])
    if failing_reports:
        lines.append("## Failing Tests")
        lines.append("")
        for report in failing_reports:
            lines.append(f"### `{report.nodeid}`")
            lines.append("```")
            if hasattr(report, "longreprtext"):
                lines.append(report.longreprtext[-2000:])
            elif hasattr(report, "longrepr"):
                lines.append(str(report.longrepr)[-2000:])
            lines.append("```")
            lines.append("")
    else:
        lines.append("## Failing Tests")
        lines.append("")
        lines.append("_None — all green_ 🟢")
        lines.append("")

    status_file = Path(__file__).parent.parent / "TEST_STATUS.md"
    status_file.write_text("\n".join(lines))


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
