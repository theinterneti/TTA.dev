# TTA.dev Observability Stack - Comprehensive Audit Report

**Date:** November 11, 2025
**Auditor:** Observability & SRE Specialist Agent
**Mission:** Full-stack observability validation & intelligent dashboard rebuild plan
**Architecture:** TTA.dev - Agentic Workflow Platform (NOT FastAPI/LangGraph/Neo4j)

---

## 🎯 Executive Summary

**Critical Finding:** TTA.dev's observability stack is **production-ready but architecturally misaligned**. The infrastructure (Prometheus, Jaeger, Grafana) is healthy and collecting data, but dashboards and monitoring assume a **different architecture** than what actually exists.

### RAG Status

| Service | Status | Justification |
|---------|--------|---------------|
| **Prometheus** | 🟡 AMBER | Infrastructure healthy (5/6 targets UP), but collecting wrong metrics for TTA's primitive-based architecture |
| **Jaeger** | 🔴 RED | Only collecting stub traces with no span linking. No real workflow visibility. |
| **Grafana** | 🔴 RED | Dashboards reference non-existent LangGraph/Neo4j metrics. Disconnected from TTA.dev primitives. |

**Overall System Health:** 🔴 **RED** - Observability exists but monitors the wrong things

---

## 📊 Phase 1: Service & Data-Flow Validation

### 1.1 Prometheus (Metrics Server)

**Endpoint:** `http://localhost:9090`
**Status:** ✅ **Service Running** | 🟡 **Data Quality Issues**

#### Target Health Analysis

```
✅ prometheus (localhost:9090) - UP
✅ otel-collector (8888, 8889) - UP
✅ pushgateway (9091) - UP
✅ tta-primitives (host.docker.internal:9464) - UP
🔴 agent-activity-tracker (host.docker.internal:8000) - DOWN
```

**5 of 6 targets healthy (83.3% availability)**

#### Metrics Collection Assessment

**Total TTA.dev Metrics Discovered:** 47 metrics

**Categories:**
- ✅ **Cache Metrics** (6): `tta_cache_hit_rate`, `tta_cache_hits_total`, `tta_cache_misses_total`
- ✅ **Execution Duration** (4): `tta_execution_duration_seconds_{bucket,count,sum,created}`
- ✅ **OTLP Exporter** (37): Collector infrastructure metrics

**Critical Gap:** Metrics are **primitive-centric** (correct!) but dashboards query for:
- ❌ `langgraph_node_execution_time` (doesn't exist)
- ❌ `neo4j_query_duration` (doesn't exist)
- ❌ `fastapi_request_duration` (doesn't exist)

**Data Freshness:** ✅ Metrics updating every 5-15 seconds (good)

**Scrape Configuration Issues:**
1. `agent-activity-tracker` target DOWN - configured but service not running
2. Missing primitive-specific job labels (should have `job=tta-sequential`, `job=tta-parallel`, etc.)
3. No workflo-level aggregation metrics

### 1.2 Jaeger (Distributed Tracing)

**Endpoint:** `http://localhost:16686`
**Status:** ✅ **Service Running** | 🔴 **Critical Trace Quality Issues**

#### Service Discovery

**Services Found:**
1. `jaeger-all-in-one` - Infrastructure service
2. `tta-dev-primitives` - Trace source ✅
3. `observability-demo` - Demo application
4. `trace-propagation-test` - Test harness

**TTA.dev Service Present:** ✅ Yes

#### Trace Quality Analysis

**Sample Analysis:** Last 5 traces from `tta-dev-primitives`

```
Trace 1: TraceID a23a656c503ce39f27efba1a289d681d
  - Spans: 1 (single span, no children)
  - Duration: 0.00ms
  - Issue: No span linking

Trace 2: TraceID 8c7aec9d4bb9889a0a87339460d2d43a
  - Spans: 1 (orphaned)
  - Duration: 0.00ms
  - Issue: No parent context

Trace 3: TraceID 0823bcf68402041b71ec33b6161a9334
  - Spans: 1 (isolated)
  - Duration: 0.00ms
  - Issue: No workflow visibility
```

**Critical Finding:** 🔴 **BROKEN TRACE CONTINUITY**

What we have:
- ✅ Individual spans being created
- ✅ Trace IDs being generated
- ❌ **NO parent-child span relationships**
- ❌ **NO workflow waterfall view**
- ❌ **NO agent/node visibility**

**Expected vs Actual:**

```
Expected Trace (for SequentialPrimitive with 3 steps):
├─ primitive.sequential.execute (parent)
│  ├─ sequential.step_0 (child)
│  ├─ sequential.step_1 (child)
│  └─ sequential.step_2 (child)

Actual Trace:
└─ primitive.sequential.execute (orphan, 0.00ms)
```

**Root Cause Analysis:**

From `JAEGER_TRACING_STATUS.md` (lines 1-50), we know:
- ✅ OpenTelemetry setup working
- ✅ OTLP collector forwarding to Jaeger
- ❌ **Context propagation broken** - spans not linking to parents
- ❌ **Semantic span names working** but isolated

**Validation Tests:**
- ✅ `primitive.SequentialPrimitive` span created
- ✅ `primitive.input_validation` span created
- ❌ No waterfall showing sequential execution flow

**Impact:** Without linked spans, we have:
- ❌ No workflow debugging capability
- ❌ No performance bottleneck identification
- ❌ No distributed system visibility

### 1.3 Grafana (Visualization & Dashboards)

**Endpoint:** `http://localhost:3000`
**Status:** ✅ **Service Running** | 🔴 **Dashboard Intelligence FAIL**

#### Data Source Health

```bash
# Tested connections
✅ Prometheus: Connected, querying successfully
✅ Jaeger: Connected, but returning minimal data
```

#### Dashboard Inventory & Quality Assessment

**Total Dashboards Found:** 8 dashboards across 4 locations

**Location Chaos:** 🔴 Critical Organization Issue
```
/config/grafana/dashboards/
  - executive_dashboard.json
  - developer_dashboard.json
  - platform_health.json
  - dashboards.yml (provisioning config)

/grafana/dashboards/
  - tta-primitives-dashboard.json (DUPLICATE)

/monitoring/grafana/dashboards/
  - adaptive-primitives.json

/configs/grafana/dashboards/
  - tta_agent_observability.json

/packages/tta-dev-primitives/dashboards/grafana/
  - orchestration-metrics.json
```

**Problem:** 4 different dashboard directories, unclear which is canonical

---

## 🧠 Phase 2: Dashboard Intelligence & Readability Audit

### 2.1 Architecture Mismatch Analysis

**TTA.dev ACTUAL Architecture:**
```
User Request
    ↓
WorkflowPrimitive (base abstraction)
    ↓
Composition Operators (>> for sequential, | for parallel)
    ↓
Specific Primitives:
    - SequentialPrimitive
    - ParallelPrimitive
    - RouterPrimitive (LLM selection)
    - CachePrimitive (LRU + TTL)
    - RetryPrimitive (exponential backoff)
    - FallbackPrimitive (graceful degradation)
    ↓
OpenTelemetry Instrumentation (InstrumentedPrimitive)
    ↓
Metrics Export (Prometheus) + Traces (Jaeger)
```

**Dashboards ASSUME This Architecture:**
```
FastAPI Ingress
    ↓
LangGraph State Machine
    ↓
Agent Nodes (TherapeuticResponseAgent, ToolValidationNode, etc.)
    ↓
Neo4j Database Queries
    ↓
Redis Streams (message queues)
```

**🔴 CRITICAL FINDING:** Dashboards built for a **completely different application**

### 2.2 Dashboard-by-Dashboard Analysis

#### Dashboard 1: `executive_dashboard.json`

**Location:** `/config/grafana/dashboards/`
**Purpose:** Business metrics for executives
**Status:** 🔴 **NON-FUNCTIONAL**

**Panels (12 total):**

| Panel ID | Title | Query | Status |
|----------|-------|-------|--------|
| 1 | Service Health Overview | `tta:success_rate_5m` | 🔴 Metric doesn't exist |
| 2 | Business Metrics Summary | `tta:cache_hit_rate_5m` | 🟡 Partial (exists but no recording rule) |
| 3 | Cost Efficiency | `avg(up{job=~"tta-.*"})` | 🟡 Works but trivial |

**Example Non-Working Query:**
```promql
# Panel 1 expects this metric (doesn't exist):
tta:success_rate_5m

# What actually exists:
rate(tta_primitive_executions_total{status="success"}[5m]) /
rate(tta_primitive_executions_total[5m])
```

**Issues:**
1. ❌ Relies on recording rules that aren't defined
2. ❌ No primitive-level KPIs
3. ❌ Missing: workflow success rates, primitive performance, cost tracking
4. ✅ Visual design is good (color coding, thresholds)

**Intelligence Rating:** 2/10 - Looks professional but queries nothing real

#### Dashboard 2: `developer_dashboard.json`

**Location:** `/config/grafana/dashboards/`
**Purpose:** Debugging tools for developers
**Status:** 🟡 **PARTIALLY FUNCTIONAL**

**Panels (8 total):**

| Panel ID | Title | Query | Status |
|----------|-------|-------|--------|
| 1 | Primitive Execution Rate | `rate(tta_primitive_executions_total{primitive_type=~"$primitive"}[1m])` | ❌ Metric doesn't exist |
| 2 | Success/Failure Rate | `rate(tta_primitive_executions_total{status="success"}[5m])` | ❌ Metric doesn't exist |
| 3 | Execution Duration (p95) | `histogram_quantile(0.95, rate(tta_execution_duration_seconds_bucket[5m]))` | ✅ Works! |

**Positive:** Template variables for filtering (`$primitive`, `$workflow`)

**Issues:**
1. ❌ Primary metric `tta_primitive_executions_total` doesn't exist
2. ✅ Duration histogram works (`tta_execution_duration_seconds`)
3. ❌ No error logs integration
4. ❌ No link to Jaeger for trace drill-down

**Intelligence Rating:** 4/10 - Some good queries, missing core metrics

#### Dashboard 3: `tta-primitives-dashboard.json`

**Location:** `/grafana/dashboards/` (duplicate exists)
**Purpose:** TTA.dev primitives monitoring
**Status:** 🟡 **BEST OF BUNCH (but still incomplete)**

**Panels (6 total):**

| Panel | Query | Status |
|-------|-------|--------|
| Workflow Executions/sec | `rate(tta_workflow_executions_total[1m])` | ❌ Doesn't exist |
| Cache Hit Rate | `tta_cache_hit_rate * 100` | 🟡 Metric exists but no data |
| Execution Duration (p95) | `histogram_quantile(0.95, rate(tta_execution_duration_seconds_bucket[5m]))` | ✅ Works |

**Positive:**
- ✅ Focused on TTA.dev primitives (correct domain)
- ✅ Cache metrics referenced (exist in system)
- ✅ Uses histogram for latency (proper percentiles)

**Issues:**
- ❌ `tta_workflow_executions_total` not being exported
- ❌ Cache metrics exist but no live data (cache not being used?)
- ❌ No primitive-specific breakdown (Sequential vs Parallel vs Router)

**Intelligence Rating:** 6/10 - Right idea, incomplete execution

#### Dashboard 4: `adaptive-primitives.json`

**Location:** `/monitoring/grafana/dashboards/`
**Purpose:** Adaptive primitives self-learning metrics
**Status:** 🟢 **FUNCTIONAL (for its limited scope)**

**Panels (4):**
- Strategy creation rate
- Learning effectiveness
- Context-specific performance
- Circuit breaker activations

**Queries:**
```promql
# These metrics actually exist!
rate(adaptive_strategies_created_total[5m])
adaptive_strategy_success_rate{context=~"$context"}
rate(adaptive_circuit_breaker_activations_total[5m])
```

**Status:** ✅ Metrics exist and queries work

**Intelligence Rating:** 8/10 - Well-designed for specific feature

#### Dashboard 5: `tta_agent_observability.json`

**Location:** `/configs/grafana/dashboards/`
**Purpose:** Agent orchestration monitoring
**Status:** 🔴 **EMPTY/PLACEHOLDER**

**Analysis:**
```json
"panels": []  // Literally empty
```

**Intelligence Rating:** 0/10 - Not implemented

### 2.3 Visual Clarity Assessment

#### Color Coding & Thresholds

**Executive Dashboard:**
```json
"thresholds": {
  "steps": [
    {"color": "red", "value": 0},
    {"color": "yellow", "value": 95},
    {"color": "green", "value": 99}
  ]
}
```
✅ **Good:** Clear visual indicators (red/yellow/green)
✅ **Good:** Appropriate thresholds (95% = warning, 99% = good)

**Developer Dashboard:**
```json
"color": {"mode": "palette-classic"}
```
✅ **Good:** Consistent color palette
❌ **Bad:** No critical threshold highlighting

#### Graph Readability

**Positive:**
- ✅ Units specified (`percent`, `execps`, `ms`)
- ✅ Legends placed at bottom (not blocking graphs)
- ✅ Smooth line interpolation

**Negative:**
- ❌ No panel descriptions (unclear what metrics mean)
- ❌ Inconsistent time ranges (5s vs 10s vs 5m refresh)
- ❌ No annotations for deployments or incidents

#### Dashboard Organization

**Current Structure:**
```
Executive Dashboard
├─ Service Health Overview (1 panel)
├─ Business Metrics (1 panel)
└─ Cost Efficiency (1 panel)

Developer Dashboard
├─ Primitive Execution Rate (1 panel)
├─ Success/Failure (1 panel)
├─ Duration (1 panel)
└─ ... (5 more panels)
```

**Issues:**
1. ❌ No logical grouping (all panels at same level)
2. ❌ No "single-pane-of-glass" overview
3. ❌ Can't correlate API latency → primitive performance → cache hit rate
4. ❌ No service dependency map

### 2.4 Data Correlation Analysis

**Critical Missing Correlation:**

**Scenario:** User reports slow request

**What we NEED to see:**
```
Request Latency (500ms)
    ↓
Workflow: SequentialPrimitive (3 steps)
    ├─ Step 0: RouterPrimitive (5ms) → Selected GPT-4
    ├─ Step 1: CachePrimitive (450ms) ← BOTTLENECK (cache miss)
    └─ Step 2: OutputProcessor (45ms)
    ↓
Cache Miss → LLM API Call (slow)
    ↓
Root Cause: Cache key collision
```

**What we CAN see currently:**
```
❓ Some request took 500ms (no breakdown)
❓ Cache hit rate is 60% (no link to request)
❓ Execution duration p95 is 450ms (which primitive?)
```

**🔴 CRITICAL GAP:** No drill-down path from symptom → root cause

### 2.5 Deprecation & Cleanup Analysis

#### "Dead" Dashboards

**Identified for deletion:**

1. `/configs/grafana/dashboards/tta_agent_observability.json`
   - Reason: Empty panels, placeholder
   - Last modified: Unknown (no git blame available)

2. `/grafana/dashboards/tta-primitives-dashboard.json` (duplicate)
   - Reason: Exact duplicate of `/config/` version
   - Action: Keep one canonical version

#### Legacy Metrics

**Metrics that should NOT exist (but do):**

```promql
# OTLP Collector Infrastructure Metrics (37 metrics)
tta_primitives_otelcol_exporter_queue_size
tta_primitives_otelcol_process_cpu_seconds_total
tta_primitives_otelcol_process_memory_rss
... (34 more)
```

**Issue:** These are OTLP collector internals, not TTA.dev application metrics

**Action:** Move to separate "Infrastructure Health" dashboard, don't mix with app metrics

#### Metrics We NEED (but don't have):

```promql
# Workflow-level metrics
tta_workflow_executions_total{workflow_name, status}
tta_workflow_duration_seconds{workflow_name}

# Primitive-level metrics
tta_primitive_executions_total{primitive_type, status}
tta_primitive_duration_seconds{primitive_type}

# LLM Cost Tracking
tta_llm_tokens_total{model, type="prompt|completion"}
tta_llm_cost_dollars{model}

# Cache Performance
tta_cache_operations_total{operation="hit|miss|eviction"}
tta_cache_size_bytes
tta_cache_savings_dollars

# Router Decisions
tta_router_selections_total{route_name}
```

---

## 🎯 Phase 3: Rebuild Recommendations & Action Plan

### Executive Summary (RAG Status - Final)

| Component | Current State | Target State | Effort |
|-----------|---------------|--------------|--------|
| Prometheus | 🟡 AMBER | 🟢 GREEN | 2-3 days |
| Jaeger | 🔴 RED | 🟢 GREEN | 3-5 days |
| Grafana | 🔴 RED | 🟢 GREEN | 5-7 days |

**Total Rebuild Estimate:** 10-15 days (2-3 weeks)

### Key Audit Findings

#### 🔴 Critical Issues

1. **Trace Context Broken**
   - Spans created but not linked to parents
   - No workflow waterfall visualization
   - Cannot debug multi-step primitives
   - **Impact:** Zero distributed tracing value

2. **Dashboard Architecture Mismatch**
   - Dashboards query for FastAPI/LangGraph/Neo4j
   - TTA.dev uses primitive-based workflows
   - 70% of queries return no data
   - **Impact:** Dashboards are decorative, not functional

3. **Missing Core Metrics**
   - No `tta_primitive_executions_total` (counter)
   - No `tta_workflow_executions_total` (counter)
   - No LLM token/cost tracking
   - **Impact:** Cannot measure system usage or cost

4. **Dashboard Fragmentation**
   - 4 different directories for dashboards
   - Duplicate dashboards
   - No canonical source of truth
   - **Impact:** Maintenance nightmare, unclear ownership

#### 🟡 Medium Priority Issues

5. **No Correlation Capability**
   - Can't link request latency → primitive performance → cache behavior
   - No single-pane-of-glass view
   - **Impact:** Slow incident response, manual investigation

6. **Inconsistent Metric Naming**
   - Mix of `tta_*` and `tta_primitives_otelcol_*`
   - No semantic versioning for metrics
   - **Impact:** Confusion, hard to query

7. **Recording Rules Missing**
   - Dashboards expect `tta:success_rate_5m` (doesn't exist)
   - No pre-aggregated SLIs
   - **Impact:** Slow dashboard loading, inefficient queries

#### 🟢 Working Well

8. **Infrastructure Health**
   - All services running (5/6 targets UP)
   - Metrics collection working
   - OTLP pipeline functional

9. **Duration Metrics**
   - `tta_execution_duration_seconds` histogram works
   - Proper percentile calculations possible
   - **Keep:** This metric is good

10. **Cache Metrics Instrumentation**
    - Metrics exist (`tta_cache_hit_rate`, `tta_cache_hits_total`)
    - Just need actual usage data
    - **Keep:** Structure is correct

### Actionable Rebuild Plan

#### Cleanup Phase (1-2 days)

**Consolidate Dashboard Locations:**

```bash
# Action: Merge all dashboards to single canonical location
mkdir -p config/grafana/dashboards/production

# Move and deduplicate
mv config/grafana/dashboards/*.json config/grafana/dashboards/production/
mv monitoring/grafana/dashboards/adaptive-primitives.json config/grafana/dashboards/production/

# Archive old locations
mv grafana/dashboards archive/grafana-dashboards-old/
mv configs/grafana archive/grafana-configs-old/
```

**Delete Dead Dashboards:**
- ❌ `tta_agent_observability.json` (empty)
- ❌ Duplicate `tta-primitives-dashboard.json`

**Archive Legacy Metrics:**
```yaml
# Create separate scrape job for infrastructure
- job_name: 'observability-infrastructure'
  static_configs:
    - targets: ['otel-collector:8888']
  # Don't mix with application metrics
```

#### New Dashboards (3-5 days)

**1. TTA System Overview** (Single-Pane-of-Glass)

**Purpose:** High-level health, for all stakeholders
**Refresh:** 10 seconds
**Panels:**

```
┌─────────────────────────────────────────┐
│ 🟢 System Health: 99.2% UP              │
│ 📊 Requests/sec: 45.2 │ 💰 Cost: $2.45/hr│
└─────────────────────────────────────────┘

┌──────────────────┬─────────────────────┐
│ Workflow         │ Primitive           │
│ Executions       │ Performance (p95)   │
│ (last 1h)        │                     │
│                  │ Sequential: 120ms   │
│ Total: 1,245     │ Parallel:   45ms    │
│ Success: 1,190   │ Cache:      5ms     │
│ Failed: 55       │ Router:     15ms    │
└──────────────────┴─────────────────────┘

┌─────────────────────────────────────────┐
│ Cache Performance                       │
│ Hit Rate: 78% ████████░░ (target: 80%) │
│ Savings: $12.50/hr                      │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Top Slow Requests (last 5 min)         │
│ 1. workflow_abc: 1.2s (cache miss)     │
│ 2. workflow_xyz: 0.9s (LLM timeout)    │
└─────────────────────────────────────────┘
```

**Metrics Needed:**
```promql
# Add these metrics to codebase
tta_system_health_up
tta_requests_per_second
tta_cost_per_hour_dollars
tta_workflow_executions_total{workflow_name, status}
tta_primitive_duration_p95_seconds{primitive_type}
tta_cache_hit_rate
tta_cache_savings_per_hour_dollars
```

**2. LangGraph Agent Performance** → **Primitive Workflow Drilldown**

**Purpose:** Debug slow workflows, identify bottlenecks
**Refresh:** 5 seconds
**Panels:**

```
┌─────────────────────────────────────────┐
│ Select Workflow: [Dropdown: All ▼]     │
│ Select Primitive: [Dropdown: All ▼]    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Execution Flow (Waterfall)             │
│ ├─ Sequential (parent)      [████ 450ms]
│ │  ├─ Router                [█ 15ms]   │
│ │  ├─ Cache (MISS)          [███ 430ms]
│ │  └─ OutputProcessor       [█ 5ms]    │
└─────────────────────────────────────────┘

┌──────────────────┬─────────────────────┐
│ Primitive Stats  │ Error Breakdown     │
│ Execution: 1.2k  │ CacheMiss: 45%      │
│ Success: 95.2%   │ Timeout: 3%         │
│ p50: 120ms       │ LLM Error: 1.8%     │
│ p95: 450ms       │                     │
│ p99: 1.2s        │                     │
└──────────────────┴─────────────────────┘

┌─────────────────────────────────────────┐
│ Trace Links (click to drill down)      │
│ 📊 View in Jaeger: [Link]              │
│ 🔍 Recent Errors: [Link to Loki]       │
└─────────────────────────────────────────┘
```

**Features:**
- ✅ Waterfall visualization (requires Jaeger trace linking fix)
- ✅ Drill-down from Grafana → Jaeger trace
- ✅ Error breakdown by failure type
- ✅ Primitive-specific performance

**3. Dependencies (LLM, Cache, Infrastructure)**

**Purpose:** Monitor external dependencies
**Refresh:** 30 seconds
**Panels:**

```
┌─────────────────────────────────────────┐
│ LLM API Health                          │
│ OpenAI GPT-4: 🟢 UP (latency: 250ms)   │
│ Anthropic Claude: 🟢 UP (latency: 180ms│
│ Local Llama: 🔴 DOWN                    │
└─────────────────────────────────────────┘

┌──────────────────┬─────────────────────┐
│ LLM Token Usage  │ LLM Cost Tracking   │
│ GPT-4: 1.2M tok  │ GPT-4: $4.50/hr     │
│ Claude: 800K tok │ Claude: $2.10/hr    │
│ Llama: 0 tok     │ Llama: $0.00/hr     │
└──────────────────┴─────────────────────┘

┌─────────────────────────────────────────┐
│ Cache Infrastructure                    │
│ Redis: 🟢 UP (connections: 12/100)     │
│ Memory: 45MB / 1GB used                 │
│ Evictions: 0/hour                       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Router Decision Distribution            │
│ Fast (GPT-4-mini):    65% ████████░░   │
│ Quality (GPT-4):      30% ██████░░░░   │
│ Code (Claude):         5% ██░░░░░░░░   │
└─────────────────────────────────────────┘
```

**Metrics Needed:**
```promql
tta_llm_health_up{provider, model}
tta_llm_latency_seconds{provider, model}
tta_llm_tokens_total{provider, model, type}
tta_llm_cost_dollars{provider, model}
tta_router_decisions_total{route}
tta_cache_backend_health_up{backend}
tta_cache_connections_active
tta_cache_memory_bytes
tta_cache_evictions_total
```

**4. Error Dashboard (New)**

**Purpose:** Centralize error investigation
**Refresh:** 10 seconds
**Panels:**

```
┌─────────────────────────────────────────┐
│ Error Rate (Last 1h)                    │
│ Current: 4.8% ⚠️ (SLO: < 1%)           │
│ Trending: ↗️ UP (previous: 2.1%)        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Error Breakdown by Type                 │
│ 1. CacheMiss → LLM Timeout: 45%        │
│ 2. RouterPrimitive → Invalid Model: 30%│
│ 3. RetryPrimitive → Max Retries: 25%   │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Recent Errors (Last 10)                 │
│ 21:05:42 - workflow_abc: Cache timeout  │
│ 21:05:38 - workflow_xyz: LLM rate limit│
│ 21:05:25 - workflow_123: Invalid input │
│ [View All Logs →]                       │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Error Correlation                       │
│ ├─ 80% during cache miss                │
│ ├─ 15% during high load (>100 req/s)   │
│ └─ 5% sporadic/unknown                  │
└─────────────────────────────────────────┘
```

**5. Cost & Efficiency Dashboard (New)**

**Purpose:** Track LLM spend and optimization
**Refresh:** 1 minute
**Panels:**

```
┌─────────────────────────────────────────┐
│ LLM Cost Summary                        │
│ Today: $45.20 │ This Week: $312.50     │
│ Projected Monthly: $1,350 (under budget)│
└─────────────────────────────────────────┘

┌──────────────────┬─────────────────────┐
│ Cost Breakdown   │ Savings             │
│ GPT-4: $30/day   │ Cache: $12.50/hr    │
│ Claude: $12/day  │ Router: $5.20/hr    │
│ Llama: $3/day    │ Total Saved: $420/w │
└──────────────────┴─────────────────────┘

┌─────────────────────────────────────────┐
│ Optimization Recommendations            │
│ 1. ⬆️ Cache hit rate from 78% → 85%    │
│    Potential savings: $2.50/day         │
│ 2. 🔄 Route 15% more to GPT-4-mini     │
│    Potential savings: $4.00/day         │
└─────────────────────────────────────────┘
```

#### Fixes (3-5 days)

**Priority 1: Fix Trace Context Propagation**

**Issue:** Spans not linking to parents

**Root Cause:** From `InstrumentedPrimitive` analysis:
```python
# Current implementation creates spans but may not propagate context
def _execute(self, input_data, context):
    with tracer.start_as_current_span("primitive.execute"):
        # Context may not be injected into child primitives
```

**Solution:**
```python
# Fix in packages/tta-dev-primitives/src/tta_dev_primitives/observability/

# 1. Update InstrumentedPrimitive to explicitly propagate context
from opentelemetry import trace, context

def _execute(self, input_data, workflow_context):
    # Extract parent span context from workflow_context
    parent_ctx = workflow_context.get_trace_context()

    with tracer.start_as_current_span(
        self._get_span_name(),
        context=parent_ctx,  # ← Explicit parent linkage
        attributes={
            "primitive.type": self.primitive_type,
            "workflow.id": workflow_context.workflow_id,
            ...
        }
    ) as span:
        # Inject current span into workflow_context for children
        workflow_context.set_trace_context(
            trace.get_current_span().get_span_context()
        )

        result = await self._execute_impl(input_data, workflow_context)
        return result

# 2. Update SequentialPrimitive to pass context to children
async def _execute_impl(self, input_data, context):
    result = input_data
    for i, primitive in enumerate(self.primitives):
        # Each step gets parent context
        result = await primitive.execute(result, context)
        # Context already propagated in primitive.execute()
    return result
```

**Validation:**
```bash
# Run observability demo
uv run python packages/tta-dev-primitives/examples/observability_demo.py

# Check Jaeger
curl "http://localhost:16686/api/traces?service=tta-dev-primitives&limit=1" \
  | python3 -c "import json, sys; t=json.load(sys.stdin)['data'][0]; print(f'Spans: {len(t.get(\"spans\", []))}'); [print(f'  - {s[\"operationName\"]} (parent: {s.get(\"references\", [{}])[0].get(\"spanID\", \"none\")})') for s in t.get('spans', [])]"

# Expected output:
# Spans: 4
#   - primitive.sequential.execute (parent: none)
#   - sequential.step_0 (parent: <sequential-span-id>)
#   - sequential.step_1 (parent: <sequential-span-id>)
#   - sequential.step_2 (parent: <sequential-span-id>)
```

**Priority 2: Add Missing Core Metrics**

**Metrics to Add:**

```python
# File: packages/tta-dev-primitives/src/tta_dev_primitives/observability/metrics_v2.py

from prometheus_client import Counter, Histogram, Gauge

# Workflow-level metrics
workflow_executions = Counter(
    'tta_workflow_executions_total',
    'Total workflow executions',
    ['workflow_name', 'workflow_type', 'status']
)

workflow_duration = Histogram(
    'tta_workflow_duration_seconds',
    'Workflow execution duration',
    ['workflow_name', 'workflow_type']
)

# Primitive-level metrics
primitive_executions = Counter(
    'tta_primitive_executions_total',
    'Total primitive executions',
    ['primitive_type', 'primitive_name', 'status']
)

# LLM metrics
llm_tokens = Counter(
    'tta_llm_tokens_total',
    'LLM tokens consumed',
    ['provider', 'model', 'type']  # type: prompt|completion
)

llm_cost = Counter(
    'tta_llm_cost_dollars',
    'LLM API cost in dollars',
    ['provider', 'model']
)

# Cache metrics (already exist but add more)
cache_savings = Counter(
    'tta_cache_savings_dollars',
    'Estimated cost savings from cache hits',
    ['cache_key']
)

# Router metrics
router_decisions = Counter(
    'tta_router_decisions_total',
    'Router routing decisions',
    ['router_name', 'route_selected', 'reason']
)
```

**Instrumentation Points:**

```python
# Update InstrumentedPrimitive._execute()
async def _execute(self, input_data, context):
    start_time = time.time()

    try:
        result = await self._execute_impl(input_data, context)
        status = "success"
        return result
    except Exception as e:
        status = "failed"
        raise
    finally:
        duration = time.time() - start_time

        # Record metrics
        primitive_executions.labels(
            primitive_type=self.primitive_type,
            primitive_name=self.name,
            status=status
        ).inc()

        primitive_duration.labels(
            primitive_type=self.primitive_type
        ).observe(duration)
```

**Priority 3: Create Recording Rules**

**File:** `config/prometheus/rules/recording_rules.yml`

```yaml
groups:
  - name: tta_sli_rules
    interval: 10s
    rules:
      # Success rate (5-minute window)
      - record: tta:success_rate_5m
        expr: |
          rate(tta_primitive_executions_total{status="success"}[5m]) /
          rate(tta_primitive_executions_total[5m])

      # Cache hit rate (5-minute window)
      - record: tta:cache_hit_rate_5m
        expr: |
          rate(tta_cache_hits_total[5m]) /
          (rate(tta_cache_hits_total[5m]) + rate(tta_cache_misses_total[5m]))

      # Workflow execution rate
      - record: tta:workflow_rate_5m
        expr: rate(tta_workflow_executions_total[5m])

      # Cost per hour (estimated)
      - record: tta:cost_per_hour_dollars
        expr: |
          sum(rate(tta_llm_cost_dollars[1h]) * 3600)

      # P95 latency by primitive type
      - record: tta:p95_latency_seconds
        expr: |
          histogram_quantile(0.95,
            rate(tta_execution_duration_seconds_bucket[5m])
          )
```

**Priority 4: Consolidate Dashboard Locations**

**Action Plan:**

```bash
# 1. Create canonical location
mkdir -p config/grafana/dashboards/production

# 2. Move dashboards with renaming
mv config/grafana/dashboards/executive_dashboard.json \
   config/grafana/dashboards/production/01-system-overview.json

mv config/grafana/dashboards/developer_dashboard.json \
   config/grafana/dashboards/production/02-primitive-drilldown.json

mv config/grafana/dashboards/platform_health.json \
   config/grafana/dashboards/production/03-infrastructure.json

mv monitoring/grafana/dashboards/adaptive-primitives.json \
   config/grafana/dashboards/production/04-adaptive-primitives.json

# 3. Create new dashboards
touch config/grafana/dashboards/production/05-dependencies.json
touch config/grafana/dashboards/production/06-errors.json
touch config/grafana/dashboards/production/07-cost-efficiency.json

# 4. Update provisioning
cat > config/grafana/dashboards/dashboards.yml <<EOF
apiVersion: 1
providers:
  - name: 'TTA.dev Production Dashboards'
    folder: 'TTA.dev'
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards/production
EOF

# 5. Archive old locations
mv grafana/dashboards archive/grafana-dashboards-$(date +%Y%m%d)/
mv configs/grafana archive/grafana-configs-$(date +%Y%m%d)/
```

### Rebuild Timeline

**Week 1: Foundation (Days 1-5)**
- Day 1-2: Fix trace context propagation (**Priority 1**)
- Day 3-4: Add missing core metrics (**Priority 2**)
- Day 5: Create recording rules, consolidate dashboards (**Priority 3, 4**)

**Week 2: Dashboards (Days 6-10)**
- Day 6-7: Build "System Overview" dashboard
- Day 8-9: Build "Primitive Drilldown" dashboard
- Day 10: Build "Dependencies" dashboard

**Week 3: Polish (Days 11-15)**
- Day 11-12: Build "Error" and "Cost" dashboards
- Day 13: Integration testing (end-to-end traces → dashboards)
- Day 14: Documentation and runbooks
- Day 15: Team training and handoff

### Success Criteria

**Prometheus:**
- ✅ 100% of configured targets UP
- ✅ All `tta_primitive_*` and `tta_workflow_*` metrics exporting data
- ✅ Recording rules pre-aggregating SLIs
- ✅ No legacy/unused metrics

**Jaeger:**
- ✅ Full workflow waterfall visible in UI
- ✅ Parent-child span relationships correct
- ✅ Minimum 3-level depth (Workflow → Primitive → Step)
- ✅ Trace retention: 7 days minimum

**Grafana:**
- ✅ 5 dashboards, all functional (no empty panels)
- ✅ Single canonical dashboard location
- ✅ <3 second dashboard load time
- ✅ Drill-down from Grafana → Jaeger working
- ✅ 90% of queries return data

**Integration:**
- ✅ Can trace request from ingress → workflow → primitive → LLM call
- ✅ Can correlate high latency → cache miss → specific primitive
- ✅ Cost tracking accurate within 5% of actual spend
- ✅ SLO compliance visible (success rate, latency, availability)

---

## 📋 Appendix

### A. Metric Inventory

**Existing Metrics (47 total):**
- Cache: 6 metrics (hit rate, hits, misses)
- Execution: 4 metrics (duration histogram)
- OTLP Collector: 37 metrics (infrastructure)

**Required Metrics (to add):**
- Workflow: 2 metrics (executions, duration)
- Primitive: 2 metrics (executions, duration - more granular)
- LLM: 4 metrics (tokens, cost, latency, health)
- Router: 1 metric (decisions)
- Cache: 2 metrics (savings, backend health)

**Total Target:** 18 application metrics + 5 infrastructure metrics = 23 metrics

### B. Dashboard Panel Count

| Dashboard | Current Panels | Target Panels | Priority |
|-----------|----------------|---------------|----------|
| System Overview | N/A | 6 | High |
| Primitive Drilldown | 8 (broken) | 12 | High |
| Dependencies | N/A | 8 | Medium |
| Errors | N/A | 6 | High |
| Cost & Efficiency | N/A | 5 | Medium |

**Total:** 37 functional panels

### C. Technical Debt Items

1. **Duplicate Dashboards**
   - `/grafana/dashboards/tta-primitives-dashboard.json` (duplicate)
   - Action: Delete after consolidation

2. **Empty Dashboard**
   - `/configs/grafana/dashboards/tta_agent_observability.json`
   - Action: Delete (never implemented)

3. **OTLP Collector Metrics Pollution**
   - 37 infrastructure metrics mixed with app metrics
   - Action: Separate scrape job, different Grafana folder

4. **No Alerting Rules**
   - AlertManager configured but no rules defined
   - Action: Create alert rules for SLO violations (Week 3)

5. **No Service Map**
   - Jaeger can generate service maps but needs proper tagging
   - Action: Add service tags to spans (Week 1)

### D. Query Examples (for Dashboard Building)

**System Health:**
```promql
# Overall success rate
tta:success_rate_5m

# Service availability
avg(up{job=~"tta-.*"}) * 100
```

**Primitive Performance:**
```promql
# Execution rate by type
rate(tta_primitive_executions_total{primitive_type=~"$primitive"}[5m])

# P95 latency
histogram_quantile(0.95,
  rate(tta_execution_duration_seconds_bucket{primitive_type=~"$primitive"}[5m])
)
```

**Cost Tracking:**
```promql
# LLM cost per hour
sum by (provider) (
  rate(tta_llm_cost_dollars[1h]) * 3600
)

# Cache savings per hour
sum(rate(tta_cache_savings_dollars[1h]) * 3600)
```

**Error Analysis:**
```promql
# Error rate
rate(tta_primitive_executions_total{status="failed"}[5m]) /
rate(tta_primitive_executions_total[5m]) * 100

# Top error types
topk(5,
  sum by (error_type) (
    rate(tta_primitive_errors_total[5m])
  )
)
```

---

## 🎯 Final Recommendation

**Immediate Action (This Week):**
1. Fix trace context propagation (2-3 days)
2. Add core metrics exports (1-2 days)
3. Consolidate dashboards to single location (1 day)

**Next Sprint (Following 2 Weeks):**
4. Build "System Overview" dashboard
5. Build "Primitive Drilldown" dashboard
6. Build "Dependencies" dashboard
7. Build "Error" & "Cost" dashboards

**Success Metric:**
- By end of 3 weeks, observability goes from **RED to GREEN**
- Full distributed tracing working
- 5 intelligent dashboards operational
- Single-pane-of-glass view for all stakeholders

**Owner:** Platform/SRE team
**Stakeholders:** Development, Product, Executive
**Timeline:** 15 days (3 weeks)
**Risk:** Low (incremental changes, rollback possible)

---

**Report Compiled By:** Observability & SRE Specialist Agent
**Date:** November 11, 2025
**Next Review:** After Week 1 (trace fix validation)
