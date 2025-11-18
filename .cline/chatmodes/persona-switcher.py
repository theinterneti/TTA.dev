#!/usr/bin/env python3
"""
Persona Switching Mechanism for Cline Agent Primitives

This module implements dynamic persona switching for role-based expertise in Cline.
It reads chatmode files and provides a mechanism to switch between different personas
based on the current task context.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Persona:
    """Represents a chatmode persona with its configuration."""

    name: str
    display_name: str
    context: str
    tools: list[str]
    token_budget: int
    focus: str
    tags: list[str]
    instructions: str


class PersonaSwitcher:
    """Manages persona switching based on task context and user requirements."""

    def __init__(self):
        self.chatmodes_dir = Path(".cline/chatmodes")
        self.personas: dict[str, Persona] = {}
        self.active_persona: str | None = None

        # Load all available chatmodes
        self._load_personas()

        # Auto-switch to generic persona if available, or first available
        if self.personas:
            self.active_persona = next(iter(self.personas.keys()))

    def _load_personas(self) -> None:
        """Load all chatmode files and parse their configurations."""
        if not self.chatmodes_dir.exists():
            return

        for file_path in self.chatmodes_dir.glob("*.chatmode.md"):
            try:
                persona = self._parse_chatmode_file(file_path)
                if persona:
                    self.personas[persona.name] = persona
            except Exception as e:
                print(f"Warning: Failed to load persona from {file_path}: {e}")

    def _parse_chatmode_file(self, file_path: Path) -> Persona | None:
        """Parse a chatmode file and return a Persona object."""
        content = file_path.read_text(encoding="utf-8")

        # Split YAML frontmatter and instructions
        if not content.startswith("---"):
            return None

        try:
            # Find the end of YAML frontmatter
            end_marker = content.find("---", 3)
            if end_marker == -1:
                return None

            yaml_content = content[3:end_marker].strip()
            instructions = content[end_marker + 3 :].strip()

            # Parse YAML metadata
            metadata = yaml.safe_load(yaml_content)

            return Persona(
                name=metadata.get("persona", file_path.stem),
                display_name=metadata.get(
                    "displayName", file_path.stem.replace("-", " ").title()
                ),
                context=metadata.get("context", "general"),
                tools=metadata.get("tools", []),
                token_budget=metadata.get("token_budget", 4000),
                focus=metadata.get("focus", ""),
                tags=metadata.get("tags", []),
                instructions=instructions,
            )

        except yaml.YAMLError:
            return None

    def list_personas(self) -> dict[str, str]:
        """Return a dictionary of available personas with their display names."""
        return {name: persona.display_name for name, persona in self.personas.items()}

    def switch_persona(self, persona_name: str) -> bool:
        """Switch to the specified persona if it exists."""
        if persona_name in self.personas:
            self.active_persona = persona_name
            return True
        return False

    def get_active_persona(self) -> Persona | None:
        """Get the currently active persona."""
        if self.active_persona and self.active_persona in self.personas:
            return self.personas[self.active_persona]
        return None

    def auto_switch_persona(self, task_description: str) -> str | None:
        """
        Automatically switch to the best persona for the given task description.
        Uses keyword matching and context awareness.
        """
        task_lower = task_description.lower()

        # Define persona selection rules
        persona_rules = {
            "backend-developer": [
                "backend",
                "api",
                "python",
                "server",
                "database",
                "sql",
                "fastapi",
                "rest",
                "async",
                "workflow",
                "primitive",
            ],
            "frontend-developer": [
                "frontend",
                "ui",
                "react",
                "javascript",
                "typescript",
                "html",
                "css",
                "component",
                "user interface",
                "web",
            ],
            "data-scientist": [
                "data",
                "analysis",
                "machine learning",
                "ml",
                "statistics",
                "jupyter",
                "pandas",
                "numpy",
                "visualization",
                "dataset",
            ],
            "devops-engineer": [
                "infrastructure",
                "deployment",
                "docker",
                "kubernetes",
                "ci/cd",
                "pipeline",
                "aws",
                "gcp",
                "azure",
                "terraform",
                "ansible",
            ],
            "testing-specialist": [
                "test",
                "testing",
                "pytest",
                "unit test",
                "integration test",
                "coverage",
                "tdd",
                "qa",
                "validation",
                "mock",
            ],
            "observability-expert": [
                "monitoring",
                "observability",
                "tracing",
                "metrics",
                "logging",
                "prometheus",
                "opentelemetry",
                "grafana",
                "alert",
            ],
        }

        # Score personas based on keyword matches
        scores = {}
        for persona_name, keywords in persona_rules.items():
            if persona_name in self.personas:
                score = sum(1 for keyword in keywords if keyword in task_lower)
                scores[persona_name] = score

        # Select the persona with the highest score
        if scores:
            best_persona = max(scores.items(), key=lambda x: x[1])
            if best_persona[1] > 0:  # Only switch if there's a match
                self.switch_persona(best_persona[0])
                return best_persona[0]

        return None

    def export_config(self) -> str:
        """Export the current persona configuration for Cline integration."""
        persona = self.get_active_persona()
        if not persona:
            return "# No active persona configured"

        config = f"""# Active Persona: {persona.display_name}
# Context: {persona.context}
# Focus: {persona.focus}
# Tags: {", ".join(persona.tags)}

{persona.instructions}
"""
        return config

    def get_capabilities(self) -> dict[str, any]:
        """Get MCP server capabilities for the active persona."""
        persona = self.get_active_persona()
        if not persona:
            return {}

        return {
            "persona": persona.name,
            "tools": persona.tools,
            "token_budget": persona.token_budget,
            "capabilities": [
                {
                    "name": "persona_switch",
                    "description": "Switch between different expert personas",
                },
                {
                    "name": "auto_persona",
                    "description": "Automatically select appropriate persona based on task",
                },
                {
                    "name": "expert_focus",
                    "description": "Apply specialized knowledge and patterns",
                },
            ]
            + [
                {
                    "name": f"expert_{tag}",
                    "description": f"Specialized expertise in {tag}",
                }
                for tag in persona.tags
            ],
        }


# Global persona switcher instance
persona_switcher = PersonaSwitcher()


def switch_persona(persona_name: str) -> bool:
    """Convenience function to switch personas."""
    return persona_switcher.switch_persona(persona_name)


def auto_switch_persona(task_description: str) -> str | None:
    """Convenience function for automatic persona switching."""
    return persona_switcher.auto_switch_persona(task_description)


def get_active_persona_config() -> str:
    """Get the current persona configuration for Cline."""
    return persona_switcher.export_config()


def list_available_personas() -> dict[str, str]:
    """List all available personas."""
    return persona_switcher.list_personas()


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "list":
            personas = list_available_personas()
            print("Available Personas:")
            for name, display in personas.items():
                print(f"  - {name}: {display}")

        elif command == "switch" and len(sys.argv) > 2:
            persona_name = sys.argv[2]
            if switch_persona(persona_name):
                print(f"Switched to persona: {persona_name}")
                print(get_active_persona_config())
            else:
                print(f"Persona not found: {persona_name}")

        elif command == "auto" and len(sys.argv) > 2:
            task_desc = " ".join(sys.argv[2:])
            result = auto_switch_persona(task_desc)
            if result:
                print(f"Auto-switched to persona: {result}")
                print(get_active_persona_config())
            else:
                print("No matching persona found")

        elif command == "config":
            print(get_active_persona_config())

        else:
            print(
                "Usage: python persona-switcher.py [list|switch <persona>|auto <task>|config]"
            )
    else:
        print("Current active persona:")
        print(get_active_persona_config())
