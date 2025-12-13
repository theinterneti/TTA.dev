- ---
- type:: [[T]] ToolInterface
- status:: stable
- tags:: #utility, #adapter, #function-wrapper
- context-level:: 3-Technical
- implemented-by:: `tta_dev_primitives.core.base.LambdaPrimitive`
- uses-data:: [[TTA.dev/Data/WorkflowContext]]
- source-file:: `packages/tta-dev-primitives/src/tta_dev_primitives/core/base.py`
- ---
- ### Summary
  - `LambdaPrimitive` is a simple primitive that wraps a Python function or lambda, allowing it to be integrated into TTA.dev workflows.
- ### Usage
  - It's primarily used for quick transformations, data adaptations, or integrating existing synchronous/asynchronous functions into a primitive chain without needing to define a full `WorkflowPrimitive` subclass.
  - Example: `transform = LambdaPrimitive(lambda x, ctx: x.upper())`


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev/Tools/Lambdaprimitive]]
