"""Example: Basic Documentation Sync with TTA.dev Patterns.

Demonstrates simple workflow composition using >> operator.
"""

import asyncio
from pathlib import Path

from tta_dev_primitives import WorkflowContext

from tta_documentation_primitives import create_basic_sync_workflow


async def main() -> None:
    """Basic documentation sync example."""
    # Create simple workflow: converter >> syncer
    workflow = create_basic_sync_workflow()

    # Create context with trace ID
    context = WorkflowContext(trace_id="basic-sync-demo")

    # Process a file
    file_path = Path("docs/guides/example.md")
    result = await workflow.execute(file_path, context)

    return result


if __name__ == "__main__":
    asyncio.run(main())
