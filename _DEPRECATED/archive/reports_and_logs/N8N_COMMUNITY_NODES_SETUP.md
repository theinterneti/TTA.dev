# n8n Community Nodes Setup for TTA.dev

## Problem Solved

If you see this error when importing workflows:
```
Unrecognized node type: @n8n/n8n-nodes-langchain.lmChatGemini
```

This means the LangChain community nodes package is not installed.

---

## Solution: Install LangChain Nodes

### Quick Fix

```bash
# Install the community nodes package
npm install -g @n8n/n8n-nodes-langchain

# Restart n8n
./launch-n8n-advanced.sh --force-restart
```

### What This Installs

The `@n8n/n8n-nodes-langchain` package provides:

- **AI/LLM Nodes:**
  - `lmChatGemini` - Google Gemini chat
  - `lmChatOpenAI` - OpenAI chat
  - `lmChatAnthropic` - Anthropic Claude
  - And many more...

- **Vector Store Nodes:**
  - Pinecone, Qdrant, Weaviate, etc.

- **Document Processing:**
  - Text splitters, embeddings, retrievers

- **Memory Nodes:**
  - Buffer memory, conversation memory

---

## Verification

After installation, verify the nodes are available:

1. Start n8n: `./launch-n8n-advanced.sh`
2. Open workflow editor
3. Click "+" to add node
4. Search for "Gemini" - you should see "Chat Gemini" node
5. Search for "OpenAI" - you should see AI-related nodes

---

## TTA.dev Workflows Using LangChain Nodes

### Workflows That Need LangChain:

1. **Smart Commit & Test** (`n8n_1_smart_commit_test.json`)
   - Uses: `lmChatGemini` for commit message generation

2. **PR Manager** (`n8n_2_pr_manager.json`)
   - Uses: `lmChatGemini` for AI code review

3. **Issue-to-Branch** (`n8n_3_issue_to_branch.json`)
   - Uses: `lmChatGemini` for implementation plan generation

4. **Release Automation** (`n8n_4_release_automation.json`)
   - Uses: `lmChatGemini` for changelog generation

---

## Alternative: HTTP Request Node

If you prefer not to use community nodes, you can replace the LangChain nodes with HTTP Request nodes calling the Gemini API directly:

### Example HTTP Request to Gemini API

```json
{
  "parameters": {
    "url": "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent",
    "authentication": "genericCredentialType",
    "genericAuthType": "httpQueryAuth",
    "sendQuery": true,
    "queryParameters": {
      "parameters": [
        {
          "name": "key",
          "value": "={{ $env.GEMINI_API_KEY }}"
        }
      ]
    },
    "method": "POST",
    "sendBody": true,
    "bodyParameters": {
      "parameters": [
        {
          "name": "contents",
          "value": "={{ [{role: 'user', parts: [{text: $json.prompt}]}] }}"
        }
      ]
    }
  },
  "type": "n8n-nodes-base.httpRequest"
}
```

However, the LangChain nodes are **much easier** and handle authentication, retries, and response parsing automatically.

---

## Troubleshooting

### Issue: "Package not found"

```bash
# Check if npm is working
npm --version

# Check node version (should be 18+)
node --version

# If using nvm, ensure correct node version
nvm use 22
```

### Issue: "Permission denied"

```bash
# Install without sudo (if using nvm)
npm install -g @n8n/n8n-nodes-langchain

# OR use sudo (if system node)
sudo npm install -g @n8n/n8n-nodes-langchain
```

### Issue: "Nodes still not showing up"

1. **Restart n8n completely:**
   ```bash
   pkill -f n8n
   ./launch-n8n-advanced.sh
   ```

2. **Check n8n community nodes settings:**
   - In n8n UI: Settings → Community Nodes
   - Verify `@n8n/n8n-nodes-langchain` is listed

3. **Clear n8n cache:**
   ```bash
   rm -rf ~/.n8n/cache
   ./launch-n8n-advanced.sh --force-restart
   ```

---

## Additional Community Nodes (Optional)

### Other Useful Packages for TTA.dev:

```bash
# PostgreSQL/database operations
npm install -g n8n-nodes-postgres-extended

# Advanced GitHub operations
npm install -g n8n-nodes-github-advanced

# Slack integration
npm install -g n8n-nodes-slack-enhanced

# Python code execution
npm install -g n8n-nodes-python-runner
```

---

## Why Use Community Nodes?

### Benefits:

1. **Easier Integration** - Pre-built, tested nodes
2. **Better Error Handling** - Built-in retries and validation
3. **Automatic Updates** - Security and feature updates via npm
4. **Less Code** - No need to write HTTP requests manually
5. **Type Safety** - Proper input/output types

### Drawbacks:

1. **Dependencies** - Additional npm packages to manage
2. **Updates Required** - Need to keep packages updated
3. **Size** - Larger installation footprint

For TTA.dev, the benefits **far outweigh** the drawbacks, especially for AI/LLM integrations.

---

## Next Steps

After installing community nodes:

1. ✅ Import all 4 workflows from `workflows/` directory
2. ✅ Configure credentials (GitHub API, Gemini API)
3. ✅ Activate workflows
4. ✅ Test with manual execution

See: `workflows/README.md` for detailed workflow documentation.

---

**Last Updated:** November 9, 2025
**Package Version:** @n8n/n8n-nodes-langchain@1.118.0
**Maintained by:** TTA.dev Team
