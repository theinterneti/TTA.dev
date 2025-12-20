#!/usr/bin/env python3
"""
Production TTA.dev API Server with Real AI Integration
Includes: Gemini LLM, TTA.dev Primitives (Cache, Retry, Fallback)
"""

import os
import sys
import time
import asyncio
import uuid
from typing import Any
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Import uvicorn
try:
    import uvicorn
except ImportError:
    print("❌ Error: uvicorn not installed. Run: uv pip install uvicorn")
    sys.exit(1)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Loaded environment variables from: {env_path}")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: uv pip install python-dotenv")
    print("⚠️  Falling back to system environment variables")

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../packages/tta-dev-primitives/src"))

# Import TTA.dev primitives
try:
    from tta_dev_primitives import WorkflowContext, WorkflowPrimitive
    from tta_dev_primitives.recovery import RetryPrimitive, RetryStrategy
    from tta_dev_primitives.performance import CachePrimitive
    TTA_PRIMITIVES_AVAILABLE = True
    print("✅ TTA.dev primitives loaded")
except ImportError as e:
    print(f"⚠️ TTA primitives not available: {e}")
    TTA_PRIMITIVES_AVAILABLE = False

# Import Gemini SDK
try:
    import google.generativeai as genai
    from tta_secrets import get_gemini_api_key

    try:
        api_key = get_gemini_api_key()
        genai.configure(api_key=api_key)
        GEMINI_AVAILABLE = True
        print("✅ Gemini API key found")
    except ValueError:
        print("⚠️ GEMINI_API_KEY not set - using mock mode")
        GEMINI_AVAILABLE = False
except ImportError:
    print("⚠️ google-generativeai not installed - using mock mode")
    GEMINI_AVAILABLE = False

# Primitive classes
if TTA_PRIMITIVES_AVAILABLE:
    class GeminiLLMPrimitive(WorkflowPrimitive):
        """Gemini LLM primitive that uses google-generativeai SDK directly."""

        def __init__(self, model_name: str = "gemini-2.5-flash"):
            """Initialize with Gemini model."""
            super().__init__()
            self.model_name = model_name

            if GEMINI_AVAILABLE:
                self.model = genai.GenerativeModel(model_name)
            else:
                self.model = None

        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            """Execute LLM generation."""
            if not GEMINI_AVAILABLE or not self.model:
                raise Exception("Gemini API not available")

            prompt = input_data.get("prompt", "")
            temperature = input_data.get("temperature", 0.7)
            max_tokens = input_data.get("max_tokens", 2048)

            try:
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    prompt,
                    generation_config={
                        "temperature": temperature,
                        "max_output_tokens": max_tokens
                    }
                )

                text = response.text if hasattr(response, 'text') else str(response)

                # Estimate tokens and cost
                prompt_tokens = len(prompt.split()) * 1.3
                completion_tokens = len(text.split()) * 1.3
                total_tokens = int(prompt_tokens + completion_tokens)

                cost_per_1m_input = 0.15
                cost_per_1m_output = 0.60
                estimated_cost = (
                    (prompt_tokens / 1_000_000 * cost_per_1m_input) +
                    (completion_tokens / 1_000_000 * cost_per_1m_output)
                )

                return {
                    "response": text,
                    "model_used": self.model_name,
                    "tokens_used": total_tokens,
                    "estimated_cost_usd": round(estimated_cost, 6)
                }

            except Exception as e:
                raise Exception(f"Gemini API error: {str(e)}")

    class MockLLMPrimitive(WorkflowPrimitive):
        """Mock LLM for when Gemini is not available."""

        async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
            """Return mock response."""
            prompt = input_data.get("prompt", "")
            return {
                "response": f"[MOCK] Analysis of: {prompt[:100]}... This is a simulated response for testing purposes.",
                "model_used": "mock-llm",
                "tokens_used": 50,
                "estimated_cost_usd": 0.0
            }

else:
    # Fallback classes when primitives not available
    class WorkflowContext:
        def __init__(self, correlation_id=None, data=None):
            self.correlation_id = correlation_id or str(uuid.uuid4())
            self.data = data or {}

    class WorkflowPrimitive:
        def __init__(self):
            pass
        async def execute(self, input_data: dict, context: Any) -> dict:
            return {"response": "TTA primitives not available", "model_used": "none"}

    class GeminiLLMPrimitive(WorkflowPrimitive):
        def __init__(self, model_name: str = "gemini-2.5-flash"):
            super().__init__()
            self.model_name = model_name

    class MockLLMPrimitive(WorkflowPrimitive):
        async def execute(self, input_data: dict, context: Any) -> dict:
            return {"response": "Mock response", "model_used": "mock"}

# Initialize FastAPI app
app = FastAPI(
    title="TTA.dev API - Production Ready",
    description="Real AI analysis with TTA.dev workflow primitives",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class AnalyzeRequest(BaseModel):
    prompt: str = Field(..., description="Analysis prompt or question")
    context: dict[str, Any] = Field(default_factory=dict, description="Additional context data")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Creativity level")

class AnalyzeResponse(BaseModel):
    success: bool
    response: str | None = None
    error: str | None = None
    execution_time_ms: float
    cache_hit: bool = False
    model_used: str
    correlation_id: str
    tokens_used: int = 0
    estimated_cost_usd: float = 0.0

class HealthResponse(BaseModel):
    status: str
    gemini_available: bool
    primitives_loaded: bool
    version: str

# Initialize workflow primitives
print("🔧 Applying TTA.dev primitives...")

# Choose LLM based on availability
if GEMINI_AVAILABLE:
    llm_primitive = GeminiLLMPrimitive()
    print("✅ Using real Gemini LLM")
else:
    llm_primitive = MockLLMPrimitive()
    print("⚠️ Using mock LLM")

if TTA_PRIMITIVES_AVAILABLE:
    # Layer 1: Cache
    cached_llm = CachePrimitive(
        primitive=llm_primitive,
        cache_key_fn=lambda data, ctx: f"{data.get('prompt', '')}:{data.get('temperature', 0.7)}",
        ttl_seconds=3600.0  # 1 hour
    )
    print("  ✅ CachePrimitive (1 hour TTL)")

    # Layer 2: Retry
    resilient_llm = RetryPrimitive(
        primitive=cached_llm,
        strategy=RetryStrategy(
            max_retries=3,
            backoff_base=2.0,
            jitter=True
        )
    )
    print("  ✅ RetryPrimitive (3 retries, exponential backoff)")

    workflow_primitive = resilient_llm
else:
    workflow_primitive = llm_primitive

print("✅ Production primitives active")

# API Endpoints
@app.get("/", response_model=dict)
async def root():
    """Root endpoint - API information"""
    return {
        "service": "TTA.dev API Server",
        "version": "2.0.0",
        "status": "production-ready",
        "gemini_available": GEMINI_AVAILABLE,
        "primitives_loaded": TTA_PRIMITIVES_AVAILABLE,
        "features": [
            "Real Gemini AI Analysis",
            "TTA.dev Workflow Primitives",
            "LRU Cache (1 hour TTL)",
            "Exponential Backoff Retry",
            "Cost Tracking & Token Estimation",
            "Structured Error Responses"
        ],
        "endpoints": {
            "health": "/health",
            "analyze": "/api/v1/analyze",
            "github": "/api/v1/github/analyze"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        gemini_available=GEMINI_AVAILABLE,
        primitives_loaded=TTA_PRIMITIVES_AVAILABLE,
        version="2.0.0"
    )

@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """Analyze text using Gemini with TTA.dev primitives"""
    start_time = time.time()

    # Create workflow context
    context = WorkflowContext(
        correlation_id=str(uuid.uuid4()),
        data=request.context
    )

    try:
        # Execute workflow
        result = await workflow_primitive.execute(
            {
                "prompt": request.prompt,
                "temperature": request.temperature
            },
            context
        )

        execution_time = (time.time() - start_time) * 1000

        return AnalyzeResponse(
            success=True,
            response=result.get("response"),
            execution_time_ms=execution_time,
            model_used=result.get("model_used", "unknown"),
            correlation_id=context.correlation_id,
            tokens_used=result.get("tokens_used", 0),
            estimated_cost_usd=result.get("estimated_cost_usd", 0.0)
        )

    except Exception as e:
        execution_time = (time.time() - start_time) * 1000

        return AnalyzeResponse(
            success=False,
            error=str(e),
            execution_time_ms=execution_time,
            model_used="error",
            correlation_id=context.correlation_id
        )

@app.post("/api/v1/github/analyze")
async def analyze_github_repo(request: dict):
    """Analyze GitHub repository data"""
    # For n8n workflow compatibility
    prompt = f"""
    Analyze this GitHub repository:

    Name: {request.get('name', 'Unknown')}
    Description: {request.get('description', 'No description')}
    Language: {request.get('language', 'Unknown')}
    Stars: {request.get('stargazers_count', 0)}
    Forks: {request.get('forks_count', 0)}
    Issues: {request.get('open_issues_count', 0)}

    Provide a brief analysis of the repository's health and activity.
    """

    analyze_request = AnalyzeRequest(prompt=prompt)
    return await analyze_text(analyze_request)

# Startup message
print("\n" + "=" * 60)
print("🚀 TTA.dev API Server - Production Ready")
print("=" * 60)
print(f"Gemini: {'✅ ENABLED' if GEMINI_AVAILABLE else '❌ DISABLED'}")
print(f"Primitives: {'✅ ACTIVE' if TTA_PRIMITIVES_AVAILABLE else '❌ INACTIVE'}")
print("=" * 60)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    )
