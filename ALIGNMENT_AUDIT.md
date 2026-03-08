# TTA.dev Vision Alignment Audit
*Date: March 8, 2026*

## 🎯 Target Vision: Batteries-Included User Journey

### Ideal Flow
1. **Clone** → `git clone https://github.com/theinterneti/TTA.dev.git`
2. **Point CLI Agent** → Agent detects `AGENTS.md` 
3. **Auto-Configure** → Agent uses TTA.dev primitives immediately
4. **Live Observability** → Web UI auto-starts showing everything
5. **Self-Growing** → UI automatically expands as agent builds more

---

## 📊 Current State Assessment

### ✅ STRENGTHS (What's Working)

#### 1. **Strong Foundation Documents** ✓
- ✅ `AGENTS.md` - Comprehensive agent guidance
- ✅ `USER_JOURNEY.md` - Clear user journey defined
- ✅ `GETTING_STARTED.md` - Setup instructions
- ✅ `PRIMITIVES_CATALOG.md` - Complete primitive reference
- ✅ `.github/copilot-instructions.md` - Agent auto-configuration

**Status**: **80% Complete** - Docs exist and are well-structured

#### 2. **Primitives Package** ✓
- ✅ `packages/tta-primitives/` - Core primitives implemented
- ✅ Workflow primitives (Sequential, Parallel, Conditional, Router)
- ✅ Recovery primitives (Retry, Fallback, Timeout, CircuitBreaker)
- ✅ Caching, Rate limiting, Validation
- ✅ Full test coverage (100%)

**Status**: **90% Complete** - Primitives are production-ready

#### 3. **Observability Foundation** ✓
- ✅ `packages/tta-observability/` - Integration package exists
- ✅ OpenTelemetry instrumentation
- ✅ LangFuse integration
- ✅ Sampling strategies (fixed, adaptive, head-based, tail-based)
- ✅ Test coverage

**Status**: **70% Complete** - Backend exists, UI missing

---

### 🚨 CRITICAL GAPS (Blocking Batteries-Included Experience)

#### 1. **NO Batteries-Included Observability UI** ❌
**Problem**: User has to manually set up observability dashboard

**What Exists**:
- `apps/platform/components/serena/core/src/serena/resources/dashboard/` - Serena's custom dashboard
- Not integrated with TTA primitives
- Requires manual setup

**What's Needed**:
```bash
# Should work like this:
git clone TTA.dev
cd TTA.dev
uv run tta-observability serve  # Auto-starts UI on localhost:8080
```

**Gap**: **100% Missing**
- No `tta-observability` CLI command
- No auto-start mechanism
- No integration with primitives telemetry

#### 2. **NO Auto-Detection by CLI Agents** ❌
**Problem**: Agents don't automatically discover and use TTA.dev

**What Exists**:
- `.github/copilot-instructions.md` - GitHub Copilot specific
- `.mcp.json` - Manual MCP server config (legacy Hypertool)
- `.claude/`, `.cline/`, `.gemini/` - Empty or minimal

**What's Needed**:
```markdown
# Auto-detection markers that ALL agents recognize
.github/
  agents/           ✅ Exists but not used by agents
  skills/           ✅ Exists but not used by agents
  copilot-instructions.md  ✅ Only works for GitHub Copilot
  
# Universal agent detection (MISSING):
.ai-config.json     ❌ Standard config all agents check
TTA_CONFIG.md       ❌ Human-readable agent instructions
```

**Gap**: **80% Missing**
- GitHub Copilot works (via .github/copilot-instructions.md)
- Claude, Cline, Gemini don't auto-detect

#### 3. **Fragmented Repository Structure** ⚠️
**Problem**: Code scattered across multiple locations

**Current Structure**:
```
TTA.dev/
├── packages/          # ✅ Modern packages (tta-primitives, tta-observability)
├── platform/          # ⚠️  Legacy platform code
│   ├── agent-context
│   ├── agent-coordination
│   ├── apm/langfuse
│   ├── dolt
│   ├── integrations
│   └── skills
├── apps/              # ⚠️  Serena (separate project, not TTA)
│   └── platform/components/serena/
└── src/               # ❌ DEPRECATED - should be removed
```

**What's Needed**:
```
TTA.dev/
├── packages/          # All TTA packages
│   ├── tta-core/             ✅ Exists
│   ├── tta-primitives/       ✅ Exists
│   ├── tta-observability/    ✅ Exists (needs UI)
│   ├── tta-agents/           ❌ MISSING - Agent coordination
│   └── tta-ui/               ❌ MISSING - Batteries-included UI
├── .github/
│   ├── agents/        ✅ Custom agents
│   ├── skills/        ✅ Agent skills
│   └── workflows/     ✅ CI/CD
├── scripts/           ✅ Utility scripts
├── tests/             ✅ Integration tests
└── docs/              ✅ Documentation

# TO REMOVE:
├── platform/          ❌ Consolidate into packages/
├── apps/serena/       ❌ Move to separate repo (not TTA)
└── src/               ❌ DEPRECATED
```

**Gap**: **40% Misaligned**

#### 4. **NO Self-Growing UI** ❌
**Problem**: UI doesn't auto-expand as agent builds things

**What's Needed**:
- UI detects new primitives → adds them to dashboard
- UI detects new workflows → visualizes them
- UI detects new traces → displays them
- UI detects new metrics → charts them

**Current State**: **100% Missing**
- No dynamic UI rendering
- No auto-discovery of new components

#### 5. **MCP Server Not TTA-Native** ⚠️
**Problem**: `.mcp.json` uses legacy Hypertool, not TTA primitives

**Current**:
```json
{
  "mcpServers": {
    "hypertool": {
      "command": "npx -y @toolprint/hypertool-mcp@0.0.45 mcp run ..."
    }
  }
}
```

**What's Needed**:
```json
{
  "mcpServers": {
    "tta-platform": {
      "command": "uv run tta-mcp serve",
      "env": {
        "TTA_AUTO_OBSERVE": "true",
        "TTA_UI_PORT": "8080"
      }
    }
  }
}
```

**Gap**: **60% Missing**
- No `tta-mcp` command
- No auto-observability flag
- Still using legacy Hypertool

---

## 🎯 Priority Action Plan

### Phase 1: Batteries-Included UI (Highest Priority)
**Goal**: User runs `uv run tta-observability serve` and gets instant dashboard

**Tasks**:
1. Create `packages/tta-ui/` package
2. Build simple HTML/JS dashboard (like Serena's, but for TTA)
3. Add `tta-observability serve` CLI command
4. Auto-detect OpenTelemetry traces from primitives
5. Display workflows, traces, metrics in real-time

**Estimated Effort**: 2-3 days
**Blocker Removed**: ✅ UI auto-starts

### Phase 2: Universal Agent Auto-Detection
**Goal**: All CLI agents (Copilot, Claude, Cline) auto-detect TTA.dev

**Tasks**:
1. Create `.ai-config.json` (standard all agents check)
2. Add `TTA_CONFIG.md` in root (human-readable instructions)
3. Update `.claude/`, `.cline/`, `.gemini/` with agent-specific configs
4. Test with Claude Code, Cline, Gemini Code Assist

**Estimated Effort**: 1 day
**Blocker Removed**: ✅ Agents auto-configure

### Phase 3: Repository Consolidation
**Goal**: Clean, understandable structure

**Tasks**:
1. Move `platform/` code into `packages/tta-agents/`
2. Archive `apps/serena/` (separate project)
3. Delete `src/` (deprecated)
4. Update all imports and tests

**Estimated Effort**: 1-2 days
**Blocker Removed**: ✅ Structure is intuitive

### Phase 4: Native MCP Server
**Goal**: Replace Hypertool with TTA-native MCP

**Tasks**:
1. Create `packages/tta-mcp/` package
2. Build MCP server exposing TTA primitives
3. Add `uv run tta-mcp serve` command
4. Update `.mcp.json` to use native server

**Estimated Effort**: 2 days
**Blocker Removed**: ✅ No external dependencies

### Phase 5: Self-Growing UI
**Goal**: UI auto-expands as agent builds

**Tasks**:
1. Add WebSocket server to `tta-observability`
2. Auto-detect new primitives → add to dashboard
3. Auto-detect new workflows → visualize
4. Auto-detect new traces → display

**Estimated Effort**: 3 days
**Blocker Removed**: ✅ UI adapts to growth

---

## 📈 Alignment Scoring

| Component | Target | Current | Gap |
|-----------|--------|---------|-----|
| **Documentation** | 100% | 80% | ⚠️ 20% - Need .ai-config.json |
| **Primitives** | 100% | 90% | ⚠️ 10% - Minor polish |
| **Observability Backend** | 100% | 70% | 🚨 30% - UI missing |
| **Observability UI** | 100% | 0% | 🚨 100% - Critical gap |
| **Agent Auto-Detection** | 100% | 20% | 🚨 80% - Only Copilot works |
| **Repo Structure** | 100% | 60% | ⚠️ 40% - Fragmented |
| **MCP Integration** | 100% | 40% | 🚨 60% - Legacy Hypertool |
| **Self-Growing UI** | 100% | 0% | 🚨 100% - Not implemented |

**Overall Alignment**: **45%** (Moderate)

---

## 🏆 Success Criteria

### ✅ Batteries-Included Experience Achieved When:
1. ✅ User clones repo
2. ✅ User runs `uv sync` (dependencies auto-install)
3. ✅ User runs `uv run tta-observability serve` (UI auto-starts)
4. ✅ User points CLI agent at repo
5. ✅ Agent auto-detects TTA.dev (via `.ai-config.json` or `.github/`)
6. ✅ Agent uses primitives immediately (workflows, retries, caching)
7. ✅ UI shows everything in real-time (traces, metrics, logs)
8. ✅ Agent builds new features → UI auto-expands to show them

---

## 🚀 Recommended Next Steps

### Immediate (This Weekend):
1. **Create batteries-included UI** (Phase 1)
   - Build `packages/tta-ui/`
   - Add `tta-observability serve` command
   - Auto-display OpenTelemetry traces

2. **Add universal agent detection** (Phase 2)
   - Create `.ai-config.json`
   - Add `TTA_CONFIG.md`
   - Test with Claude, Cline

### Short-term (Next Week):
3. **Consolidate repository** (Phase 3)
   - Move `platform/` → `packages/tta-agents/`
   - Archive `apps/serena/`
   - Delete `src/`

4. **Build native MCP server** (Phase 4)
   - Create `packages/tta-mcp/`
   - Replace Hypertool dependency

### Long-term (Next Month):
5. **Implement self-growing UI** (Phase 5)
   - Add dynamic component discovery
   - Build auto-expanding dashboard

---

## 🎯 Bottom Line

**TTA.dev has a solid foundation (primitives, observability backend), but lacks the "batteries-included" experience.**

**Critical Missing Pieces**:
1. 🚨 No auto-starting observability UI
2. 🚨 No universal agent auto-detection
3. ⚠️ Fragmented repository structure
4. 🚨 No self-growing UI

**To achieve the vision, prioritize Phase 1 (Batteries-Included UI) immediately.**

Once Phase 1 is complete, the user journey becomes:
```bash
git clone TTA.dev
cd TTA.dev
uv sync
uv run tta-observability serve  # ← UI auto-starts!
# Point your agent at the repo → it auto-detects and uses TTA.dev
```

This is the turning point that makes TTA.dev "batteries-included."
