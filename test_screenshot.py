import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle", timeout=10000)
            await page.screenshot(path="dashboard_screenshot.png", full_page=True)
            
            # Get HTML content
            content = await page.content()
            print("=== PAGE HTML (first 2000 chars) ===")
            print(content[:2000])
            print("\n=== PAGE TITLE ===")
            print(await page.title())
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

asyncio.run(main())
