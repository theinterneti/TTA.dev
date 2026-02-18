"""DoltMergePrimitive — editorial PR merge for universe convergence."""

from __future__ import annotations

from dataclasses import dataclass

from tta_dev_primitives.core.base import WorkflowContext

from .core.base import DoltPrimitive
from .core.models import DoltConfig, MergeResult, MergeStrategy


@dataclass
class MergeInput:
    """Input for merging a universe branch into a target.

    Args:
        source_branch: The universe being merged (the "PR").
        target_branch: The universe receiving the merge (usually "main").
        strategy: How to handle conflicts.
        message: Commit message for the merge commit.
        squash: Squash all source commits into one before merging —
            useful for editorial curation where the individual steps
            don't need to be preserved in the canonical timeline.
    """

    source_branch: str
    target_branch: str = "main"
    strategy: MergeStrategy = MergeStrategy.DEFAULT
    message: str = ""
    squash: bool = False


class DoltMergePrimitive(DoltPrimitive[MergeInput, MergeResult]):
    """Merge a universe branch into the canonical timeline.

    This is the editorial step: a player's explored universe — or an
    AI-curated selection of narrative events — gets reviewed and merged
    into `main`, becoming part of the shared canonical story.

    The squash option is particularly useful here: the player's exploratory
    commits collapse into a single, clean narrative event in the canon.

    Example:
        ```python
        config = DoltConfig(repo_path="/path/to/game-db")
        merge = DoltMergePrimitive(config)

        # Accept a player's universe into the canonical timeline
        result = await merge.execute(
            MergeInput(
                source_branch="player-42/brave-choice",
                target_branch="main",
                squash=True,
                message="The brave path becomes canon: forest entry event",
            ),
            context,
        )
        ```
    """

    def __init__(self, config: DoltConfig) -> None:
        super().__init__(config)

    async def execute(self, input_data: MergeInput, context: WorkflowContext) -> MergeResult:
        """Merge source universe into target universe.

        Checks out the target branch first, then merges the source into it.

        Args:
            input_data: Source branch, target branch, strategy, and options.
            context: Workflow context.

        Returns:
            MergeResult indicating success, conflicts, and the merge commit hash.
        """
        # Checkout the target branch
        _, stderr, rc = await self._run_dolt("checkout", input_data.target_branch)
        if rc != 0:
            return MergeResult(
                success=False,
                source_branch=input_data.source_branch,
                target_branch=input_data.target_branch,
                message=f"Failed to checkout target branch: {stderr}",
            )

        # Build merge args
        merge_args = ["merge", input_data.source_branch]

        if input_data.squash:
            merge_args.append("--squash")

        if input_data.strategy != MergeStrategy.DEFAULT:
            merge_args += ["--strategy", input_data.strategy.value]

        msg = input_data.message or f"Merge universe '{input_data.source_branch}' into '{input_data.target_branch}'"
        merge_args += ["-m", msg]

        stdout, stderr, rc = await self._run_dolt(*merge_args)

        if rc != 0:
            conflicts = self._parse_conflicts(stderr)
            return MergeResult(
                success=False,
                source_branch=input_data.source_branch,
                target_branch=input_data.target_branch,
                conflicts=conflicts,
                message=stderr,
            )

        # Get resulting commit hash
        hash_stdout, _, _ = await self._run_dolt("log", "--oneline", "-1")
        commit_hash = hash_stdout.split()[0] if hash_stdout else ""

        return MergeResult(
            success=True,
            source_branch=input_data.source_branch,
            target_branch=input_data.target_branch,
            commit_hash=commit_hash,
            message=msg,
        )

    def _parse_conflicts(self, stderr: str) -> list[str]:
        """Extract conflict descriptions from Dolt merge stderr."""
        return [
            line.strip()
            for line in stderr.splitlines()
            if "conflict" in line.lower()
        ]
