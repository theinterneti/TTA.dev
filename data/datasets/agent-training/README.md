# TTA.dev Agent Training Dataset

**Purpose:** Training data for AI coding agents to learn TTA.dev primitive usage patterns.

## Overview

This dataset contains 20 pairs of anti-patterns (incorrect code) and correct implementations using TTA.dev primitives. Designed for:

- **Fine-tuning** LLMs for code generation
- **RAG (Retrieval Augmented Generation)** for coding assistants
- **Few-shot learning** in AI agents
- **Example-based learning** for developers

## Dataset Structure

### Files

| File | Patterns | Focus |
|------|----------|-------|
| `primitive-patterns.jsonl` | 10 | Core patterns (sequential, parallel, retry, cache, etc.) |
| `advanced-patterns.jsonl` | 10 | Advanced patterns (adaptive, memory, E2B, type safety) |

### Format

Each line is a JSON object with:

```json
{
  "pattern": "sequential_workflow",
  "antipattern": "// Code without primitives",
  "correct": "// Code using TTA.dev primitives",
  "explanation": "Why use primitives",
  "severity": "error|warning|info",
  "rule": "TTA001-TTA005"
}
```

### Fields

- **pattern**: Pattern category (e.g., `sequential_workflow`, `retry_logic`)
- **antipattern**: Manual implementation (what agents should avoid)
- **correct**: TTA.dev primitive usage (what agents should generate)
- **explanation**: Benefits of using primitives
- **severity**: How critical the issue is
  - `error`: Must use primitives
  - `warning`: Should use primitives
  - `info`: Consider using primitives
- **rule**: TTA checker rule code (from `ruff_tta_checker.py`)

## Usage Examples

### Fine-Tuning

```python
import json

# Load training pairs
with open("primitive-patterns.jsonl") as f:
    examples = [json.loads(line) for line in f]

# Format for fine-tuning
training_data = [
    {
        "prompt": f"Fix this code to use TTA.dev primitives:\n\n{ex['antipattern']}",
        "completion": f"{ex['correct']}\n\n# {ex['explanation']}"
    }
    for ex in examples
]
```

### RAG System

```python
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings

# Index examples
examples = load_examples("primitive-patterns.jsonl")
vectorstore = Chroma.from_texts(
    texts=[ex["antipattern"] + "\n" + ex["correct"] for ex in examples],
    embeddings=OpenAIEmbeddings()
)

# Retrieve similar examples
def get_similar_examples(code: str, k: int = 3):
    return vectorstore.similarity_search(code, k=k)
```

### Few-Shot Prompting

```python
def create_few_shot_prompt(user_code: str, examples: list, k: int = 3):
    prompt = "Convert this code to use TTA.dev primitives.\n\n"

    # Add examples
    for ex in examples[:k]:
        prompt += f"Example {k}:\n"
        prompt += f"Before:\n{ex['antipattern']}\n\n"
        prompt += f"After:\n{ex['correct']}\n\n"
        prompt += f"Reason: {ex['explanation']}\n\n"

    # Add user code
    prompt += f"Now convert this:\n{user_code}\n"
    return prompt
```

## Pattern Coverage

### Core Patterns (10)

1. ✅ Sequential workflow (`>>` operator)
2. ✅ Parallel execution (`|` operator)
3. ✅ Retry logic (RetryPrimitive)
4. ✅ Timeout handling (TimeoutPrimitive)
5. ✅ Caching (CachePrimitive)
6. ✅ Fallback logic (FallbackPrimitive)
7. ✅ Workflow context (WorkflowContext)
8. ✅ Custom primitives (extending WorkflowPrimitive)
9. ✅ Production stack (layered primitives)
10. ✅ Routing (RouterPrimitive)

### Advanced Patterns (10)

1. ✅ Adaptive retry (AdaptiveRetryPrimitive)
2. ✅ Memory workflow (MemoryPrimitive)
3. ✅ Mixed composition (>> + |)
4. ✅ Instrumented primitives (InstrumentedPrimitive)
5. ✅ E2B validation (CodeExecutionPrimitive)
6. ✅ Context propagation (correlation IDs)
7. ✅ Error recovery (layered recovery)
8. ✅ Cost optimization (Cache + Router)
9. ✅ Testing (MockPrimitive)
10. ✅ Type safety (generic type parameters)

## Rules Reference

| Rule | Description | Severity |
|------|-------------|----------|
| TTA001 | Prefer primitives over manual async orchestration | error |
| TTA002 | Require WorkflowContext in execute() calls | error |
| TTA003 | Use RetryPrimitive instead of manual loops | error |
| TTA004 | Use TimeoutPrimitive instead of asyncio.wait_for() | error |
| TTA005 | Consider CachePrimitive for expensive operations | warning |
| TTA_ADAPTIVE | Use AdaptiveRetryPrimitive for auto-tuning | info |
| TTA_MEMORY | Use MemoryPrimitive for conversation history | warning |
| TTA_OBSERVABILITY | Extend InstrumentedPrimitive for observability | warning |
| TTA_E2B | Use CodeExecutionPrimitive for code validation | info |
| TTA_TESTING | Use MockPrimitive for testing workflows | info |
| TTA_TYPES | Use type parameters for type safety | warning |

## Integration with Development Workflow

### VS Code Snippets

Snippets in `.vscode/tta-primitives.code-snippets` align with these patterns:

- Type `tta-seq` → Sequential workflow
- Type `tta-par` → Parallel workflow
- Type `tta-retry` → Retry primitive
- Type `tta-cache` → Cache primitive
- And more...

### Validation Tools

Patterns detected by validation tools:

- **AST Validator:** `scripts/validate-primitive-usage.py`
- **TTA Checker:** `scripts/ruff_tta_checker.py`
- **Pre-commit Hook:** `.git/hooks/pre-commit`

### Agent Checklist

Full checklist in `.github/AGENT_CHECKLIST.md` includes:

- Pattern validation steps
- Template references
- Pre-commit verification
- Testing requirements

## Extending the Dataset

To add new patterns:

1. Identify common anti-pattern in codebase
2. Create correct implementation using TTA.dev primitives
3. Add entry to appropriate JSONL file:
   ```json
   {
     "pattern": "new_pattern",
     "antipattern": "// Manual code",
     "correct": "// Primitive-based code",
     "explanation": "Why this is better",
     "severity": "error",
     "rule": "TTA00X"
   }
   ```
4. Update this README's pattern list
5. Add validation rule to `ruff_tta_checker.py` if needed

## Statistics

- **Total Examples:** 20
- **Lines of Code (anti-patterns):** ~400
- **Lines of Code (correct):** ~600
- **Primitives Covered:** 15+
- **Rule Codes:** 11

## License

Same as TTA.dev project. See root LICENSE file.

## Related Documentation

- **Agent Instructions:** `AGENTS.md` - Main agent guidance
- **Checklist:** `.github/AGENT_CHECKLIST.md` - Validation checklist
- **Templates:** `.vscode/tta-prompts.md` - Copy-paste templates
- **Snippets:** `.vscode/tta-primitives.code-snippets` - VS Code snippets
- **Validators:** `scripts/validate-primitive-usage.py` - AST-based validation
- **Checker:** `scripts/ruff_tta_checker.py` - Ruff-compatible checker

---

**Last Updated:** November 10, 2025
**Version:** 1.0
**Maintainer:** TTA.dev Team
