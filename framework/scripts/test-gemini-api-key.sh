#!/bin/bash
# Test Gemini API Key Directly
# This script tests if API keys work with Gemini API outside GitHub Actions

set -e

echo "=== Gemini API Key Tester ==="
echo ""

# Test function for AI Studio API key
test_ai_studio() {
    local api_key=$1
    echo "Testing AI Studio API key..."
    echo "Model: gemini-1.5-flash"
    echo "Endpoint: generativelanguage.googleapis.com"
    echo ""

    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -H "Content-Type: application/json" \
        -d '{
            "contents": [{
                "parts": [{"text": "Say hello in one sentence"}]
            }]
        }' \
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${api_key}")

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d')

    echo "HTTP Status: $http_code"
    echo ""

    if [ "$http_code" = "200" ]; then
        echo "✅ SUCCESS! API key works with AI Studio"
        echo ""
        echo "Response:"
        echo "$body" | jq -r '.candidates[0].content.parts[0].text' 2>/dev/null || echo "$body"
        return 0
    else
        echo "❌ FAILED! API key does not work"
        echo ""
        echo "Error response:"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 1
    fi
}

# Test function for Vertex AI API key
test_vertex_ai() {
    local api_key=$1
    local project_id=$2
    local location=${3:-us-central1}

    echo "Testing Vertex AI API key..."
    echo "Project: $project_id"
    echo "Location: $location"
    echo "Model: gemini-1.5-flash"
    echo "Endpoint: ${location}-aiplatform.googleapis.com"
    echo ""

    response=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${api_key}" \
        -d '{
            "contents": [{
                "role": "user",
                "parts": [{"text": "Say hello in one sentence"}]
            }]
        }' \
        "https://${location}-aiplatform.googleapis.com/v1/projects/${project_id}/locations/${location}/publishers/google/models/gemini-1.5-flash:generateContent")

    http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
    body=$(echo "$response" | sed '/HTTP_CODE:/d')

    echo "HTTP Status: $http_code"
    echo ""

    if [ "$http_code" = "200" ]; then
        echo "✅ SUCCESS! API key works with Vertex AI"
        echo ""
        echo "Response:"
        echo "$body" | jq -r '.candidates[0].content.parts[0].text' 2>/dev/null || echo "$body"
        return 0
    else
        echo "❌ FAILED! API key does not work"
        echo ""
        echo "Error response:"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
        return 1
    fi
}

# Main execution
echo "This script will test your API keys directly with Google's APIs"
echo "You'll need to provide the keys from GitHub secrets manually"
echo ""
echo "=================================================="
echo ""

# Test 1: AI Studio pathway
echo "TEST 1: AI Studio API Key (GOOGLE_AI_STUDIO_API_KEY)"
echo "=================================================="
echo ""

if [ -z "$AI_STUDIO_KEY" ]; then
    echo "⚠️  Set AI_STUDIO_KEY environment variable to test"
    echo "   Example: export AI_STUDIO_KEY='your-key-here'"
    echo ""
else
    test_ai_studio "$AI_STUDIO_KEY"
fi

echo ""
echo "=================================================="
echo ""

# Test 2: Vertex AI pathway
echo "TEST 2: Vertex AI API Key (VERTEX_API_KEY)"
echo "=================================================="
echo ""

if [ -z "$VERTEX_KEY" ]; then
    echo "⚠️  Set VERTEX_KEY and GCP_PROJECT environment variables to test"
    echo "   Example: export VERTEX_KEY='your-key-here'"
    echo "   Example: export GCP_PROJECT='604126426981'"
    echo ""
elif [ -z "$GCP_PROJECT" ]; then
    echo "⚠️  Set GCP_PROJECT environment variable"
    echo "   Example: export GCP_PROJECT='604126426981'"
    echo ""
else
    test_vertex_ai "$VERTEX_KEY" "$GCP_PROJECT" "${GCP_LOCATION:-us-central1}"
fi

echo ""
echo "=================================================="
echo ""
echo "SUMMARY:"
echo "--------"
echo ""
echo "If tests succeed (✅):"
echo "  → API keys are valid"
echo "  → Problem is with gemini-cli GitHub Action"
echo "  → Consider filing bug report or using direct API calls"
echo ""
echo "If tests fail (❌):"
echo "  → Check API key permissions in Google Cloud Console"
echo "  → Verify 'Generative Language API' is enabled"
echo "  → Check billing is enabled (if required)"
echo "  → Verify API key restrictions (IP, HTTP referrer, API)"
echo ""
echo "Next steps based on results will determine path forward."
echo ""
