---
title: Docker Migration Workflow
tags: #TTA
status: Active
repo: theinterneti/TTA
path: .augment/workflows/docker-migration.workflow.md
created: 2025-11-01
updated: 2025-11-01
---

# [[TTA/Workflows/Docker Migration Workflow]]

**Purpose**: Systematically migrate project dependencies after Docker architecture changes.

**When to Use**: After major Docker refactoring, compose file consolidation, or orchestration pattern changes.

## Quick Reference

### Discovery Phase
```bash
# Find all docker-compose references
grep -r "docker-compose" --include="*.{sh,yml,yaml,md,py,js,ts}" . | grep -v ".git"

# Find compose file usage patterns
grep -r "docker-compose -f" --include="*.sh" .
```

### Update Pattern
```bash
# OLD PATTERN
docker-compose -f docker-compose.dev.yml up -d

# NEW PATTERN
bash docker/scripts/tta-docker.sh dev up -d

# OR (APM integration)
copilot run services:start
```

## Workflow Steps

### 1. Identify Dependencies
- Search for direct references
- Categorize by type (scripts, docs, configs)
- Create dependency matrix with priorities

### 2. Update Critical Path (P0)
- Cleanup/test scripts (affects CI/CD)
- Configuration files (apm.yml, etc.)
- AI agent context files
- Integration documentation

### 3. Enhance Integration
- Add new APM commands (status, restart)
- Update AI agent context consistently
- Simplify command patterns

### 4. Create Documentation
- Summary document (quick reference)
- Detailed report (file-by-file changes)
- Navigation index
- Migration status checker script

### 5. Validate
- Manual testing of updated scripts
- APM command testing
- AI agent context verification
- Documentation review

## File Update Template

```bash
# 1. Read current file
read_file <path>

# 2. Identify references
grep_search query="docker-compose" includePattern="<filename>"

# 3. Replace with context (3-5 lines)
replace_string_in_file \
  oldString="<context>\nold command\n<context>" \
  newString="<context>\nnew command\n<context>"

# 4. Validate
get_errors filePaths=["<path>"]
```

## Common Patterns

### Script Migration
**Before**: `docker-compose -f docker-compose.dev.yml down -v`
**After**: `bash docker/scripts/tta-docker.sh dev down -v`

### Documentation Updates
**Before**: `` `docker-compose -f docker-compose.dev.yml up -d` ``
**After**: `` `bash docker/scripts/tta-docker.sh dev up -d` ``

### APM Integration
```yaml
services:
  start:
    description: "Start development services"
    command: "bash docker/scripts/tta-docker.sh dev up -d"
```

## Success Criteria

- [ ] All critical path files updated
- [ ] No broken references in active scripts
- [ ] Development workflow functional
- [ ] APM commands working
- [ ] All documentation updated
- [ ] Migration tools created

## Related Resources

- **Primitive**: `.augment/rules/docker-dependency-migration.primitive.md` (detailed patterns)
- **Instructions**: `.github/instructions/docker-improvements.md` (architecture review)
- **Data Strategy**: `.github/instructions/data-separation-strategy.md` (environment isolation)

---

**For detailed patterns, anti-patterns, and real-world examples, see the primitive file.**


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___.augment workflows docker migration.workflow]]
