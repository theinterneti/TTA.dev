# TTA.dev Secrets Quick Reference

**One-page guide for common secrets management tasks**

---

## 📍 Locations

- **Master secrets:** `~/.env.tta-dev`
- **Workspace links:** `~/repos/TTA.dev-copilot/.env` (and `.augment/.env`, `.cline/.env`)
- **Documentation:** `docs/SECRETS_MANAGEMENT.md`
- **Setup script:** `scripts/setup-secrets.sh`

---

## 🚀 Quick Start

```bash
# One-time setup
./scripts/setup-secrets.sh

# Verify
python3 -c "from tta_secrets import get_env; print(get_env('ENVIRONMENT'))"
```

---

## 💻 Python Usage

```python
from tta_secrets import get_env, require_env

# Optional value (returns None if not set)
api_key = get_env('GEMINI_API_KEY')

# Required value (raises ValueError if not set)
required = require_env('OPENAI_API_KEY')
```

---

## 🔑 Common Secrets

| Variable | Purpose | Example |
|----------|---------|---------|
| `GEMINI_API_KEY` | Google Gemini API | `AIza...` |
| `OPENAI_API_KEY` | OpenAI GPT API | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic Claude | `sk-ant-...` |
| `GITHUB_PERSONAL_ACCESS_TOKEN` | GitHub API | `ghp_...` or `github_pat_...` |
| `E2B_API_KEY` | E2B Code Execution | `e2b_...` |
| `OPENROUTER_API_KEY` | OpenRouter | `sk-or-v1-...` |

---

## 🛠️ Common Tasks

### Update Secret

```bash
# Edit master file
nano ~/.env.tta-dev

# Changes apply to all workspaces automatically
```

### Add New Secret

```bash
# Add to ~/.env.tta-dev
echo "NEW_SECRET=value" >> ~/.env.tta-dev

# Use in Python (force reload)
from tta_secrets import EnvLoader
EnvLoader.load(force=True)
value = get_env('NEW_SECRET')
```

### Check What's Loaded

```bash
python3 -c "from tta_secrets import EnvLoader; print(f'Loaded: {EnvLoader.is_loaded()}')"
```

### Fix Broken Symlink

```bash
cd ~/repos/TTA.dev-copilot
rm .env
ln -s ~/.env.tta-dev .env
```

---

## 🔒 Security Rules

- ✅ **DO:** Store secrets in `~/.env.tta-dev`
- ✅ **DO:** Use symlinks for workspaces
- ✅ **DO:** Add `.env*` to `.gitignore`
- ❌ **DON'T:** Commit `.env` files
- ❌ **DON'T:** Hardcode secrets in code
- ❌ **DON'T:** Log secret values

---

## 🩹 Troubleshooting

| Problem | Solution |
|---------|----------|
| Secret not found | Check `~/.env.tta-dev` has the variable |
| Import error | Run `uv sync --all-extras` |
| Old value showing | Use `EnvLoader.load(force=True)` |
| Symlink broken | Run `./scripts/setup-secrets.sh` |

---

## 📚 Full Documentation

See `docs/SECRETS_MANAGEMENT.md` for comprehensive guide.

---

**Last Updated:** November 12, 2025
