"""
TTA.dev Secrets Management Module

Provides secure handling of API keys and sensitive configuration.
"""

from .loader import load_dotenv_if_exists
from .manager import (
    SecretsManager,
    get_config,
    get_secrets_manager,
    validate_secrets,
)

__all__ = [
    "SecretsManager",
    "get_config",
    "get_secrets_manager",
    "load_dotenv_if_exists",
    "validate_secrets",
]
