---
title: TTA Core Gameplay Loop - Manual Frontend Testing Guide
tags: #TTA
status: Active
repo: theinterneti/TTA
path: docs/testing/manual_frontend_testing_guide.md
created: 2025-11-01
updated: 2025-11-01
---
# [[TTA/Workflows/TTA Core Gameplay Loop - Manual Frontend Testing Guide]]

## Prerequisites

1. **TTA Server Running:** Ensure the TTA server is running on http://localhost:8000
2. **Browser:** Use a modern browser (Chrome, Firefox, Safari, Edge)
3. **Network:** Ensure localhost access is available

## Testing Procedure

### Phase 1: Initial Setup Validation

1. **Open Frontend Example**
   ```bash
   # Open in your default browser
   open examples/frontend_integration.html

   # Or navigate manually to:
   file:///path/to/recovered-tta-storytelling/examples/frontend_integration.html
   ```

2. **Verify Page Load**
   - ✅ Page loads without errors
   - ✅ Title shows "TTA Therapeutic Text Adventure"
   - ✅ Authentication section is visible
   - ✅ No JavaScript console errors

### Phase 2: API Documentation Testing

1. **Open API Documentation**
   ```bash
   # Open Swagger UI
   open http://localhost:8000/docs
   ```

2. **Verify API Endpoints**
   - ✅ Swagger UI loads successfully
   - ✅ Gameplay endpoints are listed:
     - `POST /api/v1/gameplay/sessions`
     - `GET /api/v1/gameplay/sessions/{session_id}`
     - `POST /api/v1/gameplay/sessions/{session_id}/choices`
     - `GET /api/v1/gameplay/health`
   - ✅ Authentication endpoints are available
   - ✅ All endpoints show proper request/response schemas

### Phase 3: Authentication Testing

#### Option A: Test Token (Recommended for Demo)
1. **Use Test Token**
   - Click "Use Test Token" button
   - ✅ Status shows "Using test token for demo"
   - ✅ Game section becomes visible
   - ✅ Authentication section hides

#### Option B: Real Authentication (If Database is Working)
1. **Try Demo Credentials**
   - Username: `demo_user`
   - Password: `demo_password`
   - Click "Login"
   - ✅ Authentication succeeds or shows appropriate error

### Phase 4: Session Management Testing

1. **Start New Session**
   - Click "Start New Session" button
   - ✅ Loading indicator appears
   - ✅ Status shows session creation result
   - ✅ Session controls become enabled

2. **Session Status Check**
   - Verify session ID is displayed
   - ✅ Session controls (Pause/End) are enabled
   - ✅ Current scene section appears

### Phase 5: API Endpoint Testing via Swagger UI

1. **Health Check Endpoint**
   ```
   GET /api/v1/gameplay/health
   ```
   - Click "Try it out"
   - Add Authorization header: `Bearer test_token_demo`
   - Execute request
   - ✅ Returns 200 OK or appropriate auth error

2. **Session Creation Endpoint**
   ```
   POST /api/v1/gameplay/sessions
   ```
   - Click "Try it out"
   - Add Authorization header: `Bearer test_token_demo`
   - Use request body:
   ```json
   {
     "therapeutic_context": {
       "goals": ["anxiety_management", "social_skills"]
     }
   }
   ```
   - Execute request
   - ✅ Returns session creation response

3. **Session Status Endpoint**
   ```
   GET /api/v1/gameplay/sessions/{session_id}
   ```
   - Use session ID from previous step
   - Add Authorization header
   - Execute request
   - ✅ Returns session status

### Phase 6: Error Handling Testing

1. **Unauthorized Access**
   - Remove Authorization header from any request
   - ✅ Returns 401 Unauthorized

2. **Invalid Session ID**
   - Use non-existent session ID
   - ✅ Returns 404 Not Found

3. **Malformed Requests**
   - Send invalid JSON
   - ✅ Returns 422 Validation Error

### Phase 7: Browser Console Testing

1. **Open Developer Tools**
   - Press F12 or right-click → Inspect
   - Go to Console tab

2. **Check for Errors**
   - ✅ No JavaScript errors
   - ✅ No CORS errors
   - ✅ Network requests succeed or fail gracefully

3. **Network Tab Inspection**
   - Go to Network tab
   - Perform actions in the frontend
   - ✅ API calls are made to correct endpoints
   - ✅ Request headers include Authorization
   - ✅ Response codes are appropriate

## Expected Results

### ✅ Success Criteria

1. **Frontend Functionality**
   - Page loads without errors
   - Authentication flow works (test token)
   - Session management UI responds correctly
   - Status messages are clear and helpful

2. **API Integration**
   - All gameplay endpoints are accessible
   - Swagger UI documentation is complete
   - Request/response formats are correct
   - Error handling is appropriate

3. **User Experience**
   - Interface is responsive and intuitive
   - Loading states are shown during API calls
   - Error messages are user-friendly
   - Session state is maintained correctly

### ⚠️ Known Limitations

1. **Database Authentication**
   - Real user authentication may fail due to database setup
   - Use test token for demonstration purposes

2. **Session Persistence**
   - Sessions may not persist due to database connectivity
   - Focus on API structure and integration testing

3. **Real-time Features**
   - WebSocket functionality not yet implemented
   - Polling-based updates only

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure server is running on localhost:8000
   - Check browser console for CORS policy errors

2. **Authentication Failures**
   - Use "Test Token" option for demo
   - Check server logs for authentication errors

3. **API Endpoint Not Found**
   - Verify server is running
   - Check endpoint URLs in frontend code

4. **Network Connectivity**
   - Ensure localhost:8000 is accessible
   - Check firewall settings

### Debug Commands

```bash
# Check server status
curl http://localhost:8000/docs

# Test health endpoint
curl -H "Authorization: Bearer test_token_demo" \
     http://localhost:8000/api/v1/gameplay/health

# Check server logs
# (View terminal where server is running)
```

## Validation Checklist

- [ ] Frontend page loads successfully
- [ ] API documentation is accessible
- [ ] Test token authentication works
- [ ] Session creation API responds
- [ ] Session status API responds
- [ ] Error handling works correctly
- [ ] Browser console shows no critical errors
- [ ] Network requests are properly formatted
- [ ] User interface is functional and responsive

## Next Steps After Testing

1. **If All Tests Pass:**
   - Integration is successful
   - Ready for production deployment preparation
   - Can proceed with advanced feature development

2. **If Issues Found:**
   - Document specific failures
   - Check server logs for detailed errors
   - Review configuration settings
   - Consider database connectivity fixes

---

**Testing Guide Version:** 1.0
**Last Updated:** September 23, 2025
**Compatible With:** TTA Core Gameplay Loop Integration v1.0


---
**Logseq:** [[TTA.dev/Platform_tta_dev/Components/Augment/Core/Kb/Tta___workflows___docs testing manual frontend testing guide]]
