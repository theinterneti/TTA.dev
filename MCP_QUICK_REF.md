# MCP Servers Quick Reference Card

## ✅ READY TO USE (Just Reload VS Code!)

### 1. Sequential Thinking
```
@workspace Use sequential thinking to [analyze | break down | reason about] ...
```
**For:** Complex problems, architecture decisions, multi-step analysis

### 2. Serena - Semantic Code Agent
```
@workspace Activate Serena and [find | search | analyze] ...
@workspace Use Serena to find all references to [symbol name]
@workspace Query Serena for project structure
```
**For:** Code navigation, symbol search, refactoring, project understanding

## ⚠️ NEEDS TOKEN

### 3. LogSeq - Knowledge Base
**Setup Required:**
1. Start LogSeq
2. Settings → Advanced → Enable "Developer mode"
3. Settings → Features → Enable "Enable HTTP APIs server"
4. Restart LogSeq
5. Click API (🔌) → Start server
6. API panel → Authorization → Add token → Copy token
7. Edit `~/.config/mcp/mcp_settings.json`:
   ```json
   "mcp-logseq": {
     "command": "/usr/bin/npx",
     "args": ["-y", "@ergut/mcp-logseq"],
     "env": {
       "LOGSEQ_API_TOKEN": "YOUR_TOKEN_HERE",
       "LOGSEQ_API_URL": "http://127.0.0.1:12315"
     },
     "disabled": false
   }
   ```
8. Reload VS Code

---

## 🎯 Action Required

**RIGHT NOW:**
```
Ctrl+Shift+P → "Developer: Reload Window"
```

**THEN TEST:**
```
@workspace Use sequential thinking to explain how Serena enhances our development workflow
```

**LATER:**
- Complete LogSeq token setup (see above)

---

## 📚 Documentation

- Full Setup: `MCP_SETUP_COMPLETE.md`
- Quick Start: `docs/MCP_SETUP_QUICKSTART.md`
- All MCP Servers: `MCP_SERVERS.md`
- Serena Project: `.serena/project.yml`
