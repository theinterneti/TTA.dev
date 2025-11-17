# TTA Rebuild - Next Session Implementation Plan

**Date:** November 8, 2025  
**Status:** ✅ All 3 Pillar Specifications Complete  
**Next Phase:** Week 1 Implementation Begins  
**Target Dates:** November 11-15, 2025

---

## 🎉 MILESTONE: Three Pillar Specs Complete

### ✅ Pillar 1: Narrative Generation Engine

- **Location:** `docs/planning/tta-analysis/specs/NARRATIVE_GENERATION_ENGINE_SPEC.md`
- **Size:** 635 lines
- **Primitives:** 5 core primitives
- **Status:** Production-ready ✅

### ✅ Pillar 2: Game System Architecture

- **Location:** `docs/planning/tta-analysis/specs/GAME_SYSTEM_ARCHITECTURE_SPEC.md`
- **Primitives:** Dual progression, rogue-like mechanics
- **Status:** Production-ready ✅

### ✅ Pillar 3: Therapeutic Integration

- **Location:** `docs/planning/tta-analysis/specs/THERAPEUTIC_INTEGRATION_SPEC.md`
- **Size:** 1,367 lines (JUST COMPLETED! 🎉)
- **Primitives:** 3 therapeutic primitives
- **Status:** Production-ready ✅

---

## 📋 Next Session: Week 1 Implementation (3-4 hours)

### 🎯 Session Goal

Build TTA foundation with:

1. Package structure
2. Core infrastructure
3. First working primitive
4. Testing framework

**Deliverable:** Working prototype with StoryGeneratorPrimitive functional

---

## 🏗️ Implementation Steps

### Step 1: Package Setup (30-45 min)

**Create `packages/tta-rebuild/` structure:**

```bash
packages/tta-rebuild/
├── pyproject.toml
├── README.md
├── src/tta_rebuild/
│   ├── __init__.py
│   ├── narrative/              # Pillar 1
│   │   ├── story_generator.py
│   │   ├── scene_composer.py
│   │   └── ...
│   ├── game/                   # Pillar 2
│   │   ├── progression.py
│   │   └── ...
│   ├── therapeutic/            # Pillar 3
│   │   ├── therapeutic_content.py
│   │   └── ...
│   ├── core/                   # Shared
│   │   ├── base_primitive.py
│   │   ├── context.py
│   │   └── metaconcepts.py
│   └── integrations/           # External
│       ├── llm_provider.py
│       └── neo4j_client.py
└── tests/
    ├── narrative/
    ├── game/
    └── therapeutic/
```

**Tasks:**

- [ ] Create directory structure
- [ ] Write `pyproject.toml` with dependencies (openai, neo4j, pydantic, pytest-asyncio)
- [ ] Add to workspace `uv` configuration
- [ ] Initialize README.md

### Step 2: Core Infrastructure (45-60 min)

**Implement base primitive:**

```python
# src/tta_rebuild/core/base_primitive.py

from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime

TInput = TypeVar('TInput')
TOutput = TypeVar('TOutput')

@dataclass
class TTAContext:
    """Context passed through all TTA primitives."""
    workflow_id: str
    correlation_id: str
    timestamp: datetime
    metaconcepts: list[str]
    player_boundaries: dict
    session_state: dict
    universe_id: str | None = None

class TTAPrimitive(ABC, Generic[TInput, TOutput]):
    """Base class for all TTA primitives."""
    
    async def execute(
        self, 
        input_data: TInput, 
        context: TTAContext
    ) -> TOutput:
        """Execute the primitive."""
        pass
```

**Implement metaconcept registry:**

```python
# src/tta_rebuild/core/metaconcepts.py

from enum import Enum
from dataclasses import dataclass

class MetaconceptCategory(Enum):
    THERAPEUTIC = "therapeutic"
    NARRATIVE = "narrative"
    SAFETY = "safety"

@dataclass
class Metaconcept:
    name: str
    category: MetaconceptCategory
    description: str
    scope: list[str]

class MetaconceptRegistry:
    """Registry of all TTA metaconcepts."""
    
    THERAPEUTIC = [
        Metaconcept(
            "Support Therapeutic Goals",
            MetaconceptCategory.THERAPEUTIC,
            "Integrate therapeutic themes subtly",
            ["therapeutic", "narrative"]
        ),
        # ... more metaconcepts
    ]
    
    @classmethod
    def get_for_primitive(cls, primitive_type: str) -> list[Metaconcept]:
        """Get applicable metaconcepts."""
        pass
```

**Tasks:**

- [ ] Implement `TTAPrimitive` base class
- [ ] Create `TTAContext` dataclass
- [ ] Build `MetaconceptRegistry` with all metaconcepts
- [ ] Write unit tests

### Step 3: First Primitive - StoryGeneratorPrimitive (60-90 min)

**Implement from Narrative Generation Engine spec:**

```python
# src/tta_rebuild/narrative/story_generator.py

from dataclasses import dataclass
from tta_rebuild.core.base_primitive import TTAPrimitive, TTAContext

@dataclass
class StoryGenerationInput:
    """Input for story generation."""
    theme: str
    universe_id: str
    timeline_position: int
    active_characters: list[dict]
    previous_context: str
    player_preferences: dict
    narrative_style: str

@dataclass
class GeneratedStory:
    """Output from story generation."""
    scene_id: str
    narrative_text: str
    dialogue: list[dict]
    setting_description: str
    emotional_tone: str
    story_branches: list[str]
    quality_score: float

class StoryGeneratorPrimitive(TTAPrimitive[StoryGenerationInput, GeneratedStory]):
    """Generates high-quality narrative content."""
    
    def __init__(self, llm_provider):
        super().__init__("StoryGenerator")
        self.llm = llm_provider
    
    async def execute(
        self,
        input_data: StoryGenerationInput,
        context: TTAContext
    ) -> GeneratedStory:
        """Generate narrative with metaconcept guidance."""
        
        # Get metaconcepts
        metaconcepts = MetaconceptRegistry.get_for_primitive("narrative")
        
        # Build LLM prompt
        prompt = self._build_prompt(input_data, metaconcepts, context)
        
        # Generate story
        response = await self.llm.generate(prompt)
        
        # Parse and structure
        story = self._parse_response(response, input_data, context)
        
        # Assess quality
        story.quality_score = await self._assess_quality(story, context)
        
        return story
    
    def _build_prompt(self, input_data, metaconcepts, context) -> str:
        """Build LLM prompt with metaconcept guidance."""
        # Implementation
        pass
```

**Tasks:**

- [ ] Implement input/output dataclasses
- [ ] Create LLM integration layer
- [ ] Implement story generation logic
- [ ] Add metaconcept prompt engineering
- [ ] Write comprehensive tests

### Step 4: Testing Infrastructure (30-45 min)

**Set up pytest with async support:**

```python
# tests/narrative/test_story_generator.py

import pytest
from tta_rebuild.narrative.story_generator import (
    StoryGeneratorPrimitive,
    StoryGenerationInput
)
from tta_rebuild.core.base_primitive import TTAContext

@pytest.fixture
def sample_context():
    """Sample TTA context."""
    return TTAContext(
        workflow_id="test_workflow",
        correlation_id="test-123",
        timestamp=datetime.now(),
        metaconcepts=["Ensure Narrative Quality"],
        player_boundaries={},
        session_state={},
        universe_id="test_universe"
    )

@pytest.mark.asyncio
async def test_story_generation_basic(sample_context):
    """Test basic story generation."""
    primitive = StoryGeneratorPrimitive(mock_llm)
    
    input_data = StoryGenerationInput(
        theme="overcoming fear",
        universe_id="test_universe",
        timeline_position=0,
        active_characters=[],
        previous_context="",
        player_preferences={},
        narrative_style="cinematic"
    )
    
    result = await primitive.execute(input_data, sample_context)
    
    assert result.narrative_text
    assert result.quality_score > 0.7
    assert len(result.story_branches) >= 2
```

**Tasks:**

- [ ] Set up pytest configuration
- [ ] Create test fixtures
- [ ] Write unit tests for StoryGeneratorPrimitive
- [ ] Configure coverage reporting (>80%)

---

## 📊 Success Criteria

**Infrastructure Complete:**

- [ ] Package structure created
- [ ] Added to workspace `uv` configuration
- [ ] Core base classes implemented
- [ ] Metaconcept registry functional

**First Primitive Working:**

- [ ] `StoryGeneratorPrimitive` implemented
- [ ] LLM integration layer functional
- [ ] Unit tests passing (>80% coverage)
- [ ] Metaconcepts applied in prompts

**Documentation:**

- [ ] Package README with quick start
- [ ] API documentation for core classes
- [ ] Usage examples for StoryGeneratorPrimitive

**Quality:**

- [ ] All tests passing
- [ ] Type hints complete
- [ ] Linting clean (ruff)
- [ ] No blocking issues

---

## 🔧 Technical Decisions Needed

**During next session, decide:**

1. **LLM Provider:** OpenAI GPT-4 / Anthropic Claude / Local model
   - **Recommendation:** Start with Anthropic Claude

2. **Neo4j Integration:** Real Neo4j / Mock in-memory
   - **Recommendation:** Mock for Week 1, real for Week 2+

3. **Async Framework:** Pure asyncio / Additional framework
   - **Recommendation:** Pure asyncio

4. **Testing Strategy:** Mock LLM calls / Real API with fixtures
   - **Recommendation:** Mock for unit tests, real API for integration tests

---

## 📚 Reference Materials

### Specifications (Read First)

- **Narrative Engine:** `docs/planning/tta-analysis/specs/NARRATIVE_GENERATION_ENGINE_SPEC.md`
- **Game System:** `docs/planning/tta-analysis/specs/GAME_SYSTEM_ARCHITECTURE_SPEC.md`
- **Therapeutic:** `docs/planning/tta-analysis/specs/THERAPEUTIC_INTEGRATION_SPEC.md`
- **Guiding Principles:** `docs/planning/tta-analysis/TTA_GUIDING_PRINCIPLES.md`

### TTA.dev Patterns

- Type Safety: Python 3.11+ type hints
- Async-First: All primitives async
- Composition: Build complex from simple
- Testability: 100% coverage target

---

## 💡 Quick Start Commands

```bash
# Create structure
mkdir -p packages/tta-rebuild/src/tta_rebuild/{narrative,game,therapeutic,core,integrations}
mkdir -p packages/tta-rebuild/tests/{narrative,game,therapeutic}

# Initialize
cd packages/tta-rebuild
uv init

# Install dependencies
uv add openai anthropic neo4j pydantic pytest pytest-asyncio

# Run tests
uv run pytest -v

# Type check
uvx pyright packages/tta-rebuild/

# Lint
uv run ruff check packages/tta-rebuild/
```

---

## 🎯 Ready to Begin

**Status:** ✅ All specifications complete  
**Next Action:** Create package structure and begin implementation  
**Timeline:** Week 1 (Nov 11-15, 2025)  
**Duration:** 3-4 hours for next session

**Let's build TTA! 🚀**
