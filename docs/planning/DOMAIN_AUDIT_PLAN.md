# Domain Audit & Improvement Plan

**Date:** 2025-11-25
**Auditor:** Domain Manager (GitHub Copilot)
**Scope:** Repository Structure, Coherence, and Hygiene

## 1. Audit Findings

### 🟢 Strengths (Functionality & Form)
*   **Core Structure**: The `platform/` directory correctly houses the core packages (`primitives`, `observability`, etc.) as defined in `pyproject.toml`.
*   **Workspace Definition**: `pyproject.toml` clearly defines the workspace members using `uv`.
*   **Tooling**: The project is set up with modern tooling (`uv`, `ruff`, `pyright`).

### 🔴 Weaknesses (Elegance & Noise)
*   **Nested Repository Copies**: There are two directories, `TTA.dev/` and `framework/`, that appear to be recursive copies or older clones of the repository. This creates significant confusion and "noise".
*   **Root Clutter**: The root directory contains many loose files:
    *   Documentation (`WORKTREE_*`, `GIT_COLLABORATION_*`) that belongs in `docs/`.
    *   Playbooks (`ace_*_playbook.json`) that belong in `playbooks/`.
    *   Config files that could be consolidated or organized.
*   **Legacy Structure**: The `packages/` directory exists alongside `platform/`, containing `tta-observability-vscode`. This breaks the `platform/` vs `apps/` convention.
*   **Orphaned Directories**: `tta-agent-coordination/` (root) appears to be an empty or leftover directory.

## 2. Improvement Plan

### Phase 1: De-clutter (High Impact)
*   [ ] **Archive Nested Copies**: Move `TTA.dev/` and `framework/` to `_archive/nested_copies/` to immediately reduce noise.
*   [ ] **Cleanup Root**:
    *   Move `WORKTREE_*.md` and other root docs to `docs/guides/` or `docs/reference/`.
    *   Move `ace_*_playbook.json` to `playbooks/`.
    *   Delete `tta-agent-coordination/` from root (if empty/redundant).

### Phase 2: Structural Alignment
*   [x] **Migrate VS Code Extension**: Move `packages/tta-observability-vscode/` to `apps/vscode-extension/` to align with the `apps/` directory structure.
*   [x] **Remove Legacy `packages/`**: Once empty, remove the `packages/` directory.

### Phase 3: Standardization
*   [x] **Update Documentation**: Update `README.md` and `CONTRIBUTING.md` to reflect the clean structure (`platform/` + `apps/`).
*   [x] **Verify Workspace**: Run `uv sync` to ensure all paths in `pyproject.toml` are correct after moves.

## 3. Execution Strategy

I recommend executing Phase 1 immediately to clear the view. Phase 2 and 3 can follow once the noise is reduced.

**Ready to execute Phase 1?**
