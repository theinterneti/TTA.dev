import asyncio

from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto("http://localhost:8000", wait_until="networkidle", timeout=10000)

            # Get all elements with IDs
            ids = await page.eval_on_selector_all("[id]", "elements => elements.map(e => e.id)")
            print("=== ELEMENTS WITH IDS ===")
            for id in ids:
                print(f"  #{id}")

            # Get all elements with classes
            classes = await page.eval_on_selector_all(
                "[class]",
                "elements => Array.from(new Set(elements.flatMap(e => e.className.split(' ')).filter(c => c)))",
            )
            print("\n=== UNIQUE CLASSES ===")
            for cls in sorted(set(classes)):
                print(f"  .{cls}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()


asyncio.run(main())
