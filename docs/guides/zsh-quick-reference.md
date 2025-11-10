# Zsh Quick Reference - TTA.dev

**Essential commands and shortcuts for AI-powered development**

## 🚀 Quick Actions

```bash
# Setup
./scripts/setup_zsh_environment.sh    # Install plugins
cp scripts/zshrc.template ~/.zshrc    # Apply config
cp scripts/zsh_local.template ~/.zsh_local  # User settings
p10k configure                         # Configure prompt

# Maintenance
reload                                 # Reload Zsh config
profile-zsh                            # Check startup time
show-plugins                           # List active plugins
omz update                             # Update Oh My Zsh
```

## ⌨️ Key Bindings

| Keys | Action | Tool |
|------|--------|------|
| `Ctrl+R` | Search command history | fzf |
| `Ctrl+T` | Search files | fzf |
| `Alt+C` | Search directories | fzf |
| `ESC ESC` | Prepend sudo to command | Oh My Zsh |

## 🎯 Navigation

```bash
# Smart cd
z TTA        # Jump to ~/repos/TTA.dev
zi           # Interactive directory selection

# Quick navigation
..           # cd ..
...          # cd ../..
....         # cd ../../..

# Directory operations
mkcd new-dir # Create and cd into directory
```

## 📁 File Operations

```bash
# Listing
l            # ls -lFh
la           # ls -lAFh (include hidden)
ll           # ls -alFh

# Search
ff "*.py"    # Find files by name
fd "tests"   # Find directories by name
hs "pytest"  # Search command history

# Archive
extract archive.tar.gz   # Extract any archive
backup file.txt          # Create timestamped backup
```

## 🔀 Git & GitHub

```bash
# Git shortcuts
g            # git
gs           # git status
ga           # git add
gc           # git commit -m
gp           # git push
gl           # git pull
gd           # git diff
gco          # git checkout
gb           # git branch

# GitHub CLI
gpr          # gh pr (Pull Requests)
gi           # gh issue (Issues)
gr           # gh repo (Repositories)

# Examples
gh pr list
gh pr view 123
gh issue create
```

## 🤖 AI Integration

```bash
# Copilot commands (requires: gh extension install github/gh-copilot)
explain      # Explain last command
suggest "search for large files"   # Get command suggestion

# Examples
ls -la
explain      # AI explains what ls -la does
```

## 🏗️ TTA.dev Project

```bash
ur           # uv run
ua           # uv add <package>
us           # uv sync --all-extras
ut           # uv run pytest -v
uf           # uv run ruff format .
ul           # uv run ruff check . --fix
uq           # Full quality check (format + lint + type + test)
```

## 🔍 Fuzzy Finding (fzf)

```bash
# Basic usage
Ctrl+R       # Search history interactively
Ctrl+T       # Insert file path
Alt+C        # cd into directory

# Piping
cat $(fzf)   # Select file, then cat it
vim $(fzf)   # Select file, then edit it
```

## ⚙️ Configuration

```bash
# Files
~/.zshrc              # Agent-managed config
~/.zsh_local          # User-only (secrets!)
~/.p10k.zsh           # Prompt config

# Edit
vim ~/.zshrc          # Shared settings
vim ~/.zsh_local      # Personal settings (NEVER commit!)

# Safety
echo ".zsh_local" >> ~/.gitignore  # Protect secrets
```

## 🎨 Customization

### Add Plugin

Edit `~/.zshrc`:
```bash
plugins=(
  git
  # ... existing ...
  docker              # Add here
  zsh-syntax-highlighting  # Keep last!
)
```

### Add Alias

**Shared** (in `~/.zshrc`):
```bash
alias myalias='command'
```

**Personal** (in `~/.zsh_local`):
```bash
alias secret='private-command'
export API_KEY="secret"
```

## 🔒 Security

### ✅ Safe for Git

- `~/.zshrc` - Configuration
- `scripts/zshrc.template` - Template
- `docs/guides/zsh-setup-guide.md` - Documentation

### ❌ NEVER Commit

- `~/.zsh_local` - Contains secrets!
- Add to `.gitignore`

## 🐛 Troubleshooting

```bash
# Plugin not working
reload              # Reload config
exec zsh            # Restart shell

# Slow startup
profile-zsh         # Check time (<200ms goal)

# Reset prompt
p10k configure      # Reconfigure

# Check installations
which fzf zoxide gh
show-plugins
```

## 📊 Performance

```bash
# Profile startup
time zsh -i -c exit

# Target: <200ms

# Common slowdowns (already optimized):
# ✅ nvm - lazy loaded
# ✅ pyenv - lazy loaded
# ✅ minimal plugins
```

## 💡 Pro Tips

```bash
# 1. Use fzf for everything
vim $(fzf)           # Quick file editing
cd $(fd -t d | fzf)  # Quick directory jump

# 2. Combine with zoxide
z proj               # Jump to project
vim $(fzf)           # Edit file there

# 3. Use aliases
uq                   # Full quality check
gpr list             # List PRs

# 4. AI assistance
suggest "compress all logs"
explain              # After any command
```

## 🔗 More Info

- **Full Guide:** `docs/guides/zsh-setup-guide.md`
- **Setup Script:** `scripts/setup_zsh_environment.sh`
- **Templates:** `scripts/zshrc.template`, `scripts/zsh_local.template`

---

**Last Updated:** November 10, 2025
