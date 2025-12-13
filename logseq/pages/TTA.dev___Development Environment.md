---
type: infrastructure
category: development-environment
tags: zsh, shell, configuration, automation
created: 2025-11-10
---

# TTA.dev Development Environment

## Overview

The TTA.dev development environment is optimized for AI-powered workflows with clear boundaries between agent-managed and user-controlled settings.

## Zsh Configuration

### Architecture

**Two-File System:**
- `~/.zshrc` - Agent-managed configuration
  - Oh My Zsh setup and plugin loading
  - Standard aliases and functions
  - Tool integrations (fzf, zoxide, gh)
  - Performance optimizations

- `~/.zsh_local` - User-only settings
  - API keys and secrets
  - Personal aliases
  - Machine-specific settings
  - **NEVER touched by agents**

### Security Model

| File | Agent Access | Git Tracked | Contains |
|------|-------------|-------------|----------|
| `~/.zshrc` | ✅ Read/Write | Template only | Config, aliases |
| `~/.zsh_local` | ❌ No Access | ❌ NEVER | Secrets, personal |
| `~/.p10k.zsh` | ✅ Read-only | Optional | Prompt config |

### Essential Plugins

- [[zsh-autosuggestions]] - Command suggestions from history
- [[zsh-syntax-highlighting]] - Real-time validation
- [[fzf]] - Fuzzy finder (Ctrl+R, Ctrl+T, Alt+C)
- [[zoxide]] - Smart directory jumping (`z` command)
- [[GitHub CLI]] - `gh` for automation

### Performance

**Target:** <200ms startup time

**Optimizations:**
- Lazy loading for version managers (nvm, pyenv)
- Minimal plugin set (only essentials)
- Efficient history settings (50k lines, dedup)
- Powerlevel10k instant prompt

**Profiling:**
```bash
profile-zsh  # Check startup time
time zsh -i -c exit  # Detailed timing
```

## Setup Scripts

### Installation

```bash
# 1. Install plugins
./scripts/setup_zsh_environment.sh

# 2. Apply configuration
./scripts/apply_zsh_config.sh

# 3. Configure prompt
p10k configure

# 4. Add secrets to ~/.zsh_local
vim ~/.zsh_local
```

### Files

- `scripts/setup_zsh_environment.sh` - Plugin installer
- `scripts/apply_zsh_config.sh` - Config deployment
- `scripts/zshrc.template` - Agent-managed template
- `scripts/zsh_local.template` - User settings template

## TTA.dev Aliases

### Project Commands

```bash
ur    # uv run
ua    # uv add
us    # uv sync --all-extras
ut    # uv run pytest -v
uf    # uv run ruff format .
ul    # uv run ruff check . --fix
uq    # Full quality check
```

### Git & GitHub

```bash
g     # git
gs    # git status
ga    # git add
gc    # git commit -m
gp    # git push
gpr   # gh pr
gi    # gh issue
```

### AI Functions

```bash
explain    # Explain last command
suggest    # Get command suggestion
```

## Documentation

- [[docs/guides/zsh-setup-guide.md]] - Full setup guide
- [[docs/guides/zsh-quick-reference.md]] - Quick reference

## Related

- [[TTA.dev/TODO Architecture]] - Development workflows
- [[Agent Skills Development]] - Agent capabilities
- [[TTA.dev/Packages]] - Package development

## Maintenance

### Weekly

```bash
omz update                    # Update Oh My Zsh
profile-zsh                   # Check performance
show-plugins                  # Review active plugins
```

### Monthly

```bash
# Update custom plugins
cd ~/.oh-my-zsh/custom/plugins/zsh-autosuggestions
git pull

cd ~/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting
git pull

cd ~/.oh-my-zsh/custom/themes/powerlevel10k
git pull
```

## TODOs

{{query (and [[TTA.dev/Development Environment]] (task TODO))}}

## Completed

{{query (and [[TTA.dev/Development Environment]] (task DONE))}}


---
**Logseq:** [[TTA.dev/Logseq/Pages/Tta.dev___development environment]]
