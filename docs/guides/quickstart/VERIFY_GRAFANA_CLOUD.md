# Verify Grafana Cloud Integration ✅

**Status:** Alloy is successfully sending metrics to Grafana Cloud US West!

## Quick Verification

### 1. Check Grafana Cloud Dashboard

Open your Grafana Cloud instance:
```
https://theinterneti.grafana.net/
```

### 2. Explore TTA.dev Metrics

Go to **Explore** → Select **Mimir** data source → Run these queries:

#### Check if TTA.dev metrics are arriving:
```promql
tta_workflow_executions_total
```

#### View primitive execution counts:
```promql
sum by (primitive_name, status) (tta_primitive_executions_total)
```

#### Monitor execution duration (p95):
```promql
histogram_quantile(0.95,
  sum by (le, primitive_type) (
    rate(tta_execution_duration_seconds_bucket[5m])
  )
)
```

#### See all TTA.dev metrics:
```promql
{job="tta-primitives"}
```

### 3. What You Should See

**Metrics Currently Flowing:**
- ✅ `tta_workflow_executions_total` - Total workflow executions
- ✅ `tta_primitive_executions_total` - Individual primitive calls
- ✅ `tta_execution_duration_seconds` - Latency distributions
- ✅ Python runtime metrics (GC, memory, etc.)

**Current Data (as of setup):**
- 5 workflow executions (SequentialPrimitive)
- 10 primitive executions (SimplePrimitive)
- Execution durations tracked in histogram buckets

### 4. Local Verification

Check metrics are being scraped locally:
```bash
# Alloy internal metrics (shows remote_write status)
curl -s http://localhost:12345/metrics | grep prometheus_remote_storage

# TTA.dev application metrics (scraped from port 9464)
curl -s http://localhost:9464/metrics | grep ^tta_
```

## Data Flow Confirmation

```
┌─────────────────────────────────────────────────────────┐
│ TTA.dev Application                                      │
│ (InstrumentedPrimitive → Prometheus metrics)            │
│ Port 9464: /metrics endpoint                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓ Scrape every 30s
┌─────────────────────────────────────────────────────────┐
│ Grafana Alloy (Local)                                   │
│ - Scrapes localhost:9464/metrics                        │
│ - Processes with relabeling rules                       │
│ - Buffers in WAL                                        │
│ Port 12345: Alloy internal metrics                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓ Remote Write (HTTPS)
┌─────────────────────────────────────────────────────────┐
│ Grafana Cloud (US West - prod-us-west-0)               │
│ Endpoint: prometheus-prod-36                            │
│ Stack ID: 2497221                                       │
│ URL: https://theinterneti.grafana.net/                  │
└─────────────────────────────────────────────────────────┘
```

**Verification Results:**
- ✅ Alloy scraping: http://localhost:9464/metrics
- ✅ Remote write active: 301,559 bytes sent
- ✅ Zero retry failures
- ✅ TTA.dev metrics present

## Current System Status

| Component | Status | Details |
|-----------|--------|---------|
| Grafana Alloy | ✅ Running | PID 24591, 37.4M memory |
| Metrics Endpoint | ✅ Active | Port 9464, TTA metrics present |
| Remote Write | ✅ Connected | US West (prod-us-west-0) |
| Data Sent | ✅ 301 KB | Zero retry failures |
| Systemd Service | ✅ Enabled | Auto-starts on boot |

## Next Steps

### 1. Create Custom Dashboard

1. Go to **Dashboards** → **New Dashboard**
2. Add panels with queries from above
3. Save as "TTA.dev Primitives Overview"

### 2. Test with Real Workflow

Run a test workflow to generate fresh metrics:
```bash
cd /home/thein/repos/TTA.dev
uv run python test_observability.py my-test-service
```

Watch metrics update in Grafana Cloud (may take 30-60 seconds for new data).

### 3. Set Up Alerts (Optional)

Create alerts for:
- High error rates: `rate(tta_primitive_executions_total{status="error"}[5m]) > 0.1`
- Slow executions: `histogram_quantile(0.95, ...) > 5`
- Service down: `up{job="tta-primitives"} == 0`

## Troubleshooting

### "No data" in Grafana Cloud

**Wait 30-60 seconds** - Initial data sync takes time

**Check Alloy logs:**
```bash
sudo journalctl -u alloy -f | grep -E "remote_write|error"
```

**Verify local metrics:**
```bash
curl http://localhost:9464/metrics | grep tta_
```

### Metrics disappeared

**Check if app is running:**
```bash
# Your TTA.dev app should be exposing metrics on port 9464
curl http://localhost:9464/metrics
```

**Restart Alloy if needed:**
```bash
sudo systemctl restart alloy
sudo systemctl status alloy
```

### Connection issues

**Test Grafana Cloud endpoint:**
```bash
curl -u "2497221:$GRAFANA_CLOUD_TOKEN" \
  https://prometheus-prod-36-prod-us-west-0.grafana.net/api/v1/query?query=up
```

## Configuration Files

All configuration is in place:
- ✅ `/etc/alloy/config.alloy` - Main configuration
- ✅ `/etc/default/alloy` - Environment variables
- ✅ `/usr/lib/systemd/system/alloy.service` - Systemd service
- ✅ `/var/lib/alloy/` - Data directory (WAL storage)

## Migration Complete ✅

**Before:** 5 Docker containers (800MB+ memory)
- prometheus
- grafana
- loki
- tempo
- node-exporter

**After:** 1 Grafana Alloy service (37.4M memory)
- All metrics → Grafana Cloud US West
- Native Linux systemd service
- 95% memory reduction
- Auto-start on boot
- Production-ready

## Resources

- **Grafana Cloud:** https://theinterneti.grafana.net/
- **Stack ID:** 2497221
- **Region:** US West (prod-us-west-0)
- **Cluster:** mimir-prod-36
- **Alloy Docs:** https://grafana.com/docs/alloy/latest/

---

**Setup Completed:** 2025-11-15 19:34 PST
**Next Action:** Open Grafana Cloud and explore your metrics!


---
**Logseq:** [[TTA.dev/Docs/Quickstart/Verify_grafana_cloud]]
