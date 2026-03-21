"""Package-manager primitives for Python (uv) and JavaScript (pnpm).

Provides composable workflow primitives that wrap CLI package-manager
commands with type safety, observability, and workflow composition via
the ``>>`` and ``|`` operators.

Example:
    ```python
    from ttadev.primitives.package_managers import (
        UvSyncPrimitive, UvSyncInput,
    )
    from primitives import WorkflowContext

    prim = UvSyncPrimitive()
    result = await prim.execute(
        UvSyncInput(all_extras=True),
        WorkflowContext(workflow_id="setup"),
    )
    ```
"""

from .base import PackageManagerOutput, PackageManagerPrimitive
from .pnpm import (
    PnpmAddInput,
    PnpmAddOutput,
    PnpmAddPrimitive,
    PnpmInstallInput,
    PnpmInstallOutput,
    PnpmInstallPrimitive,
    PnpmRemoveInput,
    PnpmRemoveOutput,
    PnpmRemovePrimitive,
    PnpmRunInput,
    PnpmRunOutput,
    PnpmRunPrimitive,
    PnpmUpdateInput,
    PnpmUpdateOutput,
    PnpmUpdatePrimitive,
)
from .uv import (
    UvAddInput,
    UvAddOutput,
    UvAddPrimitive,
    UvLockInput,
    UvLockOutput,
    UvLockPrimitive,
    UvRemoveInput,
    UvRemoveOutput,
    UvRemovePrimitive,
    UvRunInput,
    UvRunOutput,
    UvRunPrimitive,
    UvSyncInput,
    UvSyncOutput,
    UvSyncPrimitive,
    UvTreeInput,
    UvTreeOutput,
    UvTreePrimitive,
)

__all__ = [
    # Base
    "PackageManagerOutput",
    "PackageManagerPrimitive",
    # uv
    "UvAddInput",
    "UvAddOutput",
    "UvAddPrimitive",
    "UvLockInput",
    "UvLockOutput",
    "UvLockPrimitive",
    "UvRemoveInput",
    "UvRemoveOutput",
    "UvRemovePrimitive",
    "UvRunInput",
    "UvRunOutput",
    "UvRunPrimitive",
    "UvSyncInput",
    "UvSyncOutput",
    "UvSyncPrimitive",
    "UvTreeInput",
    "UvTreeOutput",
    "UvTreePrimitive",
    # pnpm
    "PnpmAddInput",
    "PnpmAddOutput",
    "PnpmAddPrimitive",
    "PnpmInstallInput",
    "PnpmInstallOutput",
    "PnpmInstallPrimitive",
    "PnpmRemoveInput",
    "PnpmRemoveOutput",
    "PnpmRemovePrimitive",
    "PnpmRunInput",
    "PnpmRunOutput",
    "PnpmRunPrimitive",
    "PnpmUpdateInput",
    "PnpmUpdateOutput",
    "PnpmUpdatePrimitive",
]
