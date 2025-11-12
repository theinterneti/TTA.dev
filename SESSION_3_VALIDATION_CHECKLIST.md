# Session 3 Validation Checklist

Run these commands to verify the Prometheus metrics implementation is working correctly.

---

## ✅ Pre-Flight Checks

### 1. Verify prometheus_client is installed
```bash
uv run python -c "from prometheus_client import Counter; print('✅ prometheus_client installed')"
```

**Expected output:** `✅ prometheus_client installed`

### 2. Check Python version
```bash
python --version
```

**Expected:** Python 3.11 or higher

---

## ✅ Code Verification

### 3. Verify prometheus_metrics module exists
```bash
ls -lh packages/tta-dev-primitives/src/tta_dev_primitives/observability/prometheus_metrics.py
```

**Expected:** File exists, ~8-10 KB

### 4. Check module imports correctly
```bash
uv run python -c "from tta_dev_primitives.observability.prometheus_metrics import get_prometheus_metrics; print('✅ Module imports correctly')"
```

**Expected output:** `✅ Module imports correctly`

### 5. Verify metrics can be created
```bash
uv run python -c "
from tta_dev_primitives.observability.prometheus_metrics import get_prometheus_metrics
prom = get_prometheus_metrics()
prom.record_workflow_execution('TestWorkflow', 'success')
print('✅ Metrics can be recorded')
"
```

**Expected output:** `✅ Metrics can be recorded`

---

## ✅ HTTP Endpoint Tests

### 6. Start test server and check endpoint
```bash
cd /home/thein/repos/TTA.dev-copilot
timeout 30 uv run python test_metrics_export.py > /tmp/metrics_test.log 2>&1 &
sleep 8
curl -s http://localhost:9464/metrics | grep "^tta_workflow_executions_total" | head -5
pkill -f "test_metrics_export"
```

**Expected output:** Lines showing workflow execution metrics with labels

### 7. Verify all metric types are exported
```bash
timeout 30 uv run python test_metrics_export.py > /tmp/metrics_test.log 2>&1 &
sleep 8
echo "Checking for all TTA metrics..."
curl -s http://localhost:9464/metrics | grep -E "^(tta_workflow|tta_primitive|tta_llm|tta_execution|tta_cache)" | grep -v "^#" | wc -l
pkill -f "test_metrics_export"
```

**Expected output:** Number > 10 (should see multiple metric lines)

---

## ✅ Prometheus Integration Tests

### 8. Check Prometheus targets
```bash
curl -s 'http://localhost:9090/api/v1/targets' | jq '.data.activeTargets[] | select(.scrapeUrl | contains("9464")) | {job: .labels.job, health: .health}'
```

**Expected output:** Two targets with `"health": "up"`

### 9. Query workflow executions (while test running)
```bash
timeout 30 uv run python test_metrics_export.py > /tmp/metrics_test.log 2>&1 &
sleep 10
curl -s 'http://localhost:9090/api/v1/query?query=tta_workflow_executions_total' | jq '.data.result | length'
pkill -f "test_metrics_export"
```

**Expected output:** Number > 0 (indicating Prometheus scraped the metrics)

### 10. Check recording rule evaluation
```bash
timeout 30 uv run python test_metrics_export.py > /tmp/metrics_test.log 2>&1 &
sleep 10
curl -s 'http://localhost:9090/api/v1/query?query=tta:workflow_rate_5m' | jq '.data.result[0].metric.__name__'
pkill -f "test_metrics_export"
```

**Expected output:** `"tta:workflow_rate_5m"` (recording rule exists)

---

## ✅ Code Integration Tests

### 11. Verify InstrumentedPrimitive integration
```bash
grep -n "from .prometheus_metrics import get_prometheus_metrics" packages/tta-dev-primitives/src/tta_dev_primitives/observability/instrumented_primitive.py
```

**Expected output:** Line number showing import exists

### 12. Verify SequentialPrimitive integration
```bash
grep -n "prom_metrics.record_workflow_execution" packages/tta-dev-primitives/src/tta_dev_primitives/core/sequential.py
```

**Expected output:** Line number showing metric recording

### 13. Verify ParallelPrimitive integration
```bash
grep -n "prom_metrics.record_workflow_execution" packages/tta-dev-primitives/src/tta_dev_primitives/core/parallel.py
```

**Expected output:** Line number showing metric recording

---

## ✅ Metric Schema Validation

### 14. Verify workflow execution metric schema
```bash
timeout 30 uv run python test_metrics_export.py > /tmp/metrics_test.log 2>&1 &
sleep 8
curl -s http://localhost:9464/metrics | grep "^tta_workflow_executions_total" | head -1
pkill -f "test_metrics_export"
```

**Expected labels:** `job`, `status`, `workflow_name`

### 15. Verify primitive execution metric schema
```bash
timeout 30 uv run python test_metrics_export.py > /tmp/metrics_test.log 2>&1 &
sleep 8
curl -s http://localhost:9464/metrics | grep "^tta_primitive_executions_total" | head -1
pkill -f "test_metrics_export"
```

**Expected labels:** `job`, `primitive_type`, `primitive_name`, `status`

### 16. Verify duration histogram buckets
```bash
timeout 30 uv run python test_metrics_export.py > /tmp/metrics_test.log 2>&1 &
sleep 8
curl -s http://localhost:9464/metrics | grep "tta_execution_duration_seconds_bucket" | grep 'le=' | head -5
pkill -f "test_metrics_export"
```

**Expected output:** Buckets with `le="0.01"`, `le="0.05"`, `le="0.1"`, etc.

---

## ✅ Grafana Dashboard Tests

### 17. Check Grafana is running
```bash
curl -s http://localhost:3001/api/health | jq '.database'
```

**Expected output:** `"ok"`

### 18. Verify Grafana can query Prometheus
```bash
curl -s http://localhost:3001/api/datasources | jq '.[] | select(.type=="prometheus") | .name'
```

**Expected output:** Datasource name (e.g., "Prometheus")

---

## ✅ Documentation Verification

### 19. Check completion report exists
```bash
ls -lh OBSERVABILITY_SESSION_3_COMPLETE.md
```

**Expected:** File exists, >25 KB

### 20. Check metrics guide exists
```bash
ls -lh docs/observability/prometheus-metrics-guide.md
```

**Expected:** File exists, >20 KB

---

## 📊 Final Validation

Run all tests in sequence:

```bash
#!/bin/bash
echo "=== SESSION 3 VALIDATION ==="
echo ""

# Test 1: Module import
echo "1. Module import..."
uv run python -c "from tta_dev_primitives.observability.prometheus_metrics import get_prometheus_metrics" && echo "✅ PASS" || echo "❌ FAIL"

# Test 2: Metric recording
echo "2. Metric recording..."
uv run python -c "
from tta_dev_primitives.observability.prometheus_metrics import get_prometheus_metrics
prom = get_prometheus_metrics()
prom.record_workflow_execution('Test', 'success')
" && echo "✅ PASS" || echo "❌ FAIL"

# Test 3: HTTP endpoint
echo "3. HTTP endpoint with metrics..."
timeout 30 uv run python test_metrics_export.py > /tmp/metrics_test.log 2>&1 &
sleep 8
METRIC_COUNT=$(curl -s http://localhost:9464/metrics | grep "^tta_" | grep -v "^#" | wc -l)
pkill -f "test_metrics_export"
if [ "$METRIC_COUNT" -gt 10 ]; then
    echo "✅ PASS ($METRIC_COUNT metrics found)"
else
    echo "❌ FAIL (only $METRIC_COUNT metrics found)"
fi

# Test 4: Prometheus targets
echo "4. Prometheus scrape targets..."
TARGET_COUNT=$(curl -s 'http://localhost:9090/api/v1/targets' | jq '.data.activeTargets[] | select(.scrapeUrl | contains("9464")) | .health' | grep "up" | wc -l)
if [ "$TARGET_COUNT" -ge 1 ]; then
    echo "✅ PASS ($TARGET_COUNT healthy targets)"
else
    echo "❌ FAIL (no healthy targets)"
fi

# Test 5: Recording rules
echo "5. Recording rules evaluation..."
timeout 30 uv run python test_metrics_export.py > /tmp/metrics_test.log 2>&1 &
sleep 10
RULE_EXISTS=$(curl -s 'http://localhost:9090/api/v1/query?query=tta:workflow_rate_5m' | jq -r '.data.result[0].metric.__name__')
pkill -f "test_metrics_export"
if [ "$RULE_EXISTS" == "tta:workflow_rate_5m" ]; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

echo ""
echo "=== VALIDATION COMPLETE ==="
```

Save as `validate_session_3.sh`, chmod +x, and run:
```bash
chmod +x validate_session_3.sh
./validate_session_3.sh
```

---

## 🎯 Success Criteria

All tests should pass (✅ PASS). If any fail:

1. Check the logs: `cat /tmp/metrics_test.log`
2. Verify observability stack is running: `docker-compose ps`
3. Check for port conflicts: `netstat -tuln | grep 9464`
4. Review the troubleshooting section in `SESSION_3_IMPLEMENTATION_SUMMARY.md`

---

**Checklist Version:** 1.0
**Last Updated:** November 11, 2025
**Expected Duration:** ~5 minutes
