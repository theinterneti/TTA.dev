# Cline Integration Guide for TTA.dev

**Quick Start Guide for Copilot ↔ Cline Collaboration**

**Status:** Ready for Implementation
**Date:** November 6, 2025
**Prerequisites:** VS Code, TTA.dev workspace, API key (Claude/OpenAI)

---

## Table of Contents

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [First Task](#first-task)
4. [Copilot Collaboration](#copilot-collaboration)
5. [CLI Usage](#cli-usage)
6. [GitHub Actions](#github-actions)
7. [Workflows](#workflows)
8. [Troubleshooting](#troubleshooting)

---

## Installation

### Step 1: Install Cline Extension

**From VS Code Marketplace:**

```bash
# Via command line
code --install-extension saoudrizwan.claude-dev

# Or via VS Code:
# Cmd+Shift+X → Search "Cline" → Install
```

**Verify Installation:**

1. Look for Cline icon in Activity Bar (left sidebar)
2. Click to open Cline panel
3. Should see welcome screen

### Step 2: Install Cline CLI (Optional but Recommended)

**For GitHub Actions and Scripting:**

```bash
# Using npm
npm install -g @cline/cli

# Verify
cline --version

# Or using npx (no install needed)
npx @cline/cli --version
```

**Configure Cline CLI:**

The CLI uses separate configuration from the VS Code extension:

```bash
# Configure for OpenRouter (recommended)
cline config set api-provider openrouter
cline config set api-key sk-or-v1-YOUR_KEY_HERE
cline config set api-model-id mistralai/mistral-small-3.2

# Alternative models for CLI
# Fast and cheap: mistralai/mistral-small-3.2
# Balanced: deepseek/deepseek-r1
# Quality: anthropic/claude-3.7-sonnet

# Verify configuration
cline config list
```

**TTA.dev CLI Configuration:**

For consistency with TTA.dev development, we use **Mistral Small 3.2** for CLI tasks:

- ✅ Fast response times
- ✅ Cost-effective (~$0.10/1M tokens)
- ✅ Good code quality
- ✅ Perfect for scripting and automation

---

## Configuration

### Step 3: Configure API Provider

**Choose Your Provider:**

TTA.dev supports multiple providers. For cost-effective development, **OpenRouter** is recommended with free/affordable models:

- **OpenRouter** (multiple models - recommended for cost)
- Anthropic (Claude - premium)
- OpenAI (GPT-4, GPT-3.5)
- Ollama (local models - free)
- AWS Bedrock
- Azure OpenAI

**Setup Steps:**

1. Open Cline panel
2. Click Settings (gear icon)
3. Select API Provider
4. Enter API Key
5. Choose Model(s)

**Recommended Setup: OpenRouter with Dual Models**

Cline supports **separate models for planning vs execution**:

```json
// Cline Settings (accessed via GUI)
{
  "apiProvider": "openrouter",
  "openRouterApiKey": "sk-or-v1-...",

  // For planning, complex reasoning (Plan)
  "apiModelId": "deepseek/deepseek-r1",

  // For execution, code generation (Act)
  "actApiProvider": "openrouter",
  "actApiModelId": "meta-llama/llama-4-scout"
}
```

**Why This Configuration?**

- ✅ **DeepSeek R1**: Excellent reasoning for task planning (~free tier available)
- ✅ **Llama 4 Scout**: Fast, cost-effective code generation
- ✅ **OpenRouter**: Single account, multiple models, pay-as-you-go
- ✅ **Total Cost**: ~$0-5/month for moderate usage

**Alternative: Premium Setup**

```json
// For maximum quality (higher cost)
{
  "apiProvider": "anthropic",
  "apiKey": "sk-ant-...",
  "apiModelId": "claude-3-5-sonnet-20241022"
}
```

**Alternative: Local/Free Setup**

```json
// For zero cost (requires Ollama installed)
{
  "apiProvider": "ollama",
  "ollamaBaseUrl": "http://localhost:11434",
  "apiModelId": "codellama",
  "actApiModelId": "deepseek-coder"
}
```

### Step 4: Verify MCP Integration

**Check MCP Servers:**

1. Open Cline Settings
2. Navigate to "MCP" tab
3. Verify TTA.dev servers detected:
   - ✅ Context7
   - ✅ Grafana
   - ✅ Pylance
   - ✅ Logseq (if enabled)
   - ✅ Database Client

**MCP Config Location:**

```bash
# Linux/macOS
~/.config/mcp/mcp_settings.json

# Windows
%APPDATA%\mcp\mcp_settings.json
```

**Test MCP Server:**

```plaintext
In Cline chat:
"Using Context7, find documentation for httpx async usage"
```

Cline should call MCP tools automatically.

---

## First Task

### Step 5: Run Your First Cline Task

**Simple Test:**

1. Open Cline panel
2. Type in chat: "List all files in platform/primitives/src/"
3. Cline will use `list_files` tool
4. Review results

**More Complex Task:**

```plaintext
"Create a new Python file at platform/primitives/examples/hello_cline.py
that demonstrates basic primitive usage. Include:
1. Import statements
2. Create a simple workflow
3. Execute and print results
4. Add comments explaining each step"
```

**What to Expect:**

- Cline analyzes request
- Creates file with diff preview
- Asks for approval
- Writes file on approval
- Confirms completion

**Approval Workflow:**

1. Cline shows diff in editor
2. Review changes carefully
3. Click "Save" to approve OR "Reject" to decline
4. Cline proceeds or reverts

---

## Copilot Collaboration

### Strategy: When to Use Each

**Use Copilot For:**

- Quick 1-3 file edits
- Code explanations
- Documentation writing
- Planning and architecture discussions
- Code review

**Use Cline For:**

- Multi-file refactorings (5+ files)
- Complex implementations requiring multiple steps
- Terminal operations
- GitHub PR workflows
- Autonomous background tasks

### Handoff Pattern: Copilot → Cline

**Example 1: Complex Refactoring**

```markdown
## In Copilot Chat (@workspace #tta-package-dev)

User: "I need to add type hints to all primitives in tta-dev-primitives"

Copilot: "That's a large task affecting 15+ files. I recommend using Cline for this.
Here's what needs to be done:
1. Add type hints to all function signatures
2. Add return type annotations
3. Update tests with proper types
4. Verify with pyright

Would you like me to prepare a task for Cline?"

User: "Yes, please"

Copilot: "I've analyzed the codebase. Here's the Cline task:

@cline Please add comprehensive type hints to all primitives in
platform/primitives/src/tta_dev_primitives/:
- Add parameter types
- Add return types
- Use modern Python 3.11+ syntax (X | None instead of Optional[X])
- Follow TTA.dev patterns in base.py
- Verify with: uvx pyright platform/primitives/
- Files to update: [list of 15 files]

Start with core/ directory, then recovery/, performance/, etc."

[Cline takes over and executes]
```

**Example 2: Parallel Work**

```markdown
## Copilot handles documentation while Cline handles implementation

User: "@workspace I need a new CostTrackingPrimitive"

Copilot: "I'll design the interface and write docs"
→ Creates PRIMITIVES_CATALOG.md entry
→ Creates example usage in docs/

User: "@cline Implement CostTrackingPrimitive based on Copilot's spec"
→ Cline reads docs
→ Implements primitive
→ Adds tests
→ Updates examples

[Both working in parallel, user reviews both]
```

### Handoff Pattern: Cline → Copilot

**Example: Review Cline's Work**

```markdown
## After Cline completes implementation

User: "@workspace #tta-pr-review Review the CachePrimitive changes Cline made"

Copilot:
- Reads git diff
- Checks test coverage
- Validates type hints
- Reviews against TTA.dev patterns
- Provides feedback:

"Cline's implementation looks good! A few suggestions:
1. Add docstring example for TTL parameter
2. Consider edge case when max_size=0
3. Add metric for eviction count
4. Great job on 100% test coverage ✅"

User: "@cline Please address Copilot's feedback"

[Cline makes updates]
```

### Custom Copilot Toolset for Cline Collaboration

**Create `#tta-cline` Toolset:**

```jsonc
// .vscode/copilot-toolsets.jsonc
{
  "tta-cline": {
    "tools": [
      "search",
      "read_file",
      "problems",
      "think",
      "todos",
      "run_in_terminal",
      "get_errors"
      // Note: Cline invoked manually, not as a tool
    ],
    "description": "TTA.dev development with Cline collaboration support",
    "icon": "robot"
  }
}
```

**Usage:**

```plaintext
@workspace #tta-cline

"I need to refactor RouterPrimitive. Can you analyze what needs to change
and prepare a task for Cline?"
```

---

## CLI Usage

### Cline CLI Basics

**Command Structure:**

```bash
cline [command] [options] [message]

# Shortcuts
cline           # Interactive mode
cline "task"    # One-shot task
cline -y "task" # Autonomous (no approvals)
```

**Common Commands:**

```bash
# Start interactive session
cline

# Send a task
cline "Add logging to RetryPrimitive"

# Autonomous mode (auto-approve)
echo "Fix all ruff errors" | cline -y

# Send to existing task
cline task send "Now add tests for that"

# Approve current action
cline task approve

# Deny current action
cline task deny

# View task status
cline task status
```

### Piping Context to Cline

**Powerful Pattern for Scripting:**

```bash
# Pipe file content
cat platform/primitives/src/cache.py | \
  cline task send "Add comprehensive docstrings to this code"

# Pipe git diff
git diff main..feature-branch | \
  cline task send "Review this diff and suggest improvements"

# Pipe validation output
./scripts/validate-package.sh tta-dev-primitives | \
  cline task send "Fix all issues found in this validation report"

# Pipe test results
uv run pytest --tb=short 2>&1 | \
  cline task send "Fix all failing tests shown in this output"
```

### Scripting with Cline CLI

**Example Script:**

```bash
#!/bin/bash
# scripts/cline/auto-review-pr.sh

PR_NUMBER=$1

if [ -z "$PR_NUMBER" ]; then
  echo "Usage: $0 <PR_NUMBER>"
  exit 1
fi

# Gather PR context
PR_INFO=$(gh pr view $PR_NUMBER --json title,body,comments)
PR_DIFF=$(gh pr diff $PR_NUMBER)

# Send to Cline for review
cat << EOF | cline task send
Review this pull request:

PR Info:
$PR_INFO

Diff:
$PR_DIFF

Please:
1. Check for code quality issues
2. Verify tests are included
3. Check documentation updates
4. Suggest improvements
5. Provide approval recommendation
EOF

echo "Cline is reviewing PR #$PR_NUMBER"
```

**Usage:**

```bash
./scripts/cline/auto-review-pr.sh 42
```

---

## GitHub Actions

### Cline in CI/CD

**Use Cases:**

- Automated PR reviews
- Code quality fixes
- Documentation generation
- Test generation
- Dependency updates

### Basic GitHub Actions Workflow

**`.github/workflows/cline-pr-review.yml`:**

```yaml
name: Cline PR Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  cline-review:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install Cline CLI
        run: npm install -g @cline/cli

      - name: Configure Cline
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cline config set api-provider anthropic
          cline config set api-key $ANTHROPIC_API_KEY
          cline config set api-model-id claude-3-5-sonnet-20241022

      - name: Get PR Details
        id: pr
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          PR_NUMBER=${{ github.event.pull_request.number }}

          # Get PR info
          gh pr view $PR_NUMBER --json title,body > pr_info.json

          # Get diff
          gh pr diff $PR_NUMBER > pr_diff.txt

          # Get files changed
          gh pr view $PR_NUMBER --json files | jq -r '.files[].path' > files.txt

      - name: Review with Cline
        run: |
          cat << 'EOF' | cline -y
          Review this Pull Request and provide detailed feedback.

          PR Info:
          $(cat pr_info.json)

          Files Changed:
          $(cat files.txt)

          Diff:
          $(cat pr_diff.txt)

          Please analyze for:
          1. Code quality and patterns
          2. Test coverage
          3. Documentation completeness
          4. Potential bugs or issues
          5. TTA.dev best practices compliance

          Provide a summary with:
          - Overall assessment
          - Specific issues found
          - Recommendations
          - Approval/changes needed decision
          EOF

      - name: Post Review Comment
        if: success()
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          # Extract Cline's review from task output
          # (This would need custom handling based on Cline output format)

          # Post as PR comment
          gh pr comment ${{ github.event.pull_request.number }} \
            --body "## Cline Review\n\n$(cat cline_review.txt)"
```

### Advanced: Automated Fixes

**`.github/workflows/cline-auto-fix.yml`:**

```yaml
name: Cline Auto-Fix Issues

on:
  workflow_dispatch:
    inputs:
      issue_type:
        description: 'Type of issue to fix'
        required: true
        type: choice
        options:
          - ruff-errors
          - type-hints
          - documentation
          - tests

jobs:
  auto-fix:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh

      - name: Setup Cline
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          npm install -g @cline/cli
          cline config set api-provider anthropic
          cline config set api-key $ANTHROPIC_API_KEY

      - name: Run Validation
        id: validate
        run: |
          case "${{ inputs.issue_type }}" in
            ruff-errors)
              uv run ruff check . > issues.txt 2>&1 || true
              ;;
            type-hints)
              uvx pyright packages/ > issues.txt 2>&1 || true
              ;;
            documentation)
              python scripts/docs/check_md.py --all > issues.txt 2>&1 || true
              ;;
            tests)
              uv run pytest --tb=short > issues.txt 2>&1 || true
              ;;
          esac

      - name: Fix with Cline
        run: |
          cat issues.txt | cline -y task send \
            "Fix all ${{ inputs.issue_type }} shown in this validation output.
             Follow TTA.dev coding standards."

      - name: Verify Fixes
        run: |
          # Re-run validation
          case "${{ inputs.issue_type }}" in
            ruff-errors)
              uv run ruff check .
              ;;
            type-hints)
              uvx pyright packages/
              ;;
          esac

      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: "fix: Auto-fix ${{ inputs.issue_type }} via Cline"
          title: "Auto-fix: ${{ inputs.issue_type }}"
          body: |
            ## Automated Fix via Cline

            **Issue Type:** ${{ inputs.issue_type }}

            **Changes:** Cline automatically fixed issues found during validation.

            **Verification:** All checks passing ✅

            **Review:** Please verify the changes align with TTA.dev standards.
          branch: cline/auto-fix-${{ inputs.issue_type }}
```

---

## Workflows

### Pre-built Workflow Templates

**Create in `docs/integrations/cline-workflows/`:**

#### 1. PR Review Workflow

**File: `pr-review.md`**

```markdown
# Cline PR Review Workflow

When I paste a PR number, please:

1. Fetch PR details: `gh pr view {PR_NUMBER} --json title,body,comments,files`
2. Get the diff: `gh pr diff {PR_NUMBER}`
3. Analyze:
   - Code quality and patterns
   - Test coverage (should be 100%)
   - Type hints completeness
   - Documentation updates
   - TTA.dev best practices compliance
4. Check for:
   - Breaking changes
   - Security issues
   - Performance concerns
5. Provide summary with:
   - Overall assessment (Approve/Changes Needed/Reject)
   - Specific issues found (with line numbers)
   - Recommendations
6. Ask if I want you to post the review

Let's start! What's the PR number?
```

**Usage:**

```plaintext
In Cline chat:
1. Type: /pr-review.md
2. Enter: "42" (PR number)
3. Cline executes workflow
```

#### 2. Create New Primitive Workflow

**File: `new-primitive.md`**

```markdown
# Create New TTA.dev Primitive

I'll guide you through creating a new primitive. First, I need:

1. Primitive name (e.g., "RateLimitPrimitive")
2. Category (recovery/performance/orchestration/core)
3. Brief description
4. Input/output types

Then I will:

1. Create primitive file in correct package location
2. Implement base structure with:
   - Proper type hints
   - InstrumentedPrimitive base class
   - Docstring with examples
   - _execute_impl method
3. Create comprehensive tests:
   - Success cases
   - Error cases
   - Edge cases
   - 100% coverage
4. Add to PRIMITIVES_CATALOG.md
5. Create example usage in examples/
6. Update package README.md

Let's start! What primitive do you want to create?
```

#### 3. Refactoring Workflow

**File: `refactor.md`**

```markdown
# Safe Refactoring Workflow

For large refactorings, I'll follow this process:

1. **Analysis Phase:**
   - Scan all files that will be affected
   - Identify dependencies
   - Check for breaking changes
   - Estimate scope

2. **Planning Phase:**
   - Create refactoring plan
   - Identify test files to update
   - List documentation updates needed
   - Get your approval on plan

3. **Execution Phase:**
   - Make changes incrementally
   - Run tests after each major change
   - Show diffs for review
   - Pause for approval at checkpoints

4. **Validation Phase:**
   - Run full test suite
   - Verify type checking passes
   - Check documentation
   - Run validation scripts

5. **Finalization:**
   - Update CHANGELOG if needed
   - Generate commit message
   - Confirm everything ready

What would you like to refactor?
```

### Slash Commands

**Cline supports custom slash commands:**

**Create: `.vscode/cline/workflows/`**

```markdown
<!-- /pr-review -->
# Include pr-review.md content here
```

**Usage:**

```plaintext
In Cline:
/pr-review
42
```

---

## Troubleshooting

### Common Issues

#### 1. MCP Servers Not Detected

**Symptoms:**

- Cline doesn't see Context7, Grafana, etc.
- MCP tab shows no servers

**Solutions:**

```bash
# Check MCP config exists
cat ~/.config/mcp/mcp_settings.json

# Verify servers configured
code ~/.config/mcp/mcp_settings.json

# Reload Cline
# In VS Code: Cmd+Shift+P → "Developer: Reload Window"

# Check Cline logs
# View → Output → Select "Cline" from dropdown
```

#### 2. API Key Invalid

**Symptoms:**

- "API key invalid" error
- Authentication failures

**Solutions:**

```bash
# Verify API key format
# Anthropic: starts with "sk-ant-"
# OpenAI: starts with "sk-"

# Re-enter in Cline settings
# Settings → API Configuration → Re-enter key

# Test with simple prompt
"Hello, can you hear me?"
```

#### 3. Terminal Integration Not Working

**Symptoms:**

- Cline can't execute commands
- Terminal shows no output

**Solutions:**

```bash
# Check VS Code shell integration
echo $VSCODE_SHELL_INTEGRATION  # Should be "1"

# Enable in settings
code ~/.config/Code/User/settings.json

# Add:
{
  "terminal.integrated.shellIntegration.enabled": true
}

# Restart VS Code
```

#### 4. Changes Not Applying

**Symptoms:**

- Cline shows diff but file unchanged
- "Save" button not working

**Solutions:**

1. Check file permissions: `ls -la path/to/file`
2. Verify file not open in another editor
3. Check git status: `git status`
4. Try manual approval in diff view

#### 5. High API Costs

**Symptoms:**

- Unexpected charges
- Budget exceeded

**Solutions:**

```bash
# Check Cline usage stats
# Settings → Usage → View costs

# Switch to cheaper model
# Settings → Model → Select GPT-3.5-turbo or local

# Set budget alerts
# (Provider dashboard: Anthropic Console, OpenAI Dashboard)

# Use local model for simple tasks
# Settings → Provider → Ollama
```

---

## Best Practices

### 1. Always Review Diffs

- ✅ DO read every file change before approving
- ✅ DO run tests after Cline changes
- ✅ DO use version control
- ❌ DON'T blindly approve multi-file changes

### 2. Use Appropriate Models

- **Complex tasks:** Claude 3.7 Sonnet, GPT-4
- **Simple tasks:** GPT-3.5, local models
- **Cost-sensitive:** Ollama (free, local)

### 3. Leverage MCP Servers

```plaintext
"Using Context7, find the latest FastAPI async patterns,
then implement them in our API routes"
```

### 4. Collaborate with Copilot

- Plan with Copilot
- Execute with Cline
- Review with Copilot
- Iterate together

### 5. Monitor Usage

```bash
# Weekly usage check
cline stats show

# Set monthly budget
cline config set monthly-budget 100
```

---

## Next Steps

1. ✅ Complete installation
2. ✅ Run first task
3. ✅ Test MCP integration
4. ✅ Try Copilot → Cline handoff
5. ✅ Create first workflow
6. ✅ Set up GitHub Actions (optional)
7. ✅ Share learnings with team

---

## Resources

- **Cline Documentation:** <https://github.com/cline/cline>
- **TTA.dev MCP Servers:** [MCP_SERVERS.md](../../MCP_SERVERS.md)
- **Copilot Toolsets:** [.vscode/copilot-toolsets.jsonc](../../.vscode/copilot-toolsets.jsonc)
- **Workflow Templates:** [docs/integrations/cline-workflows/](./cline-workflows/)

---

**Ready to collaborate with Cline! 🤖🤝🚀**
