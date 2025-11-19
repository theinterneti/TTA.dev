# GitHub Issues for tta-dev CLI MVP Milestone

**Milestone:** tta-dev CLI MVP - Intelligent VS Code Setup  
**Target Date:** November 29, 2025 (2 weeks)  
**Branch:** `feature/tta-dev-cli-mvp`

---

## Issue #1: Initialize tta-dev CLI Package Structure

**Type:** Setup  
**Priority:** P0 (Blocker)  
**Estimate:** 1 day  
**Dependencies:** None

### Description

Set up the TypeScript/Node.js package structure for the `tta-dev` CLI tool with all necessary dependencies and build configuration.

### Acceptance Criteria

- [ ] Package created at `packages/tta-dev-cli/`
- [ ] TypeScript configuration complete (`tsconfig.json`)
- [ ] Dependencies installed (commander, chalk, ora, inquirer, fs-extra)
- [ ] Dev dependencies installed (typescript, @types/node, jest)
- [ ] Package.json includes bin entry point
- [ ] Basic CLI entry point responds to `--version` and `--help`
- [ ] Build script produces executable

### Package Structure

```
packages/tta-dev-cli/
├── package.json
├── tsconfig.json
├── bin/
│   └── tta-dev.ts           # CLI entry point
├── src/
│   ├── commands/            # Command implementations
│   ├── lib/                 # Core logic
│   └── utils/               # Helpers
└── tests/                   # Test files
```

### Dependencies

```json
{
  "dependencies": {
    "commander": "^11.1.0",
    "chalk": "^5.3.0",
    "ora": "^7.0.1",
    "inquirer": "^9.2.12",
    "fs-extra": "^11.2.0",
    "yaml": "^2.3.4",
    "glob": "^10.3.10",
    "execa": "^8.0.1"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/node": "^20.10.0",
    "@types/inquirer": "^9.0.7",
    "jest": "^29.7.0",
    "@types/jest": "^29.5.11"
  }
}
```

### Code Example

```typescript
#!/usr/bin/env node
// bin/tta-dev.ts
import { Command } from 'commander';
import chalk from 'chalk';

const program = new Command();

program
  .name('tta-dev')
  .description('TTA.dev intelligent setup and management CLI')
  .version('0.1.0');

program
  .command('setup')
  .description('Intelligently setup VS Code for TTA.dev')
  .action(async () => {
    console.log(chalk.blue('🚀 TTA.dev CLI v0.1.0'));
  });

program.parse();
```

### Definition of Done

- Package builds without errors
- `npx ts-node bin/tta-dev.ts --version` works
- `npx ts-node bin/tta-dev.ts --help` shows commands
- README.md documents installation

---

## Issue #2: Implement Environment Detection Logic

**Type:** Feature  
**Priority:** P0 (Blocker)  
**Estimate:** 1 day  
**Dependencies:** Issue #1

### Description

Build detection logic to intelligently identify the project type, installed AI agents, VS Code configuration, and TTA.dev packages.

### Acceptance Criteria

- [ ] Detect project type (tta-dev-repo, new-project, existing-project)
- [ ] Detect installed AI agents (Cline, Copilot, Cursor)
- [ ] Detect VS Code workspace configuration
- [ ] Detect installed TTA.dev packages
- [ ] Detect MCP server configuration
- [ ] Unit tests for all detection functions
- [ ] Detection results logged clearly

### Implementation Files

```
src/lib/
├── detector.ts              # Main detection orchestrator
├── detectors/
│   ├── project.ts           # Project type detection
│   ├── agents.ts            # AI agent detection
│   ├── vscode.ts            # VS Code config detection
│   ├── packages.ts          # Package detection
│   └── mcp.ts               # MCP server detection
└── types.ts                 # Type definitions
```

### Code Example

```typescript
// src/lib/detector.ts
import { VSCodeExtension, getVSCodeExtensions } from './detectors/vscode';
import { fileExists, readJSON } from '../utils/files';

export type ProjectType = 'tta-dev-repo' | 'new-project' | 'existing-project';

export interface DetectionResult {
  projectType: ProjectType;
  agents: {
    cline: boolean;
    copilot: boolean;
    cursor: boolean;
  };
  vscode: {
    installed: boolean;
    workspaceFile: string | null;
    settingsFile: string | null;
  };
  packages: {
    'tta-dev-primitives': boolean;
    'tta-observability-integration': boolean;
    'universal-agent-context': boolean;
  };
  mcp: {
    configured: boolean;
    settingsPath: string | null;
    hypertoolInstalled: boolean;
  };
}

export async function detectEnvironment(): Promise<DetectionResult> {
  // Project type detection
  let projectType: ProjectType = 'new-project';
  
  if (await fileExists('packages/tta-dev-primitives')) {
    projectType = 'tta-dev-repo';
  } else if (await fileExists('pyproject.toml') || await fileExists('package.json')) {
    projectType = 'existing-project';
  }
  
  // AI agent detection
  const extensions = await getVSCodeExtensions();
  const agents = {
    cline: extensions.some(ext => ext.id === 'saoudrizwan.claude-dev'),
    copilot: extensions.some(ext => ext.id === 'github.copilot'),
    cursor: false // Cursor is separate editor
  };
  
  // VS Code detection
  const vscode = {
    installed: extensions.length > 0,
    workspaceFile: await findWorkspaceFile(),
    settingsFile: await findSettingsFile()
  };
  
  // Package detection
  const packages = {
    'tta-dev-primitives': await isPackageInstalled('tta-dev-primitives'),
    'tta-observability-integration': await isPackageInstalled('tta-observability-integration'),
    'universal-agent-context': await isPackageInstalled('universal-agent-context')
  };
  
  // MCP detection
  const mcpSettingsPath = `${process.env.HOME}/.config/mcp/mcp_settings.json`;
  const mcp = {
    configured: await fileExists(mcpSettingsPath),
    settingsPath: await fileExists(mcpSettingsPath) ? mcpSettingsPath : null,
    hypertoolInstalled: await fileExists('.hypertool')
  };
  
  return { projectType, agents, vscode, packages, mcp };
}
```

### Test Cases

```typescript
// tests/detector.test.ts
describe('detectEnvironment', () => {
  it('detects TTA.dev repo correctly', async () => {
    const result = await detectEnvironment();
    expect(result.projectType).toBe('tta-dev-repo');
  });
  
  it('detects installed AI agents', async () => {
    const result = await detectEnvironment();
    expect(result.agents.cline || result.agents.copilot).toBe(true);
  });
});
```

### Definition of Done

- All detection functions work correctly
- Tests cover happy path and edge cases
- Detection results are accurate
- Logging shows what was detected

---

## Issue #3: Implement Configuration Logic

**Type:** Feature  
**Priority:** P0 (Blocker)  
**Estimate:** 2 days  
**Dependencies:** Issue #2

### Description

Build configuration logic to automatically set up VS Code workspace, AI agent settings, MCP servers, and TTA.dev integrations based on detected environment.

### Acceptance Criteria

- [ ] Configure VS Code workspace settings
- [ ] Configure Cline settings (.cline/)
- [ ] Configure Copilot toolsets (.vscode/copilot-toolsets.jsonc)
- [ ] Configure MCP server settings (~/.config/mcp/mcp_settings.json)
- [ ] Set default persona (tta-backend-engineer)
- [ ] Install TTA.dev packages if missing
- [ ] Unit tests for all configuration functions
- [ ] Dry-run mode for testing without modifications

### Implementation Files

```
src/lib/
├── configurator.ts          # Main configuration orchestrator
├── configurators/
│   ├── workspace.ts         # VS Code workspace config
│   ├── cline.ts             # Cline configuration
│   ├── copilot.ts           # Copilot toolsets config
│   ├── mcp.ts               # MCP server config
│   └── packages.ts          # Package installation
└── templates/               # Configuration templates
    ├── workspace.json
    ├── cline-config.json
    └── mcp-settings.json
```

### Code Example

```typescript
// src/lib/configurator.ts
import { DetectionResult } from './detector';
import { configureWorkspace } from './configurators/workspace';
import { configureCline } from './configurators/cline';
import { configureCopilot } from './configurators/copilot';
import { configureMCP } from './configurators/mcp';
import { installPackages } from './configurators/packages';

export interface ConfigurationOptions {
  dryRun?: boolean;
  verbose?: boolean;
  persona?: string;
}

export async function configureEnvironment(
  detection: DetectionResult,
  options: ConfigurationOptions = {}
): Promise<void> {
  const { dryRun = false, verbose = false, persona = 'tta-backend-engineer' } = options;
  
  // 1. Configure VS Code workspace
  if (detection.projectType !== 'new-project') {
    await configureWorkspace(detection, { dryRun, verbose });
  }
  
  // 2. Configure Cline if installed
  if (detection.agents.cline) {
    await configureCline(detection, { dryRun, verbose });
  }
  
  // 3. Configure Copilot if installed
  if (detection.agents.copilot) {
    await configureCopilot(detection, { dryRun, verbose });
  }
  
  // 4. Configure MCP servers
  await configureMCP(detection, { dryRun, verbose, persona });
  
  // 5. Install missing packages
  const missingPackages = Object.entries(detection.packages)
    .filter(([pkg, installed]) => !installed)
    .map(([pkg]) => pkg);
  
  if (missingPackages.length > 0) {
    await installPackages(missingPackages, { dryRun, verbose });
  }
}
```

### Configuration Templates

```json
// src/lib/templates/workspace.json
{
  "folders": [
    { "path": "." }
  ],
  "settings": {
    "python.analysis.typeCheckingMode": "basic",
    "files.exclude": {
      "**/__pycache__": true,
      "**/.pytest_cache": true
    },
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true
    }
  },
  "extensions": {
    "recommendations": [
      "ms-python.python",
      "charliermarsh.ruff",
      "github.copilot"
    ]
  }
}
```

### Definition of Done

- All configuration functions work correctly
- Dry-run mode doesn't modify files
- Templates are validated and complete
- Tests cover configuration logic
- Error handling for file operations

---

## Issue #4: Implement `tta-dev setup` Command

**Type:** Feature  
**Priority:** P0 (Blocker)  
**Estimate:** 1 day  
**Dependencies:** Issues #2, #3

### Description

Build the main `tta-dev setup` command that orchestrates detection and configuration with a great user experience.

### Acceptance Criteria

- [ ] Command accepts `--mode` option (contributor, new-project)
- [ ] Command accepts `--dry-run` option for testing
- [ ] Interactive prompts when needed
- [ ] Progress indicators (spinner, steps)
- [ ] Clear success/error messages
- [ ] Summary of what was configured
- [ ] Instruction to restart VS Code

### Implementation

```typescript
// src/commands/setup.ts
import { Command } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import inquirer from 'inquirer';
import { detectEnvironment } from '../lib/detector';
import { configureEnvironment } from '../lib/configurator';

export function setupCommand(program: Command) {
  program
    .command('setup')
    .description('Intelligently setup VS Code for TTA.dev')
    .option('--mode <mode>', 'Setup mode: contributor | new-project | auto', 'auto')
    .option('--dry-run', 'Show what would be done without making changes', false)
    .option('--persona <persona>', 'Set initial persona', 'tta-backend-engineer')
    .action(async (options) => {
      console.log(chalk.blue.bold('\n🚀 TTA.dev Intelligent Setup\n'));
      
      // Step 1: Detection
      const spinner = ora('Detecting environment...').start();
      const detection = await detectEnvironment();
      spinner.succeed('Environment detected');
      
      console.log(chalk.gray('\nDetected:'));
      console.log(`  Project type: ${chalk.cyan(detection.projectType)}`);
      console.log(`  AI Agents: ${chalk.cyan(
        Object.entries(detection.agents)
          .filter(([k, v]) => v)
          .map(([k]) => k)
          .join(', ') || 'none'
      )}`);
      console.log(`  VS Code: ${detection.vscode.installed ? chalk.green('✓') : chalk.red('✗')}`);
      console.log(`  MCP: ${detection.mcp.configured ? chalk.green('✓') : chalk.red('✗')}\n`);
      
      // Step 2: Confirm
      if (!options.dryRun) {
        const { confirm } = await inquirer.prompt([{
          type: 'confirm',
          name: 'confirm',
          message: 'Proceed with configuration?',
          default: true
        }]);
        
        if (!confirm) {
          console.log(chalk.yellow('Setup cancelled'));
          return;
        }
      }
      
      // Step 3: Configure
      const configSpinner = ora('Configuring environment...').start();
      
      try {
        await configureEnvironment(detection, {
          dryRun: options.dryRun,
          persona: options.persona,
          verbose: true
        });
        
        configSpinner.succeed('Configuration complete');
        
        // Step 4: Summary
        console.log(chalk.green.bold('\n✅ Setup Complete!\n'));
        console.log(chalk.gray('Configured:'));
        console.log('  • VS Code workspace settings');
        if (detection.agents.cline) console.log('  • Cline configuration');
        if (detection.agents.copilot) console.log('  • Copilot toolsets');
        console.log('  • MCP server settings');
        console.log(`  • Persona: ${chalk.cyan(options.persona)}`);
        
        console.log(chalk.yellow('\n⚠️  Action Required: Restart VS Code to activate changes\n'));
        
        if (options.dryRun) {
          console.log(chalk.blue('ℹ️  This was a dry run. No files were modified.\n'));
        }
        
      } catch (error) {
        configSpinner.fail('Configuration failed');
        console.error(chalk.red(`\nError: ${error.message}\n`));
        process.exit(1);
      }
    });
}
```

### Definition of Done

- Command runs without errors
- Progress indicators work correctly
- User can cancel setup
- Dry-run mode works
- Summary is accurate and helpful

---

## Issue #5: Implement `tta-dev persona` and `tta-dev status` Commands

**Type:** Feature  
**Priority:** P1 (High)  
**Estimate:** 1 day  
**Dependencies:** Issues #2, #3

### Description

Build persona switching and system health check commands.

### Acceptance Criteria

**Persona Command:**
- [ ] `tta-dev persona ls` lists available personas
- [ ] `tta-dev persona current` shows active persona
- [ ] `tta-dev persona <name>` switches persona
- [ ] Updates MCP configuration automatically
- [ ] Shows restart instruction

**Status Command:**
- [ ] `tta-dev status` shows system health
- [ ] Checks VS Code configuration
- [ ] Checks AI agent installation
- [ ] Checks MCP server status
- [ ] Checks installed packages
- [ ] Color-coded output (green/yellow/red)

### Implementation

```typescript
// src/commands/persona.ts
import { Command } from 'commander';
import chalk from 'chalk';
import { getCurrentPersona, setPersona, listPersonas } from '../lib/persona';

export function personaCommand(program: Command) {
  const persona = program
    .command('persona')
    .description('Manage AI personas');
  
  persona
    .command('ls')
    .description('List available personas')
    .action(async () => {
      const personas = await listPersonas();
      const current = await getCurrentPersona();
      
      console.log(chalk.blue.bold('\n📋 Available Personas:\n'));
      personas.forEach(p => {
        const isCurrent = p.name === current;
        const marker = isCurrent ? chalk.green('→') : ' ';
        console.log(`${marker} ${chalk.cyan(p.name)}: ${p.description}`);
      });
      console.log();
    });
  
  persona
    .command('current')
    .description('Show current persona')
    .action(async () => {
      const current = await getCurrentPersona();
      console.log(chalk.cyan(current || 'none'));
    });
  
  persona
    .command('use <name>')
    .description('Switch to persona')
    .action(async (name: string) => {
      console.log(chalk.blue(`\n👤 Switching to ${chalk.cyan(name)}...\n`));
      
      await setPersona(name);
      
      console.log(chalk.green('✅ Persona switched successfully'));
      console.log(chalk.yellow('⚠️  Restart VS Code to apply changes\n'));
    });
}
```

```typescript
// src/commands/status.ts
import { Command } from 'commander';
import chalk from 'chalk';
import { detectEnvironment } from '../lib/detector';

export function statusCommand(program: Command) {
  program
    .command('status')
    .description('Check TTA.dev system health')
    .action(async () => {
      console.log(chalk.blue.bold('\n🏥 TTA.dev System Status\n'));
      
      const detection = await detectEnvironment();
      
      // VS Code
      const vscodeStatus = detection.vscode.installed ? chalk.green('✓') : chalk.red('✗');
      console.log(`${vscodeStatus} VS Code: ${detection.vscode.installed ? 'Installed' : 'Not found'}`);
      
      // AI Agents
      const agents = Object.entries(detection.agents).filter(([k, v]) => v).map(([k]) => k);
      const agentStatus = agents.length > 0 ? chalk.green('✓') : chalk.yellow('⚠');
      console.log(`${agentStatus} AI Agents: ${agents.join(', ') || 'None installed'}`);
      
      // MCP
      const mcpStatus = detection.mcp.configured ? chalk.green('✓') : chalk.red('✗');
      console.log(`${mcpStatus} MCP: ${detection.mcp.configured ? 'Configured' : 'Not configured'}`);
      
      // Packages
      const installedPackages = Object.entries(detection.packages)
        .filter(([k, v]) => v)
        .map(([k]) => k);
      const packageStatus = installedPackages.length > 0 ? chalk.green('✓') : chalk.yellow('⚠');
      console.log(`${packageStatus} Packages: ${installedPackages.length}/3 installed`);
      
      console.log();
    });
}
```

### Definition of Done

- Both commands work correctly
- Output is clear and helpful
- Persona switching updates MCP config
- Status check is accurate

---

## Issue #6: Add Testing and Documentation

**Type:** Testing & Docs  
**Priority:** P1 (High)  
**Estimate:** 2 days  
**Dependencies:** Issues #1-5

### Description

Comprehensive testing and documentation for the CLI tool.

### Acceptance Criteria

**Testing:**
- [ ] Unit tests for all core functions (>80% coverage)
- [ ] Integration tests for commands
- [ ] E2E tests for full workflows
- [ ] Test fixtures for different scenarios
- [ ] CI/CD pipeline configured

**Documentation:**
- [ ] README.md with installation and usage
- [ ] Command reference documentation
- [ ] Troubleshooting guide
- [ ] Contributing guide
- [ ] Example workflows

### Test Structure

```
tests/
├── unit/
│   ├── detector.test.ts
│   ├── configurator.test.ts
│   └── persona.test.ts
├── integration/
│   ├── setup.test.ts
│   ├── persona.test.ts
│   └── status.test.ts
├── e2e/
│   └── full-workflow.test.ts
└── fixtures/
    ├── tta-dev-repo/
    ├── new-project/
    └── existing-project/
```

### Documentation Outline

```markdown
# tta-dev CLI

> Intelligent setup and management for TTA.dev projects

## Installation

\`\`\`bash
npm install -g @tta-dev/cli
# or
npx @tta-dev/cli setup
\`\`\`

## Quick Start

\`\`\`bash
# Clone TTA.dev and setup
git clone https://github.com/theinterneti/TTA.dev
cd TTA.dev
tta-dev setup

# Start new project with TTA.dev
mkdir my-agent-app
cd my-agent-app
tta-dev setup --mode=new-project
\`\`\`

## Commands

### setup
### persona
### status

## Troubleshooting
## Contributing
```

### Definition of Done

- Test coverage >80%
- All tests passing
- Documentation complete and accurate
- Examples work correctly

---

## Issue #7: Polish and Ship v0.1.0

**Type:** Release  
**Priority:** P1 (High)  
**Estimate:** 1 day  
**Dependencies:** Issues #1-6

### Description

Final polish, bug fixes, and release preparation for v0.1.0.

### Acceptance Criteria

- [ ] All tests passing
- [ ] No critical bugs
- [ ] Documentation reviewed
- [ ] CHANGELOG.md created
- [ ] Version bumped to 0.1.0
- [ ] Package published (or instructions for local use)
- [ ] Release notes written
- [ ] Demo video/GIF created

### Release Checklist

- [ ] Run full test suite
- [ ] Test on fresh TTA.dev clone
- [ ] Test on new project
- [ ] Verify all commands work
- [ ] Check error messages are helpful
- [ ] Review documentation
- [ ] Create release branch
- [ ] Tag release
- [ ] Publish to npm (optional)
- [ ] Update main README.md
- [ ] Announce release

### CHANGELOG.md

```markdown
# Changelog

## [0.1.0] - 2025-11-29

### Added
- `tta-dev setup` command for intelligent VS Code setup
- `tta-dev persona` commands for persona management
- `tta-dev status` command for system health check
- Automatic detection of project type and AI agents
- Configuration of VS Code, Cline, Copilot, and MCP
- Comprehensive test suite
- Complete documentation

### Success Metrics
- Setup time: 30 minutes → <5 minutes (6x improvement)
- Setup errors: 3-5 common issues → 0 errors
- User satisfaction: High (based on dogfooding)
```

### Definition of Done

- Package is ready for production use
- All documentation is accurate
- Release is tagged and published
- Success metrics validated

---

## Milestone Summary

**Timeline:** 2 weeks (November 15-29, 2025)

**Week 1:**
- Day 1-2: Issue #1 (Package structure)
- Day 3-4: Issue #2 (Detection logic)
- Day 5-7: Issue #3 (Configuration logic)

**Week 2:**
- Day 8: Issue #4 (Setup command)
- Day 9-10: Issue #5 (Persona + status commands)
- Day 11-12: Issue #6 (Testing + docs)
- Day 13-14: Issue #7 (Polish + ship)

**Success Criteria:**
- ✅ Working CLI package
- ✅ Intelligent setup automation
- ✅ Persona switching
- ✅ System health check
- ✅ Complete documentation
- ✅ 6x faster setup time

**Branch:** `feature/tta-dev-cli-mvp`

**Related Documents:**
- Implementation plan: `docs/planning/TTA_DEV_CLI_IMPLEMENTATION_PLAN.md`
- Architecture: `docs/architecture/APPLICATION_DEPLOYMENT_ARCHITECTURE.md`
