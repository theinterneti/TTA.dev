"""
Simple test of the ML template we just built.
"""

import asyncio
import os
import time

import httpx


async def test_with_httpx():
    """Test ML template using direct HTTP API calls."""

    api_key = os.getenv("E2B_API_KEY")
    if not api_key:
        print("❌ Please set E2B_API_KEY environment variable")
        return

    print("🚀 Testing ML template: tta-ml-minimal")
    print("=" * 50)

    # Try using the E2B API directly
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    start_time = time.time()

    try:
        async with httpx.AsyncClient() as client:
            # Create sandbox with our ML template
            response = await client.post(
                "https://api.e2b.dev/sandboxes",
                headers=headers,
                json={"template": "tta-ml-minimal"},
                timeout=30.0,
            )

            if response.status_code != 200:
                print(f"❌ Failed to create sandbox: {response.status_code}")
                print(f"Response: {response.text}")
                return

            sandbox_data = response.json()
            sandbox_id = sandbox_data["sandboxId"]

            create_time = time.time() - start_time
            print(f"⚡ Sandbox created in {create_time:.2f} seconds")
            print(f"📦 Sandbox ID: {sandbox_id}")

            # Clean up
            await client.delete(f"https://api.e2b.dev/sandboxes/{sandbox_id}", headers=headers)

            print("✅ Template test successful!")
            print(f"🎯 Startup time: {create_time:.2f}s")

            if create_time < 5:
                print("🚀 EXCELLENT! Template loads in under 5 seconds")
            elif create_time < 15:
                print("✅ GOOD! Template loads reasonably fast")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("This could be due to API key issues or network problems")


if __name__ == "__main__":
    asyncio.run(test_with_httpx())
