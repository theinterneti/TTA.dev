#!/usr/bin/env python3
"""
ACE (Autonomous Cognitive Engine) Implementation
Captures and preserves development lessons for future product operations
"""

import json
import datetime
import ast
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class DevelopmentPattern:
    """Represents a captured development pattern."""

    name: str
    description: str
    context: str
    code_example: Optional[str]
    success_metrics: Dict[str, Any]
    reusability_score: float
    tags: List[str]
    captured_date: str


@dataclass
class IntegrationLearning:
    """Represents lessons learned from platform integration."""

    integration_type: str
    platform_component: str
    challenge: str
    solution: str
    performance_impact: Dict[str, Any]
    best_practices: List[str]
    captured_date: str


@dataclass
class QualityStrategy:
    """Represents a successful quality assurance approach."""

    strategy_name: str
    quality_dimension: str  # testing, performance, security, etc.
    implementation: str
    success_metrics: Dict[str, Any]
    effort_level: str  # low, medium, high
    effectiveness_score: float
    captured_date: str


class ACEKnowledgeCapture:
    """Main ACE system for capturing and preserving development lessons."""

    def __init__(self, base_path: Path = Path(".ace")):
        self.base_path = base_path
        self.ensure_directory_structure()

    def ensure_directory_structure(self):
        """Ensure ACE directory structure exists."""
        directories = [
            "knowledge-base/development-patterns",
            "knowledge-base/integration-learnings",
            "knowledge-base/performance-insights",
            "knowledge-base/quality-strategies",
            "patterns/workflow-templates",
            "patterns/testing-strategies",
            "patterns/deployment-patterns",
            "learnings/daily-insights",
            "learnings/milestone-reviews",
            "learnings/retrospectives",
            "templates/project-structure",
            "templates/tooling-configs",
            "templates/quality-gates",
        ]

        for directory in directories:
            (self.base_path / directory).mkdir(parents=True, exist_ok=True)

    def capture_development_pattern(self, pattern: DevelopmentPattern):
        """Capture a successful development pattern."""
        patterns_dir = self.base_path / "knowledge-base/development-patterns"
        pattern_file = patterns_dir / f"{pattern.name}_{pattern.captured_date}.json"

        with open(pattern_file, "w") as f:
            json.dump(asdict(pattern), f, indent=2)

        print(f"✅ Development pattern captured: {pattern.name}")
        return pattern_file

    def capture_integration_learning(self, learning: IntegrationLearning):
        """Capture lessons from platform integration."""
        learnings_dir = self.base_path / "knowledge-base/integration-learnings"
        learning_file = learnings_dir / f"{learning.integration_type}_{learning.captured_date}.json"

        with open(learning_file, "w") as f:
            json.dump(asdict(learning), f, indent=2)

        print(f"✅ Integration learning captured: {learning.integration_type}")
        return learning_file

    def capture_quality_strategy(self, strategy: QualityStrategy):
        """Capture a successful quality strategy."""
        strategies_dir = self.base_path / "knowledge-base/quality-strategies"
        strategy_file = strategies_dir / f"{strategy.strategy_name}_{strategy.captured_date}.json"

        with open(strategy_file, "w") as f:
            json.dump(asdict(strategy), f, indent=2)

        print(f"✅ Quality strategy captured: {strategy.strategy_name}")
        return strategy_file

    def analyze_codebase_patterns(self, source_path: Path = Path("packages/tta-rebuild")):
        """Analyze codebase for recurring patterns."""
        patterns = []

        for py_file in source_path.rglob("*.py"):
            if py_file.name.startswith("test_"):
                continue

            try:
                with open(py_file, "r") as f:
                    content = f.read()
                    tree = ast.parse(content)

                # Analyze for patterns
                file_patterns = self._extract_code_patterns(tree, py_file, content)
                patterns.extend(file_patterns)

            except (SyntaxError, UnicodeDecodeError):
                continue

        return patterns

    def _extract_code_patterns(
        self, tree: ast.AST, file_path: Path, content: str
    ) -> List[DevelopmentPattern]:
        """Extract patterns from AST."""
        patterns = []

        # Pattern: Class inheritance patterns
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.bases:  # Has inheritance
                    base_names = [self._get_name(base) for base in node.bases]
                    pattern = DevelopmentPattern(
                        name=f"inheritance_{node.name}",
                        description=f"Class {node.name} inherits from {', '.join(base_names)}",
                        context=f"File: {file_path}",
                        code_example=self._extract_class_code(content, node.name),
                        success_metrics={"complexity": "manageable", "reusability": "high"},
                        reusability_score=0.8,
                        tags=["inheritance", "class-design"],
                        captured_date=datetime.date.today().isoformat(),
                    )
                    patterns.append(pattern)

        return patterns

    def _get_name(self, node):
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return "Unknown"

    def _extract_class_code(self, content: str, class_name: str) -> str:
        """Extract class code from content."""
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if f"class {class_name}" in line:
                # Extract class definition (simplified)
                class_lines = [line]
                for j in range(i + 1, min(i + 10, len(lines))):
                    if lines[j].strip() and not lines[j].startswith(" "):
                        break
                    class_lines.append(lines[j])
                return "\n".join(class_lines)
        return ""

    def generate_session_report(self, session_data: Dict[str, Any]):
        """Generate a comprehensive session report."""
        date_str = datetime.date.today().isoformat()
        report_file = self.base_path / "learnings/daily-insights" / f"session_report_{date_str}.md"

        with open(report_file, "w") as f:
            f.write(f"# ACE Session Report - {date_str}\n\n")
            f.write(f"**Session ID:** {session_data.get('session_id', 'N/A')}\n")
            f.write(f"**Focus Area:** {session_data.get('focus_area', 'TTA Development')}\n\n")

            f.write("## Development Patterns Captured\n\n")
            for pattern in session_data.get("captured_patterns", []):
                f.write(
                    f"- **{pattern.get('name', 'Unknown')}**: {pattern.get('description', '')}\n"
                )

            f.write("\n## Integration Learnings\n\n")
            for learning in session_data.get("integration_learnings", []):
                f.write(
                    f"- **{learning.get('integration_type', 'Unknown')}**: {learning.get('challenge', '')}\n"
                )

            f.write("\n## Quality Insights\n\n")
            for insight in session_data.get("quality_insights", []):
                f.write(f"- {insight}\n")

            f.write("\n## Performance Notes\n\n")
            for note in session_data.get("performance_notes", []):
                f.write(f"- {note}\n")

            f.write(f"\n## Next Session Recommendations\n\n")
            f.write("- Continue monitoring development patterns\n")
            f.write("- Focus on integration performance optimization\n")
            f.write("- Document quality gate effectiveness\n")

        print(f"✅ Session report generated: {report_file}")
        return report_file

    def create_future_product_template(self, template_name: str, based_on_patterns: List[str]):
        """Create a reusable template for future products."""
        template_dir = self.base_path / "templates/project-structure"
        template_file = template_dir / f"{template_name}_template.json"

        template_data = {
            "name": template_name,
            "description": f"Project template based on TTA development patterns",
            "based_on_patterns": based_on_patterns,
            "directory_structure": {
                "src/": "Source code",
                "tests/": "Test suite",
                "docs/": "Documentation",
                "examples/": "Usage examples",
                "scripts/": "Development scripts",
            },
            "required_files": [
                "pyproject.toml",
                "README.md",
                "CHANGELOG.md",
                ".gitignore",
                "pytest.ini",
            ],
            "recommended_tools": [
                "uv (package management)",
                "ruff (linting/formatting)",
                "pytest (testing)",
                "pyright (type checking)",
            ],
            "quality_gates": [
                "100% test coverage",
                "Type checking passes",
                "Linting passes",
                "Documentation complete",
            ],
            "created_date": datetime.date.today().isoformat(),
        }

        with open(template_file, "w") as f:
            json.dump(template_data, f, indent=2)

        print(f"✅ Future product template created: {template_name}")
        return template_file


def main():
    """Main ACE capture function."""
    ace = ACEKnowledgeCapture()

    print("🧠 ACE Knowledge Capture System Initialized")
    print("📊 Analyzing current codebase for patterns...")

    # Analyze existing patterns
    patterns = ace.analyze_codebase_patterns()
    print(f"✅ Found {len(patterns)} development patterns")

    # Capture a few example patterns
    for pattern in patterns[:3]:  # Capture first 3 patterns
        ace.capture_development_pattern(pattern)

    # Create sample session data
    session_data = {
        "session_id": f"ace_session_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "focus_area": "TTA Rebuild Development",
        "captured_patterns": [asdict(p) for p in patterns[:3]],
        "integration_learnings": [],
        "quality_insights": [
            "Test-driven development effective for primitive validation",
            "Type hints crucial for API clarity",
            "Observability integration requires careful planning",
        ],
        "performance_notes": [
            "Async/await patterns show good performance",
            "Caching primitives reduce latency significantly",
        ],
    }

    # Generate session report
    ace.generate_session_report(session_data)

    # Create a future product template
    ace.create_future_product_template(
        "narrative_application",
        ["inheritance_patterns", "async_workflows", "primitive_composition"],
    )

    print("🎯 ACE Session Complete - Knowledge preserved for future operations!")


if __name__ == "__main__":
    main()
