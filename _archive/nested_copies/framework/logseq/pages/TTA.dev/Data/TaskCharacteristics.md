- ---
- type:: [[D]] DataSchema
- status:: stable
- tags:: #orchestration, #task-management, #llm, #model-selection
- context-level:: 3-Technical
- used-by:: [[TTA.dev/Data/TaskClassification]], [[TTA.dev/Graph/TaskClassifierPrimitive]]
- source-file:: `packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/task_classifier_primitive.py`
- ---
- ### Summary
  - `TaskCharacteristics` is a Pydantic model that captures various boolean flags indicating specific requirements or attributes of a task, used by the `[[TTA.dev/Graph/TaskClassifierPrimitive]]` to inform model selection.
- ### Fields
  - `requires_reasoning`: True if the task needs multi-step logical deduction.
  - `requires_creativity`: True if the task involves generating novel or imaginative output.
  - `requires_code`: True if the task involves code generation, debugging, or refactoring.
  - `requires_speed`: True if the task demands an ultra-fast response time.
  - `requires_long_context`: True if the task needs a context window larger than 100K tokens.
  - `requires_accuracy`: True if the task prioritizes high correctness and precision.


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev/Data/Taskcharacteristics]]
