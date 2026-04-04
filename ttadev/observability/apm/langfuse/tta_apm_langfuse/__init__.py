"""TTA APM LangFuse integration."""

from tta_apm_langfuse.integration import LangFuseIntegration, auto_instrument

__all__ = ["LangFuseIntegration", "auto_instrument", "get_integration"]
__version__ = "0.1.1"

_integration: "LangFuseIntegration | None" = None
_init_attempted: bool = False


def get_integration() -> "LangFuseIntegration | None":
    """Return the global LangFuseIntegration if env vars are set, else None.

    Auto-initializes on first call. Returns None (never raises) if
    LANGFUSE_PUBLIC_KEY is not set or langfuse package is unavailable.

    Returns:
        Configured :class:`LangFuseIntegration` instance, or ``None`` if
        credentials are absent or initialisation fails.
    """
    global _integration, _init_attempted
    if _init_attempted:
        return _integration
    _init_attempted = True
    import os

    if not os.environ.get("LANGFUSE_PUBLIC_KEY"):
        return None
    try:
        _integration = LangFuseIntegration.from_env()
    except Exception:
        _integration = None
    return _integration
