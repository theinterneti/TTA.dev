# TTA.dev Secrets Management Guide

**Centralized, intelligent secrets management across all agent workspaces**

**Last Updated:** November 12, 2025

---

## 🎯 Overview

TTA.dev uses a **centralized secrets management system** that:

- ✅ Stores all secrets in one place: `~/.env.tta-dev`
- ✅ Works across all agent workspaces (GitHub Copilot, Augment, Cline)
- ✅ Auto-loads environment variables on import
- ✅ Supports per-workspace overrides
- ✅ Never commits secrets to git

### Architecture

```
~/.env.tta-dev (centralized)
     ↓
     ├─→ TTA.dev-copilot/.env (symlink)
     ├─→ .augment/.env (symlink)
     └─→ .cline/.env (symlink)
```

**Benefits:**

- **Single source of truth** - Update once, applies everywhere
- **Workspace isolation** - Each workspace can override specific vars
- **Git-safe** - Symlinks and .env files are gitignored
- **Auto-loading** - Import `tta_secrets` and it's ready

---

## 🚀 Quick Start

### 1. Run Setup Script

```bash
cd /home/thein/repos/TTA.dev-copilot
./scripts/setup-secrets.sh
```

This will:

1. Copy `.env` from recovered location to `~/.env.tta-dev`
2. Create symlinks in all workspaces
3. Update `.gitignore` files
4. Verify Python imports work

### 2. Verify Setup

```bash
# Check centralized .env exists
ls -la ~/.env.tta-dev

# Check workspace symlinks
ls -la ~/repos/TTA.dev-copilot/.env
ls -la ~/repos/TTA.dev-copilot/.augment/.env
ls -la ~/repos/TTA.dev-copilot/.cline/.env

# Test Python import
python3 -c "from tta_secrets import get_env; print(get_env('ENVIRONMENT'))"
```

### 3. Use in Your Code

```python
from tta_secrets import get_env, require_env

# Get optional value with default
api_key = get_env('GEMINI_API_KEY', 'default-key')

# Get required value (raises ValueError if not set)
required_key = require_env('OPENAI_API_KEY')

# Auto-loading also works with standard os.getenv
import os
github_token = os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')
```

---

## 📁 File Locations

### Centralized Configuration

| File | Purpose | Should Commit? |
|------|---------|----------------|
| `~/.env.tta-dev` | Master secrets file | ❌ Never |
| `~/recovered-tta-storytelling/.env` | Original backup | ❌ Never |

### Workspace Files

| File | Purpose | Type |
|------|---------|------|
| `TTA.dev-copilot/.env` | Symlink to `~/.env.tta-dev` | Symlink |
| `.augment/.env` | Symlink to `~/.env.tta-dev` | Symlink |
| `.cline/.env` | Symlink to `~/.env.tta-dev` | Symlink |

### Python Package

| File | Purpose |
|------|---------|
| `tta_secrets/loader.py` | Auto-loading .env functionality |
| `tta_secrets/manager.py` | Secrets validation and caching |
| `tta_secrets/__init__.py` | Public API |

---

## 🔧 Configuration

### Environment Variables Available

From your `.env.tta-dev`, you have access to:

#### AI Model APIs

```python
get_env('GEMINI_API_KEY')          # Google Gemini
get_env('OPENAI_API_KEY')          # OpenAI GPT
get_env('ANTHROPIC_API_KEY')       # Anthropic Claude
get_env('OPENROUTER_API_KEY')      # OpenRouter
```

#### Databases

```python
get_env('POSTGRES_PASSWORD')       # PostgreSQL
get_env('NEO4J_PASSWORD')          # Neo4j
get_env('REDIS_URL')               # Redis
```

#### Services

```python
get_env('GITHUB_PERSONAL_ACCESS_TOKEN')  # GitHub
get_env('E2B_API_KEY')                   # E2B Code Execution
get_env('N8N_API_KEY')                   # n8n Automation
get_env('GRAFANA_API_KEY')               # Grafana Monitoring
```

#### Security

```python
get_env('JWT_SECRET_KEY')          # JWT tokens
get_env('ENCRYPTION_KEY')          # Data encryption
```

**Full list:** See `~/.env.tta-dev` for all available variables

---

## 🎨 Usage Patterns

### Pattern 1: Simple Access

```python
from tta_secrets import get_env

api_key = get_env('GEMINI_API_KEY')
if api_key:
    # Use the API key
    client = GeminiClient(api_key=api_key)
```

### Pattern 2: Required Variables

```python
from tta_secrets import require_env

# Raises ValueError if not set
api_key = require_env('OPENAI_API_KEY')
client = OpenAIClient(api_key=api_key)
```

### Pattern 3: Workspace Override

If you need workspace-specific values:

```python
# In TTA.dev-copilot workspace only
# Create TTA.dev-copilot/.env.local (not symlink)
CUSTOM_VAR=workspace_specific_value
```

Then use:

```python
from tta_secrets import EnvLoader

# Load workspace-specific .env.local
EnvLoader.load(force=True)
value = get_env('CUSTOM_VAR')
```

### Pattern 4: Check if Loaded

```python
from tta_secrets import EnvLoader

if EnvLoader.is_loaded():
    print("Environment variables are loaded")
else:
    EnvLoader.load()
```

### Pattern 5: Manual Loading

```python
from pathlib import Path
from tta_secrets import EnvLoader

# Load from specific workspace
workspace = Path('/home/thein/repos/TTA.dev-copilot')
EnvLoader.load(workspace_root=workspace, force=True)
```

---

## 🔒 Security Best Practices

### DO ✅

- ✅ **Store secrets in `~/.env.tta-dev`** - One centralized location
- ✅ **Use symlinks for workspaces** - Automatic updates everywhere
- ✅ **Verify `.gitignore` entries** - Never commit .env files
- ✅ **Use `require_env()` for critical vars** - Fail fast if missing
- ✅ **Rotate API keys regularly** - Update `~/.env.tta-dev` and restart
- ✅ **Use strong, unique passwords** - Generate with `openssl rand -base64 32`

### DON'T ❌

- ❌ **Don't commit `.env` files** - Use `.env.example` for templates
- ❌ **Don't hardcode secrets** - Always use environment variables
- ❌ **Don't log secrets** - `tta_secrets` handles this automatically
- ❌ **Don't share `.env` files** - Each developer has their own
- ❌ **Don't use production secrets in dev** - Separate environments

---

## 🛠️ Troubleshooting

### Issue 1: Variables Not Loading

**Symptoms:** `get_env('SOME_VAR')` returns `None`

**Solutions:**

1. Check centralized .env exists:
   ```bash
   cat ~/.env.tta-dev | grep SOME_VAR
   ```

2. Check symlink is correct:
   ```bash
   ls -la ~/repos/TTA.dev-copilot/.env
   # Should show: .env -> /home/thein/.env.tta-dev
   ```

3. Force reload in Python:
   ```python
   from tta_secrets import EnvLoader
   EnvLoader.load(force=True)
   ```

### Issue 2: Symlink Broken

**Symptoms:** `.env` shows as broken symlink

**Solution:**

```bash
cd ~/repos/TTA.dev-copilot
rm .env
ln -s ~/.env.tta-dev .env
```

### Issue 3: Import Errors

**Symptoms:** `ModuleNotFoundError: No module named 'tta_secrets'`

**Solution:**

```bash
cd ~/repos/TTA.dev-copilot
uv sync --all-extras
```

### Issue 4: Variables Not Updating

**Symptoms:** Changed `~/.env.tta-dev` but Python still sees old values

**Solution:**

```python
# In Python, force reload
from tta_secrets import EnvLoader
EnvLoader.load(force=True)

# Or restart your Python process
```

### Issue 5: Git Wants to Commit .env

**Symptoms:** `git status` shows `.env` as untracked

**Solution:**

```bash
# Ensure .gitignore has these entries
cat >> .gitignore << EOF
.env
.env.local
.env.*.local
.env.backup
EOF

git add .gitignore
```

---

## 🔄 Updating Secrets

### Update Centralized Secrets

```bash
# Edit the master file
nano ~/.env.tta-dev

# Changes apply immediately to all workspaces (after reload)
```

### Verify Update

```bash
# Check new value is present
grep SOME_VAR ~/.env.tta-dev

# Test in Python
python3 -c "from tta_secrets import EnvLoader; EnvLoader.load(force=True); print(EnvLoader.get('SOME_VAR'))"
```

### Workspace-Specific Override

If you need different values per workspace:

```bash
# Create workspace-specific file
cd ~/repos/TTA.dev-copilot
cat > .env.local << EOF
CUSTOM_VAR=workspace_specific_value
EOF

# In Python, load both files
from tta_secrets import EnvLoader
EnvLoader.load()  # Loads ~/.env.tta-dev
EnvLoader.load(workspace_root=Path.cwd())  # Loads .env.local
```

---

## 📊 Maintenance

### Regular Tasks

**Weekly:**

- [ ] Review `~/.env.tta-dev` for unused variables
- [ ] Check symlinks are intact: `./scripts/setup-secrets.sh`

**Monthly:**

- [ ] Rotate critical API keys
- [ ] Update passwords for databases
- [ ] Audit access logs

**Quarterly:**

- [ ] Review all secrets for necessity
- [ ] Update encryption keys
- [ ] Backup `~/.env.tta-dev` to secure location

### Backup Strategy

```bash
# Encrypted backup
gpg --encrypt --recipient your@email.com ~/.env.tta-dev

# Store encrypted file in secure location
mv ~/.env.tta-dev.gpg ~/secure-backups/

# Restore when needed
gpg --decrypt ~/secure-backups/.env.tta-dev.gpg > ~/.env.tta-dev
```

---

## 🤝 Multi-Agent Setup

### GitHub Copilot Workspace

```bash
cd ~/repos/TTA.dev-copilot
ln -s ~/.env.tta-dev .env
```

### Augment Workspace

```bash
cd ~/repos/TTA.dev-copilot/.augment
ln -s ~/.env.tta-dev .env
```

### Cline Workspace

```bash
cd ~/repos/TTA.dev-copilot/.cline
ln -s ~/.env.tta-dev .env
```

**Or use the setup script:**

```bash
./scripts/setup-secrets.sh
```

---

## 🔗 Related Documentation

- **Setup Script:** `scripts/setup-secrets.sh` - Automated setup
- **Python Package:** `tta_secrets/` - Source code
- **Original .env:** `/home/thein/recovered-tta-storytelling/.env` - Backup

---

## 💡 Examples

### Example 1: E2B Integration

```python
from tta_secrets import require_env
from e2b_code_interpreter import CodeInterpreter

# Get API key (raises if not set)
api_key = require_env('E2B_API_KEY')

# Use in E2B client
with CodeInterpreter(api_key=api_key) as sandbox:
    result = sandbox.notebook.exec_cell("print('Hello')")
```

### Example 2: GitHub API

```python
from tta_secrets import get_env
import requests

token = get_env('GITHUB_PERSONAL_ACCESS_TOKEN')
headers = {'Authorization': f'Bearer {token}'}

response = requests.get('https://api.github.com/user', headers=headers)
```

### Example 3: Multi-Model LLM

```python
from tta_secrets import get_env

# Try multiple providers
gemini_key = get_env('GEMINI_API_KEY')
openai_key = get_env('OPENAI_API_KEY')
anthropic_key = get_env('ANTHROPIC_API_KEY')

if gemini_key:
    # Use Gemini
    llm = GeminiClient(api_key=gemini_key)
elif openai_key:
    # Fallback to OpenAI
    llm = OpenAIClient(api_key=openai_key)
else:
    raise ValueError("No LLM API key configured")
```

---

## 📞 Getting Help

**Issues?**

1. Run diagnostics: `./scripts/setup-secrets.sh`
2. Check logs for `tta_secrets` module
3. Verify file permissions: `ls -la ~/.env.tta-dev`

**Questions?**

- Check this guide first
- Review `tta_secrets/loader.py` source code
- Open an issue on GitHub

---

**Last Updated:** November 12, 2025
**Maintained by:** TTA.dev Team
**Version:** 1.1.0


---
**Logseq:** [[TTA.dev/Docs/Secrets_management]]
