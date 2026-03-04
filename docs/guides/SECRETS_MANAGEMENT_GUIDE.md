# Secrets Management Best Practices for TTA.dev

## 🚨 CRITICAL SECURITY ALERT

**Your current .env file contains real API keys that are exposed. Take immediate action!**

## Table of Contents

1. [Immediate Actions Required](#immediate-actions-required)
2. [Current Best Practices (2024-2025)](#current-best-practices-2024-2025)
3. [Local Development Secrets Management](#local-development-secrets-management)
4. [GitHub Actions Integration](#github-actions-integration)
5. [AI Agent Secrets Handling](#ai-agent-secrets-handling)
6. [Production Secrets Management](#production-secrets-management)
7. [Security Monitoring](#security-monitoring)
8. [Migration Guide](#migration-guide)

## Immediate Actions Required

### 1. Rotate Exposed Credentials

**⚠️ URGENT: Rotate these compromised API keys immediately:**

- `GEMINI_API_KEY` (Google AI Studio)
- `GITHUB_PERSONAL_ACCESS_TOKEN`
- `E2B_API_KEY` / `E2B_KEY` (E2B/Code Interpreter)
- `N8N_API_KEY` (n8n API)

### 2. Secure Current .env File

```bash
# Move current .env to temporary location
mv .env .env.backup

# Add .env to gitignore if not present
echo ".env" >> .gitignore
```

### 3. Create Secure Environment Template

```bash
# Create .env.template
cat > .env.template << 'EOF'
# Copy this file to .env and fill in your values
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_pat_here
E2B_API_KEY=your_e2b_key_here
N8N_API_KEY=your_n8n_key_here
CACHE_METRICS_ENABLED=false
CACHE_METRICS_PORT=9090
EOF
```

## Current Best Practices (2024-2025)

### OWASP Top 10 Security Principles

1. **A02:2021 – Cryptographic Failures**: Never hardcode secrets
2. **A07:2021 – Identification and Authentication Failures**: Use strong credential rotation
3. **A10:2021 – Server-Side Request Forgery**: Validate and sanitize all inputs

### 2024-2025 Key Trends

- **Zero-trust architecture** for API access
- **Dynamic secrets** with short expiration times
- **Hardware security modules (HSMs)** for production
- **AI-specific secret management** for LLM/agent integrations

## Local Development Secrets Management

### Python Project Structure

```
TTA.dev/
├── .env                    # Local secrets (NEVER commit)
├── .env.template          # Template for team members
├── .env.local            # Machine-specific overrides
├── .gitignore            # Must include .env
├── secrets/
│   ├── __init__.py
│   └── manager.py        # Centralized secret handling
└── src/
    └── config/
        └── secrets.py    # Secret configuration
```

### Secure Environment Loading

```python
# secrets/manager.py
import os
import base64
from typing import Any, Dict
from pathlib import Path

class SecretsManager:
    """Secure secrets management for TTA.dev"""

    def __init__(self):
        self._secrets: Dict[str, str] = {}
        self._load_secrets()

    def _load_secrets(self) -> None:
        """Load secrets from environment with validation"""
        required_secrets = [
            'GEMINI_API_KEY',
            'GITHUB_PERSONAL_ACCESS_TOKEN',
            'E2B_API_KEY',
            'N8N_API_KEY'
        ]

        for secret_name in required_secrets:
            value = os.getenv(secret_name)
            if not value:
                raise ValueError(f"Required secret {secret_name} not found in environment")

            # Basic validation
            if len(value) < 10:
                raise ValueError(f"Secret {secret_name} appears to be invalid")

            self._secrets[secret_name] = value

    def get_secret(self, key: str, default: str | None = None) -> str:
        """Get secret with proper error handling"""
        return self._secrets.get(key, default)

    def get_api_key(self, service: str) -> str:
        """Get API key for specific service"""
        key_map = {
            'gemini': 'GEMINI_API_KEY',
            'github': 'GITHUB_PERSONAL_ACCESS_TOKEN',
            'e2b': 'E2B_API_KEY',
            'n8n': 'N8N_API_KEY'
        }

        env_key = key_map.get(service.lower())
        if not env_key:
            raise ValueError(f"Unknown service: {service}")

        return self.get_secret(env_key)

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return os.getenv('DEBUG', 'false').lower() == 'true'

    def get_metrics_config(self) -> Dict[str, Any]:
        """Get metrics configuration"""
        return {
            'enabled': os.getenv('CACHE_METRICS_ENABLED', 'false').lower() == 'true',
            'port': int(os.getenv('CACHE_METRICS_PORT', '9090'))
        }
```

### Configuration Integration

```python
# src/config/secrets.py
from secrets.manager import SecretsManager
from functools import lru_cache

secrets_manager = SecretsManager()

@lru_cache()
def get_gemini_api_key() -> str:
    return secrets_manager.get_api_key('gemini')

@lru_cache()
def get_github_token() -> str:
    return secrets_manager.get_api_key('github')

@lru_cache()
def get_e2b_key() -> str:
    return secrets_manager.get_api_key('e2b')

@lru_cache()
def get_n8n_key() -> str:
    return secrets_manager.get_api_key('n8n')

def get_config() -> Dict[str, Any]:
    """Get complete configuration"""
    return {
        'gemini_api_key': get_gemini_api_key(),
        'github_token': get_github_token(),
        'e2b_key': get_e2b_key(),
        'n8n_key': get_n8n_key(),
        'metrics': secrets_manager.get_metrics_config(),
        'debug': secrets_manager.is_debug_mode()
    }
```

## GitHub Actions Integration

### Repository Secrets Setup

```yaml
# .github/workflows/secrets-test.yml
name: Test Secrets Integration

on: [push, pull_request]

jobs:
  test-secrets:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        uv add python-dotenv

    - name: Test secret loading
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        GITHUB_PERSONAL_ACCESS_TOKEN: ${{ secrets.GITHUB_PERSONAL_ACCESS_TOKEN }}
        E2B_API_KEY: ${{ secrets.E2B_API_KEY }}
        N8N_API_KEY: ${{ secrets.N8N_API_KEY }}
        CACHE_METRICS_ENABLED: false
        CACHE_METRICS_PORT: 9090
      run: |
        python -c "from src.config.secrets import get_config; config = get_config(); print('Secrets loaded successfully')"

    - name: Run tests with secrets
      env:
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        GITHUB_PERSONAL_ACCESS_TOKEN: ${{ secrets.GITHUB_PERSONAL_ACCESS_TOKEN }}
        E2B_API_KEY: ${{ secrets.E2B_API_KEY }}
        N8N_API_KEY: ${{ secrets.N8N_API_KEY }}
        CACHE_METRICS_ENABLED: false
        CACHE_METRICS_PORT: 9090
        PYTEST_CURRENT_TEST: true
      run: |
        uv run pytest -v
```

### Setting Repository Secrets

```bash
# Using GitHub CLI (recommended)
gh secret set GEMINI_API_KEY
gh secret set GITHUB_PERSONAL_ACCESS_TOKEN
gh secret set E2B_API_KEY
gh secret set N8N_API_KEY

# Or set multiple secrets from file
cat secrets.json | jq -r 'to_entries | .[] | select(.value != null) | "\(.key)=\(.value)"' | while read line; do
  secret_name=$(echo $line | cut -d= -f1)
  secret_value=$(echo $line | cut -d= -f2-)
  echo $secret_value | gh secret set $secret_name
done
```

### Organization-Level Secrets (For Multiple Repos)

```bash
# Set secrets at organization level
gh secret set --org TTA.dev GEMINI_API_KEY
gh secret set --org TTA.dev E2B_API_KEY
gh secret set --org TTA.dev N8N_API_KEY

# Set visibility for specific repositories
gh secret set --org TTA.dev GEMINI_API_KEY --repos TTA.dev,tta-dev-primitives
```

## AI Agent Secrets Handling

### TTA.dev Specific Patterns

```python
# tta_dev_primitives/src/tta_dev_primitives/security/secure_secrets.py
import os
import logging
from typing import Dict, Any, Optional
from functools import lru_cache

class SecureSecrets:
    """Secure secret handling for TTA.dev primitives"""

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._secrets_cache: Dict[str, str] = {}

    @lru_cache(maxsize=128)
    def get_secret(self, secret_name: str, default: Optional[str] = None) -> str:
        """
        Get secret with proper caching and validation
        """
        # Check cache first
        if secret_name in self._secrets_cache:
            return self._secrets_cache[secret_name]

        # Get from environment
        value = os.getenv(secret_name, default)

        if not value:
            raise ValueError(f"Required secret {secret_name} not found")

        # Validate secret format
        if self._is_api_key(secret_name) and not self._validate_api_key(value):
            raise ValueError(f"Invalid API key format for {secret_name}")

        # Cache the value
        self._secrets_cache[secret_name] = value

        # Log access (no value logging for security)
        self._logger.info(f"Retrieved secret: {secret_name}")

        return value

    def _is_api_key(self, secret_name: str) -> bool:
        """Check if secret is an API key"""
        api_key_patterns = ['_API_KEY', '_TOKEN', '_KEY']
        return any(pattern in secret_name for pattern in api_key_patterns)

    def _validate_api_key(self, value: str) -> bool:
        """Basic API key validation"""
        if len(value) < 10:
            return False

        # Check for common patterns (basic validation)
        if value.startswith(('sk-', 'ghp_', 'e2b_', 'AIza')):
            return True

        # JWT tokens
        if '.' in value and len(value.split('.')) == 3:
            return True

        return True  # Basic validation, could be enhanced

    def mask_secret(self, value: str) -> str:
        """Mask secret for logging"""
        if len(value) <= 8:
            return '*' * len(value)
        return f"{value[:4]}...{value[-4:]}"

    def clear_cache(self):
        """Clear secrets cache for security"""
        self._secrets_cache.clear()
        self._logger.info("Secrets cache cleared")
```

### AI Provider Integration

```python
# tta_dev_primitives/src/tta_dev_primitives/ai/providers.py
from ..security.secure_secrets import SecureSecrets

class GeminiProvider:
    def __init__(self):
        self.secrets = SecureSecrets()
        self.api_key = self.secrets.get_secret('GEMINI_API_KEY')

    def generate_content(self, prompt: str):
        # Use secure API key
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        # ... rest of implementation
```

## Production Secrets Management

### HashiCorp Vault Integration

```python
# production/vault_client.py
import hvac
import os
from typing import Dict, Any

class VaultSecretsClient:
    """HashiCorp Vault client for production secrets"""

    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv('VAULT_URL'),
            token=os.getenv('VAULT_TOKEN'),
            verify=True
        )
        self.mount_point = 'secret'

    def get_secret(self, path: str) -> Dict[str, Any]:
        """Get secret from Vault"""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_point
            )
            return response['data']['data']
        except hvac.exceptions.InvalidPath:
            raise ValueError(f"Secret path {path} not found in Vault")
        except hvac.exceptions.Forbidden:
            raise ValueError("Insufficient permissions to access secret")

    def get_api_key(self, service: str) -> str:
        """Get API key from Vault"""
        secret_path = f"api-keys/{service}"
        secrets = self.get_secret(secret_path)
        return secrets.get('api_key')
```

### Docker Secrets (for containerized deployments)

```dockerfile
# Production Dockerfile
FROM python:3.11-slim

# Install secrets manager
RUN pip install hvac python-dotenv

# Copy application
COPY . /app
WORKDIR /app

# Install dependencies
RUN pip install -r requirements.txt
RUN uv pip install -e .

# Use non-root user
USER app

# Use Docker secrets (mounted at /run/secrets/)
CMD ["python", "-c", "from src.config.secrets_vault import get_config; get_config()"]
```

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  tta-app:
    build: .
    environment:
      - VAULT_URL=http://vault:8200
      - VAULT_TOKEN_FILE=/run/secrets/vault_token
    secrets:
      - vault_token
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        max_attempts: 3

secrets:
  vault_token:
    external: true
```

## Security Monitoring

### Secret Scanning

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on: [push, pull_request]

jobs:
  secret-scan:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Run TruffleHog OSS
      uses: trufflesecurity/trufflehog@main
      with:
        path: ./
        base: main
        head: HEAD
        extra_args: --debug --only-verified
```

### Environment Validation

```python
# security/validate_environment.py
import os
import logging
from typing import List, Set

class EnvironmentValidator:
    """Validate environment setup for security"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.allowed_env_vars: Set[str] = {
            'GEMINI_API_KEY',
            'GITHUB_PERSONAL_ACCESS_TOKEN',
            'E2B_API_KEY',
            'N8N_API_KEY',
            'VAULT_URL',
            'VAULT_TOKEN',
            'CACHE_METRICS_ENABLED',
            'CACHE_METRICS_PORT',
            'DEBUG',
            'ENVIRONMENT'
        }

    def validate(self) -> bool:
        """Validate environment security"""
        issues = []

        # Check for unexpected environment variables
        all_env_vars = set(os.environ.keys())
        unexpected_vars = all_env_vars - self.allowed_env_vars

        if unexpected_vars:
            issues.append(f"Unexpected environment variables: {unexpected_vars}")

        # Check for debug mode in production
        if os.getenv('ENVIRONMENT') == 'production' and os.getenv('DEBUG', 'false').lower() == 'true':
            issues.append("Debug mode enabled in production")

        # Check for missing required secrets in production
        if os.getenv('ENVIRONMENT') == 'production':
            required_secrets = ['GEMINI_API_KEY', 'E2B_API_KEY']
            for secret in required_secrets:
                if not os.getenv(secret):
                    issues.append(f"Required secret {secret} not found in production")

        if issues:
            self.logger.error("Environment validation failed:")
            for issue in issues:
                self.logger.error(f"  - {issue}")
            return False

        self.logger.info("Environment validation passed")
        return True
```

## Migration Guide

### Step 1: Backup Current Setup

```bash
# Create backup
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Create migration log
echo "$(date): Starting secrets migration" > secrets_migration.log
```

### Step 2: Update Code to Use New Pattern

```bash
# Find files that use old patterns
find . -name "*.py" -exec grep -l "\.env\|getenv.*API\|os\.environ" {} \;
```

### Step 3: Test Migration

```python
# Test script
import sys
sys.path.append('.')

try:
    from src.config.secrets import get_config
    config = get_config()
    print("✅ Migration successful - secrets loaded")
    print("✅ Configuration validation passed")
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)
```

### Step 4: Rotate All Compromised Credentials

1. **Gemini API**: Regenerate at <https://makersuite.google.com/app/apikey>
2. **GitHub PAT**: Regenerate in GitHub Settings > Developer settings > Personal access tokens
3. **E2B**: Regenerate at <https://e2b.dev/dashboard>
4. **n8n**: Regenerate in n8n instance settings

## Quick Commands Reference

### Local Development

```bash
# Setup local environment
cp .env.template .env
# Edit .env with your real values

# Validate environment
python security/validate_environment.py

# Test secrets loading
python -c "from src.config.secrets import get_config; print('✅ Working')"
```

### GitHub Actions

```bash
# Set repository secrets
gh secret set GEMINI_API_KEY
gh secret set GITHUB_PERSONAL_ACCESS_TOKEN
gh secret set E2B_API_KEY
gh secret set N8N_API_KEY

# List secrets
gh secret list

# Test workflow
gh workflow run secrets-test.yml
```

### Production Deployment

```bash
# Deploy to production with Vault
export VAULT_ADDR="https://vault.company.com"
export VAULT_TOKEN="your_vault_token"

# Deploy with environment validation
python security/validate_environment.py
python deploy_production.py
```

## Next Steps

1. **Immediate**: Rotate all exposed API keys
2. **This week**: Implement the new secrets management pattern
3. **Next week**: Set up production secrets management (Vault)
4. **Ongoing**: Monitor and validate secret usage

## Security Checklist

- [ ] All API keys rotated
- [ ] .env file secured (.gitignore updated)
- [ ] New secrets management pattern implemented
- [ ] GitHub Actions configured with secrets
- [ ] Local development environment validated
- [ ] Production secrets management setup
- [ ] Security monitoring implemented
- [ ] Team documentation updated

---

**Remember**: Security is an ongoing process, not a one-time setup. Regularly audit and rotate your secrets!


---
**Logseq:** [[TTA.dev/Docs/Secrets_management_guide]]
