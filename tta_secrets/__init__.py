"""
TTA.dev Secrets Management Package

This package provides secure secrets management for TTA.dev applications.
It implements current security best practices for 2024-2025.

Features:
- Centralized .env loading from ~/.env.tta-dev
- Per-workspace .env override support
- Automatic loading on import
- Secure secrets validation and caching
"""

# Auto-load environment variables first
from .loader import EnvLoader, get_env, require_env
from .manager import (
    SecretsManager,
    get_config,
    get_e2b_key,
    get_gemini_api_key,
    get_github_token,
    get_n8n_key,
    get_secrets_manager,
    validate_secrets,
)

__all__ = [
    # Environment loading
    "EnvLoader",
    "get_env",
    "require_env",
    # Secrets management
    "SecretsManager",
    "get_secrets_manager",
    "get_gemini_api_key",
    "get_github_token",
    "get_e2b_key",
    "get_n8n_key",
    "get_config",
    "validate_secrets",
]

# Version info
__version__ = "1.1.0"
