#!/usr/bin/env python3
"""
Test ML capabilities of the default E2B template.

Tests various ML libraries and capabilities needed for:
- A/B testing local models
- Training specialized models for TTA
- Data analysis and model evaluation
"""

import asyncio
import os
from pathlib import Path

from tta_dev_primitives import WorkflowContext
from tta_dev_primitives.integrations import CodeExecutionPrimitive


def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


async def test_ml_library_availability(executor: CodeExecutionPrimitive, context: WorkflowContext):
    """Test what ML libraries are available in the default environment."""
    print("🔍 Testing ML Library Availability")
    print("-" * 40)

    library_test_code = """
# Test core ML libraries
import sys
print(f"Python: {sys.version}")
print()

# Core data science stack
try:
    import numpy as np
    print(f"✅ NumPy: {np.__version__}")
except ImportError:
    print("❌ NumPy: Not available")

try:
    import pandas as pd
    print(f"✅ Pandas: {pd.__version__}")
except ImportError:
    print("❌ Pandas: Not available")

try:
    import matplotlib
    print(f"✅ Matplotlib: {matplotlib.__version__}")
except ImportError:
    print("❌ Matplotlib: Not available")

try:
    import seaborn as sns
    print(f"✅ Seaborn: {sns.__version__}")
except ImportError:
    print("❌ Seaborn: Not available")

# Machine Learning libraries
try:
    import sklearn
    print(f"✅ Scikit-learn: {sklearn.__version__}")
except ImportError:
    print("❌ Scikit-learn: Not available")

try:
    import scipy
    print(f"✅ SciPy: {scipy.__version__}")
except ImportError:
    print("❌ SciPy: Not available")

# Deep Learning frameworks
try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"  - CUDA available: {torch.cuda.is_available()}")
except ImportError:
    print("❌ PyTorch: Not available")

try:
    import tensorflow as tf
    print(f"✅ TensorFlow: {tf.__version__}")
except ImportError:
    print("❌ TensorFlow: Not available")

# NLP libraries
try:
    import transformers
    print(f"✅ Transformers: {transformers.__version__}")
except ImportError:
    print("❌ Transformers: Not available")

try:
    import openai
    print(f"✅ OpenAI: {openai.__version__}")
except ImportError:
    print("❌ OpenAI: Not available")

# Other useful libraries
try:
    import requests
    print(f"✅ Requests: {requests.__version__}")
except ImportError:
    print("❌ Requests: Not available")

try:
    import joblib
    print(f"✅ Joblib: {joblib.__version__}")
except ImportError:
    print("❌ Joblib: Not available")
"""

    result = await executor.execute({"code": library_test_code, "timeout": 60}, context)
    print(result["logs"][0] if result["logs"] else "No output")

    if result["error"]:
        print(f"❌ Error: {result['error']}")

    return result["success"]


async def test_basic_ml_workflow(executor: CodeExecutionPrimitive, context: WorkflowContext):
    """Test a basic ML workflow - data processing, model training, evaluation."""
    print("\n🧠 Testing Basic ML Workflow")
    print("-" * 40)

    ml_workflow_code = """
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd

print("🔄 Generating synthetic dataset...")
# Create synthetic classification dataset
X, y = make_classification(
    n_samples=1000,
    n_features=20,
    n_informative=15,
    n_redundant=5,
    n_classes=3,
    random_state=42
)

print(f"Dataset shape: {X.shape}")
print(f"Classes: {np.unique(y, return_counts=True)}")

print("\\n📊 Creating DataFrame...")
# Convert to DataFrame for easier handling
feature_names = [f"feature_{i}" for i in range(X.shape[1])]
df = pd.DataFrame(X, columns=feature_names)
df['target'] = y

print(f"DataFrame info:")
print(f"Shape: {df.shape}")
print(f"Memory usage: {df.memory_usage().sum() / 1024:.1f} KB")

print("\\n🔀 Splitting data...")
# Split the data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training set: {X_train.shape}")
print(f"Test set: {X_test.shape}")

print("\\n🌲 Training Random Forest model...")
# Train a model
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

print("✅ Model trained successfully!")

print("\\n📈 Evaluating model...")
# Make predictions
y_pred = rf.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"Accuracy: {accuracy:.4f}")
print(f"Feature importance (top 5):")
feature_importance = pd.DataFrame({
    'feature': feature_names,
    'importance': rf.feature_importances_
}).sort_values('importance', ascending=False)

print(feature_importance.head().to_string(index=False))

print("\\n🎯 Model successfully trained and evaluated!")
"""

    result = await executor.execute({"code": ml_workflow_code, "timeout": 90}, context)
    print(result["logs"][0] if result["logs"] else "No output")

    if result["error"]:
        print(f"❌ Error: {result['error']}")

    return result["success"]


async def test_model_ab_testing_simulation(
    executor: CodeExecutionPrimitive, context: WorkflowContext
):
    """Test A/B testing simulation for model comparison."""
    print("\n🔀 Testing A/B Model Comparison")
    print("-" * 40)

    ab_test_code = """
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score
import time

print("🔄 Setting up A/B test with multiple models...")

# Generate dataset
X, y = make_classification(
    n_samples=2000,
    n_features=15,
    n_informative=10,
    n_classes=2,
    random_state=42
)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)

# Define models for A/B testing
models = {
    'Model_A_RandomForest': RandomForestClassifier(n_estimators=50, random_state=42),
    'Model_B_LogisticRegression': LogisticRegression(random_state=42, max_iter=1000),
    'Model_C_SVM': SVC(random_state=42, probability=True)
}

results = {}

print("\\n🏁 Training and evaluating models...")
for name, model in models.items():
    print(f"\\n📊 Testing {name}:")

    # Time training
    start_time = time.time()
    model.fit(X_train, y_train)
    training_time = time.time() - start_time

    # Time prediction
    start_time = time.time()
    predictions = model.predict(X_test)
    prediction_time = time.time() - start_time

    # Calculate metrics
    accuracy = accuracy_score(y_test, predictions)
    precision = precision_score(y_test, predictions, average='weighted')
    recall = recall_score(y_test, predictions, average='weighted')

    results[name] = {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'training_time': training_time,
        'prediction_time': prediction_time
    }

    print(f"  Accuracy: {accuracy:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall: {recall:.4f}")
    print(f"  Training time: {training_time:.3f}s")
    print(f"  Prediction time: {prediction_time:.3f}s")

print("\\n🏆 A/B Test Results Summary:")
print("-" * 60)
best_accuracy = max(results.items(), key=lambda x: x[1]['accuracy'])
fastest_training = min(results.items(), key=lambda x: x[1]['training_time'])
fastest_prediction = min(results.items(), key=lambda x: x[1]['prediction_time'])

print(f"🥇 Best accuracy: {best_accuracy[0]} ({best_accuracy[1]['accuracy']:.4f})")
print(f"⚡ Fastest training: {fastest_training[0]} ({fastest_training[1]['training_time']:.3f}s)")
print(f"🚀 Fastest prediction: {fastest_prediction[0]} ({fastest_prediction[1]['prediction_time']:.3f}s)")

print("\\n✅ A/B testing simulation completed successfully!")
"""

    result = await executor.execute({"code": ab_test_code, "timeout": 120}, context)
    print(result["logs"][0] if result["logs"] else "No output")

    if result["error"]:
        print(f"❌ Error: {result['error']}")

    return result["success"]


async def test_specialized_model_training(
    executor: CodeExecutionPrimitive, context: WorkflowContext
):
    """Test training a specialized model that could be useful for TTA workflows."""
    print("\n🎯 Testing Specialized Model Training (Text Classification)")
    print("-" * 40)

    specialized_model_code = """
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

print("📝 Creating synthetic text classification dataset...")

# Simulate text data that might be relevant for TTA workflows
# (e.g., classifying code snippets, error messages, or workflow types)
sample_texts = [
    # Workflow type classification examples
    "sequential workflow with retry logic and fallback handling",
    "parallel execution using multiple workers with load balancing",
    "router primitive selecting best model based on complexity",
    "cache primitive with TTL and LRU eviction policy",
    "timeout primitive with circuit breaker pattern implementation",
    "error handling workflow with compensation and rollback",
    "async workflow with proper context propagation",
    "observability integration with metrics and tracing",
    "sequential processing pipeline with validation steps",
    "parallel batch processing with result aggregation",
    "smart routing based on input characteristics and load",
    "caching strategy with intelligent invalidation rules",
    "timeout management with graceful degradation paths",
    "comprehensive error recovery with state restoration",
    "asynchronous execution with proper resource cleanup",
    "monitoring and telemetry collection framework"
]

# Create labels (categories for different workflow patterns)
labels = [
    "sequential", "parallel", "routing", "caching", "timeout",
    "error_handling", "async", "observability",
    "sequential", "parallel", "routing", "caching",
    "timeout", "error_handling", "async", "observability"
]

print(f"Dataset: {len(sample_texts)} text samples")
print(f"Categories: {set(labels)}")

print("\\n🔧 Building specialized text classification pipeline...")

# Create a pipeline for text classification
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(max_features=1000, stop_words='english')),
    ('classifier', MultinomialNB())
])

# Split data (simple split for demo)
split_idx = int(len(sample_texts) * 0.7)
X_train, X_test = sample_texts[:split_idx], sample_texts[split_idx:]
y_train, y_test = labels[:split_idx], labels[split_idx:]

print(f"Training set: {len(X_train)} samples")
print(f"Test set: {len(X_test)} samples")

print("\\n🚀 Training specialized model...")
pipeline.fit(X_train, y_train)

print("✅ Model trained!")

print("\\n📊 Evaluating specialized model...")
predictions = pipeline.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print(f"Accuracy: {accuracy:.4f}")

print("\\n🔍 Testing model on new examples...")
test_examples = [
    "implement retry mechanism with exponential backoff strategy",
    "run multiple tasks concurrently with shared state management",
    "cache expensive operations with time-based expiration"
]

for example in test_examples:
    prediction = pipeline.predict([example])[0]
    probabilities = pipeline.predict_proba([example])[0]
    confidence = max(probabilities)
    print(f"  '{example[:50]}...' → {prediction} (confidence: {confidence:.3f})")

print("\\n🎯 Specialized model training completed successfully!")
print("This demonstrates training custom models for TTA workflow classification.")
"""

    result = await executor.execute({"code": specialized_model_code, "timeout": 90}, context)
    print(result["logs"][0] if result["logs"] else "No output")

    if result["error"]:
        print(f"❌ Error: {result['error']}")

    return result["success"]


async def main():
    """Main test runner for ML capabilities."""
    print("🧪 E2B ML Capabilities Test")
    print("=" * 50)

    load_env()

    # Initialize executor
    executor = CodeExecutionPrimitive()
    context = WorkflowContext(trace_id="ml-test-001")

    try:
        # Test 1: Library availability
        success1 = await test_ml_library_availability(executor, context)

        # Test 2: Basic ML workflow
        success2 = await test_basic_ml_workflow(executor, context)

        # Test 3: A/B testing simulation
        success3 = await test_model_ab_testing_simulation(executor, context)

        # Test 4: Specialized model training
        success4 = await test_specialized_model_training(executor, context)

        # Summary
        print("\n" + "=" * 50)
        print("🏁 ML Capabilities Test Summary")
        print("=" * 50)

        tests = [
            ("Library Availability", success1),
            ("Basic ML Workflow", success2),
            ("A/B Testing Simulation", success3),
            ("Specialized Model Training", success4),
        ]

        passed = sum(1 for _, success in tests if success)
        total = len(tests)

        for test_name, success in tests:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")

        print(f"\nOverall: {passed}/{total} tests passed")

        if passed == total:
            print("\n🎉 All ML capabilities are available!")
            print("🚀 Default E2B template is ready for:")
            print("   • A/B testing local models")
            print("   • Training specialized models for TTA")
            print("   • Data analysis and model evaluation")
            print("   • Custom ML workflow development")
        else:
            print("\n⚠️  Some capabilities may be limited.")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")

    finally:
        await executor.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
