#!/usr/bin/env python3
"""
TTA.dev + CodeGraphContext Integration Example

Demonstrates how to use CGC's graph database capabilities
within TTA.dev workflows for advanced code analysis.
"""

import asyncio
from ttadev.primitives.core import LambdaPrimitive, SequentialPrimitive
from ttadev.primitives.base import WorkflowContext


async def index_repository(repo_path: str, ctx: WorkflowContext) -> dict:
    """Index a repository using CGC."""
    import subprocess
    
    result = subprocess.run(
        ["uv", "run", "cgc", "index", repo_path],
        capture_output=True,
        text=True,
        cwd="/home/thein/repos/TTA.dev"
    )
    
    return {
        "status": "indexed" if result.returncode == 0 else "failed",
        "repo_path": repo_path,
        "output": result.stdout,
        "error": result.stderr
    }


async def analyze_dependencies(data: dict, ctx: WorkflowContext) -> dict:
    """Analyze dependencies using CGC."""
    import subprocess
    
    result = subprocess.run(
        ["uv", "run", "cgc", "analyze", "dependencies", "-p", data["repo_path"]],
        capture_output=True,
        text=True,
        cwd="/home/thein/repos/TTA.dev"
    )
    
    data["dependencies"] = result.stdout
    return data


async def find_primitives(data: dict, ctx: WorkflowContext) -> dict:
    """Find all primitive classes using CGC."""
    import subprocess
    
    result = subprocess.run(
        ["uv", "run", "cgc", "find", "classes", "-n", "Primitive", "-p", data["repo_path"]],
        capture_output=True,
        text=True,
        cwd="/home/thein/repos/TTA.dev"
    )
    
    data["primitives"] = result.stdout
    return data


async def main():
    """Demonstrate CGC integration with TTA.dev workflows."""
    
    # Build a workflow that uses CGC for code analysis
    workflow = SequentialPrimitive([
        LambdaPrimitive(index_repository),
        LambdaPrimitive(analyze_dependencies),
        LambdaPrimitive(find_primitives)
    ])
    
    ctx = WorkflowContext(workflow_id="cgc-analysis")
    
    print("🔍 Starting CGC-powered code analysis...")
    result = await workflow.execute("/home/thein/repos/TTA.dev", ctx)
    
    print("\n📊 Analysis Results:")
    print(f"Status: {result['status']}")
    print(f"\nPrimitives found:\n{result.get('primitives', 'N/A')}")
    print(f"\nDependencies:\n{result.get('dependencies', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
