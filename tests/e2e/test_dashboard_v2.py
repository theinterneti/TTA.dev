"""E2E Playwright tests for the v2 observability dashboard.

Uses the sync Playwright API to avoid pytest-asyncio scope-mismatch issues
with module-scoped fixtures.

Scenarios:
  1. Dashboard loads and shows header
  2. Sessions sidebar lists at least one session
  3. WebSocket connects (badge shows "Connected")
  4. Session auto-selects and shows span count
  5. Clicking a session loads span detail
  6. Span detail panel opens on row click
  7. CGC graph section renders (Architecture view)
  8. v1 /api/traces backward-compatibility route
"""

import subprocess
import time
import urllib.request
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, sync_playwright, expect

_PORT = 8000
_BASE = f"http://localhost:{_PORT}"
_SERVER_CMD = ["uv", "run", "python3", "-m", "ttadev.observability"]
_REPO_ROOT = Path(__file__).parents[2]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def server():
    """Start the observability server for the test module."""
    subprocess.run(["fuser", "-k", "8000/tcp"], capture_output=True)
    time.sleep(1)

    proc = subprocess.Popen(
        _SERVER_CMD,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=_REPO_ROOT,
    )

    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(f"{_BASE}/api/v2/health", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        pytest.fail("Observability server did not start within 20s")

    yield proc

    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="module")
def browser(server) -> Browser:  # noqa: ARG001
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture()
def page(browser: Browser) -> Page:
    pg = browser.new_page(viewport={"width": 1400, "height": 900})
    pg.goto(_BASE)
    pg.wait_for_timeout(3500)  # WS connect + auto-select
    yield pg
    pg.close()


# ---------------------------------------------------------------------------
# Scenario 1 — Dashboard loads with header
# ---------------------------------------------------------------------------


def test_dashboard_header_visible(page: Page) -> None:
    expect(page.locator("h1")).to_contain_text("TTA.dev Observability")


# ---------------------------------------------------------------------------
# Scenario 2 — Sessions sidebar lists sessions
# ---------------------------------------------------------------------------


def test_sessions_sidebar_has_entries(page: Page) -> None:
    items = page.locator("#session-tree .session-item")
    count = items.count()
    assert count >= 1, f"Expected ≥1 session item, got {count}"


# ---------------------------------------------------------------------------
# Scenario 3 — WebSocket connected badge
# ---------------------------------------------------------------------------


def test_websocket_connected_badge(page: Page) -> None:
    expect(page.locator("#ws-badge")).to_contain_text("Connected")


# ---------------------------------------------------------------------------
# Scenario 4 — Session auto-selects and shows span count
# ---------------------------------------------------------------------------


def test_session_auto_selected_shows_spans(page: Page) -> None:
    # The metric chip "📊 Spans N" is the canonical indicator the session loaded
    expect(page.locator(".metric-chip").first).to_be_visible(timeout=5000)


# ---------------------------------------------------------------------------
# Scenario 5 — Clicking a session loads its detail
# ---------------------------------------------------------------------------


def test_click_session_loads_detail(page: Page) -> None:
    items = page.locator(".session-item")
    count = items.count()
    target = items.nth(min(1, count - 1))
    target.click()
    page.wait_for_timeout(1000)
    placeholder = page.locator("#session-detail >> text=Select a session")
    assert not placeholder.is_visible(), "Placeholder still visible after clicking session"


# ---------------------------------------------------------------------------
# Scenario 6 — Span detail panel opens on row click
# ---------------------------------------------------------------------------


def test_span_detail_opens_on_click(page: Page) -> None:
    rows = page.locator(".span-row")
    expect(rows.first).to_be_visible(timeout=5000)
    rows.first.click()
    page.wait_for_timeout(500)
    panel = page.locator("#span-detail")
    is_hidden = panel.evaluate("el => el.style.display === 'none' || el.hidden")
    assert not is_hidden, "Span detail panel did not open after row click"


# ---------------------------------------------------------------------------
# Scenario 7 — CGC graph renders (not permanently stuck loading)
# ---------------------------------------------------------------------------


def test_cgc_graph_renders(page: Page) -> None:
    section = page.locator("#cgc-graph-section")
    expect(section).to_be_visible()
    canvas = section.locator("#cgc-canvas")
    expect(canvas).to_be_visible()
    # Allow graph to finish loading
    page.wait_for_timeout(3000)
    assert not canvas.locator("text=Loading").is_visible(), \
        "Graph still showing loading spinner after 6.5s total"


# ---------------------------------------------------------------------------
# Scenario 8 — v1 /api/traces backward-compatibility
# ---------------------------------------------------------------------------


def test_v1_traces_route_works(page: Page) -> None:
    response = page.request.get(f"{_BASE}/api/traces")
    assert response.ok
    body = response.json()
    assert "traces" in body
