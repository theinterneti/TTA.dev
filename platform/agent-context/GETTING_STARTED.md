# Getting Started - Universal Agent Context System

**5-minute quickstart guide**

---

## Choose Your Path

The Universal Agent Context System offers two complementary approaches:

1. **Cross-Platform** (`.github/`) - Works with Claude, Gemini, Copilot, Augment
2. **Augment CLI-Specific** (`.augment/`) - Advanced features for Augment CLI users

---

## Path 1: Cross-Platform Setup (Recommended for Most Users)

### Step 1: Copy Files

```bash
# Copy cross-platform primitives to your project
cp -r packages/universal-agent-context/.github/ .
cp packages/universal-agent-context/AGENTS.md .
```

### Step 2: Verify Structure

Your project should now have:
```
your-project/
├── .github/
│   ├── instructions/
│   ├── chatmodes/
│   └── copilot-instructions.md
└── AGENTS.md
```

### Step 3: Test with Your AI Agent

**For Claude**:
- Claude automatically loads `.github/` instructions
- AGENTS.md provides universal context

**For GitHub Copilot**:
- Copilot reads `.github/copilot-instructions.md`
- Instructions in `.github/instructions/` are selectively loaded

**For Gemini**:
- Gemini loads AGENTS.md for context
- Instructions are pattern-matched to active files

**For Augment**:
- Augment loads both `.github/` and AGENTS.md
- Full cross-platform compatibility

### Step 4: Customize (Optional)

Edit instruction files to match your project:

```bash
# Edit domain-specific instructions
vim .github/instructions/python-quality-standards.instructions.md

# Edit chat modes
vim .github/chatmodes/backend-dev.chatmode.md
```

---

## Path 2: Augment CLI-Specific Setup (Advanced Users)

### Step 1: Copy Files

```bash
# Copy Augment CLI-specific primitives
cp -r packages/universal-agent-context/.augment/ .
cp packages/universal-agent-context/apm.yml .
```

### Step 2: Verify Structure

Your project should now have:
```
your-project/
├── .augment/
│   ├── instructions/
│   ├── chatmodes/
│   ├── workflows/
│   ├── context/
│   ├── memory/
│   └── rules/
└── apm.yml
```

### Step 3: Initialize Context Management

```bash
# Create a new context session
python .augment/context/cli.py new my-project-session

# Add context to the session
python .augment/context/cli.py add my-project-session "Working on feature X" --importance 1.0

# Show session
python .augment/context/cli.py show my-project-session
```

### Step 4: Use Augster Identity System

The Augster identity system is automatically active through:
- `.augment/instructions/augster-core-identity.instructions.md`
- `.augment/instructions/augster-maxims.instructions.md`
- `.augment/instructions/augster-protocols.instructions.md`

No additional setup required!

---

## Path 3: Comprehensive Setup (Both Approaches)

### Step 1: Copy Everything

```bash
# Copy both structures
cp -r packages/universal-agent-context/.github/ .
cp -r packages/universal-agent-context/.augment/ .
cp packages/universal-agent-context/AGENTS.md .
cp packages/universal-agent-context/CLAUDE.md .
cp packages/universal-agent-context/GEMINI.md .
cp packages/universal-agent-context/apm.yml .
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

**Use both when**:
- Demonstrating multiple approaches
- Maximum flexibility
- Educational purposes

---

## Validation

Validate your setup:

```bash
# Run validation script
python packages/universal-agent-context/scripts/validate-export-package.py

# Expected output:
# ✅ All YAML frontmatter valid
# ✅ All cross-references valid
# ✅ File structure correct
```

---

## Next Steps

### Learn More

- **Integration Guide**: [docs/guides/INTEGRATION_GUIDE.md](docs/guides/INTEGRATION_GUIDE.md)
- **Migration Guide**: [docs/guides/MIGRATION_GUIDE.md](docs/guides/MIGRATION_GUIDE.md)
- **Architecture**: [docs/architecture/OVERVIEW.md](docs/architecture/OVERVIEW.md)

### Customize

1. **Add Custom Instructions**:
   ```bash
   # Create new instruction file
   vim .github/instructions/my-custom.instructions.md
   ```

2. **Add Custom Chat Modes**:
   ```bash
   # Create new chat mode
   vim .github/chatmodes/my-custom-role.chatmode.md
   ```

3. **Update AGENTS.md**:
   ```bash
   # Customize universal context
   vim AGENTS.md
   ```

### Get Help

- **Documentation**: [docs/](docs/)
- **Examples**: [docs/examples/](docs/examples/)
- **Issues**: [GitHub Issues](https://github.com/theinterneti/TTA.dev/issues)

---

## Common Issues

### Issue 1: Instructions Not Loading

**Problem**: AI agent doesn't seem to use instructions

**Solution**:
- Verify files are in correct location (`.github/instructions/`)
- Check YAML frontmatter is valid
- Ensure `applyTo` patterns match your files

### Issue 2: Context Management Not Working

**Problem**: `.augment/context/cli.py` not found

**Solution**:
- Ensure you copied `.augment/` directory
- Check Python is installed (`python --version`)
- Verify file permissions (`chmod +x .augment/context/cli.py`)

### Issue 3: Chat Modes Not Activating

**Problem**: Chat modes don't seem to work

**Solution**:
- Verify files are in correct location (`.github/chatmodes/` or `.augment/chatmodes/`)
- Check YAML frontmatter is valid
- Ensure your AI agent supports chat modes

---

## Quick Reference

### File Locations

| File Type | Cross-Platform | Augment CLI |
|-----------|---------------|-------------|
| Instructions | `.github/instructions/` | `.augment/instructions/` |
| Chat Modes | `.github/chatmodes/` | `.augment/chatmodes/` |
| Workflows | N/A | `.augment/workflows/` |
| Context | N/A | `.augment/context/` |
| Memory | N/A | `.augment/memory/` |
| Universal Context | `AGENTS.md` | `AGENTS.md` |
| Config | `apm.yml` | `apm.yml` |

### Commands

```bash
# Validation
python scripts/validate-export-package.py

# Context management (Augment CLI)
python .augment/context/cli.py new <session-name>
python .augment/context/cli.py add <session-name> "<message>"
python .augment/context/cli.py show <session-name>

# View documentation
cat docs/guides/INTEGRATION_GUIDE.md
cat docs/architecture/YAML_SCHEMA.md
```

---

**Ready to go!** Start using the Universal Agent Context System with your AI agent of choice.

For detailed documentation, see [README.md](README.md) and [docs/](docs/).



---
**Logseq:** [[TTA.dev/Platform/Agent-context/Getting_started]]
