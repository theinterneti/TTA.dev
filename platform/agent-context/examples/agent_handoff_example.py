"""
Simple Agent Handoff Example

Demonstrates how to use AgentHandoffPrimitive to transfer tasks between agents
with context preservation and history tracking.
"""

import asyncio

from tta_dev_primitives import WorkflowContext, WorkflowPrimitive

from universal_agent_context.primitives import AgentHandoffPrimitive


class DataCollectorAgent(WorkflowPrimitive[dict, dict]):
    """Agent that collects data."""

    def __init__(self):
        self.name = "data_collector"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Collect data from input."""
        print(f"📊 {self.name}: Collecting data...")
        return {
            "raw_data": input_data.get("query", ""),
            "data_points": 100,
            "status": "collected",
        }


class DataAnalyzerAgent(WorkflowPrimitive[dict, dict]):
    """Agent that analyzes data."""

    def __init__(self):
        self.name = "data_analyzer"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Analyze collected data."""
        print(f"🔬 {self.name}: Analyzing data...")
        print(f"   Current agent: {context.metadata.get('current_agent')}")
        print(f"   Handoff history: {context.metadata.get('agent_history', [])}")
        return {
            "raw_data": input_data.get("raw_data"),
            "analysis": "Data shows positive trend",
            "confidence": 0.85,
            "status": "analyzed",
        }


class ReportGeneratorAgent(WorkflowPrimitive[dict, dict]):
    """Agent that generates reports."""

    def __init__(self):
        self.name = "report_generator"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Generate report from analysis."""
        print(f"📝 {self.name}: Generating report...")
        print(f"   Current agent: {context.metadata.get('current_agent')}")
        print(f"   Handoff history: {context.metadata.get('agent_history', [])}")
        return {
            "report": f"Analysis Report: {input_data.get('analysis')}",
            "confidence": input_data.get("confidence"),
            "status": "complete",
        }


async def main():
    """Run agent handoff example."""
    print("=" * 60)
    print("Agent Handoff Example")
    print("=" * 60)

    # Create agents
    collector = DataCollectorAgent()
    analyzer = DataAnalyzerAgent()
    reporter = ReportGeneratorAgent()

    # Create handoff primitives
    handoff_to_analyzer = AgentHandoffPrimitive(
        target_agent="data_analyzer",
        handoff_strategy="immediate",
        preserve_context=True,
    )

    handoff_to_reporter = AgentHandoffPrimitive(
        target_agent="report_generator",
        handoff_strategy="immediate",
        preserve_context=True,
    )

    # Build workflow with handoffs
    workflow = collector >> handoff_to_analyzer >> analyzer >> handoff_to_reporter >> reporter

    # Create context
    context = WorkflowContext(workflow_id="handoff-example")
    context.metadata["current_agent"] = "data_collector"

    # Execute workflow
    print("\n🚀 Starting workflow...\n")
    result = await workflow.execute({"query": "market trends"}, context)

    # Display results
    print("\n" + "=" * 60)
    print("Results:")
    print("=" * 60)
    print(f"Final Status: {result['status']}")
    print(f"Report: {result['report']}")
    print(f"Confidence: {result['confidence']}")
    print(f"\nAgent History: {context.metadata.get('agent_history', [])}")
    print(f"Current Agent: {context.metadata.get('current_agent')}")


if __name__ == "__main__":
    asyncio.run(main())
