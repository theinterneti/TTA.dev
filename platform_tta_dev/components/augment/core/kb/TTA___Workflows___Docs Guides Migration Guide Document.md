---
title: Migration Guide - Universal Agent Context System
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/guides/MIGRATION_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Migration Guide - Universal Agent Context System]]

**Guide for migrating from legacy structures to the Universal Agent Context System**

---

## Overview

This guide helps you migrate from various legacy AI agent primitive structures to the Universal Agent Context System. Choose the migration path that matches your current setup.

---

## Migration Scenarios

### Scenario 1: From Legacy `.augment/` to Modern `.github/`

**When to use**: You have an older `.augment/` structure and want cross-platform compatibility

#### Step 1: Assess Current Structure

```bash
# Check your current .augment/ structure
ls -la .augment/
```

#### Step 2: Create Backup

```bash
# Backup existing .augment/
cp -r .augment/ .augment.backup/
```

#### Step 3: Copy New Structure

```bash
# Copy modern .github/ structure
cp -r /path/to/universal-agent-context/.github/ .
cp /path/to/universal-agent-context/AGENTS.md .
```

#### Step 4: Migrate Custom Content

For each custom instruction file in `.augment/instructions/`:

1. **Add YAML frontmatter**:
   ```yaml
   ---
   applyTo: "**/*.py"
   tags: ["python", "custom"]
   description: "Your custom instruction"
   priority: 5
   ---
   ```

2. **Copy to `.github/instructions/`**:
   ```bash
   cp .augment/instructions/my-custom.instructions.md .github/instructions/
   ```

3. **Update references** to use new file locations

#### Step 5: Test

```bash
# Test with your AI agent
# Verify instructions load correctly
```

#### Step 6: Remove Old Structure (Optional)

```bash
# Once verified, remove old .augment/
rm -rf .augment/
```

---

### Scenario 2: From Monolithic to Modular

**When to use**: You have a single large instruction file and want modular structure

#### Step 1: Analyze Current File

```bash
# Review your monolithic file
cat my-instructions.md
```

#### Step 2: Identify Sections

Break down into logical sections:
- Language-specific (Python, TypeScript, etc.)
- Domain-specific (API, frontend, backend)
- Quality standards
- Testing requirements

#### Step 3: Create Modular Files

For each section, create a new instruction file:

```bash
# Example: Python section
vim .github/instructions/python-standards.instructions.md
```

Add YAML frontmatter:
```yaml
---
applyTo: "**/*.py"
tags: ["python", "quality"]
description: "Python development standards"
priority: 5
---
```

Copy relevant content from monolithic file.

#### Step 4: Update References

Update any cross-references between files.

#### Step 5: Test

Test each modular file individually.

#### Step 6: Remove Monolithic File

```bash
# Once verified, remove old file
rm my-instructions.md
```

---

### Scenario 3: From Agent-Specific to Universal

**When to use**: You have agent-specific files (e.g., only for Claude) and want universal compatibility

#### Step 1: Review Current Files

```bash
# Check current agent-specific files
ls -la .claude/
ls -la .copilot/
```

#### Step 2: Copy Universal Structure

```bash
# Copy universal structure
cp -r /path/to/universal-agent-context/.github/ .
cp /path/to/universal-agent-context/AGENTS.md .
```

#### Step 3: Migrate Content

For each agent-specific file:

1. **Extract universal content** (works across all agents)
2. **Add to `.github/instructions/`** with YAML frontmatter
3. **Keep agent-specific content** in separate files (CLAUDE.md, GEMINI.md, etc.)

#### Step 4: Create Agent-Specific Files

```bash
# Copy agent-specific templates
cp /path/to/universal-agent-context/CLAUDE.md .
cp /path/to/universal-agent-context/GEMINI.md .
```

Update with your agent-specific content.

#### Step 5: Test with Multiple Agents

Test with at least 2 different AI agents to verify universal compatibility.

---

### Scenario 4: Adding Quality Gates

**When to use**: You want to add quality gates and component maturity workflow

#### Step 1: Copy Quality Gate Files

```bash
# Copy quality-related instruction files
cp /path/to/universal-agent-context/.github/instructions/python-quality-standards.instructions.md .github/instructions/
cp /path/to/universal-agent-context/.github/instructions/testing-requirements.instructions.md .github/instructions/
```

#### Step 2: Configure for Your Project

Edit files to match your quality standards:

```yaml
---
applyTo: "src/**/*.py"  # Adjust to your structure
tags: ["python", "quality"]
description: "Python quality standards"
priority: 8
---
```

#### Step 3: Add Component Maturity Workflow

```bash
# Copy component maturity instruction
cp /path/to/universal-agent-context/.augment/instructions/component-maturity.instructions.md .github/instructions/
```

Update maturity thresholds for your project.

#### Step 4: Implement Quality Checks

Add quality check scripts to your CI/CD pipeline.

---

## Migration Checklist

### Pre-Migration

- [ ] Backup existing structure
- [ ] Document current setup
- [ ] Identify custom content
- [ ] Plan migration timeline

### During Migration

- [ ] Copy new structure
- [ ] Migrate custom content
- [ ] Add YAML frontmatter
- [ ] Update cross-references
- [ ] Test with AI agents

### Post-Migration

- [ ] Verify all features work
- [ ] Remove old structure
- [ ] Update documentation
- [ ] Train team on new structure

---

## Common Migration Issues

### Issue 1: YAML Frontmatter Errors

**Problem**: Invalid YAML syntax

**Solution**:
```yaml
# Correct format
---
applyTo: "**/*.py"
tags: ["python"]
description: "Python guidelines"
---

# Incorrect (missing quotes)
---
applyTo: **/*.py
tags: [python]
description: Python guidelines
---
```

### Issue 2: Pattern Matching Not Working

**Problem**: Instructions not loading for expected files

**Solution**:
- Verify `applyTo` patterns are correct
- Use `**` for recursive matching
- Test patterns with glob tester

### Issue 3: Lost Custom Content

**Problem**: Custom content not migrated

**Solution**:
- Review backup carefully
- Migrate section by section
- Test each migration step

---

## Rollback Procedure

If migration fails, rollback to previous state:

### Step 1: Stop Using New Structure

```bash
# Remove new structure
rm -rf .github/
rm AGENTS.md
```

### Step 2: Restore Backup

```bash
# Restore from backup
cp -r .augment.backup/ .augment/
```

### Step 3: Verify Restoration

```bash
# Verify old structure works
ls -la .augment/
```

### Step 4: Document Issues

Document what went wrong for future migration attempt.

---

## Migration Timeline

### Week 1: Planning

- Assess current structure
- Create backup
- Plan migration approach
- Identify custom content

### Week 2: Migration

- Copy new structure
- Migrate custom content
- Add YAML frontmatter
- Update cross-references

### Week 3: Testing

- Test with AI agents
- Verify all features work
- Fix any issues
- Document changes

### Week 4: Rollout

- Remove old structure
- Update team documentation
- Train team on new structure
- Monitor for issues

---

## Success Criteria

Migration is successful when:

- ✅ All custom content migrated
- ✅ YAML frontmatter valid
- ✅ Instructions load correctly
- ✅ Chat modes work as expected
- ✅ No functionality lost
- ✅ Team trained on new structure

---

## Support

For migration help:
- See [[TTA/Workflows/INTEGRATION_GUIDE|INTEGRATION_GUIDE.md]]
- Check [examples/](../examples/)
- Open an [issue](https://github.com/theinterneti/TTA.dev/issues)
- Ask in [discussions](https://github.com/theinterneti/TTA.dev/discussions)

---

## Next Steps

After successful migration:

1. **Customize**: Tailor instruction files to your project
2. **Extend**: Add new instruction files and chat modes
3. **Optimize**: Refine `applyTo` patterns and priorities
4. **Share**: Contribute improvements back to the community

---

**Migration complete!** Your project now uses the Universal Agent Context System.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs guides migration guide document]]
