# TTA.dev Repository Consolidation - Execution Plan

## Current State Analysis

### Packages Directory
- `packages/tta-primitives/` - Core workflow primitives ✅ KEEP
- `packages/tta-observability/` - Observability integration ✅ KEEP
- `packages/tta-core/` - Core utilities ✅ KEEP
- `packages/python-pathway/` - Third-party, unclear purpose ❓ REVIEW

### Platform Directory
- `platform/agent-context/` - Agent context management ✅ KEEP
- `platform/agent-coordination/` - Multi-agent coordination ✅ KEEP
- `platform/apm/` - APM integration ✅ MERGE with observability
- `platform/dolt/` - Database versioning ❓ REVIEW
- `platform/integrations/` - External integrations ✅ KEEP
- `platform/skills/` - Agent skills ✅ KEEP

### Apps Directory
- `apps/n8n/` - Workflow automation ❌ ARCHIVE (decided to remove)
- `apps/observability-vscode/` - VS Code extension ✅ KEEP
- `apps/platform/` - Platform UI ❓ UNCLEAR
- `apps/streamlit-mvp/` - Streamlit MVP ❓ REVIEW

## Consolidation Strategy

### Phase 1: Create Unified Package Structure
```
tta-dev/
├── primitives/          # From packages/tta-primitives
├── observability/       # From packages/tta-observability + platform/apm
├── core/                # From packages/tta-core
├── agents/              # From platform/agent-* 
├── integrations/        # From platform/integrations
├── skills/              # From platform/skills
└── ui/                  # From apps/observability-vscode + streamlit
```

### Phase 2: Archive Non-Essential Items
- apps/n8n → local/archive/
- Unclear/duplicate directories → local/review/

### Phase 3: Update Import Paths
- Update all Python imports to use new structure
- Update pyproject.toml dependencies
- Update documentation

### Phase 4: Create Batteries-Included Setup
- Single `tta-dev install` command
- Auto-detection by CLI agents
- Self-hosted observability UI

## Execution Commands

```bash
# 1. Create new structure
mkdir -p tta-dev/{primitives,observability,core,agents,integrations,skills,ui}

# 2. Move core packages
cp -r packages/tta-primitives/src/tta_dev_primitives/* tta-dev/primitives/
cp -r packages/tta-observability/src/* tta-dev/observability/
cp -r packages/tta-core/src/* tta-dev/core/

# 3. Consolidate platform
cp -r platform/agent-context/* tta-dev/agents/context/
cp -r platform/agent-coordination/* tta-dev/agents/coordination/
cp -r platform/apm/* tta-dev/observability/apm/
cp -r platform/integrations/* tta-dev/integrations/
cp -r platform/skills/* tta-dev/skills/

# 4. Consolidate UI
cp -r apps/observability-vscode/* tta-dev/ui/vscode/
cp -r apps/streamlit-mvp/* tta-dev/ui/web/

# 5. Archive n8n
mkdir -p local/archive
mv apps/n8n local/archive/

# 6. Review unclear items
mkdir -p local/review
mv packages/python-pathway local/review/
mv platform/dolt local/review/
mv apps/platform local/review/
```

## Next Steps After Consolidation
1. Update pyproject.toml with new package structure
2. Create unified setup.py for batteries-included installation
3. Update all documentation references
4. Run quality gates (ruff, pyright, pytest)
5. Update AGENTS.md with new structure
