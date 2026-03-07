---
title: TTA Dependency Graph
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/architecture/dependency-graph.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Architecture/TTA Dependency Graph]]

## Package Dependencies

```mermaid
graph TD
    tta_ai[TTA AI Framework]
    tta_narrative[TTA Narrative Engine]
    tta_app[TTA Application]
    tta_app --> tta_ai

    classDef framework fill:#e1f5ff,stroke:#01579b
    classDef engine fill:#f3e5f5,stroke:#4a148c
    classDef app fill:#e8f5e9,stroke:#1b5e20
    class tta_ai framework
    class tta_narrative engine
    class tta_app app
```

## Dependency Details

### TTA AI Framework (`tta-ai-framework`)
- **Purpose**: Reusable AI infrastructure
- **Components**: Agent orchestration, model management, prompt registry
- **Dependencies**: None (base package)

### TTA Narrative Engine (`tta-narrative-engine`)
- **Purpose**: Reusable narrative generation system
- **Components**: Scene generation, narrative orchestration, coherence validation
- **Dependencies**: TTA AI Framework

### TTA Application (`tta-app`)
- **Purpose**: TTA-specific application code
- **Components**: Player experience, API gateway, therapeutic systems
- **Dependencies**: TTA AI Framework, TTA Narrative Engine

## Analysis Report

```json
{
  "packages": [
    "tta-ai-framework",
    "tta-narrative-engine",
    "tta-app"
  ],
  "dependencies": {
    "tta-ai-framework": [
      "src",
      "tta_ai"
    ],
    "tta-narrative-engine": [],
    "tta-app": [
      "src",
      "tta_ai"
    ]
  },
  "summary": {
    "total_packages": 3,
    "total_dependencies": 4
  }
}
```

Generated: generate_dependency_graph.py


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___architecture___docs architecture dependency graph]]
