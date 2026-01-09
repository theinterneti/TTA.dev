---
title: TTA E2E Tests - Quick Fix Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/project/E2E_QUICK_FIX_GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/TTA E2E Tests - Quick Fix Guide]]

This guide provides step-by-step instructions to fix the critical issues blocking E2E test execution.

---

## Priority 1: Add Test Identifiers to Components

### Why This Matters:
Tests rely on `data-testid` attributes to reliably find elements. Without them, tests fail even when the UI works correctly.

### Files to Update:

#### 1. Login Component (`src/player_experience/frontend/src/pages/Auth/Login.tsx`)

**Add these data-testid attributes:**
```tsx
<form data-testid="login-form" className="mt-8 space-y-6" onSubmit={handleSubmit}>
  <input
    data-testid="username-input"
    id="username"
    name="username"
    type="text"
    ...
  />
  <input
    data-testid="password-input"
    id="password"
    name="password"
    type="password"
    ...
  />
  <button data-testid="login-button" type="submit">
    {isLoading ? 'Signing in...' : 'Sign in'}
  </button>
</form>

{error && (
  <div data-testid="error-message" className="bg-red-50 border border-red-200">
    <p className="text-sm text-red-800">{error}</p>
  </div>
)}
```

#### 2. Dashboard Component (`src/player_experience/frontend/src/pages/Dashboard/Dashboard.tsx`)

**Add:**
```tsx
<div data-testid="dashboard" className="dashboard-container">
  <h1 data-testid="dashboard-title">Welcome, {profile?.username}</h1>
  <nav data-testid="dashboard-nav">
    {/* navigation items */}
  </nav>
</div>
```

#### 3. Character Management (`src/player_experience/frontend/src/pages/CharacterManagement/CharacterManagement.tsx`)

**Add:**
```tsx
<div data-testid="character-management">
  <button data-testid="create-character-button" onClick={handleCreate}>
    Create Character
  </button>
  <div data-testid="character-list">
    {characters.map(char => (
      <div key={char.id} data-testid={`character-card-${char.id}`}>
        {/* character card content */}
      </div>
    ))}
  </div>
</div>
```

### Pattern to Follow:
```
data-testid="{component}-{element}-{action}"

Examples:
- login-form
- username-input
- password-input
- login-button
- error-message
- dashboard
- character-list
- create-character-button
```

---

## Priority 2: Update Mock API Endpoints

### File: `tests/e2e/mocks/api-server.js`

### Add Missing Endpoints:

```javascript
// Player endpoints
app.get('/api/v1/players/:playerId', (req, res) => {
  const player = players.get(req.params.playerId) || mockPlayer(req.params.playerId);
  res.json(player);
});

app.put('/api/v1/players/:playerId', (req, res) => {
  const player = players.get(req.params.playerId);
  if (!player) {
    return res.status(404).json({ error: 'Player not found' });
  }
  Object.assign(player, req.body);
  players.set(req.params.playerId, player);
  res.json(player);
});

// Character endpoints
app.get('/api/v1/characters', (req, res) => {
  const playerId = req.query.player_id;
  const playerCharacters = Array.from(characters.values())
    .filter(char => !playerId || char.player_id === playerId);
  res.json({ characters: playerCharacters });
});

app.post('/api/v1/characters', (req, res) => {
  const character = mockCharacter(req.body.player_id);
  Object.assign(character, req.body);
  characters.set(character.id, character);
  res.json(character);
});

app.get('/api/v1/characters/:characterId', (req, res) => {
  const character = characters.get(req.params.characterId);
  if (!character) {
    return res.status(404).json({ error: 'Character not found' });
  }
  res.json(character);
});

app.put('/api/v1/characters/:characterId', (req, res) => {
  const character = characters.get(req.params.characterId);
  if (!character) {
    return res.status(404).json({ error: 'Character not found' });
  }
  Object.assign(character, req.body);
  characters.set(req.params.characterId, character);
  res.json(character);
});

app.delete('/api/v1/characters/:characterId', (req, res) => {
  characters.delete(req.params.characterId);
  res.json({ message: 'Character deleted successfully' });
});

// World endpoints
app.get('/api/v1/worlds', (req, res) => {
  const mockWorlds = [
    {
      id: 'world-1',
      name: 'Peaceful Garden',
      description: 'A serene garden environment',
      intensity: 'LOW',
      themes: ['nature', 'calm']
    },
    {
      id: 'world-2',
      name: 'Mountain Peak',
      description: 'A challenging mountain climb',
      intensity: 'MEDIUM',
      themes: ['adventure', 'challenge']
    }
  ];
  res.json({ worlds: mockWorlds });
});

// Session endpoints
app.post('/api/v1/sessions', (req, res) => {
  const session = mockSession(req.body.player_id, req.body.character_id);
  sessions.set(session.id, session);
  res.json(session);
});

app.get('/api/v1/sessions/:sessionId', (req, res) => {
  const session = sessions.get(req.params.sessionId);
  if (!session) {
    return res.status(404).json({ error: 'Session not found' });
  }
  res.json(session);
});

// Settings endpoints
app.get('/api/v1/settings/:playerId', (req, res) => {
  const playerSettings = settings.get(req.params.playerId) || {
    theme: 'light',
    notifications: true,
    intensity: 'MEDIUM'
  };
  res.json(playerSettings);
});

app.put('/api/v1/settings/:playerId', (req, res) => {
  settings.set(req.params.playerId, req.body);
  res.json(req.body);
});
```

---

## Priority 3: Fix Page Object Selectors

### File: `tests/e2e/page-objects/LoginPage.ts`

### Update Selectors to Match Actual DOM:

```typescript
export class LoginPage extends BasePage {
  // Update these selectors
  readonly usernameInput = this.page.locator('input[name="username"]');
  readonly passwordInput = this.page.locator('input[name="password"]');
  readonly loginButton = this.page.locator('button[type="submit"]');
  readonly errorMessage = this.page.locator('.bg-red-50, [data-testid="error-message"]');

  // Or use data-testid (preferred after adding them to components)
  readonly usernameInput = this.page.locator('[data-testid="username-input"]');
  readonly passwordInput = this.page.locator('[data-testid="password-input"]');
  readonly loginButton = this.page.locator('[data-testid="login-button"]');
  readonly errorMessage = this.page.locator('[data-testid="error-message"]');
}
```

---

## Quick Test Commands

### Start Mock API:
```bash
cd tests/e2e/mocks
PORT=8080 node api-server.js
```

### Run Tests:
```bash
# Run all tests
npx playwright test

# Run specific test file
npx playwright test tests/e2e/specs/auth.spec.ts

# Run in headed mode (see browser)
npx playwright test --headed

# Run with specific browser
npx playwright test --project=chromium

# Debug mode
npx playwright test --debug
```

### View Test Report:
```bash
npx playwright show-report
```

---

## Verification Checklist

After making fixes, verify:

- [ ] All components have `data-testid` attributes
- [ ] Mock API returns correct response formats
- [ ] Page object selectors match actual DOM
- [ ] Auth tests pass (target: 20+/26)
- [ ] Dashboard tests pass
- [ ] Character management tests pass
- [ ] No console errors in browser
- [ ] Mock API logs show successful requests

---

## Common Issues & Solutions

### Issue: "Element not found" errors
**Solution:** Add `data-testid` to the component or update selector in page object

### Issue: "Timeout waiting for element"
**Solution:** Check if element exists in DOM, verify selector, increase timeout if needed

### Issue: "API returns 404"
**Solution:** Add missing endpoint to mock API server

### Issue: "Login fails but UI works"
**Solution:** Check mock API response format matches frontend expectations

### Issue: "Tests pass locally but fail in CI"
**Solution:** Ensure mock API is started before tests, check environment variables

---

## Next Steps After Fixes

1. Run full test suite: `npx playwright test`
2. Check pass rate (target: >80%)
3. Fix remaining failures
4. Run cross-browser tests: `npx playwright test --project=firefox --project=webkit`
5. Generate and review HTML report: `npx playwright show-report`
6. Document any new issues found
7. Update this guide with lessons learned

---

## Getting Help

- **Test Documentation:** `tests/e2e/README.md`
- **Playwright Docs:** https://playwright.dev
- **Mock API Code:** `tests/e2e/mocks/api-server.js`
- **Page Objects:** `tests/e2e/page-objects/`
- **Test Specs:** `tests/e2e/specs/`

---

**Last Updated:** October 6, 2025
**Status:** Initial version based on validation findings


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs project e2e quick fix guide document]]
