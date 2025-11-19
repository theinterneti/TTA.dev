"""
Secure secrets management for TTA.dev

This module provides centralized, secure handling of API keys and sensitive configuration.
It follows 2024-2025 best practices including:
- Environment variable validation
- API key format validation
- Secure caching
- HashiCorp Vault integration
- No secret logging
"""

import logging
import os
from typing import Any

try:
    from .vault_client import VaultSecretsClient

    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False


class SecretsManager:
    """
    Secure secrets management for TTA.dev applications

    This class provides:
    - Validation of required secrets
    - API key format validation
    - Secure caching of secrets
    - HashiCorp Vault integration for production
    - Proper error handling
    - No secret logging (security best practice)

    In production environments (ENVIRONMENT=production), this will attempt
    to use HashiCorp Vault if available, falling back to environment variables.
    """

    def __init__(self, enable_vault: bool | None = None):
        self._logger = logging.getLogger(__name__)
        self._secrets_cache: dict[str, str] = {}
        self._secrets_loaded = False
        self._vault_client: VaultSecretsClient | None = None

        # Determine if Vault should be enabled
        self._vault_enabled = (
            enable_vault if enable_vault is not None else self._should_use_vault()
        )

        # Initialize Vault client if needed
        if self._vault_enabled and VAULT_AVAILABLE:
            try:
                self._vault_client = VaultSecretsClient()
                self._logger.info("Vault client initialized for production secrets")
            except Exception as e:
                self._logger.warning(
                    f"Failed to initialize Vault client, falling back to environment: {e}"
                )
                self._vault_enabled = False

    def _should_use_vault(self) -> bool:
        """Determine if Vault should be used based on environment and availability."""
        # Use Vault in production if available
        environment = os.getenv("ENVIRONMENT", "development").lower()
        return environment == "production" and VAULT_AVAILABLE

    def _load_secrets(self) -> None:
        """Load and validate all required secrets from environment or Vault"""
        if self._secrets_loaded:
            return

        required_secrets = [
            "GEMINI_API_KEY",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "E2B_API_KEY",
            "N8N_API_KEY",
        ]

        missing_secrets = []
        invalid_secrets = []

        for secret_name in required_secrets:
            value = self._get_secret_value(secret_name)
            if not value:
                missing_secrets.append(secret_name)
                continue

            # Validate secret format
            if not self._validate_secret_format(secret_name, value):
                invalid_secrets.append(secret_name)
                continue

            self._secrets_cache[secret_name] = value

        if missing_secrets:
            source = "Vault" if self._vault_enabled else "environment"
            raise ValueError(
                f"Required secrets not found in {source}: {missing_secrets}"
            )

        if invalid_secrets:
            raise ValueError(f"Invalid secret formats: {invalid_secrets}")

        self._secrets_loaded = True
        source = "Vault" if self._vault_enabled else "environment"
        self._logger.info(f"All required secrets validated from {source}")

    def _get_secret_value(self, key: str) -> str | None:
        """
        Get secret value from Vault first, then environment fallback.

        Args:
            key: Secret/environment variable name

        Returns:
            The secret value or None if not found
        """
        # Try Vault first if enabled
        if self._vault_enabled and self._vault_client:
            # Map environment variable names to Vault paths
            vault_path_map = {
                "GEMINI_API_KEY": ("api-keys/gemini", "GEMINI_API_KEY"),
                "GITHUB_PERSONAL_ACCESS_TOKEN": (
                    "api-keys/github",
                    "GITHUB_PERSONAL_ACCESS_TOKEN",
                ),
                "E2B_API_KEY": ("api-keys/e2b", "E2B_API_KEY"),
                "N8N_API_KEY": ("api-keys/n8n", "N8N_API_KEY"),
            }

            if key in vault_path_map:
                vault_path, vault_key = vault_path_map[key]
                try:
                    value = self._vault_client.get_secret_value(vault_path, vault_key)
                    self._logger.debug(f"Retrieved {key} from Vault")
                    return value
                except (ValueError, RuntimeError):
                    # Vault failed, fall through to environment
                    self._logger.debug(
                        f"Vault retrieval failed for {key}, trying environment"
                    )

        # Environment fallback
        return os.getenv(key)

    def _validate_secret_format(self, secret_name: str, value: str) -> bool:
        """
        Validate the format of various API keys and secrets

        Args:
            secret_name: Name of the secret for context
            value: The secret value to validate

        Returns:
            True if format appears valid, False otherwise
        """
        if not value or len(value) < 10:
            return False

        # Gemini API keys start with "AIza"
        if secret_name == "GEMINI_API_KEY":
            return value.startswith("AIza")

        # GitHub Personal Access Tokens start with "ghp_"
        if secret_name == "GITHUB_PERSONAL_ACCESS_TOKEN":
            return value.startswith("ghp_")

        # E2B API keys start with "e2b_"
        if secret_name == "E2B_API_KEY":
            return value.startswith("e2b_")

        # n8n API keys are JWT tokens (base64 encoded JSON with dots)
        if secret_name == "N8N_API_KEY":
            # Basic JWT validation: should have 3 parts separated by dots
            parts = value.split(".")
            return len(parts) == 3 and len(parts[0]) > 0

        return True  # Unknown secret type, basic length check only

    def get_secret(self, key: str, default: str | None = None) -> str:
        """
        Get a secret from the cache or environment

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            The secret value or default

        Raises:
            ValueError: If secret is required but not found
        """
        self._load_secrets()

        if key in self._secrets_cache:
            return self._secrets_cache[key]

        # Check environment as fallback
        value = os.getenv(key, default)
        if value:
            return value

        if default is None:
            raise ValueError(f"Required secret {key} not found in environment")

        return default

    def get_api_key(self, service: str) -> str:
        """
        Get API key for a specific service

        Args:
            service: Service name (gemini, github, e2b, n8n)

        Returns:
            The API key for the service

        Raises:
            ValueError: If service is unknown or key not found
        """
        service_mapping = {
            "gemini": "GEMINI_API_KEY",
            "github": "GITHUB_PERSONAL_ACCESS_TOKEN",
            "e2b": "E2B_API_KEY",
            "n8n": "N8N_API_KEY",
        }

        env_key = service_mapping.get(service.lower())
        if not env_key:
            available_services = list(service_mapping.keys())
            raise ValueError(
                f"Unknown service '{service}'. Available services: {available_services}"
            )

        return self.get_secret(env_key)

    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        debug_value = os.getenv("DEBUG", "false").lower()
        return debug_value in ("true", "1", "yes", "on")

    def get_environment(self) -> str:
        """Get current environment (development, staging, production)"""
        return os.getenv("ENVIRONMENT", "development")

    def get_metrics_config(self) -> dict[str, Any]:
        """Get metrics configuration"""
        return {
            "enabled": os.getenv("CACHE_METRICS_ENABLED", "false").lower() == "true",
            "port": int(os.getenv("CACHE_METRICS_PORT", "9090")),
        }

    def validate_environment(self) -> bool:
        """
        Validate current environment configuration

        Returns:
            True if environment is valid, False otherwise
        """
        try:
            self._load_secrets()
            return True
        except ValueError as e:
            self._logger.error(f"Environment validation failed: {e}")
            return False

    def clear_cache(self) -> None:
        """Clear secrets cache (useful for testing or security resets)"""
        self._secrets_cache.clear()
        self._secrets_loaded = False
        self._logger.info("Secrets cache cleared")

    def _get_cached_secret(self, key: str) -> str:
        """Get secret (caching handled at higher level)"""
        return self.get_secret(key)


# Global instance
_secrets_manager: SecretsManager | None = None


def get_secrets_manager() -> SecretsManager:
    """Get global secrets manager instance"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_gemini_api_key() -> str:
    """Get Gemini API key with caching"""
    return get_secrets_manager().get_api_key("gemini")


def get_github_token() -> str:
    """Get GitHub token with caching"""
    return get_secrets_manager().get_api_key("github")


def get_e2b_key() -> str:
    """Get E2B API key with caching"""
    return get_secrets_manager().get_api_key("e2b")


def get_n8n_key() -> str:
    """Get n8n API key with caching"""
    return get_secrets_manager().get_api_key("n8n")


def get_config() -> dict[str, Any]:
    """
    Get complete configuration dictionary

    Returns:
        Dictionary with all configuration values
    """
    manager = get_secrets_manager()

    return {
        "gemini_api_key": get_gemini_api_key(),
        "github_token": get_github_token(),
        "e2b_key": get_e2b_key(),
        "n8n_key": get_n8n_key(),
        "metrics": manager.get_metrics_config(),
        "debug": manager.is_debug_mode(),
        "environment": manager.get_environment(),
    }


def validate_secrets() -> bool:
    """
    Validate that all required secrets are available

    Returns:
        True if all secrets are valid, False otherwise
    """
    return get_secrets_manager().validate_environment()
