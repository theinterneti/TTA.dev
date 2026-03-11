"""Bridge to query CodeGraphContext MCP and format for dashboard."""

import json
import subprocess
from pathlib import Path


def query_cgc_graph():
    """Query CGC MCP for graph data and format for d3.js visualization."""
    try:
        # Use uv to run cgc query - just list Python files
        result = subprocess.run(
            [
                "uv",
                "run",
                "--python",
                "3.12",
                "cgc",
                "query",
                "list all Python files in this project",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            cwd="/home/thein/repos/TTA.dev",
        )

        if result.returncode != 0:
            print(f"CGC query failed: {result.stderr}")
            return {"nodes": [], "edges": [], "stats": {}}

        # Parse CGC output
        try:
            cgc_data = json.loads(result.stdout)
        except json.JSONDecodeError:
            # CGC might return text, convert to simple structure
            files = result.stdout.strip().split("\n")
            cgc_data = {"files": [f for f in files if f]}

        # Convert to d3.js graph format
        nodes = []
        edges = []

        # Group files by directory
        file_map = {}
        for idx, file_path in enumerate(cgc_data.get("files", [])):
            if not file_path:
                continue

            path = Path(file_path)
            node_id = f"file_{idx}"
            file_map[file_path] = node_id

            # Determine node type
            if path.suffix == ".py":
                node_type = "python"
            elif path.suffix in [".md", ".txt"]:
                node_type = "documentation"
            elif path.suffix in [".yml", ".yaml", ".json"]:
                node_type = "config"
            else:
                node_type = "other"

            nodes.append(
                {
                    "id": node_id,
                    "name": path.name,
                    "path": str(path),
                    "type": node_type,
                    "group": str(path.parent),
                }
            )

        # Create edges based on imports (simplified - would need AST parsing for real)
        # For now, just create directory grouping edges
        dir_nodes = {}
        for node in nodes:
            dir_name = node["group"]
            if dir_name not in dir_nodes:
                dir_id = f"dir_{len(dir_nodes)}"
                dir_nodes[dir_name] = dir_id
                nodes.append(
                    {
                        "id": dir_id,
                        "name": Path(dir_name).name or "root",
                        "path": dir_name,
                        "type": "directory",
                        "group": dir_name,
                    }
                )

            # Link file to its directory
            edges.append({"source": dir_nodes[dir_name], "target": node["id"], "type": "contains"})

        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_files": len([n for n in nodes if n["type"] != "directory"]),
                "total_directories": len([n for n in nodes if n["type"] == "directory"]),
                "python_files": len([n for n in nodes if n["type"] == "python"]),
                "doc_files": len([n for n in nodes if n["type"] == "documentation"]),
            },
        }

    except subprocess.TimeoutExpired:
        print("CGC query timed out")
        return {"nodes": [], "edges": [], "stats": {}}
    except Exception as e:
        print(f"Error querying CGC: {e}")
        return {"nodes": [], "edges": [], "stats": {}}


if __name__ == "__main__":
    # Test the bridge
    graph = query_cgc_graph()
    print(json.dumps(graph, indent=2))
