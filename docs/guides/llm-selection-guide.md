# LLM Selection Guide

**For AI Agents & Developers:** Use this guide to choose between OpenAI, Anthropic, and Ollama primitives

---

## 🎯 Quick Decision Matrix

| Priority | Best Choice | Why |
|----------|-------------|-----|
| **Quality** | OpenAIPrimitive (GPT-4) | Best reasoning, most capable |
| **Cost** | OllamaPrimitive | 100% free, runs locally |
| **Privacy** | OllamaPrimitive | Data never leaves your machine |
| **Speed** | OpenAIPrimitive (GPT-4o-mini) | Fastest API response |
| **Long Context** | AnthropicPrimitive (Claude) | 200K+ token context window |
| **Safety** | AnthropicPrimitive (Claude) | Best at refusing harmful requests |
| **Simplicity** | OpenAIPrimitive | Easiest to get started |

---

## 📊 Detailed Comparison

| Feature | OpenAI | Anthropic | Ollama |
|---------|--------|-----------|--------|
| **Best Model** | GPT-4o | Claude 3.5 Sonnet | Llama 3.2 |
| **Cost (1M tokens)** | $2.50-$15 | $3-$15 | $0 (free) |
| **Free Tier** | $5 credit | ❌ No | ✅ Unlimited |
| **Setup Difficulty** | ⭐ Easy | ⭐ Easy | ⭐⭐⭐ Medium |
| **API Latency** | ~1-2s | ~1-2s | ~5-10s (local) |
| **Context Window** | 128K tokens | 200K tokens | 128K tokens |
| **Privacy** | ⚠️ Cloud | ⚠️ Cloud | ✅ 100% local |
| **Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Deployment** | ✅ Easy | ✅ Easy | ⚠️ Need GPU |

---

## 🟢 Use OpenAIPrimitive When...

### ✅ Perfect For

1. **Production applications**
   - Reliable uptime (99.9%)
   - Fast response times
   - Proven at scale

2. **Quick prototyping**
   - $5 free credit to start
   - Simple API
   - Great documentation

3. **Cost-sensitive projects**
   - GPT-4o-mini: $0.15/1M input tokens
   - Cheapest high-quality option
   - Good for high-volume use

4. **General-purpose AI**
   - Code generation
   - Text summarization
   - Q&A systems

### ⚠️ Avoid When

- You need 100% data privacy
- You're processing sensitive data (medical, legal)
- You want to avoid vendor lock-in

---

## 🔵 Use AnthropicPrimitive When...

### ✅ Perfect For

1. **Long-context tasks**
   - Document analysis (200K+ tokens)
   - Large codebase understanding
   - Book summarization

2. **Safety-critical applications**
   - Content moderation
   - Customer support
   - Educational tools

3. **Complex reasoning**
   - Multi-step problem solving
   - Research assistance
   - Technical writing

4. **Extended thinking**
   - Deep analysis
   - Architecture decisions
   - Strategic planning

### ⚠️ Avoid When

- You need the absolute cheapest option
- You're just prototyping (no free tier)
- Speed is more important than quality

---

## 🟣 Use OllamaPrimitive When...

### ✅ Perfect For

1. **Privacy-critical applications**
   - Medical records
   - Legal documents
   - Personal data

2. **Offline/air-gapped systems**
   - No internet required
   - Works on planes, remote locations
   - Government/military use

3. **Cost-free development**
   - Unlimited testing
   - No API costs
   - Learn without spending

4. **Custom fine-tuning**
   - Train on proprietary data
   - Domain-specific models
   - Full control

### ⚠️ Avoid When

- You don't have a GPU (slow on CPU)
- You need the absolute best quality
- You want zero setup complexity

---

## 💻 Code Examples

### OpenAIPrimitive - Quick Start

```python
"""Simple chatbot using OpenAIPrimitive"""

from tta_dev_primitives.integrations import OpenAIPrimitive, OpenAIRequest
from tta_dev_primitives.core.base import WorkflowContext
import asyncio
import os

async def main():
    # Create primitive (uses GPT-4o-mini by default)
    llm = OpenAIPrimitive(api_key=os.getenv("OPENAI_API_KEY"))
    context = WorkflowContext(workflow_id="chatbot")

    # Send message
    request = OpenAIRequest(
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain async/await in Python"}
        ],
        temperature=0.7
    )

    response = await llm.execute(request, context)
    print(f"Assistant: {response.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Cost:** ~$0.0001 per request (GPT-4o-mini)
**Speed:** ~1-2 seconds
**Quality:** ⭐⭐⭐⭐⭐

---

### AnthropicPrimitive - Long Context

```python
"""Document analysis using AnthropicPrimitive"""

from tta_dev_primitives.integrations import AnthropicPrimitive, AnthropicRequest
from tta_dev_primitives.core.base import WorkflowContext
import asyncio
import os

async def main():
    # Create primitive (uses Claude 3.5 Sonnet)
    llm = AnthropicPrimitive(api_key=os.getenv("ANTHROPIC_API_KEY"))
    context = WorkflowContext(workflow_id="doc-analysis")

    # Analyze long document (up to 200K tokens)
    with open("long_document.txt") as f:
        document = f.read()

    request = AnthropicRequest(
        messages=[
            {"role": "user", "content": f"Summarize this document:\n\n{document}"}
        ],
        system="You are a technical document analyst.",
        max_tokens=1000
    )

    response = await llm.execute(request, context)
    print(f"Summary: {response.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Cost:** ~$0.003 per request (Claude 3.5 Sonnet)
**Speed:** ~2-3 seconds
**Quality:** ⭐⭐⭐⭐⭐
**Context:** Up to 200K tokens

---

### OllamaPrimitive - Local & Private

```python
"""Private chatbot using OllamaPrimitive"""

from tta_dev_primitives.integrations import OllamaPrimitive, OllamaRequest
from tta_dev_primitives.core.base import WorkflowContext
import asyncio

async def main():
    # Create primitive (runs locally, no API key needed)
    llm = OllamaPrimitive(model="llama3.2")
    context = WorkflowContext(workflow_id="private-chat")

    # Send message (data never leaves your machine)
    request = OllamaRequest(
        messages=[
            {"role": "user", "content": "Explain quantum computing"}
        ],
        temperature=0.7
    )

    response = await llm.execute(request, context)
    print(f"Assistant: {response.content}")

if __name__ == "__main__":
    asyncio.run(main())
```

**Cost:** $0 (free)
**Speed:** ~5-10 seconds (depends on GPU)
**Quality:** ⭐⭐⭐⭐
**Privacy:** ✅ 100% local

---

## 💰 Cost Breakdown (1M Tokens)

### Input Tokens

| Model | Cost |
|-------|------|
| GPT-4o-mini | $0.15 |
| GPT-4o | $2.50 |
| GPT-4 Turbo | $10.00 |
| Claude 3.5 Sonnet | $3.00 |
| Claude 3 Opus | $15.00 |
| Ollama (any model) | $0.00 |

### Output Tokens

| Model | Cost |
|-------|------|
| GPT-4o-mini | $0.60 |
| GPT-4o | $10.00 |
| GPT-4 Turbo | $30.00 |
| Claude 3.5 Sonnet | $15.00 |
| Claude 3 Opus | $75.00 |
| Ollama (any model) | $0.00 |

**Example:** 1000 requests with 500 input + 500 output tokens each:
- **GPT-4o-mini:** $0.38
- **Claude 3.5 Sonnet:** $9.00
- **Ollama:** $0.00

---

## 🚀 Recommended Workflow

### Development Phase
```python
# Use Ollama for free unlimited testing
llm = OllamaPrimitive(model="llama3.2")
```

### Production Phase
```python
# Use OpenAI for cost-effective production
llm = OpenAIPrimitive(model="gpt-4o-mini")
```

### High-Quality Phase
```python
# Use Claude for complex reasoning
llm = AnthropicPrimitive(model="claude-3-5-sonnet-20241022")
```

---

## 🔄 Multi-LLM Strategy

Use RouterPrimitive to combine multiple LLMs:

```python
from tta_dev_primitives import RouterPrimitive
from tta_dev_primitives.integrations import (
    OpenAIPrimitive,
    AnthropicPrimitive,
    OllamaPrimitive
)

# Create router with fallback strategy
router = RouterPrimitive(
    routes={
        "fast": OpenAIPrimitive(model="gpt-4o-mini"),  # Default
        "quality": AnthropicPrimitive(),  # For complex tasks
        "free": OllamaPrimitive()  # For development
    },
    default_route="fast"
)

# Route based on task complexity
def select_route(task):
    if task.complexity == "high":
        return "quality"
    elif task.is_development:
        return "free"
    return "fast"
```

---

## 📚 Related Documentation

### Cost Optimization
- **💰 LLM Cost Guide:** [llm-cost-guide.md](llm-cost-guide.md) - Free vs paid model comparison, cost analysis
- **🎯 Cost Optimization Patterns:** [cost-optimization-patterns.md](cost-optimization-patterns.md) - Production patterns for reducing LLM costs (30-70% savings)

### Implementation
- **OpenAIPrimitive API:** [`platform/primitives/src/tta_dev_primitives/integrations/openai_primitive.py`](../../platform/primitives/src/tta_dev_primitives/integrations/openai_primitive.py)
- **AnthropicPrimitive API:** [`platform/primitives/src/tta_dev_primitives/integrations/anthropic_primitive.py`](../../platform/primitives/src/tta_dev_primitives/integrations/anthropic_primitive.py)
- **OllamaPrimitive API:** [`platform/primitives/src/tta_dev_primitives/integrations/ollama_primitive.py`](../../platform/primitives/src/tta_dev_primitives/integrations/ollama_primitive.py)
- **RouterPrimitive:** [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md#routerprimitive)
- **CachePrimitive:** [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md#cacheprimitive)
- **FallbackPrimitive:** [`PRIMITIVES_CATALOG.md`](../../PRIMITIVES_CATALOG.md#fallbackprimitive)

---

**Last Updated:** October 30, 2025
**For:** AI Agents & Developers (all skill levels)
**Maintained by:** TTA.dev Team


---
**Logseq:** [[TTA.dev/Docs/Guides/Llm-selection-guide]]
