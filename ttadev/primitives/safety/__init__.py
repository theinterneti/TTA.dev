"""Safety primitives for severity-based routing and human escalation.

from ttadev.primitives.safety import SafetyGatePrimitive, SeverityLevel
"""

from .safety_gate_primitive import (
    SafetyGateEscalatedError,
    SafetyGatePrimitive,
    SeverityLevel,
)

__all__ = [
    "SafetyGatePrimitive",
    "SafetyGateEscalatedError",
    "SeverityLevel",
]
