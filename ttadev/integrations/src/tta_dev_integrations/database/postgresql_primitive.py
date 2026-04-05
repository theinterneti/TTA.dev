"""PostgreSQL integration primitive - SKELETON."""

# TODO: Implement PostgreSQLPrimitive
# type:: implementation
# priority:: high
# package:: tta-dev-integrations
# Direct PostgreSQL database access via asyncpg

from primitives import WorkflowContext

from tta_dev_integrations.database.base import (
    DatabasePrimitive,
    DatabaseQuery,
    DatabaseResult,
)


class PostgreSQLPrimitive(DatabasePrimitive):
    """PostgreSQL database integration (stub)."""

    async def _execute_impl(
        self,
        input_data: DatabaseQuery,
        context: WorkflowContext,
    ) -> DatabaseResult:
        raise NotImplementedError("PostgreSQLPrimitive is not yet implemented")
