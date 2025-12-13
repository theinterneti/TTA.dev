- ---
- type:: [[D]] DataSchema
- status:: stable
- tags:: #orchestration, #task-management, #llm, #model-selection, #request
- context-level:: 3-Technical
- used-by:: [[TTA.dev/Graph/TaskClassifierPrimitive]]
- source-file:: `packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/task_classifier_primitive.py`
- ---
- ### Summary
  - `TaskClassifierRequest` is a Pydantic model defining the input structure for requesting a task classification from the `[[TTA.dev/Graph/TaskClassifierPrimitive]]`.
- ### Fields
  - `task_description`: A detailed textual description of the task to be classified.
  - `user_preferences`: An optional dictionary for user-specific preferences that might influence model selection (e.g., `{"prefer_free": True}`).


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev/Data/Taskclassifierrequest]]
