# TTA.dev Batteries-Included Implementation Plan

**Goal:** Deliver the 5-minute clone-to-observability user journey outlined in `USER_JOURNEY.md`

## Current State Assessment

### ✅ What We Have (Ready)
1. **Agent Discovery Infrastructure**
   - `AGENTS.md` - Global coordination hub
   - `.github/copilot-instructions.md` - Coding standards
   - `PRIMITIVES_CATALOG.md` - Complete reference
   - Custom agents in `.github/agents/`

2. **Core Primitives with Built-in Observability**
   - Sequential, Parallel, Conditional, Router primitives
   - Retry, Timeout, Fallback, CircuitBreaker primitives
   - Cache, RateLimit primitives
   - All emit OpenTelemetry traces automatically

3. **Observability Foundation**
   - `platform/observability/` with OTEL integration
   - Sampling strategies (adaptive, hash-based)
   - LangFuse integration (deprecated, being removed)

### 🔄 What Needs Work (Gaps)
1. **Self-Discovering Dashboard** - Not fully self-expanding
2. **One-Command Launch** - No `dev_start.py` script yet
3. **Dashboard Auto-Growth** - Doesn't adapt to new services automatically
4. **Live Demo** - No working example showing full stack

---

## Implementation Phases

### Phase 1: Self-Discovering Dashboard (Priority: CRITICAL)

**Goal:** Dashboard automatically detects and visualizes whatever the agent builds

#### 1.1 Service Auto-Discovery
```python
# Dashboard polls OTEL collector for new service names
# Automatically creates cards for each discovered service
class ServiceDiscovery:
    def discover_services(self) -> list[str]:
        """Query OTEL for unique service.name attribute values."""
        pass
```

**Files to create/modify:**
- `platform/observability/src/dashboard/discovery.py`
- `platform/observability/src/dashboard/ui/app.js`

#### 1.2 Workflow Auto-Registration
```python
# Each primitive registers its workflow_id on first execution
# Dashboard shows live list of active workflows
registry = WorkflowRegistry()
registry.register(workflow_id="user-checkout-flow")
```

**Files to create/modify:**
- `packages/tta-dev-primitives/src/tta_dev_primitives/core/registry.py`
- `platform/observability/src/dashboard/registry_api.py`

#### 1.3 Real-Time WebSocket Updates
```python
# Dashboard receives live trace events via WebSocket
# No polling - instant updates when primitives execute
ws://localhost:8080/ws/traces
```

**Files to create/modify:**
- `platform/observability/src/dashboard/websocket_server.py`
- `platform/observability/src/dashboard/ui/app.js`

---

### Phase 2: One-Command Launch (Priority: HIGH)

**Goal:** `uv run python scripts/dev_start.py` launches everything

#### 2.1 Development Orchestrator
```python
#!/usr/bin/env python3
"""
TTA.dev Development Environment Launcher

Starts:
1. OTEL Collector (if not running)
2. Observability Dashboard (http://localhost:8080)
3. Any user-defined services (auto-discovered)
"""

import asyncio
from tta_dev_primitives import ParallelPrimitive, WorkflowContext

async def main():
    launcher = DevEnvironmentLauncher()
    await launcher.start_all()
    print("✅ TTA.dev is running!")
    print("📊 Dashboard: http://localhost:8080")
    await launcher.wait_for_shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

**Files to create:**
- `scripts/dev_start.py`
- `platform/dev_environment/launcher.py`

#### 2.2 Health Check System
```bash
# CLI command to check system status
uv run python -m tta_dev_observability health

# Output:
# ✅ OTEL Collector: Running (port 4317)
# ✅ Dashboard: Running (http://localhost:8080)
# ✅ Primitives: 12 registered
# ✅ Active Workflows: 3
```

**Files to create:**
- `platform/observability/src/cli/health.py`

---

### Phase 3: Dashboard Auto-Growth (Priority: HIGH)

**Goal:** Dashboard adapts to whatever the agent builds

#### 3.1 Dynamic Metric Cards
```javascript
// Dashboard detects new metric types and creates cards
// Example: Agent adds caching → Cache Hit Rate card appears
function discoverMetrics() {
    // Query OTEL for all metric names
    // Create cards dynamically based on discovered metrics
}
```

**Files to modify:**
- `platform/observability/src/dashboard/ui/app.js`
- `platform/observability/src/dashboard/ui/metrics.js`

#### 3.2 Custom Primitive Detection
```python
# Dashboard recognizes when agent creates custom primitives
# Shows them in "User Primitives" section
class CustomPrimitiveDiscovery:
    def scan_for_primitives(self, directory: str) -> list[PrimitiveInfo]:
        """Scan project for classes inheriting from WorkflowPrimitive."""
        pass
```

**Files to create:**
- `platform/observability/src/dashboard/primitive_scanner.py`

#### 3.3 Endpoint Discovery (for APIs)
```python
# If agent builds a FastAPI/Flask app, discover endpoints
# Show them in dashboard with request metrics
class EndpointDiscovery:
    def discover_endpoints(self) -> list[Endpoint]:
        """Auto-detect HTTP endpoints from OTEL span data."""
        pass
```

**Files to create:**
- `platform/observability/src/dashboard/endpoint_discovery.py`

---

### Phase 4: Live Demo & Examples (Priority: MEDIUM)

**Goal:** Show the full stack in action

#### 4.1 Example: E-commerce Checkout Flow
```python
# examples/ecommerce_checkout.py
from tta_dev_primitives import (
    SequentialPrimitive,
    RetryPrimitive,
    CircuitBreakerPrimitive,
    WorkflowContext,
)

async def checkout_workflow():
    """
    Demonstrates:
    - Retry logic for payment processing
    - Circuit breaker for inventory service
    - Full observability in dashboard
    """
    workflow = SequentialPrimitive([
        validate_cart,
        RetryPrimitive(process_payment, max_attempts=3),
        CircuitBreakerPrimitive(reserve_inventory),
        send_confirmation,
    ])
    
    context = WorkflowContext(workflow_id="checkout")
    result = await workflow.execute(cart_data, context)
    return result
```

**Files to create:**
- `examples/ecommerce_checkout/`
- `examples/ecommerce_checkout/README.md`
- `examples/ecommerce_checkout/app.py`

#### 4.2 Example: Background Job Processor
```python
# examples/background_jobs.py
from tta_dev_primitives import ParallelPrimitive, RateLimitPrimitive

async def job_processor():
    """
    Demonstrates:
    - Parallel job execution
    - Rate limiting to external API
    - Job failure retry logic
    """
    pass
```

**Files to create:**
- `examples/background_jobs/`

---

## Implementation Timeline

### Week 1: Critical Path
- [ ] Service auto-discovery in dashboard
- [ ] Real-time WebSocket updates
- [ ] Workflow registry for primitives
- [ ] `dev_start.py` launcher script

### Week 2: Enhanced Experience
- [ ] Dynamic metric cards
- [ ] Custom primitive detection
- [ ] Health check CLI
- [ ] E-commerce example

### Week 3: Polish & Documentation
- [ ] Endpoint discovery for APIs
- [ ] Background jobs example
- [ ] Video walkthrough
- [ ] Update all docs to reflect batteries-included approach

---

## Success Metrics

1. **Time to First Trace:** < 30 seconds from clone to seeing live trace
2. **Agent Comprehension:** Agent can use primitives immediately (no questions)
3. **Dashboard Adaptation:** New services appear automatically (no config)
4. **Example Completeness:** Example apps work out-of-the-box

---

## Dependencies

### Required Packages
```toml
[project.dependencies]
opentelemetry-api = ">=1.20.0"
opentelemetry-sdk = ">=1.20.0"
opentelemetry-exporter-otlp = ">=1.20.0"
websockets = ">=12.0"
aiohttp = ">=3.9.0"
```

### Optional (for examples)
```toml
[project.optional-dependencies]
examples = [
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
]
```

---

## Files to Create/Modify

### New Files
- `scripts/dev_start.py` - One-command launcher
- `platform/observability/src/dashboard/discovery.py` - Service discovery
- `platform/observability/src/dashboard/websocket_server.py` - Live updates
- `platform/observability/src/dashboard/registry_api.py` - Workflow registry
- `platform/observability/src/cli/health.py` - Health checks
- `packages/tta-dev-primitives/src/tta_dev_primitives/core/registry.py` - Workflow registration
- `examples/ecommerce_checkout/` - Full example
- `examples/background_jobs/` - Full example

### Modified Files
- `platform/observability/src/dashboard/ui/app.js` - Auto-discovery UI
- `platform/observability/src/dashboard/server.py` - Add WebSocket support
- `packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py` - Add registry calls
- `GETTING_STARTED.md` - Update with one-command launch
- `README.md` - Emphasize batteries-included approach

---

## Next Actions

1. **Implement service discovery** (Phase 1.1)
2. **Add workflow registry** (Phase 1.2)
3. **Create dev_start.py** (Phase 2.1)
4. **Build e-commerce example** (Phase 4.1)

Let's start with Phase 1.1 - Service Auto-Discovery.
