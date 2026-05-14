"""TTA.dev - Test-Time Augmentation for AI Development."""

__version__ = "0.1.0"


def initialize_observability() -> None:
    """Initialize observability for TTA.dev.

    Call this once at application startup to enable tracing and metrics.
    Safe to call multiple times; subsequent calls are no-ops.

    Example::

        import ttadev
        ttadev.initialize_observability()
    """
    from ttadev.observability.auto_instrument import auto_initialize

    auto_initialize()


# Lazy imports — avoid pulling in litellm, aiohttp, and other heavy
# deps until the caller actually accesses the subpackage.
def __getattr__(name: str):
    if name == "observability":
        import ttadev.observability as _obs
        return _obs
    if name == "primitives":
        import ttadev.primitives as _primitives
        return _primitives
    if name == "cli":
        import ttadev.cli as _cli
        return _cli
    if name == "workflows":
        import ttadev.workflows as _workflows
        return _workflows
    if name == "control_plane":
        import ttadev.control_plane as _cp
        return _cp
    if name == "ui":
        import ttadev.ui as _ui
        return _ui
    raise AttributeError(f"module 'ttadev' has no attribute {name!r}")
