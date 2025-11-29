# Next Session Quick Start - tta-dev CLI Implementation

**Date:** November 15, 2025  
**Milestone:** tta-dev CLI MVP - Intelligent VS Code Setup  
**Target Date:** November 29, 2025 (2 weeks)  
**Current Branch:** `feature/phase5-apm-integration` ✅ Complete  
**Next Branch:** `feature/tta-dev-cli-mvp` (to be created)

---

## ⚡ Quick Actions (First 30 Minutes)

### 1. Create GitHub Milestone

```bash
# Via GitHub CLI (if available)
gh milestone create "tta-dev CLI MVP - Intelligent VS Code Setup" \
  --description "Working CLI for intelligent VS Code setup automation. Target: 30min → <5min setup time." \
  --due-date "2025-11-29"

# Or via GitHub UI:
# https://github.com/theinterneti/TTA.dev/milestones/new
```

### 2. Create GitHub Issues

**Template source:** `docs/planning/TTA_DEV_CLI_GITHUB_ISSUES.md`

**7 Issues to Create:**

1. **Initialize tta-dev CLI Package Structure** (1 day)
2. **Implement Environment Detection Logic** (1 day)
3. **Implement Configuration Logic** (2 days)
4. **Implement `tta-dev setup` Command** (1 day)
5. **Implement `tta-dev persona` and `tta-dev status` Commands** (1 day)
6. **Add Testing and Documentation** (2 days)
7. **Polish and Ship v0.1.0** (1 day)

**Quick Create:**
```bash
# Copy issue templates from docs/planning/TTA_DEV_CLI_GITHUB_ISSUES.md
# Create each via GitHub UI or CLI
```

### 3. Create Feature Branch

```bash
cd /home/thein/repos/TTA.dev
git checkout main
git pull origin main
git checkout -b feature/tta-dev-cli-mvp
git push -u origin feature/tta-dev-cli-mvp
```

### 4. Create Draft PR

```bash
gh pr create --draft \
  --title "[WIP] tta-dev CLI MVP - Intelligent VS Code Setup" \
  --body "
## Milestone
tta-dev CLI MVP - Intelligent VS Code Setup (Due: Nov 29, 2025)

## Goal
Build a working CLI for intelligent VS Code setup automation.
- Current: 30 minutes, 3-5 errors
- Target: <5 minutes, 0 errors

## Implementation Plan
See docs/planning/TTA_DEV_CLI_IMPLEMENTATION_PLAN.md

## Architecture
See docs/architecture/APPLICATION_DEPLOYMENT_ARCHITECTURE.md

## Issues
See milestone for 7 implementation issues

## Checklist
- [ ] #1: Package structure
- [ ] #2: Detection logic
- [ ] #3: Configuration logic
- [ ] #4: Setup command
- [ ] #5: Persona + status commands
- [ ] #6: Testing + docs
- [ ] #7: Polish + ship v0.1.0
"
```

---

## 📋 Implementation Checklist (Week 1)

### Day 1-2: Package Structure (Issue #1)

```bash
# Create package directory
mkdir -p packages/tta-dev-cli/{src/{commands,lib,utils},bin,tests}
cd packages/tta-dev-cli

# Initialize npm package
npm init -y

# Install dependencies
npm install commander chalk ora inquirer fs-extra yaml glob execa

# Install dev dependencies
npm install --save-dev typescript @types/node @types/inquirer jest @types/jest

# Create TypeScript config
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
EOF

# Create entry point
cat > bin/tta-dev.ts << 'EOF'
#!/usr/bin/env node
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
  .action(() => {
    console.log(chalk.blue('🚀 TTA.dev CLI v0.1.0'));
    console.log('Setup command coming soon...');
  });

program.parse();
EOF

# Update package.json
npm pkg set "bin.tta-dev"="./bin/tta-dev.ts"
npm pkg set "scripts.build"="tsc"
npm pkg set "scripts.dev"="ts-node bin/tta-dev.ts"

# Test
npx ts-node bin/tta-dev.ts --version
npx ts-node bin/tta-dev.ts --help
```

**Commit:**
```bash
git add packages/tta-dev-cli/
git commit -m "feat: initialize tta-dev CLI package structure

- TypeScript + Node.js setup
- Dependencies installed (commander, chalk, ora, inquirer)
- Basic CLI entry point with --version and --help
- Package structure created

Related: Issue #1"
git push
```

### Day 3-4: Detection Logic (Issue #2)

**Files to create:**
- `src/lib/detector.ts`
- `src/lib/detectors/project.ts`
- `src/lib/detectors/agents.ts`
- `src/lib/detectors/vscode.ts`
- `src/lib/detectors/packages.ts`
- `src/lib/detectors/mcp.ts`
- `src/lib/types.ts`
- `tests/detector.test.ts`

**See:** `docs/planning/TTA_DEV_CLI_GITHUB_ISSUES.md` Issue #2 for code examples

### Day 5-7: Configuration Logic (Issue #3)

**Files to create:**
- `src/lib/configurator.ts`
- `src/lib/configurators/workspace.ts`
- `src/lib/configurators/cline.ts`
- `src/lib/configurators/copilot.ts`
- `src/lib/configurators/mcp.ts`
- `src/lib/configurators/packages.ts`
- `src/lib/templates/` (JSON templates)
- `tests/configurator.test.ts`

**See:** `docs/planning/TTA_DEV_CLI_GITHUB_ISSUES.md` Issue #3 for code examples

---

## 📋 Implementation Checklist (Week 2)

### Day 8: Setup Command (Issue #4)
### Day 9-10: Persona + Status Commands (Issue #5)
### Day 11-12: Testing + Docs (Issue #6)
### Day 13-14: Polish + Ship (Issue #7)

---

## 📚 Reference Documents

### Implementation Plan
- **File:** `docs/planning/TTA_DEV_CLI_IMPLEMENTATION_PLAN.md`
- **Content:** Complete 2-week timeline, code examples, test strategy
- **Use:** Daily reference for implementation details

### GitHub Issues
- **File:** `docs/planning/TTA_DEV_CLI_GITHUB_ISSUES.md`
- **Content:** 7 issues with acceptance criteria and code examples
- **Use:** Copy-paste issue templates into GitHub

### Architecture Analysis
- **File:** `docs/architecture/APPLICATION_DEPLOYMENT_ARCHITECTURE.md`
- **Content:** TTA.dev as meta-framework, CLI opportunity, daemon vs config
- **Use:** Understand "why" behind CLI design

### Session Summary
- **File:** `docs/sessions/SESSION_2025_11_15_CLI_MILESTONE.md`
- **Content:** Complete session documentation, decisions, insights
- **Use:** Context for future sessions

---

## 🎯 Success Criteria

### Must Have (MVP)

- [ ] `tta-dev setup` works on fresh TTA.dev clone
- [ ] `tta-dev setup` works on new empty project
- [ ] `tta-dev persona <name>` switches persona
- [ ] `tta-dev status` shows system health
- [ ] Setup time: <5 minutes (vs 30 minutes manual)
- [ ] Setup errors: 0 (vs 3-5 common issues)
- [ ] Documentation complete (README, commands, troubleshooting)
- [ ] Tests passing (unit, integration, E2E)

### Nice to Have (Future)

- [ ] `tta-dev init` for new projects
- [ ] `tta-dev doctor` for diagnostics
- [ ] `tta-dev metrics` for observability
- [ ] `tta-dev generate` for scaffolding
- [ ] Published to npm
- [ ] Bash/zsh completions

---

## 🔗 Quick Links

### GitHub
- **Repository:** https://github.com/theinterneti/TTA.dev
- **Milestones:** https://github.com/theinterneti/TTA.dev/milestones
- **Issues:** https://github.com/theinterneti/TTA.dev/issues
- **Pull Requests:** https://github.com/theinterneti/TTA.dev/pulls

### Documentation
- **AGENTS.md:** Agent instructions hub
- **GETTING_STARTED.md:** Setup guide (to be improved by CLI!)
- **PRIMITIVES_CATALOG.md:** Primitive reference
- **MCP_SERVERS.md:** MCP integration guide

### Current Work
- **Branch:** `feature/tta-dev-cli-mvp`
- **Milestone:** tta-dev CLI MVP
- **Target:** November 29, 2025
- **Estimate:** 2 weeks, 10 working days

---

## 💡 Key Insights to Remember

1. **TTA.dev is infrastructure** (like Rails) not application (like WordPress)
2. **"Starting TTA.dev"** means enabling developer tools, not launching a service
3. **CLI matches patterns** from Serena, Aider, Cline CLI
4. **Config files work** for MVP, daemon is optional enhancement
5. **Intelligent detection** enables great UX (detect → configure → validate)
6. **Setup automation** is high-value feature (6x faster, 0 errors)

---

## 🚨 Common Pitfalls to Avoid

1. **Over-engineering:** Start with config file editing, don't build daemon yet
2. **Incomplete detection:** Test all project types (tta-dev-repo, new-project, existing)
3. **Poor error messages:** User should know exactly what went wrong and how to fix
4. **Missing dry-run:** Always support `--dry-run` for testing
5. **Forgetting restart:** Remind user to restart VS Code after config changes
6. **No validation:** Validate configuration before writing files
7. **Hardcoded paths:** Use environment variables and detect locations

---

## ✅ Pre-Implementation Checklist

Before writing code:

- [ ] GitHub milestone created
- [ ] 7 GitHub issues created
- [ ] Issues linked to milestone
- [ ] Draft PR created
- [ ] Branch `feature/tta-dev-cli-mvp` exists
- [ ] Implementation plan reviewed
- [ ] Architecture document reviewed
- [ ] Success criteria understood

---

## 📞 Need Help?

**Reference Documents:**
- Implementation plan: `docs/planning/TTA_DEV_CLI_IMPLEMENTATION_PLAN.md`
- Issue templates: `docs/planning/TTA_DEV_CLI_GITHUB_ISSUES.md`
- Architecture: `docs/architecture/APPLICATION_DEPLOYMENT_ARCHITECTURE.md`
- Session summary: `docs/sessions/SESSION_2025_11_15_CLI_MILESTONE.md`

**Logseq:**
- Today's journal: `logseq/journals/2025_11_15.md`
- CLI documentation: `[[TTA.dev/CLI Tool]]`
- Milestones: `[[TTA.dev/Milestones]]`

---

**Ready to start?** Begin with GitHub milestone and issues, then initialize package structure!

**Remember:** This is a 2-week sprint. Ship the MVP, gather feedback, iterate. Don't let perfect be the enemy of good.

🚀 Let's build an amazing CLI tool!
