"""TTA.dev - Test-Time Augmentation for AI Development."""

__version__ = "0.1.0"

# Observability initialization (explicit opt-in)
from ttadev.observability.auto_instrument import auto_initialize


def initialize_observability() -> None:
    """Initialize observability for TTA.dev.

    Call this once at application startup to enable tracing and metrics.
    Safe to call multiple times; subsequent calls are no-ops.

    Example::

        import ttadev
        ttadev.initialize_observability()
    """
    auto_initialize()
