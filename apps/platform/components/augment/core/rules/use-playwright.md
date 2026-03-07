---
type: "agent_requested"
description: "Use Playwright for browser automation, E2E testing, and web interaction"
---

# Use Playwright for Browser Automation and E2E Testing

## Rule Priority
**HIGH** - Apply when working with web applications, E2E testing, or browser automation

## When to Use Playwright Tools

Prefer Playwright's browser automation tools for web interaction and testing:

### 1. E2E Testing
- **Use**: `browser_navigate_Playwright`, `browser_click_Playwright`, `browser_type_Playwright`
- **When**: Running end-to-end tests for web applications
- **Example**: Testing user login flow, form submissions, navigation

### 2. Browser Automation
- **Use**: `browser_fill_form_Playwright`, `browser_click_Playwright`, `browser_evaluate_Playwright`
- **When**: Automating repetitive browser tasks
- **Example**: Filling forms, clicking buttons, executing JavaScript

### 3. Web Scraping
- **Use**: `browser_navigate_Playwright`, `browser_snapshot_Playwright`, `browser_evaluate_Playwright`
- **When**: Extracting data from web pages requiring JavaScript execution
- **Example**: Scraping dynamic content, SPA data extraction

### 4. Visual Regression Testing
- **Use**: `browser_take_screenshot_Playwright`
- **When**: Capturing screenshots for visual comparison
- **Example**: Comparing UI changes, detecting visual regressions

### 5. Form Testing
- **Use**: `browser_fill_form_Playwright`, `browser_type_Playwright`, `browser_click_Playwright`
- **When**: Testing form submissions and validations
- **Example**: Testing input validation, error messages, success flows

### 6. Network Inspection
- **Use**: `browser_network_requests_Playwright`, `browser_navigate_Playwright`
- **When**: Monitoring network requests and responses
- **Example**: Debugging API calls, checking request/response data

## Benefits

- **Full Browser Context**: Executes JavaScript, handles dynamic content, simulates real user interactions
- **Accessibility Snapshots**: `browser_snapshot_Playwright` provides structured page state for element selection
- **Screenshot Capabilities**: Capture full page or specific elements for visual testing
- **Network Monitoring**: Track all network requests and responses during page interactions
- **Dialog Handling**: Automatically handle alerts, confirms, and prompts

## Concrete Examples

### Example 1: Navigate and Interact with Page Elements

```python
# Navigate to page
browser_navigate_Playwright(url="https://example.com/login")

# Get page snapshot to find elements
browser_snapshot_Playwright()

# Click login button
browser_click_Playwright(
    element="Login button",
    ref="button[type='submit']"
)
```

### Example 2: Fill and Submit Forms

```python
# Navigate to form page
browser_navigate_Playwright(url="https://example.com/signup")

# Fill multiple form fields at once
browser_fill_form_Playwright(
    fields=[
        {"name": "Email field", "type": "textbox", "ref": "input[name='email']", "value": "user@example.com"},
        {"name": "Password field", "type": "textbox", "ref": "input[name='password']", "value": "SecurePass123"},
        {"name": "Terms checkbox", "type": "checkbox", "ref": "input[name='terms']", "value": "true"}
    ]
)

# Submit form
browser_click_Playwright(
    element="Submit button",
    ref="button[type='submit']"
)
```

### Example 3: Take Screenshots

```python
# Take full page screenshot
browser_take_screenshot_Playwright(
    filename="full-page.png",
    fullPage=True,
    type="png"
)

# Take element-specific screenshot
browser_take_screenshot_Playwright(
    filename="login-form.png",
    element="Login form",
    ref="form#login-form",
    type="png"
)
```

### Example 4: Handle Dialogs and Popups

```python
# Navigate to page that shows dialog
browser_navigate_Playwright(url="https://example.com/confirm")

# Click button that triggers confirm dialog
browser_click_Playwright(
    element="Delete button",
    ref="button#delete"
)

# Handle the confirm dialog (accept)
browser_handle_dialog_Playwright(accept=True)

# Or handle prompt dialog with text
browser_handle_dialog_Playwright(
    accept=True,
    promptText="Confirmation text"
)
```

### Example 5: Inspect Network Requests

```python
# Navigate to page
browser_navigate_Playwright(url="https://example.com/dashboard")

# Get all network requests
browser_network_requests_Playwright()

# Returns: List of all requests with URL, method, status, headers, response
# Use this to debug API calls, check request/response data
```

## When NOT to Use Playwright Tools

**Use `web-fetch` or `launch-process` instead when:**

1. **Simple HTTP requests** - Just need to fetch static HTML
   ```
   ❌ Don't: browser_navigate_Playwright for static content
   ✅ Do: web-fetch(url="https://example.com")
   ```

2. **API testing** - Testing REST APIs without browser
   ```
   ❌ Don't: browser_navigate_Playwright for API endpoints
   ✅ Do: launch-process with curl or use github-api tool
   ```

3. **Static content** - Page doesn't require JavaScript execution
   ```
   ❌ Don't: Playwright for simple HTML pages
   ✅ Do: web-fetch for static content
   ```

4. **Non-browser tasks** - Task doesn't involve web interaction
   ```
   ❌ Don't: Playwright for code navigation
   ✅ Do: Use Serena tools for code operations
   ```

**Use `codebase-retrieval` instead when:**

1. **Code search** - Looking for code patterns, not web content
   ```
   ❌ Don't: Playwright to search code
   ✅ Do: codebase-retrieval("Where is user authentication?")
   ```

## Tool Selection Guide

### Decision Tree: Playwright vs web-fetch vs launch-process

```
Need to interact with web content?
├─ Requires JavaScript execution?
│  ├─ Yes → Use Playwright
│  │   ├─ Dynamic content (SPAs, React apps)
│  │   ├─ User interaction simulation
│  │   └─ Browser-specific features
│  └─ No → Use web-fetch
│      ├─ Static HTML pages
│      ├─ Simple content extraction
│      └─ No JavaScript needed
│
Need to test web application?
├─ E2E testing → Use Playwright
│   ├─ User flows
│   ├─ Form submissions
│   └─ Visual regression
│
Need to automate browser tasks?
├─ Repetitive tasks → Use Playwright
│   ├─ Form filling
│   ├─ Data extraction
│   └─ Screenshot capture
│
Need custom browser configuration?
├─ Yes → Use launch-process with headless browser
└─ No → Use Playwright (simpler, integrated)
```

### When to Combine Tools

**Pattern 1: Fetch then Interact**
```
1. web-fetch(url) → Get initial page structure
2. browser_navigate_Playwright(url) → Load page in browser
3. browser_click_Playwright(...) → Interact with dynamic elements
```

**Pattern 2: Scrape then Process**
```
1. browser_navigate_Playwright(url) → Load dynamic page
2. browser_snapshot_Playwright() → Get page structure
3. browser_evaluate_Playwright(...) → Extract data with JavaScript
4. Use Serena or view to process extracted data
```

**Pattern 3: Test then Screenshot**
```
1. browser_navigate_Playwright(url) → Navigate to page
2. browser_fill_form_Playwright(...) → Fill form
3. browser_click_Playwright(...) → Submit
4. browser_take_screenshot_Playwright(...) → Capture result
```

## Default Workflow

1. **Before browser operations**: Call `browser_snapshot_Playwright()` to get current page state
2. **Before clicking**: Verify element exists in snapshot
3. **After navigation**: Wait for page load with `browser_wait_for_Playwright()`
4. **For debugging**: Check `browser_console_messages_Playwright()` for errors
5. **For network issues**: Review `browser_network_requests_Playwright()` for failed requests

## Performance Considerations

### Browser Installation

**Ensure browser is installed:**
```python
# ✅ Good: Install browser if needed
browser_install_Playwright()

# Then proceed with browser operations
browser_navigate_Playwright(url="https://example.com")
```

**Error handling:**
```
If you get "Browser not installed" error:
1. Call browser_install_Playwright()
2. Retry the operation
```

### Element Selection

**Use accessibility snapshots for accurate element selection:**
```python
# ✅ Good: Get snapshot first
browser_snapshot_Playwright()
# Review snapshot to find correct element ref
browser_click_Playwright(element="Login button", ref="button[data-testid='login']")

# ❌ Avoid: Guessing element refs
browser_click_Playwright(element="Button", ref="button")  # Too generic, may fail
```

### Wait Strategies

**Use appropriate wait strategies:**
```python
# ✅ Good: Wait for specific text
browser_wait_for_Playwright(text="Welcome")

# ✅ Good: Wait for text to disappear
browser_wait_for_Playwright(textGone="Loading...")

# ✅ Good: Wait for specific time
browser_wait_for_Playwright(time=2)  # 2 seconds

# ❌ Avoid: No wait after navigation
browser_navigate_Playwright(url="https://example.com")
browser_click_Playwright(...)  # May fail if page not loaded
```

### Tab Management

**Manage tabs efficiently:**
```python
# List all tabs
browser_tabs_Playwright(action="list")

# Create new tab
browser_tabs_Playwright(action="new")

# Switch to specific tab
browser_tabs_Playwright(action="select", index=1)

# Close current tab
browser_tabs_Playwright(action="close")
```

## TTA-Specific Use Cases

### Test Narrative UI Components

```python
# Navigate to narrative UI
browser_navigate_Playwright(url="http://localhost:3000/narrative")

# Take screenshot of narrative scene
browser_take_screenshot_Playwright(
    filename="narrative-scene-1.png",
    element="Narrative container",
    ref="div[data-testid='narrative-scene']"
)
```

### Validate Gameplay Loop Interactions

```python
# Navigate to gameplay loop
browser_navigate_Playwright(url="http://localhost:3000/gameplay")

# Simulate user choice
browser_click_Playwright(
    element="Choice button",
    ref="button[data-choice='option-1']"
)

# Verify outcome
browser_snapshot_Playwright()
```

### Test Agent Orchestration Dashboard

```python
# Navigate to dashboard
browser_navigate_Playwright(url="http://localhost:3000/dashboard")

# Check network requests for agent API calls
browser_network_requests_Playwright()

# Verify agent status updates
browser_wait_for_Playwright(text="Agent: Active")
```

## Troubleshooting

### Browser Not Installed

**Symptom:** Error message "Browser not installed"

**Solutions:**
1. Call `browser_install_Playwright()` to install browser
2. Retry the operation after installation
3. Verify installation succeeded before proceeding

### Element Not Found

**Symptom:** Click or type operation fails with "Element not found"

**Solutions:**
1. Call `browser_snapshot_Playwright()` to get current page state
2. Verify element ref matches snapshot structure
3. Wait for element to appear with `browser_wait_for_Playwright(text="...")`
4. Check if element is in different tab or frame

### Timeout Errors

**Symptom:** Operation times out waiting for page/element

**Solutions:**
1. Increase wait time with `browser_wait_for_Playwright(time=10)`
2. Check network requests with `browser_network_requests_Playwright()` for slow APIs
3. Verify page is actually loading (check console messages)
4. Use more specific wait conditions (wait for specific text)

### Dialog Handling Errors

**Symptom:** Dialog appears but isn't handled, blocking further operations

**Solutions:**
1. Call `browser_handle_dialog_Playwright(accept=True)` immediately after triggering dialog
2. For prompts, provide `promptText` parameter
3. Check if dialog is actually present before handling
4. Use `browser_snapshot_Playwright()` to verify dialog state

### Network Request Failures

**Symptom:** Page loads but data is missing or incorrect

**Solutions:**
1. Call `browser_network_requests_Playwright()` to inspect all requests
2. Check for failed requests (status 4xx, 5xx)
3. Verify API endpoints are correct
4. Check request/response headers and data
5. Use `browser_console_messages_Playwright(onlyErrors=True)` for JavaScript errors

## Integration with Other Rules

### MCP Tool Selection
- **Primary:** Use Playwright for browser automation and E2E testing (see `Use-your-tools.md`)
- **Complement:** Use web-fetch for simple HTTP requests
- **Fallback:** Use launch-process for custom browser configurations

### Development Workflows
- **E2E Testing:** Integrate Playwright tests in integrated workflow (see `integrated-workflow.md`)
- **Visual Regression:** Use screenshots in component maturity workflow
- **Debugging:** Use network inspection and console messages for troubleshooting

## Related Documentation

- **MCP Tool Selection:** `Use-your-tools.md` - When to use Playwright vs other MCP tools
- **Integrated Workflow:** `integrated-workflow.md` - E2E testing in spec-to-production pipeline
- **System Prompt:** Playwright tool signatures and parameters

## Summary

**Primary use:** Browser automation, E2E testing, web scraping with JavaScript execution

**Key tools:** `browser_navigate_Playwright`, `browser_click_Playwright`, `browser_fill_form_Playwright`, `browser_take_screenshot_Playwright`, `browser_snapshot_Playwright`

**When to use:** Dynamic web content, user interaction simulation, visual testing, network inspection

**When NOT to use:** Static content (use web-fetch), API testing (use direct calls), code operations (use Serena)

---

**Status:** Active
**Last Updated:** 2025-10-22
**Related Rules:** `Use-your-tools.md`, `integrated-workflow.md`


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Rules/Use-playwright]]
