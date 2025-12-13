# SecretsRequestPrimitive Usage Guide

## Overview

The `SecretsRequestPrimitive` demonstrates **safe, correct patterns** for TTA.dev secrets management. This is an **educational primitive** only - never use in production.

## Learning Goals

Agents using this primitive will learn:
- ✅ How to request secrets using SecretsManager
- ✅ Proper error handling for missing secrets
- ✅ Why secret values should never be returned
- ✅ How Vault vs environment detection works
- ✅ Security best practices for TTA.dev applications

## Usage Example

```python
from examples.secrets_request_primitive_demo import SecretsRequestPrimitive
from tta_dev_primitives import WorkflowContext

# Create primitive for the secrets you need
secrets_req = SecretsRequestPrimitive([
    "GEMINI_API_KEY",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "E2B_API_KEY",
    "N8N_API_KEY"
])

# Execute in workflow context
context = WorkflowContext()
result = await secrets_req.execute({"action": "request_secrets"}, context)

# Result shows availability, never values:
{
    "secrets_status": {
        "GEMINI_API_KEY": "loaded",
        "GITHUB_PERSONAL_ACCESS_TOKEN": "missing",
        "E2B_API_KEY": "loaded",
        "N8N_API_KEY": "missing"
    },
    "total_requested": 4,
    "total_loaded": 2,
    "total_missing": 2,
    "vault_enabled": False,
    "environment": "development",
    "message": "Secrets requested successfully (values not returned for security)"
}
```

## Agent Best Practices Demonstrated

### 1. Use SecretsManager, Never os.getenv()

```python
# ❌ BAD - Direct environment access
gemini_key = os.getenv("GEMINI_API_KEY")

# ✅ GOOD - Use SecretsManager
from tta_secrets import get_gemini_api_key
gemini_key = get_gemini_api_key()  # Validates and caches automatically
```

### 2. Handle Missing Secrets Gracefully

```python
# ❌ BAD - Will crash if missing
api_key = os.getenv("API_KEY")

# ✅ GOOD - Handle missing secrets
try:
    api_key = get_secrets_manager().get_secret("API_KEY")
except ValueError as e:
    print(f"API_KEY not configured: {e}")
    # Continue with fallback or exit gracefully
```

### 3. Never Return Secret Values

```python
# ❌ BAD - Security risk
def get_secret_endpoint():
    return {"secret": os.getenv("MY_SECRET")}  # Leak!

# ✅ GOOD - Return status only
def check_secret_status():
    try:
        get_secrets_manager().get_secret("MY_SECRET")
        return {"status": "available"}
    except ValueError:
        return {"status": "missing"}
```

### 4. Use Vault in Production

```python
# Automatically detects environment
manager = get_secrets_manager()

if manager._vault_enabled:
    print("Using HashiCorp Vault for secrets")
else:
    print("Using environment variables")
```

## Complete Learning Exercise

Run the demo to see all concepts in action:

```bash
cd /path/to/tta.dev
uv run python examples/secrets_request_primitive_demo.py
```

Expected output shows:
- Secret availability status
- Vault vs environment detection
- Proper error handling
- Security best practices
- Agent learning points

## Security Warning

This primitive is for **education only**. Production code should use the underlying `tta_secrets` functions directly, never this demonstration primitive.

The primitive teaches patterns but does not provide actual secret access - use `tta_secrets.get_*()` functions in real workflows.


---
**Logseq:** [[TTA.dev/Data/Examples/Secrets_request_primitive_usage]]
