---
title: OpenHands Fixed Implementation Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/openhands/FIXED_IMPLEMENTATION_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/OpenHands Fixed Implementation Guide]]

**Date:** 2025-10-28
**Status:** ✅ Fixed - Condensation Bug Workaround Implemented
**Purpose:** Development assistant tool for AI agents

---

## 🎯 What Was Fixed

### **Problem: Condensation Loop Bug (GitHub Issue #8630)**

OpenHands Docker headless mode had a critical bug where the conversation window condenser creates an infinite loop, preventing task execution.

### **Solution: Triple-Layer Condensation Prevention**

We implemented a **three-layer defense** against the condensation loop bug:

1. **Command-line flag:** `--no-condense` (primary workaround from GitHub issue)
2. **Environment variable:** `CONDENSATION_ENABLED=false` (explicit disable)
3. **Attempt limit:** `MAX_CONDENSATION_ATTEMPTS=0` (prevent any attempts)

### **Changes Made**

**File:** `src/agent_orchestration/openhands_integration/docker_client.py`

**Before (lines 150-176):**
```python
# Old command structure
self.openhands_image,
"sh",
"-c",
f"mkdir -p /.openhands && python -m openhands.core.main -t {task_description!r}",
```

**After (lines 149-185):**
```python
# New environment variables
"-e",
"CONDENSATION_ENABLED=false",  # Disable condensation entirely
"-e",
"MAX_CONDENSATION_ATTEMPTS=0",  # Prevent any condensation attempts

# New command structure with --no-condense flag
self.openhands_image,
"python",
"-m",
"openhands.core.main",
"--no-condense",  # Disable condensation via command-line flag
"-t",
task_description,
"-d",
"/workspace",
```

---

## 🚀 Quick Start

### **1. Set Up Environment**

```bash
# Copy .env.example to .env (if not already done)
cp .env.example .env

# Edit .env and set your OpenRouter API key
# Change this line:
#   OPENROUTER_API_KEY=your_openrouter_api_key_here
# To your actual API key:
#   OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx

# Get an API key from: https://openrouter.ai

# Verify Docker is running
docker ps
```

**Note:** The OpenHands Docker client automatically loads environment variables from the `.env` file at the repository root. You do NOT need to manually export `OPENROUTER_API_KEY`.

### **2. Run Test Script**

```bash
# Test the fixed implementation
# The script automatically loads .env - no manual export needed!
python scripts/test_openhands_fixed.py
```

### **3. Expected Output**

```
================================================================================
OpenHands Docker Client - Condensation Bug Fix Verification
================================================================================

================================================================================
TEST 1: Simple File Creation
================================================================================

Task: Create a file named hello.txt with content 'Hello from OpenHands with condensation fix!'
Workspace: /tmp/openhands_test_fixed

✅ Task completed successfully!
Success: True
Exit Code: 0
Duration: 45.23s

✅ File created successfully!
Content: Hello from OpenHands with condensation fix!

================================================================================
TEST 2: Test Generation
================================================================================

Task: Generate tests for calculator.py
Workspace: /tmp/openhands_test_fixed

✅ Task completed successfully!
Success: True
Exit Code: 0
Duration: 78.56s

✅ Test file created successfully!
File size: 1234 bytes

================================================================================
TEST SUMMARY
================================================================================
Simple File Creation: ✅ PASSED
Test Generation: ✅ PASSED

Total: 2/2 tests passed

🎉 All tests passed! OpenHands is working correctly.
```

---

## 📖 Usage Examples

### **Example 1: Simple File Creation**

```python
import asyncio
from pathlib import Path
from pydantic import SecretStr
from agent_orchestration.openhands_integration.docker_client import DockerOpenHandsClient
from agent_orchestration.openhands_integration.config import OpenHandsConfig

async def create_file():
    config = OpenHandsConfig(
        api_key=SecretStr(os.getenv("OPENROUTER_API_KEY")),
        model="deepseek/deepseek-chat-v3.1:free",
        workspace_path=Path("/tmp/workspace"),
    )

    client = DockerOpenHandsClient(config)
    result = await client.execute_task(
        "Create a file named hello.txt with content 'Hello World!'",
        timeout=120
    )

    print(f"Success: {result.success}")
    print(f"Duration: {result.duration:.2f}s")

asyncio.run(create_file())
```

### **Example 2: Generate Tests for Module**

```python
async def generate_tests():
    config = OpenHandsConfig(
        api_key=SecretStr(os.getenv("OPENROUTER_API_KEY")),
        model="deepseek/deepseek-chat-v3.1:free",
        workspace_path=Path("/path/to/project"),
    )

    client = DockerOpenHandsClient(config)

    task = """
    Generate comprehensive unit tests for src/my_module.py.
    Create test_my_module.py with pytest tests covering:
    - All public functions
    - Edge cases
    - Error handling
    - 80%+ coverage
    """

    result = await client.execute_task(task, timeout=180)

    if result.success:
        print("✅ Tests generated successfully!")
    else:
        print(f"❌ Failed: {result.output}")

asyncio.run(generate_tests())
```

### **Example 3: Code Scaffolding**

```python
async def scaffold_component():
    config = OpenHandsConfig(
        api_key=SecretStr(os.getenv("OPENROUTER_API_KEY")),
        model="deepseek/deepseek-chat-v3.1:free",
        workspace_path=Path("/path/to/project"),
    )

    client = DockerOpenHandsClient(config)

    task = """
    Create a new FastAPI router for user management:
    1. Create src/api/routers/users.py
    2. Include CRUD endpoints (GET, POST, PUT, DELETE)
    3. Add Pydantic models for request/response
    4. Include docstrings and type hints
    5. Follow existing project patterns
    """

    result = await client.execute_task(task, timeout=240)

    if result.success:
        print("✅ Component scaffolded successfully!")

asyncio.run(scaffold_component())
```

---

## 🔧 Configuration Options

### **OpenHandsConfig Parameters**

```python
config = OpenHandsConfig(
    # Required
    api_key=SecretStr("your-api-key"),

    # Model selection
    model="deepseek/deepseek-chat-v3.1:free",  # Free model
    # model="anthropic/claude-3.5-sonnet",     # Premium model

    # API endpoint
    base_url="https://openrouter.ai/api/v1",

    # Workspace
    workspace_path=Path("/path/to/workspace"),

    # Docker images (optional)
    openhands_image="docker.all-hands.dev/all-hands-ai/openhands:0.59",
    runtime_image="docker.all-hands.dev/all-hands-ai/runtime:0.59-nikolaik",
)
```

### **Execution Options**

```python
result = await client.execute_task(
    task="Your task description",
    timeout=120,  # Timeout in seconds (default: 300)
)
```

---

## 📊 Performance Characteristics

### **Typical Execution Times**

| Task Type | Duration | Notes |
|-----------|----------|-------|
| Simple file creation | 30-60s | Includes Docker startup |
| Test generation (small module) | 60-120s | Depends on module complexity |
| Code scaffolding | 90-180s | Depends on component size |
| Complex refactoring | 180-300s | May require multiple iterations |

### **Resource Usage**

- **Memory:** ~2GB per container
- **CPU:** 1-2 cores during execution
- **Disk:** ~500MB for Docker images
- **Network:** Minimal (API calls only)

---

## 🐛 Troubleshooting

### **Issue: "OPENROUTER_API_KEY is not set or is using placeholder value"**

**Cause:** The `.env` file doesn't exist or contains the placeholder value.

**Solution:**

```bash
# Step 1: Copy .env.example to .env
cp .env.example .env

# Step 2: Edit .env and set your actual API key
# Change this line:
#   OPENROUTER_API_KEY=your_openrouter_api_key_here
# To your actual API key:
#   OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx

# Step 3: Get an API key from https://openrouter.ai if you don't have one
```

**Note:** The OpenHands Docker client automatically loads the `.env` file. You do NOT need to manually export the environment variable.

### **Issue: "Docker daemon not running"**

**Solution:**
```bash
# Start Docker
sudo systemctl start docker

# Verify
docker ps
```

### **Issue: "Permission denied" when accessing workspace**

**Solution:**
```bash
# Ensure workspace is writable
chmod -R 755 /path/to/workspace

# Or use /tmp for testing
workspace_path=Path("/tmp/openhands_workspace")
```

### **Issue: Task times out after 300 seconds**

**Solution:**
```python
# Increase timeout for complex tasks
result = await client.execute_task(task, timeout=600)
```

### **Issue: "Condensation loop detected"**

**Status:** ✅ **FIXED** - This should no longer occur with the new implementation.

**If it still occurs:**
1. Verify you're using the updated `docker_client.py`
2. Check Docker logs: `docker logs <container-name>`
3. Report issue with logs

---

## 📝 Best Practices

### **1. Use Specific Task Descriptions**

❌ **Bad:**
```python
task = "Create tests"
```

✅ **Good:**
```python
task = """
Generate comprehensive unit tests for src/calculator.py.
Create test_calculator.py with pytest tests that:
1. Test add() function with positive/negative numbers
2. Test subtract() function with edge cases
3. Achieve 80%+ coverage
"""
```

### **2. Set Appropriate Timeouts**

```python
# Simple tasks
result = await client.execute_task(task, timeout=120)

# Complex tasks
result = await client.execute_task(task, timeout=300)
```

### **3. Use Free Models for Development**

```python
# Free model (good for most tasks)
model="deepseek/deepseek-chat-v3.1:free"

# Premium model (for complex tasks only)
model="anthropic/claude-3.5-sonnet"
```

### **4. Check Results**

```python
result = await client.execute_task(task)

if result.success:
    print(f"✅ Task completed in {result.duration:.2f}s")
else:
    print(f"❌ Task failed: {result.output}")
```

---

## 🎯 Use Cases for AI Agents

### **When to Use OpenHands**

✅ **Good use cases:**
- Generate test files for modules
- Scaffold new components
- Create boilerplate code
- Refactor existing code
- Generate documentation

❌ **Not suitable for:**
- Runtime operations (use TTA's agent orchestration)
- Real-time user interactions
- Production deployments
- Critical business logic

### **Integration with Development Workflow**

```python
# Example: AI agent using OpenHands for test generation
async def ai_agent_workflow():
    # 1. AI agent identifies module needing tests
    module_path = "src/my_module.py"

    # 2. AI agent uses OpenHands to generate tests
    config = OpenHandsConfig(...)
    client = DockerOpenHandsClient(config)

    task = f"Generate comprehensive tests for {module_path}"
    result = await client.execute_task(task)

    # 3. AI agent validates generated tests
    if result.success:
        # Run tests to verify they work
        # Add to version control
        # Continue with next task
        pass
```

---

## 📚 Related Documentation

- **Investigation Report:** `OPENHANDS_CONDENSATION_BUG_INVESTIGATION.md`
- **Role Clarification:** `OPENHANDS_ROLE_CLARIFICATION.md`
- **Integration Analysis:** `docs/openhands/INTEGRATION_ANALYSIS_AND_RECOMMENDATION.md`
- **Test Generation Plan:** `docs/TEST_GENERATION_PLAN.md`

---

## ✅ Summary

**Status:** ✅ **FIXED AND READY FOR USE**

**What was fixed:**
- Added `--no-condense` command-line flag
- Added `CONDENSATION_ENABLED=false` environment variable
- Added `MAX_CONDENSATION_ATTEMPTS=0` environment variable
- Fixed Docker command structure

**How to use:**
1. Set `OPENROUTER_API_KEY` environment variable
2. Run `python scripts/test_openhands_fixed.py` to verify
3. Use `DockerOpenHandsClient` in your code
4. Provide specific task descriptions
5. Check results and handle errors

**Next steps:**
1. Test with your specific use cases
2. Integrate into development workflow
3. Document any issues encountered
4. Share successful patterns with team

---

**Document Owner:** TTA Development Team
**Last Updated:** 2025-10-28
**Status:** ✅ Ready for Production Use


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs openhands fixed implementation guide document]]
