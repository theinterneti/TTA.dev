"""
Langfuse initialization and configuration.

Provides global Langfuse client setup and integration with TTA.dev observability.
"""

import logging
import os

from langfuse import Langfuse

logger = logging.getLogger(__name__)

# Global Langfuse client
_langfuse_client: Langfuse | None = None
_initialized = False


def initialize_langfuse(
    public_key: str | None = None,
    secret_key: str | None = None,
    host: str = "https://cloud.langfuse.com",
    enabled: bool = True,
    debug: bool = False,
    flush_at: int = 15,
    flush_interval: float = 1.0,
) -> bool:
    """Initialize Langfuse client for LLM observability.

    Args:
        public_key: Langfuse public key (or set LANGFUSE_PUBLIC_KEY env var)
        secret_key: Langfuse secret key (or set LANGFUSE_SECRET_KEY env var)
        host: Langfuse host URL (default: cloud.langfuse.com)
        enabled: Enable/disable Langfuse (useful for testing)
        debug: Enable debug logging
        flush_at: Number of events to batch before flushing
        flush_interval: Interval in seconds between flushes

    Returns:
        True if initialization succeeded, False otherwise

    Example:
        >>> initialize_langfuse(
        ...     public_key="pk-lf-...",
        ...     secret_key="sk-lf-...",
        ...     host="https://cloud.langfuse.com"
        ... )
        True
    """
    global _langfuse_client, _initialized

    if _initialized:
        logger.warning("Langfuse already initialized, skipping re-initialization")
        return True

    if not enabled:
        logger.info("Langfuse disabled via configuration")
        return False

    # Get credentials from args or environment
    public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
    host = host or os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        logger.warning(
            "Langfuse credentials not provided. "
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables."
        )
        return False

    try:
        _langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
            debug=debug,
            flush_at=flush_at,
            flush_interval=flush_interval,
        )

        _initialized = True
        logger.info(f"Langfuse initialized successfully (host: {host})")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize Langfuse: {e}")
        return False


def is_langfuse_enabled() -> bool:
    """Check if Langfuse is initialized and enabled.

    Returns:
        True if Langfuse client is available, False otherwise
    """
    return _initialized and _langfuse_client is not None


def get_langfuse_client() -> Langfuse | None:
    """Get the global Langfuse client.

    Returns:
        Langfuse client if initialized, None otherwise
    """
    return _langfuse_client


def shutdown_langfuse() -> None:
    """Shutdown Langfuse and flush remaining events.

    Call this before application exit to ensure all events are sent.
    """
    global _langfuse_client, _initialized

    if _langfuse_client:
        logger.info("Shutting down Langfuse and flushing events...")
        _langfuse_client.flush()
        _langfuse_client = None
        _initialized = False
        logger.info("Langfuse shutdown complete")
