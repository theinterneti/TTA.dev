"""
TTA.dev Secrets Management Package

This package provides secure secrets management for TTA.dev applications.
It implements current security best practices for 2024-2025.
"""

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
__version__ = "1.0.0"
