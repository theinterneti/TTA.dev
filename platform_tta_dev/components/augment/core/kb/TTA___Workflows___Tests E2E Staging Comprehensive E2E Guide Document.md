---
title: Comprehensive E2E Testing Guide for TTA Staging
tags: #TTA
status: Active
repo: theinterneti/TTA
path: tests/e2e-staging/COMPREHENSIVE_E2E_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Comprehensive E2E Testing Guide for TTA Staging]]

This guide covers the complete end-to-end testing suite for the TTA staging environment using Playwright.

## 📋 Test Coverage

### 1. **Core User Journey** (07-complete-user-journey.staging.spec.ts)
- OAuth/demo authentication
- Dashboard navigation
- Character creation
- World selection
- Gameplay interaction
- Data persistence verification
- Logout

**Success Criteria:**
- ✅ Zero-instruction usability
- ✅ Seamless flow from login to gameplay
- ✅ All data persists correctly
- ✅ Performance acceptable

### 2. **Data Persistence** (08-data-persistence.staging.spec.ts)
- Redis session storage
- Neo4j character/world storage
- Cross-database consistency
- Session recovery
- Concurrent updates
- Database resilience

**Success Criteria:**
- ✅ Session data in Redis
- ✅ Character data in Neo4j
- ✅ Progress persists across sessions
- ✅ Databases stay in sync

### 3. **Performance Monitoring** (09-performance-monitoring.staging.spec.ts)
- Page load times
- API response times
- AI response latency
- Layout stability
- Extended session performance
- Rapid interaction handling

**Success Criteria:**
- ✅ Page loads < 3 seconds
- ✅ API responses < 1 second
- ✅ AI responses < 15 seconds
- ✅ No layout shifts (CLS < 0.1)

### 4. **Existing Test Suites**
- **01-authentication.staging.spec.ts** - Login/logout flows
- **02-ui-functionality.staging.spec.ts** - UI/UX interactions
- **03-integration.staging.spec.ts** - API integration
- **04-error-handling.staging.spec.ts** - Error states
- **05-responsive.staging.spec.ts** - Responsive design
- **06-accessibility.staging.spec.ts** - WCAG compliance

## 🚀 Quick Start

### Prerequisites
```bash
# Install Playwright browsers
npm run browsers:install

# Or manually
npx playwright install chromium firefox webkit --force
```

### Start Staging Environment
```bash
# Start all services
docker-compose -f docker-compose.staging-homelab.yml up -d

# Wait for services (30-60 seconds)
docker-compose -f docker-compose.staging-homelab.yml ps

# Verify services are ready
./scripts/validate-staging-environment.sh
```

### Run Tests

**All Tests:**
```bash
npm run test:staging
```

**Specific Test Suites:**
```bash
# Complete user journey
npm run test:staging:journey

# Data persistence
npm run test:staging:persistence

# Performance
npm run test:staging:performance

# All existing suites
npm run test:staging:auth
npm run test:staging:ui-func
npm run test:staging:integration
npm run test:staging:errors
npm run test:staging:responsive
npm run test:staging:a11y
```

**Browser-Specific:**
```bash
npm run test:staging:chromium
npm run test:staging:firefox
npm run test:staging:webkit
```

**Interactive Modes:**
```bash
# Headed mode (see browser)
npm run test:staging:headed

# UI mode (interactive)
npm run test:staging:ui

# Debug mode
npm run test:staging:debug
```

## 📊 Test Reports

### View Reports
```bash
# HTML report
npm run test:staging:report

# JSON results
cat test-results-staging/results.json

# JUnit XML
cat test-results-staging/results.xml
```

### Report Locations
- **HTML**: `playwright-staging-report/index.html`
- **JSON**: `test-results-staging/results.json`
- **JUnit**: `test-results-staging/results.xml`
- **Screenshots**: `test-results-staging/screenshots/`
- **Videos**: `test-results-staging/videos/`

## 🔧 Configuration

### Environment Variables
```bash
# Frontend
export STAGING_BASE_URL=http://localhost:3001

# API
export STAGING_API_URL=http://localhost:8081

# Databases
export REDIS_URL=redis://localhost:6380
export NEO4J_URI=bolt://localhost:7688
export DATABASE_URL=postgresql://localhost:5433/tta_staging

# OAuth
export USE_MOCK_OAUTH=true
export OPENROUTER_CLIENT_ID=your_client_id
export OPENROUTER_CLIENT_SECRET=your_client_secret
```

### Playwright Config
Edit `playwright.staging.config.ts` to customize:
- Timeouts
- Retries
- Workers
- Reporters
- Browser options

## 🎯 Success Criteria

### Zero-Instruction Usability
- [ ] Players can navigate without guidance
- [ ] All buttons/links are intuitive
- [ ] Error messages are clear
- [ ] No confusing UI elements

### Error-Free Flows
- [ ] No console errors
- [ ] No unhandled exceptions
- [ ] Graceful error handling
- [ ] Clear error messages

### Data Persistence
- [ ] Session data in Redis
- [ ] Character data in Neo4j
- [ ] Progress persists across sessions
- [ ] Databases stay consistent

### Performance
- [ ] Page loads < 3 seconds
- [ ] API responses < 1 second
- [ ] AI responses < 15 seconds
- [ ] No layout shifts

### Browser Compatibility
- [ ] Works on Chromium
- [ ] Works on Firefox
- [ ] Works on WebKit
- [ ] Responsive on mobile

## 🐛 Troubleshooting

### Playwright Browsers Not Installing
```bash
# Kill stuck processes
pkill -f "chrome|firefox|webkit"

# Remove lockfiles
rm -rf ~/.cache/ms-playwright/__dirlock

# Install directly
npx playwright install chromium firefox webkit --force
```

### Tests Timing Out
- Increase timeout in `playwright.staging.config.ts`
- Check if staging services are running
- Verify network connectivity
- Check database connections

### Database Connection Issues
```bash
# Check Redis
redis-cli -p 6380 ping

# Check Neo4j
curl -u neo4j:password http://localhost:7474/db/neo4j/exec

# Check PostgreSQL
psql -h localhost -p 5433 -U tta_user -d tta_staging_db
```

### OAuth Flow Issues
- Set `USE_MOCK_OAUTH=true` for testing
- Verify OAuth credentials in environment
- Check redirect URIs
- Review browser console for errors

## 📈 Performance Baselines

Expected performance metrics:
- **Page Load**: < 3000ms
- **API Response**: < 1000ms
- **AI Response**: < 15000ms
- **Navigation**: < 2000ms
- **CLS**: < 0.1
- **FCP**: < 2000ms

## 🔐 Security Considerations

- Tests use demo credentials (not production)
- OAuth uses mock flow by default
- Database credentials in environment variables
- No sensitive data in test reports
- Screenshots/videos excluded from version control

## 📝 Adding New Tests

1. Create new `.staging.spec.ts` file in `tests/e2e-staging/`
2. Import page objects and helpers
3. Use `test.describe()` for test suites
4. Use `test.step()` for detailed logging
5. Add to `package.json` scripts
6. Update this guide

## 🤝 Contributing

- Follow existing test patterns
- Use page objects for UI interactions
- Add comprehensive logging
- Include success criteria
- Document new helpers
- Update this guide

## 📞 Support

For issues or questions:
1. Check troubleshooting section
2. Review test logs and reports
3. Check Playwright documentation
4. Review staging environment setup


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___tests e2e staging comprehensive e2e guide document]]
