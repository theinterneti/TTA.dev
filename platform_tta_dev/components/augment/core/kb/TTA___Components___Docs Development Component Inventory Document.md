---
title: TTA Component Inventory
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/development/COMPONENT_INVENTORY.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Components/TTA Component Inventory]]

**Last Updated**: 2025-10-07
**Total Components**: 12

---

## Overview

This document provides a comprehensive inventory of all TTA components, organized by functional group. Each component is tracked for maturity stage, dependencies, and promotion readiness.

---

## Component Summary by Functional Group

| Functional Group | Components | Development | Staging | Production |
|------------------|------------|-------------|---------|------------|
| Core Infrastructure | 3 | 3 | 0 | 0 |
| AI/Agent Systems | 4 | 4 | 0 | 0 |
| Player Experience | 3 | 3 | 0 | 0 |
| Therapeutic Content | 2 | 2 | 0 | 0 |
| **Total** | **12** | **12** | **0** | **0** |

---

## Core Infrastructure Components

### 1. Neo4j
**Component ID**: `component:neo4j`
**Current Stage**: Development
**Owner**: theinterneti
**Location**: `src/components/neo4j_component.py`
**MATURITY.md**: `src/components/MATURITY.md` (Neo4j)

**Purpose**: Graph database for storing narrative state, character relationships, and world knowledge

**Key Features**:
- Docker-based deployment
- Persistent storage
- Health monitoring
- Backup/restore capabilities

**Dependencies**: None (foundational)

**Promotion Readiness**:
- [ ] Ready for Staging
- Blockers: Test coverage, documentation

---

### 2. Docker
**Component ID**: `component:docker`
**Current Stage**: Development
**Owner**: theinterneti
**Location**: `src/components/docker_component.py`
**MATURITY.md**: `src/components/MATURITY.md` (Docker)

**Purpose**: Container orchestration and infrastructure management

**Key Features**:
- Docker Compose integration
- Multi-environment support
- Container lifecycle management
- Network configuration

**Dependencies**: None (foundational)

**Promotion Readiness**:
- [ ] Ready for Staging
- Blockers: Test coverage, documentation

---

### 3. Carbon
**Component ID**: `component:carbon`
**Current Stage**: Development
**Owner**: theinterneti
**Location**: `src/components/carbon_component.py`
**MATURITY.md**: `src/components/MATURITY.md` (Carbon)

**Purpose**: Carbon-based infrastructure component

**Key Features**:
- TBD (component analysis needed)

**Dependencies**: None (foundational)

**Promotion Readiness**:
- [ ] Ready for Staging
- Blockers: Component analysis, test coverage, documentation

---

## AI/Agent Systems Components

### 4. Agent Orchestration
**Component ID**: `component:agent-orchestration`
**Current Stage**: Development
**Owner**: theinterneti
**Location**: `src/components/agent_orchestration_component.py`
**MATURITY.md**: `src/components/MATURITY.md` (Agent Orchestration)

**Purpose**: Coordinates multiple AI agents for collaborative storytelling

**Key Features**:
- Multi-agent coordination
- Agent communication protocols
- Task distribution
- Response aggregation

**Dependencies**:
- LLM (Development)
- Model Management (Development)

**Promotion Readiness**:
- [ ] Ready for Staging
- Blockers: Test coverage, integration tests, documentation

---

### 5. LLM
**Component ID**: `component:llm`
**Current Stage**: Development
**Owner**: theinterneti
**Location**: `src/components/llm_component.py`
**MATURITY.md**: `src/components/MATURITY.md` (LLM)

**Purpose**: Large Language Model integration and management

**Key Features**:
- Multiple LLM provider support
- Request/response handling
- Rate limiting
- Error handling and retries

**Dependencies**:
- Model Management (Development)

**Promotion Readiness**:
- [ ] Ready for Staging
- Blockers: Test coverage, performance validation, documentation

---

### 6. Model Management
**Component ID**: `component:model-management`
**Current Stage**: Development
**Owner**: theinterneti
**Location**: `src/components/model_management/`
**MATURITY.md**: `src/components/model_management/MATURITY.md`

**Purpose**: AI model selection, monitoring, and fallback management

**Key Features**:
- Multi-provider support (OpenAI, Anthropic, OpenRouter)
- Model selection strategies
- Performance monitoring
- Automatic fallback
- Cost tracking

**Dependencies**: None (foundational for AI systems)

**Promotion Readiness**:
- [ ] Ready for Staging
- Blockers: Test coverage, integration tests, documentation

---

### 7. Narrative Arc Orchestrator
**Component ID**: `component:narrative-arc-orchestrator`
**Current Stage**: Development
**Owner**: theinterneti
**Location**: `src/components/narrative_arc_orchestrator/`
**MATURITY.md**: `src/components/narrative_arc_orchestrator/MATURITY.md`

**Purpose**: Manages narrative arcs, conflict detection, and story progression

**Key Features**:
- Causal graph management
- Conflict detection
- Impact analysis
- Resolution engine
- Scale management

**Dependencies**:
- Neo4j (Development)
- LLM (Development)
- Narrative Coherence (Development)

**Promotion Readiness**:
- [ ] Ready for Staging
- Blockers: Test coverage, integration tests, documentation

---

## Player Experience Components

### 8. Player Experience
**Component ID**: `component:player-experience-api` / `component:player-experience-frontend`
**Current Stage**: Development
**Owner**: theinterneti
**Location**: `src/components/player_experience_component.py`
**MATURITY.md**: `src/components/MATURITY.md` (Player Experience)

**Purpose**: Player-facing web interface and API

**Key Features**:
- Web-based UI
- RESTful API
- Session management
- Real-time updates
- OAuth authentication

**Dependencies**:
- Neo4j (Development)
- Gameplay Loop (Development)
- Agent Orchestration (Development)

**Promotion Readiness**:
- [ ] Ready for Staging
- Blockers: E2E tests, UI/UX validation, documentation

---

### 9. Gameplay Loop
**Component ID**: `component:gameplay-loop`
**Current Stage**: Development
**Owner**: theinterneti
**Location**: `src/components/gameplay_loop/`
**MATURITY.md**: `src/components/gameplay_loop/MATURITY.md`

**Purpose**: Core gameplay mechanics and turn-based interaction

**Key Features**:
- Turn-based gameplay
- Choice architecture
- Consequence system
- Narrative progression
- Session state management

**Dependencies**:
- Neo4j (Development)
- Narrative Arc Orchestrator (Development)
- Therapeutic Systems (Development)

**Promotion Readiness**:
- [ ] Ready for Staging
- Blockers: Test coverage, integration tests, documentation

---

### 10. Character Arc Manager
**Component ID**: `component:character-management`
**Current Stage**: Development
**Owner**: theinterneti
**Location**: `src/components/character_arc_manager.py`
**MATURITY.md**: `src/components/MATURITY.md` (Character Arc Manager)

**Purpose**: Dynamic character development and relationship evolution

**Key Features**:
- Character arc tracking
- Relationship management
- Personality consistency
- Milestone resolution
- Character development

**Dependencies**:
- Neo4j (Development)
- LLM (Development)
- Narrative Arc Orchestrator (Development)

**Promotion Readiness**:
- [ ] Ready for Staging
- Blockers: Test coverage, integration tests, documentation

---

## Therapeutic Content Components

### 11. Therapeutic Systems
**Component ID**: `component:therapeutic-systems`
**Current Stage**: Development
**Owner**: theinterneti
**Location**: `src/components/therapeutic_systems_enhanced/`
**MATURITY.md**: `src/components/therapeutic_systems_enhanced/MATURITY.md`

**Purpose**: Therapeutic frameworks and safety systems

**Key Features**:
- Emotional safety system
- Adaptive difficulty engine
- Character development system
- Collaborative system
- Consequence system
- Error recovery manager
- Therapeutic integration

**Dependencies**:
- Neo4j (Development)
- Narrative Coherence (Development)
- Gameplay Loop (Development)

**Promotion Readiness**:
- [ ] Ready for Staging
- Blockers: Clinical validation, test coverage, documentation

---

### 12. Narrative Coherence
**Component ID**: `component:narrative-coherence`
**Current Stage**: Development
**Owner**: theinterneti
**Location**: `src/components/narrative_coherence/`
**MATURITY.md**: `src/components/narrative_coherence/MATURITY.md`

**Purpose**: Ensures narrative consistency and coherence

**Key Features**:
- Causal validation
- Coherence validation
- Contradiction detection
- Rule-based validation
- Narrative models

**Dependencies**:
- Neo4j (Development)
- Narrative Arc Orchestrator (Development)

**Promotion Readiness**:
- [ ] Ready for Staging
- Blockers: Test coverage, integration tests, documentation

---

## Dependency Graph

```
Core Infrastructure (No dependencies)
├── Neo4j
├── Docker
└── Carbon

AI/Agent Systems (Depends on Core Infrastructure)
├── Model Management
├── LLM → Model Management
├── Agent Orchestration → LLM, Model Management
└── Narrative Arc Orchestrator → Neo4j, LLM, Narrative Coherence

Player Experience (Depends on Core + AI/Agent)
├── Gameplay Loop → Neo4j, Narrative Arc Orchestrator, Therapeutic Systems
├── Character Arc Manager → Neo4j, LLM, Narrative Arc Orchestrator
└── Player Experience → Neo4j, Gameplay Loop, Agent Orchestration

Therapeutic Content (Depends on Core + AI/Agent)
├── Narrative Coherence → Neo4j, Narrative Arc Orchestrator
└── Therapeutic Systems → Neo4j, Narrative Coherence, Gameplay Loop
```

---

## Promotion Strategy

### Phase 1: Core Infrastructure (Weeks 1-2)
**Goal**: Establish stable foundation

**Components**:
1. Neo4j → Staging
2. Docker → Staging
3. Carbon → Staging (after analysis)

**Success Criteria**: All core infrastructure in staging with ≥99.5% uptime

---

### Phase 2: AI/Agent Systems (Weeks 3-5)
**Goal**: Enable AI-powered storytelling

**Components**:
1. Model Management → Staging
2. LLM → Staging
3. Agent Orchestration → Staging
4. Narrative Arc Orchestrator → Staging

**Success Criteria**: AI systems functional in staging with acceptable performance

---

### Phase 3: Player Experience (Weeks 6-8)
**Goal**: Enable player interaction

**Components**:
1. Gameplay Loop → Staging
2. Character Arc Manager → Staging
3. Player Experience → Staging

**Success Criteria**: Complete player journey functional in staging

---

### Phase 4: Therapeutic Content (Weeks 9-10)
**Goal**: Enable therapeutic features

**Components**:
1. Narrative Coherence → Staging
2. Therapeutic Systems → Staging

**Success Criteria**: Therapeutic features validated in staging

---

### Phase 5: Production Promotion (Weeks 11-12)
**Goal**: Promote stable components to production

**Strategy**: Promote components incrementally based on 7-day staging validation

---

## Next Actions

### Immediate (This Week)
- [ ] Review and customize all MATURITY.md files
- [ ] Add all components to GitHub Project board
- [ ] Create initial promotion milestones
- [ ] Identify first promotion candidates (likely Neo4j, Docker)

### Short-term (Next 2 Weeks)
- [ ] Begin Phase 1: Core Infrastructure promotion
- [ ] Increase test coverage for all components
- [ ] Complete component documentation
- [ ] Set up monitoring for staging environment

### Medium-term (Next Month)
- [ ] Complete Phase 1 and Phase 2 promotions
- [ ] Begin Phase 3: Player Experience promotion
- [ ] Establish regular promotion review cadence

---

## Related Documentation

- [[TTA/Components/COMPONENT_MATURITY_WORKFLOW|Component Maturity Workflow]]
- [[TTA/Components/COMPONENT_PROMOTION_GUIDE|Component Promotion Guide]]
- [[TTA/Components/COMPONENT_LABELS_GUIDE|Component Labels Guide]]
- [[TTA/Components/GITHUB_PROJECT_SETUP|GitHub Project Setup]]


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___components___docs development component inventory document]]
