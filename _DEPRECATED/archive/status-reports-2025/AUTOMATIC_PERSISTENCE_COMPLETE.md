# Automatic Persistence Setup for Future Sessions

**Date:** November 2, 2025

## 🎯 Problem Solved

You asked: *"How do we tell the next Copilot session to call this automatically?"*

**Solution:** Multiple layers of automation to ensure future Copilot sessions know to verify and set up persistence.

---

## ✅ What's Now Automatic

### 1. **VS Code Task (Runs on Workspace Open)**

A VS Code task now runs automatically when you open the TTA.dev workspace:

**Task:** `🔭 Verify Observability Setup`
**File:** `.vscode/tasks.json`
**When:** On folder open (`runOptions.runOn: "folderOpen"`)
**What it does:** Runs `./scripts/verify-and-setup-persistence.sh`

This gives you instant feedback when opening the project about whether observability is set up.

### 2. **Copilot Instructions (For AI Agents)**

Added a prominent section to `.github/copilot-instructions.md`:

```markdown
### 🔭 Observability Persistence Check (Required for Local Sessions)

**🖥️ LOCAL ONLY:** If you're the VS Code Extension, verify observability infrastructure on session start:

\`\`\`bash
./scripts/verify-and-setup-persistence.sh
\`\`\`
```

**Location:** Right after "Project Overview" (lines 52-69)
**Target audience:** VS Code Extension Copilot sessions
**Effect:** Future Copilot agents will check this on session start

### 3. **Smart Verification Script**

**File:** `scripts/verify-and-setup-persistence.sh`
**What it checks:**
- ✅ Systemd service status
- ✅ Docker containers running
- ✅ Restart policies configured
- ✅ Git post-commit hook installed

**Output:**
```
🔍 TTA.dev Observability Persistence Check

Checking systemd service... ❌ Not installed
Checking Docker containers... ❌ Not running
Checking Docker restart policies... ✅ Configured
Checking git post-commit hook... ✅ Installed

⚠️  Setup required

Options:
1. Run full setup (installs systemd service - requires sudo)
2. Start Docker containers only
3. View detailed documentation

Would you like to run setup now? (y/N):
```

**Features:**
- Idempotent (safe to run multiple times)
- Interactive (offers to fix issues)
- Informative (clear status for each component)

### 4. **Full Setup Script**

**File:** `scripts/setup-persistence.sh`
**What it does:**
- Installs systemd service
- Enables auto-start on boot
- Starts Docker containers with restart policies
- Verifies everything is running

---

## 🔄 How It Works

### For Human Users

1. **Open workspace** in VS Code
2. **Task automatically runs** and shows status in terminal
3. **If setup needed:** Run suggested command
4. **Done:** Everything persists across sessions

### For AI Agents (Copilot)

1. **New session starts** in VS Code
2. **Reads Copilot instructions** (`.github/copilot-instructions.md`)
3. **Sees persistence check requirement** in instructions
4. **Runs verification script** to check status
5. **If not set up:** Informs user or runs setup (with permission)

---

## 📋 Three Layers of Automation

| Layer | When | What | Audience |
|-------|------|------|----------|
| **VS Code Task** | Workspace open | Show status | Human |
| **Copilot Instructions** | Agent session start | Check and inform | AI Agent |
| **Verification Script** | On-demand / automatic | Diagnose and fix | Both |

---

## 🚀 What Happens on Next Session

### Scenario 1: Everything Already Set Up

```bash
# VS Code opens, task runs:
🔍 TTA.dev Observability Persistence Check

Checking systemd service... ✅ Running
Checking Docker containers... ✅ Running (5 containers)
Checking Docker restart policies... ✅ Configured
Checking git post-commit hook... ✅ Installed

✅ All systems operational!

📊 Access your observability stack:
   • Metrics:     http://localhost:8001/metrics
   • Prometheus:  http://localhost:9090
   • Jaeger:      http://localhost:16686
   • Grafana:     http://localhost:3000
   • Pushgateway: http://localhost:9091
```

**Result:** ✅ User sees everything is working, continues with work

### Scenario 2: Setup Needed

```bash
# VS Code opens, task runs:
🔍 TTA.dev Observability Persistence Check

Checking systemd service... ❌ Not installed
Checking Docker containers... ❌ Not running
...

⚠️  Setup required

Would you like to run setup now? (y/N):
```

**Result:** ⚠️ User prompted to run setup, one command fixes everything

### Scenario 3: Copilot Agent Session

```
# Agent reads instructions
📋 Copilot sees: "verify observability infrastructure on session start"

# Agent runs verification
./scripts/verify-and-setup-persistence.sh

# Agent reports to user
"I've checked the observability setup. Currently not running.
Would you like me to set it up? It requires sudo for systemd service."
```

**Result:** 🤖 Agent proactively checks and informs user

---

## 🎓 Teaching Future Agents

The Copilot instructions now include:

1. **What to check:** Specific components (systemd, Docker, git hook)
2. **How to check:** Exact command to run
3. **Why it matters:** Explains importance of observability
4. **What to do:** Clear instructions if not set up

This means **every future Copilot agent** will:
- ✅ Know to verify observability on session start
- ✅ Use the correct verification command
- ✅ Understand the importance
- ✅ Guide users to fix issues

---

## 📖 Documentation Created

| File | Purpose |
|------|---------|
| `scripts/verify-and-setup-persistence.sh` | Smart verification script |
| `scripts/setup-persistence.sh` | Full setup automation |
| `scripts/PERSISTENCE_SETUP.md` | Complete documentation |
| `PERSISTENCE_STATUS.md` | Quick reference summary |
| `.github/copilot-instructions.md` | Agent instructions (updated) |
| `.vscode/tasks.json` | VS Code task (updated) |

---

## 🎯 Summary

**Question:** "How do we tell the next Copilot session to call this automatically?"

**Answer:**
1. ✅ **VS Code task** runs on workspace open
2. ✅ **Copilot instructions** tell agents to check
3. ✅ **Verification script** is smart and interactive
4. ✅ **Setup script** fixes everything in one command

**Result:** Future sessions (human or AI) automatically check observability status and prompt for setup if needed.

---

**Next Steps:**
- Current session: Run `./scripts/setup-persistence.sh` to set up now
- Future sessions: Automatic verification on workspace open
- Copilot agents: Will read instructions and verify automatically

---

**Created:** November 2, 2025
**For:** Automatic persistence verification across sessions
**Benefit:** Never manually start observability infrastructure again
