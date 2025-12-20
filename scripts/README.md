# Zsh Environment Setup Scripts

**Agent-Centric Shell Configuration for TTA.dev**

## Quick Start

```bash
# 1. Install plugins and tools
./setup_zsh_environment.sh

# 2. Apply configuration
./apply_zsh_config.sh

# 3. Configure prompt (run in Zsh)
zsh
p10k configure

# 4. Add your secrets
vim ~/.zsh_local
# Add: export OPENAI_API_KEY="sk-..."
#      export GITHUB_TOKEN="ghp_..."
```

## Scripts

### setup_zsh_environment.sh

**Purpose:** Install Oh My Zsh plugins and essential tools

**What it does:**
- Installs zsh-autosuggestions
- Installs zsh-syntax-highlighting
- Installs Powerlevel10k theme
- Installs fzf (fuzzy finder)
- Installs zoxide (smart cd)
- Verifies gh (GitHub CLI) is installed
- Creates backup of existing .zshrc

**Usage:**
```bash
./setup_zsh_environment.sh
```

**Prerequisites:**
- Oh My Zsh already installed
- Git installed
- curl installed

### apply_zsh_config.sh

**Purpose:** Deploy TTA.dev Zsh configuration

**What it does:**
- Backs up existing .zshrc
- Installs agent-managed .zshrc from template
- Creates user-only .zsh_local from template
- Adds .zsh_local to .gitignore
- Provides next steps

**Usage:**
```bash
./apply_zsh_config.sh
```

**Prerequisites:**
- setup_zsh_environment.sh already run
- Zsh installed

## Templates

### zshrc.template

**Agent-Managed Configuration**

Contains:
- Oh My Zsh setup
- Plugin loading (autosuggestions, syntax-highlighting)
- Tool integrations (fzf, zoxide, gh)
- Performance optimizations (lazy loading)
- TTA.dev aliases (ur, ua, us, ut, uf, ul, uq)
- AI-powered functions (explain, suggest)
- Sources ~/.zsh_local at the end

**Agent Permissions:** ✅ Read/Write

### zsh_local.template

**User-Only Settings**

Contains:
- API key placeholders
- Personal alias examples
- Machine-specific setting examples
- Custom function examples

**Agent Permissions:** ❌ No Access

**CRITICAL:** Must be in .gitignore!

## File Structure

```
TTA.dev/
├── scripts/
│   ├── setup_zsh_environment.sh    # Plugin installer
│   ├── apply_zsh_config.sh         # Config deployer
│   ├── zshrc.template              # Agent-managed config
│   └── zsh_local.template          # User-only settings
├── docs/guides/
│   ├── zsh-setup-guide.md          # Full documentation
│   └── zsh-quick-reference.md      # Quick reference
└── ZSH_ENVIRONMENT_IMPLEMENTATION_COMPLETE.md  # Summary

User's home directory:
~/.zshrc              # Installed from zshrc.template
~/.zsh_local          # Installed from zsh_local.template
~/.p10k.zsh           # Created by p10k configure
~/.gitignore          # Contains .zsh_local
```

## Security Model

### Agent Boundaries

| File | Agent Access | Git | Purpose |
|------|-------------|-----|---------|
| `~/.zshrc` | ✅ Read/Write | Template | Configuration |
| `~/.zsh_local` | ❌ No Access | ❌ NEVER | Secrets |
| `~/.p10k.zsh` | ✅ Read-only | Optional | Prompt |

### Best Practices

1. **All secrets go in .zsh_local**
2. **Never commit .zsh_local to git**
3. **Review agent changes to .zshrc**
4. **Keep backups** (scripts create automatic backups)

## Essential Aliases

### TTA.dev Project

```bash
ur    # uv run
ua    # uv add <package>
us    # uv sync --all-extras
ut    # uv run pytest -v
uf    # uv run ruff format .
ul    # uv run ruff check . --fix
uq    # Full quality check
```

### Git & GitHub

```bash
g, gs, ga, gc, gp    # Git shortcuts
gpr                  # gh pr
gi                   # gh issue
```

### Navigation

```bash
z TTA       # Jump to TTA.dev directory
..          # cd ..
...         # cd ../..
mkcd dir    # Create and cd
```

## Performance

**Target:** <200ms startup time

**Optimizations:**
- Lazy loading for nvm, pyenv
- Minimal plugin set
- Efficient history settings
- Powerlevel10k instant prompt

**Check performance:**
```bash
profile-zsh              # Quick check
time zsh -i -c exit      # Detailed
```

## AI Integration

### GitHub Copilot CLI

```bash
# Install
gh extension install github/gh-copilot

# Use
explain                           # Explain last command
suggest "search for large files"  # Get suggestion
```

### Functions

```bash
mkcd new-project          # Create directory and cd
backup important.txt      # Timestamped backup
extract archive.tar.gz    # Extract any archive
ff "*.py"                 # Find files
fd "tests"                # Find directories
```

## Troubleshooting

### Plugin not working

```bash
reload              # Reload config
exec zsh            # Restart shell
```

### Slow startup

```bash
profile-zsh         # Check time
# Should be <200ms
```

### fzf not working

```bash
# Check installation
which fzf

# Try key bindings
Ctrl+R              # History search
Ctrl+T              # File search
Alt+C               # Directory search
```

### zoxide not jumping

```bash
# zoxide needs to learn first
cd ~/repos/TTA.dev      # Visit manually a few times
cd ~/repos/TTA.dev/packages

# Then use
z TTA               # Jump to TTA.dev
```

## Documentation

- **Full Guide:** `../docs/guides/zsh-setup-guide.md`
- **Quick Reference:** `../docs/guides/zsh-quick-reference.md`
- **Summary:** `../ZSH_ENVIRONMENT_IMPLEMENTATION_COMPLETE.md`

## Testing

All scripts tested on:
- Ubuntu 24.04 (Noble)
- Zsh 5.9
- Oh My Zsh (latest)

## Support

For issues or questions:
- Check documentation in `docs/guides/`
- Review `ZSH_ENVIRONMENT_IMPLEMENTATION_COMPLETE.md`
- Open issue on GitHub

---

**Last Updated:** November 10, 2025
**Maintained by:** TTA.dev Team
