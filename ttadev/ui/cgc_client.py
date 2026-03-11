"""CGC client for querying code graph data."""

import subprocess
from pathlib import Path


def query_cgc_structure():
    """Query CGC for codebase structure."""
    try:
        # Get list of indexed repos
        result = subprocess.run(
            ["uv", "run", "--python", "3.12", "cgc", "list"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/home/thein/repos/TTA.dev",
        )

        if result.returncode != 0:
            return {"error": "Failed to list repos", "detail": result.stderr}

        # Build graph structure from our knowledge
        graph_data = {
            "nodes": [],
            "edges": [],
            "stats": {"primitives": 0, "workflows": 0, "agents": 0, "files": 0},
        }

        # Scan for primitives
        primitives_dir = Path("/home/thein/repos/TTA.dev/ttadev/primitives")
        if primitives_dir.exists():
            for py_file in primitives_dir.glob("**/*.py"):
                if py_file.name != "__init__.py":
                    rel_path = str(py_file.relative_to("/home/thein/repos/TTA.dev"))
                    graph_data["nodes"].append(
                        {
                            "id": rel_path,
                            "type": "primitive",
                            "name": py_file.stem,
                            "path": rel_path,
                        }
                    )
                    graph_data["stats"]["primitives"] += 1

        # Scan for workflows
        workflows_dir = Path("/home/thein/repos/TTA.dev/ttadev/workflows")
        if workflows_dir.exists():
            for py_file in workflows_dir.glob("**/*.py"):
                if py_file.name != "__init__.py":
                    rel_path = str(py_file.relative_to("/home/thein/repos/TTA.dev"))
                    graph_data["nodes"].append(
                        {"id": rel_path, "type": "workflow", "name": py_file.stem, "path": rel_path}
                    )
                    graph_data["stats"]["workflows"] += 1

        # Scan for agents
        agents_dir = Path("/home/thein/repos/TTA.dev/.github/agents")
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.agent.md"):
                rel_path = str(agent_file.relative_to("/home/thein/repos/TTA.dev"))
                graph_data["nodes"].append(
                    {
                        "id": rel_path,
                        "type": "agent",
                        "name": agent_file.stem.replace(".agent", ""),
                        "path": rel_path,
                    }
                )
                graph_data["stats"]["agents"] += 1

        graph_data["stats"]["files"] = len(graph_data["nodes"])

        return graph_data

    except Exception as e:
        return {"error": str(e)}


def query_cgc_dependencies(file_path: str):
    """Query CGC for dependencies of a specific file."""
    try:
        result = subprocess.run(
            ["uv", "run", "--python", "3.12", "cgc", "analyze", "deps", file_path],
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/home/thein/repos/TTA.dev",
        )

        if result.returncode == 0:
            return {"success": True, "output": result.stdout}
        else:
            return {"success": False, "error": result.stderr}

    except Exception as e:
        return {"error": str(e)}
