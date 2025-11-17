# TTA Rebuild

**Therapeutic Through Artistry** - AI-powered collaborative storytelling with therapeutic benefits

## Overview

TTA is a rogue-like collaborative storytelling game that combines:

- **High-Quality Narrative**: AI-generated stories comparable to the best narrative media
- **Therapeutic Integration**: Subtle incorporation of narrative therapy principles
- **Player Agency**: Complete control over therapeutic content engagement
- **System-Agnostic Design**: Adaptable to any RPG rule system

## Architecture

TTA is built on three core pillars:

### 1. Narrative Generation Engine

5 primitives for generating high-quality narrative content:

- `StoryGeneratorPrimitive` - Generate narrative scenes
- `SceneComposerPrimitive` - Compose cohesive scenes
- `CharacterDevelopmentPrimitive` - Develop character arcs
- `CoherenceValidatorPrimitive` - Ensure narrative consistency
- `UniverseManagerPrimitive` - Manage multiverse timelines

### 2. Game System Architecture

System-agnostic game mechanics:

- Dual progression system (narrative + therapeutic)
- Rogue-like mechanics with permadeath
- Collaborative storytelling patterns
- Dynamic rule system adaptation

### 3. Therapeutic Integration

3 primitives for optional therapeutic benefits:

- `TherapeuticContentPrimitive` - Theme integration (externalization, re-authoring)
- `EmotionalResonancePrimitive` - Content warnings, boundary enforcement
- `ReflectionPacingPrimitive` - Optional reflection, gentle pacing

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/theinterneti/TTA.dev.git
cd TTA.dev/packages/tta-rebuild

# Install with uv (recommended)
uv sync --all-extras

# Or with pip
pip install -e ".[dev]"
```

### Basic Usage

```python
from tta_rebuild.narrative import StoryGeneratorPrimitive
from tta_rebuild.core import TTAContext
from datetime import datetime

# Initialize LLM provider
from tta_rebuild.integrations import AnthropicProvider
llm = AnthropicProvider(api_key="your-key")

# Create story generator
story_generator = StoryGeneratorPrimitive(llm)

# Create context
context = TTAContext(
    workflow_id="session-001",
    correlation_id="request-123",
    timestamp=datetime.now(),
    metaconcepts=["Ensure Narrative Quality", "Prioritize Player Agency"],
    player_boundaries={},
    session_state={},
    universe_id="universe-001"
)

# Generate story
from tta_rebuild.narrative.story_generator import StoryGenerationInput

input_data = StoryGenerationInput(
    theme="overcoming fear",
    universe_id="universe-001",
    timeline_position=0,
    active_characters=[],
    previous_context="",
    player_preferences={"tone": "hopeful"},
    narrative_style="cinematic"
)

story = await story_generator.execute(input_data, context)
print(story.narrative_text)
```

## Development

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=src/tta_rebuild --cov-report=html

# Specific category
uv run pytest tests/narrative/ -v
```

### Type Checking

```bash
uvx pyright src/
```

### Linting

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```

## Design Principles

### Metaconcept System

TTA uses **metaconcepts** - high-level AI guidance principles that shape behavior without being prescriptive:

**Therapeutic Metaconcepts:**
- "Support Therapeutic Goals" - Subtly integrate therapeutic themes
- "Promote Self-Compassion" - Emphasize self-acceptance
- "Prioritize Player Agency" - Never force therapeutic content

**Narrative Metaconcepts:**
- "Ensure Narrative Quality" - Stories comparable to best media
- "Maintain Chronology" - Track timeline consistency

**Safety Metaconcepts:**
- "Respect Player Boundaries" - Honor content preferences
- "Provide Content Warnings" - Warn about triggering content

### Trauma-Informed Design

TTA follows trauma-informed principles:

- **Safety First**: Content warnings and skip options
- **Player Control**: All therapeutic content optional
- **Gentle Pacing**: No forced reflection or rushed processing
- **Boundary Respect**: Granular content preferences
- **Validation**: Non-judgmental narrative responses

### Not Clinical Therapy

⚠️ **Important**: TTA is NOT a replacement for clinical therapy. It:

- Provides optional exposure to therapeutic storytelling patterns
- Allows safe exploration of themes at player's pace
- Respects boundaries and player agency
- Should complement, not replace, professional mental health support

## Architecture Details

### Core Infrastructure

- **TTAPrimitive**: Base class for all primitives (Generic[TInput, TOutput])
- **TTAContext**: Context passed through all operations
- **MetaconceptRegistry**: Registry of all metaconcepts

### LLM Integration

- Supports OpenAI, Anthropic, local models
- Async-first design
- Prompt engineering with metaconcept guidance
- Quality assessment and validation

### Knowledge Graph (Neo4j)

- Stores Concepts, Metaconcepts, Characters, Locations
- Tracks narrative consistency across universes
- Enables "Echoes of the Self" (recurring themes)

### Observability

- OpenTelemetry integration
- Structured logging
- Performance metrics
- Distributed tracing

## Documentation

- **Specifications**: `docs/planning/tta-analysis/specs/`
  - Narrative Generation Engine Spec
  - Game System Architecture Spec
  - Therapeutic Integration Spec
- **Guiding Principles**: `docs/planning/tta-analysis/TTA_GUIDING_PRINCIPLES.md`
- **Research Foundation**: `docs/planning/tta-analysis/research-extracts/`

## Contributing

See `CONTRIBUTING.md` in the root repository.

## License

MIT License - See `LICENSE` file

## Status

🚧 **Alpha Development** - Active implementation in progress

- ✅ All three pillar specifications complete
- 🚧 Week 1: Core infrastructure implementation
- 📅 Week 2-4: Full primitive implementation

## Contact

- Repository: https://github.com/theinterneti/TTA.dev
- Issues: https://github.com/theinterneti/TTA.dev/issues

---

**Built with TTA.dev primitives** - Production-ready AI workflow components
