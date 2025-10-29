# AI Context Optimizer - Quick Start Guide

**Time to complete:** 5 minutes  
**Difficulty:** Beginner  
**Prerequisites:** Git, AI coding assistant (Copilot, Claude, Gemini, or Augment)

---

## What You'll Get

After this 5-minute setup, your AI assistant will:

✅ Automatically follow your project's coding standards  
✅ Use correct syntax and patterns for your tech stack  
✅ Suggest tests that match your testing framework  
✅ Apply security best practices automatically  
✅ Switch between specialized roles (backend, frontend, DevOps, etc.)

---

## Step 1: Choose Your Setup (30 seconds)

Pick the option that matches your needs:

### Option A: Basic Setup (Most Common)
**Best for:** General development with any AI assistant  
**What you get:** Project instructions + coding standards  
**Time:** 2 minutes

### Option B: Advanced Setup (Augment Users)
**Best for:** Augment CLI users wanting advanced features  
**What you get:** Everything + context management + Augster AI personality  
**Time:** 5 minutes

### Option C: Full Setup (Power Users)
**Best for:** Maximum flexibility and all features  
**What you get:** Everything from A and B  
**Time:** 3 minutes

---

## Step 2: Install (2-3 minutes)

Open your terminal and navigate to your project:

```bash
cd /path/to/your/project
```

### Option A: Basic Setup

```bash
# Copy the cross-platform primitives
cp -r /path/to/TTA.dev/packages/universal-agent-context/.github/ .
cp /path/to/TTA.dev/packages/universal-agent-context/AGENTS.md .

# Done! Verify it worked:
ls -la .github/instructions/
```

**Expected output:** You should see several `.instructions.md` files

### Option B: Advanced Setup (Augment CLI)

```bash
# Copy Augment-specific primitives
cp -r /path/to/TTA.dev/packages/universal-agent-context/.augment/ .
cp /path/to/TTA.dev/packages/universal-agent-context/apm.yml .

# Initialize context management (optional)
python .augment/context/cli.py new $(basename $(pwd))

# Done! Verify it worked:
ls -la .augment/instructions/
```

**Expected output:** You should see several `.instructions.md` files

### Option C: Full Setup

```bash
# Copy everything
cp -r /path/to/TTA.dev/packages/universal-agent-context/.github/ .
cp -r /path/to/TTA.dev/packages/universal-agent-context/.augment/ .
cp /path/to/TTA.dev/packages/universal-agent-context/AGENTS.md .
cp /path/to/TTA.dev/packages/universal-agent-context/apm.yml .

# Done! Verify it worked:
ls -la .github/instructions/ .augment/instructions/
```

**Expected output:** You should see instruction files in both directories

---

## Step 3: Test It (1 minute)

### Quick Test

1. **Open your AI assistant** (GitHub Copilot, Claude, etc.)
2. **Type this question:**
   ```
   What Python coding standards should I follow in this project?
   ```
3. **Expected response:** Your AI should mention:
   - Python 3.11+ syntax
   - Type hints with `str | None` (not `Optional[str]`)
   - Google-style docstrings
   - Testing with pytest
   - Specific patterns from your project

**If you see this, you're all set! ✅**

### Alternative Test (VS Code + Copilot)

1. Create a new Python file: `test_ai.py`
2. Start typing:
   ```python
   def process_user_data(
   ```
3. **Watch Copilot's suggestions** - they should follow your project standards

---

## Step 4: Explore Features (Optional)

### Try a Chat Mode

Chat modes give your AI assistant specialized knowledge for specific tasks.

**Available modes:**
- `backend-dev` - Backend development
- `frontend-dev` - Frontend development
- `devops` - DevOps and infrastructure
- `qa-engineer` - Testing and quality assurance
- `architect` - System architecture

**How to use (if supported by your AI):**
```
Switch to devops chat mode
Help me set up a CI/CD pipeline
```

### Use Context Management (Augment CLI only)

Track important context across sessions:

```bash
# Add important context
python .augment/context/cli.py add my-project "Working on user authentication feature" --importance 1.0

# View context
python .augment/context/cli.py show my-project

# Use in a session
# Context is automatically available to Augment
```

---

## Common Issues & Fixes

### Issue: "AI doesn't seem to use the instructions"

**Fix:**
1. Restart your AI assistant
2. Ensure files are in the right place: `.github/instructions/`
3. Try a specific question: "What's in the project instructions?"

### Issue: "Can't find the TTA.dev directory"

**Fix:**
```bash
# Clone it first
git clone https://github.com/theinterneti/TTA.dev
cd TTA.dev

# Now run the copy commands, replacing /path/to/TTA.dev with your actual path
```

### Issue: "Context CLI doesn't work"

**Fix:**
1. Check Python version: `python --version` (need 3.11+)
2. Ensure `.augment/` directory exists
3. Make script executable: `chmod +x .augment/context/cli.py`

---

## Next Steps

### Customize for Your Project

Edit instruction files to match your team's specific needs:

```bash
# Edit Python standards
vim .github/instructions/python-quality-standards.instructions.md

# Edit testing requirements
vim .github/instructions/testing-requirements.instructions.md

# Edit security guidelines
vim .github/instructions/api-security.instructions.md
```

### Learn More

- **[Full Rollout Documentation](AI_Context_Optimizer_Rollout.md)** - Complete guide
- **[Package README](../../packages/universal-agent-context/README.md)** - Detailed docs
- **[FAQ](AI_Context_Optimizer_Rollout.md#frequently-asked-questions)** - Common questions

### Get Help

- **Slack:** `#ai-context-optimizer`
- **Email:** dev-tools@company.com
- **GitHub:** [Create an issue](https://github.com/theinterneti/TTA.dev/issues)

---

## Tips for Success

### 1. Start Simple
Don't try to customize everything at once. Use the defaults first, then adjust.

### 2. Share Feedback
Found something that doesn't work? Let us know! Your feedback helps everyone.

### 3. Experiment
Try different chat modes and see what works best for your workflow.

### 4. Keep It Updated
When your team's standards change, update the instruction files.

### 5. Teach Others
Once you're comfortable, help your teammates get set up.

---

## Examples

### Example 1: Python Function with Instructions

**Without AI Context Optimizer:**
```python
# Your prompt: "Create a function to validate email"
# AI response:
def validate_email(email):
    return "@" in email
```

**With AI Context Optimizer:**
```python
# Your prompt: "Create a function to validate email"
# AI response:
def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
        
    Example:
        >>> validate_email("user@example.com")
        True
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
```

### Example 2: Using Chat Modes

**Switching to DevOps mode:**
```
User: "Switch to devops chat mode"
AI: "Switched to DevOps mode. I'll focus on infrastructure, deployment, and operations."

User: "Help me set up CI/CD"
AI: "I'll help you set up a CI/CD pipeline following your project standards..."
[Provides infrastructure-as-code, follows security boundaries, includes monitoring]
```

---

## Success Checklist

- [ ] Installed AI Context Optimizer in my project
- [ ] Verified installation by testing with my AI assistant
- [ ] AI assistant now follows project coding standards
- [ ] Tried at least one chat mode
- [ ] Know where to get help if needed
- [ ] Ready to customize for my specific needs

**All checked? Congratulations! You're now using the AI Context Optimizer! 🎉**

---

## Feedback

Help us improve this guide:
- **What was unclear?**
- **What took longer than expected?**
- **What additional examples would help?**

Submit feedback in `#ai-context-optimizer` or via email to dev-tools@company.com

---

**Last Updated:** 2025-10-29  
**Version:** 1.0.0  
**Support:** dev-tools@company.com
