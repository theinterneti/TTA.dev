#!/usr/bin/env python3
"""
Generate AI assistant configuration files from universal instruction sources.

This script uses tta-dev-primitives to orchestrate the generation of
tool-specific configuration files (Copilot, Cline, Cursor, Augment) from
a single source of truth in .universal-instructions/.

Usage:
    uv run python scripts/generate_assistant_configs.py --tool copilot
    uv run python scripts/generate_assistant_configs.py --tool all
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

# Add the package to sys.path so it can be imported
_script_dir = Path(__file__).parent
_package_dir = _script_dir.parent / "packages" / "tta-dev-primitives" / "src"
if _package_dir.exists():
    sys.path.insert(0, str(_package_dir))

import yaml
from pydantic import BaseModel, Field

# When running from uv, this will work after: uv pip install -e packages/tta-dev-primitives
from tta_dev_primitives import (
    WorkflowContext,
    WorkflowPrimitive,
)

# ============================================================================
# Data Models
# ============================================================================


class PathSpecificRule(BaseModel):
    """Represents a path-specific instruction rule."""

    source_file: str = Field(..., description="Source markdown file in universal-instructions")
    apply_to: str = Field(..., description="Glob pattern for files this applies to")
    description: str = Field(..., description="Brief description of the rule")


class ToolConfig(BaseModel):
    """Configuration for a specific AI coding assistant tool."""

    name: str = Field(..., description="Tool name (copilot, cline, cursor, augment)")
    output_dir: str = Field(..., description="Output directory for generated files")
    repository_wide_file: str | None = Field(None, description="Repository-wide instructions file")
    # Note: agent_instructions_file removed - AGENTS.md is now workspace-wide hub
    path_specific_dir: str | None = Field(None, description="Directory for path-specific rules")
    path_specific_extension: str = Field(
        ".md", description="File extension for path-specific files"
    )
    frontmatter_format: str = Field("yaml", description="Frontmatter format (yaml, none)")


# ============================================================================
# File I/O Primitives
# ============================================================================


class ReadFilePrimitive(WorkflowPrimitive[Path, str]):
    """Read content from a file."""

    async def execute(self, input_data: Path, context: WorkflowContext) -> str:
        """
        Read file content.

        Args:
            input_data: Path to file
            context: Workflow context

        Returns:
            File content as string
        """
        with open(input_data, encoding="utf-8") as f:
            return f.read()


class WriteFilePrimitive(WorkflowPrimitive[dict[str, Any], Path]):
    """Write content to a file."""

    async def execute(self, input_data: dict[str, Any], context: WorkflowContext) -> Path:
        """
        Write content to file.

        Args:
            input_data: Dict with 'path' and 'content' keys
            context: Workflow context

        Returns:
            Path to written file
        """
        path = Path(input_data["path"])
        content = input_data["content"]

        # Create parent directories if needed
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return path


class ReadYAMLPrimitive(WorkflowPrimitive[Path, dict[str, Any]]):
    """Read YAML configuration file."""

    async def execute(self, input_data: Path, context: WorkflowContext) -> dict[str, Any]:
        """
        Read YAML file and parse to dict.

        Args:
            input_data: Path to YAML file
            context: Workflow context

        Returns:
            Parsed YAML as dict
        """
        with open(input_data, encoding="utf-8") as f:
            return yaml.safe_load(f)


# ============================================================================
# Content Processing Primitives
# ============================================================================


class CombineCorePrimitive(WorkflowPrimitive[list[str], str]):
    """Combine core instruction files into repository-wide instructions."""

    async def execute(self, input_data: list[str], context: WorkflowContext) -> str:
        """
        Combine core instruction files.

        Args:
            input_data: List of file contents
            context: Workflow context

        Returns:
            Combined markdown content
        """
        sections = []
        titles = ["Project Overview", "Architecture", "Development Workflow", "Quality Standards"]

        for title, content in zip(titles, input_data, strict=False):
            sections.append(f"# {title}\n\n{content}")

        return "\n\n".join(sections)


class CombineAgentBehaviorPrimitive(WorkflowPrimitive[list[str], str]):
    """Combine agent behavior files into agent instructions."""

    async def execute(self, input_data: list[str], context: WorkflowContext) -> str:
        """
        Combine agent behavior files.

        Args:
            input_data: List of file contents
            context: Workflow context

        Returns:
            Combined markdown content
        """
        sections = []
        titles = ["Communication Style", "Priority Order", "Anti-Patterns to Avoid"]

        for title, content in zip(titles, input_data, strict=False):
            sections.append(f"# {title}\n\n{content}")

        return "\n\n".join(sections)


class AddFrontmatterPrimitive(WorkflowPrimitive[dict[str, Any], str]):
    """Add YAML frontmatter to markdown content."""

    def __init__(self, format_type: str = "yaml"):
        """
        Initialize frontmatter primitive.

        Args:
            format_type: Format type ('yaml' or 'none')
        """
        super().__init__()
        self.format_type = format_type

    async def execute(self, input_data: dict[str, Any], context: WorkflowContext) -> str:
        """
        Add frontmatter to content.

        Args:
            input_data: Dict with 'content', 'apply_to', 'description' keys
            context: Workflow context

        Returns:
            Content with frontmatter
        """
        content = input_data["content"]

        if self.format_type == "none":
            return content

        # YAML frontmatter
        frontmatter = f"""---
applyTo: "{input_data["apply_to"]}"
description: "{input_data["description"]}"
---

"""
        return frontmatter + content


# ============================================================================
# Configuration Generator Workflows
# ============================================================================


class GenerateRepositoryWidePrimitive(WorkflowPrimitive[ToolConfig, Path]):
    """Generate repository-wide instructions file."""

    def __init__(self, universal_dir: Path):
        """
        Initialize with universal instructions directory.

        Args:
            universal_dir: Path to .universal-instructions/
        """
        super().__init__()
        self.universal_dir = universal_dir

    async def execute(self, input_data: ToolConfig, context: WorkflowContext) -> Path:
        """
        Generate repository-wide instructions.

        Args:
            input_data: Tool configuration
            context: Workflow context

        Returns:
            Path to generated file
        """
        if not input_data.repository_wide_file:
            return Path()  # Skip if not configured

        # Read core instruction files sequentially (simpler than parallel for 4 files)
        core_dir = self.universal_dir / "core"
        read_file = ReadFilePrimitive()

        files_to_read = [
            core_dir / "project-overview.md",
            core_dir / "architecture.md",
            core_dir / "development-workflow.md",
            core_dir / "quality-standards.md",
        ]

        # Read all files
        file_contents = []
        for file_path in files_to_read:
            content = await read_file.execute(file_path, context)
            file_contents.append(content)

        # Combine contents
        combiner = CombineCorePrimitive()
        combined = await combiner.execute(file_contents, context)

        # Write output
        writer = WriteFilePrimitive()
        output_path = Path(input_data.output_dir) / input_data.repository_wide_file
        result = await writer.execute({"path": output_path, "content": combined}, context)

        return result


class GenerateAgentsHubPrimitive(WorkflowPrimitive[Path, Path]):
    """Generate workspace-wide AGENTS.md hub file."""

    def __init__(self, universal_dir: Path):
        """
        Initialize with universal instructions directory.

        Args:
            universal_dir: Path to .universal-instructions/
        """
        super().__init__()
        self.universal_dir = universal_dir

    async def execute(self, input_data: Path, context: WorkflowContext) -> Path:
        """
        Generate AGENTS.md hub file.

        Args:
            input_data: Workspace root path
            context: Workflow context

        Returns:
            Path to generated AGENTS.md
        """
        # Read agent behavior files
        behavior_dir = self.universal_dir / "agent-behavior"
        read_file = ReadFilePrimitive()

        files_to_read = [
            behavior_dir / "communication.md",
            behavior_dir / "priorities.md",
            behavior_dir / "anti-patterns.md",
        ]

        # Read all files
        file_contents = []
        for file_path in files_to_read:
            content = await read_file.execute(file_path, context)
            file_contents.append(content)

        # Create hub header with tool reference table
        hub_header = """# Agent Instructions Hub

This file serves as the **workspace-wide hub** for AI agent behavior across all coding assistants.

## Purpose

`AGENTS.md` defines how AI agents should behave when working in this repository. All AI coding assistants (GitHub Copilot, Cline, Cursor, Augment) should follow these behavioral guidelines.

## Tool-Specific Configuration

Each coding assistant has its own technical configuration file that contains project-specific details:

| Tool | Configuration File | Purpose |
|------|-------------------|---------|
| **GitHub Copilot** | `.github/copilot-instructions.md` | Repository-wide technical instructions |
| | `.github/instructions/*.instructions.md` | Path-specific instructions with frontmatter |
| **Cline** | `.cline/instructions.md` | Repository-wide technical instructions |
| | `.cline/rules/*.md` | Path-specific rules |
| **Cursor** | `.cursor/instructions.md` | Repository-wide technical instructions |
| | `.cursor/rules/*.md` | Path-specific rules |
| **Augment** | `.augment/instructions.md` | Repository-wide technical instructions |
| | `.augment/rules/*.md` | Path-specific rules |

**Important**: This `AGENTS.md` file defines agent *behavior* (how to communicate, prioritize, and think), while the tool-specific configs contain *technical project details* (architecture, dependencies, coding standards).

---

"""

        # Create footer with config management info
        hub_footer = """
---

## Configuration Management

All agent configurations are generated from the universal instruction system located in `.universal-instructions/`.

**To regenerate all tool-specific configurations:**
```bash
./scripts/generate-configs.sh
```

This ensures consistency across all AI coding assistants.

## Source of Truth

The `.universal-instructions/` directory contains:
- `core/` - Project overview, architecture, development workflow, quality standards
- `path-specific/` - Instructions for different file types (packages, tests, scripts, docs)
- `agent-behavior/` - Communication, priorities, anti-patterns (source for this AGENTS.md)
- `mappings/` - Tool-specific configuration mappings

**All changes should be made to `.universal-instructions/` and regenerated**, not edited directly in tool-specific files or this AGENTS.md.
"""

        # Combine all content
        combined_content = hub_header + "\n".join(file_contents) + hub_footer

        # Write to workspace root
        output_path = input_data / "AGENTS.md"
        writer = WriteFilePrimitive()
        result = await writer.execute({"path": output_path, "content": combined_content}, context)

        return result


class GenerateClaudeHubPrimitive(WorkflowPrimitive[Path, Path]):
    """Generate workspace-wide CLAUDE.md model-specific hub file."""

    def __init__(self, universal_dir: Path):
        """
        Initialize with universal instructions directory.

        Args:
            universal_dir: Path to .universal-instructions/
        """
        super().__init__()
        self.universal_dir = universal_dir

    async def execute(self, input_data: Path, context: WorkflowContext) -> Path:
        """
        Generate CLAUDE.md hub file.

        Args:
            input_data: Workspace root path
            context: Workflow context

        Returns:
            Path to generated CLAUDE.md
        """
        # Read Claude-specific files
        claude_dir = self.universal_dir / "claude-specific"
        read_file = ReadFilePrimitive()

        files_to_read = [
            claude_dir / "capabilities.md",
            claude_dir / "workflows.md",
            claude_dir / "preferences.md",
            claude_dir / "mcp-integration.md",
        ]

        # Read all files
        file_contents = []
        for file_path in files_to_read:
            content = await read_file.execute(file_path, context)
            file_contents.append(content)

        # Get current date for footer
        from datetime import datetime

        current_date = datetime.now().strftime("%B %d, %Y")

        # Create hub header
        hub_header = """# Claude-Specific Instructions

> **Note**: This file provides Claude-specific guidance. For general agent behavior applicable to all AI assistants, see [`AGENTS.md`](./AGENTS.md).

## Purpose

`CLAUDE.md` contains instructions specific to Claude's capabilities, reasoning style, and features. This file is used by:

- **Cline** (uses Claude as backend)
- **Augment** (when configured with Claude models)
- **GitHub Copilot** (when using Claude models)
- **Any tool using Claude 3.5 Sonnet, Opus, or other Claude models**

## When to Use CLAUDE.md vs AGENTS.md

| File | Purpose | Example Content |
|------|---------|-----------------|
| **AGENTS.md** | Universal behavior for all agents | "Be concise", "Prioritize type safety", "Use primitives" |
| **CLAUDE.md** | Claude-specific capabilities/preferences | "Use artifacts for code generation", "Leverage extended context" |

**Rule of thumb**: If the instruction applies to any AI assistant (Copilot, Cline, Cursor), put it in `AGENTS.md`. If it's specific to Claude's capabilities, put it here.

---

"""

        # Create footer with integration info
        hub_footer = f"""

---

## Integration with Universal Config System

This file is **generated** by the universal config system from `.universal-instructions/claude-specific/`.

To regenerate `CLAUDE.md`:

```bash
./scripts/config/generate-configs.sh
```

Or directly:

```bash
cd /home/thein/repos/TTA.dev
uv run python scripts/config/generate_assistant_configs.py
```

## Source Files

The content in this file is generated from:

- `.universal-instructions/claude-specific/capabilities.md` - Claude-specific features
- `.universal-instructions/claude-specific/workflows.md` - Project-specific workflows
- `.universal-instructions/claude-specific/preferences.md` - Response formatting and tone
- `.universal-instructions/claude-specific/mcp-integration.md` - MCP server integration

## References

- **Workspace Behavior**: [`AGENTS.md`](./AGENTS.md) - Universal agent behavior
- **Technical Config**: `.cline/instructions.md` - Cline tool-specific config
- **Universal Source**: `.universal-instructions/` - Source of truth for generated configs

---

**Last Updated**: {current_date}

**Note**: Do not edit this file directly. Make changes in `.universal-instructions/claude-specific/` and regenerate.
"""

        # Combine all content
        combined_content = hub_header + "\n\n".join(file_contents) + hub_footer

        # Write to workspace root
        output_path = input_data / "CLAUDE.md"
        writer = WriteFilePrimitive()
        result = await writer.execute({"path": output_path, "content": combined_content}, context)

        return result


class GeneratePathSpecificPrimitive(WorkflowPrimitive[tuple[ToolConfig, PathSpecificRule], Path]):
    """Generate a single path-specific instruction file."""

    def __init__(self, universal_dir: Path):
        """
        Initialize with universal instructions directory.

        Args:
            universal_dir: Path to .universal-instructions/
        """
        super().__init__()
        self.universal_dir = universal_dir

    async def execute(
        self, input_data: tuple[ToolConfig, PathSpecificRule], context: WorkflowContext
    ) -> Path:
        """
        Generate path-specific instruction file.

        Args:
            input_data: Tuple of (ToolConfig, PathSpecificRule)
            context: Workflow context

        Returns:
            Path to generated file
        """
        tool_config, rule = input_data

        if not tool_config.path_specific_dir:
            return Path()  # Skip if not configured

        # Read source file
        source_path = self.universal_dir / "path-specific" / rule.source_file
        reader = ReadFilePrimitive()
        content = await reader.execute(source_path, context)

        # Add frontmatter if needed
        frontmatter_adder = AddFrontmatterPrimitive(tool_config.frontmatter_format)
        content_with_frontmatter = await frontmatter_adder.execute(
            {"content": content, "apply_to": rule.apply_to, "description": rule.description},
            context,
        )

        # Write output
        output_filename = Path(rule.source_file).stem + tool_config.path_specific_extension
        output_path = Path(tool_config.output_dir) / tool_config.path_specific_dir / output_filename
        writer = WriteFilePrimitive()
        result = await writer.execute(
            {"path": output_path, "content": content_with_frontmatter}, context
        )

        return result


class GenerateAllPathSpecificPrimitive(WorkflowPrimitive[ToolConfig, list[Path]]):
    """Generate all path-specific instruction files for a tool."""

    def __init__(self, universal_dir: Path, rules: list[PathSpecificRule]):
        """
        Initialize with universal directory and rules.

        Args:
            universal_dir: Path to .universal-instructions/
            rules: List of path-specific rules to generate
        """
        super().__init__()
        self.universal_dir = universal_dir
        self.rules = rules

    async def execute(self, input_data: ToolConfig, context: WorkflowContext) -> list[Path]:
        """
        Generate all path-specific files.

        Args:
            input_data: Tool configuration
            context: Workflow context

        Returns:
            List of generated file paths
        """
        generator = GeneratePathSpecificPrimitive(self.universal_dir)

        # Generate all files sequentially
        results = []
        for rule in self.rules:
            result = await generator.execute((input_data, rule), context)
            results.append(result)

        return results


class GenerateToolConfigPrimitive(WorkflowPrimitive[ToolConfig, dict[str, Any]]):
    """Generate all configuration files for a specific tool."""

    def __init__(self, universal_dir: Path, rules: list[PathSpecificRule], workspace_root: Path):
        """
        Initialize with universal directory and rules.

        Args:
            universal_dir: Path to .universal-instructions/
            rules: List of path-specific rules
            workspace_root: Workspace root directory for resolving relative paths
        """
        super().__init__()
        self.universal_dir = universal_dir
        self.rules = rules
        self.workspace_root = workspace_root

    async def execute(self, input_data: ToolConfig, context: WorkflowContext) -> dict[str, Any]:
        """
        Generate all config files for a tool.

        Args:
            input_data: Tool configuration
            context: Workflow context

        Returns:
            Dict with generated file paths
        """
        # Create workflow generators
        repo_gen = GenerateRepositoryWidePrimitive(self.universal_dir)
        # Note: Agent instructions now generated as workspace-wide AGENTS.md hub (not per-tool)
        path_gen = GenerateAllPathSpecificPrimitive(self.universal_dir, self.rules)

        # Update input_data to use absolute paths
        abs_tool_config = ToolConfig(
            name=input_data.name,
            output_dir=str(self.workspace_root / input_data.output_dir),
            repository_wide_file=input_data.repository_wide_file,
            path_specific_dir=input_data.path_specific_dir,
            path_specific_extension=input_data.path_specific_extension,
            frontmatter_format=input_data.frontmatter_format,
        )

        # Generate files sequentially
        repo_file = await repo_gen.execute(abs_tool_config, context)
        path_files = await path_gen.execute(abs_tool_config, context)

        return {
            "tool": input_data.name,
            "repository_wide": str(repo_file) if repo_file and repo_file != Path() else None,
            "path_specific": [str(p) for p in path_files if p and p != Path()],
        }


# ============================================================================
# Main Orchestration
# ============================================================================


async def generate_configs(tool_name: str, workspace_root: Path) -> dict[str, Any]:
    """
    Generate configuration files for specified tool(s).

    Args:
        tool_name: Name of tool ('copilot', 'cline', 'cursor', 'augment', 'all')
        workspace_root: Root directory of workspace

    Returns:
        Dict with generation results
    """
    universal_dir = workspace_root / ".universal-instructions"
    mappings_dir = universal_dir / "mappings"

    # Define path-specific rules
    path_rules = [
        PathSpecificRule(
            source_file="package-source.instructions.md",
            apply_to="packages/**/src/**/*.py",
            description="Python package source code - production quality standards",
        ),
        PathSpecificRule(
            source_file="tests.instructions.md",
            apply_to="**/tests/**/*.py,**/*_test.py,**/test_*.py",
            description="Test files - comprehensive testing with mocks and async support",
        ),
        PathSpecificRule(
            source_file="scripts.instructions.md",
            apply_to="scripts/**/*.py",
            description="Automation scripts - use primitives for orchestration and reliability",
        ),
        PathSpecificRule(
            source_file="documentation.instructions.md",
            apply_to="**/*.md,**/README.md,**/CHANGELOG.md",
            description="Documentation files - clear, actionable, with code examples",
        ),
    ]

    # Read tool mappings
    yaml_reader = ReadYAMLPrimitive()
    context = WorkflowContext(workflow_id="generate-configs")

    # Generate workspace-wide AGENTS.md hub (once, not per-tool)
    print("🤖 Generating workspace-wide AGENTS.md hub...")
    agents_hub_gen = GenerateAgentsHubPrimitive(universal_dir)
    agents_hub_path = await agents_hub_gen.execute(workspace_root, context)
    print(f"   ✅ Generated: {agents_hub_path}")

    # Generate workspace-wide CLAUDE.md model-specific hub (once, not per-tool)
    print("\n🔮 Generating workspace-wide CLAUDE.md model-specific hub...")
    claude_hub_gen = GenerateClaudeHubPrimitive(universal_dir)
    claude_hub_path = await claude_hub_gen.execute(workspace_root, context)
    print(f"   ✅ Generated: {claude_hub_path}")

    if tool_name == "all":
        tools_to_generate = ["copilot", "cline", "cursor", "augment"]
    else:
        tools_to_generate = [tool_name]

    results = {"agents_hub": str(agents_hub_path), "claude_hub": str(claude_hub_path)}

    for tool in tools_to_generate:
        # Read tool config
        mapping_file = mappings_dir / f"{tool}.yaml"
        config_data = await yaml_reader.execute(mapping_file, context)

        # Create ToolConfig
        tool_config = ToolConfig(**config_data)

        # Generate all files for this tool
        generator = GenerateToolConfigPrimitive(universal_dir, path_rules, workspace_root)
        result = await generator.execute(tool_config, context)
        results[tool] = result

        print(f"\n✅ Generated configuration for {tool}:")
        if result.get("repository_wide"):
            print(f"   📄 Repository-wide: {result['repository_wide']}")
        if result.get("path_specific"):
            print(f"   📁 Path-specific: {len(result['path_specific'])} files")

    return results


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate AI assistant configuration files from universal sources"
    )
    parser.add_argument(
        "--tool",
        type=str,
        choices=["copilot", "cline", "cursor", "augment", "all"],
        default="all",
        help="Tool to generate config for (default: all)",
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Workspace root directory",
    )

    args = parser.parse_args()

    # Run async generation
    results = asyncio.run(generate_configs(args.tool, args.workspace))

    print("\n🎉 Configuration generation complete!")
    print(f"Generated configs for {len(results)} tool(s)")


if __name__ == "__main__":
    main()
