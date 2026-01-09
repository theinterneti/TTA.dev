---
title: OpenHands Decision Guide & Usage Recommendations
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/validation/openhands-decision-guide.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/OpenHands Decision Guide & Usage Recommendations]]

**Date:** 2025-10-25
**Purpose:** Quick reference for choosing optimal OpenHands configuration
**Audience:** TTA developers and integrators

---

## Quick Decision Matrix

### "I need to generate code quickly"

```
✅ Use: Mistral Small + Direct API
⏱️  Time: 1.6-5.0s
⭐ Quality: 4.7/5
💰 Cost: Free
📝 Example: Generate function, class, or module
```

### "I need the best quality code"

```
✅ Use: DeepSeek Chat + Direct API
⏱️  Time: 5.1-26.1s
⭐ Quality: 5.0/5
💰 Cost: Free
📝 Example: Complex functions, comprehensive tests
```

### "I need to create files"

```
✅ Use: Mistral Small + CLI Mode
⏱️  Time: 3.1s + CLI overhead
⭐ Quality: 4.7/5
💰 Cost: Free
📝 Example: Create test files, config files, scripts
```

### "I need to run bash commands"

```
✅ Use: Mistral Small + CLI Mode
⏱️  Time: 3.1s + execution time
⭐ Quality: 4.7/5
💰 Cost: Free
📝 Example: Run tests, build, deploy
```

### "I need complex reasoning"

```
✅ Use: DeepSeek R1 + Direct API
⏱️  Time: 7.8-50.6s
⭐ Quality: 5.0/5
💰 Cost: Free
📝 Example: Architecture decisions, analysis
```

### "I need a complete workflow"

```
✅ Use: Mistral Small + CLI Mode
⏱️  Time: 3.1s + workflow time
⭐ Quality: 4.7/5
💰 Cost: Free
📝 Example: Generate, create, test, build
```

---

## Task-Specific Recommendations

### Code Generation Tasks

#### Simple Functions (< 50 lines)
```
Model: Mistral Small
Access: Direct API
Time: 1.6s
Quality: 4/5
Cost: Free
Reason: Fast, sufficient quality
```

#### Moderate Functions (50-200 lines)
```
Model: Mistral Small
Access: Direct API
Time: 2.7s
Quality: 5/5
Cost: Free
Reason: Fast, excellent quality
```

#### Complex Functions (> 200 lines)
```
Model: DeepSeek Chat
Access: Direct API
Time: 19.7s
Quality: 5/5
Cost: Free
Reason: Best quality for complex code
```

### Test Generation Tasks

#### Unit Tests (< 10 tests)
```
Model: Mistral Small
Access: Direct API
Time: 5.0s
Quality: 5/5
Cost: Free
Reason: Fast, comprehensive tests
```

#### Integration Tests (> 10 tests)
```
Model: DeepSeek Chat
Access: CLI Mode
Time: 26.1s + file creation
Quality: 5/5
Cost: Free
Reason: Best quality, creates files
```

### File Creation Tasks

#### Single File
```
Model: Mistral Small
Access: CLI Mode
Time: 3.1s + CLI overhead
Quality: 4.7/5
Cost: Free
Reason: Fast, reliable
```

#### Multiple Files (> 5 files)
```
Model: Mistral Small
Access: CLI Mode
Time: 3.1s per file + CLI overhead
Quality: 4.7/5
Cost: Free
Reason: Reliable, can batch
```

### Build Automation Tasks

#### Makefile Generation
```
Model: Mistral Small
Access: CLI Mode
Time: 3.1s + file creation
Quality: 4.7/5
Cost: Free
Reason: Fast, creates files
```

#### CI/CD Configuration
```
Model: DeepSeek Chat
Access: CLI Mode
Time: 19.7s + file creation
Quality: 5/5
Cost: Free
Reason: Best quality for complex configs
```

### Documentation Tasks

#### API Documentation
```
Model: DeepSeek Chat
Access: Direct API
Time: 19.7s
Quality: 5/5
Cost: Free
Reason: Best quality, comprehensive
```

#### README Generation
```
Model: Mistral Small
Access: Direct API
Time: 2.7s
Quality: 4.7/5
Cost: Free
Reason: Fast, sufficient quality
```

---

## Performance Optimization Tips

### Tip 1: Use Model Rotation for Rate Limiting

```python
# If one model is rate limited, try another
models = [
    "mistralai/mistral-small-3.2-24b-instruct:free",  # Primary
    "meta-llama/llama-3.3-70b-instruct",              # Fallback
    "deepseek/deepseek-chat",                         # Fallback
]

for model in models:
    try:
        result = call_api(model, task)
        return result
    except RateLimitError:
        continue
```

### Tip 2: Batch Simple Tasks

```python
# Instead of calling API 10 times
tasks = [generate_function(f) for f in functions]

# Call once with all tasks
result = call_api(model, "\n".join(tasks))
```

### Tip 3: Use Direct API for Speed

```python
# Direct API: 1.6-5.0s
# CLI Mode: 3.1s + overhead
# Docker Mode: 3.1s + 5-10s startup

# For speed-critical tasks, use Direct API
```

### Tip 4: Use CLI Mode for File Operations

```python
# Direct API: Generates code only
# CLI Mode: Generates AND creates files

# For file creation, use CLI Mode
```

### Tip 5: Cache Results

```python
# Cache generated code to avoid re-generation
cache = {}

def generate_with_cache(task):
    if task in cache:
        return cache[task]
    result = call_api(model, task)
    cache[task] = result
    return result
```

---

## Cost Optimization Strategies

### Strategy 1: Use Free Models Only

```
All tested models are free on OpenRouter
- Mistral Small: Free
- DeepSeek Chat: Free
- DeepSeek R1: Free
- Llama 3.3: Free
- Qwen3 Coder: Free

Cost per 100 tasks: $0
```

### Strategy 2: Prioritize Speed

```
Fastest models (lowest token usage):
1. Mistral Small: 3.1s avg, 538 tokens
2. Llama 3.3: 16.2s avg, 427 tokens
3. DeepSeek Chat: 17.0s avg, 537 tokens

Use Mistral Small for 80% of tasks
Use DeepSeek Chat for 20% of complex tasks
```

### Strategy 3: Batch Operations

```
Instead of:
- 10 API calls × 5s = 50s

Do:
- 1 API call × 5s = 5s
- Batch 10 tasks in one prompt
```

### Strategy 4: Use Direct API for Simple Tasks

```
Direct API: No file creation overhead
CLI Mode: File creation overhead

For code generation only: Use Direct API
For file creation: Use CLI Mode
```

---

## Troubleshooting Guide

### Problem: Rate Limiting (HTTP 429)

**Symptom:** "Provider returned error: 429"

**Solution:**
```python
# Implement exponential backoff
import time

def call_with_retry(model, task, max_retries=3):
    for attempt in range(max_retries):
        try:
            return call_api(model, task)
        except RateLimitError:
            wait_time = 2 ** attempt
            print(f"Rate limited. Waiting {wait_time}s...")
            time.sleep(wait_time)

    # Fallback to different model
    return call_api("meta-llama/llama-3.3-70b-instruct", task)
```

### Problem: Model Not Available (HTTP 404)

**Symptom:** "No endpoints found for model"

**Solution:**
```python
# Use alternative model
alternatives = {
    "google/gemini-flash-1.5-8b": "meta-llama/llama-3.3-70b-instruct",
    "unavailable-model": "mistralai/mistral-small-3.2-24b-instruct:free",
}

model = alternatives.get(requested_model, requested_model)
```

### Problem: Slow Response

**Symptom:** Task takes > 30s

**Solution:**
```python
# Use faster model
if execution_time > 30:
    # Switch to Mistral Small
    model = "mistralai/mistral-small-3.2-24b-instruct:free"
```

### Problem: Low Quality Output

**Symptom:** Generated code is incomplete or incorrect

**Solution:**
```python
# Use higher quality model
if quality_score < 4:
    # Switch to DeepSeek Chat
    model = "deepseek/deepseek-chat"
```

---

## Integration Examples

### Example 1: Quick Code Generation

```python
import httpx

async def generate_code(task: str) -> str:
    """Generate code using fastest model."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "mistralai/mistral-small-3.2-24b-instruct:free",
                "messages": [{"role": "user", "content": task}],
                "max_tokens": 2048,
            },
        )
    return response.json()["choices"][0]["message"]["content"]
```

### Example 2: File Creation with CLI

```python
import subprocess

def create_file_with_openhands(task: str, output_file: str):
    """Create file using CLI mode."""
    result = subprocess.run(
        ["python", "-m", "openhands.core.main", "-t", task],
        env={"LLM_API_KEY": API_KEY},
        capture_output=True,
        text=True,
    )
    return result.stdout
```

### Example 3: Model Rotation

```python
async def generate_with_fallback(task: str) -> str:
    """Generate code with automatic fallback."""
    models = [
        "mistralai/mistral-small-3.2-24b-instruct:free",
        "meta-llama/llama-3.3-70b-instruct",
        "deepseek/deepseek-chat",
    ]

    for model in models:
        try:
            return await generate_code_with_model(model, task)
        except Exception as e:
            print(f"Model {model} failed: {e}")
            continue

    raise Exception("All models failed")
```

---

## FAQ

**Q: Which model should I use?**
A: Start with Mistral Small for speed, switch to DeepSeek Chat if quality is insufficient.

**Q: How much does it cost?**
A: All tested models are free on OpenRouter. Cost is $0.

**Q: Can I use these models for production?**
A: Yes, all models are production-ready. Implement error handling and fallbacks.

**Q: What if a model is rate limited?**
A: Implement model rotation and exponential backoff (see Troubleshooting).

**Q: Should I use CLI or Docker mode?**
A: Use CLI mode for simplicity. Use Docker only if isolation is needed.

---

**Status:** Complete
**Last Updated:** 2025-10-25
**Related:** openhands-capability-matrix.md


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs validation openhands decision guide]]
