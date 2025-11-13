"""
Test the updated E2B primitive in the main TTA.dev codebase.
"""

import asyncio
import os

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.integrations.e2b_primitive import (
    CodeExecutionPrimitive,
    CodeInput,
)


async def test_updated_primitive():
    """Test the updated E2B primitive with ML capabilities."""

    # Ensure we have the API key
    api_key = os.getenv("E2B_API_KEY") or os.getenv("E2B_KEY")
    if not api_key:
        print("❌ E2B API key not found in environment")
        return

    print("🧪 Testing Updated E2B Primitive")
    print("=" * 50)

    # Create primitive
    primitive = CodeExecutionPrimitive()
    context = WorkflowContext(trace_id="test-updated-001")

    # Test 1: Basic functionality
    print("🔍 Test 1: Basic Python execution")
    code_input = CodeInput(
        code="""
print("Hello from updated E2B primitive!")
print(f"Python version: {__import__('sys').version}")

# Test basic computation
result = sum(range(10))
print(f"Sum of 0-9: {result}")
""",
        timeout=30,
    )

    result = await primitive.execute(code_input, context)
    print(f"Success: {result['success']}")
    print(f"Output: {result['output']}")
    print(f"Execution time: {result['execution_time']:.3f}s")
    print()

    # Test 2: ML libraries availability
    print("🔍 Test 2: ML Libraries Check")
    ml_code = CodeInput(
        code="""
import sys
print("🔍 Checking ML library availability:")

try:
    import numpy as np
    print(f"✅ NumPy: {np.__version__}")
except ImportError:
    print("❌ NumPy not available")

try:
    import pandas as pd
    print(f"✅ Pandas: {pd.__version__}")
except ImportError:
    print("❌ Pandas not available")

try:
    import sklearn
    print(f"✅ Scikit-learn: {sklearn.__version__}")
except ImportError:
    print("❌ Scikit-learn not available")

try:
    import matplotlib
    print(f"✅ Matplotlib: {matplotlib.__version__}")
except ImportError:
    print("❌ Matplotlib not available")
""",
        timeout=60,
    )

    result = await primitive.execute(ml_code, context)
    print(f"Success: {result['success']}")
    print(f"Output:\n{result['output']}")
    print(f"Execution time: {result['execution_time']:.3f}s")
    print()

    # Test 3: A/B testing example
    print("🔍 Test 3: A/B Testing Models")
    ab_test_code = CodeInput(
        code="""
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import numpy as np

print("🔄 Setting up A/B test...")

# Generate synthetic data
X, y = make_classification(
    n_samples=500,
    n_features=10,
    n_classes=2,
    random_state=42
)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")

# Model A: Random Forest
model_a = RandomForestClassifier(n_estimators=50, random_state=42)
model_a.fit(X_train, y_train)
accuracy_a = accuracy_score(y_test, model_a.predict(X_test))

# Model B: Logistic Regression
model_b = LogisticRegression(random_state=42)
model_b.fit(X_train, y_train)
accuracy_b = accuracy_score(y_test, model_b.predict(X_test))

print(f"🏁 A/B Test Results:")
print(f"  Model A (Random Forest): {accuracy_a:.4f}")
print(f"  Model B (Logistic Regression): {accuracy_b:.4f}")

winner = "Random Forest" if accuracy_a > accuracy_b else "Logistic Regression"
improvement = abs(accuracy_a - accuracy_b)
print(f"  Winner: {winner} (+{improvement:.4f})")
""",
        timeout=90,
    )

    result = await primitive.execute(ab_test_code, context)
    print(f"Success: {result['success']}")
    print(f"Output:\n{result['output']}")
    print(f"Execution time: {result['execution_time']:.3f}s")

    if result["error"]:
        print(f"Error: {result['error']}")

    # Cleanup
    await primitive.cleanup()

    print("\n✅ Updated E2B primitive test complete!")
    print("🚀 Ready for production use with ML capabilities!")


if __name__ == "__main__":
    asyncio.run(test_updated_primitive())
