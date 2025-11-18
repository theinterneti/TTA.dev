#!/usr/bin/env python3
"""
Context Engine for TTA.dev Agent Primitives

This module provides intelligent context understanding, relationship mapping,
and multi-file context retrieval for Cline's agentic workflow system.
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FileRelationship:
    """Represents a relationship between files or components."""

    source_file: str
    target_file: str
    relationship_type: str  # 'imports', 'calls', 'implements', 'extends', 'depends_on'
    line_number: int | None = None
    context: str | None = None  # surrounding code context


@dataclass
class ComponentMap:
    """Map of architectural components and their relationships."""

    components: dict[str, dict] = field(default_factory=dict)
    relationships: list[FileRelationship] = field(default_factory=list)
    dependency_graph: dict[str, set[str]] = field(
        default_factory=lambda: defaultdict(set)
    )


class ContextEngine:
    """
    Intelligent context retrieval and architectural relationship mapping.

    Provides optimized helpers for understanding complex codebases and
    retrieving relevant context across multiple files.
    """

    def __init__(self):
        self.base_path = Path(".")
        self.component_map = ComponentMap()

        # Pre-index common TTA.dev components
        self._load_component_index()

        # Build relationship graph
        self._build_relationship_graph()

    def _load_component_index(self):
        """Load index of key TTA.dev components."""
        # Core primitives
        self.component_map.components.update(
            {
                "tta_dev_primitives": {
                    "path": "packages/tta-dev-primitives/src/tta_dev_primitives",
                    "type": "package",
                    "description": "Core workflow primitives library",
                    "key_files": ["__init__.py", "core/base.py", "core/sequential.py"],
                },
                "workflow_primitives": {
                    "path": "packages/tta-dev-primitives/src/tta_dev_primitives/core",
                    "type": "module",
                    "description": "Fundamental workflow primitives (Sequential, Parallel, etc.)",
                },
                "recovery_primitives": {
                    "path": "packages/tta-dev-primitives/src/tta_dev_primitives/recovery",
                    "type": "module",
                    "description": "Error recovery and resilience primitives",
                },
                "performance_primitives": {
                    "path": "packages/tta-dev-primitives/src/tta_dev_primitives/performance",
                    "type": "module",
                    "description": "Performance optimization primitives (Cache, etc.)",
                },
            }
        )

    def _build_relationship_graph(self):
        """Analyze codebase and build relationship graph."""
        # Analyze Python imports and dependencies
        self._analyze_python_dependencies()

        # Look for composition patterns
        self._analyze_composition_patterns()

    def _analyze_python_dependencies(self):
        """Analyze Python import relationships."""
        for py_file in self.base_path.rglob("*.py"):
            try:
                content = py_file.read_text()
                rel_path = str(py_file.relative_to(self.base_path))

                # Find import statements
                import_pattern = r"^(?:from\s+([\w.]+(?:\s+import\s+[\w\s,]+)?)|import\s+([\w.]+(?:\s+as\s+\w+)?))$"
                for match in re.finditer(import_pattern, content, re.MULTILINE):
                    if match.group(1):  # from import
                        module_path = match.group(1).split(".")[0]
                        self.component_map.dependency_graph[rel_path].add(
                            f"packages/*/{module_path}"
                        )
                    elif match.group(2):  # direct import
                        module_path = match.group(2).split(".")[0]
                        self.component_map.dependency_graph[rel_path].add(
                            f"packages/*/{module_path}"
                        )

            except Exception as e:
                print(f"Warning: Failed to analyze {py_file}: {e}")

    def _analyze_composition_patterns(self):
        """Analyze TTA.dev composition patterns (>>, |, etc.)."""
        for py_file in self.base_path.rglob("*.py"):
            try:
                content = py_file.read_text()
                rel_path = str(py_file.relative_to(self.base_path))

                # Look for composition operators
                if ">>" in content or "|" in content:
                    self.component_map.relationships.append(
                        FileRelationship(
                            source_file=rel_path,
                            target_file="tta_dev_primitives.core",
                            relationship_type="uses_composition",
                            context="File uses TTA.dev composition operators",
                        )
                    )

            except Exception as e:
                print(f"Warning: Failed to analyze composition in {py_file}: {e}")

    def get_context_for_task(self, task_description: str, max_files: int = 5) -> dict:
        """
        Get optimized context for a development task.

        Analyzes the task and returns relevant files, patterns, and relationships.
        """
        relevant_files = self._find_relevant_files(task_description)
        relevant_patterns = self._find_relevant_patterns(task_description)
        relationships = self._find_related_components(relevant_files[:max_files])

        return {
            "relevant_files": relevant_files[:max_files],
            "suggested_patterns": relevant_patterns,
            "architectural_context": relationships,
            "task_type": self._classify_task(task_description),
        }

    def _find_relevant_files(self, task: str) -> list[dict]:
        """Find files relevant to the task."""
        task_lower = task.lower()
        relevant_files = []

        # Scoring based on file path, content, and task keywords
        file_scores = []

        for py_file in self.base_path.rglob("*.py"):
            try:
                rel_path = str(py_file.relative_to(self.base_path))
                score = 0

                # Path-based scoring
                if "primitive" in rel_path and "primitive" in task_lower:
                    score += 10
                if "workflow" in rel_path and "workflow" in task_lower:
                    score += 8
                if "test" in rel_path and (
                    "test" in task_lower or "coverage" in task_lower
                ):
                    score += 6

                # Keyword matching in path
                path_words = (
                    rel_path.lower().replace("/", " ").replace("_", " ").split()
                )
                for word in task_lower.split():
                    if word in path_words:
                        score += 5

                # Content sampling (first 1000 chars)
                content = py_file.read_text()[:1000].lower()
                for word in task_lower.split():
                    if word in content:
                        score += 2

                if score > 0:
                    file_scores.append((score, rel_path, py_file))

            except Exception:
                continue

        # Sort by relevance and return top matches
        file_scores.sort(reverse=True)

        return [
            {
                "file_path": path,
                "relevance_score": score,
                "file_size": file.stat().st_size if file.exists() else 0,
            }
            for score, path, file in file_scores[:10]
        ]

    def _find_relevant_patterns(self, task: str) -> list[dict]:
        """Find patterns relevant to the task."""
        task_lower = task.lower()
        patterns = []

        # Define pattern mappings
        pattern_mappings = {
            "sequential": ["sequence", "chain", "pipeline", "step by step"],
            "parallel": ["concurrent", "parallel", "simultaneous", "multiple"],
            "retry": ["retry", "backoff", "failure", "transient error"],
            "cache": ["cache", "performance", "speed", "optimization"],
            "router": ["route", "conditional", "decision", "direct"],
            "recovery": ["fallback", "recovery", "error handling", "resilience"],
            "observability": ["tracing", "metrics", "logging", "monitoring"],
        }

        for pattern_name, keywords in pattern_mappings.items():
            if any(keyword in task_lower for keyword in keywords):
                patterns.append(
                    {
                        "pattern_name": pattern_name,
                        "relevance": "high",
                        "reason": f"Task mentions {keywords[0]}",
                    }
                )

        return patterns[:3]

    def _find_related_components(self, file_list: list) -> dict:
        """Find architectural relationships for given files."""
        relationships = {"dependencies": [], "usage": [], "similar": []}

        for file_info in file_list:
            file_path = file_info["file_path"]

            # Find dependencies
            deps = self.component_map.dependency_graph.get(file_path, set())
            relationships["dependencies"].extend(deps)

            # Find files that use this component
            for other_file, file_deps in self.component_map.dependency_graph.items():
                if any(dep in str(file_path) for dep in file_deps):
                    relationships["usage"].append(other_file)

        # Remove duplicates and limit results
        relationships["dependencies"] = list(set(relationships["dependencies"]))[:5]
        relationships["usage"] = list(set(relationships["usage"]))[:5]

        return relationships

    def _classify_task(self, task: str) -> str:
        """Classify the type of development task."""
        task_lower = task.lower()

        if any(word in task_lower for word in ["implement", "create", "build", "add"]):
            return "implementation"
        elif any(word in task_lower for word in ["fix", "bug", "error", "issue"]):
            return "bug_fix"
        elif any(word in task_lower for word in ["test", "coverage", "unit test"]):
            return "testing"
        elif any(word in task_lower for word in ["optimize", "performance", "speed"]):
            return "optimization"
        elif any(word in task_lower for word in ["document", "doc", "readme"]):
            return "documentation"
        else:
            return "analysis"

    def get_multi_file_context(
        self, primary_file: str, context_radius: int = 2
    ) -> dict:
        """
        Get context that spans multiple related files.

        Uses the relationship graph to find files that should be considered together.
        """
        related_files = []
        visited = set([primary_file])

        # BFS through relationships
        queue = [(primary_file, 0)]  # (file, distance)

        while queue:
            current_file, distance = queue.pop(0)

            if distance >= context_radius:
                continue

            # Find files that import/use this file
            for other_file, deps in self.component_map.dependency_graph.items():
                if str(current_file) in str(deps) and other_file not in visited:
                    visited.add(other_file)
                    related_files.append(
                        {
                            "file_path": other_file,
                            "relationship": "imports_from",
                            "distance": distance + 1,
                        }
                    )
                    queue.append((other_file, distance + 1))

        return {
            "primary_file": primary_file,
            "related_files": related_files,
            "context_radius": context_radius,
        }

    def analyze_architecture(self) -> dict:
        """Provide overview of system architecture."""
        components = []
        relationships = []

        for name, info in self.component_map.components.items():
            components.append(
                {
                    "name": name,
                    "type": info.get("type", "unknown"),
                    "description": info.get("description", ""),
                    "path": info.get("path", ""),
                }
            )

        for rel in self.component_map.relationships:
            relationships.append(
                {
                    "source": rel.source_file,
                    "target": rel.target_file,
                    "type": rel.relationship_type,
                }
            )

        return {
            "components": components,
            "relationships": relationships,
            "total_files_analyzed": len(list(self.base_path.rglob("*.py"))),
            "patterns_identified": len(
                set(rel.relationship_type for rel in self.component_map.relationships)
            ),
        }


# Global context engine instance
context_engine = ContextEngine()


# Convenience functions
def get_task_context(task_description: str) -> dict:
    """Get optimized context for a development task."""
    return context_engine.get_context_for_task(task_description)


def get_multi_file_context(primary_file: str, context_radius: int = 2) -> dict:
    """Get multi-file context for better understanding."""
    return context_engine.get_multi_file_context(primary_file, context_radius)


def analyze_architecture() -> dict:
    """Get architectural analysis."""
    return context_engine.analyze_architecture()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "analyze":
            # Analyze architecture
            analysis = analyze_architecture()
            print("Architecture Analysis:")
            print(f"- Components: {len(analysis['components'])}")
            print(f"- Relationships: {len(analysis['relationships'])}")
            print(f"- Files analyzed: {analysis['total_files_analyzed']}")

        elif command == "context":
            if len(sys.argv) > 2:
                task = " ".join(sys.argv[2:])
                context = get_task_context(task)
                print(f"Task Context for: '{task}'")
                print(f"Task Type: {context['task_type']}")

                print(f"Relevant Files ({len(context['relevant_files'])}):")
                for file in context["relevant_files"][:3]:
                    print(f"  - {file['file_path']} (score: {file['relevance_score']})")

                if context["suggested_patterns"]:
                    print("Suggested Patterns:")
                    for pattern in context["suggested_patterns"]:
                        print(f"  - {pattern['pattern_name']}: {pattern['reason']}")

        elif command == "multifile":
            if len(sys.argv) > 2:
                primary = sys.argv[2]
                context = get_multi_file_context(
                    primary, int(sys.argv[3]) if len(sys.argv) > 3 else 2
                )
                print(f"Multi-file context for {primary}:")

                for related in context["related_files"]:
                    print(
                        f"  - {related['file_path']} ({related['relationship']}, distance: {related['distance']})"
                    )

        else:
            print("Commands: analyze, context <task>, multifile <file> [radius]")

    else:
        print("TTA.dev Context Engine")
        print(f"Analyzing codebase from: {context_engine.base_path.absolute()}")
        analysis = analyze_architecture()
        print(f"Components found: {len(analysis['components'])}")
        print(f"Relationship patterns: {analysis['patterns_identified']}")
        print(f"Files indexed: {analysis['total_files_analyzed']}")
