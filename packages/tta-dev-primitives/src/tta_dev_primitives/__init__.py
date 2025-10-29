"""TTA Workflow Primitives - Composable workflow building blocks."""

from .core.base import LambdaPrimitive, WorkflowContext, WorkflowPrimitive
from .core.conditional import ConditionalPrimitive, SwitchPrimitive
from .core.parallel import ParallelPrimitive
from .core.routing import RouterPrimitive
from .core.sequential import SequentialPrimitive
from .performance.cache import CachePrimitive
from .recovery.compensation import SagaPrimitive
from .recovery.fallback import FallbackPrimitive
from .recovery.retry import RetryPrimitive
from .recovery.timeout import TimeoutError, TimeoutPrimitive

# APM support (optional)
try:
    from .apm import get_meter, get_tracer, is_apm_enabled, setup_apm
    from .apm.decorators import trace_workflow, track_metric
    from .apm.instrumented import APMWorkflowPrimitive

    _apm_exports = [
        "setup_apm",
        "get_tracer",
        "get_meter",
        "is_apm_enabled",
        "APMWorkflowPrimitive",
        "trace_workflow",
        "track_metric",
    ]
except ImportError:
    # APM dependencies not installed
    _apm_exports = []

__all__ = [
    "WorkflowContext",
    "WorkflowPrimitive",
    "LambdaPrimitive",
    "ConditionalPrimitive",
    "SwitchPrimitive",
    "ParallelPrimitive",
    "SequentialPrimitive",
    "RouterPrimitive",
    "CachePrimitive",
    "RetryPrimitive",
    "FallbackPrimitive",
    "SagaPrimitive",
    "TimeoutPrimitive",
    "TimeoutError",
] + _apm_exports

__version__ = "0.2.0"
