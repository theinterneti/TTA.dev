"""
Demonstration script for the CreateSessionPage workflow.
"""

import asyncio

from tta_kb_automation.workflows.create_session_page import CreateSessionPage


async def main():
    """
    Runs the CreateSessionPage workflow for the 'CachePrimitive' topic.
    """
    print("Running CreateSessionPage workflow for topic: CachePrimitive")
    workflow = CreateSessionPage()
    output_path = await workflow.run(topic="CachePrimitive")
    print(f"Successfully created session page: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
