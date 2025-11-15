# Multi-Persona Workflow: Incident Response

**Personas:** Observability Expert → Backend Engineer → DevOps Engineer  
**Purpose:** Respond to production incidents with rapid detection, diagnosis, and resolution  
**Duration:** ~30 minutes to 2 hours (depending on severity)

---

## Workflow Overview

This workflow demonstrates **incident response orchestration** for production issues:

1. **Observability Expert** → Detect and monitor (alerts, metrics, logs, traces)
2. **Backend Engineer** → Diagnose and fix (root cause analysis, code changes)
3. **DevOps Engineer** → Deploy and verify (hotfix deployment, rollback if needed)

**TTA.dev Integrations:**
- ✅ **Hypertool Personas** - Context-aware role switching during incidents
- ✅ **APM Integration** - Real-time monitoring with Prometheus, Grafana, Loki
- ✅ **Grafana MCP** - Query metrics and logs programmatically
- ✅ **InstrumentedPrimitive** - Track incident response workflow
- ✅ **RouterPrimitive** - Auto-route based on incident severity
- ✅ **FallbackPrimitive** - Graceful degradation (fix → rollback → circuit breaker)
- ✅ **MemoryPrimitive** - Track incident context and decisions
- ✅ **Logseq** - Document post-mortem and learnings
- ✅ **GitHub MCP** - Create hotfix branches, deploy changes
- ✅ **E2B Code Execution** - Test fixes in isolation

---

## Example Incident: Elevated API Error Rate

**Incident Details:**
```
Alert: API error rate > 5% for last 5 minutes
Service: tta-dev-primitives-api
Endpoint: /api/workflows/execute
Status Code: 500 Internal Server Error
Impact: 1,500 requests/min failing (15% error rate)
Priority: P1 (Critical)
```

---

## Stage 1: Detect and Monitor (Observability Expert Persona)

**Persona:** `tta-observability-expert` (2000 tokens, 44 tools)  
**Duration:** ~5-10 minutes  
**Goal:** Identify issue, gather context, assess impact

### Activate Observability Persona

```bash
# Switch to observability persona
tta-persona observability

# Or via chatmode
/chatmode observability-expert
```

**Verify tools:**
- ✅ Grafana MCP (query_prometheus, query_loki_logs, list_alert_rules)
- ✅ APM Integration (OpenTelemetry traces)
- ✅ Sequential Thinking (investigation planning)
- ✅ Logseq (incident tracking)

### Step 1.1: Alert Triage

**Goal:** Understand alert context

**TTA Primitive Pattern:**
```python
from tta_dev_primitives import RouterPrimitive
from tta_dev_primitives.performance import MemoryPrimitive

# Store incident context
incident_memory = MemoryPrimitive(namespace="incident_2025_11_14_001")

# Route based on severity
incident_router = RouterPrimitive(
    routes={
        "p0_critical": immediate_escalation_workflow,  # SEV0: All hands
        "p1_high": standard_incident_workflow,         # SEV1: This workflow
        "p2_medium": investigate_and_fix_workflow,     # SEV2: Normal priority
        "p3_low": create_ticket_workflow               # SEV3: Backlog
    },
    router_fn=lambda data, ctx: data["priority"],
    default="p2_medium"
)

# Execute routing
workflow = await incident_router.execute(
    {"priority": "p1_high", "alert": "api_error_rate_high"},
    context
)
```

**Grafana MCP - Query Alert:**
```bash
# Tool: list_alert_rules

# Get active alerts
query_prometheus "ALERTS{alertname='APIErrorRateHigh',alertstate='firing'}"

# Result:
# APIErrorRateHigh{service="tta-dev-primitives-api"} = 1
# Labels: severity=critical, endpoint=/api/workflows/execute
```

**Store in memory:**
```python
await incident_memory.add("alert_details", {
    "alert_name": "APIErrorRateHigh",
    "service": "tta-dev-primitives-api",
    "endpoint": "/api/workflows/execute",
    "severity": "critical",
    "detected_at": "2025-11-14T14:32:00Z",
    "current_error_rate": "15%",
    "threshold": "5%"
})
```

### Step 1.2: Check Error Metrics

**Goal:** Quantify the problem

**Grafana MCP - Query Metrics:**
```bash
# Tool: query_prometheus

# Error rate over time
query_prometheus "rate(http_requests_total{status='500',endpoint='/api/workflows/execute'}[5m])"

# Request count
query_prometheus "sum(rate(http_requests_total{endpoint='/api/workflows/execute'}[5m]))"

# Error percentage
query_prometheus "100 * sum(rate(http_requests_total{status='500'}[5m])) / sum(rate(http_requests_total[5m]))"

# Response time p95
query_prometheus "histogram_quantile(0.95, http_request_duration_seconds_bucket{endpoint='/api/workflows/execute'})"
```

**Results:**
```
Error rate: 225 errors/min (15% of 1,500 req/min)
Request count: 1,500 req/min
Error percentage: 15%
P95 latency: 2.5s (up from 0.3s baseline)
```

**Store metrics:**
```python
await incident_memory.add("metrics_snapshot", {
    "error_rate": "225/min",
    "total_requests": "1500/min",
    "error_percentage": "15%",
    "p95_latency": "2.5s",
    "baseline_p95": "0.3s",
    "spike_factor": "8.3x"
})
```

### Step 1.3: Analyze Error Logs

**Goal:** Find error patterns

**Grafana MCP - Query Loki:**
```bash
# Tool: query_loki_logs

# Get recent errors
query_loki_logs '{service="tta-dev-primitives-api",level="error"} |= "/api/workflows/execute"' --limit 100 --since 5m

# Sample log entry:
# {
#   "timestamp": "2025-11-14T14:32:15Z",
#   "level": "error",
#   "message": "Database connection timeout",
#   "exception": "pymongo.errors.ServerSelectionTimeoutError",
#   "endpoint": "/api/workflows/execute",
#   "trace_id": "abc123",
#   "user_id": "user_456"
# }
```

**Pattern detection:**
```python
# Analyze logs for common patterns
log_pattern_analysis = """
Error patterns detected:
1. Database timeouts: 180/225 errors (80%)
2. Memory allocation errors: 30/225 errors (13%)
3. Other errors: 15/225 errors (7%)

Root cause hypothesis: Database connection pool exhausted
"""

await incident_memory.add("log_analysis", {
    "primary_error": "Database connection timeout",
    "exception_type": "pymongo.errors.ServerSelectionTimeoutError",
    "percentage": "80%",
    "hypothesis": "Database connection pool exhausted",
    "affected_endpoints": ["/api/workflows/execute"]
})
```

### Step 1.4: Check Distributed Traces

**Goal:** Understand request flow

**OpenTelemetry Trace Query:**
```python
from observability_integration import get_traces

# Query traces for failed requests
traces = await get_traces(
    service_name="tta-dev-primitives-api",
    status_code=500,
    time_range="5m"
)

# Analyze trace spans
for trace in traces[:5]:
    print(f"Trace {trace.trace_id}:")
    for span in trace.spans:
        print(f"  {span.name}: {span.duration_ms}ms")
        if span.status == "error":
            print(f"    Error: {span.error_message}")

# Example trace:
# Trace abc123:
#   http.server.request: 2500ms
#     workflow.execute: 2450ms
#       database.query: 2400ms (ERROR: Timeout)
#         connection_pool.acquire: 2400ms (ERROR: No connections available)
```

**Root cause identified:**
```python
await incident_memory.add("trace_analysis", {
    "bottleneck": "database.connection_pool.acquire",
    "bottleneck_duration": "2400ms",
    "normal_duration": "10ms",
    "slowdown_factor": "240x",
    "root_cause": "Database connection pool exhausted (all 10 connections in use)",
    "contributing_factor": "Increased traffic (3x normal load)"
})
```

### Step 1.5: Impact Assessment

**Goal:** Quantify business impact

**Metrics:**
```python
await incident_memory.add("impact_assessment", {
    "users_affected": "~350 users/min",
    "requests_failing": "225 req/min",
    "duration_so_far": "8 minutes",
    "total_failed_requests": "1,800",
    "revenue_impact_estimate": "$450/hour (based on avg order value)",
    "sla_breach": "Yes - 99.9% availability SLA requires <0.1% error rate",
    "customer_complaints": "12 support tickets opened"
})
```

### Step 1.6: Create Incident Record

**Goal:** Document incident for team

**Logseq - Create Incident Page:**
```markdown
# Incident INC-2025-11-14-001

**Status:** 🔴 Active  
**Severity:** P1 (Critical)  
**Started:** 2025-11-14 14:32:00 UTC  
**Duration:** 8 minutes (ongoing)

## Summary

API error rate spiked to 15% on /api/workflows/execute endpoint due to database connection pool exhaustion.

## Impact

- **Users Affected:** ~350 users/min
- **Requests Failing:** 225 req/min (15%)
- **SLA Breach:** Yes (99.9% availability)
- **Customer Complaints:** 12 support tickets

## Root Cause (Preliminary)

Database connection pool exhausted (all 10 connections in use). Traffic increased 3x normal load.

## Timeline

- 14:32:00 - Alert fired (error rate > 5%)
- 14:33:00 - Observability persona activated
- 14:35:00 - Metrics analyzed (15% error rate confirmed)
- 14:37:00 - Logs analyzed (80% database timeouts)
- 14:39:00 - Traces analyzed (connection pool bottleneck identified)
- 14:40:00 - Impact assessed (P1 severity confirmed)

## Next Steps

- [ ] Hand off to backend persona for fix
- [ ] Increase database connection pool size
- [ ] Add circuit breaker to prevent cascade failures
- [ ] Deploy hotfix
- [ ] Monitor recovery

## Metrics

```promql
# Error rate
rate(http_requests_total{status='500',endpoint='/api/workflows/execute'}[5m])

# Connection pool usage
database_connection_pool_active / database_connection_pool_max
```

#incident #p1-critical #database #connection-pool
```

**Store in Logseq:**
```bash
# Tool: mcp_logseq_create_page
# Creates: logseq/pages/Incident INC-2025-11-14-001.md
```

---

## Stage 2: Diagnose and Fix (Backend Engineer Persona)

**Persona:** `tta-backend-engineer` (2000 tokens, 48 tools)  
**Duration:** ~15-30 minutes  
**Goal:** Implement fix for connection pool exhaustion

### Activate Backend Persona

```bash
# Switch to backend persona
tta-persona backend

# Or via chatmode
/chatmode backend-developer
```

**Verify tools:**
- ✅ Context7 (Python, SQLAlchemy, MongoDB docs)
- ✅ GitHub MCP (create hotfix branch)
- ✅ E2B Code Execution (test fix)
- ✅ Sequential Thinking (fix planning)

### Step 2.1: Retrieve Incident Context

**Goal:** Understand the problem from observability analysis

```python
# Retrieve incident details
incident_memory = MemoryPrimitive(namespace="incident_2025_11_14_001")

incident_details = await incident_memory.search(
    keywords=["root_cause", "hypothesis", "bottleneck"]
)

print("Incident summary:")
for detail in incident_details:
    print(f"  {detail['key']}: {detail['value']}")

# Output:
#   root_cause: Database connection pool exhausted (all 10 connections in use)
#   hypothesis: Connection pool too small for current traffic
#   bottleneck: database.connection_pool.acquire (2400ms vs 10ms normal)
```

### Step 2.2: Reproduce Issue Locally

**Goal:** Confirm root cause

**E2B Code Execution - Test Connection Pool:**
```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive

# Test connection pool behavior
test_code = """
from pymongo import MongoClient
import time
import concurrent.futures

# Simulate connection pool exhaustion
client = MongoClient(
    'mongodb://localhost:27017',
    maxPoolSize=10,  # Current production setting
    serverSelectionTimeoutMS=5000
)

def execute_query(i):
    try:
        start = time.time()
        db = client.test_db
        result = db.test_collection.find_one({'id': i})
        duration = time.time() - start
        return {'success': True, 'duration': duration, 'query_id': i}
    except Exception as e:
        return {'success': False, 'error': str(e), 'query_id': i}

# Simulate 50 concurrent requests (5x pool size)
with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    futures = [executor.submit(execute_query, i) for i in range(50)]
    results = [f.result() for f in futures]

# Analyze results
successes = [r for r in results if r['success']]
failures = [r for r in results if not r['success']]

print(f"Successes: {len(successes)}")
print(f"Failures: {len(failures)}")
print(f"Timeout errors: {len([f for f in failures if 'timeout' in f.get('error', '').lower()])}")

# Verify failure rate matches production
failure_rate = len(failures) / len(results) * 100
print(f"Failure rate: {failure_rate:.1f}%")
"""

executor = CodeExecutionPrimitive()
result = await executor.execute(
    {"code": test_code, "timeout": 60},
    context
)

# Expected output:
# Successes: 10
# Failures: 40
# Timeout errors: 40
# Failure rate: 80.0%  # Matches production 80% database timeout rate!
```

### Step 2.3: Design Fix

**Goal:** Increase connection pool size with safety limits

**Context7 - Query MongoDB Documentation:**
```bash
# Tool: mcp_context7_get-library-docs

# Get MongoDB connection pool best practices
context7_query "MongoDB Python connection pool sizing recommendations for high traffic"

# Key recommendations:
# - maxPoolSize: 50-100 for high traffic (default 100)
# - minPoolSize: 10 for connection reuse
# - maxIdleTimeMS: 60000 (1 minute)
# - waitQueueTimeoutMS: 5000 (fail fast)
```

**Fix design:**
```python
# Current configuration (production)
mongodb_config_old = {
    "maxPoolSize": 10,  # Too small!
    "minPoolSize": 0,   # No connection reuse
    "maxIdleTimeMS": None,
    "waitQueueTimeoutMS": 30000  # Too long, causes cascading delays
}

# New configuration (fix)
mongodb_config_new = {
    "maxPoolSize": 50,       # 5x increase to handle traffic spikes
    "minPoolSize": 10,       # Keep warm connections
    "maxIdleTimeMS": 60000,  # Recycle idle connections
    "waitQueueTimeoutMS": 5000  # Fail fast to prevent cascading timeouts
}

# Store in incident memory
await incident_memory.add("fix_design", {
    "change": "Increase MongoDB connection pool size",
    "old_max_pool_size": 10,
    "new_max_pool_size": 50,
    "rationale": "Current pool exhausted at 3x traffic. New size handles 5x traffic with headroom.",
    "additional_changes": [
        "Add minPoolSize=10 for connection reuse",
        "Add maxIdleTimeMS=60000 to recycle stale connections",
        "Reduce waitQueueTimeoutMS to 5000 for fast failure"
    ]
})
```

### Step 2.4: Implement Fix

**Goal:** Update database configuration

**Create hotfix branch:**
```bash
# Create hotfix branch from production
git checkout -b hotfix/database-connection-pool-exhaustion main
```

**Update configuration:**
```python
# packages/api/src/config/database.py

from pydantic import Field
from pydantic_settings import BaseSettings

class DatabaseSettings(BaseSettings):
    """Database configuration."""
    
    mongodb_url: str = Field(..., env="MONGODB_URL")
    
    # Connection pool settings
    max_pool_size: int = Field(
        default=50,  # ← Changed from 10
        description="Maximum number of connections in pool"
    )
    min_pool_size: int = Field(
        default=10,  # ← Added
        description="Minimum number of connections to maintain"
    )
    max_idle_time_ms: int = Field(
        default=60000,  # ← Added
        description="Maximum idle time before connection recycled (ms)"
    )
    wait_queue_timeout_ms: int = Field(
        default=5000,  # ← Changed from 30000
        description="Timeout waiting for available connection (ms)"
    )

# packages/api/src/database/client.py

from pymongo import MongoClient
from config.database import DatabaseSettings

settings = DatabaseSettings()

client = MongoClient(
    settings.mongodb_url,
    maxPoolSize=settings.max_pool_size,
    minPoolSize=settings.min_pool_size,
    maxIdleTimeMS=settings.max_idle_time_ms,
    waitQueueTimeoutMS=settings.wait_queue_timeout_ms,
    serverSelectionTimeoutMS=5000
)
```

### Step 2.5: Add Circuit Breaker (Bonus Resilience)

**Goal:** Prevent future cascade failures

**TTA Primitive Integration:**
```python
# packages/api/src/workflows/execute.py

from tta_dev_primitives.recovery import CircuitBreakerPrimitive, TimeoutPrimitive

# Wrap database operations with circuit breaker
db_with_circuit_breaker = CircuitBreakerPrimitive(
    primitive=database_query_step,
    failure_threshold=10,      # Open circuit after 10 failures
    recovery_timeout=30,       # Try recovery after 30s
    expected_successes=3       # Need 3 successes to close circuit
)

# Add timeout to prevent hanging
safe_db_query = TimeoutPrimitive(
    primitive=db_with_circuit_breaker,
    timeout_seconds=5.0  # Match waitQueueTimeoutMS
)

# Use in workflow
workflow = SequentialPrimitive([
    validate_input_step,
    safe_db_query,  # ← Protected database access
    process_results_step
])
```

### Step 2.6: Test Fix with E2B

**Goal:** Verify fix resolves issue

**E2B Test:**
```python
# Test new connection pool configuration
test_fix = """
from pymongo import MongoClient
import time
import concurrent.futures

# NEW configuration (fix)
client = MongoClient(
    'mongodb://localhost:27017',
    maxPoolSize=50,          # Increased from 10
    minPoolSize=10,          # Added
    maxIdleTimeMS=60000,     # Added
    waitQueueTimeoutMS=5000, # Reduced from 30000
    serverSelectionTimeoutMS=5000
)

def execute_query(i):
    try:
        start = time.time()
        db = client.test_db
        result = db.test_collection.find_one({'id': i})
        duration = time.time() - start
        return {'success': True, 'duration': duration, 'query_id': i}
    except Exception as e:
        return {'success': False, 'error': str(e), 'query_id': i}

# Same test: 50 concurrent requests
with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
    futures = [executor.submit(execute_query, i) for i in range(50)]
    results = [f.result() for f in futures]

successes = [r for r in results if r['success']]
failures = [r for r in results if not r['success']]

print(f"Successes: {len(successes)}")
print(f"Failures: {len(failures)}")

failure_rate = len(failures) / len(results) * 100
print(f"Failure rate: {failure_rate:.1f}%")

# Verify fix worked
assert len(successes) >= 48, f"Expected >=48 successes, got {len(successes)}"
assert failure_rate < 5, f"Expected <5% failure rate, got {failure_rate:.1f}%"
print("✅ Fix validated - connection pool handles load")
"""

result = await executor.execute(
    {"code": test_fix, "timeout": 60},
    context
)

if result["success"]:
    print("✅ Fix validated in E2B")
    await incident_memory.add("fix_validation", {
        "status": "validated",
        "test_environment": "e2b_sandbox",
        "result": "Connection pool handles 50 concurrent requests with <5% failure rate"
    })
else:
    print(f"❌ Fix validation failed: {result['error']}")
```

### Step 2.7: Commit Fix

```bash
# Commit hotfix
git add packages/api/src/config/ packages/api/src/database/ packages/api/src/workflows/
git commit -m "hotfix: increase database connection pool size

Root cause: Connection pool exhausted under increased traffic (3x baseline)
Fix: Increase maxPoolSize from 10 to 50
Additional improvements:
- Add minPoolSize=10 for connection reuse
- Add maxIdleTimeMS=60000 to recycle stale connections
- Reduce waitQueueTimeoutMS to 5000 for fast failure
- Add CircuitBreakerPrimitive to prevent cascade failures

Incident: INC-2025-11-14-001
Tested: E2B sandbox (50 concurrent requests, <5% failure rate)
"

git push origin hotfix/database-connection-pool-exhaustion
```

---

## Stage 3: Deploy and Verify (DevOps Engineer Persona)

**Persona:** `tta-devops-engineer` (1800 tokens, 38 tools)  
**Duration:** ~10-15 minutes  
**Goal:** Deploy hotfix and monitor recovery

### Activate DevOps Persona

```bash
# Switch to devops persona
tta-persona devops

# Or via chatmode
/chatmode devops-engineer
```

**Verify tools:**
- ✅ Docker (container operations)
- ✅ GitHub MCP (create PR, merge, tag)
- ✅ Grafana MCP (monitor deployment)
- ✅ Sequential Thinking (deployment planning)

### Step 3.1: Create Hotfix PR

**Goal:** Fast-track hotfix for review and merge

**GitHub MCP:**
```bash
# Tool: mcp_github_github_create_pull_request

gh pr create \
  --base main \
  --head hotfix/database-connection-pool-exhaustion \
  --title "🔥 HOTFIX: Database connection pool exhaustion (INC-2025-11-14-001)" \
  --body "## Incident

**Severity:** P1 (Critical)
**Incident:** INC-2025-11-14-001
**Started:** 2025-11-14 14:32:00 UTC
**Duration:** 18 minutes (ongoing)

## Root Cause

Database connection pool exhausted (maxPoolSize=10) under increased traffic (3x baseline).

## Fix

Increase connection pool size and add resilience:
- maxPoolSize: 10 → 50 (5x increase)
- minPoolSize: 0 → 10 (connection reuse)
- maxIdleTimeMS: None → 60000 (recycle stale connections)
- waitQueueTimeoutMS: 30000 → 5000 (fail fast)
- Add CircuitBreakerPrimitive (prevent cascade failures)

## Testing

✅ E2B validation: 50 concurrent requests, <5% failure rate
✅ Unit tests passing
✅ Integration tests passing

## Deployment Plan

1. Merge PR (bypassing CI for hotfix speed)
2. Deploy to production
3. Monitor error rate recovery
4. Rollback plan: Revert commit if error rate doesn't improve in 5 minutes

## Approval

Approved by: Observability Expert (root cause analysis)
Implemented by: Backend Engineer (fix validation)
Deploying: DevOps Engineer

**Requesting immediate merge and deployment.**
" \
  --label "hotfix" \
  --label "p1-critical" \
  --label "incident"
```

### Step 3.2: Deploy Hotfix

**Goal:** Deploy to production immediately

**TTA Primitive Pattern:**
```python
from tta_dev_primitives.recovery import FallbackPrimitive, RetryPrimitive

# Deploy with automatic rollback if fails
deploy_with_rollback = FallbackPrimitive(
    primary=deploy_hotfix,
    fallbacks=[
        rollback_to_previous_version,
        enable_maintenance_mode
    ]
)

# Retry deployment on transient failures
reliable_deploy = RetryPrimitive(
    primitive=deploy_with_rollback,
    max_retries=2,
    backoff_strategy="constant",
    initial_delay=10.0
)
```

**Execute deployment:**
```bash
# Merge PR (bypass CI for hotfix)
gh pr merge --admin --squash

# Tag hotfix
git tag -a hotfix-v1.2.3 -m "Hotfix: Database connection pool exhaustion"
git push origin hotfix-v1.2.3

# Deploy to production (Kubernetes rolling update)
kubectl set image deployment/tta-api \
  tta-api=ghcr.io/theinterneti/tta-api:hotfix-v1.2.3 \
  --namespace=production

# Wait for rollout
kubectl rollout status deployment/tta-api --namespace=production --timeout=300s
```

**Store deployment info:**
```python
await incident_memory.add("deployment", {
    "version": "hotfix-v1.2.3",
    "deployed_at": "2025-11-14T14:50:00Z",
    "deployment_method": "kubernetes_rolling_update",
    "rollout_duration": "45s"
})
```

### Step 3.3: Monitor Recovery

**Goal:** Verify error rate drops

**Grafana MCP - Real-time Monitoring:**
```bash
# Tool: query_prometheus

# Monitor error rate every 30 seconds
for i in {1..10}; do
  echo "Check $i at $(date):"
  
  # Current error rate
  query_prometheus "100 * sum(rate(http_requests_total{status='500',endpoint='/api/workflows/execute'}[1m])) / sum(rate(http_requests_total{endpoint='/api/workflows/execute'}[1m]))"
  
  # Connection pool usage
  query_prometheus "database_connection_pool_active / database_connection_pool_max"
  
  sleep 30
done

# Expected progression:
# Check 1: 15% error rate, 100% pool usage
# Check 2: 12% error rate, 80% pool usage
# Check 3: 8% error rate, 60% pool usage
# Check 4: 4% error rate, 40% pool usage  ← Below threshold!
# Check 5: 2% error rate, 30% pool usage
# ...
# Check 10: 0.5% error rate, 20% pool usage  ← Normal
```

**TTA UI Dashboard - View Recovery:**
```bash
# Access TTA Observability UI
open http://localhost:8765

# View traces:
# - Before fix: database.connection_pool.acquire spans showing 2400ms timeouts
# - After fix: database.connection_pool.acquire spans showing <50ms
```

### Step 3.4: Verify SLA Recovery

**Goal:** Confirm system back to normal

**Metrics check:**
```python
import asyncio

# Check metrics every minute for 5 minutes
async def verify_recovery():
    for i in range(5):
        # Query current error rate
        error_rate = await query_metric("error_rate_percentage")
        p95_latency = await query_metric("p95_latency_ms")
        pool_usage = await query_metric("connection_pool_usage_percentage")
        
        print(f"Minute {i+1}:")
        print(f"  Error rate: {error_rate:.2f}% (threshold: <0.1%)")
        print(f"  P95 latency: {p95_latency:.0f}ms (baseline: 300ms)")
        print(f"  Pool usage: {pool_usage:.0f}% (healthy: <70%)")
        
        # Check if recovered
        if error_rate < 0.1 and p95_latency < 500 and pool_usage < 70:
            print("✅ System recovered - SLA met")
            return True
        
        await asyncio.sleep(60)
    
    return False

recovered = await verify_recovery()

if recovered:
    await incident_memory.add("recovery", {
        "recovered_at": "2025-11-14T14:55:00Z",
        "total_duration": "23 minutes",
        "sla_restored": True,
        "final_error_rate": "0.05%",
        "final_p95_latency": "320ms",
        "final_pool_usage": "35%"
    })
```

### Step 3.5: Post-Incident Actions

**Goal:** Clean up and prevent recurrence

**Alert resolution:**
```bash
# Acknowledge alert (stops paging)
query_prometheus "ALERTS{alertname='APIErrorRateHigh',alertstate='resolved'}"

# Verify alert resolved
# APIErrorRateHigh = 0 (no active alerts)
```

**Update monitoring:**
```yaml
# Add new alert for connection pool usage
- alert: DatabaseConnectionPoolHigh
  expr: database_connection_pool_active / database_connection_pool_max > 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Database connection pool usage above 80%"
    description: "Connection pool at {{ $value }}% capacity. Consider scaling."
```

**Logseq - Update Incident:**
```markdown
# Incident INC-2025-11-14-001

**Status:** ✅ Resolved  
**Severity:** P1 (Critical)  
**Duration:** 23 minutes  
**Resolved:** 2025-11-14 14:55:00 UTC

## Timeline

- 14:32:00 - Alert fired (error rate > 5%)
- 14:33:00 - Observability persona: Investigation started
- 14:40:00 - Root cause identified: Connection pool exhaustion
- 14:42:00 - Backend persona: Fix designed
- 14:48:00 - Fix implemented and tested
- 14:50:00 - DevOps persona: Hotfix deployed
- 14:55:00 - **RESOLVED** - Error rate < 0.1%, SLA restored

## Resolution

Increased MongoDB connection pool from 10 to 50 connections. Added connection reuse, idle timeout, and circuit breaker for resilience.

## Post-Mortem Actions

- [ ] Conduct full post-mortem (due: 2025-11-15)
- [ ] Update runbooks with connection pool sizing guidance
- [ ] Add connection pool usage monitoring
- [ ] Review traffic forecasting (missed 3x spike)
- [ ] Consider auto-scaling connection pool based on load

## Metrics

**Impact:**
- Users affected: ~350/min for 23 minutes = 8,050 users
- Failed requests: 5,175 total
- Estimated revenue impact: $172.50 (23 min × $450/hr)

**Recovery:**
- Error rate: 15% → 0.05% (300x improvement)
- P95 latency: 2.5s → 0.32s (7.8x improvement)
- Connection pool usage: 100% → 35% (healthy headroom)

#incident-resolved #post-mortem-required #database #connection-pool
```

---

## Complete Workflow Orchestration

**Full incident response workflow:**

```python
"""
Multi-Persona Incident Response Workflow

Orchestrates observability → backend → devops for rapid incident resolution.
"""

import asyncio
from tta_dev_primitives import SequentialPrimitive, WorkflowContext, RouterPrimitive
from tta_dev_primitives.recovery import FallbackPrimitive, RetryPrimitive
from tta_dev_primitives.performance import MemoryPrimitive

# Shared incident memory
incident_memory = MemoryPrimitive(namespace="incident_2025_11_14_001")

# Stage 1: Observability - Detect and Analyze
observability_workflow = SequentialPrimitive([
    alert_triage_step,
    check_error_metrics_step,
    analyze_error_logs_step,
    check_distributed_traces_step,
    impact_assessment_step,
    create_incident_record_step
])

# Stage 2: Backend - Diagnose and Fix
backend_workflow = SequentialPrimitive([
    retrieve_incident_context_step,
    reproduce_issue_locally_step,
    design_fix_step,
    implement_fix_step,
    add_circuit_breaker_step,
    test_fix_with_e2b_step,
    commit_fix_step
])

# Stage 3: DevOps - Deploy and Verify
devops_workflow = SequentialPrimitive([
    create_hotfix_pr_step,
    FallbackPrimitive(
        primary=deploy_hotfix_step,
        fallbacks=[rollback_step, maintenance_mode_step]
    ),
    monitor_recovery_step,
    verify_sla_recovery_step,
    post_incident_actions_step
])

# Route based on incident severity
incident_router = RouterPrimitive(
    routes={
        "p0_critical": immediate_escalation_workflow,
        "p1_high": SequentialPrimitive([
            observability_workflow,
            backend_workflow,
            devops_workflow
        ]),
        "p2_medium": investigate_and_fix_workflow,
        "p3_low": create_ticket_workflow
    },
    router_fn=lambda data, ctx: data.get("priority", "p2_medium"),
    default="p2_medium"
)

# Execute
async def main():
    context = WorkflowContext(
        workflow_id="incident-response-2025-11-14-001",
        correlation_id="inc-2025-11-14-001",
        metadata={
            "personas": ["observability", "backend", "devops"],
            "alert": "APIErrorRateHigh",
            "service": "tta-dev-primitives-api"
        }
    )
    
    result = await incident_router.execute(
        {
            "priority": "p1_high",
            "alert": "APIErrorRateHigh",
            "service": "tta-dev-primitives-api"
        },
        context
    )
    
    print(f"Incident resolved: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Metrics and Observability

**Incident Response Metrics:**
- **Detection time:** 1 minute (automated alert)
- **Investigation time:** 8 minutes (observability persona)
- **Fix time:** 8 minutes (backend persona)
- **Deployment time:** 7 minutes (devops persona)
- **Total MTTR:** 23 minutes (well within 1-hour SLA)

**Business Impact:**
- Users affected: 8,050
- Failed requests: 5,175
- Revenue impact: $172.50
- SLA breach duration: 23 minutes

**Recovery Metrics:**
- Error rate: 15% → 0.05% (300x improvement)
- P95 latency: 2.5s → 0.32s (7.8x improvement)
- Connection pool usage: 100% → 35%

---

## Post-Mortem Template

**Use this template for all P0/P1 incidents:**

```markdown
# Post-Mortem: [Incident Title]

**Date:** YYYY-MM-DD  
**Incident ID:** INC-YYYY-MM-DD-NNN  
**Severity:** P0/P1/P2  
**Duration:** X minutes/hours  
**MTTR:** X minutes

## What Happened

[Brief summary of the incident]

## Impact

- Users affected: X
- Requests failed: X
- Revenue impact: $X
- SLA breach: Yes/No

## Root Cause

[Technical root cause - be specific]

## Timeline

- HH:MM - Event 1
- HH:MM - Event 2
- ...
- HH:MM - Resolved

## What Went Well

- [Thing 1]
- [Thing 2]

## What Went Wrong

- [Issue 1]
- [Issue 2]

## Action Items

- [ ] Action 1 (Owner, Due Date)
- [ ] Action 2 (Owner, Due Date)

## Lessons Learned

[Key takeaways for future incidents]
```

---

**Workflow Status:** ✅ Production-Ready  
**Last Updated:** 2025-11-14  
**Personas Required:** Observability, Backend, DevOps  
**MTTR:** ~20-30 minutes (vs 2-4 hours manual)
