# Claude-Specific Instructions

This directory contains source content for generating `CLAUDE.md` - Claude model-specific instructions.

## Purpose

Claude has unique capabilities that warrant model-specific guidance:

- **Artifacts**: Generating substantial files in separate, editable documents
- **Extended Context**: 200K+ token windows for comprehensive analysis
- **Extended Thinking**: Deep reasoning mode for complex problems
- **MCP Integration**: Model Context Protocol for external tools and data
- **Chat Modes**: Different modes optimized for different tasks
- **Structured Output**: XML and hierarchical formatting preferences

## File Structure

- `capabilities.md` - Claude-specific features (artifacts, extended context, reasoning style)
- `workflows.md` - Project-specific workflows using Claude's strengths
- `preferences.md` - Response formatting, tone, context management
- `mcp-integration.md` - MCP server integration patterns and workflows

## Generation Process

The `GenerateClaudeHubPrimitive` in `scripts/config/generate_assistant_configs.py` combines these files to create `/CLAUDE.md`:

1. Add header explaining relationship to AGENTS.md
2. Include Purpose section with tool compatibility
3. Add "When to Use" comparison table
4. Combine content from all source files
5. Add Integration section referencing universal config system
6. Add footer with references and last updated date

## Relationship to Other Files

```text
AGENTS.md (workspace-wide hub)
    ↓
CLAUDE.md (model-specific, this directory)
    ↓
Tool configs (.cline/, .cursor/, .augment/, .github/)
```

## Usage

To regenerate `CLAUDE.md`:

```bash
./scripts/config/generate-configs.sh
```

Or directly:

```bash
cd /home/thein/repos/TTA.dev
uv run python scripts/config/generate_assistant_configs.py
```

## Maintenance

When adding Claude-specific features:

1. Determine which file to update:
   - New capability? → `capabilities.md`
   - New workflow pattern? → `workflows.md`
   - Response preference? → `preferences.md`
   - MCP integration? → `mcp-integration.md`

2. Keep it Claude-specific:
   - If it applies to all AI assistants → put in `.universal-instructions/agent-behavior/`
   - If it's Claude-specific → put it here

3. Regenerate CLAUDE.md to apply changes
