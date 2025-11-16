# TTA.dev Application Architecture - What Does "Starting" Mean?

**Date:** November 15, 2025  
**Question:** What is the "actual TTA.dev application" and how should it be deployed?

---

## 🤔 The Core Question

You've built something that **doesn't fit traditional deployment models**. Let's analyze what TTA.dev actually is and explore deployment options.

---

## 📊 What TTA.dev Actually Is

### Current Evidence

Based on the codebase:

**TTA.dev is a 3-layer meta-framework:**

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Development Primitives (Python Packages)       │
│ - tta-dev-primitives (workflow orchestration)          │
│ - tta-observability-integration (OpenTelemetry)        │
│ - universal-agent-context (multi-agent coordination)   │
└─────────────────────────────────────────────────────────┘
                          ↓ Used by
┌─────────────────────────────────────────────────────────┐
│ Layer 2: Hypertool Integration (Persona System)        │
│ - .hypertool/personas/ (6 specialized AI personas)     │
│ - .hypertool/workflows/ (multi-agent orchestration)    │
│ - MCP server configuration (tool orchestration)        │
└─────────────────────────────────────────────────────────┘
                          ↓ Powers
┌─────────────────────────────────────────────────────────┐
│ Layer 3: AI-Native Application Development             │
│ - VS Code + AI coding agents (Cline, Copilot, Cursor)  │
│ - Multi-persona full-stack development                 │
│ - Building apps like TTA (theinterneti/TTA game)       │
└─────────────────────────────────────────────────────────┘
```

### What TTA.dev Is NOT (Currently)

❌ **Not a web application** - No HTTP server to start
❌ **Not a microservice** - No REST/GraphQL API
❌ **Not a CLI tool (yet)** - Could be! See "CLI Tool Opportunity" below
❌ **Not a standalone daemon (yet)** - Doesn't run in background (see "Daemon vs Config Files" below)

### What TTA.dev IS

✅ **Development infrastructure** - Like Rails, React, or Django
✅ **Multi-agent orchestration framework** - Coordinates AI personas
✅ **Workflow primitive library** - Building blocks for AI agents
✅ **VS Code extension ecosystem** - Integrates with coding assistants

---

## 💡 CLI Tool Opportunity - Like Serena/Aider/Cursor

### What Other Agentic Coders Do

**Existing CLI tools in the ecosystem:**

1. **Cline CLI** - `npm install -g @cline/cli`
   ```bash
   cline "implement feature X"
   cline config set api-provider openrouter
   ```

2. **Universal Agent Context CLI** - Already in TTA.dev!
   ```bash
   python .augment/context/cli.py new session-id
   python .augment/context/cli.py add session-id "message"
   ```

3. **Augment/Serena Pattern** - Chat modes + personas
   - CLI-driven persona switching
   - Task automation via CLI
   - Configuration management

### TTA.dev CLI Opportunity

**YES! A `tta-dev` CLI could be excellent:**

```bash
# Installation
npm install -g @tta-dev/cli
# or
uvx tta-dev

# Usage
tta-dev init                          # Setup project
tta-dev persona backend               # Switch persona
tta-dev persona ls                    # List personas
tta-dev workflow run my-workflow      # Execute workflow
tta-dev status                        # Check system status
tta-dev metrics                       # Show observability metrics
tta-dev cache clear                   # Clear primitive caches
tta-dev generate primitive MyPrim     # Scaffold new primitive
```

**Benefits:**
- ✅ Ergonomic interface (like `git`, `docker`)
- ✅ Scriptable automation
- ✅ CI/CD integration
- ✅ Persona switching without sed commands
- ✅ Matches user mental model of "starting" TTA.dev

**Implementation Path:**
1. **Phase 1:** Wrap existing persona switching (`.hypertool/PERSONA_SWITCHING.md`)
2. **Phase 2:** Add workflow execution
3. **Phase 3:** Integrate with observability (metrics, status)

**Analogy:** Like how `docker` CLI wraps Docker daemon, `tta-dev` would wrap MCP server + primitives

---

## 🔧 Daemon vs Config Files - Integration Methods

### Current Approach: Config File Editing

**How it works now:**
```bash
# Edit MCP settings directly
sed -i 's/--persona", "[^"]*"/--persona", "tta-backend-engineer"/' ~/.config/mcp/mcp_settings.json

# Or use helper script
tta-persona backend
```

**Pros:**
- ✅ Simple, no additional processes
- ✅ Works with any MCP-compatible agent
- ✅ No daemon management overhead
- ✅ Portable (just JSON files)

**Cons:**
- ❌ Requires editor restart to apply changes
- ❌ Manual config file locations
- ❌ Less discoverable (users don't know commands exist)
- ❌ No real-time persona switching

### Alternative: Daemon-Based Architecture

**How it would work:**
```bash
# Start TTA.dev daemon (background service)
tta-dev daemon start

# Hot-reload persona switching (no restart)
tta-dev persona backend   # Updates daemon state

# Daemon serves MCP on behalf of agent
# Agent talks to daemon, daemon talks to primitives
```

**Architecture:**
```
┌─────────────────────────────────────┐
│ VS Code + AI Agent (Cline/Copilot)  │
└──────────────┬──────────────────────┘
               │ MCP Protocol
               ↓
┌─────────────────────────────────────┐
│ TTA.dev Daemon (Background Service) │ ← Runs as systemd/launchd service
│ - Persona management                │
│ - Workflow orchestration            │
│ - Real-time metrics                 │
│ - Cache management                  │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│ TTA.dev Primitives (Python)         │
│ - Sequential/Parallel/Router        │
│ - Cache/Retry/Fallback              │
│ - Observability integration         │
└─────────────────────────────────────┘
```

**Pros:**
- ✅ Hot-reload persona switching (no restart)
- ✅ Centralized state management
- ✅ Real-time metrics/status
- ✅ Better resource management (connection pooling)
- ✅ Advanced features: caching, rate limiting, coordination

**Cons:**
- ❌ Additional process to manage (start/stop/monitor)
- ❌ More complex installation
- ❌ Potential daemon failures
- ❌ OS-specific management (systemd, launchd, Windows Service)

### Recommendation: Hybrid Approach

**Start simple (Config Files), evolve to Daemon:**

**Phase 1: CLI + Config Files (Now - Q1 2026)**
```bash
# Install
npm install -g @tta-dev/cli

# CLI wraps config editing
tta-dev init
tta-dev persona backend   # Updates JSON, prompts to restart

# No daemon needed initially
```

**Phase 2: Optional Daemon (Q2 2026)**
```bash
# Install with daemon support
tta-dev daemon install
tta-dev daemon start

# Hot-reload persona switching
tta-dev persona backend   # No restart needed!

# Daemon provides advanced features
tta-dev metrics --live
tta-dev cache status
```

**Why Hybrid?**
- Start simple, validate demand
- Advanced users can opt into daemon
- Maintain backward compatibility
- Learn from user feedback

---

## 🎯 The Real "Application"

**Your actual application is:** The combination of:

1. **TTA.dev primitives** (installed via `uv add tta-dev-primitives`)
2. **Hypertool MCP server** (running in background, coordinating personas)
3. **AI coding agents** (Cline/Copilot/Cursor in VS Code)
4. **Observability stack** (Grafana Alloy → Grafana Cloud)

**When you "start" TTA.dev, you're really:**
1. Loading the persona system (MCP server)
2. Activating AI coding agents with persona context
3. Building your target application (like TTA game)

---

## 🚀 Deployment Options Analysis

### Option 1: MCP Server (Current Approach)

**What It Is:**
- Hypertool MCP server runs locally
- Exposes persona system to AI agents
- Coordinates tool access per persona

**Pros:**
- ✅ Already implemented (`.hypertool/` directory)
- ✅ Works with multiple AI agents (Cline, Copilot, Cursor)
- ✅ Local execution (fast, no network latency)
- ✅ Natural fit for developer tooling

**Cons:**
- ❌ Requires Node.js runtime
- ❌ Each developer must configure MCP
- ❌ No centralized management
- ❌ Harder to share across team

**Is it "cool" to package as MCP?**
✅ **YES!** This is exactly what MCP is designed for:
- Tool orchestration for AI agents
- Context-aware development workflows
- Persona-based tool access

**Analogy:** Like ESLint or Prettier - developer tools that enhance the coding experience.

### Option 2: VS Code Extension

**What It Would Be:**
- Native VS Code extension
- Integrates directly with Copilot/coding agents
- Provides UI for persona switching
- Manages observability dashboard

**Pros:**
- ✅ Native VS Code integration
- ✅ Better UX (UI for persona selection)
- ✅ Discoverable via VS Code Marketplace
- ✅ Automatic updates
- ✅ Can bundle MCP server internally

**Cons:**
- ❌ Major development effort (new codebase)
- ❌ Limited to VS Code (no JetBrains, etc.)
- ❌ Extension API complexity
- ❌ Publishing/maintenance overhead

**When This Makes Sense:**
- If you want TTA.dev to be **product-like**
- If you need **broad distribution**
- If you want **revenue** (marketplace)

### Option 3: Hybrid Approach (Recommended)

**Architecture:**
```
┌─────────────────────────────────────────────────────┐
│ VS Code Extension (Lightweight UI Layer)           │
│ - Persona switcher UI                              │
│ - Observability dashboard widget                   │
│ - Quick actions panel                              │
└──────────────────┬──────────────────────────────────┘
                   ↓ Communicates with
┌─────────────────────────────────────────────────────┐
│ Hypertool MCP Server (Core Logic)                  │
│ - Persona system                                    │
│ - Tool orchestration                               │
│ - Multi-agent coordination                         │
└──────────────────┬──────────────────────────────────┘
                   ↓ Uses
┌─────────────────────────────────────────────────────┐
│ TTA.dev Primitives (Python Packages)               │
│ - Workflow orchestration                           │
│ - Observability integration                        │
│ - Agent context management                         │
└─────────────────────────────────────────────────────┘
```

**Pros:**
- ✅ Best of both worlds
- ✅ Great UX with minimal extension code
- ✅ MCP server handles complexity
- ✅ Works with any MCP-compatible agent

**Cons:**
- ❌ Two components to maintain
- ❌ More complex setup initially

---

## 💡 Recommendation: CLI First, Then Daemon

### Phase 1: Polish CLI + MCP Server (Now - Q1 2026)

**Focus:** Make TTA.dev easy to use with a great CLI experience

1. **Create `@tta-dev/cli` npm package:**
   ```bash
   npm install -g @tta-dev/cli
   tta-dev --version
   ```

2. **CLI Commands (wrapping config files):**
   ```bash
   # Setup
   tta-dev init                       # Setup project + MCP config
   
   # Persona management (better UX than sed)
   tta-dev persona ls                 # List available personas
   tta-dev persona use backend        # Switch persona (edits config, prompts restart)
   tta-dev persona current            # Show current persona
   
   # Status/Diagnostics
   tta-dev status                     # Check MCP server, personas, primitives
   tta-dev doctor                     # Diagnose configuration issues
   
   # Observability
   tta-dev metrics                    # Show latest metrics snapshot
   tta-dev logs                       # Show recent primitive logs
   
   # Development
   tta-dev generate primitive MyPrim  # Scaffold new primitive
   tta-dev test workflow.py           # Run workflow with test data
   ```

3. **Improve observability:**
   - Persona-switching metrics in Grafana Cloud
   - CLI shows real-time cache hit rates
   - Cost analysis per persona

4. **Documentation:**
   - Getting started with CLI
   - Persona usage patterns
   - Migration from manual config editing

**Benefits:**
- ✅ Immediate value, low development cost
- ✅ Better UX than sed commands
- ✅ Validates concept with users
- ✅ No daemon complexity yet

### Phase 2: Optional Daemon for Advanced Features (Q2 2026)

**Once CLI is proven, add optional daemon:**

1. **Daemon Installation:**
   ```bash
   # Install daemon (systemd/launchd/Windows Service)
   tta-dev daemon install
   
   # Start daemon
   tta-dev daemon start
   
   # Check daemon status
   tta-dev daemon status
   ```

2. **Daemon Features:**
   - **Hot-reload personas** - No VS Code restart needed
   - **Connection pooling** - Reuse LLM connections
   - **Advanced caching** - Shared cache across projects
   - **Real-time metrics** - Live observability dashboard
   - **Workflow coordination** - Multi-project orchestration

3. **CLI with Daemon:**
   ```bash
   # Same commands, but faster and no restart
   tta-dev persona use backend   # Hot-reload! No restart prompt
   
   # New daemon-enabled commands
   tta-dev metrics --live         # Live metrics stream
   tta-dev cache clear --global   # Clear daemon cache
   tta-dev workflows active       # Show running workflows
   ```

**Benefits:**
- ✅ Advanced features for power users
- ✅ Backward compatible (daemon optional)
- ✅ Incremental adoption
- ✅ Learn from Phase 1 feedback

### Phase 3: VS Code Extension as UI Layer (Q3 2026)

**Beautiful UI on top of CLI/Daemon foundation:**

**Once MCP server is proven, add extension for:**

1. **Persona Switcher UI:**
   - Dropdown in status bar
   - Quick switch shortcuts
   - Visual indicators

2. **Observability Dashboard:**
   - Real-time metrics widget
   - Cost tracking
   - Agent activity timeline

3. **Quick Actions:**
   - Run test workflows
   - Generate primitives
   - View logs

**Extension serves as:** Beautiful UI layer on top of solid MCP foundation.

---

## 🎯 What "Starting TTA.dev" Actually Means

### For Developers Using TTA.dev

**Setup (once):**
```bash
# 1. Install primitives
uv add tta-dev-primitives
uv add tta-observability-integration

# 2. Install Hypertool MCP
npm install -g @tta-dev/hypertool-mcp

# 3. Configure in VS Code
tta-dev init
```

**Daily usage:**
```bash
# 1. Open VS Code with AI agent (Cline/Copilot)
code .

# 2. Hypertool MCP server starts automatically
# (configured in ~/.config/mcp/mcp_settings.json)

# 3. Switch persona based on task
tta-dev persona backend   # Working on API
tta-dev persona frontend  # Building UI
tta-dev persona devops    # Deploying

# 4. AI agent has access to persona-specific tools
# (automatically orchestrated by MCP server)
```

**What's "running":**
- ✅ Hypertool MCP server (Node.js process)
- ✅ Grafana Alloy (systemd service)
- ✅ VS Code + AI agent (Cline/Copilot/Cursor)

### For You Building TTA.dev

**Development:**
```bash
# Work on primitives
cd packages/tta-dev-primitives
uv run pytest -v

# Work on Hypertool MCP
cd .hypertool
npm run dev

# Test with real AI agent
code . # Open VS Code with Cline
```

**Testing observability:**
```bash
# This is what we just did!
uv run python test_real_workflow.py
curl http://localhost:9464/metrics | grep tta_
```

---

## 🚨 Critical Insight: TTA.dev Is Infrastructure, Not An App

**Similar to:**
- **Ruby on Rails** - Framework for building web apps
- **React** - Library for building UIs
- **OpenTelemetry** - Framework for observability

**Not similar to:**
- **WordPress** - Complete application you install
- **Slack** - Service you sign up for
- **GitHub** - Platform you use

**Your value proposition:**
> "TTA.dev makes multi-agent AI development actually work by providing structured persona-based orchestration and production-ready workflow primitives."

---

## 📋 Recommended Next Steps

### Immediate (This Session)

1. **Update Architecture Docs:**
   - ✅ Document CLI tool opportunity (like Serena/Aider)
   - ✅ Explain daemon vs config file tradeoffs
   - ✅ Recommend hybrid approach (CLI → Daemon → Extension)

2. **Branch Strategy:**
   ```bash
   # For CLI development
   git checkout -b feature/tta-dev-cli
   ```

3. **Define CLI Scope (Phase 1):**
   - Persona switching (better than sed)
   - Init/setup automation
   - Status/diagnostics
   - Config validation

### Short-term (Next 2 Weeks)

1. **Build `@tta-dev/cli` Package:**
   ```
   packages/tta-dev-cli/
   ├── package.json
   ├── bin/
   │   └── tta-dev           # CLI entry point
   ├── src/
   │   ├── commands/
   │   │   ├── init.ts       # tta-dev init
   │   │   ├── persona.ts    # tta-dev persona
   │   │   ├── status.ts     # tta-dev status
   │   │   └── doctor.ts     # tta-dev doctor
   │   └── cli.ts            # Main CLI logic
   └── README.md
   ```

2. **CLI Commands (Priority Order):**
   - `tta-dev init` - Setup project
   - `tta-dev persona` - Persona management
   - `tta-dev status` - System health
   - `tta-dev doctor` - Diagnostics

3. **Test with Real Usage:**
   - Use CLI to switch personas
   - Validate against Cline, Copilot, Cursor
   - Gather feedback from local testing

### Medium-term (Q1 2026)

1. **Polish CLI:**
   - Add observability commands (`metrics`, `logs`)
   - Improve error messages
   - Add bash/zsh completions
   - Publish to npm

2. **Documentation:**
   - CLI command reference
   - Migration guide (sed → CLI)
   - Video demos

3. **Daemon Planning:**
   - Evaluate user demand
   - Design daemon architecture
   - Prototype hot-reload

---

## 🎓 Key Takeaways

### TTA.dev Is NOT an Application to "Start"

It's **infrastructure** that powers AI-native development:
- Primitives = Building blocks
- Hypertool MCP = Orchestration layer
- Personas = Specialized agent configurations

### The "Application" Is What You Build With It

**Example:** TTA (the game)
- Uses `tta-dev-primitives` for workflow orchestration
- Uses persona system for multi-agent development
- Uses observability for monitoring

**Another Example:** Your next SaaS product
- Backend persona handles API development
- Frontend persona builds UI
- DevOps persona manages deployment
- Observability persona sets up monitoring

### Deployment = Developer Experience

**Success means:**
- ✅ Easy to install (`npm install -g @tta-dev/hypertool-mcp`)
- ✅ Simple to configure (`tta-dev init`)
- ✅ Natural to use (persona switching)
- ✅ Powerful when needed (primitives, observability)

---

## 💭 Final Thoughts

**CLI Tool:** ✅ Absolutely! Great idea inspired by Serena/Aider/Cline patterns
- Start with simple persona switching and init commands
- Better UX than sed commands
- Natural mental model for users ("starting" TTA.dev)
- Foundation for future daemon

**Daemon vs Config Files:** Hybrid approach wins
- **Phase 1:** CLI wrapping config files (simple, fast to ship)
- **Phase 2:** Optional daemon for advanced features (hot-reload, caching)
- **Phase 3:** Extension as UI layer (beautiful, optional)
- Learn from user feedback at each phase

**MCP Server:** ✅ Still the right foundation
- CLI calls MCP server underneath
- Works with any MCP-compatible agent
- Daemon would be MCP server on steroids

**VS Code Extension:** Later, after CLI validation
- Adds nice UI layer
- Not required for core functionality
- Build once CLI/daemon patterns are proven

**Your Focus Should Be:**
1. **Now:** Build `tta-dev` CLI (like `git`, `docker`)
2. **Q1 2026:** Polish CLI, gather feedback
3. **Q2 2026:** Add optional daemon for power users
4. **Q3 2026:** Consider extension as UI enhancement

**The "application" is the ecosystem you're creating** - and a great CLI is the perfect entry point!

---

## 🎯 MILESTONE: VS Code Intelligent Setup CLI

### Goal Definition

**Build a working `tta-dev` CLI that intelligently sets up VS Code for contributing to TTA.dev projects.**

**What "intelligently" means:**
1. **Detects context:**
   - Is this a new project or existing?
   - Which AI agent is installed? (Cline/Copilot/Cursor)
   - What's the project structure? (TTA.dev monorepo vs new project)

2. **Configures automatically:**
   - VS Code workspace settings (`.vscode/settings.json`)
   - AI agent configuration (Cline `.cline/`, Copilot toolsets, etc.)
   - MCP server settings (`~/.config/mcp/mcp_settings.json`)
   - Hypertool personas (`.hypertool/personas/`)

3. **Sets up TTA.dev assets:**
   - Installs primitives (`tta-dev-primitives`, `tta-observability-integration`)
   - Configures observability (Grafana Alloy)
   - Links to integrations (Context7, AI Toolkit, Pylance, etc.)
   - Sets appropriate persona for task

### User Experience Target

```bash
# Scenario 1: Contributing to TTA.dev itself
cd ~/repos/TTA.dev
tta-dev setup --mode=contributor

# Output:
# 🔍 Detected: TTA.dev monorepo
# 🤖 Detected: Cline + GitHub Copilot installed
# 📦 Installing: tta-dev-primitives, tta-observability-integration
# ⚙️  Configuring: VS Code workspace, Cline settings, MCP servers
# 👤 Setting persona: tta-backend-engineer (default for contributors)
# ✅ Setup complete! Restart VS Code to activate.

# Scenario 2: New project using TTA.dev
mkdir ~/projects/my-agent-app
cd ~/projects/my-agent-app
tta-dev setup --mode=new-project

# Output:
# 🔍 Detected: New project directory
# 🤖 Detected: GitHub Copilot installed
# 📦 Creating: package structure, pyproject.toml
# 📦 Installing: tta-dev-primitives
# ⚙️  Configuring: VS Code workspace, Copilot toolsets
# 👤 Setting persona: tta-backend-engineer
# ✅ Setup complete! Start building with TTA.dev primitives.

# Scenario 3: Switch persona mid-session
tta-dev persona frontend

# Output:
# 👤 Switching: tta-backend-engineer → tta-frontend-engineer
# ⚙️  Updating: MCP configuration, tool access
# 🔄 Action required: Restart AI agent to apply changes
```

### Minimum Viable CLI Features

**Priority 1 - Core Setup (Ship First):**

1. **`tta-dev setup`** - Intelligent project setup
   - Detect project type (TTA.dev repo vs new project)
   - Detect installed AI agents
   - Configure VS Code workspace
   - Configure AI agent settings
   - Install TTA.dev packages
   - Set default persona

2. **`tta-dev persona [name]`** - Persona switching
   - List available personas (`tta-dev persona ls`)
   - Show current persona (`tta-dev persona current`)
   - Switch persona (`tta-dev persona backend`)
   - Update MCP config automatically

3. **`tta-dev status`** - System health check
   - Check VS Code configuration
   - Check AI agent installation
   - Check MCP server status
   - Check installed packages
   - Check observability setup

**Priority 2 - Nice to Have (Later):**

4. **`tta-dev doctor`** - Diagnose issues
5. **`tta-dev metrics`** - Show observability data
6. **`tta-dev generate`** - Scaffold primitives

---

## 🚀 Implementation Plan - Milestone Focused

### Phase 1: Foundation (Week 1 - This Week)

**Branch:** `feature/tta-dev-cli-mvp`

**Day 1-2: Project Structure**
```bash
git checkout -b feature/tta-dev-cli-mvp

# Create CLI package
mkdir -p packages/tta-dev-cli
cd packages/tta-dev-cli

# Initialize TypeScript/Node.js project
npm init -y
npm install --save-dev typescript @types/node
npm install commander chalk fs-extra inquirer

# Structure
packages/tta-dev-cli/
├── package.json
├── tsconfig.json
├── bin/
│   └── tta-dev.ts           # CLI entry point
├── src/
│   ├── commands/
│   │   ├── setup.ts         # tta-dev setup
│   │   ├── persona.ts       # tta-dev persona
│   │   └── status.ts        # tta-dev status
│   ├── detectors/
│   │   ├── project.ts       # Detect project type
│   │   ├── agents.ts        # Detect AI agents
│   │   └── vscode.ts        # Detect VS Code config
│   ├── configurators/
│   │   ├── workspace.ts     # Configure .vscode/
│   │   ├── cline.ts         # Configure .cline/
│   │   ├── copilot.ts       # Configure Copilot
│   │   └── mcp.ts           # Configure MCP settings
│   └── utils/
│       ├── logger.ts        # Pretty output
│       └── files.ts         # File operations
└── README.md
```

**Day 3-4: Core Detection Logic**
```typescript
// src/detectors/project.ts
export async function detectProjectType(): Promise<'tta-dev-repo' | 'new-project' | 'existing-project'> {
  // Check for TTA.dev markers
  if (await fileExists('packages/tta-dev-primitives')) {
    return 'tta-dev-repo';
  }
  
  // Check for existing project
  if (await fileExists('pyproject.toml') || await fileExists('package.json')) {
    return 'existing-project';
  }
  
  return 'new-project';
}

// src/detectors/agents.ts
export async function detectInstalledAgents(): Promise<{
  cline: boolean;
  copilot: boolean;
  cursor: boolean;
}> {
  // Check VS Code extensions
  const extensions = await getVSCodeExtensions();
  
  return {
    cline: extensions.includes('saoudrizwan.claude-dev'),
    copilot: extensions.includes('github.copilot'),
    cursor: false // Cursor is separate editor
  };
}
```

**Day 5-7: Setup Command Implementation**
```typescript
// src/commands/setup.ts
export async function setupCommand(options: SetupOptions) {
  const logger = new Logger();
  
  // 1. Detect environment
  logger.info('🔍 Detecting environment...');
  const projectType = await detectProjectType();
  const agents = await detectInstalledAgents();
  
  logger.success(`Detected: ${projectType}`);
  logger.success(`AI Agents: ${Object.entries(agents).filter(([k,v]) => v).map(([k]) => k).join(', ')}`);
  
  // 2. Install packages
  logger.info('📦 Installing TTA.dev packages...');
  await installPackages(projectType);
  
  // 3. Configure VS Code
  logger.info('⚙️  Configuring VS Code...');
  await configureVSCode(projectType, agents);
  
  // 4. Configure AI agents
  if (agents.cline) {
    logger.info('🤖 Configuring Cline...');
    await configureCline();
  }
  
  if (agents.copilot) {
    logger.info('🤖 Configuring Copilot...');
    await configureCopilot();
  }
  
  // 5. Setup MCP
  logger.info('🔌 Configuring MCP servers...');
  await configureMCP();
  
  // 6. Set default persona
  logger.info('👤 Setting default persona...');
  await setPersona('tta-backend-engineer');
  
  logger.success('✅ Setup complete! Restart VS Code to activate.');
}
```

### Phase 2: Testing & Polish (Week 2)

**Test Scenarios:**
1. Fresh clone of TTA.dev → Run `tta-dev setup`
2. New empty directory → Run `tta-dev setup --mode=new-project`
3. Existing Python project → Run `tta-dev setup`
4. Persona switching → Run `tta-dev persona frontend`

**Documentation:**
- CLI command reference
- Setup guide for contributors
- Troubleshooting guide

### Phase 3: Ship It (Week 2 End)

**Deliverables:**
1. ✅ Working CLI package
2. ✅ Tested on TTA.dev repo
3. ✅ Tested on new projects
4. ✅ Documentation complete
5. ✅ Published to npm (optional, can use `npx` from repo)

---

## 📋 Success Criteria

**The milestone is COMPLETE when:**

1. ✅ A contributor can clone TTA.dev and run `tta-dev setup` to get fully configured
2. ✅ A developer can create a new project and run `tta-dev setup` to use TTA.dev
3. ✅ Persona switching works via `tta-dev persona [name]`
4. ✅ Status check shows all components (`tta-dev status`)
5. ✅ Documentation explains all features
6. ✅ Works with at least Cline or Copilot (both is better)

**Measurement:**
- Time from clone to productive: <5 minutes (vs current ~30 minutes manual setup)
- Commands needed: 2 (`git clone`, `tta-dev setup`) vs current ~15 manual steps
- Errors during setup: 0 (vs current ~3-5 common issues)

---

## 🎯 Next Immediate Actions

### Right Now (Next 30 Minutes)

1. **Create branch:**
   ```bash
   git checkout -b feature/tta-dev-cli-mvp
   ```

2. **Create CLI package structure:**
   ```bash
   mkdir -p packages/tta-dev-cli/{src/commands,src/detectors,src/configurators,src/utils,bin}
   cd packages/tta-dev-cli
   ```

3. **Initialize package:**
   ```bash
   npm init -y
   npm install commander chalk fs-extra inquirer
   npm install --save-dev typescript @types/node @types/inquirer
   ```

4. **Create basic CLI entry point:**
   ```typescript
   // bin/tta-dev.ts
   #!/usr/bin/env node
   import { Command } from 'commander';
   
   const program = new Command();
   
   program
     .name('tta-dev')
     .description('TTA.dev intelligent setup and management CLI')
     .version('0.1.0');
   
   program
     .command('setup')
     .description('Intelligently setup VS Code for TTA.dev')
     .action(() => {
       console.log('🚀 Setting up TTA.dev...');
     });
   
   program.parse();
   ```

### This Week

**Focus:** Ship the MVP CLI with core setup functionality

- Day 1-2: Project structure + detection logic
- Day 3-4: Setup command implementation
- Day 5-6: Persona switching + status
- Day 7: Testing + documentation

---

**Ready to start?** Should we create the branch and package structure now?

