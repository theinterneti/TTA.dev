# Adaptive Persona Switching - Implementation Roadmap

**Status:** Ready to Implement  
**Timeline:** 2-3 weeks  
**Prerequisites:** ✅ All complete (6 personas, Hypertool active, design document ready)

---

## Week 1: Core Components (5-7 days)

### Day 1-2: ContextAnalyzer Implementation

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/persona/context_analyzer.py`

**Tasks:**
1. Create persona package directory
   ```bash
   mkdir -p packages/tta-dev-primitives/src/tta_dev_primitives/persona
   touch packages/tta-dev-primitives/src/tta_dev_primitives/persona/__init__.py
   ```

2. Implement ContextAnalyzer class (from design)
   - `_extract_signals()` - File types, keywords, directories
   - `_extract_file_types()` - Parse file extensions
   - `_extract_keywords()` - Detect persona-relevant terms
   - `_extract_directories()` - Identify directory patterns
   - `_calculate_confidence()` - Score each persona

3. Write tests
   ```python
   # tests/persona/test_context_analyzer.py
   @pytest.mark.asyncio
   async def test_testing_context_detected():
       analyzer = ContextAnalyzer()
       result = await analyzer.execute({
           "query": "Write pytest tests",
           "files": ["tests/test_cache.py"]
       }, WorkflowContext())
       
       assert result["confidence_scores"]["tta-testing-specialist"] > 0.7
   ```

4. Run tests: `uv run pytest tests/persona/ -v`

**Success Criteria:**
- ✅ ContextAnalyzer correctly identifies persona signals
- ✅ Confidence scores range 0-1
- ✅ 100% test coverage
- ✅ Type hints validated with pyright

---

### Day 3-4: PersonaRouter Implementation

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/persona/persona_router.py`

**Tasks:**
1. Implement PersonaRouter class (extends RouterPrimitive)
   - `_select_persona()` - Choose based on confidence scores
   - `_create_persona_handler()` - Return persona metadata
   - Route mapping for all 6 personas

2. Integration with ContextAnalyzer
   ```python
   # Example workflow
   analyzer = ContextAnalyzer()
   router = PersonaRouter()
   
   workflow = analyzer >> router
   result = await workflow.execute(task_data, context)
   # Result: {"persona": "tta-testing-specialist", "confidence": 0.9}
   ```

3. Write tests
   ```python
   @pytest.mark.asyncio
   async def test_router_selects_testing():
       router = PersonaRouter()
       result = await router.execute({
           "confidence_scores": {
               "tta-testing-specialist": 0.95,
               "tta-backend-engineer": 0.3
           }
       }, WorkflowContext())
       
       assert result["persona"] == "tta-testing-specialist"
   ```

4. Test threshold behavior (min confidence 0.5)

**Success Criteria:**
- ✅ Router selects highest confidence persona
- ✅ Falls back to default when confidence <0.5
- ✅ Works with all 6 personas
- ✅ 100% test coverage

---

### Day 5-6: PersonaSwitcher Implementation

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/persona/persona_switcher.py`

**Tasks:**
1. Implement PersonaSwitcher class
   - `_get_current_persona()` - Read from MCP config
   - `_switch_persona()` - Update MCP config with sed
   - Skip if already on target persona

2. Handle MCP config path (~/.config/mcp/mcp_settings.json)

3. Write tests
   ```python
   @pytest.mark.asyncio
   async def test_persona_switch():
       switcher = PersonaSwitcher()
       
       # Mock MCP config
       result = await switcher.execute({
           "persona": "tta-testing-specialist",
           "confidence": 0.9
       }, WorkflowContext())
       
       assert result["success"] is True
       assert result["switched_to"] == "tta-testing-specialist"
   ```

4. Test skip behavior (already on target)

**Success Criteria:**
- ✅ Successfully updates MCP config
- ✅ Detects current persona
- ✅ Skips unnecessary switches
- ✅ <100ms switching time

---

### Day 7: Integration Testing

**File:** `tests/persona/test_integration.py`

**Tasks:**
1. Test complete workflow: Analyze → Route → Switch
   ```python
   @pytest.mark.integration
   async def test_full_persona_switching():
       # Build workflow
       workflow = (
           ContextAnalyzer() >>
           PersonaRouter() >>
           PersonaSwitcher()
       )
       
       # Execute
       result = await workflow.execute({
           "query": "Run pytest tests",
           "files": ["tests/test_cache.py"]
       }, WorkflowContext())
       
       assert result["switched_to"] == "tta-testing-specialist"
       assert result["success"] is True
   ```

2. Test multiple scenarios (backend, frontend, devops, etc.)
3. Measure end-to-end latency (<200ms target)

**Success Criteria:**
- ✅ All integration tests pass
- ✅ End-to-end latency <200ms
- ✅ No errors in real MCP config updates

---

## Week 2: Adaptive Learning (5-7 days)

### Day 8-10: AdaptivePersonaRouter Implementation

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/persona/adaptive_router.py`

**Tasks:**
1. Implement AdaptivePersonaRouter (extends AdaptivePrimitive)
   - `_execute_with_strategy()` - Apply learned patterns
   - `_consider_new_strategy()` - Detect when to learn
   - `_record_switch()` - Track switching history
   - `_analyze_switch_patterns()` - Find patterns in history

2. Implement learning logic
   - Track keyword → persona associations
   - Track directory → persona associations
   - Calculate optimal confidence threshold
   - Identify best fallback persona

3. Write tests
   ```python
   @pytest.mark.asyncio
   async def test_adaptive_learning():
       adaptive = AdaptivePersonaRouter(...)
       
       # Simulate 20 switches to testing
       for i in range(20):
           await adaptive.execute({
               "query": f"Test {i}",
               "files": [f"tests/test_{i}.py"]
           }, WorkflowContext())
       
       # Should learn testing bias
       assert len(adaptive.strategies) > 1
   ```

**Success Criteria:**
- ✅ Learns from switching patterns
- ✅ Creates new strategies after 10+ observations
- ✅ Improves selection accuracy over time
- ✅ Circuit breaker prevents bad strategies

---

### Day 11-12: Logseq Integration

**File:** `packages/tta-dev-primitives/src/tta_dev_primitives/persona/logseq_strategy_persistence.py`

**Tasks:**
1. Create LogseqStrategyPersistence class
   - `save_learned_strategy()` - Save to Logseq
   - `update_strategy_performance()` - Update metrics
   - `load_strategies()` - Restore from Logseq

2. Implement file generation
   ```markdown
   # logseq/pages/Strategies/persona_routing_learned_v1.md
   
   **Type:** AdaptivePersonaRouter
   **Performance:** 92% success rate
   
   ## Parameters
   - min_confidence: 0.45
   - keyword_boosts: {...}
   ```

3. Add to AdaptivePersonaRouter
   ```python
   adaptive = AdaptivePersonaRouter(
       ...,
       logseq_integration=LogseqStrategyPersistence("persona_routing")
   )
   ```

**Success Criteria:**
- ✅ Strategies persist to Logseq automatically
- ✅ Can reload strategies on restart
- ✅ Performance history tracked
- ✅ Logseq queries work

---

### Day 13-14: VS Code Integration

**File:** `.vscode/extensions/persona-switcher/`

**Tasks:**
1. Create VS Code extension
   ```typescript
   // extension.ts
   vscode.workspace.onDidOpenTextDocument(async (doc) => {
       const result = await callPersonaAPI({
           query: `Working on ${doc.fileName}`,
           files: [doc.fileName]
       });
       
       if (result.should_switch) {
           await switchPersona(result.persona);
       }
   });
   ```

2. Add command palette commands
   - "Switch Persona: Auto"
   - "Switch Persona: Manual..."
   - "Persona: Show Current"

3. Add status bar indicator
   ```typescript
   const statusBar = vscode.window.createStatusBarItem(
       vscode.StatusBarAlignment.Right
   );
   statusBar.text = `🎭 ${currentPersona}`;
   ```

**Success Criteria:**
- ✅ Auto-switches on file open
- ✅ Manual switching via command palette
- ✅ Status bar shows current persona
- ✅ Integrates with Cline/Copilot

---

## Week 3: Production Deployment (5-7 days)

### Day 15-16: API Server

**File:** `scripts/persona_api.py`

**Tasks:**
1. Create FastAPI server
   ```python
   from fastapi import FastAPI
   
   app = FastAPI()
   
   @app.post("/persona")
   async def get_optimal_persona(request: PersonaRequest):
       result = await adaptive_router.execute(...)
       return {"persona": result["switched_to"]}
   ```

2. Add endpoints
   - `POST /persona` - Get optimal persona
   - `GET /persona/current` - Get current persona
   - `GET /persona/history` - Get switching history
   - `GET /persona/strategies` - Get learned strategies

3. Deploy locally: `uvicorn persona_api:app --port 8765`

**Success Criteria:**
- ✅ API responds <50ms
- ✅ Copilot integration works
- ✅ Error handling robust
- ✅ OpenAPI docs generated

---

### Day 17-18: Copilot Integration

**File:** `.vscode/settings.json`

**Tasks:**
1. Configure Copilot to use persona API
   ```json
   {
     "github.copilot.advanced": {
       "personaProvider": {
         "enabled": true,
         "endpoint": "http://localhost:8765/persona"
       }
     }
   }
   ```

2. Test with Copilot chat
3. Add persona suggestions in UI

**Success Criteria:**
- ✅ Copilot queries persona API
- ✅ Automatic switching works
- ✅ User can override suggestions
- ✅ Performance acceptable

---

### Day 19-20: Testing & Documentation

**Tasks:**
1. Comprehensive testing
   - Unit tests (all components)
   - Integration tests (full workflow)
   - E2E tests (VS Code + API)
   - Performance tests (<200ms target)

2. Documentation
   - Update `.hypertool/README.md`
   - Create user guide
   - Add troubleshooting section
   - Record demo video

3. Quality checks
   ```bash
   uv run ruff format .
   uv run ruff check . --fix
   uvx pyright packages/
   uv run pytest -v --cov
   ```

**Success Criteria:**
- ✅ 100% test coverage
- ✅ All quality checks pass
- ✅ Documentation complete
- ✅ Demo works end-to-end

---

### Day 21: Rollout

**Tasks:**
1. Merge to main branch
2. Update CHANGELOG.md
3. Create GitHub release
4. Announce to team
5. Monitor usage and feedback

**Success Criteria:**
- ✅ No breaking changes
- ✅ All tests pass in CI
- ✅ Documentation deployed
- ✅ User feedback positive

---

## Implementation Checklist

### Week 1: Core Components
- [ ] Create persona package directory
- [ ] Implement ContextAnalyzer
- [ ] Write ContextAnalyzer tests
- [ ] Implement PersonaRouter
- [ ] Write PersonaRouter tests
- [ ] Implement PersonaSwitcher
- [ ] Write PersonaSwitcher tests
- [ ] Integration testing

### Week 2: Adaptive Learning
- [ ] Implement AdaptivePersonaRouter
- [ ] Write adaptive learning tests
- [ ] Implement Logseq integration
- [ ] Test strategy persistence
- [ ] Create VS Code extension
- [ ] Test VS Code integration

### Week 3: Production
- [ ] Create FastAPI server
- [ ] Add API endpoints
- [ ] Configure Copilot integration
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Quality checks
- [ ] Deployment

---

## Quick Start Commands

```bash
# Week 1: Setup
mkdir -p packages/tta-dev-primitives/src/tta_dev_primitives/persona
mkdir -p tests/persona

# Create files
touch packages/tta-dev-primitives/src/tta_dev_primitives/persona/__init__.py
touch packages/tta-dev-primitives/src/tta_dev_primitives/persona/context_analyzer.py
touch packages/tta-dev-primitives/src/tta_dev_primitives/persona/persona_router.py
touch packages/tta-dev-primitives/src/tta_dev_primitives/persona/persona_switcher.py
touch tests/persona/__init__.py
touch tests/persona/test_context_analyzer.py
touch tests/persona/test_persona_router.py
touch tests/persona/test_persona_switcher.py

# Week 2: Adaptive
touch packages/tta-dev-primitives/src/tta_dev_primitives/persona/adaptive_router.py
touch packages/tta-dev-primitives/src/tta_dev_primitives/persona/logseq_strategy_persistence.py
touch tests/persona/test_adaptive_router.py

# Week 3: API
touch scripts/persona_api.py
mkdir -p .vscode/extensions/persona-switcher
touch .vscode/extensions/persona-switcher/package.json
touch .vscode/extensions/persona-switcher/extension.ts

# Run tests
uv run pytest tests/persona/ -v --cov=packages/tta-dev-primitives/src/tta_dev_primitives/persona

# Start API
uvicorn scripts.persona_api:app --reload --port 8765
```

---

## Success Metrics

**After 1 Month:**
- 90% of persona switches are automatic
- 85% accuracy in persona selection
- <200ms average switching time
- 5+ learned strategies in Logseq
- User satisfaction: "rarely need manual switching"

**After 3 Months:**
- 95% automatic switching
- 90% accuracy
- 10+ learned strategies
- Multi-persona workflows deployed
- APM integration complete

---

## Risk Mitigation

### Risk 1: Performance Degradation
**Mitigation:** 
- Measure latency at each step
- Set <200ms hard limit
- Cache analysis results
- Optimize hot paths

### Risk 2: Inaccurate Persona Selection
**Mitigation:**
- Start with manual override option
- Track user corrections
- Learn from corrections
- Circuit breaker for bad strategies

### Risk 3: Integration Issues
**Mitigation:**
- Comprehensive integration tests
- Graceful fallback to manual switching
- Clear error messages
- Rollback plan ready

### Risk 4: User Resistance
**Mitigation:**
- Opt-in initially
- Clear documentation
- Demo videos
- Gather feedback early

---

## Resources

**Code Examples:**
- See `.hypertool/ADAPTIVE_PERSONA_SWITCHING_DESIGN.md`
- Reference TTA.dev primitives package

**Dependencies:**
- TTA.dev primitives (RouterPrimitive, AdaptivePrimitive)
- FastAPI for API server
- VS Code extension API

**Documentation:**
- VS Code Extension Guide
- TTA.dev Primitives documentation
- Hypertool MCP documentation

---

**Status:** Ready to Start ✅  
**Next Action:** Create persona package directory and implement ContextAnalyzer  
**Timeline:** 3 weeks to production-ready adaptive system  
**Goal:** 90% automatic persona switching, 85% accuracy
