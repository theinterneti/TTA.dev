- ---
- type:: [[G]] GraphComponent
- status:: stable
- tags:: #workflow, #branching, #routing, #multi-way-logic
- context-level:: 2-Operational
- component-type:: node
- in-graph:: [[TTA.dev/Concepts/WorkflowPrimitive]]
- modifies-state::
- calls-tools::
- source-file:: `packages/tta-dev-primitives/src/tta_dev_primitives/core/conditional.py`
- ---
- ### Summary
  - `SwitchPrimitive` provides multi-way conditional branching, similar to a switch/case statement, executing a specific `[[TTA.dev/Concepts/WorkflowPrimitive]]` based on a selector function's output.
- ### Logic
  - It takes a `selector` (a callable that returns a string key), a dictionary of `cases` (mapping keys to primitives), and an optional `default` primitive during initialization.
  - The `execute` method first evaluates the `selector` to get a `case_key`.
  - If `case_key` matches an entry in `cases`, the corresponding primitive is executed. If not, and a `default` primitive is provided, it is executed. Otherwise, the input is passed through.
  - Includes logging, metrics, and tracing for selector evaluation and case execution.


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev/Graph/Switchprimitive]]
