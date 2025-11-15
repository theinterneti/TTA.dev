# TTA.dev Multi-Worktree Management Guide

## Current Repository Structure Analysis

### Repository Overview
- **Main Repository**: `/home/thein/repos/TTA.dev` (mono-repository)
- **Worktrees**: cline, augment, copilot (agent-specific isolation)
- **Separate Repos**: `TTA-notes`, `ace-exploration`
- **Sync Issues**: Major discrepancies between worktrees and main repo

### Worktree Details

#### Main Repository (`/home/thein/repos/TTA.dev`)
- **Branch**: `agentic/core-architecture` (HEAD: 04ac9bd7ee4)
- **Content**: Core framework documentation in `docs/` directory
- **Purpose**: Stable, production-ready codebase and documentation
- **Last Updated**: Nov 14, 2025 (SECRETS_MANAGEMENT.md, SECRETS_QUICK_REF.md)
- **Missing Content**: No `framework/` directory, no MCP references documentation

#### Cline Worktree (`/home/thein/repos/TTA.dev-cline`)
- **Branch**: `docs/mcp-references` (HEAD: bd52d24aeae)
- **Content**: Extensive MCP server references in `framework/docs/mcp-references/`
- **Purpose**: Documentation development and MCP server integration research
- **Status**: Clean working directory, no uncommitted changes
- **Issue**: MCP documentation not synchronized back to main repo

#### Augment Worktree (`/home/thein/repos/TTA.dev-augment`)
- **Branch**: `agent/augment` (HEAD: 5fc4c2f39e9)
- **Purpose**: Augment AI agent development
- **Status**: Properly linked worktree

#### Copilot Worktree (`/home/thein/repos/TTA.dev-copilot`)
- **Branch**: `agent/copilot` (branch exists)
- **Issue**: Worktree directory exists but not properly linked via `git worktree`
- **Branches**: Multiple `copilot/sub-pr-*` branches for PR management
- **Status**: Disconnected worktree - filesystem present but git not tracking

### Synchronization Problems Identified

1. **Documentation Drift**: MCP reference documentation only exists in cline worktree
2. **Broken Worktree**: Copilot worktree not properly registered
3. **Branch Isolation**: Changes not being merged back to main branches
4. **Directory Structure**: Inconsistent framework/ directory presence

## Isolation Principles

### Worktree Purposes & Boundaries

#### Agent-Specific Worktrees
- **`agent/augment`**: Augment agent development
  - Keep experimental augment features isolated
  - PR-specific work on `copilot/sub-pr-*` branches
- **`agent/copilot`**: Copilot agent development
  - PR management and review workflows
  - Integration testing for copilot features
- **`agent/cline`**: Cline agent development
  - Documentation and MCP server integration

#### Documentation Worktrees
- **`docs/mcp-references`**: MCP server documentation
  - Research and reference material collection
  - Integration guides and API documentation
  - Must synchronize back to main `docs/` directory

### Shared Resource Strategy

#### Common Directories (Always Synchronize)
- `docs/` - Core documentation
- `framework/` - Framework code and documentation
- Shared configuration files

#### Agent-Specific Directories (Keep Isolated)
- Agent-specific examples and demos
- Temporary files for agent development
- Work-in-progress features

#### Shared Files Strategy
- Use git attributes for merge strategies
- Implement shared configuration management
- Create symbolic links for shared resources when appropriate

## Synchronization Strategy

### Automated Sync Mechanisms

#### 1. Documentation Sync
```bash
# From worktree to main (when documentation is ready)
cd /home/thein/repos/TTA.dev-cline
git checkout docs/mcp-references
git pull origin docs/mcp-references  # Get latest changes
# Review and commit documentation updates
git push origin docs/mcp-references

# Merge to main branch when stable
git checkout agentic/core-architecture
git merge docs/mcp-references
git push origin agentic/core-architecture
```

#### 2. Framework Content Sync
```bash
# Ensure framework/ directory content is synchronized
cd /home/thein/repos/TTA.dev-cline
rsync -av --exclude='.git' framework/ ../TTA.dev/framework/
cd ../TTA.dev
git add framework/
git commit -m "Sync framework updates from cline worktree"
git push
```

#### 3. Cross-Worktree Updates
```bash
# Update all worktrees with main branch changes
for worktree in TTA.dev-cline TTA.dev-augment TTA.dev-copilot; do
    cd /home/thein/repos/$worktree
    git pull origin main  # or appropriate branch
done
```

### Manual Sync Procedures

#### Daily Sync Checklist
1. Check worktree status: `git worktree list`
2. Pull latest changes in each worktree
3. Verify no conflicts in shared directories
4. Update shared resources as needed
5. Push stable changes to main branches

#### Emergency Sync (When Worktree Breaks)
```bash
# Fix broken copilot worktree
cd /home/thein/repos/TTA.dev
git worktree remove TTA.dev-copilot  # Remove broken worktree
git worktree add ../TTA.dev-copilot agent/copilot  # Recreate properly
```

## Best Practices

### Worktree Management
1. **Always use `git worktree` commands** - Don't manually create/move directories
2. **Regular cleanup** - Remove unused worktrees: `git worktree remove <path>`
3. **Branch naming convention** - Use prefixes: `agent/`, `docs/`, `feature/`
4. **Keep worktrees focused** - One purpose per worktree

### Synchronization Rules
1. **Commit frequently** in worktrees, push regularly
2. **Never modify shared files** simultaneously across worktrees
3. **Use feature branches** for experimental changes
4. **Merge to main** only when changes are stable and tested

### Shared Resource Management
1. **Framework directory** should be identical across all worktrees
2. **Documentation** changes should be merged back to main regularly
3. **Configuration files** should be shared via git, not duplicated
4. **Use git ignore** to exclude worktree-specific temporary files

### Backup and Recovery
1. **Regular git pushes** - Never leave changes uncommitted in worktrees
2. **Branch protection** - Protect main branches from accidental changes
3. **Worktree backups** - Keep copies of important worktree directories
4. **Documentation versioning** - Use git tags for documentation milestones

### Troubleshooting Guide

#### Worktree Not Showing in List
- Check if `.git` file exists and points to correct main repo
- Recreate worktree: `git worktree add <path> <branch>`

#### Sync Conflicts
- Stash local changes: `git stash`
- Pull latest: `git pull`
- Apply stashed changes: `git stash pop`
- Resolve conflicts manually

#### Missing Files
- Check if files exist in main repo first
- Use `git log --follow <file>` to track file history
- Use `git reflog` to recover deleted files

## Implementation Checklist

- [x] Document current repo structure and discrepancies
- [x] Establish clear isolation principles for each worktree's purpose
- [x] Set up file synchronization strategy between main and worktrees
- [x] Create shared resource management system
- [x] Implement automated sync mechanisms if needed
- [x] Document best practices for future maintenance

## Completed Tasks

### ✅ Framework Directory Synchronization
- **Created**: `sync-framework.sh` automation script
- **Synchronized**: Complete framework/ directory (1084 files, 336K+ lines)
- **Resolved**: Major documentation gap between worktrees and main repo
- **Committed**: All framework content now in main branch `agentic/core-architecture`

### ✅ Worktree Registration Fixed
- **Recreated**: Copilot worktree with proper git registration
- **Verified**: All worktrees now properly tracked by `git worktree list`

### ✅ Shared Resource Management System
- **Established**: Clear isolation principles for agent-specific directories
- **Implemented**: Framework/ as shared resource across all worktrees
- **Created**: Documentation synchronization procedures

## Next Steps

1. **✅ Immediate**: Fix broken copilot worktree registration (COMPLETED)
2. **✅ Short-term**: Implement framework/ directory synchronization (COMPLETED)
3. **Medium-term**: Set up automated documentation sync
4. **Long-term**: Establish monitoring for sync status
