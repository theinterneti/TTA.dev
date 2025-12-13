- ---
- type:: [[G]] GraphComponent
- status:: stable
- tags:: #performance, #caching, #optimization, #memoization
- context-level:: 2-Operational
- component-type:: node
- in-graph:: [[TTA.dev/Concepts/WorkflowPrimitive]]
- modifies-state:: [[TTA.dev/Data/WorkflowContext.state]]
- calls-tools::
- source-file:: `packages/tta-dev-primitives/src/tta_dev_primitives/performance/cache.py`
- ---
- ### Summary
  - `CachePrimitive` wraps another `[[TTA.dev/Concepts/WorkflowPrimitive]]` to store and retrieve its execution results, reducing latency and costs for expensive operations.
- ### Logic
  - It takes a target primitive, a `cache_key_fn` (to generate a unique key from input and context), and an optional `ttl_seconds` (time-to-live) during initialization.
  - Before executing the wrapped primitive, it checks if a valid result exists in its internal cache using the generated key.
  - If a cache hit occurs and the entry is not expired, the cached result is returned immediately.
  - If a cache miss or expiration occurs, the wrapped primitive is executed, and its result is stored in the cache with a timestamp.
  - Includes logging for cache hits, misses, and expirations, and tracks statistics in the `[[TTA.dev/Data/WorkflowContext.state]]`.


---
**Logseq:** [[TTA.dev/_archive/Nested_copies/Framework/Logseq/Pages/Tta.dev/Graph/Cacheprimitive]]
