---
title: Issue #48: Session Persistence - Implementation Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/ISSUE-048-IMPLEMENTATION-GUIDE.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/Issue #48: Session Persistence - Implementation Guide]]

## 🎯 Objective

Fix session persistence so users remain authenticated after page refresh.

---

## 📋 Implementation Steps

### **Phase 1: Modify secureStorage.ts (Token Persistence)**

**File**: `src/player_experience/frontend/src/utils/secureStorage.ts`

**Changes Required**:

1. **Add localStorage fallback** (after line 38):
```typescript
setToken(accessToken: string, expiresIn: number = 3600): void {
  const expiresAt = Date.now() + (expiresIn * 1000);

  this.tokenData = {
    accessToken,
    expiresAt,
  };

  // PERSIST TO LOCALSTORAGE (NEW)
  try {
    localStorage.setItem('tta_token', JSON.stringify({
      accessToken,
      expiresAt,
    }));
  } catch (error) {
    console.warn('Failed to persist token to localStorage:', error);
  }

  this.scheduleTokenRefresh(expiresAt);
}
```

2. **Restore from localStorage on init** (add new method):
```typescript
restoreFromStorage(): void {
  try {
    const stored = localStorage.getItem('tta_token');
    if (stored) {
      const data = JSON.parse(stored);
      if (Date.now() < data.expiresAt) {
        this.tokenData = data;
        this.scheduleTokenRefresh(data.expiresAt);
      } else {
        localStorage.removeItem('tta_token');
      }
    }
  } catch (error) {
    console.warn('Failed to restore token from localStorage:', error);
  }
}
```

3. **Call restoreFromStorage on module load** (add at end):
```typescript
// Restore token from localStorage on app load
secureStorage.restoreFromStorage();
```

---

### **Phase 2: Update sessionRestoration.ts**

**File**: `src/player_experience/frontend/src/utils/sessionRestoration.ts`

**Changes Required**:

1. **Restore token before verification** (line 96, in `restoreAuthentication()`):
```typescript
async function restoreAuthentication(): Promise<boolean> {
  try {
    // RESTORE TOKEN FROM STORAGE FIRST (NEW)
    secureStorage.restoreFromStorage();

    // Check retry limit...
    if (authRetryCount >= MAX_AUTH_RETRIES) {
      // ... existing code
    }
    // ... rest of function
  }
}
```

---

### **Phase 3: Update authSlice.ts**

**File**: `src/player_experience/frontend/src/store/slices/authSlice.ts`

**Changes Required**:

1. **Persist auth state to localStorage** (in `login.fulfilled`, line 144):
```typescript
.addCase(login.fulfilled, (state, action) => {
  state.isLoading = false;
  state.isAuthenticated = true;
  state.user = action.payload.user;
  state.token = action.payload.token;
  state.sessionId = action.payload.sessionId;

  // PERSIST AUTH STATE (NEW)
  try {
    localStorage.setItem('tta_auth_state', JSON.stringify({
      user: action.payload.user,
      sessionId: action.payload.sessionId,
      isAuthenticated: true,
    }));
  } catch (error) {
    console.warn('Failed to persist auth state:', error);
  }
})
```

2. **Clear on logout** (in `logout.fulfilled`, line 159):
```typescript
.addCase(logout.fulfilled, (state) => {
  // ... existing code

  // CLEAR PERSISTED STATE (NEW)
  localStorage.removeItem('tta_auth_state');
})
```

---

### **Phase 4: Verify Backend Session Management**

**File**: `src/player_experience/api/routers/openrouter_auth.py`

**Check**:
- [ ] Session cookies are set with `httponly=True`
- [ ] Session cookies have proper `max_age` (24 hours)
- [ ] Session validation endpoint exists
- [ ] Backend returns session info on `/auth/status` endpoint

---

## 🧪 Testing Checklist

### **Manual Testing**:
1. [ ] Login with demo credentials
2. [ ] Refresh page (F5)
3. [ ] Verify user remains authenticated
4. [ ] Check localStorage has token
5. [ ] Check sessionStorage has session data
6. [ ] Logout and verify cleanup

### **E2E Tests**:
1. [ ] Run: `npm test -- 01-authentication.staging.spec.ts`
2. [ ] Verify "should persist session after page refresh" passes
3. [ ] Verify "should persist session across navigation" passes
4. [ ] Check all other auth tests still pass

---

## 🔒 Security Notes

**Implemented Safeguards**:
- Token stored with expiration time
- Expired tokens automatically cleared
- localStorage cleared on logout
- XSS protection via CSP headers (backend)
- httpOnly cookies for refresh tokens (backend)

**Recommendations**:
- Monitor localStorage usage in security audits
- Consider token encryption for extra security
- Implement rate limiting on token refresh
- Add security headers to prevent XSS

---

## 📊 Expected Results

**Before Fix**:
- ❌ Session lost after page refresh
- ❌ 2 E2E tests failing
- ❌ Users redirected to login

**After Fix**:
- ✅ Session persists after page refresh
- ✅ 2 E2E tests passing
- ✅ Users remain authenticated
- ✅ Seamless user experience

---

## 🚀 Deployment

1. Implement all phases
2. Run full E2E test suite
3. Verify no regressions
4. Commit with message: `fix(session): implement token persistence for page refresh`
5. Deploy to staging
6. Validate in staging environment
7. Deploy to production


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs issue 048 implementation guide document]]
