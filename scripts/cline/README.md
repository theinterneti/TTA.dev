# Cline CLI Scripts for TTA.dev

**Automated Development Workflows Using Cline CLI**

This directory contains scripts that leverage Cline CLI's piping capabilities to automate common development tasks in TTA.dev.

---

## 🎯 Available Scripts

### 1. Auto-Fix Validation Errors

**Script:** `auto-fix-validation.sh`

**Purpose:** Automatically fix package validation issues

**Usage:**
```bash
./scripts/cline/auto-fix-validation.sh <package-name>
```

**Example:**
```bash
./scripts/cline/auto-fix-validation.sh tta-dev-primitives
```

**What it does:**
1. Runs `./scripts/validate-package.sh` on the package
2. Captures all validation errors
3. Sends to Cline CLI for automated fixing
4. Cline fixes issues following TTA.dev standards
5. Re-validates to confirm fixes

**Time saved:** 30-60 minutes → 5 minutes (review)

---

### 2. Fix Test Failures

**Script:** `fix-test-failures.sh`

**Purpose:** Analyze and fix pytest failures with AI assistance

**Usage:**
```bash
# Interactive mode (default) - Cline asks for approval
./scripts/cline/fix-test-failures.sh interactive [package-name]

# Autonomous mode - Auto-fix simple errors
./scripts/cline/fix-test-failures.sh autonomous [package-name]

# Just run on whole project
./scripts/cline/fix-test-failures.sh
```

**Examples:**
```bash
# Interactive - fix failures in specific package
./scripts/cline/fix-test-failures.sh interactive tta-dev-primitives

# Autonomous - auto-fix import/syntax errors
./scripts/cline/fix-test-failures.sh autonomous

# Interactive - fix all test failures
./scripts/cline/fix-test-failures.sh
```

**What it does:**
- **Interactive Mode:**
  1. Runs pytest and captures failures
  2. Sends to Cline for detailed analysis
  3. Cline categorizes failures (logic, assertions, imports, etc.)
  4. Proposes fixes with explanations
  5. Waits for approval before applying

- **Autonomous Mode:**
  1. Auto-fixes simple errors (ImportError, SyntaxError, etc.)
  2. Faster but less comprehensive
  3. Best for obvious mistakes

**Time saved:** 20-40 minutes → 5-10 minutes

---

### 3. Review Git Diff

**Script:** `review-diff.sh`

**Purpose:** Get AI code review before committing

**Usage:**
```bash
# Review uncommitted changes
./scripts/cline/review-diff.sh

# Review staged changes
./scripts/cline/review-diff.sh staged

# Review branch vs main
./scripts/cline/review-diff.sh feature-branch

# Review specific commit
./scripts/cline/review-diff.sh HEAD~1
```

**What it does:**
1. Captures git diff based on scope
2. Sends to Cline for review
3. Cline checks:
   - Tests included?
   - Documentation updated?
   - Type hints correct?
   - Follows TTA.dev patterns?
   - Breaking changes?
   - Security concerns?
4. Provides detailed feedback with line numbers
5. Recommends: APPROVE / CHANGES_NEEDED / REJECT

**Review depth adjusts to change size:**
- Small (<50 lines): Detailed review
- Medium (50-200 lines): Standard review
- Large (>200 lines): Summary review (critical issues only)

**Time saved:** 15-30 minutes → 2-5 minutes

---

## 📋 Prerequisites

### 1. Install Cline CLI

```bash
# Using npm
npm install -g @cline/cli

# Or using npx (no install)
npx @cline/cli --version
```

### 2. Configure Cline CLI

```bash
# OpenRouter (recommended - cost-effective)
cline config set api-provider openrouter
cline config set api-key sk-or-v1-YOUR_KEY_HERE
cline config set api-model-id mistralai/mistral-small-3.2

# Verify configuration
cline config list
```

**Get OpenRouter API key:** <https://openrouter.ai/keys>

**Cost:** ~$0.10/1M tokens (Mistral Small 3.2) = very affordable

### 3. Ensure .clinerules File Exists

All scripts rely on `.clinerules` in the repository root to understand TTA.dev coding standards.

```bash
# Check it exists
ls -la .clinerules

# If missing, create from template
cat > .clinerules << 'EOF'
# TTA.dev Coding Standards

## Package Manager
**ALWAYS use `uv`, NEVER use `pip` or `poetry`**

## Type Hints
**ALWAYS use `str | None`, NEVER use `Optional[str]`**

## Testing
**100% test coverage required**
EOF
```

---

## 🚀 Quick Start

### Try It Now!

**1. Fix validation errors:**

```bash
# Run validation to see current issues
./scripts/validate-package.sh tta-dev-primitives

# Auto-fix with Cline
./scripts/cline/auto-fix-validation.sh tta-dev-primitives
```

**2. Fix test failures:**

```bash
# Run tests to see failures
uv run pytest packages/tta-dev-primitives/tests/ -v

# Fix with Cline
./scripts/cline/fix-test-failures.sh interactive tta-dev-primitives
```

**3. Review your changes:**

```bash
# Make some changes
echo "# Test" >> README.md

# Get AI review
./scripts/cline/review-diff.sh
```

---

## 💡 Usage Patterns

### Pattern 1: Pre-Commit Workflow

```bash
# 1. Make changes
vim packages/tta-dev-primitives/src/something.py

# 2. Review with AI
./scripts/cline/review-diff.sh

# 3. Address issues Cline found

# 4. Stage and review staged
git add -p
./scripts/cline/review-diff.sh staged

# 5. Commit
git commit -m "Add feature"
```

### Pattern 2: Quality Gate Before PR

```bash
# 1. Run full validation
./scripts/cline/auto-fix-validation.sh tta-dev-primitives

# 2. Fix any remaining test failures
./scripts/cline/fix-test-failures.sh interactive tta-dev-primitives

# 3. Review all changes
./scripts/cline/review-diff.sh my-feature-branch

# 4. Create PR
gh pr create
```

### Pattern 3: Fix CI Failures

```bash
# CI fails on your PR

# 1. Pull latest
git pull

# 2. Run tests locally
uv run pytest -v

# 3. Auto-fix failures
./scripts/cline/fix-test-failures.sh autonomous

# 4. Verify
uv run pytest -v

# 5. Push fix
git add -A && git commit -m "fix: CI test failures" && git push
```

---

## 🎓 Advanced Usage

### Piping Arbitrary Output to Cline

These scripts are templates. You can pipe ANY output to Cline:

```bash
# Example: Fix ruff errors
uv run ruff check packages/tta-dev-primitives | \
  cline "Fix all ruff errors shown. Follow .clinerules standards."

# Example: Improve docstrings
uvx pydocstyle packages/tta-dev-primitives/src | \
  cline -y "Add missing docstrings following Google style."

# Example: Fix type errors
uvx pyright packages/tta-dev-primitives | \
  cline "Fix these type errors. Use 'str | None' not 'Optional[str]'."
```

### Combining Scripts

```bash
# Run validation, fix issues, then review changes
./scripts/cline/auto-fix-validation.sh tta-dev-primitives && \
./scripts/cline/review-diff.sh
```

### Custom Prompts

You can customize prompts by editing the scripts or creating wrappers:

```bash
#!/bin/bash
# my-custom-review.sh

git diff | cline "Review this diff with extra focus on:
1. Security implications
2. Performance impact
3. Backward compatibility

$(cat)"
```

---

## 🔧 Troubleshooting

### "Cline CLI not found"

```bash
# Install globally
npm install -g @cline/cli

# Or use npx
alias cline='npx @cline/cli'
```

### "Cline CLI not configured"

```bash
# Set up OpenRouter
cline config set api-provider openrouter
cline config set api-key sk-or-v1-YOUR_KEY
cline config set api-model-id mistralai/mistral-small-3.2

# Verify
cline config list
```

### ".clinerules file not found"

```bash
# Check current directory
pwd  # Should be in /home/thein/repos/TTA.dev

# Create .clinerules if missing
cat > .clinerules << 'EOF'
# TTA.dev Coding Standards
- Package manager: uv (NOT pip)
- Type hints: str | None (NOT Optional[str])
- Test coverage: 100% required
EOF
```

### "Cline gives wrong answers"

Ensure `.clinerules` contains TTA.dev standards:

```bash
# View current .clinerules
cat .clinerules

# Should include:
# - Package manager: uv
# - Type hints: str | None
# - Testing: pytest-asyncio, 100% coverage
# - Repository structure
```

### Script hangs or doesn't respond

```bash
# Check Cline process
ps aux | grep cline

# Kill if needed
pkill -f cline

# Restart
./scripts/cline/[script-name].sh
```

---

## 📊 Cost Estimates

Using OpenRouter with Mistral Small 3.2 (~$0.10/1M tokens):

| Task | Avg Input Tokens | Avg Output Tokens | Cost per Run |
|------|------------------|-------------------|--------------|
| Validation fixes | 5,000 | 2,000 | $0.0007 |
| Test failure fixes | 8,000 | 3,000 | $0.0011 |
| Diff review | 3,000 | 1,000 | $0.0004 |

**Monthly cost estimate (moderate usage):**
- 10 validation fixes: $0.007
- 20 test fixes: $0.022
- 50 diff reviews: $0.020
- **Total: ~$0.05/month** 🎉

Compare to Claude 3.7 Sonnet: ~$3.00/month for same usage (60x more expensive)

---

## 🎯 Next Steps

### Extend These Scripts

1. **Add more workflows**
   - Documentation enhancement
   - PR review automation
   - Continuous refactoring

2. **Integrate with CI/CD**
   - GitHub Actions workflows
   - Pre-commit hooks
   - Automated PR reviews

3. **Customize for your needs**
   - Adjust prompts
   - Change approval levels
   - Add package-specific rules

### Share Your Workflows

Found a useful Cline CLI pattern? Add it to this directory!

---

## 📚 Resources

- **Cline Documentation:** [../integrations/CLINE_INTEGRATION_GUIDE.md](../integrations/CLINE_INTEGRATION_GUIDE.md)
- **Workflow Opportunities:** [../integrations/CLINE_CLI_WORKFLOW_OPPORTUNITIES.md](../integrations/CLINE_CLI_WORKFLOW_OPPORTUNITIES.md)
- **TTA.dev Standards:** [.clinerules](../../.clinerules)
- **OpenRouter:** <https://openrouter.ai>

---

**Happy automating! 🤖✨**
