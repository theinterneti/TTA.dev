"""DoltCommitPrimitive — snapshot game state as a versioned commit."""

from __future__ import annotations

from dataclasses import dataclass, field

from tta_dev_primitives.core.base import WorkflowContext

from .core.base import DoltPrimitive
from .core.models import CommitInfo, DoltConfig


@dataclass
class CommitInput:
    """Input for committing game state to Dolt.

    Args:
        message: Human-readable description of this state snapshot.
            Good messages read like story beats: "Player enters the forest"
            rather than "update state".
        author: Who or what produced this state (player ID, agent name, etc.).
        tables: Specific tables to stage. If empty, stages all modified tables.
        allow_empty: Allow committing even if nothing changed.
    """

    message: str
    author: str = ""
    tables: list[str] = field(default_factory=list)
    allow_empty: bool = False


@dataclass
class CommitOutput:
    """Output of a Dolt commit operation."""

    success: bool
    commit: CommitInfo | None
    message: str = ""


class DoltCommitPrimitive(DoltPrimitive[CommitInput, CommitOutput]):
    """Snapshot the current game state as a Dolt commit.

    Every meaningful moment in TTA — a player choice, a scene transition,
    a therapeutic milestone — becomes a commit. This gives every universe
    a full, queryable history of how it came to be.

    Example:
        ```python
        config = DoltConfig(repo_path="/path/to/game-db")
        commit = DoltCommitPrimitive(config)

        result = await commit.execute(
            CommitInput(
                message="Player chose to enter the forest",
                author="player-42",
            ),
            context,
        )
        # result.commit.hash is the address of this moment in time
        ```
    """

    def __init__(self, config: DoltConfig) -> None:
        super().__init__(config)

    async def execute(self, input_data: CommitInput, context: WorkflowContext) -> CommitOutput:
        """Stage and commit current game state.

        Args:
            input_data: Commit message, author, and optional table filter.
            context: Workflow context.

        Returns:
            CommitOutput with the new commit hash.

        Raises:
            RuntimeError: If staging or committing fails.
        """
        # Stage tables
        if input_data.tables:
            for table in input_data.tables:
                _, stderr, rc = await self._run_dolt("add", table)
                if rc != 0:
                    return CommitOutput(success=False, commit=None, message=stderr)
        else:
            _, stderr, rc = await self._run_dolt("add", "-A")
            if rc != 0:
                return CommitOutput(success=False, commit=None, message=stderr)

        # Build commit args
        commit_args = ["commit", "-m", input_data.message]
        if input_data.author:
            commit_args += ["--author", f"{input_data.author} <{input_data.author}@tta>"]
        if input_data.allow_empty:
            commit_args.append("--allow-empty")

        stdout, stderr, rc = await self._run_dolt(*commit_args)

        if rc != 0:
            # "nothing to commit" is not an error in allow_empty=False mode
            if "nothing to commit" in stderr.lower():
                return CommitOutput(
                    success=True,
                    commit=None,
                    message="Nothing to commit — state unchanged",
                )
            return CommitOutput(success=False, commit=None, message=stderr)

        # Get the hash of what we just committed
        hash_stdout, _, _ = await self._run_dolt("log", "--oneline", "-1")
        commit_hash = hash_stdout.split()[0] if hash_stdout else ""

        return CommitOutput(
            success=True,
            commit=CommitInfo(hash=commit_hash, message=input_data.message, author=input_data.author),
            message=f"Committed: {commit_hash}",
        )
