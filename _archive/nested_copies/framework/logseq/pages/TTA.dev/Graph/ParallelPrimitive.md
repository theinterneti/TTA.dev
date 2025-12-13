- ---
- type:: [[G]] GraphComponent
- status:: stable
- tags:: #workflow, #composition, #parallel, #concurrency, #orchestration
- context-level:: 2-Operational
- component-type:: graph
- in-graph:: [[TTA.dev/Concepts/WorkflowPrimitive]]
- modifies-state:: [[TTA.dev/Data/WorkflowContext.state]]
- calls-tools::
- source-file:: `packages/tta-dev-primitives/src/tta_dev_primitives/core/parallel.py`
- ---
- ### Summary
  - `ParallelPrimitive` executes multiple `[[TTA.dev/Concepts/WorkflowPrimitive]]` instances concurrently, providing the same input to all and collecting their results in a list.
- ### Logic
  - It takes a list of primitives during initialization.
  - The `_execute_impl` method creates separate asynchronous tasks for each primitive, running them in parallel using `asyncio.gather`.
  - Each parallel branch receives a child `[[TTA.dev/Data/WorkflowContext]]` for proper trace context inheritance.
  - Includes extensive logging, metrics, and tracing for each branch, capturing fan-out and fan-in points.
  - Supports the `|` operator for intuitive parallel composition.


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev/Graph/Parallelprimitive]]
