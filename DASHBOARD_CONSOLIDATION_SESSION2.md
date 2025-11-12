# Dashboard Consolidation Plan - Session 2

**Date:** November 11, 2025
**Status:** ✅ In Progress
**Owner:** Observability Team

---

## 🎯 Objective

Consolidate 8 fragmented Grafana dashboards across 4 directories into a single canonical location with improved organization and functionality.

---

## 📊 Current State Analysis

### Existing Dashboard Locations (Before Consolidation)

| Location | Files | Status | Action |
|----------|-------|--------|--------|
| `/config/grafana/dashboards/` | 3 dashboards | ✅ Keep as production | Migrate to production/ |
| `/grafana/dashboards/` | 1 dashboard | ⚠️ Duplicate | Archive |
| `/configs/grafana/dashboards/` | 1 dashboard | ⚠️ Empty/placeholder | Delete |
| `/monitoring/grafana/dashboards/` | 1 dashboard | ✅ Functional | Migrate to production/ |
| `/packages/tta-dev-primitives/dashboards/grafana/` | 1 dashboard | ✅ Package-specific | Keep in place |

**Total Dashboards Found:** 8 files across 5 locations

---

## 🔄 Consolidation Strategy

### Target Structure

```
config/grafana/dashboards/
├── production/              # ← NEW: Canonical production dashboards
│   ├── 01-system-overview.json           ✅ CREATED (Session 2)
│   ├── 02-primitive-drilldown.json       📋 TODO
│   ├── 03-infrastructure.json            📋 TODO
│   └── 04-adaptive-primitives.json       📋 TODO
├── dashboards.yml           # ← UPDATED: Points to production/
├── executive_dashboard.json # ← LEGACY: To be migrated
├── developer_dashboard.json # ← LEGACY: To be migrated
└── platform_health.json     # ← LEGACY: To be migrated
```

### Migration Mapping

| Source | Destination | Notes |
|--------|-------------|-------|
| `config/grafana/dashboards/executive_dashboard.json` | `production/01-system-overview.json` | ✅ Rebuilt from scratch with recording rules |
| `config/grafana/dashboards/developer_dashboard.json` | `production/02-primitive-drilldown.json` | 📋 TODO: Enhance with proper metrics |
| `config/grafana/dashboards/platform_health.json` | `production/03-infrastructure.json` | 📋 TODO: Add infra-specific panels |
| `monitoring/grafana/dashboards/adaptive-primitives.json` | `production/04-adaptive-primitives.json` | 📋 TODO: Migrate as-is (already functional) |
| `grafana/dashboards/tta-primitives-dashboard.json` | ❌ Archive | Duplicate of developer_dashboard.json |
| `configs/grafana/dashboards/tta_agent_observability.json` | ❌ Delete | Empty placeholder, never implemented |

---

## ✅ Completed Actions (Session 2)

### 1. Recording Rules Enhancement ✅

**File:** `config/prometheus/rules/recording_rules.yml`

**Added Metrics:**
- `tta:cost_per_hour_dollars` - Cost tracking for dashboards
- `tta:p95_latency_seconds` - Alias for dashboard compatibility
- Enhanced all existing SLI aggregations

**Verification:**
```bash
# Verify rules are valid
promtool check rules config/prometheus/rules/recording_rules.yml

# Check if Prometheus loaded rules (after restart)
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].name'
```

### 2. Production Dashboard Directory ✅

**Created:** `config/grafana/dashboards/production/`

**Permissions:**
```bash
drwxr-xr-x 2 thein thein  4096 Nov 11 14:55 production
```

### 3. System Overview Dashboard ✅

**File:** `config/grafana/dashboards/production/01-system-overview.json`

**Panels (6 total):**
1. **🟢 System Health** - Gauge showing service availability (avg `up{job=~"tta-.*"}`)
2. **📊 Request Rate** - Time series using `tta:request_rate_5m` recording rule
3. **💰 Cost per Hour** - Gauge using `tta:cost_per_hour_dollars` recording rule
4. **📦 Workflow Executions** - Pie chart showing success/failure distribution
5. **⚡ Primitive Performance** - Bar chart with P95 latency by primitive type
6. **🔥 Cache Performance** - Time series using `tta:cache_hit_rate_5m` recording rule

**Features:**
- ✅ Auto-refresh every 30 seconds
- ✅ Uses recording rules for performance
- ✅ Color-coded thresholds (red/yellow/green)
- ✅ Links to other TTA.dev dashboards
- ✅ Dark theme with clean layout

### 4. Provisioning Configuration Update ✅

**File:** `config/grafana/dashboards/dashboards.yml`

**Changes:**
- Added `TTA.dev Production` provider pointing to `production/` directory
- Renamed old provider to `TTA.dev Legacy` to mark for deprecation
- Set production folder with 30s refresh interval

---

## 📋 Remaining Tasks (Session 2)

### Task 2.1: Migrate Developer Dashboard 🔄

**Source:** `config/grafana/dashboards/developer_dashboard.json`
**Destination:** `config/grafana/dashboards/production/02-primitive-drilldown.json`

**Required Changes:**
- Fix metric names (e.g., `tta_primitive_executions_total` → correct metric)
- Add template variables for workflow/primitive filtering
- Integrate Jaeger trace links
- Add error breakdown panel

**Expected Panels:**
1. Execution flow waterfall
2. Primitive statistics table
3. Error breakdown pie chart
4. Trace links to Jaeger

### Task 2.2: Migrate Platform Health Dashboard 🔄

**Source:** `config/grafana/dashboards/platform_health.json`
**Destination:** `config/grafana/dashboards/production/03-infrastructure.json`

**Required Changes:**
- Add Prometheus/Jaeger/Grafana health checks
- Add resource utilization (CPU, memory)
- Add disk space monitoring
- Add network metrics

### Task 2.3: Migrate Adaptive Primitives Dashboard 🔄

**Source:** `monitoring/grafana/dashboards/adaptive-primitives.json`
**Destination:** `config/grafana/dashboards/production/04-adaptive-primitives.json`

**Action:** Simple copy (dashboard is already functional)

```bash
cp monitoring/grafana/dashboards/adaptive-primitives.json \
   config/grafana/dashboards/production/04-adaptive-primitives.json
```

### Task 2.4: Archive Old Locations 🔄

**Create archive directory:**
```bash
mkdir -p archive/grafana-dashboards-20251111
```

**Move old dashboards:**
```bash
# Archive duplicate
mv grafana/dashboards/tta-primitives-dashboard.json \
   archive/grafana-dashboards-20251111/

# Archive configs folder
mv configs/grafana \
   archive/grafana-dashboards-20251111/configs-grafana
```

**Delete empty placeholder:**
```bash
# Verify it's empty first
cat configs/grafana/dashboards/tta_agent_observability.json

# If confirmed empty:
rm configs/grafana/dashboards/tta_agent_observability.json
```

---

## 🧪 Testing & Validation

### Pre-Deployment Checklist

- [ ] Verify all JSON files are valid
  ```bash
  for f in config/grafana/dashboards/production/*.json; do
    jq empty "$f" && echo "✅ $f" || echo "❌ $f"
  done
  ```

- [ ] Check recording rules syntax
  ```bash
  promtool check rules config/prometheus/rules/recording_rules.yml
  ```

- [ ] Verify dashboard UIDs are unique
  ```bash
  grep -r '"uid"' config/grafana/dashboards/production/ | sort | uniq -d
  ```

### Post-Deployment Validation

1. **Access Grafana:** http://localhost:3000
2. **Navigate to:** Dashboards → TTA.dev Production
3. **Verify:** All 4 dashboards load without errors
4. **Test:** Each panel returns data (no "No data" errors)
5. **Check:** Recording rules are active in Prometheus

**Query to verify recording rules:**
```promql
# Should return data if rules are working
tta:success_rate_5m
tta:cache_hit_rate_5m
tta:p95_latency_seconds
tta:cost_per_hour_dollars
```

---

## 📝 Documentation Updates Required

### Files to Update

1. **OBSERVABILITY_AUDIT_REPORT.md**
   - ✅ Mark Session 2 tasks as complete
   - Document new dashboard structure
   - Update dashboard locations section

2. **README.md** (main repo)
   - Add quick link to Grafana dashboards
   - Update observability section

3. **docs/observability/** (if exists)
   - Create dashboard guide
   - Document recording rules
   - Add troubleshooting section

---

## 🚀 Deployment Instructions

### Step 1: Restart Prometheus (to load recording rules)

```bash
# Using Docker Compose
docker-compose -f docker-compose.professional.yml restart prometheus

# Or if using standalone
sudo systemctl restart prometheus
```

### Step 2: Verify Recording Rules Loaded

```bash
# Check Prometheus API
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].name'

# Expected output should include:
# - tta_dev_performance
# - tta_dev_cache
# - tta_dev_workflows
# - tta_dev_business_metrics
# - tta_dev_sli
# - tta_dev_capacity
# - tta_dev_alerts_helper
```

### Step 3: Reload Grafana Dashboards

```bash
# Grafana automatically picks up new dashboards from provisioning
# No restart needed if provisioning is configured correctly

# Or force reload via API:
curl -X POST http://admin:admin@localhost:3000/api/admin/provisioning/dashboards/reload
```

### Step 4: Access & Validate

1. Open Grafana: http://localhost:3000
2. Navigate to: Dashboards → TTA.dev Production → 01 - TTA.dev System Overview
3. Verify all 6 panels load
4. Check for data in each panel

---

## 🎯 Success Criteria

### Session 2 Complete When:

- [x] Recording rules file enhanced with all required metrics
- [x] Production dashboard directory created
- [x] System Overview dashboard (01-system-overview.json) created with 6 panels
- [x] Dashboards.yml updated to point to production/
- [ ] Developer dashboard migrated (02-primitive-drilldown.json)
- [ ] Platform health dashboard migrated (03-infrastructure.json)
- [ ] Adaptive primitives dashboard copied (04-adaptive-primitives.json)
- [ ] Old dashboard locations archived
- [ ] All dashboards tested and functional

### Quality Metrics:

- **Dashboard Load Time:** < 3 seconds
- **Panel Query Time:** < 1 second per panel
- **Data Accuracy:** 100% of panels return data
- **Zero Errors:** No "No data" or query errors

---

## 📅 Timeline

- **Session 2 Start:** November 11, 2025, 14:30
- **Task 1 Complete:** November 11, 2025, 14:55 ✅
- **Task 2 Complete:** November 11, 2025, 15:00 ✅
- **Task 3 Complete:** November 11, 2025, 15:15 ✅
- **Expected Completion:** November 11, 2025, 16:00

---

## 🔗 Related Documents

- **Parent Report:** `OBSERVABILITY_AUDIT_REPORT.md`
- **Session 1:** `OBSERVABILITY_SESSION1_COMPLETE.md`
- **Recording Rules:** `config/prometheus/rules/recording_rules.yml`
- **Alerting Rules:** `config/prometheus/rules/alerting_rules.yml`

---

## 🆘 Troubleshooting

### Issue: Recording rules not loaded

**Symptom:** Queries like `tta:success_rate_5m` return "No data"

**Solution:**
```bash
# Check Prometheus config
curl http://localhost:9090/api/v1/status/config | jq '.data.yaml' | grep rule_files

# Verify rules file exists and is mounted
docker exec prometheus cat /etc/prometheus/rules/recording_rules.yml

# Check for syntax errors
docker exec prometheus promtool check rules /etc/prometheus/rules/recording_rules.yml
```

### Issue: Dashboard shows "No data"

**Symptom:** Panel displays "No data" message

**Solution:**
1. Check if underlying metric exists in Prometheus
2. Verify time range is appropriate
3. Check if recording rule is evaluating successfully
4. Inspect browser console for errors

### Issue: Dashboard not appearing in Grafana

**Symptom:** Dashboard not visible in folder

**Solution:**
1. Check provisioning configuration
2. Verify file permissions
3. Force reload dashboards
4. Check Grafana logs for errors

---

**Last Updated:** November 11, 2025, 15:15
**Next Review:** After completing remaining migration tasks
