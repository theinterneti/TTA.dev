---
title: TTA Staging E2E Test Execution Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: tests/e2e-staging/TEST_EXECUTION_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/TTA Staging E2E Test Execution Guide]]

Complete guide for running comprehensive end-to-end tests in the TTA staging environment.

## 🚀 Quick Start

### Prerequisites

1. **Staging Environment Running**
   ```bash
   docker-compose -f docker-compose.staging-homelab.yml up -d
   ```

2. **Browsers Installed**
   ```bash
   npm run browsers:install
   ```

3. **Environment Variables** (optional)
   ```bash
   # Create .env.staging if needed
   cp .env.staging.example .env.staging
   ```

### Run All Tests

```bash
# Run complete test suite
npm run test:staging

# Run with visible browser (headed mode)
npm run test:staging:headed

# Run with interactive UI
npm run test:staging:ui
```

## 📋 Test Suites

### 1. Authentication Tests

**Command:**
```bash
npm run test:staging:auth
```

**What it tests:**
- Login page functionality
- Demo credential authentication
- Invalid credential handling
- Session persistence
- Logout functionality
- OAuth flow (if enabled)

**Expected duration:** ~2-3 minutes

### 2. UI/UX Functionality Tests

**Command:**
```bash
npm run test:staging:ui-func
```

**What it tests:**
- Navigation menu usability
- Interactive elements
- Form accessibility
- Visual feedback
- Zero-instruction usability
- Responsive behavior

**Expected duration:** ~3-4 minutes

### 3. Integration Tests

**Command:**
```bash
npm run test:staging:integration
```

**What it tests:**
- API communication
- Database persistence (Redis, Neo4j, PostgreSQL)
- Real-time updates
- Data consistency
- WebSocket connections

**Expected duration:** ~4-5 minutes

### 4. Error Handling Tests

**Command:**
```bash
npm run test:staging:errors
```

**What it tests:**
- Network error recovery
- Invalid input handling
- Session expiry
- API error handling
- Edge cases

**Expected duration:** ~3-4 minutes

### 5. Responsive Design Tests

**Command:**
```bash
npm run test:staging:responsive
```

**What it tests:**
- Mobile viewport (375x667)
- Tablet viewport (768x1024)
- Desktop viewport (1920x1080)
- Touch interactions
- Viewport transitions

**Expected duration:** ~2-3 minutes

### 6. Accessibility Tests

**Command:**
```bash
npm run test:staging:a11y
```

**What it tests:**
- WCAG compliance
- Keyboard navigation
- ARIA labels
- Screen reader support
- Color contrast

**Expected duration:** ~2-3 minutes

## 🌐 Browser-Specific Testing

### Chromium Only
```bash
npm run test:staging:chromium
```

### Firefox Only
```bash
npm run test:staging:firefox
```

### WebKit Only
```bash
npm run test:staging:webkit
```

### All Browsers
```bash
# Default behavior runs on all configured browsers
npm run test:staging
```

## 📊 Viewing Results

### HTML Report

```bash
# Open interactive HTML report
npm run test:staging:report
```

The report includes:
- Test results by browser
- Screenshots of failures
- Video recordings
- Execution traces
- Performance metrics

### JSON Results

```bash
# View JSON results
cat test-results-staging/results.json | jq
```

### JUnit XML

```bash
# View JUnit XML (for CI/CD integration)
cat test-results-staging/results.xml
```

## 🐛 Debugging

### Debug Mode

```bash
# Run with Playwright Inspector
npm run test:staging:debug
```

This opens the Playwright Inspector where you can:
- Step through tests
- Inspect elements
- View network requests
- See console logs

### Run Single Test

```bash
# Run specific test file
npx playwright test \
  --config=playwright.staging.config.ts \
  tests/e2e-staging/01-authentication.staging.spec.ts

# Run specific test by name
npx playwright test \
  --config=playwright.staging.config.ts \
  -g "should login successfully"
```

### View Trace

```bash
# Open trace for failed test
npx playwright show-trace test-results-staging/trace.zip
```

## 🔍 Troubleshooting

### Environment Not Ready

**Error:** `Frontend not accessible at http://localhost:3001`

**Solution:**
```bash
# Check containers
docker-compose -f docker-compose.staging-homelab.yml ps

# Restart if needed
docker-compose -f docker-compose.staging-homelab.yml restart

# Check logs
docker-compose -f docker-compose.staging-homelab.yml logs -f
```

### Browser Installation Issues

**Error:** `Executable doesn't exist at /path/to/browser`

**Solution:**
```bash
# Kill stuck processes
pkill -f "chrome.*install" || true
pkill -f "playwright.*install" || true

# Remove lockfiles
rm -rf ~/.cache/ms-playwright/__dirlock

# Reinstall browsers
npm run browsers:install
```

### Test Timeouts

**Error:** `Test timeout of 300000ms exceeded`

**Solution:**
1. Check if staging environment is slow
2. Increase timeout in `playwright.staging.config.ts`
3. Check AI model response times
4. Run with `--headed` to see what's happening

### Database Connection Issues

**Error:** `Redis/Neo4j not accessible`

**Solution:**
```bash
# Check database containers
docker-compose -f docker-compose.staging-homelab.yml ps redis-staging neo4j-staging

# Check ports
netstat -an | grep -E "6380|7688"

# Restart databases
docker-compose -f docker-compose.staging-homelab.yml restart redis-staging neo4j-staging
```

## 📈 Performance Monitoring

### Check Test Duration

```bash
# View test execution times
cat test-results-staging/results.json | jq '.suites[].specs[].tests[] | {title: .title, duration: .results[0].duration}'
```

### Performance Budget

Tests should complete within:
- Authentication: < 3 minutes
- UI/UX: < 4 minutes
- Integration: < 5 minutes
- Error Handling: < 4 minutes
- Responsive: < 3 minutes
- Accessibility: < 3 minutes

**Total:** < 25 minutes for complete suite

## 🎯 Success Criteria

Tests pass when:
- ✅ All test suites complete without errors
- ✅ UI is intuitive (zero-instruction usability)
- ✅ Data persists correctly across sessions
- ✅ AI responses are received
- ✅ No critical console errors
- ✅ Performance is acceptable
- ✅ Accessibility standards are met

## 🔄 CI/CD Integration

### GitHub Actions

Tests can be integrated into CI/CD:

```yaml
- name: Run Staging E2E Tests
  run: |
    npm run browsers:install
    npm run test:staging
  env:
    STAGING_BASE_URL: ${{ secrets.STAGING_URL }}
    STAGING_API_URL: ${{ secrets.STAGING_API_URL }}
```

### Test Reports

- HTML reports: `playwright-staging-report/`
- JSON results: `test-results-staging/results.json`
- JUnit XML: `test-results-staging/results.xml`
- Screenshots: `test-results-staging/*.png`
- Videos: `test-results-staging/*.webm`

## 📝 Best Practices

1. **Run tests sequentially** - Staging uses single worker to avoid conflicts
2. **Check environment first** - Use `./scripts/validate-staging-environment.sh`
3. **Review failures** - Check screenshots and videos before re-running
4. **Update snapshots** - When UI changes are intentional
5. **Monitor performance** - Track test execution times
6. **Clean up** - Clear test data between runs if needed

## 🆘 Getting Help

If tests fail:
1. Check [Troubleshooting](#-troubleshooting) section
2. Review test output and screenshots
3. Check staging environment logs
4. Consult [[TTA/Workflows/README|README.md]] for detailed documentation
5. Open GitHub issue with test results and logs


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___tests e2e staging test execution guide document]]
