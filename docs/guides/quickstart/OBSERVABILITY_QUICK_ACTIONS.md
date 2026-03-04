# 🚀 TTA.dev Observability - Quick Actions

**Setup Status:** ✅ Complete | **Last Updated:** 2025-11-15 20:30 PST

---

## ⚡ Quick Commands

### Check System Status

```bash
# Alloy service status
sudo systemctl status alloy

# View recent logs
sudo journalctl -u alloy --since "10 minutes ago"

# Check metrics locally
curl http://localhost:9464/metrics | grep tta_
```

### Run Tests

```bash
# Quick observability test
uv run python test_observability.py my-service

# Comprehensive workflow tests
uv run python test_real_workflow.py

# Check test results
curl http://localhost:9464/metrics | grep tta_workflow
```

### Verify Data Flow

```bash
# 1. Local metrics endpoint
curl http://localhost:9464/metrics | grep tta_

# 2. Alloy scraping and sending
curl http://localhost:12345/metrics | grep prometheus_remote_storage_samples_total

# 3. Check Grafana Cloud
# Open: https://theinterneti.grafana.net/explore
# Query: tta_workflow_executions_total
```

### Restart Service (if needed)

```bash
# Restart Alloy
sudo systemctl restart alloy

# Check status
sudo systemctl status alloy

# View startup logs
sudo journalctl -u alloy -f
```

---

## 📊 Grafana Cloud Quick Queries

**URL:** https://theinterneti.grafana.net/explore

### 1. Workflow Health

```promql
# Total executions
tta_workflow_executions_total

# Success vs failure
sum by (status) (tta_workflow_executions_total)

# Execution rate (per minute)
rate(tta_workflow_executions_total[5m]) * 60
```

### 2. Performance

```promql
# P95 latency
histogram_quantile(0.95,
  sum by (le) (rate(tta_execution_duration_seconds_bucket[5m]))
)

# Average duration
avg(rate(tta_execution_duration_seconds_sum[5m])) /
avg(rate(tta_execution_duration_seconds_count[5m]))
```

### 3. Primitive Breakdown

```promql
# Executions per primitive
sum by (primitive_name) (tta_primitive_executions_total)

# Primitive success rate
sum by (primitive_name, status) (tta_primitive_executions_total)
```

### 4. Cache Performance

```promql
# Cache hit rate
sum(tta_cache_hits) / sum(tta_cache_total) * 100

# Cache efficiency
sum(tta_cache_hits) / sum(tta_primitive_executions_total{primitive_name="CachePrimitive"})
```

---

## 🔧 Configuration Locations

### Grafana Alloy

| File | Purpose |
|------|---------|
| `/etc/alloy/config.alloy` | Main configuration |
| `/etc/default/alloy` | Environment variables |
| `/usr/lib/systemd/system/alloy.service` | Systemd service |
| `/var/lib/alloy/` | Data directory (WAL) |

### Quick Edit Config

```bash
# Edit main config
sudo nano /etc/alloy/config.alloy

# Edit environment
sudo nano /etc/default/alloy

# Reload after changes
sudo systemctl daemon-reload
sudo systemctl restart alloy
```

---

## 📈 Current Metrics Summary

**As of:** 2025-11-15 20:30 PST

| Metric | Value |
|--------|-------|
| Alloy Memory | 37.4M |
| Samples Sent | 16,775+ |
| Retry Failures | 0 |
| Workflows Tested | 5 |
| Primitives Tested | 15+ |
| Uptime | 1+ hour |

---

## 🎯 Common Tasks

### 1. View Latest Metrics

```bash
# TTA.dev metrics
curl -s http://localhost:9464/metrics | grep -E "^tta_" | head -20

# Python runtime
curl -s http://localhost:9464/metrics | grep python_

# All metrics
curl http://localhost:9464/metrics
```

### 2. Check Alloy Performance

```bash
# Alloy internal metrics
curl -s http://localhost:12345/metrics | grep alloy_build_info

# Remote write stats
curl -s http://localhost:12345/metrics | grep prometheus_remote_storage
```

### 3. Monitor Logs Live

```bash
# Follow Alloy logs
sudo journalctl -u alloy -f

# Filter for errors
sudo journalctl -u alloy | grep -i error

# Last 50 lines
sudo journalctl -u alloy -n 50
```

### 4. Run Application with Observability

```bash
cd /home/thein/repos/TTA.dev

# Your TTA.dev application here
# Metrics automatically exposed on :9464
uv run python your_app.py

# Check metrics are being generated
curl http://localhost:9464/metrics | grep tta_
```

---

## 🚨 Troubleshooting Quick Fixes

### Alloy Not Running

```bash
# Start service
sudo systemctl start alloy

# Enable auto-start
sudo systemctl enable alloy

# Check for errors
sudo journalctl -u alloy -xe
```

### No Metrics Showing

```bash
# 1. Check app is running
ps aux | grep python

# 2. Check metrics endpoint
curl http://localhost:9464/metrics

# 3. Check Alloy is scraping
curl http://localhost:12345/metrics | grep tta_
```

### Data Not in Grafana Cloud

```bash
# 1. Wait 30-60 seconds for initial sync

# 2. Check Alloy logs for errors
sudo journalctl -u alloy -f | grep -E "error|remote_write"

# 3. Verify credentials
cat /etc/default/alloy

# 4. Test endpoint manually
curl -u "2497221:$GRAFANA_CLOUD_TOKEN" \
  https://prometheus-prod-36-prod-us-west-0.grafana.net/api/v1/query?query=up
```

### High Memory Usage

```bash
# Check current usage
systemctl status alloy | grep Memory

# If too high, adjust scrape interval in /etc/alloy/config.alloy:
# scrape_interval = "60s"  # Increase from 30s

sudo systemctl restart alloy
```

---

## 📚 Documentation Quick Links

### Quick Start Guides

- **5-Minute Setup:** `docs/quickstart/OBSERVABILITY_UNIFIED_QUICKSTART.md`
- **Verification:** `docs/quickstart/VERIFY_GRAFANA_CLOUD.md`
- **Test Results:** `docs/quickstart/OBSERVABILITY_TEST_RESULTS.md`

### Comprehensive Guides

- **Architecture:** `docs/guides/UNIFIED_OBSERVABILITY_ARCHITECTURE.md`
- **Linux Native:** `docs/guides/LINUX_NATIVE_OBSERVABILITY.md`
- **Migration:** `docs/guides/DOCKER_FREE_OBSERVABILITY_MIGRATION.md`
- **Multi-Workspace:** `docs/guides/MULTI_WORKSPACE_OBSERVABILITY.md`

### Complete Summary

- **Setup Complete:** `docs/OBSERVABILITY_SETUP_COMPLETE.md`

---

## 🎓 Learning Resources

### Grafana Cloud

- **Dashboard:** https://theinterneti.grafana.net/
- **Explore:** https://theinterneti.grafana.net/explore
- **Dashboards:** https://theinterneti.grafana.net/dashboards

### Documentation

- **Alloy:** https://grafana.com/docs/alloy/latest/
- **Prometheus Query:** https://prometheus.io/docs/prometheus/latest/querying/basics/
- **OpenTelemetry:** https://opentelemetry.io/docs/

---

## ✅ Health Check Checklist

Run this checklist to verify everything is working:

- [ ] Alloy service running: `sudo systemctl status alloy`
- [ ] Metrics endpoint active: `curl http://localhost:9464/metrics`
- [ ] Alloy scraping: `curl http://localhost:12345/metrics | grep samples_total`
- [ ] Data in Grafana Cloud: Query `tta_workflow_executions_total`
- [ ] Logs clean: `sudo journalctl -u alloy | grep -i error`
- [ ] Memory usage OK: Should be <50M
- [ ] Auto-start enabled: `systemctl is-enabled alloy`

**All checked?** System is healthy! ✅

---

**Quick Actions Card Version:** 1.0
**Last Updated:** 2025-11-15 20:30 PST
**System Status:** Production Ready 🚀


---
**Logseq:** [[TTA.dev/Docs/Quickstart/Observability_quick_actions]]
