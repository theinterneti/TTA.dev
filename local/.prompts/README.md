# TTA.dev Prompt Library

**Version:** 1.0
**Created:** 2025-10-30
**Purpose:** Reusable AI agent prompts for specialized modes

---

## 📚 Overview

This directory contains **curated prompts** for activating specialized AI agent modes in TTA.dev development. Each prompt is:

- **Tested**: Used successfully in real sessions
- **Documented**: Complete with context, tools, and examples
- **Reusable**: Copy-paste ready for new chat sessions
- **Versioned**: Tracked improvements over time

---

## 🎯 Available Prompts

### 1. Logseq Documentation Expert

**File:** [`logseq-doc-expert.md`](logseq-doc-expert.md)
**Version:** 1.0
**Category:** Documentation Quality
**Difficulty:** ⭐⭐ Intermediate

**What it does:**
- Analyzes Logseq markdown files for quality issues
- Identifies formatting problems, broken links, task syntax
- Scores documentation quality (0-100)
- Auto-fixes issues with permission

**When to use:**
- Need to improve Logseq documentation quality
- Want to fix formatting inconsistencies
- Need to validate task syntax
- Want quality reports

**Quick start:**
```text
I need you to become a Logseq documentation expert for my TTA.dev project. Start by analyzing my docs at logseq/ and tell me what you find.
```

**Tools required:**
- `local/logseq-tools/doc_assistant.py`
- Python 3.11+
- Access to `logseq/` directory

---

## 📖 How to Use This Library

### Starting a New Session

1. **Pick a prompt** from the list above
2. **Open the prompt file** (e.g., `logseq-doc-expert.md`)
3. **Copy the "Primary Prompt"** section
4. **Paste into new chat** with your AI assistant
5. **Follow the interaction examples** for guidance

### Example Workflow

```text
You (in new chat): "I need you to become a Logseq documentation expert for my TTA.dev project..."

AI: "I'm your Logseq documentation expert. Let me check your docs..."
[Runs analysis]
[Shows results]
[Offers to fix issues]

You: "Fix AI Research.md"

AI: [Shows detailed issues, suggests fixes, applies with permission]
```

### Customizing Prompts

Each prompt can be customized by:
- Changing file paths
- Adjusting quality thresholds
- Adding custom rules
- Modifying fix strategies

See the "Advanced Capabilities" section in each prompt.

---

## 🏗️ Prompt Structure

Every prompt follows this structure:

```markdown
# [Agent Mode Name] Prompt

## 🎯 Primary Prompt
The main prompt to copy-paste

## 📋 Alternative Entry Points
Shorter versions for quick activation

## 🛠️ Tool Instructions
Commands and APIs needed

## 📊 [Domain-Specific Content]
Reference info for this mode

## 🎯 Your Responsibilities
What the AI should do

## 💡 Example Interactions
Real conversation examples

## 🎨 Advanced Capabilities
Optional features

## 🚨 Important Constraints
What NOT to do

## 📚 Knowledge Base
Domain knowledge needed

## 🔄 Workflow
Step-by-step process

## 🎯 Success Criteria
How to know it's working

## 📖 Quick Reference
Commands and files
```

---

## 🎨 Prompt Categories

### Documentation & Quality

- **Logseq Documentation Expert** - Analyze and fix Logseq docs
- *[Future]* Markdown Linter - General markdown quality
- *[Future]* API Documentation Reviewer - OpenAPI/docstrings

### Development & Code

- *[Future]* Primitive Developer - Build workflow primitives
- *[Future]* Test Writer - Generate comprehensive tests
- *[Future]* Type Safety Enforcer - Add/fix type hints

### Architecture & Design

- *[Future]* Architecture Reviewer - Evaluate design decisions
- *[Future]* Integration Planner - Plan cross-package features
- *[Future]* Observability Designer - Add tracing/metrics

### Operations & DevOps

- *[Future]* Release Manager - Prepare releases
- *[Future]* CI/CD Optimizer - Improve workflows
- *[Future]* Docker Composer - Container orchestration

### Research & Exploration

- *[Future]* MCP Server Scout - Find and evaluate MCP servers
- *[Future]* LLM Router Optimizer - Improve routing decisions
- *[Future]* Performance Analyzer - Identify bottlenecks

---

## 📝 Creating New Prompts

### Template

Use this template for new prompts:

```markdown
# [Mode Name] Prompt

**Version:** 1.0
**Created:** YYYY-MM-DD
**Category:** [Category]
**Difficulty:** [Easy/Intermediate/Advanced]

## 🎯 Primary Prompt
[Copy-paste ready prompt]

## 📋 Alternative Entry Points
[Shorter versions]

## 🛠️ Tool Instructions
[Commands and APIs]

## [Domain Sections]
[Add relevant sections]

## 💡 Example Interactions
[Real examples]

## 🎯 Success Criteria
[How to measure success]
```

### Checklist

Before adding a new prompt:

- [ ] Test in real session first
- [ ] Document all required tools
- [ ] Include at least 3 example interactions
- [ ] Define success criteria
- [ ] Add to Available Prompts list
- [ ] Specify difficulty level
- [ ] Include version number

---

## 🔄 Prompt Evolution

### Versioning

- **1.0**: Initial tested version
- **1.1**: Minor improvements (examples, clarity)
- **2.0**: Major changes (new capabilities, tools)

### Feedback Loop

1. Use prompt in session
2. Note what worked/didn't work
3. Update prompt file
4. Increment version
5. Document changes at top

### Change Log Format

Add to top of prompt file:

```markdown
## Change Log

### 1.1 (2025-11-15)
- Added example for batch processing
- Clarified safety rules
- Fixed example output format

### 1.0 (2025-10-30)
- Initial release
- Tested on 4 documentation files
- 90.7/100 average quality score
```

---

## 🎯 Best Practices

### Writing Prompts

1. **Be specific**: Include exact commands and paths
2. **Show examples**: Real interactions > descriptions
3. **Set constraints**: What the AI should NOT do
4. **Test first**: Never release untested prompts
5. **Version carefully**: Breaking changes = major version bump

### Using Prompts

1. **Read fully**: Understand capabilities before using
2. **Customize**: Adjust paths/settings for your needs
3. **Start simple**: Use Primary Prompt first
4. **Provide feedback**: Update prompt based on experience
5. **Share improvements**: Commit better versions

### Maintaining Quality

1. **Review quarterly**: Are prompts still accurate?
2. **Update dependencies**: Tool paths, commands, APIs
3. **Archive obsolete**: Move to `archive/` if no longer relevant
4. **Cross-reference**: Link related prompts
5. **Document gaps**: Note missing capabilities

---

## 📂 Directory Structure

```text
local/.prompts/
├── README.md                    # This file
├── logseq-doc-expert.md         # Logseq documentation analyzer
├── [future-prompt].md           # Future prompts
├── templates/
│   └── prompt-template.md       # Template for new prompts
└── archive/
    └── [obsolete-prompts].md    # Deprecated prompts
```

---

## 🤝 Contributing

### Adding a Prompt

1. Create prompt file: `local/.prompts/your-prompt.md`
2. Follow template structure
3. Test in real session
4. Add to "Available Prompts" in this README
5. Commit with message: `feat(prompts): add [mode name] prompt`

### Improving a Prompt

1. Use prompt in session
2. Note improvements needed
3. Update prompt file
4. Increment version
5. Add change log entry
6. Commit with message: `chore(prompts): improve [mode name] v1.x`

---

## 📊 Metrics

### Prompt Library Stats

- **Total prompts**: 1
- **Categories**: 1 (Documentation & Quality)
- **Average version**: 1.0
- **Last updated**: 2025-10-30

### Usage Stats

Track these in your sessions:
- Times used
- Success rate
- Average session length
- Common customizations

---

## 🔗 Related Resources

### TTA.dev Documentation

- [Local Development Setup](../LOCAL_DEVELOPMENT_SETUP.md)
- [Quick Start Guide](../../QUICK_START_LOCAL.md)
- [Agent Instructions](../../AGENTS.md)

### Tools

- [Logseq Tools](../logseq-tools/)
- [Experiments](../experiments/)
- [Utilities](../utilities/)

### External

- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [AI Agent Design Patterns](https://arxiv.org/abs/2308.11432)

---

## 🎓 Learning Path

### Beginner

1. Start with Logseq Documentation Expert (⭐⭐)
2. Customize paths and thresholds
3. Try alternative entry points
4. Use in 3-5 sessions

### Intermediate

1. Create custom rules for your prompts
2. Combine multiple prompts in sequence
3. Track quality metrics over time
4. Contribute improvements

### Advanced

1. Design new prompt categories
2. Build prompt chains (output of one → input of next)
3. Create domain-specific variations
4. Write prompt templates

---

## ❓ FAQ

### Q: Can I modify prompts?

Yes! Prompts are templates. Customize for your needs, but consider contributing improvements back.

### Q: How do I know which prompt to use?

Check the "Category" and "When to use" sections. Start with what matches your current task.

### Q: What if a prompt doesn't work?

1. Check tool dependencies are installed
2. Verify file paths are correct
3. Try alternative entry points
4. Open an issue or update the prompt

### Q: Can I share prompts outside TTA.dev?

Yes, but they're designed for this monorepo structure. You'll need to adapt paths and tools.

### Q: How often should I update prompts?

Update when:
- Tools change
- You find better approaches
- Examples become outdated
- Version bumps happen

---

## 🚀 Quick Start

### First Time User

1. Read this README
2. Open `logseq-doc-expert.md`
3. Copy the "Primary Prompt" section
4. Start new chat with your AI assistant
5. Paste prompt and begin

### Regular User

1. Browse available prompts
2. Pick one matching your task
3. Copy primary or alternative prompt
4. Customize if needed
5. Use in session

### Advanced User

1. Chain multiple prompts
2. Create custom variations
3. Track quality metrics
4. Contribute new prompts

---

## 📘 Advanced Documentation

### Prompt Library Integration Guide

For a comprehensive understanding of how prompts integrate with TTA.dev's Agent Primitives framework and act as orchestrating blueprints for Agentic Workflows, see:

**[`docs/guides/prompt-library-integration-guide.md`](../../docs/guides/prompt-library-integration-guide.md)**

This guide covers:

- **Prompts as Agent Primitives** - How `.prompt.md` files are configurable, reusable building blocks
- **Integration Mechanisms** - How prompt files orchestrate context, roles, tools, and validation
- **Agent Package Manager (APM)** - Managing and distributing prompt libraries as shareable software
- **Production Deployment** - Using prompts in CI/CD pipelines
- **TTA.dev Evolution Path** - Current implementation vs future vision

---

**Last Updated:** 2025-10-30
**Maintainer:** TTA.dev Team
**Status:** Active Development
**Version:** 1.0
