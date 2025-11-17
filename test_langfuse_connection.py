#!/usr/bin/env python
"""Test Langfuse connection with user credentials."""

import sys
from pathlib import Path

# Add package to path
sys.path.insert(
    0, str(Path(__file__).parent / "packages" / "tta-langfuse-integration" / "src")
)

from langfuse_integration import (
    initialize_langfuse,
    is_langfuse_enabled,
)
from langfuse_integration.initialization import get_langfuse_client


def main():
    """Test Langfuse connection."""
    print("🔧 Initializing Langfuse...")
    initialize_langfuse()

    if is_langfuse_enabled():
        print("✅ Langfuse is enabled and ready!")

        client = get_langfuse_client()
        if client:
            print("✅ Client initialized successfully")
            print(f"   Host: {client._base_url}")

            # Try to flush to verify credentials work
            try:
                client.flush()
                print("✅ Connection verified - credentials are valid!")
                print("\n🎉 Langfuse integration is working!")
                print("\nNext steps:")
                print(
                    "  1. Check your Langfuse dashboard at https://cloud.langfuse.com"
                )
                print("  2. Try creating a test trace")
                print("  3. Integrate with your LLM primitives")
                return 0
            except Exception as e:
                print(f"❌ Connection failed: {e}")
                print("   Check your credentials and network connection")
                return 1
        else:
            print("❌ Client is None")
            return 1
    else:
        print("❌ Langfuse is not enabled")
        print(
            "   Check LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
