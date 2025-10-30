# GitHub Workflows Setup for Logseq Sync

**Date:** 2025-10-30
**Status:** ✅ **READY FOR DEPLOYMENT**
**Purpose:** Automate bidirectional sync between TTA.dev and TTA-notes

---

## 🎯 Overview

Three GitHub Actions workflows automate the Logseq sync:

1. **TTA.dev → TTA-notes** (`.github/workflows/sync-logseq-to-tta-notes.yml`)
   - Runs on push to main when logseq/ files change
   - Runs on schedule (6 AM and 6 PM UTC daily)
   - Can be triggered manually

2. **TTA-notes → TTA.dev** (`.github/workflows/sync-from-tta-notes.yml`)
   - Triggered by TTA-notes repository
   - Creates a PR in TTA.dev for review
   - Ensures changes are reviewed before merging

3. **TTA-notes Trigger** (`TTA_NOTES_WORKFLOW_TEMPLATE.yml`)
   - Template to deploy in TTA-notes repository
   - Triggers TTA.dev sync when TTA.dev pages change

---

## 📋 Setup Instructions

### Step 1: Create GitHub Personal Access Tokens

You need two PATs (Personal Access Tokens):

#### PAT 1: TTA_NOTES_PAT (for TTA.dev repository)

**Purpose:** Allow TTA.dev workflows to access TTA-notes

**Permissions:**
- `repo` (Full control of private repositories)
- `workflow` (Update GitHub Action workflows)

**Steps:**
1. Go to: https://github.com/settings/tokens/new
2. Name: `TTA.dev to TTA-notes Sync`
3. Expiration: `No expiration` (or 1 year)
4. Select scopes:
   - ✅ `repo` (all sub-scopes)
   - ✅ `workflow`
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

#### PAT 2: TTA_DEV_PAT (for TTA-notes repository)

**Purpose:** Allow TTA-notes workflows to trigger TTA.dev workflows

**Permissions:**
- `repo` (Full control of private repositories)
- `workflow` (Update GitHub Action workflows)

**Steps:**
1. Go to: https://github.com/settings/tokens/new
2. Name: `TTA-notes to TTA.dev Sync`
3. Expiration: `No expiration` (or 1 year)
4. Select scopes:
   - ✅ `repo` (all sub-scopes)
   - ✅ `workflow`
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

### Step 2: Add Secrets to TTA.dev Repository

1. Go to: https://github.com/theinterneti/TTA.dev/settings/secrets/actions
2. Click "New repository secret"
3. Add secret:
   - **Name:** `TTA_NOTES_PAT`
   - **Value:** [Paste PAT 1 from Step 1]
4. Click "Add secret"

### Step 3: Add Secrets to TTA-notes Repository

1. Go to: https://github.com/theinterneti/TTA-notes/settings/secrets/actions
2. Click "New repository secret"
3. Add secret:
   - **Name:** `TTA_DEV_PAT`
   - **Value:** [Paste PAT 2 from Step 1]
4. Click "Add secret"

### Step 4: Deploy TTA-notes Workflow

```bash
# Copy the template to TTA-notes repository
cd ~/repos/TTA-notes

# Create workflows directory if it doesn't exist
mkdir -p .github/workflows

# Copy the workflow file
cp ~/repos/TTA.dev/TTA_NOTES_WORKFLOW_TEMPLATE.yml \
   .github/workflows/sync-to-tta-dev.yml

# Commit and push
git add .github/workflows/sync-to-tta-dev.yml
git commit -m "feat: Add workflow to trigger TTA.dev sync

Automatically triggers TTA.dev sync workflow when TTA.dev pages
are modified in TTA-notes repository.

Workflow:
- Runs on push to main when logseq/pages/TTA.dev/ changes
- Can be triggered manually
- Uses repository_dispatch to trigger TTA.dev workflow"

git push origin main
```

### Step 5: Commit TTA.dev Workflows

```bash
cd ~/repos/TTA.dev

# Add the workflow files
git add .github/workflows/sync-logseq-to-tta-notes.yml
git add .github/workflows/sync-from-tta-notes.yml
git add GITHUB_WORKFLOWS_SETUP.md
git add TTA_NOTES_WORKFLOW_TEMPLATE.yml

# Commit
git commit -m "feat: Add GitHub workflows for Logseq bidirectional sync

Add automated workflows for syncing Logseq documentation between
TTA.dev and TTA-notes repositories.

Workflows:
1. sync-logseq-to-tta-notes.yml
   - Syncs TTA.dev logseq/ to TTA-notes on push to main
   - Runs on schedule (6 AM and 6 PM UTC daily)
   - Can be triggered manually

2. sync-from-tta-notes.yml
   - Syncs TTA-notes changes back to TTA.dev
   - Creates PR for review
   - Triggered by TTA-notes repository

3. TTA_NOTES_WORKFLOW_TEMPLATE.yml
   - Template for TTA-notes repository
   - Triggers TTA.dev sync via repository_dispatch

Setup:
- Requires TTA_NOTES_PAT secret in TTA.dev
- Requires TTA_DEV_PAT secret in TTA-notes
- See GITHUB_WORKFLOWS_SETUP.md for full instructions"

# Push to current branch
git push origin HEAD
```

---

## 🔄 How It Works

### Workflow 1: TTA.dev → TTA-notes (Automatic)

**Trigger:** Push to main with logseq/ changes

```
1. Developer commits to TTA.dev/logseq/pages/
2. Push to main branch
3. GitHub Actions workflow triggers
4. Workflow syncs files to TTA-notes/logseq/pages/TTA.dev/
5. Workflow commits and pushes to TTA-notes
6. ✅ TTA-notes is updated automatically
```

**Schedule:** Also runs at 6 AM and 6 PM UTC daily

### Workflow 2: TTA-notes → TTA.dev (PR-based)

**Trigger:** Changes to TTA-notes/logseq/pages/TTA.dev/

```
1. Developer edits in TTA-notes/logseq/pages/TTA.dev/
2. Push to main branch
3. TTA-notes workflow triggers TTA.dev via repository_dispatch
4. TTA.dev workflow syncs files from TTA-notes
5. TTA.dev workflow creates a new branch
6. TTA.dev workflow creates a PR for review
7. ✅ Developer reviews and merges PR
```

**Why PR?** Changes from TTA-notes should be reviewed before merging to TTA.dev main branch.

---

## 🧪 Testing the Workflows

### Test 1: TTA.dev → TTA-notes

```bash
# Make a change in TTA.dev
cd ~/repos/TTA.dev
echo "test:: [[Workflow Test]]" >> logseq/pages/Test.md

# Commit and push to main
git add logseq/pages/Test.md
git commit -m "test: Verify sync workflow"
git push origin main

# Check GitHub Actions
# Go to: https://github.com/theinterneti/TTA.dev/actions
# Look for "Sync Logseq to TTA-notes" workflow

# Verify in TTA-notes
cd ~/repos/TTA-notes
git pull origin main
cat logseq/pages/TTA.dev/Test.md  # Should contain the test line
```

### Test 2: TTA-notes → TTA.dev

```bash
# Make a change in TTA-notes
cd ~/repos/TTA-notes
echo "reverse-test:: [[Reverse Sync Test]]" >> logseq/pages/TTA.dev/Test.md

# Commit and push to main
git add logseq/pages/TTA.dev/Test.md
git commit -m "test: Verify reverse sync workflow"
git push origin main

# Check GitHub Actions
# Go to: https://github.com/theinterneti/TTA-notes/actions
# Look for "Trigger TTA.dev Sync" workflow

# Then check TTA.dev
# Go to: https://github.com/theinterneti/TTA.dev/pulls
# Look for PR created by github-actions[bot]

# Review and merge the PR
```

### Test 3: Manual Trigger

```bash
# Go to: https://github.com/theinterneti/TTA.dev/actions
# Click "Sync Logseq to TTA-notes"
# Click "Run workflow"
# Select branch: main
# Click "Run workflow"

# Workflow should run and sync files
```

---

## 📊 Workflow Status

### Check Workflow Runs

**TTA.dev:**
- https://github.com/theinterneti/TTA.dev/actions

**TTA-notes:**
- https://github.com/theinterneti/TTA-notes/actions

### View Logs

1. Click on a workflow run
2. Click on the job name
3. Expand steps to see detailed logs

---

## 🔧 Troubleshooting

### Issue: Workflow doesn't trigger

**Check:**
1. Secrets are configured correctly
2. PATs have correct permissions
3. Workflow files are in `.github/workflows/` directory
4. Branch is `main` (not `master`)

### Issue: Permission denied

**Check:**
1. PAT has `repo` and `workflow` scopes
2. PAT is not expired
3. Secret name matches workflow file (`TTA_NOTES_PAT` or `TTA_DEV_PAT`)

### Issue: No changes detected

**Check:**
1. Files are in `logseq/pages/` or `logseq/journals/`
2. Changes are committed to main branch
3. Workflow path filters match changed files

---

## 🎯 Benefits

### Automated Sync
- ✅ No manual rsync commands
- ✅ Runs on schedule (twice daily)
- ✅ Triggers on every push to main

### Safety
- ✅ TTA-notes → TTA.dev creates PR for review
- ✅ No direct commits to TTA.dev main
- ✅ Full audit trail in GitHub Actions

### Reliability
- ✅ Consistent sync behavior
- ✅ Error handling and logging
- ✅ Can be manually triggered if needed

---

## 📚 Related Documentation

- **TTA_NOTES_ARCHITECTURE.md** - Architecture overview
- **CONTEXT_AWARE_LOGSEQ_STRATEGY.md** - Organization strategy
- **TTA_NOTES_SETUP_COMPLETE.md** - Initial setup verification

---

## ✅ Checklist

- [ ] Create TTA_NOTES_PAT token
- [ ] Create TTA_DEV_PAT token
- [ ] Add TTA_NOTES_PAT secret to TTA.dev
- [ ] Add TTA_DEV_PAT secret to TTA-notes
- [ ] Deploy workflow to TTA-notes
- [ ] Commit workflows to TTA.dev
- [ ] Test TTA.dev → TTA-notes sync
- [ ] Test TTA-notes → TTA.dev sync
- [ ] Test manual trigger
- [ ] Verify scheduled runs

---

**Status:** ✅ **READY FOR DEPLOYMENT**

**Next:** Follow setup instructions to configure secrets and deploy workflows

