"""SQLite integration primitive.

Wraps aiosqlite for async SQLite database operations as a TTA.dev WorkflowPrimitive.
"""

from typing import Any

import aiosqlite
from pydantic import BaseModel, Field

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class SQLiteRequest(BaseModel):
    """Request model for SQLite primitive."""

    query: str = Field(description="SQL query to execute")
    parameters: tuple[Any, ...] | dict[str, Any] | None = Field(
        default=None, description="Query parameters for parameterized queries"
    )
    fetch: str = Field(
        default="all",
        description="Fetch mode: 'all', 'one', 'many', or 'none' (for INSERT/UPDATE/DELETE)",
    )
    fetch_size: int | None = Field(
        default=None, description="Number of rows to fetch (for 'many' mode)"
    )


class SQLiteResponse(BaseModel):
    """Response model for SQLite primitive."""

    data: list[dict[str, Any]] | dict[str, Any] | None = Field(description="Query result data")
    rowcount: int = Field(description="Number of rows affected")
    lastrowid: int | None = Field(default=None, description="Last inserted row ID (for INSERT)")
    status: str = Field(description="Operation status")


class SQLitePrimitive(WorkflowPrimitive[SQLiteRequest, SQLiteResponse]):
    """Wrapper around aiosqlite for async SQLite operations.

    This primitive provides a consistent TTA.dev interface for SQLite
    database operations with built-in observability.

    Example:
        ```python
        from tta_dev_primitives.integrations import SQLitePrimitive
        from tta_dev_primitives.core.base import WorkflowContext

        # Create primitive
        db = SQLitePrimitive(database="app.db")

        # Execute query
        context = WorkflowContext(workflow_id="db-demo")
        request = SQLiteRequest(
            query="SELECT * FROM users WHERE age > ?",
            parameters=(18,),
            fetch="all"
        )
        response = await db.execute(request, context)
        print(response.data)
        ```

    Attributes:
        database: Path to SQLite database file
    """

    def __init__(self, database: str = ":memory:") -> None:
        """Initialize SQLite primitive.

        Args:
            database: Path to SQLite database file (default: in-memory)
        """
        super().__init__()
        self.database = database

    async def execute(self, input_data: SQLiteRequest, context: WorkflowContext) -> SQLiteResponse:
        """Execute SQLite query.

        Args:
            input_data: Request with SQL query and parameters
            context: Workflow context for observability

        Returns:
            Response with query results and metadata

        Raises:
            ValueError: If fetch mode is invalid
            Exception: If database operation fails
        """
        async with aiosqlite.connect(self.database) as db:
            # Enable row factory for dict results
            db.row_factory = aiosqlite.Row

            async with db.execute(input_data.query, input_data.parameters or ()) as cursor:
                # Fetch results based on mode
                fetch_mode = input_data.fetch.lower()

                if fetch_mode == "all":
                    rows = await cursor.fetchall()
                    data = [dict(row) for row in rows]
                elif fetch_mode == "one":
                    row = await cursor.fetchone()
                    data = dict(row) if row else None
                elif fetch_mode == "many":
                    if input_data.fetch_size is None:
                        raise ValueError("fetch_size required for 'many' mode")
                    rows = await cursor.fetchmany(input_data.fetch_size)
                    data = [dict(row) for row in rows]
                elif fetch_mode == "none":
                    data = None
                else:
                    raise ValueError(
                        f"Invalid fetch mode: {fetch_mode}. Must be one of: all, one, many, none"
                    )

                # Commit changes for write operations
                await db.commit()

                return SQLiteResponse(
                    data=data,
                    rowcount=cursor.rowcount,
                    lastrowid=cursor.lastrowid,
                    status="success",
                )
