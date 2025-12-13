- ---
- type:: [[T]] ToolInterface
- status:: stable
- tags:: #llm, #openai, #api-integration, #chat-completion
- context-level:: 2-Operational
- implemented-by:: `tta_dev_primitives.integrations.openai_primitive.OpenAIPrimitive`
- uses-data:: [[TTA.dev/Data/OpenAIRequest]], [[TTA.dev/Data/OpenAIResponse]], [[TTA.dev/Data/WorkflowContext]]
- source-file:: `packages/tta-dev-primitives/src/tta_dev_primitives/integrations/openai_primitive.py`
- ---
- ### Summary
  - `OpenAIPrimitive` is a `[[TTA.dev/Concepts/WorkflowPrimitive]]` that wraps the official OpenAI SDK, providing a consistent interface for interacting with OpenAI's chat completion API.
- ### Usage
  - It allows developers to easily integrate OpenAI LLMs into TTA.dev workflows, handling request/response serialization (`[[TTA.dev/Data/OpenAIRequest]]`, `[[TTA.dev/Data/OpenAIResponse]]`) and leveraging `[[TTA.dev/Data/WorkflowContext]]` for observability.
  - Configurable with a default model and API key, with options to override per request.


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev/Tools/Openaiprimitive]]
