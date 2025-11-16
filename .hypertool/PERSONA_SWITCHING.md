# Hypertool Persona Switching Guide

## Quick Persona Switch Commands

### Switch to Backend Engineer
```bash
# Update MCP settings
sed -i 's/--persona", "[^"]*"/--persona", "tta-backend-engineer"/' ~/.config/mcp/mcp_settings.json
```

### Switch to Frontend Engineer
```bash
sed -i 's/--persona", "[^"]*"/--persona", "tta-frontend-engineer"/' ~/.config/mcp/mcp_settings.json
```

### Switch to DevOps Engineer
```bash
sed -i 's/--persona", "[^"]*"/--persona", "tta-devops-engineer"/' ~/.config/mcp/mcp_settings.json
```

### Switch to Testing Specialist
```bash
sed -i 's/--persona", "[^"]*"/--persona", "tta-testing-specialist"/' ~/.config/mcp/mcp_settings.json
```

### Switch to Observability Expert
```bash
sed -i 's/--persona", "[^"]*"/--persona", "tta-observability-expert"/' ~/.config/mcp/mcp_settings.json
```

### Switch to Data Scientist
```bash
sed -i 's/--persona", "[^"]*"/--persona", "tta-data-scientist"/' ~/.config/mcp/mcp_settings.json
```

## Or Use the Helper Script

```bash
# Create persona switcher
cat > ~/.local/bin/tta-persona << 'SCRIPT'
#!/bin/bash
PERSONA=$1
if [ -z "$PERSONA" ]; then
  echo "Usage: tta-persona [backend|frontend|devops|testing|observability|data]"
  echo "Current persona:"
  grep -oP '(?<=--persona", ")[^"]*' ~/.config/mcp/mcp_settings.json
  exit 1
fi

case $PERSONA in
  backend)
    FULL_NAME="tta-backend-engineer"
    ;;
  frontend)
    FULL_NAME="tta-frontend-engineer"
    ;;
  devops)
    FULL_NAME="tta-devops-engineer"
    ;;
  testing)
    FULL_NAME="tta-testing-specialist"
    ;;
  observability|obs)
    FULL_NAME="tta-observability-expert"
    ;;
  data|ds)
    FULL_NAME="tta-data-scientist"
    ;;
  *)
    echo "Unknown persona: $PERSONA"
    exit 1
    ;;
esac

sed -i "s/--persona\", \"[^\"]*\"/--persona\", \"$FULL_NAME\"/" ~/.config/mcp/mcp_settings.json
echo "✅ Switched to persona: $FULL_NAME"
echo "🔄 Restart your AI agent (Cline/Cursor) to apply changes"
SCRIPT

chmod +x ~/.local/bin/tta-persona
```

## Usage

```bash
# Switch persona
tta-persona backend
tta-persona frontend
tta-persona devops
tta-persona testing
tta-persona obs
tta-persona data

# Check current persona
tta-persona
```

## Integration with Chat Modes

When using TTA.dev Chat Modes, the persona is automatically selected based on the `.chatmode.md` frontmatter (coming in Phase 2).

## Manual Reload

After switching personas, you need to reload your AI agent:

### Cline
- Restart VS Code or reload window: `Ctrl+Shift+P` → "Developer: Reload Window"

### Cursor
- Restart Cursor or reload window: `Cmd/Ctrl+Shift+P` → "Developer: Reload Window"

### Claude Code
- Restart the application

## Hot-Swapping (Advanced)

For hot-swapping without restart (requires Hypertool v0.0.46+):

```bash
# Enable HTTP mode in Hypertool
export HYPERTOOL_HTTP_MODE=true
export HYPERTOOL_HTTP_PORT=3010

# Switch persona via API
curl -X POST http://localhost:3010/persona/switch \
  -H "Content-Type: application/json" \
  -d '{"persona": "tta-frontend-engineer"}'
```

## Verification

Check active persona:

```bash
# From MCP settings
grep -oP '(?<=--persona", ")[^"]*' ~/.config/mcp/mcp_settings.json

# Or with jq
cat ~/.config/mcp/mcp_settings.json | jq -r '.mcpServers.hypertool.args[] | select(. != "--persona") | select(startswith("tta-"))'
```

## Troubleshooting

### Persona Not Loading
```bash
# Verify persona file exists
ls -la /home/thein/repos/TTA.dev/.hypertool/personas/

# Validate JSON
cat /home/thein/repos/TTA.dev/.hypertool/personas/tta-backend-engineer.json | jq .
```

### MCP Server Not Found
```bash
# Check Hypertool is installed
npx @toolprint/hypertool-mcp@latest --version

# Verify server config
cat /home/thein/repos/TTA.dev/.hypertool/mcp_servers.json | jq .
```

### Changes Not Applied
```bash
# Restart AI agent
# Or clear cache
rm -rf ~/.cache/mcp/*
```
