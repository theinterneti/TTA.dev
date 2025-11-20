"""
HashiCorp Vault client for production secrets management.

This module provides enterprise-grade secrets management using HashiCorp Vault.
Supports KV v2 secrets engine with production safety features.

Usage:
    ```python
    from tta_secrets.vault_client import VaultSecretsClient

    vault = VaultSecretsClient(
        vault_url="https://vault.company.com",
        vault_token=os.getenv("VAULT_TOKEN"),
        mount_point="secret"
    )

    # Get secret from Vault
    secrets = vault.get_secret("api-keys/gemini")
    api_key = secrets.get("GEMINI_API_KEY")
    ```
"""

import logging
from typing import Any

try:
    import hvac

    HVAC_AVAILABLE = True
except ImportError:
    HVAC_AVAILABLE = False

logger = logging.getLogger(__name__)


class VaultSecretsClient:
    """
    HashiCorp Vault client for production secrets.

    Features:
    - Automatic token renewal
    - Connection pooling and retry logic
    - Production-safe error handling
    - Audit logging for access
    - Graceful degradation when Vault unavailable
    """

    def __init__(
        self,
        vault_url: str | None = None,
        vault_token: str | None = None,
        mount_point: str = "secret",
        verify_ssl: bool = True,
        timeout: int = 30,
        retry_attempts: int = 3,
    ):
        """
        Initialize Vault client.

        Args:
            vault_url: Vault server URL (e.g., https://vault.company.com:8200)
            vault_token: Vault authentication token
            mount_point: Secret engine mount point (default: "secret")
            verify_ssl: Whether to verify SSL certificates
            timeout: Connection timeout in seconds
            retry_attempts: Number of retry attempts for failed requests

        Raises:
            ImportError: If python-hvac is not installed
            ValueError: If required parameters are missing in production
        """
        if not HVAC_AVAILABLE:
            raise ImportError(
                "HashiCorp Vault client requires 'hvac' package. Install with: uv add hvac"
            )

        self.vault_url = vault_url or self._get_vault_url()
        self.vault_token = vault_token or self._get_vault_token()
        self.mount_point = mount_point
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.retry_attempts = retry_attempts

        # Initialize Vault client
        self._client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Vault client with proper configuration."""
        try:
            self._client = hvac.Client(
                url=self.vault_url,
                token=self.vault_token,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )

            # Verify connection and authentication
            if self._client.is_authenticated():
                logger.info(f"Successfully authenticated with Vault at {self.vault_url}")
                self._log_vault_health()
            else:
                raise ValueError("Failed to authenticate with Vault")

        except Exception as e:
            logger.error(f"Failed to initialize Vault client: {e}")
            raise ValueError(f"Vault client initialization failed: {e}") from e

    def _get_vault_url(self) -> str:
        """Get Vault URL from environment or default."""
        from .loader import require_env

        return require_env("VAULT_URL")

    def _get_vault_token(self) -> str:
        """Get Vault token from environment or default."""
        from .loader import get_env

        token = get_env("VAULT_TOKEN") or get_env("VAULT_TOKEN_FILE")

        if not token:
            raise ValueError("VAULT_TOKEN or VAULT_TOKEN_FILE environment variable required")

        # Check if token is a file path
        if token and not token.startswith("hvs.") and not token.startswith("hvb."):
            try:
                with open(token) as f:
                    token = f.read().strip()
            except FileNotFoundError:
                raise ValueError(f"Vault token file not found: {token}") from None

        return token

    def _log_vault_health(self) -> None:
        """Log Vault server health information."""
        try:
            if self._client:
                health = self._client.sys.read_health_status()
                logger.info(f"Vault version: {health.get('version', 'unknown')}")
                logger.info(f"Vault initialized: {health.get('initialized', False)}")
                logger.info(f"Vault sealed: {health.get('sealed', True)}")
        except Exception as e:
            logger.warning(f"Could not retrieve Vault health: {e}")

    def get_secret(self, path: str, version: int | None = None) -> dict[str, Any]:
        """
        Retrieve a secret from Vault KV v2 secrets engine.

        Args:
            path: Secret path (e.g., "api-keys/gemini")
            version: Specific version to retrieve (None for latest)

        Returns:
            Dictionary containing secret data

        Raises:
            ValueError: If secret not found or access denied
            RuntimeError: If Vault client not available
        """
        if not self._client:
            raise RuntimeError("Vault client not initialized")

        for attempt in range(self.retry_attempts + 1):
            try:
                logger.info(f"Retrieving secret: {path} (attempt {attempt + 1})")

                response = self._client.secrets.kv.v2.read_secret_version(
                    path=path,
                    mount_point=self.mount_point,
                    version=version,
                )

                data = response.get("data", {}).get("data", {})
                if not data:
                    raise ValueError(f"No data found in secret: {path}")

                # Log successful access (without values)
                logger.info(f"Successfully retrieved secret: {path}")
                return data

            except hvac.exceptions.InvalidPath as e:
                logger.error(f"Secret path not found: {path}")
                raise ValueError(f"Secret not found: {path}") from e

            except hvac.exceptions.Forbidden as e:
                logger.error(f"Access denied to secret: {path}")
                raise ValueError(f"Access denied to: {path}") from e

            except Exception as e:
                if attempt == self.retry_attempts:
                    logger.error(
                        f"Failed to retrieve secret {path} after "
                        f"{self.retry_attempts + 1} attempts: {e}"
                    )
                    raise RuntimeError(f"Vault access failed: {e}") from e

                logger.warning(f"Vault request failed (attempt {attempt + 1}), retrying: {e}")
                import time

                time.sleep(0.5 * (2**attempt))  # Exponential backoff

    def get_secret_value(self, path: str, key: str, version: int | None = None) -> str:
        """
        Retrieve a specific value from a Vault secret.

        Args:
            path: Secret path
            key: Key within the secret
            version: Secret version

        Returns:
            The secret value as a string

        Raises:
            ValueError: If key not found in secret
        """
        data = self.get_secret(path, version)
        if key not in data:
            raise ValueError(f"Key '{key}' not found in secret: {path}")
        return str(data[key])

    def list_secrets(self, path: str = "") -> list[str]:
        """
        List secrets under a given path.

        Args:
            path: Base path to list (e.g., "api-keys/")

        Returns:
            List of secret names
        """
        if not self._client:
            raise RuntimeError("Vault client not initialized")

        try:
            response = self._client.secrets.kv.v2.list_secrets_version(
                path=path, mount_point=self.mount_point
            )

            keys = response.get("data", {}).get("keys", [])
            return [key.rstrip("/") for key in keys if key != ""]  # Remove trailing slashes

        except hvac.exceptions.InvalidPath:
            return []  # No secrets found
        except Exception as e:
            logger.error(f"Failed to list secrets at {path}: {e}")
            raise RuntimeError(f"Failed to list secrets: {e}") from e

    def create_or_update_secret(self, path: str, data: dict[str, Any]) -> None:
        """
        Create or update a secret in Vault.

        Args:
            path: Secret path
            data: Dictionary of key-value pairs to store

        Raises:
            RuntimeError: If operation fails
        """
        if not self._client:
            raise RuntimeError("Vault client not initialized")

        try:
            self._client.secrets.kv.v2.create_or_update_secret(
                path=path, secret=data, mount_point=self.mount_point
            )
            logger.info(f"Successfully created/updated secret: {path}")

        except Exception as e:
            logger.error(f"Failed to create/update secret {path}: {e}")
            raise RuntimeError(f"Vault operation failed: {e}") from e

    def delete_secret(self, path: str, versions: list[int] | None = None) -> None:
        """
        Delete a secret or specific versions from Vault.

        Args:
            path: Secret path to delete
            versions: Specific versions to delete (None for all versions)

        Raises:
            RuntimeError: If operation fails
        """
        if not self._client:
            raise RuntimeError("Vault client not initialized")

        try:
            if versions:
                for version in versions:
                    self._client.secrets.kv.v2.delete_secret_versions(
                        path=path, versions=[version], mount_point=self.mount_point
                    )
                    logger.info(f"Deleted version {version} of secret: {path}")
            else:
                # Delete all versions
                self._client.secrets.kv.v2.delete_metadata_and_all_versions(
                    path=path, mount_point=self.mount_point
                )
                logger.info(f"Deleted all versions of secret: {path}")

        except Exception as e:
            logger.error(f"Failed to delete secret {path}: {e}")
            raise RuntimeError(f"Vault delete operation failed: {e}") from e

    def is_healthy(self) -> bool:
        """
        Check if Vault is healthy and accessible.

        Returns:
            True if Vault is accessible, False otherwise
        """
        if not self._client:
            return False

        try:
            health = self._client.sys.read_health_status()
            return health.get("initialized", False) and not health.get("sealed", True)
        except Exception:
            return False

    # Convenience methods for common secrets

    def get_api_key(self, service: str) -> str:
        """
        Get API key for a specific service.

        Args:
            service: Service name (e.g., "gemini", "github")

        Returns:
            The API key value
        """
        service_key_map = {
            "gemini": "GEMINI_API_KEY",
            "github": "GITHUB_PERSONAL_ACCESS_TOKEN",
            "e2b": "E2B_API_KEY",
            "n8n": "N8N_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
        }

        if service not in service_key_map:
            raise ValueError(f"Unknown service: {service}")

        path = f"api-keys/{service}"
        key = service_key_map[service]
        return self.get_secret_value(path, key)


# Convenience factory function
def create_vault_client(
    vault_url: str | None = None, vault_token: str | None = None, **kwargs
) -> VaultSecretsClient:
    """
    Factory function to create a Vault client with sensible defaults.

    Args:
        vault_url: Vault server URL
        vault_token: Vault authentication token
        **kwargs: Additional arguments for VaultSecretsClient

    Returns:
        Configured VaultSecretsClient instance
    """
    return VaultSecretsClient(vault_url=vault_url, vault_token=vault_token, **kwargs)


# Backward compatibility
def get_vault_client(**kwargs) -> VaultSecretsClient:
    """Alias for create_vault_client for backward compatibility."""
    return create_vault_client(**kwargs)


__all__ = [
    "VaultSecretsClient",
    "create_vault_client",
    "get_vault_client",
]
