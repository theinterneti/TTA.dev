#!/bin/bash
# Test script to verify MCP servers can be reached

echo "=== MCP Server Diagnostics ==="
echo ""

echo "📍 Configuration Location:"
echo "   ~/.config/mcp/mcp_settings.json"
echo ""

echo "🔍 Checking Required Commands:"
echo ""

# Check npx
if command -v /usr/bin/npx &> /dev/null; then
    echo "✅ npx: $(/usr/bin/npx --version)"
else
    echo "❌ npx: NOT FOUND at /usr/bin/npx"
fi

# Check node
if command -v /usr/bin/node &> /dev/null; then
    echo "✅ node: $(/usr/bin/node --version)"
else
    echo "❌ node: NOT FOUND at /usr/bin/node"
fi

# Check docker
if command -v /usr/bin/docker &> /dev/null; then
    echo "✅ docker: $(/usr/bin/docker --version | head -n1)"
else
    echo "❌ docker: NOT FOUND at /usr/bin/docker"
fi

# Check uv
if command -v /home/thein/.local/bin/uv &> /dev/null; then
    echo "✅ uv: $(/home/thein/.local/bin/uv --version)"
else
    echo "❌ uv: NOT FOUND at /home/thein/.local/bin/uv"
fi

echo ""
echo "🔧 Configured MCP Servers:"
echo ""

cat ~/.config/mcp/mcp_settings.json | jq -r '.mcpServers | to_entries[] | "   \(.key): \(if .value.disabled then "❌ Disabled" else "✅ Enabled" end) - \(.value.command // .value.url)"'

echo ""
echo "📊 Server Count:"
cat ~/.config/mcp/mcp_settings.json | jq '.mcpServers | length'

echo ""
echo "🧪 Testing Server Commands:"
echo ""

# Test Context7
echo "Testing Context7..."
if /usr/bin/npx -y @upstash/context7-mcp@latest --version &> /dev/null; then
    echo "   ✅ Context7 package accessible"
else
    echo "   ⚠️  Context7 may need first-time download"
fi

# Test Playwright
echo "Testing Playwright..."
if /usr/bin/npx @playwright/mcp@latest --help &> /dev/null; then
    echo "   ✅ Playwright package accessible"
else
    echo "   ⚠️  Playwright may need first-time download"
fi

# Test Docker
echo "Testing Docker..."
if /usr/bin/docker info &> /dev/null; then
    echo "   ✅ Docker daemon running"
else
    echo "   ❌ Docker daemon NOT running"
fi

# Test Sequential Thinking
echo "Testing Sequential Thinking..."
if /usr/bin/npx -y mcp-sequentialthinking-tools --version &> /dev/null; then
    echo "   ✅ Sequential Thinking package accessible"
else
    echo "   ⚠️  Sequential Thinking may need first-time download"
fi

# Test GitMCP
echo "Testing GitMCP..."
if curl -s -I https://gitmcp.io/theinterneti/TTA.dev | head -n1 | grep -q "200"; then
    echo "   ✅ GitMCP web API reachable"
else
    echo "   ⚠️  GitMCP web API may be slow or unreachable"
fi

echo ""
echo "✅ Diagnostics Complete"
echo ""
echo "🔄 Next Steps:"
echo "   1. Reload VS Code window (Ctrl+Shift+P → 'Developer: Reload Window')"
echo "   2. Check VS Code Output → MCP Servers for connection logs"
echo "   3. Test in Copilot chat with: @workspace Test Context7"
