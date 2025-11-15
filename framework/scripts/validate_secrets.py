#!/usr/bin/env python3
"""
Secrets Validation Script for TTA.dev

This script validates that secrets are properly configured and secure.
Run this to check your environment before development or deployment.

Usage:
    python scripts/validate_secrets.py
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from tta_secrets import validate_secrets, get_config, get_secrets_manager
    import logging

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger(__name__)

    def main():
        """Main validation function"""
        print("🔍 TTA.dev Secrets Validation")
        print("=" * 50)

        # Check if .env file exists (it should NOT be committed)
        env_file = project_root / ".env"
        if env_file.exists():
            print("⚠️  WARNING: .env file found in project root")
            print("   This file should NOT be committed to git!")
            print("   Add '.env' to your .gitignore if not already present")
        else:
            print("✅ No .env file in project root (good!)")

        # Check if .env.template exists
        template_file = project_root / ".env.template"
        if template_file.exists():
            print("✅ .env.template found (good for team setup)")
        else:
            print("❌ .env.template missing (needed for team members)")

        print("\n🔐 Validating secrets configuration...")

        try:
            # Validate secrets
            is_valid = validate_secrets()

            if is_valid:
                print("✅ All required secrets are properly configured")

                # Get and display config (without exposing actual values)
                config = get_config()
                print("\n📋 Configuration Summary:")
                print(f"   Environment: {config.get('environment', 'unknown')}")  # Safe - not sensitive
                print(f"   Debug Mode: {config.get('debug', False\)}")  # Safe - boolean flag
                print(f"   Metrics Enabled: {config.get('metrics', {}).get('enabled', False)}")  # Safe - boolean
                print(f"   Metrics Port: {config.get('metrics', {}).get('port', 'unknown')}")  # Safe - port number

                # Test individual API keys (without printing values)
                manager = get_secrets_manager()
                services = ['gemini', 'github', 'e2b', 'n8n']

                print("\n🔑 API Key Validation:")
                for service in services:
                    try:
                        key = manager.get_api_key(service)
                        # Mask the key for display
                        masked_key = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "*" * 8  # Always mask fully if short
                        print(f"   ✅ {service.upper()}: {masked_key} (valid format)")
                    except Exception as e:
                        print(f"   ❌ {service.upper()}: {str(e)}")

                print("\n🎉 SUCCESS: All secrets validation passed!")
                return 0

            else:
                print("❌ FAILED: Some secrets are missing or invalid")
                print("\n📝 Next steps:")
                print("   1. Copy .env.template to .env")
                print("   2. Fill in your actual API keys")
                print("   3. Run this script again")
                return 1

        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            print("\n📝 Troubleshooting:")
            print("   1. Make sure you have a .env file with all required keys")
            print("   2. Check that all API keys are properly formatted")
            print("   3. Ensure no secrets are logged or exposed")
            return 1

    if __name__ == "__main__":
        exit_code = main()
        sys.exit(exit_code)

except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure you're running this from the TTA.dev project root")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
    sys.exit(1)
