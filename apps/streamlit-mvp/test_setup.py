#!/usr/bin/env python3
"""
Quick test to verify Streamlit MVP is ready to run
"""

import sys
from pathlib import Path

print("🧪 TTA Streamlit MVP - Pre-Flight Check")
print("=" * 50)
print()

# Test 1: Check we're in the right place
print("1. Checking location...")
app_file = Path("app.py")
if app_file.exists():
    print("   ✅ Found app.py")
else:
    print("   ❌ app.py not found! Run this from apps/streamlit-mvp/")
    sys.exit(1)

# Test 2: Check Python version
print("\n2. Checking Python version...")
if sys.version_info >= (3, 8):
    print(f"   ✅ Python {sys.version_info.major}.{sys.version_info.minor}")
else:
    print(
        f"   ⚠️  Python {sys.version_info.major}.{sys.version_info.minor} (recommend 3.8+)"
    )

# Test 3: Check Streamlit import
print("\n3. Checking Streamlit...")
try:
    import streamlit as st

    print(f"   ✅ Streamlit {st.__version__} installed")
except ImportError:
    print("   ❌ Streamlit not installed")
    print("   Run: uv pip install streamlit")
    sys.exit(1)

# Test 4: Check TTA-Rebuild path
print("\n4. Checking TTA-Rebuild backend...")
tta_rebuild_path = (
    Path(__file__).parent.parent.parent / "packages" / "tta-rebuild" / "src"
)
if tta_rebuild_path.exists():
    print(f"   ✅ TTA-Rebuild found at {tta_rebuild_path}")
else:
    print("   ⚠️  TTA-Rebuild not found at expected location")
    print("   App will use fallback mode")

# Test 5: Check if app.py is valid Python
print("\n5. Checking app.py syntax...")
try:
    with open("app.py") as f:
        code = f.read()
    compile(code, "app.py", "exec")
    print("   ✅ app.py syntax is valid")
except SyntaxError as e:
    print(f"   ❌ Syntax error in app.py: {e}")
    sys.exit(1)

# Test 6: Check port availability (optional)
print("\n6. Checking port 8501...")
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("127.0.0.1", 8501))
sock.close()

if result == 0:
    print("   ⚠️  Port 8501 already in use")
    print("   You may need to use a different port or stop the existing process")
else:
    print("   ✅ Port 8501 available")

# Final summary
print("\n" + "=" * 50)
print("✅ PRE-FLIGHT CHECK COMPLETE")
print("\n🚀 Ready to launch! Run:")
print("   ./run.sh")
print("   or")
print("   streamlit run app.py")
print()
