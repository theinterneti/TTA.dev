---
title: 🎯 Sentry Integration Guide for TTA Storytelling
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/integration/SENTRY_INTEGRATION_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/🎯 Sentry Integration Guide for TTA Storytelling]]

## 📋 Overview

Sentry has been successfully integrated into your TTA (Therapeutic Text Adventure) storytelling project to provide:

- **Error Monitoring**: Automatic capture and reporting of application errors
- **Performance Tracking**: Transaction and query performance monitoring
- **Therapeutic Data Protection**: Built-in filtering to prevent sensitive therapeutic content from being sent to Sentry
- **Environment-Specific Configuration**: Different settings for development, staging, and production

## 🔧 Configuration

### Environment Variables

Add these to your `.env` file or set as environment variables:

```bash
# Required
SENTRY_DSN=https://62083b32298f29b9492a2d00702a3bf3@o4510032074178560.ingest.us.sentry.io/4510032076472320

# Optional (with defaults)
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=1.0
SENTRY_PROFILES_SAMPLE_RATE=1.0
SENTRY_SEND_DEFAULT_PII=false
SENTRY_ENABLE_LOGS=true
```

### GitHub Secrets (Production)

For production deployment, set these as GitHub secrets:

```bash
# Set your production Sentry DSN
gh secret set SENTRY_DSN --body "https://62083b32298f29b9492a2d00702a3bf3@o4510032074178560.ingest.us.sentry.io/4510032076472320"

# Set environment-specific settings
gh variable set SENTRY_ENVIRONMENT --body "production"
gh variable set SENTRY_TRACES_SAMPLE_RATE --body "0.1"  # Lower for production
```

## 🚀 Quick Start

### 1. Set Your Sentry DSN

```bash
# In your terminal or .env file
export SENTRY_DSN="https://62083b32298f29b9492a2d00702a3bf3@o4510032074178560.ingest.us.sentry.io/4510032076472320"
```

### 2. Test the Integration

```bash
# Run the integration test
cd src/player_experience/api
python test_sentry_integration.py
```

### 3. Start Your Application

```bash
# The FastAPI app will automatically initialize Sentry
uvicorn src.player_experience.api.app:app --reload
```

## 🔒 Therapeutic Data Protection

The integration includes built-in protection for sensitive therapeutic data:

### Automatically Filtered Data
- User passwords and API keys
- Therapeutic session content
- Patient notes and personal information
- Authorization headers and tokens

### Safe Error Reporting
```python
from src.player_experience.api.sentry_config import capture_therapeutic_error

try:
    # Your code here
    pass
except Exception as e:
    # This will automatically filter sensitive data
    capture_therapeutic_error(
        e,
        context={"endpoint": "/api/v1/sessions"},
        user_id="user123",  # Will be hashed for privacy
        session_id="session456"  # Will be hashed for privacy
    )
```

## 📊 Environment-Specific Settings

### Development
- **Traces Sample Rate**: 100% (capture all transactions)
- **Profiles Sample Rate**: 100% (profile all transactions)
- **Send PII**: False (never send personal information)

### Staging
- **Traces Sample Rate**: 20% (sample for testing)
- **Profiles Sample Rate**: 20%
- **Send PII**: False

### Production
- **Traces Sample Rate**: 10% (minimal sampling for performance)
- **Profiles Sample Rate**: 10%
- **Send PII**: False (critical for therapeutic applications)

## 🧪 Testing

### Manual Testing
```bash
# Set your DSN and run the test
export SENTRY_DSN="your-dsn-here"
python src/player_experience/api/test_sentry_integration.py
```

### Expected Results
- ✅ Configuration loaded successfully
- ✅ Test errors captured with sensitive data filtered
- ✅ Performance transactions recorded
- ✅ Messages logged with appropriate levels

## 📈 Monitoring Dashboard

After integration, you can monitor your application at:
- **Sentry Dashboard**: https://sentry.io/organizations/your-org/projects/
- **Error Tracking**: Real-time error reports with stack traces
- **Performance Monitoring**: Transaction times and database query performance
- **Release Tracking**: Error rates across different deployments

## 🔧 Advanced Configuration

### Custom Error Context
```python
from src.player_experience.api.sentry_config import capture_therapeutic_message

# Log important application events
capture_therapeutic_message(
    "User completed therapeutic session",
    level="info",
    context={
        "session_duration": "45_minutes",
        "completion_status": "successful"
    }
)
```

### Performance Monitoring
```python
import sentry_sdk

# Track custom performance metrics
with sentry_sdk.start_transaction(op="therapeutic_session", name="process_user_input"):
    # Your therapeutic processing code
    with sentry_sdk.start_span(op="ai_processing", description="Generate therapeutic response"):
        # AI model processing
        pass
```

## 🚨 Troubleshooting

### Common Issues

1. **"Sentry DSN not configured"**
   - Ensure `SENTRY_DSN` environment variable is set
   - Check that the DSN format is correct

2. **No events appearing in Sentry**
   - Verify the DSN is correct
   - Check that your environment allows outbound HTTPS connections
   - Ensure sample rates are > 0

3. **Too many events in development**
   - Lower `SENTRY_TRACES_SAMPLE_RATE` for development
   - Use environment-specific configuration

### Debug Mode
```bash
# Enable Sentry debug logging
export API_DEBUG=true
export SENTRY_DEBUG=true
```

## 🔐 Security Best Practices

1. **Never commit DSN to code**: Always use environment variables
2. **Use different projects**: Separate Sentry projects for dev/staging/prod
3. **Monitor data sent**: Regularly review what data is being captured
4. **Set up alerts**: Configure alerts for critical errors in production
5. **Review releases**: Use Sentry's release tracking for deployment monitoring

## 📚 Additional Resources

- [Sentry FastAPI Documentation](https://docs.sentry.io/platforms/python/guides/fastapi/)
- [Sentry Performance Monitoring](https://docs.sentry.io/product/performance/)
- [Data Privacy and Compliance](https://docs.sentry.io/data-management/sensitive-data/)

## ✅ Integration Checklist

- [x] Sentry SDK installed with FastAPI integration
- [x] Configuration system updated with Sentry settings
- [x] Therapeutic data filtering implemented
- [x] Environment-specific configurations created
- [x] Error handlers updated to use Sentry
- [x] Performance monitoring enabled
- [x] Test script created for validation
- [x] Documentation provided

Your TTA storytelling application now has comprehensive error monitoring and performance tracking while maintaining the highest standards of therapeutic data privacy! 🎉


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs integration sentry integration guide document]]
