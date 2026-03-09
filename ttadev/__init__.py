"""TTA.dev - Test-Time Augmentation for AI Development."""

__version__ = "0.1.0"

# Auto-initialize observability on import
from ttadev.observability.auto_instrument import auto_initialize

auto_initialize()
