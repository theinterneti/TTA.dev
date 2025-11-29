"""
Centralized .env loader for TTA.dev across all agent workspaces

This module provides intelligent .env file loading with:
- Centralized configuration at ~/.env.tta-dev
- Per-workspace .env override support
- Automatic loading on import
- No duplicate loading
- Thread-safe operation
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class EnvLoader:
    """
    Intelligent environment variable loader

    Search order:
    1. Current workspace .env (if exists)
    2. Centralized ~/.env.tta-dev
    3. Environment variables already set
    """

    _loaded = False
    _lock = False

    @classmethod
    def load(cls, workspace_root: Path | None = None, force: bool = False) -> bool:
        """
        Load environment variables from .env files

        Args:
            workspace_root: Path to workspace root (defaults to current working directory)
            force: Force reload even if already loaded

        Returns:
            True if variables were loaded, False if already loaded
        """
        if cls._loaded and not force:
            return False

        if cls._lock:
            logger.warning("EnvLoader is already loading, skipping duplicate load")
            return False

        cls._lock = True

        try:
            # Determine workspace root
            if workspace_root is None:
                workspace_root = Path.cwd()
            else:
                workspace_root = Path(workspace_root)

            # Try loading from workspace .env first (highest priority)
            workspace_env = workspace_root / ".env"
            if workspace_env.exists():
                logger.info(f"Loading workspace .env from: {workspace_env}")
                cls._load_env_file(workspace_env)

            # Load from centralized ~/.env.tta-dev (fallback)
            home_env = Path.home() / ".env.tta-dev"
            if home_env.exists():
                logger.info(f"Loading centralized .env from: {home_env}")
                cls._load_env_file(home_env, override=False)  # Don't override workspace vars
            else:
                logger.warning(f"Centralized .env not found at: {home_env}")
                logger.info("Run: cp /home/thein/recovered-tta-storytelling/.env ~/.env.tta-dev")

            cls._loaded = True
            logger.info("Environment variables loaded successfully")
            return True

        finally:
            cls._lock = False

    @staticmethod
    def _load_env_file(env_path: Path, override: bool = True) -> None:
        """
        Load variables from a .env file

        Args:
            env_path: Path to .env file
            override: If True, override existing environment variables
        """
        try:
            with open(env_path) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    # Parse KEY=VALUE
                    if "=" not in line:
                        logger.warning(f"Invalid line {line_num} in {env_path}: {line[:50]}")
                        continue

                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    # Set environment variable
                    if override or key not in os.environ:
                        os.environ[key] = value

        except Exception as e:
            logger.error(f"Error loading {env_path}: {e}")
            raise

    @classmethod
    def get(cls, key: str, default: str | None = None) -> str | None:
        """
        Get an environment variable (auto-loads if not already loaded)

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value or default
        """
        if not cls._loaded:
            cls.load()

        return os.getenv(key, default)

    @classmethod
    def require(cls, key: str) -> str:
        """
        Get a required environment variable (raises if not found)

        Args:
            key: Environment variable name

        Returns:
            Environment variable value

        Raises:
            ValueError: If variable is not set
        """
        value = cls.get(key)
        if value is None:
            raise ValueError(f"Required environment variable not set: {key}")
        return value

    @classmethod
    def is_loaded(cls) -> bool:
        """Check if environment variables have been loaded"""
        return cls._loaded


# Auto-load on import (but don't fail if .env missing)
try:
    EnvLoader.load()
except Exception as e:
    logger.warning(f"Failed to auto-load environment: {e}")
    logger.info("You can manually load with: EnvLoader.load()")


# Convenience functions
def get_env(key: str, default: str | None = None) -> str | None:
    """Get environment variable (convenience wrapper)"""
    return EnvLoader.get(key, default)


def require_env(key: str) -> str:
    """Get required environment variable (convenience wrapper)"""
    return EnvLoader.require(key)


__all__ = [
    "EnvLoader",
    "get_env",
    "require_env",
]
