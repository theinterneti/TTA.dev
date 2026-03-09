#!/usr/bin/env python3
"""Generate trace data to populate the observability dashboard."""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4


def write_trace(workflow_id: str, primitive_name: str, duration_ms: float, status: str = "success", error: str | None = None):
    """Write a trace to the .tta/traces directory."""
    traces_dir = Path(".tta/traces")
    traces_dir.mkdir(parents=True, exist_ok=True)
    
    trace_id = str(uuid4())
    trace = {
        "trace_id": trace_id,
        "workflow_id": workflow_id,
        "primitive": primitive_name,
        "start_time": datetime.now().isoformat(),
        "duration_ms": duration_ms,
        "status": status,
        "spans": [
            {
                "span_id": str(uuid4()),
                "name": primitive_name,
                "duration_ms": duration_ms,
                "attributes": {
                    "primitive.type": primitive_name.split("_")[0],
                    "workflow.id": workflow_id
                }
            }
        ]
    }
    
    if error:
        trace["error_message"] = error
        trace["status"] = "error"
    
    # Write trace file
    trace_file = traces_dir / f"{trace_id}.json"
    with open(trace_file, "w") as f:
        json.dump(trace, f, indent=2)
    
    return trace


async def main():
    """Generate several workflows with traces."""
    
    print("🚀 Generating trace data...")
    
    # Workflow 1: Data processing
    print("\n1. Running data processing workflow...")
    trace1 = write_trace("data_processing_001", "FetchPrimitive", 245.3, "success")
    print(f"   ✓ Created trace: {trace1['trace_id']}")
    await asyncio.sleep(0.1)
    
    trace2 = write_trace("data_processing_001", "TransformPrimitive", 189.7, "success")
    print(f"   ✓ Created trace: {trace2['trace_id']}")
    await asyncio.sleep(0.1)
    
    # Workflow 2: With retry
    print("\n2. Running workflow with retry...")
    trace3 = write_trace("retry_workflow_002", "RetryPrimitive", 567.2, "success")
    print(f"   ✓ Created trace: {trace3['trace_id']}")
    await asyncio.sleep(0.1)
    
    # Workflow 3: With error
    print("\n3. Running workflow with error...")
    trace4 = write_trace("error_workflow_003", "ValidationPrimitive", 123.4, "error", "Validation failed: Invalid input")
    print(f"   ✓ Created trace: {trace4['trace_id']}")
    await asyncio.sleep(0.1)
    
    # Workflow 4: Parallel execution
    print("\n4. Running parallel workflow...")
    trace5 = write_trace("parallel_workflow_004", "ParallelPrimitive", 892.1, "success")
    print(f"   ✓ Created trace: {trace5['trace_id']}")
    
    trace6 = write_trace("parallel_workflow_004", "CachePrimitive", 45.6, "success")
    print(f"   ✓ Created trace: {trace6['trace_id']}")
    
    print("\n✨ Trace generation complete! Check the dashboard at http://localhost:8000")
    print(f"📁 Traces written to: {Path('.tta/traces').absolute()}")


if __name__ == "__main__":
    asyncio.run(main())
