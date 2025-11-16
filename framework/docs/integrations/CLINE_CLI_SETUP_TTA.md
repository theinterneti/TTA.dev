# Cline CLI Setup for TTA.dev

**Quick configuration guide to make Cline CLI aware of TTA.dev context**

---

## ✅ Good News

TTA.dev already has Cline instructions configured at:

```
/home/thein/repos/TTA.dev/.cline/instructions.md
```

This file contains all TTA.dev-specific patterns, coding standards, and best practices.

---

## 🔍 Verify Cline CLI Can See Instructions

### Test 1: Check if Cline reads .cline/instructions.md

```bash
cd /home/thein/repos/TTA.dev

# Simple test
cline "What package manager should I use for this project?"

# Expected response should mention "uv" (from .cline/instructions.md)
```

**If Cline doesn't mention `uv`:** The CLI might not be reading the custom instructions.

### Test 2: Check MCP Server Access

```bash
# Test if Cline can access MCP servers
cline "Using Context7, find documentation for pytest-asyncio"

# Expected: Cline should call Context7 MCP server
```

**If Cline says "I don't have access to Context7":** MCP servers aren't configured for CLI.

---

## 🛠️ Configuration Steps

### Step 1: Verify MCP Configuration

Check if MCP servers are configured:

```bash
cat ~/.config/mcp/mcp_settings.json
```

**Should contain:**
- `context7` server
- `grafana` server
- `pylance` server
- Other TTA.dev MCP servers

**If file doesn't exist:** The VS Code extension has MCP servers, but CLI needs separate configuration.

### Step 2: Set Working Directory

Cline CLI needs to be run **from the TTA.dev directory** to access `.cline/instructions.md`:

```bash
# Always run Cline from TTA.dev root
cd /home/thein/repos/TTA.dev

# Then use Cline
cline "Your task here"
```

**Why:** Cline looks for `.cline/instructions.md` in the current directory or parent directories.

### Step 3: Test with TTA.dev-Specific Task

```bash
cd /home/thein/repos/TTA.dev

cline "List all primitives in packages/tta-dev-primitives/src/tta_dev_primitives/core/"
```

**Expected behavior:**
1. Cline should list files in that directory
2. Response should show awareness of TTA.dev structure
3. Should mention primitives using TTA.dev terminology

---

## 🔧 Advanced Configuration

### Option 1: Create Project-Specific Alias

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# TTA.dev-specific Cline alias
alias tta-cline='cd /home/thein/repos/TTA.dev && cline'

# Reload shell
source ~/.bashrc
```

**Usage:**
```bash
tta-cline "Add type hints to cache.py"
```

This ensures Cline always runs in TTA.dev context.

### Option 2: Create cline-config.json

Create a project-specific config file:

```bash
cat > /home/thein/repos/TTA.dev/.cline/config.json << 'EOF'
{
  "customInstructions": ".cline/instructions.md",
  "mcpServers": "~/.config/mcp/mcp_settings.json",
  "workspaceRoot": "/home/thein/repos/TTA.dev",
  "defaultModel": "mistralai/mistral-small-3.2",
  "autoApprove": false,
  "verboseLogging": true
}
EOF
```

**Note:** This is a proposed format - actual Cline CLI config format may differ. Check `cline config --help` for supported options.

### Option 3: Environment Variables

Set TTA.dev-specific environment variables:

```bash
# Add to ~/.bashrc
export CLINE_WORKSPACE=/home/thein/repos/TTA.dev
export CLINE_INSTRUCTIONS=/home/thein/repos/TTA.dev/.cline/instructions.md
export CLINE_MCP_CONFIG=~/.config/mcp/mcp_settings.json
```

---

## 🧪 Test Suite for Cline CLI

Run these tests to verify Cline CLI is properly configured:

### Test 1: Custom Instructions
```bash
cd /home/thein/repos/TTA.dev
cline "What package manager does this project use?"
```
**✅ Pass:** Response mentions `uv`
**❌ Fail:** Response suggests `pip` or doesn't know

### Test 2: Repository Structure
```bash
cline "What packages are in this monorepo?"
```
**✅ Pass:** Mentions tta-dev-primitives, tta-observability-integration, universal-agent-context
**❌ Fail:** Doesn't know the structure

### Test 3: Coding Standards
```bash
cline "Should I use Optional[str] or str | None for type hints?"
```
**✅ Pass:** Says `str | None` (Python 3.11+ style)
**❌ Fail:** Suggests `Optional[str]` or doesn't know

### Test 4: MCP Server Access
```bash
cline "Using Context7, find documentation for asyncio.gather"
```
**✅ Pass:** Calls Context7 MCP server and retrieves docs
**❌ Fail:** Says "I don't have access to Context7"

### Test 5: File Operations
```bash
cline "Show me the first 10 lines of packages/tta-dev-primitives/README.md"
```
**✅ Pass:** Displays file contents
**❌ Fail:** Can't access file or wrong directory

---

## 🐛 Troubleshooting

### Issue: Cline Doesn't Follow TTA.dev Patterns

**Symptom:** Cline suggests using `pip` instead of `uv`, doesn't know about primitives

**Solution:**
1. Make sure you're in TTA.dev directory: `pwd` should show `/home/thein/repos/TTA.dev`
2. Check `.cline/instructions.md` exists: `cat .cline/instructions.md | head -20`
3. Try explicit prompt: `cline "Read .cline/instructions.md first, then help me with..."`

### Issue: MCP Servers Not Available

**Symptom:** Context7, Grafana, Pylance not accessible from CLI

**Solution:**

The MCP servers might only be configured for VS Code extension, not CLI. Check:

```bash
# Check if MCP config exists
ls -la ~/.config/mcp/

# If missing, Cline CLI needs MCP server configuration
# This might require additional setup
```

**Workaround:** Use Cline VS Code extension for tasks requiring MCP servers, use CLI for simple file operations.

### Issue: Cline Can't Find Files

**Symptom:** "File not found" errors when Cline tries to read TTA.dev files

**Solution:**
```bash
# Always run from project root
cd /home/thein/repos/TTA.dev

# Verify
pwd  # Should show: /home/thein/repos/TTA.dev

# Then use Cline
cline "Your task"
```

### Issue: Different Behavior Than VS Code Extension

**Symptom:** VS Code extension follows TTA.dev patterns, CLI doesn't

**Explanation:**

VS Code extension has additional context:
- Workspace settings
- Open files in editor
- VS Code-specific MCP server connections
- Git integration
- Terminal integration

CLI has limited context:
- Current directory files
- Custom instructions (`.cline/instructions.md`)
- MCP servers (if configured separately)

**Solution:** For complex TTA.dev tasks, prefer VS Code extension. Use CLI for simple, focused tasks.

---

## 📋 Recommended CLI Usage Patterns

### ✅ Good CLI Use Cases

```bash
cd /home/thein/repos/TTA.dev

# File operations
cline "Add type hints to packages/tta-dev-primitives/src/cache.py"

# Simple code generation
cline "Create a test file for CachePrimitive"

# Documentation updates
cline "Update PRIMITIVES_CATALOG.md with CachePrimitive example"

# Validation fixes
./scripts/validate-package.sh tta-dev-primitives | cline -y "Fix these issues"
```

### ⚠️ Better with VS Code Extension

```plaintext
In VS Code Cline panel:

# Complex refactoring (multiple files)
"Refactor all primitives to use new InstrumentedPrimitive base class"

# Architecture decisions
"Should CachePrimitive use LRU or LFU eviction?"

# MCP server integration
"Using Context7, research best practices for async caching, then implement"

# PR reviews
"Review the changes in PR #42 for TTA.dev compliance"
```

---

## 🎯 Quick Reference

### Before Using Cline CLI

```bash
# 1. Navigate to TTA.dev
cd /home/thein/repos/TTA.dev

# 2. Verify you're in the right place
pwd  # Should be: /home/thein/repos/TTA.dev

# 3. Check instructions exist
ls .cline/instructions.md  # Should exist

# 4. Now use Cline
cline "Your task"
```

### Testing CLI Configuration

```bash
# Quick test
cd /home/thein/repos/TTA.dev
cline "What coding standards does this project follow?"

# Should mention: uv, Python 3.11+, type hints, 100% test coverage, primitives pattern
```

---

## 🔗 Related Documentation

- **Custom Instructions:** `/home/thein/repos/TTA.dev/.cline/instructions.md`
- **Agent Instructions:** `/home/thein/repos/TTA.dev/AGENTS.md`
- **Copilot Instructions:** `/home/thein/repos/TTA.dev/.github/copilot-instructions.md`
- **Cline Integration Guide:** `/home/thein/repos/TTA.dev/docs/integrations/CLINE_INTEGRATION_GUIDE.md`
- **MCP Servers:** `/home/thein/repos/TTA.dev/MCP_SERVERS.md`

---

**Next Steps:**

1. Run the test suite above to verify Cline CLI configuration
2. Report back which tests pass/fail
3. We'll troubleshoot any failing tests
4. Create optimal workflow for TTA.dev + Cline CLI

---

**Created:** November 6, 2025
**Status:** Diagnostic and setup guide
