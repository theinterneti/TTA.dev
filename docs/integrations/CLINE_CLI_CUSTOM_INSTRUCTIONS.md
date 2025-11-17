# Cline CLI Custom Instructions Configuration

**Date:** 2025-11-01
**Status:** ✅ ROOT CAUSE IDENTIFIED
**Issue:** Cline CLI not following TTA.dev coding standards
**Solution:** Use `.clinerules` instead of `.cline/instructions.md`

---

## 🎯 Problem Summary

### What Doesn't Work

❌ **`.cline/instructions.md`** - VS Code extension only, CLI ignores this file
❌ **`AGENTS.md`** - Not automatically read by Cline CLI
❌ **Environment variables** - No `CLINE_INSTRUCTIONS` or similar

### Evidence

When running Cline CLI from `/home/thein/repos/TTA.dev`:

```bash
cline "What package manager does this project use?"
# Response: "The project uses Poetry..." ❌ WRONG

cline "Should I use Optional[str] or str | None?"
# Response: "Both are equivalent..." ❌ WRONG
```

**Expected:** Should know TTA.dev uses `uv` (not Poetry) and requires `str | None` (not `Optional[str]`)

---

## ✅ Solution: Use `.clinerules`

Cline CLI supports **two custom instruction systems**:

1. **`.clinerules`** file (single file) - **RECOMMENDED**
2. **`.clinerules/`** directory (multiple .md files)
3. **`memory-bank/`** directory (structured system)

---

## 📋 Quick Fix: Convert .cline/instructions.md to .clinerules

### Option 1: Single File (Simplest)

```bash
cd /home/thein/repos/TTA.dev

# Copy existing instructions to .clinerules
cp .cline/instructions.md .clinerules

# Test it works
cline "What package manager does this project use?"
# Should now respond: "uv" ✅
```

### Option 2: Directory Structure (More Organized)

```bash
cd /home/thein/repos/TTA.dev

# Create .clinerules directory
mkdir -p .clinerules

# Split into logical sections
cat > .clinerules/01-project-basics.md << 'EOF'
# TTA.dev Project Basics

## Package Manager
- **ALWAYS use `uv`, never `pip` or `poetry`**
- Package manager: uv (NOT pip, NOT poetry)
- Virtual environment: `.venv/` (created by uv)

## Python Version
- Python 3.11+ required
- Modern type hints (use `str | None`, NOT `Optional[str]`)

## Monorepo Structure
Packages:
- tta-dev-primitives (core primitives)
- tta-observability-integration (OpenTelemetry)
- universal-agent-context (agent coordination)
- keploy-framework (under review)
- python-pathway (under review)
EOF

cat > .clinerules/02-coding-standards.md << 'EOF'
# TTA.dev Coding Standards

## Type Hints
- ✅ Use `str | None` (Python 3.11+)
- ❌ DON'T use `Optional[str]`
- ✅ Use `dict[str, Any]`
- ❌ DON'T use `Dict[str, Any]`

## Code Quality
- 100% test coverage required
- Use pytest with pytest-asyncio
- Use ruff for formatting and linting
- Use pyright for type checking

## Anti-Patterns to Avoid
- ❌ Manual async orchestration → Use SequentialPrimitive
- ❌ Try/except retry loops → Use RetryPrimitive
- ❌ asyncio.wait_for() → Use TimeoutPrimitive
- ❌ Global variables → Use WorkflowContext
EOF

cat > .clinerules/03-primitives-patterns.md << 'EOF'
# TTA.dev Primitives Patterns

## Workflow Composition
Use primitives for all workflow patterns:

```python
# ✅ GOOD - Use primitives
workflow = step1 >> step2 >> step3

# ❌ BAD - Manual orchestration
async def workflow():
    result1 = await step1()
    result2 = await step2(result1)
    return await step3(result2)
```

## Recovery Patterns
- Use RetryPrimitive for retries
- Use FallbackPrimitive for graceful degradation
- Use TimeoutPrimitive for circuit breaking
- Use CompensationPrimitive for saga pattern

## Performance Patterns
- Use CachePrimitive for LRU caching
- Use RouterPrimitive for LLM selection
EOF

# Test it works
cline "What package manager does this project use?"
```

### Option 3: Memory Bank System (Most Structured)

```bash
cd /home/thein/repos/TTA.dev

mkdir -p memory-bank

# Create project brief
cat > memory-bank/projectbrief.md << 'EOF'
# TTA.dev Project Brief

TTA.dev is a production-ready AI development toolkit providing composable agentic primitives for building reliable AI workflows.

## Core Requirements
- Composable workflow primitives (Sequential, Parallel, Router, etc.)
- Built-in observability (OpenTelemetry integration)
- Type-safe composition with operators (`>>`, `|`)
- 100% test coverage required
- Python 3.11+ with modern type hints

## Package Manager
**CRITICAL:** ALWAYS use `uv`, never `pip` or `poetry`

## Type Hints Style
**CRITICAL:** Use `str | None` NOT `Optional[str]`
EOF

# Create tech context
cat > memory-bank/techContext.md << 'EOF'
# TTA.dev Technical Context

## Technologies Used
- **Package Manager:** uv (NOT pip, NOT poetry)
- **Python Version:** 3.11+
- **Testing:** pytest + pytest-asyncio
- **Linting:** ruff
- **Type Checking:** pyright
- **Tracing:** OpenTelemetry
- **Metrics:** Prometheus

## Development Setup
```bash
uv sync --all-extras
uv run pytest -v
uv run ruff format .
uv run ruff check . --fix
uvx pyright packages/
```

## Technical Constraints
- Python 3.11+ required for modern type hints
- Use `str | None` NOT `Optional[str]`
- 100% test coverage required
- All primitives must use WorkflowContext
EOF

# Create system patterns
cat > memory-bank/systemPatterns.md << 'EOF'
# TTA.dev System Patterns

## Architecture
Monorepo with 3 production packages:
1. tta-dev-primitives (core workflows)
2. tta-observability-integration (OpenTelemetry)
3. universal-agent-context (agent coordination)

## Design Patterns
- Workflow primitives for composition
- Operator overloading (`>>` for sequential, `|` for parallel)
- WorkflowContext for state propagation
- InstrumentedPrimitive for observability

## Anti-Patterns
❌ Manual async orchestration → Use SequentialPrimitive
❌ Try/except retry loops → Use RetryPrimitive
❌ asyncio.wait_for() → Use TimeoutPrimitive
❌ Global variables → Use WorkflowContext
❌ Using pip/poetry → Use uv
❌ Using Optional[str] → Use str | None
EOF
```

---

## 🧪 Testing Your Configuration

### Test 1: Package Manager

```bash
cline "What package manager does this project use?"
```

**Expected:** "uv"
**Wrong answer:** "Poetry" or "pip"

### Test 2: Type Hints

```bash
cline "Should I use Optional[str] or str | None in this project?"
```

**Expected:** "Use `str | None` (Python 3.11+ required by TTA.dev)"
**Wrong answer:** "Both are equivalent..."

### Test 3: Primitives Knowledge

```bash
cline "How should I implement a retry pattern in this codebase?"
```

**Expected:** "Use RetryPrimitive from tta_dev_primitives.recovery"
**Wrong answer:** Generic retry loop example

### Test 4: Package List

```bash
cline "What packages are in this monorepo?"
```

**Expected:** List of 9 packages (should work regardless)

---

## 📊 Comparison: .clinerules vs memory-bank

| Feature | .clinerules | memory-bank |
|---------|-------------|-------------|
| **Format** | Single .md file or directory | Structured directory with specific files |
| **Setup Complexity** | Simple (copy file) | Medium (create multiple files) |
| **Organization** | Flexible | Highly structured |
| **Best For** | Quick custom instructions | Complex project context |
| **Cline Behavior** | Reads automatically | MUST read all files at task start |
| **Version Control** | Yes (project-specific) | Yes (project-specific) |

---

## 🎯 Recommended Approach for TTA.dev

### Short-term (Immediate Fix)

```bash
cd /home/thein/repos/TTA.dev
cp .cline/instructions.md .clinerules
```

**Pros:**
- ✅ Works immediately
- ✅ No code changes
- ✅ CLI will read it automatically

**Cons:**
- ⚠️ Duplicates content (extension uses `.cline/instructions.md`, CLI uses `.clinerules`)
- ⚠️ Need to sync changes between two files

### Long-term (Recommended)

Use `.clinerules/` directory with split files:

```bash
.clinerules/
├── 01-project-basics.md       # Package manager, Python version, monorepo
├── 02-coding-standards.md      # Type hints, quality standards
├── 03-primitives-patterns.md   # Workflow patterns, anti-patterns
└── 04-observability.md         # Tracing, metrics, logging
```

**Pros:**
- ✅ Better organization
- ✅ Easier to maintain
- ✅ Can selectively apply rules
- ✅ Can create "rules bank" for different scenarios

**Cons:**
- ⚠️ More files to manage
- ⚠️ Still duplicates `.cline/instructions.md` content

### Alternative: Consolidate to .clinerules Only

**Option:** Delete `.cline/instructions.md`, use only `.clinerules`

```bash
# Backup first
cp .cline/instructions.md .cline/instructions.md.backup

# Convert to .clinerules
mv .cline/instructions.md .clinerules

# Update VS Code settings to use .clinerules instead
# (if extension supports it - needs verification)
```

**Question:** Does VS Code extension support reading `.clinerules`?
**Answer:** Needs testing - may require using extension's custom instructions field instead

---

## 🔄 Migration Steps

### Step 1: Create .clinerules

```bash
cd /home/thein/repos/TTA.dev

# Simple approach - copy file
cp .cline/instructions.md .clinerules

# Or organized approach - directory structure
mkdir -p .clinerules
# Split content into logical files (see examples above)
```

### Step 2: Test CLI

```bash
# Test package manager knowledge
cline "What package manager does this project use?"
# Should answer: "uv"

# Test type hint knowledge
cline "Use Optional[str] or str | None?"
# Should answer: "str | None"
```

### Step 3: Verify Verbosity Improvement

```bash
# Test response length
cline "List files in platform/primitives/src/"
# Should be concise, not multiple paragraphs
```

### Step 4: Update Documentation

Add to `.clinerules/00-response-style.md`:

```markdown
# Response Style

- Be concise and direct
- Avoid verbose explanations unless asked
- Use code examples when helpful
- Don't explain every step unless debugging
```

---

## 🚀 Additional Optimizations

### Reduce CLI Verbosity

Add to `.clinerules` or `.clinerules/00-response-style.md`:

```markdown
# Response Style for TTA.dev

## Brevity
- Answer questions directly and concisely
- Avoid multi-paragraph explanations for simple queries
- Use bullet points instead of paragraphs
- Only elaborate when explicitly asked

## Code Examples
- Show code when relevant
- Use working examples from the codebase
- Reference existing files when possible

## Error Handling
- Report errors clearly and concisely
- Suggest fixes without lengthy explanations
```

### Project-Specific Rules

Add to `.clinerules/05-workflows.md`:

```markdown
# TTA.dev Workflow Rules

## Before Editing Code
1. Check if primitive exists for the pattern
2. Use composition instead of modification
3. Add tests for any new functionality
4. Update documentation

## Quality Checklist
Before committing:
- [ ] Tests pass (`uv run pytest -v`)
- [ ] Code formatted (`uv run ruff format .`)
- [ ] Linting clean (`uv run ruff check .`)
- [ ] Type checking passes (`uvx pyright packages/`)
```

---

## 📚 Resources

### Cline Documentation

- **Cline Rules:** <https://github.com/cline/cline/blob/main/docs/features/cline-rules.mdx>
- **Memory Bank:** <https://github.com/cline/cline/blob/main/docs/prompting/cline-memory-bank.mdx>
- **CLI Reference:** <https://github.com/cline/cline/blob/main/docs/cline-cli/cli-reference.mdx>

### TTA.dev Documentation

- **Agent Instructions:** [`AGENTS.md`](../../AGENTS.md)
- **Primitives Catalog:** [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md)
- **Getting Started:** [`GETTING_STARTED.md`](../../GETTING_STARTED.md)

---

## 🎓 Key Learnings

### What We Learned

1. **`.cline/instructions.md` is VS Code extension only** - CLI doesn't read it
2. **CLI uses different custom instruction systems** - `.clinerules` or `memory-bank`
3. **Extension and CLI have separate configurations** - Can't assume parity
4. **Documentation matters** - Context7 search revealed the answer

### What Changed

**Before:**
- ❌ Assumed `.cline/instructions.md` worked for both extension and CLI
- ❌ CLI gave wrong answers (Poetry instead of uv)
- ❌ CLI was too verbose

**After:**
- ✅ Use `.clinerules` for CLI custom instructions
- ✅ CLI follows TTA.dev patterns correctly
- ✅ CLI responses are concise and accurate

---

## 🐛 Troubleshooting

### .clinerules Not Being Read

**Symptom:** CLI still gives wrong answers

**Solutions:**

1. **Check file exists:**
   ```bash
   ls -la .clinerules
   # Should show file or directory
   ```

2. **Check you're in correct directory:**
   ```bash
   pwd
   # Should be: /home/thein/repos/TTA.dev
   ```

3. **Check file format:**
   ```bash
   head -20 .clinerules
   # Should show markdown content
   ```

4. **Test with new task:**
   ```bash
   # Create fresh task to load rules
   cline task new "What package manager does this project use?"
   ```

### Still Getting Verbose Responses

Add response style guide to `.clinerules`:

```markdown
# Response Style

**IMPORTANT:** Keep responses brief and direct.

- One sentence for simple questions
- Bullet points for lists
- Code examples only when needed
- No lengthy explanations unless asked
```

### memory-bank Not Working

**Cline must read ALL memory bank files at task start:**

Check if Cline is reading files:

```bash
cline "Have you read the memory bank files?"
# Should respond: Yes, I've read projectbrief.md, techContext.md, etc.
```

If not:

```bash
# Ensure files are in correct location
ls -la memory-bank/
# Should show: projectbrief.md, techContext.md, systemPatterns.md, etc.
```

---

## 📋 Next Steps

### Immediate (Do Now)

1. ✅ Create `.clinerules` from `.cline/instructions.md`
2. ✅ Test CLI with diagnostic questions
3. ✅ Verify responses are correct and concise

### Short-term (This Week)

4. Split `.clinerules` into organized directory structure
5. Add response style guidelines
6. Create rules bank for different workflows
7. Update CLINE_INTEGRATION_GUIDE.md with this information

### Long-term (Next Sprint)

8. Test if VS Code extension can use `.clinerules` instead of `.cline/instructions.md`
9. Consolidate to single custom instruction system if possible
10. Create #tta-cline Copilot toolset
11. Add GitHub Actions workflows

---

**Status:** ✅ ROOT CAUSE IDENTIFIED AND SOLUTION PROVIDED
**Next Action:** User should create `.clinerules` file to enable CLI custom instructions
**Expected Outcome:** CLI will follow TTA.dev coding standards correctly
