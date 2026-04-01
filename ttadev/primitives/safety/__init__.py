"""Safety primitives for severity-based routing and human escalation.

from ttadev.primitives.safety import SafetyGatePrimitive, SeverityLevel
"""

from .safety_gate_primitive import (
    SafetyGateEscalatedError,
    SafetyGatePrimitive,
    SafetyViolationError,
    SeverityLevel,
    ThreatLevel,
)

__all__ = [
    "SafetyGatePrimitive",
    "SafetyGateEscalatedError",
    "SafetyViolationError",
    "SeverityLevel",
    "ThreatLevel",
]
