# TTA.dev Observability Implementation Plan

## Current Status (2026-03-09)

### ✅ Phase 1 Complete: Core Infrastructure
- **Status**: 6/6 tests passing
- **Files**: 
  - `ttadev/observability/collector.py` - Data collection and persistence
  - `tests/test_observability_collector.py` - Core tests
- **Features**:
  - File-based trace persistence
  - Event recording (spans, traces, agents)
  - Trace lifecycle management
  - AgentContext tracking

### 🔧 Phase 2: Dashboard Server (In Progress)
- **Status**: 8/8 tests failing (need server auto-start)
- **Files**:
  - `ttadev/ui/observability_server.py` - HTTP + WebSocket server
  - `ttadev/ui/static/dashboard.html` - Frontend
  - `tests/test_observability_dashboard.py` - UI tests
- **Needed**:
  1. Auto-start server in test fixtures
  2. Graceful shutdown
  3. Port management for parallel tests
  4. Server health checks

### 📋 Phase 3: Hierarchical Traces (Not Started)
- **Goal**: Show Provider → Model → Agent → Workflow → Primitive hierarchy
- **Required**:
  - Enhanced trace data model
  - Parent-child span relationships
  - Timeline visualization
  - Agent role transitions

### 🎯 Phase 4: Self-Growing Dashboard (Not Started)
- **Goal**: Auto-discover and visualize user workflows
- **Required**:
  - Dynamic primitive detection
  - Workflow pattern recognition
  - Custom visualization generation
  - User project metrics

## Implementation Strategy

### TDD Approach
1. ✅ Write failing tests
2. ✅ Implement minimal code to pass
3. ⏳ Refactor for quality
4. ⏳ Repeat for next feature

### Quality Gates
- All tests must pass before moving to next phase
- Code coverage > 80%
- Playwright tests validate real UX
- No shortcuts or "quick fixes"

## Next Actions

1. **Fix Phase 2 Tests** (Priority 1)
   - Add `@pytest.fixture` for server auto-start
   - Use `subprocess` or `multiprocessing` for server
   - Add proper cleanup in `yield` fixture
   - Verify all 8 dashboard tests pass

2. **Deploy Phase 2** (Priority 2)
   - Server stays stable when running
   - WebSocket connections work reliably
   - Real-time updates function
   - Graceful error handling

3. **Begin Phase 3** (Priority 3)
   - Design hierarchical trace model
   - Write tests for agent role tracking
   - Implement provider/model/agent context
   - Build timeline visualization

## Success Criteria

### Phase 2 Complete When:
- [ ] All 14 tests passing (6 collector + 8 dashboard)
- [ ] Server auto-starts for tests
- [ ] Dashboard loads in < 2s
- [ ] WebSocket connects reliably
- [ ] Primitives catalog shows all 68 items
- [ ] Code graph renders from CGC
- [ ] Agent activity updates in real-time

### Overall Success:
- User clones repo → Runs `./setup.sh` → Opens browser → Sees their agent work live
- Zero manual configuration
- Batteries-included experience
