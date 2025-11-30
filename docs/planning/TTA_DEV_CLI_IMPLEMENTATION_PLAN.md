# TTA.dev CLI Implementation Plan - MVP

**Milestone:** Working CLI for intelligent VS Code setup
**Timeline:** 2 weeks
**Branch:** `feature/tta-dev-cli-mvp`

---

## 🎯 Success Criteria

**The CLI is successful when:**

1. ✅ `tta-dev setup` fully configures VS Code for TTA.dev contribution
2. ✅ `tta-dev setup --mode=new-project` sets up new project with TTA.dev
3. ✅ `tta-dev persona [name]` switches personas without manual config editing
4. ✅ `tta-dev status` shows health of all components
5. ✅ Works with Cline AND Copilot (detect which is installed)
6. ✅ Setup time: <5 minutes (vs current ~30 minutes)

---

## 📦 Package Structure

```
packages/tta-dev-cli/
├── package.json              # npm package config
├── tsconfig.json             # TypeScript config
├── bin/
│   └── tta-dev.ts           # CLI entry point (executable)
├── src/
│   ├── commands/
│   │   ├── setup.ts         # tta-dev setup
│   │   ├── persona.ts       # tta-dev persona
│   │   └── status.ts        # tta-dev status
│   ├── detectors/
│   │   ├── project.ts       # Detect project type
│   │   ├── agents.ts        # Detect AI agents (Cline/Copilot)
│   │   ├── vscode.ts        # Detect VS Code config
│   │   └── packages.ts      # Detect installed Python packages
│   ├── configurators/
│   │   ├── workspace.ts     # Configure .vscode/settings.json
│   │   ├── cline.ts         # Configure .cline/
│   │   ├── copilot.ts       # Configure .vscode/copilot-toolsets.jsonc
│   │   ├── mcp.ts           # Configure ~/.config/mcp/mcp_settings.json
│   │   └── packages.ts      # Install Python packages via uv
│   ├── templates/
│   │   ├── vscode/          # VS Code config templates
│   │   ├── cline/           # Cline config templates
│   │   └── mcp/             # MCP config templates
│   └── utils/
│       ├── logger.ts        # Pretty console output
│       ├── files.ts         # File operations (read/write JSON)
│       ├── shell.ts         # Execute shell commands
│       └── validators.ts    # Validate configurations
├── tests/
│   ├── detectors.test.ts
│   ├── configurators.test.ts
│   └── integration.test.ts
└── README.md                # CLI documentation
```

---

## 🔧 Implementation Phases

### Phase 1: Foundation (Days 1-2)

**Goal:** Project setup and basic CLI structure

**Tasks:**
1. Create `packages/tta-dev-cli/` directory
2. Initialize npm package with TypeScript
3. Install dependencies:
   - `commander` - CLI framework
   - `chalk` - Colored output
   - `fs-extra` - File operations
   - `inquirer` - Interactive prompts
   - `yaml` - YAML parsing
   - `jsonc-parser` - JSONC (comments) parsing
4. Setup TypeScript config
5. Create basic CLI entry point

**Deliverable:**
```bash
npx tsx packages/tta-dev-cli/bin/tta-dev.ts --version
# Output: 0.1.0
```

---

### Phase 2: Detection Logic (Days 3-4)

**Goal:** Intelligent environment detection

#### 2.1 Project Type Detection

**File:** `src/detectors/project.ts`

```typescript
export type ProjectType = 'tta-dev-repo' | 'new-project' | 'existing-project';

export async function detectProjectType(cwd: string): Promise<ProjectType> {
  // Check for TTA.dev repo markers
  const ttaMarkers = [
    'packages/tta-dev-primitives',
    'packages/tta-observability-integration',
    '.hypertool/personas'
  ];
  
  for (const marker of ttaMarkers) {
    if (await pathExists(join(cwd, marker))) {
      return 'tta-dev-repo';
    }
  }
  
  // Check for existing Python project
  if (await pathExists(join(cwd, 'pyproject.toml')) ||
      await pathExists(join(cwd, 'setup.py'))) {
    return 'existing-project';
  }
  
  // New project
  return 'new-project';
}
```

#### 2.2 AI Agent Detection

**File:** `src/detectors/agents.ts`

```typescript
export interface DetectedAgents {
  cline: boolean;
  copilot: boolean;
  cursor: boolean;
}

export async function detectInstalledAgents(): Promise<DetectedAgents> {
  // Get VS Code extensions
  const extensions = await getVSCodeExtensions();
  
  return {
    cline: extensions.includes('saoudrizwan.claude-dev'),
    copilot: extensions.includes('github.copilot') || 
             extensions.includes('github.copilot-chat'),
    cursor: false // Cursor is separate editor
  };
}

async function getVSCodeExtensions(): Promise<string[]> {
  try {
    // Run: code --list-extensions
    const { stdout } = await execAsync('code --list-extensions');
    return stdout.split('\n').filter(Boolean);
  } catch {
    return [];
  }
}
```

#### 2.3 Package Detection

**File:** `src/detectors/packages.ts`

```typescript
export async function detectInstalledPackages(cwd: string): Promise<string[]> {
  try {
    // Run: uv pip list
    const { stdout } = await execAsync('uv pip list', { cwd });
    const lines = stdout.split('\n').slice(2); // Skip header
    
    return lines
      .filter(Boolean)
      .map(line => line.split(/\s+/)[0]);
  } catch {
    return [];
  }
}

export function needsPackage(installed: string[], packageName: string): boolean {
  return !installed.includes(packageName);
}
```

**Deliverable:**
```bash
tta-dev detect
# Output:
# 🔍 Environment Detection
# 
# Project Type: tta-dev-repo
# AI Agents:
#   ✅ Cline (saoudrizwan.claude-dev)
#   ✅ GitHub Copilot (github.copilot)
# 
# Python Packages:
#   ✅ tta-dev-primitives (0.1.0)
#   ❌ tta-observability-integration (not installed)
```

---

### Phase 3: Configuration Logic (Days 5-6)

**Goal:** Automated configuration of all components

#### 3.1 VS Code Workspace Configuration

**File:** `src/configurators/workspace.ts`

```typescript
export async function configureVSCodeWorkspace(
  cwd: string,
  projectType: ProjectType
) {
  const vscodeDir = join(cwd, '.vscode');
  await ensureDir(vscodeDir);
  
  // Settings.json
  const settings = await loadOrCreateJSON(join(vscodeDir, 'settings.json'));
  
  // Add TTA.dev specific settings
  Object.assign(settings, {
    'python.defaultInterpreterPath': '${workspaceFolder}/.venv/bin/python',
    'python.terminal.activateEnvironment': true,
    'python.analysis.typeCheckingMode': 'strict',
    '[python]': {
      'editor.defaultFormatter': 'charliermarsh.ruff',
      'editor.formatOnSave': true,
      'editor.codeActionsOnSave': {
        'source.organizeImports': 'explicit'
      }
    },
    'ruff.lint.args': ['--config', 'pyproject.toml'],
    'files.exclude': {
      '**/__pycache__': true,
      '**/.pytest_cache': true,
      '**/.ruff_cache': true
    }
  });
  
  await writeJSON(join(vscodeDir, 'settings.json'), settings, { spaces: 2 });
}
```

#### 3.2 Cline Configuration

**File:** `src/configurators/cline.ts`

```typescript
export async function configureCline(cwd: string, projectType: ProjectType) {
  const clineDir = join(cwd, '.cline');
  await ensureDir(clineDir);
  
  // Copy instructions from template
  const instructionsTemplate = projectType === 'tta-dev-repo'
    ? 'templates/cline/tta-dev-contributor-instructions.md'
    : 'templates/cline/tta-dev-user-instructions.md';
  
  await copyFile(
    join(__dirname, '..', instructionsTemplate),
    join(clineDir, 'instructions.md')
  );
  
  // Create MCP config link
  const mcpConfig = {
    mcpServers: {
      context7: { enabled: true },
      'ai-toolkit': { enabled: true },
      pylance: { enabled: true },
      grafana: { enabled: projectType === 'tta-dev-repo' }
    }
  };
  
  await writeJSON(join(clineDir, 'mcp_servers.json'), mcpConfig, { spaces: 2 });
}
```

#### 3.3 MCP Server Configuration

**File:** `src/configurators/mcp.ts`

```typescript
export async function configureMCP(persona: string = 'tta-backend-engineer') {
  const mcpConfigPath = join(os.homedir(), '.config', 'mcp', 'mcp_settings.json');
  await ensureDir(dirname(mcpConfigPath));
  
  const config = await loadOrCreateJSON(mcpConfigPath);
  
  // Ensure hypertool MCP server entry
  if (!config.mcpServers) {
    config.mcpServers = {};
  }
  
  config.mcpServers.hypertool = {
    command: 'node',
    args: [
      join(process.cwd(), '.hypertool', 'server.js'),
      '--persona',
      persona
    ],
    env: {},
    disabled: false
  };
  
  await writeJSON(mcpConfigPath, config, { spaces: 2 });
}
```

**Deliverable:**
```bash
tta-dev setup --dry-run
# Output:
# 🔧 Configuration Plan
# 
# VS Code Workspace:
#   ✅ .vscode/settings.json (Python, Ruff, exclusions)
#   ✅ .vscode/tasks.json (test, lint, format)
# 
# Cline:
#   ✅ .cline/instructions.md (TTA.dev contributor guide)
#   ✅ .cline/mcp_servers.json (Context7, AI Toolkit, Pylance, Grafana)
# 
# MCP Server:
#   ✅ ~/.config/mcp/mcp_settings.json (Hypertool with tta-backend-engineer persona)
# 
# Python Packages:
#   📦 tta-dev-primitives (to install)
#   📦 tta-observability-integration (to install)
# 
# Run without --dry-run to apply changes.
```

---

### Phase 4: Setup Command (Day 7)

**Goal:** Complete setup command implementation

**File:** `src/commands/setup.ts`

```typescript
import { Command } from 'commander';
import chalk from 'chalk';
import inquirer from 'inquirer';

export function createSetupCommand(): Command {
  return new Command('setup')
    .description('Intelligently setup VS Code for TTA.dev')
    .option('--mode <mode>', 'Setup mode: contributor, new-project, existing-project')
    .option('--persona <persona>', 'Default persona to use', 'tta-backend-engineer')
    .option('--dry-run', 'Show what would be done without making changes')
    .option('-y, --yes', 'Skip confirmations')
    .action(async (options) => {
      const logger = new Logger();
      const cwd = process.cwd();
      
      // 1. Detect environment
      logger.step('Detecting environment');
      const projectType = await detectProjectType(cwd);
      const agents = await detectInstalledAgents();
      const packages = await detectInstalledPackages(cwd);
      
      logger.info(`Project type: ${chalk.cyan(projectType)}`);
      logger.info(`AI agents: ${formatAgents(agents)}`);
      logger.info(`Installed packages: ${packages.length}`);
      
      // 2. Determine mode
      let mode = options.mode;
      if (!mode) {
        mode = projectType === 'tta-dev-repo' ? 'contributor' : 'new-project';
      }
      
      // 3. Confirm with user (unless --yes)
      if (!options.yes && !options.dryRun) {
        const { confirmed } = await inquirer.prompt([{
          type: 'confirm',
          name: 'confirmed',
          message: `Setup as ${chalk.cyan(mode)}?`,
          default: true
        }]);
        
        if (!confirmed) {
          logger.warn('Setup cancelled');
          return;
        }
      }
      
      // 4. Install packages
      if (!options.dryRun) {
        logger.step('Installing Python packages');
        await installRequiredPackages(cwd, mode, packages);
      } else {
        logger.info('[DRY RUN] Would install packages');
      }
      
      // 5. Configure VS Code
      if (!options.dryRun) {
        logger.step('Configuring VS Code workspace');
        await configureVSCodeWorkspace(cwd, projectType);
      } else {
        logger.info('[DRY RUN] Would configure VS Code');
      }
      
      // 6. Configure AI agents
      if (agents.cline) {
        if (!options.dryRun) {
          logger.step('Configuring Cline');
          await configureCline(cwd, projectType);
        } else {
          logger.info('[DRY RUN] Would configure Cline');
        }
      }
      
      if (agents.copilot) {
        if (!options.dryRun) {
          logger.step('Configuring Copilot');
          await configureCopilot(cwd, projectType);
        } else {
          logger.info('[DRY RUN] Would configure Copilot');
        }
      }
      
      // 7. Setup MCP
      if (!options.dryRun) {
        logger.step('Configuring MCP servers');
        await configureMCP(options.persona);
      } else {
        logger.info('[DRY RUN] Would configure MCP');
      }
      
      // 8. Success!
      logger.success('Setup complete!');
      logger.info('');
      logger.info('Next steps:');
      logger.info('  1. Restart VS Code to apply changes');
      logger.info('  2. Open AI agent (Cline/Copilot)');
      logger.info(`  3. Confirm persona: ${chalk.cyan(options.persona)}`);
      logger.info('  4. Start building! 🚀');
    });
}
```

---

### Phase 5: Persona & Status Commands (Day 8-9)

#### Persona Command

**File:** `src/commands/persona.ts`

```typescript
export function createPersonaCommand(): Command {
  return new Command('persona')
    .description('Manage AI agent personas')
    .argument('[name]', 'Persona to switch to')
    .option('-l, --list', 'List available personas')
    .option('-c, --current', 'Show current persona')
    .action(async (name, options) => {
      const logger = new Logger();
      
      // List personas
      if (options.list) {
        const personas = await listPersonas();
        logger.info('Available personas:');
        personas.forEach(p => {
          logger.info(`  • ${chalk.cyan(p.name)} - ${p.description}`);
        });
        return;
      }
      
      // Show current
      if (options.current) {
        const current = await getCurrentPersona();
        logger.info(`Current persona: ${chalk.cyan(current)}`);
        return;
      }
      
      // Switch persona
      if (!name) {
        logger.error('Persona name required. Use --list to see available personas.');
        return;
      }
      
      logger.step(`Switching to ${chalk.cyan(name)}`);
      await setPersona(name);
      
      logger.success(`Switched to ${chalk.cyan(name)}`);
      logger.warn('⚠️  Restart your AI agent to apply changes');
    });
}
```

#### Status Command

**File:** `src/commands/status.ts`

```typescript
export function createStatusCommand(): Command {
  return new Command('status')
    .description('Check TTA.dev setup status')
    .option('--json', 'Output as JSON')
    .action(async (options) => {
      const logger = new Logger();
      const cwd = process.cwd();
      
      // Gather status
      const status = {
        project: await detectProjectType(cwd),
        agents: await detectInstalledAgents(),
        packages: await detectInstalledPackages(cwd),
        vscode: await checkVSCodeConfig(cwd),
        mcp: await checkMCPConfig(),
        persona: await getCurrentPersona()
      };
      
      if (options.json) {
        console.log(JSON.stringify(status, null, 2));
        return;
      }
      
      // Pretty output
      logger.info('📊 TTA.dev Status\n');
      
      logger.info(`Project Type: ${chalk.cyan(status.project)}`);
      logger.info(`Current Persona: ${chalk.cyan(status.persona)}\n`);
      
      logger.info('AI Agents:');
      logger.info(`  ${formatStatus(status.agents.cline)} Cline`);
      logger.info(`  ${formatStatus(status.agents.copilot)} GitHub Copilot\n`);
      
      logger.info('Python Packages:');
      const requiredPackages = ['tta-dev-primitives', 'tta-observability-integration'];
      requiredPackages.forEach(pkg => {
        const installed = status.packages.includes(pkg);
        logger.info(`  ${formatStatus(installed)} ${pkg}`);
      });
      
      logger.info('\nConfiguration:');
      logger.info(`  ${formatStatus(status.vscode)} VS Code workspace`);
      logger.info(`  ${formatStatus(status.mcp)} MCP servers`);
    });
}

function formatStatus(ok: boolean): string {
  return ok ? chalk.green('✅') : chalk.red('❌');
}
```

---

### Phase 6: Testing & Documentation (Days 10-11)

**Test Scenarios:**

1. **Fresh TTA.dev clone:**
   ```bash
   git clone https://github.com/theinterneti/TTA.dev.git
   cd TTA.dev
   tta-dev setup
   # Should configure everything for contribution
   ```

2. **New project:**
   ```bash
   mkdir my-agent-app
   cd my-agent-app
   tta-dev setup --mode=new-project
   # Should create project structure + install TTA.dev
   ```

3. **Persona switching:**
   ```bash
   tta-dev persona frontend
   tta-dev status  # Should show frontend persona
   ```

**Documentation:**
- CLI command reference (`README.md`)
- Setup guide for contributors (`docs/CLI_SETUP_GUIDE.md`)
- Troubleshooting (`docs/CLI_TROUBLESHOOTING.md`)

---

### Phase 7: Ship It (Days 12-14)

**Pre-ship checklist:**
- [ ] All commands work on fresh TTA.dev clone
- [ ] All commands work on new project
- [ ] Works with Cline
- [ ] Works with Copilot
- [ ] Documentation complete
- [ ] Tests passing
- [ ] No known bugs

**Shipping:**
1. Merge to main
2. Tag release: `v0.1.0-cli-mvp`
3. Optional: Publish to npm
4. Update main README with CLI instructions

---

## 🧪 Testing Strategy

### Unit Tests

```typescript
// tests/detectors.test.ts
describe('detectProjectType', () => {
  it('should detect TTA.dev repo', async () => {
    const type = await detectProjectType('/path/to/TTA.dev');
    expect(type).toBe('tta-dev-repo');
  });
  
  it('should detect new project', async () => {
    const type = await detectProjectType('/tmp/empty');
    expect(type).toBe('new-project');
  });
});
```

### Integration Tests

```bash
# Test script
#!/bin/bash
set -e

# Test 1: Fresh clone
cd /tmp
git clone https://github.com/theinterneti/TTA.dev.git test-tta-dev
cd test-tta-dev
npx tsx packages/tta-dev-cli/bin/tta-dev.ts setup --dry-run
echo "✅ Test 1 passed"

# Test 2: New project
mkdir /tmp/test-new-project
cd /tmp/test-new-project
npx tsx /path/to/TTA.dev/packages/tta-dev-cli/bin/tta-dev.ts setup --mode=new-project --dry-run
echo "✅ Test 2 passed"

# Test 3: Status
cd /tmp/test-tta-dev
npx tsx packages/tta-dev-cli/bin/tta-dev.ts status
echo "✅ Test 3 passed"
```

---

## 📊 Success Metrics

**Before CLI:**
- Setup time: ~30 minutes
- Manual steps: ~15
- Common errors: 3-5
- Success rate: ~60%

**After CLI:**
- Setup time: <5 minutes
- Manual steps: 2 (`git clone`, `tta-dev setup`)
- Common errors: 0
- Success rate: >95%

**Improvement:**
- ⏱️ **6x faster** setup
- ✅ **7x fewer** manual steps
- 🐛 **Zero errors** during setup
- 📈 **35% higher** success rate

---

## 🚀 Ready to Start?

**Next command:**
```bash
git checkout -b feature/tta-dev-cli-mvp
mkdir -p packages/tta-dev-cli/{src/commands,src/detectors,src/configurators,src/templates,src/utils,bin,tests}
cd packages/tta-dev-cli
npm init -y
```

Let's ship this! 🎉
