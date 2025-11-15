"""TTA Rebuild - Therapeutic Through Artistry.

AI-powered collaborative storytelling with therapeutic benefits.
"""

__version__ = "0.1.0"

from tta_rebuild.core import (
    ExecutionError,
    Metaconcept,
    MetaconceptCategory,
    MetaconceptRegistry,
    TTAContext,
    TTAPrimitive,
    TTAPrimitiveError,
    ValidationError,
)

__all__ = [
    "ExecutionError",
    "Metaconcept",
    "MetaconceptCategory",
    "MetaconceptRegistry",
    "TTAContext",
    "TTAPrimitive",
    "TTAPrimitiveError",
    "ValidationError",
    "__version__",
]
