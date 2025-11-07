# TTA.dev Agent Instruction System

**Comprehensive guidance for all agent roles, contexts, and workspace automation**

---

## 🎯 Overview

This page provides the complete agent instruction system for TTA.dev, ensuring all AI agents have appropriate guidance regardless of their context, role, or skill level.

**Quick Navigation:**
- [[#agent-contexts]] - VS Code, GitHub Actions, Cline, CLI environments
- [[#agent-roles]] - Package Developer, Observability Engineer, etc.
- [[#workspace-automation]] - Automatic setup scripts
- [[#instruction-files]] - File-type specific guidance
- [[#troubleshooting]] - Common issues and solutions

---

## 🤖 Agent Contexts

### Context Detection Matrix

| Agent Context | Environment | Available Tools | Setup Script |
|---------------|-------------|-----------------|--------------|
| **VS Code Extension** | Local VS Code | MCP servers, Copilot toolsets, full filesystem | `scripts/setup/vscode-agent.sh` |
| **GitHub Actions Coding Agent** | Ephemeral cloud runner | uv, pytest, git, standard CLI tools | `scripts/setup/github-actions-agent.sh` |
| **Cline Extension** | Local VS Code | Enhanced MCP integration, VS Code API | `scripts/setup/cline-agent.sh` |
| **GitHub CLI** | Terminal environment | GitHub API, standard shell tools | Manual setup |

### Context-Specific Capabilities

#### 🖥️ VS Code Extension (LOCAL)

**✅ Available:**
- MCP servers (Context7, AI Toolkit, Grafana, Pylance, etc.)
- Copilot toolsets (`#tta-package-dev`, `#tta-observability`, etc.)
- Full local filesystem access
- VS Code extensions and workspace settings
- Docker containers for observability stack

**❌ Not Available:**
- GitHub Actions workflow execution
- Ephemeral environment constraints

**Key Instructions:** `.github/copilot-instructions.md` (LOCAL sections)

#### ☁️ GitHub Actions Coding Agent (CLOUD)

**✅ Available:**
- Standard development tools (uv, pytest, ruff, pyright)
- Git operations and repository access
- Python environment with full dependency tree
- GitHub Actions environment variables
- 60-minute session timeout

**❌ Not Available:**
- MCP servers (VS Code-only feature)
- Copilot toolsets (VS Code-specific)
- VS Code extensions
- Local filesystem (ephemeral runner)
- Docker containers

**Key Instructions:** `.github/copilot-instructions.md` (CLOUD sections)

#### 💻 Cline Extension (LOCAL)

**✅ Available:**
- Enhanced MCP integration with shared settings
- VS Code API access for advanced file operations
- Collaborative features with other AI agents
- Full MCP server ecosystem
- Real-time workspace synchronization

**❌ Not Available:**
- GitHub Actions environment
- Ephemeral constraints

**Key Instructions:** `.cline/instructions.md`

#### 🔧 GitHub CLI (TERMINAL)

**✅ Available:**
- GitHub API operations
- Terminal environment with full shell access
- Git operations and repository management
- Standard CLI tools

**❌ Not Available:**
- MCP servers
- VS Code integration
- Copilot toolsets

**Key Instructions:** Manual setup and standard CLI workflows

---

## 👨‍💻 Agent Roles

### Role Matrix by Skill Level and Focus

| Role | Skill Level | Primary Toolsets | Focus Areas |
|------|-------------|------------------|-------------|
| **Documentation Writer** | Beginner | `#tta-docs`, `#tta-minimal` | README files, guides, user documentation |
| **Package Developer** | Intermediate | `#tta-package-dev`, `#tta-testing` | Core primitives, feature development |
| **Observability Engineer** | Advanced | `#tta-observability`, `#tta-troubleshoot` | Tracing, metrics, debugging |
| **Agent Coordinator** | Expert | `#tta-agent-dev`, `#tta-mcp-integration` | Multi-agent workflows, MCP servers |

### Role-Specific Instructions

#### 📝 Documentation Writer

**Best For:** Agents new to TTA.dev, focusing on user-facing content

**Primary Toolsets:** `#tta-docs`, `#tta-minimal`

**Workflow Pattern:**
```markdown
@workspace #tta-docs
Help me update the README.md to reflect the new CachePrimitive features
```

**Key Responsibilities:**
- Maintain user-facing documentation
- Create getting started guides
- Update API documentation
- Write tutorial content

**Skill Progression:**
1. **Start:** Basic documentation updates
2. **Develop:** Complex guide creation
3. **Master:** Technical architecture docs
4. **Graduate to:** Package Developer role

#### 🔧 Package Developer

**Best For:** Agents with Python experience, implementing features

**Primary Toolsets:** `#tta-package-dev`, `#tta-testing`

**Workflow Pattern:**
```markdown
@workspace #tta-package-dev
Implement a new RouterPrimitive with latency-based routing logic
```

**Key Responsibilities:**
- Develop new primitives
- Implement core features
- Write comprehensive tests
- Maintain package APIs

**Skill Progression:**
1. **Start:** Simple primitive modifications
2. **Develop:** New primitive creation
3. **Master:** Complex composition patterns
4. **Graduate to:** Observability Engineer or Agent Coordinator

#### 📊 Observability Engineer

**Best For:** Agents with production systems experience

**Primary Toolsets:** `#tta-observability`, `#tta-troubleshoot`

**Workflow Pattern:**
```markdown
@workspace #tta-observability
Add Prometheus metrics to track CachePrimitive hit rates and TTL effectiveness
```

**Key Responsibilities:**
- Implement tracing and metrics
- Debug production issues
- Optimize performance bottlenecks
- Maintain observability stack

**Skill Progression:**
1. **Start:** Basic metric implementation
2. **Develop:** Complex tracing patterns
3. **Master:** Production debugging expertise
4. **Graduate to:** Agent Coordinator role

#### 🧠 Agent Coordinator

**Best For:** Expert agents orchestrating complex workflows

**Primary Toolsets:** `#tta-agent-dev`, `#tta-mcp-integration`, `#tta-full-stack`

**Workflow Pattern:**
```markdown
@workspace #tta-agent-dev
Design a multi-agent workflow where one agent plans, another implements, and a third validates
```

**Key Responsibilities:**
- Design multi-agent architectures
- Develop MCP server integrations
- Coordinate cross-package workflows
- Handle complex technical decisions

**Skill Progression:**
1. **Start:** Basic agent coordination
2. **Develop:** MCP server creation
3. **Master:** Complex multi-agent orchestration
4. **Expertise:** System architecture decisions

---

## ⚡ Workspace Automation

### Master Setup Script

**Location:** `scripts/setup-agent-workspace.sh`

**Features:**
- Automatic context detection (VS Code, GitHub Actions, Cline)
- Environment validation and setup
- Role-appropriate tool installation
- Observability stack initialization
- Error handling and recovery

**Usage:**
```bash
# Auto-detect context and setup
./scripts/setup-agent-workspace.sh

# Force specific context
./scripts/setup-agent-workspace.sh --context vscode-local

# Show setup options
./scripts/setup-agent-workspace.sh --help
```

### Context-Specific Setup Scripts

| Script | Context | Purpose |
|--------|---------|---------|
| `scripts/setup-agent-workspace.sh` | Auto-detect | Master setup with context detection |
| `scripts/setup/vscode-agent.sh` | VS Code Local | MCP servers, extensions, toolsets |
| `scripts/setup/github-actions-agent.sh` | GitHub Actions | CI/CD environment validation |
| `scripts/setup/cline-agent.sh` | Cline Extension | Enhanced MCP integration |

---

## 📚 Agent Instruction Files

### File-Type Specific Instructions

Located in `.github/instructions/`:

| File | Applies To | Purpose |
|------|------------|---------|
| `package-source.instructions.md` | `packages/**/src/**/*.py` | Production code standards |
| `tests.instructions.md` | `**/tests/**/*.py` | Testing patterns and coverage |
| `documentation.instructions.md` | `**/*.md` | Documentation formatting |
| `scripts.instructions.md` | `scripts/**/*.py` | Automation script patterns |
| `logseq-knowledge-base.instructions.md` | `**` | TODO management system |

### Context-Specific Instructions

| Agent Context | Primary Instructions | Additional Files |
|---------------|---------------------|------------------|
| **VS Code Extension** | `.github/copilot-instructions.md` | `.vscode/copilot-toolsets.jsonc` |
| **Coding Agent** | `.github/copilot-instructions.md` | `.github/workflows/*.yml` |
| **Cline Extension** | `.cline/instructions.md` | MCP configuration |
| **Package Development** | `packages/*/AGENTS.md` | Package-specific guidance |

---

## 🎯 Quick Start Guide

### For New Agents

**Step 1: Detect Your Context**
```bash
# Run setup script - it will detect your environment
./scripts/setup-agent-workspace.sh
```

**Step 2: Choose Your Role**
- **New to TTA.dev?** Start with Documentation Writer (`#tta-docs`)
- **AI/Agent Experience?** Try Package Developer (`#tta-package-dev`)
- **Production Systems?** Consider Observability Engineer (`#tta-observability`)
- **Expert Developer?** Explore Agent Coordinator (`#tta-agent-dev`)

**Step 3: Test Your Setup**
```markdown
# VS Code/Cline users
@workspace #[your-chosen-toolset]
Help me understand the TTA.dev architecture and recommend next steps

# Coding Agent users
uv run pytest -v  # Validate environment
```

### For Existing Users

**Upgrade Your Setup:**
```bash
# Re-run setup to get latest configurations
./scripts/setup-agent-workspace.sh --force
```

**Switch Contexts:**
```bash
# Explicitly set context if auto-detection is wrong
./scripts/setup-agent-workspace.sh --context vscode-local
```

---

## 🔧 Troubleshooting

### Common Issues

**MCP Servers Not Working (VS Code/Cline)**
```bash
# Check MCP configuration
cat ~/.config/mcp/mcp_settings.json

# Test Node.js availability
npx --version

# Reload VS Code window
# Command Palette → "Developer: Reload Window"
```

**Toolsets Not Available (VS Code)**
```bash
# Check toolset configuration
cat .vscode/copilot-toolsets.jsonc

# Verify extensions installed
code --list-extensions | grep copilot
```

**Python Environment Issues (All Contexts)**
```bash
# Re-sync dependencies
uv sync --all-extras

# Check Python path
uv run python -c "import sys; print(sys.executable)"

# Validate core imports
uv run python -c "import tta_dev_primitives; print('✅ Working')"
```

**Observability Stack Not Running (Local)**
```bash
# Start observability infrastructure
docker-compose -f docker-compose.integration.yml up -d

# Check services
docker-compose -f docker-compose.integration.yml ps

# Verify access
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3000/api/health # Grafana
```

### Getting Help

**Priority Order:**
1. **Check setup script output** - Contains specific error messages
2. **Run workspace validation** - `./scripts/setup-agent-workspace.sh --force`
3. **Review context-specific instructions** - Match your environment
4. **Check file-type instructions** - For specific coding tasks
5. **Open GitHub issue** - For persistent problems

---

## 📈 Future Enhancements

### Planned Features

**Agent Performance Analytics:**
- Track agent effectiveness by role and toolset
- Measure setup success rates
- Optimize configurations based on usage patterns

**Dynamic Role Switching:**
- Automatically suggest role changes based on task complexity
- Context-aware toolset recommendations
- Seamless handoffs between agent types

**Enhanced MCP Integration:**
- Custom TTA.dev MCP servers
- Better integration with Cline and other agents
- Shared MCP server pools for team collaboration

**Automated Onboarding:**
- Interactive setup wizard
- Skill assessment and role matching
- Personalized learning paths

---

## 📋 Related Documentation

### Core Pages
- [[TTA.dev]] - Main project overview
- [[AGENTS.md]] - Agent hub and entry point
- [[TODO Management System]] - Task tracking system

### Setup & Configuration
- [[TTA.dev/DevOps Studio Architecture]] - Infrastructure overview
- [[TTA.dev/DevOps Studio/Monitoring Stack]] - Observability setup
- `.vscode/README.md` - Copilot toolsets guide

### Package-Specific
- [[TTA.dev/Packages/tta-dev-primitives]] - Core primitives
- [[TTA.dev/Packages/tta-observability-integration]] - Observability
- [[TTA.dev/Packages/universal-agent-context]] - Agent coordination

---

**Last Updated:** November 7, 2025
**System Version:** 1.0
**Maintained by:** TTA.dev Team
