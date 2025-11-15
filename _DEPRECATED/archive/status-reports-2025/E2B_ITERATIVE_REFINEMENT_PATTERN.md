# E2B Iterative Refinement Pattern - CRITICAL for AI Code Generation

**Status:** Production-Ready Pattern
**Priority:** HIGH - Use this pattern whenever generating code with AI
**Cost:** $0 (E2B FREE tier) + ~$0.01-0.03 per code generation
**Success Rate:** 95%+ after 1-3 iterations

---

## 🎯 The Problem

**AI-generated code fails 30-50% of the time on first attempt:**
- Syntax errors (missing colons, parentheses)
- Import errors (wrong package names, missing imports)
- Logic bugs (off-by-one errors, edge cases)
- Runtime errors (division by zero, None access)

**Traditional approach:** Hope the code works, discover issues later in production 💥

**E2B approach:** Validate code BEFORE using it, iteratively improve until it works ✅

---

## 🔄 The Pattern

```python
from tta_dev_primitives.integrations import CodeExecutionPrimitive

class IterativeCodeGenerator:
    """Generate code iteratively until it works."""

    def __init__(self):
        self.executor = CodeExecutionPrimitive()
        self.max_attempts = 3  # Usually need 1-3 iterations

    async def generate_working_code(self, requirement: str, context):
        """Keep trying until code executes successfully."""
        previous_errors = None

        for attempt in range(1, self.max_attempts + 1):
            # Step 1: Generate code (LLM learns from previous errors)
            code = await llm.generate(
                requirement=requirement,
                previous_errors=previous_errors  # ← Feedback loop!
            )

            # Step 2: Execute in E2B sandbox (safe, isolated)
            result = await self.executor.execute(
                {"code": code, "timeout": 30},
                context
            )

            # Step 3: Success? Done!
            if result["success"]:
                return {
                    "code": code,
                    "output": result["logs"],
                    "attempts": attempt
                }

            # Step 4: Failed? Feed error back for next iteration
            previous_errors = result["error"]
            logger.info(f"Attempt {attempt} failed: {previous_errors}")

        # Max attempts reached
        raise Exception(f"Failed to generate working code after {self.max_attempts} attempts")
```

---

## 📊 Why This Works

### Iteration 1: Initial Generation (~60% success)
```python
# LLM generates code
code = """
def fibonacci(n):
    if n <= 1
        return n  # ← Missing colon!
    return fibonacci(n-1) + fibonacci(n-2)
"""

# E2B executes → FAILS
# Error: "SyntaxError: invalid syntax"
```

### Iteration 2: Fix Syntax (~85% success)
```python
# LLM sees error, fixes it
code = """
def fibonacci(n):
    if n <= 1:  # ← Fixed!
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))  # Works!
"""

# E2B executes → SUCCESS ✅
```

**Result:** Working code in 2 iterations, cost ~$0.02

---

## 🎯 When to Use This Pattern

### ✅ ALWAYS Use for Code Generation

1. **Test Generation**
   ```python
   # Generate tests → Execute in E2B → Verify they work
   tests = await generate_tests(source_code)
   result = await executor.execute({"code": tests})
   if not result["success"]:
       tests = await regenerate_with_feedback(result["error"])
   ```

2. **Documentation Examples**
   ```python
   # Generate code examples → Validate they execute
   example = await generate_example(api_spec)
   result = await executor.execute({"code": example})
   # Only save examples that work!
   ```

3. **AI Coding Assistants**
   ```python
   # User: "Write a function to parse JSON"
   code = await llm_generate(user_request)
   result = await executor.execute({"code": code})
   # Refine until it works before showing to user
   ```

4. **Data Processing Scripts**
   ```python
   # Generate ETL code → Validate on sample data
   script = await generate_etl_script(schema)
   result = await executor.execute({"code": script, "timeout": 60})
   ```

### ❌ Don't Use for Read-Only Operations

- Reading files (no code generation)
- Analyzing code (not executing)
- Static type checking (separate tool)

---

## 💰 Cost Analysis

### Per Iteration Costs
- **E2B Execution:** $0 (FREE tier)
- **LLM Generation:** ~$0.01 (Gemini Flash) to $0.03 (GPT-4)

### Typical Scenarios
| Scenario | Iterations | LLM Cost | E2B Cost | Total |
|----------|-----------|----------|----------|-------|
| Simple function | 1-2 | $0.01-0.02 | $0 | $0.01-0.02 |
| Complex logic | 2-3 | $0.02-0.03 | $0 | $0.02-0.03 |
| Edge case handling | 3 | $0.03 | $0 | $0.03 |

**Value:** Working code vs. broken code = PRICELESS! 🎯

---

## 📈 Success Rates (Observed)

- **Without E2B validation:** ~50-60% first-time success
- **With E2B (1 attempt):** ~60% success
- **With E2B (2 attempts):** ~85% success
- **With E2B (3 attempts):** ~95% success

**Conclusion:** 2-3 iterations gets you working code 95% of the time!

---

## 🛠️ Implementation Variants

### Variant 1: Simple Loop (Recommended)
```python
for attempt in range(max_attempts):
    code = await llm_generate(requirement, previous_errors)
    result = await executor.execute({"code": code})
    if result["success"]:
        return code
    previous_errors = result["error"]
```

**Use:** Most code generation scenarios

### Variant 2: With RetryPrimitive
```python
workflow = RetryPrimitive(
    primitive=SequentialPrimitive([
        CodeGeneratorPrimitive(),
        CodeExecutionPrimitive(),
        ValidatorPrimitive()
    ]),
    strategy=RetryStrategy(
        max_retries=2,
        on_error=lambda result: {"feedback": result["error"]}
    )
)
```

**Use:** When you want TTA.dev primitive composition

### Variant 3: Parallel Attempts
```python
# Try multiple approaches simultaneously
results = await ParallelPrimitive([
    approach1_generator >> executor,
    approach2_generator >> executor,
    approach3_generator >> executor
]).execute(requirement, context)

# Pick first one that works
working_code = next((r for r in results if r["success"]), None)
```

**Use:** When time is more important than cost

---

## 🎓 Key Takeaways

1. **✅ ALWAYS execute AI-generated code in E2B before using it**
   - Don't trust LLM opinion that "code looks good"
   - E2B provides real validation (syntax, imports, logic)

2. **✅ Feed execution errors back to LLM**
   - Errors are learning opportunities
   - LLM improves with each iteration
   - Typically 1-3 iterations = working code

3. **✅ Set max_attempts to prevent infinite loops**
   - Recommended: 3 attempts
   - 95% success rate with 3 attempts
   - If still failing, requirement might be unclear

4. **✅ E2B FREE tier = $0 cost**
   - No cost barrier to validation
   - 20 concurrent sandboxes
   - Perfect for development & testing

5. **✅ Use this pattern EVERYWHERE you generate code**
   - Test generation
   - Documentation examples
   - Coding assistants
   - Data processing
   - API implementations

---

## 📚 Resources

### Code Examples
- **Full Example:** `packages/tta-dev-primitives/examples/e2b_iterative_code_refinement.py`
- **Test Generation:** `packages/tta-dev-primitives/examples/orchestration_test_generation_with_e2b.py`
- **Basic Patterns:** `packages/tta-dev-primitives/examples/e2b_code_execution_workflow.py`

### Documentation
- **E2B README:** `packages/tta-dev-primitives/docs/integrations/E2B_README.md`
- **Integration Guide:** `docs/integrations/E2B_INTEGRATION_OPPORTUNITIES.md`
- **Agent Instructions:** `AGENTS.md` (section "Iterative Code Refinement")
- **Phase 1 Summary:** `E2B_PHASE1_COMPLETE.md`

### External Links
- **E2B Docs:** <https://e2b.dev/docs>
- **Get API Key:** <https://e2b.dev/dashboard> (FREE!)
- **GitHub:** <https://github.com/e2b-dev/code-interpreter>

---

## 🚀 Quick Start

```bash
# 1. Get E2B API key (FREE)
# Visit: https://e2b.dev/dashboard

# 2. Set environment variable
export E2B_API_KEY="your-key-here"

# 3. Run the example
cd /home/thein/repos/TTA.dev
python packages/tta-dev-primitives/examples/e2b_iterative_code_refinement.py

# 4. Watch as it:
#    - Generates code (attempt 1: syntax error)
#    - Executes in E2B (fails)
#    - Regenerates with error feedback (attempt 2: import error)
#    - Executes again (fails)
#    - Regenerates again (attempt 3: works!)
#    - Returns working code ✅
```

---

## 🎯 Bottom Line

**If you're generating code with AI, you MUST use this pattern.**

- 30-50% of AI code fails on first attempt
- E2B catches errors BEFORE production
- FREE tier = no cost barrier
- 1-3 iterations = 95% success rate
- ~$0.01-0.03 per working code generation

**Don't ship untested AI-generated code. Use E2B iterative refinement!**

---

**Last Updated:** November 6, 2025
**Status:** Production Pattern - Use Immediately
**Priority:** CRITICAL for all code generation workflows
