"""tta-dolt-primitives — versioned, branchable data for parallel universe mechanics.

Provides composable Dolt primitives for any application that needs Git-like
versioning of its data. Designed for TTA's parallel universe mechanic but
reusable in any branching-state application.

Usage:
    ```python
    from tta_dolt_primitives import DoltConfig, DoltUniversePrimitive, BranchOperation
    from tta_dolt_primitives import DoltCommitPrimitive, DoltDiffPrimitive, DoltQueryPrimitive

    config = DoltConfig(repo_path="/path/to/my-dolt-db")

    # Fork a new private universe
    universe = DoltUniversePrimitive(config)
    await universe.execute(
        UniverseInput(operation=BranchOperation.CREATE_AND_CHECKOUT, name="player-1/forest-path"),
        context,
    )

    # Commit current state
    commit = DoltCommitPrimitive(config)
    await commit.execute(CommitInput(message="Entered the forest", author="player-1"), context)

    # Compare against canonical timeline
    diff = DoltDiffPrimitive(config)
    result = await diff.execute(DiffInput(from_branch="main", to_branch="player-1/forest-path"), context)
    ```

Primitives:
    - DoltUniversePrimitive: Branch lifecycle (create, checkout, list, delete)
    - DoltCommitPrimitive: Snapshot game state as a versioned commit
    - DoltMergePrimitive: Merge a universe into the canonical timeline (editorial PR)
    - DoltDiffPrimitive: Compare two universes to see how they diverged
    - DoltQueryPrimitive: SQL queries scoped to any branch
"""

from .commit import CommitInput, CommitOutput, DoltCommitPrimitive
from .core import (
    BranchInfo,
    BranchOperation,
    CommitInfo,
    DiffResult,
    DiffRow,
    DoltConfig,
    DoltPrimitive,
    MergeResult,
    MergeStrategy,
    QueryResult,
)
from .diff import DiffInput, DoltDiffPrimitive
from .merge import DoltMergePrimitive, MergeInput
from .query import DoltQueryPrimitive, QueryInput
from .universe import DoltUniversePrimitive, UniverseInput, UniverseOutput

__all__ = [
    # Config
    "DoltConfig",
    # Primitives
    "DoltUniversePrimitive",
    "DoltCommitPrimitive",
    "DoltMergePrimitive",
    "DoltDiffPrimitive",
    "DoltQueryPrimitive",
    # Input/Output types
    "UniverseInput",
    "UniverseOutput",
    "CommitInput",
    "CommitOutput",
    "MergeInput",
    "DiffInput",
    "QueryInput",
    # Models
    "BranchOperation",
    "MergeStrategy",
    "BranchInfo",
    "CommitInfo",
    "DiffResult",
    "DiffRow",
    "MergeResult",
    "QueryResult",
    # Base
    "DoltPrimitive",
]
