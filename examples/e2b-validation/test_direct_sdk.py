#!/usr/bin/env python3
"""Direct E2B SDK test to debug template issues"""

import asyncio
import os
import time

from e2b_code_interpreter import AsyncSandbox


async def test_template_directly():
    """Test template creation directly with E2B SDK."""

    print("🔧 Direct E2B SDK Template Test")
    print("=" * 40)

    # Set API key - try both E2B_KEY and E2B_API_KEY
    api_key = os.getenv("E2B_API_KEY") or os.getenv("E2B_KEY")
    if api_key:
        os.environ["E2B_API_KEY"] = api_key
        print(f"✅ API key set: {api_key[:20]}...")
    else:
        print("❌ No API key found in E2B_API_KEY or E2B_KEY")
        print(f"Environment keys: {list(os.environ.keys())[:5]}...")
        return

    # Test 1: Default template
    print("\n📦 Test 1: Default Template (Direct SDK)")
    try:
        start_time = time.time()
        sandbox = await AsyncSandbox.create()
        create_time = time.time() - start_time
        print(f"✅ Default sandbox created in {create_time:.2f}s: {sandbox.sandbox_id}")

        # Try simple code
        result = await sandbox.run_code("print('Hello default!')")
        exec_time = time.time() - start_time
        print(f"✅ Code executed in {exec_time:.2f}s total: {result.text}")

        await sandbox.kill()
        print("✅ Default sandbox cleaned up")

    except Exception as e:
        print(f"❌ Default template failed: {e}")

    # Test 2: ML template by name
    print("\n🤖 Test 2: ML Template by Name (Direct SDK)")
    try:
        start_time = time.time()
        sandbox = await AsyncSandbox.create(template="tta-ml-minimal")
        create_time = time.time() - start_time
        print(f"✅ ML sandbox created in {create_time:.2f}s: {sandbox.sandbox_id}")

        # Try simple code first
        result = await sandbox.run_code("print('Hello ML template!')")
        exec_time = time.time() - start_time
        print(f"✅ Simple code executed in {exec_time:.2f}s total: {result.text}")

        await sandbox.kill()
        print("✅ ML sandbox cleaned up")

    except Exception as e:
        print(f"❌ ML template by name failed: {e}")

    # Test 3: ML template by ID
    print("\n🤖 Test 3: ML Template by ID (Direct SDK)")
    try:
        start_time = time.time()
        sandbox = await AsyncSandbox.create(template="3xmp0rmfztawhlpysu4v")
        create_time = time.time() - start_time
        print(f"✅ ML sandbox created in {create_time:.2f}s: {sandbox.sandbox_id}")

        # Try simple code first
        result = await sandbox.run_code("print('Hello ML template by ID!')")
        exec_time = time.time() - start_time
        print(f"✅ Simple code executed in {exec_time:.2f}s total: {result.text}")

        await sandbox.kill()
        print("✅ ML sandbox cleaned up")

    except Exception as e:
        print(f"❌ ML template by ID failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_template_directly())
