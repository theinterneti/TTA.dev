# Universal LLM Architecture - User Requirements

**CRITICAL:** Need answers to design the right architecture for vibe coders using multiple providers/coders/modalities.

---

## 🎯 Your Current Setup

### 1. Agentic Coders You Use

**Please list which ones you actively use:**

- [x] **Cline** (VS Code extension)
  - Models you use with Cline: Gemini pro/flash, kimi, deepseek,
  - Use cases:
everything else
- [x] **GitHub Copilot** (VS Code + CLI + GitHub.com)
  - Models you use: sonnet4.5
  - Use cases:
Most complex and touchy work
- [x] **Augment Code** (VS Code)
  - Models you use: sonnet4.5
  - Use cases:

- [ ] **Other:** _______________

### 2. Model Providers You Use

**Which providers do you have API keys for?**

- [ ] **OpenAI**
  - Models: GPT-4 Turbo? GPT-4? o1-preview? o1-mini?
  - Monthly budget:

- [ ] **Anthropic**
  - Models: Claude 3.5 Sonnet? Claude 3 Opus? Claude 3 Haiku?
  - Monthly budget:

- [X] **Google AI Studio**
  - Models: Gemini 1.5 Pro? Gemini 1.5 Flash?
  - Free tier or paid?

- [X] **OpenRouter**
  - Models you use through it:
  - Monthly budget:

- [ ] **Other:** HF free (key added to main .env file)

### 3. Free vs Paid Split

**In a typical month, what's your usage split?**

- Free tier models: 50%
- Paid models (careful budget): 50%
- Paid models (no limit): 0%

**Free models you rely on:**
1. Whatever works best (empirical mostly)
2.
3.

**Paid models worth the cost:**
1.Claude
2.
3.

### 4. Multi-Coder Workflow

**How do you use multiple agentic coders together?**

Example:
- "I use Cline for initial coding, Copilot for refinement"
- "I use Augment for architecture, Cline for implementation"
- "I compare outputs from all three and pick the best"

**Your workflow:**
I've been trying to keep agents working in different domains as in one works on documentation/kb while the other works on primitives etc.

### 5. Modality Usage

**Where do you work with AI?**

- [X] **VS Code** (local development)
  - Primary coder: Copilot/augment (Claude)
  - Backup coder: Gemini pro,

- [X] **GitHub.com** (PR reviews, issues)
  - Using Copilot?
  - Using other tools? (tried openhands and gemini, but not much luck! Gemini is kind of working?)
  working on merge issues, security flaw resolution, async tasks

- [X] **Terminal/CLI**
  - Using GitHub Copilot CLI?
  - Using other tools?
  sub-agents

- [X] **Browser** (ChatGPT, Claude web, Gemini web)
  - For what tasks?
  Prompt refinement. Gems

### 6. Budget Scenarios

**What should TTA.dev do in these scenarios?**

**Scenario A: You're a broke student (FREE-ONLY mode)**
- Which models should we recommend?
The current best (which should be researched regularly, as needed when new models hit etc.)
- Should we block paid models entirely?
The user should be able to opt-in to considering paid options across the board, not just for models.
- Should we show "upgrade to paid" suggestions?
Only when, based on the usage (downloads/stars) of the product, the context, or other factors indicate that paid options may be of critical use to the project.

**Scenario B: You're being careful ($10-50/month budget)**
- How should we allocate budget?
Always put the user in charge. Use free models whenever possible
- Should we auto-route to free when possible?
Most likely yes
- Should we track spend and alert?
We should! We should also track the justification for using the paid resource over the free one.

**Scenario C: You're a company (unlimited budget)**
- Always use best model?
Presumably!
- Still use free for simple tasks?
Seems unlikely that this would make sense.
- Cost awareness at all?
I think the possibility of better answers outweights concerns about cost for this group.

### 7. Pain Points

**What frustrates you about current multi-provider workflows?**

1. Agents forget to do basic things, create/check out branches, commit to the remote
2.
Agents don't clean up after themselves, even though that obviously needs to be done whenever they create temporary files, one time use scripts etc.
3.
Agents saying work is done when it isn't functional. Even after multiple attempts it's completed properly (say, via testing) I have to tell the agent to use the browser to visually ensure it (say a grafana dashboard) works.

**What would make your life easier?**

1.
Agents that knew what they know better than me (e.g. devops)
2.
Agents asking me for more research/clarification when they aren't sure what to do
3.
TTA.dev actually working to build TTA properly.

---

## 🏗️ Proposed Architecture (Based on Answers)

### UniversalLLMPrimitive

```python
from tta_dev_primitives.integrations import UniversalLLMPrimitive

# Works with ANY coder/model/modality
llm = UniversalLLMPrimitive(
    # Auto-detect or specify
    coder="auto",  # or "cline", "copilot", "augment"
    model="auto",  # or "gpt-4", "claude-3.5-sonnet", "gemini-pro"
    budget_profile="CAREFUL",  # or "FREE", "UNLIMITED"

    # Fallback chain
    fallbacks=[
        ("gemini-1.5-pro", "FREE"),
        ("gpt-4-turbo", "PAID"),
    ]
)

# Use it
result = await llm.execute(prompt, context)
```

### Multi-Coder Orchestration

```python
from tta_dev_primitives.integrations import ClinePrimitive, CopilotPrimitive

# Use multiple coders for same task
workflow = ParallelPrimitive([
    ClinePrimitive(model="claude-3.5-sonnet"),
    CopilotPrimitive(model="gpt-4"),
    AugmentPrimitive(model="auto"),
]) >> BestOutputSelectorPrimitive()

# Or sequential (each coder does different stage)
workflow = (
    ClinePrimitive() >>  # Initial code generation
    CopilotPrimitive() >>  # Refinement
    AugmentPrimitive()  # Final polish
)
```

### Budget-Aware Routing

```python
from tta_dev_primitives.integrations import BudgetAwareLLMPrimitive

llm = BudgetAwareLLMPrimitive(
    budget_profile=UserBudgetProfile.CAREFUL,
    monthly_limit=50.00,

    # Preferences
    prefer_free=True,  # Use free tier when quality is close
    quality_threshold=0.8,  # Accept 80% quality for free

    # Routing
    routes={
        "simple": "gemini-1.5-flash",  # FREE
        "medium": "gemini-1.5-pro",    # FREE
        "complex": "gpt-4-turbo",      # PAID (only when needed)
    }
)
```

### Cost Tracking

```python
from tta_dev_primitives.integrations import CostTrackingPrimitive

workflow = CostTrackingPrimitive(
    budget_limit=50.00,
    alert_at=40.00,  # Alert at 80% budget

    # Actions when over budget
    fallback_to_free=True,
    block_paid_models=False,  # Just warn
) >> UniversalLLMPrimitive()

# Check costs
print(workflow.cost_tracker.current_spend)  # $23.45
print(workflow.cost_tracker.free_tier_usage)  # 87%
print(workflow.cost_tracker.savings)  # Saved $156 by using free tier
```

---

## ❓ Questions Before Implementation

### Architecture Questions

1. **Should primitives auto-detect which coder is available?**
   - Pro: Works seamlessly
   - Con: Less explicit

2. **Should budget profile be global or per-primitive?**
   - Global: Set once in context
   - Per-primitive: More flexible but more config

3. **Should we integrate directly with coder APIs or use them as tools?**
   - Direct: More control, more maintenance
   - As tools: Let each coder do what it does best

### Implementation Questions

1. **Which primitives are P0 for you?**
   - UniversalLLMPrimitive?
   - ClinePrimitive, CopilotPrimitive, AugmentPrimitive?
   - BudgetAwareLLMPrimitive?
   - CostTrackingPrimitive?
   - All of the above?

2. **What's the #1 pain point to solve first?**
   - Multi-provider complexity?
   - Cost tracking?
   - Quality vs price tradeoffs?
   - Something else?

3. **Do you want TTA.dev to:**
   - [ ] Manage API keys for all providers
   - [ ] Use existing coder integrations
   - [ ] Both (with fallback)

---

## 📝 Next Steps

Once you answer these questions, I'll:

1. ✅ Design the right architecture (no more over-pivoting!)
2. ✅ Implement core primitives you actually need
3. ✅ Create budget-aware system for FREE/CAREFUL/UNLIMITED users
4. ✅ Build multi-coder orchestration
5. ✅ Write vibe coder quickstart for each budget tier

**Goal:** Make TTA.dev the BEST framework for vibe coders who want to:
- Work with multiple AI coders simultaneously
- Use multiple model providers (free + paid)
- Track costs and stay within budget
- Get recommendations based on budget profile

---

**Please fill out Section 1-7 above so I can design this correctly!** 🙏


---
**Logseq:** [[TTA.dev/Docs/Planning/Universal_llm_architecture_questions]]
