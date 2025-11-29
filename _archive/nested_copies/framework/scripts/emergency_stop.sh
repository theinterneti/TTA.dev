#!/usr/bin/env bash
# Emergency stop for stale test/server processes
# Use this after a test crash or hang to clean up lingering processes

echo "🛑 Stopping stale test and server processes..."
echo ""

# Find Python processes related to tests or servers
PYTHON_PROCS=$(ps aux | grep -E '(pytest|test_|mcp.*server|run_integration|run_mcp)' | grep -v grep | awk '{print $2}')

if [ -z "$PYTHON_PROCS" ]; then
    echo "✅ No stale test/server processes found"
    exit 0
fi

echo "Found the following processes:"
ps aux | grep -E '(pytest|test_|mcp.*server|run_integration|run_mcp)' | grep -v grep
echo ""

read -p "Kill these processes? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    for pid in $PYTHON_PROCS; do
        echo "Killing process $pid..."
        kill -9 $pid 2>/dev/null || true
    done
    echo ""
    echo "✅ Processes terminated"
else
    echo "Cancelled"
    exit 1
fi

# Also check for orphaned port listeners
echo ""
echo "Checking for orphaned port listeners (8001, 8002)..."
LISTENERS=$(lsof -ti:8001,8002 2>/dev/null || true)

if [ -n "$LISTENERS" ]; then
    echo "Found processes on ports 8001/8002:"
    lsof -i:8001,8002 2>/dev/null || true
    echo ""
    read -p "Kill these port listeners? (y/N) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for pid in $LISTENERS; do
            echo "Killing process $pid on port..."
            kill -9 $pid 2>/dev/null || true
        done
        echo "✅ Port listeners terminated"
    fi
fi

echo ""
echo "✅ Cleanup complete"
