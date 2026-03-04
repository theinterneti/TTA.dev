# TTA.dev Workspace Organization Guide

**Last Updated:** 2025-11-17

## Overview

This guide documents the TTA.dev repository organization structure, designed for optimal agentic usage with clear separation of concerns, minimal root-level clutter, and elegant navigation.

## Design Principles

1. **Root Simplicity**: Only essential documentation and configs at root level
2. **Clear Categorization**: Documentation grouped by purpose and audience
3. **Agentic Clarity**: Structure that AI agents can easily navigate and understand
4. **Local vs Shared**: Clear separation between local dev files and repository content
5. **Clean History**: No temporary outputs or generated files in version control

## Directory Structure

```
TTA.dev/
├── README.md                           # Project overview & quick start
├── AGENTS.md                           # Agent instructions hub (primary entry point)
├── GETTING_STARTED.md                  # Development setup guide
├── CONTRIBUTING.md                     # Contribution guidelines
├── MCP_SERVERS.md                      # MCP integration registry
├── PRIMITIVES_CATALOG.md               # Complete primitive reference
├── ROADMAP.md                          # Project roadmap & future plans
├── CHANGELOG.md                        # Version history & release notes
│
├── .github/                            # GitHub Actions & templates
│   ├── copilot-instructions.md        # GitHub Copilot configuration
│   ├── instructions/                  # Modular instruction files
│   └── workflows/                     # CI/CD workflows
│
├── .vscode/                            # VS Code workspace configuration
│   ├── settings.json                  # Editor settings
│   ├── tasks.json                     # Build/test tasks
│   ├── copilot-toolsets.jsonc        # Copilot toolset definitions
│   └── workspaces/                    # Workspace files (.code-workspace)
│       ├── augment.code-workspace
│       ├── cline.code-workspace
│       └── github-copilot.code-workspace
│
├── docs/                               # All documentation
│   ├── README.md                       # Documentation index
│   │
│   ├── architecture/                   # Architecture & design docs
│   │   ├── COMPONENT_INTEGRATION_ANALYSIS.md
│   │   ├── OBSERVABILITY_UI_DESIGN.md
│   │   ├── PRIMITIVE_PATTERNS.md
│   │   ├── PACKAGE_INVESTIGATION_ANALYSIS.md
│   │   ├── REPOSITORY_STRUCTURE.md
│   │   └── BRANCH_ORGANIZATION_PLAN.md
│   │
│   ├── guides/                         # User & developer guides
│   │   ├── copilot-toolsets-guide.md
│   │   ├── package-development.md
│   │   ├── PRODUCTION_DEPLOYMENT_GUIDE.md
│   │   ├── CLINE_INTEGRATION_GUIDE.md
│   │   ├── AI_CODER_WORKSPACES_GUIDE.md
│   │   ├── GITHUB_WORKFLOWS_EXPERT_GUIDE.md
│   │   ├── LAZY_DEV_QUICKREF.md
│   │   ├── ZSH_QUICK_START_CARD.md
│   │   └── quick-actions/              # Quick reference cards
│   │       ├── GITHUB_WORKFLOWS_QUICK_ACTIONS.md
│   │       └── RELEASE_QUICK_ACTIONS.md
│   │
│   ├── development/                    # Development workflows
│   │   ├── CodingStandards.md
│   │   └── git/                        # Git & worktree management
│   │       ├── GIT_QUICKREF.md
│   │       ├── GIT_MANAGEMENT_SUMMARY.md
│   │       ├── GIT_CLEANUP_PLAN.md
│   │       ├── GIT_STRUCTURE_DIAGRAM.txt
│   │       ├── GIT_WORKTREE_BRANCH_ANALYSIS.md
│   │       ├── GIT_WORKTREE_SUMMARY.md
│   │       ├── WORKTREE_COORDINATION_ARCHITECTURE.md
│   │       ├── WORKTREE_COORDINATION_PROTOCOL.md
│   │       ├── WORKTREE_COORDINATION_QUICKSTART.md
│   │       ├── WORKTREE_COORDINATION_SUMMARY.md
│   │       └── COPILOT_WORKTREE_INVESTIGATION.md
│   │
│   ├── status-reports/                 # Project status & completion docs
│   │   ├── MIGRATION_FINAL.md
│   │   ├── MIGRATION_SUMMARY.md
│   │   ├── SETUP_TEST_RESULTS.md
│   │   ├── VALIDATION_RESULTS.md
│   │   ├── WORKFLOW_REBASE_COMPLETE.md
│   │   ├── BRANCH_ORGANIZATION_COMPLETE.md
│   │   ├── ZSH_ENVIRONMENT_IMPLEMENTATION_COMPLETE.md
│   │   ├── LAZY_DEV_FINAL_SUMMARY.md
│   │   └── PACKAGE_INVESTIGATION_SUMMARY.md
│   │
│   ├── troubleshooting/                # Problem-solving guides
│   │   ├── GEMINI_AUTH_ISSUE_DIAGNOSIS.md
│   │   ├── kb-broken-links-analysis.txt
│   │   └── kb-real-broken-links.txt
│   │
│   ├── knowledge/                      # Knowledge articles
│   ├── observability/                  # Observability documentation
│   ├── integrations/                   # Integration guides
│   └── mcp/                            # MCP server documentation
│
├── platform/                           # Core packages
│   ├── primitives/                     # tta-dev-primitives
│   ├── observability/                  # tta-observability-integration
│   └── agent-context/                  # universal-agent-context
│
├── apps/                               # User-facing applications
│   └── observability-ui/               # TTA Observability Dashboard
│
├── scripts/                            # Automation & utility scripts
│   ├── cleanup_workspace.sh            # Workspace cleanup
│   ├── pr_manager.py                   # PR management
│   └── validation/                     # Validation scripts
│
├── tests/                              # Integration tests
│   ├── test_observability.py
│   └── test_real_workflow.py
│
├── logseq/                             # Knowledge base & TODO system
│   ├── pages/                          # Knowledge pages
│   ├── journals/                       # Daily journals (TODOs)
│   └── logseq/                         # Logseq config
│
├── _archive/                           # Historical files
│   └── historical/                     # One-time docs & old outputs
│       ├── phases_2_3_complete_setup.md
│       ├── verification_results.json
│       ├── todos_current.csv
│       └── ...
│
└── [Configuration Files at Root]
    ├── pyproject.toml                  # Python project config
    ├── uv.lock                         # UV lock file
    ├── package.json                    # Node.js dependencies
    ├── pyrightconfig.json              # Type checking config
    ├── codecov.yml                     # Code coverage
    ├── e2b.toml                        # E2B sandbox config
    └── .gitignore                      # Git ignore patterns
```

## File Organization Rules

### Root Level - Core Documentation Only

**Files that MUST stay at root:**
- `README.md` - First thing people see
- `AGENTS.md` - Primary entry point for AI agents
- `GETTING_STARTED.md` - Essential for new developers
- `CONTRIBUTING.md` - Contribution guidelines
- `MCP_SERVERS.md` - MCP integration reference
- `PRIMITIVES_CATALOG.md` - Primitive reference
- `ROADMAP.md` - Project direction
- `CHANGELOG.md` - Version history

**Configuration files at root:**
- Language/build tools: `pyproject.toml`, `package.json`, `uv.lock`
- Type checking: `pyrightconfig.json`
- Testing: `codecov.yml`
- Integration: `e2b.toml`
- Version control: `.gitignore`, `.ruffignore`

### Documentation Categories

#### `docs/architecture/`
- System design documents
- Component integration analyses
- Architecture decision records (ADRs)
- Package structure documentation

#### `docs/guides/`
- User guides and tutorials
- Developer workflow guides
- Integration guides
- Quick reference cards (in `quick-actions/`)

#### `docs/guides/development/`
- Coding standards and conventions
- Development workflow documentation
- Git/worktree management (in `git/`)
- Testing strategies

#### `docs/_archive/status-reports/`
- Project completion summaries
- Migration reports
- Validation results
- Implementation status updates

#### `docs/guides/troubleshooting/`
- Problem diagnosis documents
- Known issues and solutions
- Debugging guides

### Special Directories

#### `.vscode/workspaces/`
All `.code-workspace` files for different development contexts:
- `augment.code-workspace` - Augment IDE config
- `cline.code-workspace` - Cline agent config
- `github-copilot.code-workspace` - GitHub Copilot config

#### `_archive/historical/`
One-time documents that are no longer actively used but preserved for reference:
- Migration completion documents
- Old verification results
- Deprecated configuration examples
- Historical status reports

## Local vs Repository Files

### Local-Only Files (in .gitignore)

**Never commit:**
- `.env` - Local environment variables
- `.venv/` - Virtual environment
- `logs/` - Runtime logs
- `htmlcov/` - Coverage HTML reports
- `__pycache__/` - Python bytecode
- `.pytest_cache/` - Test cache
- `.ruff_cache/` - Linter cache
- `.uv_cache/` - UV package cache
- `node_modules/` - NPM packages
- `tta_traces.db` - Local trace database
- `*_output.log` - Test output logs
- `auto_learning_demo/` - Demo outputs
- `production_adaptive_demo/` - Demo outputs
- `verification_test_*/` - Temporary test folders

### Shared Configuration (in repo)

**Always commit:**
- `.env.example`, `.env.template` - Environment templates
- `.gitignore`, `.ruffignore` - Ignore patterns
- `pyproject.toml`, `package.json` - Project definitions
- `.vscode/settings.json` - Shared editor config
- `.github/workflows/` - CI/CD pipelines

## Navigation for AI Agents

### Primary Entry Points

1. **AGENTS.md** - Start here! Complete agent guidance and navigation
2. **README.md** - Project overview and quick start
3. **GETTING_STARTED.md** - Development environment setup
4. **PRIMITIVES_CATALOG.md** - Complete primitive reference

### Finding Documentation

- **"How do I...?"** → `docs/guides/`
- **"What's the architecture?"** → `docs/architecture/`
- **"What changed?"** → `docs/_archive/status-reports/`
- **"Something's broken"** → `docs/guides/troubleshooting/`
- **"Git workflows"** → `docs/guides/development/git/`

### Package-Specific Guidance

Each package has its own documentation:
- `platform/primitives/AGENTS.md` - Core primitives
- `platform/observability/README.md` - Observability integration
- `platform/agent-context/AGENTS.md` - Agent context management

## Maintenance Guidelines

### Adding New Documentation

1. **Determine category**: Guide, architecture, status, or troubleshooting?
2. **Place in appropriate directory**: Use existing structure
3. **Update indexes**: Add link to `docs/README.md` if applicable
4. **Cross-reference**: Link from `AGENTS.md` if relevant for agents

### Moving Files

1. **Create destination directory**: If it doesn't exist
2. **Update all links**: Search for references and update paths
3. **Validate links**: Run link checker after moving
4. **Update .gitignore**: If moving temporary/generated files

### Archiving

Files to archive when:
- **One-time use**: Migration guides, setup completions
- **Superseded**: Replaced by newer documentation
- **Historical value only**: Old verification results
- **No longer relevant**: Deprecated feature docs

Move to `_archive/historical/` with date prefix if useful for reference.

### Cleanup Checklist

When adding new files, ensure:
- [ ] File is in correct directory per this guide
- [ ] Documentation is linked from appropriate index
- [ ] No duplicate information exists elsewhere
- [ ] Temporary files are in .gitignore
- [ ] Root level remains clean (<15 essential files)

## Tooling

### Workspace Cleanup Script

Run periodic cleanup:
```bash
./scripts/cleanup_workspace.sh
```

This script:
- Moves misplaced documentation to correct directories
- Archives historical files
- Removes temporary outputs
- Organizes workspace files

### Validation

Check workspace organization:
```bash
# Count root-level markdown files (should be ~9)
ls -1 *.md | wc -l

# Verify directory structure
tree -L 2 docs/

# Check for temporary files
find . -name "*.log" -o -name "*_output.log" -o -name "verification_test_*"
```

## Benefits of This Organization

1. **🎯 Agentic Clarity**: AI agents can quickly find relevant documentation
2. **📚 Reduced Context**: Essential files at root reduce cognitive load
3. **🔍 Easy Discovery**: Clear categorization helps find information fast
4. **🧹 Clean Git**: No temporary files polluting version history
5. **🎨 Professional**: Elegant structure reflects project quality
6. **📊 Maintainable**: Clear rules prevent future disorganization
7. **🤝 Collaborative**: Contributors know where to place new content

## Quick Reference

### "Where should I put...?"

| Content Type | Location |
|-------------|----------|
| Architecture design doc | `docs/architecture/` |
| User guide or tutorial | `docs/guides/` |
| Development workflow | `docs/guides/development/` |
| Project status report | `docs/_archive/status-reports/` |
| Troubleshooting guide | `docs/guides/troubleshooting/` |
| Quick reference card | `docs/guides/quick-actions/` |
| Git/worktree doc | `docs/guides/development/git/` |
| Workspace config file | `.vscode/workspaces/` |
| Historical/one-time doc | `_archive/historical/` |
| Package-specific doc | `platform/{package}/docs/` |

### "What stays at root?"

Only these 9 categories:
1. `README.md` (overview)
2. `AGENTS.md` (agent hub)
3. `GETTING_STARTED.md` (setup)
4. `CONTRIBUTING.md` (how to contribute)
5. `MCP_SERVERS.md` (MCP registry)
6. `PRIMITIVES_CATALOG.md` (primitive ref)
7. `ROADMAP.md` (future plans)
8. `CHANGELOG.md` (version history)
9. Essential config files (pyproject.toml, etc.)

## See Also

- [Workspace Cleanup Plan](WORKSPACE_CLEANUP_PLAN.md) - Detailed cleanup execution plan
- [Agent Instructions](AGENTS.md) - Primary agent guidance
- [Documentation README](docs/README.md) - Documentation index
- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute

---

**Maintained by:** TTA.dev Team
**Last Cleanup:** 2025-11-17
**Next Review:** When adding 5+ new root-level files


---
**Logseq:** [[TTA.dev/Docs/Workspace_organization]]
