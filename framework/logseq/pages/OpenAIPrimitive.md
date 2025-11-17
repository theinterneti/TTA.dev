# OpenAIPrimitive

**OpenAI API integration primitive for TTA.dev workflows.**

## Overview

> **Note:** This primitive is planned but not yet implemented.

OpenAIPrimitive will provide seamless integration with OpenAI's API for LLM operations in TTA.dev workflows.

## Planned Features

### Model Support
- GPT-4 (gpt-4, gpt-4-turbo)
- GPT-4 Mini (gpt-4o-mini)
- GPT-3.5 Turbo
- Streaming responses
- Function calling

### Configuration
```python
from tta_dev_primitives.llm import OpenAIPrimitive

openai = OpenAIPrimitive(
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=1000,
    api_key=os.environ["OPENAI_API_KEY"]
)
```

### Integration with Router
```python
from tta_dev_primitives import RouterPrimitive

router = RouterPrimitive(
    routes={
        "fast": OpenAIPrimitive(model="gpt-4o-mini"),
        "quality": OpenAIPrimitive(model="gpt-4"),
        "code": OpenAIPrimitive(model="gpt-4-turbo")
    },
    default_route="fast"
)
```

## Current Alternatives

Until OpenAIPrimitive is implemented, use:

### 1. Custom Primitive
```python
from tta_dev_primitives import WorkflowPrimitive
from openai import AsyncOpenAI

class CustomOpenAIPrimitive(WorkflowPrimitive):
    def __init__(self, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI()
        self.model = model

    async def _execute_impl(self, input_data, context):
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": input_data["prompt"]}]
        )
        return {"response": response.choices[0].message.content}
```

### 2. Integration Libraries
- LangChain OpenAI integration
- LlamaIndex OpenAI connector
- Direct OpenAI SDK usage

## Related Primitives

### Implemented
- [[RouterPrimitive]] - Route between LLMs
- [[CachePrimitive]] - Cache LLM responses
- [[RetryPrimitive]] - Retry failed LLM calls
- [[FallbackPrimitive]] - Fallback to alternative LLMs

### Planned
- [[AnthropicPrimitive]] - Anthropic Claude integration
- [[OllamaPrimitive]] - Local Ollama integration
- [[GeminiPrimitive]] - Google Gemini integration

## Implementation Status

- **Status:** Planned
- **Priority:** High
- **Tracking:** See project roadmap
- **Estimated:** Q1 2026

## Contributing

Interested in implementing OpenAIPrimitive? See:
- [[Contributors]] - Contribution guide
- [[TTA.dev/Guides/Custom Primitive Development]] - Development guide
- [[TTA.dev (Meta-Project)]] - Project roadmap

## Related Pages

- [[TTA.dev/Primitives]] - All primitives
- [[PRIMITIVES CATALOG]] - Primitive reference
- [[TTA.dev/Examples]] - Usage examples

## Tags

primitive:: llm
status:: planned
provider:: openai

- [[Project Hub]]