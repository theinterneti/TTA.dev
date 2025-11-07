# E2B Advanced Features - Quick Start Guide

**From Basic Iterative Refinement → Production-Ready with Templates & Webhooks**

---

## 🎯 What You Get

Starting from our **iterative code refinement pattern**, you can enhance it with:

| Feature | Benefit | Time Investment | Impact |
|---------|---------|----------------|--------|
| **Templates** | 10-50x faster startup | 15 minutes | 🚀🚀🚀🚀🚀 |
| **Webhooks** | Real-time monitoring | 30 minutes | 📊📊📊📊 |
| **Combined** | Ultimate observability | 45 minutes | 🎯🎯🎯🎯🎯 |

---

## ⚡ Quick Start 1: Create ML Template

**Time:** 15 minutes
**Benefit:** 30 seconds → 100ms sandbox startup

### Step 1: Create Template File

We've already created one for you:

```bash
# File: packages/tta-dev-primitives/examples/e2b.Dockerfile.ml-template
# Contains: PyTorch, Transformers, NumPy, Pandas, Scikit-learn
```

### Step 2: Build Template

```bash
# Navigate to examples directory
cd packages/tta-dev-primitives/examples

# Install E2B CLI (if not already installed)
npm install -g @e2b/cli

# OR using Homebrew (macOS)
brew install e2b

# Build your template
e2b template build --file e2b.Dockerfile.ml-template

# Output will show:
# ✅ Template built successfully!
# 📋 Template ID: template_abc123xyz456
#
# Copy this ID - you'll need it!
```

### Step 3: Use Your Template

```python
from e2b_code_interpreter import Sandbox

# OLD WAY (5-10 seconds startup)
sandbox = await Sandbox.create()

# NEW WAY (100ms startup!)
sandbox = await Sandbox.create(template="template_abc123xyz456")

# Execute immediately - dependencies already installed!
result = await sandbox.run_code("""
import torch
import transformers

print("Ready to go!")
""")
```

### Step 4: Test It

```bash
# Set your template ID
export E2B_ML_TEMPLATE_ID=template_abc123xyz456

# Run the advanced example
python packages/tta-dev-primitives/examples/e2b_advanced_iterative_refinement.py
```

**Expected:** Demo 2 shows ~0.1s startup vs ~5-10s without template!

---

## 📊 Quick Start 2: Enable Webhook Monitoring

**Time:** 30 minutes
**Benefit:** Real-time cost tracking, runaway detection, analytics

### Step 1: Run Webhook Server

We've created a complete server for you:

```bash
# Terminal 1: Start webhook server
export E2B_WEBHOOK_SECRET="your-secret-key-here"
export DAILY_SANDBOX_LIMIT=100
export SANDBOX_TIMEOUT_MINUTES=10

python packages/tta-dev-primitives/examples/e2b_webhook_monitoring_server.py

# Server starts on http://localhost:8000
# Endpoints:
#   POST /webhooks/e2b  - Receive events
#   GET  /metrics       - View statistics
#   GET  /health        - Health check
#   GET  /sandboxes/active  - List running sandboxes
#   GET  /sandboxes/runaway - Find long-running ones
```

### Step 2: Register Webhook with E2B

```bash
# Terminal 2: Register webhook
curl -X POST https://api.e2b.app/events/webhooks \
  -H "X-API-Key: $E2B_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Local Development Webhook",
    "url": "http://your-server.com/webhooks/e2b",
    "enabled": true,
    "events": [
      "sandbox.lifecycle.created",
      "sandbox.lifecycle.killed"
    ],
    "signatureSecret": "your-secret-key-here"
  }'

# Returns:
# {
#   "id": "webhook_xyz789abc",
#   "name": "Local Development Webhook",
#   ...
# }
```

**Note:** For local testing, use `ngrok` or similar to expose localhost:

```bash
# Install ngrok: https://ngrok.com
ngrok http 8000

# Use the ngrok URL in webhook registration:
# "url": "https://abc123.ngrok.io/webhooks/e2b"
```

### Step 3: Watch Events Stream In

```bash
# Terminal 3: Create some sandboxes
python -c "
import asyncio
from e2b_code_interpreter import Sandbox

async def test():
    sandbox = await Sandbox.create()
    print('Sandbox created!')
    await asyncio.sleep(2)
    await sandbox.kill()
    print('Sandbox killed!')

asyncio.run(test())
"

# Terminal 1 (webhook server) will show:
# 🟢 Sandbox created: abc123... (concurrent: 1, template: default)
# 🔴 Sandbox killed: abc123... (lifetime: 0:00:02)
```

### Step 4: Check Metrics Dashboard

```bash
# View current metrics
curl http://localhost:8000/metrics

# Returns:
# {
#   "metrics": {
#     "total_created": 5,
#     "total_killed": 4,
#     "current_concurrent": 1,
#     "peak_concurrent": 3,
#     "templates_used": {"default": 3, "template_ml_abc": 2},
#     "events_received": 10
#   },
#   "active_sandboxes": 1,
#   "timestamp": "2025-11-06T..."
# }
```

---

## 🎯 Quick Start 3: Combined Pattern

**Time:** 5 minutes (if you've done steps 1 & 2)
**Benefit:** Ultimate production-ready pattern

### Run Complete Demo

```bash
# Set template ID from Quick Start 1
export E2B_ML_TEMPLATE_ID=template_abc123xyz456

# Set webhook URL (if using ngrok)
export E2B_WEBHOOK_URL=https://abc123.ngrok.io/webhooks

# Run advanced example
python packages/tta-dev-primitives/examples/e2b_advanced_iterative_refinement.py

# Output:
# 🚀 E2B ADVANCED ITERATIVE REFINEMENT DEMOS
#
# ============================================================
# DEMO 1: Basic Iterative Refinement (No Template)
# ============================================================
# ... (shows basic pattern)
#
# ============================================================
# DEMO 2: With ML Template (Fast Startup)
# ============================================================
# ⚡ Template startup: 0.098s (should be ~0.1s)
# ✅ Template startup should be ~0.1s vs 5-10s without template!
#
# ============================================================
# DEMO 3: Full Stack (Template + Webhooks)
# ============================================================
# ✅ Check webhook server logs for real-time events!
#    Metrics: http://localhost:8000/metrics
```

### What You Get

- ✅ **10-50x faster** execution (template)
- ✅ **Real-time monitoring** (webhooks)
- ✅ **Working code guarantee** (iteration)
- ✅ **Cost tracking** (webhook metrics)
- ✅ **Runaway detection** (webhook timeouts)
- ✅ **Full observability** (WorkflowContext + webhooks)

---

## 📦 Template Library

### Available Templates

We provide these template examples:

| Template | File | Use Case | Installed |
|----------|------|----------|-----------|
| **ML** | `e2b.Dockerfile.ml-template` | PyTorch, Transformers | torch, transformers, numpy, pandas, sklearn |
| **Data Science** | _(create your own)_ | Analysis, visualization | pandas, matplotlib, seaborn, plotly |
| **Web Dev** | _(create your own)_ | API testing, frontend | node, flask, fastapi, requests |

### Create Your Own Template

```dockerfile
# e2b.Dockerfile.custom
FROM e2bdev/code-interpreter:latest

# Install your dependencies
RUN pip install your-package-1 your-package-2

# Install system packages
RUN apt-get update && apt-get install -y ffmpeg

# Copy files
COPY your-files/ /root/files/

# Set environment
ENV YOUR_VAR=value
```

Then build:

```bash
e2b template build --file e2b.Dockerfile.custom
```

---

## 🔍 Webhook Use Cases

### Use Case 1: Cost Tracking

```python
# Webhook automatically logs all sandbox creation/termination
# Check daily usage:
curl http://localhost:8000/metrics

# Returns:
# {
#   "total_created": 47,  # Today's sandboxes
#   "total_killed": 45,   # Terminated
#   "current_concurrent": 2  # Running now
# }
```

### Use Case 2: Budget Enforcement

```python
# In webhook_monitoring_server.py:
DAILY_SANDBOX_LIMIT = 100

# Server automatically alerts when exceeded
# You can add logic to prevent new creations
```

### Use Case 3: Runaway Detection

```python
# Check for long-running sandboxes:
curl http://localhost:8000/sandboxes/runaway

# Returns:
# {
#   "runaway_sandboxes": [
#     {
#       "sandbox_id": "abc123...",
#       "lifetime_seconds": 720,
#       "exceeded_by_seconds": 120  # 2 min over 10 min limit
#     }
#   ]
# }
```

### Use Case 4: Analytics

```python
# Template usage breakdown:
curl http://localhost:8000/metrics

# Shows which templates are most used:
# {
#   "templates_used": {
#     "template_ml_abc": 23,
#     "template_data_xyz": 15,
#     "default": 9
#   }
# }
```

---

## 🚀 Integration with TTA.dev

### Update Your Workflows

```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive

# OLD: Basic execution
executor = CodeExecutionPrimitive()

# NEW: With template + webhook monitoring
from examples.e2b_advanced_iterative_refinement import (
    AdvancedIterativeCodeGenerator
)

generator = AdvancedIterativeCodeGenerator(
    template_id="template_ml_abc123",
    webhook_url="https://your-server.com/webhooks",
    max_attempts=3
)

# Use in workflow
result = await generator.generate_working_code(
    requirement="Your task here",
    context=WorkflowContext(correlation_id="req-123")
)
```

---

## 📊 Performance Comparison

### Without Templates

```
Generate code:      1.2s
Create sandbox:     8.5s  ← Installing packages
Execute code:       0.3s
Total:             10.0s
```

### With Templates

```
Generate code:      1.2s
Create sandbox:     0.1s  ← Pre-built template!
Execute code:       0.3s
Total:              1.6s  ← 84% faster!
```

### With Templates + Webhooks

```
Generate code:      1.2s
Create sandbox:     0.1s
Execute code:       0.3s
Total:              1.6s

PLUS:
- Real-time event tracking
- Cost monitoring
- Runaway detection
- Analytics dashboard
```

---

## 🎓 Learning Path

### Level 1: Basic Iterative Refinement (Already Done!)

✅ Generate → Execute → Fix → Repeat
✅ Works with default template
✅ No setup required

**File:** `e2b_iterative_code_refinement.py`

### Level 2: Add Templates (15 minutes)

📚 Create custom template
📚 10-50x faster startup
📚 Consistent environment

**Files:**
- `e2b.Dockerfile.ml-template`
- `e2b_advanced_iterative_refinement.py` (Demo 2)

### Level 3: Add Webhooks (30 minutes)

📊 Real-time monitoring
📊 Cost tracking
📊 Budget enforcement

**Files:**
- `e2b_webhook_monitoring_server.py`
- `e2b_advanced_iterative_refinement.py` (Demo 3)

### Level 4: Production Deployment

🚀 Deploy webhook server
🚀 Create template library
🚀 Integrate with observability stack
🚀 Build analytics dashboard

**Documentation:** `E2B_ADVANCED_FEATURES_EXPANSION.md`

---

## 🔗 Related Documentation

- **Basic Pattern:** `E2B_ITERATIVE_REFINEMENT_PATTERN.md`
- **Phase 1 Complete:** `E2B_PHASE1_COMPLETE.md`
- **Integration Guide:** `E2B_README.md`
- **Advanced Features:** `E2B_ADVANCED_FEATURES_EXPANSION.md`

---

## 💡 Tips & Tricks

### Tip 1: Cache Template ID

```bash
# Save to .env file
echo "E2B_ML_TEMPLATE_ID=template_abc123xyz" >> .env

# Load in code
from dotenv import load_dotenv
load_dotenv()

template_id = os.getenv("E2B_ML_TEMPLATE_ID")
```

### Tip 2: Use ngrok for Local Webhooks

```bash
# Install ngrok
brew install ngrok  # macOS
# or download from https://ngrok.com

# Expose local server
ngrok http 8000

# Use ngrok URL in webhook registration
# https://abc123.ngrok.io/webhooks/e2b
```

### Tip 3: Monitor Template Usage

```python
# Check which templates are being used
curl http://localhost:8000/metrics | jq '.metrics.templates_used'

# Output:
# {
#   "template_ml_abc": 45,
#   "template_data_xyz": 23,
#   "default": 7
# }

# Use this to decide which templates to optimize
```

### Tip 4: Set Reasonable Limits

```bash
# In webhook server
export DAILY_SANDBOX_LIMIT=100        # Max sandboxes per day
export SANDBOX_TIMEOUT_MINUTES=10     # Max lifetime per sandbox

# Prevents runaway costs!
```

---

## 🎉 You're Ready!

You now have:

✅ **Basic iterative refinement** - Working code guarantee
✅ **Template creation** - 10-50x faster execution
✅ **Webhook monitoring** - Real-time observability
✅ **Production pattern** - All three combined

**Next steps:**

1. Build your first template (15 min)
2. Run webhook server (30 min)
3. Test combined pattern (5 min)
4. Integrate into your workflows! 🚀

---

**Last Updated:** November 6, 2025
**Status:** READY TO USE
**Questions?** See `E2B_ADVANCED_FEATURES_EXPANSION.md`
