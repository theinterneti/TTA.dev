"""Base class for database integration primitives."""

from abc import abstractmethod
from typing import Any

from pydantic import BaseModel
from tta_dev_primitives import WorkflowContext, WorkflowPrimitive


class DatabaseQuery(BaseModel):
    """Standard database query format."""

    query: str
    params: dict[str, Any] | None = None
    fetch_one: bool = False
    fetch_all: bool = True


class DatabaseResult(BaseModel):
    """Standard database result format."""

    rows: list[dict[str, Any]]
    row_count: int
    columns: list[str] | None = None


class DatabasePrimitive(WorkflowPrimitive[DatabaseQuery, DatabaseResult]):
    """
    Base class for database integration primitives.

    Provides standard interface for all database providers with:
    - Connection pooling
    - Retry logic for transient failures
    - Observability via OpenTelemetry
    - Type-safe queries/results

    Example:
        ```python
        from tta_dev_integrations import SupabasePrimitive, DatabaseQuery

        db = SupabasePrimitive(url="...", key="...")

        query = DatabaseQuery(
            query="SELECT * FROM users WHERE email = :email",
            params={"email": "user@example.com"}
        )

        result = await db.execute(query, context)
        print(result.rows)
        ```
    """

    def __init__(
        self,
        *,
        connection_string: str | None = None,
        pool_size: int = 10,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize database primitive.

        Args:
            connection_string: Database connection string
            pool_size: Connection pool size
            timeout: Query timeout in seconds
            max_retries: Maximum retry attempts
        """
        super().__init__()
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.timeout = timeout
        self.max_retries = max_retries

    @abstractmethod
    async def _execute_impl(
        self,
        input_data: DatabaseQuery,
        context: WorkflowContext,
    ) -> DatabaseResult:
        """
        Execute database query.

        Subclasses must implement provider-specific logic.

        Args:
            input_data: Database query
            context: Workflow context for tracing

        Returns:
            Database result

        Raises:
            Exception: On database errors (will trigger retry)
        """
        pass
