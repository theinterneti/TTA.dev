# n8n Workflow Management - Quick Reference

**Quick commands for managing n8n workflows in TTA.dev**

---

## 🚀 Starting n8n

```bash
# Start n8n (foreground)
npx n8n

# Start n8n (background with logs)
npx n8n > /tmp/n8n.log 2>&1 &

# Check if n8n is running
lsof -Pi :5678 -sTCP:LISTEN -t >/dev/null && echo "Running" || echo "Not running"
```

---

## 📥 Import/Export Workflows

### Import All Workflows (Clean)

```bash
./scripts/fix-workflow-imports.sh
```

### Import Single Workflow

```bash
npx n8n import:workflow --input workflows/n8n_1_smart_commit_test.json
```

### Export Workflow

```bash
# By ID
npx n8n export:workflow --id <workflow-id> --output exported.json

# Export all
npx n8n export:workflow --all --output /tmp
```

---

## ✅ Validation

### Validate All Workflows

```bash
./scripts/validate-n8n-workflows.sh
```

### Create Safe Test Workflow

```bash
./scripts/create-safe-langchain-test.sh
```

### List Available Nodes

```bash
npx n8n export:nodes --output n8n-nodes.json
cat n8n-nodes.json | jq '.[] | .name' | grep -i langchain
```

---

## 🔧 Troubleshooting

### Fix Import Warnings

If you see SQLite errors during import:

```bash
# Run the fix script - automatically adds 'active' field
./scripts/fix-workflow-imports.sh
```

### Fix Permissions Warning

```bash
# Set environment variable
export N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true

# Or add to your shell profile
echo 'export N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true' >> ~/.bashrc
```

### Check n8n Logs

```bash
# If started in background
tail -f /tmp/n8n.log

# Check for errors
grep -i error /tmp/n8n.log
```

---

## 📋 Workflow Files

### Active Workflows

| File | Description | Safe to Auto-Run? |
|------|-------------|-------------------|
| `workflows/n8n_1_smart_commit_test.json` | Smart commit & test | ❌ No (git commits) |
| `workflows/n8n_2_pr_manager.json` | PR manager | ❌ No (creates PRs) |
| `workflows/n8n_3_issue_to_branch.json` | Issue to branch | ❌ No (creates branches) |
| `workflows/n8n_4_release_automation.json` | Release automation | ❌ No (git tags) |
| `n8n_git_automation_workflow.json` | Git automation | ❌ No (git commits) |
| `n8n_github_health_dashboard.json` | GitHub health | ⚠️ Careful (API calls) |
| **Safe Test Workflow** | LangChain Gemini test | ✅ Yes (read-only) |

---

## 🎯 Common Tasks

### Verify LangChain Nodes Are Available

```bash
npx n8n export:nodes --output /tmp/nodes.json
grep -i "langchain" /tmp/nodes.json | grep -i "gemini"
```

Expected output:

```text
"@n8n/n8n-nodes-langchain.lmChatGemini"
"@n8n/n8n-nodes-langchain.embeddingsGoogleGemini"
```

### Check Workflow Has Required Fields

```bash
python3 -c "
import json
f = open('workflows/n8n_1_smart_commit_test.json')
d = json.load(f)
print('Has active field:', 'active' in d)
print('Active value:', d.get('active', 'N/A'))
"
```

### List All Imported Workflows

```bash
# Via UI: http://localhost:5678
# Or export all and count:
npx n8n export:workflow --all --output /tmp && ls -1 /tmp/My_workflow_*.json | wc -l
```

---

## 🛡️ Safety Checklist

Before running any workflow:

- [ ] Does it modify git repository? (commits, pushes, tags)
- [ ] Does it call GitHub API? (create PRs, issues, branches)
- [ ] Does it execute shell commands?
- [ ] Does it have credentials configured?
- [ ] Is it set to run on a schedule?

**If YES to any above:** Review workflow carefully before activating!

**Safe to test:**

- ✅ "LangChain Gemini Test - Safe" workflow
- ✅ Manual trigger workflows (when you control execution)
- ✅ Read-only operations (get PR info, list issues)

---

## 📚 Documentation

- **Import Fix Guide:** `N8N_WORKFLOW_IMPORT_FIX_COMPLETE.md`
- **n8n Documentation:** <https://docs.n8n.io>
- **LangChain Nodes:** <https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain/>

---

## 🆘 Help

### Import Fails

```bash
# Check n8n is running
lsof -Pi :5678 -sTCP:LISTEN

# Check workflow JSON is valid
python3 -c "import json; json.load(open('workflows/workflow.json'))"

# Try manual import
npx n8n import:workflow --input workflows/workflow.json
```

### Node Not Found

```bash
# Verify node is available
npx n8n export:nodes --output /tmp/nodes.json
cat /tmp/nodes.json | jq '.[] | select(.name | contains("NodeName"))'

# Check for duplicate packages
find node_modules -name "@n8n-nodes-langchain" -type d
```

### Can't Access UI

```bash
# Check n8n is running
curl http://localhost:5678/healthz

# Check firewall
sudo ufw status

# Restart n8n
pkill -f "n8n" && npx n8n
```

---

**Last Updated:** November 9, 2025
