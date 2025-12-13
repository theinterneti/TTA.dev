- ---
- type:: [[C]] CoreConcept
- status:: stable
- tags:: #workflow, #composition, #abstraction, #primitives
- context-level:: 1-Strategic
- summary:: The abstract base class for all composable building blocks of TTA.dev workflows.
- implemented-by:: [[TTA.dev/Graph/SequentialPrimitive]], [[TTA.dev/Graph/ParallelPrimitive]], [[TTA.dev/Tools/LambdaPrimitive]]
- ---
- ### Description
  - `WorkflowPrimitive` defines the fundamental interface for any component that can be part of a TTA.dev workflow. It provides abstract methods for execution and defines composition operators (`>>` for sequential, `|` for parallel) to build complex workflows from simpler primitives. All concrete primitives in the framework inherit from this class.


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev/Concepts/Workflowprimitive]]
