#!/bin/bash
# scripts/setup/cline-agent.sh
# Setup for Cline Extension agent context

set -euo pipefail

log_info() { echo -e "\033[0;34mℹ️  $1\033[0m"; }
log_success() { echo -e "\033[0;32m✅ $1\033[0m"; }
log_warning() { echo -e "\033[1;33m⚠️  $1\033[0m"; }

log_info "Setting up Cline Agent workspace..."

# Check if Cline extension is installed
if command -v code >/dev/null 2>&1; then
    if code --list-extensions | grep -q "saoudrizwan.claude-dev"; then
        log_success "Cline extension detected"
    else
        log_warning "Cline extension not found, installing..."
        code --install-extension saoudrizwan.claude-dev --force
    fi
else
    log_warning "VS Code not found, cannot verify Cline installation"
fi

# Setup MCP integration for Cline
log_info "Configuring MCP integration for Cline..."

# Cline uses VS Code's MCP configuration, so we set that up
mkdir -p ~/.config/mcp

# Enhanced MCP configuration with Cline-specific optimizations
cat > ~/.config/mcp/mcp_settings.json << 'EOF'
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"],
      "description": "Library documentation and code examples",
      "capabilities": ["documentation", "examples", "best-practices"]
    },
    "ai-toolkit": {
      "command": "npx",
      "args": ["-y", "@ai-toolkit/mcp-server"],
      "description": "AI development best practices and guidance",
      "capabilities": ["agent-patterns", "evaluation", "tracing"]
    },
    "grafana": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--network=host",
        "mcp-grafana"
      ],
      "description": "Observability and monitoring queries",
      "capabilities": ["metrics", "logs", "dashboards"]
    },
    "pylance": {
      "command": "python",
      "args": ["-m", "mcp_pylance"],
      "description": "Python development tools and analysis",
      "capabilities": ["syntax-check", "imports", "environments"]
    }
  },
  "cline": {
    "preferredServers": ["context7", "ai-toolkit"],
    "autoConnect": true,
    "maxConcurrentConnections": 3
  }
}
EOF

log_success "MCP configuration optimized for Cline"

# Create Cline-specific workspace configuration
log_info "Setting up Cline workspace configuration..."

mkdir -p .vscode

# Add Cline-specific settings to VS Code configuration
CLINE_SETTINGS='{
  "cline.mcp.enabled": true,
  "cline.mcp.autoConnect": true,
  "cline.contextWindow": 200000,
  "cline.maxResponseTokens": 8192,
  "cline.temperature": 0.7,
  "cline.experimental.advancedReasoning": true,
  "cline.experimental.mcp.preferredServers": [
    "context7",
    "ai-toolkit",
    "pylance"
  ]
}'

# Merge with existing settings if they exist
if [ -f .vscode/settings.json ]; then
    # Use Python to merge JSON (more reliable than manual editing)
    uv run python << 'EOF'
import json
import os

# Load existing settings
with open('.vscode/settings.json', 'r') as f:
    existing = json.load(f)

# Cline-specific settings
cline_settings = {
    "cline.mcp.enabled": True,
    "cline.mcp.autoConnect": True,
    "cline.contextWindow": 200000,
    "cline.maxResponseTokens": 8192,
    "cline.temperature": 0.7,
    "cline.experimental.advancedReasoning": True,
    "cline.experimental.mcp.preferredServers": [
        "context7",
        "ai-toolkit",
        "pylance"
    ]
}

# Merge settings
existing.update(cline_settings)

# Write back
with open('.vscode/settings.json', 'w') as f:
    json.dump(existing, f, indent=2)

print("✅ Cline settings merged with existing VS Code configuration")
EOF
else
    # Create new settings file
    cat > .vscode/settings.json << EOF
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "cline.mcp.enabled": true,
  "cline.mcp.autoConnect": true,
  "cline.contextWindow": 200000,
  "cline.maxResponseTokens": 8192,
  "cline.temperature": 0.7,
  "cline.experimental.advancedReasoning": true,
  "cline.experimental.mcp.preferredServers": [
    "context7",
    "ai-toolkit",
    "pylance"
  ]
}
EOF
    log_success "Cline VS Code settings created"
fi

# Create Cline-specific instruction file
log_info "Creating Cline-specific instructions..."

mkdir -p .cline

cat > .cline/instructions.md << 'EOF'
# Cline Agent Instructions for TTA.dev

## Context Awareness

You are **Cline**, a VS Code extension with enhanced MCP integration capabilities. You have:

✅ **Native MCP Integration** - Better than GitHub Copilot's MCP support
✅ **Enhanced Code Understanding** - Advanced reasoning capabilities
✅ **Multi-step Task Execution** - Can handle complex implementation workflows
✅ **Collaboration Ready** - Work alongside GitHub Copilot seamlessly

## Available MCP Servers

### Context7 - Library Documentation
- Use for researching patterns, best practices, API documentation
- Example: "Research the latest RetryPrimitive patterns from popular libraries"

### AI Toolkit - Agent Development
- Use for AI/agent development guidance and best practices
- Example: "Get best practices for implementing multi-agent coordination"

### Pylance - Python Development
- Use for Python-specific analysis, syntax checking, import resolution
- Example: "Check imports and dependencies for this module"

### Grafana - Observability
- Use for metrics queries, dashboard analysis, monitoring setup
- Example: "Query current cache hit ratios from Prometheus"

## TTA.dev Specific Patterns

### Primitive Development Workflow
1. **Research** - Use Context7 to understand patterns and best practices
2. **Plan** - Break down implementation into steps
3. **Implement** - Create primitive with full type safety
4. **Test** - Add comprehensive tests with 100% coverage
5. **Document** - Create examples and update documentation

### Multi-step Implementation Example
```markdown
I need to add a new CachingRetryPrimitive that combines caching and retry logic.

Step 1: Research existing patterns
- Use Context7 to find caching and retry patterns in popular libraries
- Analyze TTA.dev's existing RetryPrimitive and CachePrimitive

Step 2: Design the primitive
- Define type-safe interfaces
- Plan composition strategy (inherit vs compose)
- Design cache key generation

Step 3: Implement with tests
- Create the primitive implementation
- Add comprehensive test coverage
- Include edge case testing

Step 4: Create examples and documentation
- Write usage examples
- Update PRIMITIVES_CATALOG.md
- Add to package README
```

## Collaboration with GitHub Copilot

**Division of Labor:**
- **Cline**: Complex research, multi-step planning, architecture decisions
- **Copilot**: Quick implementations, code generation, simple edits

**Handoff Pattern:**
```markdown
Cline researches and plans:
"Based on MCP research, here's the recommended approach for RetryPrimitive..."

Then user can ask Copilot:
"@workspace #tta-package-dev
Based on Cline's research above, implement the RetryPrimitive"
```

## Best Practices

### Use MCP for Research
- Always research before implementing
- Look up current best practices
- Understand existing patterns in the ecosystem

### Plan Before Coding
- Break complex tasks into steps
- Consider edge cases and error handling
- Plan testing strategy upfront

### Maintain Context
- Keep conversation focused on current task
- Reference previous research and decisions
- Build incrementally with validation

### Quality Standards
- 100% test coverage for new code
- Full type annotations
- Comprehensive documentation
- Real-world usage examples

## Common Tasks

### Adding a New Primitive
1. Research similar primitives with Context7
2. Check TTA.dev patterns in existing primitives
3. Design type-safe interface
4. Implement with observability integration
5. Add comprehensive tests
6. Create usage examples
7. Update catalog and documentation

### Debugging Issues
1. Use Pylance MCP for syntax/import analysis
2. Check observability data with Grafana MCP
3. Analyze patterns with Context7
4. Implement fixes with comprehensive testing

### Performance Optimization
1. Query current metrics with Grafana MCP
2. Research optimization patterns with Context7
3. Implement changes with before/after benchmarks
4. Validate improvements with monitoring

## Integration Points

- **Package Structure**: Follow monorepo patterns in packages/
- **Testing**: Use pytest with 100% coverage requirement
- **Documentation**: Update both code docs and knowledge base
- **Observability**: Integrate with existing TTA.dev monitoring
- **Type Safety**: Full type annotations with Python 3.11+ features
EOF

log_success "Cline instructions created"

# Test MCP connectivity
log_info "Testing MCP server connectivity for Cline..."

# Test Node.js availability for MCP servers
if command -v npx >/dev/null 2>&1; then
    log_success "Node.js/npx available for MCP servers"

    # Test Context7 server availability (quick check)
    if timeout 10s npx -y @context7/mcp-server --version >/dev/null 2>&1; then
        log_success "Context7 MCP server accessible"
    else
        log_warning "Context7 MCP server may not be available"
    fi
else
    log_warning "Node.js/npx not found - some MCP servers may not work"
fi

# Test Docker for containerized MCP servers
if command -v docker >/dev/null 2>&1; then
    log_success "Docker available for containerized MCP servers"
else
    log_warning "Docker not found - some MCP servers may not work"
fi

log_success "Cline Agent setup complete!"
log_info "Next steps:"
log_info "  1. Reload VS Code window"
log_info "  2. Open Cline extension"
log_info "  3. Test MCP integration with: 'Research RetryPrimitive patterns'"
log_info "  4. Collaborate with Copilot using handoff patterns"
