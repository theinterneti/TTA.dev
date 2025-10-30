"""Supabase integration primitive.

Wraps the official Supabase SDK as a TTA.dev WorkflowPrimitive.
"""

from typing import Any

from pydantic import BaseModel, Field
from supabase import Client, create_client

from tta_dev_primitives.core.base import WorkflowContext, WorkflowPrimitive


class SupabaseRequest(BaseModel):
    """Request model for Supabase primitive."""

    operation: str = Field(
        description="Database operation: 'select', 'insert', 'update', 'delete'"
    )
    table: str = Field(description="Table name to operate on")
    data: dict[str, Any] | list[dict[str, Any]] | None = Field(
        default=None, description="Data for insert/update operations"
    )
    filters: dict[str, Any] | None = Field(
        default=None, description="Filter conditions for select/update/delete"
    )
    columns: str | None = Field(
        default=None, description="Columns to select (default: '*')"
    )


class SupabaseResponse(BaseModel):
    """Response model for Supabase primitive."""

    data: list[dict[str, Any]] | dict[str, Any] | None = Field(
        description="Query result data"
    )
    count: int | None = Field(default=None, description="Number of rows affected")
    status: str = Field(description="Operation status")


class SupabasePrimitive(WorkflowPrimitive[SupabaseRequest, SupabaseResponse]):
    """Wrapper around official Supabase SDK.

    This primitive provides a consistent TTA.dev interface for Supabase's
    database operations, enabling CRUD operations with built-in observability.

    Example:
        ```python
        from tta_dev_primitives.integrations import SupabasePrimitive
        from tta_dev_primitives.core.base import WorkflowContext

        # Create primitive
        db = SupabasePrimitive(
            url="https://your-project.supabase.co",
            key="your-anon-key"
        )

        # Select data
        context = WorkflowContext(workflow_id="db-demo")
        request = SupabaseRequest(
            operation="select",
            table="users",
            filters={"age": {"gte": 18}}
        )
        response = await db.execute(request, context)
        print(response.data)
        ```

    Attributes:
        client: Supabase Client instance
        url: Supabase project URL
    """

    def __init__(self, url: str, key: str, **kwargs: Any) -> None:
        """Initialize Supabase primitive.

        Args:
            url: Supabase project URL (e.g., https://xxx.supabase.co)
            key: Supabase API key (anon or service role key)
            **kwargs: Additional arguments passed to create_client
        """
        super().__init__()
        self.client: Client = create_client(url, key, **kwargs)
        self.url = url

    async def execute(
        self, input_data: SupabaseRequest, context: WorkflowContext
    ) -> SupabaseResponse:
        """Execute Supabase database operation.

        Args:
            input_data: Request with operation type and parameters
            context: Workflow context for observability

        Returns:
            Response with query results and metadata

        Raises:
            ValueError: If operation type is invalid
            Exception: If database operation fails
        """
        operation = input_data.operation.lower()

        # Build query based on operation
        if operation == "select":
            return await self._execute_select(input_data)
        elif operation == "insert":
            return await self._execute_insert(input_data)
        elif operation == "update":
            return await self._execute_update(input_data)
        elif operation == "delete":
            return await self._execute_delete(input_data)
        else:
            raise ValueError(
                f"Invalid operation: {operation}. Must be one of: select, insert, update, delete"
            )

    async def _execute_select(self, input_data: SupabaseRequest) -> SupabaseResponse:
        """Execute SELECT operation."""
        columns = input_data.columns or "*"
        query = self.client.table(input_data.table).select(columns)

        # Apply filters if provided
        if input_data.filters:
            for key, value in input_data.filters.items():
                if isinstance(value, dict):
                    # Handle filter operators (e.g., {"gte": 18})
                    for op, val in value.items():
                        query = getattr(query, op)(key, val)
                else:
                    # Simple equality filter
                    query = query.eq(key, value)

        response = query.execute()
        return SupabaseResponse(
            data=response.data, count=len(response.data), status="success"
        )

    async def _execute_insert(self, input_data: SupabaseRequest) -> SupabaseResponse:
        """Execute INSERT operation."""
        if not input_data.data:
            raise ValueError("INSERT operation requires 'data' field")

        response = self.client.table(input_data.table).insert(input_data.data).execute()
        return SupabaseResponse(
            data=response.data, count=len(response.data), status="success"
        )

    async def _execute_update(self, input_data: SupabaseRequest) -> SupabaseResponse:
        """Execute UPDATE operation."""
        if not input_data.data:
            raise ValueError("UPDATE operation requires 'data' field")

        query = self.client.table(input_data.table).update(input_data.data)

        # Apply filters if provided
        if input_data.filters:
            for key, value in input_data.filters.items():
                if isinstance(value, dict):
                    for op, val in value.items():
                        query = getattr(query, op)(key, val)
                else:
                    query = query.eq(key, value)

        response = query.execute()
        return SupabaseResponse(
            data=response.data, count=len(response.data), status="success"
        )

    async def _execute_delete(self, input_data: SupabaseRequest) -> SupabaseResponse:
        """Execute DELETE operation."""
        query = self.client.table(input_data.table).delete()

        # Apply filters if provided
        if input_data.filters:
            for key, value in input_data.filters.items():
                if isinstance(value, dict):
                    for op, val in value.items():
                        query = getattr(query, op)(key, val)
                else:
                    query = query.eq(key, value)

        response = query.execute()
        return SupabaseResponse(
            data=response.data, count=len(response.data), status="success"
        )
