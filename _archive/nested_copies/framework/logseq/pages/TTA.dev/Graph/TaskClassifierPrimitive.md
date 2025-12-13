- ---
- type:: [[G]] GraphComponent
- status:: stable
- tags:: #orchestration, #task-management, #llm, #model-selection, #routing
- context-level:: 2-Operational
- component-type:: node
- in-graph:: [[TTA.dev/Concepts/WorkflowPrimitive]]
- modifies-state::
- calls-tools:: [[TTA.dev/Tools/OpenAIPrimitive]] (implicitly, or other LLM primitives)
- source-file:: `packages/tta-dev-primitives/src/tta_dev_primitives/orchestration/task_classifier_primitive.py`
- ---
- ### Summary
  - `TaskClassifierPrimitive` is a `[[TTA.dev/Concepts/WorkflowPrimitive]]` responsible for intelligently classifying incoming tasks based on their `[[TTA.dev/Data/TaskCharacteristics]]` and `[[TTA.dev/Data/TaskComplexity]]`, then recommending the most appropriate LLM for execution.
- ### Logic
  - It takes a `[[TTA.dev/Data/TaskClassifierRequest]]` as input, which includes a `task_description` and optional `user_preferences`.
  - It analyzes the task description to determine its `[[TTA.dev/Data/TaskCharacteristics]]` (e.g., requires reasoning, creativity, code) and `[[TTA.dev/Data/TaskComplexity]]` (simple, moderate, complex, expert).
  - Based on this classification and user preferences (e.g., `prefer_free`), it recommends a specific LLM (e.g., Groq, Gemini Pro, DeepSeek R1, Claude Sonnet 4.5) and provides a `[[TTA.dev/Data/TaskClassification]]` output.
  - This primitive is crucial for dynamic model routing and cost optimization in LLM-powered workflows.


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev/Graph/Taskclassifierprimitive]]
