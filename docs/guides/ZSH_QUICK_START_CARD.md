# TTA.dev Zsh - Quick Start Card

**Print this or keep it handy!**

## 🚀 First-Time Setup

```bash
cd ~/repos/TTA.dev

# 1. Install plugins
./scripts/setup_zsh_environment.sh

# 2. Apply config
./scripts/apply_zsh_config.sh

# 3. Start Zsh and configure prompt
zsh
p10k configure

# 4. Add your secrets
vim ~/.zsh_local
# Add: export OPENAI_API_KEY="sk-..."

# 5. Reload
source ~/.zshrc
```

## ⌨️ Essential Shortcuts

| Keys | Action |
|------|--------|
| `Ctrl+R` | 🔍 Search history (fzf) |
| `Ctrl+T` | 📁 Find file |
| `Alt+C` | 📂 Jump to directory |

## 🎯 Most Used Commands

### Navigation
```bash
z TTA        # Jump to TTA.dev
..           # Up one dir
...          # Up two dirs
mkcd proj    # Make dir & cd
```

### TTA.dev
```bash
us           # Sync deps
ut           # Run tests
uq           # Full quality check
```

### Git
```bash
gs           # Status
ga .         # Add all
gc "msg"     # Commit
gp           # Push
gpr list     # List PRs
```

### AI
```bash
explain      # Explain last cmd
suggest "find big files"
```

## 📁 File Locations

```
~/.zshrc       → Agent can modify
~/.zsh_local   → YOU ONLY (secrets!)
~/.p10k.zsh    → Prompt config
```

## 🔒 Security Rules

✅ **DO:**
- Put secrets in `~/.zsh_local`
- Keep `~/.zsh_local` in `.gitignore`
- Review changes to `~/.zshrc`

❌ **DON'T:**
- Commit `~/.zsh_local` to git
- Put secrets in `~/.zshrc`

## 🛠️ Maintenance

```bash
reload       # Reload config
profile-zsh  # Check speed (<200ms)
omz update   # Update Oh My Zsh
```

## 📚 More Help

- Full Guide: `docs/guides/zsh-setup-guide.md`
- Quick Ref: `docs/guides/zsh-quick-reference.md`
- Scripts: `scripts/README.md`

---
**TTA.dev Team • 2025-11-10**


---
**Logseq:** [[TTA.dev/Docs/Guides/Zsh_quick_start_card]]
