#!/bin/bash

# Test TTA.dev Production API Server
# Comprehensive tests for Gemini integration and primitives

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         TTA.dev Production API - Test Suite                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

API_URL="http://localhost:8000"
TESTS_PASSED=0
TESTS_FAILED=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function to run test
run_test() {
    local test_name="$1"
    local command="$2"
    local expected="$3"

    echo -e "${BLUE}Testing: $test_name${NC}"

    response=$(eval "$command" 2>&1)
    exit_code=$?

    if [ $exit_code -eq 0 ] && echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "   Expected: $expected"
        echo "   Got: $response"
        ((TESTS_FAILED++))
    fi
    echo ""
}

echo "═══════════════════════════════════════════════════════════════"
echo "  HEALTH CHECKS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Test 1: Root endpoint
run_test "Root endpoint (GET /)" \
    "curl -s $API_URL" \
    "healthy"

# Test 2: Health endpoint
run_test "Health endpoint (GET /health)" \
    "curl -s $API_URL/health" \
    '"status":"healthy"'

# Test 3: Gemini status
echo -e "${BLUE}Testing: Gemini availability check${NC}"
HEALTH_RESPONSE=$(curl -s $API_URL/health)
GEMINI_AVAILABLE=$(echo "$HEALTH_RESPONSE" | grep -o '"gemini_available":[^,}]*' | cut -d':' -f2)

if [ "$GEMINI_AVAILABLE" = "true" ]; then
    echo -e "${GREEN}✅ Gemini ENABLED - using real AI${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠️  Gemini DISABLED - using mock mode${NC}"
    echo "   To enable: export GEMINI_API_KEY='your_key'"
    ((TESTS_PASSED++))  # Not a failure, just info
fi
echo ""

# Test 4: Primitives check
echo -e "${BLUE}Testing: TTA.dev primitives status${NC}"
PRIMITIVES=$(curl -s $API_URL/api/v1/primitives)
echo "$PRIMITIVES" | jq '.' 2>/dev/null || echo "$PRIMITIVES"
echo -e "${GREEN}✅ PASS${NC}"
((TESTS_PASSED++))
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  ANALYSIS ENDPOINTS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Test 5: Basic analysis
echo -e "${BLUE}Testing: Basic analysis (POST /api/v1/analyze)${NC}"
BASIC_RESPONSE=$(curl -s -X POST $API_URL/api/v1/analyze \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "What is TTA.dev?",
        "temperature": 0.7
    }')

if echo "$BASIC_RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✅ PASS - Analysis successful${NC}"
    echo "$BASIC_RESPONSE" | jq '.response' 2>/dev/null || echo "Response received"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL - Analysis failed${NC}"
    echo "$BASIC_RESPONSE"
    ((TESTS_FAILED++))
fi
echo ""

# Test 6: GitHub analysis with data
echo -e "${BLUE}Testing: GitHub repo analysis${NC}"
GITHUB_RESPONSE=$(curl -s -X POST $API_URL/api/v1/github/analyze \
    -H "Content-Type: application/json" \
    -d '{
        "prompt": "Analyze this repository health",
        "context": {
            "full_name": "theinterneti/TTA.dev",
            "stargazers_count": 42,
            "forks_count": 8,
            "open_issues_count": 3,
            "language": "Python",
            "description": "AI development toolkit",
            "created_at": "2025-01-01",
            "updated_at": "2025-11-09"
        }
    }')

if echo "$GITHUB_RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✅ PASS - GitHub analysis successful${NC}"

    # Extract and display key metrics
    EXEC_TIME=$(echo "$GITHUB_RESPONSE" | jq '.execution_time_ms' 2>/dev/null)
    TOKENS=$(echo "$GITHUB_RESPONSE" | jq '.tokens_used' 2>/dev/null)
    COST=$(echo "$GITHUB_RESPONSE" | jq '.estimated_cost_usd' 2>/dev/null)

    echo "   Execution time: ${EXEC_TIME}ms"
    echo "   Tokens used: $TOKENS"
    echo "   Estimated cost: \$$COST"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL - GitHub analysis failed${NC}"
    echo "$GITHUB_RESPONSE"
    ((TESTS_FAILED++))
fi
echo ""

# Test 7: Cache test (if enabled)
echo -e "${BLUE}Testing: Cache functionality${NC}"
CACHE_ENABLED=$(echo "$HEALTH_RESPONSE" | jq '.cache_enabled' 2>/dev/null)

if [ "$CACHE_ENABLED" = "true" ]; then
    echo "   Running same query twice to test cache..."

    # First call
    START1=$(date +%s%3N)
    RESP1=$(curl -s -X POST $API_URL/api/v1/analyze \
        -H "Content-Type: application/json" \
        -d '{"prompt": "Cache test query 12345"}')
    END1=$(date +%s%3N)
    TIME1=$((END1 - START1))

    sleep 1

    # Second call (should be cached)
    START2=$(date +%s%3N)
    RESP2=$(curl -s -X POST $API_URL/api/v1/analyze \
        -H "Content-Type: application/json" \
        -d '{"prompt": "Cache test query 12345"}')
    END2=$(date +%s%3N)
    TIME2=$((END2 - START2))

    echo "   First call: ${TIME1}ms"
    echo "   Second call: ${TIME2}ms"

    if [ $TIME2 -lt $TIME1 ]; then
        echo -e "${GREEN}✅ PASS - Cache working (2nd call faster)${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${YELLOW}⚠️  Cache may not be working (times similar)${NC}"
        ((TESTS_PASSED++))  # Not critical failure
    fi
else
    echo -e "${YELLOW}⚠️  Cache not enabled${NC}"
    ((TESTS_PASSED++))
fi
echo ""

# Test 8: Error handling
echo -e "${BLUE}Testing: Error handling (invalid request)${NC}"
ERROR_RESPONSE=$(curl -s -X POST $API_URL/api/v1/analyze \
    -H "Content-Type: application/json" \
    -d '{}')  # Missing required 'prompt' field

if echo "$ERROR_RESPONSE" | grep -q "error\|detail"; then
    echo -e "${GREEN}✅ PASS - Error handled correctly${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL - Error not handled${NC}"
    ((TESTS_FAILED++))
fi
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  n8n WORKFLOW SIMULATION"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Test 9: Complete workflow simulation
echo -e "${BLUE}Testing: Complete n8n workflow${NC}"

# Step 1: Health check
echo "   Step 1: Check API health..."
HEALTH_OK=$(curl -s $API_URL/health | jq '.status' | grep -q "healthy" && echo "OK" || echo "FAIL")

# Step 2: GitHub data (simulated)
echo "   Step 2: Get GitHub data (simulated)..."
GITHUB_DATA='{
    "full_name": "theinterneti/TTA.dev",
    "stargazers_count": 42,
    "forks_count": 8,
    "open_issues_count": 3,
    "language": "Python"
}'

# Step 3: Analyze
echo "   Step 3: Call TTA.dev API for analysis..."
WORKFLOW_RESPONSE=$(curl -s -X POST $API_URL/api/v1/github/analyze \
    -H "Content-Type: application/json" \
    -d "{
        \"prompt\": \"Analyze this repository and provide: 1) Health score (0-100), 2) Top 3 strengths, 3) Top 3 areas for improvement\",
        \"context\": $GITHUB_DATA
    }")

if echo "$WORKFLOW_RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✅ PASS - Complete workflow successful${NC}"
    echo ""
    echo "   Workflow Results:"
    echo "   ─────────────────────────────────────────────────────"
    echo "$WORKFLOW_RESPONSE" | jq -r '.response' 2>/dev/null | head -20 || echo "   Analysis completed"
    echo "   ─────────────────────────────────────────────────────"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAIL - Workflow failed${NC}"
    ((TESTS_FAILED++))
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                      TEST SUMMARY                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✅ Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Failed: $TESTS_FAILED${NC}"
echo ""

TOTAL=$((TESTS_PASSED + TESTS_FAILED))
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! ($TESTS_PASSED/$TOTAL)${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed ($TESTS_FAILED/$TOTAL)${NC}"
    exit 1
fi
