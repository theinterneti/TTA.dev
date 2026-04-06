"""Control-plane exceptions."""


class ControlPlaneError(Exception):
    """Base control-plane error."""


class TaskNotFoundError(ControlPlaneError):
    """Raised when a task ID is unknown."""


class RunNotFoundError(ControlPlaneError):
    """Raised when a run ID is unknown."""


class TaskClaimError(ControlPlaneError):
    """Raised when a task cannot be claimed or mutated."""


class TaskGateError(ControlPlaneError):
    """Raised when gate state blocks a task mutation."""


class TaskLockError(ControlPlaneError):
    """Raised when lock state blocks a task mutation."""
