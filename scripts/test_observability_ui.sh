#!/bin/bash
# Complete observability UI testing workflow

set -e

echo "🧪 Testing Observability UI"
echo "============================"
echo ""

# Step 1: Start the observability server
echo "📡 Starting observability server..."
uv run python ttadev/ui/observability_server.py &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 5

# Step 2: Verify server is running
echo "🔍 Verifying server is running..."
if curl -s http://localhost:8000 > /dev/null; then
    echo "✅ Server is running on http://localhost:8000"
else
    echo "❌ Server failed to start"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

# Step 3: Run Playwright tests
echo ""
echo "�� Running Playwright tests..."
uv run pytest tests/test_observability_dashboard.py -v

TEST_RESULT=$?

# Step 4: Cleanup
echo ""
echo "🧹 Cleaning up..."
kill $SERVER_PID 2>/dev/null || true
sleep 2

if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi
