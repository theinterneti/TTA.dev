# TTA.dev Auto-Integration Quick Start

**Goal:** Enable automatic TTA.dev integration for Copilot and Cline with zero manual configuration

**Time to Implement:** 2-3 days  
**Impact:** Immediate 80% improvement in developer experience

---

## 🎯 What This Enables

**Before (Manual):**
```bash
# New developer experience
1. Clone TTA.dev
2. Read 3+ documentation files
3. Manually configure ~/.config/mcp/mcp_settings.json
4. Restart VS Code
5. Remember to use #tta-package-dev hashtags
6. Manually select Hypertool personas
Total time: 30-60 minutes
```

**After (Automatic):**
```bash
# New developer experience
1. Clone TTA.dev
2. Open in VS Code
✨ Everything works automatically
Total time: 0 minutes
```

---

## Implementation Steps

### Step 1: Workspace MCP Configuration (30 mins)

Create workspace-level MCP configuration that auto-discovers on VS Code startup.

**1.1 Create `.vscode/mcp.json`:**

```bash
cat > .vscode/mcp.json << 'EOF'
{
  "$schema": "https://modelcontextprotocol.io/schema.json",
  "version": "1.0",
  "description": "TTA.dev MCP Auto-Configuration",
  
  "mcpServers": {
    "hypertool": {
      "command": "npx",
      "args": [
        "-y",
        "@toolprint/hypertool-mcp@latest",
        "mcp",
        "run",
        "--persona", "${env:HYPERTOOL_PERSONA:-tta-backend-engineer}"
      ],
      "env": {
        "HYPERTOOL_CONFIG_DIR": "${workspaceFolder}/.hypertool",
        "HYPERTOOL_SERVERS_FILE": "${workspaceFolder}/.hypertool/mcp_servers.json"
      },
      "disabled": false,
      "alwaysAllow": [
        "get-active-toolset",
        "list-personas",
        "get-persona-info"
      ]
    }
  },
  
  "settings": {
    "autoStart": true,
    "restartOnChange": true,
    "logLevel": "info"
  }
}
EOF
```

**1.2 Update `.vscode/settings.json`:**

```bash
cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.diagnosticMode": "workspace",
    
    // Ruff - Native Server
    "ruff.nativeServer": true,
    "ruff.configuration": "./pyproject.toml",
    "ruff.lineLength": 88,
    "ruff.fixAll": true,
    "ruff.organizeImports": true,
    
    // MCP Auto-Configuration ✨ NEW
    "mcp.configFile": "${workspaceFolder}/.vscode/mcp.json",
    "mcp.autoStart": true,
    "mcp.watchConfigChanges": true,
    
    // Copilot Integration
    "github.copilot.advanced": {
        "mcpIntegration": "enabled",
        "autoLoadToolsets": true
    },
    
    // Editor
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": "explicit",
        "source.fixAll.ruff": "explicit"
    },
    
    // Terminal
    "terminal.integrated.defaultProfile.linux": "zsh",
    "terminal.integrated.profiles.linux": {
        "zsh": {
            "path": "/usr/bin/zsh"
        }
    }
}
EOF
```

**1.3 Test Auto-Discovery:**

```bash
# Reload VS Code window
# Cmd/Ctrl + Shift + P → "Developer: Reload Window"

# Verify MCP servers started
# Check VS Code Output → "MCP Client"
# Should see: "✅ Hypertool MCP server started"

# Test in Copilot Chat
@workspace What MCP tools are available?
# Should list Hypertool tools automatically
```

---

### Step 2: Copilot Toolset Auto-Activation (1 hour)

Map Copilot toolsets to Hypertool personas for automatic context optimization.

**2.1 Create Toolset-Persona Mapping:**

```bash
cat > .vscode/toolset-persona-map.json << 'EOF'
{
  "$schema": "./schemas/toolset-persona-map.schema.json",
  "version": "1.0",
  "description": "Maps GitHub Copilot toolsets to Hypertool personas",
  
  "mappings": {
    "tta-package-dev": {
      "persona": "tta-backend-engineer",
      "description": "Python package development with TTA.dev primitives",
      "auto_activate": true
    },
    "tta-testing": {
      "persona": "tta-testing-specialist",
      "description": "Test development and quality assurance",
      "auto_activate": true
    },
    "tta-observability": {
      "persona": "tta-observability-expert",
      "description": "Monitoring, tracing, and metrics",
      "auto_activate": true
    },
    "tta-agent-dev": {
      "persona": "tta-backend-engineer",
      "description": "AI agent development and coordination",
      "auto_activate": true
    },
    "tta-mcp-integration": {
      "persona": "tta-backend-engineer",
      "description": "MCP server development",
      "auto_activate": true
    },
    "tta-docs": {
      "persona": "tta-backend-engineer",
      "description": "Documentation and knowledge base",
      "auto_activate": false
    },
    "tta-frontend": {
      "persona": "tta-frontend-engineer",
      "description": "Frontend development with React/TypeScript",
      "auto_activate": true
    },
    "tta-full-stack": {
      "persona": "tta-backend-engineer",
      "description": "Full-stack development",
      "auto_activate": false
    }
  },
  
  "fallback_persona": "tta-backend-engineer",
  "require_confirmation": false
}
EOF
```

**2.2 Create Auto-Activation Script:**

```bash
cat > .vscode/scripts/auto-activate-persona.py << 'EOF'
#!/usr/bin/env python3
"""
Auto-activate Hypertool persona based on Copilot toolset.

This script runs automatically when a Copilot toolset is activated,
switching to the appropriate Hypertool persona for context optimization.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def load_mapping() -> dict:
    """Load toolset-persona mapping."""
    mapping_file = Path(".vscode/toolset-persona-map.json")
    
    if not mapping_file.exists():
        print("⚠️  No toolset-persona mapping found")
        return {}
    
    with open(mapping_file) as f:
        return json.load(f)


def switch_persona(persona: str) -> bool:
    """Switch Hypertool persona using tta-persona CLI."""
    try:
        # Use tta-persona script if available
        result = subprocess.run(
            ["tta-persona", persona],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print(f"✅ Switched to persona: {persona}")
            return True
        else:
            print(f"⚠️  Failed to switch persona: {result.stderr}")
            return False
            
    except FileNotFoundError:
        # Fallback: Update environment variable
        os.environ["HYPERTOOL_PERSONA"] = persona
        print(f"✅ Set HYPERTOOL_PERSONA={persona}")
        return True
    except Exception as e:
        print(f"❌ Error switching persona: {e}")
        return False


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: auto-activate-persona.py <toolset-hashtag>")
        sys.exit(1)
    
    toolset = sys.argv[1].replace("#", "").replace("tta-", "")
    full_toolset = f"tta-{toolset}" if not toolset.startswith("tta-") else toolset
    
    # Load mapping
    mapping = load_mapping()
    
    if not mapping:
        sys.exit(1)
    
    # Get persona for toolset
    toolset_config = mapping.get("mappings", {}).get(full_toolset)
    
    if not toolset_config:
        fallback = mapping.get("fallback_persona", "tta-backend-engineer")
        print(f"⚠️  No mapping for {full_toolset}, using fallback: {fallback}")
        switch_persona(fallback)
        sys.exit(0)
    
    # Check if auto-activation enabled
    if not toolset_config.get("auto_activate", True):
        print(f"ℹ️  Auto-activation disabled for {full_toolset}")
        sys.exit(0)
    
    # Switch persona
    persona = toolset_config["persona"]
    description = toolset_config.get("description", "")
    
    print(f"🔄 Activating {full_toolset}")
    print(f"   → Persona: {persona}")
    print(f"   → Purpose: {description}")
    
    success = switch_persona(persona)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
EOF

chmod +x .vscode/scripts/auto-activate-persona.py
```

**2.3 Test Auto-Activation:**

```bash
# Test the script manually
python .vscode/scripts/auto-activate-persona.py tta-package-dev

# Should output:
# 🔄 Activating tta-package-dev
#    → Persona: tta-backend-engineer
#    → Purpose: Python package development with TTA.dev primitives
# ✅ Switched to persona: tta-backend-engineer

# Test in Copilot
@workspace #tta-package-dev
# Should automatically activate tta-backend-engineer persona
```

---

### Step 3: Cline Auto-Context Enhancement (1 hour)

Enhance Cline's MCP recommendation server to provide automatic TTA.dev context.

**3.1 Update `.cline/instructions.md`:**

Add automatic context loading section:

```markdown
# AUTOMATIC CONTEXT LOADING ✨ NEW

**Before starting ANY task, automatically:**

1. Analyze the task description
2. Call MCP tool: `get_tta_context(task_description)`
3. Apply recommended persona
4. Load relevant primitives
5. Use suggested patterns

**You do this automatically - no need to ask the user!**

Example flow:
```
User: "Add retry logic to this API call"
↓
You automatically call: get_tta_context("Add retry logic to this API call")
↓
Response: {
  "persona": "tta-backend-engineer",
  "primitives": ["RetryPrimitive"],
  "pattern": "recovery",
  "example": "platform/primitives/examples/recovery_patterns.py"
}
↓
You implement using RetryPrimitive without asking
```
```

**3.2 Enhance MCP Server:**

```bash
# Update .cline/mcp-server/tta_recommendations.py
# Add new tool at line 200:

cat >> .cline/mcp-server/tta_recommendations.py << 'EOF'


@server.tool()
async def get_tta_context(task_description: str) -> dict:
    """
    Automatically provide TTA.dev context for any development task.
    
    This tool is called automatically before starting work on a task.
    It provides:
    - Recommended Hypertool persona
    - Relevant TTA.dev primitives
    - Code examples and patterns
    - Best practices
    
    Args:
        task_description: What the user wants to accomplish
        
    Returns:
        Complete context for the task including primitives, examples, and guidance
    """
    
    # Analyze task intent
    task_lower = task_description.lower()
    
    # Detect keywords and map to primitives
    context = {
        "task": task_description,
        "persona": "tta-backend-engineer",  # default
        "primitives": [],
        "patterns": [],
        "examples": [],
        "best_practices": [],
        "imports": []
    }
    
    # Retry/error handling
    if any(word in task_lower for word in ["retry", "error", "fail", "timeout"]):
        context["primitives"].append("RetryPrimitive")
        context["patterns"].append("recovery")
        context["examples"].append("platform/primitives/examples/recovery_patterns.py")
        context["imports"].append("from tta_dev_primitives.recovery import RetryPrimitive")
        context["best_practices"].append("Use exponential backoff with jitter")
    
    # Caching
    if any(word in task_lower for word in ["cache", "store", "memoize", "performance"]):
        context["primitives"].append("CachePrimitive")
        context["patterns"].append("performance")
        context["examples"].append("platform/primitives/examples/cache_patterns.py")
        context["imports"].append("from tta_dev_primitives.performance import CachePrimitive")
        context["best_practices"].append("Set appropriate TTL and max_size")
    
    # Parallel/concurrent
    if any(word in task_lower for word in ["parallel", "concurrent", "multiple", "batch"]):
        context["primitives"].append("ParallelPrimitive")
        context["patterns"].append("concurrency")
        context["examples"].append("platform/primitives/examples/parallel_execution.py")
        context["imports"].append("from tta_dev_primitives import ParallelPrimitive")
        context["best_practices"].append("Use | operator for parallel composition")
    
    # Sequential workflow
    if any(word in task_lower for word in ["workflow", "pipeline", "sequence", "chain"]):
        context["primitives"].append("SequentialPrimitive")
        context["patterns"].append("composition")
        context["examples"].append("platform/primitives/examples/basic_sequential.py")
        context["imports"].append("from tta_dev_primitives import SequentialPrimitive")
        context["best_practices"].append("Use >> operator for sequential composition")
    
    # Testing
    if any(word in task_lower for word in ["test", "mock", "unittest", "pytest"]):
        context["primitives"].append("MockPrimitive")
        context["persona"] = "tta-testing-specialist"
        context["patterns"].append("testing")
        context["examples"].append("platform/primitives/tests/")
        context["imports"].append("from tta_dev_primitives.testing import MockPrimitive")
        context["best_practices"].append("Use AAA pattern (Arrange, Act, Assert)")
    
    # Observability
    if any(word in task_lower for word in ["trace", "metric", "monitor", "observability"]):
        context["persona"] = "tta-observability-expert"
        context["patterns"].append("observability")
        context["examples"].append("platform/observability/")
        context["best_practices"].append("All primitives have built-in observability")
    
    # Add general best practices
    if context["primitives"]:
        context["best_practices"].extend([
            "Always use primitives instead of manual async code",
            "Compose primitives with >> and | operators",
            "Include WorkflowContext for tracing",
            "Write tests with 100% coverage"
        ])
    
    return context
EOF
```

**3.3 Test Auto-Context:**

```bash
# Restart Cline MCP server
# In Cline chat, try:

"Add retry logic to the API call in api_client.py"

# Cline should automatically:
# 1. Call get_tta_context()
# 2. See RetryPrimitive recommended
# 3. Use it without asking
```

---

### Step 4: Add VS Code Task for Quick Setup (15 mins)

**4.1 Update `.vscode/tasks.json`:**

```bash
cat > .vscode/tasks.json << 'EOF'
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "🚀 Setup TTA.dev Auto-Integration",
            "type": "shell",
            "command": "bash",
            "args": [
                "-c",
                "echo '🔧 Setting up auto-integration...' && python .vscode/scripts/setup-auto-integration.py && echo '✅ Auto-integration ready!'"
            ],
            "problemMatcher": [],
            "group": "build"
        },
        {
            "label": "🔍 Verify MCP Servers",
            "type": "shell",
            "command": "bash",
            "args": [
                "-c",
                "echo '🔍 Checking MCP servers...' && npx @toolprint/hypertool-mcp mcp list && echo '✅ Verification complete'"
            ],
            "problemMatcher": [],
            "group": "test"
        },
        {
            "label": "Run Tests",
            "type": "shell",
            "command": "uv run pytest -v",
            "group": {
                "kind": "test",
                "isDefault": true
            }
        },
        {
            "label": "Format Code",
            "type": "shell",
            "command": "uv run ruff format .",
            "group": "build"
        },
        {
            "label": "Lint Code",
            "type": "shell",
            "command": "uv run ruff check . --fix",
            "group": "build"
        }
    ]
}
EOF
```

**4.2 Create Setup Script:**

```bash
cat > .vscode/scripts/setup-auto-integration.py << 'EOF'
#!/usr/bin/env python3
"""Quick setup script for TTA.dev auto-integration."""

import os
import subprocess
from pathlib import Path


def check_hypertool_installed() -> bool:
    """Check if Hypertool is available."""
    try:
        result = subprocess.run(
            ["npx", "-y", "@toolprint/hypertool-mcp@latest", "--version"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False


def check_mcp_config() -> bool:
    """Check if MCP config exists."""
    return Path(".vscode/mcp.json").exists()


def check_persona_mapping() -> bool:
    """Check if persona mapping exists."""
    return Path(".vscode/toolset-persona-map.json").exists()


def main():
    """Run setup checks."""
    print("\n📋 TTA.dev Auto-Integration Setup\n")
    
    checks = {
        "Hypertool MCP available": check_hypertool_installed(),
        "MCP config (.vscode/mcp.json)": check_mcp_config(),
        "Persona mapping (.vscode/toolset-persona-map.json)": check_persona_mapping()
    }
    
    all_good = True
    for check, status in checks.items():
        emoji = "✅" if status else "❌"
        print(f"{emoji} {check}")
        if not status:
            all_good = False
    
    print()
    
    if all_good:
        print("🎉 Auto-integration is ready!")
        print()
        print("Try it out:")
        print("1. @workspace #tta-package-dev (auto-activates tta-backend-engineer)")
        print("2. Ask Cline to implement something (auto-loads TTA.dev context)")
        print()
    else:
        print("⚠️  Some components need setup. See docs/mcp/AUTO_INTEGRATION_QUICKSTART.md")
        print()


if __name__ == "__main__":
    main()
EOF

chmod +x .vscode/scripts/setup-auto-integration.py
```

---

## Testing the Integration

### Test 1: Fresh Clone

```bash
# Simulate new developer
cd /tmp
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev
code .

# Wait for VS Code to load
# Check Output → MCP Client
# Should see: "✅ Hypertool MCP server started"

# Test in Copilot
@workspace What primitives are available?
# Should list TTA.dev primitives automatically
```

### Test 2: Toolset Auto-Activation

```bash
# In Copilot Chat
@workspace #tta-package-dev

# Check VS Code status bar
# Should see: "Persona: tta-backend-engineer" (if extension installed)

# Verify in terminal
echo $HYPERTOOL_PERSONA
# Should output: tta-backend-engineer
```

### Test 3: Cline Auto-Context

```bash
# In Cline chat
"Add caching to this expensive function"

# Cline should automatically:
# 1. Detect "caching" keyword
# 2. Call get_tta_context()
# 3. Suggest CachePrimitive
# 4. Implement without asking
```

---

## Success Criteria

- [ ] MCP servers auto-start when opening TTA.dev workspace
- [ ] No manual configuration required in `~/.config/mcp/mcp_settings.json`
- [ ] Copilot toolsets auto-activate correct Hypertool persona
- [ ] Cline automatically suggests TTA.dev primitives
- [ ] New developer can be productive in < 5 minutes
- [ ] Zero-config for common development tasks

---

## Rollback Plan

If auto-integration causes issues:

```bash
# Disable workspace MCP
mv .vscode/mcp.json .vscode/mcp.json.disabled

# Disable auto-activation
mv .vscode/toolset-persona-map.json .vscode/toolset-persona-map.json.disabled

# Reload VS Code
# Cmd/Ctrl + Shift + P → "Developer: Reload Window"

# Revert to manual MCP configuration
cp ~/.config/mcp/mcp_settings.json.backup ~/.config/mcp/mcp_settings.json
```

---

## Next Steps

After implementing this quick start:

1. Test with 2-3 developers
2. Gather feedback
3. Iterate on persona mappings
4. Implement Priority 3-5 from AUTO_INTEGRATION_ANALYSIS.md

---

**Last Updated:** November 17, 2025  
**Status:** Ready for Implementation  
**Estimated Time:** 2-3 days  
**Impact:** 80% reduction in setup time
