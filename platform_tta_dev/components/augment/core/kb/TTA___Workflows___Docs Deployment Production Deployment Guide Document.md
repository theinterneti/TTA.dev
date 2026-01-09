---
title: TTA E2E Testing - Production Deployment Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/TTA E2E Testing - Production Deployment Guide]]

## Overview

This guide provides step-by-step instructions for deploying the TTA E2E testing infrastructure to production. The implementation includes comprehensive GitHub Actions workflows, security scanning, performance monitoring, and automated deployment pipelines.

## 🚀 Quick Start

### Prerequisites

1. **GitHub CLI installed and authenticated**
   ```bash
   # Install GitHub CLI
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update
   sudo apt install gh

   # Authenticate
   gh auth login
   ```

2. **Repository access with admin permissions**
3. **Required service accounts and API keys** (see Configuration section)

### Automated Setup

1. **Run the automated setup script:**
   ```bash
   ./scripts/setup-repository-config.sh
   ```

2. **Validate the configuration:**
   ```bash
   ./scripts/validate-repository-config.sh
   ```

3. **Update placeholder secrets with real values** (see Configuration section)

## 📋 Manual Configuration Steps

### 1. Repository Secrets Configuration

Navigate to `Repository Settings > Secrets and variables > Actions > Repository secrets` and add:

#### Deployment & Infrastructure
```bash
# SSH keys for deployment
gh secret set STAGING_DEPLOY_KEY --body "$(cat ~/.ssh/staging_deploy_key)"
gh secret set PRODUCTION_DEPLOY_KEY --body "$(cat ~/.ssh/production_deploy_key)"

# Container registry access
gh secret set DOCKER_REGISTRY_TOKEN --body "your-docker-registry-token"

# Kubernetes configuration (if using K8s)
gh secret set KUBERNETES_CONFIG --body "$(cat ~/.kube/config | base64 -w 0)"
```

#### External Service Integration
```bash
# AI model service
gh secret set OPENROUTER_API_KEY --body "sk-or-v1-your-openrouter-key"

# Database credentials
gh secret set NEO4J_CLOUD_PASSWORD --body "your-neo4j-password"
gh secret set REDIS_CLOUD_PASSWORD --body "your-redis-password"

# Monitoring and error tracking
gh secret set SENTRY_DSN --body "https://your-sentry-dsn@sentry.io/project-id"
gh secret set DATADOG_API_KEY --body "your-datadog-api-key"
```

#### Notification & Communication
```bash
# Slack integration
gh secret set SLACK_WEBHOOK_URL --body "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

# Discord integration (optional)
gh secret set DISCORD_WEBHOOK_URL --body "https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK"

# Email service (optional)
gh secret set EMAIL_SERVICE_KEY --body "your-email-service-api-key"
```

#### Security & Compliance
```bash
# Security scanning
gh secret set SECURITY_SCAN_TOKEN --body "your-security-scan-token"
gh secret set SEMGREP_APP_TOKEN --body "your-semgrep-token"

# Test environment credentials
gh secret set TEST_USER_PASSWORD --body "secure-test-password"
gh secret set PREMIUM_TEST_PASSWORD --body "secure-premium-test-password"
```

### 2. Repository Variables Configuration

Navigate to `Repository Settings > Secrets and variables > Actions > Variables` and add:

#### Environment URLs
```bash
gh variable set STAGING_API_URL --body "https://staging-api.tta.yourdomain.com"
gh variable set PRODUCTION_API_URL --body "https://api.tta.yourdomain.com"
gh variable set STAGING_WS_URL --body "wss://staging-ws.tta.yourdomain.com"
gh variable set PRODUCTION_WS_URL --body "wss://ws.tta.yourdomain.com"
```

#### Test Configuration
```bash
gh variable set TEST_USERNAME --body "e2e_test_user"
gh variable set TEST_EMAIL --body "e2e-test@tta.yourdomain.com"
gh variable set PREMIUM_TEST_USERNAME --body "e2e_premium_user"
gh variable set PREMIUM_TEST_EMAIL --body "e2e-premium@tta.yourdomain.com"
```

#### Performance Budgets
```bash
gh variable set PERFORMANCE_BUDGET_AUTH_LOAD_TIME --body "2000"
gh variable set PERFORMANCE_BUDGET_DASHBOARD_LOAD_TIME --body "3000"
gh variable set PERFORMANCE_BUDGET_CHAT_RESPONSE_TIME --body "1500"
```

#### Feature Flags
```bash
gh variable set ENABLE_VISUAL_REGRESSION_TESTS --body "true"
gh variable set ENABLE_PERFORMANCE_BUDGETS --body "true"
gh variable set ENABLE_SECURITY_SCANNING --body "true"
gh variable set NOTIFICATION_CHANNELS --body "slack,email"
gh variable set CRITICAL_FAILURE_NOTIFICATION --body "true"
```

### 3. Environment Configuration

Create the following environments in `Repository Settings > Environments`:

#### Development Environment
- **Name**: `development`
- **Protection rules**: None
- **Secrets**: Development-specific API endpoints and credentials

#### Staging Environment
- **Name**: `staging`
- **Protection rules**:
  - Required reviewers: 1
  - Wait timer: 5 minutes
  - Deployment branches: `develop`, `main`
- **Secrets**: Staging-specific API endpoints and credentials

#### Production Environment
- **Name**: `production`
- **Protection rules**:
  - Required reviewers: 2
  - Wait timer: 30 minutes
  - Deployment branches: `main` only
  - Prevent self-review: enabled
- **Secrets**: Production API endpoints and credentials

#### Test Environment
- **Name**: `test`
- **Protection rules**: None
- **Secrets**: Test-specific configuration

### 4. Branch Protection Rules

#### Main Branch Protection
```bash
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{
    "strict": true,
    "contexts": [
      "E2E Tests (chromium - auth)",
      "E2E Tests (chromium - dashboard)",
      "Comprehensive Accessibility Audit",
      "Performance Benchmarks",
      "Security Scan"
    ]
  }' \
  --field required_pull_request_reviews='{
    "required_approving_review_count": 2,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true
  }' \
  --field enforce_admins=false \
  --field allow_force_pushes=false \
  --field allow_deletions=false
```

#### Develop Branch Protection
```bash
gh api repos/:owner/:repo/branches/develop/protection \
  --method PUT \
  --field required_status_checks='{
    "strict": true,
    "contexts": [
      "E2E Tests (chromium - auth)",
      "Security Scan"
    ]
  }' \
  --field required_pull_request_reviews='{
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true
  }' \
  --field enforce_admins=false
```

## 🔧 Workflow Configuration

### E2E Testing Workflow

The main E2E testing workflow (`.github/workflows/e2e-tests.yml`) includes:

- **Multi-browser testing**: Chromium, Firefox, WebKit
- **Mobile testing**: Mobile Chrome, Mobile Safari
- **Accessibility auditing**: WCAG 2.1 AA compliance
- **Performance monitoring**: Load time and Core Web Vitals
- **Visual regression testing**: Screenshot comparison
- **Security scanning**: Vulnerability detection
- **Deployment integration**: Automated staging deployment
- **Notification system**: Slack/Discord/Email alerts

### Security Scanning Workflow

The security workflow (`.github/workflows/security-scan.yml`) includes:

- **Dependency scanning**: npm audit and vulnerability detection
- **Code analysis**: Semgrep, CodeQL, and Trivy scanning
- **Secret detection**: TruffleHog and GitLeaks
- **SARIF reporting**: Integration with GitHub Security tab
- **Automated notifications**: Critical vulnerability alerts

## 📊 Performance Monitoring

### Performance Budget Enforcement

The performance budget checker (`scripts/check-performance-budget.js`) enforces:

- **Auth pages**: 2000ms load time, 1500ms FCP
- **Dashboard**: 3000ms load time, 2000ms FCP
- **Character creation**: 2500ms load time, 1800ms FCP
- **Chat responses**: 1500ms load time, 1200ms FCP
- **Settings pages**: 2000ms load time, 1500ms FCP

### Usage
```bash
# Check performance budgets
npm run performance:check

# Check with specific results file
npm run performance:check:with-results test-results/results.json
```

## 🔒 Security Configuration

### Security Scanning Features

- **Vulnerability scanning**: High and critical severity detection
- **Dependency review**: License and security compliance
- **Secret detection**: Prevent credential leaks
- **SARIF integration**: GitHub Security tab integration
- **Automated notifications**: Critical issue alerts

### Security Best Practices

1. **Rotate secrets regularly** (every 90 days)
2. **Use least-privilege access** for all service accounts
3. **Monitor secret usage** through GitHub audit logs
4. **Enable secret scanning** for the repository
5. **Review security alerts** promptly

## 🚀 Deployment Pipeline

### Staging Deployment

Automatically triggered on:
- Push to `develop` branch
- Successful E2E test completion

### Production Deployment

Manually triggered with:
- Push to `main` branch
- Required approvals (2 reviewers)
- 30-minute wait timer
- All E2E tests passing

### Deployment Process

1. **Build application** with environment-specific configuration
2. **Run security checks** and vulnerability scanning
3. **Execute E2E tests** across all browsers and devices
4. **Deploy to target environment** using secure SSH keys
5. **Verify deployment** with health checks
6. **Send notifications** to configured channels

## 📈 Monitoring and Alerting

### Notification Channels

Configure in repository variables:
- **Slack**: Team notifications and alerts
- **Discord**: Alternative notification channel
- **Email**: Critical failure notifications

### Alert Types

- **Test failures**: E2E test failures and regressions
- **Security issues**: High/critical vulnerabilities
- **Performance regressions**: Budget violations
- **Deployment status**: Success/failure notifications

## 🛠️ Troubleshooting

### Common Issues

#### 1. E2E Tests Failing
```bash
# Check test environment
npm run test:env:start

# Validate setup
./scripts/validate-e2e-setup.sh

# Run specific test suite
npm run test:e2e:auth -- --headed
```

#### 2. Security Scan Failures
```bash
# Check for vulnerabilities
npm run security:scan

# Fix automatically
npm run security:fix

# Manual review
gh api repos/:owner/:repo/security-advisories
```

#### 3. Performance Budget Violations
```bash
# Check performance results
npm run performance:check

# Review detailed report
cat performance-budget-report.md
```

### Support Resources

- **Configuration files**: `.github/repository-config/`
- **Validation scripts**: `./scripts/validate-repository-config.sh`
- **Setup automation**: `./scripts/setup-repository-config.sh`
- **GitHub documentation**: https://docs.github.com/en/actions

## 📚 Additional Resources

### Documentation Files

- **Secrets configuration**: `.github/repository-config/secrets-configuration.yml`
- **Environment setup**: `.github/repository-config/environments-configuration.yml`
- **Branch protection**: `.github/repository-config/branch-protection-rules.yml`
- **E2E testing guide**: `tests/e2e/README.md`

### Useful Commands

```bash
# Repository validation
npm run repo:validate

# Repository setup
npm run repo:setup

# Start test environment
npm run test:env:start

# Run all E2E tests
npm run test:e2e

# Check performance budgets
npm run performance:check

# Security scanning
npm run security:scan
```

## 🎯 Success Criteria

Your production deployment is ready when:

- ✅ All repository secrets and variables are configured
- ✅ Branch protection rules are enforced
- ✅ E2E tests pass across all browsers
- ✅ Security scans show no critical vulnerabilities
- ✅ Performance budgets are within limits
- ✅ Deployment pipeline works end-to-end
- ✅ Notifications are properly configured
- ✅ Monitoring and alerting are functional

## 🔄 Maintenance

### Regular Tasks

- **Weekly**: Review test results and performance metrics
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review and rotate secrets
- **Annually**: Audit security configuration and access controls

### Monitoring

- **GitHub Actions**: Monitor workflow execution and success rates
- **Security tab**: Review and address security advisories
- **Performance reports**: Track performance trends and regressions
- **Notification channels**: Ensure alerts are being received

---

**Need help?** Check the troubleshooting section or run `./scripts/validate-repository-config.sh` for configuration validation.


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs deployment production deployment guide document]]
