# TTA.dev Workspace Cleanup Plan

**Date:** 2025-11-17
**Status:** In Progress
**Goal:** Organize repository for optimal agentic usage - elegant, graceful, and exemplary

## Current Issues

1. **Root-level clutter**: 40+ markdown files at repository root
2. **Temporary outputs**: Multiple test/verification folders and log files
3. **Workspace file sprawl**: 6+ `.code-workspace` files
4. **Archive confusion**: Multiple archive/deprecated folders
5. **Mixed purposes**: Local dev files mixed with repo documentation

## Organization Strategy

### 1. Root Level - Essential Only

**KEEP (Core Documentation):**
- `README.md` - Project overview
- `AGENTS.md` - Agent instructions hub
- `GETTING_STARTED.md` - Quick start guide
- `CONTRIBUTING.md` - Contribution guidelines
- `MCP_SERVERS.md` - MCP integration registry
- `PRIMITIVES_CATALOG.md` - Complete primitive reference
- `ROADMAP.md` - Project roadmap
- `CHANGELOG.md` - Version history

**KEEP (Essential Configs):**
- `pyproject.toml`, `uv.lock` - Python project
- `package.json`, `package-lock.json` - Node dependencies
- `pyrightconfig.json` - Type checking
- `codecov.yml` - Coverage config
- `.gitignore`, `.ruffignore` - Git/linting
- `e2b.toml`, `e2b.Dockerfile.debug-minimal` - E2B config

### 2. Move to `docs/`

**Status Reports & Summaries** → `docs/_archive/status-reports/`
- `MIGRATION_FINAL.md`, `MIGRATION_SUMMARY.md`
- `SETUP_TEST_RESULTS.md`, `VALIDATION_RESULTS.md`
- `WORKFLOW_REBASE_COMPLETE.md`
- `BRANCH_ORGANIZATION_COMPLETE.md`
- `ZSH_ENVIRONMENT_IMPLEMENTATION_COMPLETE.md`
- `LAZY_DEV_FINAL_SUMMARY.md`
- All `*_SUMMARY.md`, `*_COMPLETE.md` files

**Guides & Documentation** → `docs/guides/`
- `PRODUCTION_DEPLOYMENT_GUIDE.md`
- `CLINE_INTEGRATION_GUIDE.md`
- `AI_CODER_WORKSPACES_GUIDE.md`
- `GITHUB_WORKFLOWS_EXPERT_GUIDE.md`
- `LAZY_DEV_QUICKREF.md`
- `ZSH_QUICK_START_CARD.md`

**Git/Worktree Docs** → `docs/guides/development/git/`
- `GIT_CLEANUP_PLAN.md`
- `GIT_MANAGEMENT_SUMMARY.md`
- `GIT_QUICKREF.md`
- `GIT_STRUCTURE_DIAGRAM.txt`
- `GIT_WORKTREE_BRANCH_ANALYSIS.md`
- `GIT_WORKTREE_SUMMARY.md`
- `WORKTREE_COORDINATION_*.md`
- `COPILOT_WORKTREE_INVESTIGATION.md`

**Quick Actions** → `docs/guides/quick-actions/`
- `GITHUB_WORKFLOWS_QUICK_ACTIONS.md`
- `RELEASE_QUICK_ACTIONS.md`

**Architecture Analysis** → `docs/architecture/`
- `PACKAGE_INVESTIGATION_ANALYSIS.md`
- `PACKAGE_INVESTIGATION_SUMMARY.md`
- `REPOSITORY_STRUCTURE.md`
- `BRANCH_ORGANIZATION_PLAN.md`

**Troubleshooting** → `docs/guides/troubleshooting/`
- `GEMINI_AUTH_ISSUE_DIAGNOSIS.md`
- `kb-broken-links-analysis.txt`
- `kb-real-broken-links.txt`

### 3. Archive (One-time/Historical)

**Move to `_archive/historical/`:**
- `phases_2_3_complete_setup.md` (one-time setup)
- `verification_results.json` (old test results)
- `todos_current.csv` (outdated)
- `PRIMITIVES_CATALOG.md.corrupted.bak` (backup file)
- `simulation_final.txt`, `simulation_output.txt` (old outputs)
- `long_term_proof_output.txt` (test output)

### 4. Delete (Temporary/Generated)

**Remove these files/folders:**
- `__pycache__/` (Python cache - in .gitignore)
- `htmlcov/` (Coverage HTML - regenerate as needed)
- `.pytest_cache/` (Pytest cache)
- `.ruff_cache/` (Ruff cache)
- `.uv_cache/` (UV cache)
- `node_modules/` (NPM packages - reinstall)
- `verification_test_*/` (Temporary test folders)
- `auto_learning_demo/` (Demo output)
- `production_adaptive_demo/` (Demo output)
- `*.log` files (test logs)
- `*_output.log` files (test outputs)
- `tta_traces.db` (Generated database - regenerate)
- `n8n.log` (Log file)

### 5. Organize by Type

**Workspace Configs** → `.vscode/workspaces/`
- `augment.code-workspace`, `augment-worktree.code-workspace`
- `cline.code-workspace`, `cline-worktree.code-workspace`
- `github-copilot.code-workspace`, `copilot-worktree.code-workspace`

**Scripts & Configs** (keep at root but document):
- `setup_aliases.sh` (setup script)
- `tasks_github.json` (task config)
- `apm.yml` (monitoring config)
- `config.alloy.new` (alloy config)

**Test Files** (move to `tests/` if not there):
- `test_observability.py`
- `test_real_workflow.py`

### 6. Local vs Repository

**Local-only (add to .gitignore if not present):**
- `.env` (secrets)
- `.venv/` (virtual env)
- `logs/` (runtime logs)
- `output/` (test outputs)
- `cache_primitive_*.log`
- `retry_primitive_*.log`
- `test_results.log`
- `tta_traces.db`
- All demo output folders

**Shared config (in repo):**
- `.env.example`, `.env.template` (templates)
- All `.*ignore` files
- `pyproject.toml`, `package.json`

## Implementation Steps

1. ✅ Create this cleanup plan
2. Create new directory structure
3. Move documentation files to appropriate locations
4. Archive historical/one-time files
5. Remove temporary/generated files
6. Organize workspace configs
7. Update .gitignore
8. Create WORKSPACE_ORGANIZATION.md guide
9. Validate all links still work
10. Update main README with new structure

## New Directory Structure

```
TTA.dev/
├── README.md                    # Project overview
├── AGENTS.md                    # Agent hub
├── GETTING_STARTED.md           # Quick start
├── CONTRIBUTING.md              # How to contribute
├── MCP_SERVERS.md              # MCP registry
├── PRIMITIVES_CATALOG.md       # Primitive reference
├── ROADMAP.md                  # Future plans
├── CHANGELOG.md                # Version history
│
├── .github/                    # GitHub configs
├── .vscode/                    # VS Code settings
│   └── workspaces/            # Workspace files
│
├── docs/                       # All documentation
│   ├── architecture/          # Design docs
│   ├── guides/               # How-to guides
│   │   ├── quick-actions/   # Quick reference
│   │   └── ...
│   ├── development/          # Dev guides
│   │   └── git/            # Git/worktree docs
│   ├── status-reports/      # Project status
│   ├── troubleshooting/     # Problem solving
│   └── ...
│
├── platform/                  # Core packages
├── apps/                     # Applications
├── scripts/                  # Automation
├── tests/                    # Test suites
├── logseq/                   # Knowledge base
│
├── _archive/                 # Historical files
│   └── historical/          # One-time docs
│
└── [configs at root]        # pyproject.toml, etc.
```

## Success Criteria

- ✅ Root level has <15 essential files
- ✅ All documentation properly categorized
- ✅ No temporary/generated files in repo
- ✅ Clear separation of local vs shared
- ✅ Workspace configs organized
- ✅ Updated .gitignore
- ✅ WORKSPACE_ORGANIZATION.md created
- ✅ All relative links validated

## Benefits

1. **Agentic clarity**: Clear structure for AI agents to navigate
2. **Reduced context**: Essential files at root reduce cognitive load
3. **Better organization**: Documentation grouped by purpose
4. **Clean git**: No temporary files in version control
5. **Elegant presentation**: Professional, maintainable structure


---
**Logseq:** [[TTA.dev/Docs/Planning/Workspace_cleanup_plan]]
