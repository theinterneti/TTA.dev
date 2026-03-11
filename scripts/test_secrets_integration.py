#!/usr/bin/env python3
"""
Test script to demonstrate secrets management integration.
This script shows the migration from direct os.getenv() calls to tta_secrets.
"""

import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_legacy_vs_new_approach():
    """Test both legacy os.getenv() and new tta_secrets approaches."""
    print("🔒 TTA.dev Secrets Integration Test")
    print("=" * 50)

    # Test 1: Legacy approach (direct os.getenv)
    print("\n📋 Test 1: Legacy os.getenv() approach")
    try:
        gemini_key = os.getenv("GEMINI_API_KEY")
        github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        e2b_key = os.getenv("E2B_API_KEY")
        n8n_key = os.getenv("N8N_API_KEY")

        print(f"Gemini key found: {'✅' if gemini_key else '❌'}")
        print(f"GitHub token found: {'✅' if github_token else '❌'}")
        print(f"E2B key found: {'✅' if e2b_key else '❌'}")
        print(f"n8n key found: {'✅' if n8n_key else '❌'}")

    except Exception as e:
        print(f"❌ Legacy approach failed: {e}")

    # Test 2: New tta_secrets approach
    print("\n📋 Test 2: New tta_secrets approach")
    try:
        from tta_secrets import (
            get_config,
            get_e2b_key,
            get_gemini_api_key,
            get_github_token,
            get_n8n_key,
        )

        gemini_key = get_gemini_api_key()
        github_token = get_github_token()
        e2b_key = get_e2b_key()
        n8n_key = get_n8n_key()

        print(f"Gemini key via tta_secrets: {'✅' if gemini_key else '❌'}")
        print(f"GitHub token via tta_secrets: {'✅' if github_token else '❌'}")
        print(f"E2B key via tta_secrets: {'✅' if e2b_key else '❌'}")
        print(f"n8n key via tta_secrets: {'✅' if n8n_key else '❌'}")

        # Test config retrieval
        config = get_config()
        print(f"Full config retrieved: {'✅' if config else '❌'}")

    except Exception as e:
        print(f"❌ New approach failed: {e}")

    # Test 3: Platform primitives secrets bridge
    print("\n📋 Test 3: Platform primitives secrets bridge")
    try:
        import platform.primitives.src.tta_dev_primitives.core.secrets as prim_secrets

        gemini_key = prim_secrets.get_gemini_api_key()
        e2b_key = prim_secrets.get_e2b_key()

        print(f"Primitives Gemini key: {'✅' if gemini_key else '❌'}")
        print(f"Primitives E2B key: {'✅' if e2b_key else '❌'}")

    except Exception as e:
        print(f"❌ Platform primitives failed: {e}")

    # Test 4: Vault integration (will fail gracefully if no vault)
    print("\n📋 Test 4: Vault integration test")
    try:
        # Test vault import
        from tta_secrets.vault_client import VaultSecretsClient

        print("✅ Vault client import successful")

        # Test vault client creation (will fail without proper config, but should be graceful)
        try:
            VaultSecretsClient()  # This will fail without proper config
            print("❌ Vault client creation should have failed without proper config")
        except (ValueError, ImportError) as e:
            print(f"✅ Vault client creation failed gracefully as expected: {type(e).__name__}")

    except ImportError as e:
        print(f"❌ Vault import failed (missing hvac?): {e}")

    # Test 5: Production environment detection
    print("\n📋 Test 5: Environment detection")
    try:
        from tta_secrets.manager import SecretsManager

        # Test development (default)
        dev_manager = SecretsManager()
        print(f"Development environment detected: {dev_manager.get_environment()}")
        print(f"Vault enabled in dev: {dev_manager._vault_enabled}")

        # Test production detection
        os.environ["ENVIRONMENT"] = "production"
        prod_manager = SecretsManager()
        print(f"Production environment detected: {prod_manager.get_environment()}")
        print(f"Vault would be enabled in prod: {prod_manager._vault_enabled}")

        # Restore environment
        if "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]

    except Exception as e:
        print(f"❌ Environment detection failed: {e}")

    print("\n" + "=" * 50)
    print("🎉 Secrets integration test complete!")
    print("\nMigration benefits:")
    print("✅ Centralized secret validation")
    print("✅ Format validation (prevents typos)")
    print("✅ Production Vault integration ready")
    print("✅ Graceful fallbacks")
    print("✅ Platform isolation (primitives can import independently)")
