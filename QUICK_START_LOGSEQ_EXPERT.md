# 🎯 Quick Reference: Using the Logseq Documentation Expert

**Copy this into your next session to activate the mode:**

---

## 📋 The Prompt (Copy-Paste This)

```text
I need you to become a Logseq documentation expert for my TTA.dev project.

Your role is to help me maintain high-quality Logseq documentation by:
1. Analyzing my Logseq markdown files for common issues
2. Identifying formatting problems, broken links, and structural issues
3. Suggesting fixes and improvements
4. Optionally applying fixes automatically

Context:
- My Logseq graph is located at: `/home/thein/repos/TTA.dev/logseq/`
- I have a custom documentation assistant tool at: `local/logseq-tools/doc_assistant.py`
- The tool can analyze files, detect issues, score quality (0-100), and auto-fix problems

When I ask you to "check my documentation" or "fix my docs", you should:
1. Run the doc_assistant.py tool to analyze all files
2. Show me the quality scores and issues found
3. Explain what the issues mean and why they matter
4. Offer to fix issues (showing what will change first)
5. Apply fixes if I approve

Start by running an analysis of my current Logseq documentation and tell me what you find.
```

---

## 🚀 What Happens Next

The AI will:

1. ✅ Become your Logseq documentation expert
2. ✅ Run: `python3 local/logseq-tools/doc_assistant.py logseq/`
3. ✅ Show quality scores for each file
4. ✅ List issues found (errors, warnings, info)
5. ✅ Prioritize what to fix first
6. ✅ Offer to fix issues with your permission

---

## 💬 Example Session

**You:** (Paste the prompt above)

**AI:** "I'm your Logseq documentation expert. Let me check your docs..."
[Runs analysis]
"📊 Analysis Results: ✅ Analyzed 4 files, ⭐ Average score: 87.3/100"
[Shows detailed breakdown]
"Would you like me to fix AI Research.md (lowest score)?"

**You:** "Yes, fix it"

**AI:** [Shows what will change]
"Should I apply these 5 fixes?"

**You:** "Yes"

**AI:** [Applies fixes]
"✅ Fixed! Score improved: 78.5 → 94.8 (+16.3 points)"
"Would you like me to continue with the next file?"

---

## 🎨 Alternative Prompts

### Quick Check

```text
Run the Logseq documentation assistant on my docs and show me the quality scores.
```

### Detailed Review

```text
I need a detailed analysis of my Logseq documentation quality. Check all pages and journals, show me the issues, and prioritize what needs fixing first.
```

### Auto-Fix Mode

```text
You're my Logseq documentation maintainer. Analyze my docs, identify all fixable issues, and batch-fix them (with my approval).
```

---

## 📊 What Gets Analyzed

### Issue Types

**🔴 Errors (Fix Immediately)**

- Task status not uppercase (`todo` → `TODO`)
- Missing space after `#` in headings
- Unclosed code blocks

**⚠️ Warnings (Should Fix)**

- Skipped heading levels (`#` → `###`)
- Missing blank lines around lists
- Code blocks missing language specifier

**ℹ️ Info (Nice to Fix)**

- Bare URLs that should be wrapped

### Quality Scores

- **90-100**: Excellent ⭐⭐⭐
- **75-89**: Good ⭐⭐
- **60-74**: Acceptable ⭐
- **Below 60**: Needs work ⚠️

---

## 🛡️ Safety Features

The AI will:

- ✅ Always show what will change before applying fixes
- ✅ Ask permission before modifying files
- ✅ Preserve all content (only fix formatting)
- ✅ Re-analyze after fixes to verify improvement
- ✅ Never delete or change meaning of content

---

## 📖 Full Documentation

- **Complete Prompt:** `local/.prompts/logseq-doc-expert.md`
- **Prompt Library:** `local/.prompts/README.md`
- **Summary:** `PROMPT_LIBRARY_COMPLETE.md`

---

## 🎯 Ready to Use?

1. **Open new chat** with your AI assistant
2. **Copy** the prompt from "📋 The Prompt" section above
3. **Paste** into the chat
4. **Follow** the AI's guidance
5. **Enjoy** better documentation quality!

---

**Pro Tip:** Bookmark this file or keep it open in a tab for easy access when starting new sessions!

---

**Last Updated:** 2025-10-30
**Version:** 1.0
**Status:** ✅ Ready for Use
