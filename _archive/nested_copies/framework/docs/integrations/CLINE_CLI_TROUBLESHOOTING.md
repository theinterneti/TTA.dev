# Cline CLI Troubleshooting Guide

**Getting Cline CLI Working with TTA.dev**

**Date:** November 6, 2025
**Status:** Active Troubleshooting

---

## Quick Diagnosis

### VS Code Extension: ✅ Working

Your Cline VS Code extension is responding well with:
- DeepSeek R1 (Plan mode)
- Llama 4 Scout (Act mode)
- OpenRouter provider

### CLI: ⚠️ Needs Configuration

The CLI is installed but may need additional setup to work properly with TTA.dev.

---

## Step-by-Step CLI Configuration

### 1. Verify Installation

```bash
# Check CLI is installed
which cline
# Should show: /home/thein/.nvm/versions/node/vXX.XX.X/bin/cline (or similar)

# Check version
cline --version
# Should show version number
```

### 2. Check Current Configuration

```bash
# List all current settings
cline config list

# Should show your settings like:
# api-provider: openrouter
# api-key: sk-or-v1-...
# api-model-id: mistralai/mistral-small-3.2
```

**If output is empty or shows errors:** Configuration needs to be set up.

### 3. Configure for OpenRouter (Recommended)

**Option A: Interactive Setup**

```bash
# Start interactive authentication wizard
cline auth

# Follow prompts:
# 1. Select "OpenRouter"
# 2. Enter your API key: sk-or-v1-YOUR_KEY_HERE
# 3. Confirm
```

**Option B: Direct Configuration**

```bash
# Set provider
cline config set api-provider openrouter

# Set API key (same as VS Code extension)
cline config set api-key YOUR_OPENROUTER_KEY

# Set model
cline config set api-model-id mistralai/mistral-small-3.2

# Verify
cline config list
```

### 4. Test CLI

```bash
# Simple test
cline "Hello, can you confirm you're working?"

# Should respond with a message from Mistral Small 3.2
```

**Expected Output:**
```
Cline CLI v1.x.x
Model: mistralai/mistral-small-3.2
Provider: OpenRouter

> Hello! Yes, I'm working properly. How can I help you?
```

**If you see errors:** Continue to troubleshooting section below.

---

## Common Issues & Solutions

### Issue 1: "API key invalid" or "Authentication failed"

**Symptoms:**
```
Error: API authentication failed
```

**Solutions:**

```bash
# 1. Verify key format
echo $OPENROUTER_API_KEY
# Should start with: sk-or-v1-

# 2. Re-enter key
cline config set api-key sk-or-v1-YOUR_FULL_KEY_HERE

# 3. Test with simple prompt
cline "test"
```

**Get your OpenRouter API key:**
1. Go to https://openrouter.ai
2. Navigate to "Keys" section
3. Copy your existing key OR create new one
4. Use in CLI: `cline config set api-key <key>`

### Issue 2: "Model not found" or "Model unavailable"

**Symptoms:**
```
Error: Model 'mistralai/mistral-small-3.2' not available
```

**Solutions:**

```bash
# Check available models at OpenRouter
# Visit: https://openrouter.ai/models

# Try alternative model
cline config set api-model-id deepseek/deepseek-r1

# Or use free model
cline config set api-model-id meta-llama/llama-3.2-3b-instruct:free
```

**Good CLI Models (OpenRouter):**

| Model | Cost | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `mistralai/mistral-small-3.2` | $ | ⚡⚡⚡ | ⭐⭐⭐⭐ | General CLI |
| `deepseek/deepseek-r1` | $ | ⚡⚡ | ⭐⭐⭐⭐⭐ | Complex tasks |
| `meta-llama/llama-3.2-3b-instruct:free` | Free | ⚡⚡⚡ | ⭐⭐⭐ | Testing |

### Issue 3: CLI not recognizing commands

**Symptoms:**
```bash
cline config list
# bash: cline: command not found
```

**Solutions:**

```bash
# 1. Reinstall CLI globally
npm install -g cline

# 2. Verify npm global bin directory in PATH
npm config get prefix
# Should show: /home/thein/.nvm/versions/node/vXX.XX.X

# 3. Check PATH includes npm bin
echo $PATH | grep npm
# Should see npm bin directory

# 4. If not in PATH, add to ~/.bashrc
echo 'export PATH="$HOME/.nvm/versions/node/$(nvm current)/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 5. Verify
which cline
```

### Issue 4: Different configuration than VS Code extension

**Symptoms:**
- VS Code extension works
- CLI doesn't work or uses different model

**Explanation:**

The CLI and VS Code extension use **separate configurations**:

- **VS Code Extension:** Settings stored in VS Code settings/GUI
- **CLI:** Configuration in `~/.clinerc` file

**Solutions:**

```bash
# View CLI config file
cat ~/.clinerc

# Should contain:
# api-provider=openrouter
# api-key=sk-or-v1-...
# api-model-id=mistralai/mistral-small-3.2

# Manually edit if needed
nano ~/.clinerc

# Or reconfigure via commands
cline config set api-provider openrouter
cline config set api-key YOUR_KEY
cline config set api-model-id mistralai/mistral-small-3.2
```

### Issue 5: Permission errors

**Symptoms:**
```
Error: EACCES: permission denied
```

**Solutions:**

```bash
# Fix npm global permissions
mkdir -p ~/.npm-global
npm config set prefix ~/.npm-global

# Add to PATH
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# Reinstall CLI
npm install -g cline
```

### Issue 6: Node.js version too old

**Symptoms:**
```
Error: Unsupported engine
```

**Requirements:**
- Node.js 20+ required

**Solutions:**

```bash
# Check Node version
node --version
# Should be v20.x.x or higher

# If too old, update Node.js
# Using nvm:
nvm install 20
nvm use 20
nvm alias default 20

# Reinstall CLI
npm install -g cline
```

---

## Configuration File Locations

### CLI Configuration

```bash
# Main config file
~/.clinerc

# Example contents:
# api-provider=openrouter
# api-key=sk-or-v1-...
# api-model-id=mistralai/mistral-small-3.2
```

### Task History

```bash
# CLI task history
~/.cline/history/

# List previous tasks
ls -la ~/.cline/history/
```

### Instance Registry

```bash
# Running instances
~/.cline/instances.json

# View
cat ~/.cline/instances.json
```

---

## Advanced Configuration

### Use Environment Variables

```bash
# Set in ~/.bashrc or ~/.zshrc
export CLINE_API_PROVIDER=openrouter
export CLINE_API_KEY=sk-or-v1-...
export CLINE_API_MODEL_ID=mistralai/mistral-small-3.2

# Reload shell
source ~/.bashrc

# CLI will use these if ~/.clinerc not found
```

### Custom Cline Directory

```bash
# Override default ~/.cline directory
export CLINE_DIR=/custom/path/.cline

# Useful for:
# - Testing different configurations
# - Team shared settings
# - CI/CD environments
```

### Set Model for Specific Task

```bash
# Override model for single task
cline --setting api-model-id deepseek/deepseek-r1 "Complex task here"

# Or using short form
cline -s api-model-id deepseek/deepseek-r1 "Task"
```

---

## Testing Your Configuration

### Test 1: Simple Echo

```bash
cline "Echo back: TTA.dev CLI is working!"

# Expected: Response echoing the message
```

### Test 2: Code Generation

```bash
cline "Write a Python function that adds two numbers"

# Expected: Python code with proper syntax
```

### Test 3: File Operations

```bash
cd /tmp
cline "Create a file called test.txt with 'Hello TTA.dev'"

# Check file created
cat test.txt
# Should show: Hello TTA.dev
```

### Test 4: Piping Input

```bash
echo "Summarize this: TTA.dev is awesome" | cline

# Expected: Summary response
```

### Test 5: Autonomous Mode

```bash
cline -y "List files in current directory"

# Should execute without asking for approval
```

---

## Verifying Your Setup

**Run this verification script:**

```bash
#!/bin/bash
echo "=== Cline CLI Verification ==="
echo ""

echo "1. CLI Installation:"
which cline && echo "✅ CLI found" || echo "❌ CLI not found"
echo ""

echo "2. Version:"
cline --version
echo ""

echo "3. Configuration:"
cline config list
echo ""

echo "4. Config File:"
cat ~/.clinerc 2>/dev/null || echo "⚠️  No config file found"
echo ""

echo "5. Test API Connection:"
echo "Testing with simple prompt..."
timeout 10 cline "Say hello" && echo "✅ API working" || echo "❌ API connection failed"
```

**Save as:** `verify-cline-cli.sh`

**Run:**
```bash
chmod +x verify-cline-cli.sh
./verify-cline-cli.sh
```

---

## Expected Working Configuration

### For TTA.dev Development

**~/.clinerc:**
```ini
api-provider=openrouter
api-key=sk-or-v1-YOUR_KEY_HERE
api-model-id=mistralai/mistral-small-3.2
```

**Verification:**
```bash
cline config list

# Output should match:
api-provider: openrouter
api-key: sk-or-v1-****** (hidden)
api-model-id: mistralai/mistral-small-3.2
```

---

## Getting Help

### Enable Verbose Output

```bash
# See detailed logs
cline --verbose "test task"

# Or short form
cline -v "test task"
```

### View Man Page

```bash
# Full CLI documentation
man cline

# Or help
cline --help
cline task --help
cline instance --help
```

### Check Logs

```bash
# CLI logs location
~/.cline/logs/

# View recent log
tail -f ~/.cline/logs/latest.log
```

---

## Next Steps After Configuration

Once CLI is working:

1. ✅ **Test Basic Commands:**
   ```bash
   cline "Hello"
   cline task list
   ```

2. ✅ **Try TTA.dev Specific Task:**
   ```bash
   cd /home/thein/repos/TTA.dev
   cline "List all primitives in packages/tta-dev-primitives/src/"
   ```

3. ✅ **Test Autonomous Mode:**
   ```bash
   echo "Add a comment to README.md" | cline -y
   ```

4. ✅ **Create Workflow Script:**
   ```bash
   # Save as scripts/cline/validate-and-fix.sh
   ./scripts/validate-package.sh tta-dev-primitives | \
     cline -y "Fix all issues shown"
   ```

5. ✅ **Set Up Aliases:**
   ```bash
   # Add to ~/.bashrc
   alias tta-review='cline "Review recent changes"'
   alias tta-fix='cline -y "Fix linting errors"'
   ```

---

## Common Workflows

### PR Review via CLI

```bash
# Get PR diff and review
gh pr diff 42 | cline "Review this PR for quality issues"
```

### Fix Validation Errors

```bash
# Pipe validation output to Cline
uv run ruff check . 2>&1 | cline -y "Fix these errors"
```

### Generate Tests

```bash
# Generate tests for file
cat packages/tta-dev-primitives/src/cache.py | \
  cline "Generate pytest tests for this code"
```

### Quick Documentation

```bash
# Document function
cline "Add docstring to CachePrimitive class in packages/tta-dev-primitives/src/cache.py"
```

---

## Resources

- **Cline CLI Docs:** https://github.com/cline/cline/blob/main/docs/cline-cli/
- **OpenRouter Models:** https://openrouter.ai/models
- **TTA.dev Cline Config:** [CLINE_CONFIGURATION_TTA.md](./CLINE_CONFIGURATION_TTA.md)
- **Integration Guide:** [CLINE_INTEGRATION_GUIDE.md](./CLINE_INTEGRATION_GUIDE.md)

---

**Need More Help?**

If you're still having issues after following this guide:

1. Check Cline CLI logs: `~/.cline/logs/latest.log`
2. Verify OpenRouter API key at https://openrouter.ai
3. Try interactive auth: `cline auth`
4. Test with free model: `cline config set api-model-id meta-llama/llama-3.2-3b-instruct:free`

---

**Configuration Complete! Ready to use Cline CLI with TTA.dev. 🚀**


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Docs/Integrations/Cline_cli_troubleshooting]]
