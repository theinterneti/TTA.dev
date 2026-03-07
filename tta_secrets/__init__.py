"""
TTA.dev Secrets Management Module

Provides secure handling of API keys and sensitive configuration.
"""

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
    "EnvLoader",
    "SecretsManager",
    "get_config",
    "get_env",
    "get_secrets_manager",
    "require_env",
    "validate_secrets",
]
