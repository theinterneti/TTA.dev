# TTA.dev API Integration Guide

**Use TTA.dev primitives from n8n workflows via REST API**

---

## 🎯 Overview

This guide shows you how to use your TTA.dev workflow primitives (RetryPrimitive, CachePrimitive, etc.) from n8n workflows via a simple REST API.

### Benefits

✅ **Use Your Own Code** - Leverage TTA.dev primitives you already built
✅ **Production-Ready** - Built-in retry, caching, observability
✅ **No LangChain Issues** - Direct API calls, no n8n node dependencies
✅ **Full Control** - Customize behavior, add new endpoints easily
✅ **Type-Safe** - FastAPI with Pydantic validation

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Start the API Server

```bash
cd /home/thein/repos/TTA.dev

# Start the TTA.dev API server
./scripts/api/start_tta_api.sh
```

**Expected output:**
```
╔════════════════════════════════════════════════════════════════╗
║                     TTA.dev API Server                         ║
╚════════════════════════════════════════════════════════════════╝

🚀 Starting server on http://localhost:8000

📚 API Documentation: http://localhost:8000/docs
🔍 Health Check: http://localhost:8000/health
```

### Step 2: Test the API

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "gemini_available": false,
  "primitives_loaded": true,
  "version": "1.0.0"
}
```

### Step 3: Import n8n Workflow

```bash
# Import the workflow
curl -X POST http://localhost:5678/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @workflows/n8n_tta_api_github_health.json
```

### Step 4: Execute Workflow in n8n

1. Open n8n: http://localhost:5678
2. Find workflow: "GitHub Health Dashboard - TTA.dev API"
3. Click "Execute Workflow"
4. View results!

---

## 📋 API Endpoints

### GET /health

Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "gemini_available": true,
  "primitives_loaded": true,
  "version": "1.0.0"
}
```

### POST /api/v1/analyze

Analyze text or data using TTA.dev primitives

**Request:**
```json
{
  "prompt": "Analyze this GitHub repository...",
  "context": {
    "repo": "theinterneti/TTA.dev",
    "type": "github_health"
  },
  "model": "gemini-1.5-flash",
  "temperature": 0.7,
  "use_cache": true,
  "max_retries": 3
}
```

**Response:**
```json
{
  "success": true,
  "response": "Analysis result here...",
  "execution_time_ms": 1234.5,
  "cache_hit": false,
  "model_used": "gemini-1.5-flash",
  "correlation_id": "abc-123-def-456"
}
```

### GET /api/v1/primitives

List available TTA.dev primitives

**Response:**
```json
{
  "primitives": [
    {
      "name": "RetryPrimitive",
      "description": "Automatic retry with exponential backoff",
      "status": "active"
    },
    {
      "name": "CachePrimitive",
      "description": "LRU cache with TTL",
      "status": "active"
    }
  ]
}
```

---

## 🔧 Configuration

### Environment Variables

```bash
# API server port (default: 8000)
export TTA_API_PORT=8000

# Gemini API key (optional, for production)
export GEMINI_API_KEY=your-api-key-here

# OpenRouter API key (alternative)
export OPENROUTER_API_KEY=your-api-key-here
```

### Production Setup

For production use, update `scripts/api/tta_api_server.py`:

1. **Add real LLM integration:**
   - Uncomment Gemini provider import
   - Or add OpenRouter integration
   - Replace `SimpleLLMPrimitive` with real implementation

2. **Update CORS settings:**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-n8n-domain.com"],  # Restrict origins
       allow_credentials=True,
       allow_methods=["POST", "GET"],
       allow_headers=["Content-Type"],
   )
   ```

3. **Add authentication:**
   ```python
   from fastapi.security import HTTPBearer

   security = HTTPBearer()

   @app.post("/api/v1/analyze")
   async def analyze(
       request: AnalyzeRequest,
       credentials: HTTPAuthorizationCredentials = Depends(security)
   ):
       # Verify API key
       if credentials.credentials != os.getenv("TTA_API_KEY"):
           raise HTTPException(status_code=401, detail="Invalid API key")
       ...
   ```

---

## 🔗 n8n Workflow Structure

The imported workflow follows this pattern:

```
Manual Trigger
    ↓
Check TTA.dev API Health (/health)
    ↓
IF API Healthy?
    ├─ YES → Set Repository Data
    │           ↓
    │       Get GitHub Stats (api.github.com)
    │           ↓
    │       Format Analysis Prompt
    │           ↓
    │       Call TTA.dev API (/api/v1/analyze)
    │           ↓
    │       Format Result
    │
    └─ NO → Show Error (API not running)
```

**Key Features:**

- ✅ Health check before execution
- ✅ Clear error handling
- ✅ Fetches real GitHub data
- ✅ Calls TTA.dev API with primitives
- ✅ Shows execution metrics (time, cache hit, correlation ID)

---

## 🎨 Customization Examples

### Example 1: Add OpenRouter Integration

Update `tta_api_server.py`:

```python
import os
import httpx

class OpenRouterPrimitive:
    """OpenRouter LLM integration"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """Call OpenRouter API"""
        import time
        start = time.time()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "http://localhost:8000",
                },
                json={
                    "model": input_data.get("model", "google/gemini-flash-1.5"),
                    "messages": [
                        {"role": "user", "content": input_data["prompt"]}
                    ],
                    "temperature": input_data.get("temperature", 0.7),
                }
            )
            response.raise_for_status()
            data = response.json()

            execution_time = (time.time() - start) * 1000

            return {
                "response": data["choices"][0]["message"]["content"],
                "execution_time_ms": execution_time,
                "model": input_data.get("model"),
            }

# Replace SimpleLLMPrimitive with OpenRouterPrimitive
llm_primitive = OpenRouterPrimitive()
```

### Example 2: Add New Endpoint for Slack Integration

```python
@app.post("/api/v1/slack/analyze")
async def slack_analysis(
    text: str,
    channel: str,
    user_id: str,
):
    """Analyze Slack message and respond"""

    context = WorkflowContext(
        correlation_id=f"slack-{channel}-{int(time.time())}",
        data={"channel": channel, "user": user_id}
    )

    input_data = {
        "prompt": f"Analyze this message: {text}",
        "model": "gemini-1.5-flash",
        "temperature": 0.7,
    }

    result = await resilient_llm.execute(input_data, context)

    return {
        "response_type": "in_channel",
        "text": result["response"],
    }
```

### Example 3: Add Workflow Orchestration Endpoint

```python
from tta_dev_primitives import SequentialPrimitive, ParallelPrimitive

@app.post("/api/v1/workflow/orchestrate")
async def orchestrate_workflow(
    workflow_type: str,
    input_data: dict,
):
    """Execute multi-step workflow"""

    if workflow_type == "github_analysis":
        # Create workflow with primitives
        workflow = (
            fetch_github_data >>
            (analyze_code | analyze_issues | analyze_prs) >>  # Parallel
            aggregate_results >>
            generate_summary
        )

        context = WorkflowContext(correlation_id=str(uuid.uuid4()))
        result = await workflow.execute(input_data, context)

        return result

    raise HTTPException(status_code=400, detail="Unknown workflow type")
```

---

## 📊 Benefits vs. LangChain Nodes

| Feature | TTA.dev API | n8n LangChain Nodes |
|---------|-------------|---------------------|
| **Installation** | ✅ Just start server | ❌ Node version issues |
| **Retry Logic** | ✅ Built-in RetryPrimitive | ⚠️ Manual configuration |
| **Caching** | ✅ Built-in CachePrimitive | ❌ Not available |
| **Observability** | ✅ OpenTelemetry integration | ⚠️ Limited |
| **Customization** | ✅ Full control of code | ❌ Limited to node config |
| **Error Handling** | ✅ Production-grade | ⚠️ Basic |
| **Multi-Model** | ✅ Easy to add providers | ⚠️ Fixed providers |
| **Testing** | ✅ Standard pytest tests | ⚠️ Manual UI testing |

---

## 🧪 Testing

### Test API Directly

```bash
# Test analysis endpoint
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the meaning of life?",
    "model": "gemini-1.5-flash",
    "temperature": 0.7,
    "use_cache": true
  }'
```

### Test from n8n

1. Open workflow in n8n
2. Click "Execute Workflow"
3. Check each node's output
4. Verify:
   - Health check passes
   - GitHub data fetched
   - TTA.dev API called successfully
   - Response formatted correctly

### Load Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test API performance
ab -n 100 -c 10 \
  -p test_request.json \
  -T application/json \
  http://localhost:8000/api/v1/analyze
```

---

## 🐛 Troubleshooting

### Issue: API Server Won't Start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
uv pip install fastapi uvicorn pydantic
```

---

### Issue: n8n Can't Connect to API

**Error:** `Connection refused` or `ECONNREFUSED`

**Solutions:**

1. **Verify API is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check API server logs:**
   ```bash
   # Look for startup messages
   ```

3. **Verify port 8000 is available:**
   ```bash
   lsof -i :8000
   ```

---

### Issue: Cache Not Working

**Symptom:** `cache_hit: false` every time

**Solution:** Check that `use_cache: true` in request and verify CachePrimitive is initialized.

---

### Issue: Slow Response Times

**Possible Causes:**

1. **No caching enabled** → Set `use_cache: true`
2. **Mock LLM delay** → Replace with real Gemini/OpenRouter
3. **Network issues** → Check connectivity

**Solution:**
```bash
# Monitor API performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

---

## 📈 Production Deployment

### Option 1: Docker Container

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy TTA.dev packages
COPY packages/ ./packages/
COPY scripts/api/ ./scripts/api/

# Install dependencies
RUN pip install fastapi uvicorn pydantic

# Expose port
EXPOSE 8000

# Start server
CMD ["python", "scripts/api/tta_api_server.py"]
```

Build and run:
```bash
docker build -t tta-api .
docker run -p 8000:8000 -e GEMINI_API_KEY=$GEMINI_API_KEY tta-api
```

### Option 2: systemd Service

Create `/etc/systemd/system/tta-api.service`:

```ini
[Unit]
Description=TTA.dev API Server
After=network.target

[Service]
Type=simple
User=thein
WorkingDirectory=/home/thein/repos/TTA.dev
Environment="PYTHONPATH=/home/thein/repos/TTA.dev/packages/tta-dev-primitives/src"
ExecStart=/usr/local/bin/uv run python scripts/api/tta_api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable tta-api
sudo systemctl start tta-api
sudo systemctl status tta-api
```

---

## 🔗 Related Documentation

- **TTA.dev Primitives:** `packages/tta-dev-primitives/README.md`
- **n8n Integration:** `N8N_LANGCHAIN_INTEGRATION_GUIDE.md`
- **Workflow Examples:** `workflows/`

---

## 💡 Next Steps

1. **Start the API server:** `./scripts/api/start_tta_api.sh`
2. **Import workflow to n8n**
3. **Execute and test**
4. **Add real LLM integration** (Gemini or OpenRouter)
5. **Customize for your use case**
6. **Deploy to production**

---

**Created:** November 9, 2025
**Status:** ✅ Ready to use
**Version:** 1.0.0
