# TTA.dev Framework Architecture

## Overview

This document describes the relationship between **TTA.dev** (the framework) and **TTA** (this project).

## Current State (Hybrid Model)

**Repository**: `theinterneti/TTA`
**Purpose**: Therapeutic Text Adventure application

This repository currently contains:
- **Project code**: The TTA application (`src/`, `tests/`, etc.)
- **TTA.dev framework assets**: Development primitives and configurations
  - `.augment/` - AI workflow primitives
  - `.tta/` - TTA.dev-specific configurations
  - `.serena/` - Serena framework integration
  - Various integration configs (`.cline/`, `.clinerules/`, etc.)

## Target Architecture (Future)

### TTA.dev (The Framework)
**Repository**: `theinterneti/TTA.dev`
**Purpose**: AI-native development toolkit

**Users will**:
1. Clone TTA.dev once: `git clone git@github.com:theinterneti/TTA.dev.git ~/tta.dev`
2. Initialize in their project: `tta-dev init /path/to/their/project`
3. TTA.dev provides:
   - CLI tools for AI development
   - VS Code configurations
   - Reusable primitives (`.augment/`)
   - Integration toolkits (Hypertool, MCP servers)
   - Project templates

### Project Repositories (Like TTA)
**Repository**: `theinterneti/TTA` (or user's own repos)
**Purpose**: Actual application code

**Projects will**:
- Contain only application-specific code
- Have `.tta.dev.config.json` pointing to local TTA.dev installation
- Optionally customize TTA.dev primitives locally
- Keep git clean of framework boilerplate

## Separation Strategy

### Option 1: Workspace-Based (Recommended)
```json
// TTA.code-workspace
{
  "folders": [
    {
      "path": "~/tta.dev",
      "name": "TTA.dev Framework (Reference)"
    },
    {
      "path": "~/projects/TTA",
      "name": "TTA Project"
    }
  ],
  "settings": {
    "tta.dev.frameworkPath": "~/tta.dev",
    "tta.dev.projectPath": "~/projects/TTA"
  }
}
```

### Option 2: Container-Based
- TTA.dev runs as a dev container
- Mounts project directory
- Framework stays isolated
- Easier for distributed teams

### Option 3: CLI Configuration
```bash
# In project directory
$ tta-dev config set framework-path ~/tta.dev
$ tta-dev link  # Creates symlinks/references as needed
```

## Migration Path

### Phase 1: Document Current State ✅
- This document

### Phase 2: Extract TTA.dev Core
- Create `theinterneti/TTA.dev` repository
- Move shareable primitives
- Create CLI/tooling

### Phase 3: Refactor TTA Project
- Remove framework boilerplate from TTA
- Keep project-specific customizations
- Add `.tta.dev.config.json`

### Phase 4: Formalize Initialization
- Create `tta-dev init` command
- Document setup process
- Create project templates

## Design Principles

1. **Separation of Concerns**: Framework vs. Application
2. **Don't Repeat Yourself**: Share primitives across projects
3. **Easy Onboarding**: Simple setup for new projects
4. **Flexibility**: Allow project-specific customizations
5. **Version Control**: Clear separation in git

## Current Git Configuration

**Remote**: `git@github.com:theinterneti/TTA.git`
**Purpose**: Correct - this is the TTA project repository

**Note**: Framework assets (`.augment/`, `.tta/`, etc.) are currently tracked here but will eventually be separated into TTA.dev.

## Questions to Resolve

1. **Container vs. Workspace**: Which isolation method?
2. **Primitive Sharing**: Symlinks, git submodules, or file copying?
3. **VS Code Extension**: Should TTA.dev have its own extension?
4. **Configuration Format**: YAML, JSON, or TOML for `.tta.dev.config`?
5. **Version Locking**: How to version framework alongside projects?

## Related Documentation

- [TTA Project README](../README.md)
- [Augment Primitives](../.augment/README.md)
- [Serena Integration](../.serena/project.yml)

---

**Last Updated**: 2025-11-16
**Status**: Architecture Planning Phase


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Hypertool/Personas/Tta_dev_architecture]]
