# Archive Directory

This directory contains deprecated, historical, under-review content, and deprecated tools from the TTA.dev repository reorganization.

**Created:** November 17, 2025
**Reorganization:** Issue #113
**Branch:** refactor/repo-reorg

## Structure

```
_archive/
├── e2b-debug-session-2025-11-07/    # Historical debugging session
├── gemini/                          # Deprecated Gemini workflow files
├── kiro/                            # Deprecated narrative tooling
├── legacy-tta-game/                  # Legacy TTA game code
├── openhands/                        # Deprecated OpenHands integration
├── packages/                         # Historical package versions
├── packages-under-review/            # Packages pending architectural review
├── phase3-status/                    # Phase 3 completion reports
├── planning/                         # Historical planning documents
├── reports/                          # Old status reports
├── speckit-planning/                 # SpecKit planning (deprecated)
├── status-reports/                   # Status reports archive
└── status-reports-2025/              # 2025 status reports
```

## Contents

### Legacy Code
- **e2b-debug-session-2025-11-07/**: E2B debugging session from November 2025
- **legacy-tta-game/**: Old TTA game codebase (pre-reorganization)

### Packages
- **packages/**: Historical package versions
- **packages-under-review/**:
  - `keploy-framework` - Under architectural review (Issue #TBD)
  - `python-pathway` - Under architectural review (Issue #TBD)
  - `js-dev-primitives` - Placeholder, not implemented

### Planning & Status
- **planning/**: Historical planning documents (ACE TODO, Agent Adoption, etc.)
- **phase3-status/**: Phase 3 completion reports
- **reports/**: Old status and analysis reports
- **speckit-planning/**: SpecKit planning (deprecated)
- **status-reports/**: Historical status reports
- **status-reports-2025/**: 2025 status reports

### Deprecated Tools
- **gemini/**: Gemini CLI workflow files (superseded by cline/serena integration)
- **kiro/**: Experimental narrative tooling (superseded by platform_tta_dev primitives)
- **openhands/**: OpenHands integration (replaced by cline with better MCP support)

## Migration Details

### Gemini Workflow Migration
All Gemini CLI workflows have been moved to this archive. Current alternatives include:
- **cline**: Superior MCP integration for VS Code workflows
- **github-copilot**: Native GitHub integration for issue/PR automation
- **Direct API calls**: For simple automation tasks

### OpenHands Migration
The OpenHands tool was evaluated but found to have:
- Limited MCP protocol support
- Poor VS Code integration
- Higher complexity vs. features provided

Replaced by cline which provides:
- ✅ Native MCP protocol support
- ✅ VS Code extension integration
- ✅ Better terminal integration

### Kiro Migration
Kiro was an experimental narrative tooling framework that has been superseded by:
- platform_tta_dev's agentic primitives
- Enhanced workflow orchestration patterns
- Better state management through WorkflowContext

## Packages Under Review

The following packages are archived pending architectural decisions:

| Package | Status | Reason | Decision Date |
|---------|--------|--------|---------------|
| keploy-framework | Under Review | No pyproject.toml, minimal implementation | TBD (by Nov 7, 2025) |
| python-pathway | Under Review | Unclear use case, not documented | TBD (by Nov 7, 2025) |
| js-dev-primitives | Placeholder | Directory structure only, no code | TBD (by Nov 14, 2025) |

## Related Issues

- **#113** - Repository Reorganization: Establish Platform Structure
- **#114** - Create platform/shared/ utilities directory (deferred)
- **#115** - Migrate and organize apps/examples/ (deferred)

## Notes

- Content in this directory is NOT included in the active workspace
- Files are preserved for historical reference and potential future use
- Do not import or depend on archived code in active packages
- Review issues above before considering re-integration

## Restoration

If content from this archive needs to be restored:

1. Create an issue describing the use case
2. Review and update the code to current standards
3. Add comprehensive tests and documentation
4. Submit PR for review
5. Add to active workspace in pyproject.toml

**Last Updated:** November 17, 2025
