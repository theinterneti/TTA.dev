"""
End-to-end tests for TTA.dev observability dashboard.

These tests verify the complete user journey per OBSERVABILITY_SPEC.md.
All tests must pass before merging dashboard changes.
"""

import json
import time
from pathlib import Path

import pytest
from playwright.async_api import Page, expect


@pytest.fixture(scope="module")
def observability_dir(tmp_path_factory):
    """Create temporary observability directory for test traces."""
    obs_dir = tmp_path_factory.mktemp("observability")
    traces_dir = obs_dir / "traces"
    traces_dir.mkdir()
    return obs_dir


@pytest.fixture(scope="module")
async def dashboard_url():
    """Start observability server and return URL."""
    # TODO: Start server in background
    # For now, assume server is running on localhost:8000
    return "http://localhost:8000"


@pytest.mark.asyncio
async def test_01_server_serves_html(page: Page, dashboard_url: str):
    """Test 1: Server starts and serves HTML."""
    await page.goto(dashboard_url)
    await expect(page).to_have_title("TTA.dev Observability")

    # Verify main sections exist
    await expect(page.locator("#activeAgents")).to_be_visible()
    await expect(page.locator("#recentTraces")).to_be_visible()
    await expect(page.locator("#workflowRegistry")).to_be_visible()
    await expect(page.locator("#primitivesCatalog")).to_be_visible()
    await expect(page.locator("#codeGraph")).to_be_visible()


@pytest.mark.asyncio
async def test_02_dashboard_loads_all_sections(page: Page, dashboard_url: str):
    """Test 2: Dashboard loads all sections with correct headers."""
    await page.goto(dashboard_url)

    # Check section headers
    assert await page.locator("text=Active Agents").is_visible()
    assert await page.locator("text=Recent Traces").is_visible()
    assert await page.locator("text=Workflow Registry").is_visible()
    assert await page.locator("text=Primitives Catalog").is_visible()
    assert await page.locator("text=Code Graph").is_visible()


@pytest.mark.asyncio
async def test_03_websocket_connects(page: Page, dashboard_url: str):
    """Test 3: WebSocket connects successfully."""
    await page.goto(dashboard_url)

    # Wait for WebSocket connection
    await page.wait_for_timeout(2000)

    # Check connection status indicator
    status = await page.locator("#connectionStatus").inner_text()
    assert "Connected" in status or "●" in status


@pytest.mark.asyncio
async def test_04_active_agents_populate(page: Page, dashboard_url: str):
    """Test 4: Active agents populate correctly."""
    await page.goto(dashboard_url)
    await page.wait_for_timeout(2000)

    # Should show at least the system/test agent
    agent_cards = await page.locator(".agent-card").count()
    assert agent_cards >= 1

    # Check agent card structure
    first_agent = page.locator(".agent-card").first
    await expect(first_agent.locator(".agent-provider")).to_be_visible()
    await expect(first_agent.locator(".agent-model")).to_be_visible()
    await expect(first_agent.locator(".agent-user")).to_be_visible()


@pytest.mark.asyncio
async def test_05_traces_display_with_hierarchy(
    page: Page, dashboard_url: str, observability_dir: Path
):
    """Test 5: Traces display with hierarchy."""
    # Create a test trace
    trace = {
        "trace_id": "test-trace-001",
        "user": "thein",
        "provider": "GitHub Copilot",
        "model": "Claude Sonnet 4.5",
        "agent_role": "backend-engineer",
        "workflow": "test_workflow",
        "primitives": ["RetryPrimitive", "CachePrimitive"],
        "tools": ["bash", "edit"],
        "status": "success",
        "start_time": time.time(),
        "duration_ms": 1234.5,
    }

    trace_file = observability_dir / "traces" / "test-trace-001.json"
    trace_file.write_text(json.dumps(trace, indent=2))

    await page.goto(dashboard_url)
    await page.wait_for_timeout(3000)  # Wait for file watch

    # Check trace appears
    await expect(page.locator("text=test-trace-001")).to_be_visible()

    # Click to expand
    await page.locator("text=test-trace-001").click()

    # Verify hierarchy is shown
    await expect(page.locator("text=GitHub Copilot")).to_be_visible()
    await expect(page.locator("text=Claude Sonnet 4.5")).to_be_visible()
    await expect(page.locator("text=backend-engineer")).to_be_visible()
    await expect(page.locator("text=RetryPrimitive")).to_be_visible()


@pytest.mark.asyncio
async def test_06_workflow_registry_shows_data(page: Page, dashboard_url: str):
    """Test 6: Workflow registry shows data."""
    await page.goto(dashboard_url)
    await page.wait_for_timeout(2000)

    # Should show registered workflows
    registry = page.locator("#workflowRegistry")
    await expect(registry).to_be_visible()

    # Check for at least one workflow
    workflows = await registry.locator(".workflow-item").count()
    assert workflows >= 1


@pytest.mark.asyncio
async def test_07_primitives_catalog_searchable(page: Page, dashboard_url: str):
    """Test 7: Primitives catalog is searchable."""
    await page.goto(dashboard_url)
    await page.wait_for_timeout(2000)

    # Find search input
    search_input = page.locator("#primitiveSearch")
    await expect(search_input).to_be_visible()

    # Count initial primitives
    initial_count = await page.locator(".primitive-item").count()
    assert initial_count > 0

    # Search for specific primitive
    await search_input.fill("Retry")
    await page.wait_for_timeout(500)

    # Should filter results
    filtered_count = await page.locator(".primitive-item").count()
    assert filtered_count < initial_count
    assert filtered_count >= 1


@pytest.mark.asyncio
async def test_08_code_graph_renders(page: Page, dashboard_url: str):
    """Test 8: Code graph renders and is interactive."""
    await page.goto(dashboard_url)
    await page.wait_for_timeout(3000)  # Graph needs time to load

    # Check graph canvas exists
    graph = page.locator("#codeGraph canvas, #codeGraph svg")
    await expect(graph).to_be_visible()

    # Check filter buttons exist
    await expect(page.locator("button:has-text('Primitives')")).to_be_visible()
    await expect(page.locator("button:has-text('Workflows')")).to_be_visible()
    await expect(page.locator("button:has-text('Agents')")).to_be_visible()


@pytest.mark.asyncio
async def test_09_realtime_updates_work(page: Page, dashboard_url: str, observability_dir: Path):
    """Test 9: Real-time updates work when new trace added."""
    await page.goto(dashboard_url)
    await page.wait_for_timeout(2000)

    # Count initial traces
    initial_count = await page.locator(".trace-item").count()

    # Add new trace while page is open
    new_trace = {
        "trace_id": f"realtime-test-{time.time()}",
        "user": "thein",
        "provider": "GitHub Copilot",
        "model": "Claude Sonnet 4.5",
        "status": "success",
        "start_time": time.time(),
        "duration_ms": 500.0,
    }

    trace_file = observability_dir / "traces" / f"{new_trace['trace_id']}.json"
    trace_file.write_text(json.dumps(new_trace, indent=2))

    # Wait for WebSocket update
    await page.wait_for_timeout(3000)

    # Should see new trace
    new_count = await page.locator(".trace-item").count()
    assert new_count > initial_count


@pytest.mark.asyncio
async def test_10_drill_down_expands_hierarchy(
    page: Page, dashboard_url: str, observability_dir: Path
):
    """Test 10: Drill-down expands trace hierarchy."""
    # Create detailed trace
    trace = {
        "trace_id": "hierarchy-test",
        "user": "thein",
        "provider": "GitHub Copilot",
        "model": "Claude Sonnet 4.5",
        "agent_role": "backend-engineer",
        "workflow": "complex_workflow",
        "spans": [
            {
                "name": "RetryPrimitive",
                "duration_ms": 100,
                "status": "success",
                "children": [
                    {"name": "bash", "duration_ms": 50},
                    {"name": "edit", "duration_ms": 50},
                ],
            },
            {"name": "CachePrimitive", "duration_ms": 200, "status": "success"},
        ],
        "status": "success",
        "start_time": time.time(),
        "duration_ms": 300.0,
    }

    trace_file = observability_dir / "traces" / "hierarchy-test.json"
    trace_file.write_text(json.dumps(trace, indent=2))

    await page.goto(dashboard_url)
    await page.wait_for_timeout(3000)

    # Find and click trace
    trace_elem = page.locator("text=hierarchy-test")
    await expect(trace_elem).to_be_visible()
    await trace_elem.click()

    # Should show expanded hierarchy
    await expect(page.locator("text=complex_workflow")).to_be_visible()
    await expect(page.locator("text=RetryPrimitive")).to_be_visible()
    await expect(page.locator("text=CachePrimitive")).to_be_visible()
    await expect(page.locator("text=bash")).to_be_visible()
    await expect(page.locator("text=edit")).to_be_visible()
