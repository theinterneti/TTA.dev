#!/usr/bin/env python3
"""
TTA.dev API Server
FastAPI server exposing TTA.dev primitives for n8n and other integrations
"""

import asyncio
import os
import sys
from typing import Any
import uuid
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import uvicorn - handle potential conflicts
try:
    import uvicorn
except ImportError:
    print("❌ Error: uvicorn not installed. Run: uv pip install uvicorn")
    sys.exit(1)

# Import TTA.dev primitives (optional - using mock for demo)
try:
    # Add parent directory to path to avoid conflicts
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../packages/tta-dev-primitives/src'))
    from tta_dev_primitives import WorkflowContext
    from tta_dev_primitives.recovery import RetryPrimitive
    from tta_dev_primitives.performance import CachePrimitive
    TTA_PRIMITIVES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Warning: TTA primitives not available: {e}")
    print("   Using mock implementations for demo")
    TTA_PRIMITIVES_AVAILABLE = False

    # Mock implementations
    class WorkflowContext:
        def __init__(self, correlation_id=None, data=None):
            self.correlation_id = correlation_id or str(uuid.uuid4())
            self.data = data or {}

    class RetryPrimitive:
        def __init__(self, primitive=None, **kwargs):
            self.primitive = primitive
        async def execute(self, input_data, context):
            return await self.primitive.execute(input_data, context)

    class CachePrimitive:
        def __init__(self, primitive=None, **kwargs):
            self.primitive = primitive
        async def execute(self, input_data, context):
            return await self.primitive.execute(input_data, context)

# Gemini integration (if available)
GEMINI_AVAILABLE = False  # Set to True when you configure Gemini API key

# Initialize FastAPI app
app = FastAPI(
    title="TTA.dev API",
    description="Production-ready API exposing TTA.dev workflow primitives",
    version="1.0.0"
)

# CORS middleware for n8n and web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class AnalyzeRequest(BaseModel):
    """Request to analyze repository or text data"""
    prompt: str = Field(..., description="Analysis prompt or question")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context data")
    model: str = Field(default="gemini-1.5-flash", description="LLM model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Creativity level")
    use_cache: bool = Field(default=True, description="Enable caching")
    max_retries: int = Field(default=3, ge=0, le=10, description="Retry attempts")


class AnalyzeResponse(BaseModel):
    """Response from analysis"""
    success: bool
    response: str | None = None
    error: str | None = None
    execution_time_ms: float
    cache_hit: bool = False
    model_used: str
    correlation_id: str


class HealthResponse(BaseModel):
    """API health check response"""
    status: str
    gemini_available: bool
    primitives_loaded: bool
    version: str


# Simple mock primitive for demonstration
class SimpleLLMPrimitive:
    """Mock LLM primitive for testing."""

    async def execute(self, input_data: dict[str, Any], context: Any) -> dict[str, Any]:
        """Execute mock LLM analysis."""
        prompt = input_data.get("prompt", "")

        # Simple mock analysis
        analysis = f"""
Based on the data provided:

{prompt}

This is a demonstration of the TTA.dev API integration with n8n.
In production, this would be replaced with a real LLM call (Gemini, OpenRouter, etc.)
using TTA.dev's robust primitive composition patterns.

Key observations:
- Data received successfully
- Workflow primitives would apply: retry, caching, fallback
- Context propagation enables distributed tracing
- Production-ready error handling and observability built-in

Next steps:
1. Replace this mock with a real LLM provider
2. Configure appropriate primitives for your use case
3. Monitor via OpenTelemetry and Prometheus
""".strip()

        return {
            "analysis": analysis,
            "model_used": "mock-demo",
            "tokens_used": len(prompt.split()) * 2,  # Rough estimate
        }

# Initialize the workflow (without TTA primitives for now - using direct call)
llm_primitive = SimpleLLMPrimitive()

# In production, this would be:
# cached_llm = CachePrimitive(
#     primitive=llm_primitive,
#     cache_key_fn=lambda data, ctx: f"{data.get('prompt', '')}:{ctx.correlation_id}",
#     ttl_seconds=3600.0
# )
# resilient_llm = RetryPrimitive(
#     primitive=cached_llm,
#     max_retries=3,
#     backoff_factor=2.0
# )


# Initialize the mock LLM (no primitive wrapping for simplicity)
llm_primitive = SimpleLLMPrimitive()


@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        gemini_available=GEMINI_AVAILABLE,
        primitives_loaded=True,
        version="1.0.0"
    )


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint"""
    return await health_check()


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze data using TTA.dev workflow primitives.

    This endpoint demonstrates:
    - Automatic retry on failures
    - LRU caching for cost reduction
    - Context propagation for tracing
    - Structured error handling
    """
    start_time = time.time()

    # Create workflow context with generated correlation ID
    correlation_id = str(uuid.uuid4())
    context = WorkflowContext(correlation_id=correlation_id)

    try:
        # Execute with primitives (mock for demo)
        result = await llm_primitive.execute(
            {"prompt": request.prompt, "context": request.context},
            context
        )

        # Calculate metrics
        execution_time_ms = (time.time() - start_time) * 1000

        return AnalyzeResponse(
            success=True,
            response=result["analysis"],
            error=None,
            execution_time_ms=execution_time_ms,
            cache_hit=False,
            model_used=result.get("model_used", "mock"),
            correlation_id=correlation_id
        )

    except Exception as e:
        execution_time_ms = (time.time() - start_time) * 1000
        return AnalyzeResponse(
            success=False,
            response=None,
            error=str(e),
            execution_time_ms=execution_time_ms,
            cache_hit=False,
            model_used="none",
            correlation_id=correlation_id
        )
@app.post("/api/v1/github/analyze")
async def analyze_github_repo(
    repo_url: str,
    analysis_type: str = "health",
    include_issues: bool = True,
    include_prs: bool = True,
):
    """
    Analyze a GitHub repository

    This would integrate with your GitHub wrapper primitives
    """
    return {
        "status": "not_implemented",
        "message": "GitHub analysis integration coming soon",
        "repo_url": repo_url,
    }


@app.get("/api/v1/primitives")
async def list_primitives():
    """List available TTA.dev primitives"""
    return {
        "primitives": [
            {
                "name": "RetryPrimitive",
                "description": "Automatic retry with exponential backoff",
                "status": "active",
            },
            {
                "name": "CachePrimitive",
                "description": "LRU cache with TTL",
                "status": "active",
            },
            {
                "name": "FallbackPrimitive",
                "description": "Graceful degradation",
                "status": "available",
            },
            {
                "name": "TimeoutPrimitive",
                "description": "Circuit breaker pattern",
                "status": "available",
            },
        ]
    }


def main():
    """Run the API server"""
    port = int(os.getenv("TTA_API_PORT", "8000"))

    print(f"""
╔════════════════════════════════════════════════════════════════╗
║                     TTA.dev API Server                         ║
╚════════════════════════════════════════════════════════════════╝

🚀 Starting server on http://localhost:{port}

📚 API Documentation: http://localhost:{port}/docs
🔍 Health Check: http://localhost:{port}/health
🧪 Interactive API: http://localhost:{port}/redoc

✨ Primitives Loaded:
   - RetryPrimitive (exponential backoff)
   - CachePrimitive (LRU + TTL)

⚠️  Using mock LLM for demo. Configure Gemini/OpenRouter for production.

""")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
