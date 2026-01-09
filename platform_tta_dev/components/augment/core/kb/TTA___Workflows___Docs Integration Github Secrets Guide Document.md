---
title: GitHub Secrets and Variables Configuration Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/integration/GITHUB_SECRETS_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/GitHub Secrets and Variables Configuration Guide]]
## TTA Storytelling Project

This guide explains how to configure GitHub secrets and variables for your TTA (Therapeutic Text Adventure) storytelling application.

## 🔐 Understanding Secrets vs Variables

### GitHub Secrets (Encrypted)
- **Purpose**: Store sensitive data like API keys, passwords, tokens
- **Security**: Encrypted at rest, only exposed during workflow execution
- **Visibility**: Cannot be viewed after creation (only updated)
- **Usage**: Automatically masked in workflow logs

### GitHub Variables (Plain Text)
- **Purpose**: Store non-sensitive configuration like URLs, usernames, feature flags
- **Security**: Stored as plain text, visible in repository settings
- **Visibility**: Can be viewed and edited anytime
- **Usage**: Visible in workflow logs

## 🚨 SENTRY_DSN Configuration

### What is Sentry?
Sentry is an error monitoring and performance tracking service that helps you:
- Track application errors and exceptions
- Monitor performance and response times
- Get real-time alerts for critical issues
- Debug issues with detailed error context

### Getting Your Sentry DSN

1. **Create Sentry Account**:
   ```bash
   # Visit https://sentry.io and sign up (free tier available)
   # Create a new project for "TTA Storytelling"
   ```

2. **Find Your DSN**:
   - Go to Settings → Projects → [Your Project] → Client Keys (DSN)
   - Copy the DSN URL (format: `https://abc123@o123456.ingest.sentry.io/123456`)

3. **Configure in GitHub**:
   ```bash
   gh secret set SENTRY_DSN --body "https://your-actual-dsn@o123456.ingest.sentry.io/123456"
   ```

### Why Sentry is Important for TTA
- **Therapeutic Safety**: Monitor errors that could affect user experience
- **Performance Tracking**: Ensure fast response times for therapeutic interactions
- **Real-time Alerts**: Get notified of critical issues immediately
- **User Experience**: Track and fix issues before they impact users

## 🌐 API URL Configuration

### Current Environment Setup
Based on your project configuration:

- **Development**: `http://localhost:8080` (from your .env file)
- **Staging**: You need to set up a staging server
- **Production**: You need to set up a production server

### Recommended Domain Structure

```bash
# Staging Environment
gh variable set STAGING_API_URL --body "https://staging-api.tta-storytelling.com"
gh variable set STAGING_WS_URL --body "wss://staging-ws.tta-storytelling.com"

# Production Environment
gh variable set PRODUCTION_API_URL --body "https://api.tta-storytelling.com"
gh variable set PRODUCTION_WS_URL --body "wss://ws.tta-storytelling.com"
```

### Alternative Naming Patterns
```bash
# Option 1: Subdomain approach
STAGING_API_URL="https://staging.tta-storytelling.com"
PRODUCTION_API_URL="https://tta-storytelling.com"

# Option 2: Path-based approach
STAGING_API_URL="https://tta-storytelling.com/staging"
PRODUCTION_API_URL="https://tta-storytelling.com"

# Option 3: Environment-specific domains
STAGING_API_URL="https://tta-staging.yourdomain.com"
PRODUCTION_API_URL="https://tta.yourdomain.com"
```

## 🤖 AI Model Configuration

### OpenRouter Integration
Your project uses OpenRouter for AI model access. Configure:

```bash
# Your OpenRouter API key (from your .env file shows you have one)
gh secret set OPENROUTER_API_KEY --body "sk-or-v1-your-actual-key-here"

# Optional: Configure model preferences
gh variable set OPENROUTER_PREFER_FREE_MODELS --body "true"
gh variable set OPENROUTER_MAX_COST_PER_TOKEN --body "0.001"
```

### Other AI Services (Optional)
```bash
# OpenAI (if you plan to use it)
gh secret set OPENAI_API_KEY --body "sk-your-openai-key"

# Anthropic (if you plan to use it)
gh secret set ANTHROPIC_API_KEY --body "sk-ant-your-anthropic-key"
```

## 🗄️ Database Configuration

### Based on Your TTA Architecture
Your project uses multiple databases:

```bash
# Neo4j (for living worlds and character relationships)
gh secret set NEO4J_STAGING_PASSWORD --body "your-staging-neo4j-password"
gh secret set NEO4J_PRODUCTION_PASSWORD --body "your-production-neo4j-password"

# Redis (for session management and caching)
gh secret set REDIS_STAGING_PASSWORD --body "your-staging-redis-password"
gh secret set REDIS_PRODUCTION_PASSWORD --body "your-production-redis-password"

# PostgreSQL (if you add it for user data)
gh secret set POSTGRES_STAGING_PASSWORD --body "your-staging-postgres-password"
gh secret set POSTGRES_PRODUCTION_PASSWORD --body "your-production-postgres-password"
```

### Database URLs (Variables)
```bash
# Staging database URLs
gh variable set STAGING_NEO4J_URL --body "bolt://staging-neo4j.tta-storytelling.com:7687"
gh variable set STAGING_REDIS_URL --body "redis://staging-redis.tta-storytelling.com:6379"

# Production database URLs
gh variable set PRODUCTION_NEO4J_URL --body "bolt://neo4j.tta-storytelling.com:7687"
gh variable set PRODUCTION_REDIS_URL --body "redis://redis.tta-storytelling.com:6379"
```

## 🔒 Security Configuration

### JWT Secrets
```bash
# Generate secure JWT secrets
JWT_STAGING_SECRET=$(openssl rand -base64 32)
JWT_PRODUCTION_SECRET=$(openssl rand -base64 32)

gh secret set JWT_STAGING_SECRET --body "$JWT_STAGING_SECRET"
gh secret set JWT_PRODUCTION_SECRET --body "$JWT_PRODUCTION_SECRET"
```

### Additional Security
```bash
# Encryption keys for sensitive therapeutic data
gh secret set ENCRYPTION_KEY_STAGING --body "$(openssl rand -base64 32)"
gh secret set ENCRYPTION_KEY_PRODUCTION --body "$(openssl rand -base64 32)"
```

## 🧪 Testing Configuration

### Test User Accounts
```bash
gh variable set TEST_USERNAME --body "e2e_test_user"
gh variable set TEST_EMAIL --body "test@tta-storytelling.com"
gh variable set PREMIUM_TEST_USERNAME --body "premium_test_user"
gh variable set PREMIUM_TEST_EMAIL --body "premium@tta-storytelling.com"

# Test passwords (secrets)
gh secret set TEST_USER_PASSWORD --body "secure-test-password-123"
gh secret set PREMIUM_TEST_PASSWORD --body "secure-premium-password-123"
```

## 📊 Performance Configuration

### Performance Budgets (Therapeutic Application Specific)
```bash
# Response time budgets (milliseconds)
gh variable set PERFORMANCE_BUDGET_AUTH_LOAD_TIME --body "2000"
gh variable set PERFORMANCE_BUDGET_DASHBOARD_LOAD_TIME --body "3000"
gh variable set PERFORMANCE_BUDGET_CHAT_RESPONSE_TIME --body "1500"  # Critical for therapeutic flow
gh variable set PERFORMANCE_BUDGET_CHARACTER_CREATION --body "2500"
gh variable set PERFORMANCE_BUDGET_WORLD_LOADING --body "3000"
```

## 🚀 Quick Setup Script

I've created a script to help you configure everything:

```bash
# Make the script executable
chmod +x github-secrets-setup.sh

# Run the interactive setup
./github-secrets-setup.sh
```

## 🔍 Verification

### Check Your Configuration
```bash
# List all secrets (names only, values are hidden)
gh secret list

# List all variables
gh variable list

# Test a workflow that uses these secrets
gh workflow run e2e-tests.yml
```

### Validate in GitHub UI
1. Go to your repository on GitHub
2. Navigate to Settings → Secrets and variables → Actions
3. Verify all secrets and variables are present
4. Check that no sensitive data is in variables (should be in secrets)

## 🎯 TTA-Specific Recommendations

### Therapeutic Application Considerations
1. **Error Monitoring**: Essential for user safety - configure Sentry
2. **Performance**: Fast response times critical for therapeutic flow
3. **Security**: Healthcare data requires extra security measures
4. **Monitoring**: Real-time monitoring for crisis detection features

### Staging Environment Priority
Set up staging first to test:
- Therapeutic content delivery
- Crisis detection systems
- Performance under load
- Security measures

### Production Readiness Checklist
- [ ] All secrets configured with production values
- [ ] Performance budgets validated
- [ ] Security scanning enabled
- [ ] Monitoring and alerting configured
- [ ] Backup and disaster recovery tested

## 🆘 Troubleshooting

### Common Issues
1. **Secret not found**: Check spelling and ensure it's a secret, not a variable
2. **Variable not accessible**: Ensure it's a variable, not a secret
3. **Workflow failures**: Check that all required secrets/variables are set
4. **Permission errors**: Ensure you have admin access to the repository

### Getting Help
- Check your existing workflows in `.github/workflows/`
- Review your deployment guides: `PRODUCTION_DEPLOYMENT_GUIDE.md`
- Validate configuration with: `./scripts/validate-repository-config.sh`


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs integration github secrets guide document]]
