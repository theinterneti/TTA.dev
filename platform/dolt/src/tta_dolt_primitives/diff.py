"""DoltDiffPrimitive — compare two universe branches."""

from __future__ import annotations

from dataclasses import dataclass, field

from tta_dev_primitives.core.base import WorkflowContext

from .core.base import DoltPrimitive
from .core.models import DiffResult, DiffRow, DoltConfig


@dataclass
class DiffInput:
    """Input for comparing two universe branches.

    Args:
        from_branch: The baseline universe (e.g., "main").
        to_branch: The universe to compare against the baseline.
        tables: Specific tables to diff. If empty, diffs all tables.
    """

    from_branch: str
    to_branch: str
    tables: list[str] = field(default_factory=list)


class DoltDiffPrimitive(DoltPrimitive[DiffInput, DiffResult]):
    """Compare two universe branches to see how they diverged.

    This is the core tool for understanding what makes one universe different
    from another — which choices were made differently, how character state
    evolved, what therapeutic progress looks like across timelines.

    The diff is the narrative distance between two universes.

    Example:
        ```python
        config = DoltConfig(repo_path="/path/to/game-db")
        diff = DoltDiffPrimitive(config)

        result = await diff.execute(
            DiffInput(
                from_branch="main",
                to_branch="player-42/brave-choice",
                tables=["character_state", "choices"],
            ),
            context,
        )
        # result.rows shows every row that differs between the universes
        ```
    """

    def __init__(self, config: DoltConfig) -> None:
        super().__init__(config)

    async def execute(self, input_data: DiffInput, context: WorkflowContext) -> DiffResult:
        """Diff two universe branches.

        Args:
            input_data: Source and target branches, optional table filter.
            context: Workflow context.

        Returns:
            DiffResult with per-row changes across all diffed tables.
        """
        tables_to_diff = input_data.tables or await self._get_tables()

        all_rows: list[DiffRow] = []
        summary: dict[str, int] = {}

        for table in tables_to_diff:
            rows = await self._diff_table(input_data.from_branch, input_data.to_branch, table)
            all_rows.extend(rows)
            if rows:
                summary[table] = len(rows)

        return DiffResult(
            from_branch=input_data.from_branch,
            to_branch=input_data.to_branch,
            tables=tables_to_diff,
            rows=all_rows,
            summary=summary,
        )

    async def _get_tables(self) -> list[str]:
        """List all tables in the repo."""
        stdout, _, _ = await self._run_dolt("ls")
        return [line.strip() for line in stdout.splitlines() if line.strip()]

    async def _diff_table(self, from_branch: str, to_branch: str, table: str) -> list[DiffRow]:
        """Diff a single table between two branches using dolt diff --result-format csv."""
        stdout, _, rc = await self._run_dolt(
            "diff",
            "--result-format",
            "csv",
            f"{from_branch}...{to_branch}",
            table,
        )
        if rc != 0 or not stdout:
            return []

        rows: list[DiffRow] = []
        lines = stdout.splitlines()
        if len(lines) < 2:
            return []

        headers = [h.strip('"') for h in lines[0].split(",")]
        diff_type_idx = next((i for i, h in enumerate(headers) if h == "diff_type"), None)

        for line in lines[1:]:
            if not line.strip():
                continue
            values = [v.strip('"') for v in line.split(",")]
            if len(values) != len(headers):
                continue

            row_dict = dict(zip(headers, values, strict=False))
            diff_type = (
                row_dict.pop("diff_type", "modified") if diff_type_idx is not None else "modified"
            )

            rows.append(
                DiffRow(
                    table=table,
                    diff_type=diff_type,
                    from_values=row_dict if diff_type == "removed" else None,
                    to_values=row_dict if diff_type in ("added", "modified") else None,
                )
            )

        return rows
