---
hypertool_enabled: true
workflow_type: multi_persona
workflow_name: bug_fix_hypertool
version: 1.0.0
personas:
  - observability-expert
  - backend-engineer
  - testing-specialist
token_budget:
  observability-expert: 2000
  backend-engineer: 2000
  testing-specialist: 1500
  total_estimated: 5500
apm_enabled: true
quality_gates:
  - root_cause_identified
  - fix_validated
  - regression_tests_added
---

# Multi-Persona Workflow: Bug Fix with Hypertool

**Purpose:** Diagnose and fix bugs using optimal persona switching

**APM Integration:** Complete observability with PersonaMetricsCollector and WorkflowTracer

---

## Stage 1: Investigation & Root Cause Analysis

**Active Persona:** `observability-expert` (Token Budget: 2000)

**Hypertool Command:**
```bash
tta-persona switch observability-expert --chatmode bug-investigation
```

**Objectives:**
- Analyze logs and traces
- Identify error patterns
- Determine root cause
- Document findings

**Tasks:**
1. Query logs with Loki
2. Analyze traces with OpenTelemetry
3. Check metrics in Prometheus
4. Review error reports
5. Identify root cause

**MCP Tools:**
- `query_loki_logs` - Search application logs
- `query_prometheus` - Check metrics
- `mcp_grafana_get_dashboard_by_uid` - View dashboards

**Example Investigation:**
```bash
# Query error logs
curl -G http://localhost:3100/loki/api/v1/query_range \
  --data-urlencode 'query={job="app"} |= "ERROR"' \
  --data-urlencode 'start=2025-11-15T00:00:00Z'

# Check error rate
curl http://localhost:9090/api/v1/query \
  --data-urlencode 'query=rate(http_requests_total{status="500"}[5m])'
```

**Expected Token Usage:** ~800 tokens

---

## Stage 2: Implement Fix

**Persona Switch:** `observability-expert` → `backend-engineer`

**Hypertool Command:**
```bash
tta-persona switch backend-engineer --chatmode bug-fix
```

**Objectives:**
- Fix the identified bug
- Add error handling
- Update documentation

**Tasks:**
1. Write fix based on root cause
2. Add comprehensive error handling
3. Update docstrings
4. Add logging for observability

**Example Fix:**
```python
async def process_request(data: dict) -> dict:
    """
    Process incoming request with proper error handling.
    
    Root Cause: Missing null check for optional field 'user_id'
    Fix: Add validation and default handling
    """
    try:
        # FIX: Validate user_id exists before processing
        user_id = data.get("user_id")
        if not user_id:
            logger.warning("Missing user_id, using anonymous")
            user_id = "anonymous"
        
        # Process with validated user_id
        result = await db.query(user_id=user_id)
        
        # Add structured logging for observability
        logger.info(
            "Request processed successfully",
            extra={"user_id": user_id, "result_count": len(result)}
        )
        
        return {"status": "success", "data": result}
        
    except Exception as e:
        logger.error(
            f"Request processing failed: {e}",
            extra={"user_id": user_id, "error_type": type(e).__name__}
        )
        raise
```

**Expected Token Usage:** ~900 tokens

---

## Stage 3: Testing & Validation

**Persona Switch:** `backend-engineer` → `testing-specialist`

**Hypertool Command:**
```bash
tta-persona switch testing-specialist --chatmode bug-validation
```

**Objectives:**
- Write regression tests
- Validate fix works
- Ensure no new bugs introduced

**Tasks:**
1. Write test for original bug
2. Write test for edge cases
3. Run full test suite
4. Validate fix in staging

**Example Tests:**
```python
@pytest.mark.asyncio
async def test_missing_user_id_handling():
    """Test that missing user_id is handled gracefully."""
    # Original bug: this would crash
    result = await process_request({"data": "test"})
    
    # Fix: should handle gracefully
    assert result["status"] == "success"
    
@pytest.mark.asyncio
async def test_null_user_id_handling():
    """Test explicit null user_id."""
    result = await process_request({"user_id": None, "data": "test"})
    assert result["status"] == "success"
```

**Expected Token Usage:** ~600 tokens

---

**Workflow Version:** 1.0.0  
**Last Updated:** 2025-11-15
