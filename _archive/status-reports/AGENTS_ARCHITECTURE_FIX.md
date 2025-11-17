# AGENTS.md Architecture - Corrected

## Summary

After consulting GitHub Copilot official documentation and community best practices via Context7, the AGENTS.md architecture has been **corrected** to match industry standards.

## What Changed

### ❌ Previous (WRONG) Architecture

```
AGENTS.md (Copilot-specific agent behavior)
CLINE_AGENT.md (Cline-specific agent behavior)
CURSOR_AGENT.md (Cursor-specific agent behavior)
AUGMENT_AGENT.md (Augment-specific agent behavior)
```

**Problem**: This duplicated agent behavior across 4 files, violating DRY principles.

### ✅ Corrected Architecture

```
AGENTS.md (workspace-wide hub for ALL agents)
├── References → .github/copilot-instructions.md (Copilot technical config)
├── References → .cline/instructions.md (Cline technical config)
├── References → .cursor/instructions.md (Cursor technical config)
└── References → .augment/instructions.md (Augment technical config)
```

**Solution**: Single workspace-wide `AGENTS.md` hub that defines behavior once, references tool-specific configs.

## Official GitHub Documentation Evidence

From `docs.github.com/en/copilot`:

> **Agent Instructions (AGENTS.md)**: Used by AI agents within Copilot Chat. These instructions can be placed in `AGENTS.md` files anywhere in the repository, with the **nearest file taking precedence**. 
> 
> For Copilot Chat in VS Code, these instructions **must be in the root of the workspace**.
>
> Alternatively, a single `CLAUDE.md` or `GEMINI.md` file can be used in the repository root.

From `github.com/awesome-copilot`:

> AGENTS.md template serves as a starting point for developers to customize based on their project's specific needs. It outlines essential sections like Project Overview, Setup Commands, Development Workflow, Testing Instructions, Code Style, and Build and Deployment.

## Key Principles

### 1. AGENTS.md is Workspace-Wide

**Location**: Repository root (`/AGENTS.md`)

**Purpose**: Defines agent behavior (communication style, priorities, anti-patterns) that applies to ALL coding assistants.

**Scope**: Universal across tools (Copilot, Cline, Cursor, Augment)

### 2. Tool Configs are Tool-Specific

**Location**: Tool-specific directories (`.github/`, `.cline/`, `.cursor/`, `.augment/`)

**Purpose**: Technical project instructions (architecture, dependencies, coding standards)

**Scope**: Specific to each tool's requirements and capabilities

### 3. Separation of Concerns

| File | Contains | Example Content |
|------|----------|-----------------|
| `AGENTS.md` | **Agent Behavior** | "Be concise and specific", "Prioritize type safety", "Avoid global state" |
| `.github/copilot-instructions.md` | **Technical Details** | "This is a Python monorepo", "Use uv for package management", "Follow PEP 8" |

## Updated YAML Mappings

The tool mappings now reflect this:

```yaml
# copilot.yaml
name: copilot
output_dir: .github
repository_wide_file: copilot-instructions.md
# Note: Copilot uses workspace-wide AGENTS.md (generated separately as hub file)
path_specific_dir: instructions
path_specific_extension: .instructions.md
frontmatter_format: yaml
```

**Removed**: `agent_instructions_file` field (no longer tool-specific)

**Added**: Comment explaining AGENTS.md is workspace-wide hub

## Benefits

1. **DRY Principle**: Agent behavior defined once, not duplicated 4 times
2. **Consistency**: All tools see same behavioral guidelines
3. **Industry Standard**: Matches official GitHub Copilot architecture
4. **Clear Separation**: Behavior (AGENTS.md) vs Technical (tool configs)
5. **Easier Maintenance**: Update agent behavior in one place

## Generator Changes Required

The `scripts/generate_assistant_configs.py` needs these updates:

1. ~~Remove `GenerateAgentInstructionsPrimitive`~~ (agent file no longer tool-specific)
2. Create single `AGENTS.md` hub file (not per-tool)
3. Remove `agent_instructions_file` from `ToolConfig` model
4. Update workflow to skip agent file generation in tool loop

## Verification Commands

```bash
# Regenerate all configs with new architecture
./scripts/generate-configs.sh

# Verify structure
ls -la AGENTS.md  # Should exist at root
ls -la CLINE_AGENT.md CURSOR_AGENT.md AUGMENT_AGENT.md  # Should NOT exist
```

## Documentation Updates

- [x] Updated YAML mappings (removed `agent_instructions_file`)
- [x] Created new workspace-wide `AGENTS.md` hub file
- [ ] Update `scripts/generate_assistant_configs.py` to skip per-tool agent generation
- [ ] Update `UNIVERSAL_CONFIG_SETUP.md` to document hub architecture
- [ ] Remove old `*_AGENT.md` files after regeneration

## References

- GitHub Copilot Docs: https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot
- Awesome Copilot: https://github.com/github/awesome-copilot
- VS Code Copilot Customization: https://code.visualstudio.com/docs/copilot/copilot-customization

---

**Status**: Architecture corrected, YAML mappings updated, new AGENTS.md created. Generator script needs update to skip per-tool agent file generation.
