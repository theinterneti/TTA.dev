"""Automated tests for observability dashboard using Playwright."""
import asyncio
import pytest
from playwright.async_api import async_playwright, expect
import json
from pathlib import Path


@pytest.mark.asyncio
async def test_dashboard_loads():
    """Test that dashboard loads and displays basic elements."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto("http://localhost:8000")
        
        # Check title
        await expect(page).to_have_title("TTA.dev Observability")
        
        # Check main sections exist
        await expect(page.locator("#stats")).to_be_visible()
        await expect(page.locator("#primitivesCatalog")).to_be_visible()
        await expect(page.locator("#workflowRegistry")).to_be_visible()
        await expect(page.locator("#recentTraces")).to_be_visible()
        
        await browser.close()


@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection status."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto("http://localhost:8000")
        
        # Wait for WebSocket connection
        await page.wait_for_timeout(2000)
        
        # Check connection status
        status = await page.locator("#connectionStatus").text_content()
        assert "Connected" in status or "Connecting" in status
        
        await browser.close()


@pytest.mark.asyncio
async def test_primitives_catalog_pagination():
    """Test primitives catalog shows all items with pagination."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(1000)
        
        # Check primitives are loaded
        primitives = await page.locator("#primitivesCatalog .primitive-item").count()
        assert primitives > 0, "No primitives loaded"
        
        # Check pagination controls exist if needed
        total_text = await page.locator("#primitivesCatalog").text_content()
        if "68" in total_text:  # We know there are 68 primitives
            # Check if pagination exists
            pagination = await page.locator(".pagination").count()
            assert pagination > 0, "Pagination should exist for 68 items"
        
        await browser.close()


@pytest.mark.asyncio
async def test_search_functionality():
    """Test search box filters primitives."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(1000)
        
        # Get initial visible count
        initial_count = await page.locator("#primitivesCatalog .primitive-item:visible").count()
        
        # Search for specific primitive
        search_box = page.locator("#searchPrimitives")
        await search_box.fill("Retry")
        await page.wait_for_timeout(500)
        
        # Check filtered results (only visible)
        filtered_count = await page.locator("#primitivesCatalog .primitive-item:visible").count()
        assert filtered_count < initial_count, "Search should filter results"
        assert filtered_count > 0, "Should find RetryPrimitive"
        
        await browser.close()


@pytest.mark.asyncio
async def test_code_graph_loads():
    """Test CGC code graph visualization loads."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)
        
        # Check graph container exists
        await expect(page.locator("#codeGraph")).to_be_visible()
        
        # Check graph controls exist
        await expect(page.locator("#fitGraph")).to_be_visible()
        await expect(page.locator("#resetGraph")).to_be_visible()
        
        await browser.close()


@pytest.mark.asyncio
async def test_trace_details_modal():
    """Test that clicking a trace opens details modal."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(2000)
        
        # Check if any traces exist
        traces = await page.locator("#recentTraces .trace-item").count()
        
        if traces > 0:
            # Click first trace
            await page.locator("#recentTraces .trace-item").first.click()
            await page.wait_for_timeout(500)
            
            # Check modal appears
            modal = page.locator("#traceModal")
            await expect(modal).to_be_visible()
            
            # Check close button works
            await page.locator(".close-modal").click()
            await expect(modal).to_be_hidden()
        
        await browser.close()


@pytest.mark.asyncio
async def test_agent_activity_tracking():
    """Test agent activity panel shows provider/model/agent info."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(1000)
        
        # Check agent activity section exists
        await expect(page.locator("#agentActivity")).to_be_visible()
        
        # If there's agent activity, verify structure
        agents = await page.locator("#agentActivity .agent-card").count()
        if agents > 0:
            first_agent = page.locator("#agentActivity .agent-card").first
            
            # Check it has provider/model/agent info
            text = await first_agent.text_content()
            assert "Provider:" in text or "Model:" in text
        
        await browser.close()


@pytest.mark.asyncio  
async def test_workflow_registry():
    """Test workflow registry displays registered workflows."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto("http://localhost:8000")
        await page.wait_for_timeout(1000)
        
        # Check workflow registry exists
        await expect(page.locator("#workflowRegistry")).to_be_visible()
        
        # Check for registered workflows text
        registry_text = await page.locator("#workflowRegistry").text_content()
        assert "Registered:" in registry_text
        
        await browser.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
