# Gemini CLI Testing Protocol

**Date:** October 31, 2025
**Purpose:** Systematic testing of @gemini mentions in GitHub issues/PRs
**Status:** Ready to Execute

---

## Test Suite Overview

This protocol defines a series of tests to validate and assess the quality of the Gemini CLI GitHub integration.

---

## Test 1: Basic Help Command

### Objective
Verify basic functionality and response time

### Steps
1. Navigate to issue #61
2. Post comment: `@gemini-cli help`
3. Monitor workflow execution
4. Assess response

### Expected Outcome
- Response within 30 seconds
- Help text with available commands
- No errors in workflow

### Success Criteria
- ✅ Response time < 30s
- ✅ Valid help information
- ✅ Proper markdown formatting

---

## Test 2: Repository Analysis

### Objective
Test natural language understanding and GitHub tool usage

### Steps
1. Navigate to issue #61
2. Post comment: `@gemini-cli Analyze the current Gemini CLI integration in this repository. What are the key components, and what recent improvements have been made?`
3. Monitor workflow execution
4. Assess response quality

### Expected Outcome
- Response within 2 minutes
- Uses GitHub MCP tools to gather context
- Mentions workflows, documentation, recent PRs
- Provides structured analysis

### Success Criteria
- ✅ Response time < 2 min
- ✅ Accurate information from repo
- ✅ Structured with headings/lists
- ✅ References specific files/PRs

---

## Test 3: PR Review Capability

### Objective
Test code review functionality

### Steps
1. Navigate to PR #74
2. Post comment: `@gemini-cli /review`
3. Monitor workflow execution
4. Assess review quality

### Expected Outcome
- Response within 3 minutes
- Analysis of changes
- Specific feedback on modified files
- Security/quality observations

### Success Criteria
- ✅ Response time < 3 min
- ✅ File-specific comments
- ✅ Actionable feedback
- ✅ No false positives

---

## Test 4: Documentation Query

### Objective
Test Context7 integration and documentation understanding

### Steps
1. Navigate to issue #61
2. Post comment: `@gemini-cli Using Context7, explain the best practices for using GitHub Actions workflows. Include caching strategies.`
3. Monitor workflow execution
4. Assess response

### Expected Outcome
- Response within 2 minutes
- References external documentation
- Includes caching best practices
- Provides actionable examples

### Success Criteria
- ✅ Response time < 2 min
- ✅ Uses Context7 tool
- ✅ Accurate external references
- ✅ Includes code examples

---

## Test 5: Issue Search

### Objective
Test GitHub search capabilities

### Steps
1. Navigate to issue #61
2. Post comment: `@gemini-cli List all open issues in this repository that are related to GitHub Actions or CI/CD`
3. Monitor workflow execution
4. Assess results

### Expected Outcome
- Response within 1 minute
- List of relevant issues
- Links to each issue
- Brief description of each

### Success Criteria
- ✅ Response time < 1 min
- ✅ Accurate search results
- ✅ Proper issue links
- ✅ No irrelevant issues

---

## Test 6: Write Operation (Plan Only)

### Objective
Test plan → approval workflow for write operations

### Steps
1. Navigate to issue #61
2. Post comment: `@gemini-cli Create a simple markdown document in docs/testing/ that explains how to test the Gemini CLI integration. Include example commands.`
3. Monitor workflow execution
4. Assess plan quality

### Expected Outcome
- Response within 2 minutes
- Detailed plan posted
- Resource estimate included
- Awaits approval
- Does NOT execute without approval

### Success Criteria
- ✅ Plan posted with checklist
- ✅ Resource estimate present
- ✅ Clear approval instructions
- ✅ No execution without approval

---

## Quality Assessment Matrix

For each test, rate on scale of 1-5:

### Accuracy (1-5)
- 5: Perfectly accurate information
- 4: Minor inaccuracies
- 3: Some incorrect information
- 2: Multiple errors
- 1: Mostly incorrect

### Completeness (1-5)
- 5: Fully addresses all aspects
- 4: Addresses most aspects
- 3: Partial response
- 2: Missing key information
- 1: Incomplete/unhelpful

### Formatting (1-5)
- 5: Excellent markdown, easy to read
- 4: Good formatting, minor issues
- 3: Adequate formatting
- 2: Poor formatting
- 1: Unformatted/hard to read

### Actionability (1-5)
- 5: Clear, specific next steps
- 4: Mostly actionable
- 3: Some actionable items
- 2: Vague suggestions
- 1: No actionable guidance

### Context Awareness (1-5)
- 5: Excellent use of repo context
- 4: Good context usage
- 3: Some context used
- 2: Minimal context
- 1: Ignores context

---

## Performance Metrics

Track for each test:

- **Start Time**: When comment posted
- **Response Time**: When Gemini responds
- **Workflow Duration**: Total workflow time
- **Tool Calls**: Number of MCP tools used
- **Error Count**: Any errors encountered

---

## A/B Test Comparison

### Scenario: Same Prompt, Different Models

**Test Prompt:**
```
Analyze the security implications of the contents:write permission in the Gemini CLI workflow. What risks exist and how are they mitigated?
```

**Models to Test:**
1. `gemini-2.0-flash-thinking-exp-1219` (current default)
2. `gemini-1.5-pro-002` (proven quality)
3. `gemini-2.0-flash-exp` (speed)

**Comparison Metrics:**
- Response time
- Quality score (average of 5 criteria)
- Token usage
- Tool calls made
- Specific insights provided

---

## Results Template

```markdown
## Test Results Summary

**Date:** [Date]
**Tester:** [Name]

### Test 1: Basic Help
- ✅/❌ Status:
- ⏱️ Response Time:
- 📊 Quality Score:
- 📝 Notes:

### Test 2: Repository Analysis
- ✅/❌ Status:
- ⏱️ Response Time:
- 📊 Quality Score:
- 📝 Notes:

[Continue for all tests...]

### Overall Assessment
- Success Rate: X/6 tests passed
- Average Response Time: Xs
- Average Quality Score: X/5
- Key Findings:
  1.
  2.
  3.

### Recommendations
1.
2.
3.
```

---

## Safety Protocols

### Before Testing
- ✅ Verify you're on a test issue/PR (not production)
- ✅ Check workflow file hasn't been modified maliciously
- ✅ Ensure API keys are valid
- ✅ Notify team of testing session

### During Testing
- ⚠️ Monitor workflow logs for errors
- ⚠️ Don't approve write operations without review
- ⚠️ Stop if unexpected behavior occurs
- ⚠️ Document all issues immediately

### After Testing
- ✅ Document all results
- ✅ Share findings with team
- ✅ Update documentation as needed
- ✅ Create issues for any bugs found

---

## Next Steps

1. **Execute Tests**: Run all 6 tests in sequence
2. **Document Results**: Fill out results template
3. **Analyze Data**: Compare against success criteria
4. **Create A/B Test**: Run comparison with different models
5. **Report Findings**: Update optimization plan with results

---

**Ready to Begin Testing!** 🚀

Let's systematically test each scenario and gather data for improvement.


---
**Logseq:** [[TTA.dev/Docs/Status-reports/Gemini-cli/Gemini-cli-testing-protocol]]
