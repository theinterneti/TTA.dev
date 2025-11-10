#!/bin/bash

# End-to-end test for TTA.dev API integration
# Tests all API endpoints and simulates n8n workflow calls

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         TTA.dev API - End-to-End Test                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

API_URL="http://localhost:8000"
FAILED=0
PASSED=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="$5"

    echo -n "Testing: $name... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "$API_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi

    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASSED${NC} (HTTP $status_code)"
        PASSED=$((PASSED + 1))

        # Pretty print JSON if available
        if command -v python3 > /dev/null 2>&1; then
            echo "$body" | python3 -m json.tool 2>/dev/null | head -20 || echo "$body"
        else
            echo "$body" | head -20
        fi
        echo ""
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (Expected HTTP $expected_status, got $status_code)"
        FAILED=$((FAILED + 1))
        echo "Response: $body"
        echo ""
        return 1
    fi
}

echo "═══════════════════════════════════════════════════════════════"
echo "  1. Health Check Tests"
echo "═══════════════════════════════════════════════════════════════"
echo ""

test_endpoint "GET /" "GET" "/" "" "200"
test_endpoint "GET /health" "GET" "/health" "" "200"

echo "═══════════════════════════════════════════════════════════════"
echo "  2. Analysis Endpoint Tests"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Test basic analysis
ANALYZE_DATA='{
  "prompt": "Analyze the health of the TTA.dev repository",
  "context": {"source": "test"},
  "model": "gemini-1.5-flash",
  "temperature": 0.7
}'

test_endpoint "POST /api/v1/analyze (basic)" "POST" "/api/v1/analyze" "$ANALYZE_DATA" "200"

# Test with GitHub data (simulating n8n workflow)
GITHUB_DATA='{
  "prompt": "Repository: TTA.dev\nStars: 42\nForks: 7\nOpen Issues: 15\nLast Commit: 2 days ago\n\nAnalyze the health and activity of this repository.",
  "context": {
    "repo_name": "TTA.dev",
    "stars": 42,
    "forks": 7,
    "open_issues": 15,
    "source": "n8n_workflow"
  }
}'

test_endpoint "POST /api/v1/analyze (GitHub data)" "POST" "/api/v1/analyze" "$GITHUB_DATA" "200"

echo "═══════════════════════════════════════════════════════════════"
echo "  3. n8n Workflow Simulation"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "Simulating n8n workflow steps..."
echo ""

# Step 1: Check API health (like n8n would)
echo "Step 1: Check API Health"
HEALTH_RESPONSE=$(curl -s "$API_URL/health")
STATUS=$(echo "$HEALTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")

if [ "$STATUS" = "healthy" ]; then
    echo -e "${GREEN}✓${NC} API is healthy"
else
    echo -e "${RED}✗${NC} API is not healthy"
    FAILED=$((FAILED + 1))
fi
echo ""

# Step 2: Get GitHub data (this would come from GitHub API in n8n)
echo "Step 2: Fetch GitHub Data (simulated)"
GITHUB_RESPONSE='{
  "repo": "theinterneti/TTA.dev",
  "stars": 42,
  "forks": 7,
  "open_issues": 15,
  "last_commit": "2 days ago"
}'
echo "$GITHUB_RESPONSE" | python3 -m json.tool
echo ""

# Step 3: Format prompt for analysis
echo "Step 3: Format Prompt"
FORMATTED_PROMPT="Repository: TTA.dev, Stars: 42, Forks: 7, Open Issues: 15, Last Commit: 2 days ago. Provide a brief health assessment."
echo "$FORMATTED_PROMPT"
echo ""

# Step 4: Call TTA.dev API for analysis
echo "Step 4: Call TTA.dev API"
FINAL_REQUEST=$(cat <<EOF
{
  "prompt": "$FORMATTED_PROMPT",
  "context": {
    "repo_name": "TTA.dev",
    "stars": 42,
    "source": "n8n_workflow"
  }
}
EOF
)

ANALYSIS_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/analyze" \
    -H "Content-Type: application/json" \
    -d "$FINAL_REQUEST")

echo "$ANALYSIS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$ANALYSIS_RESPONSE"

# Check if analysis succeeded
SUCCESS=$(echo "$ANALYSIS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))")

if [ "$SUCCESS" = "True" ]; then
    echo -e "${GREEN}✓${NC} Analysis completed successfully"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗${NC} Analysis failed"
    FAILED=$((FAILED + 1))
fi
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  Test Summary"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "Total Tests: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "🎉 Your TTA.dev API is ready for n8n integration!"
    echo ""
    echo "Next steps:"
    echo "  1. Import the workflow: ./scripts/n8n/import_tta_workflow.sh"
    echo "  2. Open n8n: http://localhost:5678"
    echo "  3. Execute the workflow and verify results"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Please check the API server logs:"
    echo "  tail -f /tmp/tta_api.log"
    echo ""
    exit 1
fi
