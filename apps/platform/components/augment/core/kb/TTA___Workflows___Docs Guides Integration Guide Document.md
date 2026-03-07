---
title: Integration Guide - Universal Agent Context System
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/guides/INTEGRATION_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Integration Guide - Universal Agent Context System]]

**Step-by-step guide for integrating the Universal Agent Context System into your project**

---

## Overview

This guide walks you through integrating the Universal Agent Context System into your project. Choose the approach that best fits your needs:

1. **Cross-Platform Integration** - Works with Claude, Gemini, Copilot, Augment
2. **Augment CLI Integration** - Advanced features for Augment CLI users
3. **Comprehensive Integration** - Both approaches for maximum flexibility

---

## Prerequisites

- Git installed
- Your project initialized as a git repository
- Basic understanding of AI-native development
- (Optional) Python 3.8+ for Augment CLI features

---

## Integration Path 1: Cross-Platform (Recommended)

### Step 1: Copy Files

```bash
# From the export package directory
cp -r .github/ /path/to/your/project/
cp AGENTS.md /path/to/your/project/
```

### Step 2: Verify Installation

```bash
cd /path/to/your/project
ls -la .github/
ls -la AGENTS.md
```

You should see:
```
.github/
├── instructions/
├── chatmodes/
└── copilot-instructions.md
AGENTS.md
```

### Step 3: Configure for Your Project

Edit instruction files to match your project's needs:

```bash
# Example: Customize Python quality standards
vim .github/instructions/python-quality-standards.instructions.md
```

Update the `applyTo` patterns to match your file structure:

```yaml
---
applyTo: "src/**/*.py"  # Adjust to your Python file locations
tags: ["python", "quality"]
description: "Python quality standards"
priority: 5
---
```

### Step 4: Test with Your AI Agent

**For Claude**:
- Open your project in Claude
- Claude automatically loads `.github/instructions/` based on file patterns
- AGENTS.md provides universal context

**For GitHub Copilot**:
- Open your project in VS Code
- Copilot reads `.github/copilot-instructions.md`
- Instructions are selectively loaded based on active files

**For Gemini**:
- Open your project with Gemini CLI
- Gemini loads AGENTS.md for context
- Instructions are pattern-matched to active files

**For Augment**:
- Open your project with Augment CLI
- Augment loads both `.github/` and AGENTS.md
- Full cross-platform compatibility

### Step 5: Customize Chat Modes (Optional)

Edit chat mode files to define role-based development modes:

```bash
vim .github/chatmodes/backend-dev.chatmode.md
```

Update the YAML frontmatter:

```yaml
---
mode: "backend-developer"
description: "Backend development role"
cognitive_focus: "Backend architecture and implementation"
security_level: "MEDIUM"
allowed_tools: ["editFiles", "runCommands", "codebase-retrieval"]
denied_tools: ["deleteFiles"]
approval_required: ["deployProduction"]
---
```

---

## Integration Path 2: Augment CLI-Specific

### Step 1: Copy Files

```bash
# From the export package directory
cp -r .augment/ /path/to/your/project/
cp apm.yml /path/to/your/project/
```

### Step 2: Verify Installation

```bash
cd /path/to/your/project
ls -la .augment/
ls -la apm.yml
```

You should see:
```
.augment/
├── instructions/
├── chatmodes/
├── workflows/
├── context/
├── memory/
└── rules/
apm.yml
```

### Step 3: Initialize Context Management

```bash
# Create a new context session
python .augment/context/cli.py new my-project

# Add context
python .augment/context/cli.py add my-project "Working on feature X" --importance 1.0

# View session
python .augment/context/cli.py show my-project
```

### Step 4: Configure Augster Identity (Optional)

The Augster identity system is automatically active. To customize:

```bash
# Edit core identity
vim .augment/instructions/augster-core-identity.instructions.md

# Edit maxims
vim .augment/instructions/augster-maxims.instructions.md

# Edit protocols
vim .augment/instructions/augster-protocols.instructions.md
```

### Step 5: Use Workflow Templates

```bash
# View available workflows
ls .augment/workflows/

# Use a workflow template
cat .augment/workflows/feature-implementation.prompt.md
```

---

## Integration Path 3: Comprehensive (Both)

### Step 1: Copy All Files

```bash
# From the export package directory
cp -r .github/ /path/to/your/project/
cp -r .augment/ /path/to/your/project/
cp AGENTS.md /path/to/your/project/
cp CLAUDE.md /path/to/your/project/
cp GEMINI.md /path/to/your/project/
cp apm.yml /path/to/your/project/
```

### Step 2: Choose Based on Context

**Use `.github/` when**:
- Working with multiple AI agents
- Need cross-platform compatibility
- Want standardized YAML frontmatter

**Use `.augment/` when**:
- Working with Augment CLI specifically
- Need advanced features (Augster, context management, memory)
- Want sophisticated agent personality

### Step 3: Configure Both

Follow steps from both Integration Path 1 and Integration Path 2.

---

## Agent-Specific Integration

### Claude Integration

1. Copy `.github/` and `AGENTS.md`
2. Copy `CLAUDE.md` for Claude-specific instructions
3. Claude automatically loads instructions based on file patterns
4. Test by opening your project in Claude

### Gemini Integration

1. Copy `.github/` and `AGENTS.md`
2. Copy `GEMINI.md` for Gemini-specific instructions
3. Gemini loads AGENTS.md for universal context
4. Test by opening your project with Gemini CLI

### GitHub Copilot Integration

1. Copy `.github/` directory
2. Copilot reads `.github/copilot-instructions.md`
3. Instructions are selectively loaded based on active files
4. Test by opening your project in VS Code

### Augment Integration

1. Copy both `.github/` and `.augment/`
2. Copy `AGENTS.md` and `apm.yml`
3. Augment loads both structures
4. Test by opening your project with Augment CLI

---

## Validation

After integration, validate your setup:

```bash
# Run validation script (if available)
python scripts/validate-export-package.py

# Or manually verify
ls -la .github/instructions/
ls -la .github/chatmodes/
ls -la .augment/  # If using Augment CLI
```

---

## Troubleshooting

### Issue: Instructions Not Loading

**Symptoms**: AI agent doesn't seem to use instructions

**Solutions**:
1. Verify files are in correct location (`.github/instructions/`)
2. Check YAML frontmatter is valid
3. Ensure `applyTo` patterns match your files
4. Restart your AI agent

### Issue: Chat Modes Not Working

**Symptoms**: Chat modes don't activate

**Solutions**:
1. Verify files are in correct location (`.github/chatmodes/`)
2. Check YAML frontmatter is valid
3. Ensure your AI agent supports chat modes
4. Check `mode` field matches expected format

### Issue: Context Management Fails

**Symptoms**: `.augment/context/cli.py` errors

**Solutions**:
1. Verify Python 3.8+ is installed
2. Check file permissions (`chmod +x .augment/context/cli.py`)
3. Install dependencies if needed
4. Check Python path

---

## Best Practices

### 1. Start Small

Begin with cross-platform integration (`.github/` + `AGENTS.md`), then add Augment CLI features if needed.

### 2. Customize Gradually

Don't modify all files at once. Start with one instruction file or chat mode, test, then expand.

### 3. Version Control

Commit your integration changes:

```bash
git add .github/ AGENTS.md
git commit -m "feat: integrate Universal Agent Context System"
```

### 4. Document Your Customizations

Keep notes on what you've customized and why.

### 5. Test with Multiple Agents

If using cross-platform approach, test with at least 2 different AI agents.

---

## Next Steps

After successful integration:

1. **Customize Instructions**: Tailor instruction files to your project
2. **Define Chat Modes**: Create project-specific chat modes
3. **Use Workflows**: Leverage workflow templates for common tasks
4. **Contribute Back**: Share improvements with the community

---

## Support

- **Documentation**: [[TTA/Workflows/README|README.md]]
- **Examples**: [docs/examples/](../examples/)
- **Issues**: [GitHub Issues](https://github.com/theinterneti/TTA.dev/issues)
- **Discussions**: [GitHub Discussions](https://github.com/theinterneti/TTA.dev/discussions)

---

**Integration complete!** Your project now has production-ready AI-native development primitives.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs guides integration guide document]]
