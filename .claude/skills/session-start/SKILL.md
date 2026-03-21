---
name: session-start
description: Use this skill at the start of every session to load context from Hindsight and orient in the codebase with CGC. Run before any task.
---

### Session Start Protocol

Run these steps at the beginning of every session, before any task work.

#### 1. Load directives

Call `mcp__hindsight__recall` with:
- bank_id: `tta-dev`
- query: `mandatory directives coding standards dev loop model strategy`

Read all results. These are non-negotiable rules for this session.

#### 2. Load mental models

Call `mcp__hindsight__recall` with:
- bank_id: `tta-dev`
- query: `mental model primitives agents workflows integrations architecture`

Read all results. This is your architectural map.

#### 3. Recall task-specific context (if task is known)

Call `mcp__hindsight__recall` with:
- bank_id: `tta-dev`
- query: `<the specific module, feature, or component you are about to work on>`

#### 4. Orient with CGC

Call `mcp__codegraphcontext__get_repository_stats` to confirm the graph is current.

If the task involves specific files/functions, also call `mcp__codegraphcontext__find_code`
for the target to understand its position in the graph.

#### 5. Acknowledge

State briefly what you loaded — directives active, mental models loaded, current graph
stats — so the user knows the session started warm.

#### Session End: Retain

Before ending the session or after completing a significant task, call
`mcp__hindsight__retain` with bank_id `tta-dev` and content covering:
- Any decision made (what + why)
- Any pattern used for the first time
- Any failure encountered (what + why)
- Any architectural insight gained

Use this format for the content:
```
[type: decision|pattern|failure|insight] <what happened>
Rationale/why: <the reason>
Context: <module or area affected>
```
