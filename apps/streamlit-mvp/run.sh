#!/bin/bash

# TTA Streamlit MVP Launcher
# Quick script to launch the Streamlit frontend

set -e

echo "🎭 TTA Streamlit MVP Launcher"
echo "==============================="
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: app.py not found. Please run this from apps/streamlit-mvp/"
    exit 1
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "📦 Streamlit not found. Installing dependencies..."
    uv pip install -r requirements.txt
fi

echo "🚀 Starting TTA Streamlit MVP..."
echo ""
echo "The app will open in your browser at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Launch streamlit
streamlit run app.py
