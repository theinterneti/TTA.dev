#!/bin/bash
# Configure NotebookLM MCP Server for TTA Research Integration

MCP_CONFIG=~/.config/mcp/mcp_settings.json
GEMINI_KEY=$(grep GEMINI_API_KEY ~/repos/TTA.dev/.env | cut -d= -f2)

echo "🔧 Configuring NotebookLM MCP Server..."

# Backup existing config
cp "$MCP_CONFIG" "$MCP_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"

# Update MCP config with NotebookLM server
cat > /tmp/mcp_update.py << 'PYTHON'
import json
import sys
import os

config_path = sys.argv[1]
gemini_key = sys.argv[2]

with open(config_path, 'r') as f:
    config = json.load(f)

# Add NotebookLM server
config['mcpServers']['notebooklm'] = {
    "command": "node",
    "args": [
        f"{os.path.expanduser('~/mcp-servers/notebooklm-mcp/dist/index.js')}"
    ],
    "env": {
        "GEMINI_API_KEY": gemini_key
    },
    "disabled": False
}

with open(config_path, 'w') as f:
    json.dump(config, f, indent=4)

print(f"✅ NotebookLM MCP server added to {config_path}")
PYTHON

python3 /tmp/mcp_update.py "$MCP_CONFIG" "$GEMINI_KEY"

echo ""
echo "✅ Configuration complete!"
echo ""
echo "Next steps:"
echo "1. Reload VS Code window (Ctrl+Shift+P → 'Developer: Reload Window')"
echo "2. Check tools available in Copilot"
echo "3. Test with: 'Query NotebookLM about TTA'"
