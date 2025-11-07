#!/usr/bin/env python3
"""
Ultra-simple E2B test to isolate the issue.
"""

import os

from e2b_code_interpreter import Sandbox


def simple_test():
    """Most basic E2B test possible."""

    # Set API key - try multiple sources
    api_key = None

    # Try direct environment variables
    if "E2B_API_KEY" in os.environ:
        api_key = os.environ["E2B_API_KEY"]
    elif "E2B_KEY" in os.environ:
        api_key = os.environ["E2B_KEY"]
        os.environ["E2B_API_KEY"] = api_key
    else:
        # Try loading from .env file manually
        try:
            with open(".env") as f:
                for line in f:
                    if line.startswith("E2B_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        os.environ["E2B_API_KEY"] = api_key
                        break
        except FileNotFoundError:
            pass

    if api_key:
        print(f"✅ API key loaded: {api_key[:20]}...")
    else:
        print("❌ No API key found in any location")
        return False

    try:
        print("🚀 Creating sandbox...")
        sandbox = Sandbox.create()
        print(f"✅ Sandbox created: {sandbox.sandbox_id}")

        print("📝 Running simple code...")
        result = sandbox.run_code("1 + 1")
        print(f"📊 Result type: {type(result)}")
        print(f"📊 Result: {result}")

        if result:
            print(f"📊 Result text: {result.text}")
            print(f"📊 Result logs: {result.logs}")

        sandbox.kill()
        print("✅ Test completed successfully")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        print(f"❌ Error type: {type(e)}")
        return False


if __name__ == "__main__":
    print("🔍 ULTRA-SIMPLE E2B TEST")
    print("=" * 30)
    success = simple_test()

    if success:
        print("\n✅ E2B is working - issue might be with specific operations")
    else:
        print("\n❌ E2B has fundamental issues - check service status")
