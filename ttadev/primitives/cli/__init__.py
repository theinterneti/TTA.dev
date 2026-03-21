"""TTA.dev CLI Module.

Command-line interface for TTA.dev primitives.

Usage:
    tta-dev analyze <file>
    tta-dev recommend <file>
    tta-dev primitives
    tta-dev docs <primitive>
    tta-dev serve
"""

from ttadev.primitives.cli.app import app

__all__ = ["app"]
