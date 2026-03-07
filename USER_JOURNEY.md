# TTA.dev User Journey

## Vision: Batteries-Included AI Development Platform

TTA.dev is a **standalone, self-contained platform** that enables AI coding agents (Claude, Copilot, Cline) to build production-grade applications with built-in observability, testing, and primitives.

## The 5-Minute Experience

### Step 1: Clone & Discover (30 seconds)

```bash
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev
```

**What happens:**
- User clones the repository
- No configuration needed yet

### Step 2: Agent Auto-Detection (Instant)

When any CLI agent (Claude, Copilot, Cline) opens the repository:

1. **Agent discovers `AGENTS.md`** - The global coordination file
2. **Agent loads `.github/copilot-instructions.md`** - TTA.dev conventions
3. **Agent detects primitives catalog** - `PRIMITIVES_CATALOG.md`
4. **Agent sees batteries-included setup** - Ready to use immediately

**Key Files the Agent Reads:**
```
TTA.dev/
├── AGENTS.md                          # 👈 Agent coordination hub
├── .github/copilot-instructions.md    # 👈 Coding standards
├── PRIMITIVES_CATALOG.md              # 👈 Available building blocks
├── USER_JOURNEY.md                    # 👈 This file
└── GETTING_STARTED.md                 # 👈 Quick start guide
```

### Step 3: Agent Starts Building (Immediate)

The agent can **immediately** use TTA.dev patterns:

```python
from tta_dev_primitives import RetryPrimitive, TimeoutPrimitive, WorkflowContext

# Agent writes this automatically - with observability built-in
workflow = TimeoutPrimitive(
    RetryPrimitive(
        my_api_call,
        max_attempts=3
    ),
    timeout_seconds=30.0
)

context = WorkflowContext(workflow_id="user-task")
result = await workflow.execute(data, context)
```

**What's happening behind the scenes:**
- ✅ OpenTelemetry traces automatically generated
- ✅ Metrics collected (latency, retries, failures)
- ✅ Logs correlated with trace IDs
- ✅ All data flows to the observability UI

### Step 4: Launch Observability Dashboard (30 seconds)

```bash
uv run python -m tta_dev_observability
```

**Browser opens to `http://localhost:8080`** showing:

```
┌─────────────────────────────────────────────────────────┐
│  TTA.dev Observability Dashboard                        │
├─────────────────────────────────────────────────────────┤
│  📊 Live Traces                                         │
│  ├─ workflow_id: user-task                              │
│  │  ├─ RetryPrimitive (3 attempts, 1.2s)               │
│  │  └─ TimeoutPrimitive (passed, 2.5s total)           │
│  │                                                       │
│  📈 System Metrics                                      │
│  ├─ Total workflows: 127                                │
│  ├─ Success rate: 94.2%                                 │
│  └─ Avg latency: 1.8s                                   │
│                                                          │
│  🔍 Recent Events                                       │
│  ├─ RetryPrimitive: 3 attempts, succeeded               │
│  └─ Agent created new workflow                          │
└─────────────────────────────────────────────────────────┘
```

### Step 5: Agent Builds More - Dashboard Grows Automatically

As the agent builds new features:

1. **Agent creates a new service** → Dashboard adds a new service card
2. **Agent adds API endpoints** → Dashboard shows endpoint metrics
3. **Agent writes background jobs** → Dashboard tracks job execution
4. **Agent adds caching** → Dashboard shows cache hit rates

**The dashboard is self-discovering** - it automatically detects and visualizes whatever the agent builds.

---

## Key Design Principles

### 1. Zero Configuration for Agents

Agents should **just work** when they see the repository structure:

- `AGENTS.md` → Coordination instructions
- `.github/copilot-instructions.md` → Coding standards
- `PRIMITIVES_CATALOG.md` → Available tools

### 2. Batteries-Included Observability

Every primitive automatically emits:
- OpenTelemetry traces
- Structured metrics
- Correlated logs

**No manual instrumentation required.**

### 3. Self-Discovering Dashboard

The observability UI:
- ✅ Discovers new workflows automatically
- ✅ Adapts to user's application structure
- ✅ Shows live data with no config files
- ✅ Grows as the agent builds more

### 4. Production-Ready from Day 1

Everything includes:
- Error handling (RetryPrimitive, FallbackPrimitive)
- Timeouts (TimeoutPrimitive)
- Circuit breaking (CircuitBreakerPrimitive)
- Rate limiting (RateLimitPrimitive)
- Caching (CachePrimitive)

---

## What Makes This Different

| Traditional Approach | TTA.dev Approach |
|---------------------|------------------|
| Manual instrumentation | Automatic via primitives |
| Configure observability tools | Built-in dashboard |
| Write retry logic | Use RetryPrimitive |
| Setup monitoring | Already running |
| Deploy to see traces | See traces locally instantly |

---

## Success Criteria

A user has succeeded when:

1. ✅ Clone repo → Agent immediately understands TTA.dev patterns
2. ✅ Agent writes code using primitives (not manual loops)
3. ✅ Launch dashboard → See live traces within 30 seconds
4. ✅ Agent builds new features → Dashboard automatically adapts
5. ✅ User deploys → Same observability works in production

---

## Implementation Roadmap

### Phase 1: Agent Discovery (Complete)
- ✅ `AGENTS.md` global coordination
- ✅ `.github/copilot-instructions.md` standards
- ✅ `PRIMITIVES_CATALOG.md` reference

### Phase 2: Batteries-Included Observability (In Progress)
- ✅ OpenTelemetry integration in primitives
- ✅ Web dashboard with live traces
- 🔄 Auto-discovery of user workflows
- 🔄 Self-expanding dashboard

### Phase 3: Production Hardening (Next)
- Circuit breaker primitive
- Rate limiting primitive
- Adaptive sampling
- Performance benchmarks

### Phase 4: Community Enablement (Future)
- Example applications
- Video tutorials
- Community primitives library

---

## Directory Structure for This Vision

```
TTA.dev/
├── AGENTS.md                      # Agent coordination hub
├── USER_JOURNEY.md                # This file - the vision
├── GETTING_STARTED.md             # Quick start for humans
├── PRIMITIVES_CATALOG.md          # Complete primitive reference
│
├── .github/
│   ├── copilot-instructions.md    # Coding standards for agents
│   └── agents/                    # Custom agent definitions
│
├── packages/
│   └── tta-dev-primitives/        # Core primitives with built-in observability
│
├── platform/
│   ├── observability/             # Self-discovering dashboard
│   └── testing/                   # Testing utilities
│
├── scripts/
│   └── dev_start.sh               # One command to launch everything
│
└── examples/                      # Working examples for agents
```

---

## Quick Commands

```bash
# Start everything (observability + any running services)
uv run python scripts/dev_start.py

# Run tests with observability
uv run pytest --with-observability

# View traces from CLI
uv run python -m tta_dev_observability traces --live

# Check system health
uv run python -m tta_dev_observability health
```

---

## Next Steps

1. Implement self-discovering dashboard
2. Create `scripts/dev_start.py` - one command to launch everything
3. Add example applications that demonstrate the full stack
4. Create video walkthrough of 5-minute experience
5. Document production deployment patterns

---

**The Goal:** Any AI agent can clone TTA.dev and immediately start building production-grade applications with world-class observability - all batteries included.
