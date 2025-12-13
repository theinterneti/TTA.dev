# Universal LLM Architecture - Design Document

**Based on:** User questionnaire responses (November 12, 2025)
**Purpose:** Support multi-provider, multi-coder, budget-aware LLM workflows for vibe coders

---

## 🎯 Requirements Summary

### User's Actual Stack

**Agentic Coders:**
- **Primary:** GitHub Copilot + Augment Code (Claude Sonnet 3.5) - Complex/touchy work
- **Secondary:** Cline (Gemini Pro/Flash, Kimi, DeepSeek) - Everything else

**Model Providers:**
- Google AI Studio (FREE tier) - Gemini 1.5 Pro/Flash
- OpenRouter - Various models
- HuggingFace (FREE) - Available as fallback

**Usage Split:**
- 50% free tier models
- 50% paid models (careful budget, tracked spending)
- Claude Sonnet worth the cost for quality

**Workflow Pattern:**
- Domain separation: Different agents on different parts (docs vs primitives)
- Empirical model selection: Use what works best based on benchmarks
- Cost justification: Track WHY paid was chosen over free

### Critical Pain Points

1. **Git hygiene:** Agents forget to create branches, commit, push, cleanup
2. **File cleanup:** Agents leave temp files, one-time scripts
3. **False completion:** Agents claim work done when not functional (need browser verification for dashboards)

---

## 🏗️ Architecture Design

### Layer 1: UniversalLLMPrimitive (Base)

**Purpose:** Single interface for ANY coder, model, modality

```python
from tta_dev_primitives.integrations import UniversalLLMPrimitive
from tta_dev_primitives.integrations.budget import UserBudgetProfile

llm = UniversalLLMPrimitive(
    # Auto-detect or specify
    coder="auto",  # Detects: copilot > augment > cline
    model="auto",  # Routes based on complexity + budget

    # Budget awareness
    budget_profile=UserBudgetProfile.CAREFUL,
    monthly_limit=50.00,
    require_justification_for_paid=True,

    # Model preferences (empirical)
    free_models=[
        "gemini-1.5-pro",     # Primary free
        "gemini-1.5-flash",   # Fast free
        "kimi",               # Cline fallback
        "deepseek",           # Cline fallback
    ],
    paid_models=[
        "claude-3.5-sonnet",  # Worth the cost
    ],

    # Quality thresholds
    prefer_free_when_close=True,
    quality_threshold=0.85,  # Accept 85% quality for free
)

# Execute with automatic routing
result = await llm.execute(
    prompt="Build a dashboard",
    context=context,
    complexity="high",  # Auto-routes to Claude (paid)
    justification="Dashboard requires complex visualization logic"
)
```

**Key Features:**
- ✅ Auto-detect which coder is available (Copilot, Augment, Cline)
- ✅ Route to appropriate model based on complexity + budget
- ✅ Track cost AND justification for paid usage
- ✅ Fallback chain with free-first preference
- ✅ Empirical model selection based on benchmarks

### Layer 2: Coder-Specific Primitives

**Purpose:** Native integration with each agentic coder

```python
from tta_dev_primitives.integrations import CopilotPrimitive, ClinePrimitive, AugmentPrimitive

# Copilot for complex work
copilot = CopilotPrimitive(
    model="claude-3.5-sonnet",
    modality="vscode",  # or "cli", "github"
    use_cases=["complex", "touchy"],
)

# Cline for everything else
cline = ClinePrimitive(
    model="auto",  # Gemini Pro/Flash, Kimi, DeepSeek
    free_tier_only=False,
    fallback_chain=[
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "kimi",
        "deepseek",
    ]
)

# Augment for parallel comparison
augment = AugmentPrimitive(
    model="claude-3.5-sonnet",
    modality="vscode",
)

# Multi-coder workflow
workflow = ParallelPrimitive([
    copilot,
    cline,
    augment,
]) >> BestOutputSelectorPrimitive(
    selection_criteria="empirical_quality"
)
```

**Capabilities:**
- **CopilotPrimitive:** VS Code, CLI, GitHub.com modalities
- **ClinePrimitive:** Multi-provider support (Google, OpenRouter, HuggingFace)
- **AugmentPrimitive:** VS Code native integration
- **Auto-detection:** Which coder is available in current environment

### Layer 3: Budget Management

**Purpose:** Track spend, justify paid usage, enforce limits

```python
from tta_dev_primitives.integrations.budget import (
    BudgetAwareLLMPrimitive,
    UserBudgetProfile,
    CostJustification,
)

llm = BudgetAwareLLMPrimitive(
    profile=UserBudgetProfile.CAREFUL,
    monthly_limit=50.00,

    # Tracking
    track_justification=True,  # WHY was paid used?
    alert_at_percent=80,       # Alert at 80% budget

    # User control
    require_user_opt_in_for_paid=True,
    show_free_alternatives=True,

    # Fallback behavior
    fallback_to_free_on_budget_exceeded=True,
)

# Usage with justification
result = await llm.execute(
    prompt="Complex dashboard logic",
    justification=CostJustification(
        reason="Dashboard complexity requires Claude",
        free_alternatives_tried=["gemini-1.5-pro", "gemini-1.5-flash"],
        expected_quality_delta="+25%",
        cost_estimate="$0.15",
    )
)

# Budget reporting
print(llm.budget_tracker.report())
# Month: November 2025
# Spent: $23.45 / $50.00 (46.9%)
# Free tier usage: 52%
# Paid usage: 48%
# Savings from free tier: $18.32
#
# Paid usage justifications:
# - Dashboard logic (Claude): +25% quality, tried Gemini first
# - Complex refactoring (Claude): +30% quality, tried Gemini first
```

**Features:**
- ✅ Track actual spend vs budget
- ✅ Require justification for paid usage
- ✅ User opt-in for paid recommendations
- ✅ Alert before exceeding budget
- ✅ Show free alternatives
- ✅ Calculate savings from free tier usage

### Layer 4: Model Benchmark Tracking

**Purpose:** Empirical model selection based on public benchmarks

```python
from tta_dev_primitives.integrations.benchmarks import (
    ModelBenchmarkTracker,
    BenchmarkSource,
)

tracker = ModelBenchmarkTracker(
    sources=[
        BenchmarkSource.LMSYS,           # LMSYS Chatbot Arena
        BenchmarkSource.HUGGINGFACE_LLM, # HuggingFace Open LLM Leaderboard
        BenchmarkSource.CUSTOM,          # User's own benchmarks
    ],
    update_frequency="monthly",

    # User's preferences
    prefer_free_tier=True,
    quality_threshold=0.85,
)

# Get current best free model
best_free = await tracker.get_best_free_model(
    use_case="code_generation",
    modality="vscode",
)
# Returns: "gemini-1.5-pro" (Nov 2025 benchmark leader)

# Get recommendation with reasoning
recommendation = await tracker.recommend_model(
    complexity="high",
    budget_profile=UserBudgetProfile.CAREFUL,
    use_case="dashboard_creation",
)
# Returns:
# {
#   "model": "claude-3.5-sonnet",
#   "cost": "PAID",
#   "reasoning": "Dashboard complexity scores 8.5/10, free models max out at 7.2/10",
#   "free_alternative": "gemini-1.5-pro (7.2/10 quality)",
#   "quality_delta": "+18%",
#   "justification": "Complex visualization logic benefits from Claude's stronger reasoning"
# }

# Update benchmarks (monthly job)
await tracker.refresh_benchmarks()
```

**Features:**
- ✅ Track LMSYS Arena rankings
- ✅ Track HuggingFace Open LLM Leaderboard
- ✅ Support custom user benchmarks
- ✅ Monthly automatic updates
- ✅ Empirical recommendations based on data
- ✅ Quality delta calculations (free vs paid)

### Layer 5: Agent Hygiene Primitives

**Purpose:** Solve the 3 pain points (git hygiene, cleanup, verification)

```python
from tta_dev_primitives.integrations.hygiene import (
    GitHygienePrimitive,
    FileCleanupPrimitive,
    VerificationLoopPrimitive,
)

# 1. Git hygiene (pain point #1)
git_hygiene = GitHygienePrimitive(
    auto_create_branch=True,
    auto_commit=True,
    auto_push=True,
    cleanup_on_complete=True,
)

workflow = (
    git_hygiene.create_branch("feature/dashboard") >>
    build_dashboard >>
    git_hygiene.commit("Add dashboard") >>
    git_hygiene.push() >>
    git_hygiene.cleanup_temp_files()
)

# 2. File cleanup (pain point #2)
cleanup = FileCleanupPrimitive(
    track_temp_files=True,
    auto_cleanup_on_complete=True,
    cleanup_patterns=[
        "*.tmp",
        "*.temp",
        "scripts/one_time_*.py",
        ".cache/*",
    ]
)

workflow = (
    task_primitive >>
    cleanup.cleanup_if_successful()
)

# 3. Verification loop (pain point #3)
verification = VerificationLoopPrimitive(
    max_attempts=3,
    verification_methods=[
        "unit_tests",
        "integration_tests",
        "browser_verification",  # For dashboards
    ],
    require_user_confirmation=True,
)

workflow = (
    build_dashboard >>
    verification.verify_until_functional(
        test_command="pytest tests/",
        browser_check_url="http://localhost:3000",
        success_criteria="Dashboard loads and displays data"
    )
)

# Combined workflow
complete_workflow = (
    git_hygiene.create_branch("feature/dashboard") >>
    cleanup.track_files() >>
    build_dashboard >>
    verification.verify_until_functional() >>
    cleanup.cleanup_temp_files() >>
    git_hygiene.commit_and_push()
)
```

**Features:**
- ✅ **GitHygienePrimitive:** Auto-create branches, commit, push, cleanup
- ✅ **FileCleanupPrimitive:** Track temp files, auto-cleanup on success
- ✅ **VerificationLoopPrimitive:** Test until functional, browser verification, user confirmation

### Layer 6: Domain-Aware Agent Orchestration

**Purpose:** Separate agents by domain (docs vs primitives vs infrastructure)

```python
from tta_dev_primitives.integrations.domain import (
    DomainRouterPrimitive,
    AgentDomain,
)

router = DomainRouterPrimitive(
    domains={
        AgentDomain.DOCUMENTATION: ClinePrimitive(model="gemini-1.5-pro"),
        AgentDomain.PRIMITIVES: CopilotPrimitive(model="claude-3.5-sonnet"),
        AgentDomain.INFRASTRUCTURE: AugmentPrimitive(model="claude-3.5-sonnet"),
        AgentDomain.KNOWLEDGE_BASE: ClinePrimitive(model="gemini-1.5-flash"),
    },

    # Prevent conflicts
    domain_isolation=True,
    context_sharing=True,  # Share context across domains
)

# Route task to appropriate agent
result = await router.execute(
    task="Update primitives documentation",
    domain=AgentDomain.DOCUMENTATION,  # Routes to Cline
    context=context,
)

# Multi-domain workflow
workflow = ParallelPrimitive([
    router.execute(
        task="Update docs",
        domain=AgentDomain.DOCUMENTATION,
    ),
    router.execute(
        task="Implement CachePrimitive",
        domain=AgentDomain.PRIMITIVES,
    ),
    router.execute(
        task="Setup CI/CD",
        domain=AgentDomain.INFRASTRUCTURE,
    ),
])
```

**Features:**
- ✅ Domain-based routing (docs, primitives, infra, KB)
- ✅ Prevent domain conflicts
- ✅ Context sharing across domains
- ✅ Agent specialization by domain

---

## 📊 Budget Profiles

### FREE-ONLY Mode

**Target:** Broke students, learners, hobbyists

**Behavior:**
- ✅ Only recommend free models
- ✅ Block paid models by default
- ✅ User can opt-in to see paid recommendations
- ✅ Show "upgrade to paid" ONLY when:
  - Project has significant usage (downloads/stars)
  - Context indicates paid may be critical
  - User explicitly asks for paid options

**Models:**
- Gemini 1.5 Pro (FREE) - Primary
- Gemini 1.5 Flash (FREE) - Fast tasks
- Kimi (FREE via Cline) - Fallback
- DeepSeek (FREE via Cline) - Fallback
- HuggingFace models (FREE) - Specialized tasks

**Cost:** $0/month

### CAREFUL Mode (Default)

**Target:** Solo developers, small teams, budget-conscious

**Behavior:**
- ✅ Prefer free models when quality is close (85%+ threshold)
- ✅ Auto-route to free when possible
- ✅ Track spend vs budget
- ✅ Alert at 80% budget
- ✅ Require justification for paid usage
- ✅ Show free alternatives with quality delta

**Split:**
- 50% free tier (Gemini, Kimi, DeepSeek)
- 50% paid (Claude Sonnet for complex work)

**Budget:** $10-50/month

**Tracking:**
- Cost per request
- Justification for paid usage
- Savings from free tier
- Monthly reports

### UNLIMITED Mode

**Target:** Companies, well-funded projects

**Behavior:**
- ✅ Always use best model for task
- ✅ Presumably skip free for non-simple tasks
- ✅ Quality > cost
- ✅ Still track spend for reporting
- ✅ No budget limits or alerts

**Models:**
- Claude 3.5 Sonnet (best reasoning)
- GPT-4 Turbo (best general)
- o1-preview (best complex reasoning)

**Cost awareness:** Tracked but not limiting

---

## 🔄 Multi-Coder Workflow Patterns

### Pattern 1: Domain Separation (User's Preference)

```python
# Agent 1: Documentation (Cline + Gemini)
docs_agent = ClinePrimitive(
    model="gemini-1.5-pro",
    domain=AgentDomain.DOCUMENTATION,
)

# Agent 2: Primitives (Copilot + Claude)
primitives_agent = CopilotPrimitive(
    model="claude-3.5-sonnet",
    domain=AgentDomain.PRIMITIVES,
)

# Parallel execution, no conflicts
workflow = ParallelPrimitive([
    docs_agent.execute("Update PRIMITIVES_CATALOG.md"),
    primitives_agent.execute("Implement CachePrimitive"),
])
```

### Pattern 2: Sequential Refinement

```python
# Cline for initial implementation (free)
# Copilot for refinement (paid)
workflow = (
    ClinePrimitive(model="gemini-1.5-pro") >>  # Draft
    CopilotPrimitive(model="claude-3.5-sonnet") >>  # Refine
    VerificationLoopPrimitive()  # Verify it works
)
```

### Pattern 3: Parallel Comparison

```python
# Get outputs from multiple coders, pick best
workflow = ParallelPrimitive([
    ClinePrimitive(model="gemini-1.5-pro"),
    CopilotPrimitive(model="claude-3.5-sonnet"),
    AugmentPrimitive(model="claude-3.5-sonnet"),
]) >> BestOutputSelectorPrimitive(
    criteria="empirical_quality",
    benchmark_source=ModelBenchmarkTracker(),
)
```

---

## 🎯 Implementation Priority

### Phase 1: Core Primitives (Week 1)

1. **UniversalLLMPrimitive**
   - Base class for all LLM operations
   - Coder auto-detection (Copilot, Augment, Cline)
   - Model routing logic
   - Budget profile support

2. **CopilotPrimitive, ClinePrimitive, AugmentPrimitive**
   - Native integration with each coder
   - Model configuration
   - Modality support (VS Code, CLI, GitHub)

3. **UserBudgetProfile + CostTrackingPrimitive**
   - FREE/CAREFUL/UNLIMITED modes
   - Cost tracking
   - Justification logging
   - Budget alerts

### Phase 2: Agent Hygiene (Week 2)

4. **GitHygienePrimitive**
   - Auto-create branches
   - Auto-commit and push
   - Cleanup temp files
   - Solve pain point #1

5. **FileCleanupPrimitive**
   - Track temp files
   - Auto-cleanup on success
   - Pattern-based cleanup
   - Solve pain point #2

6. **VerificationLoopPrimitive**
   - Test until functional
   - Browser verification for dashboards
   - User confirmation loops
   - Solve pain point #3

### Phase 3: Advanced Features (Week 3)

7. **ModelBenchmarkTracker**
   - LMSYS Arena integration
   - HuggingFace Leaderboard integration
   - Monthly updates
   - Empirical recommendations

8. **DomainRouterPrimitive**
   - Domain-based agent routing
   - Conflict prevention
   - Context sharing

9. **Multi-coder orchestration patterns**
   - Sequential refinement
   - Parallel comparison
   - Domain separation

---

## 📝 Vibe Coder Guides

### Guide 1: FREE Path ($0/month)

**Stack:**
- Cline + Gemini 1.5 Pro (FREE)
- TTA.dev primitives (FREE)
- Supabase (FREE tier)

**Content:**
- Setup Google AI Studio (5 min)
- Configure Cline
- Build chatbot in 30 min
- Cost tracking: $0

### Guide 2: CAREFUL Path ($10-50/month)

**Stack:**
- 50% Gemini (FREE)
- 50% Claude (PAID)
- Cost justification tracking
- Budget alerts

**Content:**
- When to use free vs paid
- Cost tracking setup
- Justification examples
- Monthly budget management

### Guide 3: Multi-Coder Collaboration

**Stack:**
- Domain separation pattern
- Copilot for complex work
- Cline for everything else
- Git hygiene automation

**Content:**
- Domain-based routing
- Agent specialization
- Preventing conflicts
- Cleanup automation

---

## ✅ Success Criteria

### For Vibe Coders

- [ ] Can start with $0 (FREE mode)
- [ ] Can upgrade to CAREFUL with clear cost tracking
- [ ] Know exactly WHY paid was used over free
- [ ] Can use multiple coders without conflicts
- [ ] Agents clean up after themselves
- [ ] Work is verified before claiming "done"

### For TTA.dev

- [ ] Universal interface for all coders/models
- [ ] Budget awareness built-in
- [ ] Empirical model selection
- [ ] Agent hygiene primitives solve pain points
- [ ] Domain-aware orchestration prevents conflicts

### For Adoption

- [ ] Broke students can use it (FREE mode)
- [ ] Careful spenders have cost control (CAREFUL mode)
- [ ] Companies get best quality (UNLIMITED mode)
- [ ] Multi-provider workflows are simple
- [ ] Cost justification is transparent

---

**Next Steps:** Implement Phase 1 primitives (UniversalLLMPrimitive + coder-specific primitives + budget system)


---
**Logseq:** [[TTA.dev/Docs/Architecture/Universal_llm_architecture]]
