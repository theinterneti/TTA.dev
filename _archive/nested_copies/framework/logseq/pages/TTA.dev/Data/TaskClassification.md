- ---
- type:: [[D]] DataSchema
- status:: stable
- tags:: #orchestration, #task-management, #llm, #model-selection, #response
- context-level:: 3-Technical
- used-by:: [[TTA.dev/Graph/TaskClassifierPrimitive]]
- source-file:: `packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/task_classifier_primitive.py`
- ---
- ### Summary
  - `TaskClassification` is a Pydantic model representing the output of the `[[TTA.dev/Graph/TaskClassifierPrimitive]]`, providing a recommended LLM and detailed reasoning for a given task.
- ### Fields
  - `complexity`: The `[[TTA.dev/Data/TaskComplexity]]` level of the classified task.
  - `characteristics`: The `[[TTA.dev/Data/TaskCharacteristics]]` identified for the task.
  - `recommended_model`: The name of the LLM recommended for executing this task.
  - `reasoning`: A textual explanation for why the specific model was recommended.
  - `estimated_cost`: The estimated cost in USD for using the recommended model (0.0 for free models).
  - `fallback_models`: A list of alternative models that could be used if the primary recommendation fails.


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev/Data/Taskclassification]]
