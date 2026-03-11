#!/usr/bin/env python3
"""Test the observability dashboard using Playwright."""

import asyncio

from playwright.async_api import async_playwright


async def test_dashboard():
    """Test that the dashboard loads and displays content correctly."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        print("🌐 Navigating to dashboard...")
        await page.goto("http://localhost:8000")

        print("⏳ Waiting for page to load...")
        await page.wait_for_load_state("networkidle")

        # Take screenshot
        await page.screenshot(path="/tmp/dashboard.png")
        print("📸 Screenshot saved to /tmp/dashboard.png")

        # Check for key elements
        print("\n🔍 Checking page elements...")

        title = await page.title()
        print(f"  ✓ Title: {title}")

        # Check for connection status
        status = await page.locator("#connectionStatus").text_content()
        print(f"  ✓ Connection status: {status}")

        # Check metrics
        total_workflows = await page.locator("#totalWorkflows").text_content()
        print(f"  ✓ Total workflows: {total_workflows}")

        # Check for panels
        agents_panel = await page.locator("#agentsPanel").count()
        print(f"  ✓ Agents panel: {'✓' if agents_panel > 0 else '✗'}")

        primitives_panel = await page.locator("#primitivesPanel").count()
        print(f"  ✓ Primitives panel: {'✓' if primitives_panel > 0 else '✗'}")

        workflows_panel = await page.locator("#workflowsPanel").count()
        print(f"  ✓ Workflows panel: {'✓' if workflows_panel > 0 else '✗'}")

        # Check code graph
        graph_container = await page.locator("#graphContainer").count()
        print(f"  ✓ Code graph: {'✓' if graph_container > 0 else '✗'}")

        # Check console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        await asyncio.sleep(2)

        if console_errors:
            print("\n⚠️  Console errors:")
            for error in console_errors:
                print(f"    {error.text}")
        else:
            print("\n✅ No console errors")

        await browser.close()
        print("\n✅ Dashboard test complete!")


if __name__ == "__main__":
    asyncio.run(test_dashboard())
