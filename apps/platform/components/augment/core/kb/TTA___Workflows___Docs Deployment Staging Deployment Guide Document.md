---
title: TTA Staging Environment - Deployment Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/deployment/STAGING_DEPLOYMENT_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/TTA Staging Environment - Deployment Guide]]

**Environment**: Staging
**Last Updated**: 2025-10-08
**Components Deployed**: Carbon

---

## Overview

This guide documents the deployment process for TTA components to the staging environment.

---

## Staging Environment Setup

### Infrastructure Requirements

**Server Requirements**:
- Ubuntu 22.04 LTS or later
- Python 3.12+
- 4GB RAM minimum
- 20GB disk space
- Network access for monitoring

**Dependencies**:
- Python 3.12+ runtime
- UV package manager
- codecarbon library
- Git

---

## Carbon Component Deployment

### 1. Directory Structure Setup

```bash
# Create staging directory structure
sudo mkdir -p /var/log/tta/staging/codecarbon
sudo mkdir -p /opt/tta/staging
sudo mkdir -p /etc/tta/staging

# Set permissions
sudo chown -R tta-user:tta-group /var/log/tta/staging
sudo chown -R tta-user:tta-group /opt/tta/staging
sudo chmod 755 /var/log/tta/staging/codecarbon
```

### 2. Environment Configuration

**File**: `/etc/tta/staging/environment`

```bash
# Carbon Component Configuration
export CARBON_OUTPUT_DIR="/var/log/tta/staging/codecarbon"
export CARBON_PROJECT_NAME="TTA-Staging"
export CARBON_LOG_LEVEL="info"
export CARBON_MEASUREMENT_INTERVAL="15"

# Environment
export TTA_ENV="staging"
export TTA_CONFIG="/etc/tta/staging/config.yaml"
```

### 3. Deploy Carbon Component

```bash
# Navigate to staging directory
cd /opt/tta/staging

# Clone repository (or pull latest)
git clone https://github.com/theinterneti/TTA.git .
# OR
git pull origin main

# Install dependencies
uv sync

# Copy staging configuration
cp config/staging.yaml /etc/tta/staging/config.yaml

# Source environment
source /etc/tta/staging/environment

# Verify component loads
uv run python -c "from src.components.carbon_component import CarbonComponent; from src.orchestration import TTAConfig; config = TTAConfig(); carbon = CarbonComponent(config); print('✅ Carbon component loaded successfully')"
```

### 4. Health Check

```bash
# Run health check script
uv run python scripts/health_check_carbon.py

# Expected output:
# ✅ Carbon component: OK
# ✅ Output directory writable: /var/log/tta/staging/codecarbon
# ✅ codecarbon library: Available
# ✅ Configuration: Valid
```

### 5. Integration Tests

```bash
# Run integration tests in staging
uv run pytest tests/integration/test_carbon_staging.py -v

# Verify emissions tracking
uv run python scripts/test_carbon_emissions.py

# Check log output
ls -lh /var/log/tta/staging/codecarbon/
```

---

## Monitoring Setup

### Health Check Endpoint

**File**: `scripts/health_check_carbon.py`

```python
#!/usr/bin/env python3
"""Health check script for Carbon component in staging."""

from pathlib import Path
from src.components.carbon_component import CarbonComponent
from src.orchestration import TTAConfig

def health_check():
    """Perform health check on Carbon component."""
    try:
        # Load configuration
        config = TTAConfig()

        # Initialize component
        carbon = CarbonComponent(config)

        # Check output directory
        output_dir = Path(carbon.output_dir)
        if not output_dir.exists():
            print(f"❌ Output directory does not exist: {output_dir}")
            return False

        if not output_dir.is_dir():
            print(f"❌ Output path is not a directory: {output_dir}")
            return False

        # Check write permissions
        test_file = output_dir / ".health_check"
        try:
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            print(f"❌ Cannot write to output directory: {e}")
            return False

        # Check codecarbon availability
        try:
            from codecarbon import EmissionsTracker
            print("✅ codecarbon library: Available")
        except ImportError:
            print("⚠️  codecarbon library: Not available (graceful degradation)")

        print("✅ Carbon component: OK")
        print(f"✅ Output directory writable: {output_dir}")
        print("✅ Configuration: Valid")

        return True

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    sys.exit(0 if health_check() else 1)
```

### Monitoring Dashboard

**Prometheus Metrics** (if using Prometheus):

```yaml
# /etc/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'tta-staging-carbon'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

**Grafana Dashboard**:
- Carbon emissions over time
- Component health status
- Log file size monitoring
- Error rate tracking

### Alerting

**Alert Rules**:

```yaml
# High emissions alert
- alert: HighCarbonEmissions
  expr: carbon_emissions_kg > 1.0
  for: 5m
  labels:
    severity: warning
    component: carbon
  annotations:
    summary: "High carbon emissions detected"
    description: "Carbon emissions exceeded 1kg CO2eq threshold"

# Component failure alert
- alert: CarbonComponentDown
  expr: up{job="tta-staging-carbon"} == 0
  for: 2m
  labels:
    severity: critical
    component: carbon
  annotations:
    summary: "Carbon component is down"
    description: "Carbon component health check failing"
```

---

## Logging

### Log Aggregation

**Filebeat Configuration** (if using ELK stack):

```yaml
# /etc/filebeat/filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/tta/staging/carbon.log
      - /var/log/tta/staging/codecarbon/*.json
    fields:
      environment: staging
      component: carbon
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "tta-staging-carbon-%{+yyyy.MM.dd}"
```

### Log Rotation

**File**: `/etc/logrotate.d/tta-staging`

```
/var/log/tta/staging/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 tta-user tta-group
    sharedscripts
    postrotate
        systemctl reload tta-staging || true
    endscript
}

/var/log/tta/staging/codecarbon/*.json {
    weekly
    rotate 12
    compress
    delaycompress
    notifempty
    create 0644 tta-user tta-group
}
```

---

## Validation Checklist

### Pre-Deployment
- [ ] Staging server provisioned
- [ ] Python 3.12+ installed
- [ ] UV package manager installed
- [ ] Directory structure created
- [ ] Permissions set correctly
- [ ] Configuration file created
- [ ] Environment variables set

### Deployment
- [ ] Code deployed to staging
- [ ] Dependencies installed
- [ ] Configuration applied
- [ ] Component loads successfully
- [ ] Health check passes
- [ ] Integration tests pass

### Post-Deployment
- [ ] Emissions tracking functional
- [ ] Logs being written correctly
- [ ] Monitoring configured
- [ ] Alerting configured
- [ ] Log rotation configured
- [ ] Documentation updated

---

## Rollback Procedure

If deployment fails:

```bash
# 1. Stop the component
systemctl stop tta-staging-carbon

# 2. Restore previous version
cd /opt/tta/staging
git checkout <previous-commit-hash>

# 3. Reinstall dependencies
uv sync

# 4. Restart component
systemctl start tta-staging-carbon

# 5. Verify health
scripts/health_check_carbon.py
```

---

## Operations Runbook

### Start Component
```bash
systemctl start tta-staging-carbon
```

### Stop Component
```bash
systemctl stop tta-staging-carbon
```

### Restart Component
```bash
systemctl restart tta-staging-carbon
```

### Check Status
```bash
systemctl status tta-staging-carbon
scripts/health_check_carbon.py
```

### View Logs
```bash
# Real-time logs
tail -f /var/log/tta/staging/carbon.log

# Emissions data
ls -lh /var/log/tta/staging/codecarbon/
cat /var/log/tta/staging/codecarbon/emissions_*.json | jq .
```

### Clear Logs (if needed)
```bash
# Backup first
tar -czf /tmp/carbon-logs-backup-$(date +%Y%m%d).tar.gz /var/log/tta/staging/codecarbon/

# Clear old logs
find /var/log/tta/staging/codecarbon/ -name "*.json" -mtime +30 -delete
```

---

## Troubleshooting

### Component Won't Start

**Check**:
1. Python version: `python3 --version`
2. Dependencies: `uv sync`
3. Permissions: `ls -ld /var/log/tta/staging/codecarbon`
4. Configuration: `cat /etc/tta/staging/config.yaml`
5. Logs: `tail -100 /var/log/tta/staging/carbon.log`

### Emissions Not Being Tracked

**Check**:
1. codecarbon installed: `uv run python -c "import codecarbon; print('OK')"`
2. Output directory writable: `touch /var/log/tta/staging/codecarbon/test && rm /var/log/tta/staging/codecarbon/test`
3. Configuration: Verify `CARBON_OUTPUT_DIR` is set correctly
4. Component started: `systemctl status tta-staging-carbon`

### High Disk Usage

**Check**:
1. Log file sizes: `du -sh /var/log/tta/staging/codecarbon/`
2. Old emissions files: `find /var/log/tta/staging/codecarbon/ -name "*.json" -mtime +30`
3. Log rotation: `cat /etc/logrotate.d/tta-staging`

**Fix**:
```bash
# Archive old logs
tar -czf /backup/carbon-logs-$(date +%Y%m%d).tar.gz /var/log/tta/staging/codecarbon/
find /var/log/tta/staging/codecarbon/ -name "*.json" -mtime +30 -delete
```

---

## Security Considerations

1. **File Permissions**: Ensure only tta-user can write to log directories
2. **Environment Variables**: Store sensitive config in environment, not code
3. **Log Sanitization**: Ensure no sensitive data in emissions logs
4. **Access Control**: Limit SSH access to staging server
5. **Monitoring**: Alert on unusual emissions patterns (potential security issue)

---

## Next Steps

After Carbon deployment:
1. Deploy Narrative Coherence component
2. Deploy Gameplay Loop component
3. Deploy Model Management component
4. Set up inter-component integration tests
5. Configure end-to-end monitoring

---

**Last Updated**: 2025-10-08
**Deployed Components**: Carbon
**Status**: Staging environment ready for Carbon component


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs deployment staging deployment guide document]]
