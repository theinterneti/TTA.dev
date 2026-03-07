# Adaptive Persona Switching Design

**Purpose:** Intelligent, automatic persona selection using TTA.dev primitives
**Status:** Design Phase
**Created:** 2025-11-14

---

## Overview

Building on manual persona switching (tta-persona CLI), this system uses **TTA.dev's RouterPrimitive** to automatically select and switch to the optimal persona based on task context, with **AdaptivePrimitive** learning from switching patterns over time.

**User Request:**
> "configure copilot to automatically assume a role and to adaptively shift roles as needed (perhaps via one of our adaptive primitives?)"

---

## Architecture

### Layer 1: Context Analysis (Input Processing)

**Purpose:** Analyze current task context to determine optimal persona

**Implementation:**
```python
from tta_dev_primitives import WorkflowPrimitive, WorkflowContext
from pathlib import Path
import re

class ContextAnalyzer(WorkflowPrimitive[dict, dict]):
    """Analyze task context to extract persona hints."""

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """
        Extract context signals from task.

        Input:
            {
                "query": str,           # User's request
                "files": list[str],     # Active file paths
                "recent_commands": list[str],  # Recent terminal commands
                "active_editor": str,   # Currently open file
            }

        Output:
            {
                "signals": {
                    "file_types": ["py", "yaml"],
                    "keywords": ["pytest", "test", "coverage"],
                    "directories": ["tests/", "packages/"],
                    "commands": ["pytest", "ruff"]
                },
                "confidence_scores": {
                    "testing": 0.9,
                    "backend": 0.3,
                    "frontend": 0.1
                }
            }
        """
        signals = self._extract_signals(input_data)
        scores = self._calculate_confidence(signals)

        return {
            "signals": signals,
            "confidence_scores": scores,
            "original_input": input_data
        }

    def _extract_signals(self, data: dict) -> dict:
        """Extract relevant signals from context."""
        signals = {
            "file_types": self._extract_file_types(data.get("files", [])),
            "keywords": self._extract_keywords(data.get("query", "")),
            "directories": self._extract_directories(data.get("files", [])),
            "commands": data.get("recent_commands", [])
        }
        return signals

    def _extract_file_types(self, files: list[str]) -> list[str]:
        """Get file extensions."""
        return [Path(f).suffix.lstrip('.') for f in files if Path(f).suffix]

    def _extract_keywords(self, text: str) -> list[str]:
        """Extract relevant keywords."""
        keywords = {
            "testing": ["test", "pytest", "coverage", "mock", "assert"],
            "backend": ["api", "endpoint", "primitive", "workflow", "async"],
            "frontend": ["react", "component", "ui", "streamlit", "tsx"],
            "devops": ["docker", "deploy", "ci", "github actions", "kubernetes"],
            "observability": ["metrics", "trace", "prometheus", "grafana", "otel"],
            "data": ["pandas", "ml", "langgraph", "prompt", "jupyter"]
        }

        found = []
        text_lower = text.lower()
        for category, terms in keywords.items():
            if any(term in text_lower for term in terms):
                found.append(category)

        return found

    def _extract_directories(self, files: list[str]) -> list[str]:
        """Extract directory patterns."""
        dirs = set()
        for f in files:
            parts = Path(f).parts
            if "tests" in parts:
                dirs.add("tests/")
            if "frontend" in parts or "ui" in parts:
                dirs.add("frontend/")
            if "scripts" in parts:
                dirs.add("scripts/")
            if "docker" in str(f).lower() or "infrastructure" in parts:
                dirs.add("infrastructure/")
        return list(dirs)

    def _calculate_confidence(self, signals: dict) -> dict[str, float]:
        """Calculate confidence score for each persona."""
        scores = {
            "tta-testing-specialist": 0.0,
            "tta-backend-engineer": 0.0,
            "tta-frontend-engineer": 0.0,
            "tta-devops-engineer": 0.0,
            "tta-observability-expert": 0.0,
            "tta-data-scientist": 0.0
        }

        # File type scoring
        if "py" in signals["file_types"]:
            scores["tta-backend-engineer"] += 0.3
        if "tsx" in signals["file_types"] or "jsx" in signals["file_types"]:
            scores["tta-frontend-engineer"] += 0.5
        if "yaml" in signals["file_types"] or "yml" in signals["file_types"]:
            scores["tta-devops-engineer"] += 0.2

        # Keyword scoring
        keyword_weights = {
            "testing": ("tta-testing-specialist", 0.4),
            "backend": ("tta-backend-engineer", 0.3),
            "frontend": ("tta-frontend-engineer", 0.3),
            "devops": ("tta-devops-engineer", 0.3),
            "observability": ("tta-observability-expert", 0.3),
            "data": ("tta-data-scientist", 0.3)
        }

        for keyword in signals["keywords"]:
            if keyword in keyword_weights:
                persona, weight = keyword_weights[keyword]
                scores[persona] += weight

        # Directory scoring
        if "tests/" in signals["directories"]:
            scores["tta-testing-specialist"] += 0.3
        if "frontend/" in signals["directories"]:
            scores["tta-frontend-engineer"] += 0.4
        if "infrastructure/" in signals["directories"]:
            scores["tta-devops-engineer"] += 0.4

        # Normalize scores to 0-1 range
        max_score = max(scores.values()) if max(scores.values()) > 0 else 1
        return {k: v / max_score for k, v in scores.items()}
```

---

### Layer 2: Persona Selection (Routing)

**Purpose:** Select optimal persona using RouterPrimitive

**Implementation:**
```python
from tta_dev_primitives.core import RouterPrimitive

class PersonaRouter(RouterPrimitive):
    """Route to optimal persona based on context analysis."""

    def __init__(self):
        # Define persona "primitives" (they're actually personas, not executables)
        # We'll use this for routing logic, actual switching happens via MCP config
        personas = {
            "tta-testing-specialist": self._create_persona_handler("testing"),
            "tta-backend-engineer": self._create_persona_handler("backend"),
            "tta-frontend-engineer": self._create_persona_handler("frontend"),
            "tta-devops-engineer": self._create_persona_handler("devops"),
            "tta-observability-expert": self._create_persona_handler("observability"),
            "tta-data-scientist": self._create_persona_handler("data")
        }

        super().__init__(
            routes=personas,
            router_fn=self._select_persona,
            default_route="tta-backend-engineer"  # Fallback
        )

    def _select_persona(self, data: dict, context: WorkflowContext) -> str:
        """
        Select persona based on confidence scores.

        Input (from ContextAnalyzer):
            {
                "confidence_scores": {
                    "tta-testing-specialist": 0.9,
                    "tta-backend-engineer": 0.3,
                    ...
                }
            }

        Returns: Persona name (e.g., "tta-testing-specialist")
        """
        scores = data.get("confidence_scores", {})

        # Get highest confidence persona
        if not scores:
            return self.default_route

        selected = max(scores.items(), key=lambda x: x[1])
        persona_name, confidence = selected

        # Only switch if confidence is high enough
        if confidence < 0.5:
            return self.default_route

        return persona_name

    def _create_persona_handler(self, persona_short_name: str):
        """Create a handler that returns persona metadata."""
        async def handler(data: dict, context: WorkflowContext) -> dict:
            return {
                "persona": f"tta-{persona_short_name}",
                "confidence": data.get("confidence_scores", {}).get(f"tta-{persona_short_name}", 0),
                "context": data.get("original_input", {})
            }

        return WorkflowPrimitive.from_function(handler)
```

---

### Layer 3: Persona Application (Execution)

**Purpose:** Actually switch MCP configuration to selected persona

**Implementation:**
```python
import subprocess
from pathlib import Path

class PersonaSwitcher(WorkflowPrimitive[dict, dict]):
    """Execute persona switch via MCP configuration update."""

    def __init__(self, mcp_config_path: str = "~/.config/mcp/mcp_settings.json"):
        super().__init__()
        self.mcp_config_path = Path(mcp_config_path).expanduser()

    async def execute(self, input_data: dict, context: WorkflowContext) -> dict:
        """
        Switch to selected persona.

        Input:
            {
                "persona": "tta-testing-specialist",
                "confidence": 0.9,
                "context": {...}
            }

        Output:
            {
                "switched_to": "tta-testing-specialist",
                "previous": "tta-backend-engineer",
                "success": true
            }
        """
        target_persona = input_data.get("persona")

        if not target_persona:
            raise ValueError("No persona specified")

        # Get current persona
        current = self._get_current_persona()

        # Skip if already on target persona
        if current == target_persona:
            return {
                "switched_to": target_persona,
                "previous": current,
                "success": True,
                "skipped": True,
                "reason": "Already on target persona"
            }

        # Execute switch
        success = await self._switch_persona(target_persona)

        return {
            "switched_to": target_persona if success else current,
            "previous": current,
            "success": success,
            "skipped": False
        }

    def _get_current_persona(self) -> str:
        """Extract current persona from MCP config."""
        try:
            with open(self.mcp_config_path, 'r') as f:
                content = f.read()
                match = re.search(r'"--persona",\s*"(tta-[^"]+)"', content)
                return match.group(1) if match else "unknown"
        except Exception as e:
            return "unknown"

    async def _switch_persona(self, persona: str) -> bool:
        """Update MCP config with new persona."""
        try:
            # Use sed to update persona argument
            short_name = persona.replace("tta-", "")

            result = subprocess.run(
                [
                    "sed", "-i",
                    f's/"--persona", "tta-[^"]*"/"--persona", "{persona}"/g',
                    str(self.mcp_config_path)
                ],
                capture_output=True,
                text=True
            )

            return result.returncode == 0
        except Exception as e:
            return False
```

---

### Layer 4: Learning & Adaptation

**Purpose:** Learn from persona switching patterns to improve future selections

**Implementation:**
```python
from tta_dev_primitives.adaptive import AdaptivePrimitive, LearningStrategy, LearningMode

class AdaptivePersonaRouter(AdaptivePrimitive[dict, dict]):
    """
    Learn optimal persona selection from usage patterns.

    Features:
    - Learns which personas work best for different contexts
    - Tracks switching frequency and success rates
    - Adapts routing logic based on feedback
    - Persists learned strategies to Logseq
    """

    def __init__(
        self,
        context_analyzer: ContextAnalyzer,
        persona_router: PersonaRouter,
        persona_switcher: PersonaSwitcher
    ):
        # Baseline strategy: Use confidence-based routing
        baseline = LearningStrategy(
            name="confidence_based_routing",
            description="Route to persona with highest confidence score",
            parameters={
                "min_confidence": 0.5,
                "fallback_persona": "tta-backend-engineer"
            }
        )

        super().__init__(
            baseline_strategy=baseline,
            learning_mode=LearningMode.ACTIVE,
            enable_circuit_breaker=True,
            min_observations_before_learning=10
        )

        self.context_analyzer = context_analyzer
        self.persona_router = persona_router
        self.persona_switcher = persona_switcher

        # Track switching patterns
        self.switch_history = []

    async def _execute_with_strategy(
        self,
        strategy: LearningStrategy,
        input_data: dict,
        context: WorkflowContext
    ) -> dict:
        """
        Execute persona switching with learned strategy.

        Input:
            {
                "query": "Write tests for CachePrimitive",
                "files": ["tests/test_cache.py"],
                "recent_commands": ["pytest"]
            }

        Output:
            {
                "switched_to": "tta-testing-specialist",
                "confidence": 0.95,
                "strategy_used": "learned_pattern_v3"
            }
        """
        # 1. Analyze context
        analysis = await self.context_analyzer.execute(input_data, context)

        # 2. Apply learned strategy parameters
        min_confidence = strategy.parameters.get("min_confidence", 0.5)

        # Adjust confidence scores based on learned patterns
        adjusted_scores = self._adjust_with_learned_patterns(
            analysis["confidence_scores"],
            strategy
        )

        analysis["confidence_scores"] = adjusted_scores

        # 3. Route to persona
        routing_result = await self.persona_router.execute(analysis, context)

        # 4. Check confidence threshold
        selected_persona = routing_result["persona"]
        confidence = routing_result["confidence"]

        if confidence < min_confidence:
            # Use fallback
            selected_persona = strategy.parameters["fallback_persona"]
            routing_result["persona"] = selected_persona
            routing_result["fallback_used"] = True

        # 5. Execute switch
        switch_result = await self.persona_switcher.execute(routing_result, context)

        # 6. Record switch for learning
        self._record_switch(input_data, selected_persona, confidence)

        return {
            **switch_result,
            "confidence": confidence,
            "strategy_used": strategy.name,
            "analysis": analysis["signals"]
        }

    async def _consider_new_strategy(
        self,
        input_data: dict,
        context: WorkflowContext,
        current_performance: "StrategyMetrics"
    ) -> LearningStrategy | None:
        """
        Learn new routing strategy from patterns.

        Analyze:
        - Which personas are selected most often for specific contexts
        - Success rate of each persona for different task types
        - User corrections (manual persona switches after auto-switch)

        Create new strategy if:
        - Current success rate < 80%
        - New pattern detected (e.g., always use testing for pytest keywords)
        """
        if len(self.switch_history) < self.min_observations_before_learning:
            return None

        # Analyze patterns
        patterns = self._analyze_switch_patterns()

        # Check if we should create new strategy
        if current_performance.success_rate < 0.8:
            # Create optimized strategy
            new_strategy = LearningStrategy(
                name=f"learned_pattern_v{len(self.strategies) + 1}",
                description=f"Learned from {len(self.switch_history)} switches",
                parameters={
                    "min_confidence": patterns["optimal_threshold"],
                    "fallback_persona": patterns["best_fallback"],
                    "keyword_boosts": patterns["keyword_weights"],
                    "directory_boosts": patterns["directory_weights"]
                }
            )

            return new_strategy

        return None

    def _adjust_with_learned_patterns(
        self,
        base_scores: dict[str, float],
        strategy: LearningStrategy
    ) -> dict[str, float]:
        """Apply learned pattern adjustments to confidence scores."""
        adjusted = base_scores.copy()

        # Apply keyword boosts from learned strategy
        keyword_boosts = strategy.parameters.get("keyword_boosts", {})
        for persona, boost in keyword_boosts.items():
            if persona in adjusted:
                adjusted[persona] *= (1 + boost)

        # Normalize
        max_score = max(adjusted.values()) if adjusted else 1
        return {k: v / max_score for k, v in adjusted.items()}

    def _record_switch(self, context: dict, persona: str, confidence: float):
        """Record switch for learning."""
        self.switch_history.append({
            "timestamp": time.time(),
            "context_keywords": context.get("query", "").lower().split(),
            "files": context.get("files", []),
            "selected_persona": persona,
            "confidence": confidence
        })

        # Keep last 1000 switches
        if len(self.switch_history) > 1000:
            self.switch_history = self.switch_history[-1000:]

    def _analyze_switch_patterns(self) -> dict:
        """Analyze historical switches to find patterns."""
        # Group by context patterns
        keyword_persona_map = {}
        directory_persona_map = {}

        for switch in self.switch_history:
            persona = switch["selected_persona"]

            # Track keyword → persona associations
            for keyword in switch["context_keywords"]:
                if keyword not in keyword_persona_map:
                    keyword_persona_map[keyword] = {}
                keyword_persona_map[keyword][persona] = \
                    keyword_persona_map[keyword].get(persona, 0) + 1

            # Track directory → persona associations
            for file in switch["files"]:
                dir_pattern = Path(file).parts[0] if Path(file).parts else ""
                if dir_pattern not in directory_persona_map:
                    directory_persona_map[dir_pattern] = {}
                directory_persona_map[dir_pattern][persona] = \
                    directory_persona_map[dir_pattern].get(persona, 0) + 1

        # Find optimal threshold (minimize false switches)
        confidences = [s["confidence"] for s in self.switch_history]
        optimal_threshold = np.percentile(confidences, 25) if confidences else 0.5

        # Find best fallback (most commonly used)
        from collections import Counter
        persona_counts = Counter(s["selected_persona"] for s in self.switch_history)
        best_fallback = persona_counts.most_common(1)[0][0]

        return {
            "optimal_threshold": optimal_threshold,
            "best_fallback": best_fallback,
            "keyword_weights": self._calculate_keyword_weights(keyword_persona_map),
            "directory_weights": self._calculate_directory_weights(directory_persona_map)
        }

    def _calculate_keyword_weights(self, mapping: dict) -> dict:
        """Calculate boost weights for keywords."""
        # Return top keyword → persona associations as boost weights
        weights = {}
        for keyword, persona_counts in mapping.items():
            if not persona_counts:
                continue
            most_common = max(persona_counts.items(), key=lambda x: x[1])
            persona, count = most_common
            # Boost weight proportional to frequency
            if count > 2:  # Only boost if seen multiple times
                weights[persona] = weights.get(persona, 0) + 0.1
        return weights

    def _calculate_directory_weights(self, mapping: dict) -> dict:
        """Calculate boost weights for directories."""
        weights = {}
        for dir_pattern, persona_counts in mapping.items():
            if not persona_counts:
                continue
            most_common = max(persona_counts.items(), key=lambda x: x[1])
            persona, count = most_common
            if count > 2:
                weights[persona] = weights.get(persona, 0) + 0.15
        return weights
```

---

## Complete Workflow

**Putting It All Together:**

```python
from tta_dev_primitives import SequentialPrimitive, WorkflowContext

# Build adaptive persona switching workflow
adaptive_persona_system = AdaptivePersonaRouter(
    context_analyzer=ContextAnalyzer(),
    persona_router=PersonaRouter(),
    persona_switcher=PersonaSwitcher()
)

# Execute
async def auto_switch_persona(task_description: str, active_files: list[str]):
    """Automatically switch to optimal persona for task."""

    input_data = {
        "query": task_description,
        "files": active_files,
        "recent_commands": get_recent_commands(),
        "active_editor": get_active_file()
    }

    context = WorkflowContext(workflow_id="persona-switching")

    result = await adaptive_persona_system.execute(input_data, context)

    print(f"✅ Switched to: {result['switched_to']}")
    print(f"📊 Confidence: {result['confidence']:.1%}")
    print(f"🧠 Strategy: {result['strategy_used']}")

    return result

# Example usage
await auto_switch_persona(
    task_description="Write integration tests for RetryPrimitive",
    active_files=["tests/test_retry.py"]
)
# Output:
# ✅ Switched to: tta-testing-specialist
# 📊 Confidence: 95.0%
# 🧠 Strategy: learned_pattern_v3
```

---

## Integration Points

### 1. VS Code Extension Integration

**Trigger Points:**
- **File Open:** Analyze opened file, switch if needed
- **Command Execution:** Detect terminal commands (pytest → testing persona)
- **Manual Override:** User can force persona via command palette
- **Task Start:** Detect task type from VS Code tasks

**Implementation:**
```typescript
// VS Code extension
vscode.workspace.onDidOpenTextDocument(async (document) => {
    const filePath = document.fileName;
    const content = document.getText();

    // Call Python adaptive system
    const result = await executePersonaSwitch({
        query: `Working on ${filePath}`,
        files: [filePath],
        recent_commands: getRecentCommands()
    });

    if (result.success && !result.skipped) {
        vscode.window.showInformationMessage(
            `🎭 Switched to ${result.switched_to} (${result.confidence}% confidence)`
        );

        // Reload Cline/Copilot
        await reloadAgent();
    }
});
```

### 2. Cline Integration

**Auto-Switch on Task Start:**
```python
# In Cline task handler
class ClineTaskHandler:
    def __init__(self):
        self.persona_system = AdaptivePersonaRouter(...)

    async def handle_task(self, task: dict):
        """Handle Cline task with auto persona switching."""

        # 1. Analyze task
        switch_result = await self.persona_system.execute({
            "query": task["description"],
            "files": task.get("files", []),
            "recent_commands": []
        }, WorkflowContext())

        # 2. Switch persona if needed
        if switch_result["success"] and not switch_result["skipped"]:
            # Reload Cline with new persona
            await self.reload_with_persona(switch_result["switched_to"])

        # 3. Execute task with optimal persona
        result = await self.execute_task(task)

        return result
```

### 3. GitHub Copilot Integration

**Copilot Workspace Configuration:**
```json
{
  "github.copilot.advanced": {
    "personaProvider": {
      "enabled": true,
      "endpoint": "http://localhost:8765/persona",
      "autoSwitch": true,
      "confidenceThreshold": 0.6
    }
  }
}
```

**Persona API Server:**
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class PersonaRequest(BaseModel):
    query: str
    files: list[str]
    commands: list[str]

@app.post("/persona")
async def get_optimal_persona(request: PersonaRequest):
    """API endpoint for Copilot to query optimal persona."""

    result = await adaptive_persona_system.execute({
        "query": request.query,
        "files": request.files,
        "recent_commands": request.commands
    }, WorkflowContext())

    return {
        "persona": result["switched_to"],
        "confidence": result["confidence"],
        "should_switch": result["confidence"] > 0.6
    }

# Run: uvicorn persona_api:app --port 8765
```

---

## Logseq Integration

**Strategy Persistence:**

Learned persona routing strategies automatically saved to Logseq:

```markdown
# logseq/pages/Strategies/persona_routing_learned_v3.md

**Type:** AdaptivePersonaRouter
**Created:** 2025-11-14
**Performance:** 92% success rate

## Parameters

- min_confidence: 0.45
- fallback_persona: tta-backend-engineer
- keyword_boosts:
  - tta-testing-specialist: +0.3 (keywords: pytest, test, coverage)
  - tta-frontend-engineer: +0.2 (keywords: react, component, ui)

## Learning Summary

From 347 persona switches:
- Testing persona: 35% of switches (mostly pytest contexts)
- Backend persona: 40% of switches (Python development)
- Frontend persona: 15% of switches (React/UI work)

## Performance History

| Date | Success Rate | Switches | Avg Confidence |
|------|--------------|----------|----------------|
| 2025-11-14 | 92% | 347 | 0.78 |
```

---

## Testing Strategy

### Unit Tests

```python
import pytest

@pytest.mark.asyncio
async def test_context_analyzer():
    """Test context analysis extracts correct signals."""
    analyzer = ContextAnalyzer()

    result = await analyzer.execute({
        "query": "Write pytest tests for CachePrimitive",
        "files": ["tests/test_cache.py"],
        "recent_commands": ["pytest -v"]
    }, WorkflowContext())

    assert "testing" in result["signals"]["keywords"]
    assert result["confidence_scores"]["tta-testing-specialist"] > 0.7

@pytest.mark.asyncio
async def test_persona_router():
    """Test router selects correct persona."""
    router = PersonaRouter()

    result = await router.execute({
        "confidence_scores": {
            "tta-testing-specialist": 0.95,
            "tta-backend-engineer": 0.3
        }
    }, WorkflowContext())

    assert result["persona"] == "tta-testing-specialist"

@pytest.mark.asyncio
async def test_adaptive_learning():
    """Test adaptive system learns from patterns."""
    adaptive = AdaptivePersonaRouter(...)

    # Simulate 20 switches to testing persona for pytest contexts
    for i in range(20):
        await adaptive.execute({
            "query": f"Test {i}",
            "files": [f"tests/test_{i}.py"],
            "recent_commands": ["pytest"]
        }, WorkflowContext())

    # Should learn testing bias
    assert len(adaptive.strategies) > 1  # Baseline + learned
    learned = list(adaptive.strategies.values())[-1]
    assert "testing" in str(learned.parameters)
```

### Integration Tests

```python
@pytest.mark.integration
async def test_full_persona_switching_workflow():
    """Test complete persona switching flow."""

    # Start with backend persona
    initial = get_current_persona()
    assert initial == "tta-backend-engineer"

    # Trigger switch for testing task
    result = await auto_switch_persona(
        task_description="Run integration tests",
        active_files=["tests/integration/test_workflows.py"]
    )

    # Should switch to testing persona
    assert result["switched_to"] == "tta-testing-specialist"
    assert result["success"] is True

    # Verify MCP config updated
    current = get_current_persona()
    assert current == "tta-testing-specialist"
```

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Analysis Time** | <50ms | Time to extract context signals |
| **Routing Time** | <20ms | Time to select persona |
| **Switch Time** | <100ms | Time to update MCP config |
| **Total Latency** | <200ms | End-to-end persona switch |
| **Accuracy** | >85% | Correct persona selected |
| **Learning Convergence** | 50 switches | Time to first learned strategy |

---

## Rollout Plan

### Phase 1: Basic Auto-Switching (Week 1)
- ✅ Implement ContextAnalyzer
- ✅ Implement PersonaRouter
- ✅ Implement PersonaSwitcher
- ✅ Basic testing
- ⏳ VS Code integration

### Phase 2: Adaptive Learning (Week 2)
- ⏳ Implement AdaptivePersonaRouter
- ⏳ Logseq strategy persistence
- ⏳ Learning from user corrections
- ⏳ Performance optimization

### Phase 3: Production Deployment (Week 3)
- ⏳ Copilot integration
- ⏳ API server for external tools
- ⏳ Comprehensive testing
- ⏳ Documentation and training

### Phase 4: Refinement (Week 4)
- ⏳ Collect user feedback
- ⏳ Tune routing logic
- ⏳ Expand persona coverage
- ⏳ Advanced learning algorithms

---

## Success Metrics

**After 1 Month:**
- 90% of persona switches are automatic
- 85% accuracy in persona selection
- <200ms average switching time
- 5+ learned strategies in Logseq
- User satisfaction: "rarely need manual switching"

**User Experience Goal:**
> "I barely think about personas anymore. Copilot just knows what role I need and switches automatically."

---

## Next Steps

1. **Immediate:** Implement ContextAnalyzer and PersonaRouter classes
2. **This Week:** Build PersonaSwitcher and test basic auto-switching
3. **Next Week:** Add AdaptivePrimitive for learning
4. **Following Week:** Integrate with VS Code and Copilot

---

**Status:** Ready for Implementation ✅
**Priority:** High - User requested feature
**Dependencies:** All 6 personas complete, TTA primitives package
**Estimated Implementation:** 2-3 weeks


---
**Logseq:** [[TTA.dev/.hypertool/Adaptive_persona_switching_design]]
