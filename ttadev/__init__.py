"""TTA.dev - Test-Time Augmentation for AI Development."""

__version__ = "0.1.0"

# Observability initialization (explicit opt-in)
from ttadev.observability.auto_instrument import auto_initialize


def initialize_observability() -> None:
    """Initialize observability for TTA.dev.

    This function must be called explicitly by applications that want
    observability (e.g., tracing, metrics) to be enabled.
    """
    auto_initialize()
