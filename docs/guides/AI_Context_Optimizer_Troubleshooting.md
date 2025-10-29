# AI Context Optimizer - Troubleshooting & Extended FAQ

**Version:** 1.0.0  
**Last Updated:** 2025-10-29  
**Support:** dev-tools@company.com | `#ai-context-optimizer`

---

## Table of Contents

1. [Common Issues](#common-issues)
2. [Installation Problems](#installation-problems)
3. [Usage Issues](#usage-issues)
4. [Advanced Troubleshooting](#advanced-troubleshooting)
5. [Extended FAQ](#extended-faq)
6. [Platform-Specific Issues](#platform-specific-issues)

---

## Common Issues

### Issue: AI Assistant Not Using Instructions

**Symptoms:**
- AI gives generic responses
- Doesn't follow project coding standards
- Doesn't reference project-specific patterns

**Solutions:**

1. **Verify Installation**
   ```bash
   # Check if files exist
   ls -la .github/instructions/
   ls -la .github/chatmodes/
   cat AGENTS.md
   ```
   Expected: Multiple `.instructions.md` files should be present

2. **Restart AI Assistant**
   - **VS Code:** Reload window (Cmd/Ctrl + Shift + P → "Reload Window")
   - **Claude Desktop:** Quit and reopen application
   - **Augment:** Restart Augment service
   - **Cursor:** Restart application

3. **Test Explicitly**
   Ask: "List the instruction files you can see in this project"
   
   If AI can't see them:
   - Check file permissions: `chmod 644 .github/instructions/*.md`
   - Ensure no `.gitignore` is blocking `.github/` directory
   - Verify files are committed to git (if working in a repo)

4. **Check YAML Frontmatter**
   Open an instruction file and verify YAML syntax:
   ```yaml
   ---
   title: "Python Quality Standards"
   applyTo: ["**/*.py"]
   security_level: LOW
   ---
   ```
   
   Common YAML errors:
   - Missing closing `---`
   - Invalid YAML syntax (use a YAML validator)
   - Wrong quotes or indentation

### Issue: Context Management CLI Not Working

**Symptoms:**
- `python .augment/context/cli.py` returns errors
- "No such file or directory" error
- CLI crashes or hangs

**Solutions:**

1. **Check Python Version**
   ```bash
   python --version  # Should be 3.11 or higher
   
   # If wrong version, try:
   python3 --version
   python3.11 --version
   ```
   
   Use the correct Python binary:
   ```bash
   python3.11 .augment/context/cli.py new my-project
   ```

2. **Verify Installation**
   ```bash
   # Check if .augment directory exists
   ls -la .augment/
   
   # Check if CLI file exists
   ls -la .augment/context/cli.py
   
   # Make executable
   chmod +x .augment/context/cli.py
   ```

3. **Check Dependencies**
   ```bash
   # Install required packages
   pip install pyyaml  # or uv pip install pyyaml
   ```

4. **Test with Simple Command**
   ```bash
   python .augment/context/cli.py --help
   ```
   Should show help message

### Issue: Chat Modes Not Activating

**Symptoms:**
- Asking to switch chat modes doesn't work
- AI doesn't behave differently in different modes
- "Unknown chat mode" errors

**Solutions:**

1. **Check Your AI Assistant Support**
   Not all AI assistants support chat modes:
   - ✅ **Augment CLI:** Full support
   - ⚠️ **Claude:** Limited support (manual prompting)
   - ⚠️ **Copilot:** Limited support (via comments)
   - ⚠️ **Gemini:** Limited support (manual prompting)

2. **Verify Chat Mode Files**
   ```bash
   ls -la .github/chatmodes/
   # or
   ls -la .augment/chatmodes/
   ```
   
   Expected files:
   - `backend-dev.chatmode.md`
   - `frontend-dev.chatmode.md`
   - `devops.chatmode.md`
   - etc.

3. **Manual Mode Switching**
   For AI assistants without native support, use explicit prompts:
   ```
   Act as a DevOps engineer specializing in infrastructure-as-code,
   CI/CD pipelines, and monitoring. Follow the guidelines in 
   .github/chatmodes/devops.chatmode.md
   ```

4. **Check YAML Frontmatter**
   Open a chat mode file and verify:
   ```yaml
   ---
   title: "Backend Developer"
   role: "Backend Engineer"
   expertise: ["Python", "APIs", "Databases"]
   mcp_tools_allowed: ["file_read", "code_search"]
   security_level: MEDIUM
   ---
   ```

---

## Installation Problems

### Problem: Can't Find TTA.dev Repository

**Solution:**
```bash
# Clone the repository first
git clone https://github.com/theinterneti/TTA.dev
cd TTA.dev

# Verify you have the right path
pwd  # Should end with /TTA.dev

# Now copy files
cp -r packages/universal-agent-context/.github/ /path/to/your/project/
```

### Problem: Permission Denied When Copying

**Solution:**
```bash
# Check permissions on source
ls -la /path/to/TTA.dev/packages/universal-agent-context/

# If permission denied, use sudo (with caution)
sudo cp -r packages/universal-agent-context/.github/ /path/to/your/project/

# Fix ownership after copying
sudo chown -R $USER:$USER /path/to/your/project/.github/
```

### Problem: Files Already Exist

**Symptoms:**
```
cp: .github/ already exists
```

**Solution:**
```bash
# Option 1: Backup existing files
mv .github .github.backup
mv AGENTS.md AGENTS.md.backup

# Then copy new files
cp -r /path/to/TTA.dev/packages/universal-agent-context/.github/ .
cp /path/to/TTA.dev/packages/universal-agent-context/AGENTS.md .

# Option 2: Merge (advanced)
# Manually merge existing files with new files
```

### Problem: Installation on Windows

**Symptoms:**
- Path issues
- Copy commands don't work
- Line ending problems

**Solution:**
```powershell
# Use PowerShell (not CMD)
cd C:\path\to\your\project

# Copy with PowerShell
Copy-Item -Recurse -Path "C:\path\to\TTA.dev\packages\universal-agent-context\.github" -Destination "."
Copy-Item -Path "C:\path\to\TTA.dev\packages\universal-agent-context\AGENTS.md" -Destination "."

# Or use Git Bash for Unix-style commands
```

---

## Usage Issues

### Issue: AI Gives Wrong Type Hints

**Symptom:**
AI still suggests `Optional[str]` instead of `str | None`

**Solution:**
1. Restart AI assistant
2. Explicitly reference instructions:
   ```
   Follow the Python quality standards from .github/instructions/
   Use Python 3.11+ union syntax (str | None)
   ```
3. Check instruction file exists:
   ```bash
   cat .github/instructions/python-quality-standards.instructions.md
   ```

### Issue: AI Doesn't Use Project Testing Patterns

**Symptom:**
AI suggests generic tests instead of using MockPrimitive

**Solution:**
1. Explicitly ask:
   ```
   Write tests using MockPrimitive from our testing utilities
   Follow the patterns in .github/instructions/testing-requirements.instructions.md
   ```
2. Provide example:
   ```
   Write tests like this:
   [paste example from instruction file]
   ```

### Issue: Inconsistent Behavior Across AI Assistants

**Symptom:**
Works great in Claude, but not in Copilot

**Reason:** Different AI assistants load context differently

**Solutions:**
- **GitHub Copilot:** Relies heavily on `.github/copilot-instructions.md`
  - Ensure this file exists and references other instructions
  - Use inline comments to guide: `# Follow our Python standards`
  
- **Claude:** Loads all markdown files in `.github/`
  - Should work automatically
  - Restart if needed
  
- **Augment:** Uses `.augment/` directory
  - Need `.augment/` setup, not just `.github/`
  
- **Gemini:** Loads `AGENTS.md` and `.github/`
  - Ensure both exist

---

## Advanced Troubleshooting

### Debug Mode

Enable verbose logging:

```bash
# For Augment context CLI
DEBUG=1 python .augment/context/cli.py show my-project

# Check AI assistant logs
# VS Code: Help → Toggle Developer Tools → Console
# Claude Desktop: View → Toggle Developer Tools
```

### Validate YAML Files

```bash
# Install YAML validator
pip install yamllint

# Check all instruction files
yamllint .github/instructions/*.md
yamllint .augment/instructions/*.md

# Check chat modes
yamllint .github/chatmodes/*.md
```

### Test Instruction Loading

Create a test script:

```python
# test_instructions.py
import os
import glob

def test_instructions():
    paths = [
        ".github/instructions/*.md",
        ".github/chatmodes/*.md",
        "AGENTS.md"
    ]
    
    for pattern in paths:
        files = glob.glob(pattern)
        print(f"\n{pattern}:")
        for f in files:
            size = os.path.getsize(f)
            print(f"  ✓ {f} ({size} bytes)")
    
if __name__ == "__main__":
    test_instructions()
```

Run: `python test_instructions.py`

### Check File Encoding

```bash
# Ensure UTF-8 encoding
file -I .github/instructions/*.md

# Should show: text/plain; charset=utf-8

# Fix if needed (on macOS/Linux)
for f in .github/instructions/*.md; do
    iconv -f ISO-8859-1 -t UTF-8 "$f" > "$f.tmp"
    mv "$f.tmp" "$f"
done
```

---

## Extended FAQ

### General Questions

**Q: Can I use this with multiple projects?**  
A: Yes! Install in each project separately. Each gets its own configuration.

**Q: Will this increase my AI API costs?**  
A: No significant increase. Context is loaded once, not per request.

**Q: Can I use this in a monorepo?**  
A: Yes! Install at the monorepo root, or per-package if different standards apply.

**Q: Does this work with private/enterprise AI instances?**  
A: Yes, as long as the AI can read local files in your project.

**Q: Can I version control the instructions?**  
A: Absolutely! Commit `.github/` and `AGENTS.md` to git. This way the whole team shares the same context.

### Customization Questions

**Q: How do I add team-specific instructions?**  
A: 
```bash
# Create new instruction file
cat > .github/instructions/team-customs.instructions.md << 'EOF'
---
title: "Team Custom Standards"
applyTo: ["**/*.py", "**/*.ts"]
security_level: LOW
---

# Team-Specific Standards

- Always use our custom logger: `from myapp.logging import logger`
- Database migrations must include rollback procedures
- API endpoints must have rate limiting
EOF
```

**Q: How do I disable certain instructions?**  
A: 
1. Rename file: `.instructions.md.disabled`
2. Or modify `applyTo: []` to never match

**Q: Can I create project-specific chat modes?**  
A: Yes!
```bash
# Create custom chat mode
cat > .github/chatmodes/my-specialist.chatmode.md << 'EOF'
---
title: "My Specialist Role"
role: "Domain Expert"
expertise: ["domain-specific", "patterns"]
---

# My Specialist

You are an expert in [your domain]...
EOF
```

### Integration Questions

**Q: Does this work with existing `.github/copilot-instructions.md`?**  
A: Yes! The new system extends it. Keep your existing file.

**Q: Can I integrate with CI/CD?**  
A: Yes! Instructions can reference CI/CD patterns:
```yaml
# In instruction file
---
title: "CI/CD Standards"
applyTo: [".github/workflows/*.yml"]
---

- All workflows must have timeout
- Use cached dependencies
- Include security scanning
```

**Q: Does this work with Docker containers?**  
A: Yes! Copy instructions into container or mount as volume:
```dockerfile
COPY .github/ /app/.github/
COPY AGENTS.md /app/AGENTS.md
```

### Security Questions

**Q: Are my instructions secure?**  
A: Instructions are local files in your project. Same security as any other project file.

**Q: Can I use different security levels?**  
A: Yes! Set in YAML frontmatter:
```yaml
security_level: LOW   # General guidelines
security_level: MEDIUM  # Sensitive operations
security_level: HIGH  # Critical security
```

**Q: Should I commit instructions to git?**  
A: Yes, recommended. They contain no secrets, just guidance.

---

## Platform-Specific Issues

### VS Code + Copilot

**Issue: Copilot not using instructions**
```bash
# Ensure .github/copilot-instructions.md exists
cat .github/copilot-instructions.md

# Reload VS Code
# Cmd/Ctrl + Shift + P → "Reload Window"

# Check Copilot status
# Cmd/Ctrl + Shift + P → "GitHub Copilot: Check Status"
```

### Claude Desktop

**Issue: Claude not seeing files**
```bash
# Ensure Claude has file system access
# Claude → Preferences → Privacy → Enable file system access

# Restart Claude
# Quit application completely and reopen
```

### Augment CLI

**Issue: Augment not loading context**
```bash
# Check Augment config
cat ~/.augment/config.yml

# Verify project context
python .augment/context/cli.py show $(basename $(pwd))

# Restart Augment service
augment restart
```

### Cursor IDE

**Issue: Context not loading**
```bash
# Cursor uses similar structure to Copilot
# Ensure .github/ directory exists
ls -la .github/

# Restart Cursor
# File → Quit, then reopen
```

---

## Still Having Issues?

### Quick Diagnostic

Run this diagnostic script:

```bash
#!/bin/bash
echo "=== AI Context Optimizer Diagnostic ==="
echo ""
echo "1. Checking directory structure..."
[ -d ".github" ] && echo "✓ .github/ exists" || echo "✗ .github/ missing"
[ -d ".github/instructions" ] && echo "✓ .github/instructions/ exists" || echo "✗ .github/instructions/ missing"
[ -d ".github/chatmodes" ] && echo "✓ .github/chatmodes/ exists" || echo "✗ .github/chatmodes/ missing"
[ -f "AGENTS.md" ] && echo "✓ AGENTS.md exists" || echo "✗ AGENTS.md missing"
echo ""
echo "2. Checking instruction files..."
ls -1 .github/instructions/*.md 2>/dev/null | wc -l | xargs echo "Instruction files:"
echo ""
echo "3. Checking Python version..."
python --version
echo ""
echo "4. Checking file permissions..."
ls -la .github/instructions/ | head -5
```

Save as `diagnostic.sh`, run: `bash diagnostic.sh`

### Get Help

If diagnostics show issues:

1. **Slack:** Post output in `#ai-context-optimizer`
2. **Email:** Send diagnostic output to dev-tools@company.com
3. **GitHub:** [Create issue](https://github.com/theinterneti/TTA.dev/issues) with diagnostic output

---

## Feedback

Help us improve this troubleshooting guide:
- What issues did you encounter?
- What solutions worked for you?
- What's missing from this guide?

**Submit feedback:** `#ai-context-optimizer` or dev-tools@company.com

---

**Last Updated:** 2025-10-29  
**Version:** 1.0.0  
**Support:** dev-tools@company.com | `#ai-context-optimizer`
