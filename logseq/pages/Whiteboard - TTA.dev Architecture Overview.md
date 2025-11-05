# Whiteboard: TTA.dev Architecture Overview

**Visual architecture guide for understanding TTA.dev component relationships**

---

## 🎨 Whiteboard Purpose

This whiteboard visualizes:
- **Component layers** and their relationships
- **Data flow** between primitives
- **Composition patterns** with visual examples
- **Integration points** for observability and agents

**To view:** Open this page → Click "..." menu → "Open in whiteboard"

---

## 📐 Whiteboard Structure

### Layer 1: User Application Layer (Top)

```text
┌─────────────────────────────────────────────────────────────┐
│                   USER APPLICATION LAYER                    │
│                                                             │
│  Custom Workflows    Custom Primitives    Configuration    │
│  ┌──────────┐       ┌──────────┐         ┌──────────┐    │
│  │ app.py   │       │MyAgent   │         │ config   │    │
│  │          │       │          │         │          │    │
│  └────┬─────┘       └────┬─────┘         └──────────┘    │
│       │                  │                                 │
│       └──────────────────┼─────────────────────────────────┤
│                          ↓                                 │
└─────────────────────────────────────────────────────────────┘
```

**Elements:**
- Rectangle: "User Application Layer" (blue background)
- 3 smaller rectangles inside: "Custom Workflows", "Custom Primitives", "Configuration"
- Arrows pointing down to next layer

### Layer 2: TTA.dev Primitives Layer (Middle)

```text
┌─────────────────────────────────────────────────────────────┐
│                   TTA.DEV PRIMITIVES LAYER                  │
│                  [[TTA Primitives]] Reference               │
│                                                             │
│  Core Patterns         Recovery Patterns    Performance    │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────┐  │
│  │ Sequential   │     │ Retry        │     │ Cache    │  │
│  │ Parallel     │     │ Fallback     │     │          │  │
│  │ Conditional  │     │ Timeout      │     │          │  │
│  │ Router       │     │ Compensation │     │          │  │
│  └──────────────┘     └──────────────┘     └──────────┘  │
│                                                             │
│  Orchestration         Testing                             │
│  ┌──────────────┐     ┌──────────────┐                    │
│  │ Delegation   │     │ MockPrimitive│                    │
│  │ MultiModel   │     │              │                    │
│  └──────────────┘     └──────────────┘                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Elements:**
- Large rectangle: "TTA.dev Primitives Layer" (green background)
- 5 grouped rectangles for different primitive categories
- Link to [[TTA Primitives]] page
- Each category shows key primitives

### Layer 3: Observability Layer (Bottom)

```text
┌─────────────────────────────────────────────────────────────┐
│                   OBSERVABILITY LAYER                       │
│            [[tta-observability-integration]]                │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │OpenTelemetry│  │ Prometheus  │  │  Structured │       │
│  │   Tracing   │  │   Metrics   │  │   Logging   │       │
│  │             │  │             │  │             │       │
│  │ - Spans     │  │ - Counters  │  │ - JSON logs │       │
│  │ - Context   │  │ - Gauges    │  │ - Corr IDs  │       │
│  │ - Baggage   │  │ - Histograms│  │ - Levels    │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Elements:**
- Rectangle: "Observability Layer" (yellow background)
- 3 equal-sized rectangles: OpenTelemetry, Prometheus, Logging
- Bullet points inside each showing features
- Link to [[tta-observability-integration]] page

---

## 🔄 Data Flow Diagram

### Sequential Flow (>> Operator)

```text
   INPUT
     │
     ↓
┌─────────┐
│ Step 1  │  "Validate input"
└────┬────┘
     │ result1
     ↓
┌─────────┐
│ Step 2  │  "Transform data"
└────┬────┘
     │ result2
     ↓
┌─────────┐
│ Step 3  │  "Generate output"
└────┬────┘
     │
     ↓
   OUTPUT
```

**Whiteboard implementation:**
- 3 rectangles vertically aligned
- Arrows connecting each step
- Text labels on arrows showing intermediate results
- Text annotations describing each step's purpose

### Parallel Flow (| Operator)

```text
              INPUT
                │
                ├──────────────┐
                │              │
                ↓              ↓              ↓
          ┌─────────┐    ┌─────────┐    ┌─────────┐
          │Branch 1 │    │Branch 2 │    │Branch 3 │
          │"Fast LLM"    │"Quality"│    │"Cached" │
          └────┬────┘    └────┬────┘    └────┬────┘
               │              │              │
               └──────────────┴──────────────┘
                              │
                              ↓
                        [result1, result2, result3]
                              │
                              ↓
                          AGGREGATOR
                              │
                              ↓
                           OUTPUT
```

**Whiteboard implementation:**
- 1 input node (circle)
- 3 branch rectangles horizontally aligned
- Arrows diverging from input, converging to aggregator
- Labels describing each branch's purpose

---

## 🎯 Composition Patterns Visual

### Pattern 1: Cached LLM with Recovery

```text
        INPUT
          │
          ↓
    ┌──────────┐
    │  Cache   │ ← Hit? Return immediately
    │  Check   │
    └────┬─────┘
         │ Miss
         ↓
    ┌──────────┐
    │ Timeout  │ ← Circuit breaker (30s)
    │ Wrapper  │
    └────┬─────┘
         │
         ↓
    ┌──────────┐
    │  Retry   │ ← Exponential backoff (3x)
    │ Wrapper  │
    └────┬─────┘
         │
         ↓
    ┌──────────┐
    │ Fallback │ ← GPT-4 → GPT-4-mini → Cached
    │ Cascade  │
    └────┬─────┘
         │
         ↓
       OUTPUT
```

**Sticky notes to add:**
- "40-60% cost reduction from cache"
- "99.9% availability from fallback"
- "<30s worst-case latency"
- "Code: [recovery_patterns.py]"

### Pattern 2: RAG Workflow

```text
     USER QUERY
         │
         ↓
    ┌─────────┐
    │ Query   │
    │ Router  │ ← Simple vs Complex
    └────┬────┘
         │
    ┌────┴────┐
    │         │
    ↓         ↓
[Simple]  [Complex]
    │         │
    │    ┌────────┐
    │    │Vector  │
    │    │Retriev │
    │    └───┬────┘
    │        │
    │        ↓
    │    ┌────────┐
    │    │Document│
    │    │ Grader │ ← Filter irrelevant
    │    └───┬────┘
    │        │
    └────────┴────────┐
                      ↓
                 ┌─────────┐
                 │ Answer  │
                 │Generator│
                 └────┬────┘
                      │
                      ↓
                 ┌─────────┐
                 │Hallucin │
                 │ Checker │ ← Validate grounding
                 └────┬────┘
                      │
                      ↓
                   RESPONSE
```

**Links to add:**
- [[TTA Primitives/RouterPrimitive]]
- [[AI Research/RAG Patterns]]
- [[Architecture Decisions/ADR-015 RAG Implementation]]

---

## 🏗️ Package Architecture

### TTA.dev Monorepo Structure

```text
┌────────────────────────────────────────────────┐
│                  TTA.dev Repo                  │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │        packages/ (Monorepo)              │ │
│  │                                          │ │
│  │  ┌─────────────────┐  ┌───────────────┐ │ │
│  │  │tta-dev-         │  │tta-           │ │ │
│  │  │primitives       │  │observability- │ │ │
│  │  │                 │  │integration    │ │ │
│  │  │ Core primitives │  │ OpenTelemetry │ │ │
│  │  │ SequentialPrim  │  │ Prometheus    │ │ │
│  │  │ ParallelPrim    │  │ Enhanced      │ │ │
│  │  │ Recovery        │  │ primitives    │ │ │
│  │  └─────────────────┘  └───────────────┘ │ │
│  │                                          │ │
│  │  ┌─────────────────┐  ┌───────────────┐ │ │
│  │  │universal-agent- │  │keploy-        │ │ │
│  │  │context          │  │framework      │ │ │
│  │  │                 │  │               │ │ │
│  │  │ Multi-agent     │  │ API testing   │ │ │
│  │  │ Coordination    │  │ Record/Replay │ │ │
│  │  │ State mgmt      │  │               │ │ │
│  │  └─────────────────┘  └───────────────┘ │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │            docs/                         │ │
│  │  Architecture, Guides, Examples          │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │            scripts/                      │ │
│  │  Validation, Automation                  │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

**Color coding:**
- Blue: Core primitives package
- Green: Observability package
- Purple: Agent coordination package
- Orange: Testing framework package

---

## 🔗 Integration Points

### Cross-Package Integration Map

```text
┌─────────────────┐
│  User App       │
└────────┬────────┘
         │ uses
         ↓
┌─────────────────┐      imports      ┌──────────────────┐
│ tta-dev-        │◄─────────────────►│ tta-             │
│ primitives      │                   │ observability-   │
│                 │  automatic tracing│ integration      │
│ - WorkflowPrim  │◄──────────────────│                  │
│ - Sequential    │                   │ - Initialize     │
│ - Parallel      │    Enhanced prims │ - Enhanced Cache │
│                 │◄──────────────────│ - Enhanced Router│
└────────┬────────┘                   └──────────────────┘
         │ uses
         ↓
┌─────────────────┐
│ universal-agent-│
│ context         │
│                 │
│ - Coordination  │
│ - State         │
└─────────────────┘
```

**Arrows:**
- Solid arrows: Direct dependencies
- Dashed arrows: Optional integrations
- Double arrows: Bidirectional data flow

**Annotations:**
- "All primitives auto-integrate with observability"
- "Enhanced primitives add Prometheus metrics"
- "Context package coordinates multi-agent workflows"

---

## 💡 How to Use This Whiteboard

### In Logseq Desktop App

1. **Open this page** in Logseq
2. **Click "..." menu** → "Open in whiteboard"
3. **Recreate the diagrams** using:
   - Rectangle tool for components
   - Arrow tool for data flow
   - Text tool for labels
   - Sticky notes for annotations

### Adding Interactive Elements

1. **Embed code blocks:**
   - Copy a code block from [[Learning TTA Primitives]]
   - Paste as block reference in whiteboard

2. **Link to pages:**
   - Select any shape
   - Add property: `page-ref: [[TTA Primitives]]`
   - Clicking the shape navigates to the page

3. **Add status indicators:**
   - Green shapes: Completed features
   - Yellow shapes: In progress
   - Red shapes: Blockers or issues

### Exporting

1. **For documentation:**
   - Right-click whiteboard → "Export as PNG"
   - Save to `docs/architecture/images/`
   - Include in markdown docs

2. **For presentations:**
   - Export at high resolution
   - Use in slide decks
   - Share in PRs for architectural discussions

---

## 🎨 Whiteboard Best Practices

### Layout Tips

1. **Top-to-bottom flow** for sequential processes
2. **Left-to-right flow** for parallel processes
3. **Center-out** for hub-and-spoke architectures
4. **Consistent spacing** for visual clarity

### Color Conventions

- **Blue:** Core functionality
- **Green:** Performance features
- **Yellow:** Observability
- **Red:** Errors/blockers
- **Purple:** Advanced features
- **Gray:** External dependencies

### Annotation Strategy

- **Shapes:** Components and primitives
- **Arrows:** Data flow and dependencies
- **Text labels:** Operation names
- **Sticky notes:** Detailed explanations
- **Block refs:** Code examples

---

## 🔗 Related Pages

- [[TTA Primitives]] - Complete primitives catalog
- [[TTA.dev (Meta-Project)]] - Project dashboard
- [[AI Research]] - Research notes and patterns
- [[Architecture Decisions]] - ADR log

---

## 📚 Next Steps

1. **Open in whiteboard mode** and recreate diagrams
2. **Customize for your use case** - add your own workflows
3. **Link to code** - add file references to implementation
4. **Export visuals** - include in documentation
5. **Share with team** - use in PR reviews and planning

---

**Whiteboard Type:** Architecture Overview
**Complexity:** Intermediate
**Estimated Creation Time:** 30-45 minutes
**Last Updated:** October 31, 2025
