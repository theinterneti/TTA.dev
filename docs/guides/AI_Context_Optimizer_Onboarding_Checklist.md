# AI Context Optimizer - Team Onboarding Checklist

**Purpose:** Track individual team member onboarding progress  
**Version:** 1.0.0  
**Last Updated:** 2025-10-29

---

## Team Member Information

**Name:** ___________________________  
**Role:** ___________________________  
**Primary AI Assistant:** ⬜ Copilot ⬜ Claude ⬜ Gemini ⬜ Augment ⬜ Other: __________  
**Onboarding Date:** ___________________________  
**Buddy/Mentor:** ___________________________  

---

## Phase 1: Pre-Installation (5 minutes)

### Understanding
- [ ] Read the [Team Announcement](AI_Context_Optimizer_Announcement.md)
- [ ] Watched overview video (if available) or reviewed [Quick Start Guide](AI_Context_Optimizer_Quick_Start.md)
- [ ] Understand what the AI Context Optimizer does
- [ ] Know where to get help (`#ai-context-optimizer` or dev-tools@company.com)

### Prerequisites Check
- [ ] Have at least one AI coding assistant installed
  - Which one(s)? ___________________________
- [ ] Have Git access to projects
- [ ] Have Python 3.11+ installed (for advanced features)
  - Version: `python --version` = ___________________________
- [ ] Identified first project to install in: ___________________________

**Estimated Time:** 5 minutes  
**Completed:** ⬜ Yes | Date: ___________

---

## Phase 2: Basic Installation (5 minutes)

### Choose Installation Type
- [ ] Decided on installation type:
  - ⬜ **Basic** (Cross-platform, `.github/` + `AGENTS.md`)
  - ⬜ **Advanced** (Augment CLI, `.augment/` + `apm.yml`)
  - ⬜ **Full** (Both approaches)

### Install Files
- [ ] Cloned or located TTA.dev repository
  - Path: ___________________________
- [ ] Navigated to target project directory
  - Path: ___________________________
- [ ] Copied required files using copy commands from guide
- [ ] Verified files exist:
  - [ ] `.github/instructions/` directory exists (Basic/Full)
  - [ ] `.github/chatmodes/` directory exists (Basic/Full)
  - [ ] `AGENTS.md` exists (Basic/Full)
  - [ ] `.augment/instructions/` directory exists (Advanced/Full)
  - [ ] `.augment/context/` directory exists (Advanced/Full)

### Commands Used
```bash
# Record the commands you ran:

___________________________
___________________________
___________________________
```

**Estimated Time:** 5 minutes  
**Completed:** ⬜ Yes | Date: ___________

---

## Phase 3: Verification (5 minutes)

### File Check
- [ ] Ran file verification:
  ```bash
  ls -la .github/instructions/
  # Should show multiple .instructions.md files
  ```
- [ ] Counted instruction files: ________ files found

### AI Assistant Test
- [ ] Restarted AI assistant
- [ ] Tested with question: "What Python coding standards should I follow in this project?"
- [ ] AI response mentioned project-specific standards: ⬜ Yes ⬜ No
- [ ] If No, followed troubleshooting steps: ⬜ Yes ⬜ N/A

### Code Generation Test
- [ ] Asked AI to generate a simple Python function
- [ ] Verified it used:
  - [ ] Python 3.11+ syntax (`str | None` not `Optional[str]`)
  - [ ] Type hints
  - [ ] Google-style docstrings
  - [ ] Proper imports

**Estimated Time:** 5 minutes  
**Completed:** ⬜ Yes | Date: ___________

---

## Phase 4: Exploration (15 minutes)

### Try Core Features
- [ ] Asked AI about testing standards
- [ ] Generated tests using project patterns
- [ ] Tried asking for code review based on project guidelines
- [ ] Experimented with at least 3 different prompts using project context

### Try Chat Modes (if supported)
- [ ] Tried switching to `backend-dev` mode
- [ ] Tried switching to `devops` mode
- [ ] Noticed difference in responses: ⬜ Yes ⬜ No ⬜ N/A

### Context Management (Advanced/Full only)
- [ ] Created project context session:
  ```bash
  python .augment/context/cli.py new my-project
  ```
- [ ] Added context to session
- [ ] Viewed session with `show` command

**Estimated Time:** 15 minutes  
**Completed:** ⬜ Yes | Date: ___________

---

## Phase 5: Real-World Usage (1-2 days)

### Day 1 Tasks
- [ ] Used AI Context Optimizer for at least 3 real work tasks
  1. Task: ___________________________ | Success: ⬜ Yes ⬜ No
  2. Task: ___________________________ | Success: ⬜ Yes ⬜ No
  3. Task: ___________________________ | Success: ⬜ Yes ⬜ No

### Day 2 Tasks
- [ ] Compared AI responses before and after (if possible)
- [ ] Noticed improvement in code quality: ⬜ Significant ⬜ Moderate ⬜ Minimal ⬜ None
- [ ] Estimated time saved: ⬜ 0-10% ⬜ 10-30% ⬜ 30-50% ⬜ 50%+

### Integration with Workflow
- [ ] Installed in primary project
- [ ] Installed in secondary project (if applicable)
- [ ] Comfortable using with daily development
- [ ] Know how to update/customize instructions

**Estimated Time:** 1-2 days  
**Completed:** ⬜ Yes | Date: ___________

---

## Phase 6: Customization (Optional, 30 minutes)

### Review Project Instructions
- [ ] Read through instruction files in `.github/instructions/`
- [ ] Identified instructions relevant to my work
- [ ] Identified instructions that could be improved

### Customize (Optional)
- [ ] Edited at least one instruction file for team needs
  - Which file: ___________________________
  - Changes made: ___________________________
- [ ] Tested changes with AI assistant
- [ ] Shared customizations with team: ⬜ Yes ⬜ No ⬜ N/A

### Create Custom Chat Mode (Optional)
- [ ] Created custom chat mode for specific role/task
  - Name: ___________________________
  - Purpose: ___________________________
- [ ] Tested custom chat mode
- [ ] Shared with team: ⬜ Yes ⬜ No ⬜ N/A

**Estimated Time:** 30 minutes  
**Completed:** ⬜ Yes | Date: ___________

---

## Phase 7: Knowledge Sharing (15 minutes)

### Documentation
- [ ] Read [Full Rollout Guide](AI_Context_Optimizer_Rollout.md)
- [ ] Reviewed [Troubleshooting Guide](AI_Context_Optimizer_Troubleshooting.md)
- [ ] Bookmarked documentation for future reference

### Attend Training
- [ ] Attended live training session
  - Date: ___________________________
  - Key takeaways: ___________________________
- [ ] Watched recording (if missed live): ⬜ Yes ⬜ N/A
- [ ] Asked questions during Q&A: ⬜ Yes ⬜ No

### Help Others
- [ ] Helped at least one teammate with installation
- [ ] Shared tip or best practice in `#ai-context-optimizer`
- [ ] Provided feedback on documentation

**Estimated Time:** 15 minutes + training session  
**Completed:** ⬜ Yes | Date: ___________

---

## Phase 8: Feedback & Assessment (10 minutes)

### Complete Survey
- [ ] Completed post-installation survey
- [ ] Provided specific feedback on:
  - [ ] Installation process
  - [ ] Documentation quality
  - [ ] Feature usefulness
  - [ ] Suggested improvements

### Self-Assessment
Rate your experience (1-5, 5 = excellent):
- **Ease of installation:** ⬜1 ⬜2 ⬜3 ⬜4 ⬜5
- **Documentation clarity:** ⬜1 ⬜2 ⬜3 ⬜4 ⬜5
- **Feature usefulness:** ⬜1 ⬜2 ⬜3 ⬜4 ⬜5
- **AI response improvement:** ⬜1 ⬜2 ⬜3 ⬜4 ⬜5
- **Time saved:** ⬜1 ⬜2 ⬜3 ⬜4 ⬜5
- **Overall satisfaction:** ⬜1 ⬜2 ⬜3 ⬜4 ⬜5

### Open Feedback
**What worked well:**
___________________________
___________________________
___________________________

**What could be improved:**
___________________________
___________________________
___________________________

**Unexpected benefits:**
___________________________
___________________________
___________________________

**Challenges encountered:**
___________________________
___________________________
___________________________

**Estimated Time:** 10 minutes  
**Completed:** ⬜ Yes | Date: ___________

---

## Completion Status

### Overall Progress
- [ ] **Phase 1:** Pre-Installation ✓
- [ ] **Phase 2:** Basic Installation ✓
- [ ] **Phase 3:** Verification ✓
- [ ] **Phase 4:** Exploration ✓
- [ ] **Phase 5:** Real-World Usage ✓
- [ ] **Phase 6:** Customization (Optional) ✓
- [ ] **Phase 7:** Knowledge Sharing ✓
- [ ] **Phase 8:** Feedback & Assessment ✓

### Onboarding Complete
- [ ] **All required phases complete**
- [ ] **Using AI Context Optimizer daily**
- [ ] **Comfortable troubleshooting issues**
- [ ] **Can help other team members**

**Completion Date:** ___________________________  
**Verified By:** ___________________________  
**Signature:** ___________________________

---

## Issues Encountered

If you encountered any issues during onboarding, document them here:

### Issue 1
**Problem:** ___________________________  
**When:** ___________________________  
**Resolution:** ___________________________  
**Time to resolve:** ___________________________

### Issue 2
**Problem:** ___________________________  
**When:** ___________________________  
**Resolution:** ___________________________  
**Time to resolve:** ___________________________

### Issue 3
**Problem:** ___________________________  
**When:** ___________________________  
**Resolution:** ___________________________  
**Time to resolve:** ___________________________

---

## Tips for Success

1. **Start Small** - Install in one project first, get comfortable, then expand
2. **Ask Questions** - Use `#ai-context-optimizer` for any questions
3. **Experiment** - Try different prompts and chat modes
4. **Customize** - Adjust instructions to match your workflow
5. **Share** - Help teammates and share your learnings
6. **Provide Feedback** - Your input improves the system for everyone

---

## Resources

- **[Quick Start Guide](AI_Context_Optimizer_Quick_Start.md)** - 5-minute setup
- **[Full Rollout Guide](AI_Context_Optimizer_Rollout.md)** - Complete documentation
- **[Troubleshooting Guide](AI_Context_Optimizer_Troubleshooting.md)** - Common issues
- **[Team Announcement](AI_Context_Optimizer_Announcement.md)** - Overview and benefits
- **[Package README](../../packages/universal-agent-context/README.md)** - Technical details

### Support
- **Slack:** `#ai-context-optimizer`
- **Email:** dev-tools@company.com
- **Office Hours:** Daily 2-3 PM during rollout
- **Buddy/Mentor:** ___________________________

---

## Notes

Use this space for any additional notes, observations, or reminders:

___________________________
___________________________
___________________________
___________________________
___________________________

---

**Document Version:** 1.0.0  
**Last Updated:** 2025-10-29  
**Maintained By:** Development Team Lead
