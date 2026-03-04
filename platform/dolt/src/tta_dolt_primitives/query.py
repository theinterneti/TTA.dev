"""DoltQueryPrimitive — SQL queries across universe branches."""

from __future__ import annotations

from dataclasses import dataclass, field

import aiomysql
import structlog
from tta_dev_primitives.core.base import WorkflowContext

from .core.base import DoltPrimitive
from .core.models import DoltConfig, QueryResult

logger = structlog.get_logger(__name__)


@dataclass
class QueryInput:
    """Input for a SQL query against a Dolt branch.

    Args:
        sql: The SQL query to execute.
        branch: Branch (universe) to query. Defaults to current branch.
            Use "main" for canonical universe, or any branch name.
        params: Query parameters for parameterized queries (prevents injection).
    """

    sql: str
    branch: str = "main"
    params: tuple = field(default_factory=tuple)


class DoltQueryPrimitive(DoltPrimitive[QueryInput, QueryResult]):
    """Execute SQL queries against a specific universe branch.

    Connects to the Dolt SQL server and queries any branch by name.
    This is how agents and the game engine read universe state —
    plain SQL, no special query language required.

    The `branch` parameter is the key: it scopes every query to a specific
    universe without any application-level branching logic.

    Requires a running Dolt SQL server:
        ```bash
        dolt sql-server --host 127.0.0.1 --port 3306 &
        ```

    Example:
        ```python
        config = DoltConfig(repo_path="/path/to/game-db")
        query = DoltQueryPrimitive(config)

        # Query the canonical universe
        result = await query.execute(
            QueryInput(sql="SELECT * FROM character_state WHERE player_id = %s", params=("player-42",)),
            context,
        )

        # Query a parallel universe
        result = await query.execute(
            QueryInput(
                sql="SELECT emotional_intelligence FROM character_state",
                branch="player-42/brave-choice",
            ),
            context,
        )
        ```
    """

    def __init__(self, config: DoltConfig) -> None:
        super().__init__(config)

    async def execute(self, input_data: QueryInput, context: WorkflowContext) -> QueryResult:
        """Run a SQL query against the specified universe branch.

        Args:
            input_data: SQL query, target branch, and optional params.
            context: Workflow context.

        Returns:
            QueryResult with rows as list of dicts.

        Raises:
            RuntimeError: If the Dolt SQL server is unreachable.
        """
        db = self.config.db_name()
        branch = input_data.branch

        # Dolt uses `database/branch` as the database name for branch-scoped queries
        db_with_branch = f"{db}/{branch}"

        try:
            conn = await aiomysql.connect(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                db=db_with_branch,
                autocommit=True,
            )
        except Exception as e:
            raise RuntimeError(
                f"Cannot connect to Dolt SQL server at {self.config.host}:{self.config.port}. "
                f"Is `dolt sql-server` running? Error: {e}"
            ) from e

        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(input_data.sql, input_data.params or None)
                rows = list(await cursor.fetchall())
        finally:
            conn.close()

        return QueryResult(
            branch=branch,
            sql=input_data.sql,
            rows=rows,
            row_count=len(rows),
        )
