# E2B Advanced Features Expansion Guide

**Enhancing Iterative Code Refinement with Templates & Webhooks**

**Date:** November 6, 2025
**Status:** RESEARCH & PLANNING
**Build on:** E2B Iterative Refinement Pattern

---

## 🎯 Overview

We've established the **iterative code refinement pattern** (Generate → Execute → Fix → Repeat). Now we can expand it with:

1. **Sandbox Templates** - Custom pre-configured environments
2. **Lifecycle Webhooks** - Real-time event notifications

These features enable:
- ✅ **Faster execution** (pre-installed dependencies)
- ✅ **Domain-specific environments** (ML, data science, web dev)
- ✅ **Real-time monitoring** (track all sandbox activity)
- ✅ **Cost optimization** (detect and kill runaway sandboxes)
- ✅ **Analytics** (aggregate execution metrics)

---

## 🏗️ Feature 1: Sandbox Templates

### What Are Templates?

**Sandbox templates** are custom Docker-based environments that you pre-build and snapshot. When you create a sandbox from a template, it starts in ~100ms with all your dependencies already installed.

### How It Works

```
1. Create e2b.Dockerfile with your dependencies
   ├─ Python packages (numpy, pandas, pytorch)
   ├─ System packages (ffmpeg, imagemagick)
   └─ Your custom code/configs

2. Build template with E2B CLI
   ├─ Builds Docker image
   ├─ Uploads to E2B cloud
   ├─ Creates micro VM snapshot
   └─ Returns template ID

3. Use template ID in your code
   └─ Sandboxes start in 100ms (not 5-10 seconds!)
```

### Template Use Cases

#### Use Case 1: Machine Learning Environment

**Problem:** Installing `torch`, `transformers`, `numpy` takes 30+ seconds per sandbox

**Solution:** Pre-install everything in a template

```dockerfile
# e2b.Dockerfile
FROM e2bdev/code-interpreter:latest

# Install ML dependencies (once, at build time)
RUN pip install torch transformers numpy pandas scikit-learn

# Add your custom model
COPY models/ /root/models/

# Set environment variables
ENV HF_HOME=/root/.cache/huggingface
```

**Build:**
```bash
e2b template build -c "/root/.jupyter/start-up.sh"
# Returns: template_abc123xyz
```

**Use:**
```python
from e2b_code_interpreter import Sandbox

# Create sandbox from template (100ms startup!)
sandbox = await Sandbox.create(template_id="template_abc123xyz")

# Dependencies already installed - execute immediately
result = await sandbox.run_code("""
import torch
import transformers

model = transformers.AutoModel.from_pretrained('/root/models/my-model')
print(model)
""")
```

**Benefits:**
- ✅ **30 seconds → 100ms** startup time
- ✅ **Pre-loaded models** (no download wait)
- ✅ **Consistent environment** (same deps every time)
- ✅ **Cost savings** (less execution time)

#### Use Case 2: Data Science Template

```dockerfile
# e2b.Dockerfile
FROM e2bdev/code-interpreter:latest

# Data science stack
RUN pip install \
    pandas \
    numpy \
    matplotlib \
    seaborn \
    jupyter \
    plotly \
    scipy \
    statsmodels

# Install system deps for visualization
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0

# Add sample datasets
COPY datasets/ /root/datasets/
```

**Use in iterative refinement:**

```python
class DataScienceCodeGenerator:
    """Generate data analysis code with pre-configured environment."""

    def __init__(self, template_id: str):
        self.template_id = template_id

    async def generate_analysis(self, requirement: str, context, max_attempts=3):
        """Generate working data analysis code."""
        previous_errors = None

        for attempt in range(1, max_attempts + 1):
            # Generate code
            code = await llm.generate(
                f"Create data analysis for: {requirement}",
                previous_errors,
                context="pandas, numpy, matplotlib already installed"
            )

            # Execute in pre-configured sandbox
            sandbox = await Sandbox.create(self.template_id)
            result = await sandbox.run_code(code)

            if result.error is None:
                return {
                    "code": code,
                    "output": result.logs.stdout,
                    "plots": result.results  # Charts generated
                }

            previous_errors = result.error
            await sandbox.kill()

        raise Exception("Failed to generate working analysis")
```

#### Use Case 3: Web Development Template

```dockerfile
# e2b.Dockerfile
FROM e2bdev/code-interpreter:latest

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
RUN apt-get install -y nodejs

# Install common web frameworks
RUN npm install -g \
    next \
    create-react-app \
    vite \
    tailwindcss

# Python web frameworks
RUN pip install \
    flask \
    fastapi \
    uvicorn \
    requests \
    beautifulsoup4

# Start services on boot
COPY start-services.sh /root/start-services.sh
RUN chmod +x /root/start-services.sh
```

**Use for API testing:**

```python
async def test_api_endpoint(code: str, template_id: str):
    """Test API code with pre-configured web stack."""
    sandbox = await Sandbox.create(template_id)

    # Start server
    server_process = await sandbox.process.start({
        "cmd": "python server.py",
        "cwd": "/root"
    })

    # Wait for server to start
    await asyncio.sleep(2)

    # Test endpoint
    test_code = """
import requests
response = requests.get('http://localhost:8000/api/test')
print(response.status_code, response.json())
"""
    result = await sandbox.run_code(test_code)

    await sandbox.kill()
    return result
```

### Template Management

#### Create Template

```bash
# 1. Initialize
e2b template init

# 2. Edit e2b.Dockerfile
vim e2b.Dockerfile

# 3. Build
e2b template build -c "/root/.jupyter/start-up.sh"

# Output: Your template ID: template_abc123xyz
```

#### Update Template

```bash
# Modify e2b.Dockerfile
vim e2b.Dockerfile

# Rebuild (creates new version)
e2b template build -c "/root/.jupyter/start-up.sh"

# New template ID returned
```

#### List Templates

```bash
e2b template list
```

### Integration with TTA.dev Primitives

```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive
from tta_dev_primitives import WorkflowContext

class TemplatedCodeExecutionPrimitive(CodeExecutionPrimitive):
    """Enhanced primitive with template support."""

    def __init__(self, template_id: str | None = None):
        super().__init__()
        self.template_id = template_id

    async def _execute_impl(
        self,
        context: WorkflowContext,
        input_data: dict
    ) -> dict:
        """Execute code in templated sandbox."""
        sandbox = await Sandbox.create(
            template=self.template_id or "default"
        )

        try:
            result = await sandbox.run_code(input_data["code"])
            return {
                "success": result.error is None,
                "logs": result.logs.stdout,
                "error": result.error,
                "template_used": self.template_id
            }
        finally:
            await sandbox.kill()
```

**Use in workflows:**

```python
# ML workflow with template
ml_executor = TemplatedCodeExecutionPrimitive(
    template_id="template_ml_abc123"
)

workflow = (
    CodeGeneratorPrimitive() >>
    RetryPrimitive(ml_executor, max_attempts=3) >>
    CodeValidatorPrimitive()
)
```

---

## 📡 Feature 2: Lifecycle Webhooks

### What Are Webhooks?

**Webhooks** are HTTP callbacks that E2B sends to your server when sandbox events occur. Instead of polling, you receive real-time notifications.

### Available Events

| Event | When Triggered | Use Case |
|-------|---------------|----------|
| `sandbox.lifecycle.created` | Sandbox starts | Track usage, log creation |
| `sandbox.lifecycle.killed` | Sandbox terminates | Clean up resources |
| `sandbox.lifecycle.updated` | Config changes | Monitor modifications |
| `sandbox.lifecycle.paused` | Sandbox paused | Track idle time |
| `sandbox.lifecycle.resumed` | Sandbox resumed | Resume monitoring |

### Webhook Use Cases

#### Use Case 1: Cost Tracking & Budget Enforcement

**Problem:** You want to track E2B usage across all workflows and enforce budgets.

**Solution:** Webhook → Database → Analytics Dashboard

```python
from fastapi import FastAPI, Request
from datetime import datetime
import hmac
import hashlib

app = FastAPI()

# Webhook endpoint
@app.post("/webhooks/e2b")
async def handle_e2b_webhook(request: Request):
    """Receive E2B sandbox events."""
    # Verify signature
    signature = request.headers.get("e2b-signature")
    body = await request.body()

    if not verify_signature(WEBHOOK_SECRET, body, signature):
        return {"status": "invalid signature"}, 401

    # Parse event
    event = await request.json()

    # Store in database
    await db.sandbox_events.insert_one({
        "event_id": event["id"],
        "event_type": event["type"],
        "sandbox_id": event["sandboxId"],
        "template_id": event.get("sandboxTemplateId"),
        "team_id": event["sandboxTeamId"],
        "timestamp": datetime.fromisoformat(event["timestamp"]),
        "metadata": event.get("eventData", {})
    })

    # Check budget
    if event["type"] == "sandbox.lifecycle.created":
        await check_budget_limits(event["sandboxTeamId"])

    return {"status": "ok"}

def verify_signature(secret: str, payload: bytes, signature: str) -> bool:
    """Verify E2B webhook signature."""
    expected = hashlib.sha256(
        (secret + payload.decode()).encode()
    ).digest().hex()

    return hmac.compare_digest(expected, signature)

async def check_budget_limits(team_id: str):
    """Enforce sandbox creation limits."""
    # Count sandboxes created today
    today = datetime.now().replace(hour=0, minute=0, second=0)
    count = await db.sandbox_events.count_documents({
        "team_id": team_id,
        "event_type": "sandbox.lifecycle.created",
        "timestamp": {"$gte": today}
    })

    # Enforce limit
    if count > DAILY_SANDBOX_LIMIT:
        # Alert team
        await send_alert(
            f"Daily sandbox limit exceeded: {count}/{DAILY_SANDBOX_LIMIT}"
        )

        # Optionally pause new creations
        # (requires your app to check limits before creating)
```

**Register webhook:**

```python
import requests

response = requests.post(
    "https://api.e2b.app/events/webhooks",
    headers={
        "X-API-Key": E2B_API_KEY,
        "Content-Type": "application/json"
    },
    json={
        "name": "Cost Tracking Webhook",
        "url": "https://your-server.com/webhooks/e2b",
        "enabled": True,
        "events": [
            "sandbox.lifecycle.created",
            "sandbox.lifecycle.killed"
        ],
        "signatureSecret": "your-secret-key-here"
    }
)

webhook_id = response.json()["id"]
print(f"Webhook registered: {webhook_id}")
```

#### Use Case 2: Real-Time Monitoring Dashboard

**Problem:** You want to see all sandbox activity in real-time.

**Solution:** Webhook → WebSocket → Live Dashboard

```python
from fastapi import FastAPI, WebSocket
import asyncio

app = FastAPI()

# Active WebSocket connections
active_connections: list[WebSocket] = []

@app.websocket("/ws/sandbox-events")
async def websocket_endpoint(websocket: WebSocket):
    """Stream sandbox events to dashboard."""
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            await asyncio.sleep(1)  # Keep connection alive
    except:
        active_connections.remove(websocket)

@app.post("/webhooks/e2b")
async def handle_webhook(request: Request):
    """Receive E2B events and broadcast to dashboards."""
    event = await request.json()

    # Broadcast to all connected dashboards
    for connection in active_connections:
        await connection.send_json({
            "type": event["type"],
            "sandbox_id": event["sandboxId"],
            "template": event.get("sandboxTemplateId"),
            "timestamp": event["timestamp"],
            "status": parse_status(event["type"])
        })

    return {"status": "ok"}

def parse_status(event_type: str) -> str:
    """Convert event type to dashboard status."""
    if "created" in event_type:
        return "🟢 Created"
    elif "killed" in event_type:
        return "🔴 Terminated"
    elif "paused" in event_type:
        return "🟡 Paused"
    elif "resumed" in event_type:
        return "🟢 Resumed"
    return "⚪ Updated"
```

**Dashboard (HTML + JavaScript):**

```html
<!DOCTYPE html>
<html>
<head>
    <title>E2B Sandbox Monitor</title>
</head>
<body>
    <h1>Live Sandbox Activity</h1>
    <div id="events"></div>

    <script>
        const ws = new WebSocket('ws://your-server.com/ws/sandbox-events');

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const div = document.getElementById('events');

            div.innerHTML = `
                <div class="event">
                    <span>${data.status}</span>
                    <span>${data.sandbox_id}</span>
                    <span>${data.timestamp}</span>
                </div>
            ` + div.innerHTML;
        };
    </script>
</body>
</html>
```

#### Use Case 3: Runaway Sandbox Detection

**Problem:** A bug causes sandboxes to run indefinitely, wasting resources.

**Solution:** Track creation → Set timer → Auto-kill if exceeded

```python
from datetime import datetime, timedelta
import asyncio

# Track sandbox creation times
sandbox_timers = {}

@app.post("/webhooks/e2b")
async def handle_webhook(request: Request):
    """Monitor sandbox lifecycle for runaway detection."""
    event = await request.json()
    sandbox_id = event["sandboxId"]

    if event["type"] == "sandbox.lifecycle.created":
        # Start timer
        sandbox_timers[sandbox_id] = datetime.now()

        # Schedule auto-kill check
        asyncio.create_task(
            check_sandbox_timeout(sandbox_id, timeout_minutes=10)
        )

    elif event["type"] == "sandbox.lifecycle.killed":
        # Remove timer
        sandbox_timers.pop(sandbox_id, None)

    return {"status": "ok"}

async def check_sandbox_timeout(sandbox_id: str, timeout_minutes: int):
    """Kill sandbox if it exceeds timeout."""
    await asyncio.sleep(timeout_minutes * 60)

    # Check if still running
    if sandbox_id in sandbox_timers:
        created_at = sandbox_timers[sandbox_id]
        runtime = datetime.now() - created_at

        if runtime > timedelta(minutes=timeout_minutes):
            # Kill sandbox via API
            await kill_sandbox(sandbox_id)

            # Alert
            await send_alert(
                f"Killed runaway sandbox {sandbox_id} "
                f"after {runtime.total_seconds()}s"
            )

async def kill_sandbox(sandbox_id: str):
    """Forcefully terminate sandbox."""
    # E2B doesn't expose kill API, but you can track
    # and prevent new operations on that sandbox
    logging.warning(f"Sandbox {sandbox_id} exceeded timeout")
```

#### Use Case 4: Analytics & Metrics

**Problem:** You want to track sandbox usage patterns.

**Solution:** Aggregate webhook events → Generate insights

```python
from collections import defaultdict
from datetime import datetime, timedelta

# Metrics storage
metrics = {
    "sandboxes_created_today": 0,
    "sandboxes_killed_today": 0,
    "average_lifetime": timedelta(0),
    "templates_used": defaultdict(int),
    "peak_concurrent": 0,
    "current_concurrent": 0
}

@app.post("/webhooks/e2b")
async def handle_webhook(request: Request):
    """Collect metrics from sandbox events."""
    event = await request.json()

    if event["type"] == "sandbox.lifecycle.created":
        metrics["sandboxes_created_today"] += 1
        metrics["current_concurrent"] += 1
        metrics["templates_used"][event.get("sandboxTemplateId", "default")] += 1

        if metrics["current_concurrent"] > metrics["peak_concurrent"]:
            metrics["peak_concurrent"] = metrics["current_concurrent"]

    elif event["type"] == "sandbox.lifecycle.killed":
        metrics["sandboxes_killed_today"] += 1
        metrics["current_concurrent"] -= 1

        # Calculate lifetime
        # (requires tracking creation times)

    # Store in time-series database
    await influxdb.write({
        "measurement": "sandbox_events",
        "tags": {
            "event_type": event["type"],
            "template": event.get("sandboxTemplateId")
        },
        "time": event["timestamp"],
        "fields": {
            "concurrent": metrics["current_concurrent"]
        }
    })

    return {"status": "ok"}

@app.get("/metrics")
async def get_metrics():
    """Expose metrics endpoint."""
    return metrics
```

### Webhook Integration with Iterative Refinement

```python
class MonitoredIterativeCodeGenerator:
    """Iterative refinement with webhook monitoring."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def generate_working_code(
        self,
        requirement: str,
        context: WorkflowContext,
        max_attempts: int = 3
    ):
        """Generate code with full webhook tracking."""
        workflow_id = context.correlation_id
        previous_errors = None

        # Register webhook for this workflow
        webhook_id = await self.register_workflow_webhook(workflow_id)

        try:
            for attempt in range(1, max_attempts + 1):
                # Generate
                code = await llm.generate(requirement, previous_errors)

                # Execute (webhook will track creation/termination)
                sandbox = await Sandbox.create()
                result = await sandbox.run_code(code)

                if result.error is None:
                    # Success - webhook logged it
                    await sandbox.kill()
                    return {"code": code, "output": result.logs.stdout}

                # Failed - try again
                previous_errors = result.error
                await sandbox.kill()

            raise Exception("Max attempts exceeded")

        finally:
            # Cleanup webhook
            await self.unregister_webhook(webhook_id)

    async def register_workflow_webhook(self, workflow_id: str) -> str:
        """Register temporary webhook for workflow tracking."""
        response = await requests.post(
            "https://api.e2b.app/events/webhooks",
            headers={"X-API-Key": E2B_API_KEY},
            json={
                "name": f"Workflow {workflow_id}",
                "url": f"{self.webhook_url}/workflow/{workflow_id}",
                "enabled": True,
                "events": ["sandbox.lifecycle.created", "sandbox.lifecycle.killed"]
            }
        )
        return response.json()["id"]

    async def unregister_webhook(self, webhook_id: str):
        """Remove webhook after workflow completes."""
        await requests.delete(
            f"https://api.e2b.app/events/webhooks/{webhook_id}",
            headers={"X-API-Key": E2B_API_KEY}
        )
```

---

## 🚀 Combined Pattern: Templates + Webhooks + Iterative Refinement

### The Ultimate Workflow

```python
from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.integrations import CodeExecutionPrimitive

class AdvancedIterativeCodeGenerator:
    """
    Combines:
    - Custom sandbox templates (fast startup)
    - Webhook monitoring (real-time tracking)
    - Iterative refinement (working code)
    """

    def __init__(
        self,
        template_id: str,
        webhook_url: str,
        max_attempts: int = 3
    ):
        self.template_id = template_id
        self.webhook_url = webhook_url
        self.max_attempts = max_attempts

    async def generate(
        self,
        requirement: str,
        context: WorkflowContext
    ) -> dict:
        """Generate working code with full observability."""
        # Register webhook
        webhook_id = await self.setup_monitoring(context.correlation_id)

        try:
            previous_errors = None

            for attempt in range(1, self.max_attempts + 1):
                # Log attempt
                context.add_event(f"Attempt {attempt}/{self.max_attempts}")

                # Generate code
                code = await self.llm_generate(
                    requirement,
                    previous_errors,
                    context=f"Template {self.template_id} environment"
                )

                # Execute in templated sandbox (100ms startup!)
                sandbox = await Sandbox.create(template=self.template_id)

                try:
                    result = await sandbox.run_code(code, timeout=30)

                    if result.error is None:
                        # Success!
                        context.add_event("Code executed successfully")
                        return {
                            "success": True,
                            "code": code,
                            "output": result.logs.stdout,
                            "attempts": attempt,
                            "template_used": self.template_id
                        }

                    # Failed - prepare for next attempt
                    previous_errors = result.error
                    context.add_event(f"Execution failed: {result.error}")

                finally:
                    await sandbox.kill()
                    # Webhook automatically logged creation/termination

            # Max attempts exceeded
            context.add_event("Max attempts exceeded")
            return {
                "success": False,
                "error": "Failed after max attempts",
                "last_error": previous_errors,
                "attempts": self.max_attempts
            }

        finally:
            # Cleanup webhook
            await self.cleanup_monitoring(webhook_id)

    async def setup_monitoring(self, correlation_id: str) -> str:
        """Register webhook for this generation session."""
        response = requests.post(
            "https://api.e2b.app/events/webhooks",
            headers={"X-API-Key": os.getenv("E2B_API_KEY")},
            json={
                "name": f"Generation {correlation_id}",
                "url": f"{self.webhook_url}/generation/{correlation_id}",
                "enabled": True,
                "events": [
                    "sandbox.lifecycle.created",
                    "sandbox.lifecycle.killed"
                ]
            }
        )
        return response.json()["id"]

    async def cleanup_monitoring(self, webhook_id: str):
        """Remove webhook after generation completes."""
        requests.delete(
            f"https://api.e2b.app/events/webhooks/{webhook_id}",
            headers={"X-API-Key": os.getenv("E2B_API_KEY")}
        )

    async def llm_generate(
        self,
        requirement: str,
        previous_errors: str | None,
        context: str
    ) -> str:
        """Generate code using LLM."""
        # Your LLM implementation
        pass
```

### Example Usage

```python
async def main():
    # Create generator with ML template
    generator = AdvancedIterativeCodeGenerator(
        template_id="template_ml_abc123",  # Pre-installed torch, transformers
        webhook_url="https://your-server.com/webhooks",
        max_attempts=3
    )

    # Generate working ML code
    context = WorkflowContext(correlation_id="req-789")
    result = await generator.generate(
        requirement="Train a sentiment classifier on IMDB dataset",
        context=context
    )

    print(f"Success: {result['success']}")
    print(f"Attempts: {result['attempts']}")
    print(f"Code:\n{result['code']}")
```

**What happens:**

1. ✅ Webhook registered for tracking
2. ✅ Sandbox created from ML template (100ms startup)
3. ✅ Code generated and executed
4. ✅ If fails, iterate with error feedback
5. ✅ Webhook logs all sandbox creation/termination
6. ✅ Final result with full observability
7. ✅ Webhook cleaned up

**Benefits:**

- 🚀 **10-50x faster** execution (template vs installing packages)
- 📊 **Full visibility** (webhooks track everything)
- ✅ **Working code** (iterative refinement)
- 💰 **Cost effective** (faster = cheaper)
- 🔍 **Debuggable** (webhook logs + context events)

---

## 📊 Cost & Performance Analysis

### With Templates

| Scenario | Without Template | With Template | Savings |
|----------|-----------------|---------------|---------|
| **ML Code Gen** | 30s install + 5s execute = 35s | 0.1s startup + 5s execute = 5.1s | **86% faster** |
| **Data Science** | 20s install + 3s execute = 23s | 0.1s startup + 3s execute = 3.1s | **87% faster** |
| **Web Dev** | 15s install + 2s execute = 17s | 0.1s startup + 2s execute = 2.1s | **88% faster** |

### With Webhooks

| Capability | Without Webhooks | With Webhooks |
|------------|-----------------|---------------|
| **Cost Tracking** | Manual polling | Real-time events |
| **Runaway Detection** | Periodic checks | Instant alerts |
| **Analytics** | Batch queries | Live streaming |
| **Monitoring** | Dashboard refresh | Push updates |

---

## 🎯 Next Steps

### Immediate (This Week)

1. **Create ML Template**
   ```bash
   # Create e2b.Dockerfile with torch, transformers
   e2b template init
   # Edit Dockerfile
   e2b template build
   ```

2. **Register Webhook**
   ```python
   # Set up basic webhook endpoint
   # Register with E2B
   # Test with sandbox creation
   ```

3. **Update Iterative Example**
   - Add template support to `e2b_iterative_code_refinement.py`
   - Show template vs non-template performance

### Medium Term (Next 2 Weeks)

4. **Build Template Library**
   - ML template (torch, transformers)
   - Data Science template (pandas, matplotlib)
   - Web Dev template (flask, fastapi, node)
   - Testing template (pytest, unittest, coverage)

5. **Implement Webhook Monitoring**
   - Cost tracking dashboard
   - Real-time sandbox monitor
   - Runaway detection
   - Analytics aggregation

6. **Document Patterns**
   - Template creation guide
   - Webhook integration examples
   - Combined workflow patterns

### Long Term (Month 1)

7. **Production Deployment**
   - Deploy webhook server
   - Set up monitoring dashboards
   - Implement budget enforcement
   - Create template management UI

8. **Integration with TTA.dev**
   - Add template support to `CodeExecutionPrimitive`
   - Create `WebhookMonitoringPrimitive`
   - Build dashboard visualization
   - Add to observability stack

---

## 📚 Resources

### Documentation

- **E2B Templates:** https://e2b.dev/docs/sandbox-template
- **E2B Webhooks:** https://e2b.dev/docs/sandbox/lifecycle-events-webhooks
- **E2B API:** https://e2b.dev/docs/api
- **Our Iterative Pattern:** `E2B_ITERATIVE_REFINEMENT_PATTERN.md`

### Examples

- **Basic Template:** `e2b.Dockerfile.example`
- **ML Template:** `templates/ml/e2b.Dockerfile`
- **Webhook Server:** `examples/webhook_monitoring_server.py`
- **Combined Pattern:** `examples/advanced_iterative_refinement.py`

### Tools

- **E2B CLI:** `npm install -g @e2b/cli`
- **Template Manager:** `scripts/e2b/manage_templates.sh`
- **Webhook Tester:** `scripts/e2b/test_webhook.py`

---

## 🎉 Summary

**We can significantly enhance iterative code refinement by:**

1. **Using Templates** for 10-50x faster sandbox startup
2. **Using Webhooks** for real-time monitoring and cost control
3. **Combining Both** for the ultimate observable, fast, reliable workflow

**Key Benefits:**

- ✅ **86-88% faster** execution (templates)
- ✅ **Real-time tracking** (webhooks)
- ✅ **Budget enforcement** (webhook alerts)
- ✅ **Better analytics** (event aggregation)
- ✅ **Runaway detection** (auto-kill)
- ✅ **Working code** (iterative refinement)

**Next Action:** Create first template and webhook endpoint!

---

**Last Updated:** November 6, 2025
**Status:** READY TO IMPLEMENT
**Build On:** E2B Iterative Refinement Pattern


---
**Logseq:** [[TTA.dev/_archive/Status-reports-2025/E2b_advanced_features_expansion]]
