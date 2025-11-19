"""
Core secrets management for TTA.dev primitives.

This module provides secure secrets access with proper validation and caching.
It's a wrapper around the root tta_secrets package for platform primitives.
"""

import logging

# Import from root tta_secrets package
try:
    from tta_secrets import (
        get_e2b_key,
        get_gemini_api_key,
        get_github_token,
        get_n8n_key,
        require_env,
    )

    TTA_SECRETS_AVAILABLE = True
except ImportError:
    # Fallback to direct env access if tta_secrets not available
    import os

    TTA_SECRETS_AVAILABLE = False
    logger = logging.getLogger(__name__)

    def get_e2b_key() -> str:
        """Fallback E2B key getter."""
        value = os.getenv("E2B_API_KEY") or os.getenv("E2B_KEY")
        if not value:
            raise ValueError("E2B API key not found in environment variables")
        return value

    def get_gemini_api_key() -> str:
        """Fallback Gemini key getter."""
        value = os.getenv("GEMINI_API_KEY")
        if not value:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        return value

    def get_github_token() -> str:
        """Fallback GitHub token getter."""
        value = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        if not value:
            raise ValueError("GITHUB_PERSONAL_ACCESS_TOKEN not found in environment variables")
        return value

    def get_n8n_key() -> str:
        """Fallback n8n key getter."""
        value = os.getenv("N8N_API_KEY")
        if not value:
            raise ValueError("N8N_API_KEY not found in environment variables")
        return value

    def require_env(key: str) -> str:
        """Fallback require_env function."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} not found")
        return value

    if TTA_SECRETS_AVAILABLE:
        logger.info("Using tta_secrets package for secrets management")
    else:
        logger.warning(
            "tta_secrets package not available, falling back to direct environment access"
        )

__all__ = [
    "get_e2b_key",
    "get_gemini_api_key",
    "get_github_token",
    "get_n8n_key",
    "require_env",
]
