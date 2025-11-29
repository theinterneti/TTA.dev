#!/usr/bin/env python3
"""
SecretsRequestPrimitive - Educational Primitive for Proper Secrets Management

THIS IS FOR DEMONSTRATION/LEARNING ONLY - NOT FOR PRODUCTION SECURITY

This primitive demonstrates how agents should properly use TTA.dev's secrets management system.
It shows the correct patterns for:
- Requesting secrets from the SecretsManager
- Handling missing secrets gracefully
- Never returning actual secret values (security best practice)
- Detecting vault vs environment configurations

Usage for agents learning secrets management:

```python
from examples.secrets_request_primitive_demo import SecretsRequestPrimitive
from tta_dev_primitives import WorkflowContext

# Create primitive with the secrets you need
secrets_req = SecretsRequestPrimitive([
    "GEMINI_API_KEY",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "E2B_API_KEY"
])

# Execute to request secrets
context = WorkflowContext()
result = await secrets_req.execute({"action": "request_secrets"}, context)

print(result)
# {
#   "secrets_status": {
#     "GEMINI_API_KEY": "loaded",
#     "GITHUB_PERSONAL_ACCESS_TOKEN": "missing",
#     "E2B_API_KEY": "loaded"
#   },
#   "vault_enabled": False,
#   "environment": "development",
#   "message": "Secrets requested successfully (values not returned for security)"
# }
```
"""

import sys
from pathlib import Path
from typing import Any

# Add project root to path to import tta_secrets
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive

from tta_secrets import get_secrets_manager


class SecretsRequestPrimitive(WorkflowPrimitive):
    """
    Educational primitive demonstrating proper TTA.dev secrets management usage.

    ⛔️ SECURITY WARNING ⛔️
    THIS IS FOR EDUCATION ONLY - DO NOT USE IN PRODUCTION WORKFLOWS

    This primitive teaches agents how to:
    ✅ Use SecretsManager correctly
    ✅ Handle secret lookup failures gracefully
    ✅ Validate secrets are loaded
    ✅ Format results safely (never expose secret values)
    ✅ Detect vault vs environment configurations
    """

    def __init__(self, secret_names: list[str]):
        """
        Initialize secrets request primitive.

        Args:
            secret_names: List of environment variable names to request
                        (e.g., ["GEMINI_API_KEY", "GITHUB_TOKEN"])
        """
        super().__init__()
        self.secret_names = secret_names

    async def execute(self, input_data: dict[str, Any], context: WorkflowContext) -> dict[str, Any]:
        """
        Request specified secrets from the secrets management system.

        This demonstrates the CORRECT way to access secrets in TTA.dev applications.

        Args:
            input_data: Should contain {"action": "request_secrets"} for clarity
            context: Workflow context (passed automatically by composition operators)

        Returns:
            Dictionary with secret availability status (values NEVER returned)
        """
        # Get the secrets manager instance (global singleton pattern)
        manager = get_secrets_manager()

        # Track results for each requested secret
        secrets_status = {}

        for secret_name in self.secret_names:
            try:
                # This is the CORRECT way to get secrets - they get validated and cached
                # 🔒 Security: We never return the actual secret values!
                manager.get_secret(secret_name)
                secrets_status[secret_name] = "loaded"
            except ValueError as e:
                # Handle missing secrets gracefully
                secrets_status[secret_name] = "missing"
                context.data[f"error_{secret_name}"] = str(e)

        # Build response with configuration info (for learning purposes)
        response = {
            "secrets_status": secrets_status,
            "total_requested": len(self.secret_names),
            "total_loaded": sum(1 for status in secrets_status.values() if status == "loaded"),
            "total_missing": sum(1 for status in secrets_status.values() if status == "missing"),
            "vault_enabled": getattr(manager, "_vault_enabled", False),
            "environment": manager.get_environment(),
            "message": "Secrets requested successfully (values not returned for security)",
        }

        # Add helpful agent guidance to context
        context.data["secrets_demo_completed"] = True
        context.data["secrets_loaded_count"] = response["total_loaded"]

        return response


# Demonstration function for agents learning the secrets system
async def demonstrate_secrets_management():
    """
    Complete demonstration of TTA.dev secrets management for learning purposes.

    This shows agents how to properly request and validate secrets.
    """
    print("🔐 TTA.dev Secrets Management Demonstration")
    print("=" * 50)

    # Common secrets agents might need
    common_secrets = [
        "GEMINI_API_KEY",
        "GITHUB_PERSONAL_ACCESS_TOKEN",
        "E2B_API_KEY",
        "N8N_API_KEY",
    ]

    # Create the demonstration primitive
    secrets_request = SecretsRequestPrimitive(common_secrets)

    # Create workflow context
    context = WorkflowContext(
        correlation_id="demo-secrets-request", data={"demo_purpose": "agent_education"}
    )

    print(f"📋 Requesting {len(common_secrets)} secrets.")



    print("\n🔍 Executing secrets request...")

    # Execute the primitive (this demonstrates the CORRECT usage pattern)
    try:
        result = await secrets_request.execute({"action": "request_secrets"}, context)

        print("\n✅ Secrets request completed!")
        print(f"Environment: {result['environment']}")
        print(f"Vault enabled: {result['vault_enabled']}")
        print(f"Secrets loaded: {result['total_loaded']}/{result['total_requested']}")

        print("\n📊 Secret Status:")
        print(f"  ✅ Loaded: {result['total_loaded']}")
        print(f"  ❌ Missing: {result['total_missing']}")
        print(f"  🔢 Total Requested: {result['total_requested']}")

        print("\n💡 Agent Learning Points:")
        print("  • Always use SecretsManager, never os.getenv() directly")

    except Exception as e:
        print(f"\n❌ Secrets request failed: {e}")
        print("\n💡 This is normal if secrets aren't configured in your environment")
        print("   Use this to learn proper error handling patterns!")
        return None


if __name__ == "__main__":
    # Run the demonstration when executed directly
    import asyncio

    asyncio.run(demonstrate_secrets_management())
