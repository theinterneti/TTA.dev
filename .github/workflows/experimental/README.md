# Experimental Workflow Agent Integrations

This directory contains experimental GitHub workflow integrations for testing various AI coding agents.

## Purpose

Test and validate GitHub Actions integrations with:
- @gemini (Google Gemini AI)
- @copilot (GitHub Copilot)
- @cline (Cline AI)
- Other AI coding assistants

## Workflow Categories

### Gemini Workflows

Located in `gemini/` subdirectory:

- **gemini-dispatch.yml** - Dispatch workflow for Gemini actions
- **gemini-invoke-advanced.yml** - Advanced Gemini invocation with MCP
- **gemini-invoke.yml** - Basic Gemini invocation
- **gemini-review.yml** - Gemini code review automation
- **gemini-test-minimal.yml** - Minimal Gemini test
- **gemini-triage.yml** - Issue triage with Gemini
- **list-gemini-models.yml** - List available Gemini models
- **test-gemini-api-key.yml** - Validate Gemini API key
- **test-gemini-cli-no-mcp.yml** - Test Gemini CLI without MCP
- **test-gemini-keys.yml** - Test multiple Gemini API keys

## Branch Policy

**Branch:** `experimental/workflow-agent-integrations`

This branch is specifically for:
- Testing workflow agent integrations
- Validating AI agent behaviors in CI/CD
- Experimenting with new agent features
- Debugging agent-specific issues

## Do NOT Merge to Main

These workflows are experimental and should not be merged to `main` or `refactor/repo-reorg` branches until:

1. ✅ Thoroughly tested and validated
2. ✅ Documented with clear usage guidelines
3. ✅ Approved by repository maintainers
4. ✅ Necessary secrets configured in production
5. ✅ Rate limits and costs understood

## Testing Workflow

1. Make changes to experimental workflows
2. Push to `experimental/workflow-agent-integrations` branch
3. Monitor workflow runs in Actions tab
4. Document results and issues
5. Iterate until stable
6. Create PR with documentation when ready for review

## Related Documentation

- **Main Workflows:** `../.github/workflows/` (production workflows)
- **Agent Instructions:** `AGENTS.md`
- **Copilot Setup:** `.github/COPILOT_SETUP_SUMMARY.md`
- **MCP Integration:** `MCP_SERVERS.md`

---

**Last Updated:** 2025-11-17
**Maintained by:** TTA.dev Team
**Status:** Experimental - Do Not Use in Production
