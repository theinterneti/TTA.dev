---
title: UV Configuration Guide for TTA Project
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/setup/UV_CONFIGURATION_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/UV Configuration Guide for TTA Project]]

## Overview

This guide documents the comprehensive UV configuration for the TTA (Therapeutic Text Adventure) project, optimized for WSL2 + VS Code development environment.

**Goal:** Ensure UV consistently uses `.venv` as the project virtual environment across all contexts, prevent environment variable conflicts, and optimize for WSL2 performance.

---

## Configuration Architecture

### 1. Configuration Files

```
TTA Project Root
├── pyproject.toml             # Project metadata + [tool.uv] section
├── .python-version            # Python version pinning
├── .vscode/
│   ├── settings.json          # VS Code Python interpreter config
│   └── tasks.json             # UV operation tasks
├── .gitignore                 # Excludes .uv_cache and list/
└── ~/.bashrc or ~/.zshrc      # Shell environment variables
```

### 2. Configuration Precedence

UV checks configuration in this order (highest to lowest priority):

1. **Command-line flags** (e.g., `uv sync --python 3.11`)
2. **`pyproject.toml` [tool.uv]** (project metadata, committed to git)
3. **Environment variables** (e.g., `UV_PROJECT_ENVIRONMENT`)
4. **Global UV config** (`~/.config/uv/uv.toml`)
5. **UV defaults** (`.venv` for virtual environments)

---

## Configuration Details

### `pyproject.toml` [tool.uv] Section

**Purpose:** Project-specific UV settings that take precedence over environment variables.

**Key Settings:**

```toml
[tool.uv]
# UV configuration is in pyproject.toml [tool.uv] section
# See pyproject.toml for actual configuration

[tool.uv]
cache-dir = "./.uv_cache"   # Project-local cache for WSL2 performance
managed = true              # UV manages the virtual environment
default-groups = ["dev"]    # Include dev dependencies by default
python-preference = "managed"  # Prefer UV-managed Python installations

# Optimize resolution for WSL2/Linux + Python 3.10+
environments = [
    "sys_platform == 'linux'",
    "python_version >= '3.10'",
]

# Cache invalidation triggers
cache-keys = [
    { file = "pyproject.toml" },
    { file = "uv.lock" },
]
```

**Benefits:**
- ✅ Prevents accidental system-wide installs
- ✅ Project-local cache avoids WSL2 cross-filesystem overhead
- ✅ Consistent Python versions across environments
- ✅ Faster dependency resolution

### `pyproject.toml` [tool.uv] (UPDATED)

**Purpose:** Project metadata and UV-specific settings.

**Key Additions:**

```toml
[tool.uv]
managed = true
default-groups = ["dev"]
python-preference = "managed"
cache-dir = "./.uv_cache"

environments = [
    "sys_platform == 'linux'",
    "python_version >= '3.10'",
]

cache-keys = [
    { file = "pyproject.toml" },
    { file = "uv.lock" },
]
```

**Note:** These settings mirror `uv.toml` for redundancy and clarity.

### Shell Environment Variables

**Add to `~/.bashrc` or `~/.zshrc`:**

```bash
# UV Configuration - Force use of .venv
export UV_PROJECT_ENVIRONMENT=".venv"
```

**Purpose:** Safety net to ensure UV uses `.venv` even if other configurations fail.

**Apply changes:**
```bash
source ~/.bashrc  # or source ~/.zshrc
```

### VS Code Configuration

**`.vscode/settings.json`** (already configured):

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
    "python.pythonPath": "${workspaceFolder}/.venv/bin/python",
    "python.terminal.activateEnvironment": true,
    "python.testing.pytestEnabled": true
}
```

**`.vscode/tasks.json`** (NEW):

Provides quick access to UV operations via Command Palette (`Ctrl+Shift+P` → "Tasks: Run Task"):

- **UV: Sync Dependencies** - Standard sync
- **UV: Sync with Dev Dependencies** - Sync with all extras
- **UV: Verify Environment** - Check configuration
- **UV: Check for List Directory** - Detect unwanted `list` directory
- **UV: Clean and Rebuild Environment** - Nuclear option
- **UV: Run Tests** - Execute pytest
- And more...

---

## Best Practices for WSL2 + VS Code

### 1. Always Use `.venv`

```bash
# Create virtual environment (if needed)
uv venv

# Sync dependencies
uv sync --all-extras
```

**Never** create custom-named environments like `uv venv list` unless absolutely necessary.

### 2. Check Environment Variables Before Starting

```bash
# Should be empty or point to .venv
env | grep VIRTUAL_ENV

# Should show .venv setting
env | grep UV_PROJECT_ENVIRONMENT
```

### 3. Use VS Code Tasks

Instead of typing commands, use VS Code tasks:
- `Ctrl+Shift+P` → "Tasks: Run Task" → Select UV task

### 4. Verify Configuration Regularly

```bash
./verify-uv-configuration.sh
```

Run this script after:
- Cloning the repository
- Updating UV
- Changing configuration files
- Experiencing environment issues

### 5. Project-Local Cache

The `.uv_cache/` directory is project-local for WSL2 performance:

```bash
# Check cache size
du -sh .uv_cache

# Clear cache if needed
rm -rf .uv_cache
uv sync
```

### 6. Restart VS Code After Environment Changes

After changing environment variables or configuration:

```bash
# Close all terminals in VS Code
# Then close VS Code completely
pkill -f 'vscode-server'

# Wait 5 seconds, then reopen
code /home/thein/recovered-tta-storytelling
```

---

## Verification Procedures

### Quick Verification

```bash
# 1. Check UV version
uv --version

# 2. Check Python version
.venv/bin/python --version

# 3. Check environment variables
env | grep -E 'VIRTUAL_ENV|UV_'

# 4. Check for unwanted directories
ls -la | grep list

# 5. Test sync (dry run)
uv sync --dry-run
```

### Comprehensive Verification

```bash
./verify-uv-configuration.sh
```

This script performs 15 checks:
1. UV installation
2. Configuration files
3. Virtual environment
4. Unwanted 'list' directory
5. Environment variables
6. UV cache
7. VS Code configuration
8. UV lock file
9. Python version
10. Pytest installation
11. UV managed setting
12. Default groups
13. UV sync dry run
14. List directory recreation test
15. VS Code tasks

### Expected Output

```
==========================================
Verification Summary
==========================================
Passed: 13
Warnings: 2
Failed: 0

✓ All critical checks passed!

Your UV configuration is properly set up for WSL2 + VS Code.
```

---

## Edge Cases and Gotchas

### 1. `VIRTUAL_ENV` Environment Variable Persistence

**Problem:** `VIRTUAL_ENV` set to `list` persists across sessions.

**Solution:**
```bash
# Deactivate and unset
deactivate 2>/dev/null || true
unset VIRTUAL_ENV
unset VIRTUAL_ENV_PROMPT

# Restart VS Code
pkill -f 'vscode-server'
```

**Prevention:** Always deactivate virtual environments before closing terminals.

### 2. UV Creates `list` Directory

**Problem:** UV recreates `list` directory after deletion.

**Root Cause:** `VIRTUAL_ENV` environment variable points to `list`.

**Solution:** See `FIX_LIST_DIRECTORY_RECREATION.md`

### 3. VS Code Uses Wrong Interpreter

**Problem:** VS Code uses system Python or wrong virtual environment.

**Solution:**
```bash
# 1. Clear Python extension cache
rm -rf ~/.vscode-server/data/User/workspaceStorage/*/ms-python.python/

# 2. Restart VS Code
pkill -f 'vscode-server'

# 3. Manually select interpreter
# Ctrl+Shift+P → "Python: Select Interpreter" → Choose .venv/bin/python
```

### 4. Slow UV Operations in WSL2

**Problem:** UV operations are slow due to cross-filesystem access.

**Solution:** Use project-local cache (already configured):
```toml
[tool.uv]
cache-dir = "./.uv_cache"
```

**Verify:**
```bash
# Cache should be in project directory
ls -la .uv_cache
```

### 5. Dependency Resolution Conflicts

**Problem:** UV can't resolve dependencies.

**Solution:**
```bash
# 1. Clear cache
rm -rf .uv_cache

# 2. Update lock file
uv lock --upgrade

# 3. Sync
uv sync --all-extras
```

### 6. Missing Dev Dependencies

**Problem:** Pytest or other dev tools not found.

**Solution:**
```bash
# Sync with all extras
uv sync --all-extras

# Or explicitly install dev dependencies
uv sync --group dev
```

### 7. Python Version Mismatch

**Problem:** Wrong Python version in `.venv`.

**Solution:**
```bash
# Remove and recreate with specific version
rm -rf .venv
uv venv --python 3.12
uv sync --all-extras
```

### 8. UV Configuration Not Applied

**Problem:** Changes to `uv.toml` or `pyproject.toml` not taking effect.

**Solution:**
```bash
# 1. Clear cache
rm -rf .uv_cache

# 2. Rebuild lock file
uv lock

# 3. Sync
uv sync

# 4. Restart VS Code
pkill -f 'vscode-server'
```

---

## Troubleshooting Commands

```bash
# Show UV configuration
uv config show

# Show Python installations
uv python list

# Find active Python
uv python find

# Show environment info
uv venv --help

# Dry run sync
uv sync --dry-run

# Verbose sync
uv sync -v

# Show dependency tree
uv tree

# Check for outdated packages
uv lock --upgrade-package <package>
```

---

## Quick Reference

### Common Commands

```bash
# Create virtual environment
uv venv

# Sync dependencies
uv sync

# Sync with dev dependencies
uv sync --all-extras

# Add package
uv add <package>

# Add dev package
uv add --dev <package>

# Remove package
uv remove <package>

# Update lock file
uv lock

# Run command in environment
uv run <command>

# Run tests
uv run pytest

# Verify configuration
./verify-uv-configuration.sh
```

### VS Code Tasks

- `Ctrl+Shift+P` → "Tasks: Run Task"
- Select from UV tasks menu

### Environment Variables

```bash
# Check current settings
env | grep -E 'VIRTUAL_ENV|UV_'

# Unset VIRTUAL_ENV
unset VIRTUAL_ENV VIRTUAL_ENV_PROMPT

# Set UV_PROJECT_ENVIRONMENT
export UV_PROJECT_ENVIRONMENT=".venv"
```

---

## Success Criteria

✅ UV version 0.8.17 or later installed
✅ `uv.toml` exists with proper configuration
✅ `pyproject.toml` has [tool.uv] section
✅ `.venv` directory exists and contains Python
✅ `list` directory does NOT exist
✅ `VIRTUAL_ENV` not set or points to `.venv`
✅ `UV_PROJECT_ENVIRONMENT=".venv"` in shell profile
✅ `.uv_cache/` in `.gitignore`
✅ VS Code configured to use `.venv/bin/python`
✅ `./verify-uv-configuration.sh` passes all checks
✅ `uv sync` does NOT recreate `list` directory

---

## Additional Resources

- **UV Documentation:** https://docs.astral.sh/uv/
- **UV Configuration:** https://docs.astral.sh/uv/configuration/
- **UV GitHub:** https://github.com/astral-sh/uv
- **Project-Specific Docs:**
  - `FIX_LIST_DIRECTORY_RECREATION.md` - Fix for `list` directory issue
  - `ROOT_CAUSE_ANALYSIS_LIST_DIRECTORY.md` - Technical analysis
  - `VSCODE_PYTEST_CACHE_FIX_COMPLETE.md` - VS Code pytest integration

---

**Last Updated:** 2025-10-04
**UV Version:** 0.8.17
**Python Version:** 3.12.3
**Environment:** WSL2 + VS Code Remote


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs setup uv configuration guide document]]
