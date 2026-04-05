"""SQLite integration primitive - SKELETON."""

# TODO: Implement SQLitePrimitive
# type:: implementation
# priority:: high
# package:: tta-dev-integrations
# Local SQLite database access via aiosqlite

from primitives import WorkflowContext

from tta_dev_integrations.database.base import (
    DatabasePrimitive,
    DatabaseQuery,
    DatabaseResult,
)


class SQLitePrimitive(DatabasePrimitive):
    """SQLite database integration (stub)."""

    async def _execute_impl(
        self,
        input_data: DatabaseQuery,
        context: WorkflowContext,
    ) -> DatabaseResult:
        raise NotImplementedError("SQLitePrimitive is not yet implemented")
