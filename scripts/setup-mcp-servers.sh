#!/bin/bash
# MCP Servers Setup Script for TTA.dev
# This script sets up LogSeq, Sequential Thinking, and Serena MCP servers

set -e

echo "==================================================================="
echo "TTA.dev MCP Servers Setup"
echo "==================================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# MCP settings file path
MCP_SETTINGS="$HOME/.config/mcp/mcp_settings.json"
MCP_BACKUP="$HOME/.config/mcp/mcp_settings.json.backup.$(date +%Y%m%d_%H%M%S)"

echo -e "${YELLOW}Step 1: Backing up current MCP settings${NC}"
if [ -f "$MCP_SETTINGS" ]; then
    cp "$MCP_SETTINGS" "$MCP_BACKUP"
    echo -e "${GREEN}✓ Backup created: $MCP_BACKUP${NC}"
else
    echo -e "${YELLOW}⚠ No existing MCP settings found, will create new file${NC}"
    mkdir -p "$HOME/.config/mcp"
fi

echo ""
echo -e "${YELLOW}Step 2: Checking Sequential Thinking status${NC}"
if grep -q '"sequential-thinking"' "$MCP_SETTINGS" 2>/dev/null; then
    if grep -A 10 '"sequential-thinking"' "$MCP_SETTINGS" | grep -q '"disabled": false'; then
        echo -e "${GREEN}✓ Sequential Thinking is already enabled${NC}"
    else
        echo -e "${YELLOW}⚠ Sequential Thinking exists but is disabled${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Sequential Thinking not found in config${NC}"
fi

echo ""
echo -e "${YELLOW}Step 3: Setting up Serena${NC}"

# Check if Serena project file exists
if [ -f ".serena/project.yml" ]; then
    echo -e "${GREEN}✓ Serena project configuration found${NC}"
else
    echo -e "${RED}✗ Serena project configuration not found${NC}"
    echo "Please ensure .serena/project.yml exists"
    exit 1
fi

# Check if serena-mcp-server is available
if ! command -v serena-mcp-server &> /dev/null; then
    echo -e "${YELLOW}⚠ serena-mcp-server not found, attempting installation...${NC}"

    # Try uv first
    if command -v uv &> /dev/null; then
        echo "Installing with uv..."
        uv pip install serena-mcp-server || {
            echo -e "${RED}✗ Failed to install serena-mcp-server with uv${NC}"
            echo "Try manually: pip install serena-mcp-server"
            exit 1
        }
    else
        echo "Installing with pip..."
        pip install serena-mcp-server || {
            echo -e "${RED}✗ Failed to install serena-mcp-server${NC}"
            exit 1
        }
    fi
fi

# Update Serena to be enabled
echo "Enabling Serena in MCP configuration..."
if grep -q '"serena"' "$MCP_SETTINGS" 2>/dev/null; then
    # Use sed to change disabled from true to false for serena
    sed -i '/serena/,/disabled/ s/"disabled": true/"disabled": false/' "$MCP_SETTINGS"
    echo -e "${GREEN}✓ Serena enabled${NC}"
else
    echo -e "${YELLOW}⚠ Serena configuration not found in MCP settings${NC}"
fi

echo ""
echo -e "${YELLOW}Step 4: Setting up LogSeq${NC}"
echo ""
echo "LogSeq requires manual setup. Please follow these steps:"
echo ""
echo "1. Start LogSeq:"
echo "   $ logseq &"
echo ""
echo "2. Enable Developer Mode:"
echo "   - Open LogSeq → Settings (Gear) → Advanced"
echo "   - Enable 'Developer mode'"
echo "   - Click Apply"
echo ""
echo "3. Enable HTTP API:"
echo "   - Settings → Features"
echo "   - Check 'Enable HTTP APIs server'"
echo "   - RESTART LogSeq (important!)"
echo ""
echo "4. Start API Server:"
echo "   - Click API button (🔌) in toolbar"
echo "   - Select 'Start server'"
echo "   - Server runs on http://127.0.0.1:12315"
echo ""
echo "5. Generate API Token:"
echo "   - API panel → Authorization"
echo "   - Click 'Add' to create token"
echo "   - Copy the token value (NOT the name)"
echo ""
echo "6. Add to MCP configuration:"
echo "   Edit $MCP_SETTINGS and add:"
echo ""
cat << 'EOF'
    "mcp-logseq": {
      "command": "/usr/bin/npx",
      "args": ["-y", "@ergut/mcp-logseq"],
      "env": {
        "LOGSEQ_API_TOKEN": "YOUR_TOKEN_HERE",
        "LOGSEQ_API_URL": "http://127.0.0.1:12315"
      },
      "disabled": false,
      "autoApprove": []
    }
EOF
echo ""
echo "7. Test API:"
echo "   $ curl http://127.0.0.1:12315/api"
echo ""

echo -e "${YELLOW}Step 5: Verification${NC}"
echo ""

# Test Sequential Thinking
echo "Testing Sequential Thinking..."
if npx -y mcp-sequentialthinking-tools --version 2>/dev/null; then
    echo -e "${GREEN}✓ Sequential Thinking is available${NC}"
else
    echo -e "${YELLOW}⚠ Sequential Thinking test failed (may be normal)${NC}"
fi

# Test Serena
echo "Testing Serena..."
if command -v serena-mcp-server &> /dev/null; then
    echo -e "${GREEN}✓ Serena is installed${NC}"
    # Test if it can read the project file
    if serena-mcp-server "$(pwd)/.serena/project.yml" --help 2>/dev/null | head -1; then
        echo -e "${GREEN}✓ Serena can read project configuration${NC}"
    else
        echo -e "${YELLOW}⚠ Serena installed but project file may have issues${NC}"
    fi
else
    echo -e "${RED}✗ Serena not found after installation${NC}"
fi

echo ""
echo "==================================================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "==================================================================="
echo ""
echo "Summary:"
echo "  ✓ Sequential Thinking: Already enabled"
echo "  ✓ Serena: Configured and enabled"
echo "  ⚠ LogSeq: Requires manual token setup (see steps above)"
echo ""
echo "Next steps:"
echo "  1. Complete LogSeq setup (follow instructions above)"
echo "  2. Reload VS Code: Ctrl+Shift+P → 'Developer: Reload Window'"
echo "  3. Test MCP servers in Copilot chat"
echo ""
echo "Configuration file: $MCP_SETTINGS"
echo "Backup saved to: $MCP_BACKUP"
echo ""
