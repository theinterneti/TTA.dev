# AI Guardrails Implementation Summary

**Date:** March 7, 2026
**Purpose:** Implement strict Policy-as-Code guardrails for AI coding agents in CI/CD

---

## 🎯 Overview

This implementation adds comprehensive security and process controls for AI-generated code in the TTA.dev repository, ensuring all AI agents follow organizational standards before code can be merged.

---

## 📋 Implementation Details

### 1. Draft PR Enforcement (`enforce-draft-for-ai` job)

**Trigger:** Any PR opened, synchronized, or labeled
**Detection Logic:**
- Checks if PR author contains `[bot]` or `bot` in username
- Checks for `ai-generated` label
- Verifies current draft status

**Actions:**
- Automatically converts AI-generated PRs to Draft status using `gh pr ready --undo`
- Adds explanatory comment requiring:
  - Human review of all changes
  - Quality gate validation
  - Security check for secrets/sensitive data
  - Manual "Ready for review" conversion

**Security Benefit:** Prevents accidental auto-merge of AI code without human oversight

---

### 2. Provenance Tagging (`provenance-tagging` job)

**Trigger:** Any PR from branches matching `copilot/*` or `agent/*`
**Detection Logic:**
- Pattern matches branch name
- Checks existing labels to avoid duplicates

**Actions:**
- Applies `ai-generated` label automatically
- Adds provenance comment documenting:
  - Branch pattern that triggered tagging
  - Enhanced review requirements
  - Guardrail policy applicability

**Security Benefit:** Creates audit trail for all AI-generated code

---

### 3. Security Posture Report (`security-posture` job)

**Always Runs:** On every workflow trigger
**Audits:**

#### a) Action Pinning Audit
- Scans all workflows for unpinned third-party actions
- Reports count of unpinned vs pinned actions
- **FAILS THE BUILD** if unpinned actions found
- Generates detailed security report artifact

#### b) OIDC Usage Audit
- Scans for long-lived secrets in workflows
- Excludes legitimate `GITHUB_TOKEN` usage
- Recommends OIDC migration for cloud deployments
- Reports secret usage patterns

**Security Benefit:** Enforces supply chain security and prevents secret sprawl

---

### 4. AI Compliance Validation (`validate-ai-compliance` job)

**Trigger:** Only runs for AI-generated PRs
**Validations:**

#### a) Prohibited Pattern Detection
```bash
# Checks for:
- Hardcoded secrets (api_key, secret, password, token)
- Untracked TODO/FIXME (must use #dev-todo)
- Potential credential leaks
```

#### b) Quality Gate Verification
- Queries GitHub API for PR check status
- Ensures linting, type checking, and tests passed
- Blocks merge if quality gates pending/failed

**Security Benefit:** Prevents common AI coding mistakes before merge

---

## 🔧 Supporting Tools

### Action Pinning Script (`scripts/pin_workflow_actions.sh`)

**Purpose:** Automated tool to pin all unpinned actions to commit SHAs

**Features:**
- Maps common actions to latest stable commit SHAs
- Creates backups before modification
- Provides summary report of changes
- Idempotent - safe to run multiple times

**Usage:**
```bash
./scripts/pin_workflow_actions.sh
git diff .github/workflows  # Review changes
git add .github/workflows
git commit -m "chore: pin workflow actions to commit SHAs"
```

**Current Pinned Actions:**
- `actions/checkout@v4` → `b4ffde65f46336ab88eb53be808477a3936bae11` (v4.1.1)
- `actions/setup-python@v5` → `0a5c61591373683505ea898e09a3ea4f39ef2b9c` (v5.0.0)
- `actions/setup-node@v4` → `60edb5dd545a775178f52524783378180af0d1f8` (v4.0.2)
- `actions/upload-artifact@v4` → `5d5d22a31266ced268874388b861e4b58bb5c2f3` (v4.3.1)
- `actions/download-artifact@v4` → `c850b930e6ba138125429b7e5c93fc707a7f8427` (v4.1.4)
- `actions/cache@v4` → `ab5e6d0c87105b4c9c2047343972218f562e4319` (v4.0.1)
- `actions/github-script@v7` → `60a0d83039c74a4aee543508d2ffcb1c3799cdea` (v7.0.1)
- `astral-sh/setup-uv@v2` → `3f2f00c85e1be39f0c70d3c3e5c2ebb9e6471ebe` (v2.0.0)

---

## 🔒 Security Posture Analysis

### ✅ Strengths

1. **Supply Chain Security**
   - Action pinning enforced at CI level
   - Automated detection of unpinned dependencies
   - SHA-based pinning prevents tag manipulation

2. **AI Agent Containment**
   - Mandatory draft status for AI PRs
   - Provenance tracking via labels and branch names
   - Human-in-the-loop requirement for merge

3. **Secret Protection**
   - Pattern detection for hardcoded credentials
   - OIDC recommendation for cloud deployments
   - Minimal `contents: read` permissions

4. **Quality Enforcement**
   - AI code must pass all quality gates
   - No untracked TODO/FIXME allowed
   - Compliance validation before merge

### ⚠️ Current Gaps

1. **Unpinned Actions Detected**
   - ~20+ workflow files use version tags (`@v4`) instead of SHAs
   - **Mitigation:** Run `scripts/pin_workflow_actions.sh` immediately
   - **Status:** Script provided, requires manual execution

2. **OIDC Not Fully Adopted**
   - Some workflows may use long-lived secrets
   - **Recommendation:** Audit deployment workflows for AWS/Azure/GCP
   - **Priority:** Medium (no deployment secrets detected in initial scan)

3. **Experimental Workflows Excluded**
   - Gemini experimental workflows not audited
   - **Recommendation:** Review `.github/workflows/experimental/` manually
   - **Risk Level:** Low (experimental only)

### 📊 Compliance Status

| Requirement | Status | Notes |
|-------------|--------|-------|
| Draft PR enforcement | ✅ Implemented | Auto-converts AI PRs |
| Provenance tagging | ✅ Implemented | `ai-generated` label |
| OIDC security | ⚠️ Partial | No secrets detected, OIDC recommended |
| Action pinning | ❌ Required | Script provided, needs execution |

---

## 🚀 Next Steps

### Immediate (Today)
1. Run `scripts/pin_workflow_actions.sh` to pin all actions
2. Review and commit pinning changes
3. Merge this PR to enable guardrails

### Short-term (This Week)
4. Audit experimental workflows manually
5. Document OIDC setup for cloud deployments
6. Test guardrails with a test AI-generated PR

### Long-term (This Month)
7. Add GitHub App for enhanced AI agent identity
8. Implement signed commits requirement for AI PRs
9. Create dashboard for AI code contribution metrics

---

## 🧪 Testing Strategy

### Manual Testing
```bash
# Test draft enforcement
gh pr create --draft --label ai-generated --title "Test AI PR"

# Test provenance tagging
git checkout -b copilot/test-feature
gh pr create --title "Test Copilot PR"

# Test security audit
# (Runs automatically on all workflow triggers)
```

### Validation
- Monitor workflow runs in Actions tab
- Check for security-posture-report artifacts
- Verify AI PRs auto-converted to draft
- Confirm `ai-generated` label applied

---

## 📚 References

- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Pinning Actions to Commit SHAs](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions#using-third-party-actions)
- [GitHub OIDC Documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [Draft PR API](https://docs.github.com/en/rest/pulls/pulls#update-a-pull-request)

---

## ✅ Approval Checklist

- [x] Draft PR enforcement implemented
- [x] Provenance tagging implemented
- [x] Security posture auditing implemented
- [x] Action pinning script created
- [x] Documentation complete
- [ ] Actions pinned to SHAs (requires running script)
- [ ] OIDC audit complete (if applicable)
- [ ] Tested with sample AI PR

---

**Implementation by:** GitHub Copilot CLI
**Review required by:** DevOps Team Lead
**Security review required:** Yes (action pinning changes)
