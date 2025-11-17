#!/usr/bin/env python3
"""
Persona Auto-Activator - Automatically select and activate chatmode/persona.

This script analyzes the current workspace context and AGENTS.md to determine
the most appropriate persona/chatmode for the agent to assume.

Integrates with:
- .tta/chatmodes/ - Hypertool chatmode definitions
- AGENTS.md - Agent context and guidance
- .hypertool/mcp_servers.json - Available MCP tools per persona
"""

import json
import re
from pathlib import Path
from typing import Any


class PersonaActivator:
    """Automatically activate appropriate chatmode/persona for agents."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root)
        self.chatmodes_dir = workspace_root / ".tta" / "chatmodes"
        self.agents_md = workspace_root / "AGENTS.md"
        self.hypertool_config = workspace_root / ".hypertool" / "mcp_servers.json"

    def analyze_workspace_context(self) -> dict[str, Any]:
        """
        Analyze workspace to determine current development context.

        Returns:
            Context dictionary with detected patterns
        """
        context = {
            "active_files": [],
            "open_directories": [],
            "detected_patterns": [],
            "recommended_persona": None,
        }

        # Pattern detection (simplified - would use VS Code API in real implementation)
        workspace_files = list(self.workspace_root.rglob("*.py"))

        # Backend development indicators
        if any("packages/tta-dev-primitives" in str(f) for f in workspace_files):
            context["detected_patterns"].append("backend-development")

        # Frontend development indicators
        if any("apps/observability-ui" in str(f) for f in workspace_files):
            context["detected_patterns"].append("frontend-development")

        # Testing indicators
        if any("tests/" in str(f) for f in workspace_files):
            context["detected_patterns"].append("testing")

        # Observability indicators
        if any("observability" in str(f).lower() for f in workspace_files):
            context["detected_patterns"].append("observability")

        # DevOps indicators
        if (self.workspace_root / "docker-compose.yml").exists():
            context["detected_patterns"].append("devops")

        return context

    def parse_agents_md(self) -> dict[str, Any]:
        """
        Parse AGENTS.md to extract persona mappings and requirements.

        Returns:
            Dictionary of persona definitions from AGENTS.md
        """
        if not self.agents_md.exists():
            return {}

        with open(self.agents_md) as f:
            content = f.read()

        personas = {}

        # Extract package-specific agent instructions
        package_pattern = r"\*\*([^*]+)\*\*\s+\|\s+([^|]+)\s+\|\s+\[`([^`]+)`\]"
        for match in re.finditer(package_pattern, content):
            package_name = match.group(1).strip()
            status = match.group(2).strip()
            agents_path = match.group(3).strip()

            personas[package_name] = {
                "status": status,
                "instructions_path": agents_path,
                "active": status == "✅ Active",
            }

        return personas

    def load_chatmodes(self) -> dict[str, Any]:
        """Load Hypertool chatmode definitions."""
        if not self.chatmodes_dir.exists():
            return {}

        chatmodes = {}

        for chatmode_file in self.chatmodes_dir.glob("*.json"):
            with open(chatmode_file) as f:
                chatmode = json.load(f)
                chatmodes[chatmode_file.stem] = chatmode

        return chatmodes

    def select_persona(self, context: dict[str, Any]) -> str | None:
        """
        Select appropriate persona based on workspace context.

        Args:
            context: Workspace context from analyze_workspace_context()

        Returns:
            Persona name or None
        """
        patterns = context["detected_patterns"]

        # Priority mapping based on detected patterns
        pattern_to_persona = {
            "backend-development": "tta-backend-engineer",
            "frontend-development": "tta-frontend-engineer",
            "testing": "tta-testing-specialist",
            "observability": "tta-observability-expert",
            "devops": "tta-devops-engineer",
        }

        # Select highest priority persona
        for pattern in patterns:
            if pattern in pattern_to_persona:
                return pattern_to_persona[pattern]

        # Default to backend engineer if no specific pattern
        return "tta-backend-engineer"

    def get_persona_mcp_tools(self, persona: str) -> list[str]:
        """
        Get MCP tools relevant to selected persona.

        Args:
            persona: Persona name (e.g., "tta-backend-engineer")

        Returns:
            List of MCP server names relevant to this persona
        """
        if not self.hypertool_config.exists():
            return []

        with open(self.hypertool_config) as f:
            config = json.load(f)

        servers = config.get("mcpServers", {})

        # Persona-specific tool mapping
        persona_tools = {
            "tta-backend-engineer": ["context7", "github", "sequential-thinking"],
            "tta-frontend-engineer": ["context7", "playwright", "github"],
            "tta-testing-specialist": ["playwright", "github", "sequential-thinking"],
            "tta-observability-expert": ["grafana", "github", "context7"],
            "tta-devops-engineer": ["github", "grafana", "sequential-thinking"],
            "tta-data-scientist": ["context7", "sequential-thinking"],
        }

        return persona_tools.get(persona, [])

    def generate_activation_config(self) -> dict[str, Any]:
        """
        Generate configuration for automatic persona activation.

        Returns:
            Configuration dictionary for agent initialization
        """
        context = self.analyze_workspace_context()
        selected_persona = self.select_persona(context)
        mcp_tools = (
            self.get_persona_mcp_tools(selected_persona)
            if selected_persona
            else []
        )
        personas_md = self.parse_agents_md()

        return {
            "auto_activate": True,
            "selected_persona": selected_persona,
            "context": context,
            "mcp_tools": mcp_tools,
            "instructions": {
                "primary": str(self.agents_md),
                "persona_specific": None,  # Would load from chatmode definition
            },
            "available_personas": list(personas_md.keys()),
        }

    def write_vscode_persona_config(self) -> None:
        """Write persona activation config for VS Code Copilot."""
        config = self.generate_activation_config()

        vscode_dir = self.workspace_root / ".vscode"
        vscode_dir.mkdir(exist_ok=True)

        persona_config_file = vscode_dir / "copilot-persona.json"

        with open(persona_config_file, "w") as f:
            json.dump(config, f, indent=2)

        print(f"✅ VS Code persona config written to: {persona_config_file}")
        print(f"   Selected persona: {config['selected_persona']}")
        print(f"   MCP tools: {', '.join(config['mcp_tools'])}")

    def write_cline_persona_config(self) -> None:
        """Write persona activation config for Cline."""
        config = self.generate_activation_config()

        cline_dir = self.workspace_root / ".cline"
        cline_dir.mkdir(exist_ok=True)

        persona_config_file = cline_dir / "persona-config.json"

        with open(persona_config_file, "w") as f:
            json.dump(config, f, indent=2)

        print(f"✅ Cline persona config written to: {persona_config_file}")


def main():
    """CLI interface for persona activator."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Automatically select and activate agent persona"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace root directory",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze workspace and show recommended persona",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate persona activation configs",
    )
    parser.add_argument(
        "--vscode",
        action="store_true",
        help="Generate VS Code persona config",
    )
    parser.add_argument(
        "--cline",
        action="store_true",
        help="Generate Cline persona config",
    )

    args = parser.parse_args()

    activator = PersonaActivator(args.workspace)

    if args.analyze:
        config = activator.generate_activation_config()
        print(json.dumps(config, indent=2))
    elif args.generate or args.vscode or args.cline:
        if args.vscode or args.generate:
            activator.write_vscode_persona_config()
        if args.cline or args.generate:
            activator.write_cline_persona_config()
    else:
        # Default: show current configuration
        config = activator.generate_activation_config()
        print(f"Recommended persona: {config['selected_persona']}")
        print(f"Detected patterns: {', '.join(config['context']['detected_patterns'])}")
        print(f"MCP tools: {', '.join(config['mcp_tools'])}")


if __name__ == "__main__":
    main()
