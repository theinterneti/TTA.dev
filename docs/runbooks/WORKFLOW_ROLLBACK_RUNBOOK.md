# Workflow Rollback Runbook

**Purpose**: Emergency rollback procedures for GitHub Actions workflow migration  
**Audience**: DevOps engineers, on-call staff  
**Last Updated**: 2025-11-20

---

## Rollback Trigger Conditions

Execute rollback **immediately** if any of the following occur:

### Critical (Immediate Rollback)
1. **Unique V2 Failures**: PRs fail in v2 but pass in v1 (workflow logic bug)
2. **Security Issue**: Security vulnerability discovered in v2 workflows
3. **Data Loss**: v2 workflows fail to preserve artifacts or reports
4. **Complete Outage**: V2 workflows consistently failing (>50% failure rate)

### High (Investigate + Rollback if Unresolved in 24h)
1. **Performance Degradation**: V2 is >10% slower than v1 consistently
2. **Missing Functionality**: Feature present in v1 not working in v2
3. **Team Consensus**: Team requests pause/rollback

### Medium (Extend Monitoring, No Immediate Rollback)
1. **Intermittent Failures**: Occasional v2 failures, root cause unclear
2. **Minor Performance Issues**: 5-10% slower, within acceptable range

---

## Rollback Procedures

### Phase 3.1 → v1 Primary (Automatic)

**Scenario**: Issues during parallel execution period

**Status**: ✅ **NO ACTION NEEDED**

**Rationale**:
- V1 workflows are already running and primary
- V2 workflows running in parallel for observation
- Simply stop investigating v2, let v1 continue

**Steps**:
1. Document issue in GitHub issue
2. Investigate v2 workflow problems
3. Fix v2 workflows
4. Resume parallel execution once fixed

---

### Phase 3.2 → Re-enable v1 (Manual Rollback)

**Scenario**: Issues during v2-only execution period

**Status**: ⚠️  **MANUAL ROLLBACK REQUIRED**

### Step 1: Re-enable V1 Workflows

```bash
# 1. Create emergency branch
git checkout main
git pull origin main
git checkout -b emergency/enable-v1-workflows

# 2. Edit .github/workflows/pr-validation.yml
# Remove or comment out the "if: false" line at line 16-17

# 3. Edit .github/workflows/merge-validation.yml
# Remove or comment out the "if: false" line at line 18-19

# 4. Commit and push
git add .github/workflows/pr-validation.yml .github/workflows/merge-validation.yml
git commit -m "emergency: Re-enable v1 workflows (rollback from Phase 3.2)"
git push origin emergency/enable-v1-workflows

# 5. For URGENT rollback, push directly to main (skip PR)
git push origin emergency/enable-v1-workflows:main

# 6. For NON-URGENT rollback, create PR for review
gh pr create --title "emergency: Re-enable v1 workflows" \
             --body "Rollback from Phase 3.2 due to [ISSUE_DESCRIPTION]" \
             --label "P0,rollback,ci/cd"
```

**Expected Time**: 2-5 minutes

### Step 2: Disable V2 Workflows (Optional but Recommended)

```bash
# 1. Edit .github/workflows/pr-validation-v2.yml
# Add "if: false" to job at line 17

# 2. Edit .github/workflows/merge-validation-v2.yml  
# Add "if: false" to job at line 13

# 3. Commit and push
git add .github/workflows/*-v2.yml
git commit -m "emergency: Disable v2 workflows during rollback"
git push origin emergency/enable-v1-workflows:main
```

**Expected Time**: 2-3 minutes

### Step 3: Validate Rollback

```bash
# 1. Create test PR
git checkout -b test/rollback-validation
echo "# Rollback Test" > test-rollback.md
git add test-rollback.md
git commit -m "test: Validate v1 workflows enabled"
git push origin test/rollback-validation

# 2. Create PR
gh pr create --title "test: Rollback validation" \
             --body "Testing v1 workflows after rollback"

# 3. Verify workflows
gh pr checks --watch

# Expected: pr-validation.yml runs (v1)
# Expected: pr-validation-v2.yml DOES NOT run (if disabled)

# 4. Close test PR
gh pr close --delete-branch
```

**Expected Time**: 5-10 minutes

### Step 4: Document and Investigate

```bash
# Create post-mortem issue
gh issue create \
  --title "🚨 Workflow Migration Rollback - $(date +%Y-%m-%d)" \
  --label "P0,rollback,ci/cd,post-mortem" \
  --body "# Rollback Post-Mortem

## Trigger
[Describe what triggered the rollback]

## Timeline
- **Issue Detected**: [TIME]
- **Rollback Initiated**: [TIME]
- **Rollback Completed**: [TIME]
- **Validation Completed**: [TIME]

## Root Cause
[To be determined]

## Impact
- Number of affected PRs:
- Number of failed workflow runs:
- Duration of outage:

## Action Items
- [ ] Investigate root cause
- [ ] Fix v2 workflows
- [ ] Add regression tests
- [ ] Re-validate v2 workflows
- [ ] Resume parallel execution

## Related
- Issue #79 (Workflow Rebuild Phase 3)
- Rollback commit: [COMMIT_SHA]
"
```

**Expected Time**: 10-15 minutes

---

### Phase 3.3 → Restore from Archive (Emergency)

**Scenario**: Issues after v1 workflows deleted

**Status**: 🚨 **EMERGENCY RESTORE**

### Step 1: Restore V1 Workflows from Archive

```bash
# 1. Create emergency branch
git checkout main
git pull origin main
git checkout -b emergency/restore-v1-workflows

# 2. Check if archive exists
ls archive/workflows/v1/

# 3. Restore workflows
cp archive/workflows/v1/pr-validation.yml .github/workflows/
cp archive/workflows/v1/merge-validation.yml .github/workflows/

# 4. Commit and push IMMEDIATELY to main
git add .github/workflows/
git commit -m "emergency: Restore v1 workflows from archive"
git push origin emergency/restore-v1-workflows:main

# 5. Notify team
gh issue create --title "🚨 EMERGENCY: V1 workflows restored from archive" \
                --label "P0,emergency,ci/cd" \
                --body "V1 workflows restored due to critical v2 failure. Investigation underway."
```

**Expected Time**: 3-5 minutes

### Step 2: Disable V2 Workflows

```bash
# Follow Step 2 from Phase 3.2 rollback above
```

### Step 3: Validate and Monitor

```bash
# Create multiple test PRs to ensure stability
for i in {1..3}; do
  git checkout -b test/restore-validation-$i
  echo "# Test $i" > test-$i.md
  git add test-$i.md
  git commit -m "test: Restore validation $i"
  git push origin test/restore-validation-$i
  gh pr create --title "test: Restore validation $i" --body "Testing v1 restore"
done

# Watch all PRs
gh pr list --state open | grep "test: Restore"

# Verify v1 workflows running
gh run list --workflow="pr-validation.yml" --limit 5
```

**Expected Time**: 10-15 minutes

---

## Rollback Validation Checklist

After any rollback, verify:

- [ ] ✅ V1 workflows executing on new PRs
- [ ] ✅ V2 workflows NOT executing (if disabled)
- [ ] ✅ No workflow syntax errors
- [ ] ✅ Artifacts being created (coverage reports, etc.)
- [ ] ✅ Quality gates passing/failing correctly
- [ ] ✅ Team notified of rollback
- [ ] ✅ Post-mortem issue created
- [ ] ✅ Root cause investigation underway

---

## Communication Template

### Slack/Teams Announcement

```
🚨 **CI/CD Rollback Alert**

We have rolled back from Workflow Migration Phase [X.X] to v1 workflows.

**Reason**: [Brief description]

**Impact**: Minimal - v1 workflows are stable and fully functional

**Status**: ✅ Rollback complete, PRs validating normally

**Next Steps**:
- Investigating root cause
- Post-mortem issue: #[ISSUE_NUMBER]
- Will resume migration after fixes validated

**Questions?** Comment on issue #[ISSUE_NUMBER]
```

### GitHub Issue Template

See Step 4 in Phase 3.2 rollback procedure above.

---

## Post-Rollback Actions

### Immediate (0-24 hours)
1. ✅ Complete rollback validation checklist
2. ✅ Create post-mortem issue
3. ✅ Notify team via Slack/Teams
4. ✅ Begin root cause investigation

### Short-term (1-3 days)
1. ✅ Identify root cause
2. ✅ Develop fix for v2 workflows
3. ✅ Add regression tests
4. ✅ Update post-mortem with findings

### Medium-term (1-2 weeks)
1. ✅ Validate fixes in test environment
2. ✅ Resume parallel execution (Phase 3.1)
3. ✅ Extended monitoring period
4. ✅ Post-mortem retrospective with team

---

## Emergency Contacts

**Primary**: DevOps Team Lead  
**Secondary**: Infrastructure Engineer  
**Escalation**: CTO/Engineering VP

**Issue Tracking**: GitHub Issues with `P0` + `rollback` labels  
**Communication**: Slack #engineering-alerts channel

---

## Testing Rollback Procedures

### Quarterly Rollback Drill

To ensure procedures are current and team is prepared:

```bash
# 1. Create test branch
git checkout -b test/rollback-drill-$(date +%Y-%m-%d)

# 2. Simulate rollback steps (without pushing to main)
# ...follow rollback procedures above...

# 3. Document time taken for each step
# 4. Update runbook with lessons learned
# 5. Discard test branch
```

**Schedule**: Quarterly (every 3 months)  
**Duration**: 30-45 minutes  
**Participants**: All DevOps engineers

---

## Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-11-20 | 1.0 | Initial creation | DevOps Engineer (AI) |

---

**Emergency Hotline**: Create GitHub issue with `P0` + `rollback` labels  
**Runbook Location**: `docs/runbooks/WORKFLOW_ROLLBACK_RUNBOOK.md`
