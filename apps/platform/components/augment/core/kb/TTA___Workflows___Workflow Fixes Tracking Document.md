---
title: Workflow Systemic Fixes - Implementation Tracking
tags: #TTA
status: Active
repo: theinterneti/TTA
path: WORKFLOW_FIXES_TRACKING.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Workflow Systemic Fixes - Implementation Tracking]]

## Status: 🟡 IN PROGRESS
**Started:** 2025-10-27
**Target Completion:** 2025-11-03 (1 week)
**Current Phase:** Phase 1 - Fix Systemic Failures

---

## Quick Reference

### Failing Checks (5 systemic issues)
1. ❌ Docker Build (developer-api, player-experience-frontend)
2. ❌ CodeQL JavaScript/TypeScript Analysis
3. ❌ Frontend Performance Tests
4. ❌ Integration Tests (Redis/Neo4j not available)
5. ❌ Security Reports (SBOM, Secrets Detection)

### Quick Wins (Can fix in <1 hour each)
- [ ] Docker build context paths
- [ ] CodeQL npm dependencies
- [ ] Add service containers for integration tests

---

## Phase 1: Fix Systemic Failures (This Week)

### Day 1: Docker Build Fixes
**Status:** ⏳ PENDING
**Assignee:** @DevOps
**Estimated:** 2-3 hours

**Tasks:**
- [ ] Fix context path calculation for root Dockerfiles
- [ ] Test developer-api build locally
- [ ] Test player-experience-frontend build locally
- [ ] Update docker-build.yml with fixes
- [ ] Validate all 7 Docker images build successfully

**Files to Modify:**
- `.github/workflows/docker-build.yml` (lines 40-85)

**Test Command:**
```bash
# Test locally first
docker build -f Dockerfile.developer-api -t test-dev-api .
docker build -f src/player_experience/frontend/Dockerfile -t test-frontend src/player_experience/frontend
```

---

### Day 2: CodeQL JavaScript/TypeScript
**Status:** ⏳ PENDING
**Assignee:** @Security
**Estimated:** 2 hours

**Tasks:**
- [ ] Add package-lock.json validation
- [ ] Use `npm ci --legacy-peer-deps` for compatibility
- [ ] Add explicit TypeScript build before CodeQL scan
- [ ] Test on sample PR

**Files to Modify:**
- `.github/workflows/codeql.yml` (lines 120-160)

**Test Command:**
```bash
cd src/player_experience/frontend
npm ci --legacy-peer-deps
npm run build
```

---

### Day 3: Integration Tests with Services
**Status:** ⏳ PENDING
**Assignee:** @Backend
**Estimated:** 3 hours

**Tasks:**
- [ ] Add Redis service container to tests.yml
- [ ] Add Neo4j service container to tests.yml
- [ ] Add health checks for services
- [ ] Update test configuration to use service URLs
- [ ] Test integration suite locally

**Files to Modify:**
- `.github/workflows/tests.yml`
- `.github/workflows/comprehensive-test-battery.yml`

**Test Command:**
```bash
# Local docker-compose test
docker-compose up -d redis neo4j
export REDIS_URL=redis://localhost:6379
export NEO4J_URI=bolt://localhost:7687
uv run pytest tests/integration/
```

---

### Day 4: Security & SBOM
**Status:** ⏳ PENDING
**Assignee:** @Security
**Estimated:** 2 hours

**Tasks:**
- [ ] Switch to anchore/sbom-action for SBOM generation
- [ ] Enable built-in SBOM in docker/build-push-action
- [ ] Replace detect-secrets with gitleaks
- [ ] Add .gitleaksignore for test fixtures

**Files to Modify:**
- `.github/workflows/security-scan.yml`
- `.github/workflows/docker-build.yml`
- `.gitleaksignore` (NEW)

---

### Day 5: Frontend Performance Tests
**Status:** ⏳ PENDING
**Assignee:** @Frontend
**Estimated:** 2 hours

**Tasks:**
- [ ] Add Playwright installation with browsers
- [ ] Store baseline metrics in GitHub Actions cache
- [ ] Add tolerance thresholds (not hard limits)
- [ ] Test performance suite

**Files to Modify:**
- `.github/workflows/performance-tracking.yml` (lines 150-250)

**Test Command:**
```bash
cd src/player_experience/frontend
npm ci
npx playwright install --with-deps chromium
npx playwright test
```

---

## Phase 2: Consolidation (Next Week)

### Create Reusable Workflows
- [ ] `.github/workflows/reusable/test-python.yml`
- [ ] `.github/workflows/reusable/test-typescript.yml`
- [ ] `.github/workflows/reusable/deploy-environment.yml`
- [ ] `.github/workflows/reusable/build-docker.yml`

### Create Composite Actions
- [ ] `.github/actions/setup-python-uv/action.yml`
- [ ] `.github/actions/setup-node-pnpm/action.yml`
- [ ] `.github/actions/setup-services/action.yml`
- [ ] `.github/actions/report-metrics/action.yml`

### Merge Workflows
- [ ] `tests.yml` + `comprehensive-test-battery.yml` + `monorepo-ci.yml` → `ci.yml`
- [ ] All `gemini-*.yml` → `ai-assist.yml`
- [ ] `auto-merge-*.yml` → `automation.yml`
- [ ] `deploy-*.yml` → `deploy.yml` (with environments)

---

## Success Metrics

### Current Baseline (Oct 27, 2025)
- Workflow Success Rate: ~40%
- PR #73 Failing Checks: 23 failures
- Average CI Time: ~35 minutes
- Docker Build Success: 0% (all failing)
- CodeQL JS/TS: 0% (failing)
- Integration Tests: ~60% (service-dependent)

### Phase 1 Targets (Nov 3, 2025)
- [ ] Workflow Success Rate: ≥80%
- [ ] PR #73 Failing Checks: ≤5 failures
- [ ] Average CI Time: ≤30 minutes
- [ ] Docker Build Success: 100%
- [ ] CodeQL JS/TS: 100%
- [ ] Integration Tests: 95%+

### Phase 2 Targets (Nov 10, 2025)
- [ ] Workflow Count: ≤15 (from 36)
- [ ] Workflow Success Rate: ≥95%
- [ ] Average CI Time: ≤20 minutes
- [ ] CI Cost Reduction: ≥40%

---

## Daily Standup Format

### Template
```markdown
**Date:** YYYY-MM-DD
**Phase:** [1/2/3]
**Status:** [On Track / At Risk / Blocked]

**Yesterday:**
- [x] Completed task A
- [x] Completed task B

**Today:**
- [ ] Working on task C
- [ ] Starting task D

**Blockers:**
- None / [Describe blocker]

**Metrics:**
- PR #73 Failing Checks: X → Y (change)
- Workflow Success Rate: X%
```

---

## Rollback Plan

### If Phase 1 Fails
1. Keep all original workflows in `.github/workflows/deprecated/`
2. Revert workflow changes via git
3. Re-enable old workflows
4. Post-mortem within 24 hours

### Rollback Commands
```bash
# Quick rollback
git revert <commit-sha>
git push origin feature/phase-2-async-openhands-integration

# Or restore from deprecated
cp .github/workflows/deprecated/*.yml .github/workflows/
git add .github/workflows/
git commit -m "chore: Rollback workflow changes"
git push
```

---

## Communication Plan

### Stakeholders
- **Team:** Daily updates in #engineering Slack
- **Leadership:** Weekly summary in Monday staff meeting
- **PR Authors:** Comment on affected PRs when workflows change

### Notification Templates

**Starting Phase 1:**
```
🚀 Workflow Modernization - Phase 1 Starting

We're fixing 5 systemic workflow failures:
• Docker builds
• CodeQL JS/TS analysis
• Integration tests
• Security scans
• Performance tests

Expected: Workflows green by end of week
Impact: Improved CI reliability, faster feedback

Questions? Ask in #engineering
```

**Phase 1 Complete:**
```
✅ Workflow Modernization - Phase 1 Complete!

Results:
• Workflow success rate: 40% → 80%
• Docker builds: Fixed ✅
• CodeQL JS/TS: Fixed ✅
• Integration tests: Fixed ✅

Next: Consolidating 36 workflows → 15
ETA: Next week
```

---

## Resources

### Documentation
- [GitHub Actions Best Practices 2025](https://docs.github.com/en/actions/learn-github-actions/workflow-syntax-for-github-actions)
- [Reusable Workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [Composite Actions](https://docs.github.com/en/actions/creating-actions/creating-a-composite-action)

### Team Contacts
- **DevOps Lead:** @devops-lead
- **Security Champion:** @security-team
- **Frontend Lead:** @frontend-lead
- **Backend Lead:** @backend-lead

### Related Issues
- #XXX: Workflow Modernization Epic
- #YYY: Docker Build Failures
- #ZZZ: CodeQL Configuration

---

**Last Updated:** 2025-10-27
**Next Update:** Daily during Phase 1


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___workflow fixes tracking document]]
