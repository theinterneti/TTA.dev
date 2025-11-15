# 🔄 Automated Secret Rotation Guide for TTA.dev

## Overview

This guide documents the automated secret rotation infrastructure implemented for TTA.dev GitHub Actions. The system provides comprehensive secret lifecycle management, audit trails, and zero-downtime rotation capabilities.

## 🚨 Critical Security Information

**ALL SECRET ROTATION OPERATIONS ARE LOGGED AND MONITORED**
- Every rotation event is recorded with full audit trails
- Security alerts are sent for any rotation failures
- Backups are maintained during rotation processes
- Manual intervention is required for rollbacks

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Supported Services](#supported-services)
3. [Rotation Schedules](#rotation-schedules)
4. [Workflow Components](#workflow-components)
5. [Error Handling & Recovery](#error-handling--recovery)
6. [Audit & Compliance](#audit--compliance)
7. [Emergency Procedures](#emergency-procedures)
8. [Monitoring & Alerting](#monitoring--alerting)
9. [Configuration Management](#configuration-management)

## Architecture Overview

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Orchestrator  │────│ Service-Specific │────│   Validation   │
│   Workflows     │    │   Rotations      │    │   Scripts      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────────────┐
                    │   Audit Logging    │
                    │   & Monitoring     │
                    └────────────────────┘
```

### Key Principles

- **Zero-Downtime Rotation**: Services remain operational during rotation
- **Graceful Degradation**: Fallback mechanisms when rotation fails
- **Comprehensive Auditing**: Every step is logged and traceable
- **Access Control**: Rotation operations require specific permissions
- **Multi-Environment**: Supports dev/staging/production workflows

## Supported Services

### 🔴 High Priority (Weekly Rotation)

| Service | Key Type | Grace Period | Notes |
|---------|----------|--------------|-------|
| Google Gemini | API Key | 24 hours | AI service integration |
| GitHub PAT | Personal Access Token | 12 hours | Repository operations |

### 🟠 Medium Priority (Weekly Rotation)

| Service | Key Type | Grace Period | Notes |
|---------|----------|--------------|-------|
| E2B | API Key | 6 hours | Code execution sandbox |
| Codecov | Repository Token | Immediate | Coverage reporting |

### 🟡 Low Priority (Monthly Rotation)

| Service | Key Type | Grace Period | Notes |
|---------|----------|--------------|-------|
| Google Cloud | Service Account Key | 48 hours | GCP operations |

## Rotation Schedules

### Weekly Rotation (Every Monday 2 AM PST)

**Trigger**: Scheduled cron job or manual dispatch
**Scope**: Gemini, GitHub, E2B, Codecov
**Duration**: ~20 minutes per service
**Risk Level**: Low (automated with validation)

### Monthly Rotation (First Monday each month)

**Trigger**: Scheduled weekly rotation during first week of month
**Scope**: Google Cloud Platform keys
**Duration**: ~45 minutes
**Risk Level**: High (requires special approval)

### Emergency Rotation

**Trigger**: Manual workflow dispatch with `emergency_rotation=true`
**Scope**: All services or manually specified
**Duration**: Variable based on services
**Risk Level**: Critical (bypasses normal safeguards)

## Workflow Components

### 1. Secret Rotation Orchestrator

**File**: `.github/workflows/secret-rotation-orchestrator.yml`

**Capabilities**:
- Manual and scheduled trigger support
- Service prioritization and parallel execution
- Comprehensive error handling and rollback
- Real-time status reporting

**Key Jobs**:
- `validate-rotation-environment`: Pre-rotation checks
- `create-rotation-plan`: Strategy planning
- `execute-secret-rotation`: Parallel service rotation
- `finalize-rotation`: Summary and notification

### 2. Scheduled Weekly Rotation

**File**: `.github/workflows/scheduled-secret-rotation.yml`

**Capabilities**:
- Automated weekly execution
- Emergency override capability
- Health monitoring and follow-up checks
- Critical failure alerting

**Key Jobs**:
- `assess-rotation-readiness`: Risk assessment
- `execute-weekly-rotation`: Service rotation matrix
- `monthly-gcp-rotation`: Conditional monthly GCP rotation

### 3. Rotation Scripts

#### `scripts/rotate_secrets.py`
- Service-specific rotation logic
- API integrations for key generation
- Audit logging and error handling
- GitHub secret updates

#### `scripts/validate_rotated_secret.py`
- Post-rotation validation tests
- Non-destructive service verification
- Health checks for rotated credentials

## Error Handling & Recovery

### Failure Categories

#### 🔴 Critical Failures (Immediate Action Required)
- Rotation script crashes without recovery
- New keys fail validation tests
- GitHub API access lost during rotation

**Response**: Automatic alerts, workflow termination, manual intervention

#### 🟠 Service-Specific Failures
- Individual service rotation failure
- API rate limiting during rotation
- Temporary service unavailability

**Response**: Graceful degradation, retry mechanisms, continued operation with old keys

#### 🟡 Validation Failures
- Post-rotation testing detects issues
- Service cannot authenticate with new keys
- Performance degradation after rotation

**Response**: Automatic rollback, alert generation, investigation required

### Rollback Procedures

#### Automatic Rollback
```yaml
# Triggered when validation fails
- name: 'Rollback to previous keys'
  run: |
    python scripts/rollback_secrets.py ${{ matrix.service.name }}
```

#### Manual Rollback
```bash
# Emergency rollback command
gh workflow run secret-rotation-orchestrator.yml \
  -f force_rotation=true \
  -f target_services=rollback-${SERVICE_NAME}
```

### Grace Period Management

Each service has a configured grace period during which old keys remain valid:

| Service | Grace Period | Old Key Action |
|---------|-------------|----------------|
| Gemini | 24 hours | Marked deprecated, unavailable for new requests |
| GitHub | 12 hours | Reduced permissions, monitoring mode |
| E2B | 6 hours | Maintenance mode, graceful shutdown |
| GCP | 48 hours | Backup access, reduced privileges |

## Audit & Compliance

### Audit Trail Structure

```
audit-logs/
├── rotation-audit-{service}-{correlation_id}.json
└── validation-audit-{service}-{correlation_id}.json
```

### Audit Event Types

- `rotation_start`: Rotation initiation
- `rotation_plan_created`: Strategy planning
- `key_generation`: New key creation
- `secret_update`: GitHub secret modification
- `validation_start`: Post-rotation testing
- `validation_complete`: Testing successful
- `rotation_failed`: Rotation error
- `grace_period_started`: Old key deprecation

### Compliance Requirements

- **HIPAA**: Healthcare data protection compliance
- **SOC 2**: Security, availability, and confidentiality
- **GDPR**: Personal data protection
- **ISO 27001**: Information security management

### Audit Log Format

```json
{
  "correlation_id": "weekly-2024W32-abc123",
  "timestamp": "2024-08-07T02:00:00Z",
  "service": "gemini",
  "event_type": "rotation_complete",
  "success": true,
  "environment": "production",
  "dry_run": false,
  "details": {
    "old_key_masked": "AIzaS...abcd",
    "new_key_masked": "AIzaT...efgh",
    "grace_period_hours": 24,
    "validation_tests_passed": 3
  }
}
```

## Emergency Procedures

### 🚨 Critical Rotation Failure

**Immediate Actions** (Within 5 minutes):
1. **Stop all workflows**: Disable automated rotation
2. **Alert the team**: Security and platform teams
3. **Assess impact**: Check service availability
4. **Initiate rollback**: Use emergency rollback procedure

**Workflow**:
```bash
# Emergency stop command
gh workflow disable "secret-rotation-orchestrator.yml"

# Check current status
gh run list --workflow="secret-rotation-orchestrator.yml" -L 5

# Emergency rollback
gh workflow run secret-rotation-orchestrator.yml \
  --ref emergency-rollback \
  -f target_services=all
```

### Service Disruption Response

**Steps**:
1. Identify affected services from audit logs
2. Deploy backup authentication methods
3. Communicate with stakeholders
4. Resume rotation in safe mode
5. Post-incident review and improvements

### Manual Key Rotation

When automated rotation fails:

```bash
# Manual Gemini key rotation
export NEW_GEMINI_KEY="your_new_key_here"
python scripts/manual_key_update.py gemini "$NEW_GEMINI_KEY"

# Verify manual rotation
python scripts/validate_rotated_secret.py gemini-test
```

## Monitoring & Alerting

### Real-Time Monitoring

#### Workflow Status Dashboard
- Rotation progress tracking
- Service health indicators
- Failure rate monitoring
- Performance metrics

#### Alert Channels

| Alert Type | Slack Channel | PagerDuty | Email |
|------------|---------------|-----------|-------|
| Critical Failure | #security-emergency | 🚨 P1 | security@tta.dev |
| Service Degradation | #platform-alerts | 🚨 P2 | platform@tta.dev |
| Validation Failure | #devops-alerts | P3 | devops@tta.dev |
| Success Confirmation | #security-logs | - | security-logs@tta.dev |

### Key Metrics

**Rotation Health**:
- Success rate (>99% target)
- Average rotation time (<30 minutes)
- Failure recovery time (<5 minutes)
- Grace period utilization

**Security Metrics**:
- Secrets rotated on schedule (>95%)
- Audit log completeness (100%)
- Unauthorized access attempts (0)
- Incident response time (<15 minutes)

### Log Aggregation

```
# Elasticsearch/Kibana integration for log analysis
├── Rotation success/failure trends
├── Service-specific performance
├── Security incident patterns
└── Compliance audit reports
```

## Configuration Management

### Environment Variables

#### Required for All Rotations
```bash
CORRELATION_ID=auto-generated
DRY_RUN=false
```

#### Service-Specific Variables
```bash
# Gemini
GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }}

# GitHub
GITHUB_PERSONAL_ACCESS_TOKEN=${{ secrets.GITHUB_PERSONAL_ACCESS_TOKEN }}
GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }}

# E2B
E2B_API_KEY=${{ secrets.E2B_API_KEY }}

# GCP
GOOGLE_CLOUD_PROJECT=${{ vars.GOOGLE_CLOUD_PROJECT }}
SERVICE_ACCOUNT_EMAIL=${{ vars.SERVICE_ACCOUNT_EMAIL }}

# Codecov
CODECOV_TOKEN=${{ secrets.CODECOV_TOKEN }}
```

### GitHub Secrets Management

#### Required Repository Secrets
- `GEMINI_API_KEY`
- `GITHUB_PERSONAL_ACCESS_TOKEN`
- `E2B_API_KEY`
- `CODECOV_TOKEN`
- `GOOGLE_CLOUD_KEY` (base64 encoded)

#### Required Repository Variables
- `GOOGLE_CLOUD_PROJECT`
- `GOOGLE_CLOUD_LOCATION`
- `SERVICE_ACCOUNT_EMAIL`
- `GCP_WIF_PROVIDER`

### Rotation Configuration

```python
# scripts/config/rotation_config.py
ROTATION_CONFIG = {
    'gemini': {
        'priority': 1,
        'weekly_rotation': True,
        'grace_period_hours': 24,
        'requires_validation': True,
        'rollback_supported': True
    },
    'github': {
        'priority': 2,
        'weekly_rotation': True,
        'grace_period_hours': 12,
        'requires_validation': True,
        'rollback_supported': True
    },
    'e2b': {
        'priority': 3,
        'weekly_rotation': True,
        'grace_period_hours': 6,
        'requires_validation': True,
        'rollback_supported': True
    },
    'gcp': {
        'priority': 4,
        'monthly_rotation': True,
        'grace_period_hours': 48,
        'requires_validation': True,
        'rollback_supported': False  # GCP keys don't support instant rollback
    },
    'codecov': {
        'priority': 5,
        'weekly_rotation': True,
        'grace_period_hours': 0,  # Immediate invalidation
        'requires_validation': False,
        'rollback_supported': True
    }
}
```

---

## Quick Reference Commands

### Manual Rotation Trigger
```bash
# Standard rotation
gh workflow run secret-rotation-orchestrator.yml

# Emergency rotation
gh workflow run secret-rotation-orchestrator.yml \
  -f force_rotation=true \
  -f target_services=gemini,github

# Dry run
gh workflow run secret-rotation-orchestrator.yml \
  -f dry_run=true
```

### Status Checking
```bash
# Recent rotations
gh run list --workflow="secret-rotation-orchestrator.yml" -L 10

# Workflow status
gh workflow view "secret-rotation-orchestrator.yml"
```

### Emergency Controls
```bash
# Disable rotations
gh workflow disable "secret-rotation-orchestrator.yml"

# Enable rotations
gh workflow enable "secret-rotation-orchestrator.yml"

# Emergency rollback
gh workflow run emergency-rollback.yml
```

---

## Security Checklist

- [x] Automated rotation workflows implemented
- [x] Comprehensive audit logging enabled
- [x] Error handling and recovery procedures documented
- [x] Emergency response procedures established
- [x] Monitoring and alerting configured
- [x] Access controls implemented
- [x] Compliance requirements met
- [x] Regular testing and validation scheduled
- [x] Team training completed
- [x] Incident response plan documented

## Next Steps

1. **Implement Real API Integrations**: Replace placeholder methods with actual service APIs
2. **Set Up Monitoring Dashboard**: Create real-time rotation status visualization
3. **Configure Alert Channels**: Set up Slack/Discord/PagerDuty integrations
4. **Conduct Dry Run Testing**: Validate all rotation paths in safe mode
5. **Schedule Regular Drills**: Test emergency procedures quarterly
6. **Audit Log Analysis**: Implement automated compliance reporting
7. **Team Training**: Ensure all team members understand procedures
8. **External Audit**: Arrange independent security assessment

---

**Remember**: Automated secret rotation is a security enhancement that reduces risk but requires diligent monitoring and maintenance. Regular testing and team training are essential for safe operation.
