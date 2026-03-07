---
title: Neo4j Staging Monitoring Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/component-promotion/NEO4J_STAGING_MONITORING_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/Neo4j Staging Monitoring Guide]]

**Component**: Neo4j
**Environment**: Staging
**Monitoring Period**: 7 days (2025-10-09 to 2025-10-16)
**Target Uptime**: ≥99.5%

---

## Quick Start

### 1. Verify Deployment

```bash
# Check if Neo4j staging is running
docker ps | grep tta-neo4j-staging

# Test connection
docker exec tta-neo4j-staging cypher-shell -u neo4j -p staging_password_change_me "RETURN 1"

# Access Neo4j Browser
open http://localhost:7476
```

### 2. Setup Automated Monitoring

**Option A: Using Cron (Recommended)**

```bash
# Edit crontab
crontab -e

# Add this line to run health checks every 5 minutes
*/5 * * * * cd /home/thein/recovered-tta-storytelling && ./scripts/monitor-neo4j-staging.sh >> /dev/null 2>&1
```

**Option B: Using systemd Timer**

```bash
# Create systemd service
sudo tee /etc/systemd/system/neo4j-staging-monitor.service << EOF
[Unit]
Description=Neo4j Staging Health Monitor
After=docker.service

[Service]
Type=oneshot
WorkingDirectory=/home/thein/recovered-tta-storytelling
ExecStart=/home/thein/recovered-tta-storytelling/scripts/monitor-neo4j-staging.sh
User=thein
EOF

# Create systemd timer
sudo tee /etc/systemd/system/neo4j-staging-monitor.timer << EOF
[Unit]
Description=Neo4j Staging Health Monitor Timer
Requires=neo4j-staging-monitor.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min
AccuracySec=1min

[Install]
WantedBy=timers.target
EOF

# Enable and start timer
sudo systemctl daemon-reload
sudo systemctl enable neo4j-staging-monitor.timer
sudo systemctl start neo4j-staging-monitor.timer

# Check timer status
sudo systemctl status neo4j-staging-monitor.timer
```

**Option C: Manual Monitoring (Not Recommended)**

```bash
# Run manually every 5 minutes
watch -n 300 ./scripts/monitor-neo4j-staging.sh
```

### 3. Daily Check-In

Run this command once per day to review metrics:

```bash
# Generate daily report
python scripts/analyze-neo4j-staging-metrics.py --days 1

# View last 24 hours of health checks
tail -n 288 logs/staging/neo4j-health.log  # 288 = 24 hours * 12 checks/hour
```

---

## Monitoring Metrics

### Health Checks

**Location**: `logs/staging/neo4j-health.log`

**Format**: CSV with columns:
- `timestamp`: Human-readable timestamp
- `timestamp_unix`: Unix timestamp
- `status`: UP or DOWN
- `response_time_ms`: Response time in milliseconds
- `error`: Error message (if any)

**Frequency**: Every 5 minutes (288 checks per day)

### Performance Metrics

**Location**: `logs/staging/neo4j-metrics.log`

**Format**: CSV with columns:
- `timestamp`: Human-readable timestamp
- `timestamp_unix`: Unix timestamp
- `cpu_percent`: CPU usage percentage
- `memory_usage`: Memory usage (e.g., "1.39GiB / 6GiB")
- `memory_percent`: Memory usage percentage
- `network_io`: Network I/O
- `block_io`: Block I/O
- `db_size`: Database size (if available)
- `node_count`: Number of nodes in database
- `relationship_count`: Number of relationships in database

**Frequency**: Every 5 minutes (when health check passes)

---

## Success Criteria

### Uptime Target

**Requirement**: ≥99.5% uptime over 7 days

**Calculation**:
- Total minutes in 7 days: 10,080 minutes
- Maximum allowed downtime: 50.4 minutes
- Minimum required uptime: 10,029.6 minutes

**Monitoring**:
- Health checks every 5 minutes = 2,016 total checks
- Maximum allowed failures: 10 checks (50 minutes)
- Minimum required successes: 2,006 checks

### Performance Benchmarks

**Response Time**:
- Target: <100ms average
- Acceptable: <500ms average
- Warning: >500ms average

**Resource Usage**:
- CPU: <50% average
- Memory: <80% of allocated (4.8GB of 6GB)

---

## Troubleshooting

### Neo4j Not Responding

```bash
# Check container status
docker ps -a | grep tta-neo4j-staging

# Check container logs
docker logs tta-neo4j-staging --tail 100

# Restart if needed
docker restart tta-neo4j-staging

# Wait for health check
sleep 30
docker exec tta-neo4j-staging cypher-shell -u neo4j -p staging_password_change_me "RETURN 1"
```

### High Memory Usage

```bash
# Check current usage
docker stats tta-neo4j-staging --no-stream

# Check Neo4j memory settings
docker exec tta-neo4j-staging neo4j-admin server memory-recommendation

# Adjust if needed (requires restart)
# Edit docker-compose.neo4j-staging.yml and redeploy
```

### Monitoring Not Running

```bash
# Check cron job
crontab -l | grep neo4j

# Check systemd timer
sudo systemctl status neo4j-staging-monitor.timer

# Check log files exist
ls -lh logs/staging/neo4j-*.log

# Run manual health check
./scripts/monitor-neo4j-staging.sh
```

---

## Daily Checklist

### Morning Check (9:00 AM)

- [ ] Run daily metrics analysis: `python scripts/analyze-neo4j-staging-metrics.py --days 1`
- [ ] Review uptime percentage (should be >99%)
- [ ] Check for any errors in health log
- [ ] Verify monitoring is still running

### Evening Check (5:00 PM)

- [ ] Run metrics analysis again
- [ ] Review any incidents or downtime
- [ ] Check resource usage trends
- [ ] Document any issues in incident log

---

## Weekly Report (End of 7 Days)

### Generate Final Report

```bash
# Generate comprehensive 7-day report
python scripts/analyze-neo4j-staging-metrics.py --days 7 > docs/component-promotion/NEO4J_STAGING_7DAY_REPORT.md

# Check if uptime target met
if [ $? -eq 0 ]; then
    echo "✅ Uptime target MET - Ready for production promotion"
else
    echo "❌ Uptime target NOT MET - Additional monitoring needed"
fi
```

### Report Contents

The final report should include:
- Total health checks performed
- Uptime percentage
- Downtime incidents (if any)
- Average response time
- Resource usage statistics
- Performance trends
- Recommendation for production promotion

---

## Incident Response

### If Downtime Detected

1. **Immediate**:
   - Check container status
   - Review logs for errors
   - Attempt restart if needed
   - Document incident

2. **Investigation**:
   - Determine root cause
   - Check system resources
   - Review recent changes
   - Document findings

3. **Resolution**:
   - Implement fix
   - Verify health restored
   - Update incident log
   - Adjust monitoring if needed

4. **Follow-Up**:
   - Review incident in daily check-in
   - Update troubleshooting guide
   - Consider preventive measures

### Incident Log Template

```markdown
## Incident: [Brief Description]

**Date**: YYYY-MM-DD HH:MM
**Duration**: X minutes
**Impact**: Downtime / Performance degradation
**Root Cause**: [Description]
**Resolution**: [Steps taken]
**Prevention**: [Future measures]
```

---

## Contact Information

**Component Owner**: theinterneti
**Escalation**: Create GitHub issue with label `component:neo4j` and `environment:staging`
**Documentation**: `docs/component-promotion/`

---

## Monitoring Schedule

| Day | Date | Morning Check | Evening Check | Notes |
|-----|------|---------------|---------------|-------|
| 1 | 2025-10-09 | ✅ | ⏳ | Deployment day |
| 2 | 2025-10-10 | ⏳ | ⏳ | |
| 3 | 2025-10-11 | ⏳ | ⏳ | |
| 4 | 2025-10-12 | ⏳ | ⏳ | |
| 5 | 2025-10-13 | ⏳ | ⏳ | |
| 6 | 2025-10-14 | ⏳ | ⏳ | |
| 7 | 2025-10-15 | ⏳ | ⏳ | |
| Final | 2025-10-16 | ✅ Generate Report | | |

---

**Last Updated**: 2025-10-09
**Next Review**: 2025-10-16 (End of monitoring period)


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___docs component promotion neo4j staging monitoring guide document]]
